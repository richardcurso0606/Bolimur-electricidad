# -*- coding: utf-8 -*-
import pytest
from modulos import pdf_memoria_tecnica

def test_generar_pdf_mtd_industria_murcia_bytes():
    datos_mtd = {
        "titular": {
            "nombre": "Juan Pérez Martínez",
            "nif": "48123456X",
            "domicilio": "Calle Mayor 12, 3ºB",
            "localidad": "Murcia",
            "cp": "30001",
            "provincia": "Murcia",
            "telefono": "600123456",
            "email": "juan@example.com"
        },
        "emplazamiento": {
            "direccion": "Calle Mayor 12, 3ºB",
            "localidad": "Murcia",
            "cp": "30001",
            "uso": "Vivienda Residencial"
        },
        "instalador": {
            "empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
            "cif": "B-73000000",
            "proyectista": "Richard Orlando Choque Tejerina",
            "nif_instalador": "X-1234567-Y",
            "carnet": "REBT-30/15892",
            "registro_rii": "RII-30/08492",
            "domicilio": "Rincón de Seca, Murcia",
            "telefono": "600000000"
        },
        "suministro": {
            "tension": "Monofásico 230 V",
            "potencia_solicitada_w": 5750,
            "potencia_max_w": 9200,
            "grado_electrificacion": "Básica",
            "di_longitud_m": 16.0,
            "di_seccion_fase": 10.0,
            "di_tubo": "Tubo M32",
            "di_cable_tipo": "H07Z1-K (AS)"
        },
        "protecciones": {
            "iga_amperaje": 25,
            "iga_icn_ka": 6.0,
            "sobretensiones": "POP + DPS Tipo 2 (ITC-BT-23)",
            "diferenciales": "2x Diferencial 2P 40A / 30mA Clase A"
        },
        "circuitos": [
            {"id": "C1", "denominacion": "Iluminación", "pia": 10, "dif": "Dif. 1", "cable_sec": "2x1.5+TT1.5", "tubo_diam": "M16", "long_m": 15, "cdt_pct": 0.85, "pot_w": 2300},
            {"id": "C2", "denominacion": "Tomas de corriente", "pia": 16, "dif": "Dif. 1", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 18, "cdt_pct": 1.10, "pot_w": 3450},
            {"id": "C3", "denominacion": "Cocina / Horno", "pia": 25, "dif": "Dif. 1", "cable_sec": "2x6+TT6", "tubo_diam": "M25", "long_m": 12, "cdt_pct": 0.90, "pot_w": 5400},
            {"id": "C4.1", "denominacion": "Lavadora", "pia": 16, "dif": "Dif. 2", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 14, "cdt_pct": 1.00, "pot_w": 3450},
            {"id": "C4.2", "denominacion": "Lavavajillas", "pia": 16, "dif": "Dif. 2", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 14, "cdt_pct": 1.00, "pot_w": 3450},
            {"id": "C4.3", "denominacion": "Termo eléctrico", "pia": 16, "dif": "Dif. 2", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 12, "cdt_pct": 0.85, "pot_w": 2300},
            {"id": "C5", "denominacion": "Baños y aux cocina", "pia": 16, "dif": "Dif. 2", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 16, "cdt_pct": 1.15, "pot_w": 3450}
        ],
        "fecha": "03/10/2026",
        "expediente": "EXP-30/2026/00482"
    }

    pdf_bytes = pdf_memoria_tecnica.generar_pdf_mtd_industria_murcia(datos_mtd)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF")
