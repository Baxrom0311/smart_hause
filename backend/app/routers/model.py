from datetime import datetime, timezone
import json
import logging
import threading

logger = logging.getLogger(__name__)

import joblib
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import ANOMALY_THRESHOLD_K, SAVED_MODELS_DIR
from app.database import SessionLocal, get_db
from app.ml.predict import calculate_reconstruction_error, determine_threshold
from app.ml.preprocessing import create_sequences, normalize_data, train_test_split
from app.ml.train import train_model
from app.models.db_models import SensorData, TrainingHistory
from app.models.schemas import ModelStatusResponse, TrainingRequest, TrainingResponse
from app.services.autoencoder import build_autoencoder
from app.services.data_service import get_sensor_series
from app.services.evaluation import compute_training_metrics

router = APIRouter()
TRAINING_LOCK = threading.Lock()
UNSET = object()

TRAINING_STATUS: dict[str, str | int | datetime | None] = {
    "state": "idle",
    "sensor_type": None,
    "source_file": None,
    "message": "Trening hali boshlanmagan.",
    "started_at": None,
    "finished_at": None,
    "training_id": None,
    "progress": 0,
    "current_epoch": None,
    "total_epochs": None,
    "train_loss": None,
    "val_loss": None,
    "loss_history": [],
    "val_loss_history": [],
}


def _update_status(
    *,
    state: str | object = UNSET,
    sensor_type: str | None | object = UNSET,
    source_file: str | None | object = UNSET,
    message: str | None | object = UNSET,
    started_at: datetime | None | object = UNSET,
    finished_at: datetime | None | object = UNSET,
    training_id: int | None | object = UNSET,
    progress: int | None | object = UNSET,
    current_epoch: int | None | object = UNSET,
    total_epochs: int | None | object = UNSET,
    train_loss: float | None | object = UNSET,
    val_loss: float | None | object = UNSET,
    loss_history: list[float] | object = UNSET,
    val_loss_history: list[float] | object = UNSET,
) -> None:
    with TRAINING_LOCK:
        updates = {
            "state": state,
            "sensor_type": sensor_type,
            "source_file": source_file,
            "message": message,
            "started_at": started_at,
            "finished_at": finished_at,
            "training_id": training_id,
            "progress": progress,
            "current_epoch": current_epoch,
            "total_epochs": total_epochs,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "loss_history": loss_history,
            "val_loss_history": val_loss_history,
        }
        TRAINING_STATUS.update(
            {
                key: value
                for key, value in updates.items()
                if value is not UNSET
            }
        )


def _status_snapshot() -> dict[str, str | int | datetime | float | None]:
    with TRAINING_LOCK:
        return dict(TRAINING_STATUS)


def _try_start_training(request: TrainingRequest, started_at: datetime) -> bool:
    with TRAINING_LOCK:
        if TRAINING_STATUS["state"] == "running":
            return False
        TRAINING_STATUS.update(
            {
                "state": "running",
                "sensor_type": request.sensor_type,
                "source_file": request.source_file,
                "message": "Trening navbatga qo'yildi.",
                "started_at": started_at,
                "finished_at": None,
                "training_id": None,
                "progress": 1,
                "current_epoch": 0,
                "total_epochs": request.epochs,
                "train_loss": None,
                "val_loss": None,
                "loss_history": [],
                "val_loss_history": [],
            }
        )
    return True


def _progress_callback(sensor_type: str, source_file: str | None):
    def callback(current_epoch: int, total_epochs: int, logs: dict[str, float]) -> None:
        progress = min(95, max(5, int(current_epoch / max(total_epochs, 1) * 100)))
        train_loss = float(logs["loss"]) if "loss" in logs else None
        val_loss = float(logs["val_loss"]) if "val_loss" in logs else None
        with TRAINING_LOCK:
            loss_history = list(TRAINING_STATUS.get("loss_history") or [])
            val_loss_history = list(TRAINING_STATUS.get("val_loss_history") or [])
            if train_loss is not None:
                loss_history.append(train_loss)
            if val_loss is not None:
                val_loss_history.append(val_loss)
            TRAINING_STATUS.update(
                {
                    "state": "running",
                    "sensor_type": sensor_type,
                    "source_file": source_file,
                    "message": f"{current_epoch}/{total_epochs} epoch bajarildi.",
                    "progress": progress,
                    "current_epoch": current_epoch,
                    "total_epochs": total_epochs,
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "loss_history": loss_history,
                    "val_loss_history": val_loss_history,
                }
            )

    return callback


