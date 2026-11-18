"""
verif.py — Vérifie le fichier exporté (forme, période, taux de pannes).
"""
import pandas as pd

df = pd.read_parquet("data/telemetry.parquet")
print("forme      :", df.shape)
print("colonnes   :", list(df.columns))
print("période    :", df["jour"].min(), "→", df["jour"].max())
print("machines   :", df["machine_id"].nunique())
print("types      :", df["type"].value_counts().to_dict())
print("taux panne :", f"{100 * df['fault'].notna().mean():.2f} %")
print("\nrépartition par type de panne :")
print(df["fault"].value_counts(dropna=False).to_string())
print("\n3 premières lignes :")
print(df.head(3).to_string())