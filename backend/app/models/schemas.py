from datetime import datetime
import json

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_EPOCHS,
    DEFAULT_LEARNING_RATE,
    DEFAULT_WINDOW_SIZE,
)


class ORMBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class SensorDataCreate(BaseModel):
    timestamp: datetime
    value: float
    sensor_type: str
    source_file: str


class SensorDataResponse(ORMBaseModel):
    id: int
    timestamp: datetime
    value: float
    sensor_type: str
    source_file: str
    created_at: datetime


class DataListResponse(BaseModel):
    total: int
    items: list[SensorDataResponse]


class UploadResponse(BaseModel):
    message: str
    sensor_type: str
    source_file: str
    rows_inserted: int


class SampleDatasetResponse(BaseModel):
    file_name: str
    sensor_type: str
    size_bytes: int


class SampleImportRequest(BaseModel):
    file_name: str
    sensor_type: str | None = None


class DataSourceResponse(BaseModel):
    source_file: str
    sensor_type: str
    rows_count: int


class DataStats(BaseModel):
    count: int
    mean: float | None
    min: float | None
    max: float | None
    std: float | None


class TrainingRequest(BaseModel):
    sensor_type: str = Field(..., min_length=1)
    source_file: str | None = None
    epochs: int = Field(DEFAULT_EPOCHS, ge=1, le=1000)
    batch_size: int = Field(DEFAULT_BATCH_SIZE, ge=1, le=4096)
    learning_rate: float = Field(DEFAULT_LEARNING_RATE, gt=0, le=1)
    window_size: int = Field(DEFAULT_WINDOW_SIZE, ge=5, le=512)


class TrainingResponse(ORMBaseModel):
    id: int
    model_name: str
    sensor_type: str
    source_file: str | None
    status: str
    epochs: int
    batch_size: int
    learning_rate: float
    window_size: int
    train_loss: float
    val_loss: float | None
    loss_history: list[float] = Field(default_factory=list)
    val_loss_history: list[float] = Field(default_factory=list)
    threshold: float
    accuracy: float | None
    precision_score: float | None
    recall_score: float | None
    f1: float | None
    model_path: str | None
    scaler_path: str | None
    created_at: datetime

    @field_validator("loss_history", "val_loss_history", mode="before")
    @classmethod
    def parse_loss_history(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return []
            return parsed if isinstance(parsed, list) else []
        return value


class ModelStatusResponse(BaseModel):
    state: str
    sensor_type: str | None = None
    source_file: str | None = None
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    training_id: int | None = None
    progress: int = 0
    current_epoch: int | None = None
    total_epochs: int | None = None
    train_loss: float | None = None
    val_loss: float | None = None
    loss_history: list[float] = Field(default_factory=list)
    val_loss_history: list[float] = Field(default_factory=list)


class AnomalyDetectionRequest(BaseModel):
    sensor_type: str = Field(..., min_length=1)
    source_file: str | None = None
    training_id: int | None = None


class AnomalyDetectionResponse(BaseModel):
    sensor_type: str
    source_file: str | None = None
    training_id: int
    threshold: float
    total_windows: int
    anomalies_detected: int


class AnomalyResponse(BaseModel):
    id: int
    sensor_data_id: int
    training_history_id: int | None
    anomaly_score: float
    severity_score: float
    reconstructed_value: float | None
    is_anomaly: bool
    threshold: float
    detected_at: datetime
    timestamp: datetime
    value: float
    sensor_type: str
    source_file: str


class AnomalyListResponse(BaseModel):
    total: int
    items: list[AnomalyResponse]


class AnomalyStats(BaseModel):
    total_records: int
    total_anomalies: int
    anomaly_rate: float
    by_sensor: dict[str, int]


class LatestModelSummary(BaseModel):
    id: int
    name: str
    accuracy: float | None
    f1: float | None
    created_at: datetime


class DashboardSummary(BaseModel):
    total_sensor_data: int
    total_anomalies: int
    anomaly_percentage: float
    sensor_types: list[str]
    latest_anomaly: datetime | None
    latest_model: LatestModelSummary | None
