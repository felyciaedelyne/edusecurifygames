"""Membangun data/dataset_medsos.csv (contoh postingan & DM gaya media sosial, bahasa Indonesia)
dan data/game_items.csv (soal di game, HANYA untuk pengujian).

Cara kerja: template kalimat + isian acak (nama, merek, nominal, domain palsu, dst.) + "noise"
gaya medsos (singkatan, huruf kecil semua, emoji). Setiap template punya kolom `grup` agar
evaluasi bisa memakai GroupKFold: template yang sama tidak boleh ada di train dan validasi sekaligus.
Semua domain di contoh phishing adalah rekaan.

Jalankan: python buat_dataset.py
"""
import csv
import json
import os
import re
import string
import subprocess
import random

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "data")
os.makedirs(OUT_DIR, exist_ok=True)
rng = random.Random(42)


def slug(n=6):
    return "".join(rng.choices(string.ascii_letters + string.digits, k=n))


# ---------------------------------------------------------------- isian
NAMA = ["Rani", "Dimas", "Sari", "Bayu", "Nina", "Dina", "Fajar", "Putri", "Rizky", "Agus",
        "Citra", "Eko", "Maya", "Hendra", "Wulan", "Andi", "Tika", "Galih"]
APP = ["Instagram", "TikTok", "Facebook", "WhatsApp", "Shopee", "Tokopedia", "Telegram", "X", "Kicau", "Chatku"]
BANK = ["BCA", "BRI", "BNI", "Mandiri", "DANA", "OVO", "GoPay", "ShopeePay", "LinkAja", "Jenius"]
KURIR = ["J&T", "JNE", "SiCepat", "Anteraja", "Pos Indonesia"]
TELCO = ["Telkomsel", "XL", "Indosat", "Tri", "by.U"]
DURASI = ["1 jam", "2 jam", "24 jam", "12 jam", "30 menit", "3 hari", "hari ini", "48 jam"]
NOMINAL = ["500.000", "1.000.000", "250.000", "2.000.000", "750.000", "300.000"]
HADIAH = ["mobil", "motor", "iPhone terbaru", "uang tunai 50 juta", "emas 10 gram", "umroh gratis"]
HP = ["iPhone terbaru", "HP Samsung flagship", "laptop gaming", "PS5", "motor listrik"]
SISA = ["10", "20", "50", "100"]
GAJI = ["15 juta", "5 juta", "3 juta", "8 juta"]
BIAYA = ["Rp50.000", "Rp100.000", "Rp25.000", "Rp75.000"]
UNTUNG = ["10 juta", "25 juta", "5 juta", "100 juta"]
HARI = ["3", "5", "7", "10"]
PCT = ["50", "100", "200"]
LIMIT = ["Rp10 juta", "Rp25 juta", "Rp5 juta", "Rp15 juta"]
DURASI_CAIR = ["5 menit", "15 menit", "hari ini juga", "10 menit"]
KOTA = ["Medan", "Surabaya", "Jakarta", "Bandung", "Makassar", "Batam", "Semarang", "Palembang"]
HARI_ = ["Sabtu", "Minggu", "Senin", "Jumat", "besok", "lusa", "Rabu"]
JAM = ["08.00", "09.30", "13.00", "15.00", "19.00", "10.00", "16.30"]
RUANG = ["B2", "A104", "Lab 3", "C201", "aula", "E301"]
MAKAN = ["bakso", "seblak", "mie ayam", "nasi goreng", "kopi susu", "batagor", "sate", "martabak"]
TEMPAT = ["Dago", "Malioboro", "pantai", "kafe baru itu", "perpus", "mall", "taman kota"]
MATKUL = ["statistika", "basis data", "kalkulus", "jaringan", "manajemen", "bahasa Inggris"]
HAL = ["catatan kuliah", "tugas kelompok", "slide presentasi", "laporan praktikum", "proposal"]
ACARA = ["panitia", "himpunan", "kelas", "BEM", "karang taruna", "ekskul"]
SKILL = ["desain grafis", "Python", "edit video", "public speaking", "fotografi", "Excel"]
LOMBA = ["poster digital", "debat", "coding", "esai", "fotografi", "karya tulis"]
TOKO = ["Kopi Senja", "Toko Buku Kita", "Warung Mama", "Dapur Nusantara", "Sepatu Kita", "Roti Pagi"]
TOPIK = ["keamanan data", "belajar efektif", "literasi digital", "tips magang", "kuliner lokal", "hemat uang saku"]
PENCAPAIAN = ["lulus ujian akhir", "sidang proposal selesai", "tugas besar akhirnya kelar",
              "dapat nilai A di kuis", "selesai magang", "juara lomba antar kelas"]
KEGIATAN = ["nonton bareng", "main futsal", "kerja kelompok di kafe", "camping", "bersih-bersih pantai", "belajar bareng"]
PERUSAHAAN = ["PT Maju Jaya", "CV Sinar Abadi", "PT Nusa Teknologi", "Toko Berkah Mandiri"]
BR = ["kicau", "chatku", "gramin", "insta", "tiktok", "wa", "shopee", "tokped", "dana", "ovo",
      "bca", "bri", "bni", "mandiri", "jnt", "jne", "sicepat", "telkomsel", "xl", "gopay"]
