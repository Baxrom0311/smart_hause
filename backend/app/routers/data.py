import csv
from io import StringIO
from pathlib import Path
import re
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import NAB_DATA_DIR
from app.database import get_db
from app.models.db_models import SensorData
from app.models.schemas import (
    DataListResponse,
    DataSourceResponse,
    DataStats,
    SampleDatasetResponse,
    SampleImportRequest,
    SensorDataResponse,
    UploadResponse,
)
from app.services.data_service import (
    delete_source_data,
    delete_sensor_data,
    get_data_stats,
    get_sensor_data,
    infer_sensor_type,
    list_source_files,
    list_sensor_types,
    load_csv_to_db,
)

router = APIRouter()


def _safe_export_name(prefix: str, sensor_type: str | None, source_file: str | None) -> str:
    label = Path(source_file).stem if source_file else sensor_type or "all"
    label = re.sub(r"[^a-zA-Z0-9_.-]+", "_", label).strip("_") or "all"
    return f"{prefix}_{label}.csv"


def _iter_sensor_csv(rows):
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "timestamp", "value", "sensor_type", "source_file", "created_at"])
    yield buffer.getvalue()
    buffer.seek(0)
    buffer.truncate(0)

    for row in rows:
        writer.writerow(
            [
                row.id,
                row.timestamp.isoformat(),
                row.value,
                row.sensor_type,
                row.source_file,
                row.created_at.isoformat() if row.created_at else "",
            ]
        )
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)


def _resolve_sample_path(file_name: str) -> Path:
    sample_path = (NAB_DATA_DIR / Path(file_name).name).resolve()
    try:
        sample_path.relative_to(NAB_DATA_DIR.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Noto'g'ri sample fayl nomi.") from exc
    if not sample_path.exists() or not sample_path.is_file():
        raise HTTPException(status_code=404, detail="Sample fayl topilmadi.")
    return sample_path


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    sensor_type: str | None = Form(None),
    db: Session = Depends(get_db),
):
    source_file = Path(file.filename or "uploaded.csv").name
    detected_sensor_type = sensor_type or infer_sensor_type(source_file)

    with NamedTemporaryFile(delete=False, suffix=Path(source_file).suffix or ".csv") as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(await file.read())

    try:
        rows_inserted = load_csv_to_db(
            str(temp_path),
            sensor_type=detected_sensor_type,
            db=db,
            source_file=source_file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    return UploadResponse(
        message="CSV muvaffaqiyatli yuklandi.",
        sensor_type=detected_sensor_type,
        source_file=source_file,
        rows_inserted=rows_inserted,
    )


@router.get("/samples", response_model=list[SampleDatasetResponse])
def list_samples():
    files = sorted(path for path in NAB_DATA_DIR.glob("*.csv") if path.is_file())
    return [
        SampleDatasetResponse(
            file_name=path.name,
            sensor_type=infer_sensor_type(path.name),
            size_bytes=path.stat().st_size,
        )
        for path in files
    ]


@router.post("/import-sample", response_model=UploadResponse)
def import_sample(request: SampleImportRequest, db: Session = Depends(get_db)):
    sample_path = _resolve_sample_path(request.file_name)
    sensor_type = request.sensor_type or infer_sensor_type(sample_path.name)

    try:
        rows_inserted = load_csv_to_db(
            str(sample_path),
            sensor_type=sensor_type,
            db=db,
            source_file=sample_path.name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return UploadResponse(
        message="Sample dataset muvaffaqiyatli import qilindi.",
        sensor_type=sensor_type,
        source_file=sample_path.name,
        rows_inserted=rows_inserted,
    )


@router.get("/list", response_model=DataListResponse)
def list_data(
    sensor_type: str | None = None,
    source_file: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    total, items = get_sensor_data(
        db,
        sensor_type=sensor_type,
        source_file=source_file,
        limit=limit,
        offset=offset,
    )
    return DataListResponse(
        total=total,
        items=[SensorDataResponse.model_validate(item) for item in items],
    )


@router.get("/stats", response_model=DataStats)
def stats(
    sensor_type: str | None = None,
    source_file: str | None = None,
    db: Session = Depends(get_db),
):
    return DataStats.model_validate(
        get_data_stats(db, sensor_type=sensor_type, source_file=source_file)
    )


@router.get("/export")
def export_data(
    sensor_type: str | None = None,
    source_file: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SensorData)
    if sensor_type:
        query = query.filter(SensorData.sensor_type == sensor_type)
    if source_file:
        query = query.filter(SensorData.source_file == source_file)

    rows = query.order_by(SensorData.timestamp).yield_per(1000)
    filename = _safe_export_name("sensor_data", sensor_type, source_file)
    return StreamingResponse(
        _iter_sensor_csv(rows),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sensors", response_model=list[str])
def sensors(db: Session = Depends(get_db)):
    return list_sensor_types(db)


@router.get("/sources", response_model=list[DataSourceResponse])
def sources(sensor_type: str | None = None, db: Session = Depends(get_db)):
    return [
        DataSourceResponse.model_validate(item)
        for item in list_source_files(db, sensor_type=sensor_type)
    ]


@router.delete("/{sensor_type}")
def delete_sensor(sensor_type: str, db: Session = Depends(get_db)):
    deleted_rows = delete_sensor_data(db, sensor_type)
    if deleted_rows == 0:
        raise HTTPException(status_code=404, detail="Sensor turi bo'yicha ma'lumot topilmadi.")
    return {"message": "Ma'lumotlar o'chirildi.", "deleted_rows": deleted_rows}


@router.delete("/source/{source_file:path}")
def delete_source(
    source_file: str,
    sensor_type: str | None = None,
    db: Session = Depends(get_db),
):
    deleted_rows = delete_source_data(db, Path(source_file).name, sensor_type=sensor_type)
    if deleted_rows == 0:
        raise HTTPException(status_code=404, detail="Dataset bo'yicha ma'lumot topilmadi.")
    return {"message": "Dataset ma'lumotlari o'chirildi.", "deleted_rows": deleted_rows}
