# -*- coding: utf-8 -*-
"""
Módulo Oficial de Memoria Técnica de Diseño (MTD) para la Dirección General de Energía
y Actividad Industrial y Minera de la Región de Murcia (DGEAIM - Código Provincial 30)
Permite el llenado profesional, el auto-rellenado inteligente a partir de cálculos REBT
y el guardado/recuperación persistente vinculado a las fichas de clientes en el CRM.
"""

import streamlit as st
import datetime
import math
import json
import io
import base64
from modulos import rebt_tablas as rebt
from modulos import pdf_memoria_tecnica
from modulos import db_manager, auth_manager
from modulos import auditor_ia_rebt

MUNICIPIOS_MURCIA_OFICIALES = [
    "Murcia (Capital / Pedanías)", "Cartagena", "Lorca", "Molina de Segura", 
    "Alcantarilla", "Torre Pacheco", "Águilas", "Cieza", "Yecla", 
    "San Javier", "Mazarrón", "Totana", "Caravaca de la Cruz", "Jumilla",
    "San Pedro del Pinatar", "Las Torres de Cotillas", "Alhama de Murcia",
    "Archena", "Fuente Álamo", "Santomera", "Puerto Lumbreras", "Abarán",
    "Cehegín", "Bullas", "Beniel", "Calasparra", "Fortuna", "Alguazas",
    "Moratalla", "Lorquí", "Abanilla", "Blanca", "Librilla", "Pliego",
    "Villanueva del Río Segura", "Campos del Río", "Ricote", "Ulea", "Ojós"
]

def procesar_archivo_anexo(uploaded_file) -> str:
    """
    Convierte el archivo subido (imagen o PDF de 1 página exportado de AutoCAD/Cade_Simu)
    en un string data-URI base64 optimizado para almacenamiento y ReportLab.
    """
    if uploaded_file is None:
        return ""
    try:
        raw_bytes = uploaded_file.getvalue()
        # Si es un PDF, renderizar primera página a PNG con PyMuPDF
        if raw_bytes.startswith(b"%PDF"):
            try:
                import fitz
                pdf_doc = fitz.open(stream=raw_bytes, filetype="pdf")
                if len(pdf_doc) > 0:
                    page = pdf_doc[0]
                    pix = page.get_pixmap(dpi=150)
                    raw_bytes = pix.tobytes("png")
                pdf_doc.close()
            except Exception as e_pdf:
                st.error(f"Error procesando archivo PDF: {e_pdf}")
                return ""

        from PIL import Image as PILImage
        bio_in = io.BytesIO(raw_bytes)
        with PILImage.open(bio_in) as im:
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            # Redimensionar si es muy grande manteniendo proporciones
            im.thumbnail((1600, 1600), PILImage.Resampling.LANCZOS)
            bio_out = io.BytesIO()
            im.save(bio_out, format="JPEG", quality=85, optimize=True)
            b64_str = base64.b64encode(bio_out.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        st.error(f"Error procesando imagen del plano: {e}")
        return ""

def cargar_plantilla_por_tipo(tipo: str):
    """
    Rellena automáticamente los parámetros técnicos y circuitos según el tipo de instalación reglamentaria.
    Si tipo es en blanco o no seleccionado, inicializa los campos técnicos limpios y sin circuitos.
    """
    if not tipo or "Blanco" in tipo or "Seleccionar" in tipo or tipo.startswith("⚪"):
        st.session_state["mtd_in_pot_inst"] = 0.0
        st.session_state["mtd_in_pot_max"] = 0.0
        st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = ""
        st.session_state["mtd_in_di_cable"] = ""
        st.session_state["mtd_in_di_tubo"] = ""
        st.session_state["mtd_in_di_long"] = 0.0
        st.session_state["mtd_in_di_cdt"] = 0.0
        st.session_state["mtd_in_grado"] = "Básica"
        st.session_state["mtd_in_iga"] = 25
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 6.0
        st.session_state["mtd_in_dif"] = ""
        st.session_state["mtd_in_vtp"] = ""
        st.session_state["mtd_in_tierra"] = ""
        st.session_state["mtd_in_spl"] = "No aplica"
        st.session_state["mtd_in_emp_uso"] = ""
        st.session_state["mtd_circuitos"] = []

    elif "Fotovoltaic" in tipo or "Autoconsumo" in tipo or "Solar" in tipo:
        st.session_state["mtd_in_pot_inst"] = 5000.0
        st.session_state["mtd_in_pot_max"] = 5000.0
        st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Generador Fotovoltaico Interconectado a Red Interior (ITC-BT-40)"
        st.session_state["mtd_in_di_cable"] = "3G6 mm² Cu RZ1-K (AS) 0.6/1kV"
        st.session_state["mtd_in_di_tubo"] = "Tubo M32 libre de halógenos"
        st.session_state["mtd_in_di_long"] = 12.0
        st.session_state["mtd_in_di_cdt"] = 0.58
        st.session_state["mtd_in_grado"] = "Autoconsumo Fotovoltaico (ITC-BT-40)"
        st.session_state["mtd_in_iga"] = 25
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 6.0
        st.session_state["mtd_in_dif"] = "Diferencial 2P 40A / 30mA Clase A con detección DC 6mA (UNE-EN 62955)"
        st.session_state["mtd_in_vtp"] = "Permanentes (POP) + Transitorias Tipo 2 con bobina y protección anti-isla integrada"
        st.session_state["mtd_in_tierra"] = "Conductor PE 1x6 mm² Cu uniendo marcos y estructuras a tierra | Rt ≤ 15 Ω"
        st.session_state["mtd_in_spl"] = "Smart Meter / Vatímetro de inyección cero / balance neto"
        st.session_state["mtd_in_emp_uso"] = "Instalación Generadora en Autoconsumo (RD 244/2019)"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "Línea Evacuación AC Inversor", "potencia": 5000, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 12, "cdt": 0.58, "norma": "ITC-BT-40"},
            {"nombre": "Circuito Generación DC String 1", "potencia": 2750, "pia": 15, "seccion": "2x6.0 H1Z2Z2-K", "tubo": "M25 UV", "longitud": 18, "cdt": 0.65, "norma": "ITC-BT-40"},
            {"nombre": "Circuito Generación DC String 2", "potencia": 2750, "pia": 15, "seccion": "2x6.0 H1Z2Z2-K", "tubo": "M25 UV", "longitud": 20, "cdt": 0.72, "norma": "ITC-BT-40"}
        ]

    elif "IRVE" in tipo or "Recarga" in tipo or "Vehículo" in tipo:
        st.session_state["mtd_in_pot_inst"] = 7360.0
        st.session_state["mtd_in_pot_max"] = 7360.0
        st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Centralización de Contadores (Esquema 2)"
        st.session_state["mtd_in_di_cable"] = "3G6 mm² Cu RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"
        st.session_state["mtd_in_di_tubo"] = "Tubo M32 libre de halógenos (IK08)"
        st.session_state["mtd_in_di_long"] = 25.0
        st.session_state["mtd_in_di_cdt"] = 0.86
        st.session_state["mtd_in_grado"] = "Específica IRVE (ITC-BT-52)"
        st.session_state["mtd_in_iga"] = 32
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 6.0
        st.session_state["mtd_in_dif"] = "Diferencial 2P 40A / 30mA Clase A con detección DC 6mA (IEC 62955)"
        st.session_state["mtd_in_vtp"] = "Permanentes (POP/VTP) + Transitorias Tipo 2 (DPS/VSP) con bobina de disparo"
        st.session_state["mtd_in_tierra"] = "Conductor PE 1x6 mm² Cu | Resistencia bucle tierra Rt ≤ 15 Ω"
        st.session_state["mtd_in_spl"] = "Sensor toroidal CT para modulación dinámica en tiempo real"
        st.session_state["mtd_in_emp_uso"] = "Garaje Comunitario / Punto de Recarga VE"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "Línea Específica IRVE (Wallbox)", "potencia": 7360, "pia": 32, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 25, "cdt": 0.86, "norma": "ITC-BT-52"}
        ]

    elif ("Vivienda" in tipo or "Residencial" in tipo) and any(kw in tipo for kw in ["Elevada", "Clima", "Calefacción", "Domótica"]):
        st.session_state["mtd_in_pot_inst"] = 9200.0
        st.session_state["mtd_in_pot_max"] = 9200.0
        st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Derivación Individual desde Centralización (ITC-BT-15)"
        st.session_state["mtd_in_di_cable"] = "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"
        st.session_state["mtd_in_di_tubo"] = "Tubo M40 libre de halógenos (ITC-BT-15)"
        st.session_state["mtd_in_di_long"] = 18.0
        st.session_state["mtd_in_di_cdt"] = 0.85
        st.session_state["mtd_in_grado"] = "Elevada"
        st.session_state["mtd_in_iga"] = 40
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 6.0
        st.session_state["mtd_in_dif"] = "2 x Diferencial 2P 40A / 30mA (D1: Tipo AC, D2: Tipo A Superinmunizado para Clima e Inverter)"
        st.session_state["mtd_in_vtp"] = "Permanentes (VTP) + Transitorias Tipo 2 con reconexión"
        st.session_state["mtd_in_tierra"] = "Conductor PE 1x16 mm² Cu | Picas en anillo Rt ≤ 15 Ω"
        st.session_state["mtd_in_spl"] = "No aplica"
        st.session_state["mtd_in_emp_uso"] = "Vivienda Residencial Electrificación Elevada"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora / Lavavajillas / Termo", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Auxiliares", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"},
            {"nombre": "C8.1 - Calefacción Línea 1", "potencia": 4500, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 16, "cdt": 1.18, "norma": "ITC-BT-25"},
            {"nombre": "C8.2 - Calefacción Línea 2", "potencia": 4500, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 18, "cdt": 1.25, "norma": "ITC-BT-25"},
            {"nombre": "C9 - Climatización Inverter (Tipo A SI)", "potencia": 5750, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C10 - Secadora Independiente", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.85, "norma": "ITC-BT-25"},
            {"nombre": "C11 - Domótica / Automatización y Control", "potencia": 1500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 20, "cdt": 0.75, "norma": "ITC-BT-25"}
        ]

    elif "Vivienda" in tipo or "Residencial" in tipo:
        st.session_state["mtd_in_pot_inst"] = 5750.0
        st.session_state["mtd_in_pot_max"] = 5750.0
        st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Derivación Individual desde Centralización (ITC-BT-15)"
        st.session_state["mtd_in_di_cable"] = "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"
        st.session_state["mtd_in_di_tubo"] = "Tubo M32 libre de halógenos (ITC-BT-15)"
        st.session_state["mtd_in_di_long"] = 15.0
        st.session_state["mtd_in_di_cdt"] = 0.72
        st.session_state["mtd_in_grado"] = "Básica"
        st.session_state["mtd_in_iga"] = 25
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 6.0
        st.session_state["mtd_in_dif"] = "Interruptor Diferencial 2P 40A / 30mA Clase A / Superinmunizado"
        st.session_state["mtd_in_vtp"] = "Permanentes (VTP) + Transitorias Tipo 2 con reconexión"
        st.session_state["mtd_in_tierra"] = "Conductor PE 1x10 mm² Cu | Picas en anillo Rt ≤ 15 Ω"
        st.session_state["mtd_in_spl"] = "No aplica"
        st.session_state["mtd_in_emp_uso"] = "Vivienda Residencial Unifamiliar"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora / Termo", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Auxiliares", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"}
        ]

    elif "Local" in tipo or "Comercial" in tipo or "Nave" in tipo:
        st.session_state["mtd_in_pot_inst"] = 11500.0
        st.session_state["mtd_in_pot_max"] = 14490.0
        st.session_state["mtd_in_tension"] = "Trifásico (400 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Línea General de Alimentación (LGA / CPM)"
        st.session_state["mtd_in_di_cable"] = "4x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV"
        st.session_state["mtd_in_di_tubo"] = "Tubo M40 libre de halógenos"
        st.session_state["mtd_in_di_long"] = 20.0
        st.session_state["mtd_in_di_cdt"] = 0.65
        st.session_state["mtd_in_grado"] = "Comercial / Servicios"
        st.session_state["mtd_in_iga"] = 40
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 10.0
        st.session_state["mtd_in_dif"] = "Diferencial Tetrapolar 4P 40A / 30mA Clase A / Superinmunizado"
        st.session_state["mtd_in_vtp"] = "Permanentes + Transitorias Tipo 2 con bobina de emisión"
        st.session_state["mtd_in_tierra"] = "Conductor PE 1x16 mm² Cu | Anillo cimentación Rt ≤ 10 Ω"
        st.session_state["mtd_in_spl"] = "No aplica"
        st.session_state["mtd_in_emp_uso"] = "Local Comercial / Actividad Terciaria"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "C1 - Alumbrado Comercial", "potencia": 3000, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 22, "cdt": 1.10, "norma": "ITC-BT-28"},
            {"nombre": "C2 - Alumbrado Emergencia", "potencia": 500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 30, "cdt": 0.45, "norma": "ITC-BT-28"},
            {"nombre": "C3 - Tomas Fuerza General", "potencia": 4000, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M25", "longitud": 18, "cdt": 1.12, "norma": "ITC-BT-28"},
            {"nombre": "C4 - Climatización / Bomba Calor", "potencia": 6000, "pia": 25, "seccion": "4x6.0+TT6.0", "tubo": "M32", "longitud": 15, "cdt": 0.85, "norma": "ITC-BT-28"}
        ]

    elif "Obra" in tipo or "Provisional" in tipo or "ITC-BT-33" in tipo:
        st.session_state["mtd_in_pot_inst"] = 15000.0
        st.session_state["mtd_in_pot_max"] = 15000.0
        st.session_state["mtd_in_tension"] = "Trifásico (400 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Acometida Provisional desde Red Distribuidora (CPM / CGP Intemperie)"
        st.session_state["mtd_in_di_cable"] = "4x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"
        st.session_state["mtd_in_di_tubo"] = "Tubo M40 intemperie resistente a impactos IK09"
        st.session_state["mtd_in_di_long"] = 15.0
        st.session_state["mtd_in_di_cdt"] = 0.52
        st.session_state["mtd_in_grado"] = "Provisional de Obra (ITC-BT-33)"
        st.session_state["mtd_in_iga"] = 40
        st.session_state["mtd_in_curva"] = "Curva D"
        st.session_state["mtd_in_icn"] = 10.0
        st.session_state["mtd_in_dif"] = "Diferencial 4P 40A / 30mA Clase A Superinmunizado + Seta Parada Emergencia"
        st.session_state["mtd_in_vtp"] = "Permanentes + Transitorias Tipo 2 con corte omnipolar y bobina de disparo"
        st.session_state["mtd_in_tierra"] = "Pica de puesta a tierra independiente de obra (Rt ≤ 15 Ω) | Conductor PE 1x16 mm² Cu"
        st.session_state["mtd_in_spl"] = "No aplica"
        st.session_state["mtd_in_emp_uso"] = "Instalación Provisional y Temporal de Obras (ITC-BT-33)"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "C1 - Toma CETAC Trifásica 32A 3P+N+T (Grúa / Maquinaria)", "potencia": 10000, "pia": 32, "seccion": "4x6.0+TT6.0", "tubo": "M32", "longitud": 15, "cdt": 0.65, "norma": "ITC-BT-33"},
            {"nombre": "C2 - Toma CETAC Trifásica 16A 3P+N+T (Hormigonera / Elevador)", "potencia": 5000, "pia": 16, "seccion": "4x2.5+TT2.5", "tubo": "M25", "longitud": 15, "cdt": 0.85, "norma": "ITC-BT-33"},
            {"nombre": "C3 - Tomas CETAC/Schuko Monofásicas 16A (Herramientas manuales)", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.78, "norma": "ITC-BT-33"},
            {"nombre": "C4 - Alumbrado de Seguridad y Balizamiento de Obra", "potencia": 1500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 20, "cdt": 0.60, "norma": "ITC-BT-33"}
        ]

    elif "Derivación" in tipo or " DI " in tipo or "ITC-BT-15" in tipo:
        st.session_state["mtd_in_pot_inst"] = 9200.0
        st.session_state["mtd_in_pot_max"] = 14490.0
        st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Contador / Centralización de Contadores (ITC-BT-16)"
        st.session_state["mtd_in_di_cable"] = "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV"
        st.session_state["mtd_in_di_tubo"] = "Tubo M40 libre de halógenos (ITC-BT-15)"
        st.session_state["mtd_in_di_long"] = 20.0
        st.session_state["mtd_in_di_cdt"] = 0.85
        st.session_state["mtd_in_grado"] = "Elevada"
        st.session_state["mtd_in_iga"] = 40
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 6.0
        st.session_state["mtd_in_dif"] = "Diferencial 2P 40A / 30mA Clase A Superinmunizado"
        st.session_state["mtd_in_vtp"] = "Permanentes + Transitorias Tipo 2 con bobina de emisión"
        st.session_state["mtd_in_tierra"] = "Conductor PE 1x16 mm² Cu | Rt ≤ 15 Ω"
        st.session_state["mtd_in_spl"] = "No aplica"
        st.session_state["mtd_in_emp_uso"] = "Derivación Individual B.T. (ITC-BT-15)"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "Línea Derivación Individual", "potencia": 9200, "pia": 40, "seccion": "2x16+TT16", "tubo": "M40", "longitud": 20, "cdt": 0.85, "norma": "ITC-BT-15"}
        ]

    elif "Alimentación" in tipo or "LGA" in tipo or "ITC-BT-14" in tipo:
        st.session_state["mtd_in_pot_inst"] = 43600.0
        st.session_state["mtd_in_pot_max"] = 50000.0
        st.session_state["mtd_in_tension"] = "Trifásico (400 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Caja General de Protección (CGP / ITC-BT-13)"
        st.session_state["mtd_in_di_cable"] = "3x50/25 mm² Al/Cu RZ1-K 0.6/1kV"
        st.session_state["mtd_in_di_tubo"] = "Conducto / Tubo M110 libre de halógenos"
        st.session_state["mtd_in_di_long"] = 15.0
        st.session_state["mtd_in_di_cdt"] = 0.42
        st.session_state["mtd_in_grado"] = "Comercial / Edificio"
        st.session_state["mtd_in_iga"] = 63
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 15.0
        st.session_state["mtd_in_dif"] = "Protección General con Toroidal / Relé electrónico"
        st.session_state["mtd_in_vtp"] = "Protección contra sobretensiones Tipo 1+2"
        st.session_state["mtd_in_tierra"] = "Línea principal PE 1x35 mm² Cu | Rt ≤ 10 Ω"
        st.session_state["mtd_in_spl"] = "No aplica"
        st.session_state["mtd_in_emp_uso"] = "Línea General de Alimentación (ITC-BT-14)"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "Línea General LGA Centralización", "potencia": 43600, "pia": 63, "seccion": "3x50+25+TT25", "tubo": "M110", "longitud": 15, "cdt": 0.42, "norma": "ITC-BT-14"}
        ]

