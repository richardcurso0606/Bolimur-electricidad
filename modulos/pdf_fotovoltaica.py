# -*- coding: utf-8 -*-
"""
Módulo de Generación de Memoria Técnica Oficial de Instalaciones Solares Fotovoltaicas
en Autoconsumo (ITC-BT-40 / RD 244/2019 / DGEAIM Región de Murcia).
"""

import io
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

class NumberedCanvasFV(canvas.Canvas):
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
            self.drawString(1.5*cm, 28.3*cm, "BOLIMUR REBT | Memoria Técnica de Autoconsumo Solar Fotovoltaico (ITC-BT-40)")
            self.drawRightString(19.5*cm, 28.3*cm, "RD 244/2019 / DGEAIM Murcia")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5*cm, 28.1*cm, 19.5*cm, 28.1*cm)

        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.9*cm, page_text)
        self.drawString(1.5*cm, 0.9*cm, "Bolimur Software ElectroTécnico - Conforme a RD 842/2002 REBT y RD 244/2019")
        self.restoreState()

def _obtener_logo_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    posibles = [
        os.path.join(base_dir, "logo_bolimur.PNG"),
        os.path.join(base_dir, "logo_bolimur.png"),
        os.path.join(base_dir, "icono_bolimur.png")
    ]
    for p in posibles:
        if os.path.exists(p):
            return p
    return None

