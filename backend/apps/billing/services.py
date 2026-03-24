from decimal import Decimal
from calendar import monthrange
import json
import logging
import xml.etree.ElementTree as ET

from django.db import transaction
from django.utils import timezone

from apps.organizations.models import Organization
from .models import ElectronicInvoice, InvoiceLine, PaymentRecord, RevenueSnapshot

logger = logging.getLogger(__name__)

_CR_BASE_NS = 'https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.3'

_DOCUMENT_TYPE_ROOT = {
    '01': ('FacturaElectronica', 'facturaElectronica'),
    '03': ('NotaCreditoElectronica', 'notaCreditoElectronica'),
    '04': ('TiqueteElectronico', 'tiqueteElectronico'),
}


def _tax_id_type_code(tax_id):
    """Return CR identification type code: 01=física, 02=jurídica, 03=NITE/other."""
    digits = ''.join(c for c in (tax_id or '') if c.isdigit())
    if len(digits) == 9:
        return '01'
    if len(digits) == 10:
        return '02'
    return '03'


def generate_invoice_xml(invoice):
    """Generate CR FacturaElectronica v4.3 XML string for the given invoice."""
    doc_type = invoice.document_type_code or '01'
    root_tag, schema_name = _DOCUMENT_TYPE_ROOT.get(doc_type, ('FacturaElectronica', 'facturaElectronica'))
    ns = f'{_CR_BASE_NS}/{schema_name}'
    xsi = 'http://www.w3.org/2001/XMLSchema-instance'
    ET.register_namespace('', ns)
    ET.register_namespace('xsi', xsi)

    root = ET.Element(f'{{{ns}}}{root_tag}')
    root.set(f'{{{xsi}}}schemaLocation', f'{ns} {ns}.xsd')

    def sub(parent, tag, text=None):
        el = ET.SubElement(parent, f'{{{ns}}}{tag}')
        if text is not None:
            el.text = str(text)
        return el

    fp = invoice.fiscal_profile
    issue_dt = (invoice.issued_at or timezone.now()).astimezone(timezone.get_current_timezone())
    tz_offset = issue_dt.strftime('%z') or '-0600'
    issue_iso = issue_dt.strftime('%Y-%m-%dT%H:%M:%S') + tz_offset[:3] + ':' + tz_offset[3:]

    sub(root, 'Clave', invoice.numeric_key or '')
    sub(root, 'CodigoActividad', fp.tax_activity_code or '620900')
    sub(root, 'NumeroConsecutivo', invoice.consecutive_number or '')
    sub(root, 'FechaEmision', issue_iso)

    # Emisor
    emisor = sub(root, 'Emisor')
    sub(emisor, 'Nombre', fp.legal_name)
    id_emisor = sub(emisor, 'Identificacion')
    sub(id_emisor, 'Tipo', _tax_id_type_code(fp.tax_id))
    sub(id_emisor, 'Numero', ''.join(c for c in fp.tax_id if c.isdigit()))
    if fp.commercial_name:
        sub(emisor, 'NombreComercial', fp.commercial_name)
    ubicacion = sub(emisor, 'Ubicacion')
    sub(ubicacion, 'Provincia', '1')
    sub(ubicacion, 'Canton', '01')
    sub(ubicacion, 'Distrito', '01')
    sub(ubicacion, 'OtrasSenas', fp.address or 'Costa Rica')
    if fp.phone:
        tel = sub(emisor, 'Telefono')
        sub(tel, 'CodigoPais', '506')
        sub(tel, 'NumTelefono', ''.join(c for c in fp.phone if c.isdigit())[:8])
    sub(emisor, 'CorreoElectronico', fp.email)

    # Receptor
    receptor = sub(root, 'Receptor')
    sub(receptor, 'Nombre', invoice.receiver_name or 'Consumidor Final')
    if invoice.receiver_tax_id:
        id_receptor = sub(receptor, 'Identificacion')
        sub(id_receptor, 'Tipo', _tax_id_type_code(invoice.receiver_tax_id))
        sub(id_receptor, 'Numero', ''.join(c for c in invoice.receiver_tax_id if c.isdigit()))
    if invoice.receiver_email:
        sub(receptor, 'CorreoElectronico', invoice.receiver_email)

    sub(root, 'CondicionVenta', invoice.sale_condition or '01')
    sub(root, 'MedioPago', invoice.payment_method_code or '03')

    # DetalleServicio
    detalle = sub(root, 'DetalleServicio')
    for idx, line in enumerate(invoice.lines.all(), start=1):
        linea = sub(detalle, 'LineaDetalle')
        sub(linea, 'NumeroLinea', str(idx))
        if line.cabys_code:
            codigo_el = sub(linea, 'Codigo')
            sub(codigo_el, 'Tipo', '04')
            sub(codigo_el, 'Codigo', line.cabys_code)
        sub(linea, 'Cantidad', str(line.quantity))
        sub(linea, 'UnidadMedida', 'Sp')
        sub(linea, 'Detalle', line.description)
        sub(linea, 'PrecioUnitario', str(line.unit_price))
        sub(linea, 'MontoTotal', str(line.subtotal))
        if line.discount_amount and line.discount_amount > Decimal('0'):
            dcto = sub(linea, 'Descuento')
            sub(dcto, 'MontoDescuento', str(line.discount_amount))
            sub(dcto, 'NaturalezaDescuento', 'Descuento comercial')
        taxable_base = line.subtotal - line.discount_amount
        sub(linea, 'SubTotal', str(taxable_base))
        sub(linea, 'BaseImponible', str(taxable_base))
        if line.tax_rate > Decimal('0'):
            tarifa_code = '08' if line.tax_rate == Decimal('13.00') else '07'
            imp = sub(linea, 'Impuesto')
            sub(imp, 'Codigo', '01')
            sub(imp, 'CodigoTarifa', tarifa_code)
            sub(imp, 'Tarifa', str(line.tax_rate))
            sub(imp, 'Monto', str(line.tax_amount))
        sub(linea, 'ImpuestoNeto', str(line.tax_amount))
        sub(linea, 'MontoTotalLinea', str(line.total))

    # ResumenFactura
    resumen = sub(root, 'ResumenFactura')
    tipo_moneda = sub(resumen, 'CodigoTipoMoneda')
    sub(tipo_moneda, 'CodigoMoneda', invoice.currency)
    sub(tipo_moneda, 'TipoCambio', '1')
    sub(resumen, 'TotalServGravados', str(invoice.subtotal))
    sub(resumen, 'TotalServExentos', '0.00')
    sub(resumen, 'TotalServExonerado', '0.00')
    sub(resumen, 'TotalMercanciasGravadas', '0.00')
    sub(resumen, 'TotalMercanciasExentas', '0.00')
    sub(resumen, 'TotalMercExonerada', '0.00')
    sub(resumen, 'TotalGravado', str(invoice.subtotal))
    sub(resumen, 'TotalExento', '0.00')
    sub(resumen, 'TotalExonerado', '0.00')
    sub(resumen, 'TotalVenta', str(invoice.subtotal))
    sub(resumen, 'TotalDescuentos', str(invoice.discount_total))
    sub(resumen, 'TotalVentaNeta', str(invoice.subtotal - invoice.discount_total))
    sub(resumen, 'TotalImpuesto', str(invoice.tax_total))
    sub(resumen, 'TotalIVADevuelto', '0.00')
    sub(resumen, 'TotalOtrosCargos', '0.00')
    sub(resumen, 'TotalComprobante', str(invoice.total))

    raw = ET.tostring(root, encoding='unicode')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{raw}'


