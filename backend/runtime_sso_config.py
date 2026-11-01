"""Load a private, declarative SSO deployment config; never execute config code."""
import json
import os
import stat
from urllib.parse import urlsplit

FALSE_FLAGS = frozenset({
    'DEBUG', 'ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS', 'ALLOW_LOCAL_AUTH_FALLBACK',
    'ADMIN_APPS_ALLOW_LOCAL_FALLBACK', 'ALLOW_SESSION_AUTH_FOR_DEV',
    'SMART3AI_SSO_ALLOW_2FA_BYPASS', 'USE_SQLITE_DATABASE',
})
ENVIRONMENT_KEYS = FALSE_FLAGS | frozenset({
    'ENVIRONMENT', 'DJANGO_ENV', 'SECRET_KEY', 'DJANGO_SECRET_KEY',
    'ADMIN_APPS_BASE_URL', 'ADMIN_APPS_API_KEY', 'REQUESTS_CA_BUNDLE',
    'SSL_CERT_FILE', 'OWNER_ORGANIZATION_EXTERNAL_ID',
})


def _https(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError()
    return value


def _trust(config, signing):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    if not isinstance(config, dict) or config.get('ALGORITHM') != 'RS256':
        raise ValueError()
    _https(config['ISSUER'])
    public = config['PUBLIC_KEYS']
    if not isinstance(public, dict) or not 1 <= len(public) <= 8:
        raise ValueError()
    numbers = set()
    for kid, pem in public.items():
        if not isinstance(kid, str) or not kid or not isinstance(pem, str):
            raise ValueError()
        key = serialization.load_pem_public_key(pem.encode())
        if not isinstance(key, rsa.RSAPublicKey) or key.key_size < 2048:
            raise ValueError()
        values = key.public_numbers()
        numbers.add((values.e, values.n))
    if signing:
        key = serialization.load_pem_private_key(config['PRIVATE_KEY'].encode(), password=None)
        if not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 2048:
            raise ValueError()
        pem = public[config['SIGNING_KID']]
        advertised = serialization.load_pem_public_key(pem.encode())
        if key.public_key().public_numbers() != advertised.public_numbers():
            raise ValueError()
    elif 'PRIVATE_KEY' in config or 'SIGNING_KID' in config:
        raise ValueError()
    return numbers


def load_runtime_sso_config(environ, product):
    path = environ.get('SMART3AI_RUNTIME_CONFIG')
    if not path:
        return {}
    try:
        if product not in {'ADMINAPPS', 'ISO_SMART', 'MEDSUPPLIER'} or not os.path.isabs(path):
            raise ValueError()
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, 'r', encoding='utf-8') as stream:
            meta = os.fstat(stream.fileno())
            if (not stat.S_ISREG(meta.st_mode) or stat.S_ISLNK(os.lstat(path).st_mode)
                    or meta.st_mode & 0o077 or meta.st_uid not in (0, os.geteuid())
                    or meta.st_size > 262144):
                raise ValueError()
            data = json.load(stream)
        if (not isinstance(data, dict) or set(data) != {'schema_version', 'product', 'environment', 'settings'}
                or type(data['schema_version']) is not int or data['schema_version'] != 1
                or data['product'] != product):
            raise ValueError()
        env = data['environment']
        if not isinstance(env, dict) or set(env) - ENVIRONMENT_KEYS:
            raise ValueError()
        for key, value in env.items():
            if not isinstance(value, str) or '\0' in value:
                raise ValueError()
            if key in FALSE_FLAGS and value.lower() not in {'false', '0', 'no', 'off'}:
                raise ValueError()
            if key in {'ENVIRONMENT', 'DJANGO_ENV'} and value != 'production':
                raise ValueError()
        config = data['settings']
        expected = {'SSO_CENTRAL_TRUST'}
        if product != 'ADMINAPPS':
            expected |= {'SSO_LOCAL_TRUST', 'ADMIN_APPS_SSO'}
        if not isinstance(config, dict) or set(config) != expected:
            raise ValueError()
        central = _trust(config['SSO_CENTRAL_TRUST'], signing=product == 'ADMINAPPS')
        if product != 'ADMINAPPS':
            local = _trust(config['SSO_LOCAL_TRUST'], signing=True)
            if local & central or config['SSO_LOCAL_TRUST']['ISSUER'] == config['SSO_CENTRAL_TRUST']['ISSUER']:
                raise ValueError()
            if not isinstance(config['SSO_LOCAL_TRUST'].get('AUDIENCE'), str) or not config['SSO_LOCAL_TRUST']['AUDIENCE']:
                raise ValueError()
            client = config['ADMIN_APPS_SSO']
            if (not isinstance(client, dict) or set(client) != {'BASE_URL', 'ISSUER', 'CLIENT_ID', 'AUDIENCE'}
                    or any(not isinstance(v, str) or not v for v in client.values())
                    or client['ISSUER'] != config['SSO_CENTRAL_TRUST']['ISSUER']):
                raise ValueError()
            _https(client['BASE_URL'])
            if env.get('ADMIN_APPS_BASE_URL') != client['BASE_URL'] or not env.get('ADMIN_APPS_API_KEY'):
                raise ValueError()
        return data
    except Exception:
        raise RuntimeError('Private SSO runtime configuration is invalid or inaccessible') from None

