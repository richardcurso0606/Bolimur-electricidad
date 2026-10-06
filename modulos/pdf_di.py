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

class NumberedCanvasDI(canvas.Canvas):
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
        
        if self._pageNumber > 1:
            self.drawString(1.5*cm, 28.3*cm, "BOLIMUR REBT | Memoria Técnica de Derivación Individual")
            self.drawRightString(19.5*cm, 28.3*cm, "ITC-BT-15")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5*cm, 28.1*cm, 19.5*cm, 28.1*cm)

        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.9*cm, page_text)
        self.drawString(1.5*cm, 0.9*cm, "Bolimur Software ElectroTécnico - Conforme a RD 842/2002 REBT ITC-BT-15")
        self.restoreState()


def _obtener_logo_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    posibles = [
        os.path.join(base_dir, "logo_bolimur.PNG"),
        os.path.join(base_dir, "logo_bolimur.png"),
        os.path.join(base_dir, "icono_bolimur.png"),
        os.path.join(os.getcwd(), "logo_bolimur.PNG"),
        os.path.join(os.getcwd(), "logo_bolimur.png"),
        os.path.join(os.getcwd(), "icono_bolimur.png"),
        "logo_bolimur.PNG",
        "icono_bolimur.png",
    ]
    for p in posibles:
        if p and os.path.exists(p):
            return p
    return None


def _crear_logo_flowable(width=5.6*cm, height=3.1*cm):
    path = _obtener_logo_path()
    if path:
        try:
            return Image(path, width=width, height=height)
        except Exception:
            pass
    return None


