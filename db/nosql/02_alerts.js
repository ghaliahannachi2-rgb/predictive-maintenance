// =============================================================
// 02_alerts.js — Collection alerts + index (NOS-05)
// =============================================================

use("usine");

if (!db.getCollectionNames().includes("alerts")) {
  db.createCollection("alerts");
  print("✅ collection 'alerts' créée");
} else {
  print("ℹ️  collection 'alerts' existe déjà");
}

db.alerts.createIndex({ machine_id: 1, ts: -1 });
print("✅ index { machine_id: 1, ts: -1 }");

db.alerts.createIndex({ acquittee: 1, ts: -1 });
print("✅ index { acquittee: 1, ts: -1 }");

print("\nIndex sur alerts :");
printjson(db.alerts.getIndexes());