def _resolve_subscription(organization, subscription=None):
    if subscription is not None:
        return subscription
    return organization.subscription


def _resolve_product_price(product, product_price=None, subscription=None):
    if product_price is not None:
        return product_price

    prices = product.prices.filter(is_active=True)
    if subscription is not None:
        prices = prices.filter(billing_cycle=subscription.plan.billing_cycle)
        if subscription.plan.currency:
            prices = prices.filter(currency=subscription.plan.currency)

    product_price = prices.order_by('amount', 'created_at').first()
    if product_price is None:
        raise ValueError('No existe un precio activo compatible para el producto seleccionado.')
    if product_price.product_id != product.id:
        raise ValueError('El precio seleccionado no pertenece al producto indicado.')
    if product_price.cabys_code and (not product_price.cabys_code.isdigit() or len(product_price.cabys_code) != 13):
        raise ValueError('El codigo CAByS del precio debe tener 13 digitos numericos.')
    return product_price


def _require_costa_rica_compliance(fiscal_profile, organization, product_price):
    if fiscal_profile.country != 'CR':
        return
    if not organization.tax_id:
        raise ValueError('La organizacion debe tener identificacion fiscal para emitir comprobantes en Costa Rica.')
    if not product_price.cabys_code or not product_price.has_valid_cabys_code:
        raise ValueError('El precio del producto debe tener un codigo CAByS valido de 13 digitos.')


