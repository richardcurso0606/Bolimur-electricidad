# -*- coding: utf-8 -*-
import streamlit as st
import traceback
import pandas as pd
import base64
import os

st.set_page_config(page_title="Bolimur - Cálculos Eléctricos REBT", page_icon="⚡", layout="wide")

# =========================================================================
# IMPORTACIÓN SEGURA DE MÓDULOS
# =========================================================================
errores_import = {}

try:
    from modulos import auth_manager
    from modulos import db_manager
    from modulos import perfil_instalador
    from modulos import gestion_clientes
except Exception as e:
    auth_manager = None
    errores_import["auth_manager"] = traceback.format_exc()

try:
    from modulos import calculo_rapido
except Exception as e:
    calculo_rapido = None
    errores_import["calculo_rapido"] = traceback.format_exc()

try:
    from modulos import prevision_cargas
except Exception as e:
    prevision_cargas = None
    errores_import["prevision_cargas"] = traceback.format_exc()

try:
    from modulos import lga
except Exception as e:
    lga = None
    errores_import["lga"] = traceback.format_exc()

try:
    from modulos import di
except Exception as e:
    di = None
    errores_import["di"] = traceback.format_exc()

try:
    from modulos import irve
except Exception as e:
    irve = None
    errores_import["irve"] = traceback.format_exc()

try:
    from modulos import presupuesto_vivienda
except Exception as e:
    presupuesto_vivienda = None
    errores_import["presupuesto_vivienda"] = traceback.format_exc()

try:
    from modulos import rebt_tablas as rebt
except Exception as e:
    rebt = None
    errores_import["rebt_tablas"] = traceback.format_exc()

