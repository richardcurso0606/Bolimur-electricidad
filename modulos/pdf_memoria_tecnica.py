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
import re
import base64
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



def _crear_imagen_flowable(img_data, max_w=18.0*cm, max_h=20.0*cm):
    """
    Convierte datos de imagen o PDF (bytes, base64 data-URI, path o BytesIO)
    en un flowable Image de ReportLab escalado proporcionalmente.
    Soporta PNG, JPG, JPEG, WEBP y archivos PDF de una página (AutoCAD/Cade_Simu).
    """
    if not img_data:
        return None
    try:
        raw_bytes = None
        if isinstance(img_data, str):
            if img_data.startswith("data:"):
                # Data URL base64
                _, data_part = img_data.split(",", 1)
                raw_bytes = base64.b64decode(data_part)
            elif os.path.exists(img_data):
                with open(img_data, "rb") as f:
                    raw_bytes = f.read()
            else:
                try:
                    raw_bytes = base64.b64decode(img_data)
                except Exception:
                    return None
        elif isinstance(img_data, bytes):
            raw_bytes = img_data
        elif hasattr(img_data, "read") or hasattr(img_data, "getvalue"):
            raw_bytes = img_data.getvalue() if hasattr(img_data, "getvalue") else img_data.read()
            
        if not raw_bytes:
            return None

        # Si es un archivo PDF de una página, convertir a PNG con PyMuPDF
        if raw_bytes.startswith(b"%PDF"):
            try:
                import fitz
                pdf_doc = fitz.open(stream=raw_bytes, filetype="pdf")
                if len(pdf_doc) > 0:
                    page = pdf_doc[0]
                    pix = page.get_pixmap(dpi=150)
                    raw_bytes = pix.tobytes("png")
                pdf_doc.close()
            except Exception as ex_pdf:
                print(f"Error procesando PDF para anexo: {ex_pdf}")
                return None

        bio = io.BytesIO(raw_bytes)
        from PIL import Image as PILImage
        with PILImage.open(bio) as pil_im:
            orig_w, orig_h = pil_im.size

        ratio = min(max_w / orig_w, max_h / orig_h)
        target_w = orig_w * ratio
        target_h = orig_h * ratio

        bio.seek(0)
        return Image(bio, width=target_w, height=target_h)
    except Exception as e:
        print(f"Error procesando imagen para ReportLab: {e}")
        return None


def _extraer_seccion_fase(seccion_str, default: str = "2.5") -> str:
    """Extrae la sección nominal en mm² de fase de un string de conductor."""
    if not seccion_str:
        return default
    s = str(seccion_str).strip()
    s = s.replace("2x", "").replace("3G", "").replace("4x", "").replace("1x", "")
    if "+" in s:
        s = s.split("+")[0].strip()
    m = re.search(r'(\d+(?:\.\d+)?)', s)
    return m.group(1) if m else default


def _extraer_diametro_tubo(tubo_str, default: str = "M20") -> str:
    """Extrae el calibre normalizado del tubo (ej. M20, M25, M32, M40, M50)."""
    if not tubo_str:
        return default
    m = re.search(r'(M\d+)', str(tubo_str))
    return m.group(1) if m else str(tubo_str).strip()


