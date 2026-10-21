"""
Smart3AI SSO endpoints for cross-product authentication.

This module issues centrally-managed JWTs with tenant/organization claims,
supports 2FA challenge flow, and provides token introspection for services.
"""

from __future__ import annotations

import json
import uuid
import time
from functools import wraps
from typing import Any

from django.contrib.auth import authenticate, get_user_model
from django.db import DatabaseError, transaction
from rest_framework.exceptions import APIException, ValidationError
from apps.users import two_factor_service as two_factor
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: F401 - historical probes

from apps.users.models import UserOrganization
from apps.products.models import OrganizationProductEntitlement
from .client_registry import require_client, require_tenant
from .trust_jwt import CONTRACT, decode, encode, trust
from . import session_lifecycle as lifecycle
from .authorization import entitlement_eligible

User = get_user_model()

def _json_body(request) -> dict[str, Any]:
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _serialize_memberships(memberships):
    return [
        {
            "id": str(m.organization.id),
            "name": m.organization.name,
            "code": m.organization.code,
            "role": m.role,
            "is_primary": m.is_primary,
        }
        for m in memberships
    ]


def _serialize_product_entitlements(organization_id):
    if not organization_id:
        return []

    entitlements = (
        OrganizationProductEntitlement.objects
        .filter(organization_id=organization_id)
        .select_related('organization', 'product', 'product__default_plan', 'plan', 'subscription', 'subscription__plan')
        .order_by('product__name')
    )
    payload = []
    for entitlement in entitlements:
        subscription = entitlement.effective_subscription
        plan = entitlement.effective_plan
        payload.append({
            "id": str(entitlement.id),
            "code": entitlement.product.code,
            "name": entitlement.product.name,
            "slug": entitlement.product.slug,
            "enabled": entitlement.enabled,
            "status": entitlement.status,
            "access_allowed": entitlement.access_allowed,
            "authorization_eligible": entitlement_eligible(entitlement),
            "access_denial_reason": entitlement.access_denial_reason,
            "scopes": entitlement.scopes,
            "modules_enabled": entitlement.modules_enabled,
            "starts_at": entitlement.starts_at.isoformat() if entitlement.starts_at else None,
            "ends_at": entitlement.ends_at.isoformat() if entitlement.ends_at else None,
            "plan": {
                "id": str(plan.id),
                "code": plan.code,
                "name": plan.name,
                "billing_cycle": plan.billing_cycle,
            } if plan else None,
            "subscription": {
                "id": str(subscription.id),
                "status": subscription.status,
                "is_active": subscription.is_active,
                "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                "next_billing_date": subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            } if subscription else None,
        })
    return payload


def _build_product_claims(organization_id):
    products = _serialize_product_entitlements(organization_id)
    return {
        "product_entitlements": products,
        "allowed_products": [
            product["code"]
            for product in products
            if product.get("access_allowed")
        ],
    }


def _render_session(session, user, membership, products, *, client):
    config, _ = trust('CENTRAL', signing=True)
    if config['ISSUER'] != client.issuer or config['SIGNING_KID'] not in client.allowed_kids:
        raise APIException('Invalid emission contract.')
    now = int(time.time())
    claims = {
        'auth_contract': CONTRACT, 'token_family': 'CENTRAL',
        'iss': client.issuer, 'aud': [client.audience], 'client_id': client.client_id,
        'product': client.product, 'sub': str(user.id), 'user_id': str(user.id),
        'tenant_id': str(membership.organization_id), 'organization_id': str(membership.organization_id),
        'email': user.email, 'role': membership.role,
        'amr': session.authentication_methods, 'iat': now,
        **lifecycle.claims(session),
    }
    if session.mfa_generation:
        claims['mfa_generation'] = str(session.mfa_generation)
    result = {'token_type': 'Bearer', 'allowed_products': [client.product], 'product_entitlements': products}
    for kind in ('access', 'refresh'):
        payload = dict(claims, token_type=kind, jti=str(getattr(session, kind + '_jti')),
                       exp=int(session.expires_at.timestamp()))
        result[kind + '_token'] = encode(payload, family='CENTRAL', audience=client.audience,
                                         product=client.product, client_id=client.client_id)
        result['expires_in' if kind == 'access' else 'refresh_expires_in'] = payload['exp'] - now
    return result


def _build_token_pair_unchecked(user, membership, memberships, *, audience, client_id,
                                authentication_methods=None, mfa_generation=None, client,
                                mfa_challenge_digest=None, expected_epoch=None):
    if client.client_id != client_id or audience != [client.audience]:
        raise APIException('Invalid emission contract.')
    return lifecycle.issue(user, membership, client, list(authentication_methods or []),
                           mfa_generation, mfa_challenge_digest, expected_epoch,
                           lambda *args: _render_session(*args, client=client))


def _build_token_pair(*args, **kwargs):
    try:
        two_factor.require_commit_boundary()
        return _build_token_pair_unchecked(*args, **kwargs)
    except Exception:
        raise APIException('Unable to complete authentication') from None


def _auth_user(request, email: str, password: str):
    user = authenticate(request, email=email, password=password)
    if not user:
        user = authenticate(request, username=email, password=password)
    return user


def _authentication_errors(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except two_factor.ChallengeRejected:
            return JsonResponse({'error': 'Reto 2FA inválido o expirado',
                                 'code': 'invalid_or_expired_challenge'}, status=401)
        except ValidationError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            return JsonResponse({'error': 'Código OTP inválido', 'code': 'invalid_otp',
                                 **{k: v for k, v in detail.items() if k != 'token'}}, status=401)
        except APIException as exc:
            return JsonResponse({'error': exc.detail}, status=exc.status_code)
        except DatabaseError:
            return JsonResponse({'error': 'Unable to complete authentication'}, status=503)
    return wrapped


@transaction.non_atomic_requests
@csrf_exempt
@require_http_methods(["POST"])
@_authentication_errors
@require_client
def sso_login(request):
    """
    Unified login endpoint with optional 2FA challenge.

    Request:
      {email, password, organization_id?, otp_code?, audience?, client_id?}
    """
    data = _json_body(request)
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    organization_id = str(data.get("organization_id") or "").strip() or None
    otp_code = str(data.get("otp_code") or "").strip()
    client = request.sso_client
    client_id = client.client_id
    audience = [client.audience]

    if not email or not password:
        return JsonResponse({
            "error": "Email y contraseña son requeridos",
            "code": "missing_credentials",
        }, status=400)

    expected_epoch = request.sso_authority_epoch
    user = _auth_user(request, email, password)
    if not user:
        return JsonResponse({
            "error": "Credenciales inválidas",
            "code": "invalid_credentials",
        }, status=401)

    if not user.is_active:
        return JsonResponse({
            "error": "Usuario desactivado",
            "code": "user_inactive",
        }, status=403)

    two_factor.validate_user_eligibility(user, timezone.now())

    memberships = list(
        UserOrganization.objects.filter(
            user=user,
            is_active=True,
            organization__status="active",
        ).select_related("organization")
    )
    if not memberships:
        return JsonResponse({
            "error": "Sin organización activa",
            "code": "no_organization",
        }, status=403)

    membership = None
    if organization_id:
        membership = next((m for m in memberships if str(m.organization_id) == organization_id), None)
        if not membership:
            return JsonResponse({
                "error": "El usuario no pertenece a la organización solicitada",
                "code": "not_member",
            }, status=403)
    if not membership:
        membership = next((m for m in memberships if m.is_primary), None) or memberships[0]

    require_tenant(request, str(membership.organization.id))
    two_fa = getattr(user, "two_factor_auth", None)
    two_fa_enabled = bool(two_fa and two_fa.is_enabled)

    if two_fa_enabled:
        challenge_token = two_factor.issue_challenge(user, 'sso', context={
            'authority_epoch': expected_epoch,
            'organization_id': str(membership.organization.id),
            'client_id': client_id, 'audience': audience,
            'product': client.product, 'principal_id': client.principal_id, 'contract_version': CONTRACT,
        })
        if not otp_code:
            return JsonResponse({
                'requires_2fa': True, 'challenge_token': challenge_token,
                'challenge_expires_in': 300,
                'user': {'id': str(user.id), 'email': user.email, 'full_name': user.full_name},
                'organizations': _serialize_memberships([membership]),
            }, status=200)
        user, _ = two_factor.consume_challenge(challenge_token, otp_code, 'sso', request=request)

    two_fa_bypassed = False
    tokens = _build_token_pair(
        user,
        membership,
        memberships,
        audience=audience,
        client_id=client_id,
        client=request.sso_client,
        authentication_methods=["pwd", "otp"] if two_fa_enabled else ["pwd"],
        mfa_generation=two_factor.decode_challenge(challenge_token, "sso").get("generation") if two_fa_enabled else None,
        mfa_challenge_digest=lifecycle.challenge_digest(two_factor.decode_challenge(challenge_token, "sso")) if two_fa_enabled else None,
        expected_epoch=expected_epoch,
    )

    user.last_login_at = timezone.now()
    user.last_activity_at = timezone.now()
    user.failed_login_attempts = 0
    user.save(update_fields=["last_login_at", "last_activity_at", "failed_login_attempts", "updated_at"])

    return JsonResponse({
        "requires_2fa": False,
        "two_fa_bypassed": two_fa_bypassed,
        "tokens": tokens,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": membership.role,
        },
        "current_organization": {
            "id": str(membership.organization.id),
            "name": membership.organization.name,
            "code": membership.organization.code,
        },
        "organizations": _serialize_memberships([membership]),
    }, status=200)


@transaction.non_atomic_requests
@csrf_exempt
@require_http_methods(["POST"])
@_authentication_errors
@require_client
def sso_login_verify_2fa(request):
    """
    Completes a pending 2FA challenge and returns final token pair.
    """
    data = _json_body(request)
    challenge_token = str(data.get("challenge_token") or "").strip()
    otp_code = str(data.get("otp_code") or "").strip()

    if not challenge_token or not otp_code:
        return JsonResponse({
            "error": "challenge_token y otp_code son requeridos",
            "code": "missing_2fa_payload",
        }, status=400)

    challenge_data = two_factor.decode_challenge(challenge_token, 'sso')

    user_id = str(challenge_data.get("user_id") or "")
    organization_id = str(challenge_data.get("organization_id") or "")
    client = request.sso_client
    client_id = client.client_id
    audience = [client.audience]
    if any(challenge_data.get(k) != v for k, v in {
        'client_id': client_id, 'audience': audience, 'product': client.product,
        'principal_id': client.principal_id, 'contract_version': CONTRACT,
        'authority_epoch': request.sso_authority_epoch,
    }.items()):
        return JsonResponse({'code': 'challenge_context_mismatch'}, status=403)
    require_tenant(request, organization_id)

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({
            "error": "Usuario no encontrado",
            "code": "user_not_found",
        }, status=404)

    membership = UserOrganization.objects.filter(
        user=user,
        organization_id=organization_id,
        is_active=True,
        organization__status="active",
    ).select_related("organization").first()
    if not membership:
        return JsonResponse({
            "error": "Membresía no válida",
            "code": "invalid_membership",
        }, status=403)

    user, _ = two_factor.consume_challenge(challenge_token, otp_code, 'sso', request=request)
    two_fa_bypassed = False

    memberships = list(
        UserOrganization.objects.filter(
            user=user,
            is_active=True,
            organization__status="active",
        ).select_related("organization")
    )

    tokens = _build_token_pair(
        user,
        membership,
        memberships,
        audience=[str(item) for item in audience],
        client_id=client_id,
        client=request.sso_client,
        authentication_methods=["pwd", "otp"],
        mfa_generation=challenge_data.get("generation"),
        mfa_challenge_digest=lifecycle.challenge_digest(challenge_data),
        expected_epoch=challenge_data.get("authority_epoch"),
    )

    user.last_login_at = timezone.now()
    user.last_activity_at = timezone.now()
    user.failed_login_attempts = 0
    user.save(update_fields=["last_login_at", "last_activity_at", "failed_login_attempts", "updated_at"])

    return JsonResponse({
        "requires_2fa": False,
        "two_fa_bypassed": two_fa_bypassed,
        "tokens": tokens,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": membership.role,
        },
        "current_organization": {
            "id": str(membership.organization.id),
            "name": membership.organization.name,
            "code": membership.organization.code,
        },
        "organizations": _serialize_memberships([membership]),
    }, status=200)