KW = ["verifikasi", "login", "secure", "akun", "klaim", "hadiah", "update", "cek", "bayar",
      "promo", "bantuan", "konfirmasi", "resmi", "aman"]
ORG = ["kampusmaju", "univnusa", "smanegeri5", "pemkotmaju", "politeknikkita", "institutkarya", "smkbina"]
WEB = ["kopisenja", "bukukita", "tokosepatu", "dapur-mama", "travelseru", "blogkuliner",
       "kopi-nusantara", "warungdigital", "belajar-bareng", "komunitas-kode"]


# ---------------------------------------------------------------- tautan
def url_phish():
    r = rng.random()
    brand, kw = rng.choice(BR), rng.choice(KW)
    path = rng.choice(["login", "verif", "claim", "akun", "cek", "form", "daftar", "bayar", ""])
    skema = rng.choices(["http://", "https://"], weights=[6, 4])[0]
    if r < 0.30:
        return f"{rng.choice(['bit.ly', 's.id', 'cutt.ly', 'tinyurl.com', 'rb.gy'])}/{slug(7)}"
    if r < 0.65:
        tld = rng.choice(["xyz", "top", "click", "icu", "site", "online", "buzz", "vip", "info"])
        return f"{skema}{brand}-{kw}{rng.choice(['', '1', '2', '-id', '88'])}.{tld}/{path}".rstrip("/")
    tld = rng.choice(["com", "co.id", "net", "my.id", "info"])
    return f"{skema}{kw}-{brand}.{tld}/{path}".rstrip("/")


def url_apk():
    skema = rng.choice(["http://", "https://"])
    return (f"{skema}{rng.choice(BR)}-{rng.choice(KW)}.{rng.choice(['xyz', 'top', 'site', 'com', 'click'])}"
            f"/{rng.choice(['unduh', 'undangan', 'update', 'tagihan', 'bukti'])}.apk")


def url_official():
    www = rng.choice(["", "www."])
    return (f"https://{www}{rng.choice(ORG)}.{rng.choice(['ac.id', 'go.id', 'sch.id'])}/"
            f"{rng.choice(['seminar', 'pendaftaran', 'jadwal', 'katalog', 'info', 'beasiswa/form', 'pengumuman'])}")


def url_form():
    r = rng.random()
    if r < 0.4:
        return f"https://forms.gle/{slug(10)}"
    if r < 0.8:
        return f"https://bit.ly/{rng.choice(['daftar', 'form', 'info', 'rsvp'])}-{slug(4)}"
    return f"https://s.id/{slug(5)}"


def url_com():
    return (f"https://{rng.choice(['', 'www.'])}{rng.choice(WEB)}.{rng.choice(['com', 'co.id', 'id'])}/"
            f"{rng.choice(['menu', 'artikel', 'blog', 'produk', 'info'])}")


def url_yt():
    return rng.choice([f"https://youtu.be/{slug(11)}", f"https://www.youtube.com/watch?v={slug(11)}"])


LEMBAGA = ["PLN", "BPJS", "Ditjen Pajak", "Samsat", "Dukcapil", "Imigrasi"]
JABATAN = ["Direktur", "Kepala Bagian", "Manajer", "Pimpinan"]
ORTU = ["ibu", "bapak", "mama", "papa", "tante", "om"]
VOUCHER = ["Google Play", "Steam", "Indomaret", "Alfamart", "Tokopedia"]
KRIPTO = ["USDT", "BTC", "token baru", "ETH"]
KNOWN = ["https://www.youtube.com/watch?v=", "https://youtu.be/", "https://github.com/", "https://docs.google.com/document/d/",
         "https://drive.google.com/drive/folders/", "https://id.wikipedia.org/wiki/", "https://www.kompas.com/tekno/read/",
         "https://www.instagram.com/", "https://www.tokopedia.com/", "https://www.detik.com/edu/", "https://medium.com/@"]


def url_known():
    return rng.choice(KNOWN) + slug(rng.randint(6, 11))


def url_brandfake():
    brand, kw = rng.choice(BR), rng.choice(KW)
    tld = rng.choice(["com", "net", "info", "co", "id", "xyz", "top", "online", "site", "click"])
    return rng.choice([f"https://{brand}-{kw}.{tld}/{rng.choice(['verify', 'login', 'form', 'appeal', ''])}".rstrip("/"),
                       f"https://{kw}-{brand}-center.{tld}/{rng.choice(['apply', 'cek', 'akun', ''])}".rstrip("/"),
                       f"http://{brand}{rng.choice(['1', '2', '88', '123'])}.{tld}"])


def url_sub():
    brand = rng.choice(BR)
    return (f"https://{rng.choice(['secure', 'login', 'akun', 'm'])}.{brand}.com.{rng.choice(KW)}-{slug(3).lower()}."
            f"{rng.choice(['xyz', 'top', 'site', 'online'])}/{rng.choice(['login', 'verif', 'cek'])}")


def url_ip():
    return f"http://{rng.randint(11, 223)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}/{rng.choice(['login', 'verif', 'klaim'])}"


