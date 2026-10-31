"""EduSecurity server: melayani game (folder public/) + API model phishing.

Jalankan lokal : python server.py
Produksi       : gunicorn server:app --workers 2 --threads 4 --timeout 60

Model: model_medsos.joblib. Jika file itu tidak bisa dimuat ATAU dilatih dengan versi scikit-learn yang
berbeda dari yang terpasang, server otomatis melatih ulang dari data/ saat start (beberapa detik),
sehingga game tidak pernah mati hanya karena beda versi.
"""
import json
import os
import threading
from datetime import datetime, timezone

import joblib
import sklearn
from flask import Flask, jsonify, request, send_from_directory

import fitur  # noqa: F401  (dibutuhkan saat memuat model: normalisasi_batch ada di fitur.py)
from penjelas import jelaskan, tingkat

BASE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(BASE, "public")
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE, "data"))
LOG_FILE = os.path.join(DATA_DIR, "records.jsonl")
MODEL_FILE = os.path.join(BASE, "model_medsos.joblib")
META_FILE = os.path.join(BASE, "model_meta.json")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")  # isi di hosting agar /export aman
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__, static_folder=PUBLIC, static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # batasi ukuran request


def _baca_meta():
    try:
        with open(META_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def muat_model():
    """Muat model; latih ulang otomatis bila rusak / beda versi scikit-learn."""
    meta = _baca_meta()
    if os.path.exists(MODEL_FILE) and meta.get("sklearn") == sklearn.__version__:
        try:
            return joblib.load(MODEL_FILE)
        except Exception as e:  # noqa: BLE001
            print("Gagal memuat model, melatih ulang:", e)
    else:
        print(f"Versi scikit-learn berbeda (model: {meta.get('sklearn')}, terpasang: {sklearn.__version__}) -> melatih ulang...")
    import subprocess
    import sys
    subprocess.run([sys.executable, os.path.join(BASE, "train_medsos.py")], check=True, cwd=BASE,
                   stdout=subprocess.DEVNULL)
    return joblib.load(MODEL_FILE)


model = muat_model()
META = _baca_meta()


# ---- routes ----
@app.get("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.get("/health")
def health():
    return jsonify(status="ok", sklearn=sklearn.__version__)


@app.get("/model-info")
def model_info():
    """Ringkasan kualitas model untuk ditampilkan di game (transparan)."""
    pilih = ("n_latih", "cv_akurasi", "cv_f1", "game", "mandiri", "sklearn")
    return jsonify({k: META[k] for k in pilih if k in META})


@app.post("/predict")
def predict():
    """Kembalikan peluang phishing + alasan model (sinyal yang menaikkan/menurunkan skor)."""
    data = request.get_json(silent=True) or {}
    teks = str(data.get("text", ""))[:1000]
    if not teks.strip():
        return jsonify(error="text kosong"), 400
    prob, sinyal = jelaskan(model, teks)
    return jsonify(phish_prob=prob, level=tingkat(prob), signals=sinyal)


_lock = threading.Lock()


@app.post("/log")
def log():
    """Simpan jawaban/tweet pemain untuk analisis PkM."""
    rec = request.get_json(silent=True)
    if not isinstance(rec, dict):
        return jsonify(error="bad request"), 400
    rec["server_time"] = datetime.now(timezone.utc).isoformat()
    with _lock, open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return jsonify(ok=True)


@app.get("/export")
def export():
    """Unduh semua catatan: /export?token=ADMIN_TOKEN"""
    if not ADMIN_TOKEN or request.args.get("token") != ADMIN_TOKEN:
        return jsonify(error="forbidden"), 403
    if not os.path.exists(LOG_FILE):
        return "", 204
    with open(LOG_FILE, encoding="utf-8") as f:
        return app.response_class(f.read(), mimetype="application/x-ndjson")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
