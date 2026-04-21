import numpy as np
from sklearn.preprocessing import MinMaxScaler


def normalize_data(data: np.ndarray) -> tuple[np.ndarray, MinMaxScaler]:
    array = np.asarray(data, dtype=float).reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(array)
    return scaled, scaler


def create_sequences(data: np.ndarray, window_size: int = 30) -> np.ndarray:
    array = np.asarray(data, dtype=float)
    if array.ndim == 1:
        array = array.reshape(-1, 1)
    if len(array) < window_size:
        return np.empty((0, window_size, array.shape[1]), dtype=float)
    sequences = [
        array[index : index + window_size]
        for index in range(len(array) - window_size + 1)
    ]
    return np.asarray(sequences, dtype=float)


def train_test_split(sequences: np.ndarray, test_ratio: float = 0.2) -> tuple[np.ndarray, np.ndarray]:
    if len(sequences) < 2:
        return sequences, np.empty((0, *sequences.shape[1:]), dtype=float)
    split_index = int(len(sequences) * (1 - test_ratio))
    split_index = min(max(split_index, 1), len(sequences) - 1)
    return sequences[:split_index], sequences[split_index:]
