import streamlit as st
import math
import json
import os
import sqlite3

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BOLIMUR INSTALACIONES INTEGRALES - Calculadora REBT", page_icon="⚡", layout="wide")

# --- GESTIÓN DE BASE DE DATOS LOCAL (PERFIL Y CONFIGURACIÓN) ---
DB_NAME = "bolimur_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(instalador)")
    cols_inst = [col[1] for col in cursor.fetchall()]
    if not cols_inst:
        cursor.execute('''
            CREATE TABLE instalador (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT, nif TEXT, empresa TEXT, carnet TEXT, 
                telefono TEXT, email TEXT, categoria TEXT, 
                tipo_inst TEXT, num_inscripcion TEXT, comunidad TEXT
            )
        ''')

    cursor.execute("PRAGMA table_info(configuracion)")
    cols_conf = [col[1] for col in cursor.fetchall()]
    if not cols_conf:
        cursor.execute('''
            CREATE TABLE configuracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ultimo_archivo TEXT,
                carpeta_trabajo TEXT
            )
        ''')
        cursor.execute("INSERT INTO configuracion (ultimo_archivo, carpeta_trabajo) VALUES (?, ?)", 
                       ("proyecto_bolimur_default.json", "proyectos_bolimur"))

    conn.commit()
    conn.close()

init_db()

def guardar_datos_instalador(nombre, nif, empresa, carnet, telefono, email, categoria, tipo_inst, num_inscripcion, comunidad):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM instalador")
    cursor.execute("INSERT INTO instalador (nombre, nif, empresa, carnet, telefono, email, categoria, tipo_inst, num_inscripcion, comunidad) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (nombre, nif, empresa, carnet, telefono, email, categoria, tipo_inst, num_inscripcion, comunidad))
    conn.commit()
    conn.close()

def cargar_datos_instalador():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nombre, nif, empresa, carnet, telefono, email, categoria, tipo_inst, num_inscripcion, comunidad FROM instalador LIMIT 1")
        row = cursor.fetchone()
    except sqlite3.OperationalError:
        row = None
    conn.close()
    
    if row:
        return {
            "nombre": row[0] or "", "nif": row[1] or "", "empresa": row[2] or "", 
            "carnet": row[3] or "", "telefono": row[4] or "", "email": row[5] or "", 
            "categoria": row[6] or "", "tipo_inst": row[7] or "", 
            "num_inscripcion": row[8] or "", "comunidad": row[9] or ""
        }
    return {
        "nombre": "Richard Orlando Choque Tejerina", "nif": "34331426Q", 
        "empresa": "BOLIMUR INSTALACIONES INTEGRALES", "carnet": "INS-2026-MUR", 
        "telefono": "682 195 295", "email": "richard@bolimur.com",
        "categoria": "Especialista", "tipo_inst": "Baja Tensión",
        "num_inscripcion": "30/XXXXX", "comunidad": "Región de Murcia"
    }

def guardar_config_proyecto(archivo, carpeta):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM configuracion")
    cursor.execute("INSERT INTO configuracion (ultimo_archivo, carpeta_trabajo) VALUES (?, ?)", (archivo, carpeta))
    conn.commit()
    conn.close()

def cargar_config_proyecto():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT ultimo_archivo, carpeta_trabajo FROM configuracion LIMIT 1")
        row = cursor.fetchone()
    except sqlite3.OperationalError:
        row = None
    conn.close()
    if row:
        return row[0], row[1]
    return "proyecto_bolimur_default.json", "proyectos_bolimur"

perfil_guardado = cargar_datos_instalador()
ultimo_archivo_db, carpeta_trabajo_db = cargar_config_proyecto()

# --- DISEÑO CORPORATIVO Y ESTILOS AVANZADOS ---
st.markdown("""
    <style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 14px;
        border: 2px solid #343a40 !important;
    }
    th {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        text-align: left;
        padding: 12px !important;
        border: 2px solid #343a40 !important;
        font-weight: bold;
    }
    td {
        padding: 12px !important;
        border: 1px solid #adb5bd !important;
        color: #212529 !important;
        background-color: #ffffff !important;
    }
    tr:nth-child(even) td {
        background-color: #e9ecef !important;
    }

    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 3px solid #dee2e6;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        background-color: #ffffff !important;
        border: 2px solid #ced4da !important;
        padding: 10px 15px !important;
        border-radius: 8px !important;
        margin-bottom: 8px !important;
        font-weight: bold !important;
        color: #212529 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
        background-color: #e9ecef !important;
        border-color: #ff4b4b !important;
        color: #ff4b4b !important;
    }

    .info-box-tecnico {
        background-color: #f8f9fa;
        border-left: 5px solid #0056b3;
        padding: 15px;
        border-radius: 6px;
        margin: 15px 0;
        color: #333333;
        font-size: 14px;
        line-height: 1.5;
    }
    .recomendacion-box {
        background-color: #e8f4fd;
        border: 2px solid #b8daff;
        padding: 18px;
        border-radius: 8px;
        margin: 15px 0;
        color: #004085;
    }
    </style>
""", unsafe_allow_html=True)

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
IZ_COBRE_ENTERRADO = {
    1.5: 22.0, 2.5: 29.0, 4: 38.0, 6: 48.0, 10: 65.0, 16: 85.0, 
    25: 110.0, 35: 135.0, 50: 160.0, 70: 170.0, 95: 202.0, 
    120: 230.0, 150: 270.0, 185: 310.0, 240: 360.0
}
CALIBRES_INTERRUPTORES = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630]

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
    st.session_state.grupos_viviendas = [{"nombre": "Viviendas Estándar", "qty": 10, "pot": 5750, "nocturna": False}]
