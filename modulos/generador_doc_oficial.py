# -*- coding: utf-8 -*-
"""
Módulo de Generación y Clonación de Documentos Oficiales de Industria (DGEAIM Murcia)
Genera:
1. Documento Microsoft Word (.docx) 100% oficial sobre la plantilla reglamentaria de la CARM.
2. Documento PDF Oficial clonado pixel a pixel listo para firma telemática en CARM / AutoFirma.
"""

import os
import io
import re
import datetime
import base64
import subprocess
import tempfile
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

RUTA_PLANTILLA_DOCX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plantillas", "plantilla_mtd_murcia_oficial.docx")
RUTA_PLANTILLA_PDF = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plantillas", "plantilla_mtd_murcia_oficial.pdf")


def _safe_str(val, default="") -> str:
    """Retorna un string sin espacios garantizando que None nunca lance AttributeError."""
    if val is None:
        return str(default).strip()
    s = str(val).strip()
    return s if s else str(default).strip()


def _extraer_numero(cadena, default: float = 0.0) -> float:
    if cadena is None:
        return default
    m = re.search(r'(\d+(?:\.\d+)?)', str(cadena).replace(',', '.'))
    return float(m.group(1)) if m else default


def _extraer_seccion_fase(seccion_str, default: str = "2.5") -> str:
    if not seccion_str:
        return default
    s = str(seccion_str).strip()
    s = s.replace("2x", "").replace("3G", "").replace("4x", "").replace("1x", "")
    if "+" in s:
        s = s.split("+")[0].strip()
    m = re.search(r'(\d+(?:\.\d+)?)', s)
    return m.group(1) if m else default


def _preparar_imagen_bytes(img_data) -> io.BytesIO | None:
    if not img_data:
        return None
    try:
        raw = None
        if isinstance(img_data, str):
            if img_data.startswith("data:"):
                _, part = img_data.split(",", 1)
                raw = base64.b64decode(part)
            elif os.path.exists(img_data):
                with open(img_data, "rb") as f:
                    raw = f.read()
            else:
                try:
                    raw = base64.b64decode(img_data)
                except Exception:
                    return None
        elif isinstance(img_data, bytes):
            raw = img_data
        elif hasattr(img_data, "getvalue"):
            raw = img_data.getvalue()
        elif hasattr(img_data, "read"):
            raw = img_data.read()

        if not raw:
            return None

        # Si es un PDF, renderizar primera página a imagen
        if raw.startswith(b"%PDF"):
            try:
                import fitz
                pdoc = fitz.open(stream=raw, filetype="pdf")
                if len(pdoc) > 0:
                    pix = pdoc[0].get_pixmap(dpi=150)
                    raw = pix.tobytes("png")
                pdoc.close()
            except Exception:
                return None

        from PIL import Image as PILImage
        bio = io.BytesIO(raw)
        with PILImage.open(bio) as im:
            # Optimizar tamaño si es gigante
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            if im.width > 1600 or im.height > 1600:
                im.thumbnail((1600, 1600), PILImage.Resampling.LANCZOS)
            bio_out = io.BytesIO()
            im.save(bio_out, format="JPEG", quality=85, optimize=True)
            bio_out.seek(0)
            return bio_out
    except Exception:
        return None


def _insertar_imagen_en_parrafo(parrafo, img_data, max_w_in=5.8, max_h_in=5.0) -> bool:
    """
    Inserta una imagen en un párrafo de Word escalada proporcionalmente para que
    NUNCA desborde la página y no cree páginas en blanco redundantes.
    """
    bio = _preparar_imagen_bytes(img_data)
    if not bio:
        return False
    try:
        from PIL import Image as PILImage
        bio.seek(0)
        with PILImage.open(bio) as pil_im:
            w_px, h_px = pil_im.size
            if w_px <= 0 or h_px <= 0:
                return False
            aspect = h_px / w_px

        target_w = float(max_w_in)
        target_h = target_w * aspect
        if target_h > float(max_h_in):
            target_h = float(max_h_in)
            target_w = target_h / aspect

        bio.seek(0)
        parrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = parrafo.add_run()
        run.add_picture(bio, width=Inches(target_w), height=Inches(target_h))
        return True
    except Exception:
        return False


