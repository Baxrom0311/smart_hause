# Setup Guide

Bu hujjat loyihani noldan ishga tushirish uchun kerak.

## Talablar

### Backend

- Python `3.11`
- `pip`

### Frontend

- Node.js `18+`
- npm

## 1. Repo strukturasini tekshirish

Asosiy katalog:

```text
smart_hause/
```

Muhim papkalar:

- `backend/`
- `frontend/`
- `docs/`
- `scripts/`

## 2. Backend muhitini tayyorlash

```bash
cd backend
python3.11 -m venv .venv311
source .venv311/bin/activate
pip install -r requirements.txt
```

## 3. Frontend muhitini tayyorlash

```bash
cd frontend
npm install
```

## 4. Sample datasetlarni yuklash

```bash
cd /path/to/smart_hause
bash scripts/download_nab_samples.sh
```

Yuklanadigan manzillar:

- `backend/data/nab/`
- `backend/data/nab_labels/`

## 5. Backendni ishga tushirish

```bash
cd backend
source .venv311/bin/activate
python run.py
```

Tekshirish:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

## 6. Frontendni ishga tushirish

```bash
cd frontend
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## 7. Environment va konfiguratsiya

### Backend

Backend quyidagi environment variablelarni qo'llab-quvvatlaydi:

- `SMART_HOME_DATABASE_URL`
- `SMART_HOME_SAVED_MODELS_DIR`
- `SMART_HOME_NAB_DATA_DIR`
- `SMART_HOME_NAB_LABELS_DIR`

Agar bu qiymatlar berilmasa, loyiha default lokal pathlardan foydalanadi.

### Frontend

Frontendda optional:

- `VITE_API_BASE_URL`

Default holatda frontend `/api` va `/health` ni Vite proxy orqali backendga yuboradi.

## 8. Birinchi tekshiruv

Smoke test:

```bash
backend/.venv311/bin/python scripts/e2e_smoke.py
```

Kutiladigan natija:

```text
health=ok
uploaded_rows=120
training_id=1
loss_points=2
total_windows=109
exports=ok
```
