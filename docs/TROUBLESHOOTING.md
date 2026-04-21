# Troubleshooting

Bu hujjat eng ko'p uchraydigan muammolar va ularning yechimlarini jamlaydi.

## 1. TensorFlow o'rnatilmayapti

### Belgisi

- `ImportError: No module named tensorflow`
- yoki install paytida version conflict

### Yechim

Python `3.11` dan foydalaning:

```bash
cd backend
python3.11 -m venv .venv311
source .venv311/bin/activate
pip install -r requirements.txt
```

## 2. Backend ochilmayapti

### Belgisi

- `http://localhost:8000/health` ishlamaydi

### Yechim

```bash
cd backend
source .venv311/bin/activate
python run.py
```

Port band bo'lsa:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

## 3. Frontend ochilmayapti

### Belgisi

- `http://localhost:5173` ishlamaydi

### Yechim

```bash
cd frontend
npm install
npm run dev
```

Port band bo'lsa:

```bash
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

## 4. Dashboardda ma'lumot yo'q

### Belgisi

- summary bo'sh
- chart bo'sh

### Yechim

Sample import qiling:

```bash
bash scripts/download_nab_samples.sh
```

Keyin frontenddagi `Quick Demo` yoki `Data` sahifasi orqali sample import qiling.

## 5. Training boshlanmayapti

### Belgisi

- `Trening uchun sensor ma'lumotlari topilmadi`
- yoki conflict xatosi

### Yechim

- dataset mavjudligini tekshiring
- `Data` sahifasida source listni tekshiring
- boshqa training hali tugamagan bo'lishi mumkin

## 6. Detection natijasi bo'sh

### Belgisi

- result table bo'sh
- anomaly topilmadi

### Yechim

- oldin training bo'lganini tekshiring
- to'g'ri `source_file` tanlanganini tekshiring
- `training_id` va `source_file` mos bo'lishi kerak

## 7. `So'nggi anomaliyalar` blokida eski sana ko'rinadi

### Izoh

NAB sample datasetlar original ravishda eski timestamp bilan keladi.

### Joriy yechim

Frontend display qatlamida eski sanalar hozirgi davrga yaqin ko'rinishda map qilinadi. Backenddagi original data esa o'zgarmaydi.

## 8. CSV export ishlamayapti

### Belgisi

- tugma bosilganda fayl tushmaydi

### Yechim

- browser popup/download ruxsatlarini tekshiring
- backend `Content-Disposition` header qaytaryaptimi tekshiring
- `/api/data/export` yoki `/api/anomaly/export` endpointini Swagger orqali sinab ko'ring

## 9. Smoke test yiqilyapti

### Belgisi

- `scripts/e2e_smoke.py` assertion xatosi

### Yechim

- backend muhit to'g'ri ishlayaptimi
- dependencies o'rnatilganmi
- TensorFlow import bo'lyaptimi
- o'zgarish pipeline logikasini sindirmaganmi

## 10. Frontend build warning

### Belgisi

- `Some chunks are larger than 500 kB after minification`

### Izoh

Bu hozircha warning, runtime xato emas.

### Keyingi optimizatsiya

- route-level code splitting
- manual chunk config
- kam ishlatiladigan UI qismlarini lazy load qilish