SLOTS = {
    "nama": lambda: rng.choice(NAMA), "app": lambda: rng.choice(APP), "bank": lambda: rng.choice(BANK),
    "kurir": lambda: rng.choice(KURIR), "telco": lambda: rng.choice(TELCO), "durasi": lambda: rng.choice(DURASI),
    "nominal": lambda: rng.choice(NOMINAL), "hadiah": lambda: rng.choice(HADIAH), "hp": lambda: rng.choice(HP),
    "sisa": lambda: rng.choice(SISA), "gaji": lambda: rng.choice(GAJI), "biaya": lambda: rng.choice(BIAYA),
    "untung": lambda: rng.choice(UNTUNG), "hari": lambda: rng.choice(HARI), "pct": lambda: rng.choice(PCT),
    "limit": lambda: rng.choice(LIMIT), "durasi_cair": lambda: rng.choice(DURASI_CAIR),
    "kota": lambda: rng.choice(KOTA), "hari_": lambda: rng.choice(HARI_), "jam": lambda: rng.choice(JAM),
    "ruang": lambda: rng.choice(RUANG), "makan": lambda: rng.choice(MAKAN), "tempat": lambda: rng.choice(TEMPAT),
    "matkul": lambda: rng.choice(MATKUL), "hal": lambda: rng.choice(HAL), "acara": lambda: rng.choice(ACARA),
    "skill": lambda: rng.choice(SKILL), "lomba": lambda: rng.choice(LOMBA), "toko": lambda: rng.choice(TOKO),
    "topik": lambda: rng.choice(TOPIK), "pencapaian": lambda: rng.choice(PENCAPAIAN),
    "kegiatan": lambda: rng.choice(KEGIATAN), "perusahaan": lambda: rng.choice(PERUSAHAAN),
    "rek": lambda: "".join(rng.choices(string.digits, k=10)), "no": lambda: str(rng.randint(1000, 9999)),
    "tgl": lambda: str(rng.randint(5, 28)),
    "lembaga": lambda: rng.choice(LEMBAGA), "jabatan": lambda: rng.choice(JABATAN), "ortu": lambda: rng.choice(ORTU),
    "voucher": lambda: rng.choice(VOUCHER), "kripto": lambda: rng.choice(KRIPTO),
    "url_known": url_known, "url_brandfake": url_brandfake, "url_sub": url_sub, "url_ip": url_ip,
    "url": url_phish, "url_apk": url_apk, "url_official": url_official,
    "url_form": url_form, "url_com": url_com, "url_yt": url_yt,
}


def isi(tpl):
    return re.sub(r"\{(\w+)\}", lambda m: SLOTS[m.group(1)](), tpl)


SLANG = [("yang", "yg"), ("tidak", "gak"), ("sudah", "udah"), ("banget", "bgt"), ("tolong", "tlg"),
         ("jangan", "jgn"), ("dengan", "dgn"), ("untuk", "utk"), ("sekarang", "skrg"), ("karena", "krn")]


def noise(t):
    """Noise gaya medsos. Peluangnya SAMA untuk kelas phishing dan normal."""
    if rng.random() < 0.35:
        for a, b in SLANG:
            if rng.random() < 0.6:
                t = re.sub(rf"\b{a}\b", b, t, flags=re.IGNORECASE)
    if rng.random() < 0.25:
        t = t.lower()
    if rng.random() < 0.15:
        t = t.replace("!", "!!") if "!" in t else t + "!!"
    if rng.random() < 0.20:
        t += " " + rng.choice(["🙏", "😊", "🔥", "😱", "👍", "🙌", "😄"])
    if rng.random() < 0.10:                       # typo huruf kecil: hapus satu huruf di kata panjang
        w = t.split(" ")
        i = rng.randrange(len(w))
        if len(w[i]) > 5 and "http" not in w[i]:
            j = rng.randrange(1, len(w[i]) - 1)
            w[i] = w[i][:j] + w[i][j + 1:]
        t = " ".join(w)
    if rng.random() < 0.08:
        t = t.upper() if len(t) < 90 and "http" not in t else t
    return t


