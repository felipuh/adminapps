"""Shared PostgreSQL 2FA counters. No cache/in-memory fallback."""
from rest_framework.exceptions import PermissionDenied
from .two_factor_service import MAX_ATTEMPTS, LOCKOUT_MINUTES, rate_state

MAX_TWO_FA_ATTEMPTS = MAX_ATTEMPTS
TWO_FA_LOCKOUT_MINUTES = LOCKOUT_MINUTES


def get_two_fa_attempts(user):
    return rate_state(user)


def increment_two_fa_attempts(user):
    return rate_state(user, 'increment')


def reset_two_fa_attempts(user):
    return rate_state(user, 'reset')


def check_two_fa_rate_limit(user):
    if get_two_fa_attempts(user) >= MAX_TWO_FA_ATTEMPTS:
        raise PermissionDenied('Too many failed attempts. Please try again in 15 minutes.')
