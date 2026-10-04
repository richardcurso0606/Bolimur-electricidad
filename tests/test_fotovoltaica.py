# -*- coding: utf-8 -*-
"""
Tests unitarios para el módulo de Energía Solar Fotovoltaica en Autoconsumo (ITC-BT-40 / RD 244/2019)
Verifica cálculos térmicos de strings, caídas de tensión DC/AC, protecciones, balance anual y PDF oficial.
"""

import pytest
from modulos import fotovoltaica as fv
from modulos import pdf_fotovoltaica

def test_calcular_string_dc_termico():
    """Verifica que el cálculo térmico Voc_max a -5ºC y Vmp_min a 70ºC sea matemáticamente exacto"""
    res = fv.calcular_string_dc(
        num_modulos=6,
        pot_w=500.0,
        voc_stc=50.0,
        vmp_stc=42.0,
        isc_stc=12.0,
        imp_stc=11.5,
        coef_voc=-0.0028,
        coef_pmp=-0.0035,
        t_min=-5.0,
        t_max=70.0,
        v_max_inversor=600.0,
        v_mppt_min=90.0,
        v_mppt_max=550.0
    )
    
    assert res["num_modulos"] == 6
    assert res["pot_string_stc"] == 3000.0
    # delta_t_frio = -5 - 25 = -30
    # voc_modulo_frio = 50 * (1 + (-0.0028)*(-30)) = 50 * (1 + 0.084) = 54.2 V
    # voc_string_max = 6 * 54.2 = 325.2 V
    assert res["voc_string_max"] == 325.2
    assert res["ok_voc_inversor"] is True
    
    # delta_t_calor = 70 - 25 = +45
    # vmp_modulo_calor = 42 * (1 + (-0.0035)*(45)) = 42 * (1 - 0.1575) = 42 * 0.8425 = 35.385 V
    # vmp_string_min = 6 * 35.385 = 212.31 V
    assert abs(res["vmp_string_min"] - 212.31) < 0.1
    assert res["ok_mppt_min"] is True
    
    # Isc de diseño = 12.0 * 1.25 = 15.0 A
    assert res["isc_diseno"] == 15.0
    assert res["calibre_fusible_gpv"] == 15.0

def test_string_dc_alerta_sobretension_inversor():
    """Verifica que detecte peligro cuando un string largo supera la tensión admisible del inversor"""
    res = fv.calcular_string_dc(
        num_modulos=14,  # Demasiados paneles para 600V
        pot_w=500.0,
        voc_stc=50.0,
        vmp_stc=42.0,
        isc_stc=12.0,
        imp_stc=11.5,
        coef_voc=-0.0028,
        coef_pmp=-0.0035,
        t_min=-5.0,
        t_max=70.0,
        v_max_inversor=600.0
    )
    # 14 * 54.2 = 758.8 V > 600V
    assert res["voc_string_max"] > 600.0
    assert res["ok_voc_inversor"] is False

def test_calcular_caida_tension_dc():
    """Verifica la fórmula en corriente continua: ΔU = (2 * L * I) / (gamma * S)"""
    res = fv.calcular_caida_tension_dc(
        v_string=250.0,
        i_string=11.0,
        longitud_m=20.0,
        seccion_mm2=6.0,
        material="cobre"
    )
    # delta_v = (2 * 20 * 11) / (44 * 6) = 440 / 264 = 1.666 V
    assert abs(res["delta_v_voltios"] - 1.67) < 0.05
    # pct = (1.666 / 250) * 100 = 0.666%
    assert abs(res["delta_v_porcentaje"] - 0.67) < 0.05

def test_calcular_linea_ac_monofasica():
    """Verifica el cálculo de línea monofásica AC con factor 125% REBT (ITC-BT-40)"""
    res = fv.calcular_linea_ac(
        potencia_inversor_w=5000.0,
        tension_ac=230.0,
        es_trifasico=False,
        longitud_m=12.0,
        seccion_mm2=6.0,
        material="cobre",
        cos_phi=1.0
    )
    # I_nom = 5000 / 230 = 21.74 A
    assert abs(res["i_nominal"] - 21.74) < 0.1
    # I_diseno = 21.74 * 1.25 = 27.17 A
    assert abs(res["i_diseno"] - 27.17) < 0.1
    # PIA comercial para 27.17A -> 32A
    assert res["pia_sugerido"] == 32
    assert res["dif_sugerido"] >= 32
    assert res["cumple_cdt_1pct"] is True

