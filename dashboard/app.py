"""
Tableau de bord v2 : les alertes viennent de l'IA (endpoint /etat-machine).
"""
import time
import requests
import pandas as pd
import streamlit as st

API = "http://localhost:8000"

st.set_page_config(page_title="Usine - Maintenance predictive", layout="wide")
st.title("🏭 Surveillance machine — alertes par IA")

zone = st.empty()

while True:
    with zone.container():
        rep_temp = requests.get(f"{API}/mesures/temperature?nombre=200").json()
        rep_vib  = requests.get(f"{API}/mesures/vibration?nombre=200").json()
        stats    = requests.get(f"{API}/stats/temperature").json()
        nb_anom  = requests.get(f"{API}/anomalies").json()["nombre_anomalies"]
        etat     = requests.get(f"{API}/etat-machine").json()          # ← L'IA DECIDE
        alertes  = requests.get(f"{API}/alertes").json()               # ← historique

        c1, c2, c3 = st.columns(3)
        c1.metric("Temperature moyenne", f"{stats.get('moyenne', 0):.2f} °C")
        c2.metric("Temperature max", f"{stats.get('maximum', 0):.2f} °C")
        c3.metric("⚠️ Mesures en anomalie (reel)", nb_anom)

        # ----- Bandeau d'alerte : DECIDE PAR L'IA -----
        if etat.get("anomalie_detectee"):
            st.error(f"🔴 ALERTE IA : anomalie detectee ! "
                     f"({etat['proportion_anomalies']*100:.0f}% des mesures jugees anormales — "
                     f"temp={etat['temperature_actuelle']}°C, vib={etat['vibration_actuelle']}g)")
        else:
            st.success("🟢 Machine normale (certifie par l'IA)")

        g1, g2 = st.columns(2)
        with g1:
            st.subheader("🌡️ Temperature (°C)")
            if rep_temp["mesures"]:
                df_t = pd.DataFrame(rep_temp["mesures"]).sort_values("timestamp")
                st.line_chart(df_t, x="timestamp", y="valeur")
        with g2:
            st.subheader("📳 Vibrations (g)")
            if rep_vib["mesures"]:
                df_v = pd.DataFrame(rep_vib["mesures"]).sort_values("timestamp")
                st.line_chart(df_v, x="timestamp", y="valeur")

        # ----- Historique des alertes IA -----
        if alertes:
            st.subheader("🚨 Alertes detectees par l'IA")
            df_a = pd.DataFrame(alertes)
            df_a["date"] = pd.to_datetime(df_a["date"], unit="s").dt.strftime("%H:%M:%S")
            st.dataframe(df_a, use_container_width=True)

        st.caption(f"Rafraichi toutes les 5 s — {time.strftime('%H:%M:%S')}")

    time.sleep(5)
    st.rerun()