# Diplom Loyihasi: Aqlli Uy Anomaliya Aniqlash Web Ilovasi

## Mavzu
"Vaqt ketma-ketligi asosidagi ma'lumotlarda (Time Series Data) Autoencoder mashinali o'qitish algoritmi yordamida aqlli uylarda sensorlardan olingan ma'lumotlardan anomaliyalarni aniqlash web ilovasini ishlab chiqish"

## Texnologiyalar
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React 18, Vite, Ant Design, Recharts
- **ML:** TensorFlow/Keras (LSTM Autoencoder)
- **Dataset:** NAB (Numenta Anomaly Benchmark)

---

## Loyiha Strukturasi

```
smart_hause/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, CORS, routers
│   │   ├── config.py               # Sozlamalar (DB path, model path, ...)
│   │   ├── database.py             # SQLite + SQLAlchemy session
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── db_models.py        # ORM modellari
│   │   │   └── schemas.py          # Pydantic request/response schemalar
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── data.py             # /api/data/* endpointlari
│   │   │   ├── anomaly.py          # /api/anomaly/* endpointlari
│   │   │   ├── model.py            # /api/model/* endpointlari
│   │   │   └── dashboard.py        # /api/dashboard/* endpointlari
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── data_service.py     # CSV o'qish, DB ga yozish
│   │   │   ├── autoencoder.py      # Model yaratish va saqlash
│   │   │   └── anomaly_detector.py # Anomaliya aniqlash logikasi
│   │   └── ml/
│   │       ├── __init__.py
│   │       ├── preprocessing.py    # Normalizatsiya, windowing
│   │       ├── train.py            # O'qitish pipeline
│   │       └── predict.py          # Bashorat qilish
│   ├── data/
│   │   └── nab/                    # NAB dataset CSV fayllari
│   ├── saved_models/               # .h5 saqlangan modellar
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout/             # Header, Sidebar, Layout
│   │   │   ├── Dashboard/          # StatCards, TimeSeriesChart, AnomalyChart, RecentAnomalies
│   │   │   ├── DataManagement/     # DataUpload, DataTable
│   │   │   ├── ModelTraining/      # TrainForm, TrainProgress, TrainHistory
│   │   │   └── Analysis/           # AnomalyDetection, ResultsView
│   │   ├── pages/                  # DashboardPage, DataPage, TrainingPage, AnalysisPage
│   │   ├── services/
│   │   │   └── api.js              # Axios instance + barcha API chaqiruvlar
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## BOSQICH 1: Backend Asosi

### 1.1 Virtual environment va paketlar
```bash
cd backend
python -m venv venv
source venv/bin/activate   # yoki Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy pydantic pandas numpy scikit-learn tensorflow python-multipart aiofiles
pip freeze > requirements.txt
```

### 1.2 `app/config.py`
```python
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'smart_home.db')}"
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "saved_models")
NAB_DATA_DIR = os.path.join(BASE_DIR, "data", "nab")

