import copy
import unittest
from preflight import validate, PRODUCTS, UNSAFE


def fixture():
    apps = {}
    for index, product in enumerate(PRODUCTS):
        name = product.lower()
        apps[product] = dict(product=product, environment='staging', flags=dict.fromkeys(UNSAFE, False),
            bind_address='127.0.0.1', port=18440+index,
            databases=[dict(identity='staging_'+name, role='staging_'+name)],
            source_path='/srv/smart3ai-staging/'+name+'/source',
            venv_path='/srv/smart3ai-staging/'+name+'/venv',
            data_path='/srv/smart3ai-staging/'+name+'/data', mounts=[],
            secrets_policy='new_independent_credentials', adminapps_url='https://127.0.0.1:18440/api/integration')
    return {'applications': apps}


class GuardTests(unittest.TestCase):
    def test_complete_plan_is_only_structurally_valid(self):
        self.assertEqual(validate(fixture()), [])

    def test_all_unsafe_flags_fail_closed(self):
        for product in PRODUCTS:
            for flag in UNSAFE:
                for value in (True, 'false', 0, None):
                    with self.subTest(product=product, flag=flag, value=value):
                        p=fixture();p['applications'][product]['flags'][flag]=value
                        self.assertTrue(validate(p))

    def test_missing_flags_rejected(self):
        p=fixture();p['applications']['ISO_SMART']['flags']={}
        self.assertTrue(validate(p))

    def test_shared_database_or_role_rejected(self):
        for key in ('identity','role'):
            p=fixture();a=p['applications']
            a['MEDSUPPLIER']['databases'][0][key]=a['ISO_SMART']['databases'][0][key]
            self.assertTrue(validate(p))

    def test_external_plaintext_or_credential_url_rejected(self):
        for url in ('http://127.0.0.1:18440', 'https://example.invalid', 'https://user:pass@127.0.0.1:18440', 'https://127.0.0.1:9999'):
            p=fixture();p['applications']['ISO_SMART']['adminapps_url']=url
            self.assertTrue(validate(p))

    def test_shared_dependencies_public_port_and_mount_rejected(self):
        for key,value in [('venv_path','/home/felipe/proyectos/isosmart/backend/.venv312'),('bind_address','0.0.0.0'),('port',80),('mounts',['/existing/db']),('data_path','/srv/smart3ai-staging/../production')]:
            p=fixture();p['applications']['MEDSUPPLIER'][key]=value
            self.assertTrue(validate(p))

    def test_unknown_or_missing_product_rejected(self):
        self.assertTrue(validate({}))
        p=fixture();p['applications'].pop('ADMINAPPS');self.assertTrue(validate(p))

    def test_invalid_shapes_rejected(self):
        for p in (None, [], {'applications':[]}, {'applications':dict.fromkeys(PRODUCTS,None)}):
            self.assertTrue(validate(p))


if __name__=='__main__':
    unittest.main()