def _run_training_job(request_data: dict[str, int | float | str], started_at: datetime) -> None:
    db = SessionLocal()
    request = TrainingRequest.model_validate(request_data)
    logger.info("Trening boshlandi: sensor_type=%s, source_file=%s, epochs=%d",
                request.sensor_type, request.source_file, request.epochs)
    try:
        np.random.seed(42)
        sensor_rows = get_sensor_series(db, request.sensor_type, request.source_file)
        if not sensor_rows:
            raise ValueError("Trening uchun sensor ma'lumotlari topilmadi.")

        values = np.asarray([row.value for row in sensor_rows], dtype=float)
        scaled_values, scaler = normalize_data(values)
        sequences = create_sequences(scaled_values, window_size=request.window_size)
        if len(sequences) < 2:
            raise ValueError(
                "Window yaratish uchun ma'lumot yetarli emas. window_size ni kamaytiring yoki ko'proq data yuklang."
            )

        x_train, x_test = train_test_split(sequences)
        unique_source_files = sorted({row.source_file for row in sensor_rows})
        training_source_file = unique_source_files[0] if len(unique_source_files) == 1 else None
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_sensor_type = request.sensor_type.replace(" ", "_").lower()
        model_path = SAVED_MODELS_DIR / f"autoencoder_{safe_sensor_type}_{timestamp}.keras"
        scaler_path = SAVED_MODELS_DIR / f"scaler_{safe_sensor_type}_{timestamp}.joblib"

        model = build_autoencoder(
            window_size=request.window_size,
            learning_rate=request.learning_rate,
        )
        history = train_model(
            model=model,
            x_train=x_train,
            x_test=x_test,
            epochs=request.epochs,
            batch_size=request.batch_size,
            model_path=str(model_path),
            progress_callback=_progress_callback(request.sensor_type, request.source_file),
        )
        train_errors = calculate_reconstruction_error(model, x_train)
        threshold = determine_threshold(train_errors, ANOMALY_THRESHOLD_K)
        evaluation_errors = calculate_reconstruction_error(model, sequences)
        evaluation_flags = evaluation_errors > threshold
        evaluation_timestamps = [
            np.datetime64(row.timestamp)
            for row in sensor_rows[request.window_size - 1 :]
        ]
        metrics = compute_training_metrics(
            source_file=training_source_file,
            timestamps=evaluation_timestamps,
            predicted_flags=evaluation_flags,
        )
        joblib.dump(scaler, scaler_path)

        training = TrainingHistory(
            model_name=model_path.stem,
            sensor_type=request.sensor_type,
            source_file=training_source_file,
            status="completed",
            epochs=request.epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            window_size=request.window_size,
            train_loss=float(history["loss"][-1]),
            val_loss=float(history["val_loss"][-1]) if history.get("val_loss") else None,
            loss_history=json.dumps(history.get("loss", [])),
            val_loss_history=json.dumps(history.get("val_loss", [])),
            threshold=threshold,
            accuracy=metrics["accuracy"],
            precision_score=metrics["precision_score"],
            recall_score=metrics["recall_score"],
            f1=metrics["f1"],
            model_path=str(model_path),
            scaler_path=str(scaler_path),
        )
        db.add(training)
        db.commit()
        db.refresh(training)
        logger.info("Trening muvaffaqiyatli yakunlandi: id=%d, f1=%.4f, threshold=%.6f",
                     training.id, training.f1 or 0, training.threshold)
    except RuntimeError as exc:
        logger.error("Trening runtime xatosi: %s", exc)
        _update_status(
            state="failed",
            sensor_type=request.sensor_type,
            source_file=request.source_file,
            message=str(exc),
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            training_id=None,
            progress=100,
        )
        return
    except Exception as exc:
        logger.exception("Trening xatosi: %s", exc)
        _update_status(
            state="failed",
            sensor_type=request.sensor_type,
            source_file=request.source_file,
            message=f"Trening xatosi: {exc}",
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            training_id=None,
            progress=100,
        )
        return
    finally:
        db.close()

    _update_status(
        state="completed",
        sensor_type=request.sensor_type,
        source_file=training.source_file,
        message="Model muvaffaqiyatli o'qitildi.",
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        training_id=training.id,
        progress=100,
        current_epoch=request.epochs,
        total_epochs=request.epochs,
        train_loss=float(training.train_loss),
        val_loss=float(training.val_loss) if training.val_loss is not None else None,
        loss_history=history.get("loss", []),
        val_loss_history=history.get("val_loss", []),
    )


@router.post(
    "/train",
    response_model=ModelStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def train(request: TrainingRequest, db: Session = Depends(get_db)):
    row_count = (
        db.query(func.count(SensorData.id))
        .filter(SensorData.sensor_type == request.sensor_type)
    )
    if request.source_file:
        row_count = row_count.filter(SensorData.source_file == request.source_file)
    total = row_count.scalar() or 0

    if total == 0:
        raise HTTPException(status_code=404, detail="Trening uchun sensor ma'lumotlari topilmadi.")
    if total < request.window_size + 2:
        raise HTTPException(
            status_code=400,
            detail="Window yaratish uchun ma'lumot yetarli emas. window_size ni kamaytiring yoki ko'proq data yuklang.",
        )

    started_at = datetime.now(timezone.utc)
    if not _try_start_training(request, started_at):
        raise HTTPException(
            status_code=409,
            detail="Hozir boshqa trening ishlayapti. Tugashini kuting.",
        )
    thread = threading.Thread(
        target=_run_training_job,
        args=(request.model_dump(), started_at),
        daemon=True,
    )
    thread.start()
    return ModelStatusResponse.model_validate(_status_snapshot())


@router.get("/status", response_model=ModelStatusResponse)
def status():
    return ModelStatusResponse.model_validate(_status_snapshot())


@router.get("/history", response_model=list[TrainingResponse])
def history(db: Session = Depends(get_db)):
    rows = db.query(TrainingHistory).order_by(TrainingHistory.created_at.desc()).all()
    return [TrainingResponse.model_validate(row) for row in rows]


@router.get("/history/{training_id}", response_model=TrainingResponse)
def history_detail(training_id: int, db: Session = Depends(get_db)):
    row = db.query(TrainingHistory).filter(TrainingHistory.id == training_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Training yozuvi topilmadi.")
    return TrainingResponse.model_validate(row)
