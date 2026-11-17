"""
Entraine Isolation Forest pour detecter les anomalies,
puis evalue-le grace au ground truth.
"""
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

# ---------- 1. CHARGER LES DONNEES ----------
df = pd.read_csv("donnees.csv")
X = df[["temperature", "vibration"]]            # les features (ce que le modele regarde)
y_vrai = df["vraie_anomalie"].astype(int)       # le ground truth : la verite vraie

print(f"Donnees : {len(df)} mesures, {y_vrai.sum()} anomalies reelles")

# ---------- 2. ENTRAINER LE MODELE ----------
modele = IsolationForest(
    n_estimators=200,      # nombre d'arbres (plus il y en a, plus c'est stable)
    contamination=0.2,     # ~20% d'anomalies attendues (on connait la proportion grace au simulateur)
    random_state=42        # pour que les resultats soient reproductibles
)
modele.fit(X)              # le modele APPREND le "normal"

# ---------- 3. PREDIRE ----------
predictions = modele.predict(X)     # -1 = anomalie detectee, 1 = normal
df["prediction"] = (predictions == -1).astype(int)   # on convertit : 1 = anomalie

# ---------- 4. EVALUER (le tableau qui impressionne le jury) ----------
print("\n===== RAPPORT DE CLASSIFICATION =====")
print(classification_report(y_vrai, df["prediction"], target_names=["normal", "anomalie"]))

# ---------- 5. SAUVEGARDER LE MODELE ----------
joblib.dump(modele, "modele_isolation_forest.joblib")
df.to_csv("predictions.csv", index=False)
print("\nModele sauvegarde dans modele_isolation_forest.joblib")
print("Predictions sauvegardees dans predictions.csv")