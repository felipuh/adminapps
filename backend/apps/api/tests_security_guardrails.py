import importlib
import inspect

from django.test import SimpleTestCase
from rest_framework import serializers as drf_serializers


SERIALIZER_MODULES = [
    'apps.billing.serializers',
    'apps.organizations.serializers',
    'apps.products.serializers',
    'apps.subscriptions.serializers',
    'apps.users.serializers',
]


class SerializerExposureGuardrailTests(SimpleTestCase):
    def test_model_serializers_do_not_use_fields_all(self):
        for module_name in SERIALIZER_MODULES:
            module = importlib.import_module(module_name)
            for _, serializer_class in inspect.getmembers(module, inspect.isclass):
                if not issubclass(serializer_class, drf_serializers.ModelSerializer):
                    continue
                meta = getattr(serializer_class, 'Meta', None)
                if not meta or not hasattr(meta, 'model'):
                    continue
                fields = getattr(meta, 'fields', None)
                exclude = getattr(meta, 'exclude', None)
                self.assertTrue(
                    fields is not None or exclude is not None,
                    f'{serializer_class.__name__} must declare explicit fields or exclude.',
                )
                self.assertNotEqual(fields, '__all__', f'{serializer_class.__name__} must not use fields="__all__".')
