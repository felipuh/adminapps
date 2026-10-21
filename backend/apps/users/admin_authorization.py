class RoleRestrictedAdminMixin:
    required_role = 'is_admin'

    def _has_required_role(self, request):
        user = getattr(request, 'user', None)
        return bool(
            user
            and getattr(user, 'is_authenticated', False)
            and getattr(user, self.required_role, False)
        )

    def has_add_permission(self, request):
        return (
            super().has_add_permission(request)
            and self._has_required_role(request)
        )

    def has_change_permission(self, request, obj=None):
        return (
            super().has_change_permission(request, obj)
            and self._has_required_role(request)
        )

    def has_delete_permission(self, request, obj=None):
        return (
            super().has_delete_permission(request, obj)
            and self._has_required_role(request)
        )

    def has_view_permission(self, request, obj=None):
        return (
            super().has_view_permission(request, obj)
            and self._has_required_role(request)
        )


class ReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
