"""
export_telemetry.py — Photo figée de la collection telemetry vers ml/data/.

Protège les données d'entraînement du TTL (30 jours).
Sortie : ml/data/telemetry.parquet + ml/data/telemetry.csv (aperçu).
"""
import os
from pathlib import Path

import pandas as pd
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB = "usine"
OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)
OUT_PARQUET = OUT_DIR / "telemetry.parquet"
OUT_CSV = OUT_DIR / "telemetry_apercu.csv"

client = MongoClient(MONGO_URI)
coll = client[DB]["telemetry"]

n_total = coll.estimated_document_count()
print(f"documents à exporter : {n_total:,}")

projection = {
    "_id": 0,
    "ts": 1,
    "meta.machine_id": 1,
    "meta.type": 1,
    "meta.line": 1,
    "meta.site": 1,
    "temperature": 1,
    "vibration_rms": 1,
    "current_a": 1,
    "rpm": 1,
    "ground_truth.fault": 1,
    "ground_truth.severity": 1,
}

rows = []
cursor = coll.find({}, projection).sort("ts", 1).batch_size(10_000)
for i, doc in enumerate(cursor, 1):
    meta = doc.get("meta", {})
    gt = doc.get("ground_truth") or {}
    rows.append({
        "ts":            doc["ts"],
        "machine_id":    meta.get("machine_id"),
        "type":          meta.get("type"),
        "line":          meta.get("line"),
        "site":          meta.get("site"),
        "temperature":   doc.get("temperature"),
        "vibration_rms": doc.get("vibration_rms"),
        "current_a":     doc.get("current_a"),
        "rpm":           doc.get("rpm"),
        "fault":         gt.get("fault"),
        "severity":      gt.get("severity"),
    })
    if i % 500_000 == 0:
        print(f"  lu {i:,}/{n_total:,}")

print(f"conversion en DataFrame ({len(rows):,} lignes)…")
df = pd.DataFrame(rows)
df["jour"] = pd.to_datetime(df["ts"], utc=True).dt.date
print("écriture parquet…")
df.to_parquet(OUT_PARQUET, index=False)
print("écriture csv (aperçu 1000 lignes)…")
df.head(1000).to_csv(OUT_CSV, index=False)

print(f"\n✅ export terminé : {len(df):,} lignes")
print(f"   période : {df['jour'].min()} → {df['jour'].max()}")
print(f"   taux de pannes : {100 * df['fault'].notna().mean():.2f} %")
print(f"   fichier : {OUT_PARQUET.resolve()}")