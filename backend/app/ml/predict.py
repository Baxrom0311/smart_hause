import numpy as np


def calculate_reconstruction_details(model, data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    predictions = model.predict(data, verbose=0)
    mse = np.mean(np.power(data - predictions, 2), axis=(1, 2))
    return predictions, mse


def calculate_reconstruction_error(model, data: np.ndarray) -> np.ndarray:
    _predictions, mse = calculate_reconstruction_details(model, data)
    return mse


def determine_threshold(errors: np.ndarray, k: float = 3.0) -> float:
    return float(np.mean(errors) + k * np.std(errors))


def detect_anomalies(model, data: np.ndarray, threshold: float) -> tuple[np.ndarray, np.ndarray]:
    errors = calculate_reconstruction_error(model, data)
    anomalies = errors > threshold
    return errors, anomalies