def _normalize_tax_id_for_key(tax_id):
    digits = ''.join(char for char in (tax_id or '') if char.isdigit())
    return digits.zfill(12)[-12:]


def _build_numeric_key(*, invoice):
    issue_date = (invoice.issued_at or timezone.now()).astimezone(timezone.get_current_timezone())
    date_part = issue_date.strftime('%d%m%y')
    emitter_id = _normalize_tax_id_for_key(invoice.fiscal_profile.tax_id)
    random_security = f'{invoice.fiscal_profile.invoice_sequence:08d}'[-8:]
    return f'506{date_part}{emitter_id}{invoice.consecutive_number}1{random_security}'


def prepare_invoice_for_hacienda(*, invoice):
    if invoice.fiscal_profile.country != 'CR':
        raise ValueError('La preparacion formal de comprobante aplica solo para Costa Rica.')
    if not invoice.consecutive_number:
        invoice.consecutive_number = invoice.fiscal_profile.next_consecutive_number(invoice.document_type_code)
    if not invoice.numeric_key:
        invoice.numeric_key = _build_numeric_key(invoice=invoice)

    xml_str = generate_invoice_xml(invoice)
    signed_xml = xml_str

    # Sign XML with p12 certificate if configured
    fp = invoice.fiscal_profile
    if fp.certificate_file:
        try:
            from .xml_signer import sign_invoice_xml
            signed_xml = sign_invoice_xml(xml_str, fp.certificate_file, fp.certificate_pin or '')
        except ImportError:
            logger.warning('[billing] signxml/lxml no instalado — XML guardado sin firma digital.')
        except Exception as exc:
            logger.error('[billing] Error al firmar XML para factura %s: %s', invoice.id, exc)
            raise ValueError(f'Error al firmar el XML: {exc}')

    invoice.xml_payload = signed_xml
    invoice.hacienda_status = 'processing'
    invoice.submitted_at = timezone.now()
    invoice.save(
        update_fields=['consecutive_number', 'numeric_key', 'xml_payload', 'hacienda_status', 'submitted_at', 'updated_at']
    )

    # Submit to Hacienda ATV if credentials are configured
    if fp.has_hacienda_credentials:
        try:
            from .hacienda_client import HaciendaClient
            client = HaciendaClient(fp)
            client.submit_invoice(invoice, signed_xml)
        except Exception as exc:
            # Log and continue — document is saved in 'processing' state for retry
            logger.error('[billing] Envío a Hacienda falló para factura %s: %s', invoice.id, exc)

    return invoice, signed_xml


def poll_hacienda_status(*, invoice):
    """
    Query Hacienda ATV for the current status of a submitted invoice and
    persist the result.  Returns the updated invoice.

    Raises ValueError when the invoice has no clave numérica or the
    FiscalProfile lacks Hacienda credentials.
    """
    fp = invoice.fiscal_profile
    if not invoice.numeric_key:
        raise ValueError('La factura no tiene clave numérica para consultar en Hacienda.')
    if not fp.has_hacienda_credentials:
        raise ValueError('El perfil fiscal no tiene credenciales de Hacienda configuradas.')

    from .hacienda_client import HaciendaClient
    client = HaciendaClient(fp)
    result = client.check_status(invoice.numeric_key)

    return update_hacienda_status(
        invoice=invoice,
        status_value=result['hacienda_status'],
        message=result.get('message', ''),
        track_id=result.get('track_id', ''),
    )


