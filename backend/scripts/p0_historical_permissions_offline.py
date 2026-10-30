"""Verify historical billing boundary under current explicit platform permissions."""
import importlib.util,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
p=Path(__file__).with_name('rec_sso_03d_p0r2_r1_offline.py')
spec=importlib.util.spec_from_file_location('r1',p);r1=importlib.util.module_from_spec(spec);spec.loader.exec_module(r1)
from apps.billing.views import AIUsageDashboardView
from apps.users.models import User
from rest_framework.exceptions import PermissionDenied

class HistoricalPermissionTests(unittest.TestCase):
    def request(self,role='admin',staff=True,active=True,auth=None,headers=None):
        return NS(user=User(role=role,is_staff=staff,is_active=active),auth=auth or {},headers=headers or {},method='GET',authenticators=[])
    def test_org_admin_cannot_read_cross_tenant_usage_even_with_model_permission(self):
        with patch.object(User,'has_perm',return_value=True):
            with self.assertRaises(PermissionDenied):AIUsageDashboardView().check_permissions(self.request(role='org_admin'))
    def test_nonstaff_admin_denied(self):
        with patch.object(User,'has_perm',return_value=True):
            with self.assertRaises(PermissionDenied):AIUsageDashboardView().check_permissions(self.request(staff=False))
    def test_staff_admin_without_exact_permission_denied(self):
        with patch.object(User,'has_perm',return_value=False):
            with self.assertRaises(PermissionDenied):AIUsageDashboardView().check_permissions(self.request())
    def test_explicit_platform_delegate_and_superadmin_allowed(self):
        for role in ('admin','superadmin'):
            with patch.object(User,'has_perm',return_value=True) as permission:
                AIUsageDashboardView().check_permissions(self.request(role=role))
                permission.assert_called_with('integration.view_aiusageprojection')
    def test_service_and_consumer_principals_denied(self):
        for changes in ({'auth':{'token_family':'CENTRAL'}},{'auth':{'product':'ISO_SMART'}},{'headers':{'X-API-Key':'synthetic'}}):
            with patch.object(User,'has_perm',return_value=True):
                with self.assertRaises(PermissionDenied):AIUsageDashboardView().check_permissions(self.request(**changes))
    def test_inactive_platform_actor_denied(self):
        with patch.object(User,'has_perm',return_value=True):
            with self.assertRaises(PermissionDenied):AIUsageDashboardView().check_permissions(self.request(active=False))

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HistoricalPermissionTests))
    # R1 imports the original offline harness and retains its network/database guards.
    summary=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),database_attempts=r1.h.DB.call_count,network_attempts=sum(g.call_count for g in r1.h.NETWORK))
    print(json.dumps(summary));sys.exit(not result.wasSuccessful() or summary['database_attempts'] or summary['network_attempts'])
