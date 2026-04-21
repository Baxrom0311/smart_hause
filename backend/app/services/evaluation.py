import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from app.config import NAB_LABELS_FILE


def _resolve_label_key(source_file: str, labels: dict[str, list[list[str]]]) -> str | None:
    if source_file in labels:
        return source_file
    suffix = f"/{source_file}"
    for key in labels:
        if key.endswith(suffix):
            return key
    return None


def compute_training_metrics(
    *,
    source_file: str | None,
    timestamps: list,
    predicted_flags: np.ndarray,
) -> dict[str, float | None]:
    if not source_file or not Path(NAB_LABELS_FILE).exists():
        return {
            "accuracy": None,
            "precision_score": None,
            "recall_score": None,
            "f1": None,
        }

    with Path(NAB_LABELS_FILE).open("r", encoding="utf-8") as handle:
        labels = json.load(handle)

    label_key = _resolve_label_key(source_file, labels)
    if not label_key:
        return {
            "accuracy": None,
            "precision_score": None,
            "recall_score": None,
            "f1": None,
        }

    windows = labels.get(label_key, [])
    ground_truth = np.zeros(len(timestamps), dtype=int)
    normalized_timestamps = [pd.Timestamp(timestamp) for timestamp in timestamps]

    for start_text, end_text in windows:
        start = pd.Timestamp(start_text)
        end = pd.Timestamp(end_text)
        ground_truth |= np.asarray(
            [(timestamp >= start) and (timestamp <= end) for timestamp in normalized_timestamps],
            dtype=int,
        )

    predicted = np.asarray(predicted_flags, dtype=int)
    precision, recall, f1, _support = precision_recall_fscore_support(
        ground_truth,
        predicted,
        average="binary",
        zero_division=0,
    )
    accuracy = accuracy_score(ground_truth, predicted)

    return {
        "accuracy": float(accuracy),
        "precision_score": float(precision),
        "recall_score": float(recall),
        "f1": float(f1),
    }
