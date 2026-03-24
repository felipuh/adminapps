"""
XML digital signature for Costa Rica electronic invoices.

Implements XMLDSig enveloped signature (RSA-SHA256 / SHA-256) extended with
basic XAdES-EPES qualifying properties (SigningTime, SigningCertificate,
SignaturePolicyIdentifier) as required by Hacienda Costa Rica
(Resolución DGT-R-012-2021).

Dependencies (added to requirements.txt):
    lxml>=4.9
    signxml>=3.2
    cryptography>=42

Usage::

    from apps.billing.xml_signer import sign_invoice_xml

    signed_xml = sign_invoice_xml(
        xml_string=raw_xml,
        p12_path='/secure/certs/empresa.p12',
        p12_pin='secreto',
    )
"""

import base64
import hashlib
import logging
from datetime import datetime, timezone as dt_tz

logger = logging.getLogger(__name__)

# XAdES signature policy URI published by Hacienda CR
_HACIENDA_POLICY_URI = 'https://www.hacienda.go.cr/comprobantes-electronicos/politica-firma'


def sign_invoice_xml(xml_string: str, p12_path: str, p12_pin: str) -> str:
    """
    Sign an XML document with the PKCS#12 (.p12) certificate.

    Args:
        xml_string: UTF-8 XML string of the electronic invoice (unsigned).
        p12_path:   Absolute filesystem path to the .p12 certificate file.
                    The file must NOT be web-accessible.
        p12_pin:    PIN / password for the .p12 file.

    Returns:
        Signed XML string with the ds:Signature element embedded.

    Raises:
        ImportError       if lxml, signxml, or cryptography are not installed.
        FileNotFoundError if p12_path does not exist.
        ValueError        if the certificate cannot be loaded or signing fails.
    """
    try:
        from lxml import etree
        from signxml import XMLSigner, methods
        from cryptography.hazmat.primitives.serialization import Encoding
        from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
    except ImportError as exc:
        raise ImportError(
            'Para firma digital instale: pip install lxml "signxml>=3.2" cryptography'
        ) from exc

    # --- Load p12 ---
    with open(p12_path, 'rb') as fh:
        p12_data = fh.read()

    private_key, certificate, additional_certs = load_key_and_certificates(
        p12_data, p12_pin.encode('utf-8')
    )
    if certificate is None:
        raise ValueError('No se encontró el certificado dentro del archivo .p12.')

    cert_chain = [certificate]
    if additional_certs:
        cert_chain.extend(additional_certs)

    # --- XAdES namespace URIs ---
    XADES_NS = 'http://uri.etsi.org/01903/v1.3.2#'
    DS_NS = 'http://www.w3.org/2000/09/xmldsig#'

    # --- Build XAdES QualifyingProperties before signing so they can be referenced ---
    signing_time = datetime.now(dt_tz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    cert_der = certificate.public_bytes(Encoding.DER)
    cert_digest_b64 = base64.b64encode(hashlib.sha256(cert_der).digest()).decode('ascii')

    qualifying_props = etree.Element(
        f'{{{XADES_NS}}}QualifyingProperties',
        nsmap={'xades': XADES_NS, 'ds': DS_NS},
    )
    qualifying_props.set('Target', '#Signature')

    signed_props = etree.SubElement(
        qualifying_props, f'{{{XADES_NS}}}SignedProperties',
        attrib={'Id': 'SignedProperties'},
    )
    sig_sig_props = etree.SubElement(signed_props, f'{{{XADES_NS}}}SignedSignatureProperties')

    # SigningTime
    st_el = etree.SubElement(sig_sig_props, f'{{{XADES_NS}}}SigningTime')
    st_el.text = signing_time

    # SigningCertificate
    signing_cert_el = etree.SubElement(sig_sig_props, f'{{{XADES_NS}}}SigningCertificate')
    cert_el = etree.SubElement(signing_cert_el, f'{{{XADES_NS}}}Cert')
    cert_digest_el = etree.SubElement(cert_el, f'{{{XADES_NS}}}CertDigest')
    digest_method_el = etree.SubElement(cert_digest_el, f'{{{DS_NS}}}DigestMethod')
    digest_method_el.set('Algorithm', 'http://www.w3.org/2001/04/xmlenc#sha256')
    digest_value_el = etree.SubElement(cert_digest_el, f'{{{DS_NS}}}DigestValue')
    digest_value_el.text = cert_digest_b64

    # SignaturePolicyIdentifier (Hacienda CR policy)
    sig_policy_el = etree.SubElement(sig_sig_props, f'{{{XADES_NS}}}SignaturePolicyIdentifier')
    sig_policy_id_el = etree.SubElement(sig_policy_el, f'{{{XADES_NS}}}SignaturePolicyId')
    spid_el = etree.SubElement(sig_policy_id_el, f'{{{XADES_NS}}}SigPolicyId')
    id_el = etree.SubElement(spid_el, f'{{{XADES_NS}}}Identifier')
    id_el.text = _HACIENDA_POLICY_URI

    # --- Parse the invoice XML ---
    root = etree.fromstring(xml_string.encode('utf-8'))

    # --- Sign with XMLDSig enveloped / RSA-SHA256 ---
    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm='rsa-sha256',
        digest_algorithm='sha-256',
        c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315',
    )

    signed_root = signer.sign(
        root,
        key=private_key,
        cert=cert_chain,
        reference_uri='',
    )

    # Inject XAdES QualifyingProperties into ds:Object inside the Signature element
    sig_el = signed_root.find('.//{http://www.w3.org/2000/09/xmldsig#}Signature')
    if sig_el is not None:
        obj_el = etree.SubElement(sig_el, f'{{{DS_NS}}}Object')
        obj_el.append(qualifying_props)

    subject_cn = getattr(certificate.subject, 'rfc4514_string', lambda: str(certificate.subject))()
    logger.info('[xml_signer] XML firmado con certificado: %s', subject_cn)

    return etree.tostring(signed_root, encoding='unicode')
