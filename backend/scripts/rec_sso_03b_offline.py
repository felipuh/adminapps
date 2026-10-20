"""Decision B offline logic. Simulated ORM/rollback/locks are NOT PostgreSQL evidence."""
import copy
from contextlib import contextmanager
from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import uuid

spec = importlib.util.spec_from_file_location('ch', Path.cwd() / 'backend/scripts/rec_sso_03b_ch_offline.py')
ch = importlib.util.module_from_spec(spec); spec.loader.exec_module(ch)
h = ch.h
from apps.integration import session_lifecycle as life


class LifecycleTests(ch.CHTests):
    def setUp(self):
        super().setUp()
        self.row.pk = self.row.id = 1
        self.records = {}; self.events = {}
        self.fence = NS(generation=0, authority_epoch=0, enabled=True, save=lambda **kw: None)
        self.mutex = threading.RLock()
        self.mock(life, 'locked', new=self.atomic)
        self.mock(life.SSOSecurityFence.objects, 'get', return_value=self.fence)
        self.mock(life.SSOSession.objects, 'create', side_effect=self.create)
        q = self.mock(life.SSOSession.objects, 'select_for_update')
        q.return_value.select_related.return_value.get.side_effect = self.get_session
        self.mock(life.SSORevocationOutbox.objects, 'get_or_create', side_effect=self.event)
        self.mock(life.UserOrganization.objects, 'select_related').return_value.get.side_effect = self.member_get
        self.users.side_effect = lambda **kw: self.get_user(**{('id' if k == 'pk' else k): v for k, v in kw.items()})
        self.mock(life.TwoFactorChallenge.objects, 'get', return_value=NS(consumed_at=h.timezone.now(),
            expires_at=h.timezone.now() + timedelta(seconds=300), generation=ch.GEN, scope=life.mfa.CONTRACTS['sso'][2]))

    @contextmanager
    def atomic(self):
        with self.mutex:
            records = {k: copy.copy(v) for k, v in self.records.items()}
            events = dict(self.events); generation = self.fence.generation
            try:
                yield self.fence
            except Exception:
                self.records = records; self.events = events; self.fence.generation = generation
                raise

    def create(self, **kw):
        row = NS(id=uuid.uuid4(), access_jti=uuid.uuid4(), refresh_jti=uuid.uuid4(),
                 correlation_id=uuid.uuid4(), state='active', revoked_at=None, revocation_reason='',
                 save=lambda **kw: None, **kw)
        row.user_id = row.user.pk
        self.records[str(row.id)] = row
        return row

    def event(self, session, generation, defaults):
        key = (str(session.id), generation)
        created = key not in self.events
        self.events.setdefault(key, dict(defaults))
        return self.events[key], created

    def get_session(self, pk):
        if str(pk) not in self.records: raise life.SSOSession.DoesNotExist()
        return self.records[str(pk)]

    def member_get(self, **kw):
        member = self.get_members(**kw).first()
        if not member: raise life.UserOrganization.DoesNotExist()
        return member

    def issue(self):
        factor = getattr(self.user, 'two_factor_auth', None); enabled = bool(factor and factor.is_enabled)
        return h.sso._build_token_pair(self.user, self.member, [self.member], audience=[self.row.audience],
            client_id=self.row.client_id, client=ch.registry.ClientContract.from_row(self.row),
            authentication_methods=['pwd', 'otp'] if enabled else ['pwd'],
            mfa_generation=str(factor.generation) if enabled else None,
            mfa_challenge_digest='a' * 64 if enabled else None,
            expected_epoch=self.fence.authority_epoch)['access_token']

    def data(self, token):
        return h.jwt.decode(token, ch.PUBLIC, algorithms=['RS256'], audience=self.row.audience)

    def assert_denied(self, proof):
        response, body = self.inspect(proof)
        self.assertNotEqual(body.get('active'), True)
        self.assertIn(response.status_code, (200, 401, 403, 503))

    def test_unknown_disabled_revoked_clients(self):
        token = self.issue()
        self.rows.return_value.get.side_effect = life.SSOClient.DoesNotExist
        self.assert_denied(token)
        self.rows.return_value.get.side_effect = None
        for obj, field, value in [(self.row, 'enabled', False), (self.principal, 'is_active', False),
                                  (self.principal, 'status', 'revoked'), (self.principal, 'status', 'rotated')]:
            with patch.object(obj, field, value): self.assert_denied(token)

    def test_tenant_user_membership_revocation(self):
        token = self.issue()
        for obj, field, value in [(self.org, 'status', 'disabled'), (self.user, 'is_active', False),
                                  (self.member, 'is_active', False), (self.member, 'role', 'admin')]:
            with patch.object(obj, field, value): self.assert_denied(token)
        self.tenant_allowed = False; self.assert_denied(token)

    def test_mfa_live_generation(self):
        token = self.issue()
        self.user._state.fields_cache['two_factor_auth'] = NS(is_enabled=True, generation=ch.GEN)
        self.assert_denied(token)
        token = self.issue(); self.assertTrue(self.inspect(token)[1]['active'])
        self.user.two_factor_auth.generation = uuid.uuid4(); self.assert_denied(token)

    def test_login_response_does_not_disclose_other_tenants(self):
        with patch.object(h.sso, '_auth_user', return_value=self.user), patch.object(self.user, 'save'):
            response, body = self.call(self.context(email=self.user.email, password='synthetic'), h.sso.sso_login)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m['id'] for m in body['organizations']], [str(h.ORG)])
        data = self.data(body['tokens']['access_token'])
        self.assertNotIn('memberships', data)
        self.assertNotIn('product_entitlements', data)
        self.assertEqual(data['product'], 'ISO_SMART')

    def test_challenge_binding_before_irreversible_consume(self):
        challenge = dict(self.context(), user_id=str(h.USER), organization_id=str(h.ORG),
                         principal_id=11, generation=ch.GEN, authority_epoch=0, nonce='ab' * 32)
        for key, value in [('principal_id', 22), ('product', 'MEDSUPPLIER'), ('client_id', 'other'),
                           ('contract_version', 'decision-a-v1'), ('audience', ['other']), ('authority_epoch', 1)]:
            with patch.object(h.sso.two_factor, 'decode_challenge', return_value=dict(challenge, **{key: value})), \
                 patch.object(h.sso.two_factor, 'consume_challenge') as consume:
                self.assertEqual(self.call(self.context(challenge_token='synthetic', otp_code='123456'), h.sso.sso_login_verify_2fa)[0].status_code, 403)
                consume.assert_not_called()

    def test_verify_valid_and_postconsume_failure_no_restoration(self):
        challenge = dict(self.context(), user_id=str(h.USER), organization_id=str(h.ORG), principal_id=11,
                         generation=ch.GEN, authority_epoch=0, nonce='ab' * 32)
        self.user._state.fields_cache['two_factor_auth'] = NS(is_enabled=True, generation=ch.GEN)
        with patch.object(h.sso.two_factor, 'decode_challenge', return_value=challenge), \
             patch.object(h.sso.two_factor, 'consume_challenge', return_value=(self.user, 'totp')) as consume, patch.object(self.user, 'save'):
            response, body = self.call(self.context(challenge_token='synthetic', otp_code='123456'), h.sso.sso_login_verify_2fa)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.data(body['tokens']['access_token'])['amr'], ['pwd', 'otp'])
            with patch.object(h.sso, '_render_session', side_effect=RuntimeError('private failure')):
                self.assertEqual(self.call(self.context(challenge_token='synthetic', otp_code='123456'), h.sso.sso_login_verify_2fa)[0].status_code, 500)
            self.assertEqual(len(self.records), 1); self.assertEqual(consume.call_count, 2)

    def test_logout_idempotent_and_old_signed_proof_denied(self):
        token = self.issue()
        for _ in range(2): self.assertTrue(self.call(self.context(token=token), h.sso.sso_logout)[1]['revoked'])
        self.assertEqual(len(self.events), 1); self.assert_denied(token)
        self.assertEqual(self.get_session(self.data(token)['sid']).revocation_reason, 'logout')

    def test_generation_authority_session_and_time_binding(self):
        token = self.issue(); original = self.data(token)
        for key, value in [('sid', str(uuid.uuid4())), ('sg', 0), ('sg', True), ('av', 0),
                           ('auth_time', 1), ('lifecycle', None), ('exp', original['exp'] + 1), ('jti', str(uuid.uuid4()))]:
            changed = dict(original, **{key: value})
            self.assert_denied(h.jwt.encode(changed, ch.PRIVATE, algorithm='RS256', headers={'kid': 'synthetic-central'}))

    def test_signed_legacy_ch_proof_without_session_denied(self):
        data = self.data(self.issue())
        for k in ('sid', 'sg', 'av', 'auth_time', 'lifecycle'): data.pop(k)
        self.assert_denied(h.jwt.encode(data, ch.PRIVATE, algorithm='RS256', headers={'kid': 'synthetic-central'}))

    def test_rotation_single_use_and_no_extension(self):
        token = self.issue(); data = self.data(token)
        response, result = self.call(self.context(token=token), h.sso.sso_rotate)
        self.assertEqual(response.status_code, 200)
        new = result['tokens']['access_token']; current = self.data(new)
        self.assertGreater(current['sg'], data['sg'])
        for k in ('sid', 'av', 'auth_time', 'exp'): self.assertEqual(current[k], data[k])
        self.assertTrue(self.inspect(new)[1]['active']); self.assert_denied(token)
        self.assertNotEqual(self.call(self.context(token=token), h.sso.sso_rotate)[0].status_code, 200)
        self.assertEqual(len(self.events), 1)

    def test_rotation_after_logout_never_restores(self):
        token = self.issue(); self.call(self.context(token=token), h.sso.sso_logout)
        self.assertNotEqual(self.call(self.context(token=token), h.sso.sso_rotate)[0].status_code, 200)
        self.assert_denied(token)

    def test_rotation_signing_error_rolls_back_logic(self):
        token = self.issue(); before = self.fence.generation
        with patch.object(h.sso, '_render_session', side_effect=RuntimeError('private signing error')):
            response, body = self.call(self.context(token=token), h.sso.sso_rotate)
        self.assertEqual(response.status_code, 503); self.assertNotIn('private', json.dumps(body))
        self.assertEqual(before, self.fence.generation); self.assertFalse(self.events)
        self.assertTrue(self.inspect(token)[1]['active'])

    def test_serialized_concurrent_rotation_logic(self):
        from concurrent.futures import ThreadPoolExecutor
        token = self.issue()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.call(self.context(token=token), h.sso.sso_rotate)[0].status_code, range(2)))
        self.assertEqual(results.count(200), 1); self.assertEqual(len(self.events), 1)

    def test_aba_revocation_cannot_be_undone_by_role_restore(self):
        token = self.issue(); session = self.get_session(self.data(token)['sid'])
        self.member.role = 'admin'
        with self.atomic() as fence: life.revoke_record(session, fence, 'authority_membership')
        self.member.role = 'viewer'; self.assert_denied(token)
        self.assertGreater(self.data(self.issue())['sg'], session.generation)

    def test_authentication_authority_change_fails_before_issue(self):
        self.fence.authority_epoch = 1
        with self.assertRaises(h.APIException):
            h.sso._build_token_pair(self.user, self.member, [self.member], audience=[self.row.audience],
                client_id=self.row.client_id, client=ch.registry.ClientContract.from_row(self.row),
                authentication_methods=['pwd'], expected_epoch=0)
        self.assertFalse(self.records)

    def test_unreadable_session_fails_closed_sanitized(self):
        token = self.issue()
        with patch.object(life, '_validated', side_effect=h.DatabaseError('sensitive-row')):
            response, body = self.inspect(token)
        self.assertEqual(response.status_code, 503); self.assertNotIn('sensitive', json.dumps(body))

    def test_expired_record_rejected_even_signed_token(self):
        token = self.issue(); self.get_session(self.data(token)['sid']).expires_at = h.timezone.now() - timedelta(seconds=1)
        self.assert_denied(token)

    def test_product_revocation_reloaded(self):
        token = self.issue(); self.products.return_value = [{'code': 'ISO_SMART', 'access_allowed': False}]
        self.assert_denied(token)

    def test_outbox_contains_no_credentials_and_duplicate_is_idempotent(self):
        token = self.issue(); self.call(self.context(token=token), h.sso.sso_logout)
        life.record_event(self.get_session(self.data(token)['sid']), 'logout'); self.assertEqual(len(self.events), 1)
        for secret in (token, self.user.email, 'central_proof', 'password'): self.assertNotIn(secret, str(self.events))

    def test_outbox_delivery_retry_duplicate_and_late_events(self):
        from apps.integration import session_events as events
        from contextlib import nullcontext
        event = NS(id=uuid.uuid4(), session_id=uuid.uuid4(), generation=7, client_id_snapshot='iso-client',
                   product='ISO_SMART', tenant_id_snapshot=h.ORG, reason='logout', correlation_id=uuid.uuid4(),
                   attempts=0, delivered_at=None, next_attempt_at=None, save=lambda **kw: None)
        payload = events.envelope(event)
        scope = dict(client_id='iso-client', product='ISO_SMART', tenant_id=h.ORG, session_id=event.session_id)
        self.assertEqual(events.invalidation_watermark(9, payload, **scope), 9)
        self.assertEqual(events.invalidation_watermark(7, payload, **scope), 7)
        with self.assertRaises(ValueError): events.invalidation_watermark(0, dict(payload, product='MEDSUPPLIER'), **scope)
        with patch.object(events.transaction, 'atomic', return_value=nullcontext()), \
             patch.object(events.SSORevocationOutbox.objects, 'select_for_update') as query:
            query.return_value.get.return_value = event
            self.assertFalse(events.deliver_one(event.id, lambda payload: {}))
            self.assertEqual(event.attempts, 1)
            self.assertIsNotNone(event.next_attempt_at)
            event.next_attempt_at = None
            self.assertTrue(events.deliver_one(event.id, lambda payload: {'event_id': payload['event_id']}))
            self.assertFalse(events.deliver_one(event.id, lambda payload: self.fail('duplicate delivery')))
            self.assertEqual(event.attempts, 2)

    def test_postgres_boundary_and_disabled_activation_fail_closed(self):
        with patch.object(life.mfa, 'require_commit_boundary', side_effect=h.APIException('Unavailable')):
            with self.assertRaises(h.APIException): life.authentication_epoch()
        self.fence.enabled = False
        with self.assertRaises(h.APIException): life.authentication_epoch()

    def test_admin_revocation_requires_live_superuser(self):
        token = self.issue(); session = self.get_session(self.data(token)['sid'])
        self.user.is_superuser = False
        with self.assertRaises(life.User.DoesNotExist): life.revoke_administratively(actor=self.user, session_id=session.id)
        self.assertTrue(self.inspect(token)[1]['active'])
        self.user.is_superuser = True
        self.assertTrue(life.revoke_administratively(actor=self.user, session_id=session.id))
        self.assert_denied(token)

    def test_logout_and_rotation_race_has_no_resurrection(self):
        from concurrent.futures import ThreadPoolExecutor
        token = self.issue()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda view: self.call(self.context(token=token), view), [h.sso.sso_rotate, h.sso.sso_logout]))
        self.assertEqual(results[1][0].status_code, 200)
        self.assert_denied(token)
        if results[0][0].status_code == 200: self.assert_denied(results[0][1]['tokens']['access_token'])

    def test_deleted_identity_and_membership_denied(self):
        token = self.issue()
        self.deleted_user = True; self.assert_denied(token)
        self.deleted_user = False; self.deleted_member = True; self.assert_denied(token)

    def test_locked_and_expired_temporary_password_denied(self):
        token = self.issue()
        self.user.locked_until = h.timezone.now() + timedelta(minutes=1); self.assert_denied(token)
        self.user.locked_until = None
        self.user.mark_temporary_password(h.timezone.now() - timedelta(days=30)); self.assert_denied(token)

    def test_login_mfa_challenge_mints_no_session(self):
        self.user._state.fields_cache['two_factor_auth'] = NS(is_enabled=True, generation=ch.GEN)
        with patch.object(h.sso, '_auth_user', return_value=self.user), \
             patch.object(h.sso.two_factor, 'issue_challenge', return_value='synthetic-challenge'):
            response, body = self.call(self.context(email=self.user.email, password='synthetic'), h.sso.sso_login)
        self.assertEqual(response.status_code, 200); self.assertTrue(body['requires_2fa'])
        self.assertNotIn('tokens', body); self.assertFalse(self.records)

    def test_mfa_disabled_and_missing_configuration_denied(self):
        self.user._state.fields_cache['two_factor_auth'] = NS(is_enabled=True, generation=ch.GEN)
        token = self.issue()
        self.user.two_factor_auth.is_enabled = False; self.assert_denied(token)
        self.user._state.fields_cache['two_factor_auth'] = None; self.assert_denied(token)

    def test_credential_change_between_resolution_and_use_denied(self):
        token = self.issue(); data = self.data(token)
        self.fence.authority_epoch += 1
        client = ch.registry.ClientContract.from_row(self.row)
        for fn in (lambda: life.validate(data, client, expected_epoch=0),
                   lambda: life.rotate(data, client, lambda *args: self.fail('mint'), expected_epoch=0),
                   lambda: life.logout(data, client, expected_epoch=0)):
            with self.assertRaises(h.APIException): fn()

    def test_mfa_policy_change_revokes_all_and_invalidates_pending_auth(self):
        token = self.issue(); self.user.is_superuser = True
        query = life.SSOSession.objects.select_for_update.return_value.select_related.return_value
        query.filter.return_value.order_by.return_value = list(self.records.values())
        self.assertEqual(life.revoke_mfa_policy(actor=self.user), 1)
        self.assertEqual(self.fence.authority_epoch, 1); self.assert_denied(token)

    def test_session_model_security_constraints_and_global_scope(self):
        constraints = {x.name for x in life.SSOSession._meta.constraints}
        self.assertTrue({'sso_one_session_per_mfa', 'sso_revocation_state', 'sso_positive_versions', 'sso_positive_lifetime'} <= constraints)
        for name in ('user', 'client', 'tenant'):
            self.assertEqual(life.SSOSession._meta.get_field(name).remote_field.on_delete.__name__, 'PROTECT')
        fields = {x.name for x in life.SSOSession._meta.fields}
        self.assertFalse({'token', 'password', 'secret', 'central_proof'} & fields)

    def test_sql_fence_watches_bulk_authority_and_no_telemetry(self):
        import importlib
        migration = importlib.import_module('apps.integration.migrations.0010_sso_authority_fence')
        watches = {t: fields for t, _, fields in migration.WATCHES}
        from django.apps import apps
        tables = {m._meta.db_table: {f.column for f in m._meta.fields} for m in apps.get_models(include_auto_created=True)}
        for table, _, fields in migration.WATCHES:
            self.assertIn(table, tables)
            if fields != '*': self.assertTrue(set(fields.split(',')) <= tables[table], table)
        self.assertIn('role', watches['user_organizations']); self.assertIn('generation', watches['two_factor_auth'])
        self.assertNotIn('last_used_at', watches['integration_api_keys']); self.assertNotIn('last_totp_counter', watches['two_factor_auth'])
        self.assertIn('FOR UPDATE OF x', migration.FORWARD)
        self.assertIn('ON CONFLICT (session_id, generation)', migration.FORWARD)
        self.assertIn("OLD.state = 'revoked'", migration.FORWARD)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(LifecycleTests))
    summary = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'database_attempts': h.DB_GUARD.call_count, 'network_attempts': sum(x.call_count for x in h.NETWORK_GUARDS),
        'scope': 'offline simulated ORM/locking/rollback, NOT PostgreSQL concurrency or HTTP E2E'}
    print(json.dumps(summary))
    sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
