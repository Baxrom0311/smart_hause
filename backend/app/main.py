import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.database import Base, engine, ensure_sqlite_schema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from app.routers import anomaly, dashboard, data, model

Base.metadata.create_all(bind=engine)
ensure_sqlite_schema()

app = FastAPI(title="Smart Home Anomaly Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(data.router, prefix="/api/data", tags=["Data"])
app.include_router(model.router, prefix="/api/model", tags=["Model"])
app.include_router(anomaly.router, prefix="/api/anomaly", tags=["Anomaly"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/")
def root():
    return {"message": "Smart Home Anomaly Detection API"}


@app.get("/health")
def health():
    return {"status": "ok"}
