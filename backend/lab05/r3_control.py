"""Maintenance-only R3 negative inputs and live scope changes in the disposable DB."""
import json
import os
from pathlib import Path
import sys
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

root = Path(os.environ['LAB04_ROOT']).resolve()
assert root.parent == Path('/tmp') and root.name.startswith('adminapps-lab04-')
runtime = root / 'runtime'
action = sys.argv[1]
if action == 'negative-proofs':
    trust = json.loads((runtime / 'central-trust.json').read_text())
    client = json.loads((runtime / 'sso-client.json').read_text())
    proof = json.loads((runtime / 'r3-proof-input.json').read_text())
    claims = jwt.decode(proof, trust['PUBLIC_KEYS'][trust['SIGNING_KID']], algorithms=['RS256'],
                        audience=client['audience'][0], issuer=trust['ISSUER'])
    cases = {}
    for name, changes in [('audience', {'aud': ['wrong']}),
                          ('issuer', {'iss': 'https://wrong.example.invalid'}),
                          ('client', {'client_id': 'unregistered'}),
                          ('product', {'product': 'MEDSUPPLIER'}),
                          ('tenant', {'tenant_id': client['foreign'], 'organization_id': client['foreign']}),
                          ('role', {'role': 'org_admin'})]:
        cases[name] = jwt.encode({**claims, **changes}, trust['PRIVATE_KEY'], algorithm='RS256',
                                headers={'kid': trust['SIGNING_KID']})
    cases['signature'] = jwt.encode(claims, rsa.generate_private_key(public_exponent=65537, key_size=2048),
                                   algorithm='RS256', headers={'kid': trust['SIGNING_KID']})
    path = runtime / 'r3-negative-proofs.json'
    path.write_text(json.dumps(cases))
    path.chmod(0o600)
elif action in ('remove-scopes', 'restore-scopes'):
    import lab_env
    from django.db import connection
    from apps.products.models import OrganizationProductEntitlement
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_user')
        assert cursor.fetchone()[0] == 'lab04_maintenance'
    client = json.loads((runtime / 'sso-client.json').read_text())
    scopes = [] if action == 'remove-scopes' else [
        'ISO_SMART:resources.resource:' + op for op in ('read', 'create', 'update')]
    count = OrganizationProductEntitlement.objects.filter(
        organization_id=client['tenant'], product__code='ISO_SMART').update(scopes=scopes)
    assert count == 1
else:
    raise RuntimeError('Unknown R3 maintenance action')
