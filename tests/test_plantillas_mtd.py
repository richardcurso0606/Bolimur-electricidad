# -*- coding: utf-8 -*-
"""
Pruebas unitarias para el catálogo ampliado de plantillas MTD,
resolución inteligente por tipo, ayudas para el instalador y reglas REBT asociadas.
"""

import pytest
import streamlit as st
from modulos import memoria_tecnica_industria as mtd
from modulos import asistente_ia_rebt
from modulos import auditor_ia_rebt

def test_catalogo_plantillas_mtd_completitud():
    cat = mtd.CATALOGO_PLANTILLAS_MTD
    assert len(cat) >= 15

    claves_esperadas = [
        "vivienda_basica", "vivienda_elevada_clima", "vivienda_elevada_aerotermia",
        "vivienda_elevada_max_mono", "vivienda_unifamiliar_chalet_tri",
        "irve_garaje_comunitario", "irve_trifasico_comercial", "vivienda_con_irve_integrado",
        "autoconsumo_solar_fv", "combo_vivienda_solar_irve",
        "local_comercial_monofasico", "local_comercial_trifasico",
        "lpc_bar_restaurante", "lpc_academia_clinica", "lpc_gimnasio",
        "obra_provisional", "linea_general_alimentacion", "derivacion_individual"
    ]
    for c in claves_esperadas:
        assert c in cat, f"Falta la clave '{c}' en CATALOGO_PLANTILLAS_MTD"
        item = cat[c]
        assert "potencia_inst" in item and item["potencia_inst"] > 0
        assert "potencia_max" in item and item["potencia_max"] >= item["potencia_inst"]
        assert "tension" in item
        assert "iga" in item and item["iga"] > 0
        assert "di_cable" in item and len(item["di_cable"]) > 0
        assert "circuitos" in item and len(item["circuitos"]) > 0
        assert "cuando_elegir" in item and len(item["cuando_elegir"]) > 0
        assert "criterios_rebt" in item and len(item["criterios_rebt"]) > 0

def test_opciones_tipo_instalacion_estructura():
    opts = mtd.OPCIONES_TIPO_INSTALACION
    assert len(opts) >= 16
    assert opts[0].startswith("⚪")
    assert any("Básica" in o for o in opts)
    assert any("Aerotermia" in o for o in opts)
    assert any("Máxima Monofásica" in o for o in opts)
    assert any("Chalet Trifásica" in o for o in opts)
    assert any("IRVE" in o for o in opts)
    assert any("Solar" in o for o in opts)
    assert any("Bar / Restaurante" in o for o in opts)
    assert any("Academia" in o for o in opts)
    assert any("Gimnasio" in o for o in opts)
    assert any("Provisional de Obra" in o for o in opts)

def test_obtener_info_plantilla_resolucion():
    assert mtd.obtener_info_plantilla("⚪ -- Seleccionar Tipo de Instalación (En Blanco) --") is None
    assert mtd.obtener_info_plantilla("") is None

    # Aerotermia
    info_aero = mtd.obtener_info_plantilla("🏡 Vivienda Elevada - Aerotermia + Climatización (11.500 W - 230V - IGA 50A)")
    assert info_aero["id"] == "vivienda_elevada_aerotermia"
    assert info_aero["potencia_inst"] == 11500.0
    assert info_aero["iga"] == 50

    # Máxima monofásica
    info_max = mtd.obtener_info_plantilla("🏡 Vivienda Elevada - Máxima Monofásica (14.490 W - 230V - IGA 63A)")
    assert info_max["id"] == "vivienda_elevada_max_mono"
    assert info_max["potencia_inst"] == 14490.0
    assert info_max["iga"] == 63

    # Chalet trifásica
    info_chalet = mtd.obtener_info_plantilla("🏡 Vivienda Unifamiliar / Chalet Trifásica (17.320 W - 400V - IGA 25A Tri)")
    assert info_chalet["id"] == "vivienda_unifamiliar_chalet_tri"
    assert "Trifásico" in info_chalet["tension"]

    # Bar / Restaurante LPC
    info_bar = mtd.obtener_info_plantilla("🍽️ LPC: Bar / Restaurante / Cafetería (27.710 W - 400V - IGA 40A Tri - OCA obligatoria)")
    assert info_bar["id"] == "lpc_bar_restaurante"
    assert info_bar["potencia_inst"] == 27710.0
    assert info_bar["alerta_lpc"] is True
    assert "Pública Concurrencia" in info_bar["grado"]

    # Academia LPC
    info_acad = mtd.obtener_info_plantilla("🎓 LPC: Academia / Clínica / Centro de Enseñanza (>50 pers. - 17.320 W - 400V - OCA)")
    assert info_acad["id"] == "lpc_academia_clinica"
    assert info_acad["alerta_lpc"] is True

    # Gimnasio LPC
    info_gym = mtd.obtener_info_plantilla("🏋️ LPC: Gimnasio / Polideportivo con Duchas (20.780 W - 400V - IGA 32A Tri - OCA)")
    assert info_gym["id"] == "lpc_gimnasio"
    assert info_gym["alerta_lpc"] is True

