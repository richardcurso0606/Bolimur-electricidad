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


def generar_pdf_presupuesto(proyecto_info, presupuesto_data):
    """
    Genera una oferta comercial y presupuesto técnico en PDF profesional con ReportLab.
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
    td_right = ParagraphStyle('TableCellRight', parent=td_style, alignment=2)
    td_right_bold = ParagraphStyle('TableCellRightBold', parent=td_style, fontName='Helvetica-Bold', alignment=2)

    story = []

    logo_path = "logo_bolimur.PNG"
    if not os.path.exists(logo_path):
        logo_path = "icono_bolimur.png"
    
    text_col = [
        Paragraph("PRESUPUESTO DE INSTALACIÓN ELÉCTRICA VIVIENDAS", title_style),
        Paragraph(str(proyecto_info.get("empresa", "BOLIMUR Instalaciones Integrales")), subtitle_style)
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
            Paragraph("<b>Empresa:</b>", body_style),
            Paragraph(str(proyecto_info.get("empresa", "BOLIMUR")), body_style),
            Paragraph("<b>Fecha Oferta:</b>", body_style),
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
            Paragraph(f"{proyecto_info.get('telefono', '600000000')} | {proyecto_info.get('localidad', 'Comunidad')}", body_style),
            Paragraph("<b>Gama Mecanismos:</b>", body_style),
            Paragraph(str(presupuesto_data.get("serie_mecanismos", "Estándar")), body_style)
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

    subtotal_neto = float(presupuesto_data.get("subtotal_neto", 0.0))
    iva_pct = float(presupuesto_data.get("iva_pct", 21.0))
    cuota_iva = float(presupuesto_data.get("cuota_iva", 0.0))
    total_cliente = float(presupuesto_data.get("total_cliente", 0.0))

    resumen_title = Paragraph("<b>TOTAL PRESUPUESTO OFERTA (CON IVA):</b>", ParagraphStyle('ResTitle', parent=body_style, fontSize=11, textColor=c_primary, fontName='Helvetica-Bold'))
    resumen_val = Paragraph(f"<b>{total_cliente:,.2f} €</b>", ParagraphStyle('ResVal', parent=body_style, fontSize=14, textColor=c_accent, fontName='Helvetica-Bold', alignment=2))

    desglose_resumen = Paragraph(
        f"<b>Resumen Económico:</b><br/>"
        f"• Subtotal Neto Comercial (Sin IVA): <b>{subtotal_neto:,.2f} €</b><br/>"
        f"• Impuesto sobre el Valor Añadido (IVA {iva_pct:.0f}%): <b>{cuota_iva:,.2f} €</b><br/>"
        f"• Puntos / Mecanismos Totales Instalados: <b>{presupuesto_data.get('total_puntos', 0)} uds</b> | "
        f"Precio medio por punto: <b>{presupuesto_data.get('precio_medio_punto', 0.0):.2f} €/punto</b>",
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

    story.append(Paragraph("1. Cuadro de Desglose por Estancias y Partidas de Obra", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_primary, spaceBefore=1, spaceAfter=5))

    table_p_header = [
        Paragraph("Concepto / Estancia", th_style),
        Paragraph("Detalle de Mecanismos y Cuadro", th_style),
        Paragraph("Importe Comercial (€)", th_style)
    ]
    table_p_rows = [table_p_header]

    df_comercial = presupuesto_data.get("df_comercial", [])
    if hasattr(df_comercial, 'to_dict'):
        records = df_comercial.to_dict('records')
    else:
        records = df_comercial

    for row in records:
        estancia = str(row.get('Estancia / Partida', row.get('Estancia', '')))
        detalle = str(row.get('Detalle de Mecanismos / Equipamiento', row.get('Detalle', '')))
        importe = str(row.get('Importe (€)', '0.00'))

        table_p_rows.append([
            Paragraph(estancia, td_style),
            Paragraph(detalle, td_style),
            Paragraph(importe, td_right)
        ])

    table_p_rows.append([
        Paragraph("<b>SUBTOTAL NETO (Sin IVA)</b>", ParagraphStyle('SubPres', parent=td_style, fontName='Helvetica-Bold')),
        "", Paragraph(f"<b>{subtotal_neto:,.2f} €</b>", td_right_bold)
    ])
    table_p_rows.append([
        Paragraph(f"<b>IVA ({iva_pct:.0f}%)</b>", ParagraphStyle('SubIva', parent=td_style, fontName='Helvetica-Bold')),
        "", Paragraph(f"<b>{cuota_iva:,.2f} €</b>", td_right_bold)
    ])
    table_p_rows.append([
        Paragraph("<b>TOTAL PRESUPUESTO</b>", ParagraphStyle('TotPres', parent=td_style, fontName='Helvetica-Bold', textColor=c_accent)),
        "", Paragraph(f"<b>{total_cliente:,.2f} €</b>", ParagraphStyle('TotVal', parent=td_right_bold, textColor=c_accent, fontSize=9))
    ])

    t_pres = Table(table_p_rows, colWidths=[6.0*cm, 8.5*cm, 3.5*cm])
    t_pres.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('SPAN', (0, -3), (1, -3)),
        ('SPAN', (0, -2), (1, -2)),
        ('SPAN', (0, -1), (1, -1)),
        ('BACKGROUND', (0,-3), (-1,-1), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-4), [colors.white, c_bg_light]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_pres)
    story.append(Spacer(1, 10))

    condiciones_text = (
        "<b>Condiciones Generales de la Oferta:</b><br/>"
        "1. <b>Validez de la oferta:</b> 30 días naturales desde la fecha de emisión.<br/>"
        "2. <b>Garantía:</b> 3 años en materiales e instalación conforme al REBT.<br/>"
        "3. <b>Forma de pago:</b> 40% al acopio de materiales, 40% durante la obra y 20% a la entrega del Certificado de Instalación Eléctrica (CIE)."
    )
    cond_box = Table([[Paragraph(condiciones_text, ParagraphStyle('Cond', parent=body_style, fontSize=8, leading=10.5))]], colWidths=[18.0*cm])
    cond_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_box),
        ('BOX', (0,0), (-1,-1), 0.5, c_secondary),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(cond_box)
    story.append(Spacer(1, 12))

    firma_block = [
        Paragraph("<b>ACEPTACIÓN Y CONFORMIDAD DEL CLIENTE</b>", ParagraphStyle('FirmaTit', parent=body_style, fontName='Helvetica-Bold', fontSize=9.5, textColor=c_primary)),
        Spacer(1, 16),
        Table([
            [
                Paragraph("<b>Por la Empresa Instaladora:</b><br/><br/><br/>________________________________________<br/>" + str(proyecto_info.get("empresa", "BOLIMUR")), body_style),
                Paragraph("<b>Aceptado por el Cliente:</b><br/><br/><br/>________________________________________<br/>Fecha y Firma", body_style)
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

    logo_path = "logo_bolimur.PNG"
    if not os.path.exists(logo_path):
        logo_path = "icono_bolimur.png"
    
    text_col = [
        Paragraph("ORDEN DE COMPRA Y LISTA DE ACOPIO DE MATERIALES", title_style),
        Paragraph("Listado clasificado por categorías para aprovisionamiento en tienda / almacén", subtitle_style)
    ]

    if os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=3.8*cm, height=2.53*cm)
            header_table = Table([[text_col, img]], colWidths=[14.0*cm, 4.0*cm])
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

    doc.build(story, canvasmaker=NumberedCanvasOrdenCompra)
    return buffer.getvalue()

