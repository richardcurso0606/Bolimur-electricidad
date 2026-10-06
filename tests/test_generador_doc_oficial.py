# -*- coding: utf-8 -*-
import pytest
from modulos import generador_doc_oficial

def test_generar_docx_oficial_dgeaim_murcia():
    datos_mtd = {
        "titular": {
            "nombre": "BEATRIZ IRIARTE QUIROZ",
            "nif": "34330049L",
            "telefono": "632587747",
            "email": "beita2005@gmail.com"
        },
        "emplazamiento": {
            "direccion": "CALLE CRUCETA 11",
            "cp": "30165",
            "municipio": "MURCIA (Rincón de Seca)",
            "cups": "ES0021000000000000XX",
            "uso": "Vivienda Residencial"
        },
        "instalador": {
            "empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
            "cif": "B-73123456",
            "nombre": "Richard Orlando Choque Tejerina",
            "licencia": "REBT-30/15892",
            "registro_rii": "RII-30/08492",
            "telefono": "632676824"
        },
        "suministro": {
            "potencia_instalada_w": 9200.0,
            "potencia_max_admisible_w": 9200.0,
            "tension": "Monofásico (230 V) - 50 Hz",
            "di_cable": "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (AS)",
            "di_tubo": "Tubo M40 libre de halógenos",
            "di_long_m": 18.0,
            "di_cdt_pct": 0.85,
            "grado_electrif": "Elevada"
        },
        "protecciones": {
            "iga_amperaje": 40,
            "iga_curva": "Curva C",
            "iga_icn_ka": 6.0,
            "diferenciales": "2 x 40A / 30mA",
            "sobretensiones": "VTP + DPS Tipo 2"
        },
        "ensayos": {
            "rt_ohm": 11.8
        },
        "circuitos": [
            {"nombre": "C1 - Alumbrado", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina/Horno", "potencia": 5400, "pia": 25, "seccion": "2x6+TT6", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C9 - Climatización", "potencia": 5750, "pia": 25, "seccion": "2x6+TT6", "tubo": "M25", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"}
        ],
        "anexos": {}
    }

    docx_bytes = generador_doc_oficial.generar_docx_oficial_dgeaim_murcia(datos_mtd)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 50000
    # ZIP / DOCX magic bytes: PK
    assert docx_bytes.startswith(b"PK")
