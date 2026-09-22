## What

<!-- Conventional-commit style summary: feat:/fix:/docs:/test:/chore: ... -->

## Verification

- [ ] New/changed behavior is covered by **offline** tests (`pytest` stays green, coverage ≥ 80%)
- [ ] `ruff check` + `ruff format --check` + `mypy src` pass
- [ ] Endpoint/behavior claims cite evidence (traffic, smali, or upstream commit); otherwise marked
      `BELUM TERVERIFIKASI` + TODO
- [ ] No credentials, tokens, or device IDs committed (see `.gitignore`)
- [ ] `CHANGELOG.md` updated (for user-facing changes)
