# Contributing to indic-voice

Thank you for your interest in contributing.

## Development Setup

```bash
git clone https://github.com/hrshx3o5o6/indic-voice-cloning.git
cd indic-voice-cloning
uv sync
```

Run the CLI:
```bash
uv run indic-voice --help
uv run indic-voice clone --text "नमस्ते" --ref-voice ref.wav
```

Run tests:
```bash
uv run pytest tests/ -v
```

## Branch Strategy

| Change Type | Branch |
|---|---|
| Bug fixes, refactors | `dev` |
| New features | `feat/<feature-name>` |
| Hotfixes | `hotfix/<description>` |

**Never commit directly to `main`.**

## Commit Convention

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat(tts): add support for Bengali voice cloning
fix(asr): handle missing audio file with clear error message
refactor(cli): extract temp file cleanup into context manager
docs(readme): update supported language list
```

Format: `type(scope): description`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

## Bug Fix Policy

When a bug is reported and fixed, commit the fix immediately with a descriptive message:
```
fix(tts): resolve meta tensor error in IndicF5 model loading
```

Do not group unrelated fixes into a single commit.

## Pull Request Process

1. Fork the repository and create a branch from `dev`
2. Make your changes — ensure tests pass: `uv run pytest tests/`
3. Open a PR targeting `dev`
4. Describe what the change does and why
5. Link any related issues

## Code Style

- Type hints required on all function arguments and return types
- Docstrings: Google-style on all public functions and classes
- CLI output: use `rich` for all user-facing messages — no bare `print()`
- Error handling: `try/except` with user-friendly `rich` error messages

## Dependency Policy

- Use `uv add <package>` to add dependencies (updates `pyproject.toml` + `uv.lock` automatically)
- Do not manually edit `pyproject.toml` for dependency changes
- Always commit both `pyproject.toml` and `uv.lock` together
