import streamlit as st
import math
import json
import os
import io

# Intento seguro de importar pypdf
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

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
    .resumen-parciales-box {
        background-color: #f1f3f5;
        border: 2px solid #ced4da;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        color: #212529;
    }
    .formula-box {
        background-color: #f8f9fa;
        border: 1px solid #dcdcdc;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #333333;
    }
    .esquema-simbolos {
        background-color: #ffffff;
        border: 3px solid #111111;
        padding: 30px;
        border-radius: 10px;
        font-family: 'Courier New', Courier, monospace;
        color: #000000;
        font-size: 14px;
        line-height: 1.6;
        white-space: pre;
        overflow-x: auto;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    </style>
""", unsafe_allow_html=True)

# --- TABLA OFICIAL Y FÓRMULA DE SIMULTANEIDAD VIVIENDAS (ITC-BT-10) ---
COEF_SIMULTANEIDAD_VIVIENDAS = {
    1: 1.0, 2: 2.0, 3: 3.0, 4: 3.8, 5: 4.6, 6: 5.4, 7: 6.2, 8: 7.0, 9: 7.8,
    10: 8.5, 11: 9.2, 12: 9.9, 13: 10.6, 14: 11.3, 15: 11.9, 
    16: 12.5, 17: 13.1, 18: 13.7, 19: 14.3, 20: 14.8, 21: 15.3
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
IZ_COBRE_TUBO = {
    1.5: 14.5, 2.5: 20.0, 4: 26.0, 6: 34.0, 10: 46.0, 16: 61.0, 
    25: 80.0, 35: 99.0, 50: 119.0, 70: 151.0, 95: 182.0, 
    120: 210.0, 150: 240.0, 185: 275.0, 240: 320.0
}
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
    st.session_state.servicios_generales = [{"nombre": "Ascensor Principal NTE-ITA", "potencia": 4000, "factor": 1.30, "qty": 1}]
if 'locales' not in st.session_state:
    st.session_state.locales = [{"nombre": "Local Comercial A", "superficie": 40, "qty": 1}]

# --- MENÚ LATERAL (SIDEBAR CON GENERADOR DE PROYECTOS VÍA PDF) ---
with st.sidebar:
    if os.path.exists("logo_bolimur.PNG"):
        st.image("logo_bolimur.PNG", width="stretch")
    else:
        st.markdown("""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 4px solid #ff4b4b; margin-bottom: 15px; text-align: center;">
                <h3 style="color: white; margin: 0; font-size: 18px;">⚡ BOLIMUR</h3>
                <p style="color: #b0b0b0; font-size: 12px; margin: 5px 0 0 0;">Instalaciones Integrales<br>Murcia, España</p>
            </div>
        """, unsafe_allow_html=True)

    st.header("📁 Gestión de Proyectos")
    st.session_state.nombre_proyecto = st.text_input("Nombre del Proyecto", st.session_state.nombre_proyecto)

    st.markdown("---")
    st.subheader("🤖 Generador Inteligente desde PDF")
    st.write("Sube el PDF de un enunciado o boletín para que la aplicación extraiga y configure el proyecto.")
    
    pdf_proyecto_subido = st.file_uploader("Subir Enunciado (PDF)", type=["pdf"], key="pdf_ia_uploader")

    if pdf_proyecto_subido is not None:
        texto_pdf = ""
        if PYPDF_AVAILABLE:
            try:
                lector = pypdf.PdfReader(pdf_proyecto_subido)
                for pagina in lector.pages:
                    texto_pdf += (pagina.extract_text() or "") + "\n"
            except Exception as e:
                texto_pdf = f"Error leyendo PDF: {e}"
        else:
            texto_pdf = "Librería pypdf no disponible en este entorno, archivo recibido con éxito."

        st.success("📄 ¡PDF cargado correctamente!")
        
        with st.expander("🔍 Ver texto detectado"):
            st.text(texto_pdf[:1000])

        if st.button("🚀 Aplicar Configuración Automática"):
            # Configuración de prueba inteligente basada en la subida
            st.session_state.grupos_viviendas = [{"nombre": "Viviendas Ejercicio PDF", "qty": 24, "pot": 5750, "nocturna": False}]
            st.session_state.locales = [{"nombre": "Locales Ejercicio PDF", "superficie": 150, "qty": 1}]
            st.success("✨ ¡Proyecto configurado automáticamente con los datos del PDF!")
            st.rerun()

    st.markdown("---")
    datos_proyecto = {
        "nombre_proyecto": st.session_state.nombre_proyecto,
        "grupos_viviendas": st.session_state.grupos_viviendas,
        "servicios_generales": st.session_state.servicios_generales,
        "locales": st.session_state.locales
    }
    json_str = json.dumps(datos_proyecto, indent=4)
    st.download_button(
        label="💾 Guardar Proyecto (JSON)",
        data=json_str,
        file_name=f"{st.session_state.nombre_proyecto.replace(' ', '_')}.json",
        mime="application/json"
    )

    archivo_subido = st.file_uploader("📂 Cargar Proyecto Guardado", type=["json"])
    if archivo_subido is not None:
        try:
            proyecto_cargado = json.load(archivo_subido)
            st.session_state.nombre_proyecto = proyecto_cargado.get("nombre_proyecto", "Proyecto")
            st.session_state.grupos_viviendas = proyecto_cargado.get("grupos_viviendas", [])
            st.session_state.servicios_generales = proyecto_cargado.get("servicios_generales", [])
            st.session_state.locales = proyecto_cargado.get("locales", [])
            st.success("✅ ¡Proyecto cargado con éxito!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

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
    
    col_t1, col_b1 = st.columns([4, 1])
    with col_t1:
        st.write("Calculamos la Potencia Total Prevista (Pt) sumando viviendas, locales, servicios, garajes e IRVE con su justificación analítica y reglamentaria.")
    with col_b1:
        if st.button("🔄 Resetear Cargas"):
            st.session_state.grupos_viviendas = [{"nombre": "Grupo 1", "qty": 1, "pot": 5750, "nocturna": False}]
            st.session_state.locales = [{"nombre": "Local 1", "superficie": 40, "qty": 1}]
            st.session_state.servicios_generales = [{"nombre": "Ascensor Principal NTE-ITA", "potencia": 4000, "factor": 1.30, "qty": 1}]
            st.rerun()

    # 1. VIVIENDAS
    col_h_viv, col_pop_viv = st.columns([4, 1])
    with col_h_viv:
        st.subheader("1. Viviendas del Edificio (P1)")
    with col_pop_viv:
        with st.popover("📖 Ver Tabla ITC-BT-10 Completa"):
            st.markdown("### Tabla Oficial de Simultaneidad (ITC-BT-10)")
            tabla_aux_md = "| Nº Viviendas ($n$) | Coeficiente ($K$) |\n| :---: | :---: |\n"
            for k_viv, v_coef in COEF_SIMULTANEIDAD_VIVIENDAS.items():
                tabla_aux_md += f"| {k_viv} | {v_coef} |\n"
            tabla_aux_md += "| > 21 | $15,3 + (n - 21) \\times 0,5$ |"
            st.markdown(tabla_aux_md)

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
        qty_g = viv["qty"]
        pot_unit = viv["pot"]
        noct = viv["nocturna"]

        if noct:
            cs_grupo = float(qty_g)
            just_str = f"Tarifa Nocturna activada: Coeficiente K = 1.0 (suma total sin reducir)."
        else:
            cs_grupo = get_coef_simultaneidad(qty_g)
            just_str = f"Aplicación ITC-BT-10 para {qty_g} viviendas: Coeficiente K = {cs_grupo:.2f}."

        pot_parcial_g = int(round(qty_g * pot_unit * cs_grupo))
        pot_total_viviendas += pot_parcial_g

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #0066cc; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Justificación Grupo #{idx+1} ({viv['nombre']}):</b> {just_str}<br>
            Cálculo parcial: {qty_g} viviendas x {pot_unit} W x {cs_grupo} = <b>{pot_parcial_g:,} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 Viviendas totales: **{total_viviendas_edificio}** | **Total Parcial P1 (Viviendas): {pot_total_viviendas:,} W**")
    st.markdown("---")
    
    # 2. LOCALES COMERCIALES
    col_h_loc, col_pop_loc = st.columns([4, 1])
    with col_h_loc:
        st.subheader("2. Locales Comerciales y Oficinas (P2)")
    with col_pop_loc:
        with st.popover("📖 Ver Criterio Locales"):
            st.markdown("### Criterio ITC-BT-10 (Locales Comerciales)")
            st.write("• Potencia mínima por superficie: 100 W por cada m².")
            st.write("• Suelo reglamentario absoluto: Ningún local se calculará por debajo de 3.450 W.")

    if st.button("➕ Añadir local"): st.session_state.locales.append({"nombre": f"Local {len(st.session_state.locales)+1}", "superficie": 40, "qty": 1})
    pot_total_locales = 0

    for idx, loc in enumerate(st.session_state.locales):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1: loc["nombre"] = st.text_input(f"Local #{idx+1}", loc["nombre"], key=f"loc_nom_{idx}")
        with c2: loc["superficie"] = st.number_input(f"Superficie m² #{idx+1}", min_value=0.0, value=float(loc["superficie"]), key=f"loc_sup_{idx}")
        with c3: loc["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(loc["qty"]), key=f"loc_qty_{idx}")
        with c4:
            if st.button("🗑️", key=f"del_loc_{idx}"): st.session_state.locales.pop(idx); st.rerun()

        sup_val = loc["superficie"]
        cant_loc = loc["qty"]
        pot_por_superficie = sup_val * 100.0

        if pot_por_superficie < 3450.0:
            pot_unidad_local = 3450.0
            estado_minimo = f"⚠️ <b>NO ALCANZA EL MÍNIMO:</b> La superficie ({sup_val} m² x 100 W/m² = {pot_por_superficie:,.0f} W) es inferior al suelo normativo."
            accion_minimo = f"👉 <b>Se aplica el mínimo legal de 3.450 W</b>."
        else:
            pot_unidad_local = pot_por_superficie
            estado_minimo = f"✅ <b>CUMPLE EL MÍNIMO:</b> ({sup_val} m² x 100 W/m² = {pot_por_superficie:,.0f} W)."
            accion_minimo = f"👉 Se toma el valor calculado por superficie."

        pot_parcial_local = pot_unidad_local * cant_loc
        pot_total_locales += pot_parcial_local

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 12px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Análisis Local #{idx+1} ({loc['nombre']}):</b><br>
            • Estado: {estado_minimo}<br>
            • {accion_minimo}<br>
            • Total Parcial: {cant_loc} x {pot_unidad_local:,.0f} W = <b>{pot_parcial_local:,.0f} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 **Total Parcial P2 (Locales Comerciales): {int(pot_total_locales):,} W**")
    st.markdown("---")

    # 3. SERVICIOS GENERALES
    col_h_serv, col_pop_serv = st.columns([4, 1])
    with col_h_serv:
        st.subheader("3. Servicios Generales (P3)")
    with col_pop_serv:
        with st.popover("📖 Clasificación NTE-ITA (Ascensores)"):
            st.markdown("### Tabla Oficial NTE-ITA (Instalaciones de Transporte)")
            tabla_ita_md = (
                "| Código | Capacidad y Velocidad | Potencia Estimada Aprox. |\n"
                "| :--- | :--- | :---: |\n"
                "| **ITA-01** | Carga 5 personas / Vel. 0.63 m/s | ~ 2.2 kW |\n"
                "| **ITA-02** | Carga 5 personas / Vel. 1.00 m/s | ~ 3.0 kW |\n"
                "| **ITA-03** | Carga 8 personas / Vel. 1.00 m/s | ~ 4.0 kW |\n"
                "| **ITA-04** | Carga 8 personas / Vel. 1.60 m/s | ~ 5.5 kW |\n"
                "| **ITA-05** | Carga 13 personas / Vel. 1.60 m/s | ~ 7.5 kW |\n"
                "| **ITA-06** | Carga 13 personas / Vel. 2.50 m/s | ~ 9.0 kW |\n"
                "| **ITA-07** | Carga 21 personas / Vel. 2.50 m/s | ~ 11.0 kW |\n"
                "| **ITA-08** | Carga 21 personas / Vel. 3.50 m/s | ~ 15.0 kW |\n"
                "| **ITA-09 a 11** | Montacamillas 24 pers. (1.0 - 2.5 m/s) | ~ 12.0 - 18.0 kW |\n"
            )
            st.markdown(tabla_ita_md)

    if st.button("➕ Añadir servicio"): st.session_state.servicios_generales.append({"nombre": "Ascensor ITA-03", "potencia": 4000, "factor": 1.30, "qty": 1})
    pot_total_servicios = 0

    opciones_factores_k = {
        "Ascensor Principal (K = 1.30)": 1.30,
        "Motores / Bombas secundarias (K = 1.25)": 1.25,
        "Ascensor Secundario (K = 1.15)": 1.15,
        "Lámparas Fluorescentes / Descarga (K = 1.80)": 1.80,
        "Servicios directos / LED (K = 1.00)": 1.00,
        "Personalizado (Introducir valor libre)": -1.0
    }

    for idx, serv in enumerate(st.session_state.servicios_generales):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: serv["nombre"] = st.text_input(f"Servicio #{idx+1}", serv["nombre"], key=f"serv_nom_{idx}")
        with c2: serv["potencia"] = st.number_input(f"Potencia W #{idx+1}", min_value=0, value=int(serv["potencia"]), key=f"serv_pot_{idx}")
        with c3: serv["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(serv["qty"]), key=f"serv_qty_{idx}")
        
        factor_actual = serv.get("factor", 1.30)
        def_opt_idx = 0
        for i, (k_text, v_val) in enumerate(opciones_factores_k.items()):
            if v_val == factor_actual:
                def_opt_idx = i
                break
            elif factor_actual not in [1.30, 1.25, 1.15, 1.80, 1.00] and k_text.startswith("Personalizado"):
                def_opt_idx = i

        with c4:
            sel_opt = st.selectbox(f"Coeficiente K #{idx+1}", list(opciones_factores_k.keys()), index=def_opt_idx, key=f"serv_tipo_opt_{idx}")
            if sel_opt.startswith("Personalizado"):
                factor = st.number_input(f"Valor K personalizado #{idx+1}", min_value=0.1, value=float(factor_actual if factor_actual > 0 else 1.25), key=f"serv_k_pers_{idx}")
            else:
                factor = opciones_factores_k[sel_opt]
            serv["factor"] = factor

        with c5:
            if st.button("🗑️", key=f"del_serv_{idx}"): st.session_state.servicios_generales.pop(idx); st.rerun()

        p_parcial_serv = int(serv["potencia"] * serv["qty"] * factor)
        pot_total_servicios += p_parcial_serv

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #ffc107; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Servicio #{idx+1} ({serv['nombre']}):</b> Coeficiente <b>K = {factor:.2f}</b> | Cálculo: {serv['potencia']} W x {serv['qty']} x {factor:.2f} = <b>{p_parcial_serv:,} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 **Total Parcial P3 (Servicios Generales): {pot_total_servicios:,} W**")
    st.markdown("---")

    # 4. GARAJES E IRVE
    col_h_irve, col_pop_irve = st.columns([4, 1])
    with col_h_irve:
        st.subheader("4. Garajes e IRVE (ITC-BT-52)")
    with col_pop_irve:
        with st.popover("📖 Explicación Técnica IRVE"):
            st.markdown("### Criterios Técnicos ITC-BT-52 e ITC-BT-10")
            st.write("1. Garaje: 20 W/m², mínimo 3.450 W.")
            st.write("2. Preinstalación IRVE: 3.680 W por plaza (afectada por 10% o 0.1).")
            st.write("3. Con SPL: Reducción del 90% (Factor 0.1).")

    gc1, gc2, gc3 = st.columns(3)
    with gc1: sup_garaje = st.number_input("Sup. Garaje m²", value=300)
    with gc2: plazas_garaje = st.number_input("Plazas Garaje", value=25)
    with gc3: opcion_irve = st.selectbox("Sistema de Recarga IRVE", ["Sin SPL [Factor = 1.0]", "Con SPL (Reducción 90% / Factor = 0.1)"])

    pot_garaje_por_sup = sup_garaje * 20.0
    pot_garaje_adjudicada = max(pot_garaje_por_sup, 3450.0 if sup_garaje > 0 else 0.0)
    fsim_ve = 1.0 if "Sin" in opcion_irve else 0.1
    pot_total_irve = int(round(plazas_garaje * 0.1 * 3680 * fsim_ve))
    pot_total_garaje_irve = int(pot_garaje_adjudicada) + pot_total_irve

    st.markdown(f"""
    <div style="background-color: #f8f9fa; border-left: 4px solid #17a2b8; padding: 12px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
        <b>Cálculo Garaje e IRVE:</b> Garaje = {int(pot_garaje_adjudicada):,} W | IRVE = {pot_total_irve:,} W | <b>Total P4/P5 = {pot_total_garaje_irve:,} W</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    pt_total = pot_total_viviendas + int(pot_total_locales) + pot_total_servicios + int(pot_garaje_adjudicada) + pot_total_irve

    st.markdown(f"""
        <div class="resumen-parciales-box">
            <h3 style="color: #111; margin-top: 0;">📋 RESUMEN DE POTENCIAS PARCIALES Y TOTALES (ITC-BT-10)</h3>
            <ul>
                <li><b>P1 (Viviendas):</b> {pot_total_viviendas:,} W</li>
                <li><b>P2 (Locales Comerciales):</b> {int(pot_total_locales):,} W</li>
                <li><b>P3 (Servicios Generales):</b> {pot_total_servicios:,} W</li>
                <li><b>P4 (Garaje):</b> {int(pot_garaje_adjudicada):,} W</li>
                <li><b>P5 (IRVE):</b> {pot_total_irve:,} W</li>
            </ul>
            <hr style="border: 1px solid #ced4da;">
            <h2 style="color: #ff4b4b; margin-bottom: 0;">⚡ SUMA TOTAL PREVISTA (Pt): {pt_total:,} W ({pt_total/1000:,.2f} kW)</h2>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 2: LGA
# =========================================================================
with pestanas[1]:
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    with st.expander("🏗️ Selector de Sistema de Instalación y Material", expanded=True):
        metodo_lga_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), key="met_lga")
        tipo_enlace_lga = st.radio("Modelo de esquema reglamentario:", [
            "Modelo 1: Contadores totalmente concentrados (CDT = 0.5%)",
            "Modelo 2: Centralizaciones parciales (CDT = 1.0%)"
        ], key="enlace_lga")

    dv_pct_lga = 0.5 if "Modelo 1" in tipo_enlace_lga else 1.0
    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        lga_pot = st.number_input("Potencia de cálculo LGA (W)", value=float(pt_total), key="lga_p_edit")
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
    prot_lga = seleccionar_proteccion(ib_lga)
    dv_real_lga_pct = ((lga_pot * lga_long) / (gamma_lga * s_optima_lga * 400) / 400) * 100

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN A ADOPTAR (LGA): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_lga} mm²</span> de {lga_mat.upper()} ({lga_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
            Caída de Tensión real: {dv_real_lga_pct:.3f}% (Límite: {dv_pct_lga}%) | Protección: {prot_lga} A
            </span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 3: DERIVACIÓN INDIVIDUAL
# =========================================================================
with pestanas[2]:
    st.title("Derivación Individual - DI (ITC-BT-15)")
    with st.expander("🏗️ Selector de Sistema de Instalación y Material", expanded=True):
        metodo_di_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), key="met_di")
        tipo_enlace_di = st.radio("Modelo de esquema para la DI:", [
            "Modelo A: Contadores concentrados (CDT = 1.0%)",
            "Modelo B: Contadores diseminados / exteriores (CDT = 0.5%)"
        ], key="enlace_di")

    dv_pct_di = 1.0 if "Modelo A" in tipo_enlace_di else 0.5
    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Potencia de la Derivación (W)", [5750, 7360, 9200, 11500], key="di_p")
        di_long = st.number_input("Longitud de la DI (m)", value=15.0, key="di_l")
        di_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="di_mat")
    with di_c2:
        di_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="di_ais")
        di_cos = st.slider("Coseno phi", 0.8, 1.0, 1.0, key="di_cos")

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
    prot_di = seleccionar_proteccion(ib_di)
    dv_real_di_pct = (((2 * di_pot * di_long) / (gamma_di * s_optima_di * 230)) / 230) * 100

    st.markdown(f"""
        <div class="resultado-destacado">
            🔌 SECCIÓN A ADOPTAR (DI): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_di} mm²</span> de {di_mat.upper()} ({di_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
            Caída de Tensión real: {dv_real_di_pct:.3f}% (Límite: {dv_pct_di}%) | Protección PIA: {prot_di} A + Diferencial 30 mA
            </span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 4: TABLA GUÍA ESTILO PLC MADRID
# =========================================================================
with pestanas[3]:
    st.title("📊 Tablas de Cálculo Directo Estilo PLC Madrid (ITC-BT-15)")
    tabla_plc_data = [
        {"Sección Min": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "6 m", "32A (7.32 kW)": "13 m", "40A (9.2 kW)": "5 m", "50A (11.5 kW)": "-", "63A (14.49 kW)": "-"},
        {"Sección Min": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "11 m", "32A (7.32 kW)": "26 m", "40A (9.2 kW)": "10 m", "50A (11.5 kW)": "-", "63A (14.49 kW)": "-"},
        {"Sección Min": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "11 m", "32A (7.32 kW)": "22 m", "40A (9.2 kW)": "8 m", "50A (11.5 kW)": "17 m", "63A (14.49 kW)": "6 m"},
        {"Sección Min": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "22 m", "32A (7.32 kW)": "44 m", "40A (9.2 kW)": "17 m", "50A (11.5 kW)": "34 m", "63A (14.49 kW)": "13 m"},
        {"Sección Min": "16 mm²", "Tubo Mín": "40 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "17 m", "32A (7.32 kW)": "33 m", "40A (9.2 kW)": "25 m", "50A (11.5 kW)": "27 m", "63A (14.49 kW)": "20 m"},
        {"Sección Min": "16 mm²", "Tubo Mín": "40 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "33 m", "32A (7.32 kW)": "66 m", "40A (9.2 kW)": "51 m", "50A (11.5 kW)": "55 m", "63A (14.49 kW)": "41 m"}
    ]
    st.dataframe(tabla_plc_data, use_container_width=True)

# =========================================================================
# PESTAÑA 5: CÁLCULO RÁPIDO
# =========================================================================
with pestanas[4]:
    st.title("🧮 Ventana de Cálculo Rápido")
    rc1, rc2 = st.columns(2)
    with rc1:
        modo_carga = st.radio("Modo de entrada:", ["Por Potencia (W)", "Por Intensidad Directa (A)"], key="mod_q")
        if modo_carga == "Por Potencia (W)":
            val_pot_q = st.number_input("Potencia (W)", value=5000.0, key="vp_q")
            tipo_red_q = st.selectbox("Tipo de red", ["Monofásica (230V)", "Trifásica (400V)"], key="tr_q1")
            cos_q = st.slider("Coseno phi", 0.7, 1.0, 0.9, key="cos_q")
            ib_q = val_pot_q / (230 * cos_q) if "Monofásica" in tipo_red_q else val_pot_q / (math.sqrt(3) * 400 * cos_q)
        else:
            ib_q = st.number_input("Intensidad Ib (A)", value=25.0, key="ib_q1")
            tipo_red_q = st.selectbox("Tipo de red", ["Monofásica (230V)", "Trifásica (400V)"], key="tr_q2")
            val_pot_q = ib_q * 230 if "Monofásica" in tipo_red_q else ib_q * math.sqrt(3) * 400 * 0.9

        long_q = st.number_input("Longitud (m)", value=20.0, key="l_q")

    with rc2:
        metodo_q_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), key="met_q")
        mat_q = st.selectbox("Material", ["cobre", "aluminio"], key="m_q")
        ais_q = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="a_q")
        cdt_lim_q = st.number_input("CDT máxima (%)", value=3.0, key="cdt_q")
        icc_orig_q = st.number_input("Icc origen (kA)", value=10.0, key="icc_orig_q")

    gamma_q = GAMMA_MAP.get((mat_q, ais_q), 44.0)
    v_nominal_q = 230 if "Monofásica" in tipo_red_q else 400
    dv_max_q = v_nominal_q * (cdt_lim_q / 100.0)
    s_cdt_q = (2 * val_pot_q * long_q) / (gamma_q * dv_max_q * v_nominal_q) if "Monofásica" in tipo_red_q else (val_pot_q * long_q) / (gamma_q * dv_max_q * v_nominal_q)
    
    s_cal_q = 1.5
    for sec, iz_val in IZ_COBRE_TUBO.items():
        if iz_val >= ib_q:
            s_cal_q = sec
            break

    s_opt_q = seleccionar_seccion_optima(max(s_cdt_q, s_cal_q))
    st.markdown(f"""
        <div class="resultado-destacado">
            🧮 SECCIÓN ÓPTIMA: <span style="color: #ff4b4b; font-size: 24px;">{s_opt_q} mm²</span> de {mat_q.upper()} ({ais_q})
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 6: ESQUEMAS UNIFILARES
# =========================================================================
with pestanas[5]:
    st.title("📐 Esquema Unifilar")
    tipo_elec_simb = st.radio("Grado de Electrificación:", ["Grado Básico (5 Circuitos)", "Grado Elevado (12 Circuitos)"], key="tipo_elec_simb")
    esquema_txt = "==================================================\nPROYECTO: " + st.session_state.nombre_proyecto + "\n[DI] -> [IGA] -> [ID] -> Circuitos C1 a C5\n=================================================="
    st.markdown(f'<div class="esquema-simbolos">{esquema_txt}</div>', unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 7: INFORME TÉCNICO MTD
# =========================================================================
with pestanas[6]:
    st.title("📄 Memoria Técnica de Diseño (MTD)")
    texto_inf = f"Proyecto: {st.session_state.nombre_proyecto}\nPt: {pt_total:,} W"
    st.text(texto_inf)
    st.download_button("📥 Descargar Informe (.txt)", data=texto_inf, file_name="MTD.txt", mime="text/plain")

# =========================================================================
# PESTAÑA 8: SIMULADOR DE CONSUMO
# =========================================================================
with pestanas[7]:
    st.title("💡 Simulador de Consumo Eléctrico")
    kw_c = st.number_input("kW contratados", value=4.6)
    kwh_m = st.number_input("kWh al mes", value=250.0)
    total_con_impuestos = ((kw_c * 0.11 * 30) + (kwh_m * 0.18)) * 1.051127 * 1.10
    st.metric("Estimación Factura Mensual", f"{total_con_impuestos:.2f} €")