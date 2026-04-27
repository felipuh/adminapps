"""
Rate limiting utilities for 2FA verification
Prevents brute force attacks on OTP endpoints
"""

from django.core.cache import cache
from rest_framework.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_TWO_FA_ATTEMPTS = 5  # Max failed attempts
TWO_FA_LOCKOUT_MINUTES = 15  # Lockout duration
TWO_FA_CACHE_KEY_PREFIX = 'two_fa_attempts'


def get_two_fa_cache_key(user_id):
    """Generate cache key for 2FA attempts"""
    return f'{TWO_FA_CACHE_KEY_PREFIX}:{user_id}'


def get_two_fa_attempts(user):
    """Get current failed attempts for user"""
    cache_key = get_two_fa_cache_key(user.id)
    attempts = cache.get(cache_key, 0)
    return attempts


def increment_two_fa_attempts(user):
    """Increment failed attempts and return new count"""
    cache_key = get_two_fa_cache_key(user.id)
    attempts = cache.get(cache_key, 0)
    attempts += 1
    
    # Set with timeout (TTL)
    cache.set(cache_key, attempts, TWO_FA_LOCKOUT_MINUTES * 60)
    
    logger.warning(
        f'2FA failed attempt {attempts}/{MAX_TWO_FA_ATTEMPTS} for user {user.id}',
        extra={'user_id': user.id, 'attempts': attempts}
    )
    
    return attempts


def reset_two_fa_attempts(user):
    """Reset failed attempts after successful verification"""
    cache_key = get_two_fa_cache_key(user.id)
    cache.delete(cache_key)
    
    logger.info(
        f'2FA attempts reset for user {user.id}',
        extra={'user_id': user.id}
    )


def check_two_fa_rate_limit(user):
    """
    Check if user has exceeded rate limit
    Raises PermissionDenied if limit exceeded
    """
    attempts = get_two_fa_attempts(user)
    
    if attempts >= MAX_TWO_FA_ATTEMPTS:
        logger.error(
            f'2FA rate limit exceeded for user {user.id}',
            extra={'user_id': user.id, 'attempts': attempts}
        )
        raise PermissionDenied(
            f'Too many failed attempts. Please try again in {TWO_FA_LOCKOUT_MINUTES} minutes.'
        )

