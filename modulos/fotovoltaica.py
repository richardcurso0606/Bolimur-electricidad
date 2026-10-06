# -*- coding: utf-8 -*-
"""
MÓDULO DE ENERGÍA SOLAR FOTOVOLTAICA EN AUTOCONSUMO (ITC-BT-40 / RD 244/2019)
Diseñado para la ingeniería técnica, cálculo reglamentario y ejecución de obra en calle.
Cubre tanto el cálculo de ingeniería (strings DC, cálculo térmico Voc_max/Vmp_min, protecciones,
inversor y caídas de tensión) como la experiencia real de instalación y mantenimiento de campo.
"""

import streamlit as st
import math
import io
import base64
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

# Intentar importar gestor de base de datos y PDF
try:
    from modulos import db_manager
except Exception:
    db_manager = None

try:
    from modulos import pdf_fotovoltaica
except Exception:
    pdf_fotovoltaica = None

# =========================================================================
# CONSTANTES TÉCNICAS Y REGLAMENTARIAS (REBT / CTE / UNE-EN 62548)
# =========================================================================
HSP_MURCIA_MEDIA = 5.10     # Horas Sol Pico promedio diario anual en Murcia (kWh/m²/día) - Conexión a Red
HSP_MURCIA_INVIERNO = 2.80  # Horas Sol Pico en mes desfavorable (Diciembre en Murcia) - Aisladas
TEMP_REF_STC = 25.0         # Temperatura de ensayo estándar (STC) en ºC
TEMP_MIN_DISENO = -5.0   # Temperatura ambiente mínima de diseño en Murcia / Interior (ºC)
TEMP_MAX_CELULA = 70.0   # Temperatura máxima alcanzada por la célula en cubierta en verano (ºC)
FACTOR_SEG_DC = 1.25     # Factor de seguridad REBT para Isc en generadores DC
FACTOR_SEG_AC = 1.25     # Factor de seguridad REBT ITC-BT-40 para conductores de generadores
FACTOR_CO2_KWH = 0.357   # kg CO2 evitados por cada kWh fotovoltaico generado (Mix eléctrico España)

PRESETS_PANELES = {
    "Tier 1 Monocristalino 450W (Residencial)": {
        "potencia_w": 450.0, "vmp": 41.5, "imp": 10.85, "voc": 49.8, "isc": 11.60,
        "coef_voc": -0.0028, "coef_pmp": -0.0035, "largo_m": 2.09, "ancho_m": 1.04, "peso_kg": 24.5
    },
    "Half-Cell Perc 500W (Alta Eficiencia)": {
        "potencia_w": 500.0, "vmp": 42.8, "imp": 11.69, "voc": 51.4, "isc": 12.35,
        "coef_voc": -0.0027, "coef_pmp": -0.0035, "largo_m": 2.18, "ancho_m": 1.10, "peso_kg": 26.0
    },
    "TOPCon N-Type 550W (Estándar Actual)": {
        "potencia_w": 550.0, "vmp": 42.1, "imp": 13.06, "voc": 50.2, "isc": 14.05,
        "coef_voc": -0.0025, "coef_pmp": -0.0030, "largo_m": 2.27, "ancho_m": 1.13, "peso_kg": 28.5
    },
    "Bifacial Industrial 600W (Cubiertas Grandes)": {
        "potencia_w": 600.0, "vmp": 45.4, "imp": 13.22, "voc": 54.8, "isc": 14.15,
        "coef_voc": -0.0026, "coef_pmp": -0.0032, "largo_m": 2.38, "ancho_m": 1.13, "peso_kg": 32.0
    },
    "Personalizado (Datos Ficha Técnica)": {
        "potencia_w": 500.0, "vmp": 42.0, "imp": 11.9, "voc": 50.0, "isc": 12.5,
        "coef_voc": -0.0028, "coef_pmp": -0.0035, "largo_m": 2.20, "ancho_m": 1.10, "peso_kg": 26.0
    }
}

# =========================================================================
# FUNCIONES DE CÁLCULO DE INGENIERÍA
# =========================================================================
def calcular_string_dc(
    num_modulos: int,
    pot_w: float,
    voc_stc: float,
    vmp_stc: float,
    isc_stc: float,
    imp_stc: float,
    coef_voc: float,
    coef_pmp: float,
    t_min: float = TEMP_MIN_DISENO,
    t_max: float = TEMP_MAX_CELULA,
    v_max_inversor: float = 600.0,
    v_mppt_min: float = 90.0,
    v_mppt_max: float = 550.0
) -> Dict[str, Any]:
    """
    Calcula el comportamiento térmico y eléctrico de un string fotovoltaico según UNE-EN 62548.
    Verifica que Voc a temperatura mínima no dañe el inversor y que Vmp en verano quede dentro del MPPT.
    """
    # 1. Tensión de circuito abierto máxima en la mañana más fría (T_min):
    # Voc_max = Voc_stc * [1 + coef_voc * (T_min - 25)] * num_modulos
    delta_t_frio = t_min - TEMP_REF_STC
    voc_modulo_frio = voc_stc * (1.0 + coef_voc * delta_t_frio)
    voc_string_max = round(voc_modulo_frio * num_modulos, 2)

    # 2. Tensión de máxima potencia mínima en el mediodía de verano más caluroso (T_max):
    # Vmp_min = Vmp_stc * [1 + coef_pmp * (T_max - 25)] * num_modulos
    delta_t_calor = t_max - TEMP_REF_STC
    vmp_modulo_calor = vmp_stc * (1.0 + coef_pmp * delta_t_calor)
    vmp_string_min = round(vmp_modulo_calor * num_modulos, 2)

    # 3. Tensión STC y potencia de string
    voc_string_stc = round(voc_stc * num_modulos, 2)
    vmp_string_stc = round(vmp_stc * num_modulos, 2)
    pot_string_stc = round(pot_w * num_modulos, 1)

    # 4. Corrientes de diseño (Factor de seguridad 1.25 según REBT)
    isc_diseno = round(isc_stc * FACTOR_SEG_DC, 2)
    imp_diseno = round(imp_stc, 2)

    # 5. Comprobaciones de compatibilidad con Inversor
    ok_voc_inversor = voc_string_max <= v_max_inversor
    ok_mppt_min = vmp_string_min >= v_mppt_min
    ok_mppt_max = voc_string_stc <= v_mppt_max

    # Recomendación de fusible gPV
    # Calibre gPV = 1.25 a 1.5 * Isc
    calibre_fusible_gPV = 15.0 if isc_diseno <= 15.0 else (20.0 if isc_diseno <= 20.0 else 25.0)

    return {
        "num_modulos": num_modulos,
        "pot_string_stc": pot_string_stc,
        "voc_string_max": voc_string_max,
        "vmp_string_min": vmp_string_min,
        "voc_string_stc": voc_string_stc,
        "vmp_string_stc": vmp_string_stc,
        "isc_diseno": isc_diseno,
        "imp_diseno": imp_diseno,
        "ok_voc_inversor": ok_voc_inversor,
        "ok_mppt_min": ok_mppt_min,
        "ok_mppt_max": ok_mppt_max,
        "calibre_fusible_gpv": calibre_fusible_gPV
    }

def calcular_caida_tension_dc(
    v_string: float,
    i_string: float,
    longitud_m: float,
    seccion_mm2: float,
    material: str = "cobre"
) -> Dict[str, float]:
    """
    Calcula la caída de tensión en la línea de corriente continua (DC).
    Conductividad del cobre a 70ºC (servicio normal cable solar H1Z2Z2-K): gamma = 44 m/(Ω·mm²).
    En continua: ΔU (V) = (2 * L * I) / (gamma * S)
    """
    gamma = 44.0 if material.lower() == "cobre" else 28.0
    if seccion_mm2 <= 0 or v_string <= 0:
        return {"delta_v_voltios": 0.0, "delta_v_porcentaje": 0.0}

    delta_v = (2.0 * longitud_m * i_string) / (gamma * seccion_mm2)
    porcentaje = (delta_v / v_string) * 100.0
    return {
        "delta_v_voltios": round(delta_v, 2),
        "delta_v_porcentaje": round(porcentaje, 2)
    }

def calcular_linea_ac(
    potencia_inversor_w: float,
    tension_ac: float,
    es_trifasico: bool,
    longitud_m: float,
    seccion_mm2: float,
    material: str = "cobre",
    cos_phi: float = 1.0
) -> Dict[str, Any]:
    """
    Calcula la línea de evacuación AC del inversor según ITC-BT-40.
    Aplica factor de seguridad del 125% a la corriente nominal para el dimensionamiento del conductor y PIA.
    Caída de tensión recomendada <= 1.0% para evitar sobretensiones en el inversor (> 253V).
    """
    gamma = 44.0 if material.lower() == "cobre" else 28.0

    if es_trifasico:
        # P = sqrt(3) * U * I * cos(phi)
        i_nominal = potencia_inversor_w / (math.sqrt(3.0) * tension_ac * cos_phi)
        # Caída de tensión trifásica: ΔU = (sqrt(3) * L * I * cos(phi)) / (gamma * S)
        delta_v = (math.sqrt(3.0) * longitud_m * i_nominal * cos_phi) / (gamma * seccion_mm2)
    else:
        # P = U * I * cos(phi)
        i_nominal = potencia_inversor_w / (tension_ac * cos_phi)
        # Caída de tensión monofásica: ΔU = (2 * L * I * cos(phi)) / (gamma * S)
        delta_v = (2.0 * longitud_m * i_nominal * cos_phi) / (gamma * seccion_mm2)

    i_diseno = i_nominal * FACTOR_SEG_AC  # Factor 1.25 según ITC-BT-40
    porcentaje_cdt = (delta_v / tension_ac) * 100.0

    # Determinación del PIA comercial normalizado
    pias_comerciales = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125]
    pia_sugerido = 16
    for p in pias_comerciales:
        if p >= i_diseno:
            pia_sugerido = p
            break
    else:
        pia_sugerido = 125

    # Calibre del Diferencial comercial (mínimo igual o superior al PIA)
    difs_comerciales = [25, 40, 63, 80, 100]
    dif_sugerido = 40
    for d in difs_comerciales:
        if d >= pia_sugerido:
            dif_sugerido = d
            break

    return {
        "i_nominal": round(i_nominal, 2),
        "i_diseno": round(i_diseno, 2),
        "delta_v_voltios": round(delta_v, 2),
        "delta_v_porcentaje": round(porcentaje_cdt, 2),
        "cumple_cdt_1pct": porcentaje_cdt <= 1.0,
        "cumple_cdt_rebt": porcentaje_cdt <= 1.5,
        "pia_sugerido": pia_sugerido,
        "dif_sugerido": dif_sugerido
    }

