# Smart Home Watch

Aqlli uy sensor ma'lumotlarida anomaliyalarni aniqlash uchun yaratilgan web ilova.

Loyiha FastAPI backend, React + TypeScript frontend va TensorFlow asosidagi LSTM Autoencoder modelidan tashkil topgan. Ilova `CSV` datasetlarni yuklaydi yoki NAB sample fayllarni import qiladi, modelni o'qitadi, anomaliyalarni aniqlaydi va natijalarni dashboard, chart va jadvallarda ko'rsatadi.

## Asosiy imkoniyatlar

- CSV upload va NAB sample import.
- Dataset-level filter va `source_file` bo'yicha ajratish.
- Background model training va progress polling.
- `loss / val_loss` training grafigi.
- Anomaliya aniqlash, reconstruction error tahlili.
- Dashboard `Quick Demo` oqimi.
- Data va anomaly natijalarini CSV export qilish.
- End-to-end smoke test.
- Diplom himoyasi uchun tayyor hujjatlar paketi.

## Texnologiyalar

### Backend

- FastAPI
- SQLAlchemy
- SQLite
- TensorFlow / Keras
- Pandas
- NumPy
- scikit-learn
- Joblib

### Frontend

- React 18
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui + Radix UI
- TanStack Query
- Axios
- Recharts
- Sonner

### Dataset

- NAB uslubidagi `timestamp,value` CSV fayllar

## Loyihaning tarkibi

```text
smart_hause/
├── backend/                 # FastAPI backend + ML pipeline
├── frontend/                # React + TypeScript frontend
├── docs/                    # To'liq hujjatlar
├── scripts/                 # Utility va smoke test skriptlari
├── REJA.md                  # Boshlang'ich loyiha rejasi
└── README.md
```

## Tezkor ishga tushirish

### 1. Backend

Python `3.11` tavsiya qilinadi.

```bash
cd backend
python3.11 -m venv .venv311
source .venv311/bin/activate
pip install -r requirements.txt
python run.py
```

Backend manzili:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend manzili:

```text
http://localhost:5173
```

## NAB sample dataset yuklash

Quyidagi skript 3 ta sample datasetni `backend/data/nab/` ichiga yuklaydi:

```bash
bash scripts/download_nab_samples.sh
```

Yuklanadigan fayllar:

- `ambient_temperature_system_failure.csv`
- `cpu_utilization_asg_misconfiguration.csv`
- `machine_temperature_system_failure.csv`

Skript `backend/data/nab_labels/combined_windows.json` ni ham yuklaydi. Shu fayl mavjud bo'lsa, training tugagandan keyin `accuracy`, `precision`, `recall`, `f1` metriclari hisoblanadi.

## Tekshirish

Backend pipeline uchun smoke test:

```bash
backend/.venv311/bin/python scripts/e2e_smoke.py
```

Smoke test quyidagi oqimni tekshiradi:

```text
health -> upload -> stats -> train -> status -> history -> detect -> results -> dashboard -> export
```

Bu test vaqtinchalik DB bilan ishlaydi va lokal `smart_home.db` faylini o'zgartirmaydi.

## Muhim endpointlar

- `GET /health`
- `POST /api/data/upload`
- `GET /api/data/samples`
- `POST /api/data/import-sample`
- `GET /api/data/list`
- `GET /api/data/export`
- `GET /api/data/sources`
- `GET /api/data/stats`
- `GET /api/data/sensors`
- `DELETE /api/data/source/{source_file}`
- `DELETE /api/data/{sensor_type}`
- `POST /api/model/train`
- `GET /api/model/status`
- `GET /api/model/history`
- `GET /api/model/history/{id}`
- `POST /api/anomaly/detect`
- `GET /api/anomaly/results`
- `GET /api/anomaly/results/{id}`
- `GET /api/anomaly/export`
- `GET /api/anomaly/stats`
- `GET /api/dashboard/summary`

## Frontend sahifalari

- `/` Dashboard
- `/data` Ma'lumotlar boshqaruvi
- `/training` Model o'qitish
- `/analysis` Anomaliya tahlili

## Hujjatlar

- [Docs index](docs/INDEX.md)
- [Setup guide](docs/SETUP.md)
- [Development guide](docs/DEVELOPMENT.md)
- [User guide](docs/USER_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data model](docs/DATA_MODEL.md)
- [Technical overview](docs/TECHNICAL_OVERVIEW.md)
- [API reference](docs/API_REFERENCE.md)
- [Testing guide](docs/TESTING.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Deployment notes](docs/DEPLOYMENT.md)
- [Project status](docs/PROJECT_STATUS.md)
- [Demo guide](docs/DEMO_GUIDE.md)
- [Defense speech](docs/DEFENSE_SPEECH.md)
- [Report outline](docs/REPORT_OUTLINE.md)

## Qaysi hujjatni kim o'qishi kerak

- Foydalanuvchi yoki rahbar uchun: `README`, `USER_GUIDE`, `DEMO_GUIDE`, `PROJECT_STATUS`
- Dasturchi uchun: `SETUP`, `DEVELOPMENT`, `ARCHITECTURE`, `DATA_MODEL`, `API_REFERENCE`, `TESTING`
- Diplom matni va himoya uchun: `TECHNICAL_OVERVIEW`, `DEFENSE_SPEECH`, `REPORT_OUTLINE`

## Joriy holat

Loyiha `REJA.md` dagi asosiy funksional bosqichlar bo'yicha bajarilgan:

- backend ishlaydi;
- frontend ishlaydi;
- sample import ishlaydi;
- training ishlaydi;
- anomaly detection ishlaydi;
- dashboard ishlaydi;
- export ishlaydi;
- smoke test mavjud.

## Eslatmalar

- Frontend build paytida katta bundle warning chiqishi mumkin. Bu runtime xatolik emas.
- NAB sample datasetlarning original timestampi eski bo'lishi mumkin. UI display qatlami ularni hozirgi davrga yaqin ko'rinishda ko'rsatadi, lekin backenddagi original data o'zgarmaydi.
