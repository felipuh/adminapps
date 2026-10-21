"""Live invitation authority, shared by preview and registration consumption."""
from rest_framework.exceptions import ValidationError
from apps.users.models import User, UserOrganization
from .models import Organization


def validate_invitation_authority(invitation):
    def deny():
        raise ValidationError({'invitation_token': 'La autoridad de la invitación ya no es válida.'})

    if (invitation.status != 'pending' or invitation.is_expired
            or invitation.role not in dict(User.ROLE_CHOICES)
            or not getattr(invitation, 'invited_by_id', None)):
        deny()
    try:
        inviter = User.objects.get(pk=invitation.invited_by_id, is_active=True)
        organization = Organization.objects.get(pk=invitation.organization_id, status='active')
    except (User.DoesNotExist, Organization.DoesNotExist):
        deny()
    if inviter.is_locked or inviter.must_change_password:
        deny()
    if inviter.is_admin:
        if not inviter.is_staff or not inviter.has_perm('organizations.add_organizationinvitation'):
            deny()
    else:
        if (inviter.role != 'org_admin' or inviter.organization_id != organization.pk
                or not UserOrganization.objects.filter(
                    user_id=inviter.pk, organization_id=organization.pk,
                    is_active=True, role='org_admin', organization__status='active').exists()):
            deny()
    if invitation.role == 'superadmin' and not inviter.is_superadmin:
        deny()
    if invitation.role == 'admin' and not inviter.is_admin:
        deny()
    # Replace any cached relation with the freshly checked tenant.
    invitation.organization = organization
