# Development Guide

Bu hujjat loyihani rivojlantirish va lokal ishlab chiqish tartibini tushuntiradi.

## Ishlash tartibi

Loyihada backend va frontend alohida ishga tushiriladi:

- backend: `localhost:8000`
- frontend: `localhost:5173`

## Backend development

Ishga tushirish:

```bash
cd backend
source .venv311/bin/activate
python run.py
```

Muhim fayllar:

- `app/main.py`
- `app/config.py`
- `app/database.py`
- `app/routers/`
- `app/services/`
- `app/ml/`

## Frontend development

Ishga tushirish:

```bash
cd frontend
npm run dev
```

Muhim fayllar:

- `src/App.tsx`
- `src/pages/`
- `src/components/`
- `src/services/api.ts`
- `src/services/types.ts`
- `src/lib/format.ts`

## Tavsiya etilgan oqim

1. Backendni ishga tushiring.
2. Frontendni ishga tushiring.
3. Swagger orqali endpointni tekshiring.
4. Frontend orqali real UI oqimini tekshiring.
5. O'zgarishdan keyin build va smoke test bajaring.

## Ishlatiladigan scriptlar

### Backend

```bash
python run.py
```

### Frontend

```bash
npm run dev
npm run build
npm run lint
npm test
```

### Root

```bash
backend/.venv311/bin/python scripts/e2e_smoke.py
```

## Frontend stack izohi

Joriy frontend stack:

- React + TypeScript
- Tailwind CSS
- shadcn/ui + Radix UI
- TanStack Query
- Axios
- Recharts
- Sonner

## Backend stack izohi

- FastAPI
- SQLAlchemy
- SQLite
- TensorFlow / Keras
- Pandas / NumPy / scikit-learn

## Kod bilan ishlash qoidalari

- Datasetlarni `source_file` bo'yicha ajrating.
- API xatolarini `detail` maydoni orqali foydalanuvchiga chiqarishga harakat qiling.
- Frontendda loading, empty va error state bo'lishi kerak.
- Training va detection oqimlari dataset-level bo'lishi kerak.
- CSV export endpointlariga mos blob download ishlating.

## Tavsiya etilgan tekshiruv ketma-ketligi

1. `npm run build`
2. `python3 -m compileall backend/app backend/run.py`
3. `backend/.venv311/bin/python scripts/e2e_smoke.py`

## Rivojlantirish uchun keyingi yo'nalishlar

- Frontend bundle optimizatsiyasi
- Qo'shimcha unit/integration testlar
- Docker packaging
- Auth qo'shish
- Real-time streaming data