def _introspection_errors(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except DatabaseError:
            return JsonResponse({
                "active": False, "error": "Unable to complete introspection",
            }, status=503)
    return wrapped


@transaction.non_atomic_requests
@csrf_exempt
@require_http_methods(["POST"])
@_introspection_errors
@require_client
def sso_introspect(request):
    """
    Service-to-service token introspection.
    Requires X-API-Key.
    """
    data = _json_body(request)
    token = str(data.get("token") or "").strip()
    if not token:
        return JsonResponse({"active": False, "error": "token requerido"}, status=400)

    client = request.sso_client
    try:
        parsed = decode(token, family='CENTRAL', audience=client.audience,
                        product=client.product, client_id=client.client_id, allowed_kids=client.allowed_kids)
    except APIException as exc:
        if exc.status_code == 503:
            raise
        return JsonResponse({'active': False}, status=200)
    session, user, membership, products, authorization = lifecycle.introspect(parsed, client, expected_epoch=request.sso_authority_epoch)
    return JsonResponse(dict(parsed, active=True, products=products, authorization=authorization,
                             full_name=user.full_name,
                             organization_name=membership.organization.name,
                             organization_code=membership.organization.code,
                             memberships=_serialize_memberships([membership])))


@transaction.non_atomic_requests
@csrf_exempt
@require_http_methods(['POST'])
@require_client
def sso_logout(request):
    client = request.sso_client
    parsed = decode(_json_body(request).get('token'), family='CENTRAL', audience=client.audience,
                    product=client.product, client_id=client.client_id, allowed_kids=client.allowed_kids)
    lifecycle.logout(parsed, client, expected_epoch=request.sso_authority_epoch)
    return JsonResponse({'revoked': True})


@transaction.non_atomic_requests
@csrf_exempt
@require_http_methods(['POST'])
@require_client
def sso_rotate(request):
    client = request.sso_client
    parsed = decode(_json_body(request).get('token'), family='CENTRAL', audience=client.audience,
                    product=client.product, client_id=client.client_id, allowed_kids=client.allowed_kids)
    tokens = lifecycle.rotate(parsed, client, lambda *args: _render_session(*args, client=client),
                              expected_epoch=request.sso_authority_epoch)
    return JsonResponse({'tokens': tokens})