if 'servicios_generales' not in st.session_state:
    st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 1, "potencia": 3000.0, "factor": 1.30}]
if 'locales' not in st.session_state:
    st.session_state.locales = [{"nombre": "Local Comercial A", "qty": 1, "superficie": 100.0}]
if 'irve_config' not in st.session_state:
    st.session_state.irve_config = {"con_irve": True, "tipo_esquema": "Esquema 1.5 (Recarga vinculada)", "num_plazas": 5, "pot_plaza": 3680.0}
if 'lga_long_val' not in st.session_state:
    st.session_state.lga_long_val = 20.0
if 'carpeta_trabajo_val' not in st.session_state:
    st.session_state.carpeta_trabajo_val = carpeta_trabajo_db

# --- MENÚ LATERAL ---
with st.sidebar:
    if os.path.exists("logo_bolimur.PNG"):
        st.image("logo_bolimur.PNG", use_container_width=True)
    else:
        st.markdown("""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 4px solid #ff4b4b; margin-bottom: 15px; text-align: center;">
                <h3 style="color: white; margin: 0; font-size: 18px;">⚡ BOLIMUR</h3>
                <p style="color: #b0b0b0; font-size: 12px; margin: 5px 0 0 0;">Instalaciones Integrales<br>Murcia, España</p>
            </div>
        """, unsafe_allow_html=True)

    st.header("📂 Navegación de Módulos")
    seleccion_modulo = st.radio(
        "Selecciona la sección:",
        [
            "🏠 Menú Principal",
            "🧮 Cálculo Rápido (CDT & Icc)",
            "🏢 Previsión de Cargas (Pt)",
            "⚡ Línea General (LGA)",
            "🔌 Derivación Individual (DI)",
            "📚 Tablas ITC-BT según REBT y Guías",
            "📐 Esquemas Unifilares",
            "📄 Informe Técnico MTD",
            "💡 Simulador Consumo",
            "🛡️ Resolución y Exámenes"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.header("👤 Perfil Instalador (Murcia)")
    with st.expander("⚙️ Configurar Datos"):
        inst_nombre = st.text_input("Nombre Instalador", perfil_guardado["nombre"])
        inst_nif = st.text_input("NIF", perfil_guardado["nif"])
        inst_empresa = st.text_input("Empresa", perfil_guardado["empresa"])
        inst_carnet = st.text_input("Nº Carné", perfil_guardado["carnet"])
        inst_cat = st.text_input("Categoría", perfil_guardado["categoria"])
        inst_tipo = st.text_input("Tipo", perfil_guardado["tipo_inst"])
        inst_num = st.text_input("Nº Inscripción", perfil_guardado["num_inscripcion"])
        inst_tel = st.text_input("Teléfono", perfil_guardado["telefono"])
        inst_email = st.text_input("Email", perfil_guardado["email"])

        if st.button("💾 Guardar Perfil"):
            guardar_datos_instalador(inst_nombre, inst_nif, inst_empresa, inst_carnet, inst_tel, inst_email, inst_cat, inst_tipo, inst_num, "Región de Murcia")
            st.success("✅ ¡Guardado!")
            st.rerun()

    st.markdown("---")
    st.header("📂 Proyectos (JSON)")
    st.session_state.nombre_proyecto = st.text_input("Nombre Proyecto", st.session_state.nombre_proyecto)
    st.session_state.carpeta_trabajo_val = st.text_input("Carpeta Trabajo", st.session_state.carpeta_trabajo_val)

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("💾 Guardar"):
            datos_proyecto = {
                "nombre_proyecto": st.session_state.nombre_proyecto,
                "grupos_viviendas": st.session_state.grupos_viviendas,
                "servicios_generales": st.session_state.servicios_generales,
                "locales": st.session_state.locales,
                "irve": st.session_state.irve_config,
                "lga_long": st.session_state.lga_long_val
            }
            if not os.path.exists(st.session_state.carpeta_trabajo_val):
                os.makedirs(st.session_state.carpeta_trabajo_val)
            nombre_f = os.path.join(st.session_state.carpeta_trabajo_val, "proyecto_bolimur_default.json")
            with open(nombre_f, "w", encoding="utf-8") as f:
                json.dump(datos_proyecto, f, indent=4, ensure_ascii=False)
            guardar_config_proyecto("proyecto_bolimur_default.json", st.session_state.carpeta_trabajo_val)
            st.success("✅ Guardado")
    with col_p2:
        if st.button("📂 Cargar"):
            nombre_f = os.path.join(st.session_state.carpeta_trabajo_val, "proyecto_bolimur_default.json")
            if os.path.exists(nombre_f):
                with open(nombre_f, "r", encoding="utf-8") as f:
                    proyecto_cargado = json.load(f)
                    st.session_state.nombre_proyecto = proyecto_cargado.get("nombre_proyecto", "Proyecto")
                    st.session_state.grupos_viviendas = proyecto_cargado.get("grupos_viviendas", [])
                    st.session_state.servicios_generales = proyecto_cargado.get("servicios_generales", [])
                    st.session_state.locales = proyecto_cargado.get("locales", [])
                    st.session_state.irve_config = proyecto_cargado.get("irve", {"con_irve": True, "tipo_esquema": "Esquema 1.5", "num_plazas": 5, "pot_plaza": 3680.0})
                    st.session_state.lga_long_val = proyecto_cargado.get("lga_long", 20.0)
                st.success("✅ Cargado")
                st.rerun()
            else:
                st.warning("⚠️ No encontrado")

# =========================================================================
# CONTENIDO DE LAS PANTALLAS
# =========================================================================

if seleccion_modulo.startswith("🏠"):
    st.title("⚡ BOLIMUR INSTALACIONES INTEGRALES")
    st.write("Bienvenido al panel de cálculo eléctrico REBT. Despliega el menú lateral izquierdo para seleccionar cualquier módulo de cálculo.")
    st.info("💡 **Consejo de navegación:** En teléfonos y tablets, la barra lateral se oculta automáticamente para ofrecerte una visión 100% despejada.")

elif seleccion_modulo.startswith("🧮"):
    st.title("🧮 Ventana de Cálculo Rápido Avanzado (Bombas, Líneas Largas y Extremos)")
    st.write("Herramienta de diagnóstico integral para comprobación de tramos complejos.")

elif seleccion_modulo.startswith("🏢"):
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")

elif seleccion_modulo.startswith("⚡"):
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")

elif seleccion_modulo.startswith("🔌"):
    st.title("Derivación Individual - DI (ITC-BT-15)")

# =========================================================================
# MÓDULO: TABLAS ITC-BT SEGÚN REBT Y GUÍAS (CON EXPLICACIONES Y RECOMENDACIONES)
# =========================================================================
elif seleccion_modulo.startswith("📚"):
    st.title("📚 Compendio de Tablas ITC-BT según REBT y Guías Técnicas")
    st.write("Centro de documentación técnica oficial con explicaciones de uso y recomendaciones normativas para instalaciones en obra.")

    sub_itc = st.tabs([
        "🔌 ITC-BT-15 (Derivaciones Individuales)",
        "🏢 ITC-BT-10 (Previsión de Cargas)",
        "⚡ ITC-BT-14 (Línea General LGA)",
        "🏠 ITC-BT-25 y Guías (Instalaciones Interiores y Alturas)",
        "🛡️ UNE-HD 60364-5-52 (Admisibilidad)"
    ])

    with sub_itc[0]:
        st.subheader("📑 ITC-BT-15: Derivaciones Individuales (DI)")
        
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 ¿Para qué sirve y cómo se utiliza esta tabla?</b><br>
            Esta tabla permite realizar un dimensionamiento directo de la sección de los conductores de la DI en función del calibre del Interruptor General Automático (IGA) y la longitud del trazado. Se debe comprobar que la caída de tensión no supere los límites reglamentarios (1% para contadores concentrados o 0,5% según modelo).
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 1. Cálculo Directo de Derivaciones Individuales (Cobre C = 48)")
        st.markdown("""
        | Sección Mínima DI | Diámetro Tubo (mm) | CDT Máxima | Calibre IGA: 25 A | Calibre IGA: 32 A | Calibre IGA: 40 A | Calibre IGA: 50 A | Calibre IGA: 63 A |
        | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
        | **6 mm²** | 32 mm | 0,5% / 1,0% / 1,5% | 5,75 kW / 6 m / 13 m / 19 m | 7,32 kW / 5 m / 10 m / 18 m | 9,2 kW / 6 m / 13 m | 11,5 kW / - | 14,49 kW / - |
        | **10 mm²** | 32 mm | 0,5% / 1,0% / 1,5% | 22 m / 33 m / 44 m | 17 m / 25 m / 34 m | 13 m / 20 m / 27 m | 8 m / 17 m / 22 m | 7 m / 14 m / - |
        | **16 mm²** | 40 mm | 0,5% / 1,0% / 1,5% | 35 m / 53 m / 70 m | 27 m / 41 m / 55 m | 21 m / 31 m / 42 m | 17 m / 26 m / 35 m | 14 m / 21 m / 28 m |
        | **25 mm²** | 50 mm | 0,5% / 1,0% / 1,5% | 55 m / 83 m / 110 m | 43 m / 65 m / 86 m | 34 m / 51 m / 69 m | 27 m / 41 m / 55 m | 21 m / 32 m / 43 m |
        | **35 mm²** | 50 mm | 0,5% / 1,0% / 1,5% | 77 m / 116 m / 154 m | 60 m / 91 m / 121 m | 48 m / 72 m / 96 m | 38 m / 58 m / 77 m | 31 m / 46 m / 61 m |
        """)

        st.markdown("""
        <div class="info-box-tecnico">
            <b>🏗️ Dimensionamiento de Canaladuras (Patinillos de Obra):</b><br>
            Establece la anchura (L) y profundidad (P) de los conductos de fábrica según el número de derivaciones individuales.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        | Número de Derivaciones | Anchura L (Profundidad P = 0,15 m, una fila) | Anchura L (Profundidad P = 0,30 m, dos filas) |
        | :---: | :---: | :---: |
        | **Hasta 12** | 0,65 m | 0,50 m |
        | **13 a 24** | 1,25 m | 0,65 m |
        | **25 a 36** | 1,85 m | 0,95 m |
        | **37 a 48** | 2,45 m | 1,35 m |
        """)

    with sub_itc[1]:
        st.subheader("🏢 ITC-BT-10: Previsión de Cargas para Edificios")
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 ¿Para qué sirve?</b><br>
            Define los coeficientes de simultaneidad (K) aplicables al conjunto de viviendas y locales de un edificio para calcular la potencia total prevista (Pt) de la centralización y la LGA.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        | Nº Viviendas (n) | Coeficiente de Simultaneidad (K) |
        | :---: | :---: |
        | **1** | 1,0 |
        | **2** | 2,0 |
        | **3** | 3,0 |
        | **4** | 3,8 |
        | **5 - 21** | Escalonado reglamentario oficial |
        | **> 21** | $15,3 + (n - 21) \\times 0,5$ |
        """)

    with sub_itc[2]:
        st.subheader("⚡ ITC-BT-14: Línea General de Alimentación (LGA)")
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 ¿Para qué sirve?</b><br>
            Establece los requisitos obligatorios de sección mínima ($10\\text{ mm}^2$ en Cobre y $16\\text{ mm}^2$ en Aluminio) y los límites de caída de tensión máxima (0,5% o 1,0%) para la línea que alimenta las centralizaciones de contadores.
        </div>
        """, unsafe_allow_html=True)

    with sub_itc[3]:
        st.subheader("🏠 ITC-BT-25 y Guías: Instalaciones Interiores y Alturas Reglamentarias")
        
        st.markdown("""
        <div class="recomendacion-box">
            <h4 style="margin-top: 0; color: #004085;">📌 RECOMENDACIONES IMPORTANTES Y ALTURAS DE INSTALACIÓN EN VIVIENDAS</h4>
            <ul>
                <li><b>Cajas de Registro:</b> Su parte superior debe quedar instalada a un mínimo de <b>0,20 m del techo</b>. Las tapas de registro deben ser accesibles y nunca ocultas por falsos techos fijos sin trampilla.</li>
                <li><b>Tomas de Corriente (Enchufes):</b> 
                    <ul>
                        <li>Altura habitual en paredes secas: Entre <b>0,20 m y 0,30 m</b> sobre el suelo.</li>
                        <li>En cocinas y baños: A más de <b>0,50 m</b> del fregadero o encimeras de cocción y respetando los volúmenes de protección de baños (Volumen 1 y 2).</li>
                    </ul>
                </li>
                <li><b>Interruptores y Conmutadores:</b> Altura recomendada entre <b>0,90 m y 1,10 m</b> sobre el suelo (facilitando el acceso a personas con movilidad reducida).</li>
                <li><b>Cuadros Generales de Mando y Protección (CGMP):</b> El eje del cuadro de protecciones se colocará generalmente entre <b>1,40 m y 2,00 m</b> sobre el suelo.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with sub_itc[4]:
        st.subheader("🛡️ UNE-HD 60364-5-52: Intensidades Admisibles ($I_z$)")
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 ¿Para qué sirve?</b><br>
            Proporciona la corriente máxima admisible que soporta un cable sin sobrepasar su temperatura límite de servicio según el tipo de aislamiento y modo de instalación.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        | Tipo de Cable e Instalación | Sistema | 6 mm² | 10 mm² | 16 mm² | 25 mm² | 35 mm² | 50 mm² |
        | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
        | **ES07Z1-K (450/750V) - Tubos empotrados** | Monofásico (`sm`) | 36 A | 50 A | 66 A | 84 A | 104 A | - |
        | **ES07Z1-K (450/750V) - Tubos empotrados** | Trifásico (`st`) | 32 A | 44 A | 59 A | 77 A | 96 A | 117 A |
        | **RZ1-K (0,6/1kV) - Tubos enterrados** | Monofásico (`sm`) | 71 A | 94 A | 122 A | 157 A | 186 A | - |
        | **RZ1-K (0,6/1kV) - Tubos enterrados** | Trifásico (`st`) | 58 A | 77 A | 100 A | 128 A | 152 A | 184 A |
        """)

elif seleccion_modulo.startswith("📐"):
    st.title("📐 Esquemas Unifilares")

elif seleccion_modulo.startswith("📄"):
    st.title("📄 Informe Técnico Formal MTD")

elif seleccion_modulo.startswith("💡"):
    st.title("💡 Simulador Consumo Eléctrico")

elif seleccion_modulo.startswith("🛡️"):
    st.title("🛡️ Resolución Avanzada y Exámenes")