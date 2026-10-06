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

class NumberedCanvasCR(canvas.Canvas):
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
            self.drawString(1.5*cm, 28.3*cm, "BOLIMUR REBT | Memoria Técnica de Cálculo Rápido Avanzado")
            self.drawRightString(19.5*cm, 28.3*cm, "UNE-HD 60364 / REBT")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5*cm, 28.1*cm, 19.5*cm, 28.1*cm)

        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.9*cm, page_text)
        self.drawString(1.5*cm, 0.9*cm, "Bolimur Software ElectroTécnico - Conforme a RD 842/2002 REBT")
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


def generar_pdf_calculo_rapido(proyecto_info, calc_params, calc_results):
    """
    Genera un informe técnico PDF profesional para el módulo Cálculo Rápido Avanzado.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.8*cm, bottomMargin=1.8*cm
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

    story = []

    text_col = [
        Paragraph("MEMORIA DE CÁLCULO: CÁLCULO RÁPIDO AVANZADO", title_style),
        Paragraph("DIMENSIONAMIENTO DE CONDUCTORES Y PROTECCIONES REBT", subtitle_style)
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

    fecha_str = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    meta_table_data = [
        [
            Paragraph("<b>Proyecto / Obra:</b>", body_style),
            Paragraph(str(proyecto_info.get("nombre", "Instalación General")), body_style),
            Paragraph("<b>Fecha:</b>", body_style),
            Paragraph(fecha_str, body_style)
        ],
        [
            Paragraph("<b>Emplazamiento:</b>", body_style),
            Paragraph(str(proyecto_info.get("emplazamiento", "Ubicación General")), body_style),
            Paragraph("<b>Expediente / Ref:</b>", body_style),
            Paragraph(str(proyecto_info.get("expediente", "EXP-CR-2026")), body_style)
        ],
        [
            Paragraph("<b>Proyectista / Técnico:</b>", body_style),
            Paragraph(str(proyecto_info.get("proyectista", "Técnico Instalador REBT")), body_style),
            Paragraph("<b>Normativa Base:</b>", body_style),
            Paragraph("UNE-HD 60364-5-52 / REBT", body_style)
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

    pot_w = float(calc_params.get("pot", 0.0))
    s_opt = calc_results.get("s_opt", 0)
    prot = calc_results.get("prot", 16)
    dv_pct = calc_results.get("dv_real_pct", 0.0)
    mat = str(calc_params.get("mat", "cobre")).upper()

    resumen_title = Paragraph("<b>SECCIÓN ÓPTIMA DIMENSIONADA:</b>", ParagraphStyle('ResTitle', parent=body_style, fontSize=11, textColor=c_primary, fontName='Helvetica-Bold'))
    resumen_val = Paragraph(f"<b>{s_opt} mm² ({mat})</b>", ParagraphStyle('ResVal', parent=body_style, fontSize=14, textColor=c_accent, fontName='Helvetica-Bold', alignment=2))

    desglose_resumen = Paragraph(
        f"<b>Resultados Clave del Cálculo Rápido:</b><br/>"
        f"• Carga Prevista: <b>{pot_w:,.1f} W</b> | "
        f"• Sistema: <b>{calc_params.get('red', 'Monofásico (230V)')}</b><br/>"
        f"• Intensidad de Diseño (I<sub>b</sub>): <b>{calc_results.get('ib', 0.0):.2f} A</b> | "
        f"• Caída Real: <b>{dv_pct:.3f}%</b> (Límite {calc_params.get('cdt_lim', 3.0)}%)<br/>"
        f"• Protección Recomendada: <b>PIA {prot} A (Curva C)</b> | "
        f"• Cortocircuito Icc Final: <b>{calc_results.get('icc_fin', 0.0)*1000:.1f} A</b>",
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

    story.append(Paragraph("1. Parámetros de Entrada", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=5))

    params_table_data = [
        [
            Paragraph("<b>Potencia de Cálculo (P):</b>", body_style),
            Paragraph(f"{pot_w:,.1f} W", body_style),
            Paragraph("<b>Sistema Eléctrico:</b>", body_style),
            Paragraph(str(calc_params.get("red", "Monofásico (230V)")), body_style)
        ],
        [
            Paragraph("<b>Longitud Circuito (L):</b>", body_style),
            Paragraph(f"{calc_params.get('long', 0.0)} m", body_style),
            Paragraph("<b>Factor de Potencia (cos φ):</b>", body_style),
            Paragraph(f"{calc_params.get('cos_phi', 0.85):.2f}", body_style)
        ],
        [
            Paragraph("<b>Material Conductor:</b>", body_style),
            Paragraph(f"{mat}", body_style),
            Paragraph("<b>Tipo de Aislamiento:</b>", body_style),
            Paragraph(str(calc_params.get("aisl", "")), body_style)
        ],
        [
            Paragraph("<b>Método de Instalación:</b>", body_style),
            Paragraph(str(calc_params.get("metodo", "")), body_style),
            Paragraph("<b>Icc en Origen:</b>", body_style),
            Paragraph(f"{calc_params.get('icc_orig', 10.0)} kA", body_style)
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

    story.append(Paragraph("2. Desarrollo Analítico del Cálculo", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=5))

    ib_v = calc_results.get('ib', 0.0)
    s_cdt = calc_results.get('s_cdt', 0.0)
    s_cal = calc_results.get('s_cal', 0.0)
    icc_fin = calc_results.get('icc_fin', 0.0) * 1000.0
    salta = calc_results.get('salta_proteccion', True)

    just_cr_text = (
        f"<b>a) Intensidad de Diseño:</b> I<sub>b</sub> = <b>{ib_v:.2f} A</b>.<br/>"
        f"<b>b) Criterio de Calentamiento:</b> Sección mínima por intensidad I<sub>z</sub> = <b>{s_cal} mm²</b> (Admite I<sub>z</sub> = {calc_results.get('iz_opt', 0)} A).<br/>"
        f"<b>c) Criterio de Caída de Tensión:</b> Sección teórica por CDT ({calc_params.get('cdt_lim', 3.0)}%) = <b>{s_cdt:.2f} mm²</b>.<br/>"
        f"<b>d) Verificación Cortocircuito (Disparo Magnético):</b> I<sub>cc,final</sub> = <b>{icc_fin:.1f} A</b>. "
        f"Umbral instantáneo de PIA {prot}A (Curva C = {prot*10}A) $\\rightarrow$ " +
        ("<b>✅ CUMPLE Y DISPARA INSTANTÁNEAMENTE</b>" if salta else "<b>⚠️ NO SALTA A TIEMPO</b>")
    )

    just_box = Table([[Paragraph(just_cr_text, formula_style)]], colWidths=[18.0*cm])
    just_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 0.5, c_secondary),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(just_box)
    story.append(Spacer(1, 10))

    firma_block = [
        Paragraph("<b>CONFORMIDAD Y VALIDACIÓN TÉCNICA</b>", ParagraphStyle('FirmaTit', parent=body_style, fontName='Helvetica-Bold', fontSize=9.5, textColor=c_primary)),
        Spacer(1, 3),
        Paragraph("El dimensionamiento del circuito se ha ejecutado conforme a la norma UNE-HD 60364-5-52 y las prescripciones técnicas del REBT.", body_style),
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

    doc.build(story, canvasmaker=NumberedCanvasCR)
    return buffer.getvalue()
