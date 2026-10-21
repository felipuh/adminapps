"""Named subscription resources must precede the root detail route."""

from django.test import SimpleTestCase
from django.urls import resolve

from apps.subscriptions.views import InvoiceViewSet, PaymentMethodViewSet


class SubscriptionRouteTests(SimpleTestCase):
    def test_invoice_list_reaches_invoice_viewset(self):
        match = resolve('/api/subscriptions/invoices/')
        self.assertIs(match.func.cls, InvoiceViewSet)

    def test_payment_method_list_reaches_payment_method_viewset(self):
        match = resolve('/api/subscriptions/payment-methods/')
        self.assertIs(match.func.cls, PaymentMethodViewSet)