def generar_docx_oficial_dgeaim_murcia(datos_mtd: dict) -> bytes:
    """
    Rellena la plantilla oficial de Microsoft Word de la DGEAIM de la Región de Murcia
    con los datos de la memoria técnica de diseño (MTD), conservando los logos originales,
    membretes y estilos de la Consejería.
    Garantiza alineación milimétrica en casillas de verificación y sin superposiciones.
    """
    if not os.path.exists(RUTA_PLANTILLA_DOCX):
        raise FileNotFoundError(f"No se encontró la plantilla Word oficial en {RUTA_PLANTILLA_DOCX}")

    doc = docx.Document(RUTA_PLANTILLA_DOCX)

    datos = datos_mtd or {}
    titular = datos.get("titular") or {}
    empl = datos.get("emplazamiento") or {}
    instalador = datos.get("instalador") or {}
    suministro = datos.get("suministro") or {}
    protecciones = datos.get("protecciones") or {}
    ensayos = datos.get("ensayos") or {}
    circuitos = datos.get("circuitos") or []
    anexos = datos.get("anexos") or {}

    pot_inst_w = float(suministro.get("potencia_instalada_w") or 5750.0)
    pot_inst_kw = pot_inst_w / 1000.0
    tension_str = str(suministro.get("tension") or "230 V")
    es_trifasico = "400" in tension_str
    v_nom = 400.0 if es_trifasico else 230.0

    di_cable = str(suministro.get("di_cable") or "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (AS)")
    di_tubo = str(suministro.get("di_tubo") or "Tubo M32 libre de halógenos")
    di_long = float(suministro.get("di_long_m") or 15.0)
    di_cdt = float(suministro.get("di_cdt_pct") or 0.72)
    di_sec = _extraer_seccion_fase(di_cable, default="10")

    iga_cal = int(protecciones.get("iga_amperaje") or 25)
    rt_medida = float(ensayos.get("rt_ohm") or 11.8)

    hoy = datetime.date.today()
    dia = hoy.day
    mes = MESES_ES[hoy.month - 1]
    anio = hoy.year

    # =========================================================================
    # TABLA 0: PÁGINA 1 - TITULAR, INSTALADOR, CARACTERÍSTICAS Y LGA/TIERRAS
    # =========================================================================
    if len(doc.tables) > 0:
        t0 = doc.tables[0]

        # Fila 2: Datos del Titular
        if len(t0.rows) > 2 and len(t0.rows[2].cells) > 0:
            c_tit = t0.rows[2].cells[0]
            nom_tit = _safe_str(titular.get("nombre"), "BEATRIZ IRIARTE QUIROZ")
            nif_tit = _safe_str(titular.get("nif"), "34330049L")
            dir_tit = _safe_str(empl.get("direccion"), "CALLE CRUCETA 11")
            muni_tit = _safe_str(empl.get("municipio"), "MURCIA")
            cp_tit = _safe_str(empl.get("cp"), "30165")
            tel_tit = _safe_str(titular.get("telefono"), "632000000")
            email_tit = _safe_str(titular.get("email"), "instalaciones@bolimur.com")

            if len(c_tit.paragraphs) > 0:
                c_tit.paragraphs[0].text = f"Nombre: {nom_tit.upper()}   N.I.F.: {nif_tit.upper()}"
            if len(c_tit.paragraphs) > 1:
                c_tit.paragraphs[1].text = f"Dirección: {dir_tit.upper()}   Localidad: {muni_tit.upper()}"
            if len(c_tit.paragraphs) > 2:
                c_tit.paragraphs[2].text = f"Municipio: {muni_tit.upper()}   Provincia: REGIÓN DE MURCIA   C.P.: {cp_tit}"
            if len(c_tit.paragraphs) > 3:
                c_tit.paragraphs[3].text = f"Teléfono: {tel_tit}   Correo electrónico: {email_tit}"

        # Fila 5 a 10: Datos del Instalador Habilitado
        emp_nom = _safe_str(instalador.get("empresa"), "BOLIMUR INSTALACIONES Y REFORMAS")
        emp_cif = _safe_str(instalador.get("cif"), "B-73123456")
        emp_rii = _safe_str(instalador.get("registro_rii"), "RII-30/08492")
        inst_nom = _safe_str(instalador.get("nombre"), "Richard Orlando Choque Tejerina")
        inst_nif = _safe_str(instalador.get("nif"), "34331426Q")
        inst_lic = _safe_str(instalador.get("licencia"), "REBT-30/15892")
        inst_tel = _safe_str(instalador.get("telefono"), "+34 600 000 000")

        if len(t0.rows) > 5 and len(t0.rows[5].cells) > 0:
            t0.rows[5].cells[0].text = f"Razón Social (Empresa instaladora): {emp_nom.upper()}"
            if len(t0.rows[5].cells) > 1:
                t0.rows[5].cells[1].text = f"N.I.F.: {emp_cif.upper()}"

        if len(t0.rows) > 6 and len(t0.rows[6].cells) > 0:
            t0.rows[6].cells[0].text = f"Categoría: ESPECIALISTA (IBTE)   Tipo: -   Número de Inscripción: {emp_rii}   en la Comunidad Autónoma de: REGIÓN DE MURCIA"

        if len(t0.rows) > 7 and len(t0.rows[7].cells) > 0:
            t0.rows[7].cells[0].text = "Domicilio Social: Calle Cruceta 11, Rincón de Seca"

        if len(t0.rows) > 8 and len(t0.rows[8].cells) > 0:
            t0.rows[8].cells[0].text = f"Localidad: Murcia   Municipio: Rincón de Seca   C.P.: 30165   Teléfono: {inst_tel}"

        if len(t0.rows) > 9 and len(t0.rows[9].cells) > 0:
            t0.rows[9].cells[0].text = f"Nombre (Instalador habilitado): {inst_nom.upper()}"
            if len(t0.rows[9].cells) > 1:
                t0.rows[9].cells[1].text = f"N.I.F.: {inst_nif.upper()}"

        if len(t0.rows) > 10 and len(t0.rows[10].cells) > 0:
            t0.rows[10].cells[0].text = f"Categoría: ESPECIALISTA   Número Carnet: {inst_lic}   en la Comunidad Autónoma de: REGIÓN DE MURCIA"

        # Fila 17 y 18: Clasificación ITC-BT-04 (Con tipografía alineada)
        uso_inm = _safe_str(empl.get("uso"), "Vivienda Residencial")
        es_vivienda_ofic = not ("Industrial" in uso_inm or "Agraria" in uso_inm or "Temporal" in uso_inm)
        if len(t0.rows) > 17 and len(t0.rows[17].cells) > 0:
            p17 = t0.rows[17].cells[0].paragraphs[0]
            p17.text = " [X]  INSTALACIONES PARA VIVIENDAS, OFICINAS Y/O LOCALES COMERCIALES." if es_vivienda_ofic else " [ ]  INSTALACIONES PARA VIVIENDAS, OFICINAS Y/O LOCALES COMERCIALES."
            if p17.runs:
                p17.runs[0].font.name = "Arial"
                p17.runs[0].font.size = Pt(8.5)

        if len(t0.rows) > 18 and len(t0.rows[18].cells) > 0:
            p18 = t0.rows[18].cells[0].paragraphs[0]
            p18.text = " [X]  INSTALACIONES INDUSTRIALES, TEMPORALES, AGRARIAS O DE SERVICIOS." if not es_vivienda_ofic else " [ ]  INSTALACIONES INDUSTRIALES, TEMPORALES, AGRARIAS O DE SERVICIOS."
            if p18.runs:
                p18.runs[0].font.name = "Arial"
                p18.runs[0].font.size = Pt(8.5)

        # Fila 19: Carácter de la Instalación (Separado limpiamente por celdas para evitar solapamientos)
        tipo_tram = _safe_str(datos.get("tipo_tramitacion"), "Nueva Instalación")
        nueva_chk = "[X]" if "Nueva" in tipo_tram else "[ ]"
        ampl_chk = "[X]" if "Ampliación" in tipo_tram else "[ ]"
        mod_chk = "[X]" if ("Modificación" in tipo_tram or "Reforma" in tipo_tram) else "[ ]"

        if len(t0.rows) > 19:
            # Celda 0: Casilla Nueva
            if len(t0.rows[19].cells) > 0:
                p19_0 = t0.rows[19].cells[0].paragraphs[0]
                p19_0.text = f" {nueva_chk} Nueva"
                if p19_0.runs:
                    p19_0.runs[0].font.name = "Arial"
                    p19_0.runs[0].font.size = Pt(9.0)

            # Celda 4: Casillas Ampliación y Modificación con expediente anterior
            if len(t0.rows[19].cells) > 4:
                p19_4 = t0.rows[19].cells[4].paragraphs[0]
                p19_4.text = f"   {ampl_chk} Ampliación    {mod_chk} Modificación - Nº Registro/Expediente BT anterior: ............................."
                if p19_4.runs:
                    p19_4.runs[0].font.name = "Arial"
                    p19_4.runs[0].font.size = Pt(8.5)

        # Fila 20: Emplazamiento
        if len(t0.rows) > 20 and len(t0.rows[20].cells) > 0:
            p20 = t0.rows[20].cells[0].paragraphs[0]
            p20.text = f"Emplazamiento: {dir_tit.upper()}   Localidad: {muni_tit.upper()}   C.P.: {cp_tit}   Actividad: {uso_inm.upper()}"
            if p20.runs:
                p20.runs[0].font.name = "Arial"
                p20.runs[0].font.size = Pt(8.5)

        # Fila 23: Tensión y Potencia (Usando índices de columnas exactos sin sobreescrituras)
        if len(t0.rows) > 23:
            if len(t0.rows[23].cells) > 3:
                p23_v1 = t0.rows[23].cells[3].paragraphs[0]
                p23_v1.text = " [X] 230 V" if not es_trifasico else " [ ] 230 V"
                if p23_v1.runs:
                    p23_v1.runs[0].font.name = "Arial"
                    p23_v1.runs[0].font.size = Pt(9.0)

            if len(t0.rows[23].cells) > 5:
                p23_v2 = t0.rows[23].cells[5].paragraphs[0]
                p23_v2.text = " [X] 400 V" if es_trifasico else " [ ] 400 V"
                if p23_v2.runs:
                    p23_v2.runs[0].font.name = "Arial"
                    p23_v2.runs[0].font.size = Pt(9.0)

            if len(t0.rows[23].cells) > 15:
                p23_kw = t0.rows[23].cells[15].paragraphs[0]
                p23_kw.text = f" {pot_inst_kw:.2f} kW"
                if p23_kw.runs:
                    p23_kw.runs[0].font.name = "Arial"
                    p23_kw.runs[0].font.size = Pt(9.0)

        # Fila 25: Grupo 3.1 ITC-BT-04
        if len(t0.rows) > 25 and len(t0.rows[25].cells) > 0:
            p25 = t0.rows[25].cells[0].paragraphs[0]
            p25.text = "Grupo de instalación según 3.1 ITC-BT 04: f (Viviendas unifamiliares / edificios)"
            if p25.runs:
                p25.runs[0].font.name = "Arial"
                p25.runs[0].font.size = Pt(8.5)

        # Fila 29 y 30: LGA / Derivación Individual y Puesta a Tierra en sus filas correspondientes
        if len(t0.rows) > 29 and len(t0.rows[29].cells) > 23:
            r29 = t0.rows[29]
            r29.cells[0].paragraphs[0].text = "CGP-01"
            r29.cells[2].paragraphs[0].text = "Esquema 2"
            r29.cells[5].paragraphs[0].text = f"{iga_cal} A"
            r29.cells[7].paragraphs[0].text = "DI Interior"
            r29.cells[9].paragraphs[0].text = f"{di_sec}"
            r29.cells[13].paragraphs[0].text = f"{di_long:.0f}"
            r29.cells[16].paragraphs[0].text = "RZ1-K (AS)"
            r29.cells[23].paragraphs[0].text = f"{rt_medida:.1f} Ω"
            for c_i in [0, 2, 5, 7, 9, 13, 16, 23]:
                p = r29.cells[c_i].paragraphs[0]
                if p.runs:
                    p.runs[0].font.name = "Arial"
                    p.runs[0].font.size = Pt(8.0)

        if len(t0.rows) > 30 and len(t0.rows[30].cells) > 23:
            r30 = t0.rows[30]
            r30.cells[9].paragraphs[0].text = f"ΔV={di_cdt:.2f}%"
            r30.cells[23].paragraphs[0].text = "Cu"
            for c_i in [9, 23]:
                p = r30.cells[c_i].paragraphs[0]
                if p.runs:
                    p.runs[0].font.name = "Arial"
                    p.runs[0].font.size = Pt(8.0)

        if len(t0.rows) > 31 and len(t0.rows[31].cells) > 17:
            r31 = t0.rows[31]
            r31.cells[10].paragraphs[0].text = "1"
            r31.cells[17].paragraphs[0].text = "[X]"
            for c_i in [10, 17]:
                p = r31.cells[c_i].paragraphs[0]
                if p.runs:
                    p.runs[0].font.name = "Arial"
                    p.runs[0].font.size = Pt(8.5)

    # =========================================================================
    # TABLA 1: PÁGINA 2 - PREVISIÓN DE CARGAS EN VIVIENDAS (ITC-BT-10)
    # =========================================================================
    if len(doc.tables) > 1:
        t1 = doc.tables[1]
        grado_str = _safe_str(suministro.get("grado_electrif"))
        grado_cod = "E" if (pot_inst_w >= 9200.0 or "Elevad" in grado_str) else "B"

        if len(t1.rows) > 6 and len(t1.rows[6].cells) > 4:
            t1.rows[6].cells[1].text = "1 A"
            t1.rows[6].cells[2].text = grado_cod
            t1.rows[6].cells[3].text = "120 m²"
            t1.rows[6].cells[4].text = f"{pot_inst_kw:.2f} kW"

        if len(t1.rows) > 12 and len(t1.rows[12].cells) > 3:
            t1.rows[12].cells[3].text = f"{pot_inst_kw:.2f} kW"

        if len(t1.rows) > 17 and len(t1.rows[17].cells) > 1:
            t1.rows[17].cells[1].text = f"{pot_inst_kw:.2f} kW (Simultaneidad: 1.0)"

        if len(t1.rows) > 20 and len(t1.rows[20].cells) > 3:
            t1.rows[20].cells[3].text = f"{pot_inst_kw:.2f} kW"

    # =========================================================================
    # TABLA 2: PÁGINA 3 - SERVICIOS GENERALES, EDIFICIO Y DESCRIPCIÓN TÉCNICA
    # =========================================================================
    if len(doc.tables) > 2:
        t2 = doc.tables[2]

        if len(t2.rows) > 6 and len(t2.rows[6].cells) > 3:
            t2.rows[6].cells[3].text = "0.0 kW"

        if len(t2.rows) > 13 and len(t2.rows[13].cells) > 3:
            t2.rows[13].cells[3].text = "0.0 kW"

        if len(t2.rows) > 15 and len(t2.rows[15].cells) > 1:
            t2.rows[15].cells[1].text = f"{pot_inst_kw:.2f} kW"

        # Fila 33: Breve descripción de la instalación
        grado_nom = "ELECTRIFICACION ELEVADA" if grado_cod == "E" else "ELECTRIFICACION BASICA"
        desc_oficial = (
            f"INSTALACION ELECTRICA EN BAJA TENSION PARA VIVIENDA {grado_nom} {pot_inst_w:,.0f} W. "
            f"CUADRO GENERAL DE MANDO Y PROTECCION (CGMP) CON IGA OMNIPOLAR DE {iga_cal}A (ICN=6KA), "
            f"PROTECTOR DE SOBRETENSIONES PERMANENTES Y TRANSITORIAS TIPO 2 CON BOBINA DE DISPARO (ITC-BT-23), "
            f"INTERRUPTOR DIFERENCIAL DE ALTA SENSIBILIDAD 30mA (CLASE A) Y DERIVACION INDIVIDUAL {di_cable} "
            f"BAJO {di_tubo} CON CAIDA DE TENSION ΔV = {di_cdt:.2f}% (CONFORME REBT ITC-BT-15)."
        )
        if len(t2.rows) > 33 and len(t2.rows[33].cells) > 0:
            t2.rows[33].cells[0].text = desc_oficial

    # =========================================================================
    # TABLA 8: PÁGINA 5 - PRESUPUESTO NORMALIZADO Y DECLARACIÓN RESPONSABLE
    # =========================================================================
    if len(doc.tables) > 8:
        t8 = doc.tables[8]

        # Enlace
        if len(t8.rows) > 5 and len(t8.rows[5].cells) > 6:
            t8.rows[5].cells[6].text = "650,00"

        # Receptoras
        if len(t8.rows) > 10 and len(t8.rows[10].cells) > 6:
            t8.rows[10].cells[6].text = "1.850,00"

        # Tierras
        if len(t8.rows) > 12 and len(t8.rows[12].cells) > 6:
            t8.rows[12].cells[6].text = "350,00"

        # Presupuesto Total sin IVA
        if len(t8.rows) > 14 and len(t8.rows[14].cells) > 6:
            t8.rows[14].cells[6].text = "2.850,00"

        # Lugar y Fecha
        if len(t8.rows) > 23 and len(t8.rows[23].cells) > 0:
            t8.rows[23].cells[0].text = f"En Murcia, a {dia} de {mes} de {anio}"

        # Firma del Redactor
        if len(t8.rows) > 24 and len(t8.rows[24].cells) > 0:
            t8.rows[24].cells[0].text = "[X] Instalador Habilitado en Baja Tensión   [ ] Técnico Titulado Competente"

        if len(t8.rows) > 25 and len(t8.rows[25].cells) > 0:
            t8.rows[25].cells[0].text = f"Fdo.: {inst_nom} (NIF: {inst_nif}) | Empresa: {emp_nom} (RII: {emp_rii})"

    # =========================================================================
    # TABLA 12: PÁGINA 10 - ANEXO IV: DIMENSIONAMIENTO POR TRAMOS (REBT)
    # =========================================================================
    if len(doc.tables) > 12:
        t12 = doc.tables[12]

        # Fila 12: Derivación Individual (A-B)
        if len(t12.rows) > 12:
            r_di = t12.rows[12]
            r_di.cells[0].text = "Derivación individual (A-B)"
            r_di.cells[2].text = "100"
            r_di.cells[4].text = f"{pot_inst_kw:.2f}"
            r_di.cells[6].text = f"{di_long:.0f}"
            ib_di = pot_inst_w / (1.73205 * 400.0) if es_trifasico else pot_inst_w / 230.0
            r_di.cells[8].text = f"{ib_di:.1f}"
            r_di.cells[10].text = f"{di_sec}"
            r_di.cells[12].text = f"{di_cdt:.2f}"
            r_di.cells[15].text = f"{di_cdt:.2f}"
            r_di.cells[16].text = "RZ1-K (AS)"
            r_di.cells[18].text = "0.6/1 kV"
            m_tubo = re.search(r'(M\d+)', di_tubo)
            r_di.cells[22].text = m_tubo.group(1) if m_tubo else "M32"
            r_di.cells[26].text = f"{di_sec}"
            r_di.cells[28].text = f"{di_sec}"

        # Filas 13 a 24: Circuitos derivados terminales (C-D, E-F, G-H...)
        tramos_letras = [
            "C-D", "E-F", "G-H", "I-J", "K-L", "M-N",
            "O-P", "Q-R", "S-T", "U-V", "W-X", "Y-Z"
        ]
        for idx, tramo_tag in enumerate(tramos_letras):
            row_idx = 13 + idx
            if row_idx >= len(t12.rows):
                break
            r_circ = t12.rows[row_idx]

            if idx < len(circuitos):
                c_item = circuitos[idx] or {}
                c_nom = _safe_str(c_item.get("nombre"), f"C{idx+1}")
                c_pot_w = float(c_item.get("potencia") or 2300)
                c_pot_kw = c_pot_w / 1000.0
                c_long_m = float(c_item.get("longitud") or 15)
                c_sec_str = _extraer_seccion_fase(str(c_item.get("seccion") or "2.5"), default="2.5")
                c_tubo_str = _safe_str(c_item.get("tubo"), "M20")
                c_cdt_parc = float(c_item.get("cdt") or 1.10)
                c_cdt_tot = di_cdt + c_cdt_parc
                c_trif = ("4x" in str(c_item.get("seccion", "")) or "3P" in str(c_nom) or "trifásic" in c_nom.lower())
                c_ib = c_pot_w / (1.73205 * 400.0) if c_trif else c_pot_w / 230.0

                r_circ.cells[0].text = f"{c_nom} ({tramo_tag})"
                r_circ.cells[2].text = "100"
                r_circ.cells[4].text = f"{c_pot_kw:.2f}"
                r_circ.cells[6].text = f"{c_long_m:.0f}"
                r_circ.cells[8].text = f"{c_ib:.1f}"
                r_circ.cells[10].text = f"{c_sec_str}"
                r_circ.cells[12].text = f"{c_cdt_parc:.2f}"
                r_circ.cells[15].text = f"{c_cdt_tot:.2f}"
                r_circ.cells[16].text = "H07Z1-K"
                r_circ.cells[18].text = "450/750V"
                r_circ.cells[22].text = c_tubo_str
                r_circ.cells[26].text = f"{c_sec_str}"
                r_circ.cells[28].text = f"{c_sec_str}"
            else:
                r_circ.cells[0].text = f"Reserva ({tramo_tag})"
                for col_k in [2, 4, 6, 8, 10, 12, 15, 16, 18, 22, 26, 28]:
                    r_circ.cells[col_k].text = "-"

    # =============================================================
    # INSERCIÓN EXACTA DE PLANOS GRÁFICOS EN SUS RESPECTIVOS ANEXOS OFICIALES
    # =============================================================
    # Anexo I (a): Plano de Situación en Tabla 8, Fila 27
    if anexos.get("plano_situacion") and len(doc.tables) > 8 and len(doc.tables[8].rows) > 27:
        try:
            c8 = doc.tables[8].rows[27].cells[0]
            p_target = c8.paragraphs[4] if len(c8.paragraphs) > 4 else c8.add_paragraph()
            _insertar_imagen_en_parrafo(p_target, anexos.get("plano_situacion"), max_w_in=5.8, max_h_in=5.0)
        except Exception:
            pass

    # Anexo I (b): Plano de Emplazamiento en Tabla 9, Fila 1
    if anexos.get("plano_emplazamiento") and len(doc.tables) > 9 and len(doc.tables[9].rows) > 1:
        try:
            c9 = doc.tables[9].rows[1].cells[0]
            p_target = c9.paragraphs[4] if len(c9.paragraphs) > 4 else c9.add_paragraph()
            _insertar_imagen_en_parrafo(p_target, anexos.get("plano_emplazamiento"), max_w_in=5.8, max_h_in=5.0)
        except Exception:
            pass

    # Anexo II: Plano de Distribución en Planta en Tabla 10, Fila 1
    if anexos.get("plano_distribucion") and len(doc.tables) > 10 and len(doc.tables[10].rows) > 1:
        try:
            c10 = doc.tables[10].rows[1].cells[0]
            for p_extra in c10.paragraphs[5:]:
                try:
                    p_extra._p.getparent().remove(p_extra._p)
                except Exception:
                    pass
            p_target = c10.paragraphs[4] if len(c10.paragraphs) > 4 else c10.add_paragraph()
            _insertar_imagen_en_parrafo(p_target, anexos.get("plano_distribucion"), max_w_in=5.8, max_h_in=5.0)
        except Exception:
            pass

    # Anexo III: Esquema Unifilar en Tabla 11
    if len(doc.tables) > 11 and len(doc.tables[11].rows) > 1:
        try:
            c11 = doc.tables[11].rows[1].cells[0]
            p_target = c11.paragraphs[0] if len(c11.paragraphs) > 0 else c11.add_paragraph()
            if anexos.get("unifilar_modo") == "custom" and anexos.get("plano_unifilar_custom"):
                _insertar_imagen_en_parrafo(p_target, anexos.get("plano_unifilar_custom"), max_w_in=5.8, max_h_in=5.0)
            else:
                from modulos.pdf_memoria_tecnica import generar_png_unifilar
                png_unif = generar_png_unifilar(datos_mtd)
                if png_unif:
                    _insertar_imagen_en_parrafo(p_target, png_unif, max_w_in=5.8, max_h_in=5.0)
        except Exception:
            pass

    # =============================================================
    # ANEXO V: REPORTAJE FOTOGRÁFICO DE FIN DE OBRA (ITC-BT-05)
    # =============================================================
    fotos_obra = anexos.get("fotos", []) or datos.get("fotos", [])
    if fotos_obra:
        try:
            doc.add_page_break()
            p_v_tit = doc.add_paragraph()
            r_v = p_v_tit.add_run("ANEXO V: REPORTAJE FOTOGRÁFICO DE FIN DE OBRA Y EVIDENCIAS TÉCNICAS (ITC-BT-05)")
            r_v.bold = True
            r_v.font.size = Pt(12)
            r_v.font.color.rgb = RGBColor(15, 23, 42)
            p_v_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER

            p_v_sub = doc.add_paragraph()
            r_vs = p_v_sub.add_run(f"Expediente: {datos.get('expediente', 'EXP-MTD')} | Titular: {titular.get('nombre', '')} | Ubicación: {empl.get('direccion', '')} ({empl.get('municipio', 'Murcia')})")
            r_vs.font.size = Pt(8.5)
            r_vs.font.color.rgb = RGBColor(100, 116, 139)
            p_v_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

            for f_idx, f_item in enumerate(fotos_obra):
                f_data = f_item.get("data") if isinstance(f_item, dict) else f_item
                f_tit = f_item.get("titulo", f"Fotografía de obra {f_idx + 1}") if isinstance(f_item, dict) else f"Fotografía {f_idx + 1}"

                p_f_img = doc.add_paragraph()
                p_f_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                _insertar_imagen_en_parrafo(p_f_img, f_data, max_w_in=5.5, max_h_in=4.2)

                p_f_cap = doc.add_paragraph()
                p_f_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = p_f_cap.add_run(f"📷 Foto {f_idx + 1}: {f_tit}")
                r_cap.bold = True
                r_cap.font.size = Pt(9)
                r_cap.font.color.rgb = RGBColor(30, 41, 59)

                if f_idx < len(fotos_obra) - 1 and (f_idx + 1) % 2 == 0:
                    doc.add_page_break()
                else:
                    doc.add_paragraph()
        except Exception:
            pass


    bio_out = io.BytesIO()
    doc.save(bio_out)
    return bio_out.getvalue()


