import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .utils.rate_limit import limiter
from .utils.exceptions import AppError, app_error_handler
from .config import get_settings as _get_settings
from .utils.logging_config import configure_logging, CorrelationIdMiddleware, RequestLoggingMiddleware
from .utils.csrf import CSRFMiddleware

_settings = _get_settings()
configure_logging(json_logs=_settings.LOG_JSON)

if _settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=_settings.SENTRY_DSN,
        environment=_settings.ENVIRONMENT,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

from .database import Base, engine
from .models import user, parking, enforcement, vehicle, token, guest   # registers all models
from .routers import auth, parking as parking_router, enforcement as enforcement_router, operator, admin, guest as guest_router

logger = logging.getLogger(__name__)


def init_db_with_retries(max_retries: int = 5, delay: int = 2) -> None:
    """Create all tables, retrying if the DB isn't ready yet."""
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified.")
            return
        except Exception:
            if attempt < max_retries - 1:
                logger.warning("DB not ready (attempt %d/%d), retrying in %ds…",
                               attempt + 1, max_retries, delay)
                time.sleep(delay)
            else:
                logger.error("Failed to connect to database after %d attempts.", max_retries)
                raise


def migrate_columns() -> None:
    """Idempotent column migrations — safe to run on every startup."""
    from sqlalchemy import text

    # ALTER TYPE … ADD VALUE cannot run inside a transaction in PostgreSQL.
    # Execute these with AUTOCOMMIT isolation before the regular migrations.
    enum_stmts = [
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'ADMIN'",
        "ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'GUEST'",
    ]
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for stmt in enum_stmts:
            conn.execute(text(stmt))

    # Regular DDL — safe inside a transaction
    column_stmts = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS terminated_by_operator BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS admin_permission VARCHAR",
        "ALTER TABLE parking_sessions ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ",
        "ALTER TABLE token_balances ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1",
    ]
    index_stmts = [
        "CREATE INDEX IF NOT EXISTS ix_session_plate_active ON parking_sessions (vehicle_plate, active)",
        "CREATE INDEX IF NOT EXISTS ix_check_officer_time ON enforcement_checks (officer_id, checked_at)",
        "CREATE INDEX IF NOT EXISTS ix_citation_officer_time ON citations (officer_id, issued_at)",
    ]

    with engine.connect() as conn:
        for stmt in column_stmts:
            conn.execute(text(stmt))
        for stmt in index_stmts:
            conn.execute(text(stmt))
        conn.commit()
    logger.info("Column migrations applied.")


def seed_default_users() -> None:
    """
    Seed demo accounts only when the users table is empty.

    Demo credentials (all passwords: Test123!):
        Admin accounts:
            admin@suny.edu          — ADMIN  (full_admin)
            citadmin@suny.edu       — ADMIN  (citations_admin)

        Student accounts (PARKER):
            jsmith@suny.edu         plate: ABC1234
            mjones@suny.edu         plate: XYZ5678
            abrown@suny.edu         plate: LMN3344
            tdavis@suny.edu         plate: QPR7890
            kwilson@suny.edu        plate: HJK2211
            lmartinez@suny.edu      plate: EFG4455
            rtaylor@suny.edu        plate: UVW6677
            shanks@suny.edu         plate: BCD8899
            panderson@suny.edu      plate: NOP1122
            ctaylor@suny.edu        plate: STU3366

        Other roles:
            officer1@suny.edu       — ENFORCEMENT
            operator@suny.edu       — OPERATOR
    """
    from .database import SessionLocal
    from .models.user import User, UserRole
    from .models.token import TokenBalance
    from .models.vehicle import RegisteredVehicle
    from .utils.security import hash_password

    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return

        logger.info("Seeding default demo users…")

        pw = hash_password("Test123!")

        accounts = [
            # Admins
            {"email": "admin@suny.edu",      "name": "System Administrator", "role": UserRole.ADMIN,       "admin_permission": "full_admin",       "plate": None},
            {"email": "citadmin@suny.edu",   "name": "Citations Manager",    "role": UserRole.ADMIN,       "admin_permission": "citations_admin",  "plate": None},
            # Officers / Operators
            {"email": "officer1@suny.edu",   "name": "Officer Rivera",       "role": UserRole.ENFORCEMENT, "admin_permission": None, "plate": None},
            {"email": "operator@suny.edu",   "name": "Lot Operator",         "role": UserRole.OPERATOR,    "admin_permission": None, "plate": None},
            # Students
            {"email": "jsmith@suny.edu",     "name": "James Smith",          "role": UserRole.PARKER,      "admin_permission": None, "plate": "ABC1234"},
            {"email": "mjones@suny.edu",     "name": "Maria Jones",          "role": UserRole.PARKER,      "admin_permission": None, "plate": "XYZ5678"},
            {"email": "abrown@suny.edu",     "name": "Alex Brown",           "role": UserRole.PARKER,      "admin_permission": None, "plate": "LMN3344"},
            {"email": "tdavis@suny.edu",     "name": "Taylor Davis",         "role": UserRole.PARKER,      "admin_permission": None, "plate": "QPR7890"},
            {"email": "kwilson@suny.edu",    "name": "Kai Wilson",           "role": UserRole.PARKER,      "admin_permission": None, "plate": "HJK2211"},
            {"email": "lmartinez@suny.edu",  "name": "Laura Martinez",       "role": UserRole.PARKER,      "admin_permission": None, "plate": "EFG4455"},
            {"email": "rtaylor@suny.edu",    "name": "Ryan Taylor",          "role": UserRole.PARKER,      "admin_permission": None, "plate": "UVW6677"},
            {"email": "shanks@suny.edu",     "name": "Sam Hanks",            "role": UserRole.PARKER,      "admin_permission": None, "plate": "BCD8899"},
            {"email": "panderson@suny.edu",  "name": "Pat Anderson",         "role": UserRole.PARKER,      "admin_permission": None, "plate": "NOP1122"},
            {"email": "ctaylor@suny.edu",    "name": "Casey Taylor",         "role": UserRole.PARKER,      "admin_permission": None, "plate": "STU3366"},
        ]

        for acct in accounts:
            new_user = User(
                email=acct["email"],
                name=acct["name"],
                password_hash=pw,
                role=acct["role"],
                admin_permission=acct["admin_permission"],
            )
            db.add(new_user)
            db.flush()

            if acct["role"] == UserRole.PARKER:
                db.add(TokenBalance(user_id=new_user.id, balance=0))
                if acct["plate"]:
                    db.add(RegisteredVehicle(user_id=new_user.id, plate=acct["plate"]))

        db.commit()
        logger.info("Seeded %d demo users.", len(accounts))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_with_retries()
    migrate_columns()
    seed_default_users()
    yield


app = FastAPI(title="SUNY Parking API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppError, app_error_handler)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CSRFMiddleware)


@app.middleware("http")
async def init_rate_limit_state(request: Request, call_next):
    # slowapi writes request.state.view_rate_limit only on rate-limited routes.
    # Pre-initialise to None so undecorated routes don't raise AttributeError.
    request.state.view_rate_limit = None
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5178",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Added last so it runs outermost — request_id is set before any other
# middleware or route handler logs anything.
app.add_middleware(CorrelationIdMiddleware)

_v1 = APIRouter(prefix="/v1")
_v1.include_router(auth.router)
_v1.include_router(parking_router.router)
_v1.include_router(enforcement_router.router)
_v1.include_router(operator.router)
_v1.include_router(admin.router)
_v1.include_router(guest_router.router)
app.include_router(_v1)


@app.get("/", tags=["health"])
def root():
    return {"message": "SUNY Parking API running"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
