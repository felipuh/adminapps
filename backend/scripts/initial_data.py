"""
Script para crear datos iniciales de Admin Apps
Ejecutar con: python manage.py shell < scripts/initial_data.py
"""
from apps.products.models import ISOStandard
from decimal import Decimal

print("=" * 60)
print("CREANDO ESTÁNDARES ISO DISPONIBLES")
print("=" * 60)

# ISO 9001 - Base
iso_9001, created = ISOStandard.objects.get_or_create(
    code='ISO9001',
    defaults={
        'name': 'Calidad',
        'full_name': 'ISO 9001:2015 - Sistemas de Gestión de la Calidad',
        'version': '2015',
        'description': 'Estándar internacional para sistemas de gestión de calidad. Proporciona orientación y herramientas para empresas que quieren asegurar que sus productos y servicios cumplen consistentemente con los requisitos del cliente.',
        'icon': 'shield-check',
        'color': '#3B82F6',
        'status': 'active',
        'is_base': True,
        'monthly_price': Decimal('0.00'),  # Incluido en el plan base
        'annual_price': Decimal('0.00'),
        'display_order': 1,
        'clauses_count': 10,
    }
)
print(f"{'✓ Creado' if created else '→ Ya existe'}: {iso_9001}")

# ISO 14001 - Ambiental
iso_14001, created = ISOStandard.objects.get_or_create(
    code='ISO14001',
    defaults={
        'name': 'Ambiental',
        'full_name': 'ISO 14001:2015 - Sistemas de Gestión Ambiental',
        'version': '2015',
        'description': 'Marco para un sistema de gestión ambiental efectivo. Ayuda a las organizaciones a mejorar su desempeño ambiental mediante el uso más eficiente de recursos y la reducción de residuos.',
        'icon': 'leaf',
        'color': '#10B981',
        'status': 'development',
        'is_base': False,
        'monthly_price': Decimal('299.00'),
        'annual_price': Decimal('2990.00'),
        'display_order': 2,
        'clauses_count': 10,
    }
)
print(f"{'✓ Creado' if created else '→ Ya existe'}: {iso_14001}")

# ISO 45001 - Seguridad y Salud
iso_45001, created = ISOStandard.objects.get_or_create(
    code='ISO45001',
    defaults={
        'name': 'Seguridad y Salud',
        'full_name': 'ISO 45001:2018 - Sistemas de Gestión de Seguridad y Salud en el Trabajo',
        'version': '2018',
        'description': 'Estándar internacional para sistemas de gestión de seguridad y salud ocupacional. Proporciona un marco para gestionar los riesgos y oportunidades de SST.',
        'icon': 'hard-hat',
        'color': '#F59E0B',
        'status': 'development',
        'is_base': False,
        'monthly_price': Decimal('299.00'),
        'annual_price': Decimal('2990.00'),
        'display_order': 3,
        'clauses_count': 10,
    }
)
print(f"{'✓ Creado' if created else '→ Ya existe'}: {iso_45001}")

# ISO 27001 - Seguridad de la Información
iso_27001, created = ISOStandard.objects.get_or_create(
    code='ISO27001',
    defaults={
        'name': 'Seguridad de la Información',
        'full_name': 'ISO/IEC 27001:2022 - Sistemas de Gestión de Seguridad de la Información',
        'version': '2022',
        'description': 'Estándar internacional para la gestión de la seguridad de la información. Proporciona requisitos para establecer, implementar, mantener y mejorar continuamente un SGSI.',
        'icon': 'lock',
        'color': '#6366F1',
        'status': 'development',
        'is_base': False,
        'monthly_price': Decimal('399.00'),
        'annual_price': Decimal('3990.00'),
        'display_order': 4,
        'clauses_count': 10,
    }
)
print(f"{'✓ Creado' if created else '→ Ya existe'}: {iso_27001}")

# ISO 22000 - Seguridad Alimentaria
iso_22000, created = ISOStandard.objects.get_or_create(
    code='ISO22000',
    defaults={
        'name': 'Seguridad Alimentaria',
        'full_name': 'ISO 22000:2018 - Sistemas de Gestión de Inocuidad de los Alimentos',
        'version': '2018',
        'description': 'Estándar internacional que especifica los requisitos para un sistema de gestión de inocuidad de los alimentos en la cadena alimentaria.',
        'icon': 'utensils',
        'color': '#EC4899',
        'status': 'development',
        'is_base': False,
        'monthly_price': Decimal('349.00'),
        'annual_price': Decimal('3490.00'),
        'display_order': 5,
        'clauses_count': 10,
    }
)
print(f"{'✓ Creado' if created else '→ Ya existe'}: {iso_22000}")

# ISO 42001 - Inteligencia Artificial
iso_42001, created = ISOStandard.objects.get_or_create(
    code='ISO42001',
    defaults={
        'name': 'Inteligencia Artificial',
        'full_name': 'ISO/IEC 42001:2023 - Sistemas de Gestión de Inteligencia Artificial',
        'version': '2023',
        'description': 'Primer estándar internacional para sistemas de gestión de IA. Proporciona un marco para el desarrollo, provisión y uso responsable de sistemas de IA.',
        'icon': 'brain',
        'color': '#8B5CF6',
        'status': 'development',
        'is_base': False,
        'monthly_price': Decimal('499.00'),
        'annual_price': Decimal('4990.00'),
        'display_order': 6,
        'clauses_count': 10,
    }
)
print(f"{'✓ Creado' if created else '→ Ya existe'}: {iso_42001}")

print("")
print("=" * 60)
print(f"TOTAL: {ISOStandard.objects.count()} estándares ISO en catálogo")
print(f"  - Activos: {ISOStandard.objects.filter(status='active').count()}")
print(f"  - En desarrollo: {ISOStandard.objects.filter(status='development').count()}")
print("=" * 60)
