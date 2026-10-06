# -*- coding: utf-8 -*-
"""
Módulo Oficial de Memoria Técnica de Diseño (MTD) para la Dirección General de Energía
y Actividad Industrial y Minera de la Región de Murcia (DGEAIM - Código Provincial 30)
Permite el llenado profesional, el auto-rellenado inteligente a partir de cálculos REBT
y el guardado/recuperación persistente vinculado a las fichas de clientes en el CRM.
"""

import streamlit as st
import os
import re
import datetime
import math
import copy
import pandas as pd
import json
import io
import base64
from modulos import rebt_tablas as rebt
from modulos import pdf_memoria_tecnica
from modulos import db_manager, auth_manager
from modulos import auditor_ia_rebt
from modulos import generador_doc_oficial, visor_pdf

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
    en un string data-URI base64 optimizado para almacenamiento, visualización y ReportLab.
    Aplica corrección automática de orientación EXIF para fotos tomadas con teléfonos móviles.
    """
    if uploaded_file is None:
        return ""
    try:
        raw_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file
        if not raw_bytes:
            return ""

        # Si es un PDF, renderizar primera página a PNG con PyMuPDF
        if raw_bytes.startswith(b"%PDF"):
            try:
                try:
                    import pymupdf as fitz
                except ImportError:
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

        from PIL import Image as PILImage, ImageOps
        bio_in = io.BytesIO(raw_bytes)
        with PILImage.open(bio_in) as im:
            try:
                im = ImageOps.exif_transpose(im)
            except Exception:
                pass
            if im.mode != "RGB":
                im = im.convert("RGB")
            # Redimensionar si es muy grande manteniendo proporciones
            im.thumbnail((1600, 1600), PILImage.Resampling.LANCZOS)
            bio_out = io.BytesIO()
            im.save(bio_out, format="JPEG", quality=85, optimize=True)
            b64_str = base64.b64encode(bio_out.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        st.error(f"Error procesando imagen del plano o evidencia: {e}")
        return ""


# =========================================================================
# CATÁLOGO OFICIAL DE PLANTILLAS MTD REBT - REGIÓN DE MURCIA (CÓDIGO 30)
# =========================================================================

CATALOGO_PLANTILLAS_MTD = {
    "vivienda_basica": {
        "id": "vivienda_basica",
        "titulo": "Vivienda Básica (5.750 W - 230V - IGA 25A)",
        "categoria": "🏡 Viviendas Residenciales (ITC-BT-10 / 25)",
        "potencia_inst": 5750.0,
        "potencia_max": 5750.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Derivación Individual desde Centralización (ITC-BT-15)",
        "di_cable": "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M32 libre de halógenos (ITC-BT-15)",
        "di_long": 15.0,
        "di_cdt": 0.72,
        "grado": "Básica",
        "iga": 25,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "Interruptor Diferencial 2P 40A / 30mA Clase A / Superinmunizado",
        "vtp": "Permanentes (VTP) + Transitorias Tipo 2 con reconexión",
        "tierra": "Conductor PE 1x10 mm² Cu | Picas en anillo Rt ≤ 15 Ω",
        "spl": "No aplica",
        "emp_uso": "Vivienda Residencial Electrificación Básica",
        "cuando_elegir": "Viviendas estándar de hasta 160 m² de superficie útil sin climatización centralizada, aerotermia ni calefacción eléctrica.",
        "criterios_rebt": "ITC-BT-10 e ITC-BT-25: Mínimo 5.750 W con IGA 25A. Secciones mínimas de 1,5 a 6 mm² Cu. Máximo 5 circuitos por diferencial de 30 mA.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora / Termo", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Auxiliares", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"}
        ]
    },
    "vivienda_elevada_clima": {
        "id": "vivienda_elevada_clima",
        "titulo": "Vivienda Elevada - Clima / Calefacción (9.200 W - 230V - IGA 40A)",
        "categoria": "🏡 Viviendas Residenciales (ITC-BT-10 / 25)",
        "potencia_inst": 9200.0,
        "potencia_max": 9200.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Derivación Individual desde Centralización (ITC-BT-15)",
        "di_cable": "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M40 libre de halógenos (ITC-BT-15)",
        "di_long": 18.0,
        "di_cdt": 0.85,
        "grado": "Elevada",
        "iga": 40,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "2 x Diferencial 2P 40A / 30mA (D1: Tipo AC, D2: Tipo A Superinmunizado para Clima e Inverter)",
        "vtp": "Permanentes (VTP) + Transitorias Tipo 2 con reconexión",
        "tierra": "Conductor PE 1x16 mm² Cu | Picas en anillo Rt ≤ 15 Ω",
        "spl": "No aplica",
        "emp_uso": "Vivienda Residencial Electrificación Elevada con Climatización",
        "cuando_elegir": "Vivienda habitual en Murcia equipada con aire acondicionado por conductos o varios splits, secadora y/o calefacción eléctrica.",
        "criterios_rebt": "ITC-BT-10 e ITC-BT-25. Potencia mínima 9.200 W con IGA 40A. DI obligatoria de 16 mm² Cu en tubo M40 (modelo oficial Murcia DGEAIM). Al superar 5 circuitos, se instalan obligatoriamente al menos 2 diferenciales de 30 mA.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
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
    },
    "vivienda_elevada_aerotermia": {
        "id": "vivienda_elevada_aerotermia",
        "titulo": "Vivienda Elevada - Aerotermia + Climatización (11.500 W - 230V - IGA 50A)",
        "categoria": "🏡 Viviendas Residenciales (ITC-BT-10 / 25)",
        "potencia_inst": 11500.0,
        "potencia_max": 11500.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Derivación Individual desde Centralización (ITC-BT-15)",
        "di_cable": "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M40 libre de halógenos (ITC-BT-15)",
        "di_long": 18.0,
        "di_cdt": 0.95,
        "grado": "Elevada",
        "iga": 50,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "3 x Diferencial 2P 40A / 30mA (Diferencial dedicado Tipo A Superinmunizado para Bomba de Calor Aerotérmica)",
        "vtp": "Permanentes (VTP) + Transitorias Tipo 2 con reconexión",
        "tierra": "Conductor PE 1x16 mm² Cu | Rt ≤ 15 Ω",
        "spl": "No aplica",
        "emp_uso": "Vivienda Residencial con Aerotermia y Clima Centralizado",
        "cuando_elegir": "Viviendas de obra nueva o reformas integrales con sistema de climatización por aerotermia, suelo radiante/refrescante y producción hidrónica de ACS.",
        "criterios_rebt": "ITC-BT-10 y 25. IGA de 50A a 230V. Diferencial superinmunizado clase A imprescindible para evitar disparos intempestivos provocados por los filtros EMC del compresor inverter.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora y Lavavajillas", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Tomas Húmedas", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"},
            {"nombre": "C9 - Climatización / Fancoils Inverter", "potencia": 4500, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.12, "norma": "ITC-BT-25"},
            {"nombre": "C10 - Secadora Independiente", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.85, "norma": "ITC-BT-25"},
            {"nombre": "C11 - Aerotermia Bomba de Calor ACS y Suelo Radiante", "potencia": 4500, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 14, "cdt": 0.95, "norma": "ITC-BT-25"},
            {"nombre": "C12 - Cuadro Exterior / Depuradora / Piscina", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 22, "cdt": 1.25, "norma": "ITC-BT-25"}
        ]
    },
    "vivienda_elevada_max_mono": {
        "id": "vivienda_elevada_max_mono",
        "titulo": "Vivienda Elevada - Máxima Monofásica (14.490 W - 230V - IGA 63A)",
        "categoria": "🏡 Viviendas Residenciales (ITC-BT-10 / 25)",
        "potencia_inst": 14490.0,
        "potencia_max": 14490.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Derivación Individual desde Centralización (ITC-BT-15)",
        "di_cable": "2x25 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M50 libre de halógenos (ITC-BT-15)",
        "di_long": 20.0,
        "di_cdt": 0.98,
        "grado": "Elevada",
        "iga": 63,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "3 x Diferencial 2P 63A/30mA y 40A/30mA Clase A Superinmunizados",
        "vtp": "Permanentes (VTP) + Transitorias Tipo 2 con bobina y reconexión",
        "tierra": "Conductor PE 1x16 mm² Cu | Rt ≤ 15 Ω",
        "spl": "No aplica",
        "emp_uso": "Vivienda Residencial Máxima Electrificación Monofásica",
        "cuando_elegir": "Viviendas grandes que agotan el límite máximo monofásico admitido por distribuidoras en España (63A = 14,49 kW) para evitar el cambio a trifásica.",
        "criterios_rebt": "Tope técnico monofásico (63A a 230V). Derivación individual reforzada a 25 mm² Cu en tubo M50 para mantener la caída de tensión < 1,5% y capacidad térmica suficiente.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Placa Inducción y Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora y Lavavajillas", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Zonas Húmedas", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"},
            {"nombre": "C8 - Calefacción Eléctrica / Emisores", "potencia": 5000, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 16, "cdt": 1.20, "norma": "ITC-BT-25"},
            {"nombre": "C9 - Climatización Inverter Planta Baja", "potencia": 5000, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 15, "cdt": 1.05, "norma": "ITC-BT-25"},
            {"nombre": "C10 - Secadora Independiente", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.85, "norma": "ITC-BT-25"},
            {"nombre": "C11 - Climatización Planta Alta / Dormitorios", "potencia": 4000, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 18, "cdt": 1.18, "norma": "ITC-BT-25"},
            {"nombre": "C12 - Automatización y Domótica", "potencia": 1500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 20, "cdt": 0.70, "norma": "ITC-BT-25"},
            {"nombre": "C13 - Tomas Cocina Office Reforzadas", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.92, "norma": "ITC-BT-25"}
        ]
    },
    "vivienda_unifamiliar_chalet_tri": {
        "id": "vivienda_unifamiliar_chalet_tri",
        "titulo": "Vivienda Unifamiliar / Chalet Trifásica (17.320 W - 400V - IGA 25A Tri)",
        "categoria": "🏡 Viviendas Residenciales (ITC-BT-10 / 25)",
        "potencia_inst": 17320.0,
        "potencia_max": 17320.0,
        "tension": "Trifásico (400 V) - 50 Hz",
        "origen": "Caja de Protección y Medida CPM Fachada (ITC-BT-13)",
        "di_cable": "4x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M40 libre de halógenos (ITC-BT-15)",
        "di_long": 22.0,
        "di_cdt": 0.62,
        "grado": "Elevada Trifásica",
        "iga": 25,
        "curva": "Curva C (General)",
        "icn": 10.0,
        "dif": "1 x Diferencial Tetrapolar 4P 40A/30mA + 2 x Bipolares 2P 40A/30mA Clase A",
        "vtp": "Permanentes + Transitorias Tipo 2 Tetrapolar con bobina",
        "tierra": "Conductor PE 1x16 mm² Cu | Anillo cimentación Rt ≤ 10 Ω",
        "spl": "No aplica",
        "emp_uso": "Vivienda Unifamiliar Aislada / Chalet con Parcela",
        "cuando_elegir": "Chalets, viviendas en urbanizaciones o huerta de Murcia con piscina privada, climatización trifásica centralizada, riego por goteo y portón motorizado.",
        "criterios_rebt": "ITC-BT-10 e ITC-BT-25. Suministro trifásico 400V que distribuye equilibradamente las cargas en 3 fases y reduce la sección necesaria en tiradas largas hacia jardines o anexos.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado Interior y Fachada", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora y Lavavajillas", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Zonas Húmedas", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"},
            {"nombre": "C9 - Climatización Centralizada Trifásica 400V", "potencia": 7000, "pia": 16, "seccion": "4x2.5+TT2.5", "tubo": "M25", "longitud": 16, "cdt": 0.58, "norma": "ITC-BT-25"},
            {"nombre": "C10 - Secadora Independiente", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.85, "norma": "ITC-BT-25"},
            {"nombre": "C11 - Depuradora Piscina y Bomba Pozo", "potencia": 3000, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 25, "cdt": 1.35, "norma": "ITC-BT-25"},
            {"nombre": "C12 - Riego Automático y Alumbrado Parcela", "potencia": 1800, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 30, "cdt": 1.20, "norma": "ITC-BT-25"}
        ]
    },
    "irve_garaje_comunitario": {
        "id": "irve_garaje_comunitario",
        "titulo": "IRVE - Garaje Comunitario (Esquema 2 - 7.360 W - 230V - IGA 32A/40A)",
        "categoria": "🚗 Vehículo Eléctrico IRVE (ITC-BT-52)",
        "potencia_inst": 7360.0,
        "potencia_max": 7360.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Centralización de Contadores (Esquema 2)",
        "di_cable": "3G6 mm² Cu RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M32 libre de halógenos (IK08)",
        "di_long": 25.0,
        "di_cdt": 0.86,
        "grado": "Específica IRVE (ITC-BT-52)",
        "iga": 32,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "Diferencial 2P 40A / 30mA Clase A con detección DC 6mA (IEC 62955)",
        "vtp": "Permanentes (POP/VTP) + Transitorias Tipo 2 con bobina de disparo",
        "tierra": "Conductor PE 1x6 mm² Cu | Resistencia bucle tierra Rt ≤ 15 Ω",
        "spl": "Sensor toroidal CT para modulación dinámica en tiempo real",
        "emp_uso": "Garaje Comunitario / Punto de Recarga VE",
        "cuando_elegir": "Instalación de punto de recarga en plaza de garaje comunitario en Murcia según Esquema 2 (contador principal en la centralización común de contadores).",
        "criterios_rebt": "ITC-BT-52 e ITC-BT-29. Cables obligatoriamente no propagadores de incendio y libres de halógenos Cca-s1b,d1,a1 por zonas comunes, tubo rígido/curvable IK08 y diferencial Clase A con 6mA DC.",
        "alerta_lpc": False,
        "alerta_garaje": True,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "Línea Específica IRVE (Wallbox)", "potencia": 7360, "pia": 32, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 25, "cdt": 0.86, "norma": "ITC-BT-52"}
        ]
    },
    "irve_trifasico_comercial": {
        "id": "irve_trifasico_comercial",
        "titulo": "IRVE - Trifásico Comercial / Rápido (22.000 W - 400V - IGA 32A Tri)",
        "categoria": "🚗 Vehículo Eléctrico IRVE (ITC-BT-52)",
        "potencia_inst": 22000.0,
        "potencia_max": 22000.0,
        "tension": "Trifásico (400 V) - 50 Hz",
        "origen": "Cuadro General / Línea Distribución Terciaria (ITC-BT-52)",
        "di_cable": "4x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV",
        "di_tubo": "Tubo M40 libre de halógenos (IK08)",
        "di_long": 20.0,
        "di_cdt": 0.70,
        "grado": "Específica IRVE (ITC-BT-52)",
        "iga": 32,
        "curva": "Curva C (General)",
        "icn": 10.0,
        "dif": "Diferencial Tetrapolar 4P 40A / 30mA Clase A o Tipo B con detección DC 6mA",
        "vtp": "Permanentes + Transitorias Tipo 2 con bobina de emisión",
        "tierra": "Conductor PE 1x10 mm² Cu | Rt ≤ 10 Ω",
        "spl": "Modulación dinámica de potencia según disponibilidad de red",
        "emp_uso": "Aparcamiento Comercial / Flota / Cargador Rápido VE",
        "cuando_elegir": "Cargadores trifásicos de 22 kW en parkings de oficinas, hoteles, flotas de reparto o talleres mecánicos.",
        "criterios_rebt": "ITC-BT-52 Modo 3 (32A por fase). Legalizable con MTD hasta 50 kW en interior (en exterior el límite de MTD es 10 kW; superado exige Proyecto).",
        "alerta_lpc": False,
        "alerta_garaje": True,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "Línea Recarga VE Trifásica Modo 3", "potencia": 22000, "pia": 32, "seccion": "4x10+TT10", "tubo": "M40", "longitud": 20, "cdt": 0.70, "norma": "ITC-BT-52"}
        ]
    },
    "vivienda_con_irve_integrado": {
        "id": "vivienda_con_irve_integrado",
        "titulo": "Vivienda con Recarga VE Integrada (11.500 W - 230V - IGA 50A con SPL)",
        "categoria": "🚗 Vehículo Eléctrico IRVE (ITC-BT-52)",
        "potencia_inst": 11500.0,
        "potencia_max": 11500.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Derivación Individual desde Centralización (ITC-BT-15)",
        "di_cable": "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV",
        "di_tubo": "Tubo M40 libre de halógenos (ITC-BT-15)",
        "di_long": 18.0,
        "di_cdt": 0.95,
        "grado": "Elevada + IRVE (ITC-BT-25 / ITC-BT-52)",
        "iga": 50,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "3 x Diferencial 2P 40A/30mA (Dedicado Clase A con detección DC 6mA para cargador VE)",
        "vtp": "Permanentes (VTP) + Transitorias Tipo 2 con reconexión",
        "tierra": "Conductor PE 1x16 mm² Cu | Rt ≤ 15 Ω",
        "spl": "Sensor toroidal CT con Modulación Dinámica de Carga SPL (ITC-BT-52)",
        "emp_uso": "Vivienda Unifamiliar con Garaje Privado y Punto de Recarga VE",
        "cuando_elegir": "Vivienda unifamiliar o adosado donde se instala un cargador en el garaje privado compartiendo el cuadro general mediante circuito C13 con sensor de balanceo dinámico SPL.",
        "criterios_rebt": "ITC-BT-25 e ITC-BT-52. El sistema de protección de línea (SPL) modula dinámicamente la corriente de carga del vehículo para no sobrepasar la potencia del IGA/ICP contratado.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora / Termo", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Auxiliares", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"},
            {"nombre": "C9 - Climatización Inverter", "potencia": 5000, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C10 - Secadora Independiente", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.85, "norma": "ITC-BT-25"},
            {"nombre": "C13 - Línea Recarga VE con SPL Dinámico", "potencia": 7360, "pia": 32, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 18, "cdt": 0.72, "norma": "ITC-BT-52"}
        ]
    },
    "autoconsumo_solar_fv": {
        "id": "autoconsumo_solar_fv",
        "titulo": "Autoconsumo Solar Fotovoltaico (5.000 W Inversor - 230V - IGA 25A)",
        "categoria": "☀️ Autoconsumo Fotovoltaico (ITC-BT-40)",
        "potencia_inst": 5000.0,
        "potencia_max": 5000.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Generador Fotovoltaico Interconectado a Red Interior (ITC-BT-40)",
        "di_cable": "3G6 mm² Cu RZ1-K (AS) 0.6/1kV",
        "di_tubo": "Tubo M32 libre de halógenos",
        "di_long": 12.0,
        "di_cdt": 0.58,
        "grado": "Autoconsumo Fotovoltaico (ITC-BT-40)",
        "iga": 25,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "Diferencial 2P 40A / 30mA Clase A con detección DC 6mA (UNE-EN 62955)",
        "vtp": "Permanentes (POP) + Transitorias Tipo 2 con bobina y protección anti-isla integrada",
        "tierra": "Conductor PE 1x6 mm² Cu uniendo marcos y estructuras a tierra | Rt ≤ 15 Ω",
        "spl": "Smart Meter / Vatímetro de inyección cero / balance neto",
        "emp_uso": "Instalación Generadora en Autoconsumo (RD 244/2019)",
        "cuando_elegir": "Legalización de instalación de placas solares de autoconsumo interconectadas a la red interior de una vivienda o local comercial.",
        "criterios_rebt": "ITC-BT-40 y RD 244/2019. Inversor con relé de desconexión anti-isla conforme a UNE-EN 50549-1. Caída de tensión máxima en la línea de evacuación AC ≤ 1,0% para evitar sobretensiones en la red pública.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": True,
        "circuitos": [
            {"nombre": "Línea Evacuación AC Inversor", "potencia": 5000, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 12, "cdt": 0.58, "norma": "ITC-BT-40"},
            {"nombre": "Circuito Generación DC String 1", "potencia": 2750, "pia": 15, "seccion": "2x6.0 H1Z2Z2-K", "tubo": "M25 UV", "longitud": 18, "cdt": 0.65, "norma": "ITC-BT-40"},
            {"nombre": "Circuito Generación DC String 2", "potencia": 2750, "pia": 15, "seccion": "2x6.0 H1Z2Z2-K", "tubo": "M25 UV", "longitud": 20, "cdt": 0.72, "norma": "ITC-BT-40"}
        ]
    },
    "combo_vivienda_solar_irve": {
        "id": "combo_vivienda_solar_irve",
        "titulo": "Combo: Vivienda + Solar Fotovoltaica (5 kW) + IRVE (7.36 kW)",
        "categoria": "☀️ Autoconsumo Fotovoltaico (ITC-BT-40)",
        "potencia_inst": 11500.0,
        "potencia_max": 11500.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Centralización Contadores + Inversor Fotovoltaico Interconectado",
        "di_cable": "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV",
        "di_tubo": "Tubo M40 libre de halógenos",
        "di_long": 18.0,
        "di_cdt": 0.90,
        "grado": "Vivienda Sostenible (Solar + IRVE)",
        "iga": 50,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "3 x Diferencial 2P 40A/30mA Clase A Superinmunizados (Dedicado para VE y para Solar)",
        "vtp": "Permanentes + Transitorias Tipo 2 con bobina y anti-isla",
        "tierra": "Conductor PE 1x16 mm² Cu | Estructura FV conectada a PE | Rt ≤ 15 Ω",
        "spl": "Smart Meter bidireccional con gestión de excedentes hacia cargador VE",
        "emp_uso": "Vivienda Residencial con Autoconsumo Solar e Infraestructura IRVE",
        "cuando_elegir": "Viviendas energéticamente sostenibles donde se legaliza conjuntamente el autoconsumo solar y la recarga inteligente del vehículo eléctrico.",
        "criterios_rebt": "ITC-BT-10, 25, 40 y 52. Permite tramitar simultáneamente en una sola MTD la vivienda, la planta fotovoltaica y el punto de recarga con modulación por excedentes.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": True,
        "circuitos": [
            {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora y Lavavajillas", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Auxiliares", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"},
            {"nombre": "C9 - Climatización Inverter", "potencia": 4500, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.12, "norma": "ITC-BT-25"},
            {"nombre": "C13 - Recarga VE con sensor SPL / Excedentes", "potencia": 7360, "pia": 32, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 18, "cdt": 0.72, "norma": "ITC-BT-52"},
            {"nombre": "Gen Solar AC - Inversor Fotovoltaico Interconectado", "potencia": 5000, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 12, "cdt": 0.58, "norma": "ITC-BT-40"}
        ]
    },
    "local_comercial_monofasico": {
        "id": "local_comercial_monofasico",
        "titulo": "Local Comercial Ordinario Monofásico (Oficina/Tienda - 9.200 W - 230V - IGA 40A)",
        "categoria": "🏢 Locales Comerciales Ordinarios (ITC-BT-10 / 28)",
        "potencia_inst": 9200.0,
        "potencia_max": 9200.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Módulo de Medida / CPM en Fachada (ITC-BT-13)",
        "di_cable": "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV",
        "di_tubo": "Tubo M40 libre de halógenos",
        "di_long": 16.0,
        "di_cdt": 0.75,
        "grado": "Comercial / Terciario Ordinario",
        "iga": 40,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "2 x Diferencial 2P 40A / 30mA Clase A Superinmunizados",
        "vtp": "Permanentes + Transitorias Tipo 2 con bobina de emisión",
        "tierra": "Conductor PE 1x16 mm² Cu | Rt ≤ 15 Ω",
        "spl": "No aplica",
        "emp_uso": "Local Comercial Ordinario (Oficina / Tienda / Despacho)",
        "cuando_elegir": "Locales comerciales de comercio menor, despachos u oficinas con ocupación inferior a 50 personas (tiendas de ropa, zapaterías, despachos de asesoría, inmobiliarias) sin maquinaria pesada.",
        "criterios_rebt": "ITC-BT-10.3.3: Mínimo 100 W/m² de superficie útil y mínimo absoluto de 3.450 W. Suministro monofásico estándar hasta 14.490 W (IGA 40A = 9.200 W). No requiere OCA inicial.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado Comercial LED", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.10, "norma": "ITC-BT-28"},
            {"nombre": "C2 - Alumbrado de Emergencia", "potencia": 500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 25, "cdt": 0.40, "norma": "ITC-BT-28"},
            {"nombre": "C3 - Tomas de Fuerza General y Mostrador", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-28"},
            {"nombre": "C4 - Climatización Split / Bomba Calor", "potencia": 5000, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 15, "cdt": 1.05, "norma": "ITC-BT-28"},
            {"nombre": "C5 - Informática, Servidor y TPV", "potencia": 2300, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 15, "cdt": 0.85, "norma": "ITC-BT-28"}
        ]
    },
    "local_comercial_trifasico": {
        "id": "local_comercial_trifasico",
        "titulo": "Local Comercial Trifásico (Comercio/Clima Tri - 17.320 W - 400V - IGA 25A Tri)",
        "categoria": "🏢 Locales Comerciales Ordinarios (ITC-BT-10 / 28)",
        "potencia_inst": 17320.0,
        "potencia_max": 17320.0,
        "tension": "Trifásico (400 V) - 50 Hz",
        "origen": "Línea General de Alimentación / CPM (ITC-BT-14)",
        "di_cable": "4x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV",
        "di_tubo": "Tubo M40 libre de halógenos",
        "di_long": 20.0,
        "di_cdt": 0.65,
        "grado": "Comercial Trifásico",
        "iga": 25,
        "curva": "Curva C (General)",
        "icn": 10.0,
        "dif": "Diferencial Tetrapolar 4P 40A / 30mA Clase A + Bipolares 2P 40A/30mA",
        "vtp": "Permanentes + Transitorias Tipo 2 Tetrapolar con bobina",
        "tierra": "Conductor PE 1x16 mm² Cu | Rt ≤ 10 Ω",
        "spl": "No aplica",
        "emp_uso": "Local Comercial / Nave de Servicios",
        "cuando_elegir": "Comercios o naves con maquinaria trifásica (cámaras de frío, obradores, compresores) o aire acondicionado centralizado trifásico de más de 7 kW.",
        "criterios_rebt": "ITC-BT-10.3.3. Tensión trifásica 400V para equilibrar fases. Legalizable con MTD hasta 100 kW siempre que la ocupación sea inferior a 50 personas.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado Comercial Trifásico Equilibrado", "potencia": 3000, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 22, "cdt": 1.10, "norma": "ITC-BT-28"},
            {"nombre": "C2 - Alumbrado de Emergencia", "potencia": 500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 30, "cdt": 0.45, "norma": "ITC-BT-28"},
            {"nombre": "C3 - Tomas de Fuerza General", "potencia": 4000, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M25", "longitud": 18, "cdt": 1.12, "norma": "ITC-BT-28"},
            {"nombre": "C4 - Climatización Centralizada Trifásica", "potencia": 7500, "pia": 16, "seccion": "4x2.5+TT2.5", "tubo": "M25", "longitud": 15, "cdt": 0.68, "norma": "ITC-BT-28"},
            {"nombre": "C5 - Maquinaria Auxiliar / Compresor / Cuadro Secundario", "potencia": 4500, "pia": 16, "seccion": "4x2.5+TT2.5", "tubo": "M25", "longitud": 16, "cdt": 0.55, "norma": "ITC-BT-28"}
        ]
    },
    "lpc_bar_restaurante": {
        "id": "lpc_bar_restaurante",
        "titulo": "LPC: Bar / Restaurante / Cafetería (27.710 W - 400V - IGA 40A Tri - OCA obligatoria)",
        "categoria": "🍽️ Locales de Pública Concurrencia (LPC - ITC-BT-28)",
        "potencia_inst": 27710.0,
        "potencia_max": 27710.0,
        "tension": "Trifásico (400 V) - 50 Hz",
        "origen": "Línea General de Alimentación / Centralización (ITC-BT-14)",
        "di_cable": "4x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M50 libre de halógenos",
        "di_long": 22.0,
        "di_cdt": 0.72,
        "grado": "Pública Concurrencia (ITC-BT-28)",
        "iga": 40,
        "curva": "Curva C (General)",
        "icn": 10.0,
        "dif": "Diferenciales Tetrapolares 4P 40A / 30mA Clase A Superinmunizados + Bipolares dedicados",
        "vtp": "Permanentes + Transitorias Tipo 2 con bobina y corte omnipolar general",
        "tierra": "Conductor PE 1x16 mm² Cu | Anillo cimentación Rt ≤ 10 Ω",
        "spl": "No aplica",
        "emp_uso": "Local de Pública Concurrencia: Bar / Restaurante / Cafetería",
        "cuando_elegir": "Actividades de hostelería (bares, cafeterías, restaurantes, pizzerías, pubs). Potencia estándar en la Región de Murcia: 27,7 kW a 400V (IGA 40A).",
        "criterios_rebt": "ITC-BT-28: Cables obligatoriamente AS libres de halógenos en TODO el local. Doble línea de alumbrado en zonas de público. Alumbrado de emergencia ≥ 5 lux en cuadros. Enclavamiento de corte de gas en campana extractora. Tramitable por MTD hasta 100 kW. INSPECCIÓN INICIAL OBLIGATORIA POR OCA.",
        "alerta_lpc": True,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado Bar / Salón Comedor - Línea A (Cables AS)", "potencia": 1500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 0.85, "norma": "ITC-BT-28"},
            {"nombre": "C2 - Alumbrado Bar / Salón Comedor - Línea B (Doble línea ITC-BT-28)", "potencia": 1500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 20, "cdt": 0.92, "norma": "ITC-BT-28"},
            {"nombre": "C3 - Alumbrado Cocina y Almacén", "potencia": 1000, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 14, "cdt": 0.65, "norma": "ITC-BT-28"},
            {"nombre": "C4 - Alumbrado de Emergencia y Evacuación", "potencia": 500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 25, "cdt": 0.40, "norma": "ITC-BT-28"},
            {"nombre": "C5 - Tomas Mostrador, TPV y Barra", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-28"},
            {"nombre": "C6 - Tomas Cocina y Pequeño Electrodoméstico", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.95, "norma": "ITC-BT-28"},
            {"nombre": "C7 - Cocina Industrial / Freidoras / Plancha Trifásica", "potencia": 8000, "pia": 20, "seccion": "4x4.0+TT4.0", "tubo": "M25", "longitud": 14, "cdt": 0.72, "norma": "ITC-BT-28"},
            {"nombre": "C8 - Extracción Campana con Enclavamiento Corte Gas", "potencia": 2000, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 16, "cdt": 0.88, "norma": "ITC-BT-28"},
            {"nombre": "C9 - Cámaras Frigoríficas y Botelleros", "potencia": 3000, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 15, "cdt": 0.98, "norma": "ITC-BT-28"},
            {"nombre": "C10 - Climatización Centralizada Trifásica Salón", "potencia": 8000, "pia": 20, "seccion": "4x4.0+TT4.0", "tubo": "M25", "longitud": 16, "cdt": 0.82, "norma": "ITC-BT-28"}
        ]
    },
    "lpc_academia_clinica": {
        "id": "lpc_academia_clinica",
        "titulo": "LPC: Academia / Clínica / Centro de Enseñanza (>50 pers. - 17.320 W - 400V - OCA)",
        "categoria": "🍽️ Locales de Pública Concurrencia (LPC - ITC-BT-28)",
        "potencia_inst": 17320.0,
        "potencia_max": 17320.0,
        "tension": "Trifásico (400 V) - 50 Hz",
        "origen": "Línea General de Alimentación / Centralización (ITC-BT-14)",
        "di_cable": "4x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M40 libre de halógenos",
        "di_long": 20.0,
        "di_cdt": 0.65,
        "grado": "Pública Concurrencia (ITC-BT-28)",
        "iga": 25,
        "curva": "Curva C (General)",
        "icn": 10.0,
        "dif": "Diferenciales 4P y 2P 40A / 30mA Clase A Superinmunizados",
        "vtp": "Permanentes + Transitorias Tipo 2 con bobina",
        "tierra": "Conductor PE 1x16 mm² Cu | Rt ≤ 10 Ω",
        "spl": "No aplica",
        "emp_uso": "Local de Pública Concurrencia: Academia / Clínica / Centro de Formación",
        "cuando_elegir": "Centros docentes, autoescuelas, academias de idiomas, policlínicas o despachos médicos donde el aforo supera las 50 personas.",
        "criterios_rebt": "ITC-BT-28: Clasificado como Pública Concurrencia por aforo. Obligatorio cables no propagadores de incendio y libres de halógenos (AS), doble línea de alumbrado, alumbrado de emergencia e inspección inicial por OCA.",
        "alerta_lpc": True,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado Aulas / Consultas - Línea A (AS)", "potencia": 2000, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 0.95, "norma": "ITC-BT-28"},
            {"nombre": "C2 - Alumbrado Aulas / Pasillos - Línea B (Doble línea ITC-BT-28)", "potencia": 2000, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 20, "cdt": 1.05, "norma": "ITC-BT-28"},
            {"nombre": "C3 - Alumbrado de Emergencia y Rutas Evacuación", "potencia": 500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 25, "cdt": 0.45, "norma": "ITC-BT-28"},
            {"nombre": "C4 - Tomas de Uso General y Pasillos", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-28"},
            {"nombre": "C5 - Tomas Informática y Equipamiento Específico", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 16, "cdt": 1.02, "norma": "ITC-BT-28"},
            {"nombre": "C6 - Climatización Centralizada Trifásica Aulas", "potencia": 6500, "pia": 16, "seccion": "4x2.5+TT2.5", "tubo": "M25", "longitud": 18, "cdt": 0.72, "norma": "ITC-BT-28"}
        ]
    },
    "lpc_gimnasio": {
        "id": "lpc_gimnasio",
        "titulo": "LPC: Gimnasio / Polideportivo con Duchas (20.780 W - 400V - IGA 32A Tri - OCA)",
        "categoria": "🍽️ Locales de Pública Concurrencia (LPC - ITC-BT-28)",
        "potencia_inst": 20780.0,
        "potencia_max": 20780.0,
        "tension": "Trifásico (400 V) - 50 Hz",
        "origen": "Línea General de Alimentación / CPM (ITC-BT-14)",
        "di_cable": "4x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M40 libre de halógenos",
        "di_long": 20.0,
        "di_cdt": 0.68,
        "grado": "Pública Concurrencia (ITC-BT-28)",
        "iga": 32,
        "curva": "Curva C (General)",
        "icn": 10.0,
        "dif": "Diferenciales 4P y 2P 40A / 30mA Clase A Superinmunizados",
        "vtp": "Permanentes + Transitorias Tipo 2 con bobina",
        "tierra": "Conductor PE 1x16 mm² Cu | Rt ≤ 10 Ω",
        "spl": "No aplica",
        "emp_uso": "Local de Pública Concurrencia: Gimnasio / Centro Deportivo",
        "cuando_elegir": "Centros deportivos, boxes de crossfit, gimnasios con vestuarios y duchas colectivas que demandan gran potencia para termos de ACS y ventilación forzada.",
        "criterios_rebt": "ITC-BT-28 e ITC-BT-30 (locales mojados en vestuarios). Cables AS libres de halógenos, doble circuito de alumbrado, termos trifásicos con diferencial 30 mA clase A y renovación RITE. Requiere OCA inicial.",
        "alerta_lpc": True,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Alumbrado Salas Fitness - Línea A (AS)", "potencia": 1800, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 20, "cdt": 0.95, "norma": "ITC-BT-28"},
            {"nombre": "C2 - Alumbrado Salas y Pasillos - Línea B (AS)", "potencia": 1800, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 22, "cdt": 1.05, "norma": "ITC-BT-28"},
            {"nombre": "C3 - Alumbrado de Emergencia y Evacuación", "potencia": 500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 28, "cdt": 0.42, "norma": "ITC-BT-28"},
            {"nombre": "C4 - Termos Eléctricos ACS Vestuarios Colectivos", "potencia": 6000, "pia": 25, "seccion": "4x4.0+TT4.0", "tubo": "M25", "longitud": 15, "cdt": 0.65, "norma": "ITC-BT-28"},
            {"nombre": "C5 - Ventilación Forzada y Renovación Aire RITE", "potencia": 2500, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 18, "cdt": 0.92, "norma": "ITC-BT-28"},
            {"nombre": "C6 - Climatización Centralizada Trifásica", "potencia": 7500, "pia": 16, "seccion": "4x2.5+TT2.5", "tubo": "M25", "longitud": 16, "cdt": 0.72, "norma": "ITC-BT-28"},
            {"nombre": "C7 - Tomas de Corriente Máquinas y Recepción", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.25, "norma": "ITC-BT-28"}
        ]
    },
    "obra_provisional": {
        "id": "obra_provisional",
        "titulo": "Instalación Provisional de Obra (ITC-BT-33 - 15.000 W - 400V)",
        "categoria": "🏗️ Obras y Líneas de Distribución",
        "potencia_inst": 15000.0,
        "potencia_max": 15000.0,
        "tension": "Trifásico (400 V) - 50 Hz",
        "origen": "Acometida Provisional desde Red Distribuidora (CPM / CGP Intemperie)",
        "di_cable": "4x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)",
        "di_tubo": "Tubo M40 intemperie resistente a impactos IK09",
        "di_long": 15.0,
        "di_cdt": 0.52,
        "grado": "Provisional de Obra (ITC-BT-33)",
        "iga": 40,
        "curva": "Curva D",
        "icn": 10.0,
        "dif": "Diferencial 4P 40A / 30mA Clase A Superinmunizado + Seta Parada Emergencia Exterior",
        "vtp": "Permanentes + Transitorias Tipo 2 con corte omnipolar y bobina de disparo",
        "tierra": "Pica de puesta a tierra independiente de obra (Rt ≤ 15 Ω) | Conductor PE 1x16 mm² Cu",
        "spl": "No aplica",
        "emp_uso": "Instalación Provisional y Temporal de Obras (ITC-BT-33)",
        "cuando_elegir": "Suministros de electricidad temporales para obras de edificación o reformas con tomas industriales normalizadas CETAC.",
        "criterios_rebt": "ITC-BT-33: Cuadro con envolvente mínimo IP44 e IK08, tomas con clavijas industriales CETAC UNE-EN 60309, interruptores diferenciales clase A de 30 mA y pulsador exterior de parada de emergencia con enclavamiento mecánico.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "C1 - Toma CETAC Trifásica 32A 3P+N+T (Grúa / Maquinaria)", "potencia": 10000, "pia": 32, "seccion": "4x6.0+TT6.0", "tubo": "M32", "longitud": 15, "cdt": 0.65, "norma": "ITC-BT-33"},
            {"nombre": "C2 - Toma CETAC Trifásica 16A 3P+N+T (Hormigonera / Elevador)", "potencia": 5000, "pia": 16, "seccion": "4x2.5+TT2.5", "tubo": "M25", "longitud": 15, "cdt": 0.85, "norma": "ITC-BT-33"},
            {"nombre": "C3 - Tomas CETAC/Schuko Monofásicas 16A (Herramientas)", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.78, "norma": "ITC-BT-33"},
            {"nombre": "C4 - Alumbrado de Seguridad y Balizamiento de Obra", "potencia": 1500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 20, "cdt": 0.60, "norma": "ITC-BT-33"}
        ]
    },
    "linea_general_alimentacion": {
        "id": "linea_general_alimentacion",
        "titulo": "Línea General de Alimentación LGA (ITC-BT-14 - 43.600 W - 400V)",
        "categoria": "🏗️ Obras y Líneas de Distribución",
        "potencia_inst": 43600.0,
        "potencia_max": 50000.0,
        "tension": "Trifásico (400 V) - 50 Hz",
        "origen": "Caja General de Protección (CGP / ITC-BT-13)",
        "di_cable": "3x50/25 mm² Al/Cu RZ1-K 0.6/1kV",
        "di_tubo": "Conducto / Tubo M110 libre de halógenos",
        "di_long": 15.0,
        "di_cdt": 0.42,
        "grado": "Comercial / Edificio",
        "iga": 63,
        "curva": "Curva C (General)",
        "icn": 15.0,
        "dif": "Protección General con Toroidal / Relé electrónico",
        "vtp": "Protección contra sobretensiones Tipo 1+2",
        "tierra": "Línea principal PE 1x35 mm² Cu | Rt ≤ 10 Ω",
        "spl": "No aplica",
        "emp_uso": "Línea General de Alimentación (ITC-BT-14)",
        "cuando_elegir": "Línea que enlaza la CGP con la centralización de contadores de un edificio residencial, terciario o comercial.",
        "criterios_rebt": "ITC-BT-14: Cables no propagadores de incendio y libres de halógenos. Caída de tensión máxima admisible de 0,5% para contadores totalmente concentrados.",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "Línea General LGA Centralización", "potencia": 43600, "pia": 63, "seccion": "3x50+25+TT25", "tubo": "M110", "longitud": 15, "cdt": 0.42, "norma": "ITC-BT-14"}
        ]
    },
    "derivacion_individual": {
        "id": "derivacion_individual",
        "titulo": "Derivación Individual DI (ITC-BT-15 - 9.200 W - 230V)",
        "categoria": "🏗️ Obras y Líneas de Distribución",
        "potencia_inst": 9200.0,
        "potencia_max": 14490.0,
        "tension": "Monofásico (230 V) - 50 Hz",
        "origen": "Contador / Centralización de Contadores (ITC-BT-16)",
        "di_cable": "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV",
        "di_tubo": "Tubo M40 libre de halógenos (ITC-BT-15)",
        "di_long": 20.0,
        "di_cdt": 0.85,
        "grado": "Elevada",
        "iga": 40,
        "curva": "Curva C (General)",
        "icn": 6.0,
        "dif": "Diferencial 2P 40A / 30mA Clase A Superinmunizado",
        "vtp": "Permanentes + Transitorias Tipo 2 con bobina de emisión",
        "tierra": "Conductor PE 1x16 mm² Cu | Rt ≤ 15 Ω",
        "spl": "No aplica",
        "emp_uso": "Derivación Individual B.T. (ITC-BT-15)",
        "cuando_elegir": "Renovación o adecuación de la línea que une el contador individual con el cuadro interior del usuario.",
        "criterios_rebt": "ITC-BT-15: Sección mínima de cobre 6 mm² (16 mm² recomendada en Murcia). Caída de tensión máx. 1,5%. Tubo mínimo exterior M32 (M40 para 16 mm²).",
        "alerta_lpc": False,
        "alerta_garaje": False,
        "alerta_solar": False,
        "circuitos": [
            {"nombre": "Línea Derivación Individual", "potencia": 9200, "pia": 40, "seccion": "2x16+TT16", "tubo": "M40", "longitud": 20, "cdt": 0.85, "norma": "ITC-BT-15"}
        ]
    }
}

OPCIONES_TIPO_INSTALACION = [
    "⚪ -- Seleccionar Tipo de Instalación (En Blanco) --",
    # 🏡 VIVIENDAS RESIDENCIALES
    "🏡 Vivienda Básica (5.750 W - 230V Monofásica - IGA 25A)",
    "🏡 Vivienda Elevada - Climatización / Aire Acondicionado (9.200 W - 230V - IGA 40A)",
    "🏡 Vivienda Elevada - Aerotermia + Climatización (11.500 W - 230V - IGA 50A)",
    "🏡 Vivienda Elevada - Máxima Monofásica (14.490 W - 230V - IGA 63A)",
    "🏡 Vivienda Unifamiliar / Chalet Trifásica (17.320 W - 400V - IGA 25A Tri)",
    # 🚗 VEHÍCULO ELÉCTRICO IRVE
    "🚗 IRVE - Garaje Comunitario (Esquema 2 - 7.360 W - 230V - IGA 32A/40A)",
    "🚗 IRVE - Trifásico Comercial / Rápido (22.000 W - 400V - IGA 32A Tri)",
    "🚗 Vivienda con Recarga VE Integrada (11.500 W - 230V - IGA 50A con SPL)",
    # ☀️ AUTOCONSUMO FOTOVOLTAICO
    "☀️ Autoconsumo Solar Fotovoltaico (5.000 W Inversor - 230V - IGA 25A)",
    "☀️ Combo: Vivienda + Solar Fotovoltaica (5 kW) + IRVE (7.36 kW)",
    # 🏢 LOCALES COMERCIALES ORDINARIOS
    "🏢 Local Comercial Ordinario Monofásico (Oficina/Tienda - 9.200 W - 230V - IGA 40A)",
    "🏢 Local Comercial Trifásico (Comercio/Clima Tri - 17.320 W - 400V - IGA 25A Tri)",
    # 🍽️ LOCALES DE PÚBLICA CONCURRENCIA (LPC)
    "🍽️ LPC: Bar / Restaurante / Cafetería (27.710 W - 400V - IGA 40A Tri - OCA obligatoria)",
    "🎓 LPC: Academia / Clínica / Centro de Enseñanza (>50 pers. - 17.320 W - 400V - OCA)",
    "🏋️ LPC: Gimnasio / Polideportivo con Duchas (20.780 W - 400V - IGA 32A Tri - OCA)",
    # 🏗️ OBRAS Y LÍNEAS DE DISTRIBUCIÓN
    "🏗️ Instalación Provisional de Obra (ITC-BT-33 - 15.000 W - 400V)",
    "⚡ Línea General de Alimentación LGA (ITC-BT-14 - 43.600 W - 400V)",
    "🔌 Derivación Individual DI (ITC-BT-15 - 9.200 W - 230V)"
]

OPCIONES_TRAMITE = [
    "🆕 Nueva Instalación (Alta Inicial)",
    "🏗️ Instalación Temporal de Obra (Suministro Provisional)",
    "📈 Ampliación de Potencia / Cargas",
    "🔧 Modificación de Importancia / Reforma",
    "🔄 Adecuación Reglamentaria (REBT)",
    "📋 Boletín de Reconocimiento / Cambio Titular"
]

def normalizar_opcion_tipo_inst(val: str) -> str:
    """Garantiza que la opción seleccionada pertenezca estrictamente a OPCIONES_TIPO_INSTALACION."""
    if not val or val in OPCIONES_TIPO_INSTALACION:
        return val or OPCIONES_TIPO_INSTALACION[0]
    
    val_low = str(val).lower()

    # 1. Búsqueda directa por coincidencia parcial en OPCIONES_TIPO_INSTALACION
    for opt in OPCIONES_TIPO_INSTALACION[1:]:
        if val_low in opt.lower() or opt.lower() in val_low:
            return opt

    # 2. Búsqueda por palabras clave REBT
    if "aerotermia" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "aerotermia" in o.lower()][0]
    if "máxima" in val_low or "maxima" in val_low or "14.49" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "máxima" in o.lower()][0]
    if "chalet" in val_low or ("trifásic" in val_low and "vivienda" in val_low):
        return [o for o in OPCIONES_TIPO_INSTALACION if "chalet" in o.lower()][0]
    if "combo" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "combo" in o.lower()][0]
    if "solar" in val_low or "fotovoltaic" in val_low or "autoconsumo" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "solar" in o.lower() and "combo" not in o.lower()][0]
    if "irve" in val_low or "recarga" in val_low or "vehículo" in val_low or "vehiculo" in val_low:
        if "trifásic" in val_low or "22.000" in val_low or "rápido" in val_low:
            return [o for o in OPCIONES_TIPO_INSTALACION if "trifásico comercial" in o.lower()][0]
        if "integrada" in val_low:
            return [o for o in OPCIONES_TIPO_INSTALACION if "integrada" in o.lower()][0]
        return [o for o in OPCIONES_TIPO_INSTALACION if "garaje comunitario" in o.lower()][0]
    if "bar" in val_low or "restaurante" in val_low or "cafetería" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "bar" in o.lower()][0]
    if "academia" in val_low or "clínica" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "academia" in o.lower()][0]
    if "gimnasio" in val_low or "polideportivo" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "gimnasio" in o.lower()][0]
    if "obra" in val_low or "provisional" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "obra" in o.lower()][0]
    if "lga" in val_low or "alimentación" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "lga" in o.lower()][0]
    if "derivación" in val_low or " di " in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "derivación" in o.lower()][0]
    if "clima" in val_low or "elevada" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "climatización" in o.lower()][0]
    if "vivienda" in val_low or "básica" in val_low:
        return [o for o in OPCIONES_TIPO_INSTALACION if "básica" in o.lower()][0]

    return OPCIONES_TIPO_INSTALACION[0]

def normalizar_opcion_tramite(val: str) -> str:
    """Garantiza que la opción seleccionada pertenezca estrictamente a OPCIONES_TRAMITE."""
    if not val or val in OPCIONES_TRAMITE:
        return val or OPCIONES_TRAMITE[0]
    val_low = str(val).lower()
    for opt in OPCIONES_TRAMITE:
        if ("obra" in val_low and "obra" in opt.lower()) or \
           ("alta" in val_low and "alta" in opt.lower()) or \
           ("ampliación" in val_low and "ampliación" in opt.lower()) or \
           ("reforma" in val_low and "reforma" in opt.lower()) or \
           ("adecuación" in val_low and "adecuación" in opt.lower()) or \
           ("reconocimiento" in val_low and "reconocimiento" in opt.lower()):
            return opt
    return OPCIONES_TRAMITE[0]

def obtener_info_plantilla(tipo: str) -> dict:
    """Retorna la ficha de metadatos técnicos de la plantilla seleccionada o None si es en blanco."""
    if not tipo or "Blanco" in tipo or "Seleccionar" in tipo or tipo.startswith("⚪"):
        return None
    
    t_low = tipo.lower()
    
    # 1. Aerotermia
    if "aerotermia" in t_low:
        return CATALOGO_PLANTILLAS_MTD["vivienda_elevada_aerotermia"]
    
    # 2. Máxima monofásica (14.49 kW / 14490)
    if "máxima" in t_low or "maxima" in t_low or "14.49" in t_low or "14490" in t_low:
        return CATALOGO_PLANTILLAS_MTD["vivienda_elevada_max_mono"]
    
    # 3. Chalet / Unifamiliar trifásica
    if "chalet" in t_low or ("trifásic" in t_low and "vivienda" in t_low):
        return CATALOGO_PLANTILLAS_MTD["vivienda_unifamiliar_chalet_tri"]
        
    # 4. Combo Solar + IRVE
    if "combo" in t_low or ("solar" in t_low and "irve" in t_low):
        return CATALOGO_PLANTILLAS_MTD["combo_vivienda_solar_irve"]
        
    # 5. Vivienda con IRVE integrado
    if "vivienda" in t_low and ("irve" in t_low or "recarga" in t_low or "coche" in t_low):
        return CATALOGO_PLANTILLAS_MTD["vivienda_con_irve_integrado"]
        
    # 6. IRVE Trifásico comercial
    if ("irve" in t_low or "recarga" in t_low) and ("trifásic" in t_low or "22.000" in t_low or "22000" in t_low or "rápido" in t_low or "rapido" in t_low):
        return CATALOGO_PLANTILLAS_MTD["irve_trifasico_comercial"]
        
    # 7. IRVE Garaje Comunitario
    if "irve" in t_low or "recarga" in t_low or "vehículo" in t_low or "vehiculo" in t_low:
        return CATALOGO_PLANTILLAS_MTD["irve_garaje_comunitario"]
        
    # 8. Fotovoltaica
    if "fotovoltaic" in t_low or "autoconsumo" in t_low or "solar" in t_low:
        return CATALOGO_PLANTILLAS_MTD["autoconsumo_solar_fv"]
        
    # 9. Pública Concurrencia (LPC)
    if "bar" in t_low or "restaurante" in t_low or "cafetería" in t_low or "cafeteria" in t_low or "27.710" in t_low:
        return CATALOGO_PLANTILLAS_MTD["lpc_bar_restaurante"]
    if "academia" in t_low or "clínica" in t_low or "clinica" in t_low or "enseñanza" in t_low:
        return CATALOGO_PLANTILLAS_MTD["lpc_academia_clinica"]
    if "gimnasio" in t_low or "polideportivo" in t_low or "20.780" in t_low:
        return CATALOGO_PLANTILLAS_MTD["lpc_gimnasio"]
        
    # 10. Locales Comerciales Ordinarios
    if ("local" in t_low or "oficina" in t_low or "tienda" in t_low) and ("monofásic" in t_low or "9.200" in t_low or "9200" in t_low or "ordinario" in t_low):
        return CATALOGO_PLANTILLAS_MTD["local_comercial_monofasico"]
    if "local" in t_low or "comercial" in t_low or "nave" in t_low:
        return CATALOGO_PLANTILLAS_MTD["local_comercial_trifasico"]
        
    # 11. Obras provisionales
    if "obra" in t_low or "provisional" in t_low or "itc-bt-33" in t_low:
        return CATALOGO_PLANTILLAS_MTD["obra_provisional"]
        
    # 12. Redes de distribución LGA / DI
    if "lga" in t_low or "alimentación" in t_low or "alimentacion" in t_low or "itc-bt-14" in t_low:
        return CATALOGO_PLANTILLAS_MTD["linea_general_alimentacion"]
    if "derivación" in t_low or "derivacion" in t_low or " di " in t_low or "itc-bt-15" in t_low:
        return CATALOGO_PLANTILLAS_MTD["derivacion_individual"]
        
    # 13. Viviendas Elevada estándar
    if "elevada" in t_low or "clima" in t_low or "calefacción" in t_low or "domótica" in t_low:
        return CATALOGO_PLANTILLAS_MTD["vivienda_elevada_clima"]
        
    # 14. Vivienda Básica estándar
    if "vivienda" in t_low or "residencial" in t_low:
        return CATALOGO_PLANTILLAS_MTD["vivienda_basica"]
        
    return CATALOGO_PLANTILLAS_MTD.get("vivienda_basica")

def cargar_plantilla_por_tipo(tipo: str):
    """
    Rellena automáticamente los parámetros técnicos y circuitos según el tipo de instalación reglamentaria.
    Si tipo es en blanco o no seleccionado, inicializa los campos técnicos limpios y sin circuitos.
    """
    info = obtener_info_plantilla(tipo)
    if not info:
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
        st.session_state["mtd_in_desc_instalacion"] = ""
        st.session_state["mtd_circuitos"] = []
        return

    st.session_state["mtd_in_pot_inst"] = float(info["potencia_inst"])
    st.session_state["mtd_in_pot_max"] = float(info["potencia_max"])
    st.session_state["mtd_in_tension"] = str(info["tension"])
    st.session_state["mtd_in_origen"] = str(info["origen"])
    st.session_state["mtd_in_di_cable"] = str(info["di_cable"])
    st.session_state["mtd_in_di_tubo"] = str(info["di_tubo"])
    st.session_state["mtd_in_di_long"] = float(info["di_long"])
    st.session_state["mtd_in_di_cdt"] = float(info["di_cdt"])
    st.session_state["mtd_in_grado"] = str(info["grado"])
    st.session_state["mtd_in_iga"] = int(info["iga"])
    st.session_state["mtd_in_curva"] = str(info["curva"])
    st.session_state["mtd_in_icn"] = float(info["icn"])
    st.session_state["mtd_in_dif"] = str(info["dif"])
    st.session_state["mtd_in_vtp"] = str(info["vtp"])
    st.session_state["mtd_in_tierra"] = str(info["tierra"])
    st.session_state["mtd_in_spl"] = str(info["spl"])
    st.session_state["mtd_in_emp_uso"] = str(info["emp_uso"])
    st.session_state["mtd_circuitos"] = copy.deepcopy(info["circuitos"])
    p_inst = float(info["potencia_inst"])
    tens_p = str(info["tension"]).split(' ')[0]
    nom_p = info.get("titulo", tipo).split('(')[0].replace('☀️', '').replace('🏗️', '').replace('🚗', '').replace('🏡', '').replace('🏢', '').replace('🍽️', '').replace('🏋️', '').replace('🎓', '').strip()
    p_str = f"{p_inst:,.0f}".replace(",", ".")
    st.session_state["mtd_in_desc_instalacion"] = (
        f"Instalación eléctrica en baja tensión para {nom_p} con potencia prevista de {p_str} W a tensión nominal de {tens_p}. "
        f"Cuadro CGMP con IGA de {info['iga']}A (Icn={info['icn']:.0f}kA), protección contra sobretensiones transitorias y permanentes Tipo 2 (ITC-BT-23), "
        f"interruptor diferencial 30mA Clase A (ITC-BT-24) y derivación individual {info['di_cable']} bajo {info['di_tubo']} con caída de tensión calculada ΔV = {info['di_cdt']:.2f}% (conforme REBT ITC-BT-15)."
    )

def aplicar_datos_cliente_a_formulario(cli_obj: dict):
    """Vuelca los datos del cliente de CRM en los campos del formulario"""
    if not cli_obj:
        return
    st.session_state["mtd_in_tit_nom"] = cli_obj.get("nombre_completo") or ""
    st.session_state["mtd_in_tit_nif"] = cli_obj.get("nif_cif") or ""
    st.session_state["mtd_in_tit_tel"] = cli_obj.get("telefono") or ""
    st.session_state["mtd_in_tit_email"] = cli_obj.get("email") or ""
    st.session_state["mtd_in_emp_dir"] = cli_obj.get("direccion_suministro") or cli_obj.get("direccion") or ""
    st.session_state["mtd_in_emp_cups"] = cli_obj.get("cups") or ""
    
    loc = str(cli_obj.get("localidad") or "Murcia")
    for m in MUNICIPIOS_MURCIA_OFICIALES:
        if m.lower() in loc.lower() or loc.lower() in m.lower():
            st.session_state["mtd_in_emp_muni"] = m
            break
    
    tipo_inm = cli_obj.get("tipo_inmueble") or ""
    if tipo_inm:
        st.session_state["mtd_in_emp_uso"] = tipo_inm

def renderizar():
    es_oscuro = st.session_state.get("tema_modo", "solar") == "oscuro"
    tab_list_bg = "#0b1329" if es_oscuro else "#f8fafc"
    tab_btn_bg = "#1e293b" if es_oscuro else "#ffffff"
    tab_btn_border = "#334155" if es_oscuro else "#cbd5e1"
    tab_btn_color = "#cbd5e1" if es_oscuro else "#334155"
    tab_btn_hover_bg = "#334155" if es_oscuro else "#e0f2fe"
    tab_btn_hover_color = "#38bdf8" if es_oscuro else "#0369a1"

    st.markdown(f"""
    <style>
    /* Desplegables BaseWeb Popovers: aseguramos que el menú nunca corte las descripciones */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div {{
        min-width: 650px !important;
        max-width: 96vw !important;
        width: max-content !important;
        z-index: 999999 !important;
    }}

    div[data-baseweb="popover"] ul[role="listbox"] {{
        min-width: 100% !important;
        max-width: 96vw !important;
        max-height: 480px !important;
        padding: 6px !important;
    }}

    div[data-baseweb="popover"] li[role="option"] {{
        white-space: normal !important;
        word-break: normal !important;
        overflow-wrap: break-word !important;
        overflow: visible !important;
        text-overflow: unset !important;
        padding: 10px 14px !important;
        font-size: 13.5px !important;
        line-height: 1.45 !important;
        border-bottom: 1px solid {'#1e293b' if es_oscuro else '#f1f5f9'} !important;
        border-radius: 6px !important;
        margin-bottom: 2px !important;
    }}

    div[data-baseweb="popover"] li[role="option"] > div,
    div[data-baseweb="popover"] li[role="option"] span {{
        white-space: normal !important;
        word-break: normal !important;
        overflow-wrap: break-word !important;
        overflow: visible !important;
        text-overflow: unset !important;
        display: block !important;
    }}

    div[data-baseweb="select"] {{
        width: 100% !important;
    }}

    div[data-baseweb="select"] > div {{
        min-height: 42px !important;
    }}

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div {{
        white-space: normal !important;
        word-break: break-word !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }}

    /* Barra de Pestañas (st.tabs) Mejorada y de Alto Contraste */
    div[data-baseweb="tab-list"] {{
        gap: 6px !important;
        background-color: {tab_list_bg} !important;
        padding: 8px 10px 4px 10px !important;
        border-radius: 10px 10px 0 0 !important;
        border-bottom: 3px solid #0284c7 !important;
        display: flex !important;
        flex-wrap: wrap !important;
    }}

    button[data-baseweb="tab"] {{
        background-color: {tab_btn_bg} !important;
        border: 1px solid {tab_btn_border} !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 9px 15px !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        color: {tab_btn_color} !important;
        transition: all 0.15s ease-in-out !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
    }}

    button[data-baseweb="tab"]:hover {{
        background-color: {tab_btn_hover_bg} !important;
        color: {tab_btn_hover_color} !important;
        border-color: #38bdf8 !important;
    }}

    button[data-baseweb="tab"][aria-selected="true"] {{
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border-color: #0284c7 !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.3) !important;
    }}

    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span,
    button[data-baseweb="tab"][aria-selected="true"] div {{
        color: #ffffff !important;
    }}
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
            st.session_state["_mtd_cargar_plantilla_pendiente"] = "⚪ -- Seleccionar Tipo de Instalación (En Blanco) --"
            st.session_state["_mtd_last_loaded_tipo_inst"] = "⚪ -- Seleccionar Tipo de Instalación (En Blanco) --"
            st.session_state["_mtd_msg_exito_carga"] = "✅ MTD reiniciada en blanco."
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
    # 0. APLICAR CARGAS PENDIENTES DE PROYECTO O PLANTILLA ANTES DE INSTANCIAR WIDGETS
    # =========================================================================
    if "_mtd_cargar_datos_pendientes" in st.session_state:
        pend = st.session_state.pop("_mtd_cargar_datos_pendientes", {})
        if isinstance(pend, dict):
            for k, v in pend.items():
                if k == "mtd_tipo_inst_sel":
                    st.session_state[k] = normalizar_opcion_tipo_inst(str(v))
                elif k == "mtd_tipo_tram_sel":
                    st.session_state[k] = normalizar_opcion_tramite(str(v))
                else:
                    st.session_state[k] = v
            st.session_state["_mtd_last_loaded_tipo_inst"] = st.session_state.get("mtd_tipo_inst_sel")

    tipo_pend = st.session_state.pop("_mtd_cargar_plantilla_pendiente", None)
    if tipo_pend:
        norm_tipo = normalizar_opcion_tipo_inst(tipo_pend)
        st.session_state["mtd_tipo_inst_sel"] = norm_tipo
        cargar_plantilla_por_tipo(norm_tipo)
        st.session_state["_mtd_last_loaded_tipo_inst"] = norm_tipo

    msg_exito = st.session_state.pop("_mtd_msg_exito_carga", None)
    if msg_exito:
        st.success(msg_exito)

    # =========================================================================
    # 1. EXPEDIENTE, CLIENTE (CRM) Y GUARDADO / CARGA DE MEMORIAS
    # =========================================================================
    st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">👤 1. Expediente, Cliente (CRM) y Gestión de Memorias Guardadas</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        # Callback para auto-sincronizar instantáneamente al cambiar la selección en el desplegable
        def _cb_cambio_tipo_instalacion():
            sel_nuevo = st.session_state.get("mtd_tipo_inst_sel")
            if sel_nuevo:
                cargar_plantilla_por_tipo(sel_nuevo)
                st.session_state["_mtd_last_loaded_tipo_inst"] = sel_nuevo
                if sel_nuevo.startswith("⚪") or "Blanco" in sel_nuevo:
                    st.session_state["_mtd_msg_exito_carga"] = "✅ MTD reiniciada en blanco."
                else:
                    nom_c = sel_nuevo.split('(')[0].strip()
                    st.session_state["_mtd_msg_exito_carga"] = f"✅ ¡Plantilla técnica oficial aplicada para {nom_c}! Potencia, IGA, DI y circuitos auto-sincronizados."

        # Auto-sincronización de seguridad si hay una plantilla elegida pero sus valores aún no se cargaron
        tipo_actual = normalizar_opcion_tipo_inst(st.session_state.get("mtd_tipo_inst_sel", OPCIONES_TIPO_INSTALACION[0]))
        st.session_state["mtd_tipo_inst_sel"] = tipo_actual
        if not (tipo_actual.startswith("⚪") or "Blanco" in tipo_actual):
            if st.session_state.get("_mtd_last_loaded_tipo_inst") != tipo_actual:
                if st.session_state.get("mtd_in_pot_inst", 0.0) == 0.0 or st.session_state.get("mtd_in_pot_inst") is None:
                    cargar_plantilla_por_tipo(tipo_actual)
                    st.session_state["_mtd_last_loaded_tipo_inst"] = tipo_actual

        # --- FILA 1: ELECCIÓN DE PLANTILLA TÉCNICA REGLAMENTARIA Y TRÁMITE ---
        col_p_sel, col_p_btn, col_tram = st.columns([3.8, 1.4, 2.2])
        
        with col_p_sel:
            idx_tipo_def = OPCIONES_TIPO_INSTALACION.index(tipo_actual)

            tipo_inst_sel = st.selectbox(
                "📋 Tipo de Instalación y Plantilla Técnica Oficial (REBT):",
                OPCIONES_TIPO_INSTALACION,
                index=idx_tipo_def,
                key="mtd_tipo_inst_sel",
                on_change=_cb_cambio_tipo_instalacion,
                help="Selecciona una plantilla oficial para autorellenar potencias, IGA, cable de derivación individual y circuitos reglamentarios."
            )

        with col_p_btn:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            lbl_btn_plantilla = "🧹 Limpiar MTD" if (tipo_inst_sel.startswith("⚪") or "Blanco" in tipo_inst_sel) else "🔄 Recargar Plantilla"
            if st.button(lbl_btn_plantilla, type="primary" if not tipo_inst_sel.startswith("⚪") else "secondary", use_container_width=True, key="btn_cargar_plantilla_top", help="Vuelve a volcar todos los valores reglamentarios por defecto de esta plantilla"):
                cargar_plantilla_por_tipo(tipo_inst_sel)
                st.session_state["_mtd_last_loaded_tipo_inst"] = tipo_inst_sel
                if tipo_inst_sel.startswith("⚪") or "Blanco" in tipo_inst_sel:
                    st.session_state["_mtd_msg_exito_carga"] = "✅ MTD reiniciada en blanco."
                else:
                    nom_c = tipo_inst_sel.split('(')[0].strip()
                    st.session_state["_mtd_msg_exito_carga"] = f"✅ ¡Plantilla técnica recargada para {nom_c}! (Potencia, IGA, DI y circuitos actualizados)"
                st.rerun()

        with col_tram:
            tram_actual = normalizar_opcion_tramite(st.session_state.get("mtd_tipo_tram_sel", OPCIONES_TRAMITE[0]))
            st.session_state["mtd_tipo_tram_sel"] = tram_actual
            idx_tram_def = OPCIONES_TRAMITE.index(tram_actual)

            tipo_tram_sel = st.selectbox(
                "Carácter de la Instalación / Trámite:",
                OPCIONES_TRAMITE,
                index=idx_tram_def,
                key="mtd_tipo_tram_sel"
            )

        # Separador visual sutil entre Bloque de Plantilla y Bloque de Cliente CRM
        st.markdown("<div style='margin-top: 10px; margin-bottom: 12px; border-top: 1px dashed #cbd5e1;'></div>", unsafe_allow_html=True)

        # --- FILA 2: CLIENTE ASIGNADO (CRM) Y MEMORIAS GUARDADAS ---
        col_c_cli, col_c_mtds = st.columns([1.1, 1.1])
        cli_obj = {}
        with col_c_cli:
            clientes = db_manager.listar_clientes(user_auth["id"])
            if not clientes:
                st.warning("⚠️ No hay clientes registrados en CRM. Puedes crear fichas en el módulo 'Gestión de Clientes'.")
                cli_sel_id = None
            else:
                nombres_cli = {c["id"]: f"👤 {c['nombre_completo']} - {c.get('nif_cif', '')} ({c.get('localidad', 'Murcia')})" for c in clientes}
                
                # Pre-seleccionar si ya viene en session
                idx_sel = 0
                if "cliente_activo_proyecto" in st.session_state and st.session_state["cliente_activo_proyecto"]:
                    c_act = st.session_state["cliente_activo_proyecto"]
                    if c_act.get("id") in nombres_cli:
                        idx_sel = list(nombres_cli.keys()).index(c_act["id"])

                col_cli_sel_box, col_cli_btn_box = st.columns([2.4, 1.3])
                with col_cli_sel_box:
                    cli_sel_id = st.selectbox(
                        "Cliente Asignado (CRM):",
                        options=list(nombres_cli.keys()),
                        format_func=lambda x: nombres_cli[x],
                        index=idx_sel,
                        key="mtd_sel_cliente_crm"
                    )
                    cli_obj = db_manager.obtener_cliente_por_id(cli_sel_id, user_auth["id"]) or {}
                with col_cli_btn_box:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("📋 Cargar Cliente", use_container_width=True, help="Volcar datos de contacto y suministro del cliente al formulario"):
                        aplicar_datos_cliente_a_formulario(cli_obj)
                        st.success(f"✅ Datos de {cli_obj.get('nombre_completo')} volcados a la MTD.")
                        st.rerun()

        with col_c_mtds:
            if 'cli_sel_id' in locals() and cli_sel_id:
                proyectos_mtd_cli = [
                    p for p in db_manager.listar_proyectos_por_cliente(cli_sel_id, user_auth["id"]) 
                    if "Memoria" in p.get("modulo", "") or "MTD" in p.get("modulo", "")
                ]
                if proyectos_mtd_cli:
                    nombres_projs = {p["id"]: f"📂 {p['nombre_proyecto']} ({p.get('fecha_guardado', '')[:10]})" for p in proyectos_mtd_cli}
                    col_proj_sel_box, col_proj_btn_box = st.columns([2.4, 1.3])
                    with col_proj_sel_box:
                        sel_p_id = st.selectbox("MTDs Guardadas del Cliente:", options=list(nombres_projs.keys()), format_func=lambda x: nombres_projs[x], key="sel_mtd_p_cli")
                    with col_proj_btn_box:
                        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("🚀 Cargar MTD", use_container_width=True, help="Cargar esta memoria guardada previamente"):
                            p_datos = db_manager.cargar_proyecto_por_id(sel_p_id, user_auth["id"])
                            if p_datos and "datos" in p_datos:
                                st.session_state["_mtd_cargar_datos_pendientes"] = p_datos["datos"]
                                st.session_state["_mtd_msg_exito_carga"] = f"✅ ¡Memoria '{p_datos.get('nombre_proyecto')}' cargada con éxito!"
                                st.rerun()
                else:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    st.caption("ℹ️ *Este cliente no tiene memorias MTD guardadas aún.*")

        # Ficha Dinámica de Ayuda Técnica de la Plantilla Seleccionada
        info_sel = obtener_info_plantilla(tipo_inst_sel)
        if info_sel:
            st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                col_ay_tit, col_ay_pot = st.columns([2.4, 1.6])
                with col_ay_tit:
                    st.markdown(f"##### 💡 Ficha de Ayuda para Elección: **{info_sel['titulo']}**")
                    st.caption(f"Categoría Oficial: **{info_sel.get('categoria', '')}**")
                    st.markdown(f"**📌 ¿Cuándo elegirla en Murcia?:** {info_sel['cuando_elegir']}")
                with col_ay_pot:
                    p_kw = info_sel['potencia_inst'] / 1000.0
                    st.markdown(
                        f"<div style='background-color:#f1f5f9; border-left:4px solid #0284c7; padding:8px 12px; border-radius:4px; font-size:13px;'>"
                        f"<b>⚡ Potencia de Diseño:</b> {info_sel['potencia_inst']:,.0f} W ({p_kw:.2f} kW)<br>"
                        f"<b>🔌 Tensión:</b> {info_sel['tension'].split(' - ')[0]}<br>"
                        f"<b>🛡️ IGA Cabecera:</b> {info_sel['iga']} A ({info_sel['curva'].split(' ')[0]})<br>"
                        f"<b>📏 Cable DI:</b> {info_sel['di_cable'].split(' ')[0]} Cu | <b>Tubo:</b> {info_sel['di_tubo'].split(' ')[0]}<br>"
                        f"<b>📋 Circuitos:</b> {len(info_sel['circuitos'])} circuitos incluidos"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                
                st.markdown(f"**📜 Prescripción Reglamentaria REBT:** {info_sel['criterios_rebt']}")

                if info_sel.get("alerta_lpc"):
                    st.warning(
                        "🚨 **REQUISITOS OBLIGATORIOS PARA LOCAL DE PÚBLICA CONCURRENCIA (ITC-BT-28):**\n"
                        "1. **Cables de Alta Seguridad (AS):** Obligatoriamente no propagadores del incendio y de reducida emisión de humos (H07Z1-K / RZ1-K) en **toda** la instalación interior.\n"
                        "2. **Doble línea de alumbrado general** en salas con público (si salta un PIA no quedarse a oscuras).\n"
                        "3. **Alumbrado de emergencia:** Mínimo 5 lux en cuadros y 1 lux en rutas de evacuación (autonomía ≥ 1h).\n"
                        "4. **Campana de cocina (si hostelería):** Enclavamiento obligatorio con corte de electroválvula de gas.\n"
                        "5. **INSPECCIÓN INICIAL OBLIGATORIA POR OCA:** Exigida antes de la puesta en servicio oficial y enganche con distribuidora (revisión periódica cada 5 años)."
                    )
                elif info_sel.get("alerta_garaje"):
                    st.warning(
                        "🚨 **REQUISITOS OBLIGATORIOS PARA GARAJE / IRVE (ITC-BT-52 / ITC-BT-29):**\n"
                        "1. **Cables libres de halógenos (AS)** Cca-s1b,d1,a1 obligatorios en todo el trazado por zonas comunes y parking.\n"
                        "2. **Tubo de alta resistencia mecánica:** Mínimo impacto IK08 en garajes comunitarios.\n"
                        "3. **Diferencial específico:** Clase A con detección DC de 6 mA (IEC 62955) o Tipo B.\n"
                        "4. **Comunicación a la Comunidad:** Notificación formal previa según art. 17.5 de la Ley de Propiedad Horizontal."
                    )
                elif info_sel.get("alerta_solar"):
                    st.info(
                        "ℹ️ **REQUISITOS OBLIGATORIOS PARA AUTOCONSUMO SOLAR (ITC-BT-40 / RD 244/2019):**\n"
                        "1. **Protección anti-isla:** Integrada según UNE-EN 50549-1 para desconexión inmediata si cae la red.\n"
                        "2. **Caída de tensión AC:** Diseñar para ≤ 1,0% en la línea de evacuación para evitar bloqueos por sobretensión (>253 V) a pleno sol en Murcia.\n"
                        "3. **Diferencial:** Tipo A o B según prescripción técnica del fabricante del inversor."
                    )

    # Asistente de Decisión y Calculadora de Potencia para Locales Comerciales
    with st.expander("🧮 Asistente de Decisión y Calculadora de Potencia para Locales (ITC-BT-10.3.3 / ITC-BT-28)", expanded=False):
        st.info(
            "💡 **¿Cuándo se debe utilizar esta calculadora?**\n\n"
            "* **En Viviendas:** **NO hace falta usarla.** Las viviendas se rigen por valores reglamentarios fijos: **Básica (5.750 W)** o **Elevada (9.200 W)** según ITC-BT-10.\n"
            "* **En Locales Comerciales, Oficinas, Bares y Clínicas:** **SÍ se debe utilizar.** El REBT (ITC-BT-10.3.3) prohíbe fijar potencias arbitrarias y obliga a justificar un mínimo de **100 W/m² de superficie útil**, más la climatización y maquinaria prevista."
        )
        tab_calc_loc, tab_guia_loc = st.tabs(["📊 Calculadora de Potencia para Locales", "📖 Guía de Selección para el Instalador"])

        with tab_calc_loc:
            col_cl1, col_cl2 = st.columns([1.1, 1.9])
            with col_cl1:
                st.markdown("###### 📏 Datos de Partida del Inmueble:")
                sup_calc = st.number_input("Superficie útil del local (m²):", min_value=5.0, max_value=5000.0, value=80.0, step=5.0, key="in_calc_sup_loc", help="Superficie útil computable según planos o catastro.")
                clima_calc = st.number_input("Potencia estimada Climatización / Frío (W):", min_value=0.0, max_value=60000.0, value=2000.0, step=500.0, key="in_calc_clima_loc", help="Potencia eléctrica de los splits o bomba de calor.")
                maq_calc = st.number_input("Potencia Maquinaria / Cocina / Hornos (W):", min_value=0.0, max_value=100000.0, value=0.0, step=500.0, key="in_calc_maq_loc", help="Dejar en 0 W para tiendas u oficinas corrientes sin maquinaria industrial.")
                act_calc = st.selectbox(
                    "Tipo de Actividad y Afluencia de Público:",
                    [
                        "Local Comercial Ordinario (Tienda, oficina, despacho, aforo < 50 pers.)",
                        "Bar / Restaurante / Cafetería (Hostelería con cocina industrial)",
                        "Academia / Centro Educativo / Clínica (> 50 pers. - Pública Concurrencia)",
                        "Gimnasio / Centro Deportivo con vestuarios y duchas"
                    ],
                    key="in_calc_act_loc"
                )
                pref_red = st.selectbox(
                    "Previsión de Suministro (Tensión):",
                    [
                        "🔄 Automático (Según potencia calculada)",
                        "⚡ Preferir Monofásico (230 V) - Tienda / Despacho estándar (IGA 40A - 9.2 kW)",
                        "🔌 Preferir Trifásico (400 V) - Para maquinaria o clima trifásico (IGA 25A - 17.3 kW)"
                    ],
                    key="in_calc_pref_red"
                )

            with col_cl2:
                st.markdown("###### ⚡ Cálculo Reglamentario y Recomendación:")
                base_minima = max(3450.0, sup_calc * 100.0)
                es_bar = "Bar" in act_calc or "Restaurante" in act_calc
                es_acad = "Academia" in act_calc or "Clínica" in act_calc
                es_gym = "Gimnasio" in act_calc
                es_lpc = es_bar or es_acad or es_gym

                # Factores de simultaneidad según tipo de actividad
                if es_bar:
                    coef_clima = 1.0
                    coef_maq = 0.8
                    pot_calc_total = base_minima * 0.7 + clima_calc * coef_clima + maq_calc * coef_maq
                elif es_gym:
                    coef_clima = 0.9
                    coef_maq = 0.9
                    pot_calc_total = base_minima * 0.8 + clima_calc * coef_clima + maq_calc * coef_maq
                elif es_acad:
                    coef_clima = 0.8
                    coef_maq = 0.7
                    pot_calc_total = base_minima + clima_calc * coef_clima + maq_calc * coef_maq
                else:
                    coef_clima = 0.8
                    coef_maq = 0.7
                    pot_calc_total = base_minima + clima_calc * coef_clima + maq_calc * coef_maq

                # Decisión de tensión y plantilla recomendada
                if "Preferir Monofásico" in pref_red:
                    tension_sug = "Monofásica (230 V)"
                    sub_tens = "Hasta 9.200 W (IGA 40A)"
                    plantilla_rec = "🏢 Local Comercial Ordinario Monofásico (Oficina/Tienda - 9.200 W - 230V - IGA 40A)"
                    pot_final_plantilla = 9200.0
                elif "Preferir Trifásico" in pref_red:
                    tension_sug = "Trifásica (400 V)"
                    sub_tens = "17.320 W (IGA 25A Tri)"
                    if es_bar:
                        plantilla_rec = "🍽️ LPC: Bar / Restaurante / Cafetería (27.710 W - 400V - IGA 40A Tri - OCA obligatoria)"
                        pot_final_plantilla = 27710.0
                    elif es_gym:
                        plantilla_rec = "🏋️ LPC: Gimnasio / Polideportivo con Duchas (20.780 W - 400V - IGA 32A Tri - OCA)"
                        pot_final_plantilla = 20780.0
                    else:
                        plantilla_rec = "🏢 Local Comercial Trifásico (Comercio/Clima Tri - 17.320 W - 400V - IGA 25A Tri)"
                        pot_final_plantilla = 17320.0
                else:
                    # Automático
                    if es_bar:
                        tension_sug = "Trifásica (400 V)"
                        sub_tens = "Cocina industrial (IGA 40A Tri)"
                        plantilla_rec = "🍽️ LPC: Bar / Restaurante / Cafetería (27.710 W - 400V - IGA 40A Tri - OCA obligatoria)"
                        pot_final_plantilla = 27710.0
                    elif es_gym:
                        tension_sug = "Trifásica (400 V)"
                        sub_tens = "Duchas y clima (IGA 32A Tri)"
                        plantilla_rec = "🏋️ LPC: Gimnasio / Polideportivo con Duchas (20.780 W - 400V - IGA 32A Tri - OCA)"
                        pot_final_plantilla = 20780.0
                    elif es_acad:
                        tension_sug = "Trifásica (400 V)" if pot_calc_total > 9200.0 else "Monofásica (230 V)"
                        sub_tens = "Pública Concurrencia"
                        plantilla_rec = "🎓 LPC: Academia / Clínica / Centro de Enseñanza (>50 pers. - 17.320 W - 400V - OCA)"
                        pot_final_plantilla = 17320.0
                    else:
                        if pot_calc_total <= 9600.0 and maq_calc < 2000.0:
                            tension_sug = "Monofásica (230 V)"
                            sub_tens = "Apto monofásica (IGA 40A)"
                            plantilla_rec = "🏢 Local Comercial Ordinario Monofásico (Oficina/Tienda - 9.200 W - 230V - IGA 40A)"
                            pot_final_plantilla = 9200.0
                        else:
                            tension_sug = "Trifásica (400 V)"
                            sub_tens = "Clima o cargas elevadas"
                            plantilla_rec = "🏢 Local Comercial Trifásico (Comercio/Clima Tri - 17.320 W - 400V - IGA 25A Tri)"
                            pot_final_plantilla = 17320.0

                bg_tens = "#eff6ff" if "Monofásica" in tension_sug else "#fef3c7"
                border_tens = "#0284c7" if "Monofásica" in tension_sug else "#d97706"
                color_tens = "#0369a1" if "Monofásica" in tension_sug else "#b45309"
                color_tens_lbl = "#0284c7" if "Monofásica" in tension_sug else "#92400e"

                # Tarjetas métricas limpias y responsivas sin truncado de texto
                st.markdown(
                    f"""
                    <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px;">
                        <div style="flex:1; min-width:130px; background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:8px 10px; text-align:center;">
                            <div style="font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.5px;">Base Legal Mínima</div>
                            <div style="font-size:18px; font-weight:800; color:#0f172a; margin:3px 0;">{base_minima:,.0f} W</div>
                            <div style="font-size:10.5px; color:#64748b;">100 W/m² (ITC-BT-10)</div>
                        </div>
                        <div style="flex:1; min-width:130px; background:#f0fdf4; border:1px solid #16a34a; border-radius:8px; padding:8px 10px; text-align:center;">
                            <div style="font-size:11px; font-weight:700; color:#15803d; text-transform:uppercase; letter-spacing:0.5px;">Potencia Simultánea</div>
                            <div style="font-size:18px; font-weight:800; color:#16a34a; margin:3px 0;">{pot_calc_total:,.0f} W</div>
                            <div style="font-size:10.5px; color:#15803d;"><b>{pot_calc_total/1000.0:.2f} kW</b></div>
                        </div>
                        <div style="flex:1; min-width:130px; background:{bg_tens}; border:1px solid {border_tens}; border-radius:8px; padding:8px 10px; text-align:center;">
                            <div style="font-size:11px; font-weight:700; color:{color_tens_lbl}; text-transform:uppercase; letter-spacing:0.5px;">Tensión Sugerida</div>
                            <div style="font-size:16px; font-weight:800; color:{color_tens}; margin:3px 0;">{tension_sug}</div>
                            <div style="font-size:10.5px; color:{color_tens_lbl};">{sub_tens}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Desglose matemático explicativo
                with st.container(border=True):
                    st.caption(
                        f"📊 **Desglose de cálculo REBT:** Base obligatoria ({sup_calc:.0f} m² × 100 W/m² = **{base_minima:,.0f} W**) + "
                        f"Climatización ({clima_calc:,.0f} W × {coef_clima:.1f} = **{clima_calc * coef_clima:,.0f} W**) + "
                        f"Maquinaria ({maq_calc:,.0f} W × {coef_maq:.1f} = **{maq_calc * coef_maq:,.0f} W**) = "
                        f"**{pot_calc_total:,.0f} W simultáneos**."
                    )

                st.markdown(f"**🎯 Plantilla Recomendada:** `{plantilla_rec}`")

                if pot_calc_total <= 100000.0:
                    st.success("✅ **Legalizable con MTD:** No supera los 100 kW de potencia. Puedes firmar y tramitar la instalación directamente con tu carnet de instalador autorizado.")
                else:
                    st.error("⚠️ **REQUIERE PROYECTO TÉCNICO:** Al superar los 100 kW, el REBT (ITC-BT-04 Tabla 3.1) exige obligatoriamente Proyecto visado por Ingeniero Colegiado y Dirección Técnica de Obra.")

                if es_lpc:
                    st.warning("⚠️ **Local de Pública Concurrencia (ITC-BT-28):** Obligatorio cables libres de halógenos AS, doble línea de alumbrado e inspección inicial por OCA.")

                if st.button("⚡ Cargar Plantilla Calculada en la MTD", key="btn_cargar_calc_loc", type="primary"):
                    st.session_state["_mtd_cargar_plantilla_pendiente"] = plantilla_rec
                    st.session_state["_mtd_cargar_datos_pendientes"] = {
                        "mtd_in_pot_inst": float(round(pot_final_plantilla, 0)),
                        "mtd_in_pot_max": float(max(st.session_state.get("mtd_in_pot_max", pot_final_plantilla), pot_final_plantilla))
                    }
                    st.session_state["_mtd_msg_exito_carga"] = f"✅ ¡Plantilla cargada con {pot_final_plantilla:,.0f} W y circuitos adaptados!"
                    st.rerun()

        with tab_guia_loc:
            st.markdown(r"""
            #### 📚 Criterios de Selección Oficial para el Instalador en Murcia

            | Tipo de Instalación | Potencia Habitual | Tensión | IGA | ¿Cuándo elegirla? | Trámite Legal |
            | :--- | :---: | :---: | :---: | :--- | :--- |
            | **Vivienda Básica** | 5.750 W | 230 V | 25 A | Viviendas estándar < 160 m² sin aire acondicionado centralizado. | MTD Instalador |
            | **Vivienda Elevada Clima** | 9.200 W | 230 V | 40 A | Vivienda habitual con aire por conductos o varios splits. | MTD Instalador |
            | **Vivienda Aerotermia** | 11.500 W | 230 V | 50 A | Obra nueva con bomba de calor para ACS y suelo radiante. | MTD Instalador |
            | **Vivienda Máx Monofásica** | 14.490 W | 230 V | 63 A | Límite máximo monofásico en España sin pasar a trifásica. | MTD Instalador |
            | **Chalet Trifásica** | 17.320 W | 400 V | 25 A | Parcela con piscina, riego, pozo y clima trifásico. | MTD Instalador |
            | **IRVE Garaje Comunitario** | 7.360 W | 230 V | 32 A | Wallbox en garaje comunitario (Esquema 2). Cable AS obligatorio. | MTD Instalador |
            | **IRVE Trifásico Rápido** | 22.000 W | 400 V | 32 A | Cargador rápido en empresa, hotel o flota. | MTD Instalador (≤50 kW int.) |
            | **Autoconsumo Solar** | 5.000 W | 230 V | 25 A | Placas solares interconectadas a red interior (RD 244/2019). | MTD Instalador (≤10 kW gen.) |
            | **Local Monofásico** | 9.200 W | 230 V | 40 A | Tiendas, despachos, oficinas con aforo < 50 personas. | MTD Instalador |
            | **Local Trifásico** | 17.320 W | 400 V | 25 A | Comercios con climatización trifásica o maquinaria. | MTD Instalador (≤100 kW) |
            | **Bar / Restaurante (LPC)** | 27.710 W | 400 V | 40 A | Hostelería con cocina industrial, campana y salón. Cables AS. | MTD + OCA Inicial |
            | **Academia / Clínica (LPC)** | 17.320 W | 400 V | 25 A | Aforo > 50 personas. Cables AS y doble línea de alumbrado. | MTD + OCA Inicial |
            | **Gimnasio con Duchas (LPC)** | 20.780 W | 400 V | 32 A | Vestuarios colectivos, termos de ACS y ventilación RITE. | MTD + OCA Inicial |
            | **Cuadro de Obra** | 15.000 W | 400 V | 40 A | Suministro provisional de obra con tomas CETAC y parada emergencia. | MTD Instalador (≤50 kW) |
            """)

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

        badge_sit = '<span style="color:#16a34a; font-weight:bold; font-size:12px;">✅ Adjuntado</span>' if tiene_sit else '<span style="color:#64748b; font-size:12px;">⚪ Sin adjuntar</span>'
        badge_emp = '<span style="color:#16a34a; font-weight:bold; font-size:12px;">✅ Adjuntado</span>' if tiene_emp else '<span style="color:#64748b; font-size:12px;">⚪ Sin adjuntar</span>'
        badge_dist = '<span style="color:#16a34a; font-weight:bold; font-size:12px;">✅ Adjuntado</span>' if tiene_dist else '<span style="color:#64748b; font-size:12px;">⚪ Sin adjuntar</span>'
        if unif_modo == 'auto':
            badge_unif = '<span style="color:#0284c7; font-weight:bold; font-size:12px;">⚙️ Vectorial Auto</span>'
        elif bool(st.session_state.get("mtd_plano_unifilar_custom")):
            badge_unif = '<span style="color:#16a34a; font-weight:bold; font-size:12px;">📁 Plano Propio</span>'
        else:
            badge_unif = '<span style="color:#ef4444; font-weight:bold; font-size:12px;">⚠️ Falta archivo</span>'

        bg_sit = '#f0fdf4' if tiene_sit else '#f8fafc'
        border_sit = '#16a34a' if tiene_sit else '#cbd5e1'
        bg_emp = '#f0fdf4' if tiene_emp else '#f8fafc'
        border_emp = '#16a34a' if tiene_emp else '#cbd5e1'
        bg_dist = '#f0fdf4' if tiene_dist else '#f8fafc'
        border_dist = '#16a34a' if tiene_dist else '#cbd5e1'
        bg_unif = '#f0fdf4' if (unif_modo == 'custom' and bool(st.session_state.get("mtd_plano_unifilar_custom"))) else ('#f0f9ff' if unif_modo == 'auto' else '#f8fafc')
        border_unif = '#16a34a' if (unif_modo == 'custom' and bool(st.session_state.get("mtd_plano_unifilar_custom"))) else ('#0284c7' if unif_modo == 'auto' else '#cbd5e1')
        bg_fotos = '#f0fdf4' if n_fotos > 0 else '#f8fafc'
        border_fotos = '#16a34a' if n_fotos > 0 else '#cbd5e1'

        cp1, cp2, cp3, cp4, cp5 = st.columns(5)
        with cp1:
            st.markdown(
                f"<div style='border:1px solid {border_sit}; background:{bg_sit}; padding:8px 10px; border-radius:8px; text-align:center;'>"
                f"<div style='font-size:10.5px; font-weight:bold; color:#64748b;'>ANEXO I (a)</div>"
                f"<div style='font-size:13px; font-weight:bold; margin:2px 0;'>🗺️ Situación</div>"
                f"{badge_sit}"
                f"</div>",
                unsafe_allow_html=True
            )
        with cp2:
            st.markdown(
                f"<div style='border:1px solid {border_emp}; background:{bg_emp}; padding:8px 10px; border-radius:8px; text-align:center;'>"
                f"<div style='font-size:10.5px; font-weight:bold; color:#64748b;'>ANEXO I (b)</div>"
                f"<div style='font-size:13px; font-weight:bold; margin:2px 0;'>📍 Emplazamiento</div>"
                f"{badge_emp}"
                f"</div>",
                unsafe_allow_html=True
            )
        with cp3:
            st.markdown(
                f"<div style='border:1px solid {border_dist}; background:{bg_dist}; padding:8px 10px; border-radius:8px; text-align:center;'>"
                f"<div style='font-size:10.5px; font-weight:bold; color:#64748b;'>ANEXO II</div>"
                f"<div style='font-size:13px; font-weight:bold; margin:2px 0;'>📐 Distribución</div>"
                f"{badge_dist}"
                f"</div>",
                unsafe_allow_html=True
            )
        with cp4:
            st.markdown(
                f"<div style='border:1px solid {border_unif}; background:{bg_unif}; padding:8px 10px; border-radius:8px; text-align:center;'>"
                f"<div style='font-size:10.5px; font-weight:bold; color:#64748b;'>ANEXO III</div>"
                f"<div style='font-size:13px; font-weight:bold; margin:2px 0;'>⚡ Unifilar</div>"
                f"{badge_unif}"
                f"</div>",
                unsafe_allow_html=True
            )
        with cp5:
            st.markdown(
                f"<div style='border:1px solid {border_fotos}; background:{bg_fotos}; padding:8px 10px; border-radius:8px; text-align:center;'>"
                f"<div style='font-size:10.5px; font-weight:bold; color:#64748b;'>ANEXO V</div>"
                f"<div style='font-size:13px; font-weight:bold; margin:2px 0;'>📸 Fotos Obra</div>"
                f"<span style='color:#334155; font-weight:bold; font-size:12px;'>{n_fotos} fotos</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        with st.expander("⚡ 📤 SUBIR / GESTIONAR PLANOS Y FOTOS RÁPIDAMENTE AQUÍ (Sin buscar pestañas)", expanded=abrir_planos_auto or tiene_emp or tiene_sit or tiene_dist or (n_fotos > 0)):
            st.info("💡 **Subida Rápida:** Puedes subir o sustituir tus archivos de plano (PNG, JPG o PDF de 1 página) y fotografías de fin de obra directamente aquí. Se sincronizan automáticamente con el expediente, la pestaña 7 y se incorporan al documento oficial de la Memoria Técnica.")
            
            # Fila 1: Situación y Emplazamiento
            col_qp1, col_qp2 = st.columns(2)
            with col_qp1:
                with st.container(border=True):
                    st.markdown("##### 🗺️ Anexo I (a): Plano de Situación")
                    st.caption("Mapa general / callejero de situación en el municipio (Google Maps / Cartografía).")
                    k_sit = f"quick_up_sit_{st.session_state.get('_ver_up_sit', 0)}"
                    up_sit_quick = st.file_uploader("Subir Plano de Situación (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key=k_sit)
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
                            st.session_state["_ver_up_sit"] = st.session_state.get("_ver_up_sit", 0) + 1
                            st.rerun()

            with col_qp2:
                with st.container(border=True):
                    st.markdown("##### 📍 Anexo I (b): Plano de Emplazamiento")
                    st.caption("Plano parcelario catastral o urbanístico de la finca / parcela.")
                    k_emp = f"quick_up_emp_{st.session_state.get('_ver_up_emp', 0)}"
                    up_emp_quick = st.file_uploader("Subir Plano de Emplazamiento (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key=k_emp)
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
                            st.session_state["_ver_up_emp"] = st.session_state.get("_ver_up_emp", 0) + 1
                            st.rerun()

            # Fila 2: Distribución en Planta y Unifilar Personalizado
            col_qp3, col_qp4 = st.columns(2)
            with col_qp3:
                with st.container(border=True):
                    st.markdown("##### 📐 Anexo II: Plano en Planta de Distribución en B.T.")
                    st.caption("Plano en planta con tomas de corriente, alumbrado y cuadro eléctrico (AutoCAD / Arquitectónico).")
                    k_dist = f"quick_up_dist_{st.session_state.get('_ver_up_dist', 0)}"
                    up_dist_quick = st.file_uploader("Subir Plano de Distribución (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key=k_dist)
                    if up_dist_quick is not None:
                        f_id_d = f"{up_dist_quick.name}_{up_dist_quick.size}"
                        if st.session_state.get("_last_quick_dist_id") != f_id_d:
                            b64_dq = procesar_archivo_anexo(up_dist_quick)
                            if b64_dq:
                                st.session_state["mtd_plano_distribucion"] = b64_dq
                                st.session_state["_last_quick_dist_id"] = f_id_d
                    if st.session_state.get("mtd_plano_distribucion"):
                        st.image(st.session_state["mtd_plano_distribucion"], caption="Plano de Distribución Cargado", use_container_width=True)
                        if st.button("🗑️ Quitar Distribución", key="btn_del_dist_quick"):
                            st.session_state.pop("mtd_plano_distribucion", None)
                            st.session_state.pop("_last_quick_dist_id", None)
                            st.session_state["_ver_up_dist"] = st.session_state.get("_ver_up_dist", 0) + 1
                            st.rerun()

            with col_qp4:
                with st.container(border=True):
                    st.markdown("##### ⚡ Anexo III: Esquema Unifilar Personalizado")
                    st.caption("Si tienes tu propio plano unifilar de AutoCAD o Cade_Simu, súbelo aquí para reemplazar el esquema vectorial automático.")
                    k_unif = f"quick_up_unif_{st.session_state.get('_ver_up_unif', 0)}"
                    up_unif_quick = st.file_uploader("Subir tu Esquema Unifilar Propio (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key=k_unif)
                    if up_unif_quick is not None:
                        f_id_u = f"{up_unif_quick.name}_{up_unif_quick.size}"
                        if st.session_state.get("_last_quick_unif_id") != f_id_u:
                            b64_uq = procesar_archivo_anexo(up_unif_quick)
                            if b64_uq:
                                st.session_state["mtd_plano_unifilar_custom"] = b64_uq
                                st.session_state["mtd_unifilar_modo"] = "custom"
                                st.session_state["_last_quick_unif_id"] = f_id_u
                    if st.session_state.get("mtd_plano_unifilar_custom"):
                        st.image(st.session_state["mtd_plano_unifilar_custom"], caption="Esquema Unifilar Propio Cargado", use_container_width=True)
                        if st.button("🗑️ Quitar Unifilar Propio (Usar Vectorial Auto)", key="btn_del_unif_quick"):
                            st.session_state.pop("mtd_plano_unifilar_custom", None)
                            st.session_state["mtd_unifilar_modo"] = "auto"
                            st.session_state.pop("_last_quick_unif_id", None)
                            st.session_state["_ver_up_unif"] = st.session_state.get("_ver_up_unif", 0) + 1
                            st.rerun()
                    else:
                        st.caption("ℹ️ *Actualmente se genera automáticamente el Esquema Unifilar Vectorial normalizado con los circuitos del cuadro.*")

            # Fila 3: Subida Rápida de Fotos de Obra (Anexo V)
            st.markdown("<hr style='margin:12px 0; border:0; border-top:1px dashed #cbd5e1;'/>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("##### 📸 Anexo V: Fotografías de Fin de Obra y Evidencias REBT (ITC-BT-05)")
                st.caption("Adjunta fotografías clave de la ejecución (cuadro general montado, pica de tierra, módulo de contadores, display multifunción). Se sincronizan automáticamente con el expediente y la pestaña 7.")

                if "mtd_fotos_obra" not in st.session_state:
                    st.session_state["mtd_fotos_obra"] = []

                col_qf1, col_qf2 = st.columns([1.5, 2.5])
                with col_qf1:
                    tipo_qf = st.selectbox(
                        "Tipo de Evidencia Fotográfica:",
                        [
                            "Cuadro General (CGMP) montado y rotulado",
                            "Punto de Puesta a Tierra (Pica, Arqueta y Borna)",
                            "Acometida / CGP / Módulo de Contadores",
                            "Display Comprobador Multifunción (Medida Rt / PE)",
                            "Ensayo Disparo Diferencial (Multifunción)",
                            "Canalizaciones y Tubos empotrados en obra",
                            "Mecanismos y Cuadro de Mando en Vivienda / Local",
                            "Otra fotografía de la instalación"
                        ],
                        key="sel_quick_foto_sug"
                    )
                    tit_qf_custom = st.text_input("Descripción técnica para las fotos:", value=tipo_qf, key="txt_quick_foto_desc")
                with col_qf2:
                    k_qf = f"quick_up_fotos_{st.session_state.get('_ver_quick_fotos', 0)}"
                    up_fotos_quick = st.file_uploader(
                        "Subir una o varias Fotos (JPG, PNG o WEBP):",
                        type=["png", "jpg", "jpeg", "webp"],
                        accept_multiple_files=True,
                        key=k_qf,
                        help="Puedes seleccionar varios archivos a la vez desde tu móvil, tablet o PC."
                    )
                    if up_fotos_quick:
                        f_q_id = "_".join([f"{f.name}_{f.size}" for f in up_fotos_quick])
                        if st.session_state.get("_last_quick_batch_id") != f_q_id:
                            for idx_q, f_obj in enumerate(up_fotos_quick):
                                b64_q = procesar_archivo_anexo(f_obj)
                                if b64_q:
                                    sufijo = f" (Foto {idx_q + 1})" if len(up_fotos_quick) > 1 else ""
                                    st.session_state["mtd_fotos_obra"].append({
                                        "titulo": f"{tit_qf_custom}{sufijo}",
                                        "data": b64_q
                                    })
                            st.session_state["_last_quick_batch_id"] = f_q_id
                            st.session_state["_ver_quick_fotos"] = st.session_state.get("_ver_quick_fotos", 0) + 1
                            st.success(f"✅ ¡{len(up_fotos_quick)} fotografía/s incorporada/s al expediente!")
                            st.rerun()

                # Mini galería interactiva
                fotos_guardadas = st.session_state.get("mtd_fotos_obra", [])
                if fotos_guardadas:
                    st.markdown(f"**📷 Fotografías adjuntadas en este expediente ({len(fotos_guardadas)} foto/s):**")
                    q_cols = st.columns(min(len(fotos_guardadas), 4))
                    for q_idx, q_item in enumerate(fotos_guardadas):
                        with q_cols[q_idx % len(q_cols)]:
                            with st.container(border=True):
                                st.image(q_item["data"], caption=q_item.get("titulo", ""), use_container_width=True)
                                if st.button("🗑️ Quitar", key=f"btn_del_qf_{q_idx}", use_container_width=True):
                                    st.session_state["mtd_fotos_obra"].pop(q_idx)
                                    st.rerun()

    lbl_tab7 = "🗺️ 7. PLANOS Y UNIFILAR"
    elem_adjuntos = []
    if tiene_sit: elem_adjuntos.append("Situación")
    if tiene_emp: elem_adjuntos.append("Emplazamiento")
    if tiene_dist: elem_adjuntos.append("Distribución")
    if unif_modo == "custom" and tiene_unif: elem_adjuntos.append("Unifilar")
    if n_fotos > 0: elem_adjuntos.append(f"{n_fotos} fotos")
    if elem_adjuntos:
        lbl_tab7 += f" (📎 {', '.join(elem_adjuntos)})"


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

        # Banner informativo de sincronización automática desde Bloque 1
        tipo_sel_actual = st.session_state.get("mtd_tipo_inst_sel", "")
        es_blanco = not tipo_sel_actual or tipo_sel_actual.startswith("⚪") or "Blanco" in tipo_sel_actual
        pot_actual = float(st.session_state.get("mtd_in_pot_inst", 5750.0))
        tens_actual = st.session_state.get("mtd_in_tension", "Monofásico (230 V) - 50 Hz")
        cable_actual = st.session_state.get("mtd_in_di_cable", "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (AS)")
        tubo_actual = st.session_state.get("mtd_in_di_tubo", "Tubo M32 libre de halógenos (ITC-BT-15)")

        if not es_blanco and pot_actual > 0:
            st.info(
                f"🟢 **Suministro Sincronizado Automáticamente con el Bloque I:**\n\n"
                f"• **Plantilla activa:** `{tipo_sel_actual.split('(')[0].strip()}`\n"
                f"• **Potencia asignada:** **{pot_actual:,.0f} W** ({pot_actual/1000.0:.2f} kW) | **Tensión:** `{tens_actual.split(' - ')[0]}`\n"
                f"• **Derivación Individual:** `{cable_actual}` bajo `{tubo_actual}`\n\n"
                f"✅ **No necesitas volver a introducir la potencia ni pulsar ningún botón.** Todos los parámetros oficiales ya están listos para el visado. "
                f"Los campos inferiores te permiten ajustar longitudes o secciones específicas de esta obra solo si lo requieres."
            )
        else:
            st.warning(
                "ℹ️ **Modo manual o en blanco:** Selecciona una plantilla técnica oficial en el **Bloque 1 (arriba)** para que todos estos campos se completen automáticamente, o introduce los valores manualmente a continuación."
            )

        with st.expander("⚡ Ajustes Rápidos / Sobreescribir Potencia de Suministro (Opcional)", expanded=False):
            st.caption("Usa estos botones solo si deseas sustituir puntualmente la potencia o tipo de acometida sin recargar toda la plantilla:")
            col_ps1, col_ps2, col_ps3, col_ps4, col_ps5, col_ps6 = st.columns(6)
            with col_ps1:
                if st.button("🏠 Básica (5.75 kW)", use_container_width=True, help="Vivienda Básica 230V"):
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
                if st.button("🏡 Clima (9.2 kW)", use_container_width=True, help="Vivienda Elevada Clima DGEAIM Murcia"):
                    st.session_state["mtd_in_pot_inst"] = 9200.0
                    st.session_state["mtd_in_pot_max"] = 9200.0
                    st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
                    st.session_state["mtd_in_origen"] = "Derivación Individual desde Centralización (ITC-BT-15)"
                    st.session_state["mtd_in_di_cable"] = "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (AS)"
                    st.session_state["mtd_in_di_tubo"] = "Tubo M40 libre de halógenos (ITC-BT-15)"
                    st.session_state["mtd_in_di_long"] = 18.0
                    st.session_state["mtd_in_di_cdt"] = 0.85
                    st.session_state["mtd_in_grado"] = "Elevada"
                    st.success("✅ Parámetros de Vivienda Elevada Clima cargados.")
                    st.rerun()
            with col_ps3:
                if st.button("🌡️ Aerotermia (11.5 kW)", use_container_width=True, help="Vivienda con Bomba de Calor Aerotérmica"):
                    st.session_state["mtd_in_pot_inst"] = 11500.0
                    st.session_state["mtd_in_pot_max"] = 11500.0
                    st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
                    st.session_state["mtd_in_origen"] = "Derivación Individual desde Centralización (ITC-BT-15)"
                    st.session_state["mtd_in_di_cable"] = "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (AS)"
                    st.session_state["mtd_in_di_tubo"] = "Tubo M40 libre de halógenos (ITC-BT-15)"
                    st.session_state["mtd_in_di_long"] = 18.0
                    st.session_state["mtd_in_di_cdt"] = 0.95
                    st.session_state["mtd_in_grado"] = "Elevada"
                    st.success("✅ Parámetros de Vivienda Aerotermia cargados.")
                    st.rerun()
            with col_ps4:
                if st.button("🚗 IRVE (7.36 kW)", use_container_width=True, help="Recarga VE ITC-BT-52"):
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
            with col_ps5:
                if st.button("🍽️ Bar LPC (27.7 kW)", use_container_width=True, help="Hostelería 400V Trifásica"):
                    st.session_state["mtd_in_pot_inst"] = 27710.0
                    st.session_state["mtd_in_pot_max"] = 27710.0
                    st.session_state["mtd_in_tension"] = "Trifásico (400 V) - 50 Hz"
                    st.session_state["mtd_in_origen"] = "Línea General de Alimentación / Centralización"
                    st.session_state["mtd_in_di_cable"] = "4x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (AS)"
                    st.session_state["mtd_in_di_tubo"] = "Tubo M50 libre de halógenos"
                    st.session_state["mtd_in_di_long"] = 22.0
                    st.session_state["mtd_in_di_cdt"] = 0.72
                    st.session_state["mtd_in_grado"] = "Pública Concurrencia (ITC-BT-28)"
                    st.success("✅ Parámetros de Bar / Restaurante LPC cargados.")
                    st.rerun()
            with col_ps6:
                if st.button("🏢 Comercio Tri (17.3 kW)", use_container_width=True, help="Comercial Trifásico 400V"):
                    st.session_state["mtd_in_pot_inst"] = 17320.0
                    st.session_state["mtd_in_pot_max"] = 17320.0
                    st.session_state["mtd_in_tension"] = "Trifásico (400 V) - 50 Hz"
                    st.session_state["mtd_in_origen"] = "Módulo de Medida / CPM en Fachada"
                    st.session_state["mtd_in_di_cable"] = "4x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (AS)"
                    st.session_state["mtd_in_di_tubo"] = "Tubo M40 libre de halógenos"
                    st.session_state["mtd_in_di_long"] = 20.0
                    st.session_state["mtd_in_di_cdt"] = 0.65
                    st.session_state["mtd_in_grado"] = "Comercial / Servicios"
                    st.success("✅ Parámetros de Comercio Trifásico cargados.")
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

        # Breve Descripción de la Instalación (Página 3 de la MTD Oficial DGEAIM Murcia)
        st.markdown("<hr style='margin:14px 0; border:0; border-top:1px dashed #cbd5e1;'/>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### 📝 Página 3 MTD Oficial: «BREVE DESCRIPCIÓN DE LA INSTALACIÓN»")
            st.caption(
                "En el modelo normalizado de la Región de Murcia (DGEAIM), este apartado ocupa todo el bloque inferior "
                "de la **Página 3** (Tabla 2). Dispone de un amplio espacio reglamentario de más de 10 renglones para describir la instalación. "
                "Puedes redactar libremente o pulsar uno de los botones rápidos de abajo:"
            )

            tipo_limpio_desc = tipo_inst_sel.split('(')[0].replace('☀️', '').replace('🏗️', '').replace('🚗', '').replace('🏡', '').replace('🏢', '').replace('🍽️', '').replace('🏋️', '').replace('🎓', '').strip()
            tram_nombre = tipo_tram_sel.split('(')[0].replace('🆕', '').replace('🏗️', '').replace('📈', '').replace('🔧', '').replace('🔄', '').replace('📋', '').strip().upper()
            
            # Opción 1: Breve y concisa (exactamente como en los modelos tramitados en Murcia)
            desc_breve_oficial = f"{tram_nombre} EN {tipo_limpio_desc.upper()} {sum_pot_inst:,.0f} W (REBT RD 842/2002)"
            
            # Opción 2: Detallada técnica reglamentaria
            desc_tecnica_completa = (
                f"INSTALACIÓN ELÉCTRICA EN BAJA TENSIÓN PARA {tipo_limpio_desc.upper()} ({tram_nombre}) CON POTENCIA PREVISTA DE {sum_pot_inst:,.0f} W A TENSIÓN DE {sum_tension.split(' ')[0]}. "
                f"CUADRO GENERAL DE MANDO Y PROTECCIÓN (CGMP) CON IGA OMNIPOLAR DE {st.session_state.get('mtd_in_iga', 25)}A (ICN={st.session_state.get('mtd_in_icn', 6.0):.0f}KA), "
                f"PROTECTOR DE SOBRETENSIONES PERMANENTES Y TRANSITORIAS TIPO 2 CON BOBINA DE DISPARO (ITC-BT-23), INTERRUPTOR DIFERENCIAL 30mA CLASE A (ITC-BT-24) "
                f"Y DERIVACIÓN INDIVIDUAL {sum_di_cable.upper()} BAJO {sum_di_tubo.upper()} CON CAÍDA DE TENSIÓN CALCULADA ΔV = {sum_di_cdt:.2f}% (CONFORME REBT ITC-BT-15)."
            )

            col_bd_btn1, col_bd_btn2 = st.columns(2)
            with col_bd_btn1:
                if st.button("📄 Formato Breve Tradicional (Modelo Murcia)", use_container_width=True, help="Inserta una línea concisa tal como figura en los modelos tramitados ante Industria"):
                    st.session_state["mtd_in_desc_instalacion"] = desc_breve_oficial
                    st.rerun()
            with col_bd_btn2:
                if st.button("🪄 Formato Técnico Extenso (REBT Completo)", use_container_width=True, help="Inserta descripción completa con IGA, protecciones, diferenciales y caída de tensión"):
                    st.session_state["mtd_in_desc_instalacion"] = desc_tecnica_completa
                    st.rerun()

            desc_val_actual = st.session_state.get("mtd_in_desc_instalacion", desc_breve_oficial)
            st.text_area(
                "Texto que se plasmará en la Página 3 del documento oficial:",
                value=desc_val_actual,
                height=110,
                key="mtd_in_desc_instalacion",
                help="Este texto se inserta exactamente en la casilla reglamentaria 'BREVE DESCRIPCIÓN DE LA INSTALACIÓN' de la Página 3 del modelo oficial de Murcia."
            )

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

        # Banner informativo de protecciones CGMP sincronizadas automáticamente
        tipo_sel_actual = st.session_state.get("mtd_tipo_inst_sel", "")
        es_blanco = not tipo_sel_actual or tipo_sel_actual.startswith("⚪") or "Blanco" in tipo_sel_actual
        iga_actual = int(st.session_state.get("mtd_in_iga", 25))
        curva_actual = st.session_state.get("mtd_in_curva", "Curva C (General)")
        icn_actual = float(st.session_state.get("mtd_in_icn", 6.0))
        dif_actual = st.session_state.get("mtd_in_dif", "")
        vtp_actual = st.session_state.get("mtd_in_vtp", "")

        if not es_blanco and iga_actual > 0:
            st.info(
                f"🟢 **Protecciones CGMP Sincronizadas Automáticamente:**\n\n"
                f"• **IGA Cabecera:** **{iga_actual} A** ({curva_actual}, Icn={icn_actual:.0f} kA)\n"
                f"• **Diferencial:** `{dif_actual}`\n"
                f"• **Sobretensiones:** `{vtp_actual}`\n\n"
                f"✅ Parámetros reglamentarios del cuadro general cargados según la plantilla `{tipo_sel_actual.split('(')[0].strip()}`."
            )

        with st.expander("🛡️ Ajustes Rápidos / Sobreescribir Protecciones CGMP (Opcional)", expanded=False):
            st.caption("Usa estos botones solo si deseas sustituir puntualmente el calibre del IGA o diferenciales sin recargar toda la plantilla:")
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

        # Banner informativo de circuitos sincronizados automáticamente
        tipo_sel_actual = st.session_state.get("mtd_tipo_inst_sel", "")
        es_blanco = not tipo_sel_actual or tipo_sel_actual.startswith("⚪") or "Blanco" in tipo_sel_actual
        circs_actuales = st.session_state.get("mtd_circuitos", [])
        num_circs = len(circs_actuales)

        if not es_blanco and num_circs > 0:
            st.info(
                f"🟢 **Cuadro de Circuitos Sincronizado Automáticamente:**\n\n"
                f"Se han cargado **{num_circs} circuitos reglamentarios** del REBT según la plantilla `{tipo_sel_actual.split('(')[0].strip()}`. "
                f"Están listos con sus secciones, tubos y calibres PIA. Puedes revisarlos, añadir nuevos circuitos o eliminar los que no procedan."
            )

        with st.expander("⚡ Paquetes Rápidos y Acciones Masivas de Circuitos (Opcional)", expanded=False):
            st.caption("Usa estos botones solo si deseas sustituir el listado actual por otro pack predefinido:")
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

        # =====================================================================
        # ANEXO IV: DIMENSIONAMIENTO OFICIAL POR TRAMOS Y CÁLCULOS REBT
        # =====================================================================
        st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### 📐 Anexo IV: Dimensionamiento Oficial por Tramos y Cálculos REBT (DGEAIM Murcia)")
            st.caption(
                "Cálculos justificativos reglamentarios por tramos de canalización (RD 842/2002). "
                r"Comprueba la intensidad de diseño ($I_b$), caída de tensión acumulada ($\Delta V_{DI} + \Delta V_i$) "
                "y cumplimiento estricto de los límites reglamentarios (ITC-BT-19: ≤1.5% en DI; ITC-BT-25: ≤3% alumbrado y ≤5% fuerza)."
            )

            tramos_tags = ["C-D", "E-F", "G-H", "I-J", "K-L", "M-N", "O-P", "Q-R", "S-T", "U-V", "W-X", "Y-Z"]
            es_tri_general = "400" in str(st.session_state.get("mtd_in_tension", "230"))
            pot_di_val = float(st.session_state.get("mtd_in_pot_inst", 5750.0))
            long_di_val = float(st.session_state.get("mtd_in_di_long", 15.0))
            cdt_di_val = float(st.session_state.get("mtd_in_di_cdt", 0.72))
            ib_di_val = pot_di_val / (1.73205 * 400.0) if es_tri_general else pot_di_val / 230.0
            cable_di_val = str(st.session_state.get("mtd_in_di_cable", "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV"))
            m_sec_di = re.search(r'(\d+(?:\.\d+)?)', cable_di_val)
            sec_di_val = m_sec_di.group(1) if m_sec_di else "10"
            tubo_di_val = str(st.session_state.get("mtd_in_di_tubo", "Tubo M32"))
            m_tubo_di = re.search(r'(M\d+)', tubo_di_val)
            tubo_clean_di = m_tubo_di.group(1) if m_tubo_di else tubo_di_val

            filas_anx4 = []
            filas_anx4.append({
                "Tramo": "A-B (DI)",
                "Designación": "Derivación Individual",
                "Potencia (W)": f"{pot_di_val:,.0f} W",
                "Ib (A)": f"{ib_di_val:.1f} A",
                "Long. (m)": f"{long_di_val:.0f} m",
                "Sección": f"{sec_di_val} mm² Cu",
                "ΔV Parcial": f"{cdt_di_val:.2f}%",
                "ΔV Total": f"{cdt_di_val:.2f}%",
                "Límite REBT": "≤ 1.50%",
                "Estado": "✅ Conforme" if cdt_di_val <= 1.50 else "⚠️ Supera límite",
                "Conductor": "RZ1-K 0.6/1kV (AS)",
                "Tubo": tubo_clean_di
            })

            todos_cumplen = (cdt_di_val <= 1.50)
            for idx_c, c_it in enumerate(st.session_state.get("mtd_circuitos", [])):
                t_letra = tramos_tags[idx_c] if idx_c < len(tramos_tags) else f"T{idx_c+1}"
                p_cw = float(c_it.get("potencia", 2300))
                l_cm = float(c_it.get("longitud", 15))
                cdt_cp = float(c_it.get("cdt", 1.10))
                cdt_ctot = cdt_di_val + cdt_cp
                m_sec_c = re.search(r'(\d+(?:\.\d+)?)', str(c_it.get("seccion", "2.5")))
                sec_c = m_sec_c.group(1) if m_sec_c else "2.5"
                tubo_c = str(c_it.get("tubo", "M20"))
                c_nom = str(c_it.get("nombre", f"C{idx_c+1}"))
                es_c_tri = ("4x" in str(c_it.get("seccion", "")) or "3P" in c_nom or "trifásic" in c_nom.lower())
                ib_c = p_cw / (1.73205 * 400.0) if es_c_tri else p_cw / 230.0
                es_alumbrado = "alumbrado" in c_nom.lower() or "iluminación" in c_nom.lower() or "luz" in c_nom.lower()
                limite_c = 3.0 if es_alumbrado else 5.0
                cumple_c = (cdt_ctot <= limite_c)
                if not cumple_c:
                    todos_cumplen = False

                filas_anx4.append({
                    "Tramo": t_letra,
                    "Designación": c_nom,
                    "Potencia (W)": f"{p_cw:,.0f} W",
                    "Ib (A)": f"{ib_c:.1f} A",
                    "Long. (m)": f"{l_cm:.0f} m",
                    "Sección": f"{sec_c} mm² Cu",
                    "ΔV Parcial": f"{cdt_cp:.2f}%",
                    "ΔV Total": f"{cdt_ctot:.2f}%",
                    "Límite REBT": f"≤ {limite_c:.1f}%",
                    "Estado": "✅ Conforme" if cumple_c else "⚠️ Supera límite",
                    "Conductor": "H07Z1-K 450/750V (AS)",
                    "Tubo": tubo_c
                })

            df_anx4 = pd.DataFrame(filas_anx4)
            st.dataframe(df_anx4, use_container_width=True, hide_index=True)

            if todos_cumplen:
                st.success("✅ **TODOS LOS TRAMOS DEL ANEXO IV CUMPLEN CON LA NORMATIVA REBT (ITC-BT-19 e ITC-BT-25).** Secciones e intensidades correctas para emisión oficial.")
            else:
                st.warning("⚠️ **ATENCIÓN:** Uno o más circuitos superan la caída de tensión acumulada permitida por el REBT. Aumenta la sección del conductor o reduce la longitud del tramo para subsanarlo.")

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
                k_t7_sit = f"up_mtd_sit_{st.session_state.get('_ver_tab7_sit', 0)}"
                up_sit = st.file_uploader("Subir Plano de Situación (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key=k_t7_sit)
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
                        st.session_state["_ver_tab7_sit"] = st.session_state.get("_ver_tab7_sit", 0) + 1
                        st.rerun()

            with st.container(border=True):
                st.markdown("###### 📐 Anexo II: Plano en Planta de Distribución en B.T.")
                st.caption("Plano en planta de la vivienda, local o nave con tomas, alumbrado y cuadro (AutoCAD / Plano arquitectónico).")
                k_t7_dist = f"up_mtd_dist_{st.session_state.get('_ver_tab7_dist', 0)}"
                up_dist = st.file_uploader("Subir Plano de Distribución (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key=k_t7_dist)
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
                        st.session_state["_ver_tab7_dist"] = st.session_state.get("_ver_tab7_dist", 0) + 1
                        st.rerun()

        with col_anx2:
            with st.container(border=True):
                st.markdown("###### 📍 Anexo I (b): Plano de Emplazamiento (Catastro)")
                st.caption("Plano parcelario catastral o urbanístico de la finca / parcela.")
                k_t7_emp = f"up_mtd_emp_{st.session_state.get('_ver_tab7_emp', 0)}"
                up_emp = st.file_uploader("Subir Plano de Emplazamiento (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key=k_t7_emp)
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
                        st.session_state["_ver_tab7_emp"] = st.session_state.get("_ver_tab7_emp", 0) + 1
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
                    k_t7_unif = f"up_mtd_unif_custom_{st.session_state.get('_ver_tab7_unif', 0)}"
                    up_unif = st.file_uploader("Subir tu Esquema Unifilar (PNG, JPG o PDF):", type=["png", "jpg", "jpeg", "webp", "pdf"], key=k_t7_unif)
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
                                st.session_state.pop("_last_tab7_unif_id", None)
                                st.session_state.pop("mtd_auditoria_unifilar", None)
                                st.session_state["mtd_unifilar_modo"] = "auto"
                                st.session_state["_ver_tab7_unif"] = st.session_state.get("_ver_tab7_unif", 0) + 1
                                st.rerun()
                else:
                    st.session_state["mtd_unifilar_modo"] = "auto"
                    st.info("ℹ️ Bolimur generará automáticamente el esquema unifilar vectorial con las protecciones IGA, diferenciales y circuitos configurados en las pestañas anteriores.")
                    col_pru1, col_pru2 = st.columns([1.5, 2])
                    with col_pru1:
                        if st.button("👁️ Previsualizar Unifilar Vectorial", key="btn_prev_unif_vec", use_container_width=True):
                            ctx_mock = {
                                "suministro": {
                                    "tension": sum_tension,
                                    "di_cable": sum_di_cable,
                                    "di_tubo": sum_di_tubo,
                                    "di_long_m": sum_di_long,
                                    "di_cdt_pct": sum_di_cdt
                                },
                                "protecciones": {
                                    "iga_amperaje": prot_iga,
                                    "iga_curva": prot_curva,
                                    "iga_icn_ka": prot_icn,
                                    "diferenciales": prot_dif,
                                    "sobretensiones": prot_vtp
                                },
                                "ensayos": {"rt_ohm": med_rt},
                                "circuitos": st.session_state.get("mtd_circuitos", [])
                            }
                            png_prev = pdf_memoria_tecnica.generar_png_unifilar(ctx_mock)
                            if png_prev:
                                st.session_state["_prev_unif_png"] = png_prev
                    with col_pru2:
                        if st.session_state.get("_prev_unif_png"):
                            if st.button("❌ Ocultar Previsualización", key="btn_hide_unif_prev"):
                                st.session_state.pop("_prev_unif_png", None)
                                st.rerun()
                    if st.session_state.get("_prev_unif_png"):
                        st.image(st.session_state["_prev_unif_png"], caption="Esquema Unifilar Vectorial Oficial (UNE-EN 60617)", use_container_width=True)

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
            st.caption("Sube las fotos abajo:")

        k_t7_fotos = f"uploader_foto_obra_{st.session_state.get('_ver_tab7_fotos', 0)}"
        up_nueva_foto = st.file_uploader(
            "Subir Fotografías de la Obra (JPG, PNG o WEBP):",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key=k_t7_fotos,
            help="Puedes seleccionar varias fotos a la vez desde tu móvil, tablet o PC."
        )
        if up_nueva_foto:
            f_tab7_id = "_".join([f"{f.name}_{f.size}" for f in up_nueva_foto])
            if st.session_state.get("_last_tab7_batch_id") != f_tab7_id:
                for idx_f, f_obj in enumerate(up_nueva_foto):
                    b64_f = procesar_archivo_anexo(f_obj)
                    if b64_f:
                        sufijo = f" (Foto {idx_f + 1})" if len(up_nueva_foto) > 1 else ""
                        st.session_state["mtd_fotos_obra"].append({
                            "titulo": f"{tit_foto_custom}{sufijo}",
                            "data": b64_f
                        })
                st.session_state["_last_tab7_batch_id"] = f_tab7_id
                st.session_state["_ver_tab7_fotos"] = st.session_state.get("_ver_tab7_fotos", 0) + 1
                st.success(f"✅ ¡{len(up_nueva_foto)} fotografía/s añadida/s automáticamente al reportaje!")
                st.rerun()

        # Mostrar galería de fotos adjuntadas
        fotos_actuales = st.session_state.get("mtd_fotos_obra", [])
        if fotos_actuales:
            col_tit_g, col_del_all = st.columns([3, 1])
            with col_tit_g:
                st.markdown(f"###### 📷 Fotografías registradas en este expediente ({len(fotos_actuales)} foto/s):")
            with col_del_all:
                if len(fotos_actuales) > 1:
                    if st.button("🗑️ Vaciar Todas", key="btn_del_all_fotos", use_container_width=True):
                        st.session_state["mtd_fotos_obra"] = []
                        st.rerun()

            f_cols = st.columns(min(len(fotos_actuales), 3))
            for f_idx, f_item in enumerate(fotos_actuales):
                c_idx = f_idx % len(f_cols)
                with f_cols[c_idx]:
                    with st.container(border=True):
                        st.image(f_item["data"], caption=f_item.get("titulo", ""), use_container_width=True)
                        
                        # Edición directa del pie de foto
                        new_tit = st.text_input("Pie explicativo:", value=f_item.get("titulo", ""), key=f"edit_tit_{f_idx}")
                        if new_tit != f_item.get("titulo", ""):
                            f_item["titulo"] = new_tit
                        
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
                # Si el usuario no seleccionó previamente un cliente del CRM en el Bloque 1,
                # buscamos o creamos la ficha automáticamente a partir del Titular para que NUNCA falle el guardado.
                cli_id_final = cli_sel_id
                nombre_cli_final = cli_obj.get("nombre_completo", "") if cli_obj else ""

                if not cli_id_final:
                    nom_tit_limpio = (tit_nombre or "").strip() or f"Cliente {nom_proy_mtd}".strip()
                    nif_tit_limpio = (tit_nif or "").strip().upper()
                    
                    dup = db_manager.buscar_cliente_duplicado(user_auth["id"], nif_tit_limpio, nom_tit_limpio)
                    if dup:
                        cli_id_final = dup["id"]
                        nombre_cli_final = dup.get("nombre_completo", nom_tit_limpio)
                        st.session_state["cliente_activo_proyecto"] = dup
                    else:
                        ok_cli, nuevo_c_id = db_manager.crear_cliente(user_auth["id"], {
                            "nombre_completo": nom_tit_limpio,
                            "nif_cif": nif_tit_limpio,
                            "telefono": (tit_tel or "").strip(),
                            "email": (tit_email or "").strip(),
                            "direccion_suministro": (emp_dir or "").strip(),
                            "codigo_postal": (emp_cp or "30000").strip(),
                            "localidad": (emp_muni or "Murcia").strip(),
                            "municipio": (emp_muni or "Murcia").strip(),
                            "provincia": "Murcia",
                            "cups": (emp_cups or "").strip().upper(),
                            "tipo_inmueble": (emp_uso or "Instalación Eléctrica").strip(),
                            "notas": f"Ficha autogenerada desde Memoria Técnica MTD '{nom_proy_mtd}'"
                        })
                        if ok_cli and nuevo_c_id > 0:
                            cli_id_final = nuevo_c_id
                            nombre_cli_final = nom_tit_limpio
                            st.session_state["cliente_activo_proyecto"] = {"id": nuevo_c_id, "nombre_completo": nom_tit_limpio}

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
                    "mtd_in_desc_instalacion": st.session_state.get("mtd_in_desc_instalacion", ""),
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
                    "mtd_fotos_obra": st.session_state.get("mtd_fotos_obra", []),
                    "mtd_fecha_emision": st.session_state.get("mtd_fecha_emision", datetime.date.today().strftime("%d/%m/%Y")),
                    "mtd_exp_final": st.session_state.get("mtd_exp_final", f"EXP-MTD-{emp_muni[:3].upper()}-2026-01")
                }
                resumen_txt = f"{sum_pot_inst/1000:.2f} kW | {tipo_tram_sel.split('(')[0].strip()} | {emp_muni}"
                ok, p_id = db_manager.guardar_proyecto(
                    usuario_id=user_auth["id"],
                    cliente_id=cli_id_final,
                    nombre_proyecto=nom_proy_mtd,
                    modulo="Memoria Técnica (MTD 30)",
                    datos=datos_guardar,
                    resumen=resumen_txt
                )
                if ok:
                    nombre_destino = nombre_cli_final or (tit_nombre.strip() if tit_nombre else "Cliente")
                    st.toast(f"✅ ¡Memoria Técnica grabada con éxito! (Expediente #{p_id})", icon="💾")
                    st.success(f"✅ ¡Memoria Técnica '{nom_proy_mtd}' grabada y archivada exitosamente en la ficha de **{nombre_destino}** (Expediente #{p_id})!")
                    st.balloons()
                else:
                    st.error("Error al guardar la memoria técnica en la base de datos.")

        st.divider()

        # DOCUMENTOS OFICIALES PARA INDUSTRIA Y CLIENTE
        col_g1, col_g2, col_g3 = st.columns([2.3, 1.7, 1.5])
        with col_g1:
            exp_in = st.text_input("Nº de Expediente Oficial (DGEAIM Murcia):", value=st.session_state.get("mtd_exp_final", f"EXP-MTD-{emp_muni[:3].upper()}-2026-01"), key="mtd_exp_final")
        with col_g2:
            fecha_def = datetime.date.today()
            if "mtd_fecha_emision" in st.session_state:
                f_raw = st.session_state["mtd_fecha_emision"]
                if isinstance(f_raw, datetime.date):
                    fecha_def = f_raw
                elif isinstance(f_raw, str) and "/" in f_raw:
                    try:
                        p = f_raw.strip().split("/")
                        fecha_def = datetime.date(int(p[2]), int(p[1]), int(p[0]))
                    except Exception:
                        pass
            fecha_sel = st.date_input(
                "📅 Fecha Oficial del Documento / Presentación:",
                value=fecha_def,
                format="DD/MM/YYYY",
                key="mtd_fecha_emision_widget",
                help="Puedes modificar esta fecha si redactas la memoria hoy y la presentas o firmas ante Industria más adelante (por ejemplo, 1 mes después)."
            )
            fecha_str_doc = fecha_sel.strftime("%d/%m/%Y") if hasattr(fecha_sel, "strftime") else datetime.date.today().strftime("%d/%m/%Y")
            st.session_state["mtd_fecha_emision"] = fecha_str_doc
        with col_g3:
            st.write("")
            st.caption("Generación simultánea con fecha oficial personalizable.")

        tipo_para_doc = (emp_uso.strip() or "Instalación Eléctrica en Baja Tensión") if (tipo_inst_sel.startswith("⚪") or "Blanco" in tipo_inst_sel or "Seleccionar" in tipo_inst_sel) else tipo_inst_sel

        datos_para_pdf = {
            "tipo_instalacion": tipo_para_doc,
            "tipo_tramitacion": tipo_tram_sel,
            "expediente": exp_in,
            "fecha": fecha_str_doc,
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
            "descripcion_instalacion": st.session_state.get("mtd_in_desc_instalacion", ""),
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
                cache_key = f"pdf_word_com_{exp_in}_{hash(docx_bytes_mtd)}"
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

