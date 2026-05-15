# SUNY Parking Workflow App

A production-ready, role-based parking management system for SUNY campuses. Built with a security-first architecture using FastAPI, React, PostgreSQL, and Docker.

---

## Overview

The SUNY Parking Workflow App manages the full lifecycle of campus parking — from student and guest session registration through enforcement, citations, and operator controls. All access is governed by JWT-based authentication with strict role separation at both the API and frontend routing layers.

---

## Supported Roles

| Role | Description |
|------|-------------|
| **Student (PARKER)** | Register vehicles, start/end parking sessions, view permits |
| **Guest** | Temporary parking access via time-limited tokens with configurable expiry |
| **Operator** | Manage lots, issue permits, view session activity, POS operations |
| **Enforcement** | Scan plates, issue citations, view active sessions across lots |
| **Admin** | Full system access, user management, CSV imports, audit logs |

---

## Key Features

- **Session Management** — Start, extend, and end parking sessions in real time
- **Citations** — Enforcement officers can issue, track, and resolve violations
- **Permits** — Student and guest permit issuance with expiration logic
- **POS Integration** — Operator point-of-sale flow for lot and permit management
- **CSV Import** — Bulk student and guest import via sanitized CSV upload (Admin)
- **Event Parking** — Temporary lot assignments for campus events
- **Role-Based Routing** — Frontend enforces role-gated page access
- **Guest Expiration** — Automatic guest session expiry with configurable TTL

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend API | FastAPI (Python 3.11) |
| Frontend | React 19 + TypeScript + Vite |
| Database | PostgreSQL 14 (via SQLAlchemy 2.0) |
| Authentication | JWT (python-jose) + bcrypt (passlib) |
| Styling | Tailwind CSS |
| Containerization | Docker + Docker Compose |
| Testing | Pytest (backend), Vitest (frontend) |

---

## Folder Structure

```
/
├── frontend/                   React/TypeScript SPA
│   ├── src/
│   │   ├── api/                Typed API client
│   │   ├── auth/               Auth context, guards, protected routes
│   │   ├── components/         Shared UI components
│   │   ├── context/            Global state (auth, toast)
│   │   ├── pages/              Role-gated page views
│   │   └── test/               Vitest test suite
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── Dockerfile
│
├── backend/                    FastAPI application
│   ├── app/
│   │   ├── routers/            Route handlers (auth, parking, enforcement,
│   │   │                       operator, admin, guest, permits)
│   │   ├── models/             SQLAlchemy ORM models
│   │   ├── schemas/            Pydantic request/response schemas
│   │   ├── utils/              Security helpers, dependencies, auth logic
│   │   ├── config.py           Pydantic settings (env-driven, validated)
│   │   ├── database.py         DB session factory
│   │   └── main.py             App entry point + startup migrations
│   ├── db/                     Seed SQL scripts
│   ├── scripts/                CLI utilities (seed data, password tools)
│   ├── tests/                  Pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml          Orchestrates all services (no hardcoded secrets)
├── example.env                 Environment variable template — copy to .env
├── example.env.production      Production environment template
├── .gitignore
├── .dockerignore
├── SECURITY.md
├── LICENSE
└── README.md
```

---

## Quick Start (Development)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git

### 1. Clone the repo

```bash
git clone https://github.com/ColeThebear/Parking-Workflow-App.git
cd Parking-Workflow-App
```

### 2. Set up environment variables

```bash
cp example.env .env
```

Open `.env` and set:
- `DB_PASSWORD` — any strong password for local dev
- `SECRET_KEY` — generate with the command below

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as the value of `SECRET_KEY` in `.env`.

### 3. Start all services

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5178 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### 4. Default development accounts

> These accounts are seeded automatically when the `users` table is empty on first startup.

| Email | Password | Role |
|-------|----------|------|
| student1@suny.edu | Test123! | PARKER |
| student2@suny.edu | Test123! | PARKER |
| officer1@suny.edu | Test123! | ENFORCEMENT |
| operator@suny.edu | Test123! | OPERATOR |

> **Security note:** Remove or rotate all default credentials before any deployment.

### 5. Reseed or add test data

```bash
cd backend
python scripts/seed_mock_data.py
```

---

## Running Tests

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All environment variables configured in `.env` (use `example.env.production` as template)
- [ ] `SECRET_KEY` is at least 64 characters, randomly generated
- [ ] `DB_PASSWORD` is a strong, unique password
- [ ] Default seed accounts removed or passwords changed
- [ ] HTTPS configured via reverse proxy (Nginx or Traefik)
- [ ] CORS restricted to your production domain
- [ ] Docker images built and tested locally before deploy
- [ ] Full `SECURITY.md` checklist reviewed

### Server Setup

**1. Install Docker**
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

**2. Configure Nginx reverse proxy**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /api/ {
        proxy_pass         http://localhost:8000/;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        proxy_pass http://localhost:5178/;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}
```

**3. Obtain SSL certificates**
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

**4. Configure firewall**
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirect to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
# Do NOT open 8000, 5432, or 5178 publicly
```

### Deployment Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Configure environment
cp example.env.production .env
# Edit .env with real production values

# 3. Build and start containers
docker compose up --build -d

# 4. Verify backend health
curl http://localhost:8000/health

# 5. Tail logs to confirm clean startup
docker compose logs -f backend
```

### Post-Deployment

**Log rotation** — create `/etc/logrotate.d/suny-parking`:
```
/var/log/suny-parking/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
}
```

**Automated DB backups** — add to crontab (`crontab -e`):
```bash
# Daily PostgreSQL backup at 2 AM
0 2 * * * docker exec suny_db pg_dump -U postgres suny_dev > /backups/suny-$(date +\%F).sql
```

**Monitoring** — add `sentry-sdk[fastapi]` to `requirements.txt` and set `SENTRY_DSN` in `.env`.

**Security audit cycle** — review `SECURITY.md` checklist monthly and after any dependency update.

---

## Security

See [SECURITY.md](SECURITY.md) for:
- Vulnerability reporting process
- Full pre-deployment security checklist
- Architecture overview
- Known limitations

Key security properties:
- JWT secrets stored in environment variables only — never in source code
- Passwords hashed with bcrypt via passlib
- SQL injection protected via SQLAlchemy ORM parameterization
- CORS restricted to configured origins
- Role-based access enforced at API and frontend routing layers
- CSV imports sanitized before DB insertion
- Pre-push hook blocks accidental secret commits
- GitHub Actions secret scanning on every push and PR

---

## License

See [LICENSE](LICENSE). All rights reserved — no redistribution without written permission from the copyright owner.
