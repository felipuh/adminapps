"""Resolver inventory using the API P0 synthetic harness. Never connects to DB/network."""
import csv
import inspect
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

import rec_sso_03d_api_p0_offline as harness
from django.urls import URLResolver, get_resolver
from apps.users.api_authorization import POLICIES, ControlPlaneMixin
from apps.users.platform_api_authorization import POLICIES as PLATFORM, PlatformOperationMixin

rows = []

def walk(patterns, prefix=''):
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            walk(pattern.url_patterns, route)
            continue
        if not route.startswith('api/'):
            continue
        cb = pattern.callback
        cls = getattr(cb, 'cls', None) or getattr(cb, 'view_class', None)
        if cls:
            actions = getattr(cb, 'actions', None)
            if actions:
                methods = dict(actions)
                if 'get' in methods:
                    methods['head'] = methods['get']
                methods['options'] = 'metadata'
            else:
                methods = {m: m for m in cls.http_method_names if hasattr(cls, m)}
            for method, action in methods.items():
                view = cls(**getattr(cb, 'initkwargs', {}))
                view.action = action
                view.request = SimpleNamespace(method=method.upper())
                permissions = '|'.join(type(p).__name__ for p in view.get_permissions())
                guard = ('ControlPlaneMixin' if issubclass(cls, ControlPlaneMixin) else
                         'PlatformOperationMixin' if issubclass(cls, PlatformOperationMixin) else 'EXISTING_REVIEWED')
                policy = POLICIES.get(cls.__name__) or PLATFORM.get(cls.__name__)
                rows.append(dict(route=route, method=method.upper(), handler=cls.__module__+'.'+cls.__name__, action=action,
                                 effective_permissions=permissions, additional_boundary=guard, policy=repr(policy),
                                 functional_status='SEE_AUTHORIZATION_DELTA_NOT_GLOBAL_PASS'))
        else:
            source = inspect.getsource(cb)
            match = re.search(r'require_http_methods\((\[[^]]+\])\)', source)
            import ast
            methods = ast.literal_eval(match.group(1)) if match else ['UNDECLARED']
            boundary = ('service_data_access' if '@service_data_access' in source else
                        'require_client + Decision A/B/C/H/D' if '@require_client' in source else
                        'require_api_key (existing)' if '@require_api_key' in source else 'manual/decorators')
            for method in methods:
                rows.append(dict(route=route, method=method, handler=cb.__module__+'.'+cb.__name__, action=cb.__name__,
                                 effective_permissions='decorator/manual; see boundary', additional_boundary=boundary,
                                 policy='server-side exact operation/tenant/product grant' if boundary=='service_data_access' else 'existing reviewed; residuals in REPORT',
                                 functional_status='SEE_AUTHORIZATION_DELTA_NOT_GLOBAL_PASS'))

walk(get_resolver().url_patterns)
out = Path(sys.argv[1]);out.mkdir(parents=True, exist_ok=True)
with (out/'endpoint-inventory.csv').open('w') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
summary = {'resolver_api_entries':len(rows), 'distinct_routes':len({r['route'] for r in rows}),
           'unique_handler_actions':len({(r['handler'],r['action']) for r in rows}),
           'database_attempts':harness.db_guard.call_count, 'network_attempts':sum(g.call_count for g in harness.guards)}
(out/'inventory-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary))
assert summary['database_attempts']==summary['network_attempts']==0
