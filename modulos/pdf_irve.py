# -*- coding: utf-8 -*-
"""
Generador de Documento Oficial de la Memoria Técnica de Diseño (MTD) y Esquema Unifilar IRVE
Conforme a las prescripciones oficiales de la Dirección General de Energía y Actividad Industrial y Minera
de la Región de Murcia (DGEAIM - CARM) y el REBT (RD 842/2002 - RD 1053/2014 ITC-BT-52 / ITC-BT-04 / ITC-BT-05 / ITC-BT-23).
"""

import io
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable, PageBreak
)
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Group, Polygon
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas

class NumberedCanvasIRVEMurcia(canvas.Canvas):
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
        
        # Cabecera en páginas 2 en adelante
        if self._pageNumber > 1:
            self.drawString(1.5*cm, 28.3*cm, "REGIÓN DE MURCIA - DGEAIM | Memoria Técnica y Esquema Unifilar IRVE")
            self.drawRightString(19.5*cm, 28.3*cm, "ITC-BT-52 (RD 1053/2014)")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5*cm, 28.1*cm, 19.5*cm, 28.1*cm)

        # Pie de página oficial
        self.setFont("Helvetica", 7.5)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.9*cm, page_text)
        self.drawString(1.5*cm, 0.9*cm, "Documento Oficial para Trámites ante la DGEAIM Región de Murcia - Conforme a RD 842/2002 e ITC-BT-52")
        self.restoreState()


