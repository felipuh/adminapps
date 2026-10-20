"""Decision 02-A capability checks: memory only, no Django setup, DB or IPC.

Run from repository root:
  backend/.venv312/bin/python -B backend/scripts/tests/test_s3_capability_offline.py
These tests do not demonstrate process, credential, PostgreSQL or IPC isolation.
"""
import base64
import importlib.util
import json
from pathlib import Path
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


SOURCE = Path(__file__).resolve().parents[2] / "apps/financial/capabilities.py"
SPEC = importlib.util.spec_from_file_location("s3_offline_capabilities", SOURCE)
capabilities = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capabilities)


def encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


class Decision02AOfflineTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.now = datetime(2026, 10, 9, 12, tzinfo=timezone.utc)
        self.values = dict(
            issuer_id="synthetic-issuer", key_id="synthetic-key",
            producer_registration_id=uuid.UUID(int=1), organization_id=uuid.UUID(int=2),
            product_id=uuid.UUID(int=3), invocation_id=uuid.UUID(int=4),
            grant_id=uuid.UUID(int=5), grant_version=1, environment="controlled_test",
            material_request_hash="a" * 64, now=self.now,
        )
        self.token = capabilities.mint_capability(private_key=self.key, **self.values)
        payload, self.signature = self.token.split(".")
        self.claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))

    def verify(self, token=None, **changes):
        options = dict(public_keys={"synthetic-key": self.key.public_key()},
                       issuer_id="synthetic-issuer", now=self.now)
        options.update(changes)
        return capabilities.verify_capability(self.token if token is None else token, **options)

    def signed(self, claims):
        payload = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode()
        return encode(payload) + "." + encode(self.key.sign(capabilities.canonical_capability_bytes(claims)))

    def denied(self, code, token=None, **options):
        with self.assertRaises(capabilities.CapabilityDenied) as caught:
            self.verify(token, **options)
        self.assertEqual(caught.exception.code, code)

    def test_valid_public_key_verification_and_invocation_binding(self):
        claims = self.verify(expected={"organization_id": self.values["organization_id"],
                                      "product_id": self.values["product_id"]})
        self.assertEqual(claims["jti"], str(self.values["invocation_id"]))
        self.assertEqual(claims["operation"], "admit_reserve")

    def test_exported_public_key_verifies_signature(self):
        public_material = capabilities.public_key_bytes(self.key)
        self.assertEqual(len(public_material), 32)
        challenge = b"synthetic-public-key-export-check"
        Ed25519PublicKey.from_public_bytes(public_material).verify(self.key.sign(challenge), challenge)

    def test_tenant_and_product_substitution_without_resigning_denied(self):
        for field in ("organization_id", "product_id", "jti", "grant_id", "material_request_hash"):
            with self.subTest(field=field):
                claims = {**self.claims, field: "b" * 64}
                token = encode(json.dumps(claims).encode()) + "." + self.signature
                self.denied("CAPABILITY_SIGNATURE_INVALID", token)

    def test_signature_from_different_key_denied(self):
        payload = self.token.split(".")[0]
        signature = Ed25519PrivateKey.generate().sign(capabilities.canonical_capability_bytes(self.claims))
        self.denied("CAPABILITY_SIGNATURE_INVALID", payload + "." + encode(signature))

    def test_unknown_or_removed_public_key_denied(self):
        self.denied("CAPABILITY_KEY_UNKNOWN", public_keys={})

    def test_wrong_issuer_denied(self):
        self.denied("CAPABILITY_AUDIENCE_DENIED", issuer_id="other-issuer")

    def test_wrong_audience_even_with_valid_signature_denied(self):
        self.denied("CAPABILITY_AUDIENCE_DENIED", self.signed({**self.claims, "aud": "other"}))

    def test_algorithm_confusion_denied(self):
        self.denied("CAPABILITY_ALGORITHM_DENIED", self.signed({**self.claims, "alg": "HS256"}))

    def test_unknown_version_denied(self):
        self.denied("CAPABILITY_VERSION_DENIED", self.signed({**self.claims, "version": 2}))

    def test_missing_claim_denied(self):
        claims = dict(self.claims)
        del claims["organization_id"]
        self.denied("CAPABILITY_CLAIMS_INVALID", self.signed(claims))

    def test_extra_claim_denied(self):
        self.denied("CAPABILITY_CLAIMS_INVALID", self.signed({**self.claims, "unreviewed": "value"}))

    def test_expiry_boundary_denied(self):
        self.denied("CAPABILITY_EXPIRED", now=self.now + timedelta(seconds=60))

    def test_last_valid_second_accepted(self):
        self.assertEqual(self.verify(now=self.now + timedelta(seconds=59))["jti"], self.claims["jti"])

    def test_before_not_before_denied(self):
        self.denied("CAPABILITY_EXPIRED", now=self.now - timedelta(seconds=1))

    def test_excessive_signed_lifetime_denied(self):
        self.denied("CAPABILITY_TIME_INVALID", self.signed({**self.claims, "exp": "2026-10-09T12:01:01Z"}))

    def test_malformed_timestamp_denied(self):
        self.denied("CAPABILITY_TIME_INVALID", self.signed({**self.claims, "nbf": "invalid"}))

    def test_expected_identity_mismatch_denied(self):
        self.denied("CAPABILITY_BINDING_DENIED", expected={"organization_id": uuid.UUID(int=99)})

    def test_malformed_envelope_denied(self):
        for token in ("", "onepart", "a.b.c", "e30.eA"):
            with self.subTest(token=token):
                with self.assertRaises(capabilities.CapabilityDenied):
                    self.verify(token)

    def test_mint_lifetime_out_of_range_denied(self):
        for lifetime in (0, -1, 61):
            with self.subTest(lifetime=lifetime), self.assertRaises(ValueError):
                capabilities.mint_capability(private_key=self.key, lifetime_seconds=lifetime, **self.values)


if __name__ == "__main__":
    unittest.main(verbosity=2)
