import streamlit as st
import sqlite3

# =========================================================================
# CONFIGURACIÓN DE PÁGINA (ESTÁNDAR ORIGINAL)
# =========================================================================
st.set_page_config(
    page_title="ELECTRICIDAD BAJA TENSIÓN INSTALACIONES",
    page_icon="⚡",
    layout="wide"
)

# =========================================================================
# INICIALIZACIÓN GLOBAL OBLIGATORIA
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
# MENÚ LATERAL ESTÁNDAR
# =========================================================================
with st.sidebar:
    st.title("⚡ CÁLCULOS ELÉCTRICOS")
    st.markdown("Panel Técnico REBT")
    
    st.markdown("---")

    if 'menu_activo' not in st.session_state:
        st.session_state.menu_activo = "🏠 Menú Principal"

    # Usamos radio o botones estándar limpios de Streamlit
    seleccion_modulo = st.radio(
        "📂 Navegación",
        [
            "🏠 Menú Principal",
            "🧮 Cálculo Rápido (CDT & Icc)",
            "🏢 Previsión de Cargas (Pt)",
            "⚡ Línea General (LGA)",
            "🔌 Derivación Individual (DI)",
            "📚 Tablas REBT"
        ]
    )

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
