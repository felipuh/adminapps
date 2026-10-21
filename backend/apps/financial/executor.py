"""Narrow capability-verifying PostgreSQL executor.

The executable process that imports this component receives the executor-only
database connection configuration and public verification keys.  General Django
runtime deliberately has neither.  This module offers no arbitrary SQL API.
"""
from django.db import connections

from .capabilities import verify_capability
from .services import canonical_material_request_hash


class FinancialExecutor:
    def __init__(self, *, database, public_keys, issuer_id):
        self._database = dict(database)
        self._public_keys = dict(public_keys)
        self._issuer_id = issuer_id

    def admit_reserve(self, *, capability, correlation_id, provider, model_identifier,
                      max_input_tokens, max_output_tokens, tenant_assertion,
                      request_class, schema_version=1, evidence_ids=None):
        """Verify then call the sole executor-granted admission function."""
        claims = verify_capability(
            capability, public_keys=self._public_keys, issuer_id=self._issuer_id,
        )
        material_hash = canonical_material_request_hash(
            tenant_assertion=tenant_assertion, product_id=claims['product_id'], provider=provider,
            model_identifier=model_identifier, max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens, request_class=request_class,
            schema_version=schema_version, evidence_ids=evidence_ids,
        )
        if material_hash != claims['material_request_hash']:
            raise PermissionError('CAPABILITY_MATERIAL_DENIED')
        alias = 'financial_isolated_executor'
        connections.databases[alias] = self._database
        database = connections[alias]
        try:
            if database.vendor != 'postgresql':
                raise RuntimeError('Financial executor requires PostgreSQL.')
            with database.cursor() as cursor:
                cursor.execute(
                    '''SELECT decision_id, decision_state, denial_code, reservation_id,
                              currency, reserved_amount, replayed
                       FROM public.financial_admit_reserve_capability(
                         %s::uuid, %s::text, %s::text, %s::smallint, %s::uuid, %s::integer,
                         %s::uuid, %s::uuid, %s::uuid, %s::uuid, %s::text, %s::text,
                         %s::text, %s::uuid, %s::text, %s::text, %s::bigint, %s::bigint
                       )''',
                    [
                        claims['capability_id'], claims['iss'], claims['kid'], claims['version'],
                        claims['grant_id'], claims['grant_version'], claims['producer_registration_id'],
                        claims['organization_id'], claims['product_id'], claims['jti'],
                        claims['material_request_hash'], claims['environment'], claims['operation'],
                        str(correlation_id), provider, model_identifier,
                        max_input_tokens, max_output_tokens,
                    ],
                )
                row = cursor.fetchone()
            return dict(zip(
                ('decision_id', 'decision_state', 'denial_code', 'reservation_id',
                 'currency', 'reserved_amount', 'replayed'), row,
            ))
        finally:
            database.close()
            connections.databases.pop(alias, None)