# =========================================================================
# ESTILOS CSS GLOBALES
# =========================================================================
st.markdown("""
    <style>
        /* Inputs y Selectores */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            border: 2px solid #0284c7; border-radius: 8px; background-color: #f8fafc;
        }
        
        /* Barra Lateral */
        [data-testid="stSidebar"] {
            background-color: #f8fafc; border-right: 1px solid #e2e8f0;
        }
        [data-testid="stSidebar"] button {
            width: 100%;
            text-align: left;
            background-color: #ffffff;
            border: 2px solid #cbd5e1;
            border-radius: 8px;
            color: #334155;
            font-weight: 500;
            margin-bottom: 6px;
            transition: all 0.2s ease-in-out;
        }
        [data-testid="stSidebar"] button:hover {
            border-color: #0284c7;
            background-color: #f0f9ff;
            color: #0284c7;
            box-shadow: 0 2px 6px rgba(2, 132, 199, 0.15);
            transform: translateX(2px);
        }

        /* Contenedores con Borde y Sombra */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            border: 1.5px solid #e2e8f0 !important;
            background-color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05), 0 1px 3px rgba(15, 23, 42, 0.08) !important;
            margin-bottom: 16px !important;
            transition: all 0.2s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #cbd5e1 !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08), 0 2px 4px rgba(15, 23, 42, 0.06) !important;
        }

        /* Expanders con Sombra */
        div[data-testid="stExpander"] {
            border-radius: 10px !important;
            border: 1.5px solid #e2e8f0 !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
            background: white !important;
            margin-bottom: 12px !important;
        }

        /* Cabeceras de Secciones con Insignia */
        .section-header-blue {
            background: linear-gradient(90deg, #f0f9ff 0%, #ffffff 100%);
            border-left: 5px solid #0284c7;
            padding: 10px 16px;
            border-radius: 6px;
            margin: 18px 0 12px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        .section-header-green {
            background: linear-gradient(90deg, #f0fdf4 0%, #ffffff 100%);
            border-left: 5px solid #16a34a;
            padding: 10px 16px;
            border-radius: 6px;
            margin: 18px 0 12px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        .section-header-amber {
            background: linear-gradient(90deg, #fffbeb 0%, #ffffff 100%);
            border-left: 5px solid #d97706;
            padding: 10px 16px;
            border-radius: 6px;
            margin: 18px 0 12px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        .section-header-slate {
            background: linear-gradient(90deg, #f8fafc 0%, #ffffff 100%);
            border-left: 5px solid #475569;
            padding: 10px 16px;
            border-radius: 6px;
            margin: 18px 0 12px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }

        /* Tarjeta Genérica Bolimur */
        .bolimur-card {
            background: #ffffff;
            border: 1.5px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# CONTROL DE ACCESO Y AUTENTICACIÓN
# =========================================================================
if auth_manager:
    auth_manager.inicializar_sesion_auth()
    usuario_actual = st.session_state.get("usuario_autenticado") or {}
    if not usuario_actual:
        auth_manager.renderizar_pantalla_login()
        st.stop()
else:
    usuario_actual = {
        "id": 1,
        "nombre_instalador": "Richard Orlando Choque Tejerina",
        "nombre_empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
        "num_licencia_rebt": "REBT-30/15892",
        "localidad": "Murcia, España",
        "telefono": "+34 600 000 000"
    }

# =========================================================================
# MENÚ LATERAL
# =========================================================================
with st.sidebar:
    st.markdown(f"""
        <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 12px; text-align: center;">
            <h3 style="color: #38bdf8; margin: 0; font-size: 17px;">⚡ BOLIMUR REBT</h3>
            <p style="color: #94a3b8; font-size: 11px; margin: 4px 0 0 0;">{usuario_actual.get('nombre_empresa', 'Bolimur')}</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"👤 **Instalador:**  \n<small>{usuario_actual.get('nombre_instalador', 'Usuario')}</small>", unsafe_allow_html=True)
        st.markdown(f"📜 **Licencia:**  \n<small>`{usuario_actual.get('num_licencia_rebt', 'REBT')}`</small>", unsafe_allow_html=True)
        if st.button("🚪 Cerrar Sesión", key="btn_logout_side", use_container_width=True):
            auth_manager.cerrar_sesion()

    st.markdown("<h4 style='color: #475569; margin-bottom: 5px;'>📂 Navegación</h4>", unsafe_allow_html=True)

    if 'menu_activo' not in st.session_state:
        st.session_state.menu_activo = "🏠 Menú Principal"

    opciones = [
        ("🏠  Menú Principal", "🏠 Menú Principal"),
        ("👥  Gestión de Clientes (CRM)", "👥 Gestión de Clientes (CRM)"),
        ("🏡  Presupuesto Vivienda", "🏡 Presupuesto Vivienda"),
        ("🧮  Cálculo Rápido (CDT & Icc)", "🧮 Cálculo Rápido (CDT & Icc)"),
        ("🏢  Previsión de Cargas (Pt)", "🏢 Previsión de Cargas (Pt)"),
        ("⚡  Línea General (LGA)", "⚡ Línea General (LGA)"),
        ("🔌  Derivación Individual (DI)", "🔌 Derivación Individual (DI)"),
        ("🚗  Línea Recarga (IRVE)", "🚗 Línea Recarga (IRVE)"),
        ("👤  Perfil del Instalador", "👤 Perfil del Instalador"),
        ("📚  Tablas REBT", "📚 Tablas REBT")
    ]

    for label, target in opciones:
        if st.button(label, use_container_width=True):
            st.session_state.menu_activo = target
            st.rerun()

    seleccion_modulo = st.session_state.menu_activo