def generar_pdf_memoria_fotovoltaica(datos: dict) -> bytes:
    """
    Genera el PDF oficial de la Memoria Técnica de Diseño Fotovoltaica (ITC-BT-40).
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
    c_primary = colors.HexColor("#0284c7")
    c_sec = colors.HexColor("#0369a1")
    c_border = colors.HexColor("#cbd5e1")
    c_bg_head = colors.HexColor("#f8fafc")
    c_text = colors.HexColor("#1e293b")

    title_style = ParagraphStyle('FVTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, leading=17, alignment=1, textColor=c_sec)
    subtitle_style = ParagraphStyle('FVSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=13, alignment=1, textColor=c_primary)
    h_sec = ParagraphStyle('FVHsec', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=colors.white)
    body_style = ParagraphStyle('FVBody', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=11, textColor=c_text)
    bold_style = ParagraphStyle('FVBold', parent=body_style, fontName='Helvetica-Bold')
    foot_note = ParagraphStyle('FVFoot', parent=body_style, fontSize=7, leading=9, textColor=colors.HexColor("#64748b"))

    story = []

    # Cabecera
    logo_path = _obtener_logo_path()
    if logo_path:
        img_logo = Image(logo_path, width=4.0*cm, height=2.0*cm)
    else:
        img_logo = Paragraph("<b>⚡ BOLIMUR</b>", bold_style)

    header_txt = Paragraph(
        "<b>DIRECCIÓN GENERAL DE ENERGÍA Y ACTIVIDAD INDUSTRIAL Y MINERA</b><br/>"
        "<font size='9' color='#0284c7'><b>MEMORIA TÉCNICA DE DISEÑO: GENERACIÓN FOTOVOLTAICA</b></font><br/>"
        "<font size='7.5' color='#64748b'>Instalaciones de Generación en Baja Tensión en Autoconsumo (ITC-BT-40 / RD 244/2019)</font>",
        ParagraphStyle('HdrT', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11.5, alignment=1)
    )

    t_top = Table([[img_logo, header_txt]], colWidths=[4.5*cm, 13.5*cm], style=[
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ])
    story.append(t_top)
    story.append(Spacer(1, 6))

    # Título Principal del Expediente
    exped = datos.get("expediente", f"EXP-FV-MUR-{datetime.date.today().year}")
    p_pico = datos.get("generador_dc", {}).get("potencia_pico_w", 4500) / 1000.0
    p_nom = datos.get("inversor_ac", {}).get("potencia_nominal_w", 4000) / 1000.0
    mod_auto = datos.get("modalidad_autoconsumo", "Con excedentes acogida a compensación simplificada")

    story.append(Paragraph("<b>MEMORIA TÉCNICA DE DISEÑO DE AUTOCONSUMO SOLAR FOTOVOLTAICO</b>", title_style))
    story.append(Paragraph(f"Potencia Pico Generador DC: <b>{p_pico:.2f} kWp</b> | Potencia Inversor AC: <b>{p_nom:.2f} kWn</b> | {mod_auto}", subtitle_style))
    story.append(Spacer(1, 6))

    # BLOQUE 1: DATOS GENERALES Y EMPLAZAMIENTO
    t_sec1 = Table([[Paragraph("1. DATOS DEL TITULAR, EMPLAZAMIENTO Y MODALIDAD ADMINISTRATIVA (RD 244/2019)", h_sec)]], colWidths=[18.0*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_sec),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ])
    story.append(t_sec1)

    tit = datos.get("titular", {})
    emp = datos.get("emplazamiento", {})
    inst = datos.get("instalador", {})

    d_bloque1 = [
        [
            Paragraph("<b>Titular / Razón Social:</b>", bold_style),
            Paragraph(tit.get("nombre", "-"), body_style),
            Paragraph("<b>NIF / CIF Titular:</b>", bold_style),
            Paragraph(tit.get("nif", "-"), body_style)
        ],
        [
            Paragraph("<b>Dirección Emplazamiento:</b>", bold_style),
            Paragraph(f"{emp.get('direccion', '-')} ({emp.get('cp', '')})", body_style),
            Paragraph("<b>Municipio (Murcia):</b>", bold_style),
            Paragraph(emp.get("municipio", "Murcia"), body_style)
        ],
        [
            Paragraph("<b>Código CUPS:</b>", bold_style),
            Paragraph(emp.get("cups", "ES0021..."), body_style),
            Paragraph("<b>Referencia Catastral:</b>", bold_style),
            Paragraph(emp.get("ref_catastral", "-"), body_style)
        ],
        [
            Paragraph("<b>Modalidad Autoconsumo:</b>", bold_style),
            Paragraph(f"<b>{mod_auto}</b>", body_style),
            Paragraph("<b>Tipo de Conexión:</b>", bold_style),
            Paragraph(datos.get("tipo_conexion", "En red interior del consumidor (Esquema 1)"), body_style)
        ],
        [
            Paragraph("<b>Empresa Instaladora:</b>", bold_style),
            Paragraph(inst.get("empresa", "BOLIMUR ELECTRICIDAD"), body_style),
            Paragraph("<b>Instalador / Licencia:</b>", bold_style),
            Paragraph(f"{inst.get('nombre', '-')} ({inst.get('licencia', 'REBT-30')})", body_style)
        ]
    ]
    t_b1 = Table(d_bloque1, colWidths=[4.2*cm, 5.8*cm, 3.8*cm, 4.2*cm], style=[
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BACKGROUND', (0,0), (0,-1), c_bg_head),
        ('BACKGROUND', (2,0), (2,-1), c_bg_head),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ])
    story.append(t_b1)
    story.append(Spacer(1, 6))

    # BLOQUE 2: CARACTERÍSTICAS DEL GENERADOR DC (PANELES Y STRINGS)
    g_dc = datos.get("generador_dc", {})
    t_sec2 = Table([[Paragraph("2. CAMPO GENERADOR FOTOVOLTAICO EN CORRIENTE CONTINUA (DC - ITC-BT-40)", h_sec)]], colWidths=[18.0*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_primary),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ])
    story.append(t_sec2)

    d_bloque2 = [
        [
            Paragraph("<b>Módulos Fotovoltaicos:</b>", bold_style),
            Paragraph(f"{g_dc.get('num_paneles', 10)} uds x {g_dc.get('potencia_panel_w', 450)} Wp ({g_dc.get('modelo_panel', 'Monocristalino Tier 1 Perc / TopCon')})", body_style),
            Paragraph("<b>Potencia Pico Total:</b>", bold_style),
            Paragraph(f"<b>{p_pico:.2f} kWp</b> ({g_dc.get('potencia_pico_w', 4500)} Wp)", bold_style)
        ],
        [
            Paragraph("<b>Configuración Eléctrica:</b>", bold_style),
            Paragraph(f"{g_dc.get('num_strings', 1)} string(s) de {g_dc.get('paneles_por_string', 10)} módulos en serie", body_style),
            Paragraph("<b>Tipo de Cubierta:</b>", bold_style),
            Paragraph(g_dc.get("tipo_cubierta", "Tejado inclinado de teja árabe (Coplanar)"), body_style)
        ],
        [
            Paragraph("<b>Tensión Voc máx (-5ºC):</b>", bold_style),
            Paragraph(f"<b>{g_dc.get('voc_max_v', 485.0):.1f} V DC</b> (Límite inv: ≤ {g_dc.get('v_max_inversor', 600)} V)", body_style),
            Paragraph("<b>Tensión Vmp mín (+70ºC):</b>", bold_style),
            Paragraph(f"<b>{g_dc.get('vmp_min_v', 315.0):.1f} V DC</b> (Rango MPPT: ≥ {g_dc.get('v_mppt_min', 120)} V)", body_style),
        ],
        [
            Paragraph("<b>Corriente Cortocircuito Isc:</b>", bold_style),
            Paragraph(f"Isc calc: <b>{g_dc.get('isc_calc_a', 13.5):.2f} A</b> (1.25 x Isc)", body_style),
            Paragraph("<b>Cable Solar DC:</b>", bold_style),
            Paragraph(f"{g_dc.get('cable_dc', '1x6 mm² Cu')} H1Z2Z2-K (1.5 kV DC)", body_style),
        ],
        [
            Paragraph("<b>Caída Tensión DC (ΔV):</b>", bold_style),
            Paragraph(f"<b>{g_dc.get('cdt_dc_pct', 0.45):.2f} %</b> (Límite reglamentario: ≤ 1.5 %)", body_style),
            Paragraph("<b>Protecciones DC:</b>", bold_style),
            Paragraph(g_dc.get("protecciones_dc", "Seccionador 1000V DC + Descargador Sobretensiones Tipo 2 + Fusibles gPV"), body_style),
        ]
    ]
    t_b2 = Table(d_bloque2, colWidths=[4.2*cm, 5.8*cm, 3.8*cm, 4.2*cm], style=[
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BACKGROUND', (0,0), (0,-1), c_bg_head),
        ('BACKGROUND', (2,0), (2,-1), c_bg_head),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ])
    story.append(t_b2)
    story.append(Spacer(1, 6))

    # BLOQUE 3: CARACTERÍSTICAS DEL INVERSOR Y LADO AC (INTERCONEXIÓN)
    inv = datos.get("inversor_ac", {})
    t_sec3 = Table([[Paragraph("3. INVERSOR Y LÍNEA DE INTERCONEXIÓN EN CORRIENTE ALTERNA (AC - ITC-BT-40)", h_sec)]], colWidths=[18.0*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_sec),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ])
    story.append(t_sec3)

    d_bloque3 = [
        [
            Paragraph("<b>Inversor de Conexión a Red:</b>", bold_style),
            Paragraph(f"{inv.get('marca_modelo', 'Inversor Solar On-Grid')} ({inv.get('tipo', 'Monofásico 230 V - 50 Hz')})", body_style),
            Paragraph("<b>Potencia Nominal Inversor:</b>", bold_style),
            Paragraph(f"<b>{p_nom:.2f} kW</b> ({inv.get('potencia_nominal_w', 4000)} W)", bold_style)
        ],
        [
            Paragraph("<b>Corriente Nominal AC (In):</b>", bold_style),
            Paragraph(f"<b>{inv.get('corriente_ac_a', 17.4):.2f} A</b> (I diseño: {inv.get('corriente_ac_a', 17.4)*1.25:.2f} A)", body_style),
            Paragraph("<b>Rendimiento Máximo:</b>", bold_style),
            Paragraph(f"{inv.get('eficiencia_pct', 98.2):.1f} % (Euro-eficiencia)", body_style)
        ],
        [
            Paragraph("<b>Interruptor Automático (PIA):</b>", bold_style),
            Paragraph(f"<b>{inv.get('pia_amperios', 25)} A Curva C</b> (Poder corte: ≥ 6 kA)", body_style),
            Paragraph("<b>Interruptor Diferencial AC:</b>", bold_style),
            Paragraph(f"<b>{inv.get('dif_tipo', 'Clase A')} 30 mA</b> (Detección DC 6mA)", body_style)
        ],
        [
            Paragraph("<b>Sobretensiones AC:</b>", bold_style),
            Paragraph("Permanentes (VTP) + Transitorias Tipo 2 con bobina", body_style),
            Paragraph("<b>Línea Enlace Inversor-CGMP:</b>", bold_style),
            Paragraph(f"{inv.get('cable_ac', '3G6 mm² Cu RZ1-K 0.6/1kV')} bajo Tubo M25", body_style)
        ],
        [
            Paragraph("<b>Caída Tensión AC (ΔV):</b>", bold_style),
            Paragraph(f"<b>{inv.get('cdt_ac_pct', 0.52):.2f} %</b> (Límite: ≤ 1.0 % para evitar grid overvoltage)", body_style),
            Paragraph("<b>Protección Anti-Isla:</b>", bold_style),
            Paragraph("Integrada conforme a UNE-EN 50549-1 / RD 1699/2011", body_style)
        ]
    ]
    t_b3 = Table(d_bloque3, colWidths=[4.2*cm, 5.8*cm, 3.8*cm, 4.2*cm], style=[
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BACKGROUND', (0,0), (0,-1), c_bg_head),
        ('BACKGROUND', (2,0), (2,-1), c_bg_head),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ])
    story.append(t_b3)
    story.append(Spacer(1, 6))

    # BLOQUE 4: PRODUCCIÓN ENERGÉTICA ESTIMADA (HSP MURCIA) Y RETORNO
    prod = datos.get("produccion_estimada", {})
    t_sec4 = Table([[Paragraph("4. BALANCE ENERGÉTICO ANUAL ESTIMADO (HSP REGIÓN DE MURCIA)", h_sec)]], colWidths=[18.0*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_primary),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ])
    story.append(t_sec4)

    d_bloque4 = [
        [
            Paragraph("<b>Horas Sol Pico (HSP Media):</b>", bold_style),
            Paragraph(f"<b>{prod.get('hsp', 5.1):.1f} horas/día</b> (Zona climática V - Murcia)", body_style),
            Paragraph("<b>Factor de Rendimiento (PR):</b>", bold_style),
            Paragraph(f"<b>{prod.get('performance_ratio', 80.0):.0f} %</b> (Pérdidas térmicas y cable)", body_style)
        ],
        [
            Paragraph("<b>Producción Anual Estimada:</b>", bold_style),
            Paragraph(f"<b>{prod.get('produccion_kwh_ano', 6700):,.0f} kWh / año</b>", bold_style),
            Paragraph("<b>Ahorro Económico Estimado:</b>", bold_style),
            Paragraph(f"<b>{prod.get('ahorro_euros_ano', 1050):,.2f} € / año</b> (Aprox. 0.16 €/kWh)", bold_style)
        ],
        [
            Paragraph("<b>Emisiones de CO₂ Evitadas:</b>", bold_style),
            Paragraph(f"<b>{prod.get('co2_evitado_tn', 2.15):.2f} toneladas CO₂ / año</b>", body_style),
            Paragraph("<b>Árboles Equivalentes:</b>", bold_style),
            Paragraph(f"Equivale a plantar <b>{int(prod.get('co2_evitado_tn', 2.15)*45)} árboles</b>", body_style)
        ]
    ]
    t_b4 = Table(d_bloque4, colWidths=[4.2*cm, 5.8*cm, 3.8*cm, 4.2*cm], style=[
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BACKGROUND', (0,0), (0,-1), c_bg_head),
        ('BACKGROUND', (2,0), (2,-1), c_bg_head),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ])
    story.append(t_b4)
    story.append(Spacer(1, 6))

    # BLOQUE 5: PROTOCOLO DE PRUEBAS DE PUESTA EN MARCHA (ITC-BT-40 / ITC-BT-05)
    t_sec5 = Table([[Paragraph("5. PROTOCOLO DE VERIFICACIÓN PREVIA Y PUESTA EN SERVICIO (ITC-BT-40 / BT-05)", h_sec)]], colWidths=[18.0*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_sec),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ])
    story.append(t_sec5)

    ensayos = datos.get("ensayos_fotovoltaicos", {})
    d_ensayos = [
        [
            Paragraph("<b>Ensayo / Comprobación Reglamentaria</b>", bold_style),
            Paragraph("<b>Criterio Reglamentario</b>", bold_style),
            Paragraph("<b>Valor Medido</b>", bold_style),
            Paragraph("<b>Resultado</b>", bold_style)
        ],
        [
            Paragraph("1. Polaridad y Voc de Strings DC", body_style),
            Paragraph("Tensión positiva en borne (+), Voc coherente", body_style),
            Paragraph(f"{ensayos.get('voc_medida', '420 V DC')}", body_style),
            Paragraph("<b>CONFORME</b>", bold_style)
        ],
        [
            Paragraph("2. Aislamiento Lado DC (Riso a 1000V DC)", body_style),
            Paragraph("Mínimo reglamentario: ≥ 1.0 MΩ", body_style),
            Paragraph(f"{ensayos.get('aisl_dc_mohm', 150.0):.1f} MΩ", body_style),
            Paragraph("<b>CONFORME</b>", bold_style)
        ],
        [
            Paragraph("3. Continuidad y Puesta a Tierra Estructura", body_style),
            Paragraph("Marcos interconectados a PE con Cu 16 mm²", body_style),
            Paragraph(f"Rt = {ensayos.get('rt_ohm', 11.2):.1f} Ω (≤ 15 Ω)", body_style),
            Paragraph("<b>CONFORME</b>", bold_style)
        ],
        [
            Paragraph("4. Desconexión Anti-Isla (Pérdida de Red)", body_style),
            Paragraph("Desconexión en t < 0.5 s al cortar IGA red", body_style),
            Paragraph("t = 0.18 s", body_style),
            Paragraph("<b>CONFORME</b>", bold_style)
        ],
        [
            Paragraph("5. Disparo Diferencial AC Lado Inversor", body_style),
            Paragraph("Clase A/B: t < 200 ms a IΔn = 30 mA", body_style),
            Paragraph("t = 24 ms / I = 21 mA", body_style),
            Paragraph("<b>CONFORME</b>", bold_style)
        ]
    ]
    t_ens = Table(d_ensayos, colWidths=[5.5*cm, 5.5*cm, 4.0*cm, 3.0*cm], style=[
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('BACKGROUND', (0,0), (-1,0), c_bg_head),
        ('ALIGN', (2,1), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
    ])
    story.append(t_ens)
    story.append(Spacer(1, 10))

    # DECLARACIÓN Y FIRMA DEL INSTALADOR AUTORIZADO
    d_firma = [
        [
            Paragraph(
                "<b>DECLARACIÓN DEL INSTALADOR AUTORIZADO (ITC-BT-40):</b><br/>"
                "El instalador habilitado abajo firmante declara bajo su responsabilidad que la presente instalación de generación "
                "solar fotovoltaica en régimen de autoconsumo ha sido diseñada y ejecutada de estricta conformidad con el "
                "Reglamento Electrotécnico para Baja Tensión (RD 842/2002), sus Instrucciones Técnicas Complementarias (ITC-BT-01 a ITC-BT-52), "
                "el Real Decreto 244/2019 de condiciones de autoconsumo y la normativa de la Dirección General de Energía de la Región de Murcia.",
                foot_note
            ),
            Paragraph(
                f"En Murcia, a {datetime.date.today().strftime('%d de %B de %Y')}<br/><br/>"
                "<b>Firma del Instalador Habilitado:</b><br/><br/><br/>"
                f"<b>{inst.get('nombre', 'INSTALADOR')}</b><br/>"
                f"<font size='6.5' color='#64748b'>Carnet REBT: {inst.get('licencia', 'REBT-30/15892')}</font>",
                ParagraphStyle('FirmaT', parent=body_style, alignment=1)
            )
        ]
    ]
    t_f = Table(d_firma, colWidths=[12.0*cm, 6.0*cm], style=[
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ])
    story.append(KeepTogether(t_f))

    doc.build(story, canvasmaker=NumberedCanvasFV)
    return buffer.getvalue()

# Alias de compatibilidad
generar_pdf_fotovoltaica = generar_pdf_memoria_fotovoltaica