def calcular_balance_anual(
    potencia_pico_kw: float,
    hsp: float = HSP_MURCIA_MEDIA,
    performance_ratio: float = 0.80,
    pct_autoconsumo: float = 70.0,
    precio_compra_eur: float = 0.18,
    precio_excedente_eur: float = 0.08
) -> Dict[str, Any]:
    """
    Calcula la producción estimada anual en la Región de Murcia y el balance económico.
    E_anual = Pot_pico * HSP * 365 * PR
    """
    prod_anual_kwh = potencia_pico_kw * hsp * 365.0 * performance_ratio
    prod_mensual_kwh = prod_anual_kwh / 12.0

    # Desglose autoconsumo vs excedentes
    kwh_autoconsumo = prod_anual_kwh * (pct_autoconsumo / 100.0)
    kwh_excedentes = prod_anual_kwh * ((100.0 - pct_autoconsumo) / 100.0)

    ahorro_autoconsumo = kwh_autoconsumo * precio_compra_eur
    ingreso_excedentes = kwh_excedentes * precio_excedente_eur
    ahorro_total_anual = ahorro_autoconsumo + ingreso_excedentes

    co2_evitado_kg = prod_anual_kwh * FACTOR_CO2_KWH
    co2_evitado_ton = co2_evitado_kg / 1000.0

    return {
        "prod_anual_kwh": round(prod_anual_kwh, 1),
        "prod_mensual_kwh": round(prod_mensual_kwh, 1),
        "kwh_autoconsumo": round(kwh_autoconsumo, 1),
        "kwh_excedentes": round(kwh_excedentes, 1),
        "ahorro_autoconsumo_eur": round(ahorro_autoconsumo, 2),
        "ingreso_excedentes_eur": round(ingreso_excedentes, 2),
        "ahorro_total_anual_eur": round(ahorro_total_anual, 2),
        "co2_evitado_ton": round(co2_evitado_ton, 2)
    }

def calcular_sistema_aislado_baterias(
    consumo_diario_wh: float,
    dias_autonomia: float = 3.0,
    tension_bateria_v: float = 48.0,
    tipo_bateria: str = "Litio (LiFePO4)",
    profundidad_descarga_dod: float = 0.85,
    hsp_invierno: float = 2.80,
    rendimiento_global: float = 0.75,
    potencia_pico_modulo_w: float = 500.0,
    potencia_cargas_max_w: float = 3000.0
) -> Dict[str, Any]:
    """
    Calcula una instalación fotovoltaica aislada de red (Off-Grid) con acumulación en baterías.
    Dimensiona el campo solar para el mes más desfavorable (HSP invierno Diciembre en Murcia),
    la capacidad de baterías en Ah y kWh útiles, el regulador de carga MPPT y el inversor-cargador.
    """
    # 1. Energía diaria requerida considerando pérdidas del sistema
    e_necesaria_diaria_wh = consumo_diario_wh / max(rendimiento_global, 0.5)

    # 2. Potencia pico de paneles para el peor mes
    potencia_pico_requerida_w = e_necesaria_diaria_wh / max(hsp_invierno, 1.0)
    num_modulos = max(1, math.ceil(potencia_pico_requerida_w / potencia_pico_modulo_w))
    potencia_pico_instalada_w = num_modulos * potencia_pico_modulo_w

    # 3. Capacidad del banco de baterías
    energia_util_requerida_wh = consumo_diario_wh * dias_autonomia
    energia_total_bateria_wh = energia_util_requerida_wh / max(profundidad_descarga_dod, 0.3)
    capacidad_total_ah = energia_total_bateria_wh / max(tension_bateria_v, 12.0)

    # 4. Dimensionamiento del Regulador MPPT
    corriente_regulador_a = potencia_pico_instalada_w / tension_bateria_v
    corriente_diseno_reg_a = corriente_regulador_a * 1.20
    regs_comerciales = [20, 30, 40, 50, 60, 80, 100, 150]
    reg_sugerido = 60
    for r in regs_comerciales:
        if r >= corriente_diseno_reg_a:
            reg_sugerido = r
            break
    else:
        reg_sugerido = 150

    # 5. Inversor-Cargador de Aislada (Onda Senoidal Pura)
    pot_inv_nominal_w = potencia_cargas_max_w * 1.25
    pot_inv_pico_w = pot_inv_nominal_w * 2.0
    pot_generador_kva = round((pot_inv_nominal_w * 1.3) / 1000.0, 1)

    return {
        "consumo_diario_wh": consumo_diario_wh,
        "consumo_diario_kwh": round(consumo_diario_wh / 1000.0, 2),
        "dias_autonomia": dias_autonomia,
        "tension_bateria_v": tension_bateria_v,
        "tipo_bateria": tipo_bateria,
        "dod_porcentaje": round(profundidad_descarga_dod * 100.0, 1),
        "energia_util_kwh": round(energia_util_requerida_wh / 1000.0, 2),
        "energia_total_bateria_kwh": round(energia_total_bateria_wh / 1000.0, 2),
        "capacidad_total_ah": round(capacidad_total_ah, 1),
        "potencia_pico_requerida_w": round(potencia_pico_requerida_w, 1),
        "num_modulos": num_modulos,
        "potencia_pico_instalada_w": round(potencia_pico_instalada_w, 1),
        "potencia_pico_instalada_kw": round(potencia_pico_instalada_w / 1000.0, 2),
        "corriente_regulador_a": round(corriente_regulador_a, 1),
        "corriente_diseno_reg_a": round(corriente_diseno_reg_a, 1),
        "regulador_mppt_sugerido_a": reg_sugerido,
        "inversor_nominal_w": round(pot_inv_nominal_w, 0),
        "inversor_pico_w": round(pot_inv_pico_w, 0),
        "grupo_electrogeno_kva": pot_generador_kva
    }

def clasificar_tramite_fotovoltaico(potencia_inversor_kw: float) -> Tuple[str, str, str]:
    """
    Determina si la instalación fotovoltaica requiere MTD o Proyecto de Ingeniero según ITC-BT-04 Grupo F.
    """
    if potencia_inversor_kw <= 10.0:
        tipo_doc = "Memoria Técnica de Diseño (MTD 30)"
        firmante = "Instalador Habilitado en Baja Tensión (Categoría Especialista)"
        alerta = "success"
    else:
        tipo_doc = "Proyecto Técnico de Ingeniero Colegiado"
        firmante = "Ingeniero Técnico Industrial / Graduado en Ingeniería Eléctrica con Dirección de Obra y OCA Inicial"
        alerta = "warning"
    return tipo_doc, firmante, alerta

