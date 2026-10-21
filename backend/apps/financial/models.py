"""S1 financial persistence models.

These models deliberately establish no operational workflow.  Future, separately
authorised services will own producer authentication, policy activation,
admission, settlement, and reconciliation transitions.
"""
import uuid

from django.db import models
from django.db.models import Q


MONEY_MAX_DIGITS = 20
MONEY_DECIMAL_PLACES = 10


class ProducerRegistration(models.Model):
    """Immutable producer-registration evidence.

    The current lifecycle state is derived from append-only
    :class:`ProducerRegistrationLifecycleEvent` rows.  Keeping this record
    immutable makes registration identity and its initial credential binding
    durable evidence rather than mutable operational state.
    """

    LIFECYCLE_STATES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
        ('retired', 'Retired'),
    ]
    ENVIRONMENTS = [
        ('controlled_test', 'Controlled test'),
        ('staging', 'Staging'),
        ('production', 'Production'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producer_code = models.CharField(max_length=80)
    credential = models.OneToOneField(
        'integration.IntegrationAPIKey',
        on_delete=models.PROTECT,
        related_name='financial_producer_registration',
        null=True,
        blank=True,
    )
    credential_fingerprint = models.CharField(max_length=80, blank=True)
    environment = models.CharField(max_length=20, choices=ENVIRONMENTS)
    permitted_product_ids = models.JSONField(default=list, blank=True)
    permitted_operations = models.JSONField(default=list, blank=True)
    lifecycle_state = models.CharField(max_length=16, choices=LIFECYCLE_STATES, default='pending')
    creation_evidence_hash = models.CharField(max_length=128)
    revocation_evidence_hash = models.CharField(max_length=128, blank=True)
    audit_owner = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_producer_registrations'
        constraints = [
            models.UniqueConstraint(
                fields=['producer_code', 'environment'],
                name='financial_producer_environment_unique',
            ),
        ]


class ProducerRegistrationLifecycleEvent(models.Model):
    """Append-only lifecycle evidence for a producer registration."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.ForeignKey(
        ProducerRegistration,
        on_delete=models.PROTECT,
        related_name='lifecycle_events',
    )
    lifecycle_state = models.CharField(
        max_length=16,
        choices=ProducerRegistration.LIFECYCLE_STATES,
    )
    actor_reference = models.CharField(max_length=160)
    evidence_hash = models.CharField(max_length=128)
    reason_code = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_producer_registration_events'
        ordering = ['created_at', 'id']
        indexes = [models.Index(fields=['registration', 'created_at'])]


class FinancialPermissionAuditEvent(models.Model):
    """Append-only central evidence for financial permission decisions."""

    ACTIONS = [
        ('granted', 'Granted'),
        ('revoked', 'Revoked'),
        ('denied', 'Denied'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=16, choices=ACTIONS)
    permission_code = models.CharField(max_length=80)
    actor_reference = models.CharField(max_length=160)
    subject_reference = models.CharField(max_length=160, blank=True)
    reason_code = models.CharField(max_length=80, blank=True)
    correlation_id = models.UUIDField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_permission_audit_events'
        ordering = ['created_at', 'id']
        indexes = [models.Index(fields=['permission_code', 'created_at'])]


class FinancialPolicy(models.Model):
    """A tenant-owned policy container.  Versions, rather than this row, carry terms."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.PROTECT, related_name='financial_policies'
    )
    policy_code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_policies'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'policy_code'], name='financial_policy_per_tenant_unique'
            ),
        ]
        permissions = [
            ('financial_policy_admin', 'Can administer financial policies'),
            ('financial_budget_admin', 'Can administer financial budgets'),
            ('financial_tariff_approve', 'Can approve financial tariffs'),
            ('financial_evidence_review', 'Can review financial evidence'),
            ('financial_reconcile', 'Can authorize financial reconciliation'),
            ('financial_manual_resolution', 'Can authorize restricted manual resolution'),
            ('financial_audit_read', 'Can access financial audit evidence'),
            ('financial_admin', 'Can assign financial administration permissions'),
        ]


