"""Cookie-only transport for the existing SimpleJWT authentication contract."""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck
from rest_framework import exceptions


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate a short-lived JWT from an HttpOnly cookie, never a header."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get('isosmart_access')
        if not raw_token:
            return None
        token = self.get_validated_token(raw_token)
        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            # Cookie credentials are ambient; unsafe requests require Django's
            # standard double-submit CSRF validation.
            self.enforce_csrf(request)
        return self.get_user(token), token

    @staticmethod
    def enforce_csrf(request):
        check = CSRFCheck(lambda request: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')