# =========================================================================
# =========================================================================
# EL ENRUTADOR PRINCIPAL
# =========================================================================
if seleccion_modulo == "🏠 Menú Principal" or seleccion_modulo.startswith("🏠"):
    st.title("⚡ BOLIMUR - INGENIERÍA Y CÁLCULOS ELÉCTRICOS")
    st.markdown(f"**Bienvenido, {usuario_actual.get('nombre_instalador', 'Instalador')}** | {usuario_actual.get('nombre_empresa', '')}")
    
    st.write("Selecciona un módulo en el menú lateral o en los accesos rápidos inferiores para realizar cálculos técnicos, gestionar clientes o elaborar presupuestos:")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader("👥 Gestión de Clientes (CRM) y Proyectos")
            st.write("Administra las fichas de tus clientes, datos del suministro, CUPS y asocia proyectos para recuperarlos en 1 clic.")
            if st.button("Abrir Gestión de Clientes", key="btn_home_crm", use_container_width=True):
                st.session_state.menu_activo = "👥 Gestión de Clientes (CRM)"
                st.rerun()

        with st.container(border=True):
            st.subheader("🏡 Presupuesto de Vivienda y Materiales")
            st.write("Inspector REBT ITC-BT-25, metraje de rozas, canalizaciones, cableado y mecanismos. Exportación de presupuestos y acopio.")
            if st.button("Abrir Presupuestos", key="btn_home_pres", use_container_width=True):
                st.session_state.menu_activo = "🏡 Presupuesto Vivienda"
                st.rerun()

        with st.container(border=True):
            st.subheader("🧮 Cálculo Rápido (CDT & Icc)")
            st.write("Dimensionamiento de circuitos por caída de tensión y comprobación térmica ($I_z$). Comprobación de cortocircuito y disparo magnético.")
            if st.button("Abrir Cálculo Rápido", key="btn_home_cr", use_container_width=True):
                st.session_state.menu_activo = "🧮 Cálculo Rápido (CDT & Icc)"
                st.rerun()

        with st.container(border=True):
            st.subheader("🏢 Previsión de Cargas (Pt)")
            st.write("Cálculo analítico de la potencia total del edificio conforme a ITC-BT-10. Viviendas, locales, servicios generales y garajes.")
            if st.button("Abrir Previsión de Cargas", key="btn_home_pc", use_container_width=True):
                st.session_state.menu_activo = "🏢 Previsión de Cargas (Pt)"
                st.rerun()

    with c2:
        with st.container(border=True):
            st.subheader("⚡ Línea General de Alimentación (LGA)")
            st.write("Cálculo reglamentario de la LGA según ITC-BT-14. Soporta Cobre y Aluminio, contadores concentrados o parciales y tubos normalizados.")
            if st.button("Abrir LGA", key="btn_home_lga", use_container_width=True):
                st.session_state.menu_activo = "⚡ Línea General (LGA)"
                st.rerun()

        with st.container(border=True):
            st.subheader("🔌 Derivación Individual (DI)")
            st.write("Dimensionamiento según ITC-BT-15 para enlaces a vivienda. Verificación de IGA Curva C y tubos normalizados (mínimo Ø 32 mm).")
            if st.button("Abrir Derivación Individual", key="btn_home_di", use_container_width=True):
                st.session_state.menu_activo = "🔌 Derivación Individual (DI)"
                st.rerun()

        with st.container(border=True):
            st.subheader("🚗 Línea Recarga Vehículo Eléctrico (IRVE)")
            st.write("Circuitos terminales según ITC-BT-52. Esquemas 1, 2, 3a, 3b y 4, cálculo al 1% de caída de tensión y protecciones diferenciales Tipo A/B.")
            if st.button("Abrir Módulo IRVE", key="btn_home_irve", type="primary", use_container_width=True):
                st.session_state.menu_activo = "🚗 Línea Recarga (IRVE)"
                st.rerun()

        with st.container(border=True):
            st.subheader("👤 Perfil del Instalador y Logotipo")
            st.write("Configura tus datos fiscales, número de carnet REBT, logotipo corporativo y copias de seguridad en la nube.")
            if st.button("Abrir Perfil del Instalador", key="btn_home_prof", use_container_width=True):
                st.session_state.menu_activo = "👤 Perfil del Instalador"
                st.rerun()

elif "IRVE" in seleccion_modulo or "Recarga" in seleccion_modulo or "🚗" in seleccion_modulo:
    if irve:
        irve.renderizar()
    else:
        st.error("Módulo IRVE no disponible.")
        if "irve" in errores_import:
            st.code(errores_import["irve"])

elif "Clientes" in seleccion_modulo or "CRM" in seleccion_modulo or "👥" in seleccion_modulo:
    if gestion_clientes:
        gestion_clientes.renderizar()
    else:
        st.error("Módulo de Gestión de Clientes no disponible.")

elif "Perfil" in seleccion_modulo or "👤" in seleccion_modulo:
    if perfil_instalador:
        perfil_instalador.renderizar()
    else:
        st.error("Módulo de Perfil del Instalador no disponible.")

