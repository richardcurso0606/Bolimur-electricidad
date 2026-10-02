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

class NumberedCanvasIRVE(canvas.Canvas):
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
            self.drawString(1.5*cm, 28.3*cm, "BOLIMUR REBT | Memoria Técnica de Infraestructura IRVE")
            self.drawRightString(19.5*cm, 28.3*cm, "ITC-BT-52")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5*cm, 28.1*cm, 19.5*cm, 28.1*cm)

        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.9*cm, page_text)
        self.drawString(1.5*cm, 0.9*cm, "Bolimur Software ElectroTécnico - Conforme a RD 842/2002 REBT ITC-BT-52")
        self.restoreState()


def generar_pdf_irve(proyecto_info, irve_params, irve_results):
    """
    Genera un informe técnico PDF profesional para el módulo IRVE (ITC-BT-52).
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

    logo_path = "logo_bolimur.PNG"
    if not os.path.exists(logo_path):
        logo_path = "icono_bolimur.png"
    
    text_col = [
        Paragraph("MEMORIA DE CÁLCULO: CIRCUITO DE RECARGA IRVE", title_style),
        Paragraph("INFRAESTRUCTURA PARA VEHÍCULOS ELÉCTRICOS SEGÚN ITC-BT-52", subtitle_style)
    ]

    if os.path.exists(logo_path):
        try:
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

    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=2, spaceAfter=8))

    fecha_str = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    meta_table_data = [
        [
            Paragraph("<b>Proyecto / Obra:</b>", body_style),
            Paragraph(str(proyecto_info.get("nombre", "Instalación IRVE")), body_style),
            Paragraph("<b>Fecha:</b>", body_style),
            Paragraph(fecha_str, body_style)
        ],
        [
            Paragraph("<b>Emplazamiento:</b>", body_style),
            Paragraph(str(proyecto_info.get("emplazamiento", "Ubicación Garaje")), body_style),
            Paragraph("<b>Expediente / Ref:</b>", body_style),
            Paragraph(str(proyecto_info.get("expediente", "EXP-IRVE-2026")), body_style)
        ],
        [
            Paragraph("<b>Proyectista / Técnico:</b>", body_style),
            Paragraph(str(proyecto_info.get("proyectista", "Técnico Instalador REBT")), body_style),
            Paragraph("<b>Normativa Base:</b>", body_style),
            Paragraph("ITC-BT-52 REBT", body_style)
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

    pot_w = float(irve_params.get("pot_wallbox", 7360.0))
    s_fin = irve_results.get("s_final", 6)
    in_pi = irve_results.get("in_pi", 32)
    dv_pct = irve_results.get("dv_real_pct", 0.0)

    resumen_title = Paragraph("<b>SECCIÓN ÓPTIMA CIRCUITO IRVE:</b>", ParagraphStyle('ResTitle', parent=body_style, fontSize=11, textColor=c_primary, fontName='Helvetica-Bold'))
    resumen_val = Paragraph(f"<b>{s_fin} mm² (Cobre RZ1-K)</b>", ParagraphStyle('ResVal', parent=body_style, fontSize=14, textColor=c_accent, fontName='Helvetica-Bold', alignment=2))

    desglose_resumen = Paragraph(
        f"<b>Resultados Clave del Circuito de Recarga:</b><br/>"
        f"• Potencia Cargador: <b>{pot_w:,.0f} W ({pot_w/1000:.2f} kW)</b> | "
        f"• Esquema ITC-BT-52: <b>{irve_params.get('esquema', 'Esquema 3a')}</b><br/>"
        f"• Intensidad (I<sub>b</sub>): <b>{irve_results.get('ib', 0.0):.2f} A</b> | "
        f"• Magnetotérmico: <b>PIA {in_pi} A (Curva C)</b><br/>"
        f"• Protección Diferencial: <b>Obligatorio Tipo A (6mA DC) o Tipo B</b> | "
        f"• Sobretensiones: <b>VSP/VTP en Origen</b><br/>"
        f"• Caída Real: <b>{dv_pct:.3f}%</b> (Límite normativo 1,0%)",
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

    story.append(Paragraph("1. Parámetros de la Instalación y Cargador", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=5))

    params_table_data = [
        [
            Paragraph("<b>Potencia del Cargador:</b>", body_style),
            Paragraph(f"{pot_w:,.0f} W", body_style),
            Paragraph("<b>Tipo de Alimentación:</b>", body_style),
            Paragraph(str(irve_params.get("red", "Monofásico (230 V)")), body_style)
        ],
        [
            Paragraph("<b>Longitud Cable (L):</b>", body_style),
            Paragraph(f"{irve_params.get('long', 25.0)} m", body_style),
            Paragraph("<b>Esquema Topológico:</b>", body_style),
            Paragraph(str(irve_params.get("esquema", "Esquema 3a")), body_style)
        ],
        [
            Paragraph("<b>Material Conductor:</b>", body_style),
            Paragraph("Cobre (Cu)", body_style),
            Paragraph("<b>Tipo Aislamiento:</b>", body_style),
            Paragraph(str(irve_params.get("aisl", "")), body_style)
        ],
        [
            Paragraph("<b>Método Instalación:</b>", body_style),
            Paragraph(str(irve_params.get("metodo", "")), body_style),
            Paragraph("<b>Tubo Protector:</b>", body_style),
            Paragraph(str(irve_results.get("tubo_irve", "Ø 32 mm")), body_style)
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

    story.append(Paragraph("2. Desarrollo Analítico y Requisitos de Protección (ITC-BT-52)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=5))

    ib_v = irve_results.get('ib', 0.0)
    s_cdt = irve_results.get('s_cdt', 0.0)

    just_irve_text = (
        f"<b>a) Intensidad de Diseño:</b> I<sub>b</sub> = <b>{ib_v:.2f} A</b>.<br/>"
        f"<b>b) Caída de Tensión Admisible (máx. 1.0%):</b> S<sub>cdt</sub> = <b>{s_cdt:.2f} mm²</b> $\\rightarrow$ Sección seleccionada = <b>{s_fin} mm²</b> (Caída real = <b>{dv_pct:.3f}%</b>).<br/>"
        f"<b>c) Esquema de Protecciones Exigido por ITC-BT-52:</b><br/>"
        f"• Magnetotérmico de <b>{in_pi} A (Curva C)</b> para sobreintensidades.<br/>"
        f"• Diferencial <b>Tipo A</b> (detección DC 6mA) o <b>Tipo B</b> obligatorio para cargas de vehículo eléctrico.<br/>"
        f"• Protección contra sobretensiones transitorias y permanentes (VSP/VTP) en origen del circuito."
    )

    just_box = Table([[Paragraph(just_irve_text, formula_style)]], colWidths=[18.0*cm])
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
        Paragraph("<b>CONFORMIDAD Y VALIDACIÓN TÉCNICA IRVE</b>", ParagraphStyle('FirmaTit', parent=body_style, fontName='Helvetica-Bold', fontSize=9.5, textColor=c_primary)),
        Spacer(1, 3),
        Paragraph("La derivación de recarga IRVE cumple en su totalidad con la norma ITC-BT-52 del REBT, incluyendo el esquema topológico y las protecciones diferenciales/sobretensiones obligatorias.", body_style),
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

    doc.build(story, canvasmaker=NumberedCanvasIRVE)
    return buffer.getvalue()
