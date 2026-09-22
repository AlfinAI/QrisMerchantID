# Security policy

## Supported versions

| Version       | Supported     |
| ------------- | ------------- |
| 0.1.x (alpha) | ✅ best-effort |

## Reporting a vulnerability

Open a **private** report via GitHub Security Advisories (preferred) or email the maintainer listed
in `pyproject.toml`. Include: affected version, reproduction steps (offline, no real credentials),
and impact assessment. Please do not open public issues for vulnerabilities.

## Handling secrets safely with this SDK

- `top_up_debit_prepare()` sends raw card data — never log request bodies on that path.
- The PIN is RSA-encrypted in transit, but it exists in plaintext in your process memory: read it
  via `getpass`, never hardcode it, never log it.
- `.ovo-token.json` / `.ovo-otp-pending.json` are git-ignored for a reason — keep them out of repos,
  screenshots, and issue reports.
- Session tokens live ~24 h; treat them like passwords.
