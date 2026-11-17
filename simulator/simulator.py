import json
import time
import numpy as np
import paho.mqtt.client as mqtt

# ---------- CONFIGURATION ----------
BROKER = "localhost"
PORT = 1883
TOPIC_TEMP = "factory/ligne1/machine1/temperature"
TOPIC_VIB = "factory/ligne1/machine1/vibration"
INTERVALLE = 3

# ---------- LA MACHINE SIMULEE ----------
class Machine:
    def __init__(self):
        self.t = 0
        self.debut_panne = 40
        self.duree_panne = 20

    def mesurer(self):
        self.t += 1
        cycle = self.t % 100           # le temps recommence a 0 toutes les 100 mesures
        en_panne = 40 <= cycle < 60    # donc UNE PANNE TOUTES LES ~5 MINUTES

        if en_panne:
            avancement = (cycle - 40) / 20
            temperature = 25 + avancement * 18 + np.random.normal(0, 0.8)
            vibration = 0.5 + avancement * 3.0 + np.random.normal(0, 0.15)
        else:
            temperature = 25 + np.random.normal(0, 0.4)
            vibration = 0.5 + np.random.normal(0, 0.05)

        return round(float(temperature), 2), round(float(vibration), 3), en_panne

# ---------- CONNEXION AU BROKER ----------
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, keepalive=60)
print(f"Connecte au broker MQTT {BROKER}:{PORT}")

machine = Machine()

try:
    while True:
        temperature, vibration, en_panne = machine.mesurer()

        message_temp = json.dumps({
            "value": temperature, "unit": "celsius",
            "anomaly": en_panne, "timestamp": time.time()
        })
        message_vib = json.dumps({
            "value": vibration, "unit": "g",
            "anomaly": en_panne, "timestamp": time.time()
        })

        client.publish(TOPIC_TEMP, message_temp)
        client.publish(TOPIC_VIB, message_vib)

        statut = "ANOMALIE !" if en_panne else "normal"
        print(f"[mesure {machine.t}] temp={temperature}°C | vib={vibration}g | {statut}")
        time.sleep(INTERVALLE)

except KeyboardInterrupt:
    print("Simulateur arrete.")
    client.disconnect()