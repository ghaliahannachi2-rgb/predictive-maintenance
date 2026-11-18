"""
init_mongo.py — Crée la collection time-series et les index (idempotent).

Usage :
    python scripts/init_mongo.py
"""
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

MONGO_URI = "mongodb://localhost:27017"
DB = "usine"

client = MongoClient(MONGO_URI)
db = client[DB]

# 1. Collection time-series telemetry
try:
    db.create_collection(
        "telemetry",
        timeseries={
            "timeField": "ts",
            "metaField": "meta",
            "granularity": "seconds",
        },
        expireAfterSeconds=60 * 60 * 24 * 30,  # TTL : 30 jours
    )
    print("✅ collection 'telemetry' créée (time-series, TTL 30j)")
except CollectionInvalid:
    print("ℹ️  collection 'telemetry' existe déjà")

# 2. Index utiles
db.telemetry.create_index([("meta.machine_id", 1), ("ts", -1)])
db.telemetry.create_index([("meta.type", 1)])
print("✅ index telemetry créés")

# 3. Collections référentiel + alertes
db.machines.create_index("machine_id", unique=True)
db.alerts.create_index([("machine_id", 1), ("ts", -1)])
print("✅ index 'machines' et 'alerts' créés")

print("\nRésumé :")
print("  base     :", DB)
print("  collections :", db.list_collection_names())