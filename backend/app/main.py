from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.database import get_db
from app.db.database import Base, engine

from app.models.user import User
from app.api.auth import router as auth_router
from app.models.user_session import UserSession

from app.models.vehicle import Vehicle
from app.api.vehicles import router as vehicles_router

from app.models.maintenance_record import MaintenanceRecord
from app.api.maintenance import router as maintenance_router

app = FastAPI(title="PocketMechanic API")
app.include_router(auth_router)
app.include_router(vehicles_router)
app.include_router(maintenance_router)

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/db-health")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}
