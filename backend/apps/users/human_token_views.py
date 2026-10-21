"""Session-bound refresh endpoint (no legacy SimpleJWT refresh fallback)."""
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.views import TokenRefreshView

from .human_sessions import refresh_pair
from .authentication import HumanJWTAuthentication


class HumanTokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        expected = user.pk if getattr(user, 'is_authenticated', False) else None
        return refresh_pair(attrs['refresh'], expected_user_id=expected)


class HumanTokenRefreshView(TokenRefreshView):
    serializer_class = HumanTokenRefreshSerializer
    authentication_classes = [HumanJWTAuthentication, SessionAuthentication]
