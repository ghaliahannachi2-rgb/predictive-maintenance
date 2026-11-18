"""
ingestor.py — V2 : MQTT → MongoDB en lots.

- Buffer en mémoire, flush toutes les 100 docs ou toutes les 1 s
- Reconnexion automatique MQTT (backoff) et MongoDB (retry)
- Trace les erreurs sans perdre le buffer
"""
import json
import os
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# ---------- Config ----------
BROKER    = os.getenv("MQTT_BROKER", "localhost")
PORT      = int(os.getenv("MQTT_PORT", "1883"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = "usine"
BATCH_SIZE = 100
FLUSH_INTERVAL = 1.0  # secondes

# ---------- MongoDB ----------
mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
coll  = mongo[DB_NAME]["telemetry"]

# ---------- Buffer ----------
buffer = []
lock = threading.Lock()
last_flush = time.time()


def to_doc(topic: str, payload: dict) -> dict:
    """Convertit un payload MQTT en document MongoDB."""
    parts = topic.split("/")   # factory/{site}/{line}/{machine_id}/telemetry
    return {
        "ts": datetime.fromtimestamp(payload["ts"], tz=timezone.utc),
        "meta": {
            "machine_id": payload["machine_id"],
            "type": parts[3].split("-")[0],
            "line": parts[2],
            "site": parts[1],
        },
        "temperature":   payload["temperature"],
        "vibration_rms": payload["vibration_rms"],
        "current_a":     payload["current_a"],
        "rpm":           payload["rpm"],
        **({"ground_truth": payload["ground_truth"]}
           if "ground_truth" in payload else {}),
    }


def flush(force: bool = False) -> None:
    """Envoie le buffer dans MongoDB (par lots)."""
    global buffer, last_flush
    with lock:
        if not buffer:
            return
        if not force and len(buffer) < BATCH_SIZE and \
           (time.time() - last_flush) < FLUSH_INTERVAL:
            return
        batch, buffer = buffer, []
        last_flush = time.time()

    try:
        coll.insert_many(batch, ordered=False)
        print(f"[mongo] +{len(batch)} docs "
              f"(total ~{coll.estimated_document_count():,})")
    except PyMongoError as e:
        print(f"[mongo] erreur, on remet {len(batch)} docs dans le buffer : {e}")
        with lock:
            buffer = batch + buffer


# ---------- MQTT ----------
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[mqtt] connecté à {BROKER}:{PORT}")
        client.subscribe("factory/+/+/+/telemetry")
    else:
        print(f"[mqtt] échec connexion rc={reason_code}")


def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print(f"[mqtt] déconnexion inattendue rc={reason_code}, reconnexion…")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        doc = to_doc(msg.topic, payload)
    except Exception as e:
        print(f"[mqtt] payload invalide sur {msg.topic} : {e}")
        return
    with lock:
        buffer.append(doc)
    flush()


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message
    print(f"[ingestor] démarrage — broker {BROKER}:{PORT}, mongo {MONGO_URI}")
    try:
        client.connect(BROKER, PORT)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[ingestor] arrêt demandé")
        flush(force=True)
        client.disconnect()


if __name__ == "__main__":
    main()