# ---------------------------------------------------------------- template PHISHING (label 1)
# (kategori, jenis, template)
P = [
    # akun / verifikasi / centang biru
    ("akun", "post", "Peringatan dari tim {app}: akunmu melanggar aturan komunitas. Ajukan keberatan lewat {url}, batas waktu {durasi}"),
    ("akun", "dm", "Sistem kami menemukan aktivitas aneh di akun {app} kamu. Masuk lewat {url} dalam {durasi} untuk memulihkan akses"),
    ("akun", "dm", "Ada yang mencoba masuk ke akun {app}-mu dari {kota}. Kalau itu bukan kamu, amankan sekarang: {url}"),
    ("akun", "post", "Selamat, akunmu terpilih mendapat centang biru {app}! Ajukan di {url} sebelum kuota habis"),
    ("akun", "post", "Konten kamu dilaporkan karena pelanggaran hak cipta. Ajukan banding maksimal {durasi} lewat {url} atau akun dihapus permanen"),
    ("akun", "dm", "Halo, saya petugas {app}. Akunmu kena laporan massal, mohon konfirmasi kata sandi di {url} agar tidak diblokir"),
    # hadiah / giveaway / undian
    ("hadiah", "post", "Cuma hari ini! Kamu dapat saldo {bank} Rp{nominal} gratis 🎁 Ambil di {url}, tinggal login pakai akunmu"),
    ("hadiah", "post", "Bagi-bagi {hp} gratis buat {sisa} followers pertama. Daftar dan login akun {app} lewat {url}"),
    ("hadiah", "dm", "Pengumuman undian {telco} periode ini: kamu menang {hadiah}. Pencairan lewat {url}, siapkan KTP dan kode OTP"),
    ("hadiah", "dm", "Kamu terpilih jadi pemenang {hadiah}! Isi data diri dan kode verifikasi di {url} paling lambat {durasi}"),
    ("hadiah", "post", "Voucher belanja Rp{nominal} dari {app} untuk {sisa} orang tercepat. Klaim: {url} (wajib login)"),
    # lowongan / kerja
    ("kerja", "post", "Dicari admin online, kerja dari rumah gaji {gaji} per minggu tanpa pengalaman. Daftar di {url}, isi NIK dan nomor rekening"),
    ("kerja", "post", "Part time cuma like dan subscribe, bayaran {gaji}/bulan! Chat {url}, tapi transfer biaya admin {biaya} dulu ya"),
    ("kerja", "post", "Butuh reseller dropship, modal {biaya} untung jutaan. Gabung di {url} sekarang juga"),
    ("kerja", "post", "Rekrutmen {perusahaan} tahun ini lolos tanpa tes. Kirim data lengkap dan foto KTP ke {url}"),
    # minta OTP / kode (tanpa link)
    ("otp", "dm", "Eh {nama}, tolong dong kirimin kode yang barusan masuk ke SMS kamu, nomorku salah daftar. Cepetan ya penting"),
    ("otp", "dm", "Hai ini {nama}, aku mau login tapi kodenya kekirim ke nomormu. Sebutin 6 digit kodenya ya sekarang"),
    ("otp", "dm", "Kak, kode verifikasi {app} tadi salah kirim ke nomor kakak. Boleh minta kirim kodenya? Ini darurat"),
    ("otp", "dm", "Selamat siang, saya dari tim keamanan {bank}. Mohon sebutkan PIN dan kode OTP untuk memastikan akun Anda aman"),
    ("otp", "dm", "Bro cepet kirim kode yang masuk ke hp lu, buat daftar ulang akunku, 5 menit lagi hangus"),
    # kurir / paket
    ("kurir", "dm", "Paket {kurir} atas nama kamu tertahan di gudang. Bayar biaya {biaya} di {url} dan isi data kartu untuk dikirim ulang"),
    ("kurir", "dm", "Alamat paket tidak lengkap. Perbarui data dalam {durasi} di {url} atau paket dikembalikan ke pengirim"),
    ("kurir", "dm", "Paketmu tidak bisa dikirim. Konfirmasi lewat {url} dengan login akun {bank} supaya dijadwalkan ulang"),
    # bank / e-wallet
    ("bank", "dm", "Rekening {bank} milikmu dibekukan sementara. Masukkan PIN dan OTP di {url} agar bisa aktif lagi"),
    ("bank", "dm", "Info {bank}: ada transaksi mencurigakan Rp{nominal}. Kalau bukan kamu, batalkan di {url} sekarang"),
    ("bank", "dm", "Biaya admin {bank} naik jadi Rp150.000 per bulan. Untuk tetap di tarif lama, ubah data di {url} sebelum {durasi}"),
    ("bank", "dm", "Limit kartu kredit kamu naik! Aktifkan lewat {url} dengan nomor kartu dan CVV"),
    # investasi
    ("investasi", "post", "Gabung grup trading kami, modal {biaya} bisa jadi {untung} dalam {hari} hari. Profit dijamin, daftar di {url}"),
    ("investasi", "post", "Robot trading anti rugi, member kami sudah cuan {untung}. Deposit awal {biaya}, tarik kapan saja 👉 {url}"),
    ("investasi", "post", "Info kripto pasti untung, bonus deposit {pct}%. Buruan sebelum slot penuh: {url}"),
    # pinjol
    ("pinjol", "post", "Butuh dana cepat? Pinjaman {limit} cair {durasi_cair} tanpa jaminan, tanpa survei. Ajukan di {url}"),
    ("pinjol", "dm", "Pinjaman bunga 0 persen, syarat cuma KTP. Transfer biaya asuransi {biaya} dulu, dana langsung cair. Klik {url}"),
    ("pinjol", "dm", "Kamu terpilih dapat limit pinjaman {limit}. Aktifkan lewat {url} sebelum {durasi} berakhir"),
    # bantuan / beasiswa
    ("bansos", "post", "Bantuan pemerintah Rp{nominal} untuk pelajar sudah cair. Cek namamu dan isi data di {url}"),
    ("bansos", "post", "Beasiswa penuh tanpa tes untuk {sisa} pendaftar pertama! Isi data lengkap dan foto KTP di {url}"),
    ("bansos", "dm", "Subsidi kuota gratis dari kementerian. Aktifkan di {url} dengan nomor HP dan kode verifikasi"),
    # akun teman diretas
    ("teman", "dm", "Hai {nama}, ini aku. HP-ku lagi rusak, bisa pinjam {biaya} dulu transfer ke rekening {rek}? Besok kuganti"),
    ("teman", "dm", "{nama} tolong isiin pulsa {biaya} dulu, aku darurat di jalan. Nanti kuganti, jangan bilang siapa-siapa ya"),
    ("teman", "dm", "Eh ada fotomu nih 😱 lihat di {url}, login dulu ya biar kebuka"),
    ("teman", "dm", "Ini {nama}, ada videomu viral banget loh, cek di {url}"),
    # apk berbahaya
    ("apk", "dm", "Undangan pernikahan digital kami 💌 unduh aplikasinya di {url_apk}"),
    ("apk", "post", "Pembaruan {app} wajib! Pasang versi terbaru dari {url_apk} supaya akun tetap bisa dipakai"),
    ("apk", "dm", "Cek tagihan {telco} kamu lewat aplikasi ini: {url_apk}"),
    ("apk", "dm", "Bukti transfer sudah saya kirim, silakan lihat lampiran di {url_apk}"),
]

