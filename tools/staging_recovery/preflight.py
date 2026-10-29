"""Offline staging configuration guard. Never connects, starts or migrates anything.
A valid plan is NOT proof of infrastructure isolation or permission to execute.
"""
import argparse
import json
from pathlib import Path
from isolation import inspect_capacity, inspect_local, validate_inventory
from urllib.parse import urlsplit

PRODUCTS = ('ADMINAPPS', 'ISO_SMART', 'MEDSUPPLIER')
UNSAFE = ('DEBUG', 'ALLOW_LOCAL_AUTH_BYPASS_FOR_TESTS', 'ALLOW_LOCAL_AUTH_FALLBACK',
          'ADMIN_APPS_ALLOW_LOCAL_FALLBACK', 'SMART3AI_SSO_ALLOW_2FA_BYPASS',
          'ALLOW_SESSION_AUTH_FOR_DEV', 'USE_SQLITE_DATABASE')


def validate(plan):
    errors = []
    if not isinstance(plan, dict):
        return ['invalid_plan']
    apps = plan.get('applications')
    if not isinstance(apps, dict) or set(apps) != set(PRODUCTS):
        return ['three_independent_products_required']
    identities, roles, paths, ports = set(), set(), set(), set()
    for product in PRODUCTS:
        app = apps[product]
        if not isinstance(app, dict):
            errors.append(product + ':invalid_config')
            continue
        flags = app.get('flags', {})
        if not isinstance(flags, dict):
            flags = {}
        for flag in UNSAFE:
            if flags.get(flag) is not False:
                errors.append(product + ':' + flag + '_must_be_explicit_false')
        if app.get('environment') != 'staging':
            errors.append(product + ':staging_environment_required')
        if app.get('product') != product:
            errors.append(product + ':product_mismatch')
        if app.get('bind_address') != '127.0.0.1':
            errors.append(product + ':loopback_required')
        port = app.get('port')
        if type(port) is not int or not 1024 <= port <= 65535 or port in ports:
            errors.append(product + ':distinct_unprivileged_port_required')
        else:
            ports.add(port)
        # A plan must enumerate ALL aliases, including AI/audit/foundation/test DBs.
        dbs = app.get('databases')
        if not isinstance(dbs, list) or not dbs:
            errors.append(product + ':database_inventory_required')
            dbs = []
        for db in dbs:
            if not isinstance(db, dict):
                errors.append(product + ':invalid_database')
                continue
            ident, role = db.get('identity'), db.get('role')
            if not isinstance(ident, str) or not ident.startswith('staging_') or ident in identities:
                errors.append(product + ':distinct_staging_database_required')
            else:
                identities.add(ident)
            if not isinstance(role, str) or not role.startswith('staging_') or role in roles:
                errors.append(product + ':distinct_staging_role_required')
            else:
                roles.add(role)
        for key in ('source_path', 'venv_path', 'data_path'):
            value = app.get(key)
            if not isinstance(value, str) or not value.startswith('/srv/smart3ai-staging/') or '..' in Path(value).parts or value in paths:
                errors.append(product + ':' + key + '_must_be_dedicated')
            else:
                paths.add(value)
        if app.get('mounts') != []:
            errors.append(product + ':mounts_require_separate_review')
        if app.get('secrets_policy') != 'new_independent_credentials':
            errors.append(product + ':independent_secrets_required')
        if product != 'ADMINAPPS':
            try:
                url = urlsplit(app.get('adminapps_url', ''))
                ok = (url.scheme == 'https' and url.hostname == '127.0.0.1'
                      and url.port == apps['ADMINAPPS'].get('port')
                      and not url.username and not url.password and not url.query and not url.fragment)
            except (TypeError, ValueError, AttributeError):
                ok = False
            if not ok:
                errors.append(product + ':verified_internal_https_authority_required')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    plan = None
    try:
        plan = json.loads(args.plan.read_text())
        errors = validate(plan)
    except (OSError, ValueError, TypeError):
        errors = ['plan_unreadable_or_invalid']
    if isinstance(plan, dict):
        errors += validate_inventory(plan)
        errors += inspect_capacity(plan.get('target_root', '/nonexistent'), plan.get('capacity_required'))
        if not validate(plan):
            errors += inspect_local(plan)
    # Intentionally cannot clear these with self-asserted manifest booleans.
    blockers = ['creation_authorization_required', 'fresh_cluster_identity_and_acl_evidence_required',
                'effective_settings_and_secret_provenance_required', 'port_and_mount_ownership_required',
                'private_tls_and_trust_verification_required', 'full_runtime_QA_required', 'effective_dependency_resolution_required',
                'all_service_users_and_settings_inventory_required', 'staging_network_egress_deny_to_operational_required']
    print(json.dumps({'plan_status': 'FAIL' if errors else 'STRUCTURALLY_VALID_UNATTESTED', 'errors': errors,
                      'execution_status': 'BLOCKED', 'blockers': blockers}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
