# Testing Guide

Bu hujjat loyihani qanday test qilishni tushuntiradi.

## 1. Minimal tekshiruv

Har bir katta o'zgarishdan keyin kamida quyidagini bajaring:

```bash
python3 -m compileall backend/app backend/run.py scripts/e2e_smoke.py
cd frontend && npm run build
cd ..
backend/.venv311/bin/python scripts/e2e_smoke.py
```

## 2. Backend smoke test

```bash
backend/.venv311/bin/python scripts/e2e_smoke.py
```

Tekshiradigan oqim:

- health
- upload
- stats
- train
- status
- history
- detect
- results
- dashboard
- export

Bu test:

- vaqtinchalik SQLite DB ishlatadi
- synthetic CSV yaratadi
- lokal ishlab turgan real DB ni o'zgartirmaydi

## 3. Frontend build test

```bash
cd frontend
npm run build
```

Bu:

- TypeScript/Vite build
- route va komponent importlari
- production bundle yig'ilishini tekshiradi

## 4. Frontend unit test

```bash
cd frontend
npm test
```

Loyiha ichida `Vitest` sozlangan. Hozir testlar minimal, lekin bu qatlam keyinchalik kengaytirilishi mumkin.

## 5. Frontend lint

```bash
cd frontend
npm run lint
```

## 6. Qo'lda test qilish

### Dashboard

- sahifa ochilishi
- Quick Demo ishlashi
- summary kartalari
- chartlar
- recent anomalies

### Data

- sample import
- CSV upload
- stats yangilanishi
- source filter
- delete
- CSV export

### Training

- dataset select
- training start
- progress polling
- loss graph
- history table
- detail modal

### Analysis

- dataset va model select
- detection start
- result charts
- threshold ko'rinishi
- result table
- anomaly export

## 7. Swagger orqali tekshirish

```text
http://localhost:8000/docs
```

Backend endpointlarni alohida sinash uchun ishlatiladi.

## 8. Tipik kutiladigan smoke test natijasi

```text
health=ok
uploaded_rows=120
training_id=1
loss_points=2
total_windows=109
exports=ok
```

## 9. Agar test yiqilsa

Avval quyidagilarni tekshiring:

- backend dependencies o'rnatilganmi
- `backend/.venv311` ishlayaptimi
- `frontend/node_modules` bor-mi
- sample data yuklanganmi
- portlar band emasmi

Keyin [Troubleshooting](TROUBLESHOOTING.md) hujjatini ko'ring.