def update_hacienda_status(*, invoice, status_value, message='', track_id=''):
    valid_statuses = {'processing', 'accepted', 'rejected', 'error'}
    if status_value not in valid_statuses:
        raise ValueError('Estado de Hacienda invalido.')

    invoice.hacienda_status = status_value
    invoice.hacienda_message = message
    if track_id:
        invoice.hacienda_track_id = track_id
    invoice.responded_at = timezone.now()

    if status_value == 'accepted' and invoice.status == 'pending':
        invoice.status = 'accepted'
    elif status_value in {'rejected', 'error'} and invoice.status == 'accepted':
        invoice.status = 'pending'

    invoice.save(
        update_fields=[
            'hacienda_status', 'hacienda_message', 'hacienda_track_id',
            'responded_at', 'status', 'updated_at',
        ]
    )
    return invoice


def _add_months(date_value, months):
    month = date_value.month - 1 + months
    year = date_value.year + month // 12
    month = month % 12 + 1
    day = min(date_value.day, monthrange(year, month)[1])
    return date_value.replace(year=year, month=month, day=day)


def _cycle_delta_date(base_date, billing_cycle):
    if billing_cycle == 'monthly':
        return _add_months(base_date, 1)
    if billing_cycle == 'quarterly':
        return _add_months(base_date, 3)
    return _add_months(base_date, 12)


def _advance_subscription_period(subscription, issue_date):
    current_date = issue_date.date()
    next_billing_date = subscription.next_billing_date or current_date
    next_cycle_date = _cycle_delta_date(next_billing_date, subscription.plan.billing_cycle)

    subscription.current_period_start = timezone.make_aware(
        timezone.datetime.combine(next_billing_date, timezone.datetime.min.time()),
        timezone.get_current_timezone(),
    )
    subscription.current_period_end = timezone.make_aware(
        timezone.datetime.combine(next_cycle_date, timezone.datetime.min.time()),
        timezone.get_current_timezone(),
    )
    subscription.next_billing_date = next_cycle_date
    subscription.save(update_fields=['current_period_start', 'current_period_end', 'next_billing_date', 'updated_at'])


def _get_snapshot_for_invoice(invoice):
    snapshot_date = invoice.issued_at.date() if invoice.issued_at else timezone.localdate()
    snapshot, _ = RevenueSnapshot.objects.get_or_create(
        snapshot_date=snapshot_date,
        product=invoice.product,
        organization=invoice.organization,
        currency=invoice.currency,
        defaults={
            'gross_revenue': Decimal('0.00'),
            'net_revenue': Decimal('0.00'),
            'tax_collected': Decimal('0.00'),
            'invoices_issued': 0,
            'invoices_paid': 0,
        },
    )
    return snapshot


@transaction.atomic
def issue_invoice_for_organization(
    *,
    fiscal_profile,
    organization,
    product,
    product_price,
    issued_by=None,
    subscription=None,
    quantity=Decimal('1.00'),
    discount_amount=Decimal('0.00'),
    due_date=None,
    mark_paid=False,
):
    subscription = _resolve_subscription(organization, subscription)
    product_price = _resolve_product_price(product, product_price, subscription)
    _require_costa_rica_compliance(fiscal_profile, organization, product_price)
    locked_profile = type(fiscal_profile).objects.select_for_update().get(pk=fiscal_profile.pk)
    invoice_number = locked_profile.consume_invoice_sequence()
    now = timezone.now()

    invoice = ElectronicInvoice.objects.create(
        fiscal_profile=locked_profile,
        organization=organization,
        subscription=subscription,
        product=product,
        product_price=product_price,
        invoice_number=invoice_number,
        currency=product_price.currency,
        receiver_name=organization.legal_name or organization.name,
        receiver_tax_id=organization.tax_id,
        receiver_email=organization.email,
        sale_condition='01' if mark_paid else '02',
        payment_method_code='03',
        status='paid' if mark_paid else 'pending',
        issued_at=now,
        due_date=due_date or now.date(),
        paid_at=now if mark_paid else None,
        metadata={
            'issued_by_user_id': str(issued_by.id) if issued_by else None,
            'source': 'billing.issue_invoice_for_organization',
        },
    )

    line = InvoiceLine.objects.create(
        invoice=invoice,
        description=f'{product.name} - {product_price.name}',
        cabys_code=product_price.cabys_code,
        quantity=quantity,
        unit_price=product_price.amount,
        discount_amount=discount_amount,
        tax_rate=product_price.tax_rate,
        metadata={'billing_cycle': product_price.billing_cycle},
    )

    invoice.recalculate_totals()
    invoice.save(update_fields=['subtotal', 'tax_total', 'discount_total', 'total', 'updated_at'])

    snapshot = _get_snapshot_for_invoice(invoice)
    snapshot.accumulate_invoice(invoice, mark_paid=mark_paid)
    snapshot.save(
        update_fields=[
            'gross_revenue', 'net_revenue', 'tax_collected',
            'invoices_issued', 'invoices_paid', 'updated_at',
        ]
    )

    payment_record = None
    if mark_paid:
        payment_record = PaymentRecord.objects.create(
            invoice=invoice,
            organization=organization,
            amount=invoice.total,
            currency=invoice.currency,
            method='other',
            reference=invoice_number,
            status='confirmed',
            paid_at=invoice.paid_at,
            metadata={
                'source': 'billing.issue_invoice_for_organization',
            },
        )

    if subscription is not None:
        _advance_subscription_period(subscription, invoice.issued_at)

    return invoice, line, snapshot, payment_record


