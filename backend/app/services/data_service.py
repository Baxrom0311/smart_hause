from pathlib import Path
import re

import pandas as pd
from sqlalchemy.orm import Session

from sqlalchemy import func

from app.models.db_models import Anomaly, SensorData


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
        db.commit()

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
    query = db.query(SensorData.value)
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)
    if source_file:
        query = query.filter(SensorData.source_file == source_file)

    values = [value for (value,) in query.all()]
    if not values:
        return {"count": 0, "mean": None, "min": None, "max": None, "std": None}

    series = pd.Series(values, dtype=float)
    return {
        "count": int(series.count()),
        "mean": float(series.mean()),
        "min": float(series.min()),
        "max": float(series.max()),
        "std": float(series.std(ddof=0)),
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
    db.commit()
    return deleted


def delete_source_data(db: Session, source_file: str) -> int:
    sensor_ids = [
        row_id
        for (row_id,) in db.query(SensorData.id)
        .filter(SensorData.source_file == source_file)
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
    db.commit()
    return deleted
