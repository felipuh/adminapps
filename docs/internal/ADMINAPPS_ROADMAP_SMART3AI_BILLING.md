# AdminApps Roadmap Smart3AI Billing

Estado: **COMPLETADO** ✅
Fecha base: 2026-03-24
Fecha cierre: 2026-03-24
Regla de continuidad: hasta cerrar este plan, no abrir frentes nuevos salvo bloqueos críticos.

## Vision
AdminApps sera el backoffice maestro de Smart3AI para:
- gestionar productos multi-tenant
- controlar suscripciones, modulos y habilitaciones por organizacion
- centralizar revenue total y por producto
- operar facturacion electronica y control financiero/contable
- servir como capa administrativa comun para productos actuales y futuros

Producto actual:
- ISO Smart

Productos futuros esperados:
- otros SaaS multi-tenant gestionados desde AdminApps

## Principios
- una sola fuente de verdad para planes, suscripciones, modulos y facturacion
- separacion clara entre producto, organizacion, suscripcion y documento fiscal
- compatibilidad multi-producto desde el modelo de datos
- compatibilidad multi-tenant desde el primer diseno
- cumplimiento fiscal de Costa Rica como baseline del modulo financiero

## Estado actual confirmado

### Backend fuerte
- auth y seguridad endurecidos
- permisos por rol cubiertos
- aislamiento cross-organization cubierto
- modelos de subscriptions ya existen
- modelos de products ya existen

### Gaps actuales
- dos configuraciones Django paralelas
- dashboard sin revenue real por producto
- subscriptions e invoices sin capa financiera formal
- modulo billing creado pero aun parcial
- sin integracion con Hacienda Costa Rica
- sin contabilidad operativa ni reportes fiscales

## Roadmap cerrado de trabajo

### Fase 0. Consolidacion tecnica
1. unificar configuracion Django activa sobre arquitectura apps.*
2. eliminar duplicidad root apps vs apps.*
3. dejar tests como red de seguridad antes de migracion estructural

### Fase 1. Billing foundation
1. crear app billing en apps.*
2. crear modelos:
   - FiscalProfile
   - ProductCatalog
   - ProductPrice
   - ElectronicInvoice
   - InvoiceLine
   - PaymentRecord
   - RevenueSnapshot
3. exponer endpoints base para consulta y dashboard financiero
4. agregar pruebas unitarias de reglas base
5. emitir factura desde organizacion/suscripcion
6. registrar pago y transicion pending -> paid

### Avance implementado a la fecha
- app billing creada en apps.*
- modelos base de billing implementados
- endpoints base de summary y revenue por producto implementados
- endpoint de emision de factura implementado
- endpoint de emision desde suscripcion activa implementado
- accion mark_paid implementada con PaymentRecord
- snapshot de revenue por organizacion y producto implementado
- ciclo de cobro por suscripcion implementado para suscripciones vencidas/fecha de cobro alcanzada
- batch de facturacion implementado para multiples organizaciones con reporte de procesadas, omitidas y errores
- comando Django para ejecucion manual del batch implementado
- dashboard backend con revenue por organizacion y timeline implementado
- cuentas por cobrar base implementadas
- compliance preview para Costa Rica implementado a nivel de payload interno
- validacion CAByS de 13 digitos implementada en billing
- pruebas iniciales de billing en verde

### Fase 2. Revenue por producto
1. revenue total plataforma
2. revenue por producto
3. revenue por organizacion
4. MRR, ARR, churn, trials por convertir
5. series temporales mensuales

### Fase 3. Costa Rica compliance
1. modelar emisor y configuracion fiscal CR
2. soportar IVA, exoneraciones y CAByS
3. generar estructura de comprobante electronico
4. integrar firma y estados de Hacienda
5. soportar notas de credito y estados tributarios

### Fase 4. Operacion financiera
1. pagos recibidos
2. conciliacion basica
3. cuentas por cobrar
4. aging de facturas
5. exportables para contador

### Fase 5. Frontend backoffice
1. dashboard financiero total
2. dashboard por producto
3. vista de documentos fiscales
4. vista de pagos y cobranza
5. alertas operativas

## Definicion funcional de producto
AdminApps debe controlar:
- que productos existen
- que organizacion consume que producto
- bajo que plan y precio
- que modulos tiene habilitados
- cuanto factura cada organizacion
- cuanto ingreso genera cada producto
- cuanto ingreso genera Smart3AI total

## Decision de modelado
La capa financiera debe nacer multi-producto. Aunque hoy solo exista ISO Smart, no se debe acoplar billing a un unico producto.

## Proximo corte de implementacion
1. ✅ preparar batch scheduler para ejecutar run_cycle sobre multiples organizaciones
2. ✅ agregar estados aceptado/rechazado de comprobante electronico
3. ✅ preparar XML/estructura formal de Hacienda Costa Rica
4. ✅ agregar notas de credito y conciliacion

## Estado final del módulo billing

### Backend (45/45 tests ✅)
- Modelos: FiscalProfile, ProductCatalog, ProductPrice, ElectronicInvoice, InvoiceLine, PaymentRecord, RevenueSnapshot
- Migraciones: 0001_initial, 0002_fiscalprofile_credentials, 0003_paymentrecord_notes
- Reportes recurrentes (MVP): RecurringReportSchedule + envio por email + ejecucion manual y programada
- Migraciones: 0001_initial, 0002_fiscalprofile_credentials, 0003_paymentrecord_notes, 0004_recurringreportschedule
- Hacienda CR: OAuth2 token (sandbox+prod), submit_invoice, check_status, XAdES-EPES firma digital
- Notas de crédito: create_credit_note_for_invoice, consecutivo NC, reversal de factura original
- Conciliación: register_pending_payment, confirm_payment_record, reject_payment_record, reconciliation summary
- Churn/trials: BillingChurnAnalyticsView, churn_rate, trial_conversion_rate, expiring_trials
- Dashboard por producto: ProductDashboardView con MRR/ARR/revenue/subscriptions por producto
- Alertas operativas: BillingAlertsView (overdue, hacienda_rejected, hacienda_stuck, trial_expiring, scheduler_error)
- Multi-producto: aislamiento confirmado por tests

### Frontend (build ✅)
- FinancePage: dashboard financiero completo con timeline, by-product chart, by-organization table
- MetricCards: Revenue neto, Cuentas por cobrar, Impuesto, MRR, ARR, Suscripciones, Churn Rate, Trials, Conversión
- Alertas operativas: banner contextual con severity-based coloring
- InvoiceDrawer: detalle completo, descarga XML, emitir nota de crédito inline
- Dashboard por producto: tabla con MRR/ARR/revenue/subscriptions/facturas
- Conciliación bancaria: summary grid + lista de pagos pendientes con confirmar/rechazar + modal Registrar Pago
- Batch modal: ejecutar batch de cobro para perfil fiscal + producto
- Scheduler panel: estado, próxima ejecución, log de ejecuciones, trigger manual
- Scheduler de reportes: programacion desde FinancePage, listado de horarios y ejecucion manual por horario
- api.jsx: todos los endpoints cubiertos (14 métodos billingService)
