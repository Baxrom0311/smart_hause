import csv
from io import StringIO
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Anomaly, SensorData, TrainingHistory
from app.models.schemas import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AnomalyListResponse,
    AnomalyResponse,
    AnomalyStats,
)
from app.services.anomaly_detector import run_anomaly_detection

router = APIRouter()


def _safe_export_name(prefix: str, sensor_type: str | None, source_file: str | None) -> str:
    label = source_file.rsplit(".", 1)[0] if source_file else sensor_type or "all"
    label = re.sub(r"[^a-zA-Z0-9_.-]+", "_", label).strip("_") or "all"
    return f"{prefix}_{label}.csv"


def _severity_score(anomaly_score: float, threshold: float) -> float:
    if threshold <= 0:
        return 0.0
    return float(anomaly_score / threshold)


def _iter_anomaly_csv(rows):
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "sensor_data_id",
            "training_history_id",
            "timestamp",
            "value",
            "reconstructed_value",
            "anomaly_score",
            "severity_score",
            "threshold",
            "is_anomaly",
            "sensor_type",
            "source_file",
            "detected_at",
        ]
    )
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for anomaly, sensor in rows:
        writer.writerow(
            [
                anomaly.id,
                anomaly.sensor_data_id,
                anomaly.training_history_id or "",
                sensor.timestamp.isoformat(),
                sensor.value,
                anomaly.reconstructed_value if anomaly.reconstructed_value is not None else "",
                anomaly.anomaly_score,
                _severity_score(anomaly.anomaly_score, anomaly.threshold),
                anomaly.threshold,
                int(bool(anomaly.is_anomaly)),
                sensor.sensor_type,
                sensor.source_file,
                anomaly.detected_at.isoformat() if anomaly.detected_at else "",
            ]
        )
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


@router.post("/detect", response_model=AnomalyDetectionResponse)
def detect(request: AnomalyDetectionRequest, db: Session = Depends(get_db)):
    training_query = db.query(TrainingHistory).filter(TrainingHistory.sensor_type == request.sensor_type)
    if request.training_id is not None:
        training_query = training_query.filter(TrainingHistory.id == request.training_id)
        training = training_query.order_by(TrainingHistory.created_at.desc()).first()
    elif request.source_file:
        training = (
            training_query.filter(TrainingHistory.source_file == request.source_file)
            .order_by(TrainingHistory.created_at.desc())
            .first()
        )
        if not training:
            training = (
                training_query.filter(TrainingHistory.source_file.is_(None))
                .order_by(TrainingHistory.created_at.desc())
                .first()
            )
    else:
        training = training_query.order_by(TrainingHistory.created_at.desc()).first()
    if not training:
        raise HTTPException(status_code=404, detail="Mos trening topilmadi.")
    if request.source_file and training.source_file and training.source_file != request.source_file:
        raise HTTPException(
            status_code=400,
            detail="Tanlangan trening boshqa dataset uchun yaratilgan.",
        )

    try:
        result = run_anomaly_detection(
            db,
            request.sensor_type,
            training,
            source_file=request.source_file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AnomalyDetectionResponse(
        sensor_type=request.sensor_type,
        source_file=result.get("source_file"),
        training_id=int(result["training_id"]),
        threshold=float(result["threshold"]),
        total_windows=int(result["total_windows"]),
        anomalies_detected=int(result["anomalies_detected"]),
    )


@router.get("/results", response_model=AnomalyListResponse)
def results(
    sensor_type: str | None = None,
    source_file: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Anomaly, SensorData).join(SensorData, SensorData.id == Anomaly.sensor_data_id)
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)
    if source_file:
        query = query.filter(SensorData.source_file == source_file)

    total = query.count()
    rows = (
        query.order_by(SensorData.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    items = [
        AnomalyResponse(
            id=anomaly.id,
            sensor_data_id=anomaly.sensor_data_id,
            training_history_id=anomaly.training_history_id,
            anomaly_score=anomaly.anomaly_score,
            severity_score=_severity_score(anomaly.anomaly_score, anomaly.threshold),
            reconstructed_value=anomaly.reconstructed_value,
            is_anomaly=anomaly.is_anomaly,
            threshold=anomaly.threshold,
            detected_at=anomaly.detected_at,
            timestamp=sensor.timestamp,
            value=sensor.value,
            sensor_type=sensor.sensor_type,
            source_file=sensor.source_file,
        )
        for anomaly, sensor in rows
    ]
    return AnomalyListResponse(total=total, items=items)


@router.get("/results/{anomaly_id}", response_model=AnomalyResponse)
def result_detail(anomaly_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(Anomaly, SensorData)
        .join(SensorData, SensorData.id == Anomaly.sensor_data_id)
        .filter(Anomaly.id == anomaly_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Anomaliya yozuvi topilmadi.")

    anomaly, sensor = row
    return AnomalyResponse(
        id=anomaly.id,
        sensor_data_id=anomaly.sensor_data_id,
        training_history_id=anomaly.training_history_id,
        anomaly_score=anomaly.anomaly_score,
        severity_score=_severity_score(anomaly.anomaly_score, anomaly.threshold),
        reconstructed_value=anomaly.reconstructed_value,
        is_anomaly=anomaly.is_anomaly,
        threshold=anomaly.threshold,
        detected_at=anomaly.detected_at,
        timestamp=sensor.timestamp,
        value=sensor.value,
        sensor_type=sensor.sensor_type,
        source_file=sensor.source_file,
    )


@router.get("/export")
def export_results(
    sensor_type: str | None = None,
    source_file: str | None = None,
    anomaly_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Anomaly, SensorData).join(SensorData, SensorData.id == Anomaly.sensor_data_id)
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)
    if source_file:
        query = query.filter(SensorData.source_file == source_file)
    if anomaly_only:
        query = query.filter(Anomaly.is_anomaly.is_(True))

    rows = query.order_by(SensorData.timestamp).yield_per(1000)
    filename = _safe_export_name("anomaly_results", sensor_type, source_file)
    return StreamingResponse(
        _iter_anomaly_csv(rows),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/stats", response_model=AnomalyStats)
def stats(db: Session = Depends(get_db)):
    total_records = db.query(Anomaly).count()
    total_anomalies = db.query(Anomaly).filter(Anomaly.is_anomaly.is_(True)).count()

    from sqlalchemy import func as sa_func
    rows = (
        db.query(SensorData.sensor_type, sa_func.count(Anomaly.id))
        .join(Anomaly, Anomaly.sensor_data_id == SensorData.id)
        .filter(Anomaly.is_anomaly.is_(True))
        .group_by(SensorData.sensor_type)
        .all()
    )
    by_sensor: dict[str, int] = {st: cnt for st, cnt in rows}

    anomaly_rate = (total_anomalies / total_records * 100) if total_records else 0.0
    return AnomalyStats(
        total_records=total_records,
        total_anomalies=total_anomalies,
        anomaly_rate=anomaly_rate,
        by_sensor=by_sensor,
    )
