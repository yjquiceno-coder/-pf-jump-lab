"""Conexión con la API de Catapult OpenField.
El webhook avisa que una actividad terminó; aquí descargamos sus datos
(mismas columnas que el export 'Control de Carga') para analizarlos."""
import os, io, logging
import pandas as pd
import requests

log = logging.getLogger("pf-jump-lab.catapult")

OPENFIELD_BASE = os.getenv("CATAPULT_API_BASE", "https://connect-eu.catapultsports.com/api/v6")
API_TOKEN = os.getenv("CATAPULT_API_TOKEN", "")

# Métricas a solicitar (deben coincidir con las del Control de Carga)
PARAMETERS = [
    "total_distance", "total_player_load", "high_speed_distance",
    "acceleration_count", "deceleration_count", "max_velocity",
    "meterage_per_minute", "sprint_efforts",
]


def fetch_activity_dataframe(activity_id: str, payload: dict) -> pd.DataFrame:
    """Devuelve un DataFrame con las filas por jugador de la actividad.

    1) Si el webhook trae un CSV/URL de export embebido, se usa.
    2) Si hay token de API, se consulta el efforts/stats de la actividad.
    3) Si se define DEMO_EXCEL, se usa ese archivo (para pruebas locales)."""
    demo = os.getenv("DEMO_EXCEL")
    if demo and os.path.exists(demo):
        log.info("Modo DEMO: usando %s", demo)
        return pd.read_excel(demo)

    if not API_TOKEN:
        raise RuntimeError("Falta CATAPULT_API_TOKEN para descargar datos de la actividad.")

    headers = {"Authorization": f"Bearer {API_TOKEN}", "Accept": "application/json"}
    # Stats agregadas por atleta para la actividad (ajustar endpoint según tu plan OpenField)
    url = f"{OPENFIELD_BASE}/activities/{activity_id}/athletes"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    athletes = r.json()

    rows = []
    for a in athletes:
        aid = a.get("id") or a.get("athlete_id")
        stats_url = f"{OPENFIELD_BASE}/activities/{activity_id}/athletes/{aid}/parameters"
        sr = requests.get(stats_url, headers=headers,
                          params={"parameters": ",".join(PARAMETERS)}, timeout=30)
        sr.raise_for_status()
        s = {x.get("parameter"): x.get("value") for x in sr.json()}
        rows.append({
            "Player Name": a.get("name") or f"{a.get('first_name','')} {a.get('last_name','')}".strip(),
            "Period Name": "Session",
            "Date": pd.Timestamp.now().normalize(),
            "Activity Name": a.get("activity_name", str(activity_id)),
            "Position Name": a.get("position_name", ""),
            "Total Distance": s.get("total_distance", 0),
            "Metros recorridos por minuto jugado": s.get("meterage_per_minute", 0),
            "Accel&Decel Efforts": (s.get("acceleration_count", 0) or 0) + (s.get("deceleration_count", 0) or 0),
            "High Speed Distance": s.get("high_speed_distance", 0),
            "Sprint Efforts": s.get("sprint_efforts", 0),
            "Maximum Velocity": s.get("max_velocity", 0),
            "Total Player Load": s.get("total_player_load", 0),
        })
    return pd.DataFrame(rows)
