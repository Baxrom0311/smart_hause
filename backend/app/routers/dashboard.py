from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Anomaly, SensorData, TrainingHistory
from app.models.schemas import DashboardSummary, LatestModelSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)):
    total_sensor_data = db.query(SensorData).count()
    total_anomalies = db.query(Anomaly).filter(Anomaly.is_anomaly.is_(True)).count()
    sensor_types = [
        sensor_type
        for (sensor_type,) in db.query(SensorData.sensor_type)
        .distinct()
        .order_by(SensorData.sensor_type)
        .all()
    ]

    latest_anomaly_row = (
        db.query(Anomaly)
        .filter(Anomaly.is_anomaly.is_(True))
        .order_by(Anomaly.detected_at.desc())
        .first()
    )
    latest_training = db.query(TrainingHistory).order_by(TrainingHistory.created_at.desc()).first()

    latest_model = None
    if latest_training:
        latest_model = LatestModelSummary(
            id=latest_training.id,
            name=latest_training.model_name,
            accuracy=latest_training.accuracy,
            f1=latest_training.f1,
            created_at=latest_training.created_at,
        )

    anomaly_percentage = (total_anomalies / total_sensor_data * 100) if total_sensor_data else 0.0
    return DashboardSummary(
        total_sensor_data=total_sensor_data,
        total_anomalies=total_anomalies,
        anomaly_percentage=anomaly_percentage,
        sensor_types=sensor_types,
        latest_anomaly=latest_anomaly_row.detected_at if latest_anomaly_row else None,
        latest_model=latest_model,
    )
