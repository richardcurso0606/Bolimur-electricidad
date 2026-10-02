# -*- coding: utf-8 -*-
import pytest
from modulos import pdf_calculo_rapido, pdf_irve

def test_generar_pdf_calculo_rapido_bytes():
    proyecto_info = {
        "nombre": "Instalación Test Cálculo Rápido",
        "emplazamiento": "Calle Test 123",
        "proyectista": "Ingeniero Test",
        "expediente": "EXP-CR-TEST",
        "fecha": "02/10/2026"
    }
    calc_params = {
        "pot": 9200.0,
        "long": 30.0,
        "mat": "cobre",
        "aisl": "XLPE / EPR (90ºC)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "red": "Monofásico (230V)",
        "cdt_lim": 3.0,
        "icc_orig": 10.0,
        "cos_phi": 0.85
    }
    calc_results = {
        "ib": 47.06,
        "s_cal": 10,
        "s_cdt": 8.04,
        "s_opt": 10,
        "iz_opt": 54,
        "dv_real_v": 5.54,
        "dv_real_pct": 2.41,
        "z_tot": 0.057,
        "icc_fin": 4.035,
        "prot": 50,
        "salta_proteccion": True
    }

    pdf_bytes = pdf_calculo_rapido.generar_pdf_calculo_rapido(proyecto_info, calc_params, calc_results)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")


def test_generar_pdf_irve_bytes():
    proyecto_info = {
        "nombre": "Instalación Test IRVE",
        "emplazamiento": "Garaje Test Plaza 12",
        "proyectista": "Ingeniero Test",
        "expediente": "EXP-IRVE-TEST",
        "fecha": "02/10/2026"
    }
    irve_params = {
        "pot_wallbox": 7360.0,
        "long": 25.0,
        "mat": "cobre",
        "aisl": "XLPE / EPR (90ºC) - RZ1-K",
        "metodo": "B1 (Bajo tubo empotrado)",
        "esquema": "Esquema 3a (Centralización contadores)",
        "red": "Monofásico (230 V)",
        "es_trifasico": False
    }
    irve_results = {
        "ib": 32.0,
        "dv_max": 2.3,
        "s_cdt": 14.58,
        "s_final": 16,
        "in_pi": 32,
        "dv_real_v": 2.094,
        "dv_real_pct": 0.91,
        "tubo_irve": "Ø 40 mm",
        "gamma": 44.0
    }

    pdf_bytes = pdf_irve.generar_pdf_irve(proyecto_info, irve_params, irve_results)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")