def test_calcular_linea_ac_trifasica():
    """Verifica el cálculo trifásico AC"""
    res = fv.calcular_linea_ac(
        potencia_inversor_w=10000.0,
        tension_ac=400.0,
        es_trifasico=True,
        longitud_m=15.0,
        seccion_mm2=6.0,
        material="cobre",
        cos_phi=1.0
    )
    # I_nom = 10000 / (sqrt(3) * 400) = 10000 / 692.82 = 14.43 A
    assert abs(res["i_nominal"] - 14.43) < 0.1
    # I_diseno = 14.43 * 1.25 = 18.04 A
    assert abs(res["i_diseno"] - 18.04) < 0.1
    # PIA comercial -> 20A
    assert res["pia_sugerido"] == 20

def test_calcular_balance_anual_murcia():
    """Verifica balance energético con HSP Murcia (5.10 h/día)"""
    res = fv.calcular_balance_anual(
        potencia_pico_kw=5.0,
        hsp=5.10,
        performance_ratio=0.80,
        pct_autoconsumo=70.0,
        precio_compra_eur=0.18,
        precio_excedente_eur=0.08
    )
    # Prod anual = 5.0 * 5.10 * 365 * 0.80 = 7446.0 kWh
    assert abs(res["prod_anual_kwh"] - 7446.0) < 5.0
    assert res["kwh_autoconsumo"] > 0
    assert res["kwh_excedentes"] > 0
    assert res["ahorro_total_anual_eur"] > 500.0
    assert res["co2_evitado_ton"] > 2.0

def test_clasificar_tramite_fotovoltaico():
    """Verifica límite de 10 kW según ITC-BT-04 Grupo F"""
    doc_mtd, firm_mtd, alerta_mtd = fv.clasificar_tramite_fotovoltaico(5.0)
    assert "Memoria Técnica" in doc_mtd
    assert "Instalador Habilitado" in firm_mtd
    assert alerta_mtd == "success"

    doc_proy, firm_proy, alerta_proy = fv.clasificar_tramite_fotovoltaico(15.0)
    assert "Proyecto Técnico" in doc_proy
    assert "Ingeniero" in firm_proy
    assert alerta_proy == "warning"

def test_generar_pdf_fotovoltaica():
    """Verifica la generación del PDF oficial de Memoria Técnica de Fotovoltaica"""
    datos_prueba = {
        "nombre_proyecto": "Instalación Solar FV 5kW Unifamiliar",
        "titular_nombre": "Carlos Gómez Martínez",
        "titular_nif": "48123456T",
        "titular_telefono": "+34 622 111 222",
        "titular_email": "carlos@ejemplo.com",
        "direccion": "C/ Mayor, nº 10, Murcia",
        "municipio": "Murcia (Capital / Pedanías)",
        "cp": "30001",
        "cups": "ES0021000000000000XX",
        "tipo_inmueble": "Vivienda Unifamiliar",
        "empresa_instaladora": "BOLIMUR INSTALACIONES Y REFORMAS",
        "cif_empresa": "B-73123456",
        "num_licencia": "REBT-30/15892",
        "tecnico_instalador": "Richard Orlando Choque Tejerina",
        "fecha": "04/10/2026",
        "modalidad_autoconsumo": "Con excedentes y compensación simplificada",
        "potencia_pico_w": 5500.0,
        "num_modulos": 10,
        "modelo_modulo": "TOPCon N-Type 550W",
        "pot_modulo_w": 550.0,
        "voc_modulo": 50.2,
        "vmp_modulo": 42.1,
        "isc_modulo": 14.05,
        "imp_modulo": 13.06,
        "num_strings": 2,
        "modulos_por_string": 5,
        "voc_max_string": 272.0,
        "vmp_min_string": 178.0,
        "cable_dc_seccion": "6.0 mm² Cu H1Z2Z2-K",
        "tubo_dc": "Tubo M25 UV",
        "longitud_dc": 18.0,
        "cdt_dc_pct": 0.65,
        "potencia_inversor_w": 5000.0,
        "tension_ac": 230.0,
        "es_trifasico": False,
        "i_nominal_ac": 21.74,
        "i_diseno_ac": 27.17,
        "pia_ac": 32,
        "diferencial_ac": "40A / 30mA Clase A con 6mA DC",
        "cable_ac_seccion": "6.0 mm² Cu RZ1-K (AS)",
        "tubo_ac": "Tubo M32 Libre Halógenos",
        "longitud_ac": 12.0,
        "cdt_ac_pct": 0.58,
        "hsp": 5.10,
        "produccion_anual_kwh": 8190.0,
        "ahorro_anual_eur": 1250.0,
        "co2_anual_ton": 2.92,
        "resistencia_tierra_ohm": 11.8,
        "aislamiento_dc_mohm": 95.0,
        "aislamiento_ac_mohm": 130.0
    }
    
    pdf_bytes = pdf_fotovoltaica.generar_pdf_fotovoltaica(datos_prueba)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")

