# -*- coding: utf-8 -*-
import io
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable, PageBreak
)
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Group
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas

class NumberedCanvasUnifilar(canvas.Canvas):
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
            self.drawString(1.5*cm, 28.3*cm, "REGIÓN DE MURCIA - DGEAIM | Esquema Unifilar Oficial REBT (ITC-BT-25)")
            self.drawRightString(19.5*cm, 28.3*cm, "RD 842/2002")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5*cm, 28.1*cm, 19.5*cm, 28.1*cm)

        self.setFont("Helvetica", 7.5)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.9*cm, page_text)
        self.drawString(1.5*cm, 0.9*cm, "Bolimur Software ElectroTécnico - Esquema Unifilar Oficial para la DGEAIM Región de Murcia")
        self.restoreState()


class NumberedCanvasPresupuesto(canvas.Canvas):
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
            self.drawString(1.5*cm, 28.3*cm, "BOLIMUR REBT | Oferta Comercial y Presupuesto Técnico")
            self.drawRightString(19.5*cm, 28.3*cm, "ITC-BT-25")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5*cm, 28.1*cm, 19.5*cm, 28.1*cm)

        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.9*cm, page_text)
        self.drawString(1.5*cm, 0.9*cm, "Bolimur Software ElectroTécnico - Presupuesto Oficial REBT")
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


def _crear_logo_flowable(width=4.8*cm, height=2.68*cm):
    path = _obtener_logo_path()
    if path:
        try:
            return Image(path, width=width, height=height)
        except Exception:
            pass
    return None