def generar_pdf_di(proyecto_info, di_params, di_results):
    """
    Genera un informe técnico PDF profesional para el módulo Derivación Individual (ITC-BT-15).
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

    styles = getSampleStyleSheet()
    
    c_primary = colors.HexColor("#0f172a")
    c_secondary = colors.HexColor("#0284c7")
    c_accent = colors.HexColor("#0369a1")
    c_bg_light = colors.HexColor("#f8fafc")
    c_bg_box = colors.HexColor("#f0f9ff")
    c_border = colors.HexColor("#cbd5e1")
    c_text_dark = colors.HexColor("#1e293b")

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=17, leading=21,
        textColor=c_primary, spaceAfter=3
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=12,
        textColor=c_secondary, spaceAfter=10
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, leading=14,
        textColor=c_primary, spaceBefore=12, spaceAfter=5, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=11.5,
        textColor=c_text_dark
    )
    formula_style = ParagraphStyle(
        'Formula_Text', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=8.5, leading=11.5,
        textColor=colors.HexColor("#0c4a6e")
    )
    th_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=colors.white, alignment=1
    )
    td_style = ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10,
        textColor=c_text_dark, alignment=0
    )
    td_center = ParagraphStyle('TableCellCenter', parent=td_style, alignment=1)

    story = []

    # Cabecera con Logo BOLIMUR
    text_col = [
        Paragraph("MEMORIA DE CÁLCULO: DERIVACIÓN INDIVIDUAL (DI)", title_style),
        Paragraph("CÁLCULO Y VERIFICACIÓN SEGÚN ITC-BT-15 E ITC-BT-22 DEL REBT", subtitle_style)
    ]

    logo_img = _crear_logo_flowable(width=5.6*cm, height=3.1*cm)
    if logo_img:
        header_table = Table([[text_col, logo_img]], colWidths=[12.4*cm, 5.6*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
    else:
        story.extend(text_col)

    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=2, spaceAfter=8))

    # Metadatos
    fecha_str = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    meta_table_data = [
        [
            Paragraph("<b>Proyecto / Obra:</b>", body_style),
            Paragraph(str(proyecto_info.get("nombre", "Vivienda Unifamiliar")), body_style),
            Paragraph("<b>Fecha:</b>", body_style),
            Paragraph(fecha_str, body_style)
        ],
        [
            Paragraph("<b>Emplazamiento:</b>", body_style),
            Paragraph(str(proyecto_info.get("emplazamiento", "Ubicación General")), body_style),
            Paragraph("<b>Expediente / Ref:</b>", body_style),
            Paragraph(str(proyecto_info.get("expediente", "EXP-DI-2026")), body_style)
        ],
        [
            Paragraph("<b>Proyectista / Técnico:</b>", body_style),
            Paragraph(str(proyecto_info.get("proyectista", "Técnico Instalador REBT")), body_style),
            Paragraph("<b>Normativa Base:</b>", body_style),
            Paragraph("ITC-BT-15 / CPR ES07Z1-K", body_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[3.5*cm, 6.5*cm, 3.5*cm, 4.5*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Cuadro Resumen Ejecutivo KPI
    pot_w = float(di_params.get("pot", 5750.0))
    s_fin = di_results.get("s_final", 10)
    in_iga = di_results.get("in_iga", 25)
    dv_pct = di_results.get("dv_real_pct", 0.0)
    tubo = di_results.get("tubo_diam", "Ø 32 mm")

    resumen_title = Paragraph("<b>SECCIÓN ÓPTIMA DI DIMENSIONADA:</b>", ParagraphStyle('ResTitle', parent=body_style, fontSize=11, textColor=c_primary, fontName='Helvetica-Bold'))
    resumen_val = Paragraph(f"<b>{s_fin} mm² (Cobre CPR)</b>", ParagraphStyle('ResVal', parent=body_style, fontSize=14, textColor=c_accent, fontName='Helvetica-Bold', alignment=2))

    desglose_resumen = Paragraph(
        f"<b>Resultados Clave de Diseño DI:</b><br/>"
        f"• Potencia Prevista: <b>{pot_w:,.1f} W ({pot_w/1000:.2f} kW)</b> | "
        f"• Suministro: <b>{di_params.get('suministro', 'Monofásico (230V)')}</b><br/>"
        f"• Protección IGA Recomendada: <b>{in_iga} A (Curva C)</b> | "
        f"• Caída de Tensión Real: <b>{dv_pct:.3f}%</b> (Límite normativo 1,0% / 1,5%)<br/>"
        f"• Tubo Protector Mínimo: <b>{tubo}</b> (Con reserva reglamentaria del 100% - ITC-BT-15)",
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
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(resumen_box)
    story.append(Spacer(1, 8))

    # Parámetros de Entrada
    story.append(Paragraph("1. Parámetros de Partida y Especificación de la DI", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=5))

    params_table_data = [
        [
            Paragraph("<b>Potencia Contratada / Cálculo:</b>", body_style),
            Paragraph(f"{pot_w:,.1f} W", body_style),
            Paragraph("<b>Tensión Nominal:</b>", body_style),
            Paragraph(str(di_params.get("suministro", "Monofásico (230 V)")), body_style)
        ],
        [
            Paragraph("<b>Longitud de la DI (L):</b>", body_style),
            Paragraph(f"{di_params.get('long', 0.0)} m", body_style),
            Paragraph("<b>Factor de Potencia (cos φ):</b>", body_style),
            Paragraph("1.00", body_style)
        ],
        [
            Paragraph("<b>Material Conductor:</b>", body_style),
            Paragraph("Cobre (Cu)", body_style),
            Paragraph("<b>Tipo de Aislamiento / Seguridad:</b>", body_style),
            Paragraph(str(di_params.get("aisl", "")), body_style)
        ],
        [
            Paragraph("<b>Método de Instalación:</b>", body_style),
            Paragraph(str(di_params.get("metodo", "")), body_style),
            Paragraph("<b>Reacción al Fuego (CPR):</b>", body_style),
            Paragraph("Cca-s1b,d1,a1 (Libre de Halógenos)", body_style)
        ]
    ]

    params_table = Table(params_table_data, colWidths=[4.0*cm, 5.0*cm, 4.5*cm, 4.5*cm])
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(params_table)
    story.append(Spacer(1, 8))

    # Desarrollo Analítico
    story.append(Paragraph("2. Desarrollo Analítico y Fórmulas Reglamentarias (ITC-BT-15)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=5))

    ib_val = di_results.get('ib', 0.0)
    s_cdt = di_results.get('s_cdt', 0.0)
    dv_max_v = di_results.get('dv_max', 2.3)
    gamma_val = di_results.get('gamma', 56.0)
    es_trif = di_params.get('es_trifasico', False)

    if es_trif:
        ib_expr = f"P / (√3 · 400 · 1.0) = {pot_w:,.1f} / 692.82 = <b>{ib_val:.2f} A</b>"
        s_expr = f"(P · L) / (γ · ΔV · 400) = ({pot_w:,.1f} · {di_params.get('long', 0.0)}) / ({gamma_val} · {dv_max_v:.2f} · 400) = <b>{s_cdt:.2f} mm²</b>"
    else:
        ib_expr = f"P / (230 · 1.0) = {pot_w:,.1f} / 230 = <b>{ib_val:.2f} A</b>"
        s_expr = f"(2 · P · L) / (γ · ΔV · 230) = (2 · {pot_w:,.1f} · {di_params.get('long', 0.0)}) / ({gamma_val} · {dv_max_v:.2f} · 230) = <b>{s_cdt:.2f} mm²</b>"

    just_di_text = (
        f"<b>a) Intensidad de Diseño:</b><br/>"
        f"<i>I<sub>b</sub></i> = {ib_expr}<br/><br/>"
        f"<b>b) Sección Mínima por Caída de Tensión (ΔV = {di_params.get('dv_pct', 1.0)}% = {dv_max_v:.2f} V):</b><br/>"
        f"<i>S<sub>cdt</sub></i> = {s_expr}<br/><br/>"
        f"<b>c) Cortocircuito e IGA Recomendado:</b><br/>"
        f"I<sub>cc,final</sub> = {di_results.get('icc_fin', 0.0):.1f} A. IGA seleccionado: <b>{in_iga} A (Curva C)</b> con umbral magnético de {di_results.get('umbral_mag', 0.0):.1f} A."
    )

    just_box = Table([[Paragraph(just_di_text, formula_style)]], colWidths=[18.0*cm])
    just_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 0.5, c_secondary),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(just_box)
    story.append(Spacer(1, 8))

    # Tabla Secciones
    story.append(Paragraph("3. Tabla de Verificación de Secciones Comerciales (DI)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=5))

    table_sec_header = [
        Paragraph("Sección Comercial", th_style),
        Paragraph("I<sub>z</sub> Admisible (A)", th_style),
        Paragraph("CDT Real (%)", th_style),
        Paragraph("Estado de Verificación (I<sub>n</sub> ≤ I<sub>z</sub>)", th_style)
    ]
    table_sec_rows = [table_sec_header]

    for item in di_results.get("tabla_secciones", []):
        s_c = item.get("sec", 0)
        iz_c = item.get("iz", 0)
        cdt_c = item.get("cdt", 0.0)
        est_c = item.get("estado", "")
        
        is_selected = (s_c == s_fin)
        cell_font = ParagraphStyle('CF', parent=td_style, fontName='Helvetica-Bold' if is_selected else 'Helvetica')
        
        table_sec_rows.append([
            Paragraph(f"{s_c} mm²", cell_font),
            Paragraph(f"{iz_c} A", td_center),
            Paragraph(f"{cdt_c:.3f}%", td_center),
            Paragraph(est_c, td_style)
        ])

    t_sec = Table(table_sec_rows, colWidths=[4.0*cm, 3.5*cm, 3.5*cm, 7.0*cm])
    t_sec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_sec)
    story.append(Spacer(1, 10))

    # Validación y Firma
    firma_block = [
        Paragraph("<b>CONFORMIDAD Y VALIDACIÓN TÉCNICA DI</b>", ParagraphStyle('FirmaTit', parent=body_style, fontName='Helvetica-Bold', fontSize=9.5, textColor=c_primary)),
        Spacer(1, 3),
        Paragraph("El dimensionamiento de la Derivación Individual cumple con la ITC-BT-15 del REBT. Se prescribe cableado unipolar con aislamiento termoplástico/termoestable ignífugo libre de halógenos (CPR) y tubo protector normalizado.", body_style),
        Spacer(1, 18),
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

    doc.build(story, canvasmaker=NumberedCanvasDI)
    return buffer.getvalue()
