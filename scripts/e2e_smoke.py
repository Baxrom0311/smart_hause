#!/usr/bin/env python3
"""End-to-end smoke test for the Smart Home anomaly detection backend.

The script uses a temporary SQLite database and a synthetic CSV dataset, so it
does not mutate the local development database.
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta
import math
import os
from pathlib import Path
import sys
import tempfile
import time


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"


def write_synthetic_csv(path: Path, rows_count: int = 120) -> None:
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["timestamp", "value"])
        for index in range(rows_count):
            timestamp = start_time + timedelta(minutes=index)
            value = 22 + math.sin(index / 7) * 0.8
            if index in {45, 46, 90}:
                value += 7.5
            writer.writerow([timestamp.isoformat(sep=" "), round(value, 5)])


def wait_for_training(client, timeout_seconds: int = 180) -> dict:
    deadline = time.time() + timeout_seconds
    status = client.get("/api/model/status").json()
    while status["state"] == "running" and time.time() < deadline:
        time.sleep(1)
        status = client.get("/api/model/status").json()

    if status["state"] != "completed":
        raise AssertionError(f"Training did not complete successfully: {status}")
    return status


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="smart-home-smoke-") as temp_dir:
        temp_path = Path(temp_dir)
        os.environ["SMART_HOME_DATABASE_URL"] = f"sqlite:///{temp_path / 'smoke.db'}"
        os.environ["SMART_HOME_SAVED_MODELS_DIR"] = str(temp_path / "saved_models")
        os.environ["SMART_HOME_NAB_DATA_DIR"] = str(temp_path / "nab")
        os.environ["SMART_HOME_NAB_LABELS_DIR"] = str(temp_path / "nab_labels")
        sys.path.insert(0, str(BACKEND_DIR))

        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        source_file = "smoke_temperature.csv"
        csv_path = temp_path / source_file
        write_synthetic_csv(csv_path)

        health = client.get("/health")
        assert health.status_code == 200, health.text

        with csv_path.open("rb") as file_handle:
            upload = client.post(
                "/api/data/upload",
                data={"sensor_type": "temperature"},
                files={"file": (source_file, file_handle, "text/csv")},
            )
        assert upload.status_code == 200, upload.text
        upload_data = upload.json()
        assert upload_data["rows_inserted"] == 120, upload_data

        stats = client.get(
            "/api/data/stats",
            params={"sensor_type": "temperature", "source_file": source_file},
        )
        assert stats.status_code == 200, stats.text
        assert stats.json()["count"] == 120, stats.text

        train = client.post(
            "/api/model/train",
            json={
                "sensor_type": "temperature",
                "source_file": source_file,
                "epochs": 2,
                "batch_size": 8,
                "window_size": 12,
                "learning_rate": 0.001,
            },
        )
        assert train.status_code == 202, train.text
        training_status = wait_for_training(client)
        assert training_status["training_id"], training_status
        assert training_status["loss_history"], training_status

        history = client.get("/api/model/history")
        assert history.status_code == 200, history.text
        assert history.json()[0]["loss_history"], history.text

        detect = client.post(
            "/api/anomaly/detect",
            json={
                "sensor_type": "temperature",
                "source_file": source_file,
                "training_id": training_status["training_id"],
            },
        )
        assert detect.status_code == 200, detect.text
        detection_data = detect.json()
        assert detection_data["total_windows"] > 0, detection_data

        results = client.get(
            "/api/anomaly/results",
            params={"sensor_type": "temperature", "source_file": source_file, "limit": 20},
        )
        assert results.status_code == 200, results.text
        assert results.json()["total"] == detection_data["total_windows"], results.text

        dashboard = client.get("/api/dashboard/summary")
        assert dashboard.status_code == 200, dashboard.text
        assert dashboard.json()["total_sensor_data"] == 120, dashboard.text

        data_export = client.get("/api/data/export", params={"source_file": source_file})
        assert data_export.status_code == 200, data_export.text
        assert data_export.text.splitlines()[0] == (
            "id,timestamp,value,sensor_type,source_file,created_at"
        )

        anomaly_export = client.get("/api/anomaly/export", params={"source_file": source_file})
        assert anomaly_export.status_code == 200, anomaly_export.text
        assert anomaly_export.text.splitlines()[0].startswith("id,sensor_data_id")

        print("health=ok")
        print(f"uploaded_rows={upload_data['rows_inserted']}")
        print(f"training_id={training_status['training_id']}")
        print(f"loss_points={len(training_status['loss_history'])}")
        print(f"total_windows={detection_data['total_windows']}")
        print(f"anomalies_detected={detection_data['anomalies_detected']}")
        print("exports=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
