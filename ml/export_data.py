"""
Exporte les mesures de MongoDB vers un CSV pour entrainer l'IA.
Correction : on apparie temp et vibration PAR ORDRE D'ARRIVEE
(pas par timestamp exact, qui differe de quelques microsecondes).
"""
import pandas as pd
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
col = client["usine"]["mesures"]

temps = list(col.find({"capteur": "temperature"}, {"_id": 0, "valeur": 1, "vraie_anomalie": 1}).sort("timestamp", 1))
vibs  = list(col.find({"capteur": "vibration"}, {"_id": 0, "valeur": 1}).sort("timestamp", 1))

print(f"Temperatures trouvees : {len(temps)}")
print(f"Vibrations trouvees : {len(vibs)}")

# On prend autant de paires que possible
n = min(len(temps), len(vibs))

df = pd.DataFrame({
    "temperature":  [t["valeur"] for t in temps[:n]],
    "vibration":    [v["valeur"] for v in vibs[:n]],
    "vraie_anomalie": [t["vraie_anomalie"] for t in temps[:n]],
})

df.to_csv("donnees.csv", index=False)

print(f"Exporte {len(df)} lignes dans donnees.csv")
print(f"Dont {int(df['vraie_anomalie'].sum())} mesures pendant une panne")