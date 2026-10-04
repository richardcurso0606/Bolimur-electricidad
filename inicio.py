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

auth_manager = None
db_manager = None
perfil_instalador = None
gestion_clientes = None

try:
    from modulos import auth_manager
except Exception as e:
    auth_manager = None
    errores_import["auth_manager"] = traceback.format_exc()

try:
    from modulos import db_manager
except Exception as e:
    db_manager = None
    errores_import["db_manager"] = traceback.format_exc()

try:
    from modulos import perfil_instalador
except Exception as e:
    perfil_instalador = None
    errores_import["perfil_instalador"] = traceback.format_exc()

try:
    from modulos import gestion_clientes
except Exception as e:
    gestion_clientes = None
    errores_import["gestion_clientes"] = traceback.format_exc()

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

try:
    from modulos import memoria_tecnica_industria
except Exception as e:
    memoria_tecnica_industria = None
    errores_import["memoria_tecnica_industria"] = traceback.format_exc()

try:
    from modulos import tablas_normativas
except Exception as e:
    tablas_normativas = None
    errores_import["tablas_normativas"] = traceback.format_exc()

try:
    from modulos import asistente_ia_rebt
except Exception as e:
    asistente_ia_rebt = None
    errores_import["asistente_ia_rebt"] = traceback.format_exc()

try:
    from modulos import fotovoltaica
except Exception as e:
    fotovoltaica = None
    errores_import["fotovoltaica"] = traceback.format_exc()

try:
    from modulos import radar_normativo