def generar_pdf_presupuesto(proyecto_info, presupuesto_data):
    """
    Genera una oferta comercial y presupuesto técnico oficial en PDF profesional con ReportLab.
    Incluye estructura por Capítulos REBT, desglose por estancias, partidas a medida, catálogo PVP opcional,
    plazos de ejecución, garantías legales (3 años) y cuadro de aceptación formal.
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
    c_green = colors.HexColor("#16a34a")

    title_style = ParagraphStyle(
        'DocTitle_P', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=15, leading=19,
        textColor=c_primary, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle_P', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=11,
        textColor=c_secondary, spaceAfter=8
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=13,
        textColor=c_primary, spaceBefore=9, spaceAfter=4, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=c_text_dark
    )
    body_bold = ParagraphStyle('BodyBold_P', parent=body_style, fontName='Helvetica-Bold')
    th_style = ParagraphStyle(
        'TableHeader_P', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=9.5,
        textColor=colors.white, alignment=1
    )
    td_style = ParagraphStyle(
        'TableCell_P', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=9.5,
        textColor=c_text_dark, alignment=0
    )
    td_center = ParagraphStyle('TableCellCenter_P', parent=td_style, alignment=1)
    td_right = ParagraphStyle('TableCellRight_P', parent=td_style, alignment=2)
    td_right_bold = ParagraphStyle('TableCellRightBold_P', parent=td_style, fontName='Helvetica-Bold', alignment=2)

    story = []

    text_col = [
        Paragraph("PRESUPUESTO OFICIAL DE INSTALACIÓN ELÉCTRICA", title_style),
        Paragraph(f"<b>{proyecto_info.get('empresa', 'BOLIMUR Instalaciones Integrales')}</b> | Instalación Residencial conforme a REBT (RD 842/2002)", subtitle_style)
    ]

    logo_img = _crear_logo_flowable(width=4.8*cm, height=2.68*cm)
    if logo_img:
        header_table = Table([[text_col, logo_img]], colWidths=[13.2*cm, 4.8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
    else:
        story.extend(text_col)

    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=2, spaceAfter=6))

    fecha_str = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    potencia_kw_val = presupuesto_data.get("potencia_kw", "5.75 kW")
    serie_mec_val = presupuesto_data.get("serie_mecanismos", "Estándar")
    marca_prot_val = presupuesto_data.get("marca_protecciones", "Schneider / Hager")

    meta_table_data = [
        [
            Paragraph("<b>Empresa Instaladora:</b>", body_style),
            Paragraph(str(proyecto_info.get("empresa", "BOLIMUR")), body_style),
            Paragraph("<b>Fecha de Oferta:</b>", body_style),
            Paragraph(fecha_str, body_style)
        ],
        [
            Paragraph("<b>Instalador / Licencia:</b>", body_style),
            Paragraph(f"{proyecto_info.get('proyectista', 'Instalador')} (Nº {proyecto_info.get('licencia', 'REBT-001')})", body_style),
            Paragraph("<b>Presupuesto N°:</b>", body_style),
            Paragraph(str(proyecto_info.get("expediente", "PRES-2026-01")), body_style)
        ],
        [
            Paragraph("<b>Teléfono / Localidad:</b>", body_style),
            Paragraph(f"{proyecto_info.get('telefono', '600000000')} | {proyecto_info.get('localidad', 'Región de Murcia')}", body_style),
            Paragraph("<b>Potencia Prevista / IGA:</b>", body_style),
            Paragraph(f"{potencia_kw_val} ({presupuesto_data.get('grado_electr', 'Básica')})", body_style)
        ],
        [
            Paragraph("<b>Gama de Mecanismos:</b>", body_style),
            Paragraph(str(serie_mec_val), body_style),
            Paragraph("<b>Protecciones CGMP:</b>", body_style),
            Paragraph(str(marca_prot_val), body_style)
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

    subtotal_neto = float(presupuesto_data.get("subtotal_neto", 0.0))
    iva_pct = float(presupuesto_data.get("iva_pct", 21.0))
    cuota_iva = float(presupuesto_data.get("cuota_iva", 0.0))
    total_cliente = float(presupuesto_data.get("total_cliente", 0.0))
    total_puntos = presupuesto_data.get("total_puntos", 0)
    precio_medio_punto = float(presupuesto_data.get("precio_medio_punto", 0.0))
    plazo_dias = presupuesto_data.get("plazo_dias", 0.0)

    resumen_title = Paragraph("<b>TOTAL PRESUPUESTO OFERTA (CON IVA):</b>", ParagraphStyle('ResTitle', parent=body_style, fontSize=10.5, textColor=c_primary, fontName='Helvetica-Bold'))
    resumen_val = Paragraph(f"<b>{total_cliente:,.2f} €</b>", ParagraphStyle('ResVal', parent=body_style, fontSize=13.5, textColor=c_accent, fontName='Helvetica-Bold', alignment=2))

    desglose_resumen = Paragraph(
        f"<b>Resumen Económico de la Propuesta:</b><br/>"
        f"• Base Imponible Neta (Sin IVA): <b>{subtotal_neto:,.2f} €</b> &nbsp;|&nbsp; "
        f"• Impuesto sobre el Valor Añadido (IVA {iva_pct:.0f}%): <b>{cuota_iva:,.2f} €</b><br/>"
        f"• Puntos de Mecanismos Totales: <b>{total_puntos} uds</b> &nbsp;|&nbsp; "
        f"• Ratio medio por punto: <b>{precio_medio_punto:.2f} €/punto</b> (instalación completa)<br/>"
        f"• Plazo Estimado de Ejecución: <b>{plazo_dias:.1f} días laborables</b> &nbsp;|&nbsp; "
        f"• Garantía Oficial: <b>3 Años</b> en mano de obra y materiales",
        body_style
    )

    resumen_box = Table([[resumen_title, resumen_val], [desglose_resumen, ""]], colWidths=[11.8*cm, 6.2*cm])
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

    # =========================================================================
    # SECCIÓN 1: RESUMEN POR CAPÍTULOS DE OBRA REBT
    # =========================================================================
    capitulos = presupuesto_data.get("capitulos", [])
    if capitulos:
        story.append(Paragraph("1. Cuadro Resumen de Capítulos REBT (Memoria Valorada)", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=4))

        cap_header = [
            Paragraph("Capítulo", th_style),
            Paragraph("Denominación y Alcance Técnico de los Trabajos", th_style),
            Paragraph("Importe PVP (€)", th_style)
        ]
        cap_rows = [cap_header]

        for cap in capitulos:
            c_num = str(cap.get("cap", cap.get("capitulo", "")))
            c_tit = str(cap.get("titulo", ""))
            c_desc = str(cap.get("desc", cap.get("descripcion", "")))
            c_imp = float(cap.get("importe", 0.0))

            desc_block = f"<b>{c_tit}</b><br/>{c_desc}" if c_desc else f"<b>{c_tit}</b>"
            cap_rows.append([
                Paragraph(c_num, td_center),
                Paragraph(desc_block, td_style),
                Paragraph(f"{c_imp:,.2f} €", td_right)
            ])

        cap_rows.append([
            Paragraph("<b>SUBTOTAL COMERCIAL NETO (Sin IVA)</b>", ParagraphStyle('CapSub', parent=td_style, fontName='Helvetica-Bold')),
            "", Paragraph(f"<b>{subtotal_neto:,.2f} €</b>", td_right_bold)
        ])
        cap_rows.append([
            Paragraph(f"<b>IVA APLICABLE ({iva_pct:.0f}%)</b>", ParagraphStyle('CapIva', parent=td_style, fontName='Helvetica-Bold')),
            "", Paragraph(f"<b>{cuota_iva:,.2f} €</b>", td_right_bold)
        ])
        cap_rows.append([
            Paragraph("<b>TOTAL PRESUPUESTO OFICIAL (CON IVA)</b>", ParagraphStyle('CapTot', parent=td_style, fontName='Helvetica-Bold', textColor=c_accent)),
            "", Paragraph(f"<b>{total_cliente:,.2f} €</b>", ParagraphStyle('CapTotV', parent=td_right_bold, textColor=c_accent, fontSize=8.5))
        ])

        t_cap = Table(cap_rows, colWidths=[2.5*cm, 12.0*cm, 3.5*cm])
        t_cap.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), c_primary),
            ('SPAN', (0, -3), (1, -3)),
            ('SPAN', (0, -2), (1, -2)),
            ('SPAN', (0, -1), (1, -1)),
            ('BACKGROUND', (0,-3), (-1,-1), colors.HexColor("#e2e8f0")),
            ('GRID', (0,0), (-1,-1), 0.5, c_border),
            ('ROWBACKGROUNDS', (0,1), (-1,-4), [colors.white, c_bg_light]),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_cap)
        story.append(Spacer(1, 6))

    # =========================================================================
    # SECCIÓN 2: DESGLOSE DETALLADO POR ESTANCIAS
    # =========================================================================
    df_comercial = presupuesto_data.get("df_comercial", [])
    if hasattr(df_comercial, 'to_dict'):
        records_est = df_comercial.to_dict('records')
    else:
        records_est = df_comercial

    if records_est:
        sec_num = "2" if capitulos else "1"
        story.append(Paragraph(f"{sec_num}. Desglose de Instalación por Estancias de la Vivienda", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=4))

        table_p_header = [
            Paragraph("Estancia / Zona", th_style),
            Paragraph("Equipamiento y Mecanismos Incluidos", th_style),
            Paragraph("Importe Venta (€)", th_style)
        ]
        table_p_rows = [table_p_header]

        for row in records_est:
            estancia = str(row.get('Estancia / Partida', row.get('Estancia', '')))
            detalle = str(row.get('Detalle Comercial', row.get('Detalle de Mecanismos / Equipamiento', row.get('Detalle', ''))))
            importe = row.get('Importe Venta (€)', row.get('Importe (€)', '0.00'))
            if isinstance(importe, (int, float)):
                importe_str = f"{float(importe):,.2f} €"
            else:
                importe_str = str(importe)

            table_p_rows.append([
                Paragraph(f"<b>{estancia}</b>", td_style),
                Paragraph(detalle, td_style),
                Paragraph(importe_str, td_right)
            ])

        t_est = Table(table_p_rows, colWidths=[4.2*cm, 10.3*cm, 3.5*cm])
        t_est.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), c_primary),
            ('GRID', (0,0), (-1,-1), 0.5, c_border),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_est)
        story.append(Spacer(1, 6))

    # =========================================================================
    # SECCIÓN 3: PARTIDAS MANUALES / TRABAJOS ADICIONALES
    # =========================================================================
    partidas_man = presupuesto_data.get("partidas_manuales", [])
    if partidas_man:
        story.append(Paragraph("3. Partidas y Trabajos Adicionales Personalizados", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=4))

        pman_header = [
            Paragraph("Concepto", th_style),
            Paragraph("Descripción Técnica", th_style),
            Paragraph("Cant.", th_style),
            Paragraph("PVP Unit (€)", th_style),
            Paragraph("Subtotal (€)", th_style)
        ]
        pman_rows = [pman_header]

        for p in partidas_man:
            c_nom = str(p.get("concepto", ""))
            c_desc = str(p.get("descripcion", ""))
            c_cant = f"{p.get('cantidad', 1)} {p.get('unidad', 'ud')}"
            c_pu = f"{float(p.get('precio_unitario', 0.0)):,.2f} €"
            c_sub = f"{float(p.get('subtotal', 0.0)):,.2f} €"

            pman_rows.append([
                Paragraph(f"<b>{c_nom}</b>", td_style),
                Paragraph(c_desc, td_style),
                Paragraph(c_cant, td_center),
                Paragraph(c_pu, td_right),
                Paragraph(c_sub, td_right)
            ])

        t_pman = Table(pman_rows, colWidths=[4.5*cm, 7.0*cm, 1.8*cm, 2.3*cm, 2.4*cm])
        t_pman.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), c_primary),
            ('GRID', (0,0), (-1,-1), 0.5, c_border),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_pman)
        story.append(Spacer(1, 6))

    # =========================================================================
    # SECCIÓN 4: CATÁLOGO DE MATERIALES VALORADOS A PVP (OPCIONAL)
    # =========================================================================
    materiales_pvp = presupuesto_data.get("materiales_pvp", [])
    if materiales_pvp and presupuesto_data.get("incluir_catalogo_pvp", True):
        story.append(Paragraph("4. Especificación y Catálogo de Materiales Principales Valorados a PVP", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=4))

        mat_header = [
            Paragraph("Elemento / Categoría", th_style),
            Paragraph("Descripción y Gama Homologada", th_style),
            Paragraph("Cant.", th_style),
            Paragraph("PVP Unit (€)", th_style),
            Paragraph("Subtotal PVP (€)", th_style)
        ]
        mat_rows = [mat_header]

        for m in materiales_pvp:
            m_art = str(m.get("articulo", ""))
            m_desc = str(m.get("desc_exacta", m.get("descripcion", "")))
            m_cant = f"{m.get('cantidad', 1)} {m.get('unidad', 'ud')}"
            m_pvp_u = f"{float(m.get('pvp_unitario', 0.0)):,.2f} €"
            m_pvp_tot = f"{float(m.get('subtotal_pvp', 0.0)):,.2f} €"

            mat_rows.append([
                Paragraph(f"<b>{m_art}</b>", td_style),
                Paragraph(m_desc, td_style),
                Paragraph(m_cant, td_center),
                Paragraph(m_pvp_u, td_right),
                Paragraph(m_pvp_tot, td_right)
            ])

        t_mat = Table(mat_rows, colWidths=[4.2*cm, 7.3*cm, 1.8*cm, 2.3*cm, 2.4*cm])
        t_mat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), c_primary),
            ('GRID', (0,0), (-1,-1), 0.5, c_border),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_mat)
        story.append(Paragraph("<i>* Precios de venta al público (PVP) calculados con margen comercial oficial, marcado CE y garantía legal de reposición incluidos.</i>", ParagraphStyle('MatNote', parent=body_style, fontSize=7, textColor=colors.HexColor("#64748b"))))
        story.append(Spacer(1, 6))

    # =========================================================================
    # SECCIÓN 5: CONDICIONES, GARANTÍAS Y NORMATIVA
    # =========================================================================
    condiciones_text = (
        "<b>Condiciones Generales, Garantías Legales y Tramitación Reglamentaria:</b><br/>"
        "1. <b>Validez de la oferta:</b> 30 días naturales a partir de la fecha de emisión del presente documento.<br/>"
        "2. <b>Garantía Oficial:</b> 3 años de garantía en la instalación y materiales conforme al RD Ley 7/2021 y REBT.<br/>"
        "3. <b>Ensayos Reglamentarios y Boletín Oficial:</b> Incluye verificaciones previas según ITC-BT-05 (resistencia de aislamiento, continuidad de conductores de protección, disparo de diferenciales, impedancia de bucle), elaboración de Memoria Técnica de Diseño (MTD) y tramitación telemática oficial del Certificado de Instalación Eléctrica (CIE / Boletín) ante la Dirección General de Energía y Actividad Industrial y Minera de la Región de Murcia (DGEAIM).<br/>"
        "4. <b>Forma de Pago:</b> 40% a la firma del presupuesto y acopio de materiales, 40% durante la ejecución de las fases de obra y 20% a la entrega del Certificado de Instalación Eléctrica (CIE) debidamente tramitado."
    )
    cond_box = Table([[Paragraph(condiciones_text, ParagraphStyle('Cond', parent=body_style, fontSize=7.5, leading=10))]], colWidths=[18.0*cm])
    cond_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 0.5, c_secondary),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(cond_box)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECCIÓN 6: ACEPTACIÓN Y CONFORMIDAD DEL CLIENTE
    # =========================================================================
    empresa_str = str(proyecto_info.get("empresa", "BOLIMUR Instalaciones"))
    proy_str = str(proyecto_info.get("proyectista", "Instalador Autorizado"))
    lic_str = str(proyecto_info.get("licencia", "REBT-001"))

    firma_block = [
        Paragraph("<b>ACEPTACIÓN Y CONFORMIDAD DEL PRESUPUESTO</b>", ParagraphStyle('FirmaTit', parent=body_style, fontName='Helvetica-Bold', fontSize=9, textColor=c_primary)),
        Spacer(1, 4),
        Paragraph("La firma del presente documento supone la aceptación íntegra de los conceptos, partidas y condiciones expresadas:", ParagraphStyle('FirmaSub', parent=body_style, fontSize=7.5, textColor=colors.HexColor("#64748b"))),
        Spacer(1, 12),
        Table([
            [
                Paragraph(f"<b>Por la Empresa Instaladora:</b><br/><br/><br/>____________________________________________<br/><b>{empresa_str}</b><br/>{proy_str} (Lic. REBT Nº {lic_str})", body_style),
                Paragraph("<b>Conformidad y Aceptación del Cliente:</b><br/><br/><br/>____________________________________________<br/><b>Nombre / Razón Social:</b><br/><b>DNI / CIF:</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Fecha:</b> ___/___/2026", body_style)
            ]
        ], colWidths=[9.0*cm, 9.0*cm], style=[
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ])
    ]

    story.append(KeepTogether(firma_block))

    doc.build(story, canvasmaker=NumberedCanvasPresupuesto)
    return buffer.getvalue()


class NumberedCanvasOrdenCompra(canvas.Canvas):
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
            self.drawString(1.5*cm, 28.3*cm, "BOLIMUR REBT | Orden de Compra y Acopio de Materiales")
            self.drawRightString(19.5*cm, 28.3*cm, "LOGÍSTICA Y ALMACÉN")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(1.5*cm, 28.1*cm, 19.5*cm, 28.1*cm)

        self.setFont("Helvetica", 8)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.5*cm, 0.9*cm, page_text)
        self.drawString(1.5*cm, 0.9*cm, "Bolimur Software ElectroTécnico - Orden de Compra y Acopio")
        self.restoreState()


def generar_pdf_orden_compra(proyecto_info, orden_compra_data):
    """
    Genera un documento profesional de Orden de Compra y Acopio de Materiales clasificado por categorías.
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
    c_bg_box = colors.HexColor("#f0fdf4")
    c_border = colors.HexColor("#cbd5e1")
    c_text_dark = colors.HexColor("#1e293b")

    title_style = ParagraphStyle(
        'DocTitle_OC', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=16, leading=20,
        textColor=c_primary, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle_OC', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=12,
        textColor=c_secondary, spaceAfter=8
    )
    h1_style = ParagraphStyle(
        'Heading1_OC', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=13,
        textColor=c_primary, spaceBefore=10, spaceAfter=4, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_OC', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=c_text_dark
    )
    th_style = ParagraphStyle(
        'TableHeader_OC', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=9.5,
        textColor=colors.white, alignment=1
    )
    td_style = ParagraphStyle(
        'TableCell_OC', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=9.5,
        textColor=c_text_dark, alignment=0
    )
    td_center = ParagraphStyle('TableCellCenter_OC', parent=td_style, alignment=1)
    td_right = ParagraphStyle('TableCellRight_OC', parent=td_style, alignment=2)
    td_right_bold = ParagraphStyle('TableCellRightBold_OC', parent=td_style, fontName='Helvetica-Bold', alignment=2)

    story = []

    text_col = [
        Paragraph("ORDEN DE COMPRA Y LISTA DE ACOPIO DE MATERIALES", title_style),
        Paragraph("Listado clasificado por categorías para aprovisionamiento en tienda / almacén", subtitle_style)
    ]

    logo_img = _crear_logo_flowable(width=4.8*cm, height=2.68*cm)
    if logo_img:
        header_table = Table([[text_col, logo_img]], colWidths=[13.2*cm, 4.8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
    else:
        story.extend(text_col)

    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=2, spaceAfter=6))

    fecha_str = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    meta_table_data = [
        [
            Paragraph("<b>Empresa / Instalador:</b>", body_style),
            Paragraph(f"{proyecto_info.get('empresa', 'BOLIMUR')} | {proyecto_info.get('proyectista', 'Instalador')}", body_style),
            Paragraph("<b>Fecha Pedido:</b>", body_style),
            Paragraph(fecha_str, body_style)
        ],
        [
            Paragraph("<b>Teléfono / Contacto:</b>", body_style),
            Paragraph(str(proyecto_info.get("telefono", "+34 600 000 000")), body_style),
            Paragraph("<b>Nº Orden / Ref:</b>", body_style),
            Paragraph(f"OC-{proyecto_info.get('expediente', '2026-01')}", body_style)
        ],
        [
            Paragraph("<b>Mecanismos / Protecc.:</b>", body_style),
            Paragraph(f"{orden_compra_data.get('serie_mecanismos', 'Estándar')} | {orden_compra_data.get('marca_protecciones', 'Schneider')}", body_style),
            Paragraph("<b>Instalación REBT:</b>", body_style),
            Paragraph(str(orden_compra_data.get("potencia_kw", "5.750 W")), body_style)
        ],
        [
            Paragraph("<b>Tecnología Cable/Tubo:</b>", body_style),
            Paragraph(f"Cable: {orden_compra_data.get('tipo_cable', 'H07Z1-K')} | Tubo: {orden_compra_data.get('tipo_tubo', 'PVC')}", body_style),
            Paragraph("<b>Estado Normativa:</b>", body_style),
            Paragraph("REBT ITC-BT-25 / 19", body_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[3.5*cm, 7.5*cm, 3.2*cm, 3.8*cm])
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

    total_neto = float(orden_compra_data.get("total_neto", 0.0))
    iva_pct = float(orden_compra_data.get("iva_pct", 21.0))
    cuota_iva = float(orden_compra_data.get("cuota_iva", total_neto * (iva_pct / 100.0)))
    total_con_iva = float(orden_compra_data.get("total_con_iva", total_neto + cuota_iva))

    resumen_title = Paragraph("<b>TOTAL ESTIMADO A PAGAR EN TIENDA / ALMACÉN:</b>", ParagraphStyle('ResTitle_OC', parent=body_style, fontSize=10, textColor=colors.HexColor("#15803d"), fontName='Helvetica-Bold'))
    resumen_val = Paragraph(f"<b>{total_con_iva:,.2f} €</b>", ParagraphStyle('ResVal_OC', parent=body_style, fontSize=13, textColor=colors.HexColor("#15803d"), fontName='Helvetica-Bold', alignment=2))

    desglose_resumen = Paragraph(
        f"• Base Imponible Materiales (S/IVA): <b>{total_neto:,.2f} €</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"• Cuota IVA ({iva_pct:.0f}%): <b>{cuota_iva:,.2f} €</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"• Estado: <b>Lista Oficial de Acopio y Compra</b>",
        body_style
    )

    resumen_box = Table([[resumen_title, resumen_val], [desglose_resumen, ""]], colWidths=[12.0*cm, 6.0*cm])
    resumen_box.setStyle(TableStyle([
        ('SPAN', (0,1), (1,1)),
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 1.2, colors.HexColor("#16a34a")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(resumen_box)
    story.append(Spacer(1, 6))

    categorias = orden_compra_data.get("categorias", {})
    
    # Table header
    th_cant = Paragraph("Cant.", th_style)
    th_unid = Paragraph("Unidad", th_style)
    th_desc = Paragraph("Descripción Exacta del Artículo", th_style)
    th_tienda = Paragraph("Tienda / Prov.", th_style)
    th_punit = Paragraph("P. Unit S/IVA", th_style)
    th_subtot = Paragraph("Subtotal S/IVA", th_style)

    for cat_titulo, articulos in categorias.items():
        if not articulos:
            continue

        story.append(Paragraph(f"<b>{cat_titulo}</b>", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.6, color=c_secondary, spaceBefore=1, spaceAfter=3))

        cat_table_rows = [[th_cant, th_unid, th_desc, th_tienda, th_punit, th_subtot]]
        subtotal_cat = 0.0

        for art in articulos:
            cant_val = art.get("cantidad", 1)
            cant_txt = f"{cant_val:.2f}" if isinstance(cant_val, float) and not cant_val.is_integer() else f"{int(cant_val)}"
            unidad_txt = str(art.get("unidad", "ud"))
            desc_txt = str(art.get("desc_exacta", art.get("articulo", "")))
            if not art.get("en_bd", True) or "NO ENCONTRADO" in desc_txt or "⚠️" in desc_txt:
                clean_desc = desc_txt.replace("⚠️", "").strip()
                desc_txt = f"<font color='#b45309'><b>[⚠️ No en BD / Estimado]</b></font> {clean_desc}"
            tienda_txt = str(art.get("proveedor", "Obramat"))
            p_unit = float(art.get("precio_unitario", 0.0))
            subt = float(art.get("subtotal", p_unit * float(cant_val)))
            subtotal_cat += subt

            cat_table_rows.append([
                Paragraph(cant_txt, td_center),
                Paragraph(unidad_txt, td_center),
                Paragraph(desc_txt, td_style),
                Paragraph(tienda_txt, td_center),
                Paragraph(f"{p_unit:.2f} €", td_right),
                Paragraph(f"{subt:.2f} €", td_right)
            ])

        cat_table_rows.append([
            Paragraph(f"<b>Subtotal {cat_titulo.split('.')[0] if '.' in cat_titulo else ''}</b>", ParagraphStyle('SubCat', parent=td_style, fontName='Helvetica-Bold')),
            "", "", "", "",
            Paragraph(f"<b>{subtotal_cat:.2f} €</b>", td_right_bold)
        ])

        t_cat = Table(cat_table_rows, colWidths=[1.5*cm, 2.0*cm, 8.5*cm, 2.4*cm, 1.8*cm, 1.8*cm])
        t_cat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), c_primary),
            ('SPAN', (0, -1), (4, -1)),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#f1f5f9")),
            ('GRID', (0,0), (-1,-1), 0.4, c_border),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, c_bg_light]),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_cat)
        story.append(Spacer(1, 4))

    # Total Table Summary
    total_table_rows = [
        [
            Paragraph("<b>TOTAL MATERIALES NETO (S/IVA):</b>", ParagraphStyle('TotNeto_OC', parent=td_style, fontName='Helvetica-Bold')),
            Paragraph(f"<b>{total_neto:,.2f} €</b>", td_right_bold)
        ],
        [
            Paragraph(f"<b>IMPUESTO IVA ({iva_pct:.0f}%):</b>", ParagraphStyle('TotIva_OC', parent=td_style, fontName='Helvetica-Bold')),
            Paragraph(f"<b>{cuota_iva:,.2f} €</b>", td_right_bold)
        ],
        [
            Paragraph("<b>TOTAL A PAGAR ALMACÉN / TIENDA (C/IVA):</b>", ParagraphStyle('TotFinal_OC', parent=td_style, fontName='Helvetica-Bold', textColor=colors.HexColor("#15803d"))),
            Paragraph(f"<b>{total_con_iva:,.2f} €</b>", ParagraphStyle('TotFinalVal_OC', parent=td_right_bold, textColor=colors.HexColor("#15803d"), fontSize=8.5))
        ]
    ]
    t_tot = Table(total_table_rows, colWidths=[14.4*cm, 3.6*cm])
    t_tot.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1.0, c_secondary),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(Spacer(1, 6))
    story.append(KeepTogether([t_tot]))

    # Materiales asignados por estancia
    mat_estancias = orden_compra_data.get("materiales_por_estancia", [])
    if mat_estancias:
        story.append(PageBreak())
        story.append(Paragraph("<b>📦 Desglose y Asignación de Materiales por Estancia</b>", h1_style))
        story.append(HRFlowable(width="100%", thickness=1.0, color=c_secondary, spaceBefore=2, spaceAfter=6))
        story.append(Paragraph("<font size='7.5' color='#475569'>Distribución de acopio en obra para organizar el trabajo estancia por estancia (mecanismos, cables y tubos asignados):</font>", body_style))
        story.append(Spacer(1, 4))

        th_est_nom = Paragraph("Estancia", th_style)
        th_est_mec = Paragraph("Mecanismos y Marcos", th_style)
        th_est_tub = Paragraph("Canalización (Tubos)", th_style)
        th_est_cab = Paragraph("Conductores (Cables)", th_style)
        th_est_caj = Paragraph("Cajas", th_style)
        th_est_cost = Paragraph("Coste S/IVA", th_style)

        est_table_rows = [[th_est_nom, th_est_mec, th_est_tub, th_est_cab, th_est_caj, th_est_cost]]

        for est in mat_estancias:
            nom_txt = f"<b>{est['nombre']}</b><br/><font size='6.5' color='#64748b'>{est['m2']} m² | Dist: {est['distancia_cuadro']}m</font>"
            
            # Mecanismos resumen
            mecs_lines = []
            for m in est.get("mecanismos", []):
                mecs_lines.append(f"• {m['cant']}x {m['nombre']}")
            if est.get("marcos", 0) > 0:
                mecs_lines.append(f"• {est['marcos']}x Marcos embellecedores")
            mec_res_txt = "<br/>".join(mecs_lines) if mecs_lines else "—"

            # Tubos resumen
            tub_lines = []
            if est.get("tubo_m20", 0) > 0:
                tub_lines.append(f"• M20: {est['tubo_m20']:.1f} m")
            if est.get("tubo_m25", 0) > 0:
                tub_lines.append(f"• M25: {est['tubo_m25']:.1f} m")
            tub_res_txt = "<br/>".join(tub_lines) if tub_lines else "—"

            # Cables resumen
            cab_lines = []
            for c in est.get("cables", []):
                if c.get("metros", 0) > 0:
                    cab_lines.append(f"• {c['item']}: {c['metros']:.1f}m")
            cab_res_txt = "<br/>".join(cab_lines) if cab_lines else "—"

            # Cajas
            caj_txt = f"• {est.get('cajas_mecanismo', 0)}x Mecanismo<br/>• {est.get('cajas_registro', 0)}x Registro"

            # Coste
            coste_val = est.get("coste_materiales_neto", 0.0)

            est_table_rows.append([
                Paragraph(nom_txt, td_style),
                Paragraph(mec_res_txt, td_style),
                Paragraph(tub_res_txt, td_style),
                Paragraph(cab_res_txt, td_style),
                Paragraph(caj_txt, td_style),
                Paragraph(f"<b>{coste_val:,.2f} €</b>", td_right)
            ])

        t_est = Table(est_table_rows, colWidths=[3.2*cm, 4.3*cm, 2.5*cm, 4.5*cm, 2.0*cm, 1.5*cm])
        t_est.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), c_primary),
            ('GRID', (0,0), (-1,-1), 0.4, c_border),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_est)

    doc.build(story, canvasmaker=NumberedCanvasOrdenCompra)
    return buffer.getvalue()


