import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from runtime_sso_config import load_runtime_sso_config


class RuntimeConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def material(issuer):
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            return dict(ALGORITHM='RS256', ISSUER=issuer, SIGNING_KID='test-key',
                        PRIVATE_KEY=key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode(),
                        PUBLIC_KEYS={'test-key': key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()})
        cls.central = material('https://central.example.invalid')
        cls.local = material('https://local.example.invalid')
        cls.local['AUDIENCE'] = 'local-test-audience'

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='smart3ai-config-test-')
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'private.json'

    def payload(self, product='ADMINAPPS'):
        value = dict(schema_version=1, product=product, environment={},
                     settings={'SSO_CENTRAL_TRUST': copy.deepcopy(self.central)})
        if product != 'ADMINAPPS':
            central = value['settings']['SSO_CENTRAL_TRUST']
            central.pop('PRIVATE_KEY'); central.pop('SIGNING_KID')
            value['settings']['SSO_LOCAL_TRUST'] = copy.deepcopy(self.local)
            value['settings']['ADMIN_APPS_SSO'] = dict(BASE_URL='https://127.0.0.1/api/integration', ISSUER=central['ISSUER'], CLIENT_ID='test-client', AUDIENCE='test-audience')
            value['environment'] = dict(ADMIN_APPS_API_KEY='test-key', ADMIN_APPS_BASE_URL='https://127.0.0.1/api/integration')
        return value

    def load(self, value, product='ADMINAPPS'):
        self.path.write_text(json.dumps(value)); self.path.chmod(0o600)
        return load_runtime_sso_config({'SMART3AI_RUNTIME_CONFIG': str(self.path)}, product)

    def test_optional_config_preserves_existing_settings(self):
        self.assertEqual(load_runtime_sso_config({}, 'ADMINAPPS'), {})

    def test_central_signing_config(self):
        value = self.payload()
        self.assertEqual(self.load(value), value)

    def test_public_central_and_distinct_local_consumer_keys(self):
        for product in ('ISO_SMART', 'MEDSUPPLIER'):
            value = self.payload(product)
            self.assertEqual(self.load(value, product), value)

    def test_group_readable_config_rejected(self):
        self.load(self.payload()); self.path.chmod(0o640)
        with self.assertRaises(RuntimeError):
            load_runtime_sso_config({'SMART3AI_RUNTIME_CONFIG': str(self.path)}, 'ADMINAPPS')

    def test_symlink_rejected(self):
        self.load(self.payload()); link = self.path.with_name('link.json'); link.symlink_to(self.path)
        with self.assertRaises(RuntimeError):
            load_runtime_sso_config({'SMART3AI_RUNTIME_CONFIG': str(link)}, 'ADMINAPPS')

    def test_fifo_rejected_without_blocking(self):
        os.mkfifo(self.path, 0o600)
        with self.assertRaises(RuntimeError):
            load_runtime_sso_config({'SMART3AI_RUNTIME_CONFIG': str(self.path)}, 'ADMINAPPS')

    def test_errors_do_not_echo_config_values(self):
        marker = 'synthetic-sensitive-marker'
        self.path.write_text('{"private": "' + marker); self.path.chmod(0o600)
        with self.assertRaises(RuntimeError) as error:
            load_runtime_sso_config({'SMART3AI_RUNTIME_CONFIG': str(self.path)}, 'ADMINAPPS')
        self.assertNotIn(marker, str(error.exception))

    def test_database_override_rejected(self):
        value = self.payload(); value['environment']['DB_NAME'] = 'different-database'
        with self.assertRaises(RuntimeError): self.load(value)

    def test_authentication_bypass_rejected(self):
        value = self.payload(); value['environment']['ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS'] = 'true'
        with self.assertRaises(RuntimeError): self.load(value)

    def test_development_environment_override_rejected(self):
        value = self.payload(); value['environment']['ENVIRONMENT'] = 'development'
        with self.assertRaises(RuntimeError): self.load(value)

    def test_private_central_key_in_consumer_rejected(self):
        value = self.payload('ISO_SMART'); value['settings']['SSO_CENTRAL_TRUST']['PRIVATE_KEY'] = self.central['PRIVATE_KEY']
        with self.assertRaises(RuntimeError): self.load(value, 'ISO_SMART')

    def test_reused_central_local_signer_rejected(self):
        value = self.payload('ISO_SMART'); value['settings']['SSO_LOCAL_TRUST'] = copy.deepcopy(self.central)
        value['settings']['SSO_LOCAL_TRUST'].update(ISSUER='https://local.example.invalid', AUDIENCE='local-test-audience')
        with self.assertRaises(RuntimeError): self.load(value, 'ISO_SMART')

    def test_signing_key_mismatch_rejected(self):
        value = self.payload(); value['settings']['SSO_CENTRAL_TRUST']['PRIVATE_KEY'] = self.local['PRIVATE_KEY']
        with self.assertRaises(RuntimeError): self.load(value)

    def test_wrong_product_rejected(self):
        with self.assertRaises(RuntimeError): self.load(self.payload(), 'MEDSUPPLIER')

    def test_non_rsa_algorithm_rejected(self):
        value = self.payload(); value['settings']['SSO_CENTRAL_TRUST']['ALGORITHM'] = 'HS256'
        with self.assertRaises(RuntimeError): self.load(value)

    def test_http_authority_rejected(self):
        value = self.payload('MEDSUPPLIER'); value['settings']['ADMIN_APPS_SSO']['BASE_URL'] = 'http://127.0.0.1'
        with self.assertRaises(RuntimeError): self.load(value, 'MEDSUPPLIER')

    def test_arbitrary_settings_override_rejected(self):
        value = self.payload(); value['settings']['INSTALLED_APPS'] = []
        with self.assertRaises(RuntimeError): self.load(value)


if __name__ == '__main__':
    unittest.main()

