from fastapi import FastAPI
from contextlib import asynccontextmanager
import time
from .database import Base, engine
from .models import user, parking
from .routers import auth, parking as parking_router

# Initialize database with retries
def init_db_with_retries(max_retries=5, delay=2):
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Database connection failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"Failed to initialize database after {max_retries} attempts: {e}")
                raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db_with_retries()
    yield
    # Shutdown
    pass

app = FastAPI(title="SUNY Parking Dev API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(parking_router.router)

@app.get("/")
def root():
    return {"message": "SUNY Parking Dev API running"}
