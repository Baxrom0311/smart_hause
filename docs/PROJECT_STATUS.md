# Loyiha Holati

Bu hujjat `REJA.md` dagi bosqichlar bilan joriy kod holatini solishtiradi.

## Umumiy Xulosa

Loyiha hozir MVP va diplom demo darajasida ishlaydi. Backend, frontend, ML pipeline, dataset import, model o'qitish, anomaliya aniqlash, dashboard, CSV export, hujjatlar paketi va end-to-end smoke test mavjud.

## Bosqichlar Bo'yicha Holat

| Bosqich | Rejadagi vazifa | Holat |
|---|---|---|
| 1 | Backend asosi | Bajarilgan |
| 2 | Ma'lumot yuklash va preprocessing | Bajarilgan |
| 3 | LSTM Autoencoder model | Bajarilgan |
| 4 | Anomaliya aniqlash API | Bajarilgan |
| 5 | Frontend asosi | Bajarilgan |
| 6 | Dashboard sahifasi | Bajarilgan |
| 7 | Ma'lumotlar boshqaruvi sahifasi | Bajarilgan |
| 8 | Model o'qitish sahifasi | Bajarilgan |
| 9 | Anomaliya tahlili sahifasi | Bajarilgan |
| 10 | Integratsiya va tekshirish | Avtomatlashtirilgan smoke test qo'shildi |

## Qo'shilgan Qo'shimcha Imkoniyatlar

- NAB sample datasetlarni bir bosishda import qilish.
- `source_file` bo'yicha dataset-level ajratish.
- Dataset bo'yicha alohida delete.
- Dataset va anomaly natijalarini CSV export qilish.
- Training background job sifatida ishlashi.
- Training progress polling va epoch bo'yicha `loss / val_loss` grafigi.
- Training history detail modal.
- NAB label fayli asosida `accuracy / precision / recall / f1` hisoblash.
- Dashboard `Quick Demo` pipeline.
- Dashboard va analysis chartlarida zoom/scroll brush.
- To'liq hujjatlar paketi: setup, architecture, data model, API, testing, demo.
- `scripts/e2e_smoke.py` bilan avtomatik backend pipeline tekshiruvi.

## Hozir Ishlaydigan Demo Oqim

1. Backend ishga tushiriladi.
2. Frontend ishga tushiriladi.
3. Dashboard ochiladi.
4. `Quick Demo` kartasida NAB sample tanlanadi.
5. Sample import qilinadi.
6. Model background rejimda o'qitiladi.
7. Anomaliya aniqlash bajariladi.
8. Dashboard summary, chart va recent anomaly jadvali yangilanadi.

## Qolgan Ishlar

Asosiy reja bajarilgan. Qolgan ishlar diplom himoyasi va sifatni oshirishga tegishli:

- UI screenshotlarini tayyorlash.
- Diplom matni uchun arxitektura va algoritm izohlarini rasmiylashtirish.
- Real NAB datasetlar bo'yicha yakuniy natijalar jadvalini shakllantirish.
- Agar kerak bo'lsa, deploy yoki video demo tayyorlash.
- Unit testlar sonini ko'paytirish.

## Ishga Tushirish

Backend:

```bash
cd backend
source .venv311/bin/activate
python run.py
```

Frontend:

```bash
cd frontend
npm run dev
```

Smoke test:

```bash
backend/.venv311/bin/python scripts/e2e_smoke.py
```