def aplicar_datos_cliente_a_formulario(cli_obj: dict):
    """Vuelca los datos del cliente de CRM en los campos del formulario"""
    if not cli_obj:
        return
    st.session_state["mtd_in_tit_nom"] = cli_obj.get("nombre_completo", "")
    st.session_state["mtd_in_tit_nif"] = cli_obj.get("nif_cif", "")
    st.session_state["mtd_in_tit_tel"] = cli_obj.get("telefono", "")
    st.session_state["mtd_in_tit_email"] = cli_obj.get("email", "")
    st.session_state["mtd_in_emp_dir"] = cli_obj.get("direccion_suministro", cli_obj.get("direccion", ""))
    st.session_state["mtd_in_emp_cups"] = cli_obj.get("cups", "")
    
    loc = cli_obj.get("localidad", "Murcia")
    for m in MUNICIPIOS_MURCIA_OFICIALES:
        if m.lower() in loc.lower() or loc.lower() in m.lower():
            st.session_state["mtd_in_emp_muni"] = m
            break
    
    tipo_inm = cli_obj.get("tipo_inmueble", "")
    if tipo_inm:
        st.session_state["mtd_in_emp_uso"] = tipo_inm

def renderizar():
    st.markdown("""
    <style>
    div[data-baseweb="select"] { width: 100% !important; }
    div[data-baseweb="select"] * { white-space: normal !important; word-break: break-word !important; }

    /* Barra de Pestañas (st.tabs) Mejorada y de Alto Contraste */
    div[data-baseweb="tab-list"] {
        gap: 6px !important;
        background-color: #f8fafc !important;
        padding: 8px 10px 4px 10px !important;
        border-radius: 10px 10px 0 0 !important;
        border-bottom: 3px solid #0284c7 !important;
        display: flex !important;
        flex-wrap: wrap !important;
    }

    button[data-baseweb="tab"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 9px 15px !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        color: #334155 !important;
        transition: all 0.15s ease-in-out !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    }

    button[data-baseweb="tab"]:hover {
        background-color: #e0f2fe !important;
        color: #0369a1 !important;
        border-color: #38bdf8 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border-color: #0284c7 !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.3) !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span,
    button[data-baseweb="tab"][aria-selected="true"] div {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col_tit_mtd, col_b1_m = st.columns([4, 1])
    with col_tit_mtd:
        st.title("🏛️ Memoria Técnica de Diseño (MTD) Oficial - DGEAIM Región de Murcia")
        st.caption("Formulario oficial normalizado para tramitación telemática de instalaciones en Baja Tensión ante la Dirección General de Energía (Código Provincial 30 - Murcia).")
    with col_b1_m:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Nueva MTD en Blanco", key="btn_reset_mtd_mod", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("mtd_") or k.startswith("quick_up_") or k.startswith("up_mtd_"):
                    st.session_state.pop(k, None)
            st.session_state["mtd_tipo_inst_sel"] = "⚪ -- Seleccionar Tipo de Instalación (En Blanco) --"
            cargar_plantilla_por_tipo("⚪")
            st.rerun()

    # Usuario autenticado
    user_auth = auth_manager.obtener_usuario_actual() or {
        "id": 1,
        "nombre_instalador": "Richard Orlando Choque Tejerina",
        "nombre_empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
        "num_licencia_rebt": "REBT-30/15892",
        "localidad": "Murcia, España",
        "telefono": "+34 600 000 000"
    }

    # =========================================================================
    # 1. EXPEDIENTE, CLIENTE (CRM) Y GUARDADO / CARGA DE MEMORIAS
    # =========================================================================
    st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">👤 1. Expediente, Cliente (CRM) y Gestión de Memorias Guardadas</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        col_t1, col_t1_b, col_t2 = st.columns([1.3, 1.3, 2.4])
        
        with col_t1:
            opciones_tipo_inst = [
                "⚪ -- Seleccionar Tipo de Instalación (En Blanco) --",
                "🏡 Vivienda Unifamiliar / Piso Residencial (ITC-BT-25)",
                "🏡 Vivienda Electrificación Elevada con Clima, Calefacción y Domótica (ITC-BT-25 - 9.200W)",
                "☀️ Autoconsumo Solar Fotovoltaico (ITC-BT-40 / RD 244/2019)",
                "🚗 Recarga Vehículo Eléctrico IRVE (ITC-BT-52)",
                "🏢 Local Comercial / Nave Industrial (ITC-BT-28)",
                "🏗️ Instalación Provisional y Temporal de Obras (ITC-BT-33 / Cuadro de Obra)",
                "⚡ Línea General de Alimentación LGA (ITC-BT-14)",
                "🔌 Derivación Individual DI (ITC-BT-15)"
            ]
            tipo_actual = st.session_state.get("mtd_tipo_inst_sel", opciones_tipo_inst[0])
            idx_tipo_def = opciones_tipo_inst.index(tipo_actual) if tipo_actual in opciones_tipo_inst else 0

            tipo_inst_sel = st.selectbox(
                "Tipo de Instalación (REBT):",
                opciones_tipo_inst,
                index=idx_tipo_def,
                key="mtd_tipo_inst_sel"
            )
            
            lbl_btn_plantilla = "🧹 Limpiar / Poner en Blanco" if (tipo_inst_sel.startswith("⚪") or "Blanco" in tipo_inst_sel) else "⚡ Cargar Plantilla Seleccionada"
            if st.button(lbl_btn_plantilla, type="secondary", use_container_width=True):
                cargar_plantilla_por_tipo(tipo_inst_sel)
                if tipo_inst_sel.startswith("⚪") or "Blanco" in tipo_inst_sel:
                    st.success("✅ MTD reiniciada en blanco.")
                else:
                    st.success(f"✅ ¡Plantilla técnica auto-rellenada para {tipo_inst_sel.split('(')[0].strip()}!")
                st.rerun()

        with col_t1_b:
            tipo_tram_sel = st.selectbox(
                "Carácter de la Instalación / Trámite:",
                [
                    "🆕 Nueva Instalación (Alta Inicial)",
                    "🏗️ Instalación Temporal de Obra (Suministro Provisional)",
                    "📈 Ampliación de Potencia / Cargas",
                    "🔧 Modificación de Importancia / Reforma",
                    "🔄 Adecuación Reglamentaria (REBT)",
                    "📋 Boletín de Reconocimiento / Cambio Titular"
                ],
                index=0,
                key="mtd_tipo_tram_sel"
            )

        with col_t2:
            clientes = db_manager.listar_clientes(user_auth["id"])
            if not clientes:
                st.warning("⚠️ No hay clientes registrados en CRM. Puedes crear fichas en el módulo 'Gestión de Clientes'.")
                cli_sel_id = None
                cli_obj = {}
            else:
                nombres_cli = {c["id"]: f"👤 {c['nombre_completo']} - {c.get('nif_cif', '')} ({c.get('localidad', 'Murcia')})" for c in clientes}
                
                # Pre-seleccionar si ya viene en session
                idx_sel = 0
                if "cliente_activo_proyecto" in st.session_state and st.session_state["cliente_activo_proyecto"]:
                    c_act = st.session_state["cliente_activo_proyecto"]
                    if c_act.get("id") in nombres_cli:
                        idx_sel = list(nombres_cli.keys()).index(c_act["id"])

                cli_sel_id = st.selectbox(
                    "Cliente Asignado (CRM):",
                    options=list(nombres_cli.keys()),
                    format_func=lambda x: nombres_cli[x],
                    index=idx_sel,
                    key="mtd_sel_cliente_crm"
                )
                cli_obj = db_manager.obtener_cliente_por_id(cli_sel_id, user_auth["id"]) or {}

                # Acciones sobre el cliente seleccionado
                col_c_act1, col_c_act2 = st.columns(2)
                with col_c_act1:
                    if st.button("📋 Cargar Datos del Cliente al Formulario", use_container_width=True):
                        aplicar_datos_cliente_a_formulario(cli_obj)
                        st.success(f"✅ Datos de {cli_obj.get('nombre_completo')} volcados a la MTD.")
                        st.rerun()

                with col_c_act2:
                    # Comprobar si este cliente tiene MTDs guardadas
                    proyectos_mtd_cli = [
                        p for p in db_manager.listar_proyectos_por_cliente(cli_sel_id, user_auth["id"]) 
                        if "Memoria" in p.get("modulo", "") or "MTD" in p.get("modulo", "")
                    ]
                    if proyectos_mtd_cli:
                        nombres_projs = {p["id"]: f"📂 {p['nombre_proyecto']} ({p.get('fecha_guardado', '')[:10]})" for p in proyectos_mtd_cli}
                        sel_p_id = st.selectbox("MTDs Guardadas del Cliente:", options=list(nombres_projs.keys()), format_func=lambda x: nombres_projs[x], key="sel_mtd_p_cli")
                        if st.button("🚀 Cargar MTD Guardada", use_container_width=True):
                            p_datos = db_manager.cargar_proyecto_por_id(sel_p_id, user_auth["id"])
                            if p_datos and "datos" in p_datos:
                                for k, v in p_datos["datos"].items():
                                    st.session_state[k] = v
                                st.success(f"✅ ¡Memoria '{p_datos.get('nombre_proyecto')}' cargada con éxito!")
                                st.rerun()

    # Inicialización por defecto si no existen
    if "mtd_circuitos" not in st.session_state:
        cargar_plantilla_por_tipo(tipo_inst_sel)
        if cli_obj:
            aplicar_datos_cliente_a_formulario(cli_obj)

    # =========================================================================
    # FORMULARIO TÉCNICO OFICIAL DGEAIM REGIÓN DE MURCIA (CÓDIGO 30)
    # =========================================================================
    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🏛️ 2. Formulario Oficial Normalizado de la Memoria Técnica de Diseño (DGEAIM Murcia)</h4></div>', unsafe_allow_html=True)

    # Panel Visual de Planos y Documentación Gráfica
    tiene_sit = bool(st.session_state.get("mtd_plano_situacion"))
    tiene_emp = bool(st.session_state.get("mtd_plano_emplazamiento"))
    tiene_dist = bool(st.session_state.get("mtd_plano_distribucion"))
    unif_modo = st.session_state.get("mtd_unifilar_modo", "auto")
    tiene_unif = bool(st.session_state.get("mtd_plano_unifilar_custom")) if unif_modo == "custom" else True
    n_fotos = len(st.session_state.get("mtd_fotos_obra", []))
    abrir_planos_auto = st.session_state.pop("mtd_abrir_planos", False)

    with st.container(border=True):
        st.markdown("#### 🗺️ Gestor Gráfico de Planos Oficiales y Esquema Unifilar")
        st.caption("Visualiza el estado de los documentos gráficos requeridos por Industria (DGEAIM Murcia). Puedes adjuntarlos aquí en el desplegable o en la pestaña **7. 🗺️ PLANOS Y UNIFILAR**:")

        badge_sit = '<span style="color:#16a34a; font-weight:bold; font-size:12.5px;">✅ Adjuntado</span>' if tiene_sit else '<span style="color:#64748b; font-size:12.5px;">⚪ Sin adjuntar</span>'
        badge_emp = '<span style="color:#16a34a; font-weight:bold; font-size:12.5px;">✅ Adjuntado</span>' if tiene_emp else '<span style="color:#64748b; font-size:12.5px;">⚪ Sin adjuntar</span>'
        if unif_modo == 'auto':
            badge_unif = '<span style="color:#0284c7; font-weight:bold; font-size:12.5px;">⚙️ Vectorial Auto</span>'
        elif tiene_unif:
            badge_unif = '<span style="color:#16a34a; font-weight:bold; font-size:12.5px;">📁 Plano Propio</span>'
        else:
            badge_unif = '<span style="color:#ef4444; font-weight:bold; font-size:12.5px;">⚠️ Falta archivo</span>'

        bg_sit = '#f0fdf4' if tiene_sit else '#f8fafc'
        border_sit = '#16a34a' if tiene_sit else '#cbd5e1'
        bg_emp = '#f0fdf4' if tiene_emp else '#f8fafc'
        border_emp = '#16a34a' if tiene_emp else '#cbd5e1'
        bg_fotos = '#f0fdf4' if n_fotos > 0 else '#f8fafc'
        border_fotos = '#16a34a' if n_fotos > 0 else '#cbd5e1'

        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1:
            st.markdown(
                f"<div style='border:1px solid {border_sit}; background:{bg_sit}; padding:10px 12px; border-radius:8px; text-align:center;'>"
                f"<div style='font-size:11px; font-weight:bold; color:#64748b;'>ANEXO I (a)</div>"
                f"<div style='font-size:14px; font-weight:bold; margin:3px 0;'>🗺️ Situación</div>"
                f"{badge_sit}"
                f"</div>",
                unsafe_allow_html=True
            )
        with cp2:
            st.markdown(
                f"<div style='border:1px solid {border_emp}; background:{bg_emp}; padding:10px 12px; border-radius:8px; text-align:center;'>"
                f"<div style='font-size:11px; font-weight:bold; color:#64748b;'>ANEXO I (b)</div>"
                f"<div style='font-size:14px; font-weight:bold; margin:3px 0;'>📍 Emplazamiento</div>"
                f"{badge_emp}"
                f"</div>",
                unsafe_allow_html=True
            )
        with cp3:
            st.markdown(
                f"<div style='border:1px solid #0284c7; background:#f0f9ff; padding:10px 12px; border-radius:8px; text-align:center;'>"
                f"<div style='font-size:11px; font-weight:bold; color:#64748b;'>ANEXO III</div>"
                f"<div style='font-size:14px; font-weight:bold; margin:3px 0;'>⚡ Unifilar</div>"
                f"{badge_unif}"
                f"</div>",
                unsafe_allow_html=True
            )
        with cp4:
            st.markdown(
                f"<div style='border:1px solid {border_fotos}; background:{bg_fotos}; padding:10px 12px; border-radius:8px; text-align:center;'>"
                f"<div style='font-size:11px; font-weight:bold; color:#64748b;'>ANEXO V</div>"
                f"<div style='font-size:14px; font-weight:bold; margin:3px 0;'>📸 Fotos Obra</div>"
                f"<span style='color:#334155; font-weight:bold; font-size:12.5px;'>{n_fotos} fotos</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        with st.expander("⚡ 📤 SUBIR / GESTIONAR PLANOS RÁPIDAMENTE AQUÍ (Sin buscar pestañas)", expanded=abrir_planos_auto):
            st.info("💡 **Subida Rápida:** Puedes subir o sustituir tus archivos de plano directamente aquí. Se guardan y sincronizan automáticamente con el expediente y la pestaña 7.")
            col_qp1, col_qp2 = st.columns(2)
            with col_qp1:
                with st.container(border=True):
                    st.markdown("##### 🗺️ Plano de Situación (Callejero / Municipio)")
                    st.caption("Mapa general / callejero de situación en el municipio (Google Maps / Cartografía).")
                    up_sit_quick = st.file_uploader("Subir Plano de Situación (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key="quick_up_sit")
                    if up_sit_quick is not None:
                        f_id = f"{up_sit_quick.name}_{up_sit_quick.size}"
                        if st.session_state.get("_last_quick_sit_id") != f_id:
                            b64_sq = procesar_archivo_anexo(up_sit_quick)
                            if b64_sq:
                                st.session_state["mtd_plano_situacion"] = b64_sq
                                st.session_state["_last_quick_sit_id"] = f_id
                    if st.session_state.get("mtd_plano_situacion"):
                        st.image(st.session_state["mtd_plano_situacion"], caption="Plano de Situación Cargado", use_container_width=True)
                        if st.button("🗑️ Quitar Situación", key="btn_del_sit_quick"):
                            st.session_state.pop("mtd_plano_situacion", None)
                            st.session_state.pop("_last_quick_sit_id", None)
                            st.rerun()

            with col_qp2:
                with st.container(border=True):
                    st.markdown("##### 📍 Plano de Emplazamiento (Catastro)")
                    st.caption("Plano parcelario catastral o urbanístico de la finca / parcela.")
                    up_emp_quick = st.file_uploader("Subir Plano de Emplazamiento (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key="quick_up_emp")
                    if up_emp_quick is not None:
                        f_id_e = f"{up_emp_quick.name}_{up_emp_quick.size}"
                        if st.session_state.get("_last_quick_emp_id") != f_id_e:
                            b64_eq = procesar_archivo_anexo(up_emp_quick)
                            if b64_eq:
                                st.session_state["mtd_plano_emplazamiento"] = b64_eq
                                st.session_state["_last_quick_emp_id"] = f_id_e
                    if st.session_state.get("mtd_plano_emplazamiento"):
                        st.image(st.session_state["mtd_plano_emplazamiento"], caption="Plano de Emplazamiento Cargado", use_container_width=True)
                        if st.button("🗑️ Quitar Emplazamiento", key="btn_del_emp_quick"):
                            st.session_state.pop("mtd_plano_emplazamiento", None)
                            st.session_state.pop("_last_quick_emp_id", None)
                            st.rerun()

    lbl_tab7 = "🗺️ 7. PLANOS Y UNIFILAR"
    if tiene_sit or tiene_emp or tiene_dist:
        lbl_tab7 += " (📎 Con Planos)"

    tab_f1, tab_f2, tab_f3, tab_f4, tab_f5, tab_f6, tab_f7 = st.tabs([
        "📍 1. Titular",
        "👷 2. Instalador",
        "⚡ 3. Suministro",
        "🛡️ 4. Cuadro CGMP",
        "📋 5. Circuitos",
        "🧪 6. Ensayos BT-05",
        lbl_tab7
    ])

    # --- TAB 1: TITULAR Y EMPLAZAMIENTO ---
    with tab_f1:
        st.markdown("##### 📍 Bloque I: Datos del Titular y Emplazamiento en la Región de Murcia:")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            tit_nombre = st.text_input("Nombre / Razón Social del Titular:", value=st.session_state.get("mtd_in_tit_nom", cli_obj.get("nombre_completo", "")), key="mtd_in_tit_nom")
            tit_nif = st.text_input("NIF / CIF del Titular:", value=st.session_state.get("mtd_in_tit_nif", cli_obj.get("nif_cif", "")), key="mtd_in_tit_nif")
            tit_tel = st.text_input("Teléfono del Titular:", value=st.session_state.get("mtd_in_tit_tel", cli_obj.get("telefono", "")), key="mtd_in_tit_tel")
            tit_email = st.text_input("Correo Electrónico:", value=st.session_state.get("mtd_in_tit_email", cli_obj.get("email", "")), key="mtd_in_tit_email")
        with col_e2:
            emp_dir = st.text_input("Dirección de la Instalación / Plaza:", value=st.session_state.get("mtd_in_emp_dir", cli_obj.get("direccion_suministro", cli_obj.get("direccion", ""))), key="mtd_in_emp_dir")
            emp_cp = st.text_input("Código Postal:", value=st.session_state.get("mtd_in_emp_cp", cli_obj.get("codigo_postal", "30001")), key="mtd_in_emp_cp")
            
            # Buscar index de municipio
            muni_default = st.session_state.get("mtd_in_emp_muni", "Murcia (Capital / Pedanías)")
            idx_muni = MUNICIPIOS_MURCIA_OFICIALES.index(muni_default) if muni_default in MUNICIPIOS_MURCIA_OFICIALES else 0
            emp_muni = st.selectbox("Municipio de la Región de Murcia:", MUNICIPIOS_MURCIA_OFICIALES, index=idx_muni, key="mtd_in_emp_muni")
            
            emp_cups = st.text_input("Código CUPS / Ref. Catastral:", value=st.session_state.get("mtd_in_emp_cups", cli_obj.get("cups", "")), key="mtd_in_emp_cups")
            emp_uso = st.text_input("Uso del Inmueble / Local:", value=st.session_state.get("mtd_in_emp_uso", cli_obj.get("tipo_inmueble", "")), key="mtd_in_emp_uso")

    # --- TAB 2: EMPRESA E INSTALADOR ---
    with tab_f2:
        st.markdown("##### 👷 Bloque II: Datos de la Empresa Instaladora Habilitada y Técnico (Provincia 30 - Murcia):")
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            inst_empresa = st.text_input("Razón Social Empresa Instaladora:", value=user_auth.get("nombre_empresa", "BOLIMUR INSTALACIONES Y REFORMAS"), key="mtd_in_inst_emp")
            inst_cif = st.text_input("CIF Empresa:", value=user_auth.get("nif_cif", "B-73123456"), key="mtd_in_inst_cif")
            inst_rii = st.text_input("Nº Registro Integrado Industrial (RII Murcia):", value=user_auth.get("registro_industrial", "RII-30/08492"), key="mtd_in_inst_rii")
        with col_i2:
            inst_nom = st.text_input("Nombre del Instalador Habilitado:", value=user_auth.get("nombre_instalador", "Richard Orlando Choque Tejerina"), key="mtd_in_inst_nom")
            inst_lic = st.text_input("Nº Carnet / Certificado Cualificación REBT:", value=user_auth.get("num_licencia_rebt", "REBT-30/15892"), key="mtd_in_inst_lic")
            inst_nif = st.text_input("NIF del Instalador:", value="48500000A", key="mtd_in_inst_nif")

    # --- TAB 3: SUMINISTRO Y POTENCIAS ---
    with tab_f3:
        st.markdown("##### ⚡ Bloque III: Suministro, Potencia de Cálculo y Derivación Individual:")

        with st.expander("📘 Guía Técnica Oficial: ¿De dónde sacar cada dato para Industria (DGEAIM Murcia)?", expanded=False):
            st.markdown(r"""
            **Fuentes oficiales y normativa técnica (DGEAIM Murcia - REBT RD 842/2002):**
            * **Potencia de Diseño / Prevista (W):**
              - *Vivienda Básica (ITC-BT-10):* **5.750 W** (suministro monofásico estándar sin aire ni calefacción acumulada).
              - *Vivienda Elevada (ITC-BT-10):* **9.200 W** (*Valor oficial del modelo DGEAIM Murcia adjunto*). Obligatoria si superficie > 160 m², o si dispone de aire acondicionado (C9), calefacción eléctrica (C8), secadora (C10) o domótica (C11).
              - *IRVE Punto de Recarga (ITC-BT-52):* **7.360 W** (Modo 3 - 32A monofásico) o 11 kW / 22 kW trifásico.
              - *Local Comercial / Oficinas:* Mínimo **100 W/m²** de superficie útil (con un mínimo de 3.450 W a 230 V).
            * **Potencia Máxima Admisible (W):**
              - Es la potencia límite que soporta térmicamente la Derivación Individual (DI) y el IGA según la ITC-BT-19. Para cable de 10 mm² con IGA 25A es **5.750 W** (admite hasta 11.500 W térmicos). Para cable de 16 mm² con IGA 40A es **9.200 W** (admite hasta 14.490 W térmicos). En el CIE se consigna esta potencia máxima.
            * **Tensión Nominal y Fases:**
              - Monofásico 230 V (Fase + Neutro) o Trifásico 400 V (3 Fases + Neutro). Se obtiene de la factura de electricidad de la comercializadora o del contrato técnico con la distribuidora (i-DE Redes Eléctricas Inteligentes en la Región de Murcia).
            * **Origen del Suministro:**
              - *Vivienda unifamiliar / Chalet:* "Caja de Protección y Medida (CPM) en valla de cerramiento / fachada exterior (ITC-BT-13)".
              - *Piso / Edificio residencial:* "Centralización de Contadores en planta baja / sótano (ITC-BT-16)".
              - *Local comercial:* "Módulo de medida individual en fachada o CPM".
            * **Conductor de la Derivación Individual (DI):**
              - Exigido por ITC-BT-15: Cables unipolares no propagadores de la llama, de reducida emisión de humos y libres de halógenos (AS), clase de reacción al fuego Cca-s1b,d1,a1 (ej. `RZ1-K (AS) 0.6/1 kV`).
              - Sección fase y neutro: Mínimo **10 mm² Cu** (viviendas básicas) o **16 mm² Cu** (viviendas elevadas, como en el modelo oficial de Murcia). Conductor de protección (tierra PE): misma sección que la fase.
            * **Tubo Protector:**
              - ITC-BT-15 Tabla 1: Diámetro exterior mínimo **M32** para cables de 10 mm², y **M40** para cables de 16 mm².
            * **Longitud y Caída de Tensión (ΔV%):**
              - Longitud: Metros reales medidos desde el contador hasta el cuadro CGMP.
              - Límite reglamentario: Máximo **1.5%** para contadores totalmente centralizados, o **0.5%** si es contador individual adosado (CPM).
            """)

        # Botones de Carga Rápida Automática de Suministro
        st.caption("⚡ **Plantillas Automáticas de Suministro Oficial (1 Clic):**")
        col_ps1, col_ps2, col_ps3, col_ps4 = st.columns(4)
        with col_ps1:
            if st.button("🏠 Básica (5.750 W)", use_container_width=True, help="Vivienda Básica 230V"):
                st.session_state["mtd_in_pot_inst"] = 5750.0
                st.session_state["mtd_in_pot_max"] = 5750.0
                st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
                st.session_state["mtd_in_origen"] = "Derivación Individual desde Centralización (ITC-BT-15)"
                st.session_state["mtd_in_di_cable"] = "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (AS)"
                st.session_state["mtd_in_di_tubo"] = "Tubo M32 libre de halógenos (ITC-BT-15)"
                st.session_state["mtd_in_di_long"] = 15.0
                st.session_state["mtd_in_di_cdt"] = 0.72
                st.session_state["mtd_in_grado"] = "Básica"
                st.success("✅ Parámetros de Vivienda Básica cargados.")
                st.rerun()
        with col_ps2:
            if st.button("🏡 Elevada (9.200 W Murcia)", use_container_width=True, help="Vivienda Elevada DGEAIM Murcia"):
                st.session_state["mtd_in_pot_inst"] = 9200.0
                st.session_state["mtd_in_pot_max"] = 9200.0
                st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
                st.session_state["mtd_in_origen"] = "Derivación Individual desde Centralización (ITC-BT-15)"
                st.session_state["mtd_in_di_cable"] = "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (AS)"
                st.session_state["mtd_in_di_tubo"] = "Tubo M40 libre de halógenos (ITC-BT-15)"
                st.session_state["mtd_in_di_long"] = 18.0
                st.session_state["mtd_in_di_cdt"] = 0.85
                st.session_state["mtd_in_grado"] = "Elevada"
                st.success("✅ Parámetros de Vivienda Elevada (Modelo DGEAIM Murcia) cargados.")
                st.rerun()
        with col_ps3:
            if st.button("🚗 IRVE 32A (7.360 W)", use_container_width=True, help="Recarga VE ITC-BT-52"):
                st.session_state["mtd_in_pot_inst"] = 7360.0
                st.session_state["mtd_in_pot_max"] = 7360.0
                st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
                st.session_state["mtd_in_origen"] = "Centralización de Contadores (Esquema 2 ITC-BT-52)"
                st.session_state["mtd_in_di_cable"] = "3G6 mm² Cu RZ1-K 0.6/1kV (AS)"
                st.session_state["mtd_in_di_tubo"] = "Tubo M32 libre de halógenos (IK08)"
                st.session_state["mtd_in_di_long"] = 25.0
                st.session_state["mtd_in_di_cdt"] = 0.86
                st.session_state["mtd_in_grado"] = "Específica IRVE (ITC-BT-52)"
                st.success("✅ Parámetros de Recarga IRVE cargados.")
                st.rerun()
        with col_ps4:
            if st.button("🏢 Comercial (14.490 W 400V)", use_container_width=True, help="Trifásico 400V"):
                st.session_state["mtd_in_pot_inst"] = 14490.0
                st.session_state["mtd_in_pot_max"] = 14490.0
                st.session_state["mtd_in_tension"] = "Trifásico (400 V) - 50 Hz"
                st.session_state["mtd_in_origen"] = "Módulo de Medida / CPM en Fachada"
                st.session_state["mtd_in_di_cable"] = "4x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (AS)"
                st.session_state["mtd_in_di_tubo"] = "Tubo M40 libre de halógenos"
                st.session_state["mtd_in_di_long"] = 20.0
                st.session_state["mtd_in_di_cdt"] = 0.62
                st.session_state["mtd_in_grado"] = "Comercial / Servicios"
                st.success("✅ Parámetros de Suministro Trifásico cargados.")
                st.rerun()

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sum_pot_inst = st.number_input("Potencia de Diseño / Prevista (W):", value=float(st.session_state.get("mtd_in_pot_inst", 5750.0)), step=250.0, key="mtd_in_pot_inst")
            sum_pot_max = st.number_input("Potencia Máxima Admisible de la Línea (W):", value=float(st.session_state.get("mtd_in_pot_max", 5750.0)), step=250.0, key="mtd_in_pot_max")
            
            t_opts = ["Monofásico (230 V) - 50 Hz", "Trifásico (400 V) - 50 Hz"]
            t_def = st.session_state.get("mtd_in_tension", t_opts[0])
            idx_t = t_opts.index(t_def) if t_def in t_opts else 0
            sum_tension = st.selectbox("Tensión Nominal y Fases:", t_opts, index=idx_t, key="mtd_in_tension")
            sum_origen = st.text_input("Origen del Suministro:", value=st.session_state.get("mtd_in_origen", "Derivación Individual desde Centralización (ITC-BT-15)"), key="mtd_in_origen")
        with col_s2:
            sum_di_cable = st.text_input("Conductor de Alimentación / DI:", value=st.session_state.get("mtd_in_di_cable", "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (AS)"), key="mtd_in_di_cable")
            sum_di_tubo = st.text_input("Tubo Protector:", value=st.session_state.get("mtd_in_di_tubo", "Tubo M32 libre de halógenos (ITC-BT-15)"), key="mtd_in_di_tubo")
            sum_di_long = st.number_input("Longitud de la Línea (m):", value=float(st.session_state.get("mtd_in_di_long", 15.0)), step=1.0, key="mtd_in_di_long")
            sum_di_cdt = st.number_input("Caída de Tensión Calculada (%):", value=float(st.session_state.get("mtd_in_di_cdt", 0.72)), step=0.05, key="mtd_in_di_cdt")
            
            g_opts = ["Básica", "Elevada", "Específica IRVE (ITC-BT-52)", "Comercial / Servicios", "Provisional de Obra (ITC-BT-33)", "Autoconsumo Fotovoltaico (ITC-BT-40)"]
            g_def = st.session_state.get("mtd_in_grado", g_opts[0])
            idx_g = g_opts.index(g_def) if g_def in g_opts else 0
            sum_grado = st.selectbox("Grado de Electrificación / Uso:", g_opts, index=idx_g, key="mtd_in_grado")

        # Asistente de cálculo en vivo de Caída de Tensión REBT
        col_cdt_btn, col_cdt_res = st.columns([1.5, 2])
        with col_cdt_btn:
            if st.button("🧮 Auto-calcular Caída de Tensión (ΔV%) según REBT", use_container_width=True, key="btn_calc_cdt_di"):
                import re
                sec_match = re.search(r'(\d+(?:\.\d+)?)\s*mm', sum_di_cable)
                s_val = float(sec_match.group(1)) if sec_match else 10.0
                es_trif = "400" in sum_tension
                v_nom = 400.0 if es_trif else 230.0
                gamma = 44.0  # Cu 90°C XLPE según REBT ITC-BT-19
                if es_trif:
                    cdt_calc = (sum_pot_inst * sum_di_long * 100.0) / (gamma * s_val * (v_nom ** 2))
                else:
                    cdt_calc = (2.0 * sum_pot_inst * sum_di_long * 100.0) / (gamma * s_val * (v_nom ** 2))
                st.session_state["mtd_in_di_cdt"] = round(cdt_calc, 2)
                st.rerun()
        with col_cdt_res:
            if sum_di_cdt <= 1.50:
                st.success(f"✅ **ΔV = {sum_di_cdt:.2f}%** cumple con el límite reglamentario de la ITC-BT-15 (≤ 1.50%).")
            else:
                st.warning(f"⚠️ **ΔV = {sum_di_cdt:.2f}%** supera el límite reglamentario (1.50%). Aumenta la sección de la DI.")

    # --- TAB 4: CUADRO CGMP Y PROTECCIONES ---
    with tab_f4:
        st.markdown("##### 🛡️ Bloque IV: Dispositivos Generales de Mando y Protección (CGMP):")

        with st.expander("📘 Guía Técnica Oficial: Protecciones del Cuadro CGMP según REBT (ITC-BT-17, 23, 24)", expanded=False):
            st.markdown(r"""
            **Criterios técnicos exigidos por Industria (DGEAIM Murcia):**
            * **Calibre del Interruptor General (IGA):**
              - Corte omnipolar con corte de neutro.
              - **25 A** para Vivienda Básica (5.750 W).
              - **40 A** para Vivienda Elevada (9.200 W - *Caso oficial del modelo DGEAIM Murcia adjunto*).
              - **32 A** para IRVE (7.360 W).
            * **Curva de Disparo:**
              - **Curva C** (disparo instantáneo 5-10 In) es el estándar general en viviendas y pequeños comercios.
            * **Poder de Corte $I_{cn}$ (kA):**
              - La ITC-BT-17 fija un mínimo de 4.5 kA, pero la norma técnica de distribuidora (i-DE) e Industria exige **6.0 kA** (6.000 A) en CGMP.
            * **Interruptor Diferencial:**
              - Sensibilidad: **30 mA** de alta sensibilidad ($I_{\Delta n} = 0.03\text{ A}$).
              - Calibre: Debe ser mayor o igual al IGA ($\ge 40\text{ A}$).
              - Tipo: **Tipo AC** para circuitos generales resistivos, y **Tipo A (o Superinmunizado)** obligatorio para circuitos con electrónica, climatización inverter (C9), placas de inducción o IRVE (con protección DC 6mA según IEC 62955).
              - En Elevada (ITC-BT-25): Mínimo **2 diferenciales** (máximo 5 circuitos por diferencial).
            * **Protección contra Sobretensiones (ITC-BT-23):**
              - Obligatorio en la Región de Murcia:
              - *Permanentes (VTP/POP):* Bobina de emisión que dispara el IGA ante tensiones > 275V causadas por rotura del neutro.
              - *Transitorias (DPS Tipo 2):* Cartuchos descargadores a tierra con capacidad de derivación $I_n \ge 15\text{ kA}$.
            * **Puesta a Tierra (PE):**
              - Conductor de protección en cobre ($1\times 10\text{ mm}^2$ o $1\times 16\text{ mm}^2$) conectado al borne principal de tierra y picas hincadas. Resistencia medida conforme al REBT $R_t \le 15\,\Omega$.
            * **SPL (Sistema de Protección de Línea):**
              - Modulación de carga para cargadores de vehículo eléctrico (ITC-BT-52) o fotovoltaica; en viviendas estándar consignar "No aplica".
            """)

        st.caption("🛡️ **Plantillas Automáticas de CGMP y Protecciones (1 Clic):**")
        col_pp1, col_pp2, col_pp3 = st.columns(3)
        with col_pp1:
            if st.button("🛡️ Básica (IGA 25A | 1 Dif 40A/30mA)", use_container_width=True):
                st.session_state["mtd_in_iga"] = 25
                st.session_state["mtd_in_curva"] = "Curva C (General)"
                st.session_state["mtd_in_icn"] = 6.0
                st.session_state["mtd_in_dif"] = "Diferencial 2P 40A / 30mA Clase AC (1 unidad para máx. 5 circuitos)"
                st.session_state["mtd_in_vtp"] = "Permanentes (VTP/POP) + Transitorias Tipo 2 (DPS) con bobina de disparo (ITC-BT-23)"
                st.session_state["mtd_in_tierra"] = "Conductor PE 1x10 mm² Cu | Pica tierra 2m | Rt ≤ 15 Ω"
                st.session_state["mtd_in_spl"] = "No aplica"
                st.success("✅ Cuadro CGMP para Vivienda Básica cargado.")
                st.rerun()
        with col_pp2:
            if st.button("🏡 Elevada (IGA 40A | 2 Dif Tipo A/AC Murcia)", use_container_width=True):
                st.session_state["mtd_in_iga"] = 40
                st.session_state["mtd_in_curva"] = "Curva C (General)"
                st.session_state["mtd_in_icn"] = 6.0
                st.session_state["mtd_in_dif"] = "2 x Diferencial 2P 40A / 30mA (D1: Tipo AC uso general, D2: Tipo A Superinmunizado para Clima C9 e inducción)"
                st.session_state["mtd_in_vtp"] = "Permanentes (VTP/POP) + Transitorias Tipo 2 con bobina y reconexión (ITC-BT-23)"
                st.session_state["mtd_in_tierra"] = "Conductor PE 1x16 mm² Cu | Picas en anillo Rt ≤ 15 Ω"
                st.session_state["mtd_in_spl"] = "No aplica"
                st.success("✅ Cuadro CGMP para Vivienda Elevada (Modelo DGEAIM Murcia) cargado.")
                st.rerun()
        with col_pp3:
            if st.button("🚗 IRVE (IGA 32A | Dif Clase A IEC 62955)", use_container_width=True):
                st.session_state["mtd_in_iga"] = 32
                st.session_state["mtd_in_curva"] = "Curva C (General)"
                st.session_state["mtd_in_icn"] = 6.0
                st.session_state["mtd_in_dif"] = "Diferencial 2P 40A / 30mA Clase A con detección de corriente continua 6mA (IEC 62955 / ITC-BT-52)"
                st.session_state["mtd_in_vtp"] = "Permanentes (POP) + Transitorias Tipo 2 con bobina de disparo"
                st.session_state["mtd_in_tierra"] = "Conductor PE 1x6 mm² Cu | Resistencia de bucle Rt ≤ 15 Ω"
                st.session_state["mtd_in_spl"] = "Sensor toroidal CT para modulación de recarga dinámica en tiempo real"
                st.success("✅ Cuadro CGMP para Recarga IRVE cargado.")
                st.rerun()

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            prot_iga = st.number_input("Calibre del Interruptor General (IGA / PIA) (A):", value=int(st.session_state.get("mtd_in_iga", 25)), step=1, key="mtd_in_iga")
            
            c_opts = ["Curva C (General)", "Curva B", "Curva D"]
            c_def = st.session_state.get("mtd_in_curva", c_opts[0])
            idx_c = c_opts.index(c_def) if c_def in c_opts else 0
            prot_curva = st.selectbox("Curva de Disparo IGA:", c_opts, index=idx_c, key="mtd_in_curva")
            
            prot_icn = st.number_input("Poder de Corte Icn (kA):", value=float(st.session_state.get("mtd_in_icn", 6.0)), step=1.0, key="mtd_in_icn")
            prot_dif = st.text_input("Interruptor Diferencial Principal:", value=st.session_state.get("mtd_in_dif", "Diferencial 2P 40A / 30mA Clase A (ITC-BT-24)"), key="mtd_in_dif")
        with col_p2:
            prot_vtp = st.text_input("Protección Sobretensiones:", value=st.session_state.get("mtd_in_vtp", "Permanentes (VTP/POP) + Transitorias Tipo 2 (DPS) con bobina de disparo (ITC-BT-23)"), key="mtd_in_vtp")
            prot_tierra = st.text_input("Puesta a Tierra (PE):", value=st.session_state.get("mtd_in_tierra", "Conductor PE 1x10 mm² Cu | Pica tierra 2m | Rt ≤ 15 Ω"), key="mtd_in_tierra")
            prot_spl = st.text_input("Sistema de Balanceo de Carga (SPL):", value=st.session_state.get("mtd_in_spl", "No aplica"), key="mtd_in_spl")

    # --- TAB 5: CIRCUITOS DERIVADOS ---
    with tab_f5:
        st.markdown("##### 📋 Bloque V: Cuadro de Circuitos Interiores / Terminales Derivados:")

        # Botones de Carga Rápida de Paquetes de Circuitos
        st.caption("⚡ **Acciones Rápidas de Configuración del Cuadro de Circuitos:**")
        col_c_p1, col_c_p2, col_c_p3, col_c_p4 = st.columns(4)
        with col_c_p1:
            if st.button("🏠 Cargar Pack Básico (C1-C5)", use_container_width=True, help="Circuito C1 a C5"):
                st.session_state["mtd_circuitos"] = [
                    {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
                    {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
                    {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
                    {"nombre": "C4 - Lavadora / Lavavajillas / Termo", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
                    {"nombre": "C5 - Baños y Auxiliares Cocina", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"}
                ]
                st.success("✅ Pack reglamentario Básico C1 a C5 cargado.")
                st.rerun()
        with col_c_p2:
            if st.button("🏡 Pack Elevado (C1-C10 Murcia)", use_container_width=True, help="Modelo DGEAIM Murcia"):
                st.session_state["mtd_circuitos"] = [
                    {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
                    {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
                    {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
                    {"nombre": "C4.1 - Lavadora", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
                    {"nombre": "C4.2 - Lavavajillas", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 15, "cdt": 0.95, "norma": "ITC-BT-25"},
                    {"nombre": "C4.3 - Termo Eléctrico", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.85, "norma": "ITC-BT-25"},
                    {"nombre": "C5 - Baños y Auxiliares Cocina", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"},
                    {"nombre": "C8 - Calefacción Eléctrica", "potencia": 4500, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 16, "cdt": 1.18, "norma": "ITC-BT-25"},
                    {"nombre": "C9 - Climatización Inverter", "potencia": 5750, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
                    {"nombre": "C10 - Secadora Independiente", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.85, "norma": "ITC-BT-25"}
                ]
                st.success("✅ Pack reglamentario Elevado C1 a C10 (Modelo DGEAIM Murcia) cargado.")
                st.rerun()
        with col_c_p3:
            if st.button("🚗 Pack con IRVE (C1-C5+C13)", use_container_width=True, help="Vivienda con Recarga VE"):
                st.session_state["mtd_circuitos"] = [
                    {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
                    {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
                    {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
                    {"nombre": "C4 - Lavadora / Lavavajillas", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
                    {"nombre": "C5 - Baños y Auxiliares Cocina", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"},
                    {"nombre": "C13 - Recarga IRVE (Wallbox)", "potencia": 7360, "pia": 32, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 25, "cdt": 0.86, "norma": "ITC-BT-52"}
                ]
                st.success("✅ Pack con IRVE cargado.")
                st.rerun()
        with col_c_p4:
            if st.button("🗑️ Vaciar Todos", use_container_width=True, help="Eliminar todos los circuitos"):
                st.session_state["mtd_circuitos"] = []
                st.success("🗑️ Cuadro de circuitos vaciado.")
                st.rerun()

        circs_actuales = st.session_state.get("mtd_circuitos", [])
        
        # Resumen técnico REBT del cuadro actual
        if circs_actuales:
            tot_pot_circs = sum(float(c.get("potencia", 0)) for c in circs_actuales)
            num_difs_req = max(1, (len(circs_actuales) + 4) // 5)
            
            m_c1, m_c2, m_c3 = st.columns(3)
            with m_c1:
                st.metric("Total Circuitos", f"{len(circs_actuales)} uds.")
            with m_c2:
                st.metric("Potencia Sumada Terminales", f"{tot_pot_circs/1000:.2f} kW")
            with m_c3:
                st.metric("Diferenciales REBT Exigidos", f"{num_difs_req} uds.", help="ITC-BT-25: Máximo 5 circuitos por diferencial de 30mA")

            # Lista detallada interactiva con opción individual de ELIMINAR
            with st.container(border=True):
                st.markdown("###### 🔍 Circuitos Actuales en el Expediente (Gestionar / Eliminar):")
                for idx, c in enumerate(circs_actuales):
                    col_rw1, col_rw2, col_rw3, col_rw4, col_rw5 = st.columns([2.8, 2.0, 2.0, 2.0, 1.2])
                    with col_rw1:
                        st.markdown(f"**{idx + 1}. {c.get('nombre', 'Circuito')}**")
                        st.caption(f"Norma: `{c.get('norma', 'ITC-BT-25')}`")
                    with col_rw2:
                        st.markdown(f"⚡ **{c.get('potencia', 0)} W**")
                        st.caption(f"PIA: **{c.get('pia', 16)} A**")
                    with col_rw3:
                        st.markdown(f"📏 **{c.get('seccion', '-')}**")
                        st.caption(f"Tubo: `{c.get('tubo', '-')}`")
                    with col_rw4:
                        st.markdown(f"📍 **{c.get('longitud', 0)} m**")
                        st.caption(f"ΔV: **{c.get('cdt', 0.0)}%**")
                    with col_rw5:
                        if st.button("🗑️", key=f"btn_del_circ_{idx}", help=f"Eliminar {c.get('nombre')}"):
                            st.session_state["mtd_circuitos"].pop(idx)
                            st.rerun()
                    if idx < len(circs_actuales) - 1:
                        st.markdown("<hr style='margin:4px 0; border:0; border-top:1px dashed #cbd5e1;'/>", unsafe_allow_html=True)
        else:
            st.info("ℹ️ No hay circuitos en la lista. Puedes cargarlos con los botones rápidos superiores o añadir circuitos manualmente a continuación.")

        # Selector de plantillas y formulario para añadir / modificar circuitos
        plantillas_circuito_rapido = {
            "-- Seleccionar Plantilla para Cargar Parámetros --": None,
            "C1 - Alumbrado General (10A - 1.5mm²)": {"nom": "C1 - Alumbrado General", "pot": 2300, "pia": 10, "sec": "2x1.5+TT1.5", "tubo": "M20", "long": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            "C2 - Tomas de Uso General (16A - 2.5mm²)": {"nom": "C2 - Tomas de Uso General", "pot": 3450, "pia": 16, "sec": "2x2.5+TT2.5", "tubo": "M20", "long": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            "C3 - Cocina / Horno (25A - 6.0mm²)": {"nom": "C3 - Cocina / Horno", "pot": 5400, "pia": 25, "sec": "2x6.0+TT6.0", "tubo": "M25", "long": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            "C4.1 - Lavadora (16A/20A - 4.0mm²)": {"nom": "C4.1 - Lavadora", "pot": 3450, "pia": 20, "sec": "2x4.0+TT4.0", "tubo": "M20", "long": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            "C4.2 - Lavavajillas (16A - 2.5mm²)": {"nom": "C4.2 - Lavavajillas", "pot": 2300, "pia": 16, "sec": "2x2.5+TT2.5", "tubo": "M20", "long": 15, "cdt": 0.95, "norma": "ITC-BT-25"},
            "C4.3 - Termo Eléctrico (16A - 2.5mm²)": {"nom": "C4.3 - Termo Eléctrico", "pot": 2300, "pia": 16, "sec": "2x2.5+TT2.5", "tubo": "M20", "long": 12, "cdt": 0.85, "norma": "ITC-BT-25"},
            "C5 - Baños y Auxiliares Cocina (16A - 2.5mm²)": {"nom": "C5 - Baños y Auxiliares Cocina", "pot": 3450, "pia": 16, "sec": "2x2.5+TT2.5", "tubo": "M20", "long": 14, "cdt": 0.98, "norma": "ITC-BT-25"},
            "C8 - Calefacción Eléctrica (25A - 6.0mm²)": {"nom": "C8 - Calefacción Eléctrica", "pot": 4500, "pia": 25, "sec": "2x6.0+TT6.0", "tubo": "M25", "long": 16, "cdt": 1.18, "norma": "ITC-BT-25"},
            "C9 - Climatización Inverter Conductos (25A - 6.0mm²)": {"nom": "C9 - Climatización Inverter (Tipo A SI)", "pot": 5750, "pia": 25, "sec": "2x6.0+TT6.0", "tubo": "M25", "long": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            "C9 - Climatización Split Individual (16A - 2.5mm²)": {"nom": "C9 - Climatización Split", "pot": 2500, "pia": 16, "sec": "2x2.5+TT2.5", "tubo": "M20", "long": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            "C10 - Secadora Independiente (16A - 2.5mm²)": {"nom": "C10 - Secadora Independiente", "pot": 2300, "pia": 16, "sec": "2x2.5+TT2.5", "tubo": "M20", "long": 12, "cdt": 0.85, "norma": "ITC-BT-25"},
            "C11 - Domótica / Automatización y Control (10A - 1.5mm²)": {"nom": "C11 - Domótica / Control", "pot": 1500, "pia": 10, "sec": "2x1.5+TT1.5", "tubo": "M20", "long": 20, "cdt": 0.75, "norma": "ITC-BT-25"},
            "C13 - Recarga Vehículo Eléctrico IRVE (32A - 6.0mm²)": {"nom": "C13 - Recarga IRVE (ITC-BT-52)", "pot": 7360, "pia": 32, "sec": "2x6.0+TT6.0", "tubo": "M32", "long": 25, "cdt": 0.86, "norma": "ITC-BT-52"}
        }

        with st.expander("➕ Añadir Nuevo Circuito a la Lista (o Personalizar Plantilla):", expanded=True):
            def _on_cambio_plantilla_circuito():
                sel = st.session_state.get("mtd_circ_preset_sel")
                if sel and sel in plantillas_circuito_rapido and plantillas_circuito_rapido[sel]:
                    p_val = plantillas_circuito_rapido[sel]
                    st.session_state["mtd_in_nc_nom"] = p_val["nom"]
                    st.session_state["mtd_in_nc_pot"] = int(p_val["pot"])
                    st.session_state["mtd_in_nc_pia"] = int(p_val["pia"])
                    st.session_state["mtd_in_nc_sec"] = str(p_val["sec"])
                    st.session_state["mtd_in_nc_tubo"] = str(p_val["tubo"])
                    st.session_state["mtd_in_nc_long"] = int(p_val["long"])
                    st.session_state["mtd_in_nc_cdt"] = float(p_val["cdt"])
                    st.session_state["mtd_in_nc_norma"] = str(p_val["norma"])

            st.selectbox(
                "🎯 Seleccionar Plantilla de Circuito REBT (Carga automática de campos):",
                list(plantillas_circuito_rapido.keys()),
                index=0,
                key="mtd_circ_preset_sel",
                on_change=_on_cambio_plantilla_circuito
            )

            # Inicialización de campos con C1 Alumbrado por defecto (NUNCA IRVE por defecto)
            if "mtd_in_nc_nom" not in st.session_state:
                st.session_state["mtd_in_nc_nom"] = "C1 - Alumbrado General"
            if "mtd_in_nc_pot" not in st.session_state:
                st.session_state["mtd_in_nc_pot"] = 2300
            if "mtd_in_nc_pia" not in st.session_state:
                st.session_state["mtd_in_nc_pia"] = 10
            if "mtd_in_nc_sec" not in st.session_state:
                st.session_state["mtd_in_nc_sec"] = "2x1.5+TT1.5"
            if "mtd_in_nc_tubo" not in st.session_state:
                st.session_state["mtd_in_nc_tubo"] = "M20"
            if "mtd_in_nc_long" not in st.session_state:
                st.session_state["mtd_in_nc_long"] = 18
            if "mtd_in_nc_cdt" not in st.session_state:
                st.session_state["mtd_in_nc_cdt"] = 1.15
            if "mtd_in_nc_norma" not in st.session_state:
                st.session_state["mtd_in_nc_norma"] = "ITC-BT-25"

            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1:
                nc_nom = st.text_input("Nombre Circuito:", key="mtd_in_nc_nom")
                nc_pot = st.number_input("Potencia (W):", step=250, key="mtd_in_nc_pot")
            with col_c2:
                nc_pia = st.number_input("PIA (A):", step=1, key="mtd_in_nc_pia")
                nc_sec = st.text_input("Conductor:", key="mtd_in_nc_sec")
            with col_c3:
                nc_tubo = st.text_input("Tubo Protector:", key="mtd_in_nc_tubo")
                nc_long = st.number_input("Longitud (m):", step=1, key="mtd_in_nc_long")
            with col_c4:
                nc_cdt = st.number_input("ΔV (%):", step=0.05, key="mtd_in_nc_cdt")
                nc_norma = st.text_input("Norma ITC:", key="mtd_in_nc_norma")
                
            if st.button("➕ Insertar Circuito al Cuadro", type="primary", use_container_width=True, key="btn_add_circ_mtd"):
                st.session_state["mtd_circuitos"].append({
                    "nombre": nc_nom, "potencia": nc_pot, "pia": nc_pia,
                    "seccion": nc_sec, "tubo": nc_tubo, "longitud": nc_long,
                    "cdt": nc_cdt, "norma": nc_norma
                })
                st.success(f"✅ ¡Circuito '{nc_nom}' añadido al cuadro con éxito!")
                st.rerun()

        col_b_mtd1, col_b_mtd2 = st.columns([1.6, 1])
        with col_b_mtd1:
            if st.button("💰 Generar Presupuesto de Obra desde este Cuadro de Circuitos", type="secondary", use_container_width=True, key="btn_gen_presup_from_mtd"):
                st.session_state["presupuesto_circuitos_importados"] = st.session_state.get("mtd_circuitos", [])
                st.session_state.menu_activo = "🏡 Presupuesto Vivienda"
                st.success("✅ ¡Traspasando cuadro de protecciones y líneas al módulo de Presupuestos! Redirigiendo...")
                st.rerun()
        with col_b_mtd2:
            st.caption("Crea automáticamente un presupuesto con las líneas, PIAs, diferenciales y metros de cable.")

    # --- TAB 6: PROTOCOLO DE ENSAYOS (ITC-BT-05) ---
    with tab_f6:
        st.markdown("##### 🧪 Bloque VI: Protocolo de Ensayos y Verificaciones Previas (ITC-BT-05 Murcia):")
        st.markdown("""
        Introduce los valores medidos con el equipo verificador multifunción en la instalación:
        """)
        col_t_1, col_t_2 = st.columns(2)
        with col_t_1:
            med_pe = st.number_input("Continuidad de Conductores PE (Ω) [Límite ≤ 0.50 Ω]:", value=float(st.session_state.get("mtd_in_med_pe", 0.11)), step=0.01, format="%.2f", key="mtd_in_med_pe")
            med_aisl = st.number_input("Resistencia de Aislamiento a 500 Vcc (MΩ) [Límite ≥ 1.0 MΩ]:", value=float(st.session_state.get("mtd_in_med_aisl", 100.0)), step=1.0, format="%.1f", key="mtd_in_med_aisl")
            med_rt = st.number_input("Resistencia de Bucle / Toma de Tierra Rt (Ω) [Límite ≤ 15 Ω]:", value=float(st.session_state.get("mtd_in_med_rt", 11.8)), step=0.1, format="%.1f", key="mtd_in_med_rt")
        with col_t_2:
            med_dif_ma = st.number_input("Corriente de Disparo Diferencial (mA) [Límite ≤ 30 mA]:", value=float(st.session_state.get("mtd_in_med_dif_ma", 22.0)), step=1.0, format="%.1f", key="mtd_in_med_dif_ma")
            med_dif_ms = st.number_input("Tiempo de Disparo Diferencial (ms) [Límite ≤ 300 ms]:", value=float(st.session_state.get("mtd_in_med_dif_ms", 26.0)), step=1.0, format="%.1f", key="mtd_in_med_dif_ms")
            med_vsp = st.selectbox("Comprobación Disparo de Sobretensiones (VTP + DPS):", ["Conforme (Disparo y señalización verificados)", "No Conforme"], key="mtd_in_med_vsp")

        # Semáforo de verificación ITC-BT-05
        cumple_ensayos = (med_pe <= 0.50) and (med_aisl >= 1.0) and (med_rt <= 15.0) and (med_dif_ma <= 30.0) and (med_dif_ms <= 300.0) and ("Conforme" in med_vsp)
        if cumple_ensayos:
            st.success("✅ **TODAS LAS VERIFICACIONES PREVIAS ITC-BT-05 SON CONFORMES CON EL REBT.** Instalación apta para puesta en servicio.")
        else:
            st.error("⚠️ **HAY MEDIDAS QUE SUPERAN LOS LÍMITES REGLAMENTARIOS DEL REBT.** Subsanar anomalías antes de la tramitación ante Industria.")

    # --- TAB 7: PLANOS Y ANEXOS OFICIALES (I, II Y III) ---
    with tab_f7:
        st.markdown("##### 🗺️ Planos Oficiales, Anexos Gráficos y Auditoría Inteligente REBT:")
        st.caption("Adjunta los planos de situación, emplazamiento y distribución para su incorporación en el PDF oficial. También puedes auditar tus fotos y unifilar con el Copiloto de Inteligencia Artificial.")

        auditor_ia_rebt.render_ui_configuracion_ia()

        col_anx1, col_anx2 = st.columns(2)
        with col_anx1:
            with st.container(border=True):
                st.markdown("###### 🗺️ Anexo I (a): Plano de Situación")
                st.caption("Mapa general / callejero de situación en el municipio (Google Maps / Cartografía).")
                up_sit = st.file_uploader("Subir Plano de Situación (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key="up_mtd_sit")
                if up_sit is not None:
                    f_id_s = f"{up_sit.name}_{up_sit.size}"
                    if st.session_state.get("_last_tab7_sit_id") != f_id_s:
                        b64_sit = procesar_archivo_anexo(up_sit)
                        if b64_sit:
                            st.session_state["mtd_plano_situacion"] = b64_sit
                            st.session_state["_last_tab7_sit_id"] = f_id_s
                if st.session_state.get("mtd_plano_situacion"):
                    st.success("✅ Plano de Situación listo para el PDF oficial.")
                    st.image(st.session_state["mtd_plano_situacion"], caption="Plano de Situación cargado", use_container_width=True)
                    if st.button("🗑️ Quitar Plano de Situación", key="btn_del_sit"):
                        st.session_state.pop("mtd_plano_situacion", None)
                        st.session_state.pop("_last_tab7_sit_id", None)
                        st.rerun()

            with st.container(border=True):
                st.markdown("###### 📐 Anexo II: Plano en Planta de Distribución en B.T.")
                st.caption("Plano en planta de la vivienda, local o nave con tomas, alumbrado y cuadro (AutoCAD / Plano arquitectónico).")
                up_dist = st.file_uploader("Subir Plano de Distribución (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key="up_mtd_dist")
                if up_dist is not None:
                    f_id_d = f"{up_dist.name}_{up_dist.size}"
                    if st.session_state.get("_last_tab7_dist_id") != f_id_d:
                        b64_dist = procesar_archivo_anexo(up_dist)
                        if b64_dist:
                            st.session_state["mtd_plano_distribucion"] = b64_dist
                            st.session_state["_last_tab7_dist_id"] = f_id_d
                if st.session_state.get("mtd_plano_distribucion"):
                    st.success("✅ Plano de Distribución listo para el PDF oficial.")
                    st.image(st.session_state["mtd_plano_distribucion"], caption="Plano de Distribución cargado", use_container_width=True)
                    if st.button("🗑️ Quitar Plano de Distribución", key="btn_del_dist"):
                        st.session_state.pop("mtd_plano_distribucion", None)
                        st.session_state.pop("_last_tab7_dist_id", None)
                        st.rerun()

        with col_anx2:
            with st.container(border=True):
                st.markdown("###### 📍 Anexo I (b): Plano de Emplazamiento (Catastro)")
                st.caption("Plano parcelario catastral o urbanístico de la finca / parcela.")
                up_emp = st.file_uploader("Subir Plano de Emplazamiento (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key="up_mtd_emp")
                if up_emp is not None:
                    f_id_e = f"{up_emp.name}_{up_emp.size}"
                    if st.session_state.get("_last_tab7_emp_id") != f_id_e:
                        b64_emp = procesar_archivo_anexo(up_emp)
                        if b64_emp:
                            st.session_state["mtd_plano_emplazamiento"] = b64_emp
                            st.session_state["_last_tab7_emp_id"] = f_id_e
                if st.session_state.get("mtd_plano_emplazamiento"):
                    st.success("✅ Plano de Emplazamiento listo para el PDF oficial.")
                    st.image(st.session_state["mtd_plano_emplazamiento"], caption="Plano de Emplazamiento cargado", use_container_width=True)
                    if st.button("🗑️ Quitar Plano de Emplazamiento", key="btn_del_emp"):
                        st.session_state.pop("mtd_plano_emplazamiento", None)
                        st.session_state.pop("_last_tab7_emp_id", None)
                        st.rerun()

            with st.container(border=True):
                st.markdown("###### ⚡ Anexo III: Esquema Unifilar Oficial")
                st.caption("Elige si deseas que Bolimur genere el unifilar vectorial oficial o si prefieres anexar tu propio plano unifilar:")
                
                opciones_unifilar = [
                    "🔹 Generar Esquema Unifilar Automático de Bolimur (Vectorial UNE-EN 60617)",
                    "📁 Adjuntar mi Propio Plano de Esquema Unifilar (AutoCAD / Cade_Simu / PDF)"
                ]
                modo_def_idx = 1 if st.session_state.get("mtd_unifilar_modo") == "custom" else 0
                sel_modo_unif = st.radio(
                    "Modo de Generación del Esquema Unifilar:",
                    opciones_unifilar,
                    index=modo_def_idx,
                    key="radio_sel_modo_unif"
                )
                
                if "Adjuntar mi Propio" in sel_modo_unif:
                    st.session_state["mtd_unifilar_modo"] = "custom"
                    st.markdown("<div style='background:#fef3c7; border:1px solid #f59e0b; padding:8px 12px; border-radius:6px; margin:8px 0; font-size:13px;'>📁 <b>Modo Plano Propio Activado:</b> Selecciona abajo tu imagen o PDF del unifilar para reemplazar el esquema estándar.</div>", unsafe_allow_html=True)
                    up_unif = st.file_uploader("Subir tu Esquema Unifilar (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key="up_mtd_unif_custom")
                    if up_unif is not None:
                        f_id_u = f"{up_unif.name}_{up_unif.size}"
                        if st.session_state.get("_last_tab7_unif_id") != f_id_u:
                            b64_unif = procesar_archivo_anexo(up_unif)
                            if b64_unif:
                                st.session_state["mtd_plano_unifilar_custom"] = b64_unif
                                st.session_state["_last_tab7_unif_id"] = f_id_u
                    if st.session_state.get("mtd_plano_unifilar_custom"):
                        st.image(st.session_state["mtd_plano_unifilar_custom"], caption="Tu Esquema Unifilar Personalizado", use_container_width=True)
                        st.success("✅ Tu propio esquema unifilar se insertará en el Anexo III con el cajetín oficial de Industria.")

                        # Auditoría IA del Unifilar
                        if st.session_state.get("mtd_auditoria_unifilar"):
                            auditor_ia_rebt.render_tarjeta_auditoria(st.session_state["mtd_auditoria_unifilar"], "Esquema Unifilar Personalizado")

                        col_u1, col_u2 = st.columns([1.5, 1])
                        with col_u1:
                            lbl_u_btn = "🔄 Re-auditar Unifilar" if st.session_state.get("mtd_auditoria_unifilar") else "🤖 Auditar Unifilar con IA"
                            if st.button(lbl_u_btn, key="btn_audit_unif", use_container_width=True):
                                with st.spinner("Auditoría REBT en curso: analizando protecciones, secciones y normativa..."):
                                    ctx_u = {
                                        "tipo": tipo_inst_sel,
                                        "potencia_w": sum_pot_inst,
                                        "tension": sum_tension,
                                        "iga": f"{prot_iga} A",
                                        "diferenciales": f"{prot_dif} mA",
                                        "sobretensiones": prot_vtp
                                    }
                                    res_u = auditor_ia_rebt.auditar_evidencia_multimodal(
                                        imagen_b64=st.session_state["mtd_plano_unifilar_custom"],
                                        tipo_evidencia="Esquema Unifilar B.T.",
                                        descripcion_usuario="Plano unifilar personalizado",
                                        contexto_instalacion=ctx_u
                                    )
                                    st.session_state["mtd_auditoria_unifilar"] = res_u
                                    st.rerun()
                        with col_u2:
                            if st.button("🗑️ Quitar Unifilar Propio", key="btn_del_unif", use_container_width=True):
                                st.session_state.pop("mtd_plano_unifilar_custom", None)
                                st.session_state.pop("mtd_auditoria_unifilar", None)
                                st.rerun()
                else:
                    st.session_state["mtd_unifilar_modo"] = "auto"
                    st.info("ℹ️ Bolimur generará automáticamente el esquema unifilar vectorial con las protecciones IGA, diferenciales y circuitos configurados en las pestañas anteriores.")

        st.markdown("---")
        st.markdown("##### 📸 Anexo V: Reportaje Fotográfico de Fin de Obra y Evidencias REBT (ITC-BT-05)")
        st.caption("Guarda fotografías clave de la ejecución. Es tu blindaje legal ante inspecciones de Industria o averías futuras, y se incluye como Anexo V oficial con pie explicativo:")

        if "mtd_fotos_obra" not in st.session_state:
            st.session_state["mtd_fotos_obra"] = []

        col_add_f1, col_add_f2, col_add_f3 = st.columns([2, 2.5, 1.2])
        with col_add_f1:
            tipo_foto_sugerida = st.selectbox(
                "Tipo de Evidencia Fotográfica:",
                [
                    "Cuadro General (CGMP) montado y rotulado",
                    "Punto de Puesta a Tierra (Pica, Arqueta y Borna)",
                    "Acometida / CGP / Módulo de Contadores",
                    "Display Comprobador Multifunción (Medida Rt / PE)",
                    "Ensayo Disparo Diferencial (Multifunción)",
                    "Canalizaciones y Tubos empotrados en obra",
                    "Mecanismos y Cuadro de Mando en Vivienda / Local",
                    "Otra fotografía libre de la instalación"
                ],
                key="sel_tipo_foto_sug"
            )
        with col_add_f2:
            tit_foto_custom = st.text_input("Descripción técnica de la foto:", value=tipo_foto_sugerida, key="txt_desc_foto_in")
        with col_add_f3:
            st.write("")
            st.caption("Sube la foto abajo:")

        up_nueva_foto = st.file_uploader("Subir Fotografía de la Obra (JPG o PNG):", type=["png", "jpg", "jpeg", "webp"], key="uploader_foto_obra_temp")
        if up_nueva_foto is not None:
            col_bf1, col_bf2 = st.columns([1.5, 3])
            with col_bf1:
                if st.button("➕ Insertar Foto al Reportaje", type="primary", use_container_width=True, key="btn_add_foto_list"):
                    b64_f = procesar_archivo_anexo(up_nueva_foto)
                    if b64_f:
                        st.session_state["mtd_fotos_obra"].append({
                            "titulo": tit_foto_custom,
                            "data": b64_f
                        })
                        st.success(f"✅ Foto '{tit_foto_custom}' añadida al reportaje.")
                        st.rerun()

        # Mostrar galería de fotos adjuntadas
        fotos_actuales = st.session_state.get("mtd_fotos_obra", [])
        if fotos_actuales:
            st.markdown(f"###### 📷 Fotografías registradas en este expediente ({len(fotos_actuales)} foto/s):")
            f_cols = st.columns(min(len(fotos_actuales), 3))
            for f_idx, f_item in enumerate(fotos_actuales):
                c_idx = f_idx % len(f_cols)
                with f_cols[c_idx]:
                    with st.container(border=True):
                        st.image(f_item["data"], caption=f_item["titulo"], use_container_width=True)
                        
                        # Mostrar tarjeta de auditoría si ya está auditada
                        if f_item.get("auditoria"):
                            auditor_ia_rebt.render_tarjeta_auditoria(f_item["auditoria"], f_item["titulo"])

                        col_fa1, col_fa2 = st.columns([1.5, 1])
                        with col_fa1:
                            lbl_fa_btn = "🔄 Re-auditar" if f_item.get("auditoria") else "🤖 Auditar IA"
                            if st.button(lbl_fa_btn, key=f"btn_audit_foto_{f_idx}", use_container_width=True):
                                with st.spinner("Analizando evidencia con IA y REBT..."):
                                    ctx_f = {
                                        "tipo": tipo_inst_sel,
                                        "potencia_w": sum_pot_inst,
                                        "tension": sum_tension,
                                        "iga": f"{prot_iga} A",
                                        "diferenciales": f"{prot_dif} mA",
                                        "sobretensiones": prot_vtp
                                    }
                                    res_f = auditor_ia_rebt.auditar_evidencia_multimodal(
                                        imagen_b64=f_item["data"],
                                        tipo_evidencia=f_item.get("titulo", "Evidencia de Obra"),
                                        descripcion_usuario=f_item.get("titulo", ""),
                                        contexto_instalacion=ctx_f
                                    )
                                    f_item["auditoria"] = res_f
                                    st.rerun()
                        with col_fa2:
                            if st.button("🗑️ Eliminar", key=f"btn_del_foto_{f_idx}", use_container_width=True):
                                st.session_state["mtd_fotos_obra"].pop(f_idx)
                                st.rerun()

    # =========================================================================
    # 3. GUARDAR VINCULADO AL CLIENTE (CRM) Y GENERACIÓN DE DOCUMENTACIÓN OFICIAL
    # =========================================================================
    st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">💾 3. Guardar en Ficha del Cliente y Exportar Documentación Oficial (Murcia / REBT)</h4></div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        col_s_name, col_s_btn = st.columns([3, 1.5])
        with col_s_name:
            if tipo_inst_sel.startswith("⚪") or "Blanco" in tipo_inst_sel or "Seleccionar" in tipo_inst_sel:
                tipo_desc = emp_uso.strip() or "Instalación Eléctrica BT"
            else:
                tipo_desc = tipo_inst_sel.split('(')[0].replace('☀️', '').replace('🏗️', '').replace('🚗', '').replace('🏡', '').replace('🏢', '').replace('⚡', '').replace('🔌', '').strip()
            nom_proy_default = f"MTD - {tipo_desc} - {tit_nombre or 'Sin Titular'}"
            nom_proy_mtd = st.text_input("Nombre / Referencia del Expediente para Guardar:", value=nom_proy_default, key="mtd_nom_guardar")
        with col_s_btn:
            st.write("")
            st.write("")
            if st.button("💾 Guardar en Ficha de Cliente", type="primary", use_container_width=True):
                if not cli_sel_id:
                    st.error("Debes seleccionar un cliente del CRM arriba para asociar la memoria técnica.")
                else:
                    datos_guardar = {
                        "mtd_tipo_inst_sel": tipo_inst_sel,
                        "mtd_tipo_tram_sel": tipo_tram_sel,
                        "mtd_in_tit_nom": tit_nombre,
                        "mtd_in_tit_nif": tit_nif,
                        "mtd_in_tit_tel": tit_tel,
                        "mtd_in_tit_email": tit_email,
                        "mtd_in_emp_dir": emp_dir,
                        "mtd_in_emp_cp": emp_cp,
                        "mtd_in_emp_muni": emp_muni,
                        "mtd_in_emp_cups": emp_cups,
                        "mtd_in_emp_uso": emp_uso,
                        "mtd_in_pot_inst": sum_pot_inst,
                        "mtd_in_pot_max": sum_pot_max,
                        "mtd_in_tension": sum_tension,
                        "mtd_in_origen": sum_origen,
                        "mtd_in_di_cable": sum_di_cable,
                        "mtd_in_di_tubo": sum_di_tubo,
                        "mtd_in_di_long": sum_di_long,
                        "mtd_in_di_cdt": sum_di_cdt,
                        "mtd_in_grado": sum_grado,
                        "mtd_in_iga": prot_iga,
                        "mtd_in_curva": prot_curva,
                        "mtd_in_icn": prot_icn,
                        "mtd_in_dif": prot_dif,
                        "mtd_in_vtp": prot_vtp,
                        "mtd_in_tierra": prot_tierra,
                        "mtd_in_spl": prot_spl,
                        "mtd_circuitos": st.session_state.get("mtd_circuitos", []),
                        "mtd_in_med_pe": med_pe,
                        "mtd_in_med_aisl": med_aisl,
                        "mtd_in_med_rt": med_rt,
                        "mtd_in_med_dif_ma": med_dif_ma,
                        "mtd_in_med_dif_ms": med_dif_ms,
                        "mtd_plano_situacion": st.session_state.get("mtd_plano_situacion", ""),
                        "mtd_plano_emplazamiento": st.session_state.get("mtd_plano_emplazamiento", ""),
                        "mtd_plano_distribucion": st.session_state.get("mtd_plano_distribucion", ""),
                        "mtd_unifilar_modo": st.session_state.get("mtd_unifilar_modo", "auto"),
                        "mtd_plano_unifilar_custom": st.session_state.get("mtd_plano_unifilar_custom", ""),
                        "mtd_auditoria_unifilar": st.session_state.get("mtd_auditoria_unifilar", {}),
                        "mtd_fotos_obra": st.session_state.get("mtd_fotos_obra", [])
                    }
                    resumen_txt = f"{sum_pot_inst/1000:.2f} kW | {tipo_tram_sel.split('(')[0].strip()} | {emp_muni}"
                    ok, p_id = db_manager.guardar_proyecto(
                        usuario_id=user_auth["id"],
                        cliente_id=cli_sel_id,
                        nombre_proyecto=nom_proy_mtd,
                        modulo="Memoria Técnica (MTD 30)",
                        datos=datos_guardar,
                        resumen=resumen_txt
                    )
                    if ok:
                        st.success(f"✅ ¡Memoria Técnica '{nom_proy_mtd}' guardada exitosamente en la ficha de {cli_obj.get('nombre_completo', 'Cliente')}!")
                        st.rerun()
                    else:
                        st.error("Error al guardar la memoria técnica en la base de datos.")

        st.divider()

        # DOCUMENTOS OFICIALES PARA INDUSTRIA Y CLIENTE
        col_g1, col_g2 = st.columns([3, 2])
        with col_g1:
            exp_in = st.text_input("Nº de Expediente Oficial (DGEAIM Murcia):", value=f"EXP-MTD-{emp_muni[:3].upper()}-2026-01", key="mtd_exp_final")
        with col_g2:
            st.write("")
            st.caption("Generación simultánea de toda la documentación requerida por Industria y el REBT.")

        tipo_para_doc = (emp_uso.strip() or "Instalación Eléctrica en Baja Tensión") if (tipo_inst_sel.startswith("⚪") or "Blanco" in tipo_inst_sel or "Seleccionar" in tipo_inst_sel) else tipo_inst_sel

        datos_para_pdf = {
            "tipo_instalacion": tipo_para_doc,
            "tipo_tramitacion": tipo_tram_sel,
            "expediente": exp_in,
            "fecha": datetime.date.today().strftime("%d/%m/%Y"),
            "titular": {
                "nombre": tit_nombre,
                "nif": tit_nif,
                "telefono": tit_tel,
                "email": tit_email
            },
            "emplazamiento": {
                "direccion": emp_dir,
                "cp": emp_cp,
                "municipio": emp_muni,
                "cups": emp_cups,
                "uso": emp_uso
            },
            "instalador": {
                "empresa": inst_empresa,
                "cif": inst_cif,
                "nombre": inst_nom,
                "licencia": inst_lic,
                "nif": inst_nif,
                "registro_rii": inst_rii,
                "telefono": user_auth.get("telefono", "+34 600 000 000")
            },
            "suministro": {
                "potencia_instalada_w": sum_pot_inst,
                "potencia_max_admisible_w": sum_pot_max,
                "tension": sum_tension,
                "origen": sum_origen,
                "di_cable": sum_di_cable,
                "di_tubo": sum_di_tubo,
                "di_long_m": sum_di_long,
                "di_cdt_pct": sum_di_cdt,
                "grado_electrif": sum_grado
            },
            "protecciones": {
                "iga_amperaje": prot_iga,
                "iga_curva": prot_curva,
                "iga_icn_ka": prot_icn,
                "diferenciales": prot_dif,
                "sobretensiones": prot_vtp,
                "puesta_a_tierra": prot_tierra
            },
            "ensayos": {
                "pe_ohm": med_pe,
                "aisl_mohm": med_aisl,
                "rt_ohm": med_rt,
                "dif_ma": med_dif_ma,
                "dif_ms": med_dif_ms
            },
            "circuitos": st.session_state.get("mtd_circuitos", []),
            "anexos": {
                "plano_situacion": st.session_state.get("mtd_plano_situacion", ""),
                "plano_emplazamiento": st.session_state.get("mtd_plano_emplazamiento", ""),
                "plano_distribucion": st.session_state.get("mtd_plano_distribucion", ""),
                "unifilar_modo": st.session_state.get("mtd_unifilar_modo", "auto"),
                "plano_unifilar_custom": st.session_state.get("mtd_plano_unifilar_custom", ""),
                "fotos": st.session_state.get("mtd_fotos_obra", [])
            }
        }

        tab_doc1, tab_doc2, tab_doc3 = st.tabs([
            "🏛️ Memoria Técnica Oficial (MTD 30)",
            "📑 Certificado de Instalación (CIE / Boletín)",
            "📘 Manual de Instrucciones (ITC-BT-04)"
        ])

        from modulos import visor_pdf
        from modulos import generador_doc_oficial

        with tab_doc1:
            st.info("💡 **Doble Formato Oficial Disponible:** Puedes descargar la Memoria Técnica tanto en **PDF oficial** (para firmar con AutoFirma/DNIe y registrar en la Sede Electrónica de la CARM) como en **Word (.docx editable)** (sobre la plantilla oficial de la DGEAIM Murcia para edición personal o archivo).")
            
            docx_bytes_mtd = None
            try:
                docx_bytes_mtd = generador_doc_oficial.generar_docx_oficial_dgeaim_murcia(datos_para_pdf)
            except Exception as err_docx:
                st.warning(f"⚠️ Nota Word: {err_docx}")

            es_windows = (os.name == "nt")
            opciones_motor = [
                "⚡ PDF Vectorial Homologado (ReportLab + Membrete CARM)",
                "🏛️ PDF Clonado por Word COM (Plantilla Word + Logos CARM)"
            ] if not es_windows else [
                "🏛️ PDF Clonado por Word COM (Plantilla Word + Logos CARM)",
                "⚡ PDF Vectorial Homologado (ReportLab + Membrete CARM)"
            ]

            col_d_act1, col_d_act2 = st.columns([1.2, 1.8])
            with col_d_act1:
                if docx_bytes_mtd:
                    st.download_button(
                        label="📝 Descargar Word (.docx Editable)",
                        data=docx_bytes_mtd,
                        file_name=f"MTD_Oficial_DGEAIM_Murcia_{exp_in}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="secondary",
                        use_container_width=True,
                        key=f"dl_word_btn_{exp_in.replace('-', '_').replace(' ', '_')}",
                        help="Descarga el documento de Microsoft Word original de Industria de Murcia con todos tus datos introducidos en sus tablas y casillas."
                    )
            with col_d_act2:
                formato_pdf_sel = st.radio(
                    "Motor de Renderizado PDF:",
                    opciones_motor,
                    horizontal=True,
                    key="sel_motor_pdf_mtd"
                )

            pdf_bytes_mtd = None
            es_clonado_word = "Word COM" in formato_pdf_sel

            if es_clonado_word and docx_bytes_mtd:
                cache_key = f"pdf_word_com_{exp_in}"
                if cache_key in st.session_state:
                    pdf_bytes_mtd = st.session_state[cache_key]
                else:
                    with st.spinner("Compilando PDF idéntico a Word con motor oficial de Microsoft Word..."):
                        pdf_bytes_mtd = generador_doc_oficial.convertir_docx_a_pdf(docx_bytes_mtd)
                        if pdf_bytes_mtd:
                            st.session_state[cache_key] = pdf_bytes_mtd
                        else:
                            st.info("ℹ️ El motor Word COM requiere un entorno Windows con Word instalado. En servidores en la nube (Linux) se genera con el motor vectorial homologado con membrete y logos de la CARM.")

            if not pdf_bytes_mtd:
                try:
                    pdf_bytes_mtd = pdf_memoria_tecnica.generar_pdf_mtd_industria_murcia(datos_para_pdf)
                except Exception as err:
                    st.error(f"⚠️ Error al generar el PDF de la MTD: {err}")

            if pdf_bytes_mtd:
                visor_pdf.mostrar_visor_pdf(
                    pdf_bytes=pdf_bytes_mtd,
                    nombre_archivo=f"MTD_Oficial_DGEAIM_Murcia_{exp_in}.pdf",
                    label_boton="📥 Descargar Memoria Técnica Oficial MTD (PDF Murcia - Listo para Firmar)"
                )

        with tab_doc2:
            try:
                pdf_bytes_cie = pdf_memoria_tecnica.generar_pdf_cie_oficial(datos_para_pdf)
                visor_pdf.mostrar_visor_pdf(
                    pdf_bytes=pdf_bytes_cie,
                    nombre_archivo=f"CIE_Boletin_Oficial_{exp_in}.pdf",
                    label_boton="📥 Descargar Certificado de Instalación CIE (Boletín Eléctrico)"
                )
            except Exception as err:
                st.error(f"⚠️ Error al generar el Certificado CIE: {err}")

        with tab_doc3:
            try:
                pdf_bytes_man = pdf_memoria_tecnica.generar_pdf_manual_usuario(datos_para_pdf)
                visor_pdf.mostrar_visor_pdf(
                    pdf_bytes=pdf_bytes_man,
                    nombre_archivo=f"Manual_Instrucciones_Usuario_{tit_nombre.replace(' ', '_')}.pdf",
                    label_boton="📥 Descargar Manual de Instrucciones de Usuario (ITC-BT-04)"
                )
            except Exception as err:
                st.error(f"⚠️ Error al generar el Manual de Usuario: {err}")