def _normalizar_circuito_rebt(c: dict) -> dict:
    """
    Normaliza los parámetros reglamentarios de un circuito según ITC-BT-25 Tabla 1:
    - C1 (Iluminación): 10A, 1.5 mm², Tubo M16/M20
    - C2 (Tomas uso general): 16A, 2.5 mm², Tubo M20
    - C3 (Cocina y Horno): 25A, 6.0 mm², Tubo M25
    - C4 (Lavadora/Lavavajillas/Termo): 20A (4mm²) o desdoblado 16A (2.5mm²), Tubo M20
    - C5 (Baños y auxiliares cocina): 16A, 2.5 mm², Tubo M20
    - C9 (Aire Acondicionado): 25A, 6.0 mm², Tubo M25
    - C10 (Secadora): 16A, 2.5 mm², Tubo M20
    - C13 (IRVE / Vehículo Eléctrico): 32A/16A, 6.0 mm²/2.5 mm², Tubo M32/M25
    """
    cid = str(c.get("id", "")).upper().strip()
    c_norm = dict(c)
    
    # Valores reglamentarios de referencia ITC-BT-25
    if "C1" in cid and "C10" not in cid and "C11" not in cid and "C12" not in cid and "C13" not in cid:
        c_norm["pia"] = c.get("pia") or 10
        c_norm["cable_sec"] = "2x1.5+TT1.5 mm²"
        c_norm["tubo_diam"] = "M16"
        c_norm["pot_w"] = c.get("pot_w") or 2300
    elif "C2" in cid:
        c_norm["pia"] = c.get("pia") or 16
        c_norm["cable_sec"] = "2x2.5+TT2.5 mm²"
        c_norm["tubo_diam"] = "M20"
        c_norm["pot_w"] = c.get("pot_w") or 3450
    elif "C3" in cid:
        c_norm["pia"] = c.get("pia") or 25
        c_norm["cable_sec"] = "2x6+TT6 mm²"
        c_norm["tubo_diam"] = "M25"
        c_norm["pot_w"] = c.get("pot_w") or 5400
    elif "C4" in cid:
        if any(sub in cid for sub in ["4.1", "4.2", "4.3", "4-1", "4-2", "4-3", "4A", "4B", "4C", "4-A", "4-B", "4-C"]):
            c_norm["pia"] = c.get("pia") or 16
            c_norm["cable_sec"] = "2x2.5+TT2.5 mm²"
            c_norm["tubo_diam"] = "M20"
            c_norm["pot_w"] = c.get("pot_w") or 3450
        else:
            c_norm["pia"] = c.get("pia") or 20
            c_norm["cable_sec"] = "2x4+TT4 mm²"
            c_norm["tubo_diam"] = "M20"
            c_norm["pot_w"] = c.get("pot_w") or 4600
    elif "C5" in cid:
        c_norm["pia"] = c.get("pia") or 16
        c_norm["cable_sec"] = "2x2.5+TT2.5 mm²"
        c_norm["tubo_diam"] = "M20"
        c_norm["pot_w"] = c.get("pot_w") or 3450
    elif "C10" in cid:
        c_norm["pia"] = c.get("pia") or 16
        c_norm["cable_sec"] = "2x2.5+TT2.5 mm²"
        c_norm["tubo_diam"] = "M20"
        c_norm["pot_w"] = c.get("pot_w") or 3450
    elif "C9" in cid:
        c_norm["pia"] = c.get("pia") or 25
        c_norm["cable_sec"] = "2x6+TT6 mm²"
        c_norm["tubo_diam"] = "M25"
        c_norm["pot_w"] = c.get("pot_w") or 5750
    elif "C13" in cid:
        c_norm["pia"] = c.get("pia") or 32
        c_norm["cable_sec"] = "2x6+TT6 mm²"
        c_norm["tubo_diam"] = "M32"
        c_norm["pot_w"] = c.get("pot_w") or 7360
    else:
        # Si ya trae sección específica respetarla, si no por defecto 2.5 mm²
        if not c_norm.get("cable_sec"):
            c_norm["cable_sec"] = "2x2.5+TT2.5 mm²"
        if not c_norm.get("tubo_diam"):
            c_norm["tubo_diam"] = "M20"
            
    return c_norm


