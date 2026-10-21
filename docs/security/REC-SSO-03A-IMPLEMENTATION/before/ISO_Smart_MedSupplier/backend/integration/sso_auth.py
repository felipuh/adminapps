"""
Smart3AI SSO authentication for ISO Smart.

Accepts JWTs issued by AdminApps and synchronizes local user/profile context
from token claims so multi-tenant scoping works across services.
"""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils.text import slugify
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from authentication.models import UserProfile
from core.models import Organization
from integration.backends import ROLE_MAP

User = get_user_model()
logger = logging.getLogger(__name__)


class Smart3AISSOAuthentication(JWTAuthentication):
    """JWT auth backend that supports centrally-issued AdminApps SSO tokens."""

    def get_user(self, validated_token):
        user_id = validated_token.get("user_id") or validated_token.get("sub")
        email = str(validated_token.get("email") or "").strip().lower()

        if not user_id and not email:
            raise AuthenticationFailed("Token inválido: faltan claims de usuario", code="token_invalid")

        user = None
        if user_id:
            try:
                user = User.objects.filter(id=user_id).first()
            except Exception:
                user = None

        if user is None and email:
            user = User.objects.filter(email=email).first()

        if user is None:
            first_name = str(validated_token.get("first_name") or "").strip()
            last_name = str(validated_token.get("last_name") or "").strip()
            full_name = str(validated_token.get("full_name") or "").strip()
            if not first_name and full_name:
                first_name = full_name.split(" ")[0]
            if not last_name and full_name and " " in full_name:
                last_name = " ".join(full_name.split(" ")[1:]).strip()

            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )
            user.set_unusable_password()
            try:
                user.save()
            except IntegrityError as exc:
                raise AuthenticationFailed("No fue posible sincronizar el usuario SSO") from exc

        if not user.is_active:
            raise AuthenticationFailed("Usuario inactivo", code="user_inactive")

        self._sync_profile_from_token(user, validated_token)
        return user

    def _sync_profile_from_token(self, user, validated_token):
        org_external_id = str(validated_token.get("organization_id") or "").strip()
        org_name = str(validated_token.get("organization_name") or "").strip()
        org_code = str(validated_token.get("organization_code") or "").strip()
        role = str(validated_token.get("role") or "user").strip().lower()
        mapped_role = ROLE_MAP.get(role, "user")

        if not org_external_id:
            return

        organization = None

        # Local tokens can carry the internal organization PK (int); prefer
        # that lookup before treating the claim as external_id.
        if org_external_id.isdigit():
            organization = Organization.objects.filter(id=int(org_external_id)).first()

        if not organization:
            organization = Organization.objects.filter(external_id=org_external_id).first()

        if not organization:
            source_slug = org_code or org_name or org_external_id
            base_slug = slugify(source_slug) if source_slug else f"org-{org_external_id}"
            slug = base_slug[:80] or f"org-{org_external_id}"
            organization = Organization.objects.create(
                external_id=org_external_id,
                name=org_name or f"Organization {org_external_id}",
                slug=slug,
                is_active=True,
            )

        try:
            UserProfile.objects.update_or_create(
                user=user,
                organization=organization,
                defaults={"role": mapped_role, "is_active": True},
            )
            return
        except IntegrityError:
            # Legacy schemas may still enforce unique(user_id) and reject a
            # second profile row for the same user across organizations.
            existing_profile = UserProfile.objects.filter(user=user).first()
            if not existing_profile:
                raise

            existing_profile.organization = organization
            existing_profile.role = mapped_role
            existing_profile.is_active = True
            existing_profile.save(update_fields=["organization", "role", "is_active"])
            logger.warning(
                "Perfil de usuario reasignado por restriccion unica legacy (SSO). user=%s org=%s",
                user.id,
                organization.id,
            )
