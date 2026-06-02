"""Generador de informe PDF — PF Jump Lab / Patriotas Boyacá."""
import os, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

ROJO = colors.HexColor("#D11E2A")
VERDE = colors.HexColor("#0E8A3C")
TINTA = colors.HexColor("#15171C")
GRIS = colors.HexColor("#6B7280")
ZONE_BG = {"red": colors.HexColor("#FCE4E6"), "amber": colors.HexColor("#FEF3D7"),
           "green": colors.HexColor("#E3F5E9"), "blue": colors.HexColor("#E4ECFB"),
           "gray": colors.HexColor("#EFEFEF")}
ZONE_TX = {"red": ROJO, "amber": colors.HexColor("#9A6700"), "green": VERDE,
           "blue": colors.HexColor("#1F4FB0"), "gray": GRIS}


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("H1", parent=s["Title"], textColor=TINTA, fontSize=20, spaceAfter=2))
    s.add(ParagraphStyle("Sub", parent=s["Normal"], textColor=GRIS, fontSize=10, alignment=TA_CENTER))
    s.add(ParagraphStyle("H2", parent=s["Heading2"], textColor=ROJO, fontSize=12, spaceBefore=10, spaceAfter=4))
    s.add(ParagraphStyle("Body", parent=s["Normal"], fontSize=9.5, leading=14, textColor=TINTA))
    s.add(ParagraphStyle("Small", parent=s["Normal"], fontSize=7.5, textColor=GRIS))
    return s


def build_pdf(result, narrative, out_path, logo_path=None):
    S = _styles()
    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=16*mm, bottomMargin=14*mm,
                            leftMargin=15*mm, rightMargin=15*mm)
    story, t = [], result["team"]

    # Encabezado
    head = []
    if logo_path and os.path.exists(logo_path):
        head.append(Image(logo_path, width=20*mm, height=20*mm))
    title = [Paragraph("INFORME AUTOMÁTICO DE CARGA", S["H1"]),
             Paragraph(f"Patriotas Boyacá S.A. · {t['sesion']} · {t['fecha']}", S["Sub"])]
    if head:
        story.append(Table([[head[0], title]], colWidths=[22*mm, None],
                     style=[("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    else:
        story += title
    story.append(HRFlowable(width="100%", thickness=2, color=ROJO, spaceBefore=6, spaceAfter=8))

    # KPIs de equipo
    def kpi(lbl, val):
        return [Paragraph(f"<b>{val}</b>", ParagraphStyle("k", fontSize=15, textColor=ROJO, alignment=TA_CENTER)),
                Paragraph(lbl, S["Small"])]
    kpis = [kpi("Jugadores", t["n_jugadores"]), kpi("PL prom.", t["load_prom"]),
            kpi("PL máx.", t["load_max"]), kpi("Dist. prom (m)", t["dist_prom"]),
            kpi("HSR prom (m)", t["hsr_prom"]), kpi("Sprints", t["sprints_tot"])]
    row1 = [k[0] for k in kpis]; row2 = [k[1] for k in kpis]
    kt = Table([[k[1] for k in kpis],[k[0] for k in kpis]], colWidths=[None]*6)
    kt.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#E0E0E0")),
        ("INNERGRID",(0,0),(-1,-1),0.5,colors.HexColor("#E0E0E0")),("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story += [kt, Spacer(1, 8)]

    # Análisis IA
    story.append(Paragraph("ANÁLISIS DEL ENTRENAMIENTO", S["H2"]))
    for para in narrative.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip().replace("\n", "<br/>"), S["Body"]))
            story.append(Spacer(1, 3))

    # Tabla por jugador
    story.append(Paragraph("DETALLE POR JUGADOR (ordenado por Player Load)", S["H2"]))
    header = ["Jugador", "Pos.", "Dist (m)", "m/min", "PL", "HSR", "Spr", "A+D", "Vmáx", "ACWR", "Zona"]
    data = [header]
    for p in result["players"]:
        data.append([p["jugador"].title(), p["posicion"][:8], int(p["distancia"]), int(p["m_min"]),
                     int(p["player_load"]), int(p["hsr"]), p["sprints"], p["accel_decel"],
                     p["vmax"], p["acwr"] if p["acwr"] is not None else "—", p["zona"]])
    tbl = Table(data, repeatRows=1, colWidths=[34*mm,16*mm,15*mm,12*mm,11*mm,12*mm,9*mm,9*mm,12*mm,12*mm,20*mm])
    style = [("BACKGROUND",(0,0),(-1,0),TINTA),("TEXTCOLOR",(0,0),(-1,0),colors.white),
             ("FONTSIZE",(0,0),(-1,-1),7),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
             ("ALIGN",(2,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
             ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#F7F7F7")]),
             ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#DADADA")),("TOPPADDING",(0,0),(-1,-1),3),
             ("BOTTOMPADDING",(0,0),(-1,-1),3)]
    for i, p in enumerate(result["players"], start=1):
        style.append(("BACKGROUND",(10,i),(10,i), ZONE_BG[p["color"]]))
        style.append(("TEXTCOLOR",(10,i),(10,i), ZONE_TX[p["color"]]))
    tbl.setStyle(TableStyle(style))
    story += [tbl, Spacer(1, 6)]

    story.append(Paragraph(
        "<b>ACWR</b> (Acute:Chronic Workload Ratio) — &lt;0.80 Subcarga · 0.80–1.30 Óptimo · "
        "1.31–1.50 Precaución · &gt;1.50 Riesgo alto. PL = Player Load · HSR = dist. alta velocidad · "
        "A+D = esfuerzos de aceleración/desaceleración.", S["Small"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
    story.append(Paragraph(
        f"Generado automáticamente por PF Jump Lab · {datetime.datetime.now():%Y-%m-%d %H:%M} · "
        "Por la gloria.", S["Small"]))
    doc.build(story)
    return out_path
