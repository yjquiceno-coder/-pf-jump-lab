"""Análisis narrativo — PF Jump Lab.
Usa la API de Claude (Anthropic) para redactar el análisis del entrenamiento.
Si no hay ANTHROPIC_API_KEY definida, usa un análisis basado en reglas (mismas métricas)."""
import os, json

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")

SYSTEM = (
    "Eres un preparador físico de élite del fútbol profesional. Redactas en español, "
    "tono técnico pero claro para el cuerpo técnico. A partir de los datos GPS/Catapult de la "
    "sesión, escribe un análisis breve (3-4 párrafos) que incluya: (1) lectura general de la carga "
    "del equipo, (2) jugadores en riesgo por ACWR alto o subcarga marcada y recomendación, "
    "(3) sugerencia de manejo para la próxima sesión. No inventes datos fuera de los entregados."
)


def ai_narrative(result):
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return _rule_based(result)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        payload = {"equipo": result["team"],
                   "jugadores": result["players"],
                   "en_riesgo": [p["jugador"] for p in result["riesgo"]],
                   "subcarga": [p["jugador"] for p in result["subcarga"]]}
        msg = client.messages.create(
            model=MODEL, max_tokens=900, system=SYSTEM,
            messages=[{"role": "user",
                       "content": "Datos de la sesión (JSON):\n" + json.dumps(payload, ensure_ascii=False)}])
        return "".join(b.text for b in msg.content if b.type == "text").strip()
    except Exception as e:
        return _rule_based(result) + f"\n\n(Nota: análisis generado en modo local; IA no disponible: {e})"


def _rule_based(result):
    t = result["team"]
    riesgo = result["riesgo"]; sub = result["subcarga"]
    p1 = (f"La sesión <b>{t['sesion']}</b> ({t['fecha']}) registró {t['n_jugadores']} jugadores "
          f"con un Player Load promedio de <b>{int(t['load_prom'])}</b> (máximo {int(t['load_max'])}), "
          f"distancia media de <b>{int(t['dist_prom'])} m</b> y {int(t['hsr_prom'])} m de alta velocidad "
          f"por jugador, con {t['sprints_tot']} sprints totales. Es una carga "
          + ("alta" if t['load_prom'] > 450 else "moderada" if t['load_prom'] > 300 else "baja-regenerativa")
          + " a nivel de grupo.")

    if riesgo:
        nombres = ", ".join(f"{p['jugador'].title()} (ACWR {p['acwr']}, {p['zona']})" for p in riesgo)
        p2 = (f"<b>Atención individual:</b> {nombres}. Estos jugadores presentan un ratio agudo:crónico "
              "por encima del rango óptimo (&gt;1.30), lo que se asocia a mayor riesgo lesional. Se "
              "recomienda modular su volumen en las próximas 48–72 h, priorizar recuperación activa y "
              "revisar percepción de esfuerzo (RPE) y marcadores de fatiga.")
    else:
        p2 = ("<b>Atención individual:</b> ningún jugador supera el umbral de riesgo de ACWR (&gt;1.30) "
              "en esta sesión. El grupo se mantiene dentro de rangos controlados.")

    if sub:
        nombres = ", ".join(p["jugador"].title() for p in sub[:6])
        p3 = (f"<b>Subcarga:</b> {nombres} muestran ACWR &lt;0.80, indicando estímulo por debajo de su "
              "media crónica (posible reintegro, rotación o minutos reducidos). Conviene progresar su "
              "carga gradualmente para evitar el efecto rebote al volver a competir.")
    else:
        p3 = "<b>Subcarga:</b> sin casos relevantes de descarga marcada en el grupo evaluado."

    p4 = ("<b>Recomendación próxima sesión:</b> ajustar el diseño de tareas para acercar a los jugadores "
          "subcargados a su rango óptimo y aliviar a los señalados en precaución/riesgo, manteniendo el "
          "estímulo de alta velocidad del bloque competitivo. Reevaluar ACWR tras la siguiente sesión.")
    return "\n\n".join([p1, p2, p3, p4])
