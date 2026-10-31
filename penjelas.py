"""Penjelasan prediksi: sinyal apa yang paling menaikkan / menurunkan skor phishing.

Model memakai Logistic Regression di atas TF-IDF, sehingga sumbangan tiap fitur bisa dihitung langsung
(nilai TF-IDF x koefisien). Token ciri buatan (z...) diterjemahkan ke bahasa yang mudah dipahami anak-anak.
"""
import numpy as np

from fitur import normalisasi

# token ciri -> (ikon, judul, penjelasan singkat)
ZLABEL = {
    "zshort": ("🔗", "Tautan dipendekkan", "Tujuan asli tautan disembunyikan."),
    "ztldmurah": ("🌐", "Akhiran domain murah", "Domain seperti .xyz/.top sering dipakai situs penipuan."),
    "ztldresmi": ("🏛️", "Domain lembaga resmi", "Akhiran .ac.id/.go.id hanya untuk lembaga terdaftar."),
    "zumum": ("✅", "Situs umum yang dikenal", "Domain milik layanan besar (mis. YouTube, GitHub, Google)."),
    "zhyphen": ("🎭", "Domain dirangkai tanda hubung", "Pola umum domain tiruan, mis. nama-merek-verifikasi."),
    "zhyphen2": ("🎭", "Domain bertanda hubung berlapis", "Makin banyak tanda hubung, makin mirip domain tiruan."),
    "zkwhost": ("🔑", "Kata pancingan di domain", "Kata login/verifikasi/klaim/hadiah di nama domain."),
    "zkwpath": ("🔑", "Kata pancingan di alamat tautan", "Mis. /login atau /verif di ujung tautan."),
    "zapk": ("📦", "Mengajak mengunduh .apk", "Aplikasi di luar toko resmi bisa berisi virus."),
    "zhttp": ("🔓", "Tanpa HTTPS", "Situs login resmi hampir selalu memakai https."),
    "zhttps": ("🔒", "Memakai HTTPS", "HTTPS saja tidak menjamin aman, tetapi lebih baik daripada http."),
    "zbrandpalsu": ("🪞", "Meniru nama merek", "Nama merek terkenal ada di domain yang bukan milik merek itu."),
    "zsubdomain": ("🧩", "Subdomain menumpuk", "Alamat panjang berlapis untuk mengecoh mata."),
    "zipHost": ("🧭", "Alamat berupa angka IP", "Situs resmi jarang memakai alamat angka."),
    "zpunycode": ("🔤", "Huruf domain menyamar", "Karakter mirip huruf biasa untuk memalsukan nama."),
    "zat": ("📧", "Tanda @ di dalam tautan", "Trik untuk menyembunyikan tujuan sebenarnya."),
    "zpanjang": ("📏", "Tautan sangat panjang", "Tautan panjang sering menyembunyikan alamat asli."),
    "zdigithost": ("🔢", "Angka di nama domain", "Sering muncul pada domain tiruan, mis. bri88."),
    "ztanpalink": ("💬", "Tanpa tautan", "Tidak ada tautan; risiko ada pada isi permintaannya."),
    "zc_rahasia": ("🔑", "Menyebut data rahasia", "OTP, PIN, sandi, atau kode verifikasi disebut dalam pesan."),
    "zc_pribadi": ("🪪", "Menyebut data pribadi", "KTP/NIK/rekening/selfie dipakai untuk menipu atas namamu."),
    "zc_tekanan": ("⏰", "Menekan dengan waktu", "Batas waktu dibuat sempit supaya kamu panik."),
    "zc_ancam": ("😨", "Mengancam kerugian", "Akun/rekening diblokir, denda, atau dihapus bila tidak menurut."),
    "zc_hadiah": ("🎁", "Penawaran terlalu bagus", "Hadiah, bonus, atau untung pasti yang datang tiba-tiba."),
    "zc_bayardulu": ("💸", "Meminta uang di muka", "Transfer/biaya diminta lebih dulu sebelum sesuatu 'cair'."),
    "zc_otoritas": ("🎭", "Mengaku pihak resmi", "Mengaku petugas/CS/pimpinan untuk membuatmu percaya."),
    "zc_rahasiakan": ("🤫", "Minta dirahasiakan", "Penipu sering melarangmu memberi tahu orang lain."),
    "zc_klik": ("👆", "Mengajak klik/unduh/login", "Ajakan bertindak lewat tautan atau aplikasi."),
    "zc_edukasi": ("📚", "Nada mengingatkan/edukasi", "Pesan justru melarang membagikan data atau mengajak waspada."),
    "zc_resmiapp": ("📱", "Mengarah ke jalur resmi", "Mengarahkan ke aplikasi, situs resmi, atau loket."),
    "zc_akrab": ("🙂", "Obrolan sehari-hari", "Bahasa akrab tentang kegiatan biasa."),
    "zkombo_mintarahasia": ("🚨", "Meminta data rahasia", "Ada permintaan kode/PIN/sandi tanpa konteks peringatan."),
    "zkombo_rahasia_tekanan": ("🚨", "Data rahasia + tekanan", "Minta kode sambil mendesak: pola klasik penipuan OTP."),
    "zkombo_edukasi_rahasia": ("🛡️", "Menyebut OTP untuk melarang", "Kata OTP dipakai untuk mengingatkan agar tidak dibagikan."),
    "zkombo_hadiah_biaya": ("🚨", "Hadiah + syarat bayar/data", "Hadiah yang meminta biaya, data pribadi, atau klik."),
    "zkombo_pribadi_desak": ("🚨", "Data pribadi + desakan", "Meminta data pribadi sambil menekan atau mengajak klik."),
    "zkombo_uang_rahasia": ("🚨", "Minta uang + dirahasiakan", "Permintaan uang yang disuruh dirahasiakan."),
    "zkombo_otoritas_minta": ("🚨", "Pihak 'resmi' meminta data/uang", "Instansi asli tidak meminta ini lewat pesan."),
    "zkombo_wajar": ("🙂", "Konteks wajar", "Isi pesan sehari-hari tanpa permintaan berisiko."),
    "zrisiko3": ("🚨", "Banyak ciri berisiko sekaligus", "Beberapa tanda bahaya muncul bersamaan."),
    "zrisiko4": ("🚨", "Sangat banyak ciri berisiko", "Hampir semua tanda bahaya muncul bersamaan."),
}
STOP = {"anda", "ini", "itu", "yang", "dan", "di", "ke", "ya", "kamu", "kak", "aku", "saya", "untuk", "dari", "pun", "siapa",
        "siapa pun", "dengan", "atau", "akan", "ada", "sudah", "udah", "kita", "nya", "juga", "dong", "nih", "deh", "banget",
        "yg", "gak", "tidak", "bisa", "mau", "lagi", "kalau", "jika", "agar", "supaya", "pada", "oleh", "bagi"}
