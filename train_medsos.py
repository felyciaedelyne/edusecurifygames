"""Melatih model phishing gaya media sosial (v2) dan menyimpan model_medsos.joblib + model_meta.json.

Evaluasi tiga lapis (semuanya jujur: data uji TIDAK ikut dilatih):
  1. GroupKFold per template: template yang sama tidak boleh muncul di train DAN validasi.
     Dipakai untuk MEMILIH konfigurasi (C, dst.).
  2. data/uji_mandiri.csv: pesan tulisan tangan di luar template (uji "dunia nyata" kecil).
  3. data/game_items.csv: soal yang ada di game.

Jalankan: python train_medsos.py
"""
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, recall_score, precision_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer

from fitur import normalisasi_batch

BASE = os.path.dirname(os.path.abspath(__file__))


def buat_pipeline(C=10.0, char=True):
    bagian = [("kata", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, token_pattern=r"(?u)\b\w+\b"))]
    if char:
        bagian.append(("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True)))
    return Pipeline([
        ("norm", FunctionTransformer(normalisasi_batch, validate=False)),
        ("tfidf", FeatureUnion(bagian)),
        ("clf", LogisticRegression(C=C, class_weight="balanced", max_iter=5000)),
    ])


def cv_group(df, C=10.0, k=5, char=True):
    acc, f1 = [], []
    for tr, va in GroupKFold(n_splits=k).split(df["teks"], df["label"], df["grup"]):
        m = buat_pipeline(C, char).fit(df["teks"].iloc[tr], df["label"].iloc[tr])
        p = m.predict(df["teks"].iloc[va])
        acc.append(accuracy_score(df["label"].iloc[va], p))
        f1.append(f1_score(df["label"].iloc[va], p))
    return float(np.mean(acc)), float(np.mean(f1))


def ringkas(nama, df, model):
    prob = model.predict_proba(df["teks"])[:, 1]
    pred = (prob >= 0.5).astype(int)
    r = dict(n=int(len(df)), akurasi=round(accuracy_score(df["label"], pred), 4),
             presisi=round(precision_score(df["label"], pred, zero_division=0), 4),
             recall=round(recall_score(df["label"], pred, zero_division=0), 4),
             f1=round(f1_score(df["label"], pred, zero_division=0), 4))
    print(f"\n{nama}: n={r['n']} akurasi={r['akurasi']:.3f} presisi={r['presisi']:.3f} recall={r['recall']:.3f} F1={r['f1']:.3f}")
    print(classification_report(df["label"], pred, target_names=["Normal", "Phishing"], zero_division=0))
    salah = df.assign(prob=prob.round(2), pred=pred)
    salah = salah[salah["label"] != salah["pred"]]
    for _, x in salah.iterrows():
        print(f"  SALAH label={x['label']} prob={x['prob']} :: {str(x['teks'])[:95]}")
    return r


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(BASE, "data", "dataset_medsos.csv"))
    game = pd.read_csv(os.path.join(BASE, "data", "game_items.csv"))
    mandiri_path = os.path.join(BASE, "data", "uji_mandiri.csv")
    mandiri = pd.read_csv(mandiri_path) if os.path.exists(mandiri_path) else None
    print(f"scikit-learn {sklearn.__version__}")
    print(f"Latih: {len(df)} contoh ({int(df['label'].sum())} phishing, {df['grup'].nunique()} template)"
          f" | Uji game: {len(game)} | Uji mandiri: {0 if mandiri is None else len(mandiri)}")

    print("\nGroupKFold (5 lipatan, per template) untuk memilih konfigurasi:")
    terbaik = None
    for char in (False, True):
        for C in (1, 3, 10, 30):
            acc, f1 = cv_group(df, C=C, char=char)
            print(f"  char={char!s:<5} C={C:<3} akurasi={acc:.3f}  F1 phishing={f1:.3f}")
            if terbaik is None or f1 > terbaik[2] + 1e-9:
                terbaik = (C, char, f1, acc)
    C, char, cv_f1, cv_acc = terbaik
    print(f"-> dipilih C={C}, char={char} (CV akurasi={cv_acc:.3f}, F1={cv_f1:.3f})")

    # Skor uji yang DILAPORKAN memakai model yang dilatih pada seluruh data latih
    model = buat_pipeline(C, char).fit(df["teks"], df["label"])
    meta = dict(sklearn=sklearn.__version__, C=C, char=char, n_latih=int(len(df)),
                cv_akurasi=round(cv_acc, 4), cv_f1=round(cv_f1, 4))
    meta["game"] = ringkas("Uji soal game", game, model)
    if mandiri is not None:
        meta["mandiri"] = ringkas("Uji mandiri (tulisan tangan, di luar template)", mandiri, model)

    out = os.path.join(BASE, "model_medsos.joblib")
    joblib.dump(model, out, compress=3)
    with open(os.path.join(BASE, "model_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"\nTersimpan: {out} ({os.path.getsize(out) / 1024:.0f} KB) + model_meta.json")
