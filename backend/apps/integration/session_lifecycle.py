"""Durable session lifecycle, serialized with the authority-write SQL triggers.

Lock order: singleton security fence, then session. Never lock user/MFA rows
here (the MFA service has its own committed transaction). PostgreSQL READ
COMMITTED reads after the fence observe committed authority changes. Deadlock
or serialization failures deny; callers must reauthenticate after lost replies.
"""
from contextlib import contextmanager
import hashlib
import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from apps.users import two_factor_service as mfa
from apps.users.models import User, UserOrganization
from apps.users.models_2fa import TwoFactorChallenge
from .client_registry import ClientContract
from .models import SSOClient, SSOSecurityFence, SSOSession, SSORevocationOutbox

LIFECYCLE = 'rec-sso-03b-v1'


def deny():
    raise AuthenticationFailed('Session authority rejected.')


@contextmanager
def locked():
    mfa.require_commit_boundary()
    with transaction.atomic(durable=True):
        fence = SSOSecurityFence.objects.select_for_update().get(pk=1)
        if fence.enabled is not True:
            deny()
        yield fence


def next_generation(fence):
    fence.generation += 1
    fence.save(update_fields=['generation'])
    return fence.generation


def authentication_epoch():
    mfa.require_commit_boundary()
    fence = SSOSecurityFence.objects.get(pk=1)
    if fence.enabled is not True:
        deny()
    return fence.authority_epoch


def live_context(client, subject, tenant):
    row = SSOClient.objects.select_related('principal', 'product').get(client_id=client.client_id)
    if ClientContract.from_row(row) != client:
        deny()
    if not row.tenants.filter(pk=tenant, status='active').exists():
        deny()
    user = User.objects.get(pk=subject, is_active=True)
    mfa.validate_user_eligibility(user, timezone.now())
    member = UserOrganization.objects.select_related('organization').get(
        user=user, organization_id=tenant, is_active=True, organization__status='active')
    from .sso_views import _serialize_product_entitlements
    products = [p for p in _serialize_product_entitlements(tenant) if p['code'] == client.product]
    if not any(p.get('access_allowed') is True for p in products):
        deny()
    return row, user, member, products


def check_mfa(user, methods, generation):
    factor = getattr(user, 'two_factor_auth', None)
    if methods not in (['pwd'], ['pwd', 'otp']):
        deny()
    if factor and factor.is_enabled:
        if methods != ['pwd', 'otp'] or str(factor.generation) != generation:
            deny()
    elif methods != ['pwd'] or generation is not None:
        deny()


def issue(user, membership, client, methods, mfa_generation, challenge_digest, expected_epoch, render):
    with locked() as fence:
        if type(expected_epoch) is not int or fence.authority_epoch != expected_epoch:
            deny()
        row, current, member, products = live_context(client, user.pk, membership.organization_id)
        if current.password != user.password or member.role != membership.role:
            deny()
        check_mfa(current, methods, mfa_generation)
        now = timezone.now()
        if 'otp' in methods:
            challenge = TwoFactorChallenge.objects.get(pk=challenge_digest, user=current)
            if (challenge.consumed_at is None or challenge.expires_at <= now
                    or str(challenge.generation) != mfa_generation or challenge.scope != mfa.CONTRACTS['sso'][2]):
                deny()
        elif challenge_digest:
            deny()
        version = next_generation(fence)
        from datetime import timedelta
        session = SSOSession.objects.create(
            user=current, client=row, tenant_id=member.organization_id, product=client.product,
            generation=version, authority_version=version, authenticated_at=now,
            expires_at=now + timedelta(seconds=300), role=member.role,
            authentication_methods=methods, mfa_generation=mfa_generation,
            mfa_challenge_digest=challenge_digest or '')
        # Signing and serialization errors roll back issuance; no token escapes before commit.
        return render(session, current, member, products)


def claims(session):
    return {'lifecycle': LIFECYCLE, 'sid': str(session.id), 'sg': session.generation,
            'av': session.authority_version, 'auth_time': int(session.authenticated_at.timestamp())}


def check_record(session, data, client, *, kind='access'):
    now = timezone.now()
    if (data.get('lifecycle') != LIFECYCLE or session.state != 'active'
            or session.revoked_at is not None or session.revocation_reason
            or str(session.id) != data.get('sid') or str(session.user_id) != data.get('sub')
            or session.client.client_id != client.client_id or session.product != client.product
            or str(session.tenant_id) != data.get('tenant_id')
            or type(data.get('sg')) is not int or data['sg'] != session.generation
            or type(data.get('av')) is not int or data['av'] != session.authority_version
            or data.get('auth_time') != int(session.authenticated_at.timestamp())
            or data.get('exp') != int(session.expires_at.timestamp())
            or not session.authenticated_at <= now < session.expires_at
            or data.get('role') != session.role or data.get('amr') != session.authentication_methods
            or data.get('mfa_generation') != (str(session.mfa_generation) if session.mfa_generation else None)
            or data.get('jti') != str(getattr(session, kind + '_jti'))):
        deny()


