"""Service layer for user auth/account flows."""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserActivityLog


class LogoutError(Exception):
    """Raised when logout operation cannot be completed."""


class InvalidResetLinkError(Exception):
    """Raised when reset link data cannot be resolved to a user."""


@dataclass(frozen=True)
class RequestContext:
    """Minimal request metadata used by service layer."""

    ip_address: str | None
    user_agent: str


def blacklist_refresh_token(refresh_token: str | None) -> None:
    """Blacklist refresh token when provided."""
    if not refresh_token:
        return
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError as exc:
        raise LogoutError("Token de refresco invalido") from exc


def log_logout_activity(*, user: User, context: RequestContext) -> None:
    """Persist logout audit log."""
    UserActivityLog.objects.create(
        user=user,
        organization=user.organization,
        action='logout',
        ip_address=context.ip_address,
        user_agent=context.user_agent,
    )


def resolve_password_reset_user(uid: str) -> User:
    """Decode uid and return user for password reset confirmation."""
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
        raise InvalidResetLinkError("Enlace de restablecimiento invalido.") from exc


def is_valid_password_reset_token(*, user: User, token: str) -> bool:
    """Validate reset token for a user."""
    return default_token_generator.check_token(user, token)
