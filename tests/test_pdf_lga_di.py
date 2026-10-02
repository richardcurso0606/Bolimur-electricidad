# -*- coding: utf-8 -*-
import pytest
from modulos import pdf_lga, pdf_di

def test_generar_pdf_lga_bytes():
    proyecto_info = {
        "nombre": "Edificio Residencial Test LGA",
        "emplazamiento": "Calle Test 123",
        "proyectista": "Ingeniero Test",
        "expediente": "EXP-LGA-TEST",
        "fecha": "02/10/2026"
    }
    lga_params = {
        "pot": 68824.0,
        "long": 25.0,
        "mat": "cobre",
        "aisl": "XLPE / EPR (90ºC) - RZ1-K",
        "metodo": "D (Cables enterrados bajo tubo)",
        "enlace": "Totalmente concentrados (Límite CDT = 0.5%)",
        "icc_orig": 10.0,
        "dv_pct": 0.5
    }
    lga_results = {
        "ib": 110.38,
        "dv_max": 2.0,
        "s_cdt": 37.89,
        "s_final": 50,
        "in_auto": 125,
        "dv_real_v": 1.516,
        "dv_real_pct": 0.379,
        "r_cable": 0.01136,
        "z_tot": 0.05136,
        "icc_fin": 7788.1,
        "tubo_diam": "Ø 140 mm",
        "razon_tubo": "Capacidad para 4 conductores unipolares de 50 mm²",
        "gamma": 44.0,
        "tabla_secciones": [
            {"sec": 35, "iz": 150, "cdt": 0.541, "estado": "Falla CDT"},
            {"sec": 50, "iz": 180, "cdt": 0.379, "estado": "CUMPLE IDEAL"},
            {"sec": 70, "iz": 220, "cdt": 0.271, "estado": "Sobredimensionado"}
        ]
    }

    pdf_bytes = pdf_lga.generar_pdf_lga(proyecto_info, lga_params, lga_results)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")


def test_generar_pdf_di_bytes():
    proyecto_info = {
        "nombre": "Vivienda Test DI",
        "emplazamiento": "Calle Test 456",
        "proyectista": "Ingeniero Test",
        "expediente": "EXP-DI-TEST",
        "fecha": "02/10/2026"
    }
    di_params = {
        "pot": 5750.0,
        "long": 15.0,
        "mat": "cobre",
        "aisl": "XLPE / EPR (90ºC) - RZ1-K",
        "metodo": "B1 (Bajo tubo empotrado)",
        "suministro": "Monofásico (230 V)",
        "icc_orig": 10.0,
        "dv_pct": 1.0,
        "es_trifasico": False
    }
    di_results = {
        "ib": 25.0,
        "dv_max": 2.3,
        "s_cdt": 6.69,
        "s_final": 10,
        "in_iga": 25,
        "dv_real_v": 1.539,
        "dv_real_pct": 0.669,
        "r_cable": 0.03409,
        "icc_fin": 2525.6,
        "umbral_mag": 250.0,
        "tubo_diam": "Ø 32 mm",
        "razon_tubo": "Tubo normalizado para DI con reserva del 100%",
        "gamma": 44.0,
        "tabla_secciones": [
            {"sec": 6, "iz": 40, "cdt": 1.115, "estado": "Falla CDT"},
            {"sec": 10, "iz": 54, "cdt": 0.669, "estado": "CUMPLE IDEAL"},
            {"sec": 16, "iz": 73, "cdt": 0.418, "estado": "Sobredimensionado"}
        ]
    }

    pdf_bytes = pdf_di.generar_pdf_di(proyecto_info, di_params, di_results)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")
