# API Reference

Backend base URL:

```text
http://localhost:8000
```

Frontend development rejimida browser chaqiruvlari odatda `/api` va `/health` orqali `Vite proxy` dan o'tadi.

## 1. Umumiy qoidalar

### Javob formatlari

Ko'p endpointlar quyidagi formatlardan birini qaytaradi:

- oddiy obyekt
- ro'yxat
- `{ "total": number, "items": [...] }`

### Sana formatlari

Backend datetime maydonlarini `ISO 8601` ko'rinishida qaytaradi.

### Xatolik formatlari

FastAPI xatolari odatda `detail` maydoni orqali qaytadi:

```json
{
  "detail": "Xatolik matni"
}
```

## 2. Health

### `GET /health`

Backendning ishlayotganini tekshiradi.

Javob:

```json
{
  "status": "ok"
}
```

## 3. Data API

### `POST /api/data/upload`

CSV fayl yuklaydi. Faylda kamida `timestamp,value` ustunlari bo'lishi kerak.

Form-data:

- `file`: CSV fayl
- `sensor_type`: optional

Namuna javob:

```json
{
  "message": "CSV muvaffaqiyatli yuklandi.",
  "sensor_type": "temperature",
  "source_file": "ambient_temperature_system_failure.csv",
  "rows_inserted": 7267
}
```

### `GET /api/data/samples`

`backend/data/nab/` ichidagi lokal sample datasetlar ro'yxatini qaytaradi.

Namuna javob:

```json
[
  {
    "file_name": "ambient_temperature_system_failure.csv",
    "sensor_type": "temperature",
    "size_bytes": 243517
  }
]
```

### `POST /api/data/import-sample`

Lokal sample faylni bazaga import qiladi.

Request:

```json
{
  "file_name": "ambient_temperature_system_failure.csv",
  "sensor_type": null
}
```

### `GET /api/data/list`

Sensor data yozuvlarini qaytaradi.

Query params:

- `sensor_type`: optional
- `source_file`: optional
- `limit`: default `100`
- `offset`: default `0`

Namuna javob:

```json
{
  "total": 7267,
  "items": [
    {
      "id": 1,
      "timestamp": "2014-04-01T00:00:00",
      "value": 71.3,
      "sensor_type": "temperature",
      "source_file": "ambient_temperature_system_failure.csv",
      "created_at": "2026-04-21T10:00:00"
    }
  ]
}
```

### `GET /api/data/stats`

Dataset statistikasi.

Query params:

- `sensor_type`: optional
- `source_file`: optional

Namuna javob:

```json
{
  "count": 7267,
  "mean": 71.24,
  "min": 57.45,
  "max": 86.22,
  "std": 4.91
}
```

### `GET /api/data/sources`

Bazadagi datasetlar ro'yxatini qaytaradi.

Query params:

- `sensor_type`: optional

Namuna javob:

```json
[
  {
    "source_file": "ambient_temperature_system_failure.csv",
    "sensor_type": "temperature",
    "rows_count": 7267
  }
]
```

### `GET /api/data/sensors`

Mavjud sensor turlarini qaytaradi.

Namuna javob:

```json
["temperature", "cpu"]
```

### `GET /api/data/export`

Tanlangan filter bo'yicha sensor datani CSV ko'rinishida qaytaradi.

Query params:

- `sensor_type`: optional
- `source_file`: optional

Response:

- `Content-Type: text/csv`
- `Content-Disposition: attachment; filename=...`

### `DELETE /api/data/source/{source_file}`

Bitta datasetni va unga bog'liq anomaly yozuvlarini o'chiradi.

### `DELETE /api/data/{sensor_type}`

Tanlangan sensor turiga tegishli barcha data va anomaly yozuvlarini o'chiradi.

Bu endpoint odatda `source_file` filter tanlanmagan holatda ishlatiladi.

## 4. Model API

### `POST /api/model/train`

Training jarayonini background rejimda ishga tushiradi.

Request:

```json
{
  "sensor_type": "temperature",
  "source_file": "ambient_temperature_system_failure.csv",
  "epochs": 50,
  "batch_size": 32,
  "learning_rate": 0.001,
  "window_size": 30
}
```

Status code:

```text
202 Accepted
```

Namuna javob:

```json
{
  "state": "running",
  "sensor_type": "temperature",
  "source_file": "ambient_temperature_system_failure.csv",
  "message": "Trening navbatga qo'yildi.",
  "progress": 1,
  "current_epoch": 0,
  "total_epochs": 50,
  "train_loss": null,
  "val_loss": null,
  "loss_history": [],
  "val_loss_history": []
}
```

