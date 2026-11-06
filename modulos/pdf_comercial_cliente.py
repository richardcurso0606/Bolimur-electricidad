# -*- coding: utf-8 -*-
"""
Módulo de generación de PDF comercial para clientes y listas de compra para almacén.
Permite emitir ofertas en Modo Empresa o Modo Autónomo, así como checklists de acopio imprimibles.
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

def _limpiar_texto(txt):
    if not txt:
        return ""
    # Reemplazar emojis o caracteres no compatibles con fuentes estándar Helvetica
    s = str(txt)
    reemplazos = {
        "🏢": "", "🧑‍🔧": "", "👤": "", "🔨": "", "📦": "", "📈": "", "📋": "", "🚗": "",
        "🚦": "", "🟢": "", "🔵": "", "🔴": "", "💰": "", "💶": "", "💵": "", "⚡": "",
        "🔌": "", "🏠": "", "📐": "", "🛋️": "", "🍳": "", "🛏️": "", "🚿": "", "🚪": "",
        "🌅": "", "🧺": "", "🔑": "", "🛡️": "", "📡": "", "🏆": "", "🏁": "", "🌐": "", "🏪": "",
        "🏛️": "", "🏷️": "", "🔍": "", "👁️": "", "✅": "", "⚠️": "", "❌": "", "🎯": "",
        "🛒": "", "📂": "", "📲": "", "💳": "", "✨": "", "•": "-"
    }
    for k, v in reemplazos.items():
        s = s.replace(k, v)
    # Filtrar caracteres fuera de latin-1 para compatibilidad garantizada con ReportLab
    s_clean = "".join(c for c in s if ord(c) < 256)
    return s_clean.strip()

class NumberedCanvasComercial(canvas.Canvas):
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
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        
        # Pie de página
        self.line(1.5*cm, 1.4*cm, 19.5*cm, 1.4*cm)
        self.drawString(1.5*cm, 0.9*cm, "BOLIMUR Software ElectroTécnico | Presupuesto Profesional y Garantía Legal REBT")
        self.drawRightString(19.5*cm, 0.9*cm, f"Página {self._pageNumber} de {page_count}")
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
    ]
    for p in posibles:
        if p and os.path.exists(p):
            return p
    return None

def generar_pdf_oferta_comercial(proyecto_info: dict, presupuesto_data: dict, modo: str = "autonomo") -> bytes:
    """
    Genera un presupuesto profesional para entregar al cliente.
    modo: 'autonomo' o 'empresa'
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.6*cm, bottomMargin=1.8*cm
    )

    styles = getSampleStyleSheet()
    
    es_emp = (modo.lower() == "empresa")
    color_banner = colors.HexColor("#0f172a") if es_emp else colors.HexColor("#16a34a")
    color_sub = colors.HexColor("#0284c7")
    
    title_style = ParagraphStyle(
        'DocTitle_Com', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=15, leading=19,
        textColor=colors.HexColor("#0f172a")
    )
    badge_style = ParagraphStyle(
        'Badge_Com', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=11,
        textColor=colors.white, alignment=1
    )
    norm_style = ParagraphStyle(
        'Norm_Com', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=12,
        textColor=colors.HexColor("#1e293b")
    )
    bold_style = ParagraphStyle(
        'Bold_Com', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=12,
        textColor=colors.HexColor("#0f172a")
    )
    desc_style = ParagraphStyle(
        'Desc_Com', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=11,
        textColor=colors.HexColor("#475569")
    )

    story = []

    # 1. ENCABEZADO CON LOGO Y DATOS DE EMPRESA
    logo_path = _obtener_logo_path()
    if logo_path:
        img_logo = Image(logo_path, width=4.8*cm, height=2.4*cm)
    else:
        img_logo = Paragraph("<b>BOLIMUR</b><br/><font size=7 color='#64748b'>INGENIERIA & ELECTRICIDAD</font>", title_style)

    badge_txt = "OFERTA COMERCIAL - MODELO EMPRESA" if es_emp else "PRESUPUESTO PROFESIONAL - MODO AUTONOMO"
    p_badge = Paragraph(f"<para align=center bgcolor='{color_banner.hexval()}'><font color=white><b>  {badge_txt}  </b></font></para>", badge_style)
    
    empresa_nom = _limpiar_texto(proyecto_info.get("empresa", "BOLIMUR ELECTRICIDAD"))
    licencia = _limpiar_texto(proyecto_info.get("licencia", "REBT-MU-2026 / DGEAIM"))
    tel = _limpiar_texto(proyecto_info.get("telefono", "+34 600 000 000"))
    email = _limpiar_texto(proyecto_info.get("email", "info@bolimur.es"))
    fecha_hoy = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))

    txt_empresa = Paragraph(f"""
    <b>{empresa_nom}</b><br/>
    <font size=8 color='#475569'>Instalador Autorizado REBT ({licencia})<br/>
    Tel: {tel} | Email: {email}<br/>
    Fecha de emisión: <b>{fecha_hoy}</b></font>
    """, norm_style)

    tabla_cabecera = Table([
        [img_logo, txt_empresa, p_badge]
    ], colWidths=[5.2*cm, 7.8*cm, 5.0*cm])
    tabla_cabecera.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tabla_cabecera)
    story.append(Spacer(1, 0.4*cm))

    # 2. CAJA DE DATOS DEL CLIENTE Y EXPEDIENTE
    cliente_nom = _limpiar_texto(proyecto_info.get("cliente", "Cliente Particular / Obra"))
    emplazamiento = _limpiar_texto(proyecto_info.get("direccion", proyecto_info.get("emplazamiento", "Direccion de la instalacion")))
    expediente = _limpiar_texto(proyecto_info.get("expediente", "EXP-BOL-2026"))
    validez = _limpiar_texto(proyecto_info.get("validez", "30 dias naturales"))
    concepto_obra = _limpiar_texto(proyecto_info.get("concepto", "Instalacion Electrica"))

    info_cliente_data = [
        [
            Paragraph(f"<b>CLIENTE / PROPIETARIO:</b><br/>{cliente_nom}", norm_style),
            Paragraph(f"<b>EMPLAZAMIENTO / OBRA:</b><br/>{emplazamiento}", norm_style)
        ],
        [
            Paragraph(f"<b>EXPEDIENTE / REF:</b> {expediente} | <b>VALIDEZ:</b> {validez}", norm_style),
            Paragraph(f"<b>OBJETO DE LA OFERTA:</b> {concepto_obra}", norm_style)
        ]
    ]
    t_cli = Table(info_cliente_data, colWidths=[9.0*cm, 9.0*cm])
    t_cli.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_cli)
    story.append(Spacer(1, 0.5*cm))

    # 3. CUADRO DE PARTIDAS Y CAPÍTULOS DE TRABAJO
    story.append(Paragraph("<b>DESGLOSE DE PARTIDAS Y MEMORIA VALORADA DE TRABAJOS:</b>", bold_style))
    story.append(Spacer(1, 0.2*cm))

    cabecera_partidas = [
        Paragraph("<b>Nº / Cap.</b>", bold_style),
        Paragraph("<b>Partida / Concepto Técnico</b>", bold_style),
        Paragraph("<b>Alcance y Descripción de los Trabajos</b>", bold_style),
        Paragraph("<b>Importe (€ S/IVA)</b>", ParagraphStyle('R_hdr', parent=bold_style, alignment=2))
    ]

    filas_partidas = [cabecera_partidas]
    items_presupuesto = presupuesto_data.get("partidas", [])
    if not items_presupuesto:
        # Partidas estándar automáticas del balance
        items_presupuesto = []
        part_idx = 1
        coste_mat_val = float(presupuesto_data.get("coste_materiales_venta", presupuesto_data.get("coste_materiales", 0.0)))
        if coste_mat_val > 0:
            items_presupuesto.append({
                "num": f"PART. {part_idx:02d}",
                "titulo": "Materiales Normalizados y Canalización",
                "desc": f"Suministro de materiales homologados conforme a REBT ({_limpiar_texto(presupuesto_data.get('detalle_materiales', 'Cables libres de halogenos, tubo corrugado M25/M32 e hilo telegestion'))}).",
                "importe": coste_mat_val
            })
            part_idx += 1

        coste_mo_val = float(presupuesto_data.get("coste_mo_venta", 0.0))
        if coste_mo_val > 0:
            items_presupuesto.append({
                "num": f"PART. {part_idx:02d}",
                "titulo": "Mano de Obra Especializada y Montaje",
                "desc": f"Tendido, fijacion y conexionado profesional ({presupuesto_data.get('horas_mo', 6.0):.1f} horas estimadas de instalador cualificado).",
                "importe": coste_mo_val
            })
            part_idx += 1

        coste_tram_val = float(presupuesto_data.get("coste_tramitacion", 0.0))
        if coste_tram_val > 0:
            items_presupuesto.append({
                "num": f"PART. {part_idx:02d}",
                "titulo": "Ensayos ITC-BT-05 y Certificado CIE / SIEM",
                "desc": "Medidas de aislamiento con megohmetro, continuidad, disparo diferencial y tramitacion oficial de boletin electrico ante Industria / SIEM.",
                "importe": coste_tram_val
            })
            part_idx += 1

        desp_val = float(presupuesto_data.get("desplazamiento", 0.0))
        if desp_val > 0:
            items_presupuesto.append({
                "num": f"PART. {part_idx:02d}",
                "titulo": "Desplazamiento y Medios Auxiliares",
                "desc": "Vehiculo de taller, acopio y portes al centro de trabajo.",
                "importe": desp_val
            })
            part_idx += 1

        for pa in presupuesto_data.get("partidas_adicionales", []):
            pa_tit = pa.get("titulo") or pa.get("concepto") or "Trabajos Adicionales"
            pa_desc = pa.get("desc") or pa.get("descripcion") or "Partida adicional de obra acordada con el cliente."
            pa_imp = float(pa.get("importe", 0.0))
            if pa_imp > 0:
                items_presupuesto.append({
                    "num": f"PART. {part_idx:02d}",
                    "titulo": pa_tit,
                    "desc": pa_desc,
                    "importe": pa_imp
                })
                part_idx += 1

    for p in items_presupuesto:
        num_str = p.get("num") or p.get("cap") or "PART."
        tit_str = _limpiar_texto(p.get("titulo") or p.get("concepto") or "")
        desc_str = _limpiar_texto(p.get("desc") or p.get("descripcion") or "")
        imp_val = float(p.get("importe", 0.0))

        filas_partidas.append([
            Paragraph(f"<b>{num_str}</b>", norm_style),
            Paragraph(f"<b>{tit_str}</b>", norm_style),
            Paragraph(desc_str, desc_style),
            Paragraph(f"<b>{imp_val:,.2f} €</b>", ParagraphStyle('R_val', parent=norm_style, alignment=2))
        ])

    t_partidas = Table(filas_partidas, colWidths=[2.2*cm, 5.0*cm, 7.8*cm, 3.0*cm])
    t_partidas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_partidas)
    story.append(Spacer(1, 0.4*cm))

    # 4. RESUMEN ECONÓMICO FINAL
    base_imponible = float(presupuesto_data.get("base_imponible", 0.0))
    iva_pct = float(presupuesto_data.get("iva_pct", 21.0))
    cuota_iva = float(presupuesto_data.get("cuota_iva", base_imponible * (iva_pct / 100.0)))
    total_cliente = float(presupuesto_data.get("total_cliente", base_imponible + cuota_iva))

    filas_totales = [
        [Paragraph("<b>BASE IMPONIBLE (NETO S/IVA):</b>", bold_style), Paragraph(f"<b>{base_imponible:,.2f} €</b>", ParagraphStyle('R_tot1', parent=bold_style, alignment=2))],
        [Paragraph(f"<b>CUOTA I.V.A. ({iva_pct:.0f}%):</b>", norm_style), Paragraph(f"{cuota_iva:,.2f} €", ParagraphStyle('R_tot2', parent=norm_style, alignment=2))],
        [Paragraph(f"<font size=10 color='{color_banner.hexval()}'><b>TOTAL FACTURA OFICIAL (C/IVA):</b></font>", bold_style), Paragraph(f"<font size=11 color='{color_banner.hexval()}'><b>{total_cliente:,.2f} €</b></font>", ParagraphStyle('R_tot3', parent=bold_style, alignment=2))]
    ]
    t_totales = Table(filas_totales, colWidths=[12.5*cm, 5.5*cm])
    t_totales.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1.5, color_banner),
        ('LINEBELOW', (0,0), (-1,1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_totales)
    story.append(Spacer(1, 0.4*cm))

    # 5. GARANTÍAS Y CONDICIONES
    plazo_txt = _limpiar_texto(proyecto_info.get("plazo", "1-2 dias laborables tras recepcion de materiales"))
    mostrar_fpago = bool(proyecto_info.get("mostrar_forma_pago", True))
    forma_pago_txt = _limpiar_texto(proyecto_info.get("forma_pago", ""))
    
    lineas_cond = [
        "<b>CONDICIONES Y GARANTIAS LEGALES:</b><br/>",
        "• <b>Garantia de Instalacion:</b> 3 anos de garantia oficial conforme a la Ley de Ordenacion de la Edificacion (LOE) y REBT RD 842/2002.<br/>",
        f"• <b>Plazo estimado de ejecucion:</b> {plazo_txt}.<br/>"
    ]
    if mostrar_fpago and forma_pago_txt:
        lineas_cond.append(f"• <b>Forma de pago acordada:</b> {forma_pago_txt}.<br/>")

    lineas_cond.extend([
        "• <b>Seguro de Responsabilidad Civil:</b> Cobertura profesional de instalador autorizado en vigor.<br/>",
        f"• <b>Validez de la oferta:</b> {validez}. Pasado este plazo, las tarifas de materiales pueden variar por tarifa de distribuidor."
    ])

    txt_condiciones = "".join(lineas_cond)
    p_cond = Paragraph(txt_condiciones, desc_style)
    story.append(p_cond)
    story.append(Spacer(1, 0.4*cm))

    # 6. CUADRO DE FIRMAS
    firmas_data = [
        [
            Paragraph("<b>POR LA EMPRESA INSTALADORA:</b><br/><br/><br/>________________________________________<br/>Firma y Sello Instalador Autorizado", desc_style),
            Paragraph("<b>CONFORMIDAD DEL CLIENTE:</b><br/><br/><br/>________________________________________<br/>Firma de aceptacion y fecha", desc_style)
        ]
    ]
    t_firmas = Table(firmas_data, colWidths=[9.0*cm, 9.0*cm])
    t_firmas.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_firmas)

    doc.build(story, canvasmaker=NumberedCanvasComercial)
    return buffer.getvalue()