P += [
    ("akun", "dm", "Notifikasi {app}: pendaftaran ulang akun wajib dilakukan sebelum {durasi}. Unggah verifikasi lewat {url}"),
    ("akun", "post", "Kami mendeteksi pelanggaran hak cipta pada kontenmu. Isi formulir banding di {url_brandfake} atau channel ditutup"),
    ("akun", "dm", "{app} Security: sandi akunmu hampir kedaluwarsa. Atur ulang sekarang di {url_sub}"),
    ("akun", "dm", "Halo, akun {app} kamu dilaporkan spam. Balas pesan ini dengan username dan sandi supaya kami bisa memeriksa"),
    ("akun", "dm", "Akun {app}mu ditandai bermasalah. Pulihkan lewat {url_ip} dalam {durasi}"),
    ("lembaga", "dm", "{lembaga}: terdapat tunggakan atas nama Anda. Selesaikan dalam {durasi} lewat {url} atau layanan dihentikan"),
    ("lembaga", "dm", "Pemberitahuan {lembaga}: data Anda perlu diperbarui. Masukkan NIK dan nomor kartu di {url_brandfake}"),
    ("lembaga", "dm", "{lembaga} mengingatkan: bayar denda Rp{nominal} hari ini lewat transfer langsung agar tidak diproses hukum"),
    ("lembaga", "dm", "Selamat siang, saya petugas {lembaga}. Mohon sebutkan nomor rekening dan kode yang masuk ke HP Anda"),
    ("lembaga", "dm", "Anda terlibat kasus hukum. Untuk menyelesaikannya, transfer uang jaminan Rp{nominal} ke rekening {rek} hari ini"),
    ("penyamaran", "dm", "Pak, saya {jabatan} Anda. Tolong segera belikan voucher {voucher} Rp{nominal}, kirim kodenya ke saya. Jangan hubungi lewat telepon"),
    ("penyamaran", "dm", "Nak, {ortu} lagi di rumah sakit, tolong transfer Rp{nominal} ke rekening {rek} sekarang ya. Nanti diganti, jangan bilang yang lain"),
    ("penyamaran", "dm", "{nama}, tolong isiin saldo {bank} {biaya} dulu ya, hp lagi bermasalah, nanti kuganti"),
    ("jualbeli", "dm", "Pembeli: dana sudah saya kirim ya. Cek bukti dan konfirmasi pakai login {bank} lewat {url}"),
    ("jualbeli", "dm", "Barang di {app} masih ada? Saya mau bayar sekarang, klik {url_sub} untuk menerima pembayaran"),
    ("jualbeli", "dm", "Pembayaran Anda tertunda. Masukkan PIN {bank} di {url} untuk menerima dana"),
    ("kripto", "post", "AIRDROP {kripto} gratis untuk {sisa} wallet pertama! Hubungkan wallet kamu di {url}"),
    ("kripto", "post", "Mining {kripto} tanpa modal, penarikan dijamin tiap hari. Deposit {biaya} untuk aktivasi, daftar {url}"),
    ("followers", "post", "Mau followers {app} gratis? Masukkan username dan sandi akunmu di {url_brandfake}"),
    ("followers", "post", "Naikkan followers {app} {sisa} ribu dalam {durasi}, cukup login pakai akunmu di {url}"),
    ("kerja", "post", "Lowongan {perusahaan} lolos tanpa tes, bayar {biaya} untuk seragam dan pelatihan, hubungi nomor ini"),
    ("kerja", "post", "Dibutuhkan tenaga admin dari rumah, gaji {gaji}/minggu. Setor deposit {biaya} dulu untuk aktivasi akun kerja"),
    ("bank", "dm", "Kartu {bank} Anda akan diblokir. Perbarui data kartu dan CVV di {url_brandfake}"),
    ("bank", "dm", "Kami dari tim keamanan {bank}. Terdeteksi login mencurigakan. Balas dengan PIN dan OTP Anda untuk pemblokiran otomatis"),
    ("teman", "dm", "Ada yang upload fotomu di grup 😳 cek sebelum disebar: {url}, login dulu"),
    ("apk", "dm", "Tiket konser kamu sudah terbit. Unduh dan aktivasi lewat {url_apk}"),
    ("hadiah", "post", "Scan barcode ini untuk klaim hadiah {bank} Rp{nominal}, masukkan PIN untuk pencairan, berlaku {durasi}"),
    ("hadiah", "dm", "Pemenang undian {app} periode ini adalah kamu! Hubungi admin dan siapkan KTP serta nomor rekening untuk pencairan"),
    ("otp", "dm", "Kak maaf, tadi salah kirim 6 digit kode ke nomor kakak. Tolong dikirim balik ya, urgent"),
    ("otp", "dm", "Halo, saya dari {app}. Untuk menghindari penutupan akun, kirimkan kode verifikasi yang baru kamu terima"),
    ("otp", "dm", "Tim {bank} di sini. Kami perlu OTP yang baru masuk untuk membatalkan transaksi mencurigakan"),
    ("otp", "dm", "Boleh minta screenshot kode yang dikirim {app} ke HP kamu? Aku lupa sandi dan nomorku mati"),
    ("investasi", "dm", "Admin grup: untuk gabung VIP transfer {biaya} dulu, profit dijamin {pct}% per hari, uang kembali kalau rugi"),
    ("investasi", "post", "Modal {biaya} jadi {untung} dalam {hari} hari, member kami sudah ribuan. Daftar sekarang {url_brandfake}, slot terbatas!!"),
    ("kurir", "dm", "Kurir {kurir}: paket gagal diantar karena alamat salah. Isi ulang alamat dan bayar ongkir {biaya} di {url_brandfake}"),
]