### `GET /api/model/status`

Joriy training statusini qaytaradi.

Muhim maydonlar:

- `state`: `idle`, `running`, `completed`, `failed`
- `progress`: 0 dan 100 gacha
- `current_epoch`
- `total_epochs`
- `train_loss`
- `val_loss`
- `loss_history`
- `val_loss_history`
- `training_id`

### `GET /api/model/history`

Barcha training yozuvlarini qaytaradi.

Namuna yozuv:

```json
[
  {
    "id": 1,
    "model_name": "autoencoder_temperature_20260421_120000",
    "sensor_type": "temperature",
    "source_file": "ambient_temperature_system_failure.csv",
    "status": "completed",
    "epochs": 50,
    "batch_size": 32,
    "learning_rate": 0.001,
    "window_size": 30,
    "train_loss": 0.0021,
    "val_loss": 0.0027,
    "loss_history": [0.012, 0.006, 0.0021],
    "val_loss_history": [0.014, 0.007, 0.0027],
    "threshold": 0.01234,
    "accuracy": 0.91,
    "precision_score": 1.0,
    "recall_score": 0.0978,
    "f1": 0.1782,
    "model_path": "backend/saved_models/autoencoder_temperature.keras",
    "scaler_path": "backend/saved_models/autoencoder_temperature.joblib",
    "created_at": "2026-04-21T12:00:00"
  }
]
```

### `GET /api/model/history/{id}`

Bitta training yozuvining to'liq tafsilotini qaytaradi.

UI dagi history detail modal shu endpointga tayangan.

## 5. Anomaly API

### `POST /api/anomaly/detect`

Tanlangan dataset ustida saved model bilan anomaly detection bajaradi.

Request:

```json
{
  "sensor_type": "temperature",
  "source_file": "ambient_temperature_system_failure.csv",
  "training_id": 1
}
```

Namuna javob:

```json
{
  "sensor_type": "temperature",
  "source_file": "ambient_temperature_system_failure.csv",
  "training_id": 1,
  "threshold": 0.01234,
  "total_windows": 7238,
  "anomalies_detected": 78
}
```

Muhim qoida:

- `training_id` noto'g'ri datasetga tegishli bo'lsa backend `400` qaytaradi

### `GET /api/anomaly/results`

Anomaly natijalarini ro'yxat ko'rinishida qaytaradi.

Query params:

- `sensor_type`: optional
- `source_file`: optional
- `limit`: default `100`
- `offset`: default `0`

Namuna javob:

```json
{
  "total": 78,
  "items": [
    {
      "id": 1,
      "sensor_data_id": 301,
      "training_history_id": 1,
      "anomaly_score": 0.0241,
      "reconstructed_value": 69.22,
      "is_anomaly": true,
      "threshold": 0.01234,
      "detected_at": "2026-04-21T12:45:00",
      "timestamp": "2014-05-28T15:00:00",
      "value": 72.58,
      "sensor_type": "temperature",
      "source_file": "ambient_temperature_system_failure.csv"
    }
  ]
}
```

### `GET /api/anomaly/results/{id}`

Bitta anomaly yozuvining tafsilotini qaytaradi.

### `GET /api/anomaly/export`

Anomaly natijalarini CSV ko'rinishida qaytaradi.

Query params:

- `sensor_type`: optional
- `source_file`: optional
- `anomaly_only`: default `false`

### `GET /api/anomaly/stats`

Anomaly bo'yicha umumiy statistika qaytaradi.

Namuna javob:

```json
{
  "total_records": 7238,
  "total_anomalies": 78,
  "anomaly_rate": 1.07,
  "by_sensor": {
    "temperature": 78
  }
}
```

## 6. Dashboard API

### `GET /api/dashboard/summary`

Dashboard summary uchun agregat natijalarni qaytaradi.

Namuna javob:

```json
{
  "total_sensor_data": 7267,
  "total_anomalies": 78,
  "anomaly_percentage": 1.07,
  "sensor_types": ["temperature"],
  "latest_anomaly": "2026-04-21T12:45:00",
  "latest_model": {
    "id": 1,
    "name": "autoencoder_temperature_20260421_120000",
    "accuracy": 0.91,
    "f1": 0.18,
    "created_at": "2026-04-21T12:00:00"
  }
}
```

`latest_model` `null` bo'lishi mumkin. Frontend shu holatni ham xavfsiz ko'tarishi kerak.
