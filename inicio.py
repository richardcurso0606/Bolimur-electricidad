import streamlit as st
import sqlite3

# =========================================================================
# CONFIGURACIÓN DE PÁGINA (TÍTULO Y ICONO NITIDO PARA MÓVIL)
# =========================================================================
st.set_page_config(
    page_title="ELECTRICIDAD BAJA TENSIÓN INSTALACIONES",
    page_icon="⚡",
    layout="wide"
)

# =========================================================================
# INICIALIZACIÓN GLOBAL OBLIGATORIA (¡Arriba del todo para evitar errores!)
# =========================================================================
if 'grupos_viviendas' not in st.session_state:
    st.session_state.grupos_viviendas = [{"nombre": "Plantas 1ª a 4ª (Básica)", "qty": 8, "pot": 5750, "nocturna": False}]
if 'locales' not in st.session_state:
    st.session_state.locales = [{"nombre": "Locales Comerciales", "qty": 2, "superficie": 100.0}]
if 'servicios_generales' not in st.session_state:
    st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 1, "potencia": 4000.0, "factor": 1.30, "cos_phi": 1.0}]
if 'garajes' not in st.session_state:
    st.session_state.garajes = {"sup": 240.0, "plazas_irve": 18, "tipo_irve": "10% (Sin sistema de gestión)"}

# =========================================================================
# IMPORTACIÓN SEGURA DE MÓDULOS
# =========================================================================
try:
    from modulos import calculo_rapido
except Exception as e:
    st.error(f"Error al cargar el módulo calculo_rapido: {e}")

try:
    from modulos import prevision_cargas
except Exception as e:
    st.error(f"Error al cargar el módulo prevision_cargas: {e}")

try:
    from modulos import lga
except Exception as e:
    st.error(f"Error al cargar el módulo lga: {e}")

try:
    from modulos import di
except Exception as e:
    st.error(f"Error al cargar el módulo di: {e}")

# =========================================================================
# ESTILOS CSS GLOBALES
# =========================================================================
st.markdown("""
    <style>
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            border: 2px solid #2563eb; border-radius: 6px; background-color: #f8fafc;
        }
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
        }
        [data-testid="stSidebar"] button:hover {
            border-color: #0284c7;
            background-color: #f0f9ff;
            color: #0284c7;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# MENÚ LATERAL (BOTONES EN FORMATO RECUADRO)
# =========================================================================
with st.sidebar:
    st.markdown("""
        <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 15px; text-align: center;">
            <h3 style="color: #38bdf8; margin: 0; font-size: 18px;">⚡ CÁLCULOS ELÉCTRICOS</h3>
            <p style="color: #94a3b8; font-size: 12px; margin: 5px 0 0 0;">Panel Técnico REBT</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h4 style='color: #475569; margin-bottom: 5px;'>📂 Navegación</h4>", unsafe_allow_html=True)

    if 'menu_activo' not in st.session_state:
        st.session_state.menu_activo = "🏠 Menú Principal"

    if st.button("🏠  Menú Principal", use_container_width=True):
        st.session_state.menu_activo = "🏠 Menú Principal"
        st.rerun()
        
    if st.button("🧮  Cálculo Rápido (CDT & Icc)", use_container_width=True):
        st.session_state.menu_activo = "🧮 Cálculo Rápido (CDT & Icc)"
        st.rerun()
        
    if st.button("🏢  Previsión de Cargas (Pt)", use_container_width=True):
        st.session_state.menu_activo = "🏢 Previsión de Cargas (Pt)"
        st.rerun()
        
    if st.button("⚡  Línea General (LGA)", use_container_width=True):
        st.session_state.menu_activo = "⚡ Línea General (LGA)"
        st.rerun()
        
    if st.button("🔌  Derivación Individual (DI)", use_container_width=True):
        st.session_state.menu_activo = "🔌 Derivación Individual (DI)"
        st.rerun()
        
    if st.button("📚  Tablas REBT", use_container_width=True):
        st.session_state.menu_activo = "📚 Tablas REBT"
        st.rerun()

    seleccion_modulo = st.session_state.menu_activo

# =========================================================================
# EL ENRUTADOR (CARGA DE VENTANAS)
# =========================================================================
if seleccion_modulo.startswith("🏠"):
    st.title("⚡ CÁLCULOS ELÉCTRICOS")
    st.write("Bienvenido al panel de cálculo eléctrico. Selecciona una opción en el menú lateral para empezar.")

elif seleccion_modulo.startswith("🧮"):
    try:
        calculo_rapido.renderizar()
    except Exception as e:
        st.error(f"Error al ejecutar Cálculo Rápido: {e}")

elif "Previsión" in seleccion_modulo or seleccion_modulo.startswith("🏢"):
    try:
        prevision_cargas.renderizar()
    except Exception as e:
        st.error(f"Error al ejecutar Previsión de Cargas: {e}")

elif seleccion_modulo.startswith("⚡"):
    try:
        lga.renderizar()
    except Exception as e:
        st.error(f"Error al ejecutar LGA: {e}")

elif seleccion_modulo.startswith("🔌"):
    try:
        di.renderizar()
    except Exception as e:
        st.error(f"Error al ejecutar DI: {e}")

elif seleccion_modulo.startswith("📚"):
    st.title("📚 Tablas REBT")