elif "Cálculo Rápido" in seleccion_modulo or "🧮" in seleccion_modulo or "CDT" in seleccion_modulo:
    if calculo_rapido:
        calculo_rapido.renderizar()
    else:
        st.error("Módulo Cálculo Rápido no disponible.")
        if "calculo_rapido" in errores_import:
            st.code(errores_import["calculo_rapido"])

elif "Previsión" in seleccion_modulo or "🏢" in seleccion_modulo or "(Pt)" in seleccion_modulo:
    if prevision_cargas:
        prevision_cargas.renderizar()
    else:
        st.error("Módulo Previsión de Cargas no disponible.")
        if "prevision_cargas" in errores_import:
            st.code(errores_import["prevision_cargas"])

elif "LGA" in seleccion_modulo or "Línea General" in seleccion_modulo or "⚡" in seleccion_modulo:
    if lga:
        lga.renderizar()
    else:
        st.error("Módulo LGA no disponible.")
        if "lga" in errores_import:
            st.code(errores_import["lga"])

elif "DI" in seleccion_modulo or "Derivación" in seleccion_modulo or "🔌" in seleccion_modulo:
    if di:
        di.renderizar()
    else:
        st.error("Módulo DI no disponible.")
        if "di" in errores_import:
            st.code(errores_import["di"])

elif "Presupuesto" in seleccion_modulo or "🏡" in seleccion_modulo or "Vivienda" in seleccion_modulo:
    if presupuesto_vivienda:
        presupuesto_vivienda.renderizar()
    else:
        st.error("Error: El módulo presupuesto_vivienda no se pudo importar correctamente.")
        if "presupuesto_vivienda" in errores_import:
            st.code(errores_import["presupuesto_vivienda"])