# ---------------------------------------------------------------- template NORMAL (label 0)
N = [
    # obrolan teman
    ("obrolan", "dm", "Eh {nama}, tugas {hal} udah kamu kumpul belum? Batasnya {hari_} jam {jam} ya 🙏"),
    ("obrolan", "dm", "Makasih ya udah bantuin {hal} kemarin! Nanti aku traktir {makan} hari {hari_}"),
    ("obrolan", "dm", "Besok jadi ke {tempat}? Aku jemput jam {jam} ya, jangan telat"),
    ("obrolan", "dm", "Aku telat dikit ya, macet banget di {kota}. Mulai duluan aja nggak apa-apa"),
    ("obrolan", "dm", "Kamu udah makan belum? Ada {makan} enak nih di depan kampus, mau titip?"),
    ("obrolan", "dm", "Boleh minta tolong fotoin catatan {matkul} kemarin? Aku nggak masuk, nanti kuganti traktir kopi"),
    ("obrolan", "dm", "Selamat ulang tahun {nama}! Semoga sehat terus dan makin sukses 🎉"),
    ("obrolan", "dm", "Rapat {acara} dipindah ke {hari_} jam {jam}, ruang {ruang}. Tolong dikonfirmasi ya"),
    ("obrolan", "dm", "Paketmu udah sampai ya, kuletakkan di depan pintu. Cek dulu isinya 😊"),
    ("obrolan", "dm", "Udah kutransfer yang kemarin ya, tolong dicek di m-banking kamu"),
    ("obrolan", "dm", "Patungan {acara} masing-masing 25 ribu ya, kasih ke {nama} langsung pas ketemu"),
    # postingan pribadi
    ("pribadi", "post", "Baru nyobain {makan} langganan anak kampus, rasanya juara banget 😋 besok ke sini lagi"),
    ("pribadi", "post", "Alhamdulillah {pencapaian}! Terima kasih buat semua yang sudah mendoakan 🙏"),
    ("pribadi", "post", "Hujan deras lagi di {kota}, jadi pengen {makan} anget"),
    ("pribadi", "post", "Weekend ini mau {kegiatan} bareng temen-temen. Ada yang mau ikut?"),
    ("pribadi", "post", "Lagi belajar {skill}, ada yang punya rekomendasi tutorial yang enak diikuti?"),
    ("pribadi", "post", "Sore ini langit di {tempat} bagus banget, sayang kalau nggak difoto 📸"),
    ("pribadi", "post", "Capek banget minggu ini, tapi {pencapaian}. Worth it sih"),
    # info resmi dengan tautan
    ("info", "post", "Seminar {topik} gratis hari {hari_}, pukul {jam} WIB. Info dan pendaftaran: {url_official}"),
    ("info", "post", "Perpustakaan buka sampai pukul {jam} selama minggu ujian. Katalog daring: {url_official}"),
    ("info", "post", "Jadwal ujian semester sudah terbit, cek di {url_official}"),
    ("info", "post", "Pendaftaran lomba {lomba} dibuka sampai {hari_}. Formulir: {url_form}"),
    ("info", "post", "Meetup komunitas {skill} {hari_} depan, daftar lewat {url_form}. Gratis dan terbuka untuk pemula"),
    ("info", "post", "Menu baru {toko} sudah tersedia! Lihat daftar lengkapnya di {url_com}"),
    ("info", "dm", "Video tutorial {skill} yang aku ceritain kemarin: {url_yt}"),
    ("info", "dm", "Artikel menarik soal {topik} nih, coba baca: {url_com}"),
    ("info", "post", "Lowongan magang desain di kampus, kirim portofolio lewat {url_official}. Tidak dipungut biaya apa pun"),
    ("info", "post", "Giveaway buku untuk 3 pemenang! Cukup follow akun ini, like postingan, dan tag 2 temanmu. Pemenang diumumkan {hari_}. Tanpa biaya"),
    # toko / layanan resmi
    ("layanan", "dm", "Pesanan #{no} sudah kami kirim. Lacak lewat menu Pesanan di aplikasi resmi {toko}. Terima kasih sudah berbelanja!"),
    ("layanan", "dm", "Pesananmu sudah kami terima dan sedang diproses, estimasi tiba {hari_}. Terima kasih 🙏"),
    ("layanan", "dm", "Ada login ke akunmu dari perangkat baru. Kalau itu kamu, abaikan saja. Kalau bukan, ganti sandi lewat menu Pengaturan di aplikasi"),
    ("layanan", "dm", "Pengingat: tagihan listrik jatuh tempo tanggal {tgl}. Bayar lewat aplikasi resmi atau loket terdekat"),
    ("layanan", "post", "Info: layanan {bank} maintenance {hari_} pukul {jam}. Transaksi normal kembali setelahnya, detail ada di aplikasi"),
    # edukasi keamanan (kata OTP/PIN muncul tapi justru melarang)
    ("edukasi", "post", "Ingat ya, jangan pernah bagikan kode OTP ke siapa pun, termasuk yang ngaku dari {bank}!"),
    ("edukasi", "post", "Waspada penipuan! Pesan yang meminta PIN atau kata sandi pasti palsu. Laporkan lalu blokir akunnya"),
    ("edukasi", "post", "Tips aman online: periksa dulu tautannya sebelum diklik, dan jangan login lewat link yang nggak jelas"),
    ("edukasi", "post", "Hati-hati phishing! Kalau ada yang minta kode verifikasi, jangan dikasih. Share ke teman-temanmu juga ya"),
    ("edukasi", "post", "Tadi ada yang kirim pesan minta OTP ke aku, untung nggak kuladeni. Kalian hati-hati ya"),
]