@transaction.atomic
def create_credit_note_for_invoice(*, original_invoice, reason, issued_by=None):
    if original_invoice.status not in {'paid', 'accepted'}:
        raise ValueError('Solo se pueden crear notas de credito para facturas aceptadas o pagadas.')

    fp = original_invoice.fiscal_profile
    locked_fp = type(fp).objects.select_for_update().get(pk=fp.pk)
    note_number = locked_fp.consume_credit_note_sequence()
    now = timezone.now()

    note = ElectronicInvoice.objects.create(
        fiscal_profile=fp,
        organization=original_invoice.organization,
        subscription=original_invoice.subscription,
        product=original_invoice.product,
        product_price=original_invoice.product_price,
        invoice_number=note_number,
        document_type_code='03',
        currency=original_invoice.currency,
        receiver_name=original_invoice.receiver_name,
        receiver_tax_id=original_invoice.receiver_tax_id,
        receiver_email=original_invoice.receiver_email,
        sale_condition=original_invoice.sale_condition,
        payment_method_code=original_invoice.payment_method_code,
        status='pending',
        issued_at=now,
        due_date=now.date(),
        metadata={
            'issued_by_user_id': str(issued_by.id) if issued_by else None,
            'source': 'billing.create_credit_note_for_invoice',
            'original_invoice_id': str(original_invoice.id),
            'original_invoice_number': original_invoice.invoice_number,
            'reason': reason,
        },
    )

    for original_line in original_invoice.lines.all():
        InvoiceLine.objects.create(
            invoice=note,
            description=f'[NC] {original_line.description}',
            cabys_code=original_line.cabys_code,
            quantity=original_line.quantity,
            unit_price=original_line.unit_price,
            discount_amount=original_line.discount_amount,
            tax_rate=original_line.tax_rate,
            metadata={
                'original_line_id': str(original_line.id),
                'credit_note_reason': reason,
            },
        )

    note.recalculate_totals()
    note.save(update_fields=['subtotal', 'tax_total', 'discount_total', 'total', 'updated_at'])

    snapshot = _get_snapshot_for_invoice(original_invoice)
    snapshot.gross_revenue -= original_invoice.subtotal
    snapshot.net_revenue -= original_invoice.total
    snapshot.tax_collected -= original_invoice.tax_total
    snapshot.invoices_issued = max(0, snapshot.invoices_issued - 1)
    if original_invoice.status == 'paid':
        snapshot.invoices_paid = max(0, snapshot.invoices_paid - 1)
    snapshot.save(
        update_fields=['gross_revenue', 'net_revenue', 'tax_collected', 'invoices_issued', 'invoices_paid', 'updated_at']
    )

    original_invoice.metadata = {
        **original_invoice.metadata,
        'credit_note_id': str(note.id),
        'credit_note_number': note_number,
    }
    original_invoice.status = 'reversed'
    original_invoice.save(update_fields=['status', 'metadata', 'updated_at'])

    return note, snapshot


