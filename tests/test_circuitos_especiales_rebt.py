# -*- coding: utf-8 -*-
import pytest
import streamlit as st
from modulos import calculo_rapido
from modulos import memoria_tecnica_industria

def test_presets_calculo_rapido_existencia_y_parametros():
    presets = calculo_rapido.PRESETS_CIRCUITOS_REBT
    assert "C8.1 - Calefacción Eléctrica Línea 1 (25A - 6.0 mm²)" in presets
    assert "C8.2 - Calefacción Eléctrica Línea 2 (25A - 6.0 mm²)" in presets
    assert "C9 - Climatización / Bomba Calor Conductos Inverter (25A - 6.0 mm²)" in presets
    assert "C11 - Domótica Inalámbrica / WiFi / Zigbee / Shelly (10A - 1.5 mm²)" in presets
    assert "C11 - Domótica Cableada por Bus KNX (10A - 1.5 mm²)" in presets

    # Verificar que las notas técnicas mencionan prescripciones clave del REBT
    c8_info = presets["C8.1 - Calefacción Eléctrica Línea 1 (25A - 6.0 mm²)"]
    assert "5.750 W" in c8_info["nota"]
    assert "desdoblar" in c8_info["nota"]

    c9_info = presets["C9 - Climatización / Bomba Calor Conductos Inverter (25A - 6.0 mm²)"]
    assert "Superinmunizado" in c9_info["nota"] or "Clase A" in c9_info["nota"]

    c11_inal_info = presets["C11 - Domótica Inalámbrica / WiFi / Zigbee / Shelly (10A - 1.5 mm²)"]
    assert "60 mm" in c11_inal_info["nota"]
    assert "neutro" in c11_inal_info["nota"]

    c11_knx_info = presets["C11 - Domótica Cableada por Bus KNX (10A - 1.5 mm²)"]
    assert "KNX" in c11_knx_info["nota"]
    assert "M20" in c11_knx_info["nota"]

def test_mtd_cargar_plantilla_vivienda_elevada():
    tipo_sel = "🏡 Vivienda Electrificación Elevada con Clima, Calefacción y Domótica (ITC-BT-25 - 9.200W)"
    memoria_tecnica_industria.cargar_plantilla_por_tipo(tipo_sel)

    assert st.session_state["mtd_in_pot_inst"] == 9200.0
    assert st.session_state["mtd_in_grado"] == "Elevada"
    assert st.session_state["mtd_in_iga"] == 40
    assert "2x16 mm²" in st.session_state["mtd_in_di_cable"]
    assert "Superinmunizado" in st.session_state["mtd_in_dif"]

    circuitos = st.session_state["mtd_circuitos"]
    nombres = [c["nombre"] for c in circuitos]
    assert any("C8.1" in n for n in nombres)
    assert any("C8.2" in n for n in nombres)
    assert any("C9" in n for n in nombres)
    assert any("C11" in n for n in nombres)
