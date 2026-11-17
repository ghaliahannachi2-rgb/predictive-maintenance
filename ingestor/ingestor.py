import json
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from pymongo import MongoClient, ASCENDING

BROKER = "localhost"
PORT = 1883
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "usine"
COLLECTION = "mesures"

mongo = MongoClient(MONGO_URI)
col = mongo[DB_NAME][COLLECTION]
col.create_index([("timestamp", ASCENDING)])
col.create_index([("capteur", ASCENDING)])
print("Connecte a MongoDB + index crees")

def quand_message_recu(client, userdata, msg):
    try:
        donnees = json.loads(msg.payload.decode())
        document = {
            "topic": msg.topic,
            "capteur": msg.topic.split("/")[-1],
            "valeur": donnees["value"],
            "unite": donnees["unit"],
            "vraie_anomalie": donnees.get("anomaly", False),
            "timestamp": donnees["timestamp"],
            "recu_a": datetime.now(timezone.utc).isoformat(),
        }
        col.insert_one(document)
        print(f"Range : {document['capteur']} = {document['valeur']}")
    except Exception as e:
        print(f"Erreur : {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = quand_message_recu
client.connect(BROKER, PORT, keepalive=60)
client.subscribe("factory/#")
print("J'ecoute les topics factory/# ...")
client.loop_forever()