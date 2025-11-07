# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Cyber-PI-Intel seriously. If you have discovered a security vulnerability, we appreciate your help in disclosing it to us responsibly.

### Where to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities through one of these channels:

1. **Email**: security@cyber-pi-intel.local (preferred)
2. **Private Security Advisory**: Use GitHub's "Report a vulnerability" feature

### What to Include

Please include the following information in your report:

- **Description**: A clear description of the vulnerability
- **Impact**: What an attacker could achieve
- **Steps to Reproduce**: Detailed steps to reproduce the vulnerability
- **Proof of Concept**: If applicable, include PoC code or screenshots
- **Affected Components**: Which parts of the system are affected
- **Suggested Fix**: If you have suggestions for remediation
- **CVE Information**: If already assigned a CVE number

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - **Critical**: 7 days
  - **High**: 30 days
  - **Medium**: 90 days
  - **Low**: Next release cycle

### Severity Classification

We use the following severity levels:

| Severity | Description | Examples |
|----------|-------------|----------|
| **Critical** | Complete system compromise | RCE, Authentication bypass, Data breach |
| **High** | Significant security impact | SQL injection, XSS, Privilege escalation |
| **Medium** | Limited security impact | Information disclosure, CSRF |
| **Low** | Minimal security impact | Minor information leaks, DoS |

### Our Commitment

- We will acknowledge receipt of your vulnerability report
- We will send you regular updates on our progress
- We will credit you in our security advisories (unless you prefer to remain anonymous)
- We will not take legal action against researchers who:
  - Report vulnerabilities in good faith
  - Make a reasonable effort to avoid privacy violations and data destruction
  - Do not exploit vulnerabilities beyond the minimum necessary to demonstrate the issue

## Scope

### In Scope

- Cyber-PI-Intel API (`backend/api/`)
- Authentication and authorization systems (`backend/core/security.py`)
- Database connections and queries (`backend/core/connections.py`)
- ML threat prediction module (`backend/ml/threat_predictor.py`)
- STIX converter (`backend/core/stix_converter.py`)
- All Kubernetes deployment configurations (`deployment/`)

### Out of Scope

- DDoS attacks
- Physical security issues
- Social engineering attacks
- Third-party dependencies (report to the maintainers directly)

## Known Security Issues

We maintain a list of known security issues being addressed:

### Currently Being Fixed

None at this time (as of November 2, 2025)

### Previously Addressed

- **2025-11-02**: Hardcoded credentials removed (v1.0.1)
- **2025-11-02**: JWT secret validation added (v1.0.1)
- **2025-11-02**: CORS wildcard fixed (v1.0.1)

## Security Best Practices

### For Deployers

1. **Use Environment Variables**: Never commit credentials to version control
2. **Generate Strong Secrets**: Use cryptographically secure random values
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(64))'
   ```
3. **Enable TLS**: Use TLS/SSL for all database connections
4. **Restrict CORS**: Set `CORS_ORIGINS` to only your trusted domains
5. **Monitor Logs**: Enable audit logging and review regularly
6. **Update Regularly**: Apply security patches promptly

### For Developers

1. **Input Validation**: Use `InputValidator` class for all user inputs
2. **Parameterized Queries**: Always use parameters for database queries
3. **Security Headers**: Middleware automatically adds security headers
4. **Rate Limiting**: Implement rate limiting on public endpoints
5. **Error Handling**: Never expose sensitive information in error messages
6. **Code Review**: All PRs require security review
7. **Dependency Scanning**: Run `pip-audit` and `bandit` in CI/CD

## Security Tools

We use the following tools to maintain security:

- **Bandit**: Python security linter
  ```bash
  pip install bandit
  bandit -r backend/
  ```

- **Safety**: Dependency vulnerability scanner
  ```bash
  pip install safety
  safety check
  ```

- **pip-audit**: Audit dependencies for known vulnerabilities
  ```bash
  pip install pip-audit
  pip-audit
  ```

## Security Updates

Subscribe to security updates:

- GitHub Security Advisories: Watch this repository
- Security Mailing List: security@cyber-pi-intel.local

## Responsible Disclosure Example

```
Subject: [SECURITY] SQL Injection in /actors/{actor_name} endpoint

Severity: High
Affected Version: 1.0.0
Component: backend/api/threat_intel_api.py

Description:
The /actors/{actor_name} endpoint is vulnerable to SQL injection
through the actor_name parameter.

Steps to Reproduce:
1. Send GET request to /actors/'; DROP TABLE ThreatActor; --
2. Observe database query error
3. Database potentially compromised

Impact:
An unauthenticated attacker can execute arbitrary database queries,
leading to data exfiltration or data loss.

Suggested Fix:
Use parameterized queries with proper input sanitization via
InputValidator.sanitize_neo4j_parameter()

PoC:
curl http://api.example.com/actors/%27%3B%20DROP%20TABLE%20ThreatActor%3B%20--

Reporter: security-researcher@example.com
```

## Hall of Fame

We recognize and thank the following security researchers:

- *Your name could be here!*

## Contact

- **Security Team**: security@cyber-pi-intel.local
- **PGP Key**: (Coming soon)
- **GitHub**: https://github.com/yourusername/cyber-pi-intel

## Legal

This security policy is provided to encourage responsible disclosure of security
vulnerabilities. We reserve the right to modify this policy at any time.

Last Updated: November 2, 2025
