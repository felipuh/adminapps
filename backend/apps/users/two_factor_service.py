"""REC-2FA-03B: PostgreSQL is the only authority for second-factor consumption.

Lock order: user -> configuration -> challenge. Public mutations own their
transaction and reject ambient transactions (including manual autocommit off).
Rejections are raised AFTER commit so failed-attempt counters survive DRF errors.
A lost response or issuer failure never restores a consumed challenge/factor.
Legacy signed challenges without a 256-bit nonce/version are rejected outright.
"""
from datetime import timedelta
from functools import wraps
import hashlib
import ipaddress
import json
import secrets
import uuid

from django.core import signing
from django.db import DatabaseError, connection, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from .models import User, UserOrganization
from .models_2fa import TwoFactorAuth, TwoFactorAuthLog, TwoFactorChallenge

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
VERSION = 1
CONTRACTS = {
    'login': ('adminapps.2fa.login', '2fa_verification', 'totp_verification_only'),
    'sso': ('smart3ai.sso.2fa', 'sso_2fa_verification', 'sso_verification_only'),
}


class PersistenceUnavailable(APIException):
    status_code = 503
    default_detail = 'Unable to complete 2FA authentication'
    default_code = 'two_factor_unavailable'


class ChallengeRejected(PermissionDenied):
    default_code = 'invalid_or_expired_challenge'


def require_commit_boundary():
    if connection.vendor != 'postgresql' or connection.in_atomic_block or not connection.get_autocommit():
        raise PersistenceUnavailable()


