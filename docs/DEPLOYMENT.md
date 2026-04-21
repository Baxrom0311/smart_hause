# Deployment Notes

Bu hujjat loyiha lokal demo darajasidan deploy yoki release holatiga olib chiqish uchun tavsiyalarni beradi.

## Joriy holat

Loyiha hozir lokal demo va diplom himoyasi uchun tayyorlangan. Production deployment to'liq avtomatlashtirilmagan.

## Backend deployment

### Tavsiya etilgan stack

- Python 3.11
- Uvicorn yoki Gunicorn + Uvicorn workers
- Reverse proxy: Nginx
- SQLite o'rniga PostgreSQL tavsiya etiladi

### Muhim masalalar

- `saved_models/` va scaler fayllar uchun persistent storage kerak
- upload qilingan datasetlar uchun ham persistent volume kerak
- environment variablelar tashqi konfiguratsiyaga chiqarilishi kerak

## Frontend deployment

Frontend Vite build:

```bash
cd frontend
npm run build
```

Hosil bo'lgan `dist/` ni Nginx yoki statik hosting orqali serve qilish mumkin.

### Frontend environment

Productionda quyidagini berish mumkin:

```text
VITE_API_BASE_URL=https://api.example.com
```

Yoki reverse proxy ishlatilsa, default `/api` yetadi.

## Tavsiya etilgan production o'zgarishlar

- SQLite -> PostgreSQL
- auth qo'shish
- HTTPS
- logging va monitoring
- rate limiting
- backup strategiyasi
- frontend bundle optimizatsiyasi

## Minimal release checklist

- `npm run build` o'tgan
- backend smoke test o'tgan
- `http://localhost:8000/docs` ishlagan
- sample import ishlagan
- training ishlagan
- detection ishlagan
- CSV export ishlagan

## Docker bo'yicha keyingi ish

Hozir repo ichida Dockerfile yoki compose konfiguratsiyasi tayyor emas. Agar deploy kerak bo'lsa, keyingi bosqich sifatida quyidagilar tayyorlanadi:

- backend Dockerfile
- frontend Dockerfile
- docker-compose.yml
- volume va environment konfiguratsiyasi

## Demo release uchun tavsiya

Agar faqat himoya yoki ko'rsatish kerak bo'lsa:

1. backendni lokal yoki VPS da ko'taring
2. frontend build qiling
3. reverse proxy bilan `/api` backendga yo'naltiring
4. sample datasetlar va model storage pathlarni tayyorlab qo'ying
