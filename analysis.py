"""Envío del informe PDF al cuerpo técnico por correo (SMTP)."""
import os, smtplib, logging
from email.message import EmailMessage

log = logging.getLogger("pf-jump-lab.mailer")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")          # contraseña de aplicación
MAIL_FROM = os.getenv("MAIL_FROM", SMTP_USER)
MAIL_TO   = [x.strip() for x in os.getenv("MAIL_TO", "").split(",") if x.strip()]


def send_report(pdf_path, result):
    if not (SMTP_USER and SMTP_PASS and MAIL_TO):
        log.warning("SMTP no configurado; informe NO enviado. PDF en: %s", pdf_path)
        return
    t = result["team"]
    riesgo = ", ".join(p["jugador"].title() for p in result["riesgo"]) or "ninguno"
    msg = EmailMessage()
    msg["Subject"] = f"Informe de carga · {t['sesion']} · {t['fecha']}"
    msg["From"] = MAIL_FROM
    msg["To"] = ", ".join(MAIL_TO)
    msg.set_content(
        f"Adjunto el informe automático de la sesión {t['sesion']} ({t['fecha']}).\n\n"
        f"Jugadores: {t['n_jugadores']} · Player Load promedio: {int(t['load_prom'])}\n"
        f"Jugadores en precaución/riesgo (ACWR): {riesgo}\n\n"
        f"Generado por PF Jump Lab. Por la gloria.")
    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf",
                           filename=os.path.basename(pdf_path))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    log.info("Correo enviado a %s", MAIL_TO)
