"""
check_phase1.py — Vérifie les critères d'acceptation de la Phase 1.
"""
import time
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

c = MongoClient("mongodb://localhost:27017")
db = c["usine"]

n = db.telemetry.estimated_document_count()
machines = db.telemetry.distinct("meta.machine_id")
print(f"documents : {n:,}")
print(f"machines  : {len(machines)} ({machines[:3]}...)")

# Q2 : moyenne par heure sur 7 jours pour une machine
since = datetime.now(timezone.utc) - timedelta(days=7)
t0 = time.time()
res = list(db.telemetry.aggregate([
    {"$match": {"meta.machine_id": machines[0], "ts": {"$gte": since}}},
    {"$group": {
        "_id": {"$dateTrunc": {"date": "$ts", "unit": "hour"}},
        "avg_temp": {"$avg": "$temperature"},
        "avg_vib":  {"$avg": "$vibration_rms"},
        "n":        {"$sum": 1},
    }},
    {"$sort": {"_id": 1}},
]))
dt = (time.time() - t0) * 1000
print(f"Q2 (moyenne/heure 7j, {machines[0]}) : {len(res)} buckets en {dt:.0f} ms")

# Top-K machines par température max sur 24h
since24 = datetime.now(timezone.utc) - timedelta(hours=24)
t0 = time.time()
top = list(db.telemetry.aggregate([
    {"$match": {"ts": {"$gte": since24}}},
    {"$group": {"_id": "$meta.machine_id",
                "max_temp": {"$max": "$temperature"}}},
    {"$sort": {"max_temp": -1}},
    {"$limit": 5},
]))
dt2 = (time.time() - t0) * 1000
print(f"Top-5 temp max 24h : {dt2:.0f} ms")
for r in top:
    print(f"  {r['_id']:14s} {r['max_temp']:.1f} °C")

# Taux de pannes (ground_truth présent)
n_fault = db.telemetry.count_documents({"ground_truth": {"$exists": True}})
print(f"\ntaux de pannes : {100 * n_fault / n:.2f} %  ({n_fault:,} docs en panne)")

assert n >= 1_000_000, "❌ moins d'1 M de documents"
assert dt < 200,          "❌ Q2 > 200 ms"
assert 1.0 <= 100 * n_fault / n <= 6.0, "❌ taux de pannes hors de [1 %, 6 %]"
print("\n✅ Phase 1 : critères d'acceptation OK")