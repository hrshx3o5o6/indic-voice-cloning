# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please open a GitHub issue with the label `security` or email the maintainer directly. Do **not** file a public issue.

All security reports are acknowledged within 48 hours and triaged within 5 business days.

## Security Notes

- **HuggingFace token**: If you use a HF token for gated model access, treat it as a secret — never commit it to the repository
- **Model downloads**: Model weights are downloaded directly from HuggingFace at runtime — verify the repository URL before using
- **Local inference only**: The CLI runs entirely locally; no audio data is transmitted to external servers after models are downloaded