def test_calcular_sistema_aislado_baterias():
    """Verifica el cálculo de una instalación solar aislada con baterías (Off-Grid)"""
    res = fv.calcular_sistema_aislado_baterias(
        consumo_diario_wh=3000.0,
        dias_autonomia=3.0,
        tension_bateria_v=48.0,
        tipo_bateria="Litio LiFePO4",
        profundidad_descarga_dod=0.85,
        hsp_invierno=2.80,
        rendimiento_global=0.75,
        potencia_pico_modulo_w=500.0,
        potencia_cargas_max_w=3000.0
    )

    assert res["consumo_diario_kwh"] == 3.0
    assert res["dias_autonomia"] == 3.0
    assert res["tension_bateria_v"] == 48.0
    # Energía útil = 3000 * 3 = 9000 Wh = 9 kWh
    assert res["energia_util_kwh"] == 9.0
    # Energía total batería = 9000 / 0.85 = 10588.2 Wh = 10.59 kWh
    assert abs(res["energia_total_bateria_kwh"] - 10.59) < 0.1
    # Capacidad total Ah = 10588.2 / 48 = 220.6 Ah
    assert abs(res["capacidad_total_ah"] - 220.6) < 1.0
    # Potencia requerida paneles = (3000 / 0.75) / 2.80 = 4000 / 2.80 = 1428.6 W
    assert abs(res["potencia_pico_requerida_w"] - 1428.6) < 1.0
    # Módulos de 500W -> ceil(1428.6 / 500) = 3 módulos = 1500 Wp
    assert res["num_modulos"] == 3
    assert res["potencia_pico_instalada_w"] == 1500.0
    # Regulador MPPT: 1500 / 48 = 31.25 A -> con 1.20 = 37.5 A -> comercial 40A
    assert res["regulador_mppt_sugerido_a"] == 40
    # Inversor nominal = 3000 * 1.25 = 3750 W
    assert res["inversor_nominal_w"] == 3750.0
    assert res["inversor_pico_w"] == 7500.0
    assert res["grupo_electrogeno_kva"] > 4.0

def test_generar_pdf_fotovoltaica_aislada():
    """Verifica la generación del PDF oficial de una instalación fotovoltaica aislada con baterías"""
    datos_aislada = {
        "nombre_proyecto": "Instalación Solar Aislada Casa de Campo 3kWp",
        "titular_nombre": "Antonio Martínez Sánchez",
        "titular_nif": "23456789W",
        "titular_telefono": "+34 655 444 333",
        "titular_email": "antonio@ejemplo.com",
        "direccion": "Paraje Los Aljibes, s/n, Murcia",
        "municipio": "Murcia (Capital / Pedanías)",
        "cp": "30001",
        "cups": "SIN CUPS (Instalación Aislada de Red)",
        "tipo_inmueble": "Vivienda Aislada",
        "empresa_instaladora": "BOLIMUR INSTALACIONES Y REFORMAS",
        "cif_empresa": "B-73123456",
        "num_licencia": "REBT-30/15892",
        "tecnico_instalador": "Richard Orlando Choque Tejerina",
        "fecha": "04/10/2026",
        "modalidad_autoconsumo": "Instalación Aislada con Baterías Litio LiFePO4 (220Ah @ 48V)",
        "potencia_pico_w": 3000.0,
        "num_modulos": 6,
        "modelo_modulo": "TOPCon N-Type 500W",
        "pot_modulo_w": 500.0,
        "voc_modulo": 50.0,
        "vmp_modulo": 42.0,
        "isc_modulo": 12.0,
        "imp_modulo": 11.5,
        "num_strings": 1,
        "modulos_por_string": 6,
        "voc_max_string": 300.0,
        "vmp_min_string": 210.0,
        "cable_dc_seccion": "6.0 mm² Cu H1Z2Z2-K",
        "tubo_dc": "Tubo M25 UV",
        "longitud_dc": 10.0,
        "cdt_dc_pct": 0.55,
        "potencia_inversor_w": 3750.0,
        "tension_ac": 230.0,
        "es_trifasico": False,
        "i_nominal_ac": 16.30,
        "i_diseno_ac": 20.38,
        "pia_ac": 25,
        "diferencial_ac": "40A / 30mA Clase A Superinmunizado",
        "cable_ac_seccion": "6.0 mm² Cu RZ1-K",
        "tubo_ac": "Tubo M32 Libre Halógenos",
        "longitud_ac": 8.0,
        "cdt_ac_pct": 0.42,
        "hsp": 2.80,
        "produccion_anual_kwh": 4380.0,
        "ahorro_anual_eur": 850.0,
        "co2_anual_ton": 1.56,
        "resistencia_tierra_ohm": 10.8,
        "aislamiento_dc_mohm": 92.0,
        "aislamiento_ac_mohm": 125.0
    }

    pdf_bytes = pdf_fotovoltaica.generar_pdf_fotovoltaica(datos_aislada)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")
