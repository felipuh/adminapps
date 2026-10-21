# Frontend Auth Security

Date: 2026-07-03

## Current Risk

The three frontends still store JWT access and refresh tokens in `localStorage`. This is acceptable only for controlled demo/pilot use with explicit restrictions because any successful XSS could read bearer tokens.

## Mitigations Present Or Required For Pilot

- Logout must remove `access_token` and `refresh_token`.
- Refresh failure must clear both tokens.
- Tokens must not be logged.
- UI preferences can remain in `localStorage`; credentials and sensitive business data must not.
- API calls should use centralized token handling rather than ad hoc storage reads where feasible.

## Recommended CSP

Use a restrictive CSP in staging/production:

```text
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self' https://adminapps.example.com https://isosmart.example.com https://medsupplier.example.com;
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

## Migration Plan To HttpOnly Cookies

1. Add backend cookie issuance for access/refresh tokens with `HttpOnly`, `Secure`, and `SameSite=Lax` or `Strict`.
2. Keep CSRF protection enabled for unsafe methods.
3. Update frontends to rely on `credentials: include` / Axios `withCredentials`.
4. Add compatibility window for bearer tokens only in development.
5. Remove persistent JWT storage from browser storage.

## Pilot Restriction

Controlled pilot can proceed only with trusted users, no untrusted custom HTML/content injection, CSP enabled in target environment, and documented acceptance of the temporary `localStorage` token risk.