except Exception as e:
    radar_normativo = None
    errores_import["radar_normativo"] = traceback.format_exc()



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

    user_email = usuario_actual.get("email", "")
    is_google = "gmail.com" in user_email.lower() or bool(usuario_actual.get("google_id")) or usuario_actual.get("auth_provider") == "Google"

    with st.container(border=True):
        if is_google:
            st.markdown(f"""
            <div style="background: #f0f9ff; border: 1.5px solid #0284c7; border-radius: 8px; padding: 10px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 18px;">🔴</span>
                    <div>
                        <div style="font-size: 11px; font-weight: bold; color: #0369a1; text-transform: uppercase;">Cuenta Google Activa</div>
                        <div style="font-size: 12px; color: #1e293b; font-weight: 600; word-break: break-all;">{user_email}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 10px; margin-bottom: 8px;">
                <div style="font-size: 11px; font-weight: bold; color: #475569; text-transform: uppercase;">👤 Sesión de Usuario</div>
                <div style="font-size: 12px; color: #1e293b; font-weight: 600; word-break: break-all;">{user_email or usuario_actual.get('username_windows', 'Local')}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"👤 **Instalador:** `{usuario_actual.get('nombre_instalador', 'Usuario')}`")
        st.markdown(f"📜 **Licencia:** `{usuario_actual.get('num_licencia_rebt', 'REBT-30/00000')}`")
        
        col_sbtn1, col_sbtn2 = st.columns(2)
        with col_sbtn1:
            if st.button("🔄 Cambiar", key="btn_switch_acc", use_container_width=True, help="Cambiar a otra cuenta de Google o usuario"):
                auth_manager.cerrar_sesion()
        with col_sbtn2:
            if st.button("🚪 Salir", key="btn_logout_side", use_container_width=True, help="Cerrar sesión actual"):
                auth_manager.cerrar_sesion()

    st.markdown("<h4 style='color: #475569; margin-bottom: 5px;'>📂 Navegación</h4>", unsafe_allow_html=True)

    if 'menu_activo' not in st.session_state:
        st.session_state.menu_activo = "🏠 Menú Principal"

    opciones = [
        ("🏠  Menú Principal", "🏠 Menú Principal"),
        ("🤖  Consultor IA REBT", "🤖 Consultor IA REBT"),
        ("☀️  Solar Fotovoltaica", "☀️ Solar Fotovoltaica"),
        ("🛰️  Radar Normativo BOE", "🛰️ Radar Normativo BOE"),
        ("🏛️  Memoria Técnica & Planos (MTD 30)", "🏛️ Memoria Técnica (MTD 30)"),
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
        es_activo = (st.session_state.menu_activo == target)
        btn_type = "primary" if es_activo else "secondary"
        btn_label = f"▶ {label}" if es_activo else label
        if st.button(btn_label, key=f"nav_btn_{target}", use_container_width=True, type=btn_type):
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
    
    st.write("Selecciona un módulo en el menú lateral o en los accesos rápidos inferiores para realizar cálculos técnicos, resolver dudas reglamentarias con la IA o tramitar memorias oficiales:")

    # BANNER DESTACADO 1: CONSULTOR IA EXPERTO REBT
    with st.container(border=True):
        col_ia_txt, col_ia_btn = st.columns([3, 1])
        with col_ia_txt:
            st.markdown("### 🤖 Consultor IA: Experto REBT & Ingeniero Eléctrico")
            st.write("Tu asesor técnico 24/7 con doble visión de **Ingeniero Eléctrico** y **Maestro Instalador de Campo**. Resuelve cualquier duda reglamentaria del REBT, cálculos de caídas de tensión, coordinación de protecciones, límites de MTD vs Proyecto de Ingeniero y requisitos de Industria en Murcia.")
        with col_ia_btn:
            st.write("")
            st.write("")
            if st.button("💬 Consultar a la IA", key="btn_home_ia_consultor", type="primary", use_container_width=True):
                st.session_state.menu_activo = "🤖 Consultor IA REBT"
                st.rerun()

    # BANNER DESTACADO 2: SOLAR FOTOVOLTAICA
    with st.container(border=True):
        col_pv_txt, col_pv_btn = st.columns([3, 1])
        with col_pv_txt:
            st.markdown("### ☀️ Energía Solar Fotovoltaica en Autoconsumo (ITC-BT-40 / RD 244/2019)")
            st.write("Dimensionamiento de ingeniería y campo: cálculo térmico de strings ($V_{oc,\\max}$ a -5ºC, $V_{mp,\\min}$ a 70ºC), verificación MPPT e inversor, cable solar H1Z2Z2-K, cuadro AC con diferencial 6mA DC, balance de producción anual (HSP Murcia), guía de obra de calle, resolución de averías y Memoria Técnica de Diseño Oficial (DGEAIM Murcia).")
        with col_pv_btn:
            st.write("")
            st.write("")
            if st.button("☀️ Abrir Fotovoltaica", key="btn_home_pv_featured", use_container_width=True):
                st.session_state.menu_activo = "☀️ Solar Fotovoltaica"
                st.rerun()

    # BANNER DESTACADO 3: MTD INDUSTRIA MURCIA & PLANOS
    with st.container(border=True):
        col_mtd_txt, col_mtd_btn = st.columns([3, 1])
        with col_mtd_txt:
            st.markdown("### 🏛️ Generador Oficial de Memoria Técnica de Diseño (MTD 30) & Planos Oficiales")
            st.write("Módulo oficial para tramitación ante Industria (DGEAIM Murcia). Incluye auto-rellenado desde cálculos, protocolo ITC-BT-05, **gestor gráfico de Planos de Situación, Emplazamiento Catastral y Esquema Unifilar oficial** (con auditoría IA REBT), y exportación en PDF de MTD, CIE y Manual.")
        with col_mtd_btn:
            st.write("")
            st.write("")
            if st.button("🚀 Tramitar MTD & Planos", key="btn_home_mtd_featured", use_container_width=True):
                st.session_state.menu_activo = "🏛️ Memoria Técnica (MTD 30)"
                st.rerun()

    # BANNER DESTACADO 4: RADAR NORMATIVO BOE & VIGILANCIA LEGISLATIVA
    with st.container(border=True):
        col_rad_txt, col_rad_btn = st.columns([3, 1])
        with col_rad_txt:
            st.markdown("### 🛰️ Radar Normativo BOE & Vigilancia Reglamentaria en Tiempo Real")
            st.write("Conexión en vivo con la **API de Datos Abiertos del Boletín Oficial del Estado (BOE)**. Monitorización continua de reformas en el REBT (RD 842/2002), Autoconsumo Solar (RD 244/2019), IRVE (ITC-BT-52) y CTE DB-HE. Incluye **análisis de impacto reglamentario con IA** para mantener Bolimur siempre 100% actualizado ante cambios normativos.")
        with col_rad_btn:
            st.write("")
            st.write("")
            if st.button("🛰️ Abrir Radar BOE", key="btn_home_radar_featured", use_container_width=True):
                st.session_state.menu_activo = "🛰️ Radar Normativo BOE"
                st.rerun()

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
            if st.button("Abrir Módulo IRVE", key="btn_home_irve", use_container_width=True):
                st.session_state.menu_activo = "🚗 Línea Recarga (IRVE)"
                st.rerun()

        with st.container(border=True):
            st.subheader("👤 Perfil del Instalador y Logotipo")
            st.write("Configura tus datos fiscales, número de carnet REBT, logotipo corporativo y copias de seguridad en la nube.")
            if st.button("Abrir Perfil del Instalador", key="btn_home_prof", use_container_width=True):
                st.session_state.menu_activo = "👤 Perfil del Instalador"
                st.rerun()

elif "Consultor IA" in seleccion_modulo or "🤖" in seleccion_modulo:
    if asistente_ia_rebt:
        asistente_ia_rebt.render_interfaz_asistente_rebt()
    else:
        st.error("Módulo Consultor IA REBT no disponible.")
        if "asistente_ia_rebt" in errores_import:
            st.code(errores_import["asistente_ia_rebt"])

elif "Solar" in seleccion_modulo or "☀️" in seleccion_modulo or "Fotovoltaica" in seleccion_modulo:
    if fotovoltaica:
        fotovoltaica.renderizar()
    else:
        st.error("Módulo de Solar Fotovoltaica no disponible.")
        if "fotovoltaica" in errores_import:
            st.code(errores_import["fotovoltaica"])

elif "Radar" in seleccion_modulo or "🛰️" in seleccion_modulo or "Normativo" in seleccion_modulo or "BOE" in seleccion_modulo:
    if radar_normativo:
        radar_normativo.renderizar()
    else:
        st.error("Módulo de Radar Normativo BOE no disponible.")
        if "radar_normativo" in errores_import:
            st.code(errores_import["radar_normativo"])

elif "Memoria" in seleccion_modulo or "MTD" in seleccion_modulo or "🏛️" in seleccion_modulo or "Industria" in seleccion_modulo:
    if memoria_tecnica_industria:
        memoria_tecnica_industria.renderizar()
    else:
        st.error("Módulo de Memoria Técnica Oficial (Industria DGEAIM) no disponible.")
        if "memoria_tecnica_industria" in errores_import:
            st.code(errores_import["memoria_tecnica_industria"])

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
    if tablas_normativas:
        tablas_normativas.renderizar()
    else:
        st.error("Módulo de Tablas Normativas no disponible.")
        if "tablas_normativas" in errores_import:
            st.code(errores_import["tablas_normativas"])

