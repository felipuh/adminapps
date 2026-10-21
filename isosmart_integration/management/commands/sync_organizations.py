"""
Comando para sincronizar organizaciones desde Admin Apps
python manage.py sync_organizations
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from integration.client import admin_apps_client
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sincroniza organizaciones desde Admin Apps'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar sincronización completa (ignorar caché)',
        )
        parser.add_argument(
            '--org-id',
            type=int,
            help='Sincronizar solo una organización específica',
        )
    
    def handle(self, *args, **options):
        from core.models import Organization
        
        force = options['force']
        org_id = options.get('org_id')
        
        self.stdout.write(self.style.NOTICE('Iniciando sincronización con Admin Apps...'))
        
        # Verificar conexión
        health = admin_apps_client.health_check()
        if 'error' in health:
            raise CommandError(f"No se puede conectar a Admin Apps: {health['error']}")
        
        self.stdout.write(self.style.SUCCESS(f"✓ Conectado a Admin Apps ({health.get('service')})"))
        
        if org_id:
            # Sincronizar una organización específica
            self._sync_organization(org_id, force)
        else:
            # Sincronizar todas las organizaciones
            self._sync_all_organizations(force)
        
        self.stdout.write(self.style.SUCCESS('Sincronización completada'))
    
    def _sync_all_organizations(self, force):
        """Sincroniza todas las organizaciones"""
        from core.models import Organization
        
        result = admin_apps_client.get_organizations(use_cache=not force)
        
        if 'error' in result:
            raise CommandError(f"Error obteniendo organizaciones: {result['error']}")
        
        organizations = result.get('organizations', [])
        self.stdout.write(f"Encontradas {len(organizations)} organizaciones en Admin Apps")
        
        created = 0
        updated = 0
        
        for org_data in organizations:
            org, was_created = Organization.objects.update_or_create(
                id=org_data['id'],
                defaults={
                    'name': org_data['name'],
                    'slug': org_data['slug'],
                    'is_active': org_data['status'] == 'active',
                }
            )
            
            if was_created:
                created += 1
                self.stdout.write(f"  + Creada: {org.name}")
            else:
                updated += 1
                self.stdout.write(f"  ~ Actualizada: {org.name}")
        
        self.stdout.write(self.style.SUCCESS(
            f"Resumen: {created} creadas, {updated} actualizadas"
        ))
    
    def _sync_organization(self, org_id, force):
        """Sincroniza una organización específica"""
        from core.models import Organization
        
        result = admin_apps_client.get_organization(org_id, use_cache=not force)
        
        if 'error' in result:
            raise CommandError(f"Error obteniendo organización {org_id}: {result['error']}")
        
        org, created = Organization.objects.update_or_create(
            id=result['id'],
            defaults={
                'name': result['name'],
                'slug': result['slug'],
                'is_active': result['status'] == 'active',
            }
        )
        
        action = "Creada" if created else "Actualizada"
        self.stdout.write(self.style.SUCCESS(f"{action}: {org.name}"))
        
        # Sincronizar usuarios de la organización
        self._sync_organization_users(org_id, force)
    
    def _sync_organization_users(self, org_id, force):
        """Sincroniza usuarios de una organización"""
        from django.contrib.auth import get_user_model
        from core.models import Organization
        from authentication.models import UserProfile
        
        User = get_user_model()
        
        result = admin_apps_client.get_organization_users(org_id, use_cache=not force)
        
        if 'error' in result:
            self.stdout.write(self.style.WARNING(
                f"Error obteniendo usuarios: {result['error']}"
            ))
            return
        
        users = result.get('users', [])
        self.stdout.write(f"  Sincronizando {len(users)} usuarios...")
        
        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Organización {org_id} no existe localmente"
            ))
            return
        
        for user_data in users:
            user, user_created = User.objects.update_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_active': True,
                }
            )
            
            if user_created:
                user.set_unusable_password()
                user.save()
            
            profile, profile_created = UserProfile.objects.update_or_create(
                user=user,
                organization=organization,
                defaults={
                    'role': user_data['role'],
                    'job_title': user_data.get('job_title', ''),
                    'department': user_data.get('department', ''),
                    'is_active': True,
                }
            )
            
            status = "+" if user_created else "~"
            self.stdout.write(f"    {status} {user.email} ({user_data['role']})")
