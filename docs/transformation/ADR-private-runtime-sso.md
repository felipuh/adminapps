# Private runtime SSO configuration
Date: 2026-10-31
Status: deployment configuration support; activation requires a coordinated service transition.

The three products retain their own code directories. Each backend optionally loads
an absolute JSON path supplied through SMART3AI_RUNTIME_CONFIG, after its existing
.env and before security-policy validation. The file must be regular, not a symlink,
owned by the application user or root, and inaccessible to group and other users.
Private JSON files, RSA private keys and integration credentials never belong in Git.

Schema version 1 contains product, environment and settings sections. Product identity
must match ADMINAPPS, ISO_SMART or MEDSUPPLIER. Environment changes have a fixed
allowlist; database settings and arbitrary Django settings cannot be supplied.
Operational overrides cannot enable debug, local authentication fallback or bypasses.
The central service receives the central signing key. Consumers receive its public
keyring and their own distinct local signer, with explicit HTTPS authority, issuer,
client ID and audience. Keyrings are validated before settings are installed.

Existing installations without SMART3AI_RUNTIME_CONFIG preserve their previous
settings. Invalid supplied configuration fails closed without echoing file contents.
The loader changes no HTTP contract, database schema, permissions or entitlement.

Validation: python -m unittest -v test_runtime_sso_config from backend.
Service activation also requires Django checks, verified TLS, matching registered
clients, preserved tenant/product grants and a coordinated rollback-tested transition.
