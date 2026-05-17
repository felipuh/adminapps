"""
Smart3AI SSO endpoints for cross-product authentication.

This module issues centrally-managed JWTs with tenant/organization claims,
supports 2FA challenge flow, and provides token introspection for services.
"""

from __future__ import annotations

import json
from typing import Any

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core import signing
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.users.models import UserOrganization
from .views import require_api_key

User = get_user_model()

_TWO_FA_SALT = "smart3ai.sso.2fa"
_TWO_FA_BYPASS_CODE = "BYPASS-LOCAL-2FA"


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


def _build_token_pair(
    user,
    membership,
    memberships,
    *,
    audience: list[str],
    client_id: str,
):
    issuer = getattr(settings, "SMART3AI_SSO_ISSUER", "https://sso.smart3ai.local")

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

    return {
        "token_type": "Bearer",
        "access_token": str(access),
        "refresh_token": str(refresh),
        "expires_in": int(getattr(settings, "SIMPLE_JWT", {}).get("ACCESS_TOKEN_LIFETIME").total_seconds()),
        "refresh_expires_in": int(getattr(settings, "SIMPLE_JWT", {}).get("REFRESH_TOKEN_LIFETIME").total_seconds()),
    }


def _auth_user(request, email: str, password: str):
    user = authenticate(request, email=email, password=password)
    if not user:
        user = authenticate(request, username=email, password=password)
    return user


def _is_local_2fa_bypass(otp_code: str) -> bool:
    return bool(
        getattr(settings, "SMART3AI_SSO_ALLOW_2FA_BYPASS", False)
        and otp_code == _TWO_FA_BYPASS_CODE
    )


@csrf_exempt
@require_http_methods(["POST"])
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

    if two_fa_enabled and not otp_code:
        challenge_token = signing.dumps(
            {
                "user_id": str(user.id),
                "organization_id": str(membership.organization.id),
                "client_id": client_id,
                "audience": audience,
            },
            salt=_TWO_FA_SALT,
        )
        return JsonResponse({
            "requires_2fa": True,
            "challenge_token": challenge_token,
            "challenge_expires_in": 300,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
            },
            "organizations": _serialize_memberships(memberships),
        }, status=200)

    two_fa_bypassed = False
    if two_fa_enabled:
        if _is_local_2fa_bypass(otp_code):
            two_fa_bypassed = True
        else:
            otp_ok = two_fa.verify_token(otp_code)
            backup_ok = False
            if not otp_ok:
                backup_ok = two_fa.use_backup_code(otp_code)
                if backup_ok:
                    two_fa.save(update_fields=["backup_codes_used", "updated_at"])
            if not otp_ok and not backup_ok:
                return JsonResponse({
                    "error": "Código OTP inválido",
                    "code": "invalid_otp",
                }, status=401)

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


@csrf_exempt
@require_http_methods(["POST"])
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

    try:
        challenge_data = signing.loads(challenge_token, salt=_TWO_FA_SALT, max_age=300)
    except signing.BadSignature:
        return JsonResponse({
            "error": "Reto 2FA inválido o expirado",
            "code": "invalid_or_expired_challenge",
        }, status=401)

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

    two_fa = getattr(user, "two_factor_auth", None)
    if not two_fa or not two_fa.is_enabled:
        return JsonResponse({
            "error": "2FA no está habilitado",
            "code": "2fa_not_enabled",
        }, status=400)

    otp_ok = two_fa.verify_token(otp_code)
    two_fa_bypassed = False
    if _is_local_2fa_bypass(otp_code):
        two_fa_bypassed = True
    else:
        otp_ok = two_fa.verify_token(otp_code)
        backup_ok = False
        if not otp_ok:
            backup_ok = two_fa.use_backup_code(otp_code)
            if backup_ok:
                two_fa.save(update_fields=["backup_codes_used", "updated_at"])
        if not otp_ok and not backup_ok:
            return JsonResponse({
                "error": "Código OTP inválido",
                "code": "invalid_otp",
            }, status=401)

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


@csrf_exempt
@require_http_methods(["POST"])
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

    return JsonResponse({
        "active": True,
        "sub": str(parsed.get("user_id") or parsed.get("sub") or ""),
        "email": parsed.get("email"),
        "full_name": parsed.get("full_name"),
        "role": parsed.get("role"),
        "organization_id": parsed.get("organization_id"),
        "organization_name": parsed.get("organization_name"),
        "organization_code": parsed.get("organization_code"),
        "memberships": parsed.get("memberships", []),
        "client_id": parsed.get("client_id"),
        "aud": parsed.get("aud"),
        "iss": parsed.get("iss"),
        "exp": parsed.get("exp"),
        "iat": parsed.get("iat"),
    }, status=200)