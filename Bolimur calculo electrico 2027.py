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
     /* Estilo para convertir los botones de la barra lateral en tarjetas/recuadros */
        [data-testid="stSidebar"] button {
            width: 100% !important;
            text-align: left !important;
            background-color: #ffffff !important;
            border: 2px solid #cbd5e1 !important;
            border-radius: 8px !important;
            color: #334155 !important;
            font-weight: 500 !important;
            margin-bottom: 6px !important;
            transition: all 0.2s ease-in-out !important;
        }
        [data-testid="stSidebar"] button:hover {
            border-color: #0284c7 !important;
            background-color: #f0f9ff !important;
            color: #0284c7 !important;
        }
        
        /* =========================================================
           ESTILO DE TARJETAS / RECUADROS PARA EL MENÚ LATERAL
           ========================================================= */
        [data-testid="stSidebar"] div.row-widget.stRadio div[role="radiogroup"] label {
            background-color: #ffffff !important;
            border: 2px solid #cbd5e1 !important;
            border-radius: 10px !important;
            padding: 12px 14px !important;
            margin-bottom: 10px !important;
            width: 100% !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
            transition: all 0.2s ease-in-out !important;
            cursor: pointer !important;
        }
        
        /* Efecto al pasar el ratón por encima del recuadro */
        [data-testid="stSidebar"] div.row-widget.stRadio div[role="radiogroup"] label:hover {
            border-color: #38bdf8 !important;
            background-color: #f0f9ff !important;
            transform: translateY(-1px);
        }
        
        /* Estilo para la tarjeta seleccionada (recuadro azul destacado) */
        [data-testid="stSidebar"] div.row-widget.stRadio div[role="radiogroup"] label[data-checked="true"],
        [data-testid="stSidebar"] div.row-widget.stRadio div[role="radiogroup"] label:has(input:checked) {
            border: 2.5px solid #0284c7 !important;
            background-color: #e0f2fe !important;
            box-shadow: 0 4px 6px rgba(2, 132, 199, 0.15) !important;
        }

        /* Tipografía del texto dentro de las tarjetas del menú */
        [data-testid="stSidebar"] div.row-widget.stRadio div[role="radiogroup"] label p {
            color: #334155 !important;
            font-size: 15px !important;
            font-weight: 500 !important;
        }
        
        [data-testid="stSidebar"] div.row-widget.stRadio div[role="radiogroup"] label input:checked ~ div p {
            color: #0369a1 !important;
            font-weight: bold !important;
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

/* Estilo para convertir los botones de la barra lateral en tarjetas/recuadros */
        [data-testid="stSidebar"] button {
            width: 100% !important;
            text-align: left !important;
            background-color: #ffffff !important;
            border: 2px solid #cbd5e1 !important;
            border-radius: 8px !important;
            color: #334155 !important;
            font-weight: 500 !important;
            margin-bottom: 6px !important;
            transition: all 0.2s ease-in-out !important;
        }
        [data-testid="stSidebar"] button:hover {
            border-color: #0284c7 !important;
            background-color: #f0f9ff !important;
            color: #0284c7 !important;
        }
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
    lga.renderizar()


elif seleccion_modulo.startswith("🔌"):
    di.renderizar()

elif seleccion_modulo.startswith("📚"):
    st.title("📚 Tablas REBT")
