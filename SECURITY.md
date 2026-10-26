# Security Policy

## Supported Versions

We actively provide security patches for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The security and privacy of student data is our utmost priority.

If you discover a security vulnerability within the AI Study Buddy platform, **please DO NOT create a public GitHub issue**. Instead, submit a responsible disclosure report directly:

- **Email**: security@aistudybuddy.local
- Include detailed reproduction steps, potential impact, and suggested mitigations.
- You will receive an acknowledgment within 48 hours.

## Security Practices
- All API keys and connection credentials must be loaded exclusively through environment variables.
- Sensitive files (`.env`, database files, caches) are strictly enforced in `.gitignore`.
- Production containers run under an unprivileged `appuser` system account.
