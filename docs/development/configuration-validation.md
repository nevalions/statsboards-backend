# Configuration Validation

Configuration validation runs automatically on startup. Summary:

- Database settings validation (required fields, port range, connection strings)
- Application settings validation (CORS origins format, SSL file pairing)
- Path validation (static, uploads, templates, SSL)
- Database connectivity checks (version, database name, user)

Manual validation:

```bash
python validate_config.py
```

See `docs/CONFIGURATION_VALIDATION.md` for the full reference.