@transaction.atomic
def record_invoice_payment(*, invoice, method, reference='', paid_at=None, metadata=None):
    if invoice.status == 'paid':
        raise ValueError('La factura ya se encuentra pagada.')

    paid_timestamp = paid_at or timezone.now()
    invoice.status = 'paid'
    invoice.paid_at = paid_timestamp
    invoice.save(update_fields=['status', 'paid_at', 'updated_at'])

    payment = PaymentRecord.objects.create(
        invoice=invoice,
        organization=invoice.organization,
        amount=invoice.total,
        currency=invoice.currency,
        method=method,
        reference=reference,
        status='confirmed',
        paid_at=paid_timestamp,
        metadata=metadata or {},
    )

    snapshot = _get_snapshot_for_invoice(invoice)
    snapshot.register_payment()
    snapshot.save(update_fields=['invoices_paid', 'updated_at'])

    return invoice, payment, snapshot


@transaction.atomic
def run_subscription_billing_cycle(*, fiscal_profile, organization, product, product_price=None, issued_by=None, today=None, mark_paid=False):
    subscription = organization.subscription
    if subscription is None:
        raise ValueError('La organizacion no tiene una suscripcion asociada.')
    if not subscription.is_active:
        raise ValueError('La suscripcion no esta activa para facturacion.')

    reference_date = today or timezone.localdate()
    billing_date = subscription.next_billing_date or reference_date
    if billing_date > reference_date:
        raise ValueError('La suscripcion aun no alcanza su fecha de cobro.')

    return issue_invoice_for_organization(
        fiscal_profile=fiscal_profile,
        organization=organization,
        product=product,
        product_price=product_price,
        issued_by=issued_by,
        subscription=subscription,
        due_date=billing_date,
        mark_paid=mark_paid,
    )


def run_billing_cycle_batch(*, fiscal_profile, product, product_price=None, organization_ids=None, issued_by=None, today=None, mark_paid=False):
    reference_date = today or timezone.localdate()
    queryset = Organization.objects.filter(subscription__isnull=False)

    if organization_ids:
        queryset = queryset.filter(id__in=organization_ids)

    queryset = queryset.select_related('subscription__plan').order_by('name')

    report = {
        'run_date': str(reference_date),
        'processed': [],
        'skipped': [],
        'errors': [],
    }

    for organization in queryset:
        subscription = organization.subscription
        if subscription is None:
            report['skipped'].append({
                'organization_id': str(organization.id),
                'organization_name': organization.name,
                'reason': 'missing_subscription',
            })
            continue

        if not subscription.is_active:
            report['skipped'].append({
                'organization_id': str(organization.id),
                'organization_name': organization.name,
                'reason': 'inactive_subscription',
            })
            continue

        billing_date = subscription.next_billing_date or reference_date
        if billing_date > reference_date:
            report['skipped'].append({
                'organization_id': str(organization.id),
                'organization_name': organization.name,
                'reason': 'not_due_yet',
                'next_billing_date': str(billing_date),
            })
            continue

        try:
            invoice, _, _, _ = run_subscription_billing_cycle(
                fiscal_profile=fiscal_profile,
                organization=organization,
                product=product,
                product_price=product_price,
                issued_by=issued_by,
                today=reference_date,
                mark_paid=mark_paid,
            )
        except ValueError as exc:
            report['errors'].append({
                'organization_id': str(organization.id),
                'organization_name': organization.name,
                'error': str(exc),
            })
            continue

        report['processed'].append({
            'organization_id': str(organization.id),
            'organization_name': organization.name,
            'invoice_id': str(invoice.id),
            'invoice_number': invoice.invoice_number,
            'status': invoice.status,
            'total': str(invoice.total),
        })

    report['summary'] = {
        'processed_count': len(report['processed']),
        'skipped_count': len(report['skipped']),
        'error_count': len(report['errors']),
    }
    return report


# ---------------------------------------------------------------------------
# Bank reconciliation
# ---------------------------------------------------------------------------