N += [
    ("tautan", "dm", "Tutorial {skill} yang aku ceritain: {url_known}"),
    ("tautan", "dm", "Materi minggu ini sudah kuunggah di {url_known}, silakan diunduh"),
    ("tautan", "post", "Artikel bagus soal {topik}, layak dibaca: {url_known}"),
    ("tautan", "dm", "Dokumen absensi kelas: {url_known}. Isi nama sebelum {hari_} ya"),
    ("tautan", "post", "Repo proyek {skill} kami ada di {url_known}, boleh dicek dan dikasih masukan"),
    ("tautan", "post", "Cek profil komunitas kami: {url_known}. Gratis dan terbuka untuk semua"),
    ("otpresmi", "dm", "Kode OTP Anda adalah {no}{no}. Jangan berikan kode ini kepada siapa pun, termasuk pihak yang mengaku dari {app}."),
    ("otpresmi", "dm", "Kode verifikasi {app} kamu: {no}. Berlaku 5 menit, rahasiakan dari siapa pun."),
    ("otpresmi", "dm", "{no} adalah kode masuk {app}-mu. Jangan bagikan ke orang lain."),
    ("edukasi", "post", "Ingat, {bank} tidak pernah meminta PIN atau OTP lewat chat. Kalau ada yang meminta, laporkan"),
    ("edukasi", "post", "Hati-hati penipuan mengatasnamakan {kurir}. Jangan klik tautan dari nomor asing dan jangan kasih kode apa pun"),
    ("edukasi", "post", "Thread: tips mengamankan akun {app}, aktifkan verifikasi dua langkah dan jangan pakai sandi yang sama"),
    ("edukasi", "post", "Kalau ada yang minta kode verifikasi lewat chat, itu penipu. Laporkan ke {app} ya teman-teman"),
    ("edukasi", "post", "Transaksi resmi {lembaga} tidak pernah meminta transfer ke rekening pribadi. Waspada penipuan!"),
    ("edukasi", "post", "Kemarin ada yang nyamar jadi {ortu}ku minta transfer, untung langsung kutelepon dulu. Kalian hati-hati ya"),
    ("obrolan", "dm", "Boleh minta tolong kirim link zoom-nya? Aku belum dapat undangan rapat {acara}"),
    ("obrolan", "dm", "Tolong pinjemin charger dong, hp-ku mau mati"),
    ("obrolan", "dm", "Aku udah transfer uang patungan {hari_} ya, tolong dicek di mutasi"),
    ("obrolan", "dm", "Selamat {nama}, kamu {pencapaian}! Traktiran dong 😄"),
    ("obrolan", "dm", "Foto {kegiatan} kemarin udah kukirim lewat grup kelas ya, bagus-bagus hasilnya"),
    ("obrolan", "post", "Dompetku ketinggalan di {tempat}, ada yang lihat? Warnanya hitam"),
    ("obrolan", "dm", "Nanti malam {kegiatan} yuk, jam {jam} ya"),
    ("obrolan", "dm", "Kamu udah isi formulir {acara}? Batasnya {hari_} ya"),
    ("obrolan", "dm", "Eh kode kelas {matkul} yang di e-learning apa ya? Aku lupa catat"),
    ("obrolan", "dm", "Ibu lagi masak {makan} nih, nanti mampir ya. Bawa tugasnya sekalian"),
    ("layanan", "dm", "Pesanan #{no} sudah dikemas dan diserahkan ke kurir {kurir}. Lacak lewat menu Pesanan di aplikasi resmi"),
    ("layanan", "post", "Diskon akhir bulan di {toko}, semua item sampai 30%. Datang langsung ke gerai kami"),
    ("layanan", "dm", "Pengingat: tagihan internet jatuh tempo tanggal {tgl}. Bayar lewat aplikasi resmi atau minimarket terdekat"),
    ("layanan", "dm", "Kurir akan tiba sekitar jam {jam}. Siapkan uang pas kalau COD ya"),
    ("info", "post", "Info vaksin gratis di puskesmas, bawa KTP asli. Pendaftaran langsung di tempat"),
    ("info", "post", "Webinar {topik} gratis {hari_} jam {jam} WIB, tautan zoom dikirim ke email setelah daftar di situs resmi panitia"),
    ("info", "post", "Kuliah {matkul} {hari_} diganti tugas mandiri, detail ada di e-learning kampus"),
    ("info", "dm", "Rapat {acara} ditunda ke {hari_} pukul {jam}, mohon konfirmasi kehadiran"),
    ("info", "post", "Open recruitment {acara} dibuka sampai {hari_}, daftar via formulir: {url_form}. Gratis"),
    ("info", "post", "Bazar kampus {hari_} ini, banyak {makan} dan thrift murah. Gratis masuk, ayo datang!"),
    ("info", "post", "Giveaway {hal} nih! Syaratnya gampang: follow, repost, dan mention satu teman. Tidak ada biaya apa pun, pemenang kami umumkan {hari_}"),
    ("info", "post", "Bagi-bagi merchandise komunitas {skill} buat 5 orang yang komen jawaban kuis. Gratis, tanpa data pribadi, diumumkan {hari_}"),
    ("pribadi", "post", "Lagi cari teman buat ikut lomba {lomba} bulan depan, ada yang minat? Skill {skill} boleh"),
    ("pribadi", "post", "Baru selesai lari pagi, badan pegel tapi segar. Habis ini {makan} dulu 🏃"),
]