def sanitize_database_errors(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except DatabaseError:
            raise PersistenceUnavailable() from None
    return wrapped


def persistent_operation(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            require_commit_boundary()
            return fn(*args, **kwargs)
        except DatabaseError:
            raise PersistenceUnavailable() from None
    return wrapped


def validate_user_eligibility(user, now):
    expiry = user.get_temporary_password_expiry()
    if not user.is_active or user.is_locked or (expiry and now >= expiry):
        raise PermissionDenied('Invalid 2FA verification user')


def _lock(user_id, *, create=False):
    try:
        user = User.objects.select_for_update().get(pk=user_id)
    except (User.DoesNotExist, ValueError, ValidationError):
        raise PermissionDenied('Invalid 2FA verification user') from None
    validate_user_eligibility(user, timezone.now())
    if create:
        TwoFactorAuth.objects.get_or_create(user=user)
    try:
        config = TwoFactorAuth.objects.select_for_update().get(user=user)
    except TwoFactorAuth.DoesNotExist:
        raise PermissionDenied('2FA is not configured') from None
    return user, config


def _digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _context(payload):
    return _digest(json.dumps(payload, sort_keys=True, separators=(',', ':')))


def decode_challenge(token, channel='login'):
    salt, purpose, scope = CONTRACTS[channel]
    try:
        payload = signing.loads(token, salt=salt, max_age=300)
        nonce = payload['nonce']
        if (payload['version'] != VERSION or payload['purpose'] != purpose
                or payload['scope'] != scope or not isinstance(nonce, str)
                or len(nonce) != 64 or len(bytes.fromhex(nonce)) != 32):
            raise ValueError
        uuid.UUID(payload['user_id'])
        uuid.UUID(payload['generation'])
        return payload
    except (signing.BadSignature, ValueError, TypeError, KeyError, AttributeError):
        raise ChallengeRejected('Invalid or expired 2FA challenge; start a new login') from None


@persistent_operation
def issue_challenge(user, channel='login', *, context=None):
    salt, purpose, scope = CONTRACTS[channel]
    with transaction.atomic(durable=True):
        locked_user, config = _lock(user.pk)
        if not config.is_enabled:
            raise PermissionDenied('2FA is not enabled')
        now = timezone.now()
        payload = dict(context or {})
        payload.update(user_id=str(locked_user.pk), email=locked_user.email,
                       purpose=purpose, scope=scope, nonce=secrets.token_hex(32),
                       version=VERSION, generation=str(config.generation))
        TwoFactorChallenge.objects.create(
            nonce_digest=_digest(payload['nonce']), user=locked_user,
            version=VERSION, purpose=purpose, scope=scope,
            generation=config.generation, context_digest=_context(payload),
            issued_at=now, expires_at=now + timedelta(seconds=300),
        )
        token = signing.dumps(payload, salt=salt)
    return token


def _attempts(config, now):
    if config.attempts_expires_at is None or now >= config.attempts_expires_at:
        config.failed_attempts = 0
        config.attempts_expires_at = None
    return config.failed_attempts


def _factor(config, token, now, *, allow_backup=True, backup_only=False):
    token = str(token or '')
    if not backup_only and len(token) == 6 and token.isascii() and token.isdigit():
        totp = config.get_totp()
        if totp:
            counter = totp.timecode(now)
            matches = [c for c in range(counter - 1, counter + 2)
                       if c >= 0 and secrets.compare_digest(totp.generate_otp(c), token)]
            if matches:
                matched = max(matches)
                if config.last_totp_counter is None or matched > config.last_totp_counter:
                    config.last_totp_counter = matched
                    return 'token_verified'
    if allow_backup:
        # Mark every matching index: duplicate backup values cannot be reused.
        matches = [i for i, code in enumerate(config.get_backup_codes())
                   if secrets.compare_digest(code.encode(), token.upper().encode())]
        used = set(config.backup_codes_used or [])
        if matches and not used.intersection(matches):
            config.backup_codes_used = sorted(used.union(matches))
            return 'backup_code_used'
    return None


def _audit(user, event, request=None):
    # Keep the remote IP, but omit arbitrary headers that may contain secrets.
    remote_ip = None
    if request is not None:
        try:
            remote_ip = str(ipaddress.ip_address(request.META.get('REMOTE_ADDR', '')))
        except ValueError:
            pass
    TwoFactorAuthLog.objects.create(
        user=user, event_type=event,
        status='failure' if event == 'token_failed' else 'success',
        details={}, ip_address=remote_ip,
    )


def _verify_locked(user, config, token, now, request=None, **options):
    if _attempts(config, now) >= MAX_ATTEMPTS:
        return None, PermissionDenied('Too many failed attempts. Please try again in 15 minutes.')
    event = _factor(config, token, now, **options)
    if event:
        config.failed_attempts = 0
        config.attempts_expires_at = None
    else:
        config.failed_attempts += 1
        # Preserve the existing sliding TTL: 15 minutes from last failed attempt.
        config.attempts_expires_at = now + timedelta(minutes=LOCKOUT_MINUTES)
    config.save(update_fields=['last_totp_counter', 'backup_codes_used',
                              'failed_attempts', 'attempts_expires_at', 'updated_at'])
    _audit(user, event or 'token_failed', request)
    if event:
        return event, None
    remaining = MAX_ATTEMPTS - config.failed_attempts
    detail = {'token': 'Invalid OTP token or backup code', 'remaining_attempts': remaining}
    if 0 < remaining <= 2:
        detail['warning'] = f'Only {remaining} attempt(s) remaining before lockout'
    return None, ValidationError(detail)


@persistent_operation
def consume_challenge(token, factor, channel='login', *, request=None):
    payload = decode_challenge(token, channel)
    rejection = None
    with transaction.atomic(durable=True):
        user, config = _lock(payload['user_id'])
        try:
            challenge = TwoFactorChallenge.objects.select_for_update().get(
                pk=_digest(payload['nonce']))
        except TwoFactorChallenge.DoesNotExist:
            raise ChallengeRejected('Invalid or expired 2FA challenge') from None
        # This clock MUST be read after every blocking lock acquisition.
        now = timezone.now()
        validate_user_eligibility(user, now)
        if (not config.is_enabled or challenge.consumed_at is not None
                or not challenge.issued_at <= now < challenge.expires_at
                or challenge.user_id != user.pk
                or challenge.generation != config.generation
                or str(config.generation) != payload['generation']
                or challenge.version != VERSION
                or challenge.purpose != payload['purpose']
                or challenge.scope != payload['scope']
                or challenge.context_digest != _context(payload)):
            raise ChallengeRejected('Invalid or expired 2FA challenge')
        if channel == 'sso' and not UserOrganization.objects.filter(
                user=user, organization_id=payload.get('organization_id'),
                is_active=True, organization__status='active').exists():
            raise PermissionDenied('Invalid membership')
        event, rejection = _verify_locked(user, config, factor, now, request)
        if event:
            challenge.consumed_at = now
            challenge.save(update_fields=['consumed_at'])
    if rejection:
        raise rejection
    return user, event


@persistent_operation
def consume_factor(user_id, token, *, allow_backup=True, backup_only=False):
    """Compatibility for model callers; no JWT authorization without a challenge."""
    with transaction.atomic(durable=True):
        user, config = _lock(user_id)
        if not config.is_enabled:
            return False
        event, rejection = _verify_locked(user, config, token, timezone.now(),
                                          allow_backup=allow_backup, backup_only=backup_only)
    return event is not None


@persistent_operation
def initiate_configuration(user_id):
    with transaction.atomic(durable=True):
        user, config = _lock(user_id, create=True)
        if config.is_enabled:
            raise ValidationError('2FA is already enabled for this user')
        config.secret = config.generate_secret()
        config.backup_codes = ''
        config._backup_codes_encrypted = ''
        config.backup_codes_used = []
        config.save()
        TwoFactorAuthLog.objects.create(user=user, event_type='setup_initiated', status='success')
        secret = config.secret
    return secret


@persistent_operation
def verify_configuration(user_id, token):
    with transaction.atomic(durable=True):
        user, config = _lock(user_id)
        if config.is_enabled:
            raise ValidationError('2FA is already enabled for this user')
        event, rejection = _verify_locked(user, config, token, timezone.now(), allow_backup=False)
        if event:
            codes = config.generate_backup_codes()
            config.backup_codes_used = []
            config.is_enabled = True
            config.verified_at = timezone.now()
            config.save()
            TwoFactorAuthLog.objects.create(user=user, event_type='setup_verified', status='success',
                                           details={'backup_codes_count': len(codes)})
    if rejection:
        raise rejection
    return config, codes


@persistent_operation
def disable_configuration(user_id, *, password=None, reason='User disabled 2FA'):
    with transaction.atomic(durable=True):
        user, config = _lock(user_id)
        if password is not None and not user.check_password(password):
            raise PermissionDenied('Invalid password')
        config.is_enabled = False
        config.generation = uuid.uuid4()
        config.last_totp_counter = None
        config.disabled_at = timezone.now()
        config.disabled_reason = reason
        config.save()
        TwoFactorAuthLog.objects.create(user=user, event_type='disabled', status='success')


@persistent_operation
def rate_state(user, operation='read'):
    with transaction.atomic(durable=True):
        _, config = _lock(user.pk)
        now = timezone.now()
        count = _attempts(config, now)
        if operation == 'increment':
            config.failed_attempts = min(MAX_ATTEMPTS, count + 1)
            config.attempts_expires_at = now + timedelta(minutes=LOCKOUT_MINUTES)
        elif operation == 'reset':
            config.failed_attempts, config.attempts_expires_at = 0, None
        config.save(update_fields=['failed_attempts', 'attempts_expires_at', 'updated_at'])
    return config.failed_attempts