def register_pending_payment(*, invoice, method, reference='', amount, notes=''):
    """
    Register a payment that has been reported by the customer but is not yet
    confirmed by the bank.  The invoice is NOT marked as paid until the
    payment is confirmed.

    Returns the created PaymentRecord (status='pending').
    """
    if invoice.status == 'paid':
        raise ValueError('La factura ya está pagada.')

    return PaymentRecord.objects.create(
        invoice=invoice,
        organization=invoice.organization,
        amount=amount,
        currency=invoice.currency,
        method=method,
        reference=reference,
        notes=notes,
        status='pending',
    )


def confirm_payment_record(*, payment, notes=''):
    """
    Confirm a pending PaymentRecord.  Marks the linked invoice as paid and
    updates the revenue snapshot.

    Returns (invoice, payment, snapshot).
    Raises ValueError if the payment is not in 'pending' state.
    """
    if payment.status != 'pending':
        raise ValueError(f'Solo se pueden confirmar pagos en estado pendiente (estado actual: {payment.status}).')

    invoice = payment.invoice

    if notes:
        payment.notes = (payment.notes + '\n' + notes).strip()
    payment.status = 'confirmed'
    payment.paid_at = timezone.now()
    payment.save(update_fields=['status', 'paid_at', 'notes', 'updated_at'])

    if invoice.status != 'paid':
        invoice.status = 'paid'
        invoice.paid_at = payment.paid_at
        invoice.save(update_fields=['status', 'paid_at', 'updated_at'])

        snapshot = _get_snapshot_for_invoice(invoice)
        snapshot.register_payment()
        snapshot.save(update_fields=['invoices_paid', 'updated_at'])
    else:
        snapshot = _get_snapshot_for_invoice(invoice)

    return invoice, payment, snapshot


def reject_payment_record(*, payment, notes=''):
    """
    Mark a PaymentRecord as failed/rejected (e.g. bank returned the transfer).

    Returns the updated PaymentRecord.
    """
    if payment.status not in ('pending', 'confirmed'):
        raise ValueError(f'No se puede rechazar un pago en estado {payment.status}.')

    if notes:
        payment.notes = (payment.notes + '\n' + notes).strip()
    payment.status = 'failed'
    payment.save(update_fields=['status', 'notes', 'updated_at'])
    return payment


def get_reconciliation_summary(*, date_from=None, date_to=None):
    """
    Return a reconciliation summary dict with:
        pending_payments    — PaymentRecord.status='pending' count + amount
        confirmed_payments  — PaymentRecord.status='confirmed' count + amount
        overdue_invoices    — invoices past due_date with no confirmed payment
        unmatched_invoices  — invoices in pending/accepted with no any payment
    """
    from django.db.models import Count, Sum, Q
    from django.db.models.functions import Coalesce

    qs = PaymentRecord.objects.all()
    invoice_qs = ElectronicInvoice.objects.exclude(status__in=['paid', 'reversed'])

    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
        invoice_qs = invoice_qs.filter(issued_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
        invoice_qs = invoice_qs.filter(issued_at__date__lte=date_to)

    from decimal import Decimal as _D
    today = timezone.localdate()

    def _agg(status_val):
        agg = qs.filter(status=status_val).aggregate(
            cnt=Count('id'), total=Sum('amount')
        )
        return agg['cnt'] or 0, agg['total'] or _D('0.00')

    pending_cnt, pending_amt = _agg('pending')
    confirmed_cnt, confirmed_amt = _agg('confirmed')

    # Overdue: due_date is set, past today, invoice not paid
    overdue_qs = invoice_qs.filter(due_date__lt=today, due_date__isnull=False)
    overdue_agg = overdue_qs.aggregate(cnt=Count('id'), total=Sum('total'))
    overdue_cnt = overdue_agg['cnt'] or 0
    overdue_amt = overdue_agg['total'] or _D('0.00')

    # Unmatched: no PaymentRecord at all
    unmatched_cnt = invoice_qs.filter(payments__isnull=True).count()

    return {
        'pending_payments': pending_cnt,
        'pending_amount': pending_amt,
        'confirmed_payments': confirmed_cnt,
        'confirmed_amount': confirmed_amt,
        'overdue_invoices': overdue_cnt,
        'overdue_amount': overdue_amt,
        'unmatched_invoices': unmatched_cnt,
    }
