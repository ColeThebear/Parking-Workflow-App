# Security Policy

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report privately by contacting the maintainer: cole.abrahams0@gmail.com

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Any suggested remediation

We will respond within 72 hours and work toward a fix promptly.

---

## Security Audit Checklist

Use this checklist before every deployment and after any significant code or dependency change.

### Backend

- [ ] `SECRET_KEY` is stored in environment variables only — never in source code or version control
- [ ] `SECRET_KEY` is at least 64 characters, randomly generated
      (`python -c "import secrets; print(secrets.token_hex(64))"`)
- [ ] No secrets exist in any committed file or git history
- [ ] No secrets exposed in frontend source code or build artifacts
- [ ] HTTPS is enforced at the reverse proxy layer — all HTTP redirects to HTTPS
- [ ] CORS `allow_origins` is restricted to known frontend origins (never `*` in production)
- [ ] All passwords are hashed with bcrypt via `passlib` — no plaintext storage
- [ ] SQL injection is mitigated — all DB queries use SQLAlchemy ORM parameterization
- [ ] CSV import data is validated and sanitized before database insertion
- [ ] Guest session expiration logic is verified — expired tokens are rejected at the API layer
- [ ] JWT tokens are validated on every protected endpoint
- [ ] `ACCESS_TOKEN_EXPIRE_MINUTES` is appropriately short for production (recommend ≤ 60)
- [ ] Default seed accounts are removed or passwords changed before any deployment

### Frontend

- [ ] No hardcoded backend URLs in source — all via `VITE_BACKEND_URL` environment variable
- [ ] No sensitive values logged to the browser console in production builds
- [ ] No JWT tokens or secrets exposed in client-side code or comments
- [ ] Role-based routing is enforced — unauthenticated users cannot access protected routes
- [ ] API responses are validated before rendering — no raw server error messages shown to users
- [ ] Frontend dependencies audited: `npm audit` shows no high/critical vulnerabilities

### Infrastructure

- [ ] Docker containers do not run as root (or this risk is explicitly acknowledged)
- [ ] PostgreSQL port (`5432`) is **not** publicly exposed — accessible only within Docker network
- [ ] Backend port (`8000`) is **not** publicly exposed in production — only via reverse proxy
- [ ] Frontend port (`5178`) is **not** publicly exposed in production — only via reverse proxy
- [ ] SSL/TLS certificates are valid and auto-renewed (Let's Encrypt / Certbot recommended)
- [ ] Firewall allows only ports 22 (SSH), 80 (redirect), 443 (HTTPS)
- [ ] Database backups are scheduled and tested for restorability
- [ ] Application logs are enabled and rotated
- [ ] Monitoring is configured (Sentry, Datadog, or equivalent)
- [ ] Docker base images are pinned to specific versions — not `latest`

### Repository

- [ ] `.env` is listed in `.gitignore` and has never been committed
- [ ] `.env.production` is listed in `.gitignore` and has never been committed
- [ ] No log files are committed to the repository
- [ ] No database dump or seed files with real data are committed
- [ ] No sensitive CSV files (student or guest imports) are committed
- [ ] `docker-compose.yml` contains no hardcoded credentials — all values sourced from `.env`
- [ ] Pre-push hook (`.git/hooks/pre-push`) is installed and active
- [ ] GitHub Actions secret scanning workflow is active and passing on all PRs

---

## Security Architecture

### Authentication Flow

```
Client  →  POST /auth/token  →  JWT issued (HS256, configurable expiry)
           All protected routes  →  Bearer token validated on each request
           Role extracted from token  →  Route-level permission enforced
```

### Secret Management

- All secrets loaded via environment variables using `pydantic-settings`
- Application validates `SECRET_KEY` length at startup — refuses to start if too short
- No secrets baked into Docker images — injected at runtime via `docker-compose` environment block

### Database Security

- Credentials never hardcoded — sourced from `${DB_PASSWORD}` at container runtime
- SQLAlchemy ORM parameterization prevents SQL injection by default
- Database not exposed on public network interfaces

### Role Separation

| Role        | Access Level                                              |
|-------------|-----------------------------------------------------------|
| PARKER      | Own sessions, vehicle registration, permit view           |
| GUEST       | Temporary sessions, time-limited access                   |
| ENFORCEMENT | Read all active sessions, issue and view citations        |
| OPERATOR    | Manage lots, issue permits, view all sessions, POS        |
| ADMIN       | Full system access, user management, CSV import, audit    |

---

## Known Limitations

- Alembic migrations are not yet configured — schema changes are applied via `migrate_columns()`
  in `main.py`. A proper Alembic setup is planned for a future release.
- `app/services/` separation layer is not yet implemented — business logic lives in routers.
- Rate limiting is not currently applied to authentication endpoints (`/auth/token`).
  Consider adding `slowapi` or a reverse-proxy-level rate limiter before production deployment.

---

## Dependency Security

Run regularly and before each release:

```bash
# Backend — requires pip-audit
pip install pip-audit
pip-audit -r backend/requirements.txt

# Frontend
cd frontend && npm audit
```