ABAIKAN = {"zurl", "zkode", "znomor", "zrupiah", "zseru", "zbanyaklink", "ztldbiasa", "zrisiko0", "zrisiko1", "zrisiko2"}


def tingkat(p):
    return "tinggi" if p >= 0.7 else "sedang" if p >= 0.4 else "rendah"


def jelaskan(model, teks, n_naik=4, n_turun=3, ambang=0.12):
    """Kembalikan (prob_phishing, daftar sinyal). Aman dipanggil untuk satu teks."""
    prob = float(model.predict_proba([teks])[0][1])
    try:
        tfidf = model.named_steps["tfidf"]
        clf = model.named_steps["clf"]
        x = tfidf.transform([normalisasi(teks)]).tocoo()
        nama = tfidf.get_feature_names_out()
        sumbang = {}
        for j, v in zip(x.col, x.data):
            n = nama[j]
            if not n.startswith("kata__"):
                continue                       # n-gram huruf tidak mudah dibaca manusia
            sumbang[n[6:]] = float(v * clf.coef_[0][j])
        sinyal = []
        # sinyal berlabel jelas (ciri tautan/isi) ditampilkan lebih dulu daripada kata biasa
        for kata, w in sorted(sumbang.items(), key=lambda kv: (kv[0] not in ZLABEL, -abs(kv[1]))):
            if abs(w) < ambang or kata in ABAIKAN:
                continue
            if not kata.startswith("z") and (set(kata.split()) <= STOP or abs(w) < 0.2):
                continue                       # kata umum / lemah: bikin penjelasan membingungkan
            if kata in ZLABEL:
                ik, jd, ket = ZLABEL[kata]
            elif kata.startswith("z"):
                continue
            else:
                ik, jd, ket = ("🔤", f"Kata “{kata}”", "Kata/frasa ini sering muncul pada pesan " + ("phishing." if w > 0 else "biasa."))
            sinyal.append({"ikon": ik, "judul": jd, "ket": ket, "arah": "naik" if w > 0 else "turun", "bobot": round(w, 2)})
        naik = [s for s in sinyal if s["arah"] == "naik"][:n_naik]
        turun = [s for s in sinyal if s["arah"] == "turun"][:n_turun]
        return prob, naik + turun
    except Exception:  # penjelasan tidak boleh menggagalkan prediksi
        return prob, []
