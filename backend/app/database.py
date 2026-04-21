from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_sqlite_schema() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        anomaly_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(anomalies)")
        }
        if anomaly_columns and "reconstructed_value" not in anomaly_columns:
            connection.exec_driver_sql(
                "ALTER TABLE anomalies ADD COLUMN reconstructed_value FLOAT"
            )

        training_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(training_history)")
        }
        if training_columns and "source_file" not in training_columns:
            connection.exec_driver_sql(
                "ALTER TABLE training_history ADD COLUMN source_file VARCHAR"
            )
        if training_columns and "loss_history" not in training_columns:
            connection.exec_driver_sql(
                "ALTER TABLE training_history ADD COLUMN loss_history TEXT"
            )
        if training_columns and "val_loss_history" not in training_columns:
            connection.exec_driver_sql(
                "ALTER TABLE training_history ADD COLUMN val_loss_history TEXT"
            )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
