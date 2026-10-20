"""CH trust codec. Explicit RSA keyrings only; no legacy/global JWT fallback.

This file is intentionally identical in the three independently deployed products.
Only synthetic test runners provision keys here; runtime configuration is external.
"""
from datetime import timedelta
import time
import uuid

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed, APIException

CONTRACT = 'rec-sso-03b-ch-v1'
PRODUCTS = {'ISO_SMART', 'MEDSUPPLIER'}


class TrustUnavailable(APIException):
    status_code = 503
    default_detail = 'Authentication trust configuration unavailable.'
    default_code = 'trust_unavailable'


def _public_keys(config):
    values = config.get('PUBLIC_KEYS')
    if not isinstance(values, dict) or not values:
        raise ValueError()
    result = {}
    for kid, pem in values.items():
        if not isinstance(kid, str) or not kid or not isinstance(pem, str):
            raise ValueError()
        key = serialization.load_pem_public_key(pem.encode())
        if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 2048:
            raise ValueError()
        result[kid] = key
    return result


def trust(family, *, signing=False):
    try:
        if family not in ('CENTRAL', 'LOCAL'):
            raise ValueError()
        config = getattr(settings, 'SSO_' + family + '_TRUST', None)
        if not isinstance(config, dict) or config.get('ALGORITHM') != 'RS256':
            raise ValueError()
        if not isinstance(config.get('ISSUER'), str) or not config['ISSUER'].startswith('https://'):
            raise ValueError()
        keys = _public_keys(config)
        if family == 'LOCAL':
            central, central_keys = trust('CENTRAL')
            if central.get('PRIVATE_KEY') or config['ISSUER'] == central['ISSUER']:
                raise ValueError()
            if any(a.public_numbers() == b.public_numbers() for a in keys.values() for b in central_keys.values()):
                raise ValueError()
            if not isinstance(config.get('AUDIENCE'), str) or not config['AUDIENCE']:
                raise ValueError()
        if signing:
            kid = config['SIGNING_KID']
            key = serialization.load_pem_private_key(config['PRIVATE_KEY'].encode(), password=None)
            if (not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 2048
                    or kid not in keys or key.public_key().public_numbers() != keys[kid].public_numbers()):
                raise ValueError()
        return config, keys
    except TrustUnavailable:
        raise
    except Exception:
        raise TrustUnavailable() from None


def _claims(data, family, issuer, audience, product, client_id):
    if (data.get('iss') != issuer or data.get('aud') != [audience]
            or data.get('auth_contract') != CONTRACT or data.get('token_family') != family
            or data.get('product') != product or product not in PRODUCTS
            or data.get('client_id') != client_id or not isinstance(client_id, str) or not client_id
            or data.get('token_type') not in ('access', 'refresh')
            or not isinstance(data.get('amr'), list) or data['amr'] not in (['pwd'], ['pwd', 'otp'])
            or not isinstance(data.get('jti'), str) or not data['jti']):
        raise ValueError()
    for claim in ('sub', 'tenant_id'):
        if str(uuid.UUID(data[claim])) != data[claim]:
            raise ValueError()
    if family == 'CENTRAL' and (data.get('organization_id') != data['tenant_id']
                                or data.get('user_id') != data['sub']):
        raise ValueError()
    if (type(data.get('exp')) is not int or type(data.get('iat')) is not int
            or data['iat'] > time.time() or data['exp'] <= time.time() or data['exp'] <= data['iat']):
        raise ValueError()


def decode(token, *, family, audience, product, client_id, token_type='access', allowed_kids=None):
    config, keys = trust(family)
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')
        if (header.get('alg') != 'RS256' or header.get('typ') != 'JWT'
                or not isinstance(kid, str) or kid not in keys
                or (allowed_kids is not None and kid not in allowed_kids)
                or any(k in header for k in ('crit', 'jku', 'jwk', 'x5u'))):
            raise ValueError()
        data = jwt.decode(token, keys[kid], algorithms=['RS256'], issuer=config['ISSUER'],
                          audience=audience, options={'require': ['exp', 'iat', 'sub', 'jti', 'aud', 'iss']})
        _claims(data, family, config['ISSUER'], audience, product, client_id)
        if data['token_type'] != token_type:
            raise ValueError()
        return data
    except Exception:
        raise AuthenticationFailed('Invalid authentication proof.') from None


def encode(data, *, family, audience, product, client_id):
    config, _ = trust(family, signing=True)
    try:
        _claims(data, family, config['ISSUER'], audience, product, client_id)
        return jwt.encode(data, config['PRIVATE_KEY'], algorithm='RS256',
                          headers={'kid': config['SIGNING_KID'], 'typ': 'JWT'})
    except Exception:
        raise TrustUnavailable() from None


def leeway():
    return timedelta(0)
