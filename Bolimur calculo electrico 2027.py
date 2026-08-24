import streamlit as st
import math
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BOLIMUR INSTALACIONES INTEGRALES - Calculadora REBT", page_icon="⚡", layout="wide")

# --- DISEÑO CORPORATIVO Y ESTILOS ---
st.markdown("""
    <style>
    .bolimur-header {
        border-bottom: 3px solid #ff4b4b;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .resultado-destacado {
        background-color: #1e1e1e;
        color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #ff4b4b;
        font-size: 18px;
        font-weight: bold;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .formula-box {
        background-color: #f8f9fa;
        border: 1px solid #dcdcdc;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #333333;
    }
    .esquema-grafico {
        background-color: #fcfcfc;
        border: 2px solid #222222;
        padding: 25px;
        border-radius: 8px;
        font-family: 'Courier New', Courier, monospace;
        color: #000000;
        font-size: 14px;
        line-height: 1.5;
        white-space: pre;
        overflow-x: auto;
    }
    </style>
""", unsafe_allow_html=True)

# --- TABLA OFICIAL Y FÓRMULA DE SIMULTANEIDAD VIVIENDAS (ITC-BT-10) ---
COEF_SIMULTANEIDAD_VIVIENDAS = {
    1: 1.0, 2: 2.0, 3: 3.0, 4: 3.8, 5: 4.6, 6: 5.4, 7: 6.2, 8: 7.0, 9: 7.8,
    10: 8.2, 11: 8.6, 12: 9.0, 13: 9.4, 14: 9.8, 15: 10.2, 
    16: 12.5, 17: 13.0, 18: 13.5, 19: 14.0, 20: 14.5, 21: 15.3
}

def get_coef_simultaneidad(num):
    if num <= 0: return 0.0
    if num <= 21: return COEF_SIMULTANEIDAD_VIVIENDAS.get(num, 15.3)
    return float(round(15.3 + (num - 21) * 0.5, 1))

METODOS_INSTALACION = {
    "B1 (Bajo tubo empotrado en pared aislante - Habitual Viviendas)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas / empotrado"},
    "B2 (Bajo tubo en superficie / canal protectora)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Cable multiconductor fijado directamente a pared)": {"ref": "C", "desc": "Cable multiconductor en superficie o empotrado directo"},
    "D (Cables enterrados bajo tubo)": {"ref": "D", "desc": "Instalación subterránea"}
}

GAMMA_MAP = {
    ("cobre", "PVC (70ºC)"): 48.5,
    ("cobre", "XLPE / EPR (90ºC)"): 44.0,
    ("aluminio", "PVC (70ºC)"): 31.0,
    ("aluminio", "XLPE / EPR (90ºC)"): 28.0
}

SECCIONES_COMERCIALES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
IZ_COBRE_TUBO = {1.5: 14.5, 2.5: 20.0, 4: 26.0, 6: 34.0, 10: 46.0, 16: 61.0, 25: 80.0, 35: 99.0, 50: 119.0, 70: 151.0, 95: 182.0}
CALIBRES_INTERRUPTORES = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400]

def seleccionar_seccion_optima(s_necesaria):
    for sec in SECCIONES_COMERCIALES:
        if sec >= s_necesaria:
            return sec
    return SECCIONES_COMERCIALES[-1]

def seleccionar_proteccion(ib):
    for cal in CALIBRES_INTERRUPTORES:
        if cal >= ib:
            return cal
    return CALIBRES_INTERRUPTORES[-1]

# --- ESTADO INICIAL DE LA SESIÓN ---
if 'nombre_proyecto' not in st.session_state:
    st.session_state.nombre_proyecto = "Estudio Eléctrico Edificio Plurifamiliar"
if 'grupos_viviendas' not in st.session_state:
    st.session_state.grupos_viviendas = [{"nombre": "Viviendas Básicas", "qty": 16, "pot": 5750, "nocturna": False}]
if 'servicios_generales' not in st.session_state:
    st.session_state.servicios_generales = [{"nombre": "Ascensor Común Trifásico", "potencia": 4000, "tipo": "elevator", "qty": 1}]
