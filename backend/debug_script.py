import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adminapps.settings')
django.setup()

import sys
from django.db import connection
from django.contrib.auth import get_user_model, authenticate
from rest_framework.test import APIRequestFactory

User = get_user_model()
email = "felipe@smart3ai.com"
password = "F3l1p32191"

try:
    # 1. Buscar usuario (evitando columnas inexistentes si es posible)
    user = User.objects.get(email__iexact=email)
    print(f"--- 1. User Found ---")
    print(f"User: {user.email} (ID: {user.id})")
    
    # 2. check_password
    print(f"--- 2. check_password ---")
    match = user.check_password(password)
    print(f"check_password('{password}'): {match}")
    
    # 3. Memberships
    print(f"--- 3. Active Memberships ---")
    from users.models import OrganizationMembership
    memberships = OrganizationMembership.objects.filter(user=user, status='active')
    if not memberships.exists():
        print("No active memberships found.")
    for m in memberships:
        org = m.organization
        print(f"Org ID: {org.id}, Name: {org.name}, Status: {m.status}, Primary: {m.is_primary}, Role: {m.role}")

    # 4. authenticate
    print(f"--- 4. authenticate() ---")
    try:
        auth_user = authenticate(email=email, password=password)
        print(f"authenticate returns: {auth_user}")
    except Exception as e_auth:
        print(f"authenticate error: {e_auth}")

    # 5. LoginView
    print(f"--- 5. APIRequestFactory LoginView ---")
    from users.views import LoginView
    factory = APIRequestFactory()
    request = factory.post('/api/users/login/', {'email': email, 'password': password}, format='json')
    view = LoginView.as_view()
    try:
        response = view(request)
        print(f"Status Code: {response.status_code}")
        response.render()
        print(f"Body: {response.content.decode()}")
    except Exception as e_view:
        print(f"View error: {e_view}")

except Exception as e:
    print(f"An error occurred: {e}")
    # Si falla por columna inexistente, intentamos obtener solo ID y EMAIL
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, email, password FROM users WHERE email = %s", [email])
            row = cursor.fetchone()
            if row:
                print(f"Fallback RAW DB: Found user ID {row[0]}, Email {row[1]}")
                # No podemos usar check_password facilmente sin el objeto, pero esto confirma existencia.
            else:
                print(f"Fallback RAW DB: User {email} not found.")
    except Exception as e_raw:
        print(f"Raw query error: {e_raw}")

