"""
rapport_qualite.py — Rapport qualité chiffré (DAT-03).

Compare :
- ce qui est dans MongoDB (telemetry)
- ce qui est conforme au validateur $jsonSchema
- ce qui serait rejeté (valeurs manquantes, hors plage, machine inconnue)
"""
import os
from datetime import datetime

from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB = "usine"

client = MongoClient(MONGO_URI)
db = client[DB]
coll = db["telemetry"]

n_total = coll.estimated_document_count()
print(f"=== Rapport qualité — {datetime.now().isoformat(timespec='seconds')} ===")
print(f"Documents dans telemetry : {n_total:,}")

# 1. Valeurs manquantes (champ obligatoire absent)
missing = coll.count_documents({
    "$or": [
        {"ts": {"$exists": False}},
        {"meta.machine_id": {"$exists": False}},
        {"temperature": {"$exists": False}},
        {"vibration_rms": {"$exists": False}},
        {"current_a": {"$exists": False}},
        {"rpm": {"$exists": False}},
    ]
})
print(f"Champs obligatoires manquants : {missing:,}")

# 2. Valeurs hors plage
out_of_range = coll.count_documents({
    "$or": [
        {"temperature": {"$lt": 0}},
        {"temperature": {"$gt": 150}},
        {"vibration_rms": {"$lt": 0}},
        {"vibration_rms": {"$gt": 20}},
        {"current_a": {"$lt": 0}},
        {"current_a": {"$gt": 100}},
        {"rpm": {"$lt": 0}},
        {"rpm": {"$gt": 5000}},
    ]
})
print(f"Valeurs hors plage : {out_of_range:,}")

# 3. Machines inconnues du référentiel SQL
pg_machines = {
    "pump-00", "pump-03", "pump-06", "pump-09", "pump-12", "pump-15", "pump-18",
    "motor-01", "motor-04", "motor-07", "motor-10", "motor-13", "motor-16", "motor-19",
    "compressor-02", "compressor-05", "compressor-08", "compressor-11",
    "compressor-14", "compressor-17",
}
known = coll.count_documents({"meta.machine_id": {"$in": list(pg_machines)}})
print(f"Documents avec machine connue : {known:,}")

# 4. Doublons (même machine_id + même ts)
pipeline = [
    {"$group": {"_id": {"m": "$meta.machine_id", "t": "$ts"}, "n": {"$sum": 1}}},
    {"$match": {"n": {"$gt": 1}}},
    {"$count": "doublons"},
]
dup = list(coll.aggregate(pipeline))
n_dup = dup[0]["doublons"] if dup else 0
print(f"Doublons (machine_id + ts) : {n_dup:,}")

# 5. Synthèse
print("\n=== Synthèse ===")
print(f"Importés     : {n_total:,}")
print(f"Rejetés      : {missing + out_of_range:,}")
print(f"Conservés    : {n_total - missing - out_of_range:,}")
print(f"Taux de rejet: {100 * (missing + out_of_range) / max(n_total, 1):.4f} %")