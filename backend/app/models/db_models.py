from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    sensor_type = Column(String, nullable=False, index=True)
    source_file = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    anomalies = relationship(
        "Anomaly",
        back_populates="sensor_data",
        cascade="all, delete-orphan",
    )


class TrainingHistory(Base):
    __tablename__ = "training_history"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    sensor_type = Column(String, nullable=False, index=True)
    source_file = Column(String, nullable=True)
    status = Column(String, nullable=False, default="completed")
    epochs = Column(Integer, nullable=False)
    batch_size = Column(Integer, nullable=False)
    learning_rate = Column(Float, nullable=False)
    window_size = Column(Integer, nullable=False)
    train_loss = Column(Float, nullable=False)
    val_loss = Column(Float, nullable=True)
    loss_history = Column(Text, nullable=True)
    val_loss_history = Column(Text, nullable=True)
    threshold = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1 = Column(Float, nullable=True)
    model_path = Column(String, nullable=True)
    scaler_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    anomalies = relationship("Anomaly", back_populates="training_history")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    sensor_data_id = Column(
        Integer,
        ForeignKey("sensor_data.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    training_history_id = Column(
        Integer,
        ForeignKey("training_history.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    anomaly_score = Column(Float, nullable=False)
    reconstructed_value = Column(Float, nullable=True)
    is_anomaly = Column(Boolean, default=False, nullable=False, index=True)
    threshold = Column(Float, nullable=False)
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    sensor_data = relationship("SensorData", back_populates="anomalies")
    training_history = relationship("TrainingHistory", back_populates="anomalies")