if 'locales' not in st.session_state:
    st.session_state.locales = [{"nombre": "Local Comercial A", "superficie": 40, "qty": 1}]

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.markdown("""
    <div style="background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 4px solid #ff4b4b; margin-bottom: 15px;">
        <h3 style="color: white; margin: 0; font-size: 16px;">⚡ BOLIMUR</h3>
        <p style="color: #b0b0b0; font-size: 12px; margin: 5px 0 0 0;">Instalaciones Integrales<br>Murcia, España</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 Gestión de Proyectos")
st.session_state.nombre_proyecto = st.sidebar.text_input("Nombre del Proyecto", st.session_state.nombre_proyecto)

datos_proyecto = {
    "nombre_proyecto": st.session_state.nombre_proyecto,
    "grupos_viviendas": st.session_state.grupos_viviendas,
    "servicios_generales": st.session_state.servicios_generales,
    "locales": st.session_state.locales
}
json_str = json.dumps(datos_proyecto, indent=4)
st.sidebar.download_button(
    label="💾 Guardar Proyecto (JSON)",
    data=json_str,
    file_name=f"{st.session_state.nombre_proyecto.replace(' ', '_')}.json",
    mime="application/json"
)

archivo_subido = st.sidebar.file_uploader("📂 Cargar Proyecto Guardado", type=["json"])
if archivo_subido is not None:
    try:
        proyecto_cargado = json.load(archivo_subido)
        st.session_state.nombre_proyecto = proyecto_cargado.get("nombre_proyecto", "Proyecto")
        st.session_state.grupos_viviendas = proyecto_cargado.get("grupos_viviendas", [])
        st.session_state.servicios_generales = proyecto_cargado.get("servicios_generales", [])
        st.session_state.locales = proyecto_cargado.get("locales", [])
        st.sidebar.success("✅ ¡Proyecto cargado con éxito!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error al leer el archivo: {e}")

st.sidebar.markdown("---")

# --- PESTAÑAS PRINCIPALES ---
pestanas = st.tabs([
    "🏢 Previsión de Cargas (Pt)", 
    "⚡ Línea General (LGA)", 
    "🔌 Derivación Individual (DI)", 
    "📊 Tabla Guía Estilo PLC Madrid",
    "🧮 Cálculo Rápido (CDT & Icc)",
    "📐 Esquemas Unifilares",
    "📄 Informe Técnico MTD",
    "💡 Simulador Consumo"
])

# =========================================================================
# PESTAÑA 1: PREVISIÓN DE CARGAS
# =========================================================================
with pestanas[0]:
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")
    
    with st.expander("💡 ¿Qué estoy haciendo en esta sección?"):
        st.write("Calculamos la Potencia Total Prevista (Pt) sumando viviendas, locales, servicios, garajes e IRVE aplicando rigurosamente los coeficientes del REBT.")

    st.subheader("1. Viviendas del Edificio (P1)")
    if st.button("➕ Añadir Grupo de Viviendas"):
        st.session_state.grupos_viviendas.append({"nombre": f"Grupo {len(st.session_state.grupos_viviendas)+1}", "qty": 4, "pot": 9200, "nocturna": False})

    total_viviendas_edificio = 0
    pot_total_viviendas = 0

    for idx, viv in enumerate(st.session_state.grupos_viviendas):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: viv["nombre"] = st.text_input(f"Descripción #{idx+1}", viv["nombre"], key=f"viv_nom_{idx}")
        with c2: viv["qty"] = st.number_input(f"Nº Viviendas #{idx+1}", min_value=1, value=int(viv["qty"]), key=f"viv_qty_{idx}")
        with c3: viv["pot"] = st.selectbox(f"Unidad de Potencia n.º {idx+1}", [5750, 7360, 9200, 11500], index=[5750, 7360, 9200, 11500].index(viv["pot"]) if viv["pot"] in [5750, 7360, 9200, 11500] else 0, key=f"viv_pot_{idx}")
        with c4: viv["nocturna"] = st.checkbox(f"Tarifa Nocturna #{idx+1}", value=viv["nocturna"], key=f"viv_noc_{idx}")
        with c5:
            if st.button("🗑️", key=f"del_viv_{idx}"):
                if len(st.session_state.grupos_viviendas) > 1: st.session_state.grupos_viviendas.pop(idx); st.rerun()

        total_viviendas_edificio += viv["qty"]
        cs_grupo = float(viv["qty"]) if viv["nocturna"] else get_coef_simultaneidad(viv["qty"])
        pot_total_viviendas += int(round(viv["pot"] * cs_grupo))

    st.info(f"💡 Viviendas totales: **{total_viviendas_edificio}** | Potencia P1: **{pot_total_viviendas:,}W**")
    st.markdown("---")
    
    st.subheader("2. Locales Comerciales y Oficinas (P2)")
    if st.button("➕ Añadir local"): st.session_state.locales.append({"nombre": f"Local {len(st.session_state.locales)+1}", "superficie": 40, "qty": 1})
    pot_total_locales = 0
    for idx, loc in enumerate(st.session_state.locales):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1: loc["nombre"] = st.text_input(f"Local #{idx+1}", loc["nombre"], key=f"loc_nom_{idx}")
        with c2: loc["superficie"] = st.number_input(f"Superficie m² #{idx+1}", min_value=0.0, value=float(loc["superficie"]), key=f"loc_sup_{idx}")
        with c3: loc["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(loc["qty"]), key=f"loc_qty_{idx}")
        with c4:
            if st.button("🗑️", key=f"del_loc_{idx}"): st.session_state.locales.pop(idx); st.rerun()
        pot_total_locales += max(loc["superficie"] * 100, 3450) * loc["qty"]

    st.markdown(f"**Potencia Locales (P2):** `{int(pot_total_locales):,} W`")
    st.markdown("---")

    st.subheader("3. Servicios Generales (P3)")
    if st.button("➕ Añadir servicio"): st.session_state.servicios_generales.append({"nombre": "Servicio", "potencia": 1000, "tipo": "direct", "qty": 1})
    pot_total_servicios = 0
    for idx, serv in enumerate(st.session_state.servicios_generales):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: serv["nombre"] = st.text_input(f"Servicio #{idx+1}", serv["nombre"], key=f"serv_nom_{idx}")
        with c2: serv["potencia"] = st.number_input(f"Potencia W #{idx+1}", min_value=0, value=int(serv["potencia"]), key=f"serv_pot_{idx}")
        with c3: serv["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(serv["qty"]), key=f"serv_qty_{idx}")
        with c4: serv["tipo"] = st.selectbox(f"Tipo #{idx+1}", ["direct", "discharge", "motor", "elevator"], index=0, key=f"serv_tipo_{idx}")
        with c5:
            if st.button("🗑️", key=f"del_serv_{idx}"): st.session_state.servicios_generales.pop(idx); st.rerun()
        factor = {"direct": 1.0, "discharge": 1.8, "motor": 1.25, "elevator": 1.3}[serv["tipo"]]
        pot_total_servicios += int(serv["potencia"] * serv["qty"] * factor)

    st.markdown(f"**Potencia Servicios (P3):** `{pot_total_servicios:,} W`")
    st.markdown("---")

    st.subheader("4. Garajes e Infraestructura de Recarga de Vehículos Eléctricos - IRVE (ITC-BT-52)")
    gc1, gc2, gc3 = st.columns(3)
    with gc1: sup_garaje = st.number_input("Sup. Garaje m²", value=300)
    with gc2: plazas_garaje = st.number_input("Plazas Garaje", value=25)
    with gc3: opcion_irve = st.selectbox("Sistema de Recarga IRVE (ITC-BT-52)", ["Sin SPL [Factor = 1.0]", "Con Sistema de Protección de Línea - SPL (Reducción 90% / Factor = 0.1)"])

    pot_garaje_adjudicada = max(sup_garaje * 20, 3450 if sup_garaje > 0 else 0)
    fsim_ve = 1.0 if "Sin" in opcion_irve else 0.1
    pot_total_irve = int(round(plazas_garaje * 0.1 * 3680 * fsim_ve))

    st.markdown(f"- **Potencia Garaje (P4):** `{pot_garaje_adjudicada:,} W`")
    st.markdown(f"- **Potencia IRVE (Vehículos Eléctricos):** `{pot_total_irve:,} W`")
    st.markdown("---")

    pt_total = pot_total_viviendas + int(pot_total_locales) + pot_total_servicios + pot_garaje_adjudicada + pot_total_irve
    st.success(f"### ⚡ POTENCIA TOTAL PREVISTA (Pt): {pt_total:,} W")

# =========================================================================
# PESTAÑA 2: LGA
# =========================================================================
with pestanas[1]:
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    
    with st.expander("🏗️ Selector de Sistema de Instalación y Material (Métodos UNE-HD 60364-5-52)", expanded=True):
        metodo_lga_key = st.selectbox("Método de Instalación recomendado (por defecto B1 para viviendas):", list(METODOS_INSTALACION.keys()), key="met_lga")
        st.info(f"**Detalle del método:** {METODOS_INSTALACION[metodo_lga_key]['desc']}")

        tipo_enlace_lga = st.radio("Modelo de esquema reglamentario para la LGA:", [
            "Modelo 1: Contadores totalmente concentrados en un único local o armario principal (Límite CDT = 0.5%)",
            "Modelo 2: Centralizaciones parciales distribuidas / ramificadas (Límite CDT = 1.0%)"
        ], key="enlace_lga")

    dv_pct_lga = 0.5 if "Modelo 1" in tipo_enlace_lga else 1.0

    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        lga_pot = st.number_input("Potencia de cálculo LGA (W)", value=float(pt_total), key="lga_p")
        lga_long = st.number_input("Longitud de la LGA (m)", value=25.0, key="lga_l")
        lga_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="lga_mat")
    with lga_c2:
        lga_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="lga_ais")
        lga_cos = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.9, key="lga_cos")
        lga_icc_orig = st.number_input("Icc en el origen (kA)", value=15.0, key="lga_icc")

    gamma_lga = GAMMA_MAP.get((lga_mat, lga_aisl), 44.0)
    ib_lga = lga_pot / (math.sqrt(3) * 400 * lga_cos)
    dv_max_lga = 400 * (dv_pct_lga / 100.0)
    s_cdt_lga = (lga_pot * lga_long) / (gamma_lga * dv_max_lga * 400)
    
    s_cal_lga = 1.5
    for sec, iz_val in IZ_COBRE_TUBO.items():
        if iz_val >= ib_lga:
            s_cal_lga = sec
            break

    min_reg_lga = 10.0 if lga_mat == "cobre" else 16.0
    s_bruta_lga = max(s_cdt_lga, s_cal_lga, min_reg_lga)
    s_optima_lga = seleccionar_seccion_optima(s_bruta_lga)

    r_lga = (0.018 * lga_long) / s_optima_lga
    z_lga_tot = (400 / (lga_icc_orig * 1000)) + (2 * r_lga)
    icc_fin_lga = 400 / z_lga_tot / 1000 if z_lga_tot > 0 else 0
    prot_lga = seleccionar_proteccion(ib_lga)

    dv_real_lga_v = (lga_pot * lga_long) / (gamma_lga * s_optima_lga * 400)
    dv_real_lga_pct = (dv_real_lga_v / 400) * 100

    st.markdown("---")
    st.subheader("📐 Desglose detallado de Fórmulas y Resultados - LGA")
    st.markdown(f"""
    1. **Intensidad de Diseño (Ib):** Ib = Potencia / (Raíz de 3 * V * cos phi) = {lga_pot:.1f} / (1.732 * 400 * {lga_cos}) = **{ib_lga:.2f} A**
    2. **Sección por Caída de Tensión (Delta V <= {dv_pct_lga}%):** S = (P * L) / (gamma * Delta V * V) = ({lga_pot:.1f} * {lga_long}) / ({gamma_lga} * {dv_max_lga:.2f} * 400) = **{s_cdt_lga:.2f} mm²** (Real: **{dv_real_lga_pct:.3f}%**)
    3. **Sección por Calentamiento (Iz >= Ib):** Mínimo requerido = **{s_cal_lga} mm²** (Método {METODOS_INSTALACION[metodo_lga_key]['ref']})
    4. **Corriente de Cortocircuito (Icc final):** **{icc_fin_lga:.2f} kA**
    """)

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN A ADOPTAR (LGA): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_lga} mm²</span> de {lga_mat.upper()} ({lga_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">Protección General Asociada: Magnetotérmico de {prot_lga} A</span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 3: DERIVACIÓN INDIVIDUAL
# =========================================================================
with pestanas[2]:
    st.title("Derivación Individual - DI (ITC-BT-15)")
    
    with st.expander("🏗️ Selector de Sistema de Instalación y Material (Métodos UNE-HD 60364-5-52)", expanded=True):
        metodo_di_key = st.selectbox("Método de Instalación recomendado (por defecto B1):", list(METODOS_INSTALACION.keys()), key="met_di")
        st.info(f"**Detalle del método:** {METODOS_INSTALACION[metodo_di_key]['desc']}")

        tipo_enlace_di = st.radio("Modelo de esquema para la Derivación Individual:", [
            "Modelo A: DI desde contadores concentrados en centralización única (Límite CDT = 1.0%)",
            "Modelo B: DI desde contadores diseminados / exteriores / en viviendas (Límite CDT = 0.5%)"
        ], key="enlace_di")

    dv_pct_di = 1.0 if "Modelo A" in tipo_enlace_di else 0.5

    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Potencia de la Derivación (W)", [5750, 7360, 9200, 11500], key="di_p")
        di_long = st.number_input("Longitud de la DI (m)", value=15.0, key="di_l")
        di_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="di_mat")
    with di_c2:
        di_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="di_ais")
        di_cos = st.slider("Coseno phi (cos phi)", 0.8, 1.0, 1.0, key="di_cos")

    gamma_di = GAMMA_MAP.get((di_mat, di_aisl), 44.0)
    ib_di = di_pot / (230 * di_cos)
    dv_max_di = 230 * (dv_pct_di / 100.0)
    s_cdt_di = (2 * di_pot * di_long) / (gamma_di * dv_max_di * 230)
    
    s_cal_di = 1.5
    for sec, iz_val in IZ_COBRE_TUBO.items():
        if iz_val >= ib_di:
            s_cal_di = sec
            break

    min_reg_di = 6.0 if di_mat == "cobre" else 10.0
    s_bruta_di = max(s_cdt_di, s_cal_di, min_reg_di)
    s_optima_di = seleccionar_seccion_optima(s_bruta_di)

    r_di = (0.018 * di_long) / s_optima_di
    z_di_tot = (230 / (10000)) + (2 * r_di)
    icc_fin_di = 230 / z_di_tot / 1000 if z_di_tot > 0 else 0
    prot_di = seleccionar_proteccion(ib_di)

    dv_real_di_v = (2 * di_pot * di_long) / (gamma_di * s_optima_di * 230)
    dv_real_di_pct = (dv_real_di_v / 230) * 100

    st.markdown("---")
    st.subheader("📐 Desglose detallado de Fórmulas y Resultados - DI")
    st.markdown(f"""
    1. **Intensidad de Diseño (Ib monofásica):** Ib = Potencia / (V * cos phi) = {di_pot} / (230 * {di_cos}) = **{ib_di:.2f} A**
    2. **Sección por Caída de Tensión (Delta V <= {dv_pct_di}%):** S = (2 * P * L) / (gamma * Delta V * V) = (2 * {di_pot} * {di_long}) / ({gamma_di} * {dv_max_di:.2f} * 230) = **{s_cdt_di:.2f} mm²** (Real: **{dv_real_di_pct:.3f}%**)
    3. **Sección por Calentamiento (Iz >= Ib):** Mínimo requerido = **{s_cal_di} mm²** (Método {METODOS_INSTALACION[metodo_di_key]['ref']})
    4. **Corriente de Cortocircuito (Icc final):** **{icc_fin_di:.2f} kA**
    """)

    st.markdown("---")
    st.subheader("🎯 Comprobación del Tramo Más Desfavorable (LGA + DI Acumulada)")
    cdt_acumulada_pct = dv_real_lga_pct + dv_real_di_pct
    limite_global_conjunto = 1.5
    
    col_df1, col_df2 = st.columns(2)
    with col_df1: st.metric("Caída Acumulada (LGA + DI)", f"{cdt_acumulada_pct:.3f}%")
    with col_df2: st.metric("Límite Reglamentario Global", f"{limite_global_conjunto}%")

    if cdt_acumulada_pct <= limite_global_conjunto:
        st.success(f"✅ **Verificación superada:** Cumple estrictamente con el límite global de {limite_global_conjunto}%.")
    else:
        st.warning(f"⚠️ **Atención:** Supera el límite recomendado de {limite_global_conjunto}%.")

    st.markdown(f"""
        <div class="resultado-destacado">
            🔌 SECCIÓN A ADOPTAR (DI): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_di} mm²</span> de {di_mat.upper()} ({di_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">Protección PIA Asociado: {prot_di} A + Diferencial 30 mA</span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 4: TABLA GUÍA ESTILO PLC MADRID
# =========================================================================
with pestanas[3]:
    st.title("📊 Tablas de Cálculo Directo Estilo PLC Madrid (ITC-BT-15)")
    st.write("Consulta horizontal rápida para Derivaciones Individuales con conductores de cobre bajo tubo empotrado (método B1, cos phi = 1, gamma = 48):")

    tabla_plc_data = [
        {"Sección Min": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "6 m", "32A (7.32 kW)": "13 m", "40A (9.2 kW)": "5 m", "50A (11.5 kW)": "-", "63A (14.49 kW)": "-"},
        {"Sección Min": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "11 m", "32A (7.32 kW)": "26 m", "40A (9.2 kW)": "10 m", "50A (11.5 kW)": "-", "63A (14.49 kW)": "-"},
        {"Sección Min": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "11 m", "32A (7.32 kW)": "22 m", "40A (9.2 kW)": "8 m", "50A (11.5 kW)": "17 m", "63A (14.49 kW)": "6 m"},
        {"Sección Min": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "22 m", "32A (7.32 kW)": "44 m", "40A (9.2 kW)": "17 m", "50A (11.5 kW)": "34 m", "63A (14.49 kW)": "13 m"},
        {"Sección Min": "16 mm²", "Tubo Mín": "40 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "17 m", "32A (7.32 kW)": "33 m", "40A (9.2 kW)": "25 m", "50A (11.5 kW)": "27 m", "63A (14.49 kW)": "20 m"},
        {"Sección Min": "16 mm²", "Tubo Mín": "40 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "33 m", "32A (7.32 kW)": "66 m", "40A (9.2 kW)": "51 m", "50A (11.5 kW)": "55 m", "63A (14.49 kW)": "41 m"},
        {"Sección Min": "25 mm²", "Tubo Mín": "50 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "27 m", "32A (7.32 kW)": "53 m", "40A (9.2 kW)": "41 m", "50A (11.5 kW)": "43 m", "63A (14.49 kW)": "34 m"},
        {"Sección Min": "25 mm²", "Tubo Mín": "50 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "55 m", "32A (7.32 kW)": "106 m", "40A (9.2 kW)": "83 m", "50A (11.5 kW)": "86 m", "63A (14.49 kW)": "69 m"}
    ]
    st.dataframe(tabla_plc_data, use_container_width=True)

# =========================================================================
# PESTAÑA 5: CÁLCULO RÁPIDO
# =========================================================================
with pestanas[4]:
    st.title("🧮 Ventana de Cálculo Rápido (Justificación Analítica)")
    st.write("Calcula cualquier tramo eligiendo libremente el método de instalación reglamentario visualizando las fórmulas y cálculos desarrollados paso a paso.")

    rc1, rc2 = st.columns(2)
    with rc1:
        modo_carga = st.radio("Modo de entrada de corriente:", ["Por Potencia (W)", "Por Intensidad Directa (A)"], key="mod_q")
        if modo_carga == "Por Potencia (W)":
            val_pot_q = st.number_input("Potencia de diseño (W)", value=5000.0, key="vp_q")
            tipo_red_q = st.selectbox("Tipo de red", ["Monofásica (230V)", "Trifásica (400V)"], key="tr_q1")
            cos_q = st.slider("Coseno phi", 0.7, 1.0, 0.9, key="cos_q")
            ib_q = val_pot_q / (230 * cos_q) if "Monofásica" in tipo_red_q else val_pot_q / (math.sqrt(3) * 400 * cos_q)
        else:
            ib_q = st.number_input("Intensidad de diseño Ib (A)", value=25.0, key="ib_q1")
            tipo_red_q = st.selectbox("Tipo de red", ["Monofásica (230V)", "Trifásica (400V)"], key="tr_q2")
            val_pot_q = ib_q * 230 if "Monofásica" in tipo_red_q else ib_q * math.sqrt(3) * 400 * 0.9

        long_q = st.number_input("Longitud del tramo (m)", value=20.0, key="l_q")

    with rc2:
        metodo_q_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), key="met_q")
        mat_q = st.selectbox("Material", ["cobre", "aluminio"], key="m_q")
        ais_q = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="a_q")
        cdt_lim_q = st.number_input("Caída de Tensión máxima permitida (%)", value=3.0, key="cdt_q")
        icc_orig_q = st.number_input("Icc en origen (kA)", value=10.0, key="icc_orig_q")

    gamma_q = GAMMA_MAP.get((mat_q, ais_q), 44.0)
    v_nominal_q = 230 if "Monofásica" in tipo_red_q else 400
    dv_max_q = v_nominal_q * (cdt_lim_q / 100.0)
    
    if "Monofásica" in tipo_red_q:
        s_cdt_q = (2 * val_pot_q * long_q) / (gamma_q * dv_max_q * v_nominal_q)
    else:
        s_cdt_q = (val_pot_q * long_q) / (gamma_q * dv_max_q * v_nominal_q)

    s_cal_q = 1.5
    for sec, iz_val in IZ_COBRE_TUBO.items():
        if iz_val >= ib_q:
            s_cal_q = sec
            break

    s_opt_q = seleccionar_seccion_optima(max(s_cdt_q, s_cal_q))
    r_q = (0.018 * long_q) / s_opt_q
    
    if "Monofásica" in tipo_red_q:
        z_tot_q = (v_nominal_q / (icc_orig_q * 1000)) + (2 * r_q)
    else:
        z_tot_q = (v_nominal_q / (icc_orig_q * 1000)) + r_q
        
    icc_fin_q = v_nominal_q / z_tot_q / 1000 if z_tot_q > 0 else 0
    prot_q = seleccionar_proteccion(ib_q)

    st.markdown("---")
    st.subheader("📋 Justificación Analítica y Fórmulas Aplicadas")

    st.markdown(f"""
    <div class="formula-box">
        <b>1. Intensidad de Diseño (Ib):</b><br>
        Fórmula: Ib = Potencia / (V * cos phi) [Monofásica] o Ib = Potencia / (Raíz(3) * V * cos phi) [Trifásica]<br>
        Cálculo: {val_pot_q:.1f} / ({v_nominal_q} * {cos_q if modo_carga=='Por Potencia (W)' else '0.9'}) = <b>{ib_q:.2f} A</b>
    </div>

    <div class="formula-box">
        <b>2. Sección por Caída de Tensión (Delta V):</b><br>
        Fórmula: S = (m * P * L) / (gamma * Delta V * V) (donde m = 2 para monofásica y 1 para trifásica)<br>
        Cálculo: (2 * {val_pot_q:.1f} * {long_q}) / ({gamma_q} * {dv_max_q:.2f} * {v_nominal_q}) = <b>{s_cdt_q:.2f} mm²</b>
    </div>

    <div class="formula-box">
        <b>3. Comprobación por Calentamiento (Iz >= Ib):</b><br>
        Se requiere un conductor con admisibilidad superior a {ib_q:.2f} A bajo el método {METODOS_INSTALACION[metodo_q_key]['ref']}. Sección mínima admisible: <b>{s_cal_q} mm²</b>
    </div>

    <div class="formula-box">
        <b>4. Corriente de Cortocircuito (Icc final):<</b><br>
        Fórmula: Icc = V / Z_total<br>
        Cálculo: <b>{icc_fin_q:.2f} kA</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="resultado-destacado">
            🧮 SECCIÓN ÓPTIMA SELECCIONADA: <span style="color: #ff4b4b; font-size: 24px;">{s_opt_q} mm²</span> de {mat_q.upper()} ({ais_q})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">Protección recomendada: {prot_q} A | Icc final: {icc_fin_q:.2f} kA</span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 6: ESQUEMAS UNIFILARES EN FORMATO GRÁFICO (ESTILO PLANO TÉCNICO)
# =========================================================================
with pestanas[5]:
    st.title("📐 Esquema Unifilar Gráfico (Estilo Plano Técnico REBT)")
    st.write("Representación unifilar esquemática estructurada con símbolos de magnetotérmicos, protecciones y trazado de hilos por circuito:")

    tipo_electrificacion_grafica = st.radio("Grado de Electrificación para el Esquema Gráfico:", [
        "Grado Básico (ITC-BT-25 - 5 Circuitos)",
        "Grado Básico con C4 Desdoblado",
        "Grado Elevado (12 Circuitos)"
    ], key="tipo_elec_graf")

    if "Básico" in tipo_electrificacion_grafica and "Desdoblado" not in tipo_electrificacion_grafica:
        esquema_dibujo = """
==========================================================================================
PROYECTO: """ + st.session_state.nombre_proyecto + """
GRADO DE ELECTRIFICACIÓN: BÁSICO (ITC-BT-25) - BOLIMUR INSTALACIONES INTEGRALES
==========================================================================================

   [ DI ] ──────────────── [ IGA ] ─────────────── [ SOBRETENSIONES ] ────────────── [ ID ]
    10 mm²                 25 A                     Transitorias +           40 A
   (F+N+TT)              (2 Polos)                  Permanentes (Bobina)     30 mA
     │                      │                             │                    │
     └──────────────────────┴─────────────────────────────┴────────────────────┴──┬──────────────────
                                                                                 │
         ┌───────────────────────────────────────────────────────────────────────┘
         │
         ├─(10 A)──[/]─── 2x1,5+1,5 Tubo 16 ── // ─── C1: Iluminación
         │
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C2: TC usos varios
         │
         ├─(25 A)──[/]─── 2x6,0+6,0 Tubo 25 ── // ─── C3: Cocina y Horno
         │
         ├─(20 A)──[/]─── 2x4,0+4,0 Tubo 20 ── // ─── C4: Lavadora, lavavajillas y termo
         │
         └─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C5: TC Baños y aux. de cocina
=========================================================================================="""
    elif "Desdoblado" in tipo_electrificacion_grafica:
        esquema_dibujo = """
==========================================================================================
PROYECTO: """ + st.session_state.nombre_proyecto + """
GRADO DE ELECTRIFICACIÓN: BÁSICO CON C4 DESDOBLADO - BOLIMUR INSTALACIONES INTEGRALES
==========================================================================================

   [ DI ] ──────────────── [ IGA ] ─────────────── [ SOBRETENSIONES ] ────────────── [ ID ]
    10 mm²                 25 A                     Transitorias +           40 A
   (F+N+TT)              (2 Polos)                  Permanentes              30 mA
     │                      │                             │                    │
     └──────────────────────┴─────────────────────────────┴────────────────────┴──┬──────────────────
                                                                                 │
         ┌───────────────────────────────────────────────────────────────────────┘
         │
         ├─(10 A)──[/]─── 2x1,5+1,5 Tubo 16 ── // ─── C1: Iluminación
         │
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C2: TC usos varios
         │
         ├─(25 A)──[/]─── 2x6,0+6,0 Tubo 25 ── // ─── C3: Cocina y Horno
         │
         ├─(20 A)──[/]─── 2x4,0+4,0 Tubo 20 ── // ─── C4-A: Lavadora y Termo
         │
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C4-B: Lavavajillas independiente
         │
         └─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C5: TC Baños y aux. de cocina
=========================================================================================="""
    else:
        esquema_dibujo = """
==========================================================================================
PROYECTO: """ + st.session_state.nombre_proyecto + """
GRADO DE ELECTRIFICACIÓN: ELEVADO (12 CIRCUITOS) - BOLIMUR INSTALACIONES INTEGRALES
==========================================================================================

   [ DI ] ──────────────── [ IGA ] ─────────────── [ SOBRETENSIONES ] ────────────── [ ID ]
    16 mm²                 40 A                     Transitorias +           63 A
   (F+N+TT)              (2 Polos)                  Permanentes              30 mA
     │                      │                             │                    │
     └──────────────────────┴─────────────────────────────┴────────────────────┴──┬──────────────────
                                                                                 │
         ┌───────────────────────────────────────────────────────────────────────┘
         │
         ├─(10 A)──[/]─── 2x1,5+1,5 Tubo 16 ── // ─── C1: Iluminación principal
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C2: Tomas de corriente generales
         ├─(25 A)──[/]─── 2x6,0+6,0 Tubo 25 ── // ─── C3: Cocina y horno
         ├─(20 A)──[/]─── 2x4,0+4,0 Tubo 20 ── // ─── C4-A: Lavadora y termo
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C4-B: Lavavajillas
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C5: Baños y cocina (húmedas)
         ├─(10 A)──[/]─── 2x1,5+1,5 Tubo 16 ── // ─── C6: Iluminación adicional
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C7: Tomas de corriente adicionales
         ├─(25 A)──[/]─── 2x6,0+6,0 Tubo 25 ── // ─── C8: Calefacción / Climatización
         ├─(20 A)──[/]─── 2x4,0+4,0 Tubo 20 ── // ─── C9: Aire acondicionado
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C10: Secadora independiente
         ├─(10 A)──[/]─── 2x1,5+1,5 Tubo 16 ── // ─── C11: Automatización / Domótica / Alarma
         └─(25 A)──[/]─── 2x6,0+6,0 Tubo 25 ── // ─── C12: Circuitos especiales (Hidromasaje)
=========================================================================================="""

    # Mostrar esquema en caja gráfica tipo plano
    st.markdown(f'<div class="esquema-grafico">{esquema_dibujo}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.download_button(
        label="📥 Descargar Plano Unifilar Gráfico (.txt)",
        data=esquema_dibujo,
        file_name=f"Plano_Esquema_Grafico_{st.session_state.nombre_proyecto.replace(' ', '_')}.txt",
        mime="text/plain"
    )

# =========================================================================
# PESTAÑA 7: INFORME TÉCNICO MTD
# =========================================================================
with pestanas[6]:
    st.markdown("""
        <div class="bolimur-header">
            <h1 style="color: #ff4b4b; margin: 0; font-size: 26px;">BOLIMUR INSTALACIONES INTEGRALES</h1>
            <p style="margin: 5px 0 0 0; font-size: 14px; font-weight: bold; color: #555;">MEMORIA TÉCNICA DE DISEÑO (MTD) - INSTALACIÓN ELÉCTRICA</p>
        </div>
    """, unsafe_allow_html=True)

    st.write(f"**Nombre del Proyecto:** {st.session_state.nombre_proyecto}")
    st.write("**Normativa de Aplicación:** REBT (Real Decreto 842/2002) y Guías Técnicas de Aplicación")

    texto_informe = f"""==================================================
BOLIMUR INSTALACIONES INTEGRALES
MEMORIA TÉCNICA DE DISEÑO (MTD) - INSTALACIÓN ELÉCTRICA
==================================================
Nombre del Proyecto: {st.session_state.nombre_proyecto}
Normativa: REBT (Real Decreto 842/2002)

1. RESUMEN DE PREVISIÓN DE CARGAS (ITC-BT-10)
- Potencia Total Prevista (Pt): {pt_total:,} W
- Viviendas asociadas: {total_viviendas_edificio} unidades
- Potencia Locales Comerciales (P2): {int(pot_total_locales):,} W
- Potencia Servicios Generales (P3): {pot_total_servicios:,} W
- Potencia Garaje (P4) e IRVE (ITC-BT-52): {pot_garaje_adjudicada + pot_total_irve:,} W

2. LÍNEA GENERAL DE ALIMENTACIÓN - LGA (ITC-BT-14)
- Método de Instalación: {METODOS_INSTALACION[metodo_lga_key]['ref']}
- Potencia de cálculo / Longitud: {lga_pot:,.1f} W / {lga_long} m
- Conductor seleccionado: {s_optima_lga} mm2 de {lga_mat.upper()} ({lga_aisl})
- Caída de Tensión real estimada: {dv_real_lga_pct:.3f}% (Límite admisible: {dv_pct_lga}%)
- Protección General: Magnetotérmico de {prot_lga} A

3. DERIVACIÓN INDIVIDUAL - DI (ITC-BT-15)
- Método de Instalación: {METODOS_INSTALACION[metodo_di_key]['ref']}
- Potencia / Longitud de cálculo: {di_pot} W / {di_long} m
- Conductor seleccionado: {s_optima_di} mm2 de {di_mat.upper()} ({di_aisl})
- Caída de Tensión real estimada: {dv_real_di_pct:.3f}% (Límite admisible: {dv_pct_di}%)
- Verificación Tramo Más Desfavorable (LGA + DI): {cdt_acumulada_pct:.3f}% (Límite global: 1.5%) -> CUMPLE
- Protección PIA asociado: {prot_di} A + Diferencial 30 mA

==================================================
Documento técnico redactado y verificado para BOLIMUR INSTALACIONES INTEGRALES.
"""

    st.markdown(f"""
    ---
    #### 1. RESUMEN DE PREVISIÓN DE CARGAS (ITC-BT-10)
    - **Potencia Total Prevista (Pt):** `{pt_total:,} W`
    - **Viviendas asociadas:** `{total_viviendas_edificio}` unidades
    - **Potencia en Locales Comerciales (P2):** `{int(pot_total_locales):,} W`
    - **Potencia en Servicios Generales (P3):** `{pot_total_servicios:,} W`
    - **Potencia Garaje e IRVE (ITC-BT-52):** `{pot_garaje_adjudicada + pot_total_irve:,} W`

    ---
    #### 2. DIMENSIONAMIENTO DE LA LÍNEA GENERAL DE ALIMENTACIÓN - LGA (ITC-BT-14)
    - **Método de Instalación:** {METODOS_INSTALACION[metodo_lga_key]['ref']}
    - **Potencia de cálculo / Longitud:** `{lga_pot:,.1f} W` / `{lga_long} m`
    - **Conductor seleccionado:** **`{s_optima_lga} mm²` de {lga_mat.upper()}** ({lga_aisl})
    - **Caída de Tensión real estimada:** `{dv_real_lga_pct:.3f}%` (Límite admisible: `{dv_pct_lga}%`)
    - **Protección General:** Magnetotérmico de `{prot_lga} A`

    ---
    #### 3. DIMENSIONAMIENTO DE LA DERIVACIÓN INDIVIDUAL - DI (ITC-BT-15)
    - **Método de Instalación:** {METODOS_INSTALACION[metodo_di_key]['ref']}
    - **Potencia / Longitud de cálculo:** `{di_pot} W` / `{di_long} m`
    - **Conductor seleccionado:** **`{s_optima_di} mm²` de {di_mat.upper()}** ({di_aisl})
    - **Caída de Tension real estimada:** `{dv_real_di_pct:.3f}%` (Límite admisible: `{dv_pct_di}%`)
    - **Verificación Tramo Más Desfavorable (LGA + DI):** `{cdt_acumulada_pct:.3f}%` (Límite global: `1.5%`) -> **CUMPLE**
    - **Protección PIA asociado:** `{prot_di} A` + Diferencial `30 mA`

    ---
    *Documento técnico redactado y verificado para BOLIMUR INSTALACIONES INTEGRALES.*
    """)

    st.markdown("---")
    
    st.download_button(
        label="📥 Descargar Informe Técnico Formal (.txt)",
        data=texto_informe,
        file_name=f"Informe_MTD_{st.session_state.nombre_proyecto.replace(' ', '_')}.txt",
        mime="text/plain"
    )

# =========================================================================
# PESTAÑA 8: SIMULADOR DE CONSUMO
# =========================================================================
with pestanas[7]:
    st.title("Simulador de Consumo Eléctrico")
    kw_c = st.number_input("kW contratados", value=4.6)
    kwh_m = st.number_input("kWh al mes", value=250.0)
    total_con_impuestos = ((kw_c * 0.11 * 30) + (kwh_m * 0.18)) * 1.051127 * 1.10
    st.metric("Estimación Factura Mensual", f"{total_con_impuestos:.2f} €")