def generar_pdf_lista_materiales_almacen(proyecto_info: dict, filas_materiales: list, coste_total_neto: float, iva_pct: float = 21.0) -> bytes:
    """
    Genera un checklist PDF imprimible para el almacén (Obramat, Saltoki, Electro Stocks).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.6*cm, bottomMargin=1.8*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle_Mat', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14, leading=18,
        textColor=colors.HexColor("#0f172a")
    )
    norm_style = ParagraphStyle(
        'Norm_Mat', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=11,
        textColor=colors.HexColor("#1e293b")
    )
    bold_style = ParagraphStyle(
        'Bold_Mat', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    desc_style = ParagraphStyle(
        'Desc_Mat', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10,
        textColor=colors.HexColor("#475569")
    )

    story = []

    # Encabezado
    logo_path = _obtener_logo_path()
    if logo_path:
        img_logo = Image(logo_path, width=4.5*cm, height=2.2*cm)
    else:
        img_logo = Paragraph("<b>BOLIMUR</b><br/><font size=7 color='#64748b'>ACOPIO DE MATERIALES</font>", title_style)

    badge_mat = Paragraph("<para align=center bgcolor='#0284c7'><font color=white><b>  LISTA DE COMPRA Y ACOPIO  </b></font></para>", bold_style)
    
    obra_nom = _limpiar_texto(proyecto_info.get("concepto", proyecto_info.get("nombre", "Obra Electrica")))
    instalador = _limpiar_texto(proyecto_info.get("instalador", "Instalador Autorizado"))
    fecha_hoy = proyecto_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))

    txt_hdr = Paragraph(f"""
    <b>ORDEN DE ACOPIO PARA MOSTRADOR DE ALMACEN</b><br/>
    <font size=8 color='#475569'>Obra / Proyecto: <b>{obra_nom}</b><br/>
    Solicitante: <b>{instalador}</b> | Fecha: <b>{fecha_hoy}</b></font>
    """, norm_style)

    t_hdr = Table([[img_logo, txt_hdr, badge_mat]], colWidths=[4.8*cm, 8.2*cm, 5.0*cm])
    t_hdr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_hdr)
    story.append(Spacer(1, 0.4*cm))

    # Tabla con checkboxes
    cabecera = [
        Paragraph("<b>Check</b>", ParagraphStyle('C_chk', parent=bold_style, alignment=1)),
        Paragraph("<b>Cant.</b>", bold_style),
        Paragraph("<b>Unid.</b>", bold_style),
        Paragraph("<b>Denominacion del Material / Articulo</b>", bold_style),
        Paragraph("<b>Donde Comprar (Proveedor)</b>", bold_style),
        Paragraph("<b>P. Unit</b>", ParagraphStyle('R_pu', parent=bold_style, alignment=2)),
        Paragraph("<b>Subtotal Est.</b>", ParagraphStyle('R_sub', parent=bold_style, alignment=2))
    ]
    filas_tabla = [cabecera]

    for idx, m in enumerate(filas_materiales):
        c_nom = _limpiar_texto(m.get("mat") or m.get("concepto") or m.get("nombre") or f"Articulo {idx+1}")
        c_cant = m.get("cant") or m.get("cantidad") or 1.0
        c_unid = _limpiar_texto(m.get("unid") or m.get("unidad") or "ud")
        c_pu = float(m.get("p_u") or m.get("precio_ud") or m.get("precio") or 0.0)
        c_sub = float(c_cant) * c_pu
        
        c_prov = _limpiar_texto(m.get("proveedor") or m.get("tienda") or m.get("donde_comprar") or "Obramat / Almacen")
        c_sku = _limpiar_texto(m.get("sku") or m.get("ref") or "")
        if c_sku and c_sku != "S/Ref":
            txt_prov = f"<b>{c_prov}</b><br/><font size=7 color='#64748b'>Ref: {c_sku}</font>"
        else:
            txt_prov = f"<b>{c_prov}</b>"

        filas_tabla.append([
            Paragraph("[  ]", ParagraphStyle('Chk_b', parent=bold_style, alignment=1, fontSize=11)),
            Paragraph(f"{c_cant}", norm_style),
            Paragraph(c_unid, norm_style),
            Paragraph(c_nom, norm_style),
            Paragraph(txt_prov, desc_style),
            Paragraph(f"{c_pu:,.2f} €", ParagraphStyle('R_val_pu', parent=norm_style, alignment=2)),
            Paragraph(f"{c_sub:,.2f} €", ParagraphStyle('R_val_sb', parent=norm_style, alignment=2))
        ])

    t_items = Table(filas_tabla, colWidths=[1.2*cm, 1.2*cm, 1.2*cm, 7.2*cm, 3.6*cm, 1.8*cm, 1.8*cm])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284c7")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 0.4*cm))

    # Totales
    cuota_iva = coste_total_neto * (iva_pct / 100.0)
    total_tienda = coste_total_neto + cuota_iva

    t_res = Table([
        [Paragraph("<b>TOTAL MATERIALES NETO (S/IVA):</b>", bold_style), Paragraph(f"<b>{coste_total_neto:,.2f} €</b>", ParagraphStyle('R_t1', parent=bold_style, alignment=2))],
        [Paragraph(f"<b>IVA ALMACEN ({iva_pct:.0f}%):</b>", norm_style), Paragraph(f"{cuota_iva:,.2f} €", ParagraphStyle('R_t2', parent=norm_style, alignment=2))],
        [Paragraph("<font color='#0284c7'><b>TOTAL ESTIMADO A PAGAR EN TIENDA / MOSTRADOR:</b></font>", bold_style), Paragraph(f"<font color='#0284c7'><b>{total_tienda:,.2f} €</b></font>", ParagraphStyle('R_t3', parent=bold_style, alignment=2))]
    ], colWidths=[12.5*cm, 5.5*cm])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0284c7")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("""
    <b>NOTAS PARA EL MOSTRADOR / ALMACEN:</b><br/>
    • Verificar que todos los conductores de cobre tengan marcado obligatorio CPR libre de halogenos (H07Z1-K / Afumex) segun ITC-BT-15.<br/>
    • Los tubos protectores empotrados o en superficie deben cumplir con resistencia al impacto minima IK08 y no propagadores de la llama.<br/>
    • Comprobar albaran y numero de bobinas antes de salir del almacen.
    """, desc_style))

    doc.build(story, canvasmaker=NumberedCanvasComercial)
    return buffer.getvalue()
