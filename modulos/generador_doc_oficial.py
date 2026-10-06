# -*- coding: utf-8 -*-
"""
Módulo de Generación y Clonación de Documentos Oficiales de Industria (DGEAIM Murcia)
Genera:
1. Documento Microsoft Word (.docx) 100% oficial sobre la plantilla reglamentaria de la CARM.
2. Documento PDF Oficial listo para firma telemática.
"""

import os
import io
import re
import datetime
import base64
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

RUTA_PLANTILLA_DOCX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plantillas", "plantilla_mtd_murcia_oficial.docx")
RUTA_PLANTILLA_PDF = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plantillas", "plantilla_mtd_murcia_oficial.pdf")


def _extraer_numero(cadena: str, default: float = 0.0) -> float:
    if not cadena:
        return default
    m = re.search(r'(\d+(?:\.\d+)?)', str(cadena).replace(',', '.'))
    return float(m.group(1)) if m else default


def _extraer_seccion_fase(seccion_str: str, default: str = "2.5") -> str:
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
            im.verify()
        bio.seek(0)
        return bio
    except Exception:
        return None


def generar_docx_oficial_dgeaim_murcia(datos_mtd: dict) -> bytes:
    """
    Rellena la plantilla oficial de Microsoft Word de la DGEAIM de la Región de Murcia
    con los datos de la memoria técnica de diseño (MTD), conservando los logos originales,
    membretes y estilos de la Consejería.
    """
    if not os.path.exists(RUTA_PLANTILLA_DOCX):
        raise FileNotFoundError(f"No se encontró la plantilla Word oficial en {RUTA_PLANTILLA_DOCX}")

    doc = docx.Document(RUTA_PLANTILLA_DOCX)

    titular = datos_mtd.get("titular", {})
    empl = datos_mtd.get("emplazamiento", {})
    instalador = datos_mtd.get("instalador", {})
    suministro = datos_mtd.get("suministro", {})
    protecciones = datos_mtd.get("protecciones", {})
    ensayos = datos_mtd.get("ensayos", {})
    circuitos = datos_mtd.get("circuitos", [])
    anexos = datos_mtd.get("anexos", {})

    pot_inst_w = float(suministro.get("potencia_instalada_w", 5750.0))
    pot_inst_kw = pot_inst_w / 1000.0
    tension_str = str(suministro.get("tension", "230 V"))
    es_trifasico = "400" in tension_str
    v_nom = 400.0 if es_trifasico else 230.0

    di_cable = str(suministro.get("di_cable", "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (AS)"))
    di_tubo = str(suministro.get("di_tubo", "Tubo M32 libre de halógenos"))
    di_long = float(suministro.get("di_long_m", 15.0))
    di_cdt = float(suministro.get("di_cdt_pct", 0.72))
    di_sec = _extraer_seccion_fase(di_cable, default="10")

    iga_cal = int(protecciones.get("iga_amperaje", 25))
    rt_medida = float(ensayos.get("rt_ohm", 11.8))

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
            nom_tit = titular.get("nombre", "").strip() or "BEATRIZ IRIARTE QUIROZ"
            nif_tit = titular.get("nif", "").strip() or "34330049L"
            dir_tit = empl.get("direccion", "").strip() or "CALLE CRUCETA 11"
            muni_tit = empl.get("municipio", "MURCIA").strip()
            cp_tit = empl.get("cp", "30165").strip()
            tel_tit = titular.get("telefono", "").strip() or "632000000"
            email_tit = titular.get("email", "").strip() or "instalaciones@bolimur.com"

            c_tit.paragraphs[0].text = f"Nombre: {nom_tit.upper()}   N.I.F.: {nif_tit.upper()}"
            if len(c_tit.paragraphs) > 1:
                c_tit.paragraphs[1].text = f"Dirección: {dir_tit.upper()}   Localidad: {muni_tit.upper()}"
            if len(c_tit.paragraphs) > 2:
                c_tit.paragraphs[2].text = f"Municipio: {muni_tit.upper()}   Provincia: REGIÓN DE MURCIA   C.P.: {cp_tit}"
            if len(c_tit.paragraphs) > 3:
                c_tit.paragraphs[3].text = f"Teléfono: {tel_tit}   Correo electrónico: {email_tit}"

        # Fila 5 a 10: Datos del Instalador Habilitado
        emp_nom = instalador.get("empresa", "BOLIMUR INSTALACIONES Y REFORMAS").strip()
        emp_cif = instalador.get("cif", "B-73123456").strip()
        emp_rii = instalador.get("registro_rii", "RII-30/08492").strip()
        inst_nom = instalador.get("nombre", "Richard Orlando Choque Tejerina").strip()
        inst_nif = instalador.get("nif", "34331426Q").strip()
        inst_lic = instalador.get("licencia", "REBT-30/15892").strip()
        inst_tel = instalador.get("telefono", "+34 600 000 000").strip()

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

        # Fila 17 y 18: Clasificación ITC-BT-04
        uso_inm = empl.get("uso", "Vivienda Residencial").strip()
        if len(t0.rows) > 17 and len(t0.rows[17].cells) > 0:
            t0.rows[17].cells[0].text = "[X]  INSTALACIONES PARA VIVIENDAS, OFICINAS Y/O LOCALES COMERCIALES."
        if len(t0.rows) > 18 and len(t0.rows[18].cells) > 0:
            t0.rows[18].cells[0].text = "[ ]  INSTALACIONES INDUSTRIALES, TEMPORALES, AGRARIAS O DE SERVICIOS."

        # Fila 19: Carácter de la Instalación
        tipo_tram = datos_mtd.get("tipo_tramitacion", "Nueva Instalación")
        nueva_mark = "[X]" if "Nueva" in tipo_tram else "[ ]"
        ampl_mark = "[X]" if "Ampliación" in tipo_tram else "[ ]"
        mod_mark = "[X]" if "Modificación" in tipo_tram or "Reforma" in tipo_tram else "[ ]"
        if len(t0.rows) > 19 and len(t0.rows[19].cells) > 0:
            t0.rows[19].cells[0].text = f"{nueva_mark} Nueva   {ampl_mark} Ampliación   {mod_mark} Modificación"

        # Fila 20: Emplazamiento
        if len(t0.rows) > 20 and len(t0.rows[20].cells) > 0:
            t0.rows[20].cells[0].text = f"Emplazamiento: {dir_tit.upper()}   Localidad: {muni_tit.upper()}   C.P.: {cp_tit}   Actividad: {uso_inm.upper()}"

        # Fila 23: Tensión y Potencia
        if len(t0.rows) > 23 and len(t0.rows[23].cells) > 4:
            t0.rows[23].cells[1].text = "[X] 230 V" if not es_trifasico else "[ ] 230 V"
            t0.rows[23].cells[2].text = "[X] 400 V" if es_trifasico else "[ ] 400 V"
            t0.rows[23].cells[4].text = f"{pot_inst_kw:.2f} kW ({pot_inst_w:,.0f} W)"

        # Fila 25: Grupo 3.1 ITC-BT-04
        if len(t0.rows) > 25 and len(t0.rows[25].cells) > 0:
            t0.rows[25].cells[0].text = "Grupo de instalación según 3.1 ITC-BT 04: Grupo F (Viviendas unifamiliares / edificios)"

        # Fila 28 y 29: LGA / Derivación Individual y Puesta a Tierra
        if len(t0.rows) > 28 and len(t0.rows[28].cells) > 7:
            t0.rows[28].cells[0].text = "CGP-01"
            t0.rows[28].cells[1].text = "Esquema 2 (i-DE)"
            t0.rows[28].cells[2].text = f"{iga_cal} A"
            t0.rows[28].cells[3].text = "DI Interior"
            t0.rows[28].cells[4].text = f"{di_sec} mm² Cu"
            t0.rows[28].cells[5].text = f"{di_long:.0f} m"
            t0.rows[28].cells[6].text = "Bajo tubo"
            t0.rows[28].cells[7].text = f"{rt_medida:.1f} Ω"

        if len(t0.rows) > 29 and len(t0.rows[29].cells) > 2:
            t0.rows[29].cells[1].text = f"Línea de Enlace: {di_sec} mm² Cu"
            t0.rows[29].cells[2].text = f"ΔV = {di_cdt:.2f}%"

        if len(t0.rows) > 30 and len(t0.rows[30].cells) > 2:
            t0.rows[30].cells[1].text = f"Línea Principal: {di_sec} mm² Cu | Tubo: {di_tubo}"

        if len(t0.rows) > 31 and len(t0.rows[31].cells) > 3:
            t0.rows[31].cells[1].text = "Nº Contadores: 1"
            t0.rows[31].cells[3].text = "[X] CONTADOR INDIVIDUAL"

    # =========================================================================
    # TABLA 1: PÁGINA 2 - PREVISIÓN DE CARGAS EN VIVIENDAS (ITC-BT-10)
    # =========================================================================
    if len(doc.tables) > 1:
        t1 = doc.tables[1]
        grado_cod = "E" if (pot_inst_w >= 9200.0 or "Elevad" in str(suministro.get("grado_electrif", ""))) else "B"

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
            r_di.cells[8].text = f"{pot_inst_w / v_nom:.1f}"
            r_di.cells[10].text = f"{di_sec}"
            r_di.cells[12].text = f"{di_cdt:.2f}"
            r_di.cells[15].text = f"{di_cdt:.2f}"
            r_di.cells[16].text = "RZ1-K (AS)"
            r_di.cells[18].text = "0.6/1 kV"
            r_di.cells[22].text = di_tubo.split()[1] if len(di_tubo.split()) > 1 else "M32"
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
                c_item = circuitos[idx]
                c_nom = str(c_item.get("nombre", f"C{idx+1}"))
                c_pot_w = float(c_item.get("potencia", 2300))
                c_pot_kw = c_pot_w / 1000.0
                c_long_m = float(c_item.get("longitud", 15))
                c_sec_str = _extraer_seccion_fase(str(c_item.get("seccion", "2.5")), default="2.5")
                c_tubo_str = str(c_item.get("tubo", "M20"))
                c_cdt_parc = float(c_item.get("cdt", 1.10))
                c_cdt_tot = di_cdt + c_cdt_parc
                c_ib = c_pot_w / 230.0

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

    # =========================================================================
    # INSERCIÓN DE PLANOS GRÁFICOS EN ANEXOS I, II Y III (SI EXISTEN)
    # =========================================================================
    img_sit = _preparar_imagen_bytes(anexos.get("plano_situacion"))
    if img_sit and len(doc.tables) > 8:
        try:
            t_sit = doc.tables[8]  # Al pie de Table 8 o en Table 9
            # Se inserta en Table 9 si existe
            if len(doc.tables) > 9 and len(doc.tables[9].rows) > 1:
                p_sit = doc.tables[9].rows[1].cells[0].paragraphs[0]
                p_sit.add_run().add_picture(img_sit, width=Inches(6.2))
        except Exception:
            pass

    img_emp = _preparar_imagen_bytes(anexos.get("plano_emplazamiento"))
    if img_emp and len(doc.tables) > 10 and len(doc.tables[10].rows) > 1:
        try:
            p_emp = doc.tables[10].rows[1].cells[0].paragraphs[0]
            p_emp.add_run().add_picture(img_emp, width=Inches(6.2))
        except Exception:
            pass

    img_dist = _preparar_imagen_bytes(anexos.get("plano_distribucion"))
    if img_dist and len(doc.tables) > 11 and len(doc.tables[11].rows) > 1:
        try:
            p_dist = doc.tables[11].rows[1].cells[0].paragraphs[0]
            p_dist.add_run().add_picture(img_dist, width=Inches(6.2))
        except Exception:
            pass

    bio_out = io.BytesIO()
    doc.save(bio_out)
    return bio_out.getvalue()
