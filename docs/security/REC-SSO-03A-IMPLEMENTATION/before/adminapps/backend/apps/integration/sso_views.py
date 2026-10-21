"""
Smart3AI SSO endpoints for cross-product authentication.

This module issues centrally-managed JWTs with tenant/organization claims,
supports 2FA challenge flow, and provides token introspection for services.
"""

from __future__ import annotations

import json
import uuid
from functools import wraps
from typing import Any

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db import DatabaseError, transaction
from rest_framework.exceptions import APIException, ValidationError
from apps.users import two_factor_service as two_factor
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.users.models import UserOrganization
from apps.products.models import OrganizationProductEntitlement
from .views import require_api_key

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


def _build_token_pair_unchecked(
    user,
    membership,
    memberships,
    *,
    audience: list[str],
    client_id: str,
):
    issuer = getattr(settings, "SMART3AI_SSO_ISSUER", "https://sso.smart3ai.local")
    product_claims = _build_product_claims(membership.organization.id)

    refresh = RefreshToken.for_user(user)
    refresh["iss"] = issuer
    refresh["aud"] = audience
    refresh["client_id"] = client_id
    refresh["email"] = user.email
    refresh["full_name"] = user.full_name
    refresh["organization_id"] = str(membership.organization.id)
    refresh["organization_code"] = membership.organization.code
    refresh["organization_name"] = membership.organization.name
    refresh["role"] = membership.role
    refresh["memberships"] = _serialize_memberships(memberships)
    refresh["scope"] = "openid profile email tenant:read tenant:write"
    refresh["allowed_products"] = product_claims["allowed_products"]
    refresh["product_entitlements"] = product_claims["product_entitlements"]

    access = refresh.access_token
    access["iss"] = issuer
    access["aud"] = audience
    access["client_id"] = client_id
    access["email"] = user.email
    access["full_name"] = user.full_name
    access["organization_id"] = str(membership.organization.id)
    access["organization_code"] = membership.organization.code
    access["organization_name"] = membership.organization.name
    access["role"] = membership.role
    access["memberships"] = _serialize_memberships(memberships)
    access["scope"] = "openid profile email tenant:read tenant:write"
    access["allowed_products"] = product_claims["allowed_products"]
    access["product_entitlements"] = product_claims["product_entitlements"]

    return {
        "token_type": "Bearer",
        "access_token": str(access),
        "refresh_token": str(refresh),
        "expires_in": int(getattr(settings, "SIMPLE_JWT", {}).get("ACCESS_TOKEN_LIFETIME").total_seconds()),
        "refresh_expires_in": int(getattr(settings, "SIMPLE_JWT", {}).get("REFRESH_TOKEN_LIFETIME").total_seconds()),
        "allowed_products": product_claims["allowed_products"],
        "product_entitlements": product_claims["product_entitlements"],
    }


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
    client_id = str(data.get("client_id") or "smart3ai-portfolio").strip() or "smart3ai-portfolio"

    raw_audience = data.get("audience") or ["smart3ai-portfolio"]
    if isinstance(raw_audience, str):
        audience = [raw_audience.strip()] if raw_audience.strip() else ["smart3ai-portfolio"]
    elif isinstance(raw_audience, list):
        audience = [str(item).strip() for item in raw_audience if str(item).strip()]
        audience = audience or ["smart3ai-portfolio"]
    else:
        audience = ["smart3ai-portfolio"]

    if not email or not password:
        return JsonResponse({
            "error": "Email y contraseña son requeridos",
            "code": "missing_credentials",
        }, status=400)

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

    two_fa = getattr(user, "two_factor_auth", None)
    two_fa_enabled = bool(two_fa and two_fa.is_enabled)

    if two_fa_enabled:
        challenge_token = two_factor.issue_challenge(user, 'sso', context={
            'organization_id': str(membership.organization.id),
            'client_id': client_id, 'audience': audience,
        })
        if not otp_code:
            return JsonResponse({
                'requires_2fa': True, 'challenge_token': challenge_token,
                'challenge_expires_in': 300,
                'user': {'id': str(user.id), 'email': user.email, 'full_name': user.full_name},
                'organizations': _serialize_memberships(memberships),
            }, status=200)
        user, _ = two_factor.consume_challenge(challenge_token, otp_code, 'sso', request=request)

    two_fa_bypassed = False
    tokens = _build_token_pair(
        user,
        membership,
        memberships,
        audience=audience,
        client_id=client_id,
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
        "organizations": _serialize_memberships(memberships),
    }, status=200)


@transaction.non_atomic_requests
@csrf_exempt
@require_http_methods(["POST"])
@_authentication_errors
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
    client_id = str(challenge_data.get("client_id") or "smart3ai-portfolio")
    audience = challenge_data.get("audience") or ["smart3ai-portfolio"]

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
    )

    user.last_login_at = timezone.now()
    user.last_activity_at = timezone.now()
    user.failed_login_attempts = 0
    user.save(update_fields=["last_login_at", "last_activity_at", "failed_login_attempts", "updated_at"])

    return JsonResponse({
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
        "organizations": _serialize_memberships(memberships),
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


@csrf_exempt
@require_http_methods(["POST"])
@_introspection_errors
@require_api_key
def sso_introspect(request):
    """
    Service-to-service token introspection.
    Requires X-API-Key.
    """
    data = _json_body(request)
    token = str(data.get("token") or "").strip()
    if not token:
        return JsonResponse({"active": False, "error": "token requerido"}, status=400)

    try:
        parsed = AccessToken(token)
    except TokenError:
        return JsonResponse({"active": False}, status=200)

    # Reuse the issuer contract of _build_token_pair_unchecked. Audience/client
    # registration is a separate contract; a caller-supplied audience is not an
    # authorization policy.
    issuer = getattr(settings, "SMART3AI_SSO_ISSUER", "https://sso.smart3ai.local")
    if not issuer or parsed.get("iss") != issuer:
        return JsonResponse({"active": False}, status=200)

    organization_id = str(parsed.get("organization_id") or "")
    user_id = str(parsed.get("user_id") or parsed.get("sub") or "")
    try:
        uuid.UUID(organization_id)
        uuid.UUID(user_id)
    except ValueError:
        return JsonResponse({"active": False}, status=200)

    # Match the live identity/membership predicates used at SSO login. Token
    # snapshots alone cannot establish continued access to this organization.
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({"active": False}, status=200)
    if not UserOrganization.objects.filter(
        user=user,
        organization_id=organization_id,
        is_active=True,
        organization__status="active",
    ).exists():
        return JsonResponse({"active": False}, status=200)

    return JsonResponse({
        "active": True,
        "sub": user_id,
        "email": parsed.get("email"),
        "full_name": parsed.get("full_name"),
        "role": parsed.get("role"),
        "organization_id": organization_id,
        "organization_name": parsed.get("organization_name"),
        "organization_code": parsed.get("organization_code"),
        "memberships": parsed.get("memberships", []),
        "products": _serialize_product_entitlements(organization_id),
        "client_id": parsed.get("client_id"),
        "aud": parsed.get("aud"),
        "iss": parsed.get("iss"),
        "exp": parsed.get("exp"),
        "iat": parsed.get("iat"),
    }, status=200)
