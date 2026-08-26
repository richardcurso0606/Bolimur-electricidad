import streamlit as st
import sqlite3

# =========================================================================
# 1. IMPORTACIÓN DE LOS MÓDULOS AISLADOS
# =========================================================================
# Le decimos a Python que busque en la carpeta 'modulos' nuestro archivo
from modulos import calculo_rapido
from modulos import prevision_cargas
from modulos import lga
from modulos import di

# Cuando aísles los demás, quitarás el '#' para importarlos así:
# from modulos import prevision_cargas
# from modulos import lga
# from modulos import di

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
            border: 2.5px solid #2563eb !important; border-radius: 6px !important; background-color: #f8fafc !important;
        }
        div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
            border: 3px solid #1e40af !important; background-color: #ffffff !important; box-shadow: 0 0 8px rgba(37, 99, 235, 0.5) !important;
        }
        div[data-baseweb="popover"], ul[data-baseweb="menu"] {
            max-height: 250px !important; overflow-y: auto !important;
        }
        [data-testid="stSidebar"] {
            background-color: #f8fafc !important; border-right: 1px solid #e2e8f0;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
            background-color: transparent !important; padding: 10px 5px !important; margin-bottom: 5px !important; color: #334155 !important; font-size: 16px !important; border-radius: 8px;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
            background-color: #e0f2fe !important;
        }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-baseweb="radio"] input:checked + div {
            color: #0369a1 !important; font-weight: bold !important;
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
# 4. INICIALIZACIÓN DE VARIABLES GLOBALES (Evita que se borren datos al cambiar de ventana)
# =========================================================================
if 'grupos_viviendas' not in st.session_state: st.session_state.grupos_viviendas = [{"nombre": "Plantas 1ª a 4ª (Básica)", "qty": 8, "pot": 5750, "nocturna": False}]
if 'locales' not in st.session_state: st.session_state.locales = [{"nombre": "Locales Comerciales", "qty": 2, "superficie": 100.0}]
if 'servicios_generales' not in st.session_state: st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 1, "potencia": 4000.0, "factor": 1.30}]
if 'garajes' not in st.session_state: st.session_state.garajes = {"sup": 240.0, "plazas_irve": 18, "tipo_irve": "10% (Sin sistema de gestión)"}

# =========================================================================
# 5. MENÚ LATERAL
# =========================================================================
with st.sidebar:
    st.markdown("""
        <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 15px; text-align: center;">
            <h3 style="color: #38bdf8; margin: 0; font-size: 18px;">⚡ BOLIMUR</h3>
            <p style="color: #94a3b8; font-size: 12px; margin: 5px 0 0 0;">Instalaciones Integrales</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h4 style='color: #475569; margin-bottom: 5px;'>📂 Navegación</h4>", unsafe_allow_html=True)
    seleccion_modulo = st.radio("Selecciona:", [
        "🏠 Menú Principal", 
        "🧮 Cálculo Rápido (CDT & Icc)", 
        "🏢 Previsión de Cargas (Pt)", 
        "⚡ Línea General (LGA)", 
        "🔌 Derivación Individual (DI)", 
        "📚 Tablas REBT"
    ], label_visibility="collapsed")

# =========================================================================
# 6. EL ENRUTADOR (CARGA DE VENTANAS)
# =========================================================================
if seleccion_modulo.startswith("🏠"):
    st.title("⚡ BOLIMUR INSTALACIONES INTEGRALES")
    st.write("Bienvenido al panel de cálculo eléctrico. Selecciona un módulo en el menú lateral para empezar.")

elif seleccion_modulo.startswith("🧮"):
    # ¡AQUÍ ESTÁ LA MAGIA! Llamamos a la función que guardamos en cuarentena en el otro archivo.
    calculo_rapido.renderizar()

elif "Previsión" in seleccion_modulo or seleccion_modulo.startswith("🏢"):
    prevision_cargas.renderizar()
    

elif seleccion_modulo.startswith("⚡"):
    lga.renderizar(calcular_pt_global, METODOS_INSTALACION, IZ_COBRE_TUBO, IZ_COBRE_ENTERRADO, SECCIONES_COMERCIALES, seleccionar_seccion_optima, seleccionar_proteccion)

elif seleccion_modulo.startswith("🔌"):
    di.renderizar(METODOS_INSTALACION, GAMMA_MAP, IZ_COBRE_TUBO, IZ_COBRE_ENTERRADO, seleccionar_seccion_optima, seleccionar_proteccion)
    

elif seleccion_modulo.startswith("📚"):
    st.title("📚 Tablas REBT")