def _validated(data, client):
    try:
        sid = uuid.UUID(data['sid'])
    except (KeyError, ValueError, TypeError, AttributeError):
        deny()
    session = SSOSession.objects.select_for_update(of=('self',)).select_related('client').get(pk=sid)
    check_record(session, data, client)
    _, user, member, products = live_context(client, session.user_id, session.tenant_id)
    check_mfa(user, data['amr'], data.get('mfa_generation'))
    if member.role != session.role or data.get('email') != user.email:
        deny()
    return session, user, member, products


def validate(data, client, *, expected_epoch):
    with locked() as fence:
        if fence.authority_epoch != expected_epoch:
            deny()
        return _validated(data, client)


def record_event(session, reason):
    SSORevocationOutbox.objects.get_or_create(session=session, generation=session.generation,
        defaults={'client_id_snapshot': session.client.client_id, 'product': session.product,
                  'tenant_id_snapshot': session.tenant_id, 'reason': reason,
                  'correlation_id': session.correlation_id})


def revoke_record(session, fence, reason):
    if session.state == 'revoked':
        return False
    session.generation = next_generation(fence)
    session.authority_version = session.generation
    session.state = 'revoked'
    session.revoked_at = timezone.now()
    session.revocation_reason = reason
    session.save(update_fields=['generation', 'authority_version', 'state', 'revoked_at', 'revocation_reason'])
    record_event(session, reason)
    return True


def logout(data, client, *, expected_epoch):
    with locked() as fence:
        if fence.authority_epoch != expected_epoch:
            deny()
        session = SSOSession.objects.select_for_update(of=('self',)).select_related('client').get(pk=data['sid'])
        if (session.client.client_id != client.client_id or str(session.user_id) != data['sub']
                or str(session.tenant_id) != data['tenant_id'] or session.product != client.product):
            deny()
        # Old signed generations can revoke their own session, never revive it.
        revoke_record(session, fence, 'logout')


def rotate(data, client, render, *, expected_epoch):
    with locked() as fence:
        if fence.authority_epoch != expected_epoch:
            deny()
        session, user, member, products = _validated(data, client)
        record_event(session, 'rotation')
        session.generation = next_generation(fence)
        session.access_jti = uuid.uuid4()
        session.refresh_jti = uuid.uuid4()
        session.save(update_fields=['generation', 'access_jti', 'refresh_jti'])
        # No central lifetime extension; the prior generation is single-use.
        return render(session, user, member, products)


def revoke_administratively(*, actor, session_id):
    # Callable by an authenticated central admin flow, never an integration-key endpoint.
    with locked() as fence:
        current = User.objects.get(pk=actor.pk, is_active=True, is_superuser=True)
        mfa.validate_user_eligibility(current, timezone.now())
        session = SSOSession.objects.select_for_update(of=('self',)).select_related('client').get(pk=session_id)
        return revoke_record(session, fence, 'administrative')


def revoke_for_user(*, actor, session_id=None):
    """Revoke one owned central session, or all owned central sessions.

    A local AdminApps JTI is never a central SID or a consumer session ID.
    No caller-supplied user, tenant, client or keep-ID can change this scope.
    """
    if not isinstance(actor, User) or not actor.is_authenticated:
        deny()
    with locked() as fence:
        try:
            current = User.objects.get(pk=actor.pk, is_active=True)
        except User.DoesNotExist:
            deny()
        mfa.validate_user_eligibility(current, timezone.now())
        sessions = SSOSession.objects.select_for_update(of=('self',)).select_related('client')
        if session_id is not None:
            try:
                session = sessions.get(pk=session_id, user_id=current.pk)
            except SSOSession.DoesNotExist:
                deny()
            return int(revoke_record(session, fence, 'user_revocation'))
        sessions = sessions.filter(user_id=current.pk, state='active').order_by('id')
        return sum(revoke_record(session, fence, 'user_revocation') for session in sessions)


def challenge_digest(payload):
    return hashlib.sha256(payload['nonce'].encode()).hexdigest()


def revoke_mfa_policy(*, actor):
    """Authorized global policy transition hook; call before activating policy.

Policy settings themselves are outside this service. Disabling access while
changing deployment policy remains part of the activation runbook.
"""
    with locked() as fence:
        current = User.objects.get(pk=actor.pk, is_active=True, is_superuser=True)
        mfa.validate_user_eligibility(current, timezone.now())
        fence.authority_epoch += 1
        fence.save(update_fields=['authority_epoch'])
        sessions = SSOSession.objects.select_for_update(of=('self',)).select_related('client').filter(state='active').order_by('id')
        return sum(revoke_record(session, fence, 'mfa_policy') for session in sessions)


def introspect(data, client, *, expected_epoch):
    # Resolve functional evidence before releasing the same fence used by B.
    # A signed/active authentication proof with denied grants grants no API access.
    from .authorization import resolve
    with locked() as fence:
        if fence.authority_epoch != expected_epoch:
            deny()
        session, user, member, products = _validated(data, client)
        authorization = resolve(session, user, member, products, client)
        return session, user, member, products, authorization
