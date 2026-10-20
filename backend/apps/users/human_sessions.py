"""Local human JWT authority. Lock order: User -> UserSession.

No bearer token is persisted. Legacy unbound JWTs/rows cannot gain authority.
PostgreSQL authority/monotonic triggers in users.0005 are required at activation.
"""
from datetime import datetime, timezone as dt_timezone
import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import DatabaseError, connection, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, Token

from .models import User, UserSession

FAMILY = 'ADMINAPPS_HUMAN_LOCAL'
VERSION = 1


class SessionUnavailable(APIException):
    status_code = 503
    default_detail = 'Human session authority unavailable'
    default_code = 'human_session_unavailable'


class HumanRefreshToken(Token):
    """Refresh token without SimpleJWT's full-token OutstandingToken storage."""
    token_type = 'refresh'
    lifetime = api_settings.REFRESH_TOKEN_LIFETIME

    @property
    def access_token(self):
        access = AccessToken()
        for key, value in self.payload.items():
            if key not in {api_settings.TOKEN_TYPE_CLAIM, 'exp', 'iat', api_settings.JTI_CLAIM}:
                access[key] = value
        # Both credentials are bounded by the durable family's absolute expiry.
        access['exp'] = min(access['exp'], self['exp'])
        return access


def _deny():
    raise AuthenticationFailed('Invalid or revoked human session', code='human_session_invalid')


def _store():
    # Existing IAM persistence contract is PostgreSQL. No cache/stateless fallback.
    if connection.vendor != 'postgresql':
        raise SessionUnavailable()


def _write_store():
    _store()
    # A caller's later audit/serialization failure must not roll revocation back.
    if connection.in_atomic_block or not connection.get_autocommit():
        raise SessionUnavailable()


def _claims(token, kind):
    try:
        sid = uuid.UUID(token['sid'])
        fid = uuid.UUID(token['fid'])
        uid = uuid.UUID(token[api_settings.USER_ID_CLAIM])
        if (token[api_settings.TOKEN_TYPE_CLAIM] != kind
                or token['token_family'] != FAMILY
                or token.get('principal_type', 'human') != 'human'
                or token.get('client_id') or token.get('product')
                or type(token['hsv']) is not int or token['hsv'] != VERSION
                or any(type(token[k]) is not int or token[k] < 1 for k in ('sg', 'av', 'exp', 'iat'))
                or not isinstance(token[api_settings.JTI_CLAIM], str)
                or not token[api_settings.JTI_CLAIM]):
            _deny()
        return sid, fid, uid
    except (KeyError, ValueError, TypeError, AttributeError):
        _deny()


def _check(token, session, user, kind):
    sid, fid, uid = _claims(token, kind)
    now = timezone.now()
    expiry = user.get_temporary_password_expiry()
    if (not user.is_active or user.is_locked or (expiry and now >= expiry)
            or session.pk != sid or session.user_id != uid or user.pk != uid
            or session.contract_version != VERSION or session.token_family != FAMILY
            or session.family_id != fid or not session.is_active or session.revoked_at is not None
            or session.generation != token['sg']
            or session.authority_version != token['av'] or user.human_auth_version != token['av']
            or not session.created_at <= now < session.expires_at
            or not int(session.created_at.timestamp()) <= token['iat'] <= int(now.timestamp())
            or not now.timestamp() < token['exp'] <= int(session.expires_at.timestamp())
            or token['exp'] <= token['iat']
            or (kind == 'refresh' and session.token_jti != token[api_settings.JTI_CLAIM])):
        _deny()
    return user


def authenticate_access(token):
    """One joined statement reads live user + authoritative session consistently."""
    sid, _, uid = _claims(token, 'access')
    try:
        _store()
        session = UserSession.objects.select_related('user').get(pk=sid, user_id=uid)
        return _check(token, session, session.user, 'access')
    except (UserSession.DoesNotExist, User.DoesNotExist, DjangoValidationError, ValueError):
        _deny()
    except DatabaseError:
        raise SessionUnavailable() from None


