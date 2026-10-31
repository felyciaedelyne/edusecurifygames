# Pembaruan model ML (v2): lebih akurat + terhubung ke seluruh game

## Mana yang model ML-nya?
- `model_medsos.joblib` = model yang dipakai game (TF-IDF + Logistic Regression), dilatih oleh `train_medsos.py` / `Train_Medsos.ipynb`.
- `fitur.py` = pengolah teks + pembuat ciri (dipakai training DAN server). `penjelas.py` = pembuat alasan prediksi.
- `server.py` memuat model dan membuka `/predict`; `ml-hook.js` di browser memanggilnya.

## Apa yang berubah
**Akurasi.** Data latih 454 -> 1.088 contoh (151 template; contoh baru: penipuan bos/keluarga/instansi, jual-beli, kripto,
followers, KTA/pinjol, serta pesan NORMAL yang sulit: tautan YouTube/GitHub/Drive, OTP resmi, pesan edukasi, obrolan yang memuat kata
"transfer" atau "kode"). Ciri baru di `fitur.py`: merek palsu di domain, subdomain menumpuk, IP/@/punycode, domain umum tepercaya,
dan ciri ISI pesan (minta data rahasia, tekanan waktu, ancaman, hadiah, bayar di muka, mengaku pihak resmi, konteks edukasi).

| Uji (tidak ikut dilatih) | Model lama | Model baru |
|---|---|---|
| 36 soal game | 100% | 100% |
| 78 pesan tulisan tangan (`uji_mandiri.csv`) | 93,6% (recall phishing 87,5%) | 98,7% (recall 97,5%) |
| 40 pesan "buta" (`uji_buta.csv`) | 92,5% (recall 85%) | 97,5% (recall 95%) |
| GroupKFold per template | ~0,94 | ~0,98 |

**Hal yang perlu ditulis jujur di laporan:**
- `uji_mandiri` ditulis SEBELUM template baru dibuat, tetapi topik template baru saya pilih setelah melihat kesalahan model lama, jadi angkanya
  condong optimis. `uji_buta` baru ditulis setelah model baru dilatih; setelah itu kamus ciri diperluas (kata "kirim dana", "ke rek",
  "secepatnya", "jangan sampai ... tau") berdasarkan 2 kesalahan di sana, jadi angka 97,5% (naik dari 95%) juga bukan murni buta lagi.
- Semua uji kecil (36-78 pesan) dan ditulis oleh pembuat sistem. Di postingan sungguhan, angkanya bisa lebih rendah.
- Titik lemah yang masih ada: permintaan uang dari "keluarga/teman" tanpa tautan dan tanpa kata mendesak (mis. "pinjemin 700rb dulu transfer ke dana ...")
  masih bisa lolos dengan skor sedang. Cara terbaik memperbaikinya: tambahkan contoh NYATA ke `data/dataset_medsos.csv`.

## Bagaimana model sekarang terhubung ke game
1. Setiap task dinilai model otomatis saat dibuka (dan semua task dihangatkan sejak layar loading, jadi server Render yang "tidur" sudah bangun).
2. Setelah anak menjawab, muncul kartu **"Penilaian model Bima"**: persen phishing, apakah model dan anak sependapat / siapa yang benar, dan
   **alasan model** (mis. "Meniru nama merek", "Data rahasia + tekanan", "Nada mengingatkan/edukasi").
3. Tombol hint maskot menyebut 2 sinyal paling mencolok, bukan hanya persen. Tab Tweet juga menampilkan alasan model.
4. Lencana baru "Duet dengan AI" (8 kali sependapat dengan model) dan kartu "Tentang model AI" di tab Task (angka dari `/model-info`).
5. Log jawaban punya kolom baru: `modelPhishProb`, `modelSource`, `modelAgree`, `modelCorrect` (sebelumnya skor model hanya tercatat bila anak memakai hint).
6. Jika server model tidak terjangkau, game memakai aturan sederhana di perangkat dan memberi catatan di kartu (tidak error).
7. Jika `model_medsos.joblib` rusak atau dilatih dengan versi scikit-learn berbeda, `server.py` melatih ulang otomatis saat start. `render.yaml`
   juga melatih model saat build. `requirements.txt` tidak lagi mengunci scikit-learn ke satu versi.

## Struktur folder
```
server.py  fitur.py  penjelas.py  train_medsos.py  buat_dataset.py  Train_Medsos.ipynb
model_medsos.joblib  model_meta.json  requirements.txt  render.yaml
public/  (index.html, style.css, data.js, game.js, fx.js, ml-hook.js)
data/    (dataset_medsos.csv, game_items.csv, uji_mandiri.csv, uji_buta.csv)
```

---

# Langkah cepat (versi game baru)

