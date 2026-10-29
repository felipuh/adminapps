import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from isolation import inspect_capacity, inspect_local, overlaps, validate_inventory
from test_preflight import fixture


def inventory():
    p=fixture()
    for product,app in p['applications'].items():
        app.update(authority_product=product, identity_authority='ADMINAPPS',
                   secret_references={k:'vault/qa/'+product+'/'+k for k in ('django','database','sso')}, redis={'enabled':False})
        app['databases']=[]
        for alias in (('default',) if product=='ADMINAPPS' else ('default','ai_db','audit_db')):
            name='staging_'+product.lower()+'_'+alias
            app['databases'].append(dict(alias=alias,engine='django.db.backends.postgresql',host='127.0.0.1',port='15432',name=name,identity=name,role=name,cluster_id='qa-cluster',volume_id=name))
    return p

class IsolationTests(unittest.TestCase):
    def test_complete_inventory_is_structural_only(self):self.assertEqual(validate_inventory(inventory()),[])
    def test_database_aliases_and_actual_destinations(self):
        for field in ('engine','alias','host','cluster_id','volume_id'):
            p=inventory();p['applications']['ISO_SMART']['databases'][0][field]=''
            self.assertTrue(validate_inventory(p))
        p=inventory();apps=p['applications'];apps['MEDSUPPLIER']['databases'][0]['name']=apps['ISO_SMART']['databases'][0]['name']
        self.assertIn('MEDSUPPLIER:shared_database_destination',validate_inventory(p))
    def test_shared_roles_volumes_and_missing_alias(self):
        for field in ('role','volume_id'):
            p=inventory();apps=p['applications'];apps['MEDSUPPLIER']['databases'][0][field]=apps['ISO_SMART']['databases'][0][field]
            self.assertTrue(validate_inventory(p))
        p=inventory();p['applications']['ISO_SMART']['databases'].pop();self.assertTrue(validate_inventory(p))
    def test_nested_or_symlink_paths_overlap(self):
        p=inventory();app=p['applications']['ISO_SMART'];app['venv_path']=app['source_path']+'/.venv';self.assertTrue(validate_inventory(p))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'real').mkdir();(root/'alias').symlink_to(root/'real')
            self.assertTrue(overlaps(root/'alias',root/'real'))
            self.assertFalse(overlaps(root/'real',root/'really'))
    def test_missing_secrets_redis_and_wrong_authority(self):
        for field,value in [('secret_references',{}),('redis',{'enabled':True}),('authority_product','ISO_SMART'),('identity_authority','local')]:
            p=inventory();p['applications']['MEDSUPPLIER'][field]=value;self.assertTrue(validate_inventory(p))
    def test_capacity_every_dimension_and_unknown(self):
        need=dict(disk_bytes=10,memory_bytes=10,cpus=4)
        self.assertEqual(inspect_capacity('/',need,need),[])
        for field in need:
            measured=dict(need);measured[field]=0
            self.assertIn('insufficient_'+field,inspect_capacity('/',need,measured))
        self.assertTrue(inspect_capacity('/nonexistent',need))
        self.assertTrue(inspect_capacity('/',{}))
    def local_fixture(self,tmp):
        app=dict(source_path=str(tmp/'source'),venv_path=str(tmp/'venv'),data_path=str(tmp/'data'))
        for field in ('source_path','venv_path','data_path'):Path(app[field]).mkdir()
        venv=Path(app['venv_path']);(venv/'pyvenv.cfg').write_text('include-system-site-packages = false\n')
        meta=venv/'lib/python3.12/site-packages/Django-5.2.dist-info/METADATA';meta.parent.mkdir(parents=True);meta.write_text('Name: Django\nVersion: 5.2.99\n')
        lock=tmp/'requirements.lock';lock.write_text('Django==5.2.99 --hash=sha256:'+'a'*64+'\n')
        app['dependency_lock']=dict(path=str(lock),sha256=hashlib.sha256(lock.read_bytes()).hexdigest())
        return {'applications':{'ISO_SMART':app}},meta
    def test_local_probe_is_not_execution_attestation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,_=self.local_fixture(Path(tmp));self.assertEqual(inspect_local(p,running=[]),[])
    def test_active_checkout_and_dependency_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,_=self.local_fixture(Path(tmp));app=p['applications']['ISO_SMART']
            errors=inspect_local(p,running=[app['source_path']+'/backend'])
            self.assertIn('ISO_SMART:source_path_used_by_active_process',errors)
            (Path(app['venv_path'])/'pyvenv.cfg').write_text('include-system-site-packages = true\n')
            self.assertIn('ISO_SMART:venv_not_independent',inspect_local(p,running=[]))
    def test_lock_mismatch_unsupported_version_and_no_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            p,meta=self.local_fixture(Path(tmp));meta.write_text('Name: Django\nVersion: 4.2.22\n')
            errors=inspect_local(p,running=[])
            self.assertIn('ISO_SMART:dependency_lock_mismatch',errors);self.assertIn('ISO_SMART:unsupported_django_baseline',errors)
            lock=Path(p['applications']['ISO_SMART']['dependency_lock']['path']);lock.write_text('Django==5.2.99\n')
            p['applications']['ISO_SMART']['dependency_lock']['sha256']=hashlib.sha256(lock.read_bytes()).hexdigest()
            self.assertIn('ISO_SMART:reproducible_dependency_lock_unverified',inspect_local(p,running=[]))
    def test_cli_always_blocks_execution_and_handles_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=Path(tmp)/'plan.json'
            for value in ('invalid',json.dumps(fixture()),'null'):
                plan.write_text(value)
                r=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('preflight.py')),str(plan)],capture_output=True,text=True)
                self.assertEqual(r.returncode,2,r.stderr)
                result=json.loads(r.stdout);self.assertEqual(result['execution_status'],'BLOCKED');self.assertNotEqual(result['plan_status'],'PASS')

if __name__=='__main__':unittest.main()