def test_cargar_plantilla_lpc_bar_circuitos_y_seguridad():
    tipo_bar = "🍽️ LPC: Bar / Restaurante / Cafetería (27.710 W - 400V - IGA 40A Tri - OCA obligatoria)"
    mtd.cargar_plantilla_por_tipo(tipo_bar)

    assert st.session_state["mtd_in_pot_inst"] == 27710.0
    assert "Trifásico" in st.session_state["mtd_in_tension"]
    assert st.session_state["mtd_in_iga"] == 40
    assert "4x16" in st.session_state["mtd_in_di_cable"]

    circuitos = st.session_state["mtd_circuitos"]
    nombres = [c["nombre"] for c in circuitos]

    # Verificar prescripciones de Pública Concurrencia ITC-BT-28
    assert any("Línea A" in n for n in nombres), "Debe tener Línea A de alumbrado"
    assert any("Línea B" in n for n in nombres), "Debe tener doble línea B obligatoria de alumbrado"
    assert any("Emergencia" in n for n in nombres), "Debe incluir alumbrado de emergencia"
    assert any("Campana" in n or "Gas" in n for n in nombres), "Debe incluir campana con corte de gas"
    assert any("Frigoríficas" in n or "Cámaras" in n for n in nombres), "Debe incluir cámaras frigoríficas"

def test_cargar_plantilla_irve_garaje_comunitario():
    tipo_irve = "🚗 IRVE - Garaje Comunitario (Esquema 2 - 7.360 W - 230V - IGA 32A/40A)"
    mtd.cargar_plantilla_por_tipo(tipo_irve)

    assert st.session_state["mtd_in_pot_inst"] == 7360.0
    assert st.session_state["mtd_in_iga"] == 32
    assert "Esquema 2" in st.session_state["mtd_in_origen"]
    assert "IK08" in st.session_state["mtd_in_di_tubo"]
    assert "DC 6mA" in st.session_state["mtd_in_dif"] or "Clase A" in st.session_state["mtd_in_dif"]

def test_cargar_plantilla_obra_provisional():
    tipo_obra = "🏗️ Instalación Provisional de Obra (ITC-BT-33 - 15.000 W - 400V)"
    mtd.cargar_plantilla_por_tipo(tipo_obra)

    assert st.session_state["mtd_in_pot_inst"] == 15000.0
    assert st.session_state["mtd_in_curva"] == "Curva D"
    assert "CETAC" in st.session_state["mtd_circuitos"][0]["nombre"]
    assert "Emergencia" in st.session_state["mtd_in_dif"]

def test_asistente_ia_respuestas_offline_locales_y_lpc():
    # Consulta sobre locales y cálculo 100 W/m2
    resp_loc = asistente_ia_rebt.buscar_respuesta_offline("¿Cómo calcular la potencia para un local comercial con 100 w/m2?")
    assert "100" in resp_loc
    assert "3.450" in resp_loc or "3450" in resp_loc
    assert "ITC-BT-10" in resp_loc

    # Consulta sobre Pública Concurrencia y OCA
    resp_lpc = asistente_ia_rebt.buscar_respuesta_offline("¿Cuáles son los requisitos de un local de pública concurrencia y cuándo se exige OCA?")
    assert "ITC-BT-28" in resp_lpc
    assert "halógenos" in resp_lpc or "AS" in resp_lpc
    assert "doble" in resp_lpc.lower() or "emergencia" in resp_lpc.lower()
    assert "OCA" in resp_lpc

    # Consulta sobre potencias de vivienda y aerotermia
    resp_viv = asistente_ia_rebt.buscar_respuesta_offline("¿Qué potencias de vivienda y aerotermia se manejan según el REBT?")
    assert "5.750" in resp_viv or "5750" in resp_viv
    assert "9.200" in resp_viv or "9200" in resp_viv
    assert "11.500" in resp_viv or "11500" in resp_viv
    assert "14.490" in resp_viv or "14490" in resp_viv

def test_auditor_ia_con_contexto_publica_concurrencia():
    ctx = {
        "tipo": "Local de Pública Concurrencia - Bar Restaurante",
        "grado": "Pública Concurrencia (ITC-BT-28)",
        "potencia_w": 27710
    }
    res = auditor_ia_rebt._auditar_con_motor_reglas_rebt(
        tipo_evidencia="Cuadro General de Mando y Protección (CGMP)",
        descripcion_usuario="Cuadro de bar restaurante con IGA 40A y diferenciales",
        contexto_instalacion=ctx
    )
    assert res["estado"] in ("conforme", "advertencia")
    assert "ITC-BT-28" in res["normas_aplicadas"]
    criterios = [c["criterio"] for c in res["comprobaciones"]]
    assert any("Halógenos" in c or "AS" in c for c in criterios)
    assert any("OCA" in c for c in criterios)
