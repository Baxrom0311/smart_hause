# Himoya Nutqi

Quyidagi matn 5-7 daqiqalik diplom himoyasi uchun tayyorlangan. Uni o'zingizning uslubingizga moslab qisqartirish yoki kengaytirish mumkin.

## 1. Kirish

Assalomu alaykum. Mening diplom loyiham mavzusi: vaqt ketma-ketligi asosidagi ma'lumotlarda LSTM Autoencoder mashinali o'qitish algoritmi yordamida aqlli uy sensorlaridan olingan ma'lumotlardan anomaliyalarni aniqlash web ilovasini ishlab chiqish.

Ushbu loyiha aqlli uy tizimlarida sensorlardan keladigan ma'lumotlarni tahlil qilish, odatiy holatdan chetga chiqadigan qiymatlarni aniqlash va ularni foydalanuvchiga tushunarli web interfeys orqali ko'rsatishga qaratilgan.

## 2. Muammo Dolzarbligi

Aqlli uy tizimlarida harorat, namlik, energiya sarfi, CPU monitoring yoki boshqa sensorlar doimiy ravishda ma'lumot yuboradi. Bu ma'lumotlar vaqt ketma-ketligi ko'rinishida bo'ladi. Agar sensor noto'g'ri ishlasa, qurilma nosoz bo'lsa yoki tizimda kutilmagan holat yuz bersa, qiymatlar odatiy naqshdan chetga chiqadi.

Bunday holatlarni qo'lda kuzatish qiyin. Shu sababli avtomatik anomaliya aniqlash tizimi kerak bo'ladi.

## 3. Taklif Qilingan Yechim

Loyihada backend, frontend va mashinali o'qitish modeli birlashtirilgan web ilova ishlab chiqildi.

Backend qismi FastAPI yordamida yozildi. Ma'lumotlar SQLite bazasida saqlanadi. Frontend React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query va Recharts asosida ishlab chiqildi. Mashinali o'qitish qismida TensorFlow/Keras orqali LSTM Autoencoder modeli ishlatiladi.

Foydalanuvchi CSV formatdagi sensor ma'lumotini yuklaydi yoki tayyor NAB sample datasetni import qiladi. Keyin model shu dataset asosida o'qitiladi. O'qitilgan model yordamida anomaliya aniqlanadi va natijalar dashboard, grafik va jadval ko'rinishida chiqariladi.

## 4. Algoritm Mantiqi

LSTM Autoencoder normal vaqt ketma-ketliklarini qayta tiklashni o'rganadi. Training paytida kirish va chiqish bir xil bo'ladi, ya'ni model `X -> X` shaklida o'qitiladi.

Normal ma'lumotni model yaxshi qayta tiklaydi, reconstruction error past bo'ladi. Anomal ma'lumotni esa model yaxshi qayta tiklay olmaydi, shuning uchun reconstruction error yuqori chiqadi.

Threshold quyidagi formula asosida hisoblanadi:

```text
threshold = mean(error) + k * std(error)
```

Bu loyihada default `k = 3`. Agar reconstruction error threshold qiymatidan katta bo'lsa, tizim bu nuqtani anomaliya deb belgilaydi.

## 5. Dastur Arxitekturasi

Dastur 3 asosiy qatlamdan iborat:

- Backend: FastAPI, SQLAlchemy, SQLite, TensorFlow.
- Frontend: React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Recharts.
- ML pipeline: preprocessing, LSTM Autoencoder training, prediction, evaluation.

Backendda `SensorData`, `TrainingHistory` va `Anomaly` jadvallari mavjud. `SensorData` sensor o'lchovlarini saqlaydi. `TrainingHistory` model o'qitish natijalarini, parametrlarini, threshold va metriclarni saqlaydi. `Anomaly` esa detection natijalarini saqlaydi.

Datasetlar `source_file` orqali ajratiladi. Bu bir xil sensor turiga ega bir nechta dataset aralashib ketmasligi uchun muhim.

## 6. Frontend Imkoniyatlari

Ilovada 4 ta asosiy sahifa bor.

Dashboard sahifasida umumiy statistikalar, vaqt ketma-ketligi grafigi, anomaly xaritasi va Quick Demo kartasi mavjud.

Data sahifasida CSV upload, NAB sample import, dataset filter, statistika, jadval, delete va CSV export funksiyalari bor.

Training sahifasida model parametrlarini tanlash, background training progress, epoch bo'yicha loss/val_loss grafigi va training history detail modal mavjud.

Analysis sahifasida anomaly detection bajariladi. Natijalar sensor qiymati, reconstructed value, reconstruction error grafigi va jadvalda ko'rsatiladi.

## 7. Tekshirish

Loyihada end-to-end smoke test yozildi. U vaqtinchalik SQLite DB bilan quyidagi oqimni tekshiradi:

```text
upload -> stats -> train -> detect -> results -> dashboard -> CSV export
```

Bu test lokal DB ni buzmaydi va backend pipeline ishlayotganini tez tekshiradi.

## 8. Natija

Natijada aqlli uy sensor ma'lumotlari uchun anomaliya aniqlash web ilovasi ishlab chiqildi. Ilova CSV ma'lumotni qabul qiladi, LSTM Autoencoder modelini o'qitadi, anomaliya topadi, natijalarni grafik va jadvalda ko'rsatadi hamda CSV export imkoniyatini beradi.

Loyiha diplom mavzusidagi asosiy talablarni bajaradi: vaqt ketma-ketligi, Autoencoder algoritmi, web ilova, sensor ma'lumotlari, anomaliya aniqlash va natijalarni vizual tahlil qilish.

E'tiboringiz uchun rahmat.
