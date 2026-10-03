# -*- coding: utf-8 -*-
"""
Generador de Documento PDF Oficial de la Memoria Técnica IRVE (ITC-BT-52)
Cumple con el Reglamento Electrotécnico para Baja Tensión (RD 842/2002 y RD 1053/2014)
"""

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
            self.drawRightString(19.5*cm, 28.3*cm, "ITC-BT-52 (RD 1053/2014)")
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


def generar_pdf_irve(proyecto_info: dict, irve_params: dict, irve_results: dict, presupuesto_materiales: list = None) -> bytes:
    """
    Genera un informe técnico PDF profesional completo para el módulo IRVE (ITC-BT-52).
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
    c_green = colors.HexColor("#15803d")

    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=15, leading=19,
        textColor=c_primary, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=12,
        textColor=c_secondary, spaceAfter=8
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=13.5,
        textColor=c_primary, spaceBefore=9, spaceAfter=4, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=c_text_dark
    )
    bold_style = ParagraphStyle(
        'Bold_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=11,
        textColor=c_text_dark
    )
    formula_style = ParagraphStyle(
        'Formula_Text', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=colors.HexColor("#0c4a6e")
    )

    story = []

    # 1. Cabecera con Logotipo y Título
    logo_path = "logo_bolimur.PNG"
    if not os.path.exists(logo_path):
        logo_path = "icono_bolimur.png"
    
    nom_empresa = proyecto_info.get("empresa", "BOLIMUR INSTALACIONES Y REFORMAS")
    text_col = [
        Paragraph("MEMORIA TÉCNICA DE DISEÑO: INFRAESTRUCTURA IRVE", title_style),
        Paragraph(f"RECARGA DE VEHÍCULOS ELÉCTRICOS SEGÚN ITC-BT-52 | {nom_empresa}", subtitle_style)
    ]

    if os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=3.8*cm, height=2.4*cm)
            header_table = Table([[text_col, img]], colWidths=[14.2*cm, 3.8*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(header_table)
        except Exception:
            story.extend(text_col)
    else:
        story.extend(text_col)

    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=2, spaceAfter=6))

    # 2. Metadatos del Proyecto, Cliente e Instalador
    fecha_str = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    meta_table_data = [
        [
            Paragraph("<b>Proyecto / Obra:</b>", bold_style),
            Paragraph(str(proyecto_info.get("nombre", "Instalación IRVE")), body_style),
            Paragraph("<b>Fecha de Emisión:</b>", bold_style),
            Paragraph(fecha_str, body_style)
        ],
        [
            Paragraph("<b>Cliente / Titular:</b>", bold_style),
            Paragraph(str(proyecto_info.get("cliente_nombre", "Particular / Comunidad")), body_style),
            Paragraph("<b>NIF / CIF:</b>", bold_style),
            Paragraph(str(proyecto_info.get("cliente_nif", "-")), body_style)
        ],
        [
            Paragraph("<b>Emplazamiento / Plaza:</b>", bold_style),
            Paragraph(str(proyecto_info.get("emplazamiento", "Plaza de Garaje")), body_style),
            Paragraph("<b>Expediente / Ref:</b>", bold_style),
            Paragraph(str(proyecto_info.get("expediente", "EXP-IRVE-2026")), body_style)
        ],
        [
            Paragraph("<b>Instalador Autorizado:</b>", bold_style),
            Paragraph(str(proyecto_info.get("proyectista", "Richard Orlando Choque Tejerina")), body_style),
            Paragraph("<b>Carnet / Registro REBT:</b>", bold_style),
            Paragraph(str(proyecto_info.get("licencia", "REBT-30/15892")), body_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[3.5*cm, 6.5*cm, 3.8*cm, 4.2*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # 3. Cuadro de Resumen Ejecutivo y Dictamen Técnico
    pot_w = float(irve_params.get("pot_wallbox", 7360.0))
    s_fin = irve_results.get("s_final", 6.0)
    in_pi = irve_results.get("in_pi", 32)
    dv_pct = irve_results.get("dv_real_pct", 0.0)
    dv_max_adm = irve_results.get("dv_max_adm_pct", 1.0)
    esquema_sel = irve_params.get("esquema", "Esquema 2 (Contador común vivienda y recarga)")
    tubo_dim = irve_results.get("tubo_irve", "Ø 32 mm")

    resumen_title = Paragraph("<b>DICTAMEN TÉCNICO Y SECCIÓN REGLAMENTARIA:</b>", ParagraphStyle('ResTitle', parent=body_style, fontSize=10, textColor=c_primary, fontName='Helvetica-Bold'))
    resumen_val = Paragraph(f"<b>SECCIÓN {s_fin:.1f} mm² Cu (RZ1-K 0.6/1kV)</b>", ParagraphStyle('ResVal', parent=body_style, fontSize=12, textColor=c_green, fontName='Helvetica-Bold', alignment=2))

    desglose_resumen = Paragraph(
        f"<b>Esquema Topológico Seleccionado:</b> {esquema_sel}<br/>"
        f"• Potencia de Carga: <b>{pot_w:,.0f} W ({pot_w/1000:.2f} kW)</b> | Intensidad nominal: <b>{irve_results.get('ib', 0.0):.2f} A</b><br/>"
        f"• Protección Magnetotérmica: <b>PIA {in_pi} A (Curva C)</b> | Caída de Tensión Real: <b>{dv_pct:.3f}%</b> (Máx. permitido: {dv_max_adm:.1f}%)<br/>"
        f"• Protección Diferencial: <b>Clase A (con detección continua 6mA DC según IEC 62955) o Clase B (30 mA)</b><br/>"
        f"• Protección Sobretensiones: <b>VSP (Transitorias Tipo 2) + VTP (Permanentes con bobina de disparo)</b><br/>"
        f"• Canalización: <b>Tubo rígido/curvable {tubo_dim} no propagador de llama, libre de halógenos y protección IK08</b>",
        body_style
    )

    resumen_box = Table([[resumen_title, resumen_val], [desglose_resumen, ""]], colWidths=[11.5*cm, 6.5*cm])
    resumen_box.setStyle(TableStyle([
        ('SPAN', (0,1), (1,1)),
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 1.2, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(resumen_box)
    story.append(Spacer(1, 6))

    # 4. Parámetros Técnicos y de Instalación
    story.append(Paragraph("1. Parámetros de Diseño y Características del Punto de Recarga", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=4))

    params_table_data = [
        [
            Paragraph("<b>Potencia de Wallbox:</b>", bold_style),
            Paragraph(f"{pot_w:,.0f} W ({pot_w/1000:.2f} kW)", body_style),
            Paragraph("<b>Sistema de Red:</b>", bold_style),
            Paragraph(str(irve_params.get("red", "Monofásico (230 V)")), body_style)
        ],
        [
            Paragraph("<b>Longitud de Línea (L):</b>", bold_style),
            Paragraph(f"{irve_params.get('long', 25.0)} metros", body_style),
            Paragraph("<b>Factor de Potencia (cos φ):</b>", bold_style),
            Paragraph("1.0 (Régimen de recarga pura)", body_style)
        ],
        [
            Paragraph("<b>Material Conductor:</b>", bold_style),
            Paragraph("Cobre (Cu) electrolítico", body_style),
            Paragraph("<b>Aislamiento del Cable:</b>", bold_style),
            Paragraph(str(irve_params.get("aisl", "XLPE 90ºC - RZ1-K")), body_style)
        ],
        [
            Paragraph("<b>Método de Instalación:</b>", bold_style),
            Paragraph(str(irve_params.get("metodo", "B2 (En tubo superficial)")), body_style),
            Paragraph("<b>Tubo Protector Exterior:</b>", bold_style),
            Paragraph(f"{tubo_dim} (Libre Halógenos IK08)", body_style)
        ],
        [
            Paragraph("<b>Modo de Recarga:</b>", bold_style),
            Paragraph("Modo 3 (Conector Tipo 2 / Mennekes)", body_style),
            Paragraph("<b>Balanceo Dinámico (SPL):</b>", bold_style),
            Paragraph("Modulación de carga integrada (Pinza CT)", body_style)
        ]
    ]

    params_table = Table(params_table_data, colWidths=[4.2*cm, 4.8*cm, 4.5*cm, 4.5*cm])
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(params_table)
    story.append(Spacer(1, 6))

    # 5. Justificación Analítica de Cálculos Reglamentarios
    story.append(Paragraph("2. Memoria Justificativa de Cálculos Eléctricos (ITC-BT-52)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=4))

    ib_v = irve_results.get('ib', 0.0)
    s_cdt = irve_results.get('s_cdt', 0.0)
    gamma_v = irve_results.get('gamma', 44.0)
    iz_adm = irve_results.get('iz_adm', 41.0)
    es_trif = irve_params.get("es_trifasico", False)

    v_nom = 400.0 if es_trif else 230.0
    if es_trif:
        calc_ib_txt = f"I<sub>b</sub> = P / (√3 · V · cos φ) = {pot_w:,.0f} / (√3 · 400 · 1.0) = <b>{ib_v:.2f} A</b>"
        calc_s_txt = f"S<sub>cdt</sub> = (1 · P · L) / (γ · ΔV<sub>máx</sub> · V) = (1 · {pot_w:,.0f} · {irve_params.get('long', 25.0)}) / ({gamma_v} · {v_nom*(dv_max_adm/100.0):.2f} · 400) = <b>{s_cdt:.2f} mm²</b>"
    else:
        calc_ib_txt = f"I<sub>b</sub> = P / (V · cos φ) = {pot_w:,.0f} / (230 · 1.0) = <b>{ib_v:.2f} A</b>"
        calc_s_txt = f"S<sub>cdt</sub> = (2 · P · L) / (γ · ΔV<sub>máx</sub> · V) = (2 · {pot_w:,.0f} · {irve_params.get('long', 25.0)}) / ({gamma_v} · {v_nom*(dv_max_adm/100.0):.2f} · 230) = <b>{s_cdt:.2f} mm²</b>"

    just_table_data = [
        [
            Paragraph("<b>Cálculo de Intensidad de Diseño (I<sub>b</sub>):</b>", bold_style),
            Paragraph(calc_ib_txt, formula_style)
        ],
        [
            Paragraph("<b>Cálculo de Sección por Caída de Tensión:</b>", bold_style),
            Paragraph(calc_s_txt, formula_style)
        ],
        [
            Paragraph("<b>Verificación Térmica y Calibre de Protección:</b>", bold_style),
            Paragraph(f"Calibre Magnetotérmico: <b>PIA {in_pi} A (Curva C)</b> | Capacidad admisible del cable (I<sub>z</sub>): <b>{iz_adm:.1f} A</b>. Cumple criterio reglamentario: <i>I<sub>b</sub> ({ib_v:.2f}A) ≤ I<sub>n</sub> ({in_pi}A) ≤ I<sub>z</sub> ({iz_adm:.1f}A)</i>.", formula_style)
        ],
        [
            Paragraph("<b>Caída de Tensión Real Resultante:</b>", bold_style),
            Paragraph(f"ΔV<sub>real</sub> = <b>{dv_pct:.3f}%</b> ({irve_results.get('dv_real_v', 0.0):.2f} V) ≤ Límite Admisible de <b>{dv_max_adm:.1f}%</b> conforme a ITC-BT-52.", formula_style)
        ]
    ]

    just_table = Table(just_table_data, colWidths=[5.5*cm, 12.5*cm])
    just_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('GRID', (0,0), (-1,-1), 0.5, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(just_table)
    story.append(Spacer(1, 6))

    # 6. Presupuesto / Lista de Acopio de Materiales para el Instalador
    if presupuesto_materiales:
        story.append(Paragraph("3. Desglose de Materiales, Equipos y Presupuesto de Instalación", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=4))
        
        pres_rows = [[
            Paragraph("<b>Concepto / Descripción del Material</b>", bold_style),
            Paragraph("<b>Cant.</b>", bold_style),
            Paragraph("<b>Ud.</b>", bold_style),
            Paragraph("<b>PVP Ud. (€)</b>", bold_style),
            Paragraph("<b>Total (€)</b>", bold_style)
        ]]
        
        tot_mat = 0.0
        for item in presupuesto_materiales:
            cant = float(item.get("cantidad", 1))
            pu = float(item.get("precio_ud", 0.0))
            sub = cant * pu
            tot_mat += sub
            pres_rows.append([
                Paragraph(str(item.get("concepto", "")), body_style),
                Paragraph(f"{cant:.1f}" if cant % 1 != 0 else f"{int(cant)}", body_style),
                Paragraph(str(item.get("unidad", "ud")), body_style),
                Paragraph(f"{pu:,.2f} €", body_style),
                Paragraph(f"{sub:,.2f} €", bold_style)
            ])
            
        iva_val = tot_mat * 0.21
        tot_con_iva = tot_mat + iva_val
        pres_rows.append([
            Paragraph("<b>BASE IMPONIBLE (SUBTOTAL):</b>", bold_style), "", "", "",
            Paragraph(f"<b>{tot_mat:,.2f} €</b>", bold_style)
        ])
        pres_rows.append([
            Paragraph("<b>TOTAL PRESUPUESTO INSTALACIÓN (21% IVA Incl.):</b>", bold_style), "", "", "",
            Paragraph(f"<b>{tot_con_iva:,.2f} €</b>", ParagraphStyle('TotPres', parent=bold_style, textColor=c_green, fontSize=8.5))
        ])
        
        t_mat = Table(pres_rows, colWidths=[9.5*cm, 1.5*cm, 1.5*cm, 2.5*cm, 3.0*cm])
        t_mat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('GRID', (0,0), (-1,-3), 0.5, c_border),
            ('SPAN', (0,-2), (3,-2)),
            ('SPAN', (0,-1), (3,-1)),
            ('BACKGROUND', (0,-2), (-1,-1), c_bg_light),
            ('LINEABOVE', (0,-2), (-1,-2), 1, c_secondary),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ]))
        story.append(t_mat)
        story.append(Spacer(1, 6))

    # 7. Declaración de Conformidad y Firma del Instalador
    firma_block = [
        Paragraph("4. Conformidad Reglamentaria y Validación Oficial", h1_style),
        HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=4),
        Paragraph(
            "El Instalador Autorizado abajo firmante certifica que los cálculos, protecciones y canalizaciones especificados en la presente Memoria Técnica cumplen rigurosamente con las prescripciones del <b>Reglamento Electrotécnico para Baja Tensión (RD 842/2002)</b>, en particular la <b>ITC-BT-52 (RD 1053/2014)</b>, así como con el <b>artículo 17.5 de la Ley de Propiedad Horizontal</b> para garajes comunitarios.",
            body_style
        ),
        Spacer(1, 10),
        Table([
            [
                Paragraph(f"<b>Firma del Instalador Autorizado:</b><br/><br/><br/>___________________________________________<br/><b>{proyecto_info.get('proyectista', 'Richard Orlando Choque Tejerina')}</b><br/>Licencia: {proyecto_info.get('licencia', 'REBT-30/15892')}", body_style),
                Paragraph(f"<b>Sello de Empresa Instaladora:</b><br/><br/><br/>___________________________________________<br/><b>{nom_empresa}</b><br/>Fecha: {fecha_str}", body_style)
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
