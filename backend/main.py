"""
Backend : le vendeur du magasin.
Version 2 : integre le modele d'IA Isolation Forest pour les alertes.
"""
import time
import joblib
from fastapi import FastAPI, Query
from pymongo import MongoClient, DESCENDING

# ---------- CONNEXIONS ----------
client = MongoClient("mongodb://localhost:27017/")
db = client["usine"]
col = db["mesures"]
col_alertes = db["alertes"]          # nouveau tiroir : l'historique des alertes IA

# ---------- CHARGEMENT DU MODELE IA ----------
modele = joblib.load("modele_isolation_forest.joblib")
print("Modele IA charge.")

# ---------- CREATION DE L'API ----------
app = FastAPI(title="API Maintenance predictive")

@app.get("/")
def accueil():
    return {"message": "API en marche !", "ia": "Isolation Forest active"}

@app.get("/mesures/{capteur}")
def dernieres_mesures(capteur: str, nombre: int = Query(default=10, le=500)):
    resultats = list(col.find({"capteur": capteur}, {"_id": 0})
                     .sort("timestamp", DESCENDING).limit(nombre))
    return {"capteur": capteur, "nombre": len(resultats), "mesures": resultats}

@app.get("/stats/{capteur}")
def statistiques(capteur: str):
    pipeline = [
        {"$match": {"capteur": capteur}},
        {"$group": {"_id": None, "moyenne": {"$avg": "$valeur"},
                    "minimum": {"$min": "$valeur"}, "maximum": {"$max": "$valeur"},
                    "total": {"$sum": 1}}}
    ]
    resultat = list(col.aggregate(pipeline))
    return resultat[0] if resultat else {"message": "aucune donnee"}

@app.get("/anomalies")
def anomalies():
    return {"nombre_anomalies": col.count_documents({"vraie_anomalie": True})}

# ========== NOUVEAU : L'IA JUGE L'ETAT DE LA MACHINE ==========
@app.get("/etat-machine")
def etat_machine():
    # 1. Recuperer les 20 dernieres mesures de chaque capteur
    temps = list(col.find({"capteur": "temperature"}, {"_id": 0, "valeur": 1})
                 .sort("timestamp", DESCENDING).limit(20))
    vibs = list(col.find({"capteur": "vibration"}, {"_id": 0, "valeur": 1})
                .sort("timestamp", DESCENDING).limit(20))

    if len(temps) < 5 or len(vibs) < 5:
        return {"anomalie_detectee": False, "message": "pas assez de donnees"}

    # 2. Apparier par ordre (comme dans l'export) et predire sur chaque paire
    n = min(len(temps), len(vibs))
    paires = [[temps[i]["valeur"], vibs[i]["valeur"]] for i in range(n)]
    predictions = modele.predict(paires)          # -1 = anomalie, 1 = normal

    # 3. Vote majoritaire : au moins 60% d'anomalies pour declencher l'alerte
    nb_anomalies = int((predictions == -1).sum())
    alerte = nb_anomalies / n >= 0.6

    # 4. Journaliser l'alerte (eviter les doublons : 1 alerte par minute max)
    if alerte:
        derniere = col_alertes.find_one(sort=[("date", DESCENDING)])
        if not derniere or time.time() - derniere["date"] > 60:
            col_alertes.insert_one({
                "date": time.time(), "score": nb_anomalies / n,
                "detail": f"{nb_anomalies}/{n} mesures jugees anormales"
            })

    return {
        "anomalie_detectee": alerte,
        "proportion_anomalies": round(nb_anomalies / n, 2),
        "temperature_actuelle": temps[0]["valeur"],
        "vibration_actuelle": vibs[0]["valeur"],
    }

@app.get("/alertes")
def alertes():
    """Historique des alertes declenchees par l'IA."""
    return list(col_alertes.find({}, {"_id": 0}).sort("date", DESCENDING).limit(20))