# Model default parametrlari
DEFAULT_WINDOW_SIZE = 30
DEFAULT_EPOCHS = 50
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 0.001
ANOMALY_THRESHOLD_K = 3  # mean + k*std
```

### 1.3 `app/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 1.4 `app/models/db_models.py` - 3 ta jadval
```python
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class SensorData(Base):
    __tablename__ = "sensor_data"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    sensor_type = Column(String, nullable=False)      # harorat, namlik, ...
    source_file = Column(String, nullable=False)       # NAB fayl nomi
    created_at = Column(DateTime, default=datetime.utcnow)
    anomalies = relationship("Anomaly", back_populates="sensor_data")

class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, index=True)
    sensor_data_id = Column(Integer, ForeignKey("sensor_data.id"))
    anomaly_score = Column(Float, nullable=False)      # reconstruction error
    is_anomaly = Column(Boolean, default=False)
    threshold = Column(Float, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    sensor_data = relationship("SensorData", back_populates="anomalies")

class TrainingHistory(Base):
    __tablename__ = "training_history"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    sensor_type = Column(String, nullable=False)
    epochs = Column(Integer)
    window_size = Column(Integer)
    train_loss = Column(Float)
    val_loss = Column(Float)
    threshold = Column(Float)                          # aniqlangan threshold
    accuracy = Column(Float, nullable=True)            # agar label mavjud bo'lsa
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1 = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 1.5 `app/models/schemas.py` - Pydantic modellari
Har bir DB model uchun:
- `SensorDataCreate` - timestamp, value, sensor_type, source_file
- `SensorDataResponse` - id + barcha maydonlar
- `AnomalyResponse` - id, sensor_data_id, anomaly_score, is_anomaly, threshold, detected_at
- `TrainingRequest` - sensor_type, epochs, batch_size, learning_rate, window_size
- `TrainingResponse` - id + barcha natijalar
- `DashboardSummary` - total_data, total_anomalies, latest_anomaly, model_accuracy
- `DataStats` - count, mean, min, max, std

### 1.6 `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import data, model, anomaly, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Home Anomaly Detection", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router, prefix="/api/data", tags=["Data"])
app.include_router(model.router, prefix="/api/model", tags=["Model"])
app.include_router(anomaly.router, prefix="/api/anomaly", tags=["Anomaly"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/")
def root():
    return {"message": "Smart Home Anomaly Detection API"}
```

### 1.7 `run.py`
```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

---

## BOSQICH 2: Ma'lumotlarni Yuklash va Preprocessing

### 2.1 NAB Dataset yuklab olish
```bash
# GitHub dan NAB dataset yuklab olish
# https://github.com/numenta/NAB
# Kerakli fayllar: data/realKnownCause/ papkasidagi CSV lar
# Masalan:
#   - realKnownCause/ambient_temperature_system_failure.csv
#   - realKnownCause/cpu_utilization_asg_misconfiguration.csv
#   - realKnownCause/machine_temperature_system_failure.csv
# Har bir CSV da 2 ta ustun: timestamp, value
```

### 2.2 `app/services/data_service.py`
Vazifalar:
1. **`load_csv_to_db(file_path, sensor_type, db)`** - CSV faylni o'qib DB ga yozish
   - `pd.read_csv()` bilan o'qish
   - `timestamp` ustunini `pd.to_datetime()` ga convert qilish
   - Har bir qatorni `SensorData` obyektiga aylantirib DB ga saqlash
   - Bulk insert ishlatish (tezroq): `db.bulk_save_objects()`

2. **`get_sensor_data(db, sensor_type, limit, offset)`** - DB dan ma'lumot olish
   - Pagination bilan (limit/offset)
   - sensor_type bo'yicha filter

3. **`get_data_stats(db, sensor_type)`** - Statistika hisoblash
   - Pandas bilan: count, mean, std, min, max qaytarish

### 2.3 `app/ml/preprocessing.py`
```python
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def normalize_data(data):
    """Min-Max normalizatsiya (0-1)"""
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data.reshape(-1, 1))
    return scaled, scaler

def create_sequences(data, window_size=30):
    """Sliding window bilan ketma-ketliklar yaratish"""
    sequences = []
    for i in range(len(data) - window_size):
        sequences.append(data[i:i + window_size])
    return np.array(sequences)

def train_test_split(sequences, test_ratio=0.2):
    """Ma'lumotni train/test ga ajratish"""
    split_idx = int(len(sequences) * (1 - test_ratio))
    return sequences[:split_idx], sequences[split_idx:]
```

### 2.4 `app/routers/data.py` endpointlari
| Method | Path | Tavsif |
|--------|------|--------|
| POST | `/api/data/upload` | CSV fayl yuklash (UploadFile) |
| GET | `/api/data/list` | Ma'lumotlar ro'yxati (sensor_type, limit, offset query params) |
| GET | `/api/data/stats` | Statistika (sensor_type query param) |
| GET | `/api/data/sensors` | Mavjud sensor turlari ro'yxati |
| DELETE | `/api/data/{sensor_type}` | Sensor ma'lumotlarini o'chirish |

**Upload endpoint muhim detallari:**
- `UploadFile` qabul qilish
- CSV ni vaqtinchalik faylga saqlash
- `data_service.load_csv_to_db()` ni chaqirish
- Nechta qator yuklangani haqida javob qaytarish

---

## BOSQICH 3: LSTM Autoencoder Model

### 3.1 `app/services/autoencoder.py` - Model arxitekturasi
```python
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, RepeatVector, TimeDistributed, Dense

def build_autoencoder(window_size, n_features=1):
    # ENCODER
    inputs = Input(shape=(window_size, n_features))
    encoded = LSTM(64, activation='relu', return_sequences=True)(inputs)
    encoded = LSTM(32, activation='relu', return_sequences=False)(encoded)
    # encoded shape: (batch_size, 32) - bu bottleneck

    # DECODER
    decoded = RepeatVector(window_size)(encoded)
    decoded = LSTM(32, activation='relu', return_sequences=True)(decoded)
    decoded = LSTM(64, activation='relu', return_sequences=True)(decoded)
    decoded = TimeDistributed(Dense(n_features))(decoded)

    model = Model(inputs, decoded)
    model.compile(optimizer='adam', loss='mse')
    return model
```

**Arxitektura tushuntirishi (diplom uchun muhim):**
```
Input (30, 1) → LSTM(64) → LSTM(32) → [Bottleneck: 32] → RepeatVector(30) → LSTM(32) → LSTM(64) → Dense(1) → Output (30, 1)

Encoder: Ma'lumotni siqib, muhim xususiyatlarni chiqaradi (64→32)
Bottleneck: 32 o'lchamli vektor - ma'lumotning eng muhim tasviri
Decoder: Siqilgan vektordan asl ma'lumotni qayta tiklashga harakat qiladi

ANOMALIYA MANTIQ:
- Normal ma'lumot: model yaxshi qayta tiklaydi → past reconstruction error
- Anomal ma'lumot: model qayta tiklay olmaydi → yuqori reconstruction error
- Agar error > threshold → ANOMALIYA
```

### 3.2 `app/ml/train.py` - O'qitish pipeline
```python
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

def train_model(model, X_train, X_test, epochs, batch_size, model_path):
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        ModelCheckpoint(model_path, monitor='val_loss', save_best_only=True)
    ]

    history = model.fit(
        X_train, X_train,          # Autoencoder: input = output!
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_test, X_test),
        callbacks=callbacks,
        shuffle=False               # Time series uchun tartibni saqlash
    )
    return history
```

**Muhim:** `model.fit(X_train, X_train)` - Autoencoder o'zini o'zi qayta tiklashga o'rganadi!

### 3.3 `app/ml/predict.py` - Anomaliya bashorat
```python
import numpy as np

def calculate_reconstruction_error(model, data):
    """Har bir window uchun MSE hisoblash"""
    predictions = model.predict(data)
    mse = np.mean(np.power(data - predictions, 2), axis=(1, 2))
    return mse

def determine_threshold(errors, k=3):
    """Threshold = mean + k * std"""
    threshold = np.mean(errors) + k * np.std(errors)
    return threshold

def detect_anomalies(model, data, threshold):
    """Anomaliyalarni aniqlash"""
    errors = calculate_reconstruction_error(model, data)
    anomalies = errors > threshold
    return errors, anomalies
```

### 3.4 `app/routers/model.py` endpointlari
| Method | Path | Tavsif |
|--------|------|--------|
| POST | `/api/model/train` | Model o'qitish (TrainingRequest body) |
| GET | `/api/model/status` | Joriy o'qitish holati |
| GET | `/api/model/history` | Barcha o'qitishlar tarixi |
| GET | `/api/model/history/{id}` | Bitta o'qitish tafsiloti |

**Train endpoint logikasi:**
1. Request dan parametrlarni olish (epochs, batch_size, window_size, sensor_type)
2. DB dan sensor ma'lumotlarini olish
3. Preprocessing: normalize → create_sequences → train_test_split
4. Model yaratish: `build_autoencoder(window_size)`
5. O'qitish: `train_model(model, X_train, X_test, ...)`
6. Threshold hisoblash: train data dagi errorlar asosida
7. Natijalarni DB ga saqlash (TrainingHistory)
8. Modelni `.h5` formatda saqlash (`saved_models/` papkaga)

---

## BOSQICH 4: Anomaliya Aniqlash API

### 4.1 `app/services/anomaly_detector.py`
```python
def run_anomaly_detection(db, sensor_type, model_path, threshold, window_size, scaler):
    """
    1. DB dan sensor ma'lumotlarini olish
    2. Normalizatsiya (saqlangan scaler bilan)
    3. Windowlarga ajratish
    4. Modelni yuklash (load_model)
    5. Reconstruction error hisoblash
    6. Threshold bilan solishtirish
    7. Anomaliyalarni DB ga saqlash (Anomaly jadvaliga)
    8. Natijalarni qaytarish
    """
```

### 4.2 `app/routers/anomaly.py` endpointlari
| Method | Path | Tavsif |
|--------|------|--------|
| POST | `/api/anomaly/detect` | Anomaliya aniqlashni boshlash (sensor_type body param) |
| GET | `/api/anomaly/results` | Aniqlangan anomaliyalar (sensor_type, limit, offset) |
| GET | `/api/anomaly/results/{id}` | Bitta anomaliya tafsiloti |
| GET | `/api/anomaly/stats` | Anomaliya statistikasi |

### 4.3 `app/routers/dashboard.py` endpointlari
| Method | Path | Tavsif |
|--------|------|--------|
| GET | `/api/dashboard/summary` | Umumiy statistika |

**Summary qaytarishi kerak:**
```json
{
  "total_sensor_data": 7000,
  "total_anomalies": 42,
  "anomaly_percentage": 0.6,
  "sensor_types": ["temperature", "cpu", "machine"],
  "latest_anomaly": "2024-01-15T10:30:00",
  "latest_model": {
    "name": "autoencoder_temperature",
    "accuracy": 0.95,
    "f1": 0.87,
    "created_at": "2024-01-14"
  }
}
```

---

## BOSQICH 5: Frontend Asosi

### 5.1 Loyiha yaratish
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install axios recharts antd react-router-dom @ant-design/icons
```

### 5.2 `vite.config.js` - proxy sozlash
```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

### 5.3 `src/services/api.js`
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Data
export const uploadData = (file, sensorType) => { /* FormData POST */ };
export const getDataList = (sensorType, limit, offset) => { /* GET */ };
export const getDataStats = (sensorType) => { /* GET */ };
export const getSensors = () => { /* GET */ };

// Model
export const trainModel = (params) => { /* POST */ };
export const getTrainStatus = () => { /* GET */ };
export const getTrainHistory = () => { /* GET */ };

// Anomaly
export const detectAnomalies = (sensorType) => { /* POST */ };
export const getAnomalyResults = (sensorType, limit, offset) => { /* GET */ };
export const getAnomalyStats = () => { /* GET */ };

// Dashboard
export const getDashboardSummary = () => { /* GET */ };
```

### 5.4 `src/App.jsx` - Router
```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
// 4 ta sahifa import

<BrowserRouter>
  <Layout>
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/data" element={<DataPage />} />
      <Route path="/training" element={<TrainingPage />} />
      <Route path="/analysis" element={<AnalysisPage />} />
    </Routes>
  </Layout>
</BrowserRouter>
```

### 5.5 Layout komponentlari
- **Sidebar:** Antd `Menu` - 4 ta link (Dashboard, Ma'lumotlar, O'qitish, Tahlil)
- **Header:** Logo + sarlavha "Smart Home Anomaly Detection"
- **Layout:** Antd `Layout` - Sidebar chap, Content o'ng

---

## BOSQICH 6: Dashboard Sahifasi

### 6.1 `StatCards.jsx`
Antd `Card` + `Statistic` bilan 4 ta karta:
- Jami ma'lumotlar soni (ko'k)
- Aniqlangan anomaliyalar (qizil)
- Model aniqligi / F1 score (yashil)
- So'nggi anomaliya vaqti (sariq)

### 6.2 `TimeSeriesChart.jsx`
Recharts `LineChart`:
- X axis: vaqt (timestamp)
- Y axis: sensor qiymati (value)
- Sensor turini tanlash dropdown (Antd Select)
- Zoom va scroll imkoniyati

### 6.3 `AnomalyChart.jsx`
Recharts `ComposedChart`:
- `Line` - sensor qiymatlari (ko'k chiziq)
- `Scatter` - anomaliya nuqtalari (qizil doiralar)
- Anomaliya bo'lgan joylar vizual ajralib turishi kerak

### 6.4 `RecentAnomalies.jsx`
Antd `Table`:
- Ustunlar: Vaqt, Sensor turi, Qiymat, Anomaliya bali, Holat
- So'nggi 10 ta anomaliya
- Holat: qizil/yashil tag (Anomaliya/Normal)

---

## BOSQICH 7: Ma'lumotlar Boshqaruvi Sahifasi

### 7.1 `DataUpload.jsx`
- Antd `Upload.Dragger` - CSV faylni drag & drop qilish
- Sensor turini tanlash (Antd Select: temperature, cpu, machine, ...)
- "Yuklash" tugmasi
- Yuklash progressi va natijasi (nechta qator yuklandi)

### 7.2 `DataTable.jsx`
- Antd `Table` - pagination bilan
- Ustunlar: #, Vaqt, Qiymat, Sensor turi
- Sensor turi bo'yicha filter
- Jadvalni CSV ga export tugmasi (bonus)

---

## BOSQICH 8: Model O'qitish Sahifasi

### 8.1 `TrainForm.jsx`
Antd `Form` bilan parametrlar:
- Sensor turini tanlash (Select)
- Epochs: 10-200 (Slider yoki InputNumber, default: 50)
- Batch size: 16/32/64 (Select, default: 32)
- Window size: 10-100 (Slider, default: 30)
- Learning rate: 0.0001 - 0.01 (InputNumber, default: 0.001)
- "O'qitishni boshlash" tugmasi

### 8.2 `TrainProgress.jsx`
- O'qitish jarayonida: Antd `Progress` bar + holat matni
- API ga polling (har 2 sekundda `/api/model/status`)
- Tugagandan keyin: loss/val_loss grafigi

### 8.3 `TrainHistory.jsx`
- Antd `Table` - barcha oldingi o'qitishlar
- Ustunlar: Model nomi, Sensor turi, Epochs, Loss, Val Loss, F1, Sana
- Har bir qatorni bosib tafsilotini ko'rish

---

## BOSQICH 9: Anomaliya Tahlili Sahifasi

### 9.1 `AnomalyDetection.jsx`
- Sensor turini tanlash (Select)
- "Anomaliya aniqlash" tugmasi
- Natijalar yuklanayotganda: Antd `Spin` loading

### 9.2 `ResultsView.jsx`
3 ta bo'lim:

**A) Anomaliya grafigi:**
Recharts `ComposedChart`:
- `Line`: sensor qiymatlari (ko'k)
- `Scatter`: anomaliya nuqtalari (qizil)
- `ReferenceLine`: threshold chizig'i (to'q qizil punktir)

**B) Reconstruction Error grafigi:**
Recharts `AreaChart`:
- `Area`: reconstruction error qiymatlari
- `ReferenceLine`: threshold chizig'i
- Threshold dan yuqori joy qizil rangda

**C) Natijalar jadvali:**
Antd `Table`:
- Ustunlar: Vaqt, Asl qiymat, Qayta tiklangan qiymat, Error, Holat
- Anomaliya qatorlari qizil fon bilan
- Export CSV tugmasi

---

## BOSQICH 10: Integratsiya va Tekshirish

### 10.1 Ishga tushirish
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python run.py
# http://localhost:8000/docs da Swagger ochilishi kerak

# Terminal 2: Frontend
cd frontend
npm run dev
# http://localhost:5173 da React app ochilishi kerak
```

### 10.2 End-to-end test scenariysi
1. **Ma'lumot yuklash:** DataPage → NAB CSV faylni yuklash → jadvalda ko'rinishi
2. **Statistika:** DataPage → stats ko'rsatilishi (count, mean, min, max)
3. **Model o'qitish:** TrainingPage → parametrlarni tanlash → "O'qitish" → progress → natija
4. **Anomaliya aniqlash:** AnalysisPage → sensor tanlash → "Aniqlash" → grafik + jadval
5. **Dashboard:** DashboardPage → barcha statistikalar, grafiklar to'g'ri ko'rinishi

### 10.3 Xatolarni tekshirish
- Backend: `http://localhost:8000/docs` da har bir endpointni sinash
- CORS xatosi: `main.py` dagi `allow_origins` ni tekshirish
- Model xatosi: `saved_models/` papkada `.h5` fayl borligini tekshirish
- DB xatosi: `smart_home.db` fayl yaratilganini tekshirish

---

## API Endpointlari Umumiy Jadvali

| # | Method | Endpoint | Tavsif |
|---|--------|----------|--------|
| 1 | POST | `/api/data/upload` | CSV fayl yuklash |
| 2 | GET | `/api/data/list?sensor_type=&limit=&offset=` | Ma'lumotlar ro'yxati |
| 3 | GET | `/api/data/stats?sensor_type=` | Statistika |
| 4 | GET | `/api/data/sensors` | Sensor turlari |
| 5 | DELETE | `/api/data/{sensor_type}` | Ma'lumot o'chirish |
| 6 | POST | `/api/model/train` | Model o'qitish |
| 7 | GET | `/api/model/status` | O'qitish holati |
| 8 | GET | `/api/model/history` | O'qitish tarixi |
| 9 | POST | `/api/anomaly/detect` | Anomaliya aniqlash |
| 10 | GET | `/api/anomaly/results?sensor_type=` | Anomaliya natijalari |
| 11 | GET | `/api/anomaly/stats` | Anomaliya statistikasi |
| 12 | GET | `/api/dashboard/summary` | Dashboard umumiy ko'rsatkichlar |

---

## Foydali Eslatmalar

1. **Autoencoder nima uchun ishlaydi:** Model faqat NORMAL ma'lumotlarni ko'rib o'rganadi. Anomal ma'lumotni qayta tiklay olmaydi → yuqori error → anomaliya.

2. **NAB dataset formati:** Har bir CSV da `timestamp` va `value` ustunlari bor. Anomaliyalar alohida `labels` papkasida belgilangan.

3. **Threshold tanlash:** `k=3` standart, lekin sensitivity ni sozlash uchun `k=2` (ko'proq anomaliya topadi) yoki `k=4` (kamroq) ishlatish mumkin.

4. **Model saqlash:** `model.save("model.h5")` va `load_model("model.h5")` - TensorFlow/Keras bilan.

5. **Scaler saqlash:** `joblib.dump(scaler, "scaler.pkl")` va `joblib.load("scaler.pkl")` - yangi ma'lumotni xuddi shu tarzda normalizatsiya qilish uchun.
