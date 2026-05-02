from pathlib import Path
import re

import pandas as pd
from sqlalchemy.orm import Session

from sqlalchemy import func, or_

from app.models.db_models import Anomaly, SensorData, TrainingHistory


def infer_sensor_type(filename: str) -> str:
    stem = Path(filename).stem.lower().strip()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    if "temperature" in stem:
        return "temperature"
    if "humidity" in stem:
        return "humidity"
    if "cpu" in stem:
        return "cpu"
    if "pressure" in stem:
        return "pressure"
    return stem or "unknown_sensor"


def load_csv_to_db(
    file_path: str,
    sensor_type: str,
    db: Session,
    source_file: str | None = None,
) -> int:
    source_name = source_file or Path(file_path).name
    dataframe = pd.read_csv(file_path)
    required_columns = {"timestamp", "value"}
    missing = required_columns.difference(dataframe.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"CSV faylda kerakli ustunlar yo'q: {missing_columns}")

    dataframe = dataframe[["timestamp", "value"]].copy()
    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"], errors="coerce")
    dataframe["value"] = pd.to_numeric(dataframe["value"], errors="coerce")
    dataframe = dataframe.dropna(subset=["timestamp", "value"]).sort_values("timestamp")
    if dataframe.empty:
        raise ValueError("CSV faylda saqlash uchun yaroqli qator topilmadi.")

    existing_ids = [
        row_id
        for (row_id,) in db.query(SensorData.id)
        .filter(
            SensorData.sensor_type == sensor_type,
            SensorData.source_file == source_name,
        )
        .all()
    ]
    if existing_ids:
        db.query(Anomaly).filter(Anomaly.sensor_data_id.in_(existing_ids)).delete(
            synchronize_session=False
        )
        db.query(SensorData).filter(SensorData.id.in_(existing_ids)).delete(
            synchronize_session=False
        )
    _delete_stale_training_history(
        db,
        sensor_type=sensor_type,
        source_file=source_name,
        include_global=True,
    )

    rows = [
        SensorData(
            timestamp=row.timestamp.to_pydatetime(),
            value=float(row.value),
            sensor_type=sensor_type,
            source_file=source_name,
        )
        for row in dataframe.itertuples(index=False)
    ]
    db.bulk_save_objects(rows)
    db.commit()
    return len(rows)


def _delete_stale_training_history(
    db: Session,
    *,
    sensor_type: str,
    source_file: str | None = None,
    include_global: bool = False,
) -> int:
    query = db.query(TrainingHistory).filter(TrainingHistory.sensor_type == sensor_type)
    if source_file is not None:
        source_filters = [TrainingHistory.source_file == source_file]
        if include_global:
            source_filters.append(TrainingHistory.source_file.is_(None))
        query = query.filter(or_(*source_filters))

    stale_ids = [row_id for (row_id,) in query.with_entities(TrainingHistory.id).all()]
    if not stale_ids:
        return 0

    db.query(Anomaly).filter(Anomaly.training_history_id.in_(stale_ids)).delete(
        synchronize_session=False
    )
    return (
        db.query(TrainingHistory)
        .filter(TrainingHistory.id.in_(stale_ids))
        .delete(synchronize_session=False)
    )


def get_sensor_data(
    db: Session,
    sensor_type: str | None = None,
    source_file: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[SensorData]]:
    query = db.query(SensorData)
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)
    if source_file:
        query = query.filter(SensorData.source_file == source_file)
    total = query.count()
    items = (
        query.order_by(SensorData.timestamp)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return total, items


def get_sensor_series(
    db: Session,
    sensor_type: str,
    source_file: str | None = None,
) -> list[SensorData]:
    query = db.query(SensorData).filter(SensorData.sensor_type == sensor_type)
    if source_file:
        query = query.filter(SensorData.source_file == source_file)
    return query.order_by(SensorData.timestamp).all()


def get_data_stats(
    db: Session,
    sensor_type: str | None = None,
    source_file: str | None = None,
) -> dict[str, float | int | None]:
    query = db.query(
        func.count(SensorData.value),
        func.avg(SensorData.value),
        func.min(SensorData.value),
        func.max(SensorData.value),
    )
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)
    if source_file:
        query = query.filter(SensorData.source_file == source_file)

    count, mean, min_val, max_val = query.one()
    if not count:
        return {"count": 0, "mean": None, "min": None, "max": None, "std": None}

    # SQLite has no built-in stddev, compute via variance formula
    var_query = db.query(func.avg((SensorData.value - mean) * (SensorData.value - mean)))
    if sensor_type:
        var_query = var_query.filter(SensorData.sensor_type == sensor_type)
    if source_file:
        var_query = var_query.filter(SensorData.source_file == source_file)
    variance = var_query.scalar() or 0.0

    return {
        "count": int(count),
        "mean": float(mean),
        "min": float(min_val),
        "max": float(max_val),
        "std": float(variance ** 0.5),
    }


def list_sensor_types(db: Session) -> list[str]:
    rows = db.query(SensorData.sensor_type).distinct().order_by(SensorData.sensor_type).all()
    return [sensor_type for (sensor_type,) in rows]


def list_source_files(db: Session, sensor_type: str | None = None) -> list[dict[str, str | int]]:
    query = (
        db.query(
            SensorData.source_file,
            SensorData.sensor_type,
            func.count(SensorData.id).label("rows_count"),
        )
        .group_by(SensorData.source_file, SensorData.sensor_type)
        .order_by(SensorData.sensor_type, SensorData.source_file)
    )
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)

    return [
        {
            "source_file": source_file,
            "sensor_type": sensor_type_value,
            "rows_count": int(rows_count),
        }
        for source_file, sensor_type_value, rows_count in query.all()
    ]


def delete_sensor_data(db: Session, sensor_type: str) -> int:
    sensor_ids = [
        row_id
        for (row_id,) in db.query(SensorData.id)
        .filter(SensorData.sensor_type == sensor_type)
        .all()
    ]
    if not sensor_ids:
        return 0

    db.query(Anomaly).filter(Anomaly.sensor_data_id.in_(sensor_ids)).delete(
        synchronize_session=False
    )
    deleted = (
        db.query(SensorData)
        .filter(SensorData.id.in_(sensor_ids))
        .delete(synchronize_session=False)
    )
    _delete_stale_training_history(db, sensor_type=sensor_type)
    db.commit()
    return deleted


def delete_source_data(db: Session, source_file: str, sensor_type: str | None = None) -> int:
    query = db.query(SensorData).filter(SensorData.source_file == source_file)
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)

    rows = query.with_entities(SensorData.id, SensorData.sensor_type).all()
    sensor_ids = [row_id for row_id, _sensor_type in rows]
    if not sensor_ids:
        return 0
    affected_sensor_types = sorted({_sensor_type for _row_id, _sensor_type in rows})

    db.query(Anomaly).filter(Anomaly.sensor_data_id.in_(sensor_ids)).delete(
        synchronize_session=False
    )
    deleted = (
        db.query(SensorData)
        .filter(SensorData.id.in_(sensor_ids))
        .delete(synchronize_session=False)
    )
    for affected_sensor_type in affected_sensor_types:
        _delete_stale_training_history(
            db,
            sensor_type=affected_sensor_type,
            source_file=source_file,
            include_global=True,
        )
    db.commit()
    return deleted
