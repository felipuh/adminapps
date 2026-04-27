"""Request-scoped context helpers for logging."""

from __future__ import annotations

import contextvars
import logging


_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='-')


def set_request_id(request_id: str) -> None:
    _request_id_var.set(request_id or '-')


def get_request_id() -> str:
    return _request_id_var.get()


def clear_request_id() -> None:
    _request_id_var.set('-')


class RequestIDLogFilter(logging.Filter):
    """Attach request_id to all log records for formatter usage."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
