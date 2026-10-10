# Security policy

## Supported versions

| Version       | Supported      |
| ------------- | -------------- |
| `0.3.2`       | ✅ Yes          |
| `0.1.x`       | best-effort    |

## Reporting a vulnerability

Open a **private** report via GitHub Security Advisories (preferred) or email the maintainer listed
in `pyproject.toml`. Include: affected version, reproduction steps (offline, no real credentials),
and impact assessment. Please do not open public issues for vulnerabilities.

## Handling secrets safely with this SDK

- Session files (`.gopay-session.json`, `.shopee-session.json`) and pending-OTP caches are
  git-ignored for a reason — keep them out of repos, screenshots, and issue reports.
- Treat tokens like passwords: GoPay `access_token`/`refresh_token`, ShopeePay `B:` tokens, and
  the `device_report` blob. Never log them, never commit them, `chmod 600` session files.
- OTP codes are single-use and time-limited — never paste real ones into issues, docs, or chat.
- Credentials you enter are only ever sent to the providers' own official servers; the SDK never
  phones home anywhere else.
