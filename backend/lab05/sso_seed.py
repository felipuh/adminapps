"""Maintenance-only disposable trust/registry and narrower SSO runtime grants."""
import json
import os
import secrets
from datetime import timedelta
import lab_env
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.db import connection
from django.utils import timezone
from apps.integration.models import IntegrationAPIKey, SSOClient, SSOSecurityFence
from apps.products.models import ProductSystem, OrganizationProductEntitlement
from apps.users.models import User

root = lab_env.ROOT / 'runtime'
fixtures = json.loads((root / 'fixtures.json').read_text())
with connection.cursor() as cursor:
    cursor.execute('SELECT current_user')
    assert cursor.fetchone()[0] == 'lab04_maintenance'
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
trust = dict(ALGORITHM='RS256', ISSUER='https://central.lab.example.invalid',
             SIGNING_KID='lab05-c1-r1', PUBLIC_KEYS={'lab05-c1-r1': key.public_key().public_bytes(
                 serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()},
             PRIVATE_KEY=key.private_bytes(serialization.Encoding.PEM,
                 serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode())
credential, unregistered, password = (secrets.token_urlsafe(40) for _ in range(3))
principal = IntegrationAPIKey.objects.create(name='LAB05 SSO', key=credential)
IntegrationAPIKey.objects.create(name='LAB05 unregistered', key=unregistered)
product = ProductSystem.objects.get(code='ISO_SMART')
assert product.is_available and not product.billing_enabled
client = SSOClient.objects.create(client_id='lab05-iso-smart', product=product,
    principal=principal, audience='urn:lab05:iso-smart', issuer=trust['ISSUER'],
    allowed_kids=[trust['SIGNING_KID']], enabled=True)
client.tenants.add(fixtures['tenant'])
client.full_clean()
OrganizationProductEntitlement.objects.create(organization_id=fixtures['tenant'],
    product=product, enabled=True, status='active', starts_at=timezone.now()-timedelta(minutes=1),
    scopes=['ISO_SMART:core.document:read'], modules_enabled=[])
user = User.objects.get(pk=fixtures['viewer'])
user.set_password(password)
user.save(update_fields=['password'])
from apps.users.models_2fa import TwoFactorAuth
mfa_user = User.objects.get(pk=fixtures['target'])
mfa_user.set_password(password)
mfa_user.save(update_fields=['password'])
factor = TwoFactorAuth(user=mfa_user, is_enabled=True)
factor.secret = factor.generate_secret()
factor.save()
SSOSecurityFence.objects.filter(pk=1).update(enabled=True)
for name, value in [('central-trust', trust), ('sso-client', dict(
        credential=credential, unregistered=unregistered, password=password, otp_secret=factor.secret,
        client_id=client.client_id, audience=[client.audience], product=product.code,
        contract_version=client.contract_version, tenant=fixtures['tenant'], foreign=fixtures['foreign']))]:
    with open(root / (name+'.json'), 'x', opener=lambda p,f: os.open(p,f,0o600)) as stream:
        json.dump(value, stream)
# Start from the reviewed IAM ACL ceiling, then remove human/admin capabilities.
# No grants are added to IAM or CP; SSO has no registry or business writes.
with connection.cursor() as cursor:
    cursor.execute('''
        REVOKE ALL ON user_sessions, organization_invitations, django_session,
            organization_settings, organization_feature_flags, auth_permission,
            auth_group, auth_group_permissions, users_groups, users_user_permissions,
            django_content_type, user_activity_logs FROM lab04_sso;
        REVOKE INSERT, UPDATE ON user_organizations FROM lab04_sso;
        REVOKE INSERT, UPDATE ON users FROM lab04_sso;
        GRANT UPDATE (last_login, last_login_at, last_activity_at, failed_login_attempts,
                      updated_at) ON users TO lab04_sso;
        REVOKE INSERT ON two_factor_auth FROM lab04_sso;
    ''')
    cursor.execute("SELECT sequencename FROM pg_sequences WHERE schemaname='public'")
    for (name,) in cursor.fetchall():
        from psycopg2 import sql
        cursor.execute(sql.SQL('REVOKE ALL ON SEQUENCE {} FROM lab04_sso').format(sql.Identifier(name)))
