"""
fleet.py — Simulateur de flotte (Phase 1 du PRD)

- 20 machines de 3 types (pump, motor, compressor)
- 4 capteurs : temperature, vibration_rms, current_a, rpm
- 4 types de pannes : overheat, bearing_wear, misalignment, sensor_fault
- Cycle de charge journalier (jour/nuit)
- Taux global de pannes ≈ 3 %
- 2 modes :
    * --mode realtime  : publie en MQTT (1 message par machine et par tick)
    * --mode backfill  : génère N jours d'historique directement dans MongoDB

Usage :
    python fleet.py --mode realtime
    python fleet.py --mode backfill --days 30 --period 10
"""

import argparse
import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np
import paho.mqtt.client as mqtt
from pymongo import MongoClient

# ------------------------------------------------------------------
# 1. Constantes du contrat de données (identiques au PRD)
# ------------------------------------------------------------------
SITE = "tunis"
MACHINE_TYPES = ["pump", "motor", "compressor"]
FAULT_TYPES = ["overheat", "bearing_wear", "misalignment", "sensor_fault"]

# Valeurs nominales par type de machine
NOMINAL = {
    "pump":       {"temp": 40.0, "vib": 1.2, "current": 12.0, "rpm": 2950},
    "motor":      {"temp": 45.0, "vib": 1.5, "current": 15.0, "rpm": 1480},
    "compressor": {"temp": 55.0, "vib": 2.0, "current": 20.0, "rpm": 980},
}

# Probabilité de démarrer une panne à chaque tick
# Avec un tick toutes les 10 s sur 30 jours = 259 200 ticks par machine.
# 3 % du temps en panne, avec durée moyenne ~180 ticks (30 min) :
#   p_start ≈ 0.03 / 180 ≈ 1.7e-4
P_FAULT_PER_TICK = 1.7e-4


# ------------------------------------------------------------------
# 2. Modèle de machine
# ------------------------------------------------------------------
@dataclass
class Machine:
    machine_id: str
    type: str
    line: str
    nominal: dict
    state: dict = field(default_factory=dict)
    fault: dict = field(default_factory=dict)


def build_fleet(n: int = 20, seed: int = 42) -> list:
    """Crée N machines réparties sur 3 types et 2 lignes."""
    rng = random.Random(seed)
    fleet = []
    for i in range(n):
        t = MACHINE_TYPES[i % len(MACHINE_TYPES)]
        m = Machine(
            machine_id=f"{t}-{i:02d}",
            type=t,
            line=f"ligne{(i % 2) + 1}",
            nominal=dict(NOMINAL[t]),
            state={},
            fault={"type": None},
        )
        m.state = {
            "temp":    m.nominal["temp"]    + rng.uniform(-2, 2),
            "vib":     m.nominal["vib"]     + rng.uniform(-0.1, 0.1),
            "current": m.nominal["current"] + rng.uniform(-0.5, 0.5),
            "rpm":     m.nominal["rpm"]     + rng.uniform(-20, 20),
        }
        fleet.append(m)
    return fleet


# ------------------------------------------------------------------
# 3. Signatures de pannes
# ------------------------------------------------------------------
def maybe_start_fault(m: Machine, tick_idx: int, rng: random.Random) -> None:
    """Démarre une panne aléatoire avec probabilité P_FAULT_PER_TICK."""
    if m.fault["type"] is not None:
        return
    if rng.random() < P_FAULT_PER_TICK:
        m.fault = {
            "type":  rng.choice(FAULT_TYPES),
            "start": tick_idx,
            "dur":   rng.randint(60, 300),   # 10 à 50 min si tick = 10 s
            "sev":   rng.uniform(0.3, 1.0),
        }


def apply_fault(m: Machine, tick_idx: int) -> None:
    """Applique la panne en cours (rampe progressive de 0 à sev)."""
    f = m.fault
    if f["type"] is None:
        return
    elapsed = tick_idx - f["start"]
    if elapsed > f["dur"]:
        m.fault = {"type": None}
        return

    sev = f["sev"] * (elapsed / f["dur"])  # rampe linéaire

    if f["type"] == "overheat":
        # Température dérive, vibration stable
        m.state["temp"] += 30 * sev
    elif f["type"] == "bearing_wear":
        # Vibration monte, température monte légèrement
        m.state["vib"] += 3.0 * sev
        m.state["temp"] += 5 * sev
    elif f["type"] == "misalignment":
        # Vibration et courant montent ensemble
        m.state["vib"] += 2.5 * sev
        m.state["current"] += 4.0 * sev
    elif f["type"] == "sensor_fault":
        # Initialise la valeur figée au premier tick de la panne (elapsed == 0)
        if "frozen_temp" not in f:
            f["frozen_temp"] = m.state["temp"]
        m.state["temp"] = f["frozen_temp"]


# ------------------------------------------------------------------
# 4. Cycle de charge journalier
# ------------------------------------------------------------------
def daily_load(t: float) -> float:
    """Facteur 0.9 (nuit) → 1.1 (jour). t = epoch secondes."""
    h = (t / 3600) % 24
    return 1.0 + 0.1 * np.sin((h - 6) / 24 * 2 * np.pi)


