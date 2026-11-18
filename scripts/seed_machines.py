"""
seed_machines.py — Remplit la collection 'machines' (référentiel des 20 machines).
Idempotent : upsert par machine_id.
"""
from pymongo import MongoClient, UpdateOne

client = MongoClient("mongodb://localhost:27017")
db = client["usine"]

NOMINAL = {
    "pump":       {"temp": 40.0, "vib": 1.2, "current": 12.0, "rpm": 2950},
    "motor":      {"temp": 45.0, "vib": 1.5, "current": 15.0, "rpm": 1480},
    "compressor": {"temp": 55.0, "vib": 2.0, "current": 20.0, "rpm": 980},
}
TYPES = ["pump", "motor", "compressor"]

ops = []
for i in range(20):
    t = TYPES[i % 3]
    ops.append(UpdateOne(
        {"machine_id": f"{t}-{i:02d}"},
        {"$set": {
            "machine_id": f"{t}-{i:02d}",
            "type": t,
            "line": f"ligne{(i % 2) + 1}",
            "site": "tunis",
            "nominal": NOMINAL[t],
        }},
        upsert=True,
    ))

res = db.machines.bulk_write(ops)
print(f"✅ machines : {res.upserted_count} créées, {res.modified_count} mises à jour")
print(f"   total : {db.machines.count_documents({})}")

# Force la création de 'alerts' si elle n'existe pas
if "alerts" not in db.list_collection_names():
    db.create_collection("alerts")
print("collections :", sorted(db.list_collection_names()))