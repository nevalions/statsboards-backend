# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| master  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** create a public issue
2. Email details to the maintainers privately
3. Include steps to reproduce and impact assessment
4. Allow time for the fix to be developed and tested

## Recent Security Updates

### 2026-01-19 - aiohttp Zip Bomb Vulnerability (GHSA-vvjp-jh4p-6p3g)
- **Severity**: High
- **Affected**: aiohttp <= 3.13.2
- **Fixed**: Upgraded to aiohttp 3.13.3
- **Impact**: Memory exhaustion from malicious compressed requests
- **CVE**: Pending
- **Details**: HTTP Parser auto_decompress feature vulnerable to zip bomb DoS attacks

### 2026-01-17 - pyasn1 DoS Vulnerability (GHSA-7q9g-r576-3hj8)
- **Severity**: Medium
- **Affected**: pyasn1 v0.6.1
- **Fixed**: Upgraded to pyasn1 v0.6.2
- **Impact**: Memory exhaustion from malformed RELATIVE-OID with excessive continuation octets in the decoder
- **CVE**: Pending
- **Commit**: e3ceb97

### Previous Security Updates
- 2025: aiohttp 3.11.11 upgrade (CVE-2024-30251)
- 2025: FastAPI, Starlette, python-multipart upgrades (DoS vulnerabilities)
- 2025: Image filename sanitization (path traversal prevention)
- 2025: Error message sanitization (information disclosure prevention)

## Security Best Practices

- Keep dependencies updated regularly
- Use Dependabot alerts for vulnerability notifications
- Run security scans before deploying
- Sanitize all user inputs
- Use parameterized queries for database access
- Implement proper authentication and authorization
- Keep secrets out of code repositories

## Dependency Management

We use Poetry for dependency management. Security updates are handled via:

```bash
# Update a specific package
poetry update <package-name>

# Check for outdated packages
poetry show --outdated

# Run tests after dependency updates
pytest
```

All dependency updates must pass the full test suite before being committed.