# ------------------------------------------------------------------
# 5. Génération d'un relevé (tick)
# ------------------------------------------------------------------
def make_tick(m: Machine, t: float, tick_idx: int, rng: random.Random) -> dict:
    """Retourne le payload JSON pour une machine à l'instant t."""
    # Reset vers le nominal + bruit gaussien
    m.state["temp"]    = m.nominal["temp"]    + rng.gauss(0, 0.4)
    m.state["vib"]     = m.nominal["vib"]     + rng.gauss(0, 0.05)
    m.state["current"] = m.nominal["current"] + rng.gauss(0, 0.2)
    m.state["rpm"]     = m.nominal["rpm"]     + rng.gauss(0, 5)

    # Cycle de charge journalier
    load = daily_load(t)
    m.state["temp"]    *= load
    m.state["current"] *= load

    # Panne éventuelle
    maybe_start_fault(m, tick_idx, rng)
    apply_fault(m, tick_idx)

    payload = {
        "machine_id":    m.machine_id,
        "ts":            t,
        "temperature":   round(m.state["temp"], 2),
        "vibration_rms": round(m.state["vib"], 3),
        "current_a":     round(m.state["current"], 2),
        "rpm":           round(m.state["rpm"], 1),
    }
    if m.fault["type"] is not None:
        payload["ground_truth"] = {
            "fault":    m.fault["type"],
            "severity": round(m.fault["sev"], 2),
        }
    return payload


def topic_for(m: Machine) -> str:
    return f"factory/{SITE}/{m.line}/{m.machine_id}/telemetry"


# ------------------------------------------------------------------
# 6. Mode temps réel (MQTT)
# ------------------------------------------------------------------
def run_realtime(fleet, broker: str = "localhost", period_s: float = 1.0,
                 seed: int = 42) -> None:
    rng = random.Random(seed)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect(broker, 1883)
    client.loop_start()

    tick_idx = 0
    print(f"[realtime] {len(fleet)} machines, période {period_s}s, broker {broker}")
    try:
        while True:
            t = time.time()
            for m in fleet:
                payload = make_tick(m, t, tick_idx, rng)
                client.publish(topic_for(m), json.dumps(payload))
            tick_idx += 1
            time.sleep(period_s)
    except KeyboardInterrupt:
        print("\n[realtime] arrêt demandé")
    finally:
        client.loop_stop()
        client.disconnect()


# ------------------------------------------------------------------
# 7. Mode backfill (écriture directe dans MongoDB)
# ------------------------------------------------------------------
def payload_to_doc(m: Machine, payload: dict) -> dict:
    return {
        "ts": datetime.fromtimestamp(payload["ts"], tz=timezone.utc),
        "meta": {
            "machine_id": payload["machine_id"],
            "type":       m.type,
            "line":       m.line,
            "site":       SITE,
        },
        "temperature":   payload["temperature"],
        "vibration_rms": payload["vibration_rms"],
        "current_a":     payload["current_a"],
        "rpm":           payload["rpm"],
        **({"ground_truth": payload["ground_truth"]}
           if "ground_truth" in payload else {}),
    }


def run_backfill(fleet, days: int = 30, period_s: float = 10.0,
                 seed: int = 42, mongo_uri: str = "mongodb://localhost:27017",
                 batch_size: int = 5000) -> None:
    rng = random.Random(seed)
    mongo = MongoClient(mongo_uri)
    coll = mongo["usine"]["telemetry"]

    now = time.time()
    start = now - days * 86400
    n_ticks = int(days * 86400 / period_s)
    print(f"[backfill] {len(fleet)} machines × {n_ticks} ticks = "
          f"{len(fleet) * n_ticks:,} documents attendus")

    batch = []
    tick_idx = 0
    for i in range(n_ticks):
        t = start + i * period_s
        for m in fleet:
            payload = make_tick(m, t, tick_idx, rng)
            batch.append(payload_to_doc(m, payload))
        tick_idx += 1

        if len(batch) >= batch_size:
            coll.insert_many(batch, ordered=False)
            batch = []

        if i % 1000 == 0 and i > 0:
            print(f"  tick {i}/{n_ticks} — "
                  f"{coll.estimated_document_count():,} docs insérés")

    if batch:
        coll.insert_many(batch, ordered=False)

    print(f"[backfill] terminé — {coll.estimated_document_count():,} documents")


# ------------------------------------------------------------------
# 8. CLI
# ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Simulateur de flotte (Phase 1)")
    ap.add_argument("--mode", choices=["realtime", "backfill"], default="realtime")
    ap.add_argument("--machines", type=int, default=20)
    ap.add_argument("--days", type=int, default=30, help="jours à générer (backfill)")
    ap.add_argument("--period", type=float, default=10.0,
                    help="secondes entre deux relevés (backfill)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--broker", default="localhost")
    ap.add_argument("--mongo", default="mongodb://localhost:27017")
    args = ap.parse_args()

    fleet = build_fleet(args.machines, args.seed)

    if args.mode == "realtime":
        run_realtime(fleet, broker=args.broker, period_s=1.0, seed=args.seed)
    else:
        run_backfill(fleet, days=args.days, period_s=args.period,
                     seed=args.seed, mongo_uri=args.mongo)


if __name__ == "__main__":
    main()