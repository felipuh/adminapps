"""Prepared DRF wiring: replace JWTAuthentication with HumanJWTAuthentication.

No active settings are changed. SessionAuthentication remains a separate cookie
backend; a rejected bearer raises and cannot fall through to a valid cookie.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from .human_sessions import authenticate_access


class HumanJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        # Pin access type even if AUTH_TOKEN_CLASSES is broadened elsewhere.
        try:
            return AccessToken(raw_token)
        except TokenError:
            raise InvalidToken('Invalid human access token') from None

    def get_user(self, validated_token):
        return authenticate_access(validated_token)
