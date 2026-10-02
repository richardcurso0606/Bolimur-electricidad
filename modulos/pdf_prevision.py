# -*- coding: utf-8 -*-
import io
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Canvas personalizado para numeración de páginas dinámica ('Página X de Y')
    y cabecera/pie de página reglamentarios.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Cabecera para páginas posteriores a la 1
        if self._pageNumber > 1:
            self.drawString(1.5*cm, 28.3*cm, "BOLIMUR REBT | Memoria Técnica de Previsión de Cargas")
            self.drawRightString(19.5*cm, 28.3*cm, "ITC-BT-10 e ITC-BT-52")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5*cm, 28.1*cm, 19.5*cm, 28.1*cm)

        # Pie de página para todas las páginas
        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.9*cm, page_text)
        self.drawString(1.5*cm, 0.9*cm, "Bolimur Software ElectroTécnico - Conforme a RD 842/2002 REBT")
        self.restoreState()


def generar_pdf_prevision(
    proyecto_info,
    grupos_viviendas,
    k_diurno,
    viviendas_diurnas_qty,
    pot_total_viviendas,
    locales,
    pot_total_locales,
    servicios_generales,
    pot_total_servicios,
    garajes,
    p_gar_base,
    p_irve,
    pot_total_garaje,
    pt_total
):
    """
    Genera un informe PDF técnico y profesional de la Previsión de Cargas.
    Devuelve los bytes del PDF en un io.BytesIO.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.8*cm,
        bottomMargin=1.8*cm
    )

    # Estilos Base
    styles = getSampleStyleSheet()
    
    # Paleta de colores
    c_primary = colors.HexColor("#0f172a")      # Azul Oscuro / Slate 900
    c_secondary = colors.HexColor("#0284c7")    # Azul Sky 600
    c_accent = colors.HexColor("#0369a1")       # Sky 700
    c_bg_light = colors.HexColor("#f8fafc")     # Slate 50
    c_bg_box = colors.HexColor("#f0f9ff")       # Sky 50
    c_border = colors.HexColor("#cbd5e1")       # Slate 300
    c_text_dark = colors.HexColor("#1e293b")    # Slate 800

    # Definición de estilos tipográficos
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=c_secondary,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=c_text_dark
    )

    body_bold = ParagraphStyle(
        'Body_Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    formula_style = ParagraphStyle(
        'Formula_Text',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0c4a6e")
    )

    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1 # Centrado
    )

    td_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=c_text_dark,
        alignment=0 # Izquierda
    )

    td_center = ParagraphStyle(
        'TableCellCenter',
        parent=td_style,
        alignment=1
    )

    td_right = ParagraphStyle(
        'TableCellRight',
        parent=td_style,
        alignment=2
    )

    td_right_bold = ParagraphStyle(
        'TableCellRightBold',
        parent=td_style,
        fontName='Helvetica-Bold',
        alignment=2
    )

    story = []

    # -------------------------------------------------------------------------
    # CABECERA Y LOGO
    # -------------------------------------------------------------------------
    logo_path = "logo_bolimur.PNG"
    if not os.path.exists(logo_path):
        logo_path = "icono_bolimur.png"
    
    header_data = []
    text_col = [
        Paragraph("MEMORIA DE CÁLCULO: PREVISIÓN DE CARGAS", title_style),
        Paragraph("REGLAMENTO ELECTROTÉCNICO PARA BAJA TENSIÓN (ITC-BT-10 / ITC-BT-52)", subtitle_style)
    ]

    if os.path.exists(logo_path):
        try:
            # Mantener proporción aproximada
            img = Image(logo_path, width=4.0*cm, height=2.67*cm)
            header_table = Table([[text_col, img]], colWidths=[13.5*cm, 4.5*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(header_table)
        except Exception:
            story.extend(text_col)
    else:
        story.extend(text_col)

    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=4, spaceAfter=10))

    # -------------------------------------------------------------------------
    # DATOS DEL PROYECTO
    # -------------------------------------------------------------------------
    fecha_str = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    meta_table_data = [
        [
            Paragraph("<b>Proyecto / Obra:</b>", body_style),
            Paragraph(str(proyecto_info.get("nombre", "Edificio Residencial")), body_style),
            Paragraph("<b>Fecha:</b>", body_style),
            Paragraph(fecha_str, body_style)
        ],
        [
            Paragraph("<b>Emplazamiento:</b>", body_style),
            Paragraph(str(proyecto_info.get("emplazamiento", "Ubicación General")), body_style),
            Paragraph("<b>Expediente / Ref:</b>", body_style),
            Paragraph(str(proyecto_info.get("expediente", "EXP-2026-001")), body_style)
        ],
        [
            Paragraph("<b>Proyectista / Técnico:</b>", body_style),
            Paragraph(str(proyecto_info.get("proyectista", "Técnico Instalador REBT")), body_style),
            Paragraph("<b>Normativa:</b>", body_style),
            Paragraph("RD 842/2002 REBT", body_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[3.5*cm, 6.5*cm, 3.5*cm, 4.5*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # CUADRO RESUMEN EJECUTIVO (KPI)
    # -------------------------------------------------------------------------
    pt_kw = pt_total / 1000.0
    resumen_title = Paragraph(f"<b>POTENCIA TOTAL PREVISTA DEL EDIFICIO (P<sub>t</sub>):</b>", ParagraphStyle('ResTitle', parent=body_style, fontSize=11, textColor=c_primary, fontName='Helvetica-Bold'))
    resumen_val = Paragraph(f"<b>{pt_total:,.2f} W  ({pt_kw:.2f} kW)</b>", ParagraphStyle('ResVal', parent=body_style, fontSize=14, textColor=c_accent, fontName='Helvetica-Bold', alignment=2))

    desglose_resumen = Paragraph(
        f"<b>Desglose por Servicios:</b><br/>"
        f"• 🏠 Viviendas (P<sub>1</sub>): <b>{pot_total_viviendas:,} W</b> | "
        f"• 🏪 Locales Comerciales (P<sub>2</sub>): <b>{pot_total_locales:,.0f} W</b><br/>"
        f"• 💡 Servicios Generales (P<sub>3</sub>): <b>{pot_total_servicios:,.2f} W</b> | "
        f"• 🚗 Garajes e IRVE (P<sub>4</sub>): <b>{pot_total_garaje:,.2f} W</b>",
        body_style
    )

    resumen_box_data = [
        [resumen_title, resumen_val],
        [desglose_resumen, ""]
    ]

    resumen_box = Table(resumen_box_data, colWidths=[11.5*cm, 6.5*cm])
    resumen_box.setStyle(TableStyle([
        ('SPAN', (0,1), (1,1)),
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 1.5, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(resumen_box)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECCIÓN 1: VIVIENDAS (P1)
    # -------------------------------------------------------------------------
    story.append(Paragraph("1. Previsión de Carga para Viviendas (P<sub>1</sub> - ITC-BT-10)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=6))

    table_viv_header = [
        Paragraph("Grupo / Descripción", th_style),
        Paragraph("Nº Viv.", th_style),
        Paragraph("Pot. Unitaria (W)", th_style),
        Paragraph("Tarifa Nocturna", th_style),
        Paragraph("Subtotal Calculado (W)", th_style)
    ]
    table_viv_rows = [table_viv_header]

    for g in grupos_viviendas:
        table_viv_rows.append([
            Paragraph(str(g.get("nombre", "")), td_style),
            Paragraph(str(g.get("qty", 0)), td_center),
            Paragraph(f"{g.get('pot', 0):,} W", td_center),
            Paragraph("Sí (100%)" if g.get("nocturna") else "No", td_center),
            Paragraph(f"{g.get('pot_calculada', 0):,} W", td_right)
        ])

    table_viv_rows.append([
        Paragraph("<b>SUBTOTAL VIVIENDAS (P<sub>1</sub>)</b>", ParagraphStyle('SubViv', parent=td_style, fontName='Helvetica-Bold')),
        "", "", "",
        Paragraph(f"<b>{pot_total_viviendas:,} W</b>", td_right_bold)
    ])

    t_viv = Table(table_viv_rows, colWidths=[6.5*cm, 2.0*cm, 3.0*cm, 3.0*cm, 3.5*cm])
    t_viv.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('SPAN', (0, -1), (3, -1)),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_viv)
    story.append(Spacer(1, 6))

    # Justificación Analítica P1
    suma_bruta_diurna = sum(g["qty"] * g["pot"] for g in grupos_viviendas if not g.get("nocturna"))
    just_p1_text = (
        f"<b>Justificación Analítica REBT (ITC-BT-10):</b><br/>"
        f"• Total viviendas diurnas (n): <b>{viviendas_diurnas_qty}</b> | Coeficiente de simultaneidad de tabla (K): <b>{k_diurno}</b><br/>"
        f"• Expresión reglamentaria: <i>P<sub>1</sub> = [ Σ (n<sub>i</sub> · P<sub>u,i</sub>) ] · (K / n<sub>diurnas</sub>) + Σ P<sub>nocturnas</sub></i><br/>"
        f"• Sustitución numérica: P<sub>1</sub> = [ {suma_bruta_diurna:,} W ] · ({k_diurno} / {viviendas_diurnas_qty if viviendas_diurnas_qty > 0 else 1}) = <b>{pot_total_viviendas:,} W</b>"
    )
    p1_box = Table([[Paragraph(just_p1_text, formula_style)]], colWidths=[18.0*cm])
    p1_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 0.5, c_secondary),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(p1_box)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECCIÓN 2: LOCALES COMERCIALES (P2)
    # -------------------------------------------------------------------------
    story.append(Paragraph("2. Previsión de Carga para Locales Comerciales (P<sub>2</sub> - ITC-BT-10)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=6))

    table_loc_header = [
        Paragraph("Local / Descripción", th_style),
        Paragraph("Superficie (m²)", th_style),
        Paragraph("Cantidad", th_style),
        Paragraph("Criterio REBT Aplicado", th_style),
        Paragraph("Subtotal Calculado (W)", th_style)
    ]
    table_loc_rows = [table_loc_header]

    for loc in locales:
        sup = float(loc.get("superficie", 0.0))
        qty = int(loc.get("qty", 1))
        pot_u = max(sup * 100.0, 3450.0 if sup > 0 else 0.0)
        pot_parc = pot_u * qty
        table_loc_rows.append([
            Paragraph(str(loc.get("nombre", "")), td_style),
            Paragraph(f"{sup:,.1f} m²", td_center),
            Paragraph(str(qty), td_center),
            Paragraph(f"max({sup:,.0f}×100, 3450 W)", td_center),
            Paragraph(f"{pot_parc:,.0f} W", td_right)
        ])

    table_loc_rows.append([
        Paragraph("<b>SUBTOTAL LOCALES COMERCIALES (P<sub>2</sub>)</b>", ParagraphStyle('SubLoc', parent=td_style, fontName='Helvetica-Bold')),
        "", "", "",
        Paragraph(f"<b>{pot_total_locales:,.0f} W</b>", td_right_bold)
    ])

    t_loc = Table(table_loc_rows, colWidths=[6.0*cm, 2.5*cm, 2.0*cm, 4.0*cm, 3.5*cm])
    t_loc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('SPAN', (0, -1), (3, -1)),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_loc)
    story.append(Spacer(1, 6))

    just_p2_text = (
        "<b>Justificación Reglamentaria (ITC-BT-10):</b> Mínimo 100 W por m² de superficie construida, con un mínimo absoluto de 3.450 W por local."
    )
    p2_box = Table([[Paragraph(just_p2_text, formula_style)]], colWidths=[18.0*cm])
    p2_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 0.5, c_secondary),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(p2_box)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECCIÓN 3: SERVICIOS GENERALES (P3)
    # -------------------------------------------------------------------------
    story.append(Paragraph("3. Previsión para Servicios Generales del Edificio (P<sub>3</sub> - ITC-BT-10)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=6))

    table_serv_header = [
        Paragraph("Servicio / Equipo", th_style),
        Paragraph("Pot. Unit. (W)", th_style),
        Paragraph("Uds.", th_style),
        Paragraph("Factor (K)", th_style),
        Paragraph("cos φ", th_style),
        Paragraph("Subtotal (W)", th_style)
    ]
    table_serv_rows = [table_serv_header]

    for serv in servicios_generales:
        pot_u = float(serv.get("potencia", 0.0))
        qty = int(serv.get("qty", 1))
        f_k = float(serv.get("factor", 1.30))
        c_phi = float(serv.get("cos_phi", 1.0))
        if f_k == 1.80 and c_phi < 1.0:
            p_parc = pot_u * qty * f_k * c_phi
        else:
            p_parc = pot_u * qty * f_k

        table_serv_rows.append([
            Paragraph(str(serv.get("nombre", "")), td_style),
            Paragraph(f"{pot_u:,.0f} W", td_center),
            Paragraph(str(qty), td_center),
            Paragraph(f"{f_k:.2f}", td_center),
            Paragraph(f"{c_phi:.2f}", td_center),
            Paragraph(f"{p_parc:,.2f} W", td_right)
        ])

    table_serv_rows.append([
        Paragraph("<b>SUBTOTAL SERVICIOS GENERALES (P<sub>3</sub>)</b>", ParagraphStyle('SubServ', parent=td_style, fontName='Helvetica-Bold')),
        "", "", "", "",
        Paragraph(f"<b>{pot_total_servicios:,.2f} W</b>", td_right_bold)
    ])

    t_serv = Table(table_serv_rows, colWidths=[6.5*cm, 2.5*cm, 1.5*cm, 2.0*cm, 2.0*cm, 3.5*cm])
    t_serv.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('SPAN', (0, -1), (4, -1)),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_serv)
    story.append(Spacer(1, 6))

    just_p3_text = (
        "<b>Expresión Aplicada:</b> <i>P<sub>servicio</sub> = P<sub>unitaria</sub> · Uds · K · (cos φ)</i>. "
        "Se aplican coeficientes K reglamentarios: Ascensores/Motores K=1,30; Bombas K=1,25; Lámparas de descarga K=1,80."
    )
    p3_box = Table([[Paragraph(just_p3_text, formula_style)]], colWidths=[18.0*cm])
    p3_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 0.5, c_secondary),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(p3_box)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------------------
    # SECCIÓN 4: GARAJES E IRVE (P4)
    # -------------------------------------------------------------------------
    story.append(Paragraph("4. Previsión para Garajes e Infraestructura IRVE (P<sub>4</sub> - ITC-BT-10 e ITC-BT-52)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=6))

    esquema_irve_str = str(garajes.get("esquema_irve", "Esquema 3a"))
    spl_activo = bool(garajes.get("spl", False))
    factor_irve_pct = "5% (Con Control Dinámico SPL)" if spl_activo else "10% (Sin SPL)"
    sup_g = float(garajes.get("sup", 0.0))
    plazas_g = int(garajes.get("plazas_irve", 0))

    table_gar_data = [
        [
            Paragraph("<b>Superficie Garaje:</b>", body_style),
            Paragraph(f"{sup_g:,.1f} m²", body_style),
            Paragraph("<b>Potencia Base Garaje:</b>", body_style),
            Paragraph(f"{p_gar_base:,.0f} W", body_style)
        ],
        [
            Paragraph("<b>Plazas Totales IRVE:</b>", body_style),
            Paragraph(f"{plazas_g} plazas", body_style),
            Paragraph("<b>Factor Simultaneidad IRVE:</b>", body_style),
            Paragraph(factor_irve_pct, body_style)
        ],
        [
            Paragraph("<b>Esquema ITC-BT-52:</b>", body_style),
            Paragraph(esquema_irve_str, body_style),
            Paragraph("<b>Potencia Recarga (P<sub>IRVE</sub>):</b>", body_style),
            Paragraph(f"{p_irve:,.2f} W", body_style)
        ],
        [
            Paragraph("<b>SUBTOTAL GARAJE E IRVE (P<sub>4</sub>):</b>", ParagraphStyle('SubGarTitle', parent=body_style, fontName='Helvetica-Bold')),
            Paragraph(f"<b>{pot_total_garaje:,.2f} W</b>", ParagraphStyle('SubGarVal', parent=body_style, fontName='Helvetica-Bold', textColor=c_accent)),
            "", ""
        ]
    ]

    t_gar = Table(table_gar_data, colWidths=[4.0*cm, 5.0*cm, 4.5*cm, 4.5*cm])
    t_gar.setStyle(TableStyle([
        ('SPAN', (0, 3), (1, 3)),
        ('BACKGROUND', (0,0), (-1,-2), colors.white),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#e2e8f0")),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_gar)
    story.append(Spacer(1, 6))

    just_p4_text = (
        f"<b>Justificación ITC-BT-52 / ITC-BT-10:</b> P<sub>base</sub> = max(Superficie · ratio W/m², 3.450 W). "
        f"P<sub>IRVE</sub> = Plazas · Factor_simultaneidad · 3.680 W. "
        f"P<sub>4</sub> = P<sub>base</sub> ({p_gar_base:,.0f} W) + P<sub>IRVE</sub> ({p_irve:,.2f} W) = <b>{pot_total_garaje:,.2f} W</b>."
    )
    p4_box = Table([[Paragraph(just_p4_text, formula_style)]], colWidths=[18.0*cm])
    p4_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 0.5, c_secondary),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(p4_box)
    story.append(Spacer(1, 14))

    # -------------------------------------------------------------------------
    # VALIDACIÓN Y FIRMA TÉCNICA
    # -------------------------------------------------------------------------
    firma_block = [
        Paragraph("<b>CONFORMIDAD Y VALIDACIÓN TÉCNICA</b>", ParagraphStyle('FirmaTit', parent=body_style, fontName='Helvetica-Bold', fontSize=10, textColor=c_primary)),
        Spacer(1, 4),
        Paragraph("El presente cálculo de previsión de cargas ha sido desarrollado en estricto cumplimiento de las Instrucciones Técnicas Complementarias del REBT (ITC-BT-10 e ITC-BT-52) para su integración en el proyecto general del edificio.", body_style),
        Spacer(1, 20),
        Table([
            [
                Paragraph("<b>Firma del Técnico Proyectista:</b><br/><br/><br/>________________________________________<br/>" + str(proyecto_info.get("proyectista", "Instalador Autorizado REBT")), body_style),
                Paragraph("<b>Sello / Validación Oficial:</b><br/><br/><br/>________________________________________<br/>Fecha: " + fecha_str, body_style)
            ]
        ], colWidths=[9.0*cm, 9.0*cm], style=[
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ])
    ]

    story.append(KeepTogether(firma_block))

    # Construir PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