class FinancialPolicyVersion(models.Model):
    STATES = [('draft', 'Draft'), ('approved', 'Approved'), ('superseded', 'Superseded'), ('retired', 'Retired')]
    ROUNDING_RULES = [('half_up', 'Half up'), ('half_even', 'Half even'), ('down', 'Down'), ('up', 'Up')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(FinancialPolicy, on_delete=models.PROTECT, related_name='versions')
    version = models.PositiveIntegerField()
    state = models.CharField(max_length=16, choices=STATES, default='draft')
    currency = models.CharField(max_length=3)
    period_timezone = models.CharField(max_length=64)
    period_boundary = models.CharField(max_length=64)
    amount_precision = models.PositiveSmallIntegerField(default=MONEY_DECIMAL_PLACES)
    rounding_rule = models.CharField(max_length=16, choices=ROUNDING_RULES)
    allowed_provider = models.CharField(max_length=120, blank=True)
    allowed_model = models.CharField(max_length=200, blank=True)
    # These are admission bounds, not provider execution settings.  A missing
    # bound is intentionally unusable by S3: output-only max_tokens is not an
    # input-exposure guarantee.
    max_input_tokens = models.PositiveBigIntegerField(null=True, blank=True)
    max_output_tokens = models.PositiveBigIntegerField(null=True, blank=True)
    effective_from = models.DateTimeField(null=True, blank=True)
    effective_until = models.DateTimeField(null=True, blank=True)
    approved_evidence_hash = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_policy_versions'
        constraints = [
            models.UniqueConstraint(fields=['policy', 'version'], name='financial_policy_version_unique'),
            models.CheckConstraint(
                check=Q(amount_precision__gte=0) & Q(amount_precision__lte=MONEY_DECIMAL_PLACES),
                name='financial_policy_precision_range',
            ),
            models.CheckConstraint(
                check=Q(effective_until__isnull=True) | Q(effective_from__isnull=True) | Q(effective_until__gt=models.F('effective_from')),
                name='financial_policy_effective_range',
            ),
        ]


class BudgetScope(models.Model):
    SCOPE_TYPES = [('tenant_global', 'Tenant global'), ('tenant_product', 'Tenant product')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.PROTECT, related_name='financial_budget_scopes'
    )
    product = models.ForeignKey(
        'products.ProductSystem', on_delete=models.PROTECT, related_name='financial_budget_scopes', null=True, blank=True
    )
    policy_version = models.ForeignKey(
        FinancialPolicyVersion, on_delete=models.PROTECT, related_name='budget_scopes'
    )
    scope_type = models.CharField(max_length=20, choices=SCOPE_TYPES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    limit_amount = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    reserved_exposure = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES, default=0)
    settled_exposure = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES, default=0)
    unresolved_exposure = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES, default=0)
    approved_liability = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES, default=0)
    request_limit = models.PositiveBigIntegerField(null=True, blank=True)
    reserved_request_count = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_budget_scopes'
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'product', 'policy_version', 'period_start'],
                condition=Q(product__isnull=False),
                name='financial_budget_product_period_unique',
            ),
            models.UniqueConstraint(
                fields=['organization', 'policy_version', 'period_start'],
                condition=Q(scope_type='tenant_global'),
                name='financial_budget_global_period_unique',
            ),
            models.CheckConstraint(check=Q(period_end__gt=models.F('period_start')), name='financial_budget_period_range'),
            models.CheckConstraint(check=Q(limit_amount__gte=0), name='financial_budget_limit_nonnegative'),
            models.CheckConstraint(
                check=Q(reserved_exposure__gte=0) & Q(settled_exposure__gte=0)
                & Q(unresolved_exposure__gte=0) & Q(approved_liability__gte=0),
                name='financial_budget_exposure_nonnegative',
            ),
            models.CheckConstraint(
                check=(Q(scope_type='tenant_global', product__isnull=True) | Q(scope_type='tenant_product', product__isnull=False)),
                name='financial_budget_scope_product_shape',
            ),
        ]
        indexes = [models.Index(fields=['organization', 'scope_type', 'period_start'])]


class VerifiedTariff(models.Model):
    STATES = [('draft', 'Draft'), ('verified', 'Verified'), ('superseded', 'Superseded'), ('retired', 'Retired')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=120)
    model_identifier = models.CharField(max_length=200)
    version = models.PositiveIntegerField()
    state = models.CharField(max_length=16, choices=STATES, default='draft')
    currency = models.CharField(max_length=3)
    input_unit_cost = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    output_unit_cost = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    unit_size = models.PositiveBigIntegerField()
    source_reference = models.TextField()
    source_hash = models.CharField(max_length=128)
    effective_from = models.DateTimeField(null=True, blank=True)
    effective_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_verified_tariffs'
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'model_identifier', 'version'], name='financial_tariff_version_unique'
            ),
            models.CheckConstraint(check=Q(input_unit_cost__gte=0), name='financial_tariff_input_nonnegative'),
            models.CheckConstraint(check=Q(output_unit_cost__gte=0), name='financial_tariff_output_nonnegative'),
            models.CheckConstraint(check=Q(unit_size__gt=0), name='financial_tariff_unit_positive'),
            models.CheckConstraint(
                check=Q(effective_until__isnull=True) | Q(effective_from__isnull=True) | Q(effective_until__gt=models.F('effective_from')),
                name='financial_tariff_effective_range',
            ),
        ]