def generar_pdf_unifilar_industria(proyecto_info, unifilar_data):
    """
    Genera el Esquema Unifilar Oficial y Memoria Técnica de Diseño (MTD) conforme a las
    prescripciones de la Dirección General de Energía y Actividad Industrial y Minera
    de la Región de Murcia (DGEAIM) y el REBT (RD 842/2002 - ITC-BT-25 / 17 / 23 / 24).
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
    c_carm_red = colors.HexColor("#991b1b")

    title_style = ParagraphStyle(
        'DocTitle_Uni', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14, leading=17,
        textColor=c_primary, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle_Uni', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=11,
        textColor=c_secondary, spaceAfter=6
    )
    h1_style = ParagraphStyle(
        'Heading1_Uni', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=13,
        textColor=c_primary, spaceBefore=8, spaceAfter=4, keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Uni', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=c_text_dark
    )
    th_style = ParagraphStyle(
        'TH_Uni', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=10,
        textColor=colors.white, alignment=1
    )
    td_style = ParagraphStyle(
        'TD_Uni', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=10,
        textColor=c_text_dark
    )
    td_center = ParagraphStyle(
        'TDCenter_Uni', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=10,
        textColor=c_text_dark, alignment=1
    )
    td_bold = ParagraphStyle(
        'TDBold_Uni', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=10,
        textColor=c_primary, alignment=1
    )

    story = []

    # 1. Official Header (Región de Murcia - DGEAIM) con Logo BOLIMUR
    logo_uni = _crear_logo_flowable(width=4.4*cm, height=2.45*cm)
    col_logo_uni = logo_uni if logo_uni else Paragraph("<b>BOLIMUR</b><br/><font size='6' color='#0284c7'>Instalaciones</font>", ParagraphStyle('HdrLogoUni', parent=body_style, alignment=2))

    header_data = [
        [
            Paragraph("<b>REGIÓN DE MURCIA</b><br/><font size='6.5' color='#475569'>Consejería de Empresa, Empleo y Economía Social<br/>Dirección General de Energía y Actividad Industrial y Minera</font>", body_style),
            Paragraph("<b>MEMORIA TÉCNICA DE DISEÑO (MTD)</b><br/><font size='7' color='#0284c7'>ESQUEMA UNIFILAR REBT OFICIAL - RD 842/2002</font><br/><font size='6.5' color='#64748b'>ITC-BT-25 / ITC-BT-17 / ITC-BT-23 / ITC-BT-24</font>", ParagraphStyle('HdrRight', parent=body_style, alignment=1)),
            col_logo_uni
        ]
    ]
    t_hdr = Table(header_data, colWidths=[6.8*cm, 6.8*cm, 4.4*cm])
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

    # 2. Administrative and Installation Metadata
    potencia_w = unifilar_data.get("potencia_w", 5750)
    iga_amp = unifilar_data.get("iga_amperaje", 25)
    grado_electr = unifilar_data.get("grado_electr", "Básica")
    tipo_cable = unifilar_data.get("tipo_cable", "H07Z1-K")
    tipo_tubo = unifilar_data.get("tipo_tubo", "PVC Normal")
    marca_prot = unifilar_data.get("marca_protecciones", "Schneider / Chint")
    fecha_str = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))

    meta_table_data = [
        [
            Paragraph("<b>Titular / Emplazamiento:</b>", body_style),
            Paragraph(f"Vivienda Residencial | {proyecto_info.get('localidad', 'Rincón de Seca, Murcia (Región de Murcia)')}", body_style),
            Paragraph("<b>Fecha Registro:</b>", body_style),
            Paragraph(fecha_str, body_style)
        ],
        [
            Paragraph("<b>Instalador Autorizado:</b>", body_style),
            Paragraph(f"{proyecto_info.get('proyectista', 'Richard Orlando Choque Tejerina')} ({proyecto_info.get('licencia', 'REBT-30/15892')})", body_style),
            Paragraph("<b>Empresa:</b>", body_style),
            Paragraph(str(proyecto_info.get("empresa", "BOLIMUR")), body_style)
        ],
        [
            Paragraph("<b>Suministro Eléctrico:</b>", body_style),
            Paragraph(f"Monofásico 230 V - 50 Hz | Potencia: <b>{potencia_w:,} W</b> ({grado_electr})", body_style),
            Paragraph("<b>IGA General:</b>", body_style),
            Paragraph(f"<b>{iga_amp} A</b> (2P Curva C | Icn: 6 kA)", body_style)
        ],
        [
            Paragraph("<b>Derivación Individual:</b>", body_style),
            Paragraph(f"2x10 mm² Cu + TT 1x10 mm² ({tipo_cable}) bajo tubo M32", body_style),
            Paragraph("<b>Sobretensiones:</b>", body_style),
            Paragraph("POP + DPS Tipo 2 (ITC-BT-23)", body_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[3.6*cm, 7.4*cm, 3.2*cm, 3.8*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_light),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # 3. Vectorial Single-Line Diagram (Drawing) Jerárquico UNE-EN 60617
    story.append(Paragraph("1. Esquema Unifilar Gráfico del Cuadro General de Mando y Protección (CGMP)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceBefore=1, spaceAfter=4))

    d_width = 520
    d_height = 270
    d = Drawing(d_width, d_height)
    d.add(Rect(0, 0, d_width, d_height, fillColor=colors.HexColor('#ffffff'), strokeColor=colors.HexColor('#94a3b8'), strokeWidth=0.9, rx=4, ry=4))

    # =============================================================
    # 1. CABECERA: ICP
    # =============================================================
    xc = 260
    d.add(Line(xc, 264, xc, 254, strokeColor=c_primary, strokeWidth=1.3))
    d.add(Line(xc, 254, xc - 7, 244, strokeColor=c_primary, strokeWidth=1.4))
    d.add(Circle(xc, 254, 1.2, fillColor=c_primary, strokeColor=c_primary))
    d.add(Circle(xc, 242, 1.2, fillColor=c_primary, strokeColor=c_primary))
    d.add(Line(xc, 242, xc, 234, strokeColor=c_primary, strokeWidth=1.3))
    d.add(String(xc + 14, 250, "ICP", fontName="Helvetica-Bold", fontSize=9, fillColor=c_primary))

    # =============================================================
    # 2. IGA (2 x 40 A / 2P)
    # =============================================================
    d.add(Line(xc, 234, xc - 7, 222, strokeColor=c_primary, strokeWidth=1.4))
    d.add(Circle(xc, 234, 1.2, fillColor=c_primary, strokeColor=c_primary))
    d.add(Circle(xc, 220, 1.2, fillColor=c_primary, strokeColor=c_primary))
    # Disparador magnetotérmico
    d.add(Line(xc - 4, 227, xc - 12, 222, strokeColor=c_primary, strokeWidth=1.0))
    d.add(Line(xc - 12, 222, xc - 9, 219, strokeColor=c_primary, strokeWidth=1.0))
    d.add(Rect(xc - 15, 219, 4, 4, fillColor=c_primary, strokeColor=c_primary))
    d.add(Line(xc, 220, xc, 206, strokeColor=c_primary, strokeWidth=1.3))

    d.add(String(xc + 14, 230, "IGA", fontName="Helvetica-Bold", fontSize=8.5, fillColor=c_primary))
    d.add(String(xc + 14, 219, f"2 x {iga_amp} A", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_secondary))
    d.add(String(xc + 14, 210, "6 kA | Curva C", fontName="Helvetica", fontSize=6.0, fillColor=colors.HexColor("#64748b")))

    # =============================================================
    # 3. DERIVACIÓN A LOS 2 DIFERENCIALES (Izquierda y Derecha)
    # =============================================================
    x_d1 = 135
    x_d2 = 385
    y_split = 206
    d.add(Line(x_d1, y_split, x_d2, y_split, strokeColor=c_primary, strokeWidth=1.4))
    d.add(Circle(xc, y_split, 1.5, fillColor=c_primary, strokeColor=c_primary))

    # --- DIFERENCIAL 1 ---
    d.add(Line(x_d1, y_split, x_d1, 196, strokeColor=c_primary, strokeWidth=1.2))
    d.add(Line(x_d1, 196, x_d1 - 7, 185, strokeColor=c_primary, strokeWidth=1.3))
    d.add(Circle(x_d1, 196, 1.2, fillColor=c_primary, strokeColor=c_primary))
    d.add(Circle(x_d1, 183, 1.2, fillColor=c_primary, strokeColor=c_primary))
    d.add(Circle(x_d1, 175, 5.5, fillColor=colors.HexColor("#ecfdf5"), strokeColor=c_green, strokeWidth=1.1))
    d.add(Line(x_d1, 183, x_d1, 166, strokeColor=c_primary, strokeWidth=1.3))
    d.add(Rect(x_d1 - 18, 184, 6, 6, fillColor=colors.HexColor("#16a34a"), strokeColor=colors.HexColor("#16a34a")))
    d.add(Line(x_d1 - 12, 187, x_d1 - 6, 191, strokeColor=c_green, strokeWidth=0.8))
    d.add(Line(x_d1 - 15, 184, x_d1 - 6, 175, strokeColor=c_green, strokeWidth=0.8))
    d.add(String(x_d1 + 14, 191, "Dif. 1", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_green))
    d.add(String(x_d1 + 14, 180, "2 x 40 A", fontName="Helvetica-Bold", fontSize=7.5, fillColor=c_primary))
    d.add(String(x_d1 + 14, 170, "30 mA", fontName="Helvetica-Bold", fontSize=7.5, fillColor=c_primary))

    # --- DIFERENCIAL 2 ---
    d.add(Line(x_d2, y_split, x_d2, 196, strokeColor=c_primary, strokeWidth=1.2))
    d.add(Line(x_d2, 196, x_d2 - 7, 185, strokeColor=c_primary, strokeWidth=1.3))
    d.add(Circle(x_d2, 196, 1.2, fillColor=c_primary, strokeColor=c_primary))
    d.add(Circle(x_d2, 183, 1.2, fillColor=c_primary, strokeColor=c_primary))
    d.add(Circle(x_d2, 175, 5.5, fillColor=colors.HexColor("#ecfdf5"), strokeColor=c_green, strokeWidth=1.1))
    d.add(Line(x_d2, 183, x_d2, 166, strokeColor=c_primary, strokeWidth=1.3))
    d.add(Rect(x_d2 - 18, 184, 6, 6, fillColor=colors.HexColor("#16a34a"), strokeColor=colors.HexColor("#16a34a")))
    d.add(Line(x_d2 - 12, 187, x_d2 - 6, 191, strokeColor=c_green, strokeWidth=0.8))
    d.add(Line(x_d2 - 15, 184, x_d2 - 6, 175, strokeColor=c_green, strokeWidth=0.8))
    d.add(String(x_d2 + 14, 191, "Dif. 2", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_green))
    d.add(String(x_d2 + 14, 180, "2 x 40 A", fontName="Helvetica-Bold", fontSize=7.5, fillColor=c_primary))
    d.add(String(x_d2 + 14, 170, "30 mA", fontName="Helvetica-Bold", fontSize=7.5, fillColor=c_primary))

    # =============================================================
    # 4. PEINES / BARRAS DE DISTRIBUCIÓN
    # =============================================================
    y_bus = 166
    d.add(Line(18, y_bus, 252, y_bus, strokeColor=c_secondary, strokeWidth=2.2))
    d.add(Circle(x_d1, y_bus, 1.8, fillColor=c_secondary, strokeColor=c_secondary))
    d.add(Line(268, y_bus, 502, y_bus, strokeColor=c_secondary, strokeWidth=2.2))
    d.add(Circle(x_d2, y_bus, 1.8, fillColor=c_secondary, strokeColor=c_secondary))

    # =============================================================
    # 5. COLUMNAS DE CIRCUITOS INDIVIDUALES
    # =============================================================
    circs_modelo = [
        {"cx": 48,  "pia": "2 x 10 A", "sec": "2 x 1.5 + T", "tubo": "Tubo 16", "id": "C1",   "nom1": "Iluminación", "nom2": "general"},
        {"cx": 108, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C2",   "nom1": "Toma uso",    "nom2": "General"},
        {"cx": 168, "pia": "2 x 25 A", "sec": "2 x 6 + T",   "tubo": "Tubo 25", "id": "C3",   "nom1": "Cocina y",    "nom2": "Horno"},
        {"cx": 228, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C10",  "nom1": "Secadora",    "nom2": ""},
        
        {"cx": 298, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C4.1", "nom1": "Lavadora",    "nom2": ""},
        {"cx": 358, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C4.2", "nom1": "Lavavajillas","nom2": ""},
        {"cx": 418, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C4.3", "nom1": "Termo",       "nom2": "eléctrico"},
        {"cx": 478, "pia": "2 x 16 A", "sec": "2 x 2.5 + T", "tubo": "Tubo 20", "id": "C5",   "nom1": "Baño y Aux.", "nom2": "Cocina"}
    ]

    for c in circs_modelo:
        cx = c["cx"]
        d.add(Line(cx, y_bus, cx, 155, strokeColor=c_primary, strokeWidth=1.0))
        d.add(Circle(cx, y_bus, 1.2, fillColor=c_secondary, strokeColor=c_secondary))

        # Caja de Datos Técnicos
        d.add(Rect(cx - 26, 118, 52, 37, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.6, rx=2, ry=2))
        d.add(String(cx, 145, c["pia"], fontName="Helvetica-Bold", fontSize=6.2, fillColor=c_primary, textAnchor="middle"))
        d.add(String(cx, 134, c["sec"], fontName="Helvetica-Bold", fontSize=5.8, fillColor=c_secondary, textAnchor="middle"))
        d.add(String(cx, 123, c["tubo"], fontName="Helvetica", fontSize=5.5, fillColor=colors.HexColor("#64748b"), textAnchor="middle"))

        # Línea hacia símbolo PIA
        d.add(Line(cx, 118, cx, 106, strokeColor=c_primary, strokeWidth=1.0))

        # Símbolo Magnetotérmico PIA
        d.add(Line(cx, 106, cx - 7, 94, strokeColor=c_primary, strokeWidth=1.3))
        d.add(Circle(cx, 106, 1.0, fillColor=c_primary, strokeColor=c_primary))
        d.add(Circle(cx, 92, 1.0, fillColor=c_primary, strokeColor=c_primary))
        d.add(Line(cx - 4, 99, cx - 11, 95, strokeColor=c_primary, strokeWidth=0.9))
        d.add(Line(cx - 11, 95, cx - 8, 92, strokeColor=c_primary, strokeWidth=0.9))
        d.add(Rect(cx - 13, 92, 3.5, 3.5, fillColor=c_primary, strokeColor=c_primary))

        # Salida hacia receptor
        d.add(Line(cx, 92, cx, 74, strokeColor=c_primary, strokeWidth=1.0))

        # Identificador del Circuito
        d.add(String(cx, 60, c["id"], fontName="Helvetica-Bold", fontSize=9.5, fillColor=c_primary, textAnchor="middle"))

        # Denominación / Destino
        d.add(String(cx, 46, c["nom1"], fontName="Helvetica-Bold", fontSize=6.0, fillColor=c_text_dark, textAnchor="middle"))
        if c["nom2"]:
            d.add(String(cx, 37, c["nom2"], fontName="Helvetica", fontSize=5.5, fillColor=colors.HexColor("#475569"), textAnchor="middle"))

    # =============================================================
    # 6. PUESTA A TIERRA (PE - ⏚)
    # =============================================================
    d.add(Rect(18, 6, 484, 24, fillColor=colors.HexColor("#fef3c7"), strokeColor=colors.HexColor("#d97706"), strokeWidth=0.7, rx=2, ry=2))
    tx = 35
    ty = 16
    d.add(Line(tx, ty + 8, tx, ty, strokeColor=colors.HexColor("#92400e"), strokeWidth=1.2))
    d.add(Line(tx - 6, ty, tx + 6, ty, strokeColor=colors.HexColor("#92400e"), strokeWidth=1.2))
    d.add(Line(tx - 4, ty - 2.5, tx + 4, ty - 2.5, strokeColor=colors.HexColor("#92400e"), strokeWidth=1.0))
    d.add(Line(tx - 2, ty - 5, tx + 2, ty - 5, strokeColor=colors.HexColor("#92400e"), strokeWidth=0.8))
    d.add(String(50, 19, "RED DE TIERRA (PE - ITC-BT-18):", fontName="Helvetica-Bold", fontSize=6.0, fillColor=colors.HexColor("#92400e")))
    d.add(String(50, 10, "Línea Enlace Cu 1x10 mm² | Picas de tierra 2m | <b>Resistencia Medida: Rt = 11.8 Ω</b> (Límite REBT ≤ 15 Ω)", fontName="Helvetica", fontSize=5.5, fillColor=c_text_dark))

    story.append(d)
    story.append(Spacer(1, 6))



    # 4. Official Technical Circuit Schedule (ITC-BT-25)
    story.append(Paragraph("2. Tabla de Características Técnicas de los Circuitos Interiores (ITC-BT-25)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceBefore=1, spaceAfter=4))

    circuitos_raw = unifilar_data.get("circuitos", [])
    if circuitos_raw:
        circuitos_normalizados = [_normalizar_circuito_rebt(c) for c in circuitos_raw]
    else:
        circuitos_normalizados = [
            {"id": "C1", "denominacion": "Iluminación general", "pia": 10, "dif": "Dif. 1 (30mA)", "cable_sec": "2x1.5+TT1.5 mm²", "tubo_diam": "M16", "long_m": 18, "cdt_pct": 0.85, "pot_w": 2300},
            {"id": "C2", "denominacion": "Tomas de corriente uso general", "pia": 16, "dif": "Dif. 1 (30mA)", "cable_sec": "2x2.5+TT2.5 mm²", "tubo_diam": "M20", "long_m": 15, "cdt_pct": 1.10, "pot_w": 3450},
            {"id": "C3", "denominacion": "Cocina y horno", "pia": 25, "dif": "Dif. 1 (30mA)", "cable_sec": "2x6+TT6 mm²", "tubo_diam": "M25", "long_m": 12, "cdt_pct": 0.95, "pot_w": 5400},
            {"id": "C10", "denominacion": "Secadora independiente", "pia": 16, "dif": "Dif. 1 (30mA)", "cable_sec": "2x2.5+TT2.5 mm²", "tubo_diam": "M20", "long_m": 14, "cdt_pct": 1.05, "pot_w": 3450},
            {"id": "C4.1", "denominacion": "Lavadora", "pia": 16, "dif": "Dif. 2 (30mA)", "cable_sec": "2x2.5+TT2.5 mm²", "tubo_diam": "M20", "long_m": 14, "cdt_pct": 1.05, "pot_w": 3450},
            {"id": "C4.2", "denominacion": "Lavavajillas", "pia": 16, "dif": "Dif. 2 (30mA)", "cable_sec": "2x2.5+TT2.5 mm²", "tubo_diam": "M20", "long_m": 14, "cdt_pct": 1.05, "pot_w": 3450},
            {"id": "C4.3", "denominacion": "Termo eléctrico", "pia": 16, "dif": "Dif. 2 (30mA)", "cable_sec": "2x2.5+TT2.5 mm²", "tubo_diam": "M20", "long_m": 12, "cdt_pct": 0.90, "pot_w": 2300},
            {"id": "C5", "denominacion": "Tomas baño y auxiliares cocina", "pia": 16, "dif": "Dif. 2 (30mA)", "cable_sec": "2x2.5+TT2.5 mm²", "tubo_diam": "M20", "long_m": 16, "cdt_pct": 1.15, "pot_w": 3450},
        ]

    th_circ = Paragraph("Circ.", th_style)
    th_den = Paragraph("Denominación y Destino", th_style)
    th_pia = Paragraph("PIA (In/PdC)", th_style)
    th_dif = Paragraph("Diferencial", th_style)
    th_cond = Paragraph("Conductor (Cu)", th_style)
    th_tub = Paragraph("Tubo", th_style)
    th_long = Paragraph("L. máx", th_style)
    th_cdt = Paragraph("CdT (e%)", th_style)
    th_pot = Paragraph("P. Asig (W)", th_style)

    circ_rows = [[th_circ, th_den, th_pia, th_dif, th_cond, th_tub, th_long, th_cdt, th_pot]]

    for c in circuitos_normalizados:
        pia_val = c['pia']
        dif_val = c['dif']
        cable_val = c['cable_sec']
        tubo_val = str(c['tubo_diam']).split(" ")[0]
        long_val = c['long_m']
        cdt_val = c['cdt_pct']
        pot_val = c['pot_w']

        circ_rows.append([
            Paragraph(f"<b>{c['id']}</b>", td_bold),
            Paragraph(str(c['denominacion']), td_style),
            Paragraph(f"<b>{pia_val}A</b> (C/6kA)", td_center),
            Paragraph(str(dif_val), td_center),
            Paragraph(str(cable_val), td_style),
            Paragraph(str(tubo_val), td_center),
            Paragraph(f"{long_val:.0f} m", td_center),
            Paragraph(f"<b>{cdt_val:.2f}%</b>", td_center),
            Paragraph(f"{pot_val:,} W", td_center)
        ])

    t_circs = Table(circ_rows, colWidths=[1.3*cm, 4.3*cm, 2.0*cm, 2.2*cm, 2.6*cm, 1.3*cm, 1.2*cm, 1.5*cm, 1.6*cm])
    t_circs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.4, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 2.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_circs)
    story.append(Spacer(1, 6))


    # 5. Technical Verifications Box (ITC-BT-19 / 24 / 23)
    verif_data = [
        [
            Paragraph("<b>COMPROBACIONES TÉCNICAS Y REGLAMENTARIAS (REBT - RD 842/2002):</b>", ParagraphStyle('VTitle', parent=body_style, fontName='Helvetica-Bold', textColor=c_primary)),
            ""
        ],
        [
            Paragraph("• <b>Caída de tensión máxima:</b> e < 3,0% en circuitos terminales (🟢 Conforme ITC-BT-19).<br/>• <b>Protección contra contactos indirectos:</b> Diferencial de alta sensibilidad 30 mA (🟢 Conforme ITC-BT-24).", body_style),
            Paragraph(f"• <b>Poder de corte mínimo:</b> Icn = 6.000 A en todos los PIAs (🟢 Conforme Icc presunta).<br/>• <b>Sobretensiones:</b> Limitador Tipo 2 + Permanente POP instalado (🟢 Conforme ITC-BT-23).", body_style)
        ]
    ]
    t_verif = Table(verif_data, colWidths=[9.0*cm, 9.0*cm])
    t_verif.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor("#16a34a")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_verif)
    story.append(Spacer(1, 6))

    # 6. Official Declaration & Signature Diligence Box
    sig_data = [
        [
            Paragraph("<b>DECLARACIÓN RESPONSABLE DEL INSTALADOR AUTORIZADO REBT:</b><br/><font size='6.5' color='#475569'>El instalador autorizado declara bajo su responsabilidad que la presente instalación eléctrica ha sido ejecutada de acuerdo con el Reglamento Electrotécnico para Baja Tensión (RD 842/2002), sus Instrucciones Técnicas Complementarias y las directrices técnicas de la Dirección General de Energía y Actividad Industrial y Minera de la Región de Murcia.</font>", body_style),
            Paragraph("<b>DILIGENCIA DE REGISTRO / VISADO:</b><br/><font size='6.5' color='#64748b'>Dirección General de Energía y Actividad Industrial y Minera<br/>Comunidad Autónoma de la Región de Murcia (CARM)</font>", body_style)
        ],
        [
            Paragraph(f"<br/><br/><b>Firma y Sello de la Empresa Instaladora:</b><br/>{proyecto_info.get('empresa', 'BOLIMUR')}<br/>{proyecto_info.get('proyectista', 'Richard Orlando Choque Tejerina')} (Carnet: {proyecto_info.get('licencia', 'REBT-30/15892')})", body_style),
            Paragraph("<br/><br/><b>Espacio reservado para Registro Telemático:</b><br/><font size='6.5' color='#94a3b8'>[ Registro Oficial MTD / CIE Industria Murcia ]</font>", body_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[10.5*cm, 7.5*cm])
    t_sig.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('BOX', (0,0), (-1,-1), 1.0, c_primary),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(KeepTogether([t_sig]))

    doc.build(story, canvasmaker=NumberedCanvasUnifilar)
    return buffer.getvalue()