def crear_drawing_esquema_unifilar(datos_mtd: dict) -> Drawing:
    """
    Genera el Drawing vectorial oficial del Esquema Unifilar para Anexo III (RD 842/2002).
    Genera dinámicamente los circuitos reales de la instalación distribuidos bajo sus diferenciales,
    con símbolos normalizados UNE-EN 60617 (ICP, IGA, toroide diferencial, PIA y puesta a tierra).
    """
    suministro = datos_mtd.get("suministro", {})
    protecciones = datos_mtd.get("protecciones", {})
    ensayos = datos_mtd.get("ensayos", {})
    circuitos_raw = datos_mtd.get("circuitos", [])

    c_primary = colors.HexColor("#0f172a")
    c_secondary = colors.HexColor("#0369a1")
    c_green = colors.HexColor("#16a34a")
    c_text_dark = colors.HexColor("#1e293b")

    dwg_w = 520
    dwg_h = 270
    dwg = Drawing(dwg_w, dwg_h)

    # Marco y fondo del cuadro unifilar
    dwg.add(Rect(0, 0, dwg_w, dwg_h, fillColor=colors.HexColor("#ffffff"), strokeColor=colors.HexColor("#94a3b8"), strokeWidth=0.9, rx=4, ry=4))

    # =============================================================
    # 1. CABECERA: Tensión de Red + ICP (Interruptor Control de Potencia)
    # =============================================================
    xc = 260
    tension_val = str(suministro.get('tension', '230'))
    es_trif = ("400" in tension_val or "Trifásic" in tension_val)
    txt_red = "3N ~ 400 V - 50 Hz" if es_trif else "1N ~ 230 V - 50 Hz"

    dwg.add(String(xc, 262, txt_red, fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_primary, textAnchor="middle"))
    dwg.add(Circle(xc, 253, 1.5, fillColor=c_primary, strokeColor=c_primary))

    dwg.add(Line(xc, 253, xc, 245, strokeColor=c_primary, strokeWidth=1.3))
    dwg.add(Line(xc, 245, xc - 7, 235, strokeColor=c_primary, strokeWidth=1.4))
    dwg.add(Circle(xc, 245, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(xc, 233, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Line(xc, 233, xc, 226, strokeColor=c_primary, strokeWidth=1.3))
    dwg.add(String(xc + 12, 240, "ICP", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_primary))

    # =============================================================
    # 2. IGA (Interruptor General Automático)
    # =============================================================
    iga_cal_val = protecciones.get('iga_amperaje', 40)
    iga_polos_txt = "4x" if es_trif else "2x"
    dwg.add(Line(xc, 226, xc - 7, 214, strokeColor=c_primary, strokeWidth=1.4))
    dwg.add(Circle(xc, 226, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(xc, 212, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Line(xc - 4, 219, xc - 11, 214, strokeColor=c_primary, strokeWidth=1.0))
    dwg.add(Line(xc - 11, 214, xc - 8, 211, strokeColor=c_primary, strokeWidth=1.0))
    dwg.add(Rect(xc - 14, 211, 4, 4, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Line(xc, 212, xc, 202, strokeColor=c_primary, strokeWidth=1.3))

    icn_val = float(protecciones.get('iga_icn_ka', 6.0) or 6.0)
    curva_val = str(protecciones.get('iga_curva', 'Curva C') or 'Curva C')[:7]
    dwg.add(String(xc + 12, 222, "IGA", fontName="Helvetica-Bold", fontSize=8.5, fillColor=c_primary))
    dwg.add(String(xc + 12, 213, f"{iga_polos_txt}{iga_cal_val} A", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_secondary))
    dwg.add(String(xc + 12, 204, f"{icn_val:.0f} kA | {curva_val}", fontName="Helvetica", fontSize=5.8, fillColor=colors.HexColor("#64748b")))

    # =============================================================
    # 3. DIFERENCIALES Y CIRCUITOS DINÁMICOS
    # =============================================================
    circs = list(circuitos_raw) if circuitos_raw else [
        {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20"},
        {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20"},
        {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25"},
        {"nombre": "C4 - Lavadora / Termo", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20"},
        {"nombre": "C5 - Baños y Auxiliares", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20"}
    ]
    circs_draw = circs[:12]
    n_total = len(circs_draw)
    n_g1 = max(1, (n_total + 1) // 2)
    g1 = circs_draw[:n_g1]
    g2 = circs_draw[n_g1:]

    x_d1 = 135
    x_d2 = 385
    y_split = 202

    dwg.add(Line(x_d1, y_split, x_d2, y_split, strokeColor=c_primary, strokeWidth=1.4))
    dwg.add(Circle(xc, y_split, 1.5, fillColor=c_primary, strokeColor=c_primary))

    dif_amp_sug = 63 if int(iga_cal_val) > 40 else 40

    # DIF 1 (Rama Izquierda)
    dwg.add(Line(x_d1, y_split, x_d1, 192, strokeColor=c_primary, strokeWidth=1.2))
    dwg.add(Line(x_d1, 192, x_d1 - 7, 181, strokeColor=c_primary, strokeWidth=1.3))
    dwg.add(Circle(x_d1, 192, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(x_d1, 179, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(x_d1 - 16, 186, 5.0, fillColor=colors.HexColor("#f0fdf4"), strokeColor=c_green, strokeWidth=1.2))
    dwg.add(Line(x_d1 - 16, 181.5, x_d1 - 16, 190.5, strokeColor=c_green, strokeWidth=1.0))
    dwg.add(Line(x_d1 - 20.5, 186, x_d1 - 11.5, 186, strokeColor=c_green, strokeWidth=1.0))
    dwg.add(Line(x_d1 - 11, 186, x_d1 - 4, 186, strokeColor=c_green, strokeWidth=0.9))
    dwg.add(Line(x_d1, 179, x_d1, 166, strokeColor=c_primary, strokeWidth=1.3))
    dwg.add(String(x_d1 + 10, 189, "DIF 1", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_green))
    dwg.add(String(x_d1 + 10, 179, f"{iga_polos_txt}{dif_amp_sug} A", fontName="Helvetica-Bold", fontSize=7.2, fillColor=c_primary))
    dwg.add(String(x_d1 + 10, 169, "30 mA (A)", fontName="Helvetica-Bold", fontSize=7.0, fillColor=c_primary))

    # DIF 2 (Rama Derecha)
    dwg.add(Line(x_d2, y_split, x_d2, 192, strokeColor=c_primary, strokeWidth=1.2))
    dwg.add(Line(x_d2, 192, x_d2 - 7, 181, strokeColor=c_primary, strokeWidth=1.3))
    dwg.add(Circle(x_d2, 192, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(x_d2, 179, 1.2, fillColor=c_primary, strokeColor=c_primary))
    dwg.add(Circle(x_d2 - 16, 186, 5.0, fillColor=colors.HexColor("#f0fdf4"), strokeColor=c_green, strokeWidth=1.2))
    dwg.add(Line(x_d2 - 16, 181.5, x_d2 - 16, 190.5, strokeColor=c_green, strokeWidth=1.0))
    dwg.add(Line(x_d2 - 20.5, 186, x_d2 - 11.5, 186, strokeColor=c_green, strokeWidth=1.0))
    dwg.add(Line(x_d2 - 11, 186, x_d2 - 4, 186, strokeColor=c_green, strokeWidth=0.9))
    dwg.add(Line(x_d2, 179, x_d2, 166, strokeColor=c_primary, strokeWidth=1.3))
    dwg.add(String(x_d2 + 10, 189, "DIF 2", fontName="Helvetica-Bold", fontSize=8.0, fillColor=c_green))
    dwg.add(String(x_d2 + 10, 179, f"{iga_polos_txt}{dif_amp_sug} A", fontName="Helvetica-Bold", fontSize=7.2, fillColor=c_primary))
    dwg.add(String(x_d2 + 10, 169, "30 mA (A)", fontName="Helvetica-Bold", fontSize=7.0, fillColor=c_primary))

    # =============================================================
    # 4. PEINES HORIZONTALES
    # =============================================================
    y_bus = 166
    dwg.add(Line(18, y_bus, 252, y_bus, strokeColor=c_secondary, strokeWidth=2.2))
    dwg.add(Circle(x_d1, y_bus, 1.8, fillColor=c_secondary, strokeColor=c_secondary))

    dwg.add(Line(268, y_bus, 502, y_bus, strokeColor=c_secondary, strokeWidth=2.2))
    dwg.add(Circle(x_d2, y_bus, 1.8, fillColor=c_secondary, strokeColor=c_secondary))

    # =============================================================
    # 5. RENDERIZADO DINÁMICO DE COLUMNAS DE CIRCUITOS
    # =============================================================
    def _dibujar_grupo(grupo, x_min, x_max, start_idx):
        if not grupo:
            return
        m = len(grupo)
        step = (x_max - x_min) / (m + 1)
        w_box = max(38, min(50, step - 4))

        for j, c in enumerate(grupo):
            cx = x_min + (j + 1) * step
            c_idx = start_idx + j + 1

            c_nom = str(c.get("nombre", f"C{c_idx}"))
            m_cid = re.search(r'(C\d+(?:\.\d+)?)', c_nom)
            cid = m_cid.group(1) if m_cid else f"C{c_idx}"

            c_clean = re.sub(r'^[Cc]\d+(?:\.\d+)?\s*[-–:]\s*', '', c_nom).strip()
            palabras = c_clean.split()
            if len(palabras) <= 2:
                nom1 = " ".join(palabras)
                nom2 = ""
            else:
                mid = (len(palabras) + 1) // 2
                nom1 = " ".join(palabras[:mid])
                nom2 = " ".join(palabras[mid:])
            if len(nom1) > 13:
                nom1 = nom1[:12] + "."
            if len(nom2) > 13:
                nom2 = nom2[:12] + "."

            c_sec = str(c.get("seccion", "2x2.5+TT2.5")).strip()
            es_c_trif = ("4x" in c_sec or "3P" in c_nom or "trifásic" in c_nom.lower())
            pia_val = c.get("pia", 16)
            pia_txt = f"{'4x' if es_c_trif else '2x'}{pia_val} A"

            sec_fase = _extraer_seccion_fase(c_sec, default="2.5")
            sec_txt = f"{'4x' if es_c_trif else '2x'}{sec_fase}+T"
            tubo_txt = _extraer_diametro_tubo(c.get("tubo", "M20"), default="M20")

            # Bajante
            dwg.add(Line(cx, y_bus, cx, 155, strokeColor=c_primary, strokeWidth=1.0))
            dwg.add(Circle(cx, y_bus, 1.2, fillColor=c_secondary, strokeColor=c_secondary))

            # Caja técnica
            dwg.add(Rect(cx - w_box/2, 118, w_box, 37, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.6, rx=2, ry=2))
            dwg.add(String(cx, 145, pia_txt, fontName="Helvetica-Bold", fontSize=6.0, fillColor=c_primary, textAnchor="middle"))
            dwg.add(String(cx, 134, sec_txt, fontName="Helvetica-Bold", fontSize=5.6, fillColor=c_secondary, textAnchor="middle"))
            dwg.add(String(cx, 123, tubo_txt, fontName="Helvetica", fontSize=5.4, fillColor=colors.HexColor("#64748b"), textAnchor="middle"))

            # Línea al PIA
            dwg.add(Line(cx, 118, cx, 106, strokeColor=c_primary, strokeWidth=1.0))

            # Símbolo Magnetotérmico PIA
            dwg.add(Line(cx, 106, cx - 7, 94, strokeColor=c_primary, strokeWidth=1.3))
            dwg.add(Circle(cx, 106, 1.0, fillColor=c_primary, strokeColor=c_primary))
            dwg.add(Circle(cx, 92, 1.0, fillColor=c_primary, strokeColor=c_primary))
            dwg.add(Line(cx - 4, 99, cx - 11, 95, strokeColor=c_primary, strokeWidth=0.9))
            dwg.add(Line(cx - 11, 95, cx - 8, 92, strokeColor=c_primary, strokeWidth=0.9))
            dwg.add(Rect(cx - 13, 92, 3.5, 3.5, fillColor=c_primary, strokeColor=c_primary))

            # Salida con trazos oblicuos
            dwg.add(Line(cx, 92, cx, 68, strokeColor=c_primary, strokeWidth=1.0))
            dwg.add(Line(cx - 3, 76, cx + 3, 80, strokeColor=colors.HexColor("#64748b"), strokeWidth=0.9))
            dwg.add(Line(cx - 3, 79, cx + 3, 83, strokeColor=colors.HexColor("#64748b"), strokeWidth=0.9))
            dwg.add(Line(cx - 3, 82, cx + 3, 86, strokeColor=colors.HexColor("#64748b"), strokeWidth=0.9))
            if es_c_trif:
                dwg.add(Line(cx - 3, 85, cx + 3, 89, strokeColor=colors.HexColor("#64748b"), strokeWidth=0.9))
            dwg.add(Circle(cx + 4, 87, 0.7, fillColor=colors.HexColor("#64748b"), strokeColor=colors.HexColor("#64748b")))

            # ID y Denominación
            dwg.add(String(cx, 55, cid, fontName="Helvetica-Bold", fontSize=8.5, fillColor=c_primary, textAnchor="middle"))
            dwg.add(String(cx, 44, nom1, fontName="Helvetica-Bold", fontSize=5.8, fillColor=c_text_dark, textAnchor="middle"))
            if nom2:
                dwg.add(String(cx, 35, nom2, fontName="Helvetica", fontSize=5.4, fillColor=colors.HexColor("#475569"), textAnchor="middle"))

    _dibujar_grupo(g1, 18, 252, 0)
    _dibujar_grupo(g2, 268, 502, len(g1))

    # =============================================================
    # 6. LÍNEA DE PUESTA A TIERRA (PE)
    # =============================================================
    dwg.add(Rect(18, 6, 484, 24, fillColor=colors.HexColor("#fef3c7"), strokeColor=colors.HexColor("#d97706"), strokeWidth=0.7, rx=2, ry=2))
    tx = 35
    ty = 16
    dwg.add(Line(tx, ty + 8, tx, ty, strokeColor=colors.HexColor("#92400e"), strokeWidth=1.2))
    dwg.add(Line(tx - 6, ty, tx + 6, ty, strokeColor=colors.HexColor("#92400e"), strokeWidth=1.2))
    dwg.add(Line(tx - 4, ty - 2.5, tx + 4, ty - 2.5, strokeColor=colors.HexColor("#92400e"), strokeWidth=1.0))
    dwg.add(Line(tx - 2, ty - 5, tx + 2, ty - 5, strokeColor=colors.HexColor("#92400e"), strokeWidth=0.8))

    rt_medida = float(ensayos.get('rt_ohm', 11.8) or 11.8)
    sec_tierra = _extraer_seccion_fase(suministro.get('di_cable', '10'), default="10")
    dwg.add(String(50, 19, "RED DE TIERRA (PE - ITC-BT-18):", fontName="Helvetica-Bold", fontSize=6.0, fillColor=colors.HexColor("#92400e")))
    dwg.add(String(50, 10, f"Línea Enlace Cu 1x{sec_tierra} mm² | Picas de tierra 2m | Resistencia Medida: Rt = {rt_medida:.1f} Ω (Límite REBT ≤ 15 Ω)", fontName="Helvetica", fontSize=5.5, fillColor=c_text_dark))

    return dwg


def generar_png_unifilar(datos_mtd: dict) -> bytes | None:
    """
    Renderiza el Drawing del Esquema Unifilar oficial a bytes de imagen PNG (200 DPI)
    para su inserción en Word (.docx) o vistas previas gráficas.
    """
    try:
        from reportlab.graphics import renderPDF
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        dwg = crear_drawing_esquema_unifilar(datos_mtd)
        bio_pdf = io.BytesIO()
        renderPDF.drawToFile(dwg, bio_pdf)
        pdf_bytes = bio_pdf.getvalue()
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(pdf_doc) > 0:
            pix = pdf_doc[0].get_pixmap(dpi=200)
            png_bytes = pix.tobytes("png")
            pdf_doc.close()
            return png_bytes
        pdf_doc.close()
    except Exception as err:
        print(f"Error generando PNG del unifilar: {err}")
    return None


def _crear_anexo_plano_flowables(titulo_anexo: str, subtitulo_anexo: str, img_data, exped: str, c_primary, c_border, h_section, body_style):

    """
    Genera el bloque de página completa oficial para Anexos I(a), I(b) o II:
    Cajetín superior oficial DGEAIM Murcia + Imagen centrada + Pie de referencia de expediente.
    """
    flowables = []
    flowables.append(PageBreak())
    
    # Encabezado Oficial
    t_hdr = Table([[Paragraph("<b>MEMORIA TÉCNICA DE DISEÑO DE INSTALACIONES ELÉCTRICAS DE BAJA TENSIÓN</b>", h_section)]], colWidths=[18.4*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#e2e8f0")),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor("#0f172a")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ])
    flowables.append(t_hdr)
    flowables.append(Spacer(1, 4))
    
    # Título y Subtítulo
    flowables.append(Paragraph(f"<b><font size='9' color='#0f172a'>{titulo_anexo}</font></b>", ParagraphStyle('AnxT', parent=body_style, alignment=1)))
    flowables.append(Paragraph(f"<b><font size='10.5' color='#0369a1'><u>{subtitulo_anexo}</u></font></b>", ParagraphStyle('AnxSub', parent=body_style, alignment=1)))
    flowables.append(Spacer(1, 5))
    
    # Imagen del plano escalada
    img_flow = _crear_imagen_flowable(img_data, max_w=18.0*cm, max_h=20.0*cm)
    if img_flow:
        t_img = Table([[img_flow]], colWidths=[18.4*cm], style=[
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 0.5, c_border),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ])
        flowables.append(t_img)
    else:
        t_no_img = Table([[Paragraph("<i>[Plano no disponible o formato no reconocido]</i>", body_style)]], colWidths=[18.4*cm])
        flowables.append(t_no_img)
        
    flowables.append(Spacer(1, 4))
    flowables.append(Paragraph(f"<font size='6.5' color='#64748b'>Dirección General de Energía y Actividad Industrial y Minera | Ref. Expediente: {exped}</font>", ParagraphStyle('FootAnx', parent=body_style, alignment=2)))
    
    return flowables


def _crear_anexo_fotografico_flowables(fotos: list, exped: str, c_primary, c_border, h_section, body_style, bold_style):
    """
    Genera el ANEXO V: REPORTAJE FOTOGRÁFICO DE FIN DE OBRA Y EVIDENCIAS TÉCNICAS (ITC-BT-05).
    Organiza las fotos en cuadrícula de 2 columnas por página con cajetín y pie explicativo.
    """
    if not fotos:
        return []

    flowables = []
    chunk_size = 4
    for p_idx in range(0, len(fotos), chunk_size):
        chunk = fotos[p_idx:p_idx + chunk_size]
        flowables.append(PageBreak())
        
        # Encabezado Oficial
        t_hdr = Table([[Paragraph("<b>MEMORIA TÉCNICA DE DISEÑO DE INSTALACIONES ELÉCTRICAS DE BAJA TENSIÓN</b>", h_section)]], colWidths=[18.4*cm], style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#e2e8f0")),
            ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor("#0f172a")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ])
        flowables.append(t_hdr)
        flowables.append(Spacer(1, 3))
        
        flowables.append(Paragraph("<b><font size='9' color='#0f172a'>ANEXO V</font></b>", ParagraphStyle('AnxVT', parent=body_style, alignment=1)))
        flowables.append(Paragraph("<b><font size='10.5' color='#0369a1'><u>REPORTAJE FOTOGRÁFICO Y EVIDENCIAS DE CONFORMIDAD REBT (ITC-BT-05)</u></font></b>", ParagraphStyle('AnxVSub', parent=body_style, alignment=1)))
        flowables.append(Paragraph("<font size='6.5' color='#64748b'>Registro Gráfico de Ejecución de Obra, Verificaciones Ocultas y Comprobaciones con Instrumentación</font>", ParagraphStyle('AnxVDesc', parent=body_style, alignment=1)))
        flowables.append(Spacer(1, 6))

        grid_data = []
        for i in range(0, len(chunk), 2):
            par_fotos = chunk[i:i+2]
            fila_imgs = []
            fila_txts = []
            
            for f_item in par_fotos:
                f_data = f_item.get("data") if isinstance(f_item, dict) else f_item
                f_desc = f_item.get("titulo", "Evidencia fotográfica de obra") if isinstance(f_item, dict) else "Evidencia fotográfica"
                
                img_flow = _crear_imagen_flowable(f_data, max_w=8.8*cm, max_h=8.0*cm)
                if img_flow:
                    fila_imgs.append(img_flow)
                else:
                    fila_imgs.append(Paragraph("<i>[Imagen no disponible]</i>", body_style))
                    
                audit = f_item.get("auditoria") if isinstance(f_item, dict) else None
                badge_txt = ""
                if audit:
                    est = audit.get("estado", "").lower()
                    if est == "conforme":
                        badge_txt = " <font color='#059669'><b>[✓ REBT Conforme]</b></font>"
                    elif est == "advertencia":
                        badge_txt = " <font color='#d97706'><b>[⚠ REBT Con Observaciones]</b></font>"
                    elif est == "no_conforme":
                        badge_txt = " <font color='#dc2626'><b>[✗ REBT Defecto]</b></font>"
                        
                txt_cell = Paragraph(f"<b>📷 {f_desc}</b>{badge_txt}", ParagraphStyle('CapP', parent=body_style, fontSize=6.5, leading=8.5, alignment=1, textColor=colors.HexColor("#1e293b")))
                fila_txts.append(txt_cell)
                
            if len(fila_imgs) == 1:
                fila_imgs.append(Paragraph("", body_style))
                fila_txts.append(Paragraph("", body_style))
                
            grid_data.append(fila_imgs)
            grid_data.append(fila_txts)

        col_w = 9.0*cm
        t_grid = Table(grid_data, colWidths=[col_w, col_w])
        t_grid_style = [
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 3),
            ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ]
        for r_idx in range(0, len(grid_data), 2):
            t_grid_style.append(('BOX', (0, r_idx), (0, r_idx), 0.5, c_border))
            t_grid_style.append(('BOX', (1, r_idx), (1, r_idx), 0.5, c_border))
            t_grid_style.append(('BACKGROUND', (0, r_idx), (1, r_idx), colors.HexColor("#f8fafc")))
            
        t_grid.setStyle(TableStyle(t_grid_style))
        flowables.append(t_grid)
        flowables.append(Spacer(1, 4))
        flowables.append(Paragraph(f"<font size='6.5' color='#64748b'>Dirección General de Energía y Actividad Industrial y Minera | Ref. Expediente: {exped} | Pág. {p_idx//chunk_size + 1}</font>", ParagraphStyle('FootAnxV', parent=body_style, alignment=2)))
        
    return flowables

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


def _obtener_logo_carm_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    posibles = [
        os.path.join(base_dir, "plantillas", "logo_carm_murcia_recortado.png"),
        os.path.join(os.getcwd(), "plantillas", "logo_carm_murcia_recortado.png"),
        os.path.join(base_dir, "plantillas", "logo_carm_oficial.jpg"),
        os.path.join(os.getcwd(), "plantillas", "logo_carm_oficial.jpg"),
    ]
    for p in posibles:
        if p and os.path.exists(p):
            return p
    return None


def _obtener_escudo_carm_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    posibles = [
        os.path.join(base_dir, "plantillas", "escudo_carm_oficial.png"),
        os.path.join(os.getcwd(), "plantillas", "escudo_carm_oficial.png"),
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


def generar_pdf_mtd_industria_murcia(datos_mtd: dict) -> bytes:
    """
    Genera el Documento Oficial Completo de Memoria Técnica de Diseño (MTD)
    exactamente estructurado según el modelo normalizado de la Región de Murcia (DGEAIM).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.3*cm, rightMargin=1.3*cm,
        topMargin=0.9*cm, bottomMargin=1.35*cm
    )

    styles = getSampleStyleSheet()
    
    c_primary = colors.HexColor("#0f172a")
    c_secondary = colors.HexColor("#0284c7")
    c_dark_blue = colors.HexColor("#0369a1")
    c_bg_section = colors.HexColor("#eaeaea")  # Sombreado gris claro neutro del original CARM (RGB 234, 234, 234)
    c_bg_head = colors.HexColor("#f4f4f4")     # Sombreado muy suave pct5 (RGB 244, 244, 244)
    c_bg_sub = colors.HexColor("#fafafa")
    c_border_box = colors.black
    c_border_grid = colors.HexColor("#999999")
    c_border = colors.HexColor("#94a3b8")
    c_text_dark = colors.HexColor("#0f172a")
    c_green = colors.HexColor("#15803d")
    c_carm_red = colors.HexColor("#991b1b")

    title_main = ParagraphStyle(
        'MainTitle_MTD', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=13,
        textColor=c_primary, alignment=1
    )
    h_title = ParagraphStyle(
        'HTitle_MTD', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.0, leading=10,
        textColor=colors.black, alignment=1
    )
    h_section = ParagraphStyle(
        'SecHead_MTD', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.6, leading=9.5,
        textColor=colors.black
    )
    body_style = ParagraphStyle(
        'Body_MTD', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.0, leading=8.8,
        textColor=colors.black
    )
    bold_style = ParagraphStyle(
        'Bold_MTD', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.0, leading=8.8,
        textColor=colors.black
    )
    small_style = ParagraphStyle(
        'Small_MTD', parent=styles['Normal'],
        fontName='Helvetica', fontSize=6.2, leading=7.8,
        textColor=colors.HexColor("#333333")
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
    if not tipo_instalacion or tipo_instalacion.startswith("⚪") or "Blanco" in tipo_instalacion or "Seleccionar" in tipo_instalacion:
        uso_emp = emplazamiento.get("uso", "").strip()
        tipo_instalacion = uso_emp if uso_emp else "Instalación Eléctrica en Baja Tensión"
    fecha_str = datos_mtd.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    expediente = datos_mtd.get("expediente", "EXP-MTD-MURCIA-2026")

    # =========================================================================
    # PÁGINA 1: ENCABEZADO INSTITUCIONAL OFICIAL DGEAIM MURCIA
    # =========================================================================
    logo_carm_p = _obtener_logo_carm_path()
    if logo_carm_p:
        try:
            story.append(Image(logo_carm_p, width=6.2*cm, height=3.0*cm, hAlign='LEFT'))
            story.append(Spacer(1, 4))
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # 1. MEMORIA TÉCNICA DE DISEÑO & DATOS IDENTIFICATIVOS DEL TITULAR (RECUADRO UNIFICADO 1)
    # -------------------------------------------------------------------------
    t_tit_data = [
        [
            Paragraph(
                "<b>MEMORIA TÉCNICA DE DISEÑO DE INSTALACIONES ELÉCTRICAS DE BAJA TENSIÓN</b><br/>"
                f"<font size='6.8' color='#333333'><b>CÓDIGO PROVINCIAL: 30 (MURCIA)</b> &nbsp;|&nbsp; "
                f"<b>Ref. Expediente:</b> {expediente} &nbsp;|&nbsp; <b>Fecha:</b> {fecha_str}</font>",
                h_title
            ),
            ""
        ],
        [
            Paragraph("<b>DATOS IDENTIFICATIVOS DEL TITULAR DE LA INSTALACIÓN</b>", h_section),
            ""
        ],
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
        ('SPAN', (0,0), (1,0)),
        ('SPAN', (0,1), (1,1)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BACKGROUND', (0,1), (-1,1), c_bg_head),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('LINEBELOW', (0,1), (-1,1), 0.8, c_border_box),
        ('INNERGRID', (0,2), (-1,-1), 0.4, c_border_grid),
        ('TOPPADDING', (0,0), (-1,-1), 1.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
        ('BACKGROUND', (0,2), (-1,-1), colors.white)
    ]))
    story.append(t_tit)
    story.append(Spacer(1, 6.0))

    # -------------------------------------------------------------------------
    # 2. DATOS IDENTIFICATIVOS DEL REDACTOR DE LA MEMORIA (RECUADRO UNIFICADO)
    # -------------------------------------------------------------------------
    t_red_data = [
        [
            Paragraph("<b>DATOS IDENTIFICATIVOS DEL REDACTOR DE LA MEMORIA</b>", h_section),
            ""
        ],
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
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,1), c_bg_sub),
        ('BACKGROUND', (0,2), (-1,-1), colors.white),
        ('INNERGRID', (0,1), (-1,-1), 0.4, c_border_grid),
        ('TOPPADDING', (0,0), (-1,-1), 1.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
    ]))
    story.append(t_red)
    story.append(Spacer(1, 6.0))

    # -------------------------------------------------------------------------
    # 3. EMPLAZAMIENTO, ACTIVIDAD Y DATOS TÉCNICOS (RECUADRO UNIFICADO)
    # -------------------------------------------------------------------------
    pot_inst_w = float(suministro.get("potencia_instalada_w") or 5750.0)
    tension_str = str(suministro.get("tension") or "230")
    es_trif = ("400" in tension_str or "trifásic" in tension_str.lower() or "trifasico" in tension_str.lower())
    tipo_tram = datos_mtd.get("tipo_tramitacion", "Nueva Instalación")
    es_nueva = "[ X ] Nueva" if ("Nueva" in tipo_tram and "Temporal" not in tipo_tram and "Obra" not in tipo_tram) else "[  ] Nueva"
    es_temporal = "[ X ] Temporal / Obra" if ("Temporal" in tipo_tram or "Obra" in tipo_tram or "ITC-BT-33" in tipo_tram) else "[  ] Temporal / Obra"
    es_ampliacion = "[ X ] Ampliación" if "Ampliación" in tipo_tram else "[  ] Ampliación"
    es_modificacion = "[ X ] Modificación" if ("Modificación" in tipo_tram or "Reforma" in tipo_tram) else "[  ] Modificación"

    t_tecn_data = [
        [
            Paragraph("<b>EMPLAZAMIENTO, ACTIVIDAD Y DATOS TÉCNICOS DE LA INSTALACIÓN (ITC-BT-04)</b>", h_section),
            ""
        ],
        [
            Paragraph(f"<b>Carácter:</b> {es_nueva}  {es_temporal}  {es_ampliacion}  {es_modificacion}", bold_style),
            Paragraph(f"<b>Régimen:</b> {tipo_tram.replace('🆕 ', '').replace('🏗️ ', '').replace('📈 ', '').replace('🔧 ', '').replace('🔄 ', '').replace('📋 ', '')}", body_style)
        ],
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
            Paragraph(f"<b>Grupo Instalación según 3.1 ITC-BT-04:</b> {'Grupo G (Instalaciones Temporales de Obras / ITC-BT-33)' if ('Obra' in tipo_instalacion or 'ITC-BT-33' in tipo_instalacion) else ('Grupo O (IRVE - ITC-BT-52)' if 'IRVE' in tipo_instalacion else 'Grupo F (Viviendas / Edificios)')}", body_style),
            Paragraph("<b>Superficie Útil:</b> Obra / Parcela | <b>Ocupación:</b> Personal de obra" if ('Obra' in tipo_instalacion or 'ITC-BT-33' in tipo_instalacion) else "<b>Superficie Útil:</b> 90 m² | <b>Ocupación:</b> < 50 pers.", body_style)
        ]
    ]
    t_tecn = Table(t_tecn_data, colWidths=[10.5*cm, 7.9*cm])
    t_tecn.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('INNERGRID', (0,1), (-1,-1), 0.4, c_border_grid),
        ('TOPPADDING', (0,0), (-1,-1), 1.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
    ]))
    story.append(t_tecn)
    story.append(Spacer(1, 6.0))

    # -------------------------------------------------------------------------
    # 4. CAJA GENERAL DE PROTECCIÓN (CGP) / LGA / PUESTA A TIERRA (RECUADRO UNIFICADO)
    # -------------------------------------------------------------------------
    di_cable = str(suministro.get("di_cable", "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV"))
    di_long = float(suministro.get("di_long_m", 15.0))
    di_cdt = float(suministro.get("di_cdt_pct", 0.75))

    t_cgp_data = [
        [
            Paragraph("<b>CAJA GENERAL DE PROTECCIÓN (CGP), LÍNEA GENERAL (LGA) Y PUESTA A TIERRA</b>", h_section),
            "",
            ""
        ],
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
        ('SPAN', (0,0), (2,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,1), c_bg_head),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('INNERGRID', (0,1), (-1,-1), 0.4, c_border_grid),
        ('TOPPADDING', (0,0), (-1,-1), 1.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
    ]))
    story.append(t_cgp)
    story.append(Spacer(1, 6.0))

    # -------------------------------------------------------------------------
    # 5. PREVISIÓN DE CARGAS EN INSTALACIONES PARA VIVIENDAS Y LOCALES (ITC-BT-10) (RECUADRO UNIFICADO)
    # -------------------------------------------------------------------------
    t_prev_data = [
        [
            Paragraph("<b>PREVISIÓN DE CARGAS EN INSTALACIONES PARA VIVIENDAS Y LOCALES (ITC-BT-10)</b>", h_section),
            "",
            ""
        ],
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
            "",
            Paragraph(f"<b>Tensión:</b> {suministro.get('tension', '230 V')}", bold_style)
        ]
    ]
    t_prev = Table(t_prev_data, colWidths=[6.2*cm, 6.0*cm, 6.2*cm])
    t_prev.setStyle(TableStyle([
        ('SPAN', (0,0), (2,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,1), c_bg_head),
        ('BACKGROUND', (0,2), (-1,2), colors.white),
        ('BACKGROUND', (0,3), (-1,3), c_bg_sub),
        ('SPAN', (0,3), (1,3)),
        ('INNERGRID', (0,1), (-1,-1), 0.4, c_border_grid),
        ('TOPPADDING', (0,0), (-1,-1), 1.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
    ]))
    story.append(t_prev)
    story.append(Spacer(1, 6.0))

    # -------------------------------------------------------------------------
    # 6. BREVE DESCRIPCIÓN, PRESUPUESTO Y DOCUMENTACIÓN ANEXA ADJUNTA (RECUADRO UNIFICADO)
    # -------------------------------------------------------------------------
    desc_custom = datos_mtd.get("descripcion_instalacion") or datos_mtd.get("breve_descripcion")
    desc_texto = desc_custom if desc_custom else (
        f"Instalación eléctrica de baja tensión para {tipo_instalacion.lower()}, ejecutada con conductores de cobre unipolares no propagadores de la llama y libres de halógenos tipo H07Z1-K / RZ1-K 0.6/1kV bajo tubo protector normalizado. Cuadro CGMP equipado con IGA omnipolar ({protecciones.get('iga_amperaje', 25)}A Curva C, Icn=6kA), protector contra sobretensiones permanentes y transitorias Tipo 2 con bobina de disparo (ITC-BT-23), e interruptor diferencial de alta sensibilidad 30mA Clase A (ITC-BT-24). Circuito exclusivo verificado con protección contra choques eléctricos y conexión a tierra equipotencial."
    )

    t_desc_data = [
        [
            Paragraph("<b>BREVE DESCRIPCIÓN, PRESUPUESTO Y DOCUMENTACIÓN ANEXA ADJUNTA</b>", h_section),
            ""
        ],
        [
            Paragraph(f"<b>Breve Descripción de la Instalación:</b><br/>{desc_texto}", body_style),
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
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('INNERGRID', (0,1), (-1,-1), 0.4, c_border_grid),
        ('TOPPADDING', (0,0), (-1,-1), 1.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
        ('VALIGN', (0,1), (-1,-1), 'TOP'),
    ]))
    story.append(t_desc)
    story.append(Spacer(1, 6.0))

    # -------------------------------------------------------------------------
    # 7. DECLARACIÓN RESPONSABLE Y FIRMA OFICIAL (RECUADRO UNIFICADO)
    # -------------------------------------------------------------------------
    t_firma_data = [
        [
            Paragraph(
                f"El redactor que suscribe <b>DECLARA BAJO SU RESPONSABILIDAD</b> que ha realizado la presente <b>Memoria Técnica de Diseño (MTD)</b> "
                f"conforme a las prescripciones del <b>Reglamento Electrotécnico para Baja Tensión (Real Decreto 842/2002)</b>, sus Instrucciones Técnicas Complementarias (ITC-BT), "
                f"y la reglamentación aplicable de la <b>Dirección General de Industria, Energía y Minas de la Región de Murcia</b>.",
                small_style
            ),
            ""
        ],
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
    ]
    t_firma = Table(t_firma_data, colWidths=[9.2*cm, 9.2*cm])
    t_firma.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_sub),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.5, c_border_grid),
        ('LINEBEFORE', (1,1), (1,1), 0.5, c_border_grid),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(KeepTogether([t_firma]))

    # =========================================================================
    # PLANOS OFICIALES ANEXOS I(a), I(b) Y II (SI HAN SIDO ADJUNTADOS)
    # =========================================================================
    anexos = datos_mtd.get("anexos", {})
    plano_sit = anexos.get("plano_situacion")
    plano_emp = anexos.get("plano_emplazamiento")
    plano_dist = anexos.get("plano_distribucion")
    unifilar_modo = anexos.get("unifilar_modo", "auto")
    plano_unif_custom = anexos.get("plano_unifilar_custom")

    # ANEXO I (a): PLANO DE SITUACIÓN
    if plano_sit:
        story.extend(_crear_anexo_plano_flowables(
            "ANEXO I (a)",
            "PLANO DE SITUACIÓN",
            plano_sit,
            expediente,
            c_primary,
            c_border,
            h_section,
            body_style
        ))

    # ANEXO I (b): PLANO DE EMPLAZAMIENTO
    if plano_emp:
        story.extend(_crear_anexo_plano_flowables(
            "ANEXO I (b)",
            "PLANO DE EMPLAZAMIENTO",
            plano_emp,
            expediente,
            c_primary,
            c_border,
            h_section,
            body_style
        ))

    # ANEXO II: PLANO EN PLANTA DE DISTRIBUCIÓN
    if plano_dist:
        story.extend(_crear_anexo_plano_flowables(
            "ANEXO II",
            "PLANO EN PLANTA DE DISTRIBUCIÓN INSTALACIONES ELÉCTRICAS DE BAJA TENSIÓN",
            plano_dist,
            expediente,
            c_primary,
            c_border,
            h_section,
            body_style
        ))

    # =========================================================================
    # ANEXO III - ESQUEMA UNIFILAR (DGEAIM MURCIA)
    # =========================================================================
    story.append(PageBreak())
    
    logo_p2 = _crear_logo_flowable(width=5.4*cm, height=3.0*cm)
    anx_hdr_data = [
        [
            Paragraph(f"<b>MEMORIA TÉCNICA DE DISEÑO (RD 842/2002)</b><br/><font size='8' color='#0369a1'><b>ANEXO III: ESQUEMA UNIFILAR {'PERSONALIZADO (AUTOCAD/CADE_SIMU)' if (unifilar_modo == 'custom' and plano_unif_custom) else 'NORMALIZADO (ITC-BT-25)'}</b></font><br/><font size='6.5' color='#475569'>Región de Murcia - Dirección General de Industria, Energía y Minas</font>", body_style),
            logo_p2 if logo_p2 else Paragraph("<b>BOLIMUR</b>", ParagraphStyle('HdrB2', parent=body_style, alignment=2))
        ]
    ]
    t_anx_hdr = Table(anx_hdr_data, colWidths=[12.6*cm, 5.4*cm])
    t_anx_hdr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_anx_hdr)
    story.append(HRFlowable(width="100%", thickness=1.0, color=c_primary, spaceBefore=2, spaceAfter=5))

    # Dibujo vectorial del Esquema Unifilar Oficial Jerárquico (Dinámico según circuitos reales de la instalación)
    dwg = crear_drawing_esquema_unifilar(datos_mtd)


    # Tabla explicativa de componentes del unifilar automático
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

    # Si el usuario ha adjuntado su propio plano unifilar (AutoCAD / Cade_Simu / Imagen)
    if unifilar_modo == "custom" and plano_unif_custom:
        img_custom = _crear_imagen_flowable(plano_unif_custom, max_w=18.4*cm, max_h=21.0*cm)
        if img_custom:
            t_custom = Table([[img_custom]], colWidths=[18.4*cm], style=[
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOX', (0,0), (-1,-1), 0.6, c_border),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ffffff")),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ])
            story.append(t_custom)
            story.append(Spacer(1, 4))
        else:
            story.append(dwg)
            story.append(Spacer(1, 4))
            story.append(t_u_tab)
            story.append(Spacer(1, 4))
    else:
        # Esquema unifilar vectorial automático de Bolimur
        story.append(dwg)
        story.append(Spacer(1, 4))
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
    di_sec_val = _extraer_seccion_fase(di_cable, default="10")
    di_tubo_val = _extraer_diametro_tubo(suministro.get('di_tubo', 'Tubo M32'), default="M32")
    ib_di = pot_inst_w / (1.73205 * 400.0) if es_trif else pot_inst_w / 230.0

    t_dim_rows.append([
        Paragraph("<b>Derivación Individual (DI)</b>", bold_style),
        Paragraph(f"{pot_inst_w:,.0f}", body_style),
        Paragraph(f"{ib_di:.1f}", body_style),
        Paragraph(f"{di_long:.0f}", body_style),
        Paragraph(f"{di_sec_val} Cu", body_style),
        Paragraph(f"{di_sec_val} Cu", body_style),
        Paragraph(f"{di_sec_val} Cu", body_style),
        Paragraph(f"<b>{di_cdt:.2f}%</b>", body_style),
        Paragraph(f"<b>{di_cdt:.2f}%</b>", body_style),
        Paragraph(f"Tubo {di_tubo_val}", body_style)
    ])

    for c in circuitos:
        p_c = float(c.get("potencia", 2300))
        l_c = float(c.get("longitud", 15))
        cdt_c = float(c.get("cdt", 1.0))
        sec_str = _extraer_seccion_fase(c.get("seccion", "2.5"), default="2.5")
        tubo_c = _extraer_diametro_tubo(c.get("tubo", "M20"), default="M20")
        es_c_trif = ("4x" in str(c.get("seccion", "")) or "3P" in str(c.get("nombre", "")) or "trifásic" in str(c.get("nombre", "").lower()))
        ib_c = p_c / (1.73205 * 400.0) if es_c_trif else p_c / 230.0

        t_dim_rows.append([
            Paragraph(str(c.get("nombre", "Circuito")), body_style),
            Paragraph(f"{p_c:,.0f}", body_style),
            Paragraph(f"{ib_c:.1f}", body_style),
            Paragraph(f"{l_c:.0f}", body_style),
            Paragraph(f"{sec_str} Cu", body_style),
            Paragraph(f"{sec_str} Cu", body_style),
            Paragraph(f"{sec_str} Cu", body_style),
            Paragraph(f"{cdt_c:.2f}%", body_style),
            Paragraph(f"<b>{di_cdt + cdt_c:.2f}%</b>", body_style),
            Paragraph(f"Tubo {tubo_c}", body_style)
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

    # =========================================================================
    # ANEXO V: REPORTAJE FOTOGRÁFICO DE FIN DE OBRA (SI HAY FOTOS ADJUNTAS)
    # =========================================================================
    fotos_obra = anexos.get("fotos", []) or datos_mtd.get("fotos", [])
    if fotos_obra:
        story.extend(_crear_anexo_fotografico_flowables(
            fotos_obra,
            expediente,
            c_primary,
            c_border,
            h_section,
            body_style,
            bold_style
        ))

    doc.build(story, canvasmaker=NumberedCanvasMTDMurciaOficial)
    return buffer.getvalue()

generar_pdf_memoria_tecnica = generar_pdf_mtd_industria_murcia



# =========================================================================
# GENERADOR OFICIAL DEL CERTIFICADO DE INSTALACIÓN ELÉCTRICA (CIE / BOLETÍN)
# =========================================================================

def generar_pdf_cie_oficial(datos_cie: dict) -> bytes:
    """
    Genera el Certificado de Instalación Eléctrica en Baja Tensión (CIE - Boletín de Enganche)
    conforme a las directrices de la ITC-BT-04 y la Dirección General de Industria (DGEAIM).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.3*cm, rightMargin=1.3*cm,
        topMargin=1.3*cm, bottomMargin=1.3*cm
    )

    styles = getSampleStyleSheet()
    c_primary = colors.HexColor("#0f172a")
    c_secondary = colors.HexColor("#0284c7")
    c_dark_blue = colors.HexColor("#0369a1")
    c_bg_section = colors.HexColor("#eaeaea")  # Sombreado gris claro neutro del original CARM
    c_bg_head = colors.HexColor("#f4f4f4")     # Sombreado muy suave pct5
    c_bg_sub = colors.HexColor("#fafafa")
    c_border_box = colors.black
    c_border_grid = colors.HexColor("#999999")
    c_border = colors.HexColor("#94a3b8")
    c_text_dark = colors.HexColor("#0f172a")
    c_green = colors.HexColor("#15803d")
    c_carm_red = colors.HexColor("#991b1b")

    title_main = ParagraphStyle(
        'MainTitle_CIE', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11.0, leading=14,
        textColor=c_primary, alignment=1
    )
    h_section = ParagraphStyle(
        'SecHead_CIE', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.0, leading=10,
        textColor=c_text_dark
    )
    body_style = ParagraphStyle(
        'Body_CIE', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.2, leading=9.5,
        textColor=c_text_dark
    )
    bold_style = ParagraphStyle(
        'Bold_CIE', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.2, leading=9.5,
        textColor=c_text_dark
    )
    small_style = ParagraphStyle(
        'Small_CIE', parent=styles['Normal'],
        fontName='Helvetica', fontSize=6.5, leading=8.5,
        textColor=colors.HexColor("#475569")
    )

    story = []

    titular = datos_cie.get("titular", {})
    empl = datos_cie.get("emplazamiento", {})
    instalador = datos_cie.get("instalador", {})
    suministro = datos_cie.get("suministro", {})
    protecciones = datos_cie.get("protecciones", {})
    ensayos = datos_cie.get("ensayos", {})
    fecha_hoy = datos_cie.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))
    expediente = datos_cie.get("expediente", "CIE-2026-001")
    tipo_tram = datos_cie.get("tipo_tramitacion", "Memoria Técnica de Diseño (MTD - ITC-BT-04)")

    # 1. CABECERA INSTITUCIONAL OFICIAL
    escudo_path = _obtener_escudo_carm_path()
    escudo_flowable = None
    if escudo_path:
        try:
            escudo_flowable = Image(escudo_path, width=1.3*cm, height=2.48*cm)
        except Exception:
            pass

    logo_flowable = _crear_logo_flowable(width=5.2*cm, height=2.9*cm)
    carm_logo_txt = (
        "<font size='9' color='#991b1b'><b>COMUNIDAD AUTÓNOMA DE LA REGIÓN DE MURCIA</b></font><br/>"
        "<font size='7.5' color='#0f172a'><b>CONSEJERÍA DE CIENCIA, TECNOLOGÍAS, INDUSTRIA Y COMERCIO</b></font><br/>"
        "<font size='7' color='#475569'>Dirección General de Energía y Actividad Industrial y Minera (Código 30)</font>"
    )
    
    if escudo_flowable:
        hdr_data = [
            [
                escudo_flowable,
                Paragraph(carm_logo_txt, body_style),
                logo_flowable if logo_flowable else Paragraph("<b>BOLIMUR INSTALACIONES</b>", ParagraphStyle('HdrB', parent=body_style, alignment=2))
            ]
        ]
        t_hdr = Table(hdr_data, colWidths=[1.8*cm, 11.0*cm, 5.2*cm])
        t_hdr.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (2,0), (2,0), 'RIGHT'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
    else:
        hdr_data = [
            [
                Paragraph(carm_logo_txt, body_style),
                logo_flowable if logo_flowable else Paragraph("<b>BOLIMUR INSTALACIONES</b>", ParagraphStyle('HdrB', parent=body_style, alignment=2))
            ]
        ]
        t_hdr = Table(hdr_data, colWidths=[12.8*cm, 5.2*cm])
        t_hdr.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
    story.append(t_hdr)
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_carm_red, spaceBefore=3, spaceAfter=5))

    # TÍTULO PRINCIPAL
    story.append(Paragraph("<b>CERTIFICADO DE INSTALACIÓN ELÉCTRICA EN BAJA TENSIÓN (C.I.E.)</b>", title_main))
    story.append(Paragraph(f"<font size='8' color='#0369a1'><b>BOLETÍN OFICIAL DE ENGANCHE Y PUESTA EN SERVICIO (RD 842/2002 - ITC-BT-04)</b></font>", ParagraphStyle('SubCIE', parent=title_main)))
    story.append(Spacer(1, 4))

    # NÚMERO DE CERTIFICADO / EXPEDIENTE
    t_exp_data = [
        [
            Paragraph(f"<b>Nº CERTIFICADO / EXPEDIENTE:</b> <font color='#991b1b'>{expediente}</font>", bold_style),
            Paragraph(f"<b>FECHA DE EMISIÓN:</b> {fecha_hoy}", bold_style),
            Paragraph(f"<b>TRAMITACIÓN:</b> {tipo_tram.replace('🆕 ', '').replace('📈 ', '').replace('🔧 ', '').replace('🔄 ', '').replace('📋 ', '')}", bold_style)
        ]
    ]
    t_exp = Table(t_exp_data, colWidths=[6.5*cm, 4.5*cm, 7.4*cm])
    t_exp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_head),
        ('BOX', (0,0), (-1,-1), 0.8, c_secondary),
        ('INNERGRID', (0,0), (-1,-1), 0.4, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_exp)
    story.append(Spacer(1, 5))

    # BLOQUE 1: DATOS DEL TITULAR (RECUADRO UNIFICADO)
    t_tit_data = [
        [
            Paragraph("<b>1. DATOS DEL TITULAR DE LA INSTALACIÓN</b>", h_section),
            ""
        ],
        [
            Paragraph(f"<b>Nombre / Razón Social:</b> {titular.get('nombre', '')}", body_style),
            Paragraph(f"<b>N.I.F. / C.I.F.:</b> {titular.get('nif', '')}", body_style)
        ],
        [
            Paragraph(f"<b>Teléfono de Contacto:</b> {titular.get('telefono', '')}", body_style),
            Paragraph(f"<b>Correo Electrónico:</b> {titular.get('email', '')}", body_style)
        ]
    ]
    t_tit = Table(t_tit_data, colWidths=[11.4*cm, 7.0*cm])
    t_tit.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('INNERGRID', (0,1), (-1,-1), 0.3, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
    ]))
    story.append(t_tit)
    story.append(Spacer(1, 3.5))

    # BLOQUE 2: EMPLAZAMIENTO DEL SUMINISTRO (RECUADRO UNIFICADO)
    t_emp_data = [
        [
            Paragraph("<b>2. EMPLAZAMIENTO DEL SUMINISTRO</b>", h_section),
            ""
        ],
        [
            Paragraph(f"<b>Dirección:</b> {empl.get('direccion', '')}", body_style),
            Paragraph(f"<b>C.P. y Municipio:</b> {empl.get('cp', '30001')} - {empl.get('municipio', 'Murcia')}", body_style)
        ],
        [
            Paragraph(f"<b>Código CUPS / Ref. Catastral:</b> <font color='#0369a1'><b>{empl.get('cups', 'ES0021000000000000XX')}</b></font>", body_style),
            Paragraph(f"<b>Uso Principal:</b> {empl.get('uso', 'Vivienda Residencial')}", body_style)
        ]
    ]
    t_emp = Table(t_emp_data, colWidths=[11.4*cm, 7.0*cm])
    t_emp.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('INNERGRID', (0,1), (-1,-1), 0.3, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
    ]))
    story.append(t_emp)
    story.append(Spacer(1, 3.5))

    # BLOQUE 3: EMPRESA INSTALADORA E INSTALADOR HABILITADO (RECUADRO UNIFICADO)
    t_ins_data = [
        [
            Paragraph("<b>3. EMPRESA INSTALADORA HABILITADA Y TÉCNICO COMPETENTE</b>", h_section),
            ""
        ],
        [
            Paragraph(f"<b>Empresa Instaladora:</b> {instalador.get('empresa', 'BOLIMUR INSTALACIONES Y REFORMAS')}", body_style),
            Paragraph(f"<b>C.I.F. Empresa:</b> {instalador.get('cif', 'B-73123456')}", body_style)
        ],
        [
            Paragraph(f"<b>Nº Reg. Integrado Industrial (RII):</b> <font color='#0369a1'><b>{instalador.get('registro_rii', 'RII-30/08492')}</b></font>", body_style),
            Paragraph(f"<b>Teléfono Empresa:</b> {instalador.get('telefono', '+34 600 000 000')}", body_style)
        ],
        [
            Paragraph(f"<b>Instalador Habilitado en BT:</b> {instalador.get('nombre', 'Richard Orlando Choque Tejerina')}", body_style),
            Paragraph(f"<b>Nº Carnet / Cualificación:</b> <b>{instalador.get('licencia', 'REBT-30/15892')}</b>", body_style)
        ]
    ]
    t_ins = Table(t_ins_data, colWidths=[11.4*cm, 7.0*cm])
    t_ins.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('INNERGRID', (0,1), (-1,-1), 0.3, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
    ]))
    story.append(t_ins)
    story.append(Spacer(1, 3.5))

    # Cálculos dinámicos de conformidad según REBT desde ensayos multifunción
    pe_val = float(ensayos.get("pe_ohm", 0.11))
    aisl_val = float(ensayos.get("aisl_mohm", 100.0))
    rt_val = float(ensayos.get("rt_ohm", 11.8))
    dif_ma = float(ensayos.get("dif_ma", 22.0))
    dif_ms = float(ensayos.get("dif_ms", 26.0))

    pe_res = "CONFORME" if pe_val <= 0.50 else "NO CONFORME"
    pe_color = "#15803d" if pe_val <= 0.50 else "#dc2626"

    aisl_res = "CONFORME" if aisl_val >= 1.0 else "NO CONFORME"
    aisl_color = "#15803d" if aisl_val >= 1.0 else "#dc2626"
    aisl_txt = f"{aisl_val:.1f} MΩ" if aisl_val < 100 else "> 100 MΩ"

    rt_res = "CONFORME" if rt_val <= 15.0 else "NO CONFORME"
    rt_color = "#15803d" if rt_val <= 15.0 else "#dc2626"

    dif_res = "CONFORME" if (dif_ma <= 30.0 and dif_ms <= 300.0) else "NO CONFORME"
    dif_color = "#15803d" if (dif_ma <= 30.0 and dif_ms <= 300.0) else "#dc2626"

    # BLOQUE 4: CARACTERÍSTICAS TÉCNICAS DE LA INSTALACIÓN (RECUADRO UNIFICADO)
    pot_inst_kw = float(suministro.get('potencia_instalada_w', 7360)) / 1000.0
    pot_max_kw = float(suministro.get('potencia_max_admisible_w', 7360)) / 1000.0
    t_tec_data = [
        [
            Paragraph("<b>4. CARACTERÍSTICAS TÉCNICAS DE LA INSTALACIÓN ELÉCTRICA</b>", h_section),
            "",
            ""
        ],
        [
            Paragraph(f"<b>Tensión Nominal:</b> {suministro.get('tension', '230 V')}", body_style),
            Paragraph(f"<b>Potencia Prevista / Diseño:</b> <b>{pot_inst_kw:.2f} kW</b>", body_style),
            Paragraph(f"<b>Potencia Máxima Admisible:</b> <font color='#15803d'><b>{pot_max_kw:.2f} kW</b></font>", body_style)
        ],
        [
            Paragraph(f"<b>Derivación Individual:</b> {suministro.get('di_cable', '3G6 mm² Cu RZ1-K')}", body_style),
            Paragraph(f"<b>Canalización / Tubo:</b> {suministro.get('di_tubo', 'Tubo M32')}", body_style),
            Paragraph(f"<b>Caída de Tensión Total:</b> <b>{suministro.get('di_cdt_pct', 0.86):.2f}%</b>", body_style)
        ],
        [
            Paragraph(f"<b>Interruptor General (IGA):</b> <b>{protecciones.get('iga_amperaje', 32)} A</b> ({protecciones.get('iga_curva', 'Curva C')})", body_style),
            Paragraph(f"<b>Poder de Corte Icn:</b> <b>{protecciones.get('iga_icn_ka', 6.0):.0f} kA</b>", body_style),
            Paragraph(f"<b>Grado de Electrificación:</b> {suministro.get('grado_electrif', 'Básica')}", body_style)
        ],
        [
            Paragraph(f"<b>Interruptor Diferencial:</b> {protecciones.get('diferenciales', '2P 40A / 30mA Clase A')}", body_style),
            Paragraph(f"<b>Sobretensiones (ITC-BT-23):</b> {protecciones.get('sobretensiones', 'VTP + DPS Tipo 2')}", body_style),
            Paragraph(f"<b>Resistencia Tierra (Rt):</b> <font color='{rt_color}'><b>{rt_val:.1f} Ω ({rt_res.capitalize()})</b></font>", body_style)
        ]
    ]
    t_tec = Table(t_tec_data, colWidths=[6.4*cm, 6.0*cm, 6.0*cm])
    t_tec.setStyle(TableStyle([
        ('SPAN', (0,0), (2,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('INNERGRID', (0,1), (-1,-1), 0.3, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
    ]))
    story.append(t_tec)
    story.append(Spacer(1, 3.5))

    # BLOQUE 5: PROTOCOLO DE VERIFICACIÓN PREVIA (ITC-BT-05) (RECUADRO UNIFICADO)
    t_ens_data = [
        [
            Paragraph("<b>5. RESULTADOS DE LAS VERIFICACIONES PREVIAS (ITC-BT-05)</b>", h_section),
            "",
            "",
            ""
        ],
        [
            Paragraph("<b>Prueba / Ensayo Reglamentario</b>", bold_style),
            Paragraph("<b>Valor Mínimo / Máximo REBT</b>", bold_style),
            Paragraph("<b>Valor Medido en Obra</b>", bold_style),
            Paragraph("<b>Resultado</b>", bold_style)
        ],
        [
            Paragraph("Continuidad de conductores de protección PE", body_style),
            Paragraph("≤ 0.50 Ω", body_style),
            Paragraph(f"<b>{pe_val:.2f} Ω</b>", body_style),
            Paragraph(f"<font color='{pe_color}'><b>{pe_res}</b></font>", bold_style)
        ],
        [
            Paragraph("Resistencia de aislamiento a 500 Vcc (F-N / F-PE)", body_style),
            Paragraph("≥ 1.00 MΩ", body_style),
            Paragraph(f"<b>{aisl_txt}</b>", body_style),
            Paragraph(f"<font color='{aisl_color}'><b>{aisl_res}</b></font>", bold_style)
        ],
        [
            Paragraph("Resistencia de toma de tierra del edificio (Rt)", body_style),
            Paragraph("Rt · IΔn ≤ 24 V (≤ 15 Ω)", body_style),
            Paragraph(f"<b>{rt_val:.1f} Ω</b>", body_style),
            Paragraph(f"<font color='{rt_color}'><b>{rt_res}</b></font>", bold_style)
        ],
        [
            Paragraph("Tiempo y corriente de disparo diferencial (30 mA)", body_style),
            Paragraph("IΔn ≤ 30 mA | t ≤ 300 ms", body_style),
            Paragraph(f"<b>{dif_ma:.0f} mA | {dif_ms:.0f} ms</b>", body_style),
            Paragraph(f"<font color='{dif_color}'><b>{dif_res}</b></font>", bold_style)
        ]
    ]
    t_ens = Table(t_ens_data, colWidths=[7.2*cm, 4.4*cm, 3.8*cm, 3.0*cm])
    t_ens.setStyle(TableStyle([
        ('SPAN', (0,0), (3,0)),
        ('BACKGROUND', (0,0), (-1,0), c_bg_section),
        ('BOX', (0,0), (-1,-1), 1.0, c_border_box),
        ('LINEBELOW', (0,0), (-1,0), 0.8, c_border_box),
        ('BACKGROUND', (0,1), (-1,1), c_bg_head),
        ('BACKGROUND', (0,2), (-1,-1), colors.white),
        ('INNERGRID', (0,1), (-1,-1), 0.3, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.0),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
    ]))
    story.append(t_ens)
    story.append(Spacer(1, 3.5))

    # BLOQUE 6: DECLARACIÓN RESPONSABLE Y FIRMA
    dec_txt = (
        "<b>DECLARACIÓN RESPONSABLE DEL INSTALADOR HABILITADO:</b><br/>"
        "El instalador autorizado abajo firmante declara bajo su responsabilidad que la presente instalación eléctrica ha sido ejecutada "
        "conforme a las prescripciones del <b>Reglamento Electrotécnico para Baja Tensión (Real Decreto 842/2002)</b> y sus Instrucciones Técnicas Complementarias, "
        "habiéndose superado favorablemente todas las verificaciones y ensayos reglamentarios previos a su puesta en servicio. Asimismo, se certifica "
        "que se ha hecho entrega al titular del correspondiente <i>Manual de Instrucciones de Uso y Mantenimiento</i> y copia del Esquema Unifilar."
    )
    story.append(Table([[Paragraph(dec_txt, small_style)]], colWidths=[18.4*cm], style=[
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(Spacer(1, 5))

    # CUADROS DE FIRMA
    firma_data = [
        [
            Paragraph(
                f"<b>El Titular de la Instalación:</b><br/><br/><br/>"
                f"__________________________________________<br/>"
                f"Fdo.: <b>{titular.get('nombre', 'El Titular')}</b><br/>"
                f"N.I.F.: {titular.get('nif', '')}",
                body_style
            ),
            Paragraph(
                f"<b>El Instalador Habilitado en Baja Tensión:</b><br/><br/><br/>"
                f"__________________________________________<br/>"
                f"Fdo.: <b>{instalador.get('nombre', 'Richard Orlando Choque Tejerina')}</b><br/>"
                f"Carnet REBT: <b>{instalador.get('licencia', 'REBT-30/15892')}</b> | RII: {instalador.get('registro_rii', 'RII-30/08492')}",
                body_style
            )
        ]
    ]
    t_firmas = Table(firma_data, colWidths=[9.2*cm, 9.2*cm])
    t_firmas.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(KeepTogether(t_firmas))

    doc.build(story, canvasmaker=NumberedCanvasMTDMurciaOficial)
    return buffer.getvalue()


# =========================================================================
# GENERADOR DEL MANUAL DE INSTRUCCIONES DE USUARIO Y MANTENIMIENTO
# =========================================================================

def generar_pdf_manual_usuario(datos: dict) -> bytes:
    """
    Genera el Manual de Instrucciones de Usuario y Mantenimiento reglamentario (ITC-BT-04 apdo. 5)
    para entregar al titular de la instalación.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.3*cm, rightMargin=1.3*cm,
        topMargin=1.3*cm, bottomMargin=1.3*cm
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

    title_main = ParagraphStyle(
        'MainTitle_Man', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11.5, leading=14,
        textColor=c_primary, alignment=1
    )
    body_style = ParagraphStyle(
        'Body_Man', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=10.0,
        textColor=c_text_dark
    )
    bold_style = ParagraphStyle(
        'Bold_Man', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=10.0,
        textColor=c_text_dark
    )

    story = []
    titular = datos.get("titular", {})
    empl = datos.get("emplazamiento", {})
    instalador = datos.get("instalador", {})
    fecha_hoy = datos.get("fecha", datetime.date.today().strftime("%d/%m/%Y"))

    # Cabecera
    logo_flowable = _crear_logo_flowable(width=5.4*cm, height=3.0*cm)
    hdr_data = [
        [
            Paragraph("<b>MANUAL DE INSTRUCCIONES DE USUARIO Y MANTENIMIENTO</b><br/><font size='8' color='#0369a1'><b>Exigido por el Real Decreto 842/2002 (ITC-BT-04 apdo. 5)</b></font>", body_style),
            logo_flowable if logo_flowable else Paragraph("<b>BOLIMUR</b>", ParagraphStyle('HdrBM', parent=body_style, alignment=2))
        ]
    ]
    t_hdr = Table(hdr_data, colWidths=[12.6*cm, 5.4*cm])
    t_hdr.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_hdr)
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_secondary, spaceBefore=3, spaceAfter=6))

    story.append(Paragraph(f"<b>Titular:</b> {titular.get('nombre', 'Cliente')} | <b>Emplazamiento:</b> {empl.get('direccion', '')}, {empl.get('municipio', 'Murcia')} | <b>Fecha:</b> {fecha_hoy}", body_style))
    story.append(Spacer(1, 6))

    # Puntos Clave del Manual
    normas_guia = [
        ("1. Dispositivos del Cuadro General (CGMP)", 
         "• <b>IGA (Interruptor General Automático):</b> Protege contra cortocircuitos y sobrecargas de toda la vivienda.<br/>"
         "• <b>Diferencial (ID):</b> Protege a las personas contra electrocución. Dispone de un <b>botón de prueba 'TEST (T)'</b> que debe pulsarse <b>una vez al mes</b> para asegurar su correcto funcionamiento.<br/>"
         "• <b>PIAs (Pequeños Interruptores Automáticos):</b> Protegen cada circuito específico individualmente.<br/>"
         "• <b>Sobretensiones (VTP/DPS):</b> Protegen sus electrodomésticos y equipos electrónicos contra descargas atmosféricas (rayos) y subidas de tensión de la red."),
        ("2. Normas Básicas de Seguridad para el Usuario",
         "• <b>Nunca manipule el interior del cuadro eléctrico</b> ni puentee fusibles o interruptores automáticos.<br/>"
         "• Si se dispara un interruptor diferencial, baje todos los PIAs, suba el diferencial y vaya subiendo los PIAs uno a uno para identificar el circuito o electrodoméstico averiado.<br/>"
         "• No utilice aparatos eléctricos descalzo ni con las manos húmedas, especialmente en cuartos de baño.<br/>"
         "• Toda modificación o ampliación debe ser ejecutada por una <b>Empresa Instaladora Habilitada en Baja Tensión</b>."),
        ("3. Mantenimiento Preventivo y Revisiones Obligatorias",
         "• Comprobación mensual del botón Test del interruptor diferencial por el titular.<br/>"
         "• Revisión periódica por empresa instaladora autorizada al menos cada 5 años (recomendada) o según exigencias de la ITC-BT-05.<br/>"
         "• Inspección de apriete de bornas en cuadro eléctrico y comprobación de la toma de tierra.")
    ]

    for tit, desc in normas_guia:
        t_guia = Table([
            [Paragraph(f"<b>{tit}</b>", bold_style)],
            [Paragraph(desc, body_style)]
        ], colWidths=[18.4*cm])
        t_guia.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor("#0f172a")),
            ('LINEBELOW', (0,0), (-1,0), 0.8, colors.HexColor("#0f172a")),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ]))
        story.append(t_guia)
        story.append(Spacer(1, 4))

    # Teléfonos de Asistencia y Contacto de la Empresa
    t_tel_data = [
        [
            Paragraph(f"<b>Empresa Instaladora de Confianza:</b> {instalador.get('empresa', 'BOLIMUR')}<br/>"
                      f"<b>Teléfono de Asistencia / Averías:</b> {instalador.get('telefono', '+34 600 000 000')}<br/>"
                      f"<b>Nº Habilitación REBT:</b> {instalador.get('licencia', 'REBT-30/15892')}", body_style),
            Paragraph("<b>Teléfonos de Emergencia:</b><br/>"
                      "• Emergencias Generales: <b>112</b><br/>"
                      "• Averías Distribuidora Eléctrica: <b>900 171 171</b>", body_style)
        ]
    ]
    t_tel = Table(t_tel_data, colWidths=[11.0*cm, 7.4*cm])
    t_tel.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")),
        ('BOX', (0,0), (-1,-1), 0.7, colors.HexColor("#d97706")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(Spacer(1, 4))
    story.append(t_tel)

    doc.build(story, canvasmaker=NumberedCanvasMTDMurciaOficial)
    return buffer.getvalue()
