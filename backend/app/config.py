import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv(
    "SMART_HOME_DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'smart_home.db'}",
)
SAVED_MODELS_DIR = Path(
    os.getenv("SMART_HOME_SAVED_MODELS_DIR", str(BASE_DIR / "saved_models"))
)
NAB_DATA_DIR = Path(os.getenv("SMART_HOME_NAB_DATA_DIR", str(BASE_DIR / "data" / "nab")))
NAB_LABELS_DIR = Path(
    os.getenv("SMART_HOME_NAB_LABELS_DIR", str(BASE_DIR / "data" / "nab_labels"))
)
NAB_LABELS_FILE = NAB_LABELS_DIR / "combined_windows.json"

DEFAULT_WINDOW_SIZE = 30
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001
ANOMALY_THRESHOLD_K = 3.0

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

for path in (SAVED_MODELS_DIR, NAB_DATA_DIR, NAB_LABELS_DIR):
    path.mkdir(parents=True, exist_ok=True)