# =========================================================================
# MODO AISLADA DE RED CON BATERÍAS (OFF-GRID)
# =========================================================================
def _renderizar_modo_aislada(user_auth, cliente_sel):
    es_osc_fv = st.session_state.get('tema_modo', 'solar') == 'oscuro'
    b_bg = "#064e3b" if es_osc_fv else "#f0fdf4"
    b_bd = "#22c55e" if es_osc_fv else "#16a34a"
    b_tit = "#4ade80" if es_osc_fv else "#15803d"
    b_sub = "#86efac" if es_osc_fv else "#166534"
    b_badge_bg = "#0f172a" if es_osc_fv else "rgba(22, 163, 74, 0.15)"

    st.markdown(f"""
        <div style="background: {b_bg}; border: 1.5px solid {b_bd}; border-radius: 8px; padding: 12px 16px; margin-bottom: 18px;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div>
                    <span style="color: {b_tit}; font-weight: bold; font-size: 16px;">🔋 Modo Instalación Solar Aislada de Red (Off-Grid con Acumulación en Baterías)</span>
                    <p style="color: {b_sub}; font-size: 12.5px; margin: 3px 0 0 0;">Dimensionamiento para el mes más desfavorable de invierno (Diciembre en Murcia: HSP = 2.80 h/día) para garantizar suministro continuo 24/7 sin red de compañía.</p>
                </div>
                <div style="background: {b_badge_bg}; border-radius: 6px; padding: 4px 10px; text-align: center; border: 1px solid {b_bd};">
                    <span style="color: {b_tit}; font-size: 12px; font-weight: bold;">HSP Invierno: 2.8 h/d</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab_ais_bat, tab_ais_pv, tab_ais_inv, tab_ais_obra, tab_ais_pdf = st.tabs([
        "🔋 1. Consumo & Banco de Baterías",
        "☀️ 2. Campo Solar & Regulador MPPT",
        "⚡ 3. Inversor-Cargador & Grupo Electrógeno",
        "🛠️ 4. Guía de Obra & Mantenimiento Off-Grid",
        "📑 5. Memoria Oficial PDF Aislada & CRM"
    ])

    with tab_ais_bat:
        st.markdown("#### 🔋 Dimensionamiento del Banco de Baterías y Autonomía")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("##### 💡 Consumo Diario de la Instalación")
            modo_calc_e = st.radio("Método de Estimación de Consumo:", ["Directo (Wh/día o kWh/día)", "Asistente por Electrodomésticos"], horizontal=True, key="pv_ais_modo_e")
            
            if "Directo" in modo_calc_e:
                e_diaria_wh = st.number_input("Consumo Diario Total Estimado (Wh/día):", min_value=100.0, max_value=50000.0, value=3500.0, step=100.0, key="pv_ais_e_directa")
            else:
                st.caption("Indica el equipamiento en la vivienda o caseta de campo:")
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    w_luces = st.number_input("Iluminación LED (Wh/día):", min_value=0.0, value=250.0, step=50.0, key="pv_ais_w_luces")
                    w_frigo = st.number_input("Frigorífico / Congelador (Wh/día):", min_value=0.0, value=900.0, step=100.0, key="pv_ais_w_frigo")
                    w_tv = st.number_input("TV / Portátil / WiFi (Wh/día):", min_value=0.0, value=400.0, step=50.0, key="pv_ais_w_tv")
                with col_e2:
                    w_bomba = st.number_input("Bomba de Agua / Presión (Wh/día):", min_value=0.0, value=650.0, step=50.0, key="pv_ais_w_bomba")
                    w_otros = st.number_input("Otros / Herramientas / Cargas (Wh/día):", min_value=0.0, value=800.0, step=100.0, key="pv_ais_w_otros")
                e_diaria_wh = w_luces + w_frigo + w_tv + w_bomba + w_otros
                st.info(f"Consumo Total Calculado: **{e_diaria_wh:.0f} Wh/día** ({e_diaria_wh/1000.0:.2f} kWh/día)")

            dias_autonomia = st.slider("Días de Autonomía Requeridos (sin sol):", min_value=1.0, max_value=5.0, value=3.0, step=0.5, key="pv_ais_dias_auto", help="Número de días nublados consecutivos que las baterías deben alimentar el consumo sin descargarse en exceso.")

        with col_c2:
            st.markdown("##### ⚙️ Parámetros del Banco de Baterías")
            tipo_bat = st.selectbox("Tecnología de Baterías:", [
                "Litio LiFePO4 (DOD 85% - Larga Duración >4000 ciclos)",
                "GEL / AGM Hermética (DOD 50% - Sin Mantenimiento)",
                "Plomo Ácido Abierto / OPzS (DOD 50% - Estacionaria Industrial)"
            ], index=0, key="pv_ais_tipo_bat")

            dod = 0.85 if "Litio" in tipo_bat else 0.50

            v_bat = st.selectbox("Tensión Nominal del Sistema de Acumulación (V):", [12.0, 24.0, 48.0], index=2, key="pv_ais_v_bat", help="12V para consumos < 1 kWh/día; 24V para 1-3 kWh/día; 48V para consumos > 3 kWh/día (estándar profesional)")

            p_cargas_max = st.number_input("Potencia Máxima Simultánea de Cargas (W):", min_value=300.0, max_value=20000.0, value=3000.0, step=250.0, key="pv_ais_p_max_w")

        # CÁLCULO OFF-GRID
        res_ais = calcular_sistema_aislado_baterias(
            consumo_diario_wh=e_diaria_wh,
            dias_autonomia=dias_autonomia,
            tension_bateria_v=v_bat,
            tipo_bateria=tipo_bat,
            profundidad_descarga_dod=dod,
            hsp_invierno=HSP_MURCIA_INVIERNO,
            rendimiento_global=0.75,
            potencia_pico_modulo_w=500.0,
            potencia_cargas_max_w=p_cargas_max
        )

        st.markdown("---")
        mb1, mb2, mb3, mb4 = st.columns(4)
        with mb1:
            st.metric("Consumo Diario", f"{res_ais['consumo_diario_kwh']:.2f} kWh/día", f"{res_ais['consumo_diario_wh']:.0f} Wh/día")
        with mb2:
            st.metric("Capacidad Total Batería", f"{res_ais['capacidad_total_ah']:.0f} Ah", f"a {v_bat:.0f} V")
        with mb3:
            st.metric("Energía Acumulada Total", f"{res_ais['energia_total_bateria_kwh']:.2f} kWh", f"DOD: {res_ais['dod_porcentaje']}%")
        with mb4:
            st.metric("Energía Útil Acumulada", f"{res_ais['energia_util_kwh']:.2f} kWh", f"{dias_autonomia} días autonomía")

        with st.container(border=True):
            st.markdown(f"""
            💡 **Configuración Recomendada de Batería ({tipo_bat.split('(')[0].strip()} a {v_bat:.0f}V):**
            - Capacidad requerida a {v_bat:.0f}V: **`{res_ais['capacidad_total_ah']:.0f} Ah`** (Energía bruta: `{res_ais['energia_total_bateria_kwh']:.2f} kWh`).
            - Si utilizas módulos comerciales de Litio de 48V (ej. Pylontech US3000 / US5000 de ~3.5 a 4.8 kWh): Requieres **`{max(1, math.ceil(res_ais['energia_total_bateria_kwh'] / 3.5))} módulos`** en paralelo.
            - Si utilizas elementos de 2V de tracción/OPzS: Requieres una serie de **`{int(v_bat / 2)} vasos de 2V`** de `{res_ais['capacidad_total_ah']:.0f} Ah` C10.
            """)

    with tab_ais_pv:
        st.markdown("#### ☀️ Dimensionamiento del Campo Solar y Regulador MPPT (Mes Desfavorable)")
        st.write(f"En una instalación aislada, el número de placas se calcula obligatoriamente para el **mes peor de invierno** (Diciembre en Murcia, HSP = **`{HSP_MURCIA_INVIERNO} h/día`**), asegurando que las baterías alcancen el 100% de carga incluso en los días más cortos del año.")

        col_pv1, col_pv2 = st.columns(2)
        with col_pv1:
            sel_preset_ais = st.selectbox("Modelo de Panel Solar para Aislada:", list(PRESETS_PANELES.keys()), index=1, key="pv_ais_mod_sel")
            p_data_ais = PRESETS_PANELES[sel_preset_ais]
            p_pot_ais = st.number_input("Potencia Panel (Wp):", min_value=100.0, max_value=700.0, value=float(p_data_ais["potencia_w"]), step=10.0, key="pv_ais_p_pot")
            p_voc_ais = st.number_input("Voc Módulo (V):", value=float(p_data_ais["voc"]), step=0.1, key="pv_ais_voc")
            p_vmp_ais = st.number_input("Vmp Módulo (V):", value=float(p_data_ais["vmp"]), step=0.1, key="pv_ais_vmp")
        with col_pv2:
            p_isc_ais = st.number_input("Isc Módulo (A):", value=float(p_data_ais["isc"]), step=0.1, key="pv_ais_isc")
            p_imp_ais = st.number_input("Imp Módulo (A):", value=float(p_data_ais["imp"]), step=0.1, key="pv_ais_imp")
            hsp_inv_ais = st.number_input("HSP Mes Desfavorable (Invierno):", min_value=1.5, max_value=5.0, value=HSP_MURCIA_INVIERNO, step=0.1, key="pv_ais_hsp_inv")
            v_max_mppt = st.selectbox("Tensión Máx. Entrada PV Regulador MPPT:", [100.0, 150.0, 250.0, 450.0], index=1, key="pv_ais_vmppt_max")

        # Recálculo con panel elegido
        res_ais = calcular_sistema_aislado_baterias(
            consumo_diario_wh=e_diaria_wh,
            dias_autonomia=dias_autonomia,
            tension_bateria_v=v_bat,
            tipo_bateria=tipo_bat,
            profundidad_descarga_dod=dod,
            hsp_invierno=hsp_inv_ais,
            rendimiento_global=0.75,
            potencia_pico_modulo_w=p_pot_ais,
            potencia_cargas_max_w=p_cargas_max
        )

        st.markdown("---")
        mpv1, mpv2, mpv3, mpv4 = st.columns(4)
        with mpv1:
            st.metric("Potencia Pico Requerida", f"{res_ais['potencia_pico_requerida_w']:.0f} Wp", f"HSP Invierno: {hsp_inv_ais} h/d")
        with mpv2:
            st.metric("Nº de Paneles Solares", f"{res_ais['num_modulos']} módulos", f"de {p_pot_ais:.0f} Wp")
        with mpv3:
            st.metric("Potencia Pico Instalada", f"{res_ais['potencia_pico_instalada_kw']:.2f} kWp", f"{res_ais['potencia_pico_instalada_w']:.0f} Wp")
        with mpv4:
            st.metric("Regulador MPPT Sugerido", f"{res_ais['regulador_mppt_sugerido_a']} A", f"Corriente cálculo: {res_ais['corriente_regulador_a']:.1f} A")

        with st.container(border=True):
            st.markdown(f"""
            ##### 🔌 Esquema del Campo Solar DC y Conexión al MPPT:
            - **Potencia Total Campo Solar:** `{res_ais['potencia_pico_instalada_w']:.0f} Wp` distribuidos en `{res_ais['num_modulos']} módulos`.
            - **Configuración de Strings recomendada:** Conectar en series de **`2 a 3 paneles`** para obtener entre 80V y 125V de trabajo, dentro del rango óptimo del regulador MPPT (límite máximo: `{v_max_mppt:.0f} V`).
            - **Corriente de Carga hacia Baterías:** `{res_ais['corriente_regulador_a']:.1f} A` a `{v_bat:.0f}V` ➔ **Regulador MPPT comercial de `{res_ais['regulador_mppt_sugerido_a']} A`** (ej. Victron SmartSolar MPPT 150/{res_ais['regulador_mppt_sugerido_a']} o similar).
            """)

    with tab_ais_inv:
        st.markdown("#### ⚡ Inversor-Cargador de Aislada y Generador de Apoyo")
        col_inv1, col_inv2 = st.columns(2)
        with col_inv1:
            st.markdown("##### 🔌 Inversor-Cargador Senoidal Puro")
            st.markdown(f"""
            - **Potencia Nominal Continua Sugerida:** `{res_ais['inversor_nominal_w']:.0f} W` (230V AC - 50 Hz).
            - **Potencia Pico de Arranque:** `{res_ais['inversor_pico_w']:.0f} W` (capacidad de sobrecarga del 200% para arranque de bombas y compresores frigoríficos).
            - **Tensión de Entrada DC:** `{v_bat:.0f} V DC`.
            - **Forma de Onda:** Onda Senoidal Pura (imprescindible para no quemar motores, bombas ni electrónica fina).
            """)
        with col_inv2:
            st.markdown("##### ⛽ Grupo Electrógeno de Apoyo / Socorro")
            st.markdown(f"""
            - **Potencia Recomendada del Generador:** `{res_ais['grupo_electrogeno_kva']:.1f} kVA` (Gasolina / Diésel a 1.500 o 3.000 rpm con AVR).
            - **Arranque Automático por Contacto Seco:** El inversor dispone de un relé libre de potencial que envía señal de arranque al grupo cuando la batería desciende del umbral crítico (ej. `< 20%` en litio o `< 46V` en sistema de 48V).
            - **Cargador AC Integrado:** El inversor rectifica la corriente del grupo y recarga la batería a 30-50A mientras alimenta simultáneamente la casa.
            """)

        st.markdown("##### 🛡️ Protecciones Críticas en Instalaciones Aisladas")
        st.markdown(f"""
        - **Fusible de Protección del Banco de Baterías:** Fusible ultrarrápido tipo **Mega / ANL de 150 A a 250 A** situado inmediatamente en el borne positivo (+) antes de llegar al inversor.
        - **Sección de Cables de Batería:** Debido a las altas corrientes a `{v_bat:.0f}V` ($I = P/V = {res_ais['inversor_nominal_w']/v_bat:.0f}\\text{ A}$), se exige cable de cobre flexible de **mínimo 35 mm² a 50 mm²**.
        - **Puesta a Tierra y Creación del Régimen de Neutro:** Conectar uno de los polos de salida AC del inversor a la pica de tierra general ($R_t \\le 15\\ \\Omega$) para definir el **Neutro de la instalación** y permitir que el interruptor diferencial de 30 mA dispare ante una derivación.
        """)

    with tab_ais_obra:
        st.markdown("#### 🛠️ Guía de Obra y Mantenimiento de Sistemas Aislados con Baterías")
        col_mo1, col_mo2 = st.columns(2)
        with col_mo1:
            st.markdown("""
            ##### 🔋 1. Sala de Baterías y Seguridad (ITC-BT-30)
            - **Ventilación Obligatoria:** Si se emplean baterías de plomo abierto u OPzS, durante la fase de carga desprenden hidrógeno. El local debe disponer de ventilación natural cruzada alta y baja al exterior para evitar riesgo de explosión (norma UNE-EN 50272-2).
            - **Bandeja Antiácido:** Banco colocado sobre bancada aislada del suelo con cubeto de retención de derrames.
            - **Temperatura de Operación:** La temperatura ideal es **20ºC a 25ºC**. Con más de 35ºC en verano, la vida de las baterías de plomo se reduce a la mitad. En invierno, si la temperatura baja de 0ºC, el BMS de las baterías de litio bloquea la carga para no degradar las celdas.
            """)
        with col_mo2:
            st.markdown("""
            ##### 🧪 2. Protocolo de Mantenimiento Preventivo
            - **Para Baterías de Plomo / OPzS:**
              1. Medir densidad del electrolito cada 3 meses con densímetro: valor correcto entre **1.24 y 1.28 g/cm³** a plena carga.
              2. Reponer nivel exclusivamente con **agua destilada o desionizada** (nunca añadir ácido sulfúrico).
              3. Programar en el regulador/inversor una **carga de ecualización periódica mensual** a 2.4V/celda durante 2 horas para eliminar cristales de sulfato de plomo.
            - **Para Baterías de Litio LiFePO4:**
              1. Comprobar periódicamente el balanceo de celdas mediante la app o display del BMS (diferencia entre celdas < 0.02V).
              2. Mantener firmware del inversor y protocolo de comunicación CAN/RS485 actualizado.
            """)

    with tab_ais_pdf:
        st.markdown("#### 📑 Generación de Memoria Oficial y Guardado CRM (Aislada)")
        col_pa1, col_pa2 = st.columns(2)
        with col_pa1:
            nom_proy_ais = st.text_input("Nombre del Proyecto:", value=f"Instalación Solar Aislada {res_ais['potencia_pico_instalada_kw']:.1f}kWp + Bat {res_ais['energia_total_bateria_kwh']:.1f}kWh - {cliente_sel.get('nombre_completo', 'Casa de Campo') if cliente_sel else 'Casa de Campo'}", key="pv_ais_nom_proy")
            tit_ais_nom = st.text_input("Titular:", value=cliente_sel.get("nombre_completo", "Propietario Casa de Campo") if cliente_sel else "Propietario Casa de Campo", key="pv_ais_tit_nom")
            tit_ais_nif = st.text_input("NIF / CIF:", value=cliente_sel.get("nif_cif", "12345678Z") if cliente_sel else "12345678Z", key="pv_ais_tit_nif")
        with col_pa2:
            dir_ais = st.text_input("Ubicación Emplazamiento:", value=cliente_sel.get("direccion_suministro", "Paraje Los Aljibes, Parcela 42, Murcia") if cliente_sel else "Paraje Los Aljibes, Parcela 42, Murcia", key="pv_ais_dir")
            muni_ais = st.selectbox("Municipio (Murcia):", ["Murcia (Capital / Pedanías)", "Cartagena", "Lorca", "Molina de Segura", "Cieza", "Yecla", "Jumilla", "Caravaca de la Cruz", "Moratalla", "Totana"], index=0, key="pv_ais_muni")

        datos_memoria_ais = {
            "nombre_proyecto": nom_proy_ais,
            "titular_nombre": tit_ais_nom,
            "titular_nif": tit_ais_nif,
            "titular_telefono": cliente_sel.get("telefono", "+34 600 000 000") if cliente_sel else "+34 600 000 000",
            "titular_email": cliente_sel.get("email", "cliente@ejemplo.com") if cliente_sel else "cliente@ejemplo.com",
            "direccion": dir_ais,
            "municipio": muni_ais,
            "cp": "30001",
            "cups": "SIN CUPS (Instalación Aislada de Red)",
            "tipo_inmueble": "Vivienda Aislada / Caseta de Campo / Bombeo",
            "empresa_instaladora": user_auth.get("nombre_empresa", "BOLIMUR INSTALACIONES Y REFORMAS"),
            "cif_empresa": user_auth.get("nif_cif", "B-73123456"),
            "num_licencia": user_auth.get("num_licencia_rebt", "REBT-30/15892"),
            "tecnico_instalador": user_auth.get("nombre_instalador", "Richard Orlando Choque Tejerina"),
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "modalidad_autoconsumo": f"Instalación Aislada de Red con Baterías ({tipo_bat.split('(')[0].strip()} {res_ais['capacidad_total_ah']:.0f}Ah @ {v_bat:.0f}V)",
            "potencia_pico_w": res_ais["potencia_pico_instalada_w"],
            "num_modulos": res_ais["num_modulos"],
            "modelo_modulo": sel_preset_ais,
            "pot_modulo_w": p_pot_ais,
            "voc_modulo": p_voc_ais,
            "vmp_modulo": p_vmp_ais,
            "isc_modulo": p_isc_ais,
            "imp_modulo": p_imp_ais,
            "num_strings": 1,
            "modulos_por_string": res_ais["num_modulos"],
            "voc_max_string": p_voc_ais * res_ais["num_modulos"],
            "vmp_min_string": p_vmp_ais * res_ais["num_modulos"] * 0.85,
            "cable_dc_seccion": "6.0 mm² Cu H1Z2Z2-K",
            "tubo_dc": "Tubo M25 UV",
            "longitud_dc": 12.0,
            "cdt_dc_pct": 0.65,
            "potencia_inversor_w": res_ais["inversor_nominal_w"],
            "tension_ac": 230.0,
            "es_trifasico": False,
            "i_nominal_ac": round(res_ais["inversor_nominal_w"] / 230.0, 2),
            "i_diseno_ac": round((res_ais["inversor_nominal_w"] / 230.0) * 1.25, 2),
            "pia_ac": 25,
            "diferencial_ac": "40A / 30mA Clase A Superinmunizado",
            "cable_ac_seccion": "6.0 mm² Cu RZ1-K",
            "tubo_ac": "Tubo M32 Libre Halógenos",
            "longitud_ac": 8.0,
            "cdt_ac_pct": 0.45,
            "hsp": hsp_inv_ais,
            "produccion_anual_kwh": round(res_ais["potencia_pico_instalada_kw"] * 5.10 * 365 * 0.80, 1),
            "ahorro_anual_eur": round((res_ais["consumo_diario_kwh"] * 365) * 0.22, 2),
            "co2_anual_ton": round((res_ais["potencia_pico_instalada_kw"] * 5.10 * 365 * 0.80 * 0.357) / 1000.0, 2),
            "resistencia_tierra_ohm": 11.2,
            "aislamiento_dc_mohm": 92.0,
            "aislamiento_ac_mohm": 115.0
        }

        col_ba1, col_ba2 = st.columns(2)
        with col_ba1:
            if st.button("💾 Guardar Proyecto Aislada en CRM", type="primary", key="btn_save_crm_aislada", use_container_width=True):
                if db_manager:
                    c_id = cliente_sel.get("id") if cliente_sel else None
                    ok_db, proy_id = db_manager.guardar_proyecto(
                        usuario_id=user_auth.get("id", 1),
                        cliente_id=c_id,
                        nombre_proyecto=nom_proy_ais,
                        modulo="Fotovoltaica Aislada con Baterías",
                        datos=datos_memoria_ais,
                        resumen=f"{res_ais['potencia_pico_instalada_kw']} kWp Solar | Bat {res_ais['energia_total_bateria_kwh']} kWh ({res_ais['capacidad_total_ah']:.0f}Ah @ {v_bat:.0f}V) | Inv {res_ais['inversor_nominal_w']:.0f}W"
                    )
                    if ok_db:
                        st.toast(f"✅ ¡Proyecto Aislado '{nom_proy_ais}' grabado con éxito! (ID #{proy_id})", icon="☀️")
                        st.success(f"✅ ¡Proyecto Fotovoltaico Aislado '{nom_proy_ais}' guardado con éxito! (ID: {proy_id})")
                        st.balloons()
                    else:
                        st.error("Error al guardar en base de datos.")
        with col_ba2:
            if st.button("📄 Generar Memoria Oficial MTD Aislada (PDF)", key="btn_gen_pdf_aislada", use_container_width=True):
                if pdf_fotovoltaica:
                    with st.spinner("Compilando Memoria Técnica Oficial de Instalación Solar Aislada..."):
                        try:
                            pdf_bytes = pdf_fotovoltaica.generar_pdf_fotovoltaica(datos_memoria_ais)
                            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                            st.success("✅ ¡Memoria Oficial de Instalación Aislada generada correctamente!")
                            st.download_button(
                                label=f"⬇️ Descargar Memoria Fotovoltaica Aislada ({nom_proy_ais}.pdf)",
                                data=pdf_bytes,
                                file_name=f"MTD_Aislada_{res_ais['potencia_pico_instalada_kw']:.1f}kWp_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="650" type="application/pdf" style="border: 2px solid #16a34a; border-radius: 8px;"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        except Exception as ex:
                            st.error(f"Error generando PDF: {ex}")

# =========================================================================
# INTERFAZ STREAMLIT PRINCIPAL
# =========================================================================
def renderizar():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); padding: 18px 22px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">☀️ INGENIERÍA Y MONTAJE SOLAR FOTOVOLTAICO</h2>
                    <p style="color: #e0f2fe; margin: 5px 0 0 0; font-size: 13px;">Autoconsumo Conectado a Red (RD 244/2019) e Instalaciones Aisladas con Baterías (Off-Grid) | DGEAIM Murcia</p>
                </div>
                <div style="background: rgba(255,255,255,0.15); border-radius: 8px; padding: 6px 14px; text-align: center; border: 1px solid rgba(255,255,255,0.3);">
                    <span style="color: #fef08a; font-size: 11px; font-weight: bold; text-transform: uppercase;">Región de Murcia</span><br>
                    <span style="color: #ffffff; font-size: 15px; font-weight: bold;">HSP 2.8 a 5.1</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Obtener usuario autenticado
    user_auth = st.session_state.get("usuario_autenticado", {
        "id": 1,
        "nombre_instalador": "Richard Orlando Choque Tejerina",
        "nombre_empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
        "num_licencia_rebt": "REBT-30/15892",
        "nif_cif": "B-73123456",
        "localidad": "Murcia, España",
        "telefono": "+34 600 000 000"
    })

    # Barra superior con tipo de instalación y cliente CRM
    col_t_sel, col_cli_sel = st.columns([1.6, 1.4])
    with col_t_sel:
        tipologia_inst = st.radio(
            "⚡ Tipología de Instalación Fotovoltaica:",
            [
                "🌐 Conectada a Red (Autoconsumo RD 244/2019 / ITC-BT-40)",
                "🔋 Aislada de Red con Baterías (Off-Grid / Casas de Campo / Bombeo)"
            ],
            horizontal=False,
            key="pv_tipologia_sistema_radio"
        )
    with col_cli_sel:
        clientes = db_manager.listar_clientes(user_auth["id"]) if db_manager else []
        cliente_sel = None
        if clientes:
            nombres_cli = {c["id"]: f"👤 {c['nombre_completo']} ({c.get('nif_cif', '')}) - {c.get('localidad', 'Murcia')}" for c in clientes}
            cli_id = st.selectbox("Asociar Cliente CRM al Estudio Solar:", options=list(nombres_cli.keys()), format_func=lambda x: nombres_cli[x], key="pv_cli_sel")
            cliente_sel = db_manager.obtener_cliente_por_id(cli_id, user_auth["id"]) if db_manager else None
        else:
            st.info("💡 Puedes asociar clientes registrados en el CRM o ingresar los datos directamente.")

    if "Aislada" in tipologia_inst:
        _renderizar_modo_aislada(user_auth, cliente_sel)
        return

    # MODO CONECTADA A RED (AUTOCONSUMO RD 244/2019)
    col_red1, col_red2 = st.columns([2, 1])
    with col_red1:
        modalidad_ac = st.selectbox(
            "Modalidad Autoconsumo (RD 244/2019):",
            [
                "Con excedentes y compensación simplificada",
                "Sin excedentes (Inyección Cero / Anti-vertido)",
                "Con excedentes sin compensación (Venta directa)",
                "Colectivo con compensación horaria"
            ],
            index=0,
            key="pv_modalidad"
        )
    with col_red2:
        st.write("")
        st.info("🌐 Conexión a red interior según ITC-BT-40")

    # PESTAÑAS PRINCIPALES DEL MÓDULO FOTOVOLTAICO
    tab_dc, tab_ac, tab_eco, tab_obra, tab_pdf = st.tabs([
        "☀️ 1. Generador DC & Strings",
        "⚡ 2. Inversor & Evacuación AC",
        "📈 3. Balance Anual & Amortización",
        "🛠️ 4. Guía de Obra & Averías de Calle",
        "📑 5. Memoria Oficial PDF & Trámite"
    ])

    # =========================================================================
    # TAB 1: GENERADOR DC Y STRINGS
    # =========================================================================
    with tab_dc:
        st.markdown("#### ☀️ Dimensionamiento del Generador DC y Verificación Térmica de Strings")
        col_mod1, col_mod2 = st.columns(2)
        
        with col_mod1:
            sel_preset = st.selectbox("Seleccionar Modelo de Panel Fotovoltaico:", list(PRESETS_PANELES.keys()), index=2, key="pv_preset_panel")
            panel_data = PRESETS_PANELES[sel_preset].copy()

            p_pot = st.number_input("Potencia Pico del Módulo (Wp):", min_value=100.0, max_value=800.0, value=float(panel_data["potencia_w"]), step=5.0, key="pv_p_pot")
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                p_vmp = st.number_input("Tensión Vmp (V):", min_value=10.0, max_value=80.0, value=float(panel_data["vmp"]), step=0.1, key="pv_p_vmp")
                p_voc = st.number_input("Tensión Voc (V):", min_value=15.0, max_value=90.0, value=float(panel_data["voc"]), step=0.1, key="pv_p_voc")
            with col_v2:
                p_imp = st.number_input("Corriente Imp (A):", min_value=2.0, max_value=30.0, value=float(panel_data["imp"]), step=0.1, key="pv_p_imp")
                p_isc = st.number_input("Corriente Isc (A):", min_value=2.0, max_value=35.0, value=float(panel_data["isc"]), step=0.1, key="pv_p_isc")

        with col_mod2:
            st.markdown("##### ❄️ Parámetros Térmicos y Configuración")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                p_coef_voc = st.number_input("Coef. Temp. Voc (%/ºC):", value=float(panel_data["coef_voc"] * 100.0), step=0.01, format="%.3f", key="pv_coef_voc") / 100.0
                t_min_amb = st.number_input("Temp. Mínima Invierno (ºC):", min_value=-20.0, max_value=10.0, value=TEMP_MIN_DISENO, step=1.0, key="pv_t_min")
            with col_t2:
                p_coef_pmp = st.number_input("Coef. Temp. Pmp (%/ºC):", value=float(panel_data["coef_pmp"] * 100.0), step=0.01, format="%.3f", key="pv_coef_pmp") / 100.0
                t_max_cel = st.number_input("Temp. Máx. Célula Verano (ºC):", min_value=40.0, max_value=90.0, value=TEMP_MAX_CELULA, step=1.0, key="pv_t_max")

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                num_strings = st.number_input("Nº de Strings en Paralelo:", min_value=1, max_value=10, value=2, step=1, key="pv_num_strings")
            with col_s2:
                mods_por_string = st.number_input("Módulos por String:", min_value=2, max_value=30, value=6, step=1, key="pv_mods_por_string")

        # Inversor límites para comprobación
        col_inv_lim1, col_inv_lim2, col_inv_lim3 = st.columns(3)
        with col_inv_lim1:
            inv_vmax = st.number_input("Tensión Máx. Inversor Vmax (V):", min_value=300.0, max_value=1500.0, value=600.0, step=50.0, key="pv_inv_vmax")
        with col_inv_lim2:
            inv_mppt_min = st.number_input("Límite Inferior MPPT (V):", min_value=50.0, max_value=400.0, value=90.0, step=10.0, key="pv_inv_mppt_min")
        with col_inv_lim3:
            inv_mppt_max = st.number_input("Límite Superior MPPT (V):", min_value=300.0, max_value=1200.0, value=550.0, step=25.0, key="pv_inv_mppt_max")

        # CÁLCULO DE STRING
        res_string = calcular_string_dc(
            num_modulos=mods_por_string,
            pot_w=p_pot,
            voc_stc=p_voc,
            vmp_stc=p_vmp,
            isc_stc=p_isc,
            imp_stc=p_imp,
            coef_voc=p_coef_voc,
            coef_pmp=p_coef_pmp,
            t_min=t_min_amb,
            t_max=t_max_cel,
            v_max_inversor=inv_vmax,
            v_mppt_min=inv_mppt_min,
            v_mppt_max=inv_mppt_max
        )

        total_modulos = num_strings * mods_por_string
        pot_pico_total_kw = round((total_modulos * p_pot) / 1000.0, 2)
        isc_total_dc = round(res_string["isc_diseno"] * num_strings, 2)

        # CABLE SOLAR DC
        st.markdown("##### 🔌 Conductor Solar DC (Norma EN 50618 - Cable H1Z2Z2-K)")
        col_c_dc1, col_c_dc2, col_c_dc3 = st.columns(3)
        with col_c_dc1:
            long_dc_m = st.number_input("Longitud de Línea DC (m):", min_value=2.0, max_value=150.0, value=18.0, step=1.0, key="pv_long_dc")
        with col_c_dc2:
            sec_dc_mm2 = st.selectbox("Sección Cable Solar H1Z2Z2-K (mm²):", [4.0, 6.0, 10.0, 16.0], index=1, key="pv_sec_dc")
        with col_c_dc3:
            tubo_dc = st.selectbox("Canalización / Tubo Exterior:", ["Tubo Curvado M25 Libre Halógenos UV", "Tubo Rígido M25 Acero / PVC UV", "Bandeja Perforada Rejilla con Tapa"], index=0, key="pv_tubo_dc")

        res_cdt_dc = calcular_caida_tension_dc(
            v_string=res_string["vmp_string_stc"],
            i_string=res_string["imp_diseno"],
            longitud_m=long_dc_m,
            seccion_mm2=sec_dc_mm2,
            material="cobre"
        )

        # TARJETAS DE RESULTADOS DC
        st.markdown("---")
        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            st.metric("Potencia Pico Total", f"{pot_pico_total_kw:.2f} kWp", f"{total_modulos} módulos")
        with rc2:
            st.metric("Voc Máx (a -5ºC)", f"{res_string['voc_string_max']:.1f} V", f"Límite Inversor: {inv_vmax:.0f} V")
        with rc3:
            st.metric("Vmp Mín (a 70ºC)", f"{res_string['vmp_string_min']:.1f} V", f"MPPT Mín: {inv_mppt_min:.0f} V")
        with rc4:
            st.metric("Caída Tensión DC", f"{res_cdt_dc['delta_v_porcentaje']:.2f}%", f"{res_cdt_dc['delta_v_voltios']:.2f} V")

        # VALIDACIONES TÉCNICAS
        if not res_string["ok_voc_inversor"]:
            st.error(f"🚨 ¡PELIGRO DE DESTRUCCIÓN DEL INVERSOR! La tensión de circuito abierto a {t_min_amb}ºC ({res_string['voc_string_max']} V) supera la tensión máxima admitida ({inv_vmax} V). Debes reducir el número de módulos por string a {mods_por_string - 1} o inferior.")
        else:
            st.success(f"✅ Voc Máx a temperatura de helada ({res_string['voc_string_max']} V) está dentro del rango seguro (< {inv_vmax} V). Margen de seguridad: {inv_vmax - res_string['voc_string_max']:.1f} V.")

        if not res_string["ok_mppt_min"]:
            st.warning(f"⚠️ ATENCIÓN: En verano con la célula a {t_max_cel}ºC, la tensión Vmp descenderá a {res_string['vmp_string_min']} V, por debajo del arranque MPPT ({inv_mppt_min} V). El inversor perderá rendimiento.")
        else:
            st.info(f"✅ Vmp en verano ({res_string['vmp_string_min']} V) garantiza el seguimiento del punto de máxima potencia (> {inv_mppt_min} V).")

        if res_cdt_dc["delta_v_porcentaje"] > 1.5:
            st.warning(f"⚠️ Caída de tensión DC ({res_cdt_dc['delta_v_porcentaje']}%) superior al 1.5% recomendado. Considera aumentar sección a {sec_dc_mm2 * 1.5:.0f} mm².")
        else:
            st.success(f"✅ Caída de tensión en línea DC: {res_cdt_dc['delta_v_porcentaje']}% (óptima < 1.5%).")

    # =========================================================================
    # TAB 2: INVERSOR Y LÍNEA DE EVACUACIÓN AC
    # =========================================================================
    with tab_ac:
        st.markdown("#### ⚡ Dimensionamiento del Inversor y Cuadro de Protección AC (ITC-BT-40)")
        col_ac1, col_ac2 = st.columns(2)

        with col_ac1:
            tipo_red = st.radio("Tipo de Conexión a Red Interior:", ["Monofásica (230 V)", "Trifásica (400 V)"], horizontal=True, key="pv_tipo_red")
            es_tri = "Trifásica" in tipo_red
            u_nom = 400.0 if es_tri else 230.0

            pot_inv_kw = st.number_input("Potencia Nominal del Inversor (kW):", min_value=1.0, max_value=150.0, value=5.0 if not es_tri else 10.0, step=0.5, key="pv_pot_inv")
            pot_inv_w = pot_inv_kw * 1000.0

            # Ratio DC/AC
            ratio_dc_ac = round(pot_pico_total_kw / pot_inv_kw, 2) if pot_inv_kw > 0 else 1.0
            st.write(f"📊 **Ratio de Sobredimensionamiento DC/AC:** `{ratio_dc_ac:.2f}` (Recomendado entre 1.15 y 1.30 en Murcia)")

        with col_ac2:
            st.markdown("##### 📏 Línea de Evacuación AC Inversor ➔ CGMP")
            long_ac_m = st.number_input("Longitud de la Línea AC (m):", min_value=1.0, max_value=200.0, value=12.0, step=1.0, key="pv_long_ac")
            sec_ac_mm2 = st.selectbox("Sección del Conductor AC (mm² Cu):", [2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0], index=2, key="pv_sec_ac")
            tubo_ac = st.selectbox("Tubo de Conducción AC:", ["Tubo M32 Libre de Halógenos (Cca)", "Tubo M40 Libre de Halógenos (Cca)", "Bandeja Metálica Puesta a Tierra"], index=0, key="pv_tubo_ac")

        # CÁLCULOS AC
        res_ac = calcular_linea_ac(
            potencia_inversor_w=pot_inv_w,
            tension_ac=u_nom,
            es_trifasico=es_tri,
            longitud_m=long_ac_m,
            seccion_mm2=sec_ac_mm2,
            material="cobre"
        )

        st.markdown("---")
        mac1, mac2, mac3, mac4 = st.columns(4)
        with mac1:
            st.metric("Corriente Nominal Inversor", f"{res_ac['i_nominal']:.2f} A")
        with mac2:
            st.metric("Corriente Diseño (125% REBT)", f"{res_ac['i_diseno']:.2f} A", "ITC-BT-40")
        with mac3:
            st.metric("PIA Sugerido (Curva C)", f"{res_ac['pia_sugerido']} A", f"Icn ≥ 6 kA")
        with mac4:
            st.metric("Caída de Tensión AC", f"{res_ac['delta_v_porcentaje']:.2f}%", f"{res_ac['delta_v_voltios']:.2f} V")

        # ALERTA DE CAÍDA DE TENSIÓN ESTRICTA (< 1.0%)
        if not res_ac["cumple_cdt_1pct"]:
            st.warning(f"⚠️ **Caída de tensión AC ({res_ac['delta_v_porcentaje']}%) supera el 1.0% recomendado.** En horas punta de radiación, la resistencia de este cable provocará una sobreelevación de tensión. Si la red sube a 245V, el inversor puede llegar a 253V y apagarse por avería 'Grid Overvoltage'. Sube la sección a la siguiente normalizada.")
        else:
            st.success(f"✅ **Caída de tensión AC excelente ({res_ac['delta_v_porcentaje']}% <= 1.0%).** Evita sobretensiones inducidas en bornes del inversor.")

        # PROTECCIONES OBLIGATORIAS ITC-BT-40
        st.markdown("##### 🛡️ Cuadro de Protección AC Normalizado")
        st.markdown(f"""
        - **Interruptor Automático Magnetotérmico (PIA):** `{res_ac['pia_sugerido']} A` Curva C, Poder de corte mínimo `6 kA` (UNE-EN 60898).
        - **Interruptor Diferencial:** `{res_ac['dif_sugerido']} A / 30 mA` Clase A Superinmunizado o Clase B con detección de corrientes de fuga continua `> 6 mA` (UNE-EN 62955).
        - **Protección contra Sobretensiones:** Combinada Permanentes (POP) + Transitorias Tipo 2 con bobina de disparo asociada al IGA.
        - **Protección Anti-Isla:** Homologada según norma **UNE-EN 50549-1** con desconexión en menos de `0.5 s` por fallo de red distribuidora.
        - **Vatímetro / Smart Meter:** Conectado en cabecera para monitorización, inyección cero o control dinámico de excedentes.
        """)

        # CLASIFICACIÓN ADMINISTRATIVA
        tipo_doc, firmante, clase_alerta = clasificar_tramite_fotovoltaico(pot_inv_kw)
        with st.container(border=True):
            st.markdown(f"#### 🏛️ Tramitación Administrativa en Murcia (ITC-BT-04 Grupo F)")
            if pot_inv_kw <= 10.0:
                st.success(f"✅ **Potencia Inversor: {pot_inv_kw} kW (≤ 10 kW)** ➔ Se tramita mediante **{tipo_doc}** firmada directamente por el **{firmante}**.")
            else:
                st.warning(f"⚠️ **Potencia Inversor: {pot_inv_kw} kW (> 10 kW)** ➔ ¡Supera el límite de MTD! Requiere **{tipo_doc}**, Dirección de Obra visada y Acta de Inspección Inicial por OCA.")

    # =========================================================================
    # TAB 3: BALANCE ENERGÉTICO Y AMORTIZACIÓN (MURCIA)
    # =========================================================================
    with tab_eco:
        st.markdown("#### 📈 Balance Energético Anual, Ahorro Económico y Reducción de CO2")
        col_ec1, col_ec2 = st.columns(2)

        with col_ec1:
            hsp_in = st.number_input("Horas Sol Pico en Emplazamiento (HSP diaria promedio):", min_value=3.0, max_value=7.0, value=HSP_MURCIA_MEDIA, step=0.1, key="pv_hsp")
            pr_in = st.slider("Performance Ratio (PR) del Sistema:", min_value=0.70, max_value=0.90, value=0.80, step=0.01, format="%.2f", key="pv_pr", help="Rendimiento global considerando pérdidas por temperatura, suciedad y cableado")
            pct_autoconsumo = st.slider("Porcentaje de Autoconsumo Directo Estimado (%):", min_value=10, max_value=100, value=65, step=5, key="pv_pct_auto")

        with col_ec2:
            coste_total_eur = st.number_input("Presupuesto Llave en Mano Instalación (€):", min_value=1000.0, max_value=100000.0, value=round(pot_pico_total_kw * 1150.0, 2), step=100.0, key="pv_coste_eur")
            precio_compra_eur = st.number_input("Precio de Compra de Energía Red (€/kWh):", min_value=0.05, max_value=0.50, value=0.18, step=0.01, key="pv_pr_compra")
            precio_exced_eur = st.number_input("Precio Compensación Excedentes (€/kWh):", min_value=0.02, max_value=0.25, value=0.08, step=0.01, key="pv_pr_exced")

        res_eco = calcular_balance_anual(
            potencia_pico_kw=pot_pico_total_kw,
            hsp=hsp_in,
            performance_ratio=pr_in,
            pct_autoconsumo=pct_autoconsumo,
            precio_compra_eur=precio_compra_eur,
            precio_excedente_eur=precio_exced_eur
        )

        payback_anos = round(coste_total_eur / res_eco["ahorro_total_anual_eur"], 1) if res_eco["ahorro_total_anual_eur"] > 0 else 99.0

        st.markdown("---")
        ec1, ec2, ec3, ec4 = st.columns(4)
        with ec1:
            st.metric("Producción Anual Estimada", f"{res_eco['prod_anual_kwh']:,.0f} kWh/año".replace(",", "."))
        with ec2:
            st.metric("Ahorro Económico Anual", f"{res_eco['ahorro_total_anual_eur']:,.2f} €/año".replace(",", "."))
        with ec3:
            st.metric("Período de Retorno (Payback)", f"{payback_anos:.1f} años", f"Inversión {coste_total_eur:,.0f} €")
        with ec4:
            st.metric("Emisiones CO2 Evitadas", f"{res_eco['co2_evitado_ton']:.2f} tCO₂/año")

        with st.container(border=True):
            st.markdown(f"""
            ##### 💡 Desglose de Energía y Compensación
            - **Autoconsumo en Vivienda/Local:** `{res_eco['kwh_autoconsumo']:,.0f} kWh/año` ➔ Ahorro directo: `{res_eco['ahorro_autoconsumo_eur']:,.2f} €`
            - **Excedentes Inyectados a Red:** `{res_eco['kwh_excedentes']:,.0f} kWh/año` ➔ Ingreso por compensación: `{res_eco['ingreso_excedentes_eur']:,.2f} €`
            - **Producción Promedio Mensual:** `{res_eco['prod_mensual_kwh']:,.0f} kWh/mes`
            """)

    # =========================================================================
    # TAB 4: GUÍA DE OBRA DE CALLE, PROTOCOLO DE ENSAYOS Y AVERÍAS
    # =========================================================================
    with tab_obra:
        st.markdown("#### 🛠️ Guía Maestra de Montaje en Calle, Protocolo de Ensayos y Diagnóstico de Averías")
        
        col_ob1, col_ob2 = st.columns(2)
        with col_ob1:
            st.markdown("""
            ##### 🏗️ 1. Estructuras, Anclajes y Estanqueidad en Cubierta
            - **Cubierta de Teja:** Utilizar ganchos salvatejas regulables fijados directamente al forjado o vigas con taco químico o tirafondo a viga de madera/hormigón. **Nunca fijar el gancho solo a la teja.**
            - **Cubierta de Chapa Sándwich:** Fijación mediante tornillo autorroscante salvapuntas con arandela de EPDM directamente a las correas metálicas, sellado complementario con cinta de butilo o polímero MS.
            - **Azotea Plana Lastrada:** Utilizar soportes de hormigón premoldeado con inclinación 15º a 20º. Verificar carga de viento en Murcia (Zona Eólica B, Categoría de terreno III) con lastre mínimo de **40-60 kg por panel** según altura del edificio (CTE DB-SE-AE).
            - **Par de Apriete:** Respetar el par de apriete del fabricante (típicamente **10-12 Nm**) en las grapas intermedias y finales para no quebrar las células de silicio (microcracks).
            """)

            st.markdown("""
            ##### 🔌 2. Tendido DC y Conectores MC4 (¡Cero Arcos!)
            - **Crimpado Profesional:** Usar **únicamente tenaza crimpadora específica para MC4 con carraca**. Los alicates convencionales dejan falsos contactos que producen puntos calientes y arcos voltaicos en continua.
            - **Compatibilidad de Conectores:** Nunca mezclar machos y hembras de distintas marcas (ej. Stäubli original con marcas genéricas). Las tolerancias milimétricas causan fuego a largo plazo.
            - **Protección UV y Radios:** Los cables deben fijarse con bridas inoxidables o resistentes a UV bajo las guías de aluminio, sin apoyar sobre tejas ni canalones. Radio de curvatura mínimo: **5 veces el diámetro exterior**.
            """)

        with col_ob2:
            st.markdown("""
            ##### ⚡ 3. Puesta a Tierra Obligatoria (ITC-BT-18 / ITC-BT-40)
            - **Unión Equipotencial de Marcos:** Todos los módulos fotovoltaicos y perfiles de aluminio deben estar interconectados equipotencialmente con grapas de mordaza que atraviesen la capa de anodizado.
            - **Conductor de Tierra:** Conectar la estructura al embarrado de tierra general del edificio mediante conductor de cobre de **mínimo 6 mm²** (color verde-amarillo).
            - **Resistencia de Tierra:** La resistencia del circuito de tierra no debe superar los **15 Ω** (conforme a los protocolos de DGEAIM Murcia).
            """)

            st.markdown("""
            ##### 🧪 4. Protocolo Oficial de Ensayos Previos a la Conexión (ITC-BT-05)
            1. **Ensayo de Aislamiento DC a 1.000 V:** Medir entre polos (+ / -) cortocircuitados y tierra con megóhmetro calibrado. Debe ser **R_iso ≥ 1.0 MΩ**.
            2. **Comprobación de Voc y Polaridad:** Verificar con voltímetro DC que la polaridad es correcta y que la tensión en circuito abierto coincide con el cálculo a la temperatura actual antes de enchufar al inversor.
            3. **Ensayo de Aislamiento AC a 500 V:** Entre conductores activos y tierra: **R_iso ≥ 0.5 MΩ**.
            4. **Ensayo de Disparo Anti-Isla:** Cortar el IGA de la vivienda con el inversor produciendo a plena potencia; el inversor debe desconectarse en **t < 0.5 segundos**.
            """)

        # BLOQUE DE RESOLUCIÓN DE AVERÍAS FRECUENTES EN CAMPO
        st.markdown("---")
        st.markdown("##### 🚨 Manual de Resolución Rápida de Averías en Obra (Doble Visión Instalador/Ingeniero)")
        
        with st.expander("🔴 Error Inversor: 'Isolation Fault' / 'Fallo de Aislamiento DC'", expanded=False):
            st.markdown("""
            - **Causa Raíz:** Hay una derivación de un cable o panel a la estructura metálica o tierra, agravado por rocío o lluvia.
            - **Procedimiento de Calle para Localizarlo en 5 minutos:**
              1. Desconectar el string del inversor.
              2. Con el polímetro en DC, medir tensión entre polo (+) y tierra, y entre polo (-) y tierra.
              3. Si la tensión polo (+)-tierra es 120V y polo (-)-tierra es 180V (total string 300V), la fuga está exactamente a `120 / (Voc_modulo)` paneles del polo positivo.
              4. Inspeccionar visualmente ese conector o panel concreto (cable pellizcado con la grapa de aluminio o conector sumergido en agua).
            """)

        with st.expander("🔴 Error Inversor: 'Grid Overvoltage' / Tensión de Red > 253 V", expanded=False):
            st.markdown("""
            - **Causa Raíz:** La normativa europea exige que los inversores se desconecten si la tensión de red supera 253 V (+10% de 230V). Esto sucede al mediodía cuando el inversor empuja mucha corriente por un cable largo o delgado.
            - **Solución Técnica:**
              1. Medir tensión en el cuadro general (CGMP) y en los bornes AC del inversor a plena producción.
              2. Si la diferencia es > 3-4 V, la línea de evacuación AC tiene una sección insuficiente. Sustituir el cable por uno de mayor sección (ej. pasar de 4 mm² a 6 mm² o 10 mm²).
              3. Si en el CGMP ya hay > 250 V sin generar, reclamar a la distribuidora (i-DE) por toma de tomas del transformador alta.
            """)

        with st.expander("🔴 Error Inversor: 'RCD Fault' / Disparo del Diferencial AC", expanded=False):
            st.markdown("""
            - **Causa Raíz:** Capacidad parásita entre los paneles y la tierra por condensación, o fuga de componente continua hacia la red AC.
            - **Solución:**
              1. Sustituir diferencial estándar por uno de **Clase A Superinmunizado** o **Clase B** con filtro de altas frecuencias y tolerancia a 6 mA DC.
              2. Comprobar apriete de bornes y conexión correcta del neutro (no invertir fase y neutro en inversores monofásicos).
            """)

    # =========================================================================
    # TAB 5: MEMORIA OFICIAL PDF Y GUARDADO DE PROYECTO
    # =========================================================================
    with tab_pdf:
        st.markdown("#### 📑 Generación de la Memoria Técnica de Diseño Oficial (DGEAIM Murcia)")
        st.write("Genera el documento oficial visable en PDF según el modelo normalizado de la Dirección General de Energía y Actividad Industrial y Minera de la Región de Murcia (Código de Trámite 30):")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            nombre_proyecto_fv = st.text_input("Nombre del Proyecto:", value=f"Instalación Solar FV {pot_inv_kw:.1f}kW - {cliente_sel.get('nombre_completo', 'Autoconsumo') if cliente_sel else 'Autoconsumo Residencial'}", key="pv_nom_proy")
            titular_nom = st.text_input("Titular de la Instalación:", value=cliente_sel.get("nombre_completo", "D. Juan Pérez Martínez") if cliente_sel else "D. Juan Pérez Martínez", key="pv_tit_nom")
            titular_nif = st.text_input("NIF / CIF Titular:", value=cliente_sel.get("nif_cif", "12345678Z") if cliente_sel else "12345678Z", key="pv_tit_nif")
            emplazamiento_dir = st.text_input("Dirección del Emplazamiento:", value=cliente_sel.get("direccion_suministro", "C/ Mayor, nº 12, Murcia") if cliente_sel else "C/ Mayor, nº 12, Murcia", key="pv_emp_dir")
        
        with col_p2:
            muni_sel = st.selectbox("Municipio de la Región de Murcia:", [
                "Murcia (Capital / Pedanías)", "Cartagena", "Lorca", "Molina de Segura", "Alcantarilla",
                "Torre-Pacheco", "Águilas", "Cieza", "Yecla", "San Javier", "Mazarrón", "Totana"
            ], index=0, key="pv_muni_sel")
            cups_str = st.text_input("Código CUPS / Referencia Catastral:", value=cliente_sel.get("cups", "ES0021000000000000XX") if cliente_sel else "ES0021000000000000XX", key="pv_cups")
            num_registro_inst = st.text_input("Nº Registro Empresa Instaladora:", value=user_auth.get("num_licencia_rebt", "REBT-30/15892"), key="pv_reg_inst")
            tec_firmante = st.text_input("Técnico Instalador Competente:", value=user_auth.get("nombre_instalador", "Richard Orlando Choque Tejerina"), key="pv_tec_firm")

        # Preparar diccionario de datos para exportación PDF
        datos_memoria_fv = {
            "nombre_proyecto": nombre_proyecto_fv,
            "titular_nombre": titular_nom,
            "titular_nif": titular_nif,
            "titular_telefono": cliente_sel.get("telefono", "+34 600 000 000") if cliente_sel else "+34 600 000 000",
            "titular_email": cliente_sel.get("email", "cliente@ejemplo.com") if cliente_sel else "cliente@ejemplo.com",
            "direccion": emplazamiento_dir,
            "municipio": muni_sel,
            "cp": "30001",
            "cups": cups_str,
            "tipo_inmueble": "Vivienda Unifamiliar / Nave / Edificio",
            "empresa_instaladora": user_auth.get("nombre_empresa", "BOLIMUR INSTALACIONES Y REFORMAS"),
            "cif_empresa": user_auth.get("nif_cif", "B-73123456"),
            "num_licencia": num_registro_inst,
            "tecnico_instalador": tec_firmante,
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "modalidad_autoconsumo": modalidad_ac,
            "potencia_pico_w": pot_pico_total_kw * 1000.0,
            "num_modulos": total_modulos,
            "modelo_modulo": sel_preset,
            "pot_modulo_w": p_pot,
            "voc_modulo": p_voc,
            "vmp_modulo": p_vmp,
            "isc_modulo": p_isc,
            "imp_modulo": p_imp,
            "num_strings": num_strings,
            "modulos_por_string": mods_por_string,
            "voc_max_string": res_string["voc_string_max"],
            "vmp_min_string": res_string["vmp_string_min"],
            "cable_dc_seccion": f"{sec_dc_mm2} mm² Cu H1Z2Z2-K",
            "tubo_dc": tubo_dc,
            "longitud_dc": long_dc_m,
            "cdt_dc_pct": res_cdt_dc["delta_v_porcentaje"],
            "potencia_inversor_w": pot_inv_w,
            "tension_ac": u_nom,
            "es_trifasico": es_tri,
            "i_nominal_ac": res_ac["i_nominal"],
            "i_diseno_ac": res_ac["i_diseno"],
            "pia_ac": res_ac["pia_sugerido"],
            "diferencial_ac": f"{res_ac['dif_sugerido']}A / 30mA Clase A/B con 6mA DC",
            "cable_ac_seccion": f"{sec_ac_mm2} mm² Cu RZ1-K (AS)",
            "tubo_ac": tubo_ac,
            "longitud_ac": long_ac_m,
            "cdt_ac_pct": res_ac["delta_v_porcentaje"],
            "hsp": hsp_in,
            "produccion_anual_kwh": res_eco["prod_anual_kwh"],
            "ahorro_anual_eur": res_eco["ahorro_total_anual_eur"],
            "co2_anual_ton": res_eco["co2_evitado_ton"],
            "resistencia_tierra_ohm": 12.5,
            "aislamiento_dc_mohm": 85.0,
            "aislamiento_ac_mohm": 120.0
        }

        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("💾 Guardar Proyecto en Base de Datos (CRM)", type="primary", use_container_width=True):
                if db_manager:
                    c_id = cliente_sel.get("id") if cliente_sel else None
                    ok_db, proy_id = db_manager.guardar_proyecto(
                        usuario_id=user_auth.get("id", 1),
                        cliente_id=c_id,
                        nombre_proyecto=nombre_proyecto_fv,
                        modulo="Fotovoltaica Autoconsumo",
                        datos=datos_memoria_fv,
                        resumen=f"{pot_pico_total_kw} kWp DC | {pot_inv_kw} kW AC | {res_eco['prod_anual_kwh']:,.0f} kWh/año"
                    )
                    if ok_db:
                        st.toast(f"✅ ¡Proyecto fotovoltaico '{nombre_proyecto_fv}' grabado con éxito! (ID #{proy_id})", icon="☀️")
                        st.success(f"✅ ¡Proyecto fotovoltaico '{nombre_proyecto_fv}' guardado con éxito en CRM! (ID: {proy_id})")
                        st.balloons()
                    else:
                        st.error("Error al guardar en la base de datos.")
                else:
                    st.warning("Módulo db_manager no disponible.")

        with col_btn2:
            generar_pdf = st.button("📄 Generar Memoria Oficial MTD en PDF", type="secondary", use_container_width=True)

        if generar_pdf:
            if pdf_fotovoltaica:
                with st.spinner("Compilando Memoria Técnica de Diseño Fotovoltaica Oficial (DGEAIM Murcia)..."):
                    try:
                        pdf_bytes = pdf_fotovoltaica.generar_pdf_fotovoltaica(datos_memoria_fv)
                        b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
                        
                        st.success("✅ ¡Memoria Técnica de Diseño Oficial generada correctamente!")
                        st.download_button(
                            label=f"⬇️ Descargar Memoria Fotovoltaica ({nombre_proyecto_fv}.pdf)",
                            data=pdf_bytes,
                            file_name=f"MTD_Fotovoltaica_{pot_inv_kw:.0f}kW_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                        # Visor embebido
                        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="650" type="application/pdf" style="border: 2px solid #0284c7; border-radius: 8px;"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    except Exception as ex:
                        st.error(f"Error generando documento PDF: {ex}")
            else:
                st.error("El generador PDF de fotovoltaica no está disponible.")
