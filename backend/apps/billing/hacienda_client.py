"""
Client for the Costa Rica Hacienda ATV (Administración Tributaria Virtual) API v2.

Authentication: OAuth2 Resource Owner Password Credentials Grant
                (IDP endpoint of comprobanteselectronicos.go.cr).

Submission:  POST JSON with base64-encoded signed XML to the recepcion endpoint.
Status poll: GET the recepcion endpoint filtered by clave numérica.

Environments:
    sandbox    → rut-stag realm + recepcion-fact-stag URL
    production → rut realm    + recepcion-fact URL
"""

import base64
import logging
from datetime import datetime, timedelta
from typing import Optional

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Endpoint constants
# ---------------------------------------------------------------------------

_TOKEN_URLS = {
    'sandbox':    'https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token',
    'production': 'https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token',
}

_API_URLS = {
    'sandbox':    'https://api.comprobanteselectronicos.go.cr/recepcion-fact-stag/v2/recepcion',
    'production': 'https://api.comprobanteselectronicos.go.cr/recepcion-fact/v2/recepcion',
}

_REQUEST_TIMEOUT = 30  # seconds


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class HaciendaClientError(Exception):
    """Raised when the Hacienda ATV API returns an error or the call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_body: str = ''):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class HaciendaClient:
    """
    Wraps the Hacienda ATV API for a single FiscalProfile.

    Usage::

        client = HaciendaClient(fiscal_profile)
        client.submit_invoice(invoice, signed_xml_string)
        status = client.check_status(invoice.numeric_key)
    """

    def __init__(self, fiscal_profile):
        self.profile = fiscal_profile
        self.env: str = fiscal_profile.hacienda_environment or 'sandbox'
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_token(self) -> None:
        """Fetch a new access token only when the cached one is absent or near-expiry."""
        if self._access_token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return
        self._access_token = None
        self._token_expiry = None
        self.get_token()

    def _auth_headers(self) -> dict:
        self._ensure_token()
        return {'Authorization': f'Bearer {self._access_token}'}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_token(self) -> str:
        """
        Obtain an OAuth2 access token from the Hacienda IDP.

        Uses grant_type=password with client_id / client_secret /
        hacienda_username / hacienda_password from the FiscalProfile.

        Returns the access_token string.
        Raises HaciendaClientError on HTTP or connection error.
        """
        token_url = _TOKEN_URLS.get(self.env, _TOKEN_URLS['sandbox'])
        payload = {
            'grant_type': 'password',
            'client_id': self.profile.client_id or '',
            'client_secret': self.profile.client_secret or '',
            'username': self.profile.hacienda_username or '',
            'password': self.profile.hacienda_password or '',
        }
        try:
            resp = requests.post(token_url, data=payload, timeout=_REQUEST_TIMEOUT)
        except RequestException as exc:
            raise HaciendaClientError(f'No se pudo conectar con el IDP de Hacienda: {exc}')

        if resp.status_code != 200:
            raise HaciendaClientError(
                f'Error al obtener token de Hacienda (HTTP {resp.status_code})',
                status_code=resp.status_code,
                response_body=resp.text,
            )

        data = resp.json()
        self._access_token = data['access_token']
        expires_in = int(data.get('expires_in', 300))
        self._token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 60)

        logger.info('[hacienda_client] Token obtenido — perfil=%s env=%s', self.profile.id, self.env)
        return self._access_token

    def submit_invoice(self, invoice, signed_xml: str) -> dict:
        """
        Submit a signed XML document to the Hacienda ATV reception endpoint.

        The API accepts the XML as a base64-encoded string inside a JSON body.
        A 202 response means Hacienda acknowledged the document for processing.

        Returns the parsed JSON body (or {} when the body is empty).
        Raises HaciendaClientError on HTTP 4xx/5xx or connection failure.
        """
        from django.utils import timezone as tz

        api_url = _API_URLS.get(self.env, _API_URLS['sandbox'])
        issued = invoice.issued_at or tz.now()
        issue_iso = issued.astimezone(tz.get_current_timezone()).strftime('%Y-%m-%dT%H:%M:%S-06:00')

        fp = invoice.fiscal_profile
        tax_digits = ''.join(c for c in (fp.tax_id or '') if c.isdigit())
        id_type = '02' if len(tax_digits) == 10 else '01'

        xml_b64 = base64.b64encode(signed_xml.encode('utf-8')).decode('utf-8')

        body: dict = {
            'clave': invoice.numeric_key,
            'fecha': issue_iso,
            'emisor': {
                'tipoIdentificacion': id_type,
                'numeroIdentificacion': tax_digits,
            },
            'comprobanteXml': xml_b64,
            'callbackUrl': '',
        }

        if invoice.receiver_tax_id:
            rcv_digits = ''.join(c for c in invoice.receiver_tax_id if c.isdigit())
            rcv_type = '02' if len(rcv_digits) == 10 else '01'
            body['receptor'] = {
                'tipoIdentificacion': rcv_type,
                'numeroIdentificacion': rcv_digits,
            }

        try:
            resp = requests.post(
                api_url,
                json=body,
                headers={**self._auth_headers(), 'Content-Type': 'application/json'},
                timeout=_REQUEST_TIMEOUT,
            )
        except RequestException as exc:
            raise HaciendaClientError(f'No se pudo enviar comprobante a Hacienda: {exc}')

        if resp.status_code in (200, 201, 202):
            logger.info(
                '[hacienda_client] Comprobante enviado — factura=%s clave=%s',
                invoice.id, invoice.numeric_key,
            )
            return resp.json() if resp.text.strip() else {}

        raise HaciendaClientError(
            f'Hacienda rechazó el envío (HTTP {resp.status_code}): {resp.text[:400]}',
            status_code=resp.status_code,
            response_body=resp.text,
        )

    def check_status(self, clave: str) -> dict:
        """
        Poll the Hacienda ATV for the current processing status of a document.

        Returns a normalized dict::

            {
                'hacienda_status': 'processing' | 'accepted' | 'rejected' | 'error',
                'message':  str,
                'track_id': str,
                'raw':      original Hacienda response dict,
            }

        A 404 response means Hacienda has not yet processed the document.
        Raises HaciendaClientError on HTTP 5xx or connection failure.
        """
        api_url = _API_URLS.get(self.env, _API_URLS['sandbox'])
        url = f'{api_url}/{clave}'

        try:
            resp = requests.get(url, headers=self._auth_headers(), timeout=_REQUEST_TIMEOUT)
        except RequestException as exc:
            raise HaciendaClientError(f'No se pudo consultar estado en Hacienda: {exc}')

        if resp.status_code == 404:
            logger.debug('[hacienda_client] Clave %s aún no procesada por Hacienda.', clave)
            return {'hacienda_status': 'processing', 'message': 'Aún no procesado', 'track_id': '', 'raw': {}}

        if resp.status_code != 200:
            raise HaciendaClientError(
                f'Error al consultar estado en Hacienda (HTTP {resp.status_code})',
                status_code=resp.status_code,
                response_body=resp.text,
            )

        data = resp.json()
        ind_estado = (data.get('ind-estado') or '').lower()

        _status_map = {
            'recibido':   'processing',
            'procesando': 'processing',
            'aceptado':   'accepted',
            'rechazado':  'rejected',
            'error':      'error',
        }
        hacienda_status = _status_map.get(ind_estado, 'processing')

        raw_message = data.get('respuesta-xml') or data.get('mensajeHacienda') or ''
        if isinstance(raw_message, dict):
            raw_message = raw_message.get('detalleMensaje', str(raw_message))

        logger.info(
            '[hacienda_client] Estado Hacienda para clave %s: %s',
            clave, hacienda_status,
        )
        return {
            'hacienda_status': hacienda_status,
            'message': str(raw_message)[:1000],
            'track_id': data.get('numeroConsecutivoReceptor', ''),
            'raw': data,
        }
