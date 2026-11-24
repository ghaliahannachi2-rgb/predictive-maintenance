// =============================================================
// 01_validation.js — Validation de schéma MongoDB (NOS-02)
// =============================================================

use("usine");

db.runCommand({
  collMod: "telemetry",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["ts", "meta", "temperature", "vibration_rms", "current_a", "rpm"],
      properties: {
        ts: { bsonType: "date" },
        meta: {
          bsonType: "object",
          required: ["machine_id", "type", "line", "site"],
          properties: {
            machine_id: { bsonType: "string", pattern: "^(pump|motor|compressor)-[0-9]{2}$" },
            type: { enum: ["pump", "motor", "compressor"] },
            line: { enum: ["ligne1", "ligne2"] },
            site: { enum: ["tunis"] }
          }
        },
        temperature:   { bsonType: "double", minimum: 0, maximum: 150 },
        vibration_rms: { bsonType: "double", minimum: 0, maximum: 20 },
        current_a:     { bsonType: "double", minimum: 0, maximum: 100 },
        rpm:           { bsonType: ["int", "double"], minimum: 0, maximum: 5000 },
        batch_id:      { bsonType: "string" },
        ground_truth: {
          bsonType: "object",
          properties: {
            fault:    { enum: ["overheat", "bearing_wear", "misalignment", "sensor_fault"] },
            severity: { bsonType: "double", minimum: 0, maximum: 1 }
          }
        }
      }
    }
  },
  validationLevel: "moderate",
  validationAction: "error"
});

print("✅ validateur $jsonSchema appliqué sur usine.telemetry");