# ---------------------------------------------------------------- hasilkan
N_PHISH, N_NORMAL = 7, 8


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / max(len(a | b), 1)


def toks(t):
    return re.findall(r"[a-z0-9]+", re.sub(r"https?://\S+", " ", t.lower()))


def muat_game():
    """Ambil POSTS, MSGS, ENDLESS dari public/data.js lewat node."""
    js = os.path.join(BASE, "public", "data.js")
    kode = ("const vm=require('vm'),fs=require('fs');const c={};vm.createContext(c);"
            "vm.runInContext(fs.readFileSync(process.argv[1],'utf8')+';globalThis.out={POSTS,MSGS,ENDLESS}',c);"
            "console.log(JSON.stringify(c.out))")
    hasil = subprocess.run(["node", "-e", kode, js], capture_output=True, text=True, check=True)
    d = json.loads(hasil.stdout)
    rows = []
    for sumber, key in (("utama-post", "POSTS"), ("utama-pesan", "MSGS"), ("endless", "ENDLESS")):
        for i, it in enumerate(d[key]):
            rows.append({"id": it.get("id", f"e{i + 1}"), "teks": it["text"],
                         "label": int(it["phishing"]), "sumber": sumber})
    return rows


game = muat_game()
game_tok = [toks(g["teks"]) for g in game]

rows, seen, dibuang = [], set(), 0
for label, daftar, n_per in ((1, P, N_PHISH), (0, N, N_NORMAL)):
    for ti, (kat, jenis, tpl) in enumerate(daftar):
        grup = f"{'P' if label else 'N'}-{kat}-{ti}"
        n = tries = 0
        while n < n_per and tries < 80:
            tries += 1
            teks = noise(isi(tpl))
            kunci = re.sub(r"\W+", "", teks.lower())
            if kunci in seen:
                continue
            if any(jaccard(toks(teks), gt) >= 0.6 for gt in game_tok):  # jangan mirip soal game
                dibuang += 1
                continue
            seen.add(kunci)
            rows.append({"teks": teks, "label": label, "kategori": kat, "jenis": jenis, "grup": grup})
            n += 1

rng.shuffle(rows)
with open(os.path.join(OUT_DIR, "dataset_medsos.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["teks", "label", "kategori", "jenis", "grup"])
    w.writeheader()
    w.writerows(rows)
with open(os.path.join(OUT_DIR, "game_items.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "teks", "label", "sumber"])
    w.writeheader()
    w.writerows(game)

n1 = sum(r["label"] for r in rows)
print(f"dataset_medsos.csv: {len(rows)} baris (phishing {n1}, normal {len(rows) - n1}), "
      f"{len({r['grup'] for r in rows})} template")
print(f"dibuang karena terlalu mirip soal game: {dibuang}")
print(f"game_items.csv: {len(game)} soal (hanya untuk uji)")
