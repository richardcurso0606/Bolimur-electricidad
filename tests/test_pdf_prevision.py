# -*- coding: utf-8 -*-
import pytest
from modulos import pdf_prevision, prevision_cargas

def test_coeficiente_simultaneidad():
    assert prevision_cargas.get_coef_simultaneidad(1) == 1.0
    assert prevision_cargas.get_coef_simultaneidad(10) == 8.5
    assert prevision_cargas.get_coef_simultaneidad(20) == 15.4
    assert prevision_cargas.get_coef_simultaneidad(22) == 16.4

def test_generar_pdf_prevision_bytes():
    proyecto_info = {
        "nombre": "Edificio Residencial Test",
        "emplazamiento": "Calle Falsa 123",
        "proyectista": "Ingeniero Test",
        "expediente": "EXP-2026-TEST",
        "fecha": "02/10/2026"
    }
    grupos_viviendas = [
        {"nombre": "Planta 1 a 4", "qty": 8, "pot": 5750, "nocturna": False, "pot_calculada": 32200}
    ]
    locales = [
        {"nombre": "Local Comercial", "superficie": 120.0, "qty": 1}
    ]
    servicios_generales = [
        {"nombre": "Ascensor", "potencia": 4000.0, "qty": 1, "factor": 1.30, "cos_phi": 1.0}
    ]
    garajes = {
        "sup": 200.0,
        "plazas_irve": 10,
        "esquema_irve": "Esquema 3a",
        "spl": True
    }
    
    pdf_bytes = pdf_prevision.generar_pdf_prevision(
        proyecto_info=proyecto_info,
        grupos_viviendas=grupos_viviendas,
        k_diurno=7.0,
        viviendas_diurnas_qty=8,
        pot_total_viviendas=32200,
        locales=locales,
        pot_total_locales=12000.0,
        servicios_generales=servicios_generales,
        pot_total_servicios=5200.0,
        garajes=garajes,
        p_gar_base=4000.0,
        p_irve=1840.0,
        pot_total_garaje=5840.0,
        pt_total=55240.0
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")
