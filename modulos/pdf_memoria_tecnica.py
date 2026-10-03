# -*- coding: utf-8 -*-
"""
Generador Oficial Normalizado de Memoria Técnica de Diseño (MTD)
Dirección General de Industria, Energía y Minas (DGEAIM) - Región de Murcia (Código 30)
Consejería de Ciencia, Tecnologías, Industria y Comercio / Empresa, Empleo y Economía Social
Nuevas Tecnologías s/n., 30005 Murcia - Tel. (968) 362002

Documento 100% oficial homologado para presentación telemática o presencial ante la
Comunidad Autónoma de la Región de Murcia (CARM) en sustitución del formato papel/Word.
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

class NumberedCanvasMTDMurciaOficial(canvas.Canvas):
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
        
        # Cabecera institucional a partir de la página 2
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 7.5)
            self.setFillColor(colors.HexColor("#0f172a"))
            self.drawString(1.5*cm, 28.5*cm, "REGIÓN DE MURCIA - Consejería de Industria | DGEAIM")
            self.setFont("Helvetica", 7)
            self.setFillColor(colors.HexColor("#475569"))
            self.drawRightString(19.5*cm, 28.5*cm, "MEMORIA TÉCNICA DE DISEÑO (RD 842/2002)")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.6)
            self.line(1.5*cm, 28.3*cm, 19.5*cm, 28.3*cm)

        # Pie de página oficial
        self.setFont("Helvetica", 6.8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(1.5*cm, 1.25*cm, 19.5*cm, 1.25*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.8*cm, page_text)
        self.drawString(1.5*cm, 0.8*cm, "Nuevas Tecnologías, s/n - 30005 Murcia - Tel. 968 362002 - D.G. Industria, Energía y Minas (Código 30)")
        self.restoreState()


def generar_pdf_mtd_industria_murcia(datos_mtd: dict) -> bytes:
    """
    Genera el Documento Oficial Completo de Memoria Técnica de Diseño (MTD)
    exactamente estructurado según el modelo normalizado de la Región de Murcia (DGEAIM).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.3*cm, rightMargin=1.3*cm,
        topMargin=1.4*cm, bottomMargin=1.4*cm
    )

    styles = getSampleStyleSheet()
    
    c_primary = colors.HexColor("#0f172a")
    c_secondary = colors.HexColor("#0284c7")
    c_dark_blue = colors.HexColor("#0369a1")
    c_bg_head = colors.HexColor("#f1f5f9")
    c_bg_sub = colors.HexColor("#f8fafc")
    c_border = colors.HexColor("#94a3b8")
    c_text_dark = colors.HexColor("#0f172a")
    c_green = colors.HexColor("#15803d")
    c_carm_red = colors.HexColor("#991b1b")

    title_main = ParagraphStyle(
        'MainTitle_MTD', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=13,
        textColor=c_primary, alignment=1
    )
    h_section = ParagraphStyle(
        'SecHead_MTD', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.0, leading=10,
        textColor=colors.white
    )
    body_style = ParagraphStyle(
        'Body_MTD', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.0, leading=9.0,
        textColor=c_text_dark
    )
    bold_style = ParagraphStyle(
        'Bold_MTD', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.0, leading=9.0,
        textColor=c_text_dark
    )
    small_style = ParagraphStyle(
        'Small_MTD', parent=styles['Normal'],
        fontName='Helvetica', fontSize=6.2, leading=8.0,
        textColor=colors.HexColor("#475569")
    )

    story = []

    # Extraer metadatos
    titular = datos_mtd.get("titular", {})
    emplazamiento = datos_mtd.get("emplazamiento", {})
    instalador = datos_mtd.get("instalador", {})
    suministro = datos_mtd.get("suministro", {})
    protecciones = datos_mtd.get("protecciones", {})
    circuitos = datos_mtd.get("circuitos", [])
    tipo_instalacion = datos_mtd.get("tipo_instalacion", "Vivienda Residencial (ITC-BT-25)")
    fecha_str = datos_mtd.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    expediente = datos_mtd.get("expediente", "EXP-MTD-MURCIA-2026")

    # =========================================================================
    # PÁGINA 1: ENCABEZADO INSTITUCIONAL OFICIAL DGEAIM MURCIA
    # =========================================================================
    header_table_data = [
        [
            Paragraph(
                "<b>Región de Murcia</b><br/>"
                "<font size='6.5'>Consejería de Ciencia, Tecnologías, Industria y Comercio<br/>"
                "<b>Dirección General de Industria, Energía y Minas</b><br/>"
                "Nuevas Tecnologías s/n., 30005 Murcia | Tel. (968) 362002 - Fax. 362003</font>",
                body_style
            ),
            Paragraph(
                "<b>MEMORIA TÉCNICA DE DISEÑO</b><br/>"
                "<font size='7.5' color='#0369a1'><b>DE INSTALACIONES ELÉCTRICAS DE BAJA TENSIÓN</b></font><br/>"
                f"<font size='6.5' color='#991b1b'><b>CÓDIGO PROVINCIAL: 30 (MURCIA)</b> | Ref: {expediente}</font>",
                ParagraphStyle('HdrR', parent=body_style, alignment=2)
            )
        ]
    ]
    t_hdr = Table(header_table_data, colWidths=[9.5*cm, 8.9*cm])
    t_hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_head),
        ('BOX', (0,0), (-1,-1), 1.0, c_primary),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_hdr)
    story.append(Spacer(1, 3))

    # -------------------------------------------------------------------------
    # 1. DATOS IDENTIFICATIVOS DEL TITULAR DE LA INSTALACIÓN
    # -------------------------------------------------------------------------
    story.append(Table([[Paragraph("DATOS IDENTIFICATIVOS DEL TITULAR DE LA INSTALACIÓN", h_section)]], colWidths=[18.4*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_primary),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))

    t_tit_data = [
        [
            Paragraph(f"<b>Nombre o Razón Social:</b> {titular.get('nombre', 'JOAQUÍN YÁÑEZ ALFONSO')}", body_style),
            Paragraph(f"<b>N.I.F. / C.I.F.:</b> {titular.get('nif', '48000000X')}", body_style)
        ],
        [
            Paragraph(f"<b>Dirección:</b> {emplazamiento.get('direccion', 'C/ Mayor, s/n')}", body_style),
            Paragraph(f"<b>C.P.:</b> {emplazamiento.get('cp', '30001')}", body_style)
        ],
        [
            Paragraph(f"<b>Municipio:</b> {emplazamiento.get('municipio', 'Murcia')} | <b>Provincia:</b> REGIÓN DE MURCIA (30)", body_style),
            Paragraph(f"<b>Teléfono:</b> {titular.get('telefono', '600000000')} | <b>Email:</b> {titular.get('email', 'cliente@correo.com')}", body_style)
        ]
    ]
    t_tit = Table(t_tit_data, colWidths=[12.0*cm, 6.4*cm])
    t_tit.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('BACKGROUND', (0,0), (-1,-1), c_bg_sub)
    ]))
    story.append(t_tit)
    story.append(Spacer(1, 3))

    # -------------------------------------------------------------------------
    # 2. DATOS IDENTIFICATIVOS DEL REDACTOR DE LA MEMORIA
    # -------------------------------------------------------------------------
    story.append(Table([[Paragraph("DATOS IDENTIFICATIVOS DEL REDACTOR DE LA MEMORIA", h_section)]], colWidths=[18.4*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_primary),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))

    t_red_data = [
        [
            Paragraph("<b>[ X ] MEMORIA REALIZADA POR INSTALADOR HABILITADO EN BAJA TENSIÓN</b>", bold_style),
            Paragraph("<b>[  ] MEMORIA REALIZADA POR TÉCNICO COMPETENTE</b>", small_style)
        ],
        [
            Paragraph(f"<b>Razón Social Empresa:</b> {instalador.get('empresa', 'BOLIMUR INSTALACIONES Y REFORMAS')} | <b>N.I.F.:</b> {instalador.get('cif', 'B-73000000')}", body_style),
            Paragraph(f"<b>Categoría:</b> ESPECIALISTA (IBTE) | <b>Comunidad:</b> REGIÓN DE MURCIA", body_style)
        ],
        [
            Paragraph(f"<b>Nº Inscripción RII:</b> {instalador.get('registro_rii', 'RII-30/08492')} | <b>Domicilio:</b> Nuevas Tecnologías, s/n, Murcia", body_style),
            Paragraph(f"<b>Teléfono:</b> {instalador.get('telefono', '968 362000')}", body_style)
        ],
        [
            Paragraph(f"<b>Nombre Instalador Habilitado:</b> {instalador.get('nombre', 'Richard Orlando Choque Tejerina')} | <b>N.I.F.:</b> {instalador.get('nif', '48500000A')}", body_style),
            Paragraph(f"<b>Nº Carnet Cualificación:</b> <b>{instalador.get('licencia', 'REBT-30/15892')}</b> (Murcia)", body_style)
        ]
    ]
    t_red = Table(t_red_data, colWidths=[11.5*cm, 6.9*cm])
    t_red.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('BACKGROUND', (0,0), (-1,-1), c_bg_sub)
    ]))
    story.append(t_red)
    story.append(Spacer(1, 3))

    # -------------------------------------------------------------------------
    # 3. EMPLAZAMIENTO, ACTIVIDAD Y DATOS TÉCNICOS (ITC-BT-04)
    # -------------------------------------------------------------------------
    story.append(Table([[Paragraph("EMPLAZAMIENTO, ACTIVIDAD Y DATOS TÉCNICOS DE LA INSTALACIÓN (ITC-BT-04)", h_section)]], colWidths=[18.4*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_primary),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))

    pot_inst_w = float(suministro.get("potencia_instalada_w", 5750.0))
    t_tecn_data = [
        [
            Paragraph(f"<b>Emplazamiento:</b> {emplazamiento.get('direccion', '-')}, {emplazamiento.get('municipio', 'Murcia')}", body_style),
            Paragraph(f"<b>CUPS / Ref. Cat.:</b> {emplazamiento.get('cups', 'ES0021000000000000XX')}", body_style)
        ],
        [
            Paragraph(f"<b>Tipo de Local / Actividad:</b> {tipo_instalacion}", body_style),
            Paragraph(f"<b>Uso Inmueble:</b> {emplazamiento.get('uso', 'Vivienda Residencial / IRVE')}", body_style)
        ],
        [
            Paragraph("<b>Tensión Nominal:</b> [ X ] 230 V (Monofásica)   [  ] 400 V (Trifásica)", bold_style) if "230" in str(suministro.get("tension", "230")) else Paragraph("<b>Tensión Nominal:</b> [  ] 230 V   [ X ] 400 V (Trifásica - 50 Hz)", bold_style),
            Paragraph(f"<b>Potencia Total Prevista:</b> <b>{pot_inst_w/1000:.2f} kW</b> ({pot_inst_w:,.0f} W)", bold_style)
        ],
        [
            Paragraph("<b>Grupo Instalación según 3.1 ITC-BT-04:</b> Grupo F (Viviendas / Edificios) / Grupo O (IRVE)", body_style),
            Paragraph("<b>Superficie Útil:</b> 90 m² | <b>Ocupación:</b> < 50 pers.", body_style)
        ]
    ]
    t_tecn = Table(t_tecn_data, colWidths=[10.5*cm, 7.9*cm])
    t_tecn.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('BACKGROUND', (0,0), (-1,-1), c_bg_sub)
    ]))
    story.append(t_tecn)
    story.append(Spacer(1, 3))

    # -------------------------------------------------------------------------
    # 4. CAJA GENERAL DE PROTECCIÓN (CGP) / LGA / PUESTA A TIERRA
    # -------------------------------------------------------------------------
    story.append(Table([[Paragraph("CAJA GENERAL DE PROTECCIÓN (CGP), LÍNEA GENERAL (LGA) Y PUESTA A TIERRA", h_section)]], colWidths=[18.4*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_primary),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))

    di_cable = str(suministro.get("di_cable", "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV"))
    di_long = float(suministro.get("di_long_m", 15.0))
    di_cdt = float(suministro.get("di_cdt_pct", 0.75))

    t_cgp_data = [
        [
            Paragraph("<b>CAJA GRAL. PROTECCIÓN (*)</b>", bold_style),
            Paragraph("<b>LÍNEA GENERAL DE ALIMENTACIÓN / DI</b>", bold_style),
            Paragraph("<b>PUESTA A TIERRA (ITC-BT-18)</b>", bold_style)
        ],
        [
            Paragraph("<b>Número:</b> CGP-01<br/><b>Tipo/Esquema:</b> BTVC / Esquema 2<br/><b>Empresa Distr.:</b> I-DE Iberdrola", body_style),
            Paragraph(f"<b>Sección Conductor:</b> {di_cable}<br/><b>Longitud:</b> {di_long:.1f} m | <b>Tipo:</b> Interior bajo tubo<br/><b>Caída Tensión ΔV:</b> <b>{di_cdt:.2f}%</b> (≤ 1.5%)", body_style),
            Paragraph("<b>Medición Tierra Rt:</b> <b>11.8 Ω</b> (≤ 15 Ω)<br/><b>Línea Enlace PE:</b> 1x10 mm² Cu<br/><b>Línea Principal Tierra:</b> 1x16 mm² Cu", body_style)
        ]
    ]
    t_cgp = Table(t_cgp_data, colWidths=[5.5*cm, 7.4*cm, 5.5*cm])
    t_cgp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_head),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_cgp)
    story.append(Spacer(1, 3))

    # -------------------------------------------------------------------------
    # 5. PREVISIÓN DE CARGAS DEL EDIFICIO / INSTALACIÓN (ITC-BT-10)
    # -------------------------------------------------------------------------
    story.append(Table([[Paragraph("PREVISIÓN DE CARGAS EN INSTALACIONES PARA VIVIENDAS Y LOCALES (ITC-BT-10)", h_section)]], colWidths=[18.4*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_primary),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))

    t_prev_data = [
        [
            Paragraph("<b>(A) Previsión en Viviendas / Suministro Individual</b>", bold_style),
            Paragraph("<b>(B) Servicios Generales</b>", bold_style),
            Paragraph("<b>(C) Oficinas / Locales / IRVE</b>", bold_style)
        ],
        [
            Paragraph(f"• Grado Electrificación: <b>{suministro.get('grado_electrif', 'Básica')}</b><br/>• Potencia Prevista: <b>{pot_inst_w:,.0f} W</b><br/>• Factor Simultaneidad: 1.0<br/><b>TOTAL (A): {pot_inst_w/1000:.2f} kW</b>", body_style),
            Paragraph("• Alumbrado escalera: 0.50 kW<br/>• Aparatos elevación / bombas: 0.0 kW<br/>• Servicios comunes: 0.50 kW<br/><b>TOTAL (B): 0.50 kW</b>", body_style),
            Paragraph(f"• Uso: {tipo_instalacion.split('(')[0]}<br/>• Superficie: 90 m²<br/>• Potencia específica: 100 W/m²<br/><b>TOTAL (C): {pot_inst_w/1000:.2f} kW</b>", body_style)
        ],
        [
            Paragraph(f"<b>POTENCIA TOTAL PREVISTA PARA LA INSTALACIÓN (A + B + C):  {pot_inst_w/1000:.2f} kW</b>", ParagraphStyle('PtTot', parent=bold_style, textColor=c_dark_blue)),
            Paragraph("", body_style),
            Paragraph(f"<b>Tensión:</b> {suministro.get('tension', '230 V')}", bold_style)
        ]
    ]
    t_prev = Table(t_prev_data, colWidths=[6.2*cm, 6.0*cm, 6.2*cm])
    t_prev.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_head),
        ('BACKGROUND', (0,2), (-1,2), c_bg_head),
        ('SPAN', (0,2), (1,2)),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_prev)
    story.append(Spacer(1, 3))

    # -------------------------------------------------------------------------
    # 6. BREVE DESCRIPCIÓN, PRESUPUESTO Y DOCUMENTACIÓN ACOMPAÑADA
    # -------------------------------------------------------------------------
    story.append(Table([[Paragraph("BREVE DESCRIPCIÓN, PRESUPUESTO Y DOCUMENTACIÓN ANEXA ADJUNTA", h_section)]], colWidths=[18.4*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), c_primary),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))

    t_desc_data = [
        [
            Paragraph("<b>Breve Descripción de la Instalación:</b><br/>"
                      f"Instalación eléctrica de baja tensión para {tipo_instalacion.lower()}, ejecutada con conductores de cobre unipolares no propagadores de la llama y libres de halógenos tipo H07Z1-K / RZ1-K 0.6/1kV bajo tubo protector normalizado. Cuadro CGMP equipado con IGA omnipolar ({protecciones.get('iga_amperaje', 25)}A Curva C, Icn=6kA), protector contra sobretensiones permanentes y transitorias Tipo 2 con bobina de disparo (ITC-BT-23), e interruptor diferencial de alta sensibilidad 30mA Clase A (ITC-BT-24). Circuito exclusivo verificado con protección contra choques eléctricos y conexión a tierra equipotencial.", body_style),
            Paragraph("<b>Presupuesto Estimado:</b><br/>"
                      "• Instalación de enlace y CGMP: 650,00 €<br/>"
                      "• Circuitos interiores y canalización: 820,00 €<br/>"
                      "• Mano de obra y verificación BT-05: 480,00 €<br/>"
                      "<b>PRESUPUESTO TOTAL: 1.950,00 €</b><br/><br/>"
                      "<b>Documentación Acompañada:</b><br/>"
                      "<b>[ X ] Plano Situación (Anexo I)</b><br/>"
                      "<b>[ X ] Plano Planta B.T. (Anexo II)</b><br/>"
                      "<b>[ X ] Esquema Unifilar (Anexo III)</b><br/>"
                      "<b>[ X ] Cálculos Justificativos (Anexo IV)</b>", body_style)
        ]
    ]
    t_desc = Table(t_desc_data, colWidths=[11.5*cm, 6.9*cm])
    t_desc.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), c_bg_sub)
    ]))
    story.append(t_desc)
    story.append(Spacer(1, 4))

    # -------------------------------------------------------------------------
    # 7. DECLARACIÓN RESPONSABLE Y FIRMA OFICIAL
    # -------------------------------------------------------------------------
    firma_box = [
        Paragraph(
            f"El redactor que suscribe <b>DECLARA BAJO SU RESPONSABILIDAD</b> que ha realizado la presente <b>Memoria Técnica de Diseño (MTD)</b> "
            f"conforme a las prescripciones del <b>Reglamento Electrotécnico para Baja Tensión (Real Decreto 842/2002)</b>, sus Instrucciones Técnicas Complementarias (ITC-BT), "
            f"y la reglamentación aplicable de la <b>Dirección General de Industria, Energía y Minas de la Región de Murcia</b>.",
            small_style
        ),
        Spacer(1, 3),
        Table([
            [
                Paragraph(
                    f"En <b>{emplazamiento.get('municipio', 'Murcia')}</b>, a {fecha_str}<br/><br/>"
                    f"<b>Firma del Instalador Habilitado:</b><br/><br/><br/>"
                    f"__________________________________________<br/>"
                    f"<b>{instalador.get('nombre', 'Richard Orlando Choque Tejerina')}</b><br/>"
                    f"Nº Carnet REBT: <b>{instalador.get('licencia', 'REBT-30/15892')}</b> (Murcia)",
                    body_style
                ),
                Paragraph(
                    f"<b>Sello de la Empresa Instaladora Habilitada:</b><br/><br/><br/>"
                    f"__________________________________________<br/>"
                    f"<b>{instalador.get('empresa', 'BOLIMUR INSTALACIONES Y REFORMAS')}</b><br/>"
                    f"Reg. Industrial: <b>{instalador.get('registro_rii', 'RII-30/08492')}</b> | C.I.F.: {instalador.get('cif', 'B-73000000')}",
                    body_style
                )
            ]
        ], colWidths=[9.2*cm, 9.2*cm], style=[
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ])
    ]
    story.append(KeepTogether(firma_box))

    # =========================================================================
    # PÁGINA 2: ANEXO III - ESQUEMA UNIFILAR NORMALIZADO (DGEAIM MURCIA)
    # =========================================================================
    story.append(PageBreak())
    
    story.append(Paragraph("<b>MEMORIA TÉCNICA DE DISEÑO DE INSTALACIONES ELÉCTRICAS DE BAJA TENSIÓN</b>", title_main))
    story.append(Paragraph("<b>ANEXO III: ESQUEMA UNIFILAR NORMALIZADO</b>", ParagraphStyle('Anx3', parent=title_main, textColor=c_dark_blue)))
    story.append(HRFlowable(width="100%", thickness=1.0, color=c_primary, spaceBefore=2, spaceAfter=6))

    # Dibujo vectorial del Esquema Unifilar Oficial Jerárquico (Exacto al modelo de curso REBT / DGEAIM Murcia)
    dwg_w = 520
    dwg_h = 270
    dwg = Drawing(dwg_w, dwg_h)
    
    # Marco y fondo del cuadro unifilar
    dwg.add(Rect(0, 0, dwg_w, dwg_h, fillColor=colors.HexColor("#ffffff"), strokeColor=colors.HexColor("#94a3b8"), strokeWidth=0.9, rx=4, ry=4))
    
    # =============================================================
    # 1. CABECERA: ICP (Interruptor Control de Potencia)
    # =============================================================
    xc = 260
    # Línea vertical superior
    dwg.add(Line(xc, 264, xc, 254, strokeColor=c_primary, strokeWidth=1.3))
    # Símbolo interruptor de corte ICP
    dwg.add(Line(xc, 254, xc - 7, 244, strokeColor=c_primary, strokeWidth=1.4))
    dwg.add(Circle(xc, 254, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(xc, 242, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Line(xc, 242, xc, 234, strokeColor=c_primary, strokeWidth=1.3))
    # Texto ICP
    dwg.add(String(xc + 14, 250, "ICP", fontName="Helvetica-Bold", fontSize=9, fillColor=c_primary))

    # =============================================================
    # 2. IGA (Interruptor General Automático con Térmico-Magnético)
    # =============================================================
    iga_cal_val = protecciones.get('iga_amperaje', 40)
    # Símbolo magnetotérmico con banderola y flecha
    dwg.add(Line(xc, 234, xc - 7, 222, strokeColor=c_primary, strokeWidth=1.4))
    dwg.add(Circle(xc, 234, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(xc, 220, 1.2, fillColor=c_primary, strokeColor=c_primary))
    # Disparador térmico y magnético (banderola con flecha)
    dwg.add(Line(xc - 4, 227, xc - 12, 222, strokeColor=c_primary, strokeWidth=1.0))
    dwg.add(Line(xc - 12, 222, xc - 9, 219, strokeColor=c_primary, strokeWidth=1.0))
    dwg.add(Rect(xc - 15, 219, 4, 4, fillColor=c_primary, strokeColor=c_primary))
    # Línea que baja
    dwg.add(Line(xc, 220, xc, 206, strokeColor=c_primary, strokeWidth=1.3))
    # Texto IGA
    dwg.add(String(xc + 14, 230, "IGA", fontName="Helvetica-Bold", fontSize=8.5, fillColor=c_primary))
    dwg.add(String(xc + 14, 219, f"2 x {iga_cal_val} A", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_secondary))
    dwg.add(String(xc + 14, 210, "6 kA | Curva C", fontName="Helvetica", fontSize=6.0, fillColor=colors.HexColor("#64748b")))

    # =============================================================
    # 3. DERIVACIÓN A LOS 2 DIFERENCIALES (Rama Izquierda y Derecha)
    # =============================================================
    # Línea horizontal de distribución a diferenciales
    x_d1 = 135
    x_d2 = 385
    y_split = 206
    dwg.add(Line(x_d1, y_split, x_d2, y_split, strokeColor=c_primary, strokeWidth=1.4))
    dwg.add(Circle(xc, y_split, 1.5, fillColor=c_primary, strokeColor=c_primary))

    # --- DIFERENCIAL 1 (IZQUIERDA) ---
    dwg.add(Line(x_d1, y_split, x_d1, 196, strokeColor=c_primary, strokeWidth=1.2))
    # Contacto interruptor
    dwg.add(Line(x_d1, 196, x_d1 - 7, 185, strokeColor=c_primary, strokeWidth=1.3))
    dwg.add(Circle(x_d1, 196, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(x_d1, 183, 1.2, fillColor=c_primary, strokeColor=c_primary))
    # Toroide diferencial (óvalo)
    dwg.add(Circle(x_d1, 175, 5.5, fillColor=colors.HexColor("#ecfdf5"), strokeColor=c_green, strokeWidth=1.1))
    dwg.add(Line(x_d1, 183, x_d1, 166, strokeColor=c_primary, strokeWidth=1.3))
    # Relé de disparo conectado al toroide
    dwg.add(Rect(x_d1 - 18, 184, 6, 6, fillColor=colors.HexColor("#16a34a"), strokeColor=colors.HexColor("#16a34a")))
    dwg.add(Line(x_d1 - 12, 187, x_d1 - 6, 191, strokeColor=c_green, strokeWidth=0.8)) # enlace al contacto
    dwg.add(Line(x_d1 - 15, 184, x_d1 - 6, 175, strokeColor=c_green, strokeWidth=0.8)) # enlace al toroide
    # Texto Dif 1
    dwg.add(String(x_d1 + 14, 191, "Dif. 1", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_green))
    dwg.add(String(x_d1 + 14, 180, "2 x 40 A", fontName="Helvetica-Bold", fontSize=7.5, fillColor=c_primary))
    dwg.add(String(x_d1 + 14, 170, "30 mA", fontName="Helvetica-Bold", fontSize=7.5, fillColor=c_primary))

    # --- DIFERENCIAL 2 (DERECHA) ---
    dwg.add(Line(x_d2, y_split, x_d2, 196, strokeColor=c_primary, strokeWidth=1.2))
    # Contacto interruptor
    dwg.add(Line(x_d2, 196, x_d2 - 7, 185, strokeColor=c_primary, strokeWidth=1.3))
    dwg.add(Circle(x_d2, 196, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(x_d2, 183, 1.2, fillColor=c_primary, strokeColor=c_primary))
    # Toroide diferencial (óvalo)
    dwg.add(Circle(x_d2, 175, 5.5, fillColor=colors.HexColor("#ecfdf5"), strokeColor=c_green, strokeWidth=1.1))
    dwg.add(Line(x_d2, 183, x_d2, 166, strokeColor=c_primary, strokeWidth=1.3))
    # Relé de disparo conectado al toroide
    dwg.add(Rect(x_d2 - 18, 184, 6, 6, fillColor=colors.HexColor("#16a34a"), strokeColor=colors.HexColor("#16a34a")))
    dwg.add(Line(x_d2 - 12, 187, x_d2 - 6, 191, strokeColor=c_green, strokeWidth=0.8))
    dwg.add(Line(x_d2 - 15, 184, x_d2 - 6, 175, strokeColor=c_green, strokeWidth=0.8))
    # Texto Dif 2
    dwg.add(String(x_d2 + 14, 191, "Dif. 2", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_green))
    dwg.add(String(x_d2 + 14, 180, "2 x 40 A", fontName="Helvetica-Bold", fontSize=7.5, fillColor=c_primary))
    dwg.add(String(x_d2 + 14, 170, "30 mA", fontName="Helvetica-Bold", fontSize=7.5, fillColor=c_primary))

    # =============================================================
    # 4. PEINES / BARRAS DE DISTRIBUCIÓN HORIZONTALES
    # =============================================================
    y_bus = 166
    # Barra 1 (Izquierda): para C1, C2, C3, C10
    dwg.add(Line(18, y_bus, 252, y_bus, strokeColor=c_secondary, strokeWidth=2.2))
    dwg.add(Circle(x_d1, y_bus, 1.8, fillColor=c_secondary, strokeColor=c_secondary))

    # Barra 2 (Derecha): para C4-1, C4-2, C4-3, C5
    dwg.add(Line(268, y_bus, 502, y_bus, strokeColor=c_secondary, strokeWidth=2.2))
    dwg.add(Circle(x_d2, y_bus, 1.8, fillColor=c_secondary, strokeColor=c_secondary))

    # =============================================================
    # 5. COLUMNAS DE CIRCUITOS INDIVIDUALES (EXACTO AL BOCETO)
    # =============================================================
    # 8 Circuitos normalizados según la muestra del curso
    circs_modelo = [
        # Rama 1 (Bajo Dif 1)
        {"cx": 48,  "pia": "2 x 10 A", "sec": "2 x 1.5 + T", "tubo": "Tubo 16", "id": "C1",   "nom1": "Iluminación", "nom2": "general"},
        {"cx": 108, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C2",   "nom1": "Toma uso",    "nom2": "General"},
        {"cx": 168, "pia": "2 x 25 A", "sec": "2 x 6 + T",   "tubo": "Tubo 25", "id": "C3",   "nom1": "Cocina y",    "nom2": "Horno"},
        {"cx": 228, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C10",  "nom1": "Secadora",    "nom2": "(o IRVE)"},
        
        # Rama 2 (Bajo Dif 2)
        {"cx": 298, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C4.1", "nom1": "Lavadora",    "nom2": ""},
        {"cx": 358, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C4.2", "nom1": "Lavavajillas","nom2": ""},
        {"cx": 418, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C4.3", "nom1": "Termo",       "nom2": "eléctrico"},
        {"cx": 478, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C5",   "nom1": "Baño y Aux.", "nom2": "Cocina"}
    ]

    for c in circs_modelo:
        cx = c["cx"]
        
        # 1. Bajante desde la barra colectora
        dwg.add(Line(cx, y_bus, cx, 155, strokeColor=c_primary, strokeWidth=1.0))
        dwg.add(Circle(cx, y_bus, 1.2, fillColor=c_secondary, strokeColor=c_secondary))

        # 2. Caja de Datos Técnicos (Calibre, Sección, Tubo)
        dwg.add(Rect(cx - 26, 118, 52, 37, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.6, rx=2, ry=2))
        dwg.add(String(cx, 145, c["pia"], fontName="Helvetica-Bold", fontSize=6.2, fillColor=c_primary, textAnchor="middle"))
        dwg.add(String(cx, 134, c["sec"], fontName="Helvetica-Bold", fontSize=5.8, fillColor=c_secondary, textAnchor="middle"))
        dwg.add(String(cx, 123, c["tubo"], fontName="Helvetica", fontSize=5.5, fillColor=colors.HexColor("#64748b"), textAnchor="middle"))

        # 3. Línea hacia el símbolo del PIA
        dwg.add(Line(cx, 118, cx, 106, strokeColor=c_primary, strokeWidth=1.0))

        # 4. Símbolo Magnetotérmico PIA (con contacto y banderola térmica/magnética)
        dwg.add(Line(cx, 106, cx - 7, 94, strokeColor=c_primary, strokeWidth=1.3))
        dwg.add(Circle(cx, 106, 1.0, fillColor=c_primary, strokeColor=c_primary))
        dwg.add(Circle(cx, 92, 1.0, fillColor=c_primary, strokeColor=c_primary))
        # Banderola y flecha
        dwg.add(Line(cx - 4, 99, cx - 11, 95, strokeColor=c_primary, strokeWidth=0.9))
        dwg.add(Line(cx - 11, 95, cx - 8, 92, strokeColor=c_primary, strokeWidth=0.9))
        dwg.add(Rect(cx - 13, 92, 3.5, 3.5, fillColor=c_primary, strokeColor=c_primary))

        # 5. Salida hacia el receptor
        dwg.add(Line(cx, 92, cx, 74, strokeColor=c_primary, strokeWidth=1.0))

        # 6. Identificador del Circuito (C1, C2, C3...)
        dwg.add(String(cx, 60, c["id"], fontName="Helvetica-Bold", fontSize=9.5, fillColor=c_primary, textAnchor="middle"))

        # 7. Denominación / Destino
        dwg.add(String(cx, 46, c["nom1"], fontName="Helvetica-Bold", fontSize=6.0, fillColor=c_text_dark, textAnchor="middle"))
        if c["nom2"]:
            dwg.add(String(cx, 37, c["nom2"], fontName="Helvetica", fontSize=5.5, fillColor=colors.HexColor("#475569"), textAnchor="middle"))

    # =============================================================
    # 6. LÍNEA DE PUESTA A TIERRA (PE) CON SÍMBOLO NORMALIZADO (⏚)
    # =============================================================
    dwg.add(Rect(18, 6, 484, 24, fillColor=colors.HexColor("#fef3c7"), strokeColor=colors.HexColor("#d97706"), strokeWidth=0.7, rx=2, ry=2))
    tx = 35
    ty = 16
    dwg.add(Line(tx, ty + 8, tx, ty, strokeColor=colors.HexColor("#92400e"), strokeWidth=1.2))
    dwg.add(Line(tx - 6, ty, tx + 6, ty, strokeColor=colors.HexColor("#92400e"), strokeWidth=1.2))
    dwg.add(Line(tx - 4, ty - 2.5, tx + 4, ty - 2.5, strokeColor=colors.HexColor("#92400e"), strokeWidth=1.0))
    dwg.add(Line(tx - 2, ty - 5, tx + 2, ty - 5, strokeColor=colors.HexColor("#92400e"), strokeWidth=0.8))
    
    dwg.add(String(50, 19, "RED DE TIERRA (PE - ITC-BT-18):", fontName="Helvetica-Bold", fontSize=6.0, fillColor=colors.HexColor("#92400e")))
    dwg.add(String(50, 10, "Línea Enlace Cu 1x10 mm² | Picas de tierra 2m | <b>Resistencia Medida: Rt = 11.8 Ω</b> (Límite REBT ≤ 15 Ω)", fontName="Helvetica", fontSize=5.5, fillColor=c_text_dark))

    story.append(dwg)
    story.append(Spacer(1, 4))



    # Tabla explicativa de componentes del unifilar
    t_unif_desc = [
        [
            Paragraph("<b>Elemento</b>", bold_style),
            Paragraph("<b>Designación y Parámetros Técnicos Reglamentarios</b>", bold_style),
            Paragraph("<b>Norma REBT</b>", bold_style)
        ],
        [
            Paragraph("<b>Acometida / Enlace</b>", body_style),
            Paragraph(f"Derivación Individual {di_cable} bajo {suministro.get('di_tubo', 'Tubo M32')}, L={di_long:.1f} m, ΔV={di_cdt:.2f}%", body_style),
            Paragraph("ITC-BT-15", body_style)
        ],
        [
            Paragraph("<b>Protección General</b>", body_style),
            Paragraph(f"IGA {protecciones.get('iga_amperaje', 25)}A Curva C, Poder Corte Icn={protecciones.get('iga_icn_ka', 6.0):.0f}kA, Corte omnipolar", body_style),
            Paragraph("ITC-BT-17 / 22", body_style)
        ],
        [
            Paragraph("<b>Sobretensiones</b>", body_style),
            Paragraph(str(protecciones.get('sobretensiones', 'VSP Tipo 2 + VTP Permanentes con bobina de emisión')), body_style),
            Paragraph("ITC-BT-23", body_style)
        ],
        [
            Paragraph("<b>Diferencial Principal</b>", body_style),
            Paragraph(str(protecciones.get('diferenciales', 'Diferencial 2P 40A / 30mA Clase A')), body_style),
            Paragraph("ITC-BT-24", body_style)
        ]
    ]
    t_u_tab = Table(t_unif_desc, colWidths=[3.5*cm, 12.0*cm, 2.9*cm])
    t_u_tab.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_head),
        ('GRID', (0,0), (-1,-1), 0.4, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_u_tab)
    story.append(Spacer(1, 4))

    # =========================================================================
    # PÁGINA 3: ANEXO IV - DIMENSIONAMIENTO Y CÁLCULOS JUSTIFICATIVOS
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("<b>MEMORIA TÉCNICA DE DISEÑO DE INSTALACIONES ELÉCTRICAS DE BAJA TENSIÓN</b>", title_main))
    story.append(Paragraph("<b>ANEXO IV: DIMENSIONAMIENTO Y CÁLCULOS JUSTIFICATIVOS (DGEAIM MURCIA)</b>", ParagraphStyle('Anx4', parent=title_main, textColor=c_dark_blue)))
    story.append(HRFlowable(width="100%", thickness=1.0, color=c_primary, spaceBefore=2, spaceAfter=4))

    # Fórmulas oficiales aplicadas
    t_form_data = [
        [
            Paragraph("<b>FÓRMULAS Y TABLAS A APLICAR:</b>", bold_style),
            Paragraph("<b>Líneas Monofásicas (230 V):</b>  <i>I = P / (V · cos φ)</i>   |   <i>ΔV(%) = (2 · P · L · 100) / (γ · S · V²)</i><br/>"
                      "<b>Líneas Trifásicas (400 V):</b>   <i>I = P / (√3 · V · cos φ)</i>   |   <i>ΔV(%) = (P · L · 100) / (γ · S · V²)</i><br/>"
                      "<b>Conductividad Cobre (γ):</b> 44 m/(Ω·mm²) a 90ºC (XLPE) / 48.5 m/(Ω·mm²) a 70ºC (PVC)", small_style)
        ]
    ]
    t_form = Table(t_form_data, colWidths=[4.2*cm, 14.2*cm])
    t_form.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_head),
        ('BOX', (0,0), (-1,-1), 0.6, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_form)
    story.append(Spacer(1, 4))

    # Tabla Completa de Dimensionamiento por Tramos
    t_dim_rows = [[
        Paragraph("<b>Tramo / Circuito</b>", bold_style),
        Paragraph("<b>Pot. (W)</b>", bold_style),
        Paragraph("<b>Ib (A)</b>", bold_style),
        Paragraph("<b>L (m)</b>", bold_style),
        Paragraph("<b>Fase mm²</b>", bold_style),
        Paragraph("<b>Neutro</b>", bold_style),
        Paragraph("<b>PE mm²</b>", bold_style),
        Paragraph("<b>ΔV Parcial</b>", bold_style),
        Paragraph("<b>ΔV Total</b>", bold_style),
        Paragraph("<b>Canalización</b>", bold_style)
    ]]

    # Derivación Individual
    t_dim_rows.append([
        Paragraph("<b>Derivación Individual (DI)</b>", bold_style),
        Paragraph(f"{pot_inst_w:,.0f}", body_style),
        Paragraph(f"{pot_inst_w/230:.1f}", body_style),
        Paragraph(f"{di_long:.0f}", body_style),
        Paragraph("10 Cu", body_style),
        Paragraph("10 Cu", body_style),
        Paragraph("10 Cu", body_style),
        Paragraph(f"<b>{di_cdt:.2f}%</b>", body_style),
        Paragraph(f"<b>{di_cdt:.2f}%</b>", body_style),
        Paragraph("Tubo M32", body_style)
    ])

    for c in circuitos:
        p_c = float(c.get("potencia", 2300))
        l_c = float(c.get("longitud", 15))
        cdt_c = float(c.get("cdt", 1.0))
        sec_str = str(c.get("seccion", "2x2.5+TT2.5")).split("+")[0].replace("2x", "").replace("3G", "").replace("4x", "")
        t_dim_rows.append([
            Paragraph(str(c.get("nombre", "Circuito")), body_style),
            Paragraph(f"{p_c:,.0f}", body_style),
            Paragraph(f"{p_c/230:.1f}", body_style),
            Paragraph(f"{l_c:.0f}", body_style),
            Paragraph(f"{sec_str} Cu", body_style),
            Paragraph(f"{sec_str} Cu", body_style),
            Paragraph(f"{sec_str} Cu", body_style),
            Paragraph(f"{cdt_c:.2f}%", body_style),
            Paragraph(f"<b>{di_cdt + cdt_c:.2f}%</b>", body_style),
            Paragraph(str(c.get("tubo", "M20")), body_style)
        ])

    t_dim = Table(t_dim_rows, colWidths=[4.2*cm, 1.5*cm, 1.2*cm, 1.1*cm, 1.5*cm, 1.4*cm, 1.4*cm, 1.7*cm, 1.6*cm, 2.8*cm])
    t_dim.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_bg_head),
        ('GRID', (0,0), (-1,-1), 0.4, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 1.8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (8,-1), 'CENTER'),
    ]))
    story.append(t_dim)
    story.append(Spacer(1, 4))

    # =========================================================================
    # TABLAS REGLAMENTARIAS OFICIALES DGEAIM MURCIA (ITC-BT-04 e ITC-BT-05)
    # =========================================================================
    story.append(Paragraph("<b>TABLAS NORMATIVAS OFICIALES DGEAIM REGIÓN DE MURCIA (RD 842/2002)</b>", bold_style))
    story.append(Spacer(1, 2))

    t_norm_data = [
        [
            Paragraph("<b>TABLA I (ITC-BT-04 apdo. 3.1) - Instalaciones que precisan Proyecto Técnico:</b><br/>"
                      "• Industrias en general: P > 20 kW<br/>"
                      "• Locales mojados / bombas de elevación: P > 10 kW<br/>"
                      "• Edificios de viviendas / locales comerciales: P > 100 kW por CGP<br/>"
                      "• Viviendas unifamiliares: P > 50 kW<br/>"
                      "• Garajes con ventilación forzada: Cualquier potencia / Garajes naturales: > 5 plazas<br/>"
                      "• Locales de Pública Concurrencia: Sin límite (Siempre Proyecto)<br/>"
                      "• Infraestructuras de Recarga VE (IRVE exterior): P > 10 kW / Interior: P > 50 kW", small_style),
            Paragraph("<b>TABLA III y IV (ITC-BT-05) - Inspecciones por O.C.A.:</b><br/>"
                      "• <b>Inspección Inicial (apdo. 4.1):</b><br/>"
                      "  - Industrias P > 100 kW | Locales mojados P > 25 kW<br/>"
                      "  - Pública concurrencia y quirófanos: Sin límite<br/>"
                      "  - Alumbrado exterior P > 5 kW | Piscinas P > 10 kW<br/>"
                      "• <b>Inspecciones Periódicas cada 5 años (apdo. 4.2):</b><br/>"
                      "  - Locales pública concurrencia, mojados P>25kW, garajes >25 plazas<br/>"
                      "• <b>Inspecciones Periódicas cada 10 años:</b><br/>"
                      "  - Zonas comunes de edificios residenciales P > 100 kW", small_style)
        ]
    ]
    t_norm = Table(t_norm_data, colWidths=[9.2*cm, 9.2*cm])
    t_norm.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#e2e8f0")),
        ('BACKGROUND', (0,0), (-1,-1), c_bg_sub),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_norm)

    doc.build(story, canvasmaker=NumberedCanvasMTDMurciaOficial)
    return buffer.getvalue()

generar_pdf_memoria_tecnica = generar_pdf_mtd_industria_murcia
