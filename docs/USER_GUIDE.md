# Foydalanuvchi Qo'llanmasi

Bu hujjat tizimdan foydalanuvchi, rahbar yoki tekshiruvchi uchun yozilgan. Maqsad: ilovani qanday ishlatish, qaysi sahifa nima vazifa bajarishi va natijalarni qanday talqin qilishni tushuntirish.

## 1. Tizimga kirishdan oldin

Quyidagilar ishga tushgan bo'lishi kerak:

- backend: `http://localhost:8000`
- frontend: `http://localhost:5173`

Tekshiruv:

- health: `http://localhost:8000/health`
- swagger: `http://localhost:8000/docs`

## 2. Asosiy menyu

Ilovada 4 ta asosiy sahifa mavjud:

- `Dashboard`
- `Ma'lumotlar`
- `Model o'qitish`
- `Tahlil`

Desktopda chap sidebar mavjud. Mobil qurilmada menyu yig'iladigan shaklda ishlaydi.

## 3. Dashboard

Dashboard loyiha bo'yicha eng tez umumiy ko'rinishni beradi.

Asosiy bloklar:

- `Jami ma'lumotlar`: bazadagi barcha sensor yozuvlari soni
- `Anomaliyalar`: aniqlangan anomaliya yozuvlari soni
- `Anomaliya foizi`: anomaliyalar ulushi
- `So'nggi model · F1`: eng oxirgi modelning sifat ko'rsatkichi
- `Tezkor demo`: bir tugma bilan to'liq pipeline
- `Sensor qiymatlari va anomaliyalar`: vaqt qatori ko'rinishi
- `So'nggi anomaliyalar`: eng yangi flaglangan yozuvlar

### Tezkor demo qanday ishlaydi

`Tezkor demo` kartasida sample dataset tanlanadi va quyidagi oqim avtomatik bajariladi:

1. sample dataset import qilinadi
2. model o'qitiladi
3. status polling orqali training progress kuzatiladi
4. anomaly detection bajariladi
5. dashboard qayta yangilanadi

Bu demo himoya paytida eng qulay usul hisoblanadi.

## 4. Ma'lumotlar sahifasi

Bu sahifada sensor ma'lumotlari yuklanadi va boshqariladi.

Imkoniyatlar:

- CSV upload
- sample import
- `sensor_type` bo'yicha filter
- `source_file` bo'yicha filter
- statistika ko'rish
- jadval orqali ma'lumotlarni ko'rish
- datasetni o'chirish
- CSV export

### CSV format talabi

CSV kamida quyidagi ustunlarga ega bo'lishi kerak:

```text
timestamp,value
```

Misol:

```csv
timestamp,value
2026-04-20T10:00:00,72.1
2026-04-20T11:00:00,71.8
```

### `sensor_type` va `source_file` farqi

- `sensor_type`: sensor kategoriyasi, masalan `temperature`, `cpu`
- `source_file`: aynan qaysi dataset import qilingani

Bir xil `sensor_type` bo'lgan bir nechta dataset aralashib ketmasligi uchun tizim `source_file` ni asosiy dataset identifikatori sifatida ishlatadi.

## 5. Model o'qitish sahifasi

Bu sahifa LSTM Autoencoder modelini o'qitish uchun ishlatiladi.

Asosiy parametrlar:

- `epochs`
- `batch_size`
- `window_size`
- `learning_rate`

Ko'rinadigan natijalar:

- training holati
- joriy epoch
- progress foizi
- `train_loss`
- `val_loss`
- loss grafigi
- training history

### Training history

Oldingi barcha treninglar tarixda saqlanadi. Qatorni bosganda:

- model nomi
- dataset
- sensor turi
- threshold
- accuracy
- precision
- recall
- f1
- model path
- scaler path

ko'rinadi.

## 6. Tahlil sahifasi

Bu sahifada o'qitilgan model yordamida anomaliya aniqlanadi.

Jarayon:

1. dataset tanlanadi
2. model tanlanadi yoki avtomatik variant qoldiriladi
3. `Aniqlashni boshlash` bosiladi
4. natijalar chart va jadvalda ko'rsatiladi

Natija bloklari:

- `Jami oynalar`
- `Anomaliyalar`
- `Chegara (threshold)`
- `Sensor`

Chartlar:

- original qiymat va reconstructed qiymat
- reconstruction error va threshold

Jadval:

- vaqt
- original qiymat
- qayta tiklangan qiymat
- xatolik
- threshold
- holat

Anomaliya qatorlari qizg'ish fonda ajratiladi.

## 7. Natijalarni qanday talqin qilish kerak

### `Normal`

Model ushbu nuqtani odatiy naqshga yaqin deb baholagan.

### `Anomaliya`

Model qayta tiklash xatoligi thresholddan katta bo'lgan nuqtani g'ayritabiiy deb belgilagan.

### `Threshold`

Bu anomaliya uchun chegara qiymati. `error > threshold` bo'lsa, nuqta anomal deb olinadi.

### `Reconstructed value`

Bu modelning normal deb hisoblagan qayta tiklangan signalidir. Original signal bilan katta farq paydo bo'lsa, error oshadi.

## 8. CSV export

Quyidagi sahifalarda eksport mavjud:

- `Ma'lumotlar`: tanlangan dataset bo'yicha xom sensor data
- `Tahlil`: anomaly natijalari yoki faqat anomaly qatorlari

Browser faylni `Content-Disposition` sarlavhasidagi nom bilan saqlashga harakat qiladi.

## 9. Tavsiya etilgan foydalanish tartibi

Eng sodda demo:

1. `Dashboard`
2. `Tezkor demo`
3. chart va statistikani ko'rsatish
4. `Tahlil` sahifasiga o'tib natijalarni chuqur ko'rsatish

To'liq texnik oqim:

1. `Ma'lumotlar` sahifasida sample import
2. `Model o'qitish` sahifasida training
3. `Tahlil` sahifasida detection
4. `Dashboard` orqali yakuniy summary

## 10. Muhim eslatmalar

- Sample datasetlar original manbada eski timestamp bilan bo'lishi mumkin.
- Frontend display qatlamida eski sanalar hozirgi davrga yaqin ko'rinishda beriladi.
- Backenddagi original timestamp o'zgarmaydi.
- Agar natija chiqmasa, avval dataset import qilinganini va training bajarilganini tekshiring.
