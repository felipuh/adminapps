"""Historical pure-function reproductions from reviewed historical fixtures; no Django/settings/.env imports.
These tests CONFIRM risk conditions; passing is not a safety certification.
"""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

FIXTURES = Path(__file__).with_name("fixtures")


def extract(path, names, settings):
    source=path.read_text()
    tree=ast.parse(source)
    nodes=[n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in names]
    if len(nodes)!=len(names):
        raise AssertionError('Source contract changed; review extraction')
    namespace={'settings':settings}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
    return namespace


class SourceRiskTests(unittest.TestCase):
    def test_iso_recovery_trusts_spoofed_forwarded_local_ip_when_enabled(self):
        settings=NS(ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS=True,LOCAL_AUTH_BYPASS_HOSTS=set())
        f=extract(FIXTURES/'iso_recovery.py.txt',
                  {'_request_ip_address','_local_debug_recovery_allowed'},settings)
        request=NS(META={'REMOTE_ADDR':'192.0.2.1','HTTP_X_FORWARDED_FOR':'127.0.0.1'},
                   get_host=lambda:'untrusted.example.invalid')
        self.assertTrue(f['_local_debug_recovery_allowed'](request))
        settings.ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS=False
        self.assertFalse(f['_local_debug_recovery_allowed'](request))

    def test_consumer_fallback_guard_excludes_prod_but_not_staging(self):
        for repo in ('isosmart','ISO_Smart_MedSupplier'):
            settings=NS(IS_PRODUCTION=False,ENVIRONMENT='staging',ALLOW_LOCAL_AUTH_FALLBACK=True,
                        ADMIN_APPS_INTEGRATION={'ALLOW_LOCAL_FALLBACK':True})
            f=extract(FIXTURES/('iso_fallback.py.txt' if repo == 'isosmart' else 'med_fallback.py.txt'),{'_local_fallback_allowed'},settings)
            self.assertTrue(f['_local_fallback_allowed'](None))
            settings.IS_PRODUCTION=True
            self.assertFalse(f['_local_fallback_allowed'](None))


if __name__=='__main__':
    unittest.main()