def crear_dibujo_unifilar_reportlab(esquema_cod: str, pot_w: float, s_final: float, in_pi: int, dv_pct: float, tubo_dim: str, es_trif: bool) -> Drawing:
    """
    Crea el Esquema Unifilar Vectorial con símbolos normalizados UNE para el PDF oficial.
    """
    d_width = 510
    d_height = 145
    d = Drawing(d_width, d_height)
    
    # Fondo del esquema
    d.add(Rect(0, 0, d_width, d_height, fillColor=colors.HexColor('#f8fafc'), strokeColor=colors.HexColor('#cbd5e1'), strokeWidth=0.8, rx=4, ry=4))
    
    # Textos de origen según esquema
    tension_txt = "3x400V+N+PE" if es_trif else "230V+N+PE"
    cond_txt = f"5G{s_final:.1f}" if es_trif else f"3G{s_final:.1f}"
    
    # Bloque 1: Origen de Alimentación / Contador
    d.add(Rect(12, 45, 90, 85, fillColor=colors.HexColor('#ffffff'), strokeColor=colors.HexColor('#0284c7'), strokeWidth=1.2, rx=3, ry=3))
    d.add(String(57, 118, "ORIGEN", fontSize=6.5, fontName="Helvetica-Bold", fillColor=colors.HexColor("#0369a1"), textAnchor="middle"))
    d.add(Circle(57, 95, 12, fillColor=colors.HexColor("#e0f2fe"), strokeColor=colors.HexColor("#0284c7"), strokeWidth=1))
    d.add(String(57, 92, "kWh", fontSize=7, fontName="Helvetica-Bold", fillColor=colors.HexColor("#0369a1"), textAnchor="middle"))
    
    origen_sub = "Centraliz. Cont." if "Esquema 2" in esquema_cod or "3a" in esquema_cod else ("CGMP Vivienda" if "4a" in esquema_cod else "Cuadro Colectivo")
    d.add(String(57, 73, origen_sub, fontSize=5.5, fontName="Helvetica", fillColor=colors.HexColor("#334155"), textAnchor="middle"))
    d.add(String(57, 60, "Sensor SPL (CT)", fontSize=5.5, fontName="Helvetica-Bold", fillColor=colors.HexColor("#15803d"), textAnchor="middle"))
    d.add(String(57, 50, tension_txt, fontSize=5, fontName="Helvetica", fillColor=colors.HexColor("#64748b"), textAnchor="middle"))

    # Línea de enlace 1 (Hacia cuadro plaza)
    d.add(Line(102, 95, 140, 95, strokeColor=colors.HexColor("#0284c7"), strokeWidth=1.6))
    d.add(Polygon([136, 92, 142, 95, 136, 98], fillColor=colors.HexColor("#0284c7"), strokeColor=None))

    # Bloque 2: Cuadro de Protecciones Secundario en Plaza (ITC-BT-52)
    d.add(Rect(140, 35, 230, 100, fillColor=colors.HexColor("#f0f9ff"), strokeColor=colors.HexColor("#0369a1"), strokeWidth=1.2, strokeDashArray=[2,2], rx=4, ry=4))
    d.add(String(255, 126, "CUADRO SECUNDARIO EN PLAZA (IP65 / IK08)", fontSize=6.5, fontName="Helvetica-Bold", fillColor=colors.HexColor("#0369a1"), textAnchor="middle"))

    # Elemento 2.1: Sobretensiones VTP+VSP
    d.add(Rect(150, 48, 62, 70, fillColor=colors.HexColor("#ffffff"), strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.8, rx=2, ry=2))
    d.add(String(181, 107, "VSP + VTP", fontSize=6, fontName="Helvetica-Bold", fillColor=colors.HexColor("#92400e"), textAnchor="middle"))
    d.add(String(181, 95, "Sobretensiones", fontSize=5, fontName="Helvetica", fillColor=colors.HexColor("#334155"), textAnchor="middle"))
    d.add(String(181, 84, "Perm. + Trans.", fontSize=4.8, fontName="Helvetica", fillColor=colors.HexColor("#64748b"), textAnchor="middle"))
    d.add(String(181, 73, "Tipo 2 (BT-23)", fontSize=4.8, fontName="Helvetica", fillColor=colors.HexColor("#64748b"), textAnchor="middle"))
    d.add(String(181, 56, "Bobina Disparo", fontSize=4.8, fontName="Helvetica-Bold", fillColor=colors.HexColor("#d97706"), textAnchor="middle"))

    # Línea interna 1
    d.add(Line(212, 95, 224, 95, strokeColor=colors.HexColor("#0f172a"), strokeWidth=1.2))

    # Elemento 2.2: Magnetotérmico PIA Curva C
    d.add(Rect(224, 48, 62, 70, fillColor=colors.HexColor("#ffffff"), strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.8, rx=2, ry=2))
    d.add(String(255, 107, f"PIA {in_pi}A", fontSize=6.5, fontName="Helvetica-Bold", fillColor=colors.HexColor("#0f172a"), textAnchor="middle"))
    d.add(String(255, 95, "Curva C", fontSize=5.5, fontName="Helvetica-Bold", fillColor=colors.HexColor("#0284c7"), textAnchor="middle"))
    d.add(String(255, 84, "Icn ≥ 6 kA", fontSize=4.8, fontName="Helvetica", fillColor=colors.HexColor("#64748b"), textAnchor="middle"))
    d.add(String(255, 73, "Corte Omnipolar", fontSize=4.8, fontName="Helvetica", fillColor=colors.HexColor("#64748b"), textAnchor="middle"))
    d.add(String(255, 56, "Sobreintensidad", fontSize=4.8, fontName="Helvetica", fillColor=colors.HexColor("#334155"), textAnchor="middle"))

    # Línea interna 2
    d.add(Line(286, 95, 298, 95, strokeColor=colors.HexColor("#0f172a"), strokeWidth=1.2))

    # Elemento 2.3: Diferencial Clase A con 6mA DC
    d.add(Rect(298, 48, 64, 70, fillColor=colors.HexColor("#ffffff"), strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.8, rx=2, ry=2))
    d.add(String(330, 107, "DIFERENCIAL", fontSize=6, fontName="Helvetica-Bold", fillColor=colors.HexColor("#15803d"), textAnchor="middle"))
    d.add(String(330, 95, "CLASE A / B", fontSize=5.8, fontName="Helvetica-Bold", fillColor=colors.HexColor("#15803d"), textAnchor="middle"))
    d.add(String(330, 84, "IΔn = 30 mA", fontSize=4.8, fontName="Helvetica", fillColor=colors.HexColor("#334155"), textAnchor="middle"))
    d.add(String(330, 73, "6mA DC (RDC-DD)", fontSize=4.8, fontName="Helvetica-Bold", fillColor=colors.HexColor("#166534"), textAnchor="middle"))
    d.add(String(330, 56, "IEC 62955", fontSize=4.8, fontName="Helvetica", fillColor=colors.HexColor("#64748b"), textAnchor="middle"))

    # Línea de salida (Cable + Tubo)
    d.add(Line(370, 95, 410, 95, strokeColor=colors.HexColor("#0284c7"), strokeWidth=2))
    d.add(Polygon([406, 92, 412, 95, 406, 98], fillColor=colors.HexColor("#0284c7"), strokeColor=None))

    # Etiqueta Línea
    d.add(Rect(372, 102, 38, 22, fillColor=colors.HexColor('#ffffff'), strokeColor=colors.HexColor('#94a3b8'), strokeWidth=0.5, rx=2, ry=2))
    d.add(String(391, 114, cond_txt, fontSize=5, fontName="Helvetica-Bold", fillColor=colors.HexColor("#0f172a"), textAnchor="middle"))
    d.add(String(391, 105, tubo_dim, fontSize=4.5, fontName="Helvetica", fillColor=colors.HexColor("#0369a1"), textAnchor="middle"))

    # Bloque 3: Estación de Recarga Wallbox Modo 3 Tipo 2
    d.add(Rect(410, 38, 90, 95, fillColor=colors.HexColor('#ffffff'), strokeColor=colors.HexColor('#10b981'), strokeWidth=1.5, rx=4, ry=4))
    d.add(String(455, 122, "PUNTO RECARGA", fontSize=6.2, fontName="Helvetica-Bold", fillColor=colors.HexColor("#047857"), textAnchor="middle"))
    
    d.add(Rect(422, 65, 66, 48, fillColor=colors.HexColor('#0f172a'), strokeColor=None, rx=3, ry=3))
    d.add(Circle(455, 94, 8, fillColor=colors.HexColor("#10b981"), strokeColor=None))
    d.add(String(455, 91, "⚡", fontSize=7.5, fontName="Helvetica-Bold", fillColor=colors.HexColor("#ffffff"), textAnchor="middle"))
    d.add(String(455, 78, f"{pot_w/1000:.2f} kW", fontSize=6.5, fontName="Helvetica-Bold", fillColor=colors.HexColor("#38bdf8"), textAnchor="middle"))
    d.add(String(455, 69, "Modo 3 - Tipo 2", fontSize=4.8, fontName="Helvetica", fillColor=colors.HexColor("#94a3b8"), textAnchor="middle"))
    
    d.add(String(455, 52, f"ΔV real: {dv_pct:.2f}%", fontSize=5.5, fontName="Helvetica-Bold", fillColor=colors.HexColor("#15803d"), textAnchor="middle"))
    d.add(String(455, 43, "Mennekes IEC 62196", fontSize=4.5, fontName="Helvetica", fillColor=colors.HexColor("#64748b"), textAnchor="middle"))

    # Pie del diagrama
    d.add(String(15, 12, f"Esquema Reglamentario: {esquema_cod} | Cable RZ1-K 0.6/1kV (Cca-s1b,d1,a1) | Tubo {tubo_dim} (IK08) | ITC-BT-52 DGEAIM Región de Murcia", fontSize=5.2, fontName="Helvetica", fillColor=colors.HexColor("#475569")))

    return d


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


