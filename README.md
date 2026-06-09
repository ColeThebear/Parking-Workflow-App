# A&C Parking Management System

A production-ready, role-based parking management web application for campus environments, shopping malls, or any managed parking area. Built with a security-first architecture using FastAPI, React, PostgreSQL, and Docker. Operators, enforcement officers, students, and guests each have a tailored interface with real-time session tracking, enforcement workflows, CSV bulk import, historic data analytics, and interactive Plotly dashboards.

---

## Table of Contents

- [Supported Roles](#supported-roles)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [CSV Import Formats](#csv-import-formats)
- [Production Deployment](#production-deployment)
- [Changelog](#changelog)
- [Security](#security)

---

## Supported Roles

| Role | Description |
|------|-------------|
| **Student (PARKER)** | Register vehicles, start/end parking sessions, view history and balance |
| **Guest** | Temporary parking access with academic-year expiry; can appeal citations |
| **Operator** | Full session management, historic analytics, Plotly dashboards, CSV import |
| **Enforcement** | Plate lookup, issue and track citations across lots |
| **Admin** | Full system access, user management, balance credits, CSV imports |

Admin accounts carry a sub-permission (`full_admin`, `citations_admin`, `events_admin`, `reporting_admin`) that narrows their sidebar navigation accordingly.

---

## Key Features

- **Session Management** — Start, extend, and end parking sessions in real time (1-hour expiry)
- **Live Operator Dashboard** — 4 stat cards auto-refreshing every 10 seconds plus six interactive Plotly charts
- **Historic Sessions** — Import, browse, and filter historic parking data across 9 filter dimensions
- **Interactive Plotly Analytics** — Line, bar, and donut charts with hover tooltips, zoom, and responsive layout
- **Dual-Mode CSV Import** — Bulk student account creation or historic session import with full validation and duplicate detection
- **Citations** — Enforcement officers issue, track, and resolve violations; guests can appeal
- **Enforcement Audit Trail** — Every plate lookup is logged with officer and result
- **Role-Based Routing** — Frontend and API layers both enforce access independently
- **Guest Expiration** — Automatic expiry at next August 1st
- **Token Balance System** — Student parking credits with full transaction audit trail
- **Responsive UI** — Mobile-first layout with collapsible sidebar and Tailwind CSS

---

## Technology Stack

### Frontend

| Package | Version | Purpose |
|---|---|---|
| React | ^19 | UI framework |
| React Router DOM | ^6 | Client-side routing with role-gated `ProtectedRoute` |
| TypeScript | ^4.9 | Static typing across all components |
| Vite | ^7 | Build tool and hot-reload dev server |
| Tailwind CSS | ^3 | Utility-first styling |
| Axios | ^1.6 | HTTP client with JWT auth interceptor and 401/403 handling |
| MUI (Material UI) | ^5 | Supplemental component library |
| **react-plotly.js** | **^2.6** | **Interactive Plotly chart component for React** |
| **plotly.js** | **^2.27** | **Chart engine — line, bar, pie/donut charts** |
| **@types/react-plotly.js** | **^2.6** | **TypeScript declarations for react-plotly.js** |
| Vitest | ^4 | Unit and component testing |
| @testing-library/react | ^16 | Component testing utilities |

### Backend

| Package | Version | Purpose |
|---|---|---|
| FastAPI | >=0.100 | Async web framework with automatic OpenAPI docs |
| Uvicorn | >=0.20 | ASGI server with hot reload |
| SQLAlchemy | >=2.0 | ORM with declarative models |
| psycopg2-binary | >=2.9 | PostgreSQL sync driver |
| python-jose[cryptography] | >=3.3 | JWT creation and verification (HS256) |
| passlib[argon2] | >=1.7 | Password hashing via Argon2 |
| pydantic | >=2.0 | Request/response validation (v2) |
| pydantic-settings | >=2.0 | Settings loading from `.env` with validation |
| email-validator | >=2.0 | `EmailStr` field validation |
| python-multipart | >=0.0.9 | Multipart form data and file upload support |

### Infrastructure

| Tool | Purpose |
|---|---|
| Docker | Containerisation for frontend, backend, and database |
| Docker Compose | Multi-service orchestration |
| PostgreSQL 14 | Primary relational database |
| GitHub Actions | CI/CD — lint, tests, secret scanning on every push |

---

## Project Structure

```
suny-parking/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── parking.py          # ParkingSession + HistoricParkingSession
│   │   │   ├── user.py             # User, UserRole enum
│   │   │   ├── enforcement.py      # EnforcementCheck, Citation
│   │   │   ├── vehicle.py          # RegisteredVehicle
│   │   │   ├── token.py            # TokenBalance, Transaction
│   │   │   └── guest.py            # GuestProfile
│   │   ├── routers/
│   │   │   ├── operator.py         # Sessions, search, import, historic, chart-data
│   │   │   ├── auth.py
│   │   │   ├── parking.py
│   │   │   ├── enforcement.py
│   │   │   ├── admin.py
│   │   │   └── guest.py
│   │   ├── schemas/
│   │   │   └── parking.py          # ParkingSessionOut, HistoricSessionOut, etc.
│   │   ├── utils/                  # security.py, dependencies.py
│   │   ├── database.py
│   │   ├── config.py               # Pydantic settings, .env loading
│   │   └── main.py                 # App factory, DB init, migrations, demo seed
│   ├── scripts/                    # One-off admin utilities
│   ├── tests/                      # pytest integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── operator/
│   │   │   │   ├── Dashboard.tsx        # Stat cards + 6 Plotly charts
│   │   │   │   ├── Sessions.tsx         # Live/today/checks/violations tabs
│   │   │   │   ├── HistoricSessions.tsx # Historic data browser + filters
│   │   │   │   ├── CsvImport.tsx        # Dual-mode: students + historic import
│   │   │   │   └── Search.tsx
│   │   │   ├── student/
│   │   │   ├── enforcement/
│   │   │   ├── admin/
│   │   │   └── guest/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── TopNav.tsx           # A&C Parking branding
│   │   │   │   ├── Sidebar.tsx          # Role-based nav with Historic Sessions link
│   │   │   │   └── Layout.tsx
│   │   │   └── ui/                      # Button, Card, Badge, Alert, Input, Spinner, Icons
│   │   ├── auth/                        # AuthContext, ProtectedRoute
│   │   └── api/                         # Axios client with JWT interceptor
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── example.env                          # Template — copy to .env and populate
├── example.env.production               # Production env template
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recommended)
- Or Python 3.11+ and Node 20+ for local development

### Quick Start (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/ColeThebear/Parking-Workflow-App.git
cd Parking-Workflow-App

# 2. Create your environment file from the template
cp example.env .env
# Open .env and set DB_PASSWORD and SECRET_KEY

# 3. Build and start all services
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5178 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### Demo Credentials

All demo accounts use the password `Test123!`

| Email | Role | Notes |
|---|---|---|
| `admin@suny.edu` | Admin (full) | Full system access |
| `citadmin@suny.edu` | Admin (citations) | Citations tab only |
| `operator@suny.edu` | Operator | Dashboard, sessions, import, historic |
| `officer1@suny.edu` | Enforcement | Plate lookup, citations |
| `jsmith@suny.edu` | Student | Plate: ABC1234 |
| `mjones@suny.edu` | Student | Plate: XYZ5678 |

> **Security note:** Remove or rotate all default credentials before any production deployment.

---

## Environment Variables

Copy `example.env` to `.env` in the project root. **Never commit `.env` or `backend/.env`** — both are gitignored.

| Variable | Required | Description |
|---|---|---|
| `DB_PASSWORD` | Yes | PostgreSQL password used by Compose and the backend DATABASE_URL |
| `SECRET_KEY` | Yes | JWT signing key — minimum 32 characters |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token lifetime in minutes (default: 1440) |

Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

For local (non-Docker) backend development, create `backend/.env`:

```
DATABASE_URL=postgresql+psycopg2://user:${DB_PASSWORD}@localhost:5432/dbname
SECRET_KEY=<your-generated-key>
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## Running the App

### Docker Compose (recommended)

```bash
# Start all services
docker-compose up --build

# Stop containers
docker-compose down

# Full reset — stops containers and removes the database volume
docker-compose down -v
```

### Local Development

**Backend** (requires PostgreSQL running locally):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
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

## CSV Import Formats

The operator's **Import** page (`/operator/import`) supports two modes selectable via tabs.

### Mode 1 — Student Import

Bulk-creates student (PARKER) accounts:

```csv
email,plate,password
student@domain.edu,ABC1234,Temp123!
another@domain.edu,XYZ9876
```

- `plate` and `password` are optional (default password: `Temp123!`)
- Duplicate detection: skips rows where the email or plate already exists

### Mode 2 — Historic Session Import

Imports historic parking records into the `historic_parking_sessions` table for analytics and reporting:

```csv
plate,zone,started_at,ended_at,user_type,session_type,payment_type,enforcement_status,notes
ABC1234,Lot A,2024-01-15 08:00,2024-01-15 09:30,STUDENT,STANDARD,TOKEN,NONE,
XYZ9876,Lot B,2024-01-15 10:00,,GUEST,EVENT,FREE,CHECKED,Event parking
```

| Column | Required | Valid Values |
|---|---|---|
| `plate` | Yes | Any alphanumeric plate |
| `zone` | Yes | Free text zone name (e.g. `Lot A`) |
| `started_at` | Yes | `YYYY-MM-DD HH:MM` |
| `ended_at` | No | `YYYY-MM-DD HH:MM` — duration is auto-calculated |
| `user_type` | No | `STUDENT` · `GUEST` · `UNREGISTERED` |
| `session_type` | No | `STANDARD` · `PERMIT` · `EVENT` |
| `payment_type` | No | `TOKEN` · `CASH` · `CARD` · `FREE` |
| `enforcement_status` | No | `NONE` · `CHECKED` · `CITED` |
| `notes` | No | Free text |

Duplicate detection: same `plate` + `started_at` combination is skipped with an explanation.

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All environment variables set in `.env` (use `example.env.production` as template)
- [ ] `SECRET_KEY` is at least 64 characters, randomly generated
- [ ] `DB_PASSWORD` is a strong, unique password
- [ ] Default seed accounts removed or passwords changed
- [ ] HTTPS configured via reverse proxy (Nginx or Traefik)
- [ ] CORS restricted to your production domain in `backend/app/main.py`
- [ ] Docker images built and tested locally before deploy
- [ ] `SECURITY.md` checklist reviewed

### Server Setup

```bash
# 1. Install Docker
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER

# 2. Configure environment
cp example.env.production .env
# Edit .env with real production values

# 3. Build and start
docker compose up --build -d

# 4. Verify
curl http://localhost:8000/health
docker compose logs -f backend
```

### Nginx Reverse Proxy

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

### Automated DB Backups

```bash
# Add to crontab — daily backup at 2 AM
0 2 * * * docker exec suny_db pg_dump -U postgres suny_dev > /backups/parking-$(date +\%F).sql
```

---

## Changelog

### 2026-06-09 — Historic Sessions, Plotly Dashboards, A&C Branding

#### Branding (all roles)
- Replaced all visible **SUNY** references in the UI with **A&C** across every role
- Updated: `TopNav` header brand, `Login` page title
- Email addresses (`*@suny.edu`) and backend identifiers are intentionally unchanged

#### Operator: Historic Sessions (new)
- New `historic_parking_sessions` database table — created automatically on first startup via `Base.metadata.create_all`
- New page at `/operator/historic` — **Historic Sessions** browser with a 9-dimension filter panel:
  - Date from / Date to
  - License plate (partial match)
  - User type (`STUDENT` / `GUEST` / `UNREGISTERED`)
  - Zone
  - Session type (`STANDARD` / `PERMIT` / `EVENT`)
  - Payment type (`TOKEN` / `CASH` / `CARD` / `FREE`)
  - Enforcement status (`NONE` / `CHECKED` / `CITED`)
  - Duration min / Duration max (in minutes)
- Paginated results table — 50 rows per page with a **Load more** button
- Colour-coded `Badge` components for payment type and enforcement status
- **Historic Sessions** nav item added to the operator sidebar (clock icon)
- Route registered at `/operator/historic` with `OPERATOR` role protection

#### Operator: CSV Import — Historic Mode (new tab)
- Import page now has two tabs: **Import Students** and **Import Historic Sessions**
- Historic tab shows an amber-coloured format guide with all valid column values
- Backend validates all enum fields, calculates `duration_minutes` automatically from `started_at` / `ended_at`
- Duplicate detection: same `plate` + `started_at` skipped with a reason
- Both modes return a per-row summary card: added count, skipped duplicates with reasons, errors with reasons and row numbers

#### Operator: Plotly Analytics Dashboard (new)
- Added `react-plotly.js` and `plotly.js` to the frontend dependency stack
- Dashboard now fetches `/operator/chart-data` alongside `/operator/stats` in a single parallel call
- Six interactive Plotly charts added in a card-based layout below the stat cards:

| # | Chart | Type | Data Source |
|---|---|---|---|
| 1 | Sessions per Day — Last 30 Days | Dual-series line (live + historic) | `parking_sessions` + `historic_parking_sessions` |
| 2 | Sessions by Zone | Horizontal bar | `parking_sessions` (all time) |
| 3 | User Type Distribution | Donut | `historic_parking_sessions` |
| 4 | Payment Type Distribution | Donut | `historic_parking_sessions` |
| 5 | Enforcement Status Breakdown | Bar | `historic_parking_sessions` |
| 6 | Session Type Distribution | Donut | `historic_parking_sessions` |

- Charts are fully interactive: hover tooltips, zoom, pan, download
- All charts display a graceful **"No data yet"** placeholder before any historic data is imported
- Responsive — auto-scales to container width on mobile and desktop
- Colour palette matches the operator green theme (`#15803d`, `#1d4ed8`, `#d97706`, `#dc2626`)

#### New Backend API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/operator/historic-sessions` | OPERATOR | Filtered + paginated historic session list (9 query params) |
| `POST` | `/operator/import-historic` | OPERATOR | Historic session CSV bulk import with validation |
| `GET` | `/operator/chart-data` | OPERATOR | Aggregated data for all six Plotly dashboard charts |

#### New DB Model — `HistoricParkingSession`

```
historic_parking_sessions
  id                 INTEGER PK
  vehicle_plate      VARCHAR  (indexed)
  zone               VARCHAR
  started_at         TIMESTAMPTZ
  ended_at           TIMESTAMPTZ  (nullable)
  duration_minutes   INTEGER      (nullable, auto-calculated on import)
  user_type          VARCHAR  default STUDENT
  session_type       VARCHAR  default STANDARD
  payment_type       VARCHAR  default FREE
  enforcement_status VARCHAR  default NONE
  notes              VARCHAR  (nullable)
  user_id            INTEGER FK → users (nullable)
  imported_at        TIMESTAMPTZ
```

#### Security & Repository Hygiene
- `.gitignore` updated to exclude `*_mock.csv` and `historic_sessions_mock.csv`
- All `.env` files, `backend/.env`, and import CSV files remain excluded from version control

---

## Security

See [SECURITY.md](SECURITY.md) for the full vulnerability reporting process and deployment checklist.

Key security properties:

- **JWT secrets** stored in environment variables only — never in source code
- **Passwords** hashed with Argon2 via passlib — no plain-text storage at any layer
- **SQL injection** protected by SQLAlchemy ORM parameterized queries
- **CORS** restricted to configured origins (`localhost:5173`, `localhost:5178` in dev)
- **Role enforcement** applied at the API layer via FastAPI `Depends` — frontend routing is a UX layer only
- **File upload validation** — only `.csv` files accepted; UTF-8 with BOM stripping applied
- **Secret scanning** runs on every push via GitHub Actions
- **Never** commit `.env`, `backend/.env`, or any file containing real credentials — all are gitignored
- For production: rotate `SECRET_KEY` and `DB_PASSWORD` and store in a secrets manager

---

## License

See [LICENSE](LICENSE). All rights reserved — no redistribution without written permission from the copyright owner.
