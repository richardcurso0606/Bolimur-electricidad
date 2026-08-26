import streamlit as st
import sqlite3

# =========================================================================
# 1. IMPORTACIÓN DE LOS MÓDULOS AISLADOS
# =========================================================================
from modulos import calculo_rapido
from modulos import prevision_cargas
from modulos import lga
from modulos import di

# =========================================================================
# 2. CONFIGURACIÓN GENERAL (SIEMPRE LA PRIMERA LÍNEA)
# =========================================================================
st.set_page_config(page_title="BOLIMUR INSTALACIONES INTEGRALES", page_icon="⚡", layout="wide")

# =========================================================================
# 3. ESTILOS CSS GLOBALES (Para que toda la app se vea perfecta)
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

# --- BASE DE DATOS LOCAL ---
DB_NAME = "bolimur_database.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(instalador)")
    if not [col[1] for col in cursor.fetchall()]:
        cursor.execute('''CREATE TABLE instalador (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, nif TEXT, empresa TEXT, carnet TEXT, 
            telefono TEXT, email TEXT, categoria TEXT, tipo_inst TEXT, num_inscripcion TEXT, comunidad TEXT)''')
    conn.commit()
    conn.close()
init_db()

# =========================================================================
# 4. INICIALIZACIÓN DE VARIABLES GLOBALES
# =========================================================================
if 'grupos_viviendas' not in st.session_state: st.session_state.grupos_viviendas = [{"nombre": "Plantas 1ª a 4ª (Básica)", "qty": 8, "pot": 5750, "nocturna": False}]
if 'locales' not in st.session_state: st.session_state.locales = [{"nombre": "Locales Comerciales", "qty": 2, "superficie": 100.0}]
if 'servicios_generales' not in st.session_state: st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 1, "potencia": 4000.0, "factor": 1.30}]
if 'garajes' not in st.session_state: st.session_state.garajes = {"sup": 240.0, "plazas_irve": 18, "tipo_irve": "10% (Sin sistema de gestión)"}

# =========================================================================
# 5. MENÚ LATERAL (BOTONES EN FORMATO RECUADRO)
# =========================================================================
with st.sidebar:
    st.markdown("""
        <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 15px; text-align: center;">
            <h3 style="color: #38bdf8; margin: 0; font-size: 18px;">⚡ BOLIMUR</h3>
            <p style="color: #94a3b8; font-size: 12px; margin: 5px 0 0 0;">Instalaciones Integrales</p>
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
# 6. EL ENRUTADOR (CARGA DE VENTANAS)
# =========================================================================
if seleccion_modulo.startswith("🏠"):
    st.title("⚡ BOLIMUR INSTALACIONES INTEGRALES")
    st.write("Bienvenido al panel de cálculo eléctrico. Selecciona una opción en el menú lateral para empezar.")

elif seleccion_modulo.startswith("🧮"):
    calculo_rapido.renderizar()

elif "Previsión" in seleccion_modulo or seleccion_modulo.startswith("🏢"):
    prevision_cargas.renderizar()

elif seleccion_modulo.startswith("⚡"):
    lga.renderizar()

elif seleccion_modulo.startswith("🔌"):
    di.renderizar()

elif seleccion_modulo.startswith("📚"):
    st.title("📚 Tablas REBT")
