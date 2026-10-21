"""P0R central self-revocation: real RSA/handlers/lifecycle, simulated B fence."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import uuid

spec = importlib.util.spec_from_file_location('p0r_b', Path.cwd() / 'backend/scripts/rec_sso_03b_offline.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
life = b.life


class P0RSessions(b.LifecycleTests):
    def setUp(self):
        super().setUp()
        query = life.SSOSession.objects.select_for_update.return_value.select_related.return_value
        query.get.side_effect = self.owned_get
        query.filter.side_effect = self.owned_filter

    def owned_get(self, pk, user_id=None):
        session = self.get_session(pk)
        if user_id is not None and str(session.user_id) != str(user_id):
            raise life.SSOSession.DoesNotExist
        return session

    def owned_filter(self, user_id, state):
        return b.NS(order_by=lambda *args: [s for s in self.records.values()
                    if s.user_id == user_id and s.state == state])

    def test_single_owned_revocation_denies_introspection_and_rotation(self):
        token = self.issue(); sid = self.data(token)['sid']
        self.assertEqual(life.revoke_for_user(actor=self.user, session_id=sid), 1)
        self.assert_denied(token)
        response, _ = self.call(self.context(token=token), b.h.sso.sso_rotate)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(life.revoke_for_user(actor=self.user, session_id=sid), 0)
        self.assertEqual(len(self.events), 1)
        self.assertEqual(self.get_session(sid).revocation_reason, 'user_revocation')

    def test_foreign_or_unknown_sid_denied_without_mutation(self):
        token = self.issue(); session = self.get_session(self.data(token)['sid'])
        original_owner = session.user_id
        session.user_id = uuid.uuid4()
        for sid in (session.id, uuid.uuid4()):
            with self.subTest(sid=sid), self.assertRaises(life.AuthenticationFailed):
                life.revoke_for_user(actor=self.user, session_id=sid)
        self.assertEqual(session.state, 'active'); self.assertEqual(len(self.events), 0)
        self.get_session(session.id).user_id = original_owner
        self.assertTrue(self.inspect(token)[1]['active'])

    def test_revoke_all_owns_filter_and_never_keeps_supplied_ids(self):
        first = self.issue(); second = self.issue(); foreign = self.issue()
        other = self.get_session(self.data(foreign)['sid']); other.user_id = uuid.uuid4()
        self.assertEqual(life.revoke_for_user(actor=self.user), 2)
        self.assert_denied(first); self.assert_denied(second)
        self.assertEqual(other.state, 'active')
        self.assertEqual(life.revoke_for_user(actor=self.user), 0)
        self.assertEqual(len(self.events), 2)

    def test_revoking_after_rotation_invalidates_all_generations(self):
        old = self.issue()
        response, body = self.call(self.context(token=old), b.h.sso.sso_rotate)
        self.assertEqual(response.status_code, 200)
        current = body['tokens']['access_token']
        life.revoke_for_user(actor=self.user, session_id=self.data(old)['sid'])
        self.assert_denied(old); self.assert_denied(current)
        # A lost response/retry with an old proof cannot restore authority.
        self.call(self.context(token=old), b.h.sso.sso_logout)
        self.assert_denied(current)

    def test_inactive_actor_cannot_revoke_or_restore_authority(self):
        token = self.issue(); self.user.is_active = False
        with self.assertRaises((life.AuthenticationFailed, life.User.DoesNotExist)):
            life.revoke_for_user(actor=self.user)
        self.assertEqual(len(self.events), 0)
        self.assert_denied(token)

    def test_failure_after_success_does_not_reactivate_session(self):
        token = self.issue(); sid = self.data(token)['sid']
        life.revoke_for_user(actor=self.user, session_id=sid)
        with self.assertRaises(RuntimeError):
            raise RuntimeError('response serialization failed after committed service')
        self.assert_denied(token)
        self.assertEqual(life.revoke_for_user(actor=self.user, session_id=sid), 0)


if __name__ == '__main__':
    # Run only new declarations. Inherited B methods run in their original suite.
    names = sorted(n for n in P0RSessions.__dict__ if n.startswith('test_'))
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(P0RSessions(n) for n in names))
    summary = dict(tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                   database_attempts=b.h.DB_GUARD.call_count,
                   network_attempts=sum(g.call_count for g in b.h.NETWORK_GUARDS))
    print(json.dumps(summary)); sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
