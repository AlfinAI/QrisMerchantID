# Contributing

## Ground rules (non-negotiable)

1. **No guessing.** Every endpoint/behavior claim needs evidence: app traffic, APK
   smali/strings reference, or a reference-repo commit (with link). Otherwise mark it
   `BELUM TERVERIFIKASI` + TODO.
2. **Tests stay offline.** Never hit the real API; never require credentials. Use the
   `FakeHttpClient` in `tests/conftest.py`.
3. **No credentials in the repo.** Tokens, PINs, OTPs, device IDs — keep them in env vars.
4. **Conventional Commits** (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).

## Setup

```bash
pip install -e ".[dev]"
pytest
ruff check src tests && ruff format --check src tests
mypy src
```

## Porting discipline

This SDK mirrors [lintangtimur/ovoid](https://github.com/lintangtimur/ovoid). When porting:

- Keep method parity (`camelCase` PHP → `snake_case` Python) and the same wire shapes.
- Deliberate deviations (like the APK-verified header defaults) must cite
  `research/` evidence and be noted in `CHANGELOG.md`.
- Update `docs/services/<name>.md` and add an offline test for every behavior change.
