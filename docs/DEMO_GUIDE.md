# Demo va Himoya Ssenariysi

Bu hujjat loyihani himoyada qanday ko'rsatish kerakligini qisqa va aniq tartibda beradi.

## 1. Tayyorlash

Backend muhit:

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

Brauzer:

```text
http://localhost:5173
```

Backend docs:

```text
http://localhost:8000/docs
```

## 2. Demo Uchun Dataset Tayyorlash

Agar NAB sample fayllar hali yuklanmagan bo'lsa:

```bash
bash scripts/download_nab_samples.sh
```

Sample fayllar:

- `ambient_temperature_system_failure.csv`
- `cpu_utilization_asg_misconfiguration.csv`
- `machine_temperature_system_failure.csv`

## 3. Eng Tez Demo Oqimi

Dashboard sahifasidan boshlash tavsiya qilinadi.

1. `/` Dashboard sahifasini oching.
2. `Quick Demo` kartasidan sample dataset tanlang.
3. `Demoni ishga tushirish` tugmasini bosing.
4. Jarayon quyidagicha ketadi:
   - sample import;
   - background model training;
   - anomaly detection;
   - dashboard update.
5. Dashboard summary kartalari, time-series chart va anomaly chartni ko'rsating.

## 4. To'liq Qo'lda Demo Oqimi

### Data sahifasi

1. `/data` sahifasiga o'ting.
2. Local NAB sample import qiling yoki CSV upload qiling.
3. Stats kartalarini ko'rsating:
   - qatorlar soni;
   - o'rtacha qiymat;
   - standart og'ish.
4. Dataset filterini ko'rsating.
5. CSV export tugmasini ko'rsating.

### Training sahifasi

1. `/training` sahifasiga o'ting.
2. Dataset tanlang.
3. Parametrlarni tushuntiring:
   - `epochs`;
   - `batch_size`;
   - `window_size`;
   - `learning_rate`.
4. Training boshlang.
5. Progress bar va `loss / val_loss` grafigini ko'rsating.
6. Training history qatorini bosing va detail modalni ko'rsating.

### Analysis sahifasi

1. `/analysis` sahifasiga o'ting.
2. Dataset va training model tanlang.
3. Anomaly detection boshlang.
4. 3 ta natija bo'limini ko'rsating:
   - sensor qiymati va reconstructed value grafigi;
   - reconstruction error grafigi;
   - result table.
5. Threshold chizig'ini tushuntiring.
6. Anomaly qatorlari qizil bilan ajratilganini ko'rsating.
7. CSV export tugmasini ko'rsating.

## 5. Himoyada Aytish Uchun Qisqa Izoh

Loyiha FastAPI backend, React frontend va LSTM Autoencoder modelidan tashkil topgan. Sensor data CSV formatda yuklanadi, backend uni SQLite bazaga saqlaydi. Training paytida sensor qiymatlari normalizatsiya qilinadi va sliding window orqali LSTM Autoencoder modeliga beriladi. Model normal holatlarni qayta tiklashni o'rganadi. Detection paytida qayta tiklash xatosi, ya'ni reconstruction error, threshold bilan solishtiriladi. Agar error threshold qiymatidan katta bo'lsa, tizim bu holatni anomaliya deb belgilaydi.

## 6. Screenshot Checklist

Himoya yoki hisobot uchun quyidagi screenshotlar yetarli:

- Dashboard umumiy ko'rinishi.
- Quick Demo ishlayotgan progress.
- Data sahifasida sample import va table.
- Training sahifasida progress va loss chart.
- Training history detail modal.
- Analysis sahifasida anomaly chart.
- Reconstruction error chart.
- Result table va CSV export tugmasi.
- Swagger `/docs` endpointlar ro'yxati.

## 7. Ishonchlilikni Ko'rsatish

Demo oldidan quyidagi testni ishlating:

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

Bu test asosiy backend pipeline ishlayotganini isbotlaydi.

## 8. Ehtimoliy Savollarga Javob

**Nima uchun Autoencoder?**

Autoencoder normal data strukturani o'rganadi. Anomal data normal strukturaga mos kelmagani uchun model uni yaxshi qayta tiklay olmaydi va reconstruction error oshadi.

**Threshold qanday topiladi?**

Training reconstruction errorlari bo'yicha `mean + k * std` formula ishlatiladi. Bu loyihada default `k = 3`.

**Nima uchun LSTM?**

Sensor data vaqt ketma-ketligi bo'lgani uchun LSTM oldingi vaqt nuqtalaridagi kontekstni hisobga oladi.

**Dataset aralashib ketmaydimi?**

Yo'q. Har bir dataset `source_file` bilan ajratilgan, training va detection aniq datasetga bog'lanadi.

**Metriclar qayerdan olinadi?**

NAB `combined_windows.json` label fayli mavjud bo'lsa, detection flaglari label oynalari bilan solishtirilib `accuracy`, `precision`, `recall`, `f1` hisoblanadi.