elif "Tablas" in seleccion_modulo or "📚" in seleccion_modulo:
    st.title("📚 Tablas y Fórmulas Oficiales del REBT")
    st.markdown("Consulta rápida de parámetros normalizados según el Real Decreto 842/2002 y normas UNE asociadas.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🌡️ Conductividades y Resistividades",
        "⚡ Intensidades Admisibles (Iz)",
        "🛠️ Tubos Reglamentarios",
        "📐 Fórmulas Oficiales"
    ])

    with tab1:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🌡️ Conductividad (γ) y Resistividad (ρ) a Temperatura de Servicio</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("""
            Según la norma **UNE-HD 60364-5-52**, la conductividad del conductor disminuye con la temperatura. Para cálculos en régimen permanente se adoptan los valores a máxima temperatura admisible:
            """)
            df_cond = pd.DataFrame([
                {"Material": "Cobre", "Aislamiento": "XLPE / EPR", "Temp. Máx Servicio": "90 ºC", "Conductividad γ [m/(Ω·mm²)]": 44.0, "Resistividad ρ [Ω·mm²/m]": 0.0227},
                {"Material": "Cobre", "Aislamiento": "PVC", "Temp. Máx Servicio": "70 ºC", "Conductividad γ [m/(Ω·mm²)]": 48.5, "Resistividad ρ [Ω·mm²/m]": 0.0206},
                {"Material": "Aluminio", "Aislamiento": "XLPE / EPR", "Temp. Máx Servicio": "90 ºC", "Conductividad γ [m/(Ω·mm²)]": 28.0, "Resistividad ρ [Ω·mm²/m]": 0.0357},
                {"Material": "Aluminio", "Aislamiento": "PVC", "Temp. Máx Servicio": "70 ºC", "Conductividad γ [m/(Ω·mm²)]": 31.0, "Resistividad ρ [Ω·mm²/m]": 0.0323},
            ])
            st.dataframe(df_cond, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">⚡ Intensidades Admisibles en Conductores (Iz) - UNE-HD 60364-5-52 / ITC-BT-19</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            c_mat, c_ais, c_met = st.columns(3)
            with c_mat:
                sel_m = st.selectbox("Material:", ["Cobre", "Aluminio"], key="tab_m")
            with c_ais:
                sel_a = st.selectbox("Aislamiento:", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="tab_a")
            with c_met:
                sel_met = st.selectbox("Método de Instalación:", ["Bajo tubo (B1 / B2)", "Enterrado bajo tubo (D)"], key="tab_met")

            if rebt:
                tabla = rebt.obtener_tabla_iz(sel_m, sel_a, sel_met)
                df_iz = pd.DataFrame([
                    {"Sección (mm²)": s, "Intensidad Admisible Iz (A)": iz} for s, iz in sorted(tabla.items())
                ])
                st.dataframe(df_iz, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🛠️ Diámetros Exteriores Mínimos de Tubos Protectores</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("#### Derivaciones Individuales (ITC-BT-15 apdo. 3)")
                st.info("⚠️ **El diámetro mínimo reglamentario para cualquier Derivación Individual es Ø 32 mm** con previsión para ampliación del 100%.")
                df_tubo_di = pd.DataFrame([
                    {"Sección Conductor": "Hasta 6 mm²", "Diámetro Tubo": "Ø 32 mm", "Norma": "ITC-BT-15 (Mínimo absoluto)"},
                    {"Sección Conductor": "10 a 16 mm²", "Diámetro Tubo": "Ø 40 mm", "Norma": "ITC-BT-15"},
                    {"Sección Conductor": "25 a 35 mm²", "Diámetro Tubo": "Ø 50 mm", "Norma": "ITC-BT-15"},
                    {"Sección Conductor": "≥ 50 mm²", "Diámetro Tubo": "Ø 63 mm o Bandeja", "Norma": "ITC-BT-15"}
                ])
                st.dataframe(df_tubo_di, use_container_width=True, hide_index=True)

            with col_t2:
                st.markdown("#### Línea General de Alimentación - LGA (ITC-BT-14 Tabla 1)")
                st.info("⚠️ **El diámetro mínimo reglamentario para LGA trifásica (3F+N+PE) parte de Ø 110 mm**.")
                df_tubo_lga = pd.DataFrame([
                    {"Sección Conductor": "Hasta 25 mm²", "Diámetro Mínimo Tubo": "Ø 110 mm", "Norma": "ITC-BT-14 Tabla 1"},
                    {"Sección Conductor": "35 mm²", "Diámetro Mínimo Tubo": "Ø 125 mm", "Norma": "ITC-BT-14 Tabla 1"},
                    {"Sección Conductor": "50 a 70 mm²", "Diámetro Mínimo Tubo": "Ø 140 mm", "Norma": "ITC-BT-14 Tabla 1"},
                    {"Sección Conductor": "95 a 120 mm²", "Diámetro Mínimo Tubo": "Ø 160 mm", "Norma": "ITC-BT-14 Tabla 1"},
                    {"Sección Conductor": "150 mm²", "Diámetro Mínimo Tubo": "Ø 180 mm", "Norma": "ITC-BT-14 Tabla 1"},
                    {"Sección Conductor": "≥ 185 mm²", "Diámetro Mínimo Tubo": "Ø 200 a 225 mm", "Norma": "ITC-BT-14 Tabla 1"}
                ])
                st.dataframe(df_tubo_lga, use_container_width=True, hide_index=True)

    with tab4:
        st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">📐 Formulario Reglamentario REBT</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(r"""
            * **Intensidad de Diseño Monofásica:**
              $$I_b = \frac{P}{V \cdot \cos\varphi}$$
            * **Intensidad de Diseño Trifásica:**
              $$I_b = \frac{P}{\sqrt{3} \cdot V \cdot \cos\varphi}$$
            * **Caída de Tensión Monofásica ($230\text{ V}$):**
              $$\Delta V = \frac{2 \cdot P \cdot L}{\gamma \cdot S \cdot V} \quad \implies \quad \Delta V\% = \frac{\Delta V}{V} \cdot 100$$
            * **Caída de Tensión Trifásica ($400\text{ V}$):**
              $$\Delta V = \frac{P \cdot L}{\gamma \cdot S \cdot V} \quad \implies \quad \Delta V\% = \frac{\Delta V}{V} \cdot 100$$
            * **Previsión de Cargas en Edificios Residenciales (ITC-BT-10):**
              $$P_t = P_1 (\text{Viviendas}) + P_2 (\text{Locales}) + P_3 (\text{Servicios}) + P_4 (\text{Garajes e IRVE})$$
              Para $n > 20$ viviendas: $K = 15,4 + (n - 20) \cdot 0,5$.
            """)
