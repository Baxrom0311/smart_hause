from pathlib import Path

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.ml.predict import calculate_reconstruction_details
from app.ml.preprocessing import create_sequences
from app.models.db_models import Anomaly, TrainingHistory
from app.services.data_service import get_sensor_series


def _load_model(model_path: str):
    try:
        from tensorflow.keras.models import load_model
    except ImportError as exc:
        raise RuntimeError(
            "TensorFlow o'rnatilmagan. `pip install -r requirements.txt` ni ishga tushiring."
        ) from exc
    return load_model(model_path)


def run_anomaly_detection(
    db: Session,
    sensor_type: str,
    training: TrainingHistory,
) -> dict[str, int | float]:
    sensor_rows = get_sensor_series(db, sensor_type, training.source_file)
    if not sensor_rows:
        raise ValueError(f"`{sensor_type}` uchun ma'lumot topilmadi.")
    if not training.model_path or not training.scaler_path:
        raise ValueError("Trening yozuvida model yoki scaler manzili saqlanmagan.")
    if not Path(training.model_path).exists():
        raise ValueError("Saqlangan model fayli topilmadi.")
    if not Path(training.scaler_path).exists():
        raise ValueError("Saqlangan scaler fayli topilmadi.")

    values = np.asarray([row.value for row in sensor_rows], dtype=float).reshape(-1, 1)
    scaler = joblib.load(training.scaler_path)
    scaled_values = scaler.transform(values)
    sequences = create_sequences(scaled_values, training.window_size)
    if len(sequences) == 0:
        raise ValueError("Anomaliya aniqlash uchun window_size ga yetarli ma'lumot yo'q.")

    model = _load_model(training.model_path)
    predictions, errors = calculate_reconstruction_details(model, sequences)
    flags = errors > training.threshold
    reconstructed_values = scaler.inverse_transform(
        predictions[:, -1, :].reshape(-1, 1)
    ).reshape(-1)

    target_rows = sensor_rows[training.window_size - 1 :]
    target_ids = [row.id for row in target_rows]
    if target_ids:
        db.query(Anomaly).filter(Anomaly.sensor_data_id.in_(target_ids)).delete(
            synchronize_session=False
        )

    anomaly_rows = [
        Anomaly(
            sensor_data_id=row.id,
            training_history_id=training.id,
            anomaly_score=float(error),
            reconstructed_value=float(reconstructed_value),
            is_anomaly=bool(flag),
            threshold=float(training.threshold),
        )
        for row, error, flag, reconstructed_value in zip(
            target_rows,
            errors,
            flags,
            reconstructed_values,
            strict=False,
        )
    ]
    if anomaly_rows:
        db.bulk_save_objects(anomaly_rows)
    db.commit()

    detected = int(sum(bool(flag) for flag in flags))
    return {
        "training_id": training.id,
        "source_file": training.source_file,
        "threshold": float(training.threshold),
        "total_windows": len(anomaly_rows),
        "anomalies_detected": detected,
    }