1. Ekstrak zip ini, buka foldernya di VS Code (File > Open Folder).
2. Terminal > New Terminal, lalu jalankan:
```
python -m pip install -r requirements.txt
python server.py
```
3. Buka http://localhost:5000 di browser. Layar loading muncul sebentar, lalu ikuti arahan maskot Bima.
4. Cek cepat: jawab soal pertama, ketuk ikon maskot (hint harus menampilkan persentase), lalu lihat tanda bahaya di bawah umpan balik.
5. Di HP (WiFi sama): `http://IP-LAPTOP:5000` (cek IP dengan `ipconfig`), izinkan Python di Private network.
6. Deploy: push folder ke GitHub, lalu render.com > New > Blueprint (langkah lengkap di bagian "Deploy" bawah).

Model di zip ini dilatih dengan scikit-learn 1.8.0. Jika versimu berbeda, server melatih ulang otomatis saat start (beberapa detik).

## Yang baru di game
- Kombo (+2 poin per jawaban benar beruntun, maks +10), pangkat (Satpam Magang sampai Legenda Siber), 12 lencana.
- Setelah menjawab, game menjelaskan tanda bahaya (domain murah, tautan pendek, OTP, batas waktu, dst.) atau tanda aman.
- Profil lucu: tiap akun di game punya avatar hewan, dan pemain mendapat nama + bio acak (mis. "Kucing Anti-Klik") yang bisa diacak ulang dengan 🎲 di tab Task. Profil hanya disimpan di perangkat, tidak dikirim ke server. Avatar akun diatur di `AVATARS` pada `public/data.js`.
- Efek suara (tombol 🔊), konfeti, dialog bergaya mesin ketik, tampilan kartu dan navigasi baru.
- Soal Endless bertambah 14 (total 26 soal tambahan). File `fx.js` berisi semua efek ini.
- Log jawaban punya dua kolom baru: `combo` dan `bonus`. Poin per sesi sedikit lebih tinggi dari versi lama karena bonus kombo.

---

# Panduan EduSecurity (model gaya media sosial)

## Isi folder
- `public/`            : game (index.html, style.css, data.js, game.js, ml-hook.js)
- `server.py`          : melayani game + `/predict` (model) + `/log` (catat jawaban) + `/export`
- `model_medsos.joblib`: model SIAP PAKAI (sudah dilatih), tidak perlu Data_Prep.ipynb lagi untuk menjalankan game
- `fitur.py`           : normalisasi teks + ciri tautan (dipakai training dan server)
- `buat_dataset.py`    : pembuat dataset gaya medsos + data uji dari soal game
- `train_medsos.py`, `Train_Medsos.ipynb` : melatih ulang + evaluasi (notebook ini untuk laporan)
- `data/dataset_medsos.csv`, `data/game_items.csv`, `data/uji_mandiri.csv`, `data/uji_buta.csv`
- `requirements.txt`, `render.yaml` : untuk deploy

## Menjalankan di laptop (Windows, VS Code)
1. File > Open Folder > pilih folder ini.
2. Terminal > New Terminal:
```
python -m pip install -r requirements.txt
python server.py
```
3. Buka http://localhost:5000 . Ketuk ikon maskot: persentase hint berasal dari model baru.
4. HP di WiFi yang sama: buka `http://IP-LAPTOP:5000` (cek IP dengan `ipconfig`).
   Saat Windows bertanya, izinkan Python di Private network.

Kalau muncul error saat memuat `model_medsos.joblib` (biasanya beda versi scikit-learn),
latih ulang di komputer yang sama: `python train_medsos.py`.

## Deploy untuk 40 HP (Render, gratis)
1. Taruh seluruh folder di repo GitHub (termasuk `model_medsos.joblib` dan `data/`).
2. render.com > New > Blueprint > pilih repo. Tunggu build, bagikan link/QR.
3. Server gratis "tidur" saat idle: buka linknya sendiri 5 menit sebelum sesi.
4. Data jawaban bisa hilang saat restart: unduh segera lewat
   `https://NAMA-APP.onrender.com/export?token=ADMIN_TOKEN` (token ada di Render > Environment).

## Melatih ulang / menambah data
- Tambah template di `buat_dataset.py` (daftar `P` untuk phishing, `N` untuk normal), lalu:
```
python buat_dataset.py
python train_medsos.py
```
- Lebih baik lagi: tambahkan contoh NYATA (postingan/DM yang kamu labeli sendiri) ke `data/dataset_medsos.csv`
  dengan kolom `teks,label,kategori,jenis,grup` (grup = nama unik per contoh asli).
- Jika kamu mengubah soal di `public/data.js`, jalankan `python buat_dataset.py` lagi agar data uji ikut diperbarui
  dan contoh latih yang mirip soal baru disaring.

## Hal yang perlu ditulis jujur di laporan (tambahan dari versi lama)
- Dataset dibuat dari template + variasi acak dengan domain rekaan, bukan hasil scraping akun nyata.
- 36 soal game dipakai sebagai data uji (tidak ikut dilatih), jadi angkanya kasar. Lihat tabel di atas untuk angka terbaru.
- Titik lemah: pesan penipuan tanpa tautan (misalnya minta transfer) hanya mengandalkan kata-kata, jadi
  lebih rentan salah. Model memberi persentase perkiraan, bukan kepastian.
- Tab Tweet menyimpan teks ke server; ingatkan anak jangan menulis data pribadi asli.