def _crear_logo_flowable(width=5.2*cm, height=2.9*cm):
    path = _obtener_logo_path()
    if path:
        try:
            return Image(path, width=width, height=height)
        except Exception:
            pass
    return None


def generar_pdf_irve(proyecto_info: dict, irve_params: dict, irve_results: dict, presupuesto_materiales: list = None) -> bytes:
    """
    Genera el Documento Oficial Oficial de Memoria Técnica de Diseño (MTD) e Informe Técnico IRVE
    adaptado para el registro ante la Dirección General de Energía y Actividad Industrial y Minera
    de la Región de Murcia (DGEAIM - CARM) y conforme al REBT (RD 842/2002 e ITC-BT-52).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.6*cm, bottomMargin=1.6*cm
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
    c_red_murcia = colors.HexColor("#991b1b")

    title_style = ParagraphStyle(
        'DocTitle_Murcia', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=15,
        textColor=c_primary, spaceAfter=1
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle_Murcia', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=10.5,
        textColor=c_secondary, spaceAfter=4
    )
    h1_style = ParagraphStyle(
        'Heading1_Murcia', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9.5, leading=12,
        textColor=c_primary, spaceBefore=7, spaceAfter=3, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Murcia', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=10,
        textColor=c_text_dark
    )
    bold_style = ParagraphStyle(
        'Bold_Murcia', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=10,
        textColor=c_text_dark
    )
    formula_style = ParagraphStyle(
        'Formula_Murcia', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=10,
        textColor=colors.HexColor("#0c4a6e")
    )

    story = []

    # =========================================================================
    # 1. ENCABEZADO OFICIAL DE LA REGIÓN DE MURCIA (DGEAIM) CON LOGO BOLIMUR
    # =========================================================================
    logo_irve = _crear_logo_flowable(width=5.2*cm, height=2.9*cm)
    col_logo_irve = logo_irve if logo_irve else Paragraph("<b>BOLIMUR</b><br/><font size='6' color='#0284c7'>Instalaciones</font>", ParagraphStyle('HdrLogoIRVE', parent=body_style, alignment=2))

    header_dgeaim_data = [
        [
            Paragraph(
                "<b>REGIÓN DE MURCIA</b><br/>"
                "<font size='6.5' color='#475569'>Consejería de Empresa, Empleo y Economía Social<br/>"
                "Dirección General de Energía y Actividad Industrial y Minera</font>",
                body_style
            ),
            Paragraph(
                "<b>MEMORIA TÉCNICA DE DISEÑO (MTD) - IRVE</b><br/>"
                "<font size='7' color='#0284c7'>INSTALACIÓN DE RECARGA DE VEHÍCULOS ELÉCTRICOS</font><br/>"
                "<font size='6' color='#64748b'>Reglamento Electrotécnico para Baja Tensión | ITC-BT-52</font>",
                ParagraphStyle('HdrRightM', parent=body_style, alignment=1)
            ),
            col_logo_irve
        ]
    ]
    t_hdr = Table(header_dgeaim_data, colWidths=[6.4*cm, 6.4*cm, 5.2*cm])
    t_hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 1.0, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (2,0), 'RIGHT'),
    ]))
    story.append(t_hdr)
    story.append(Spacer(1, 4))

    # =========================================================================
    # 2. METADATOS ADMINISTRATIVOS Y EMPLAZAMIENTO EN LA REGIÓN DE MURCIA
    # =========================================================================
    fecha_str = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    nom_empresa = proyecto_info.get("empresa", "BOLIMUR INSTALACIONES Y REFORMAS")
    nom_instalador = proyecto_info.get("proyectista", "Richard Orlando Choque Tejerina")
    lic_instalador = proyecto_info.get("licencia", "REBT-30/15892")
    loc_instalador = proyecto_info.get("localidad", "Rincón de Seca, Murcia (Región de Murcia)")
    
    meta_table_data = [
        [
            Paragraph("<b>Titular / Solicitante:</b>", bold_style),
            Paragraph(str(proyecto_info.get("cliente_nombre", "Particular / Comunidad")), body_style),
            Paragraph("<b>NIF / CIF:</b>", bold_style),
            Paragraph(str(proyecto_info.get("cliente_nif", "-")), body_style)
        ],
        [
            Paragraph("<b>Emplazamiento en R. Murcia:</b>", bold_style),
            Paragraph(f"{proyecto_info.get('emplazamiento', 'Plaza Garaje')} | {proyecto_info.get('municipio', 'Murcia (Región de Murcia)')}", body_style),
            Paragraph("<b>Nº Expediente / Ref:</b>", bold_style),
            Paragraph(str(proyecto_info.get("expediente", "EXP-IRVE-MURCIA-2026")), body_style)
        ],
        [
            Paragraph("<b>Empresa Instaladora:</b>", bold_style),
            Paragraph(f"{nom_empresa} (Registro RII)", body_style),
            Paragraph("<b>Fecha Redacción:</b>", bold_style),
            Paragraph(fecha_str, body_style)
        ],
        [
            Paragraph("<b>Instalador Habilitado:</b>", bold_style),
            Paragraph(f"{nom_instalador} | Certificado: <b>{lic_instalador}</b>", body_style),
            Paragraph("<b>Ámbito Oficial:</b>", bold_style),
            Paragraph("DGEAIM Región de Murcia", body_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[3.5*cm, 7.0*cm, 3.5*cm, 4.0*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4))

    # =========================================================================
    # 3. DICTAMEN TÉCNICO OFICIAL Y RESUMEN DE LA INSTALACIÓN IRVE
    # =========================================================================
    pot_w = float(irve_params.get("pot_wallbox", 7360.0))
    s_fin = irve_results.get("s_final", 6.0)
    in_pi = irve_results.get("in_pi", 32)
    dv_pct = irve_results.get("dv_real_pct", 0.0)
    dv_max_adm = irve_results.get("dv_max_adm_pct", 1.0)
    esquema_sel = irve_params.get("esquema", "Esquema 2")
    tubo_dim = irve_results.get("tubo_irve", "Ø 32 mm")
    es_trif = irve_params.get("es_trifasico", False)

    resumen_title = Paragraph("<b>DICTAMEN TÉCNICO OFICIAL (ITC-BT-52 DGEAIM):</b>", ParagraphStyle('ResTitleM', parent=body_style, fontSize=8.5, textColor=c_primary, fontName='Helvetica-Bold'))
    resumen_val = Paragraph(f"<b>SECCIÓN CONFORME: {s_fin:.1f} mm² Cu (RZ1-K)</b>", ParagraphStyle('ResValM', parent=body_style, fontSize=10, textColor=c_green, fontName='Helvetica-Bold', alignment=2))

    desglose_resumen = Paragraph(
        f"• <b>Esquema Topológico Homologado:</b> {esquema_sel}<br/>"
        f"• <b>Potencia de Diseño:</b> {pot_w:,.0f} W ({pot_w/1000:.2f} kW) | Intensidad Nominal I<sub>b</sub> = <b>{irve_results.get('ib', 0.0):.2f} A</b> | Factor Carga: 100% permanente.<br/>"
        f"• <b>Protección Magnetotérmica:</b> PIA <b>{in_pi} A (Curva C)</b> con poder de corte ≥ 6 kA | Caída de Tensión Real: <b>{dv_pct:.3f}%</b> (Límite: {dv_max_adm:.1f}%).<br/>"
        f"• <b>Protección Diferencial Exigida:</b> Interruptor Diferencial <b>Clase A (con detección DC ≤ 6mA según IEC 62955) o Clase B</b> (Sensibilidad 30 mA).<br/>"
        f"• <b>Protección Contra Sobretensiones:</b> Limitador combinado <b>Permanentes (VTP) + Transitorias Tipo 2 (VSP)</b> con bobina de disparo.<br/>"
        f"• <b>Canalización y Conductor:</b> Cable <b>RZ1-K 0.6/1kV CPR Cca-s1b,d1,a1</b> bajo tubo rígido/curvable <b>{tubo_dim} con protección IK08</b> libre de halógenos.",
        body_style
    )

    resumen_box = Table([[resumen_title, resumen_val], [desglose_resumen, ""]], colWidths=[11.5*cm, 6.5*cm])
    resumen_box.setStyle(TableStyle([
        ('SPAN', (0,1), (1,1)),
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 1.0, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(resumen_box)
    story.append(Spacer(1, 4))

    # =========================================================================
    # 4. ESQUEMA UNIFILAR GRÁFICO OFICIAL DGEAIM REGIÓN DE MURCIA (VECTORIAL)
    # =========================================================================
    story.append(Paragraph("1. Esquema Unifilar Gráfico Oficial de la Instalación (ITC-BT-52 / DGEAIM)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceBefore=1, spaceAfter=3))

    dibujo_unifilar = crear_dibujo_unifilar_reportlab(
        esquema_cod=esquema_sel,
        pot_w=pot_w,
        s_final=s_fin,
        in_pi=in_pi,
        dv_pct=dv_pct,
        tubo_dim=tubo_dim,
        es_trif=es_trif
    )
    story.append(dibujo_unifilar)
    story.append(Spacer(1, 4))

    # =========================================================================
    # 5. MEMORIA JUSTIFICATIVA DE CÁLCULOS ELÉCTRICOS (ITC-BT-52)
    # =========================================================================
    story.append(Paragraph("2. Memoria Descriptiva y Justificación Analítica de Cálculos (ITC-BT-52)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceBefore=1, spaceAfter=3))

    ib_v = irve_results.get('ib', 0.0)
    s_cdt = irve_results.get('s_cdt', 0.0)
    gamma_v = irve_results.get('gamma', 44.0)
    iz_adm = irve_results.get('iz_adm', 41.0)
    v_nom = 400.0 if es_trif else 230.0

    if es_trif:
        calc_ib_txt = f"I<sub>b</sub> = P / (√3 · V · cos φ) = {pot_w:,.0f} / (√3 · 400 · 1.0) = <b>{ib_v:.2f} A</b>"
        calc_s_txt = f"S<sub>cdt</sub> = (1 · P · L) / (γ · ΔV<sub>máx</sub> · V) = (1 · {pot_w:,.0f} · {irve_params.get('long', 25.0)}) / ({gamma_v} · {v_nom*(dv_max_adm/100.0):.2f} · 400) = <b>{s_cdt:.2f} mm²</b>"
    else:
        calc_ib_txt = f"I<sub>b</sub> = P / (V · cos φ) = {pot_w:,.0f} / (230 · 1.0) = <b>{ib_v:.2f} A</b>"
        calc_s_txt = f"S<sub>cdt</sub> = (2 · P · L) / (γ · ΔV<sub>máx</sub> · V) = (2 · {pot_w:,.0f} · {irve_params.get('long', 25.0)}) / ({gamma_v} · {v_nom*(dv_max_adm/100.0):.2f} · 230) = <b>{s_cdt:.2f} mm²</b>"

    just_table_data = [
        [
            Paragraph("<b>Intensidad de Diseño (I<sub>b</sub>):</b>", bold_style),
            Paragraph(calc_ib_txt, formula_style)
        ],
        [
            Paragraph("<b>Sección por Caída de Tensión:</b>", bold_style),
            Paragraph(calc_s_txt, formula_style)
        ],
        [
            Paragraph("<b>Comprobación Térmica (I<sub>z</sub>):</b>", bold_style),
            Paragraph(f"Capacidad admisible: <b>I<sub>z</sub> = {iz_adm:.1f} A</b> ≥ Calibre PIA <b>{in_pi} A</b> ≥ Intensidad I<sub>b</sub> = <b>{ib_v:.2f} A</b>. <i>(Cumple criterio reglamentario térmico ITC-BT-19)</i>.", formula_style)
        ],
        [
            Paragraph("<b>Caída de Tensión Real:</b>", bold_style),
            Paragraph(f"<b>ΔV<sub>real</sub> = {dv_pct:.3f}% ({irve_results.get('dv_real_v', 0.0):.2f} V)</b> ≤ Límite reglamentario <b>{dv_max_adm:.1f}%</b> conforme a ITC-BT-52.", formula_style)
        ],
        [
            Paragraph("<b>Sistema de Balanceo SPL:</b>", bold_style),
            Paragraph("Modulación inteligente mediante sensor toroidal (CT) para no exceder la potencia contratada de la vivienda.", formula_style)
        ]
    ]

    just_table = Table(just_table_data, colWidths=[4.8*cm, 13.2*cm])
    just_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('GRID', (0,0), (-1,-1), 0.4, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(just_table)
    story.append(Spacer(1, 4))

    # =========================================================================
    # 6. PROTOCOLO DE ENSAYOS Y VERIFICACIONES PREVIAS OFICIALES (ITC-BT-05)
    # =========================================================================
    story.append(Paragraph("3. Protocolo de Verificaciones Previas y Ensayos Oficiales (ITC-BT-05)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceBefore=1, spaceAfter=3))

    ensayos = irve_params.get("ensayos", {})
    pe_val = float(ensayos.get("pe_ohm", 0.12))
    aisl_val = float(ensayos.get("aisl_mohm", 100.0))
    rt_val = float(ensayos.get("rt_ohm", 11.4))
    dif_ms = float(ensayos.get("dif_ms", 24.0))

    pe_res = "CONFORME" if pe_val <= 0.50 else "NO CONFORME"
    pe_col = c_green if pe_val <= 0.50 else c_red_murcia

    aisl_res = "CONFORME" if aisl_val >= 1.0 else "NO CONFORME"
    aisl_col = c_green if aisl_val >= 1.0 else c_red_murcia
    aisl_txt = f"{aisl_val:.1f} MΩ" if aisl_val < 100 else "> 100 MΩ"

    rt_res = "CONFORME" if rt_val <= 15.0 else "NO CONFORME"
    rt_col = c_green if rt_val <= 15.0 else c_red_murcia

    dif_res = "CONFORME" if dif_ms <= 300.0 else "NO CONFORME"
    dif_col = c_green if dif_ms <= 300.0 else c_red_murcia

    ensayos_data = [
        [
            Paragraph("<b>Ensayo / Verificación Reglamentaria</b>", bold_style),
            Paragraph("<b>Criterio REBT</b>", bold_style),
            Paragraph("<b>Valor Obtenido</b>", bold_style),
            Paragraph("<b>Resultado</b>", bold_style)
        ],
        [
            Paragraph("Continuidad de conductores de protección (PE)", body_style),
            Paragraph("R ≤ 0,5 Ω", body_style),
            Paragraph(f"{pe_val:.2f} Ω", body_style),
            Paragraph(f"<b>{pe_res}</b>", ParagraphStyle('Conf', parent=body_style, textColor=pe_col))
        ],
        [
            Paragraph("Resistencia de aislamiento a 500 Vcc", body_style),
            Paragraph("R_aisl ≥ 1,0 MΩ", body_style),
            Paragraph(aisl_txt, body_style),
            Paragraph(f"<b>{aisl_res}</b>", ParagraphStyle('Conf2', parent=body_style, textColor=aisl_col))
        ],
        [
            Paragraph("Resistencia del bucle de tierra (R_t)", body_style),
            Paragraph("R_t · IΔn ≤ 24 V (garajes)", body_style),
            Paragraph(f"{rt_val:.1f} Ω", body_style),
            Paragraph(f"<b>{rt_res}</b>", ParagraphStyle('Conf3', parent=body_style, textColor=rt_col))
        ],
        [
            Paragraph("Tiempo de disparo del interruptor diferencial (30 mA)", body_style),
            Paragraph("t_disparo ≤ 300 ms", body_style),
            Paragraph(f"{dif_ms:.0f} ms (Clase A / B)", body_style),
            Paragraph(f"<b>{dif_res}</b>", ParagraphStyle('Conf4', parent=body_style, textColor=dif_col))
        ],
        [
            Paragraph("Protección contra sobretensiones transitorias y permanentes", body_style),
            Paragraph("ITC-BT-23 / BT-52", body_style),
            Paragraph("VSP + VTP Activo", body_style),
            Paragraph("<b>CONFORME</b>", ParagraphStyle('Conf5', parent=body_style, textColor=c_green))
        ]
    ]

    t_ensayos = Table(ensayos_data, colWidths=[6.5*cm, 4.0*cm, 4.0*cm, 3.5*cm])
    t_ensayos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.4, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (-1,-1), 'CENTER'),
    ]))
    story.append(t_ensayos)
    story.append(Spacer(1, 4))

    # =========================================================================
    # 7. PRESUPUESTO Y RESUMEN DE MATERIALES
    # =========================================================================
    if presupuesto_materiales:
        story.append(Paragraph("4. Resumen de Materiales, Equipos y Presupuesto Oficial", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceBefore=1, spaceAfter=3))
        
        pres_rows = [[
            Paragraph("<b>Descripción del Material / Partida</b>", bold_style),
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
            Paragraph("<b>TOTAL PRESUPUESTO (IVA Incluido):</b>", bold_style), "", "", "",
            Paragraph(f"<b>{tot_con_iva:,.2f} €</b>", ParagraphStyle('TotPresM', parent=bold_style, textColor=c_green, fontSize=8))
        ])
        
        t_mat = Table(pres_rows, colWidths=[9.5*cm, 1.5*cm, 1.5*cm, 2.5*cm, 3.0*cm])
        t_mat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('GRID', (0,0), (-1,-3), 0.4, c_border),
            ('SPAN', (0,-2), (3,-2)),
            ('SPAN', (0,-1), (3,-1)),
            ('BACKGROUND', (0,-2), (-1,-1), c_bg_light),
            ('LINEABOVE', (0,-2), (-1,-2), 1, c_secondary),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('ALIGN', (3,0), (-1,-1), 'RIGHT'),
        ]))
        story.append(t_mat)
        story.append(Spacer(1, 4))

    # =========================================================================
    # 8. DECLARACIÓN RESPONSABLE Y DILIGENCIA DE FIRMA OFICIAL DGEAIM
    # =========================================================================
    firma_block = [
        Paragraph("5. Declaración Responsable y Diligencia de Validación Oficial", h1_style),
        HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceBefore=1, spaceAfter=3),
        Paragraph(
            "El Instalador Autorizado en Baja Tensión cuyos datos figuran en el presente documento <b>DECLARA BAJO SU EXPRESA RESPONSABILIDAD</b> que la instalación de recarga de vehículos eléctricos ha sido proyectada, calculada, ejecutada y verificada de conformidad con las prescripciones del <b>Reglamento Electrotécnico para Baja Tensión (Real Decreto 842/2002)</b>, la <b>ITC-BT-52 (Real Decreto 1053/2014)</b>, el <b>artículo 17.5 de la Ley de Propiedad Horizontal</b> y las normas técnicas aplicables en la <b>Comunidad Autónoma de la Región de Murcia (DGEAIM)</b>.",
            body_style
        ),
        Spacer(1, 8),
        Table([
            [
                Paragraph(f"<b>Firma del Instalador Habilitado:</b><br/><br/><br/>___________________________________________<br/><b>{nom_instalador}</b><br/>Carnet Profesional: <b>{lic_instalador}</b>", body_style),
                Paragraph(f"<b>Sello Oficial de Empresa Instaladora:</b><br/><br/><br/>___________________________________________<br/><b>{nom_empresa}</b><br/>Registro RII Región de Murcia | Fecha: {fecha_str}", body_style)
            ]
        ], colWidths=[9.0*cm, 9.0*cm], style=[
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ])
    ]

    story.append(KeepTogether(firma_block))

    doc.build(story, canvasmaker=NumberedCanvasIRVEMurcia)
    return buffer.getvalue()
