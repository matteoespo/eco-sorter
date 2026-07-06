# Security Policy

## Supported Versions

The following versions of Eco-Sorter are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

We take the security of Eco-Sorter seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, send an email to: **matteoespo@users.noreply.github.com**

Include the following information in your report:

- A clear description of the vulnerability
- Steps to reproduce the issue
- The potential impact of the vulnerability
- Any suggested fixes or mitigations (if applicable)

### What to Expect

1. **Acknowledgment**: We will acknowledge receipt of your report within **48 hours**.
2. **Assessment**: We will investigate and assess the severity of the vulnerability within **7 days**.
3. **Resolution**: We will work on a fix and coordinate a timeline for disclosure. Critical vulnerabilities will be prioritized.
4. **Disclosure**: Once the fix is released, we will publicly disclose the vulnerability with credit to the reporter (unless anonymity is requested).

### Security Update Process

- Security patches are released as soon as possible after a vulnerability is confirmed.
- Updates are published as new patch releases (e.g., `2.0.1`).
- Security advisories are posted in the [GitHub Security Advisories](https://github.com/matteoespo/eco-sorter/security/advisories) section.
- Users are encouraged to keep their deployments up to date by pulling the latest images.

### Scope

The following areas are in scope for security reports:

- The FastAPI CV backend service
- The Next.js frontend application
- The Ollama LLM integration
- Docker Compose configuration and container security
- Dependency vulnerabilities

## Best Practices for Deployment

- Always use the latest tagged release.
- Do not expose internal services (backend, Ollama) directly to the internet.
- Review and restrict Docker network access as needed.
- Keep Docker and all dependencies up to date.

Thank you for helping keep Eco-Sorter and its users safe! 🔒
