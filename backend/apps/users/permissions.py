"""
Permissions for Admin Apps
"""
from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permiso solo para superadministradores
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superadmin


class IsAdmin(permissions.BasePermission):
    """
    Permiso para administradores (superadmin o admin)
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsOrgAdmin(permissions.BasePermission):
    """
    Permiso para administradores de organización
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_org_admin


class IsISOManager(permissions.BasePermission):
    """
    Permiso para gestores ISO
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_iso_manager


class CanEdit(permissions.BasePermission):
    """
    Permiso para usuarios que pueden editar (no viewers ni auditors)
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_edit


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso para el propietario del objeto o administradores
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        
        # Verificar si el objeto tiene un campo user o created_by
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsSameOrganization(permissions.BasePermission):
    """
    Permiso para verificar que el usuario pertenece a la misma organización
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        
        # Verificar organización del objeto
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.organization
        if hasattr(obj, 'organization_id'):
            return obj.organization_id == request.user.organization_id
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permiso de solo lectura
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsActiveUser(permissions.BasePermission):
    """
    Verificar que el usuario está activo
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active


class IsVerifiedUser(permissions.BasePermission):
    """
    Verificar que el usuario tiene email verificado
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verified