class AdmissionDecision(models.Model):
    STATES = [('reserved', 'Reserved'), ('denied', 'Denied')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producer_registration = models.ForeignKey(ProducerRegistration, on_delete=models.PROTECT, related_name='admission_decisions')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.PROTECT, related_name='financial_admission_decisions')
    product = models.ForeignKey('products.ProductSystem', on_delete=models.PROTECT, related_name='financial_admission_decisions')
    invocation_id = models.UUIDField()
    material_request_hash = models.CharField(max_length=128)
    decision_state = models.CharField(max_length=16, choices=STATES)
    correlation_id = models.UUIDField()
    policy_version = models.ForeignKey(FinancialPolicyVersion, null=True, blank=True, on_delete=models.PROTECT, related_name='admission_decisions')
    tariff = models.ForeignKey(VerifiedTariff, null=True, blank=True, on_delete=models.PROTECT, related_name='admission_decisions')
    currency = models.CharField(max_length=3, blank=True)
    reserved_amount = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES, null=True, blank=True)
    denial_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_admission_decisions'
        constraints = [
            models.UniqueConstraint(fields=['producer_registration', 'organization', 'product', 'invocation_id'], name='financial_admission_identity_unique'),
            models.CheckConstraint(check=Q(reserved_amount__isnull=True) | Q(reserved_amount__gte=0), name='financial_admission_amount_nonnegative'),
        ]
        indexes = [models.Index(fields=['organization', 'product', 'created_at'])]


class FinancialReservation(models.Model):
    STATES = [('reserved', 'Reserved'), ('settled', 'Settled'), ('released', 'Released'), ('unresolved', 'Unresolved'), ('liability_recorded', 'Liability recorded')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admission_decision = models.OneToOneField(AdmissionDecision, on_delete=models.PROTECT, related_name='reservation')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.PROTECT, related_name='financial_reservations')
    product = models.ForeignKey('products.ProductSystem', on_delete=models.PROTECT, related_name='financial_reservations')
    policy_version = models.ForeignKey(FinancialPolicyVersion, on_delete=models.PROTECT, related_name='reservations')
    tariff = models.ForeignKey(VerifiedTariff, on_delete=models.PROTECT, related_name='reservations')
    currency = models.CharField(max_length=3)
    reserved_amount = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    state = models.CharField(max_length=24, choices=STATES, default='reserved')
    budget_period_start = models.DateTimeField()
    budget_period_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    state_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'financial_reservations'
        constraints = [
            models.CheckConstraint(check=Q(reserved_amount__gte=0), name='financial_reservation_amount_nonnegative'),
            models.CheckConstraint(check=Q(budget_period_end__gt=models.F('budget_period_start')), name='financial_reservation_period_range'),
        ]
        indexes = [models.Index(fields=['organization', 'state', 'budget_period_start'])]


class SettlementEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.ForeignKey(FinancialReservation, on_delete=models.PROTECT, related_name='settlements')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.PROTECT, related_name='financial_settlements')
    settlement_id = models.UUIDField()
    settlement_payload_hash = models.CharField(max_length=128)
    evidence_id = models.UUIDField(unique=True)
    evidence_class = models.CharField(max_length=4)
    provider_request_id = models.CharField(max_length=255, blank=True)
    source_owner = models.CharField(max_length=160)
    retention_classification = models.CharField(max_length=80)
    payload_hash = models.CharField(max_length=128)
    captured_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_settlement_evidence'
        constraints = [
            models.UniqueConstraint(fields=['reservation', 'settlement_id'], name='financial_settlement_identity_unique'),
            models.CheckConstraint(check=Q(evidence_class__in=['A', 'B', 'C', 'D', 'E', 'F']), name='financial_evidence_class_valid'),
        ]
        indexes = [models.Index(fields=['organization', 'created_at'])]


class ResolutionHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.ForeignKey(FinancialReservation, on_delete=models.PROTECT, related_name='resolution_history')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.PROTECT, related_name='financial_resolution_history')
    resolution_id = models.UUIDField()
    payload_hash = models.CharField(max_length=128)
    reason = models.TextField()
    evidence_references = models.JSONField(default=list)
    before_state = models.CharField(max_length=24)
    after_state = models.CharField(max_length=24)
    before_amount = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    after_amount = models.DecimalField(max_digits=MONEY_MAX_DIGITS, decimal_places=MONEY_DECIMAL_PLACES)
    actor_reference = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_resolution_history'
        constraints = [models.UniqueConstraint(fields=['reservation', 'resolution_id'], name='financial_resolution_identity_unique')]
        indexes = [models.Index(fields=['organization', 'created_at'])]


class FinancialAuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.PROTECT, related_name='financial_audit_events')
    event_type = models.CharField(max_length=100)
    actor_reference = models.CharField(max_length=160)
    correlation_id = models.UUIDField(null=True, blank=True)
    entity_type = models.CharField(max_length=100)
    entity_id = models.UUIDField()
    payload_hash = models.CharField(max_length=128)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_audit_events'
        indexes = [models.Index(fields=['organization', 'created_at']), models.Index(fields=['entity_type', 'entity_id'])]


class ProducerTenantGrant(models.Model):
    """Authoritative, explicitly scoped producer-to-tenant authority.

    This is deliberately separate from a producer's product scope: possession
    of an active producer credential never implies authority over an active
    organization.  Lifecycle transitions are represented by immutable events.
    """

    STATES = [('active', 'Active'), ('suspended', 'Suspended'), ('revoked', 'Revoked')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    producer_registration = models.ForeignKey(
        ProducerRegistration, on_delete=models.PROTECT, related_name='tenant_grants'
    )
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.PROTECT, related_name='financial_producer_grants'
    )
    product = models.ForeignKey(
        'products.ProductSystem', on_delete=models.PROTECT, related_name='financial_producer_grants'
    )
    operation = models.CharField(max_length=40)
    environment = models.CharField(max_length=20, choices=ProducerRegistration.ENVIRONMENTS)
    state = models.CharField(max_length=16, choices=STATES, default='active')
    version = models.PositiveIntegerField(default=1)
    effective_from = models.DateTimeField()
    effective_until = models.DateTimeField(null=True, blank=True)
    revocation_evidence_hash = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_producer_tenant_grants'
        constraints = [
            models.UniqueConstraint(
                fields=['producer_registration', 'organization', 'product', 'operation', 'environment', 'version'],
                name='financial_producer_tenant_grant_version_unique',
            ),
            models.CheckConstraint(
                check=Q(effective_until__isnull=True) | Q(effective_until__gt=models.F('effective_from')),
                name='financial_grant_effective_range',
            ),
        ]
        indexes = [models.Index(fields=['producer_registration', 'organization', 'product', 'state'])]


class ProducerTenantGrantLifecycleEvent(models.Model):
    """Append-only audit evidence for producer-to-tenant grant lifecycle."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grant = models.ForeignKey(ProducerTenantGrant, on_delete=models.PROTECT, related_name='lifecycle_events')
    state = models.CharField(max_length=16, choices=ProducerTenantGrant.STATES)
    actor_reference = models.CharField(max_length=160)
    evidence_hash = models.CharField(max_length=128)
    reason_code = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_producer_tenant_grant_events'
        ordering = ['created_at', 'id']
        indexes = [models.Index(fields=['grant', 'created_at'])]


class FinancialInvocationLedger(models.Model):
    """Immutable replay and authorization evidence for a signed capability."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capability_id = models.UUIDField(unique=True)
    producer_registration = models.ForeignKey(ProducerRegistration, on_delete=models.PROTECT)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.PROTECT)
    product = models.ForeignKey('products.ProductSystem', on_delete=models.PROTECT)
    grant = models.ForeignKey(ProducerTenantGrant, on_delete=models.PROTECT)
    invocation_id = models.UUIDField()
    material_request_hash = models.CharField(max_length=128)
    issuer_id = models.CharField(max_length=120)
    key_id = models.CharField(max_length=120)
    capability_version = models.PositiveSmallIntegerField(default=1)
    decision = models.OneToOneField(AdmissionDecision, null=True, blank=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'financial_invocation_ledger'
        constraints = [
            models.UniqueConstraint(
                fields=['producer_registration', 'organization', 'product', 'invocation_id'],
                name='financial_invocation_ledger_identity_unique',
            ),
        ]