def convertir_docx_a_pdf(docx_bytes: bytes) -> bytes | None:
    """
    Convierte un documento Word (.docx) a PDF utilizando Microsoft Word COM en Windows.
    Produce una copia 100% idéntica, con los membretes, sellos, fuentes y tablas oficiales de la CARM.
    Si no está en Windows o Word COM no está disponible, devuelve None de forma segura.
    """
    if os.name != "nt" or not docx_bytes:
        return None

    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix="bolimur_carm_")
        tmp_docx = os.path.join(tmp_dir, "mtd_oficial.docx")
        tmp_pdf = os.path.join(tmp_dir, "mtd_oficial.pdf")

        with open(tmp_docx, "wb") as f_in:
            f_in.write(docx_bytes)

        ps_script = f"""
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {{
    $doc = $word.Documents.Open('{tmp_docx}')
    $doc.SaveAs([ref]'{tmp_pdf}', [ref]17)
    $doc.Close([ref]0)
}} finally {{
    $word.Quit([ref]0)
}}
"""
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=25
        )

        if res.returncode == 0 and os.path.exists(tmp_pdf) and os.path.getsize(tmp_pdf) > 1000:
            with open(tmp_pdf, "rb") as f_out:
                return f_out.read()
    except Exception:
        pass
    finally:
        if tmp_dir and os.path.exists(tmp_dir):
            try:
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

    return None