def issue_refresh(user):
    """Issue only after login/MFA gates; re-read live authority under the user lock."""
    try:
        _write_store()
        with transaction.atomic(durable=True):
            live = User.objects.select_for_update().get(pk=user.pk)
            now = timezone.now()
            expiry = live.get_temporary_password_expiry()
            if (not live.is_active or live.is_locked or (expiry and now >= expiry)
                    or live.password != user.password
                    or live.human_auth_version != user.human_auth_version):
                # Re-reading live state must not upgrade an authentication that
                # predates a password change or disable/re-enable transition.
                _deny()
            token = HumanRefreshToken.for_user(live)
            sid, fid = uuid.uuid4(), uuid.uuid4()
            # Use JWT second precision in the durable expiry too.
            expires = datetime.fromtimestamp(token['exp'], tz=dt_timezone.utc)
            session = UserSession.objects.create(
                id=sid, user=live, token_jti=token[api_settings.JTI_CLAIM],
                contract_version=VERSION, token_family=FAMILY, family_id=fid,
                generation=1, authority_version=live.human_auth_version,
                expires_at=expires,
            )
            token.payload.update(sid=str(session.pk), fid=str(fid), token_family=FAMILY,
                                 hsv=VERSION, sg=1, av=live.human_auth_version)
        return token
    except User.DoesNotExist:
        _deny()
    except DatabaseError:
        raise SessionUnavailable() from None


def refresh_pair(raw, *, expected_user_id=None):
    """Serialized rotation: old generations and lost-response retries stay denied."""
    try:
        token = HumanRefreshToken(raw)
        sid, _, uid = _claims(token, 'refresh')
        if expected_user_id is not None and str(uid) != str(expected_user_id):
            _deny()
        _write_store()
        with transaction.atomic(durable=True):
            user = User.objects.select_for_update().get(pk=uid)
            session = UserSession.objects.select_for_update().get(pk=sid, user_id=uid)
            _check(token, session, user, 'refresh')
            if api_settings.ROTATE_REFRESH_TOKENS:
                session.generation += 1
                token.set_jti()
                token.set_iat()
                token['sg'] = session.generation
                session.token_jti = token[api_settings.JTI_CLAIM]
                session.save(update_fields=['generation', 'token_jti'])
            # No sliding extension of the durable family's absolute lifetime.
            result = {'access': str(token.access_token)}
            if api_settings.ROTATE_REFRESH_TOKENS:
                result['refresh'] = str(token)
        return result
    except (TokenError, User.DoesNotExist, UserSession.DoesNotExist,
            DjangoValidationError, ValueError, TypeError):
        _deny()
    except DatabaseError:
        raise SessionUnavailable() from None


def revoke(user, *, session_id=None, keep_session_id=None, reason='user_revocation'):
    """Owned single/all/other revocation. Repeated revocation never restores state."""
    if session_id is not None and keep_session_id is not None:
        _deny()
    try:
        sid = uuid.UUID(str(session_id)) if session_id is not None else None
        keep = uuid.UUID(str(keep_session_id)) if keep_session_id is not None else None
        _write_store()
        with transaction.atomic(durable=True):
            live = User.objects.select_for_update().get(pk=user.pk)
            if not live.is_active:
                _deny()
            rows = UserSession.objects.select_for_update().filter(user_id=live.pk)
            if sid is not None:
                # Check ownership even on retries; never mutate foreign/unknown IDs.
                rows.get(pk=sid)
                rows = rows.filter(pk=sid)
            if keep is not None:
                rows.get(pk=keep)
                rows = rows.exclude(pk=keep)
            return rows.filter(is_active=True, revoked_at__isnull=True).update(
                is_active=False, revoked_at=timezone.now(), revocation_reason=reason,
                generation=F('generation') + 1,
            )
    except (User.DoesNotExist, UserSession.DoesNotExist, ValueError, TypeError, DjangoValidationError):
        _deny()
    except DatabaseError:
        raise SessionUnavailable() from None


def logout_session(user, access, refresh=None):
    """A supplied refresh must belong to the SAME authenticated family."""
    sid, fid, uid = _claims(access, 'access')
    if str(uid) != str(user.pk):
        _deny()
    if refresh:
        try:
            token = HumanRefreshToken(refresh)
            rsid, rfid, ruid = _claims(token, 'refresh')
        except TokenError:
            _deny()
        if (rsid, rfid, ruid) != (sid, fid, uid):
            _deny()
    return revoke(user, session_id=sid, reason='logout')


def logout_cookie_refresh(user, raw):
    """Withdraw an owned bound refresh for a cookie caller; persist no JWT."""
    try:
        token = HumanRefreshToken(raw)
    except TokenError:
        _deny()
    sid, fid, uid = _claims(token, 'refresh')
    if str(uid) != str(user.pk):
        _deny()
    try:
        _store()
        row = UserSession.objects.get(pk=sid, user_id=uid)
        if row.family_id != fid or row.contract_version != VERSION or row.token_family != FAMILY:
            _deny()
    except (UserSession.DoesNotExist, DjangoValidationError, ValueError):
        _deny()
    except DatabaseError:
        raise SessionUnavailable() from None
    revoke(user, session_id=sid, reason='logout')
    return True
