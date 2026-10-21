import importlib.util, runpy, unittest, sys, json
from pathlib import Path
# Bootstrap the immutable pre-change harness, then load only the new probes.
runpy.run_path('backend/scripts/rec_sso_03d_api_p0_offline.py', run_name='offline_setup')
source=Path('/home/felipe/proyectos/adminapps/backend/apps/api/test_p0r.py')
spec=importlib.util.spec_from_file_location('p0r_reproduction',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
# Client loader must inspect the baseline consumers as well.
module.__file__=str(Path.cwd()/'backend/apps/api/test_p0r.py')
names=[('ServiceGrantTests','test_unknown_or_incomplete_grant_denies_all_operations'),
 ('ServiceGrantTests','test_modules_exclude_foreign_products_and_unmapped_owner_exemptions'),
 ('ServiceGrantTests','test_revoked_timestamp_unsaved_or_wrong_format_principal_denied'),
 ('InvitationLifecycleTests','test_authority_removed_after_validation_is_denied_at_consumption'),
 ('SessionAPITests','test_logout_real_signed_refresh_idempotent_and_foreign_denied'),
 ('ConsumerGrantCompatibilityTests','test_both_adapters_reject_revocation_grant_removal_and_product_tenant_escape'),
 ('ConsumerGrantCompatibilityTests','test_both_module_helpers_reject_authorization_denial_even_with_module_payload')]
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(getattr(module,cls)(name) for cls,name in names))
print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'expected':'baseline defects; not final suite'}))
sys.exit(not result.wasSuccessful())
