#!/usr/bin/env bash
set -euo pipefail

# Bootstrap for a fresh AdminApps setup using Smart3AI baseline.
# Usage:
#   SUPERUSER_PASSWORD='StrongPass!123' ./scripts/bootstrap_smart3ai.sh

EMAIL="${SUPERUSER_EMAIL:-felipe@smart3ai.com}"
PASSWORD="${SUPERUSER_PASSWORD:-}"
FIRST_NAME="${SUPERUSER_FIRST_NAME:-Felipe}"
LAST_NAME="${SUPERUSER_LAST_NAME:-Admin}"
ORG_NAME="${SMART3AI_ORG_NAME:-Smart3AI}"
ORG_EMAIL="${SMART3AI_ORG_EMAIL:-felipe@smart3ai.com}"

if [[ -z "${PASSWORD}" ]]; then
  echo "ERROR: define SUPERUSER_PASSWORD before running this script."
  exit 1
fi

python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization
from apps.users.models import UserOrganization

email = os.getenv('SUPERUSER_EMAIL', 'felipe@smart3ai.com')
password = os.getenv('SUPERUSER_PASSWORD')
first_name = os.getenv('SUPERUSER_FIRST_NAME', 'Felipe')
last_name = os.getenv('SUPERUSER_LAST_NAME', 'Admin')
org_name = os.getenv('SMART3AI_ORG_NAME', 'Smart3AI')
org_email = os.getenv('SMART3AI_ORG_EMAIL', 'felipe@smart3ai.com')

if not password:
    raise SystemExit('SUPERUSER_PASSWORD is required')

User = get_user_model()

user, _ = User.objects.get_or_create(
    email=email,
    defaults={
        'first_name': first_name,
        'last_name': last_name,
        'is_active': True,
        'is_staff': True,
        'is_superuser': True,
        'role': 'superadmin',
    },
)

user.first_name = first_name
user.last_name = last_name
user.is_active = True
user.is_staff = True
user.is_superuser = True
user.role = 'superadmin'
user.set_password(password)
user.save()

org, _ = Organization.objects.get_or_create(
    name=org_name,
    defaults={
        'email': org_email,
        'status': 'active',
        'industry': 'services',
        'size': 'small',
        'employees_count': 10,
        'max_users': 50,
    },
)

if org.email != org_email or org.status != 'active':
    org.email = org_email
    org.status = 'active'
    org.save(update_fields=['email', 'status', 'updated_at'])

user.organization = org
user.save(update_fields=['organization', 'updated_at'])

UserOrganization.objects.update_or_create(
    user=user,
    organization=org,
    defaults={
        'role': 'superadmin',
        'is_primary': True,
        'is_active': True,
    },
)

print(f'AdminApps ready: superuser={email}, organization={org.name}')
PY

echo "Done. You can now log in with ${EMAIL}."
