"""Custom middleware for AdminApps backend."""

from __future__ import annotations

import uuid

from config.request_context import set_request_id


class RequestIDMiddleware:
    """Attach and propagate a request id for end-to-end tracing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        set_request_id(request.request_id)
        response = self.get_response(request)
        response['X-Request-ID'] = request.request_id
        return response


class ProductionSecurityHeadersMiddleware:
    """Apply explicit browser policy headers not covered by Django defaults."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Content-Security-Policy', "frame-ancestors 'none'")
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()')
        return response
