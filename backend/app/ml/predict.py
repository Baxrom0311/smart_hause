import numpy as np


def calculate_reconstruction_details(model, data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    predictions = model.predict(data, verbose=0)
    mse = np.mean(np.power(data[:, -1, :] - predictions[:, -1, :], 2), axis=1)
    return predictions, mse


def calculate_reconstruction_error(model, data: np.ndarray) -> np.ndarray:
    _predictions, mse = calculate_reconstruction_details(model, data)
    return mse


def determine_threshold(errors: np.ndarray, k: float = 3.0) -> float:
    values = np.asarray(errors, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return 0.0

    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad > 0:
        robust_threshold = median + k * 1.4826 * mad
    else:
        robust_threshold = float(np.mean(values) + k * np.std(values))

    percentile_threshold = float(np.percentile(values, 97.5))
    return float(max(min(robust_threshold, percentile_threshold), median))


def detect_anomalies(model, data: np.ndarray, threshold: float) -> tuple[np.ndarray, np.ndarray]:
    errors = calculate_reconstruction_error(model, data)
    anomalies = errors > threshold
    return errors, anomalies
