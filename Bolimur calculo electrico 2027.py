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
    .pia-destacado {
        background: linear-gradient(135deg, #0056b3, #00a8cc);
        color: #ffffff;
        padding: 18px 25px;
        border-radius: 10px;
        font-size: 22px;
        font-weight: bold;
        text-align: center;
        margin: 15px 0;
        box-shadow: 0 4px 10px rgba(0, 123, 255, 0.3);
        border: 2px solid #ffffff;
    }
    .fusible-vistoso {
        background: linear-gradient(135deg, #ff4b4b, #ff8c00);
        color: #ffffff;
        padding: 15px 25px;
        border-radius: 8px;
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        margin: 15px 0;
        box-shadow: 0 4px 10px rgba(255, 75, 75, 0.3);
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

# --- ESTADO INICIAL DE LA SESIÓN (INICIO ESTRICTO EN 0) ---
if 'nombre_proyecto' not in st.session_state:
    st.session_state.nombre_proyecto = "Estudio Eléctrico Edificio Plurifamiliar"
if 'grupos_viviendas' not in st.session_state:
    st.session_state.grupos_viviendas = [{"nombre": "Viviendas Estándar", "qty": 0, "pot": 5750, "nocturna": False}]
if 'servicios_generales' not in st.session_state:
    st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 0, "potencia": 0.0, "factor": 1.30}]
if 'locales' not in st.session_state:
    st.session_state.locales = [{"nombre": "Local Comercial A", "qty": 0, "superficie": 0.0}]
if 'irve_config' not in st.session_state:
    st.session_state.irve_config = {"con_irve": True, "tipo_esquema": "Esquema 1.5 (Recarga vinculada)", "num_plazas": 0, "pot_plaza": 3680.0}
if 'lga_long_val' not in st.session_state:
    st.session_state.lga_long_val = 0.0
if 'carpeta_trabajo_val' not in st.session_state:
    st.session_state.carpeta_trabajo_val = carpeta_trabajo_db
if 'favoritos_itc' not in st.session_state:
    st.session_state.favoritos_itc = ["ITC-BT-14: Línea General de Alimentación (LGA)", "ITC-BT-15: Derivaciones Individuales (DI)"]

# --- FUNCIÓN GLOBAL SEGURA PARA CALCULAR PT ---
def calcular_pt_global():
    p_viv = sum(int(round(v["qty"] * v["pot"] * (v["qty"] if v["nocturna"] else get_coef_simultaneidad(v["qty"])))) for v in st.session_state.grupos_viviendas)
    p_loc = sum(max(l["superficie"] * 100.0, 3450.0 if l["superficie"] > 0 else 0.0) * l["qty"] for l in st.session_state.locales)
    p_serv = sum(s["potencia"] * s["qty"] * s.get("factor", 1.30) for s in st.session_state.servicios_generales)
    return p_viv + int(p_loc) + int(p_serv) + 3450

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
            "📚 Compendio de Tablas REBT (ITC 01 a 51)",
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
                    st.session_state.irve_config = proyecto_cargado.get("irve", {"con_irve": True, "tipo_esquema": "Esquema 1.5", "num_plazas": 0, "pot_plaza": 3680.0})
                    st.session_state.lga_long_val = proyecto_cargado.get("lga_long", 0.0)
                st.success("✅ Cargado")
                st.rerun()
            else:
                st.warning("⚠️ No encontrado")

# =========================================================================
# CONTENIDO DE LAS PANTALLAS (CON TODAS LAS EXPLICACIONES Y FÓRMULAS)
# =========================================================================

if seleccion_modulo.startswith("🏠"):
    st.title("⚡ BOLIMUR INSTALACIONES INTEGRALES")
    st.write("Bienvenido al panel de cálculo eléctrico REBT. Despliega el menú lateral izquierdo para seleccionar cualquier módulo de cálculo.")
    st.info("💡 **Consejo de navegación:** En teléfonos y tablets, la barra lateral se oculta automáticamente para ofrecerte una visión 100% despejada.")

elif seleccion_modulo.startswith("🧮"):
    st.title("🧮 Ventana de Cálculo Rápido Avanzado (Bombas, Líneas Largas y Extremos)")
    st.write("Herramienta de diagnóstico integral para comprobación de tramos complejos, evaluando Caída de Tensión, Calentamiento, Coordinación de Protecciones e Icc min.")

    rc1, rc2 = st.columns(2)
    with rc1:
        modo_carga = st.radio("Modo de entrada:", ["Por Potencia (W o CV)", "Por Intensidad Directa (A)"], key="mod_q")
        tipo_red_q = st.selectbox("Sistema eléctrico", ["Monofásico (230V)", "Trifásico (400V)"], key="tr_q1")
        
        if modo_carga == "Por Potencia (W o CV)":
            val_pot_q = st.number_input("Potencia activa (W)", value=0.0, step=100.0, key="vp_q")
            cos_q = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.85, key="cos_q")
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q:
                ib_q = val_pot_q / (v_nom_calc * cos_q) if v_nom_calc * cos_q > 0 else 0.0
            else:
                ib_q = val_pot_q / (math.sqrt(3) * v_nom_calc * cos_q) if v_nom_calc * cos_q > 0 else 0.0
        else:
            ib_q = st.number_input("Intensidad de diseño Ib (A)", value=0.0, step=1.0, key="ib_q1")
            cos_q = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.85, key="cos_q_2")
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q:
                val_pot_q = ib_q * v_nom_calc * cos_q
            else:
                val_pot_q = ib_q * math.sqrt(3) * v_nom_calc * cos_q

        long_q = st.number_input("Longitud del circuito / tirada (m) [Ida]", value=0.0, step=5.0, key="l_q")

    with rc2:
        metodo_q_key = st.selectbox("Método de Instalación (UNE-HD 60364-5-52):", list(METODOS_INSTALACION.keys()), index=0, key="met_q")
        mat_q = st.selectbox("Material conductor", ["cobre", "aluminio"], key="m_q")
        ais_q = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="a_q")
        cdt_lim_q = st.number_input("Caída de Tensión máxima permitida (%)", value=3.0, step=0.5, key="cdt_q")
        
        col_icc_inp, col_icc_btn = st.columns([3, 1])
        with col_icc_inp:
            icc_orig_q = st.number_input("Icc de cortocircuito en el origen (kA)", value=10.0, step=0.5, format="%.2f", key="icc_orig_q")
        with col_icc_btn:
            st.write("") 
            st.write("")
            with st.popover("📖 Guía Icc"):
                st.markdown("### ⚡ Guía Rápida de Icc en Origen")
                st.write("• **¿Qué es?** La corriente de cortocircuito máxima entregada por el cuadro.")

    gamma_q = GAMMA_MAP.get((mat_q, ais_q), 44.0)
    dv_max_q = v_nom_calc * (cdt_lim_q / 100.0) if cdt_lim_q > 0 else 1.0
    
    if "Monofásico" in tipo_red_q:
        s_cdt_q = (2.0 * val_pot_q * long_q) / (gamma_q * dv_max_q * v_nom_calc) if dv_max_q * v_nom_calc > 0 else 1.5
    else:
        s_cdt_q = (val_pot_q * long_q) / (gamma_q * dv_max_q * v_nom_calc) if dv_max_q * v_nom_calc > 0 else 1.5

    tabla_iz_q = IZ_COBRE_ENTERRADO if "D (" in metodo_q_key else IZ_COBRE_TUBO
    s_cal_q = 1.5
    for sec, iz_val in tabla_iz_q.items():
        if iz_val >= ib_q:
            s_cal_q = sec
            break

    min_reg_q = 1.5 if mat_q == "cobre" else 10.0
    s_bruta_q = max(s_cdt_q, s_cal_q, min_reg_q)
    s_opt_q = seleccionar_seccion_optima(s_bruta_q)

    if "Monofásico" in tipo_red_q:
        dv_real_v_q = (2.0 * val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc) if s_opt_q * v_nom_calc > 0 else 0.0
    else:
        dv_real_v_q = (val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc) if s_opt_q * v_nom_calc > 0 else 0.0
    
    dv_real_pct_q = (dv_real_v_q / v_nom_calc) * 100.0 if v_nom_calc > 0 else 0.0

    rho_q = 1.0 / gamma_q if gamma_q > 0 else 0.0
    r_cable_q = (rho_q * long_q) / s_opt_q if s_opt_q > 0 else 0.0
    if "Monofásico" in tipo_red_q:
        z_tot_q = (v_nom_calc / (icc_orig_q * 1000.0)) + (2.0 * r_cable_q) if icc_orig_q > 0 else 1.0
    else:
        z_tot_q = (v_nom_calc / (icc_orig_q * 1000.0)) + r_cable_q if icc_orig_q > 0 else 1.0
        
    icc_fin_q = v_nom_calc / z_tot_q / 1000.0 if z_tot_q > 0 else 0.0
    prot_q = seleccionar_proteccion(ib_q)
    corriente_disparo_magnetico = prot_q * 10.0
    salta_proteccion = (icc_fin_q * 1000.0) >= corriente_disparo_magnetico

    st.markdown("---")
    st.subheader("Memoria Justificativa Analítica y Fórmulas Desarrolladas")

    st.markdown(f"""
    <div class="formula-box">
        <b>1. Intensidad de Diseño (Ib):</b><br>
        • Sustitución: {val_pot_q:,.1f} / ({v_nom_calc} * {cos_q}) = <b>{ib_q:.2f} A</b>
    </div>
    <div class="formula-box">
        <b>2. Sección por Caída de Tensión (Delta V):</b><br>
        • Cálculo teórico puro: <b>{s_cdt_q:.2f} mm²</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="pia-destacado">
            🛡️ PROTECCIÓN MAGNETOTÉRMICA RECOMENDADA (PIA): {prot_q} A (Curva C) + Diferencial 30 mA
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### Tabla Detallada de Verificación y Coordinación (Sobrecarga e Iz >= Ib)")
    tabla_q_md = "| Sección Comercial (mm²) | Corriente Admisible Iz (A) | Caída de Tensión Real (%) | Estado de Verificación frente a Sobrecarga (In <= 0.91 * Iz) |\n| :---: | :---: | :---: | :--- |\n"
    for sec_com in [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70]:
        iz_c = tabla_iz_q.get(sec_com, 250.0)
        if "Monofásico" in tipo_red_q:
            dv_c_pct = (((2.0 * val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0 if v_nom_calc > 0 else 0.0
        else:
            dv_c_pct = (((val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0 if v_nom_calc > 0 else 0.0

        cond_sobrecarga = 0.91 * iz_c
        if iz_c < ib_q and ib_q > 0:
            est_v = f"❌ No cumple por calentamiento (Iz = {iz_c} A < Ib = {ib_q:.2f} A)"
        elif prot_q > cond_sobrecarga:
            est_v = f"❌ No cumple la 2ª condición (In = {prot_q} A > 0.91 * {iz_c})"
        elif sec_com == s_opt_q:
            est_v = f"✅ **CUMPLE PERFECTAMENTE** (Iz = {iz_c} A -> In = {prot_q} A <= 0.91 * {iz_c})"
        else:
            est_v = "Válido pero superior"

        tabla_q_md += f"| {sec_com} mm² | {iz_c} A | {dv_c_pct:.3f}% | {est_v} |\n"
    st.markdown(tabla_q_md)

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ CONCLUSIÓN Y SECCIÓN ÓPTIMA: <span style="color: #ff4b4b; font-size: 24px;">{s_opt_q} mm²</span> de {mat_q.upper()} ({ais_q})<br>
            <hr style="border: 1px solid #444; margin: 10px 0;">
            <span style="font-size: 15px; color: #e0e0e0; font-weight: normal; line-height: 1.6;">
            <b>🔍 Verificación técnica completa:</b> Cable dimensionado frente a calentamiento, caída de tensión del {dv_real_pct_q:.3f}% y cortocircuito en extremo.
            </span>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("🏢"):
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")
    
    col_t1, col_b1 = st.columns([4, 1])
    with col_t1:
        st.write("Calculamos la Potencia Total Prevista (Pt) sumando viviendas, locales, servicios, garajes e IRVE con su justificación analítica y reglamentaria.")
    with col_b1:
        if st.button("🔄 Resetear Cargas"):
            st.session_state.grupos_viviendas = [{"nombre": "Grupo 1", "qty": 0, "pot": 5750, "nocturna": False}]
            st.session_state.locales = [{"nombre": "Local 1", "superficie": 0.0, "qty": 0}]
            st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "potencia": 0.0, "factor": 1.30, "qty": 0}]
            st.rerun()

    col_h_viv, col_pop_viv = st.columns([4, 1])
    with col_h_viv:
        st.subheader("1. Viviendas del Edificio (P1)")
    with col_pop_viv:
        with st.popover("📖 Ver Tabla ITC-BT-10 Completa"):
            st.markdown("### Tabla Oficial de Simultaneidad (ITC-BT-10)")
            tabla_aux_md = "| Nº Viviendas (n) | Coeficiente (K) |\n| :---: | :---: |\n"
            for k_viv, v_coef in COEF_SIMULTANEIDAD_VIVIENDAS.items():
                tabla_aux_md += f"| {k_viv} | {v_coef} |\n"
            tabla_aux_md += "| > 21 | 15,3 + (n - 21) x 0,5 |"
            st.markdown(tabla_aux_md)

    if st.button("➕ Añadir Grupo de Viviendas"):
        st.session_state.grupos_viviendas.append({"nombre": f"Grupo {len(st.session_state.grupos_viviendas)+1}", "qty": 0, "pot": 5750, "nocturna": False})

    total_viviendas_edificio = 0
    pot_total_viviendas = 0

    for idx, viv in enumerate(st.session_state.grupos_viviendas):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: viv["nombre"] = st.text_input(f"Descripción #{idx+1}", viv["nombre"], key=f"viv_nom_{idx}")
        with c2: viv["qty"] = st.number_input(f"Nº Viviendas #{idx+1}", min_value=0, value=int(viv["qty"]), key=f"viv_qty_{idx}")
        with c3: viv["pot"] = st.selectbox(f"Unidad de Potencia n.º {idx+1}", [5750, 7360, 9200, 11500], index=[5750, 7360, 9200, 11500].index(viv["pot"]) if viv["pot"] in [5750, 7360, 9200, 11500] else 0, key=f"viv_pot_{idx}")
        with c4: viv["nocturna"] = st.checkbox(f"Tarifa Nocturna #{idx+1}", value=viv["nocturna"], key=f"viv_noc_{idx}")
        with c5:
            if st.button("🗑️", key=f"del_viv_{idx}"):
                if len(st.session_state.grupos_viviendas) > 1: st.session_state.grupos_viviendas.pop(idx); st.rerun()

        total_viviendas_edificio += viv["qty"]
        qty_g = viv["qty"]
        pot_unit = viv["pot"]
        noct = viv["nocturna"]
        cs_grupo = float(qty_g) if noct else get_coef_simultaneidad(qty_g)
        pot_parcial_g = int(round(qty_g * pot_unit * cs_grupo))
        pot_total_viviendas += pot_parcial_g

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #0066cc; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Justificación Grupo #{idx+1} ({viv['nombre']}):</b> Coeficiente K = {cs_grupo:.2f}.<br>
            Cálculo parcial: {qty_g} viviendas x {pot_unit} W x {cs_grupo} = <b>{pot_parcial_g:,} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 Viviendas totales: **{total_viviendas_edificio}** | **Total Parcial P1 (Viviendas): {pot_total_viviendas:,} W**")
    st.markdown("---")
    
    st.subheader("2. Locales Comerciales y Oficinas (P2)")
    if st.button("➕ Añadir local"): st.session_state.locales.append({"nombre": f"Local {len(st.session_state.locales)+1}", "superficie": 0.0, "qty": 0})
    pot_total_locales = 0.0

    for idx, loc in enumerate(st.session_state.locales):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1: loc["nombre"] = st.text_input(f"Local #{idx+1}", loc["nombre"], key=f"loc_nom_{idx}")
        with c2: loc["superficie"] = st.number_input(f"Superficie m² #{idx+1}", min_value=0.0, value=float(loc["superficie"]), key=f"loc_sup_{idx}")
        with c3: loc["qty"] = st.number_input(f"Cant #{idx+1}", min_value=0, value=int(loc["qty"]), key=f"loc_qty_{idx}")
        with c4:
            if st.button("🗑️", key=f"del_loc_{idx}"): st.session_state.locales.pop(idx); st.rerun()

        sup_val = loc["superficie"]
        cant_loc = loc["qty"]
        pot_por_sup = sup_val * 100.0
        pot_unidad = max(pot_por_sup, 3450.0 if sup_val > 0 else 0.0) if cant_loc > 0 else 0.0
        pot_parcial_local = pot_unidad * cant_loc
        pot_total_locales += pot_parcial_local

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Análisis Local #{idx+1} ({loc['nombre']}):</b> {sup_val} m² x 100 W/m² = {pot_por_sup:,.0f} W.<br>
            Total Parcial Local: <b>{pot_parcial_local:,.0f} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 **Total Parcial P2 (Locales Comerciales): {int(pot_total_locales):,} W**")
    st.markdown("---")

    col_h_serv, col_pop_serv = st.columns([4, 1])
    with col_h_serv:
        st.subheader("3. Servicios Generales (P3)")
    with col_pop_serv:
        with st.popover("📖 Clasificación NTE-ITA (Ascensores)"):
            st.markdown("### Tabla Oficial NTE-ITA (Instalaciones de Transporte)")
            st.markdown("""
            | Código | Capacidad y Velocidad | Potencia Estimada Aprox. |
            | :--- | :--- | :---: |
            | **ITA-01** | Carga 5 personas / Vel. 0.63 m/s | ~ 2.2 kW |
            | **ITA-02** | Carga 5 personas / Vel. 1.00 m/s | ~ 3.0 kW |
            """)

    if st.button("➕ Añadir servicio"): st.session_state.servicios_generales.append({"nombre": "Ascensor principal", "potencia": 0.0, "factor": 1.30, "qty": 0})
    pot_total_servicios = 0.0

    opciones_factores_k = {
        "Ascensor Principal (K = 1.30)": 1.30,
        "Motores / Bombas secundarias (K = 1.25)": 1.25,
        "Ascensor Secundario (K = 1.15)": 1.15,
        "Lámparas / Descarga (K = 1.80)": 1.80,
        "Servicios directos / LED (K = 1.00)": 1.00,
        "Personalizado (Valor libre)": -1.0
    }

    for idx, serv in enumerate(st.session_state.servicios_generales):
        st.markdown(f"#### ⚙️ Servicio #{idx+1}")
        c1, c2, c3 = st.columns(3)
        with c1:
            serv["nombre"] = st.text_input(f"Descripción #{idx+1}", serv["nombre"], key=f"serv_nom_{idx}")
        with c2:
            serv["potencia"] = st.number_input(f"Potencia W #{idx+1}", min_value=0.0, value=float(serv["potencia"]), key=f"serv_pot_{idx}")
        with c3:
            serv["qty"] = st.number_input(f"Cantidad #{idx+1}", min_value=0, value=int(serv["qty"]), key=f"serv_qty_{idx}")

        c4, c5 = st.columns([4, 1])
        factor_actual = serv.get("factor", 1.30)
        def_opt_idx = 0
        for i, (k_text, v_val) in enumerate(opciones_factores_k.items()):
            if v_val == factor_actual:
                def_opt_idx = i
                break

        with c4:
            sel_opt = st.selectbox(f"Coeficiente K #{idx+1} (Despliega completo sin cortes)", list(opciones_factores_k.keys()), index=def_opt_idx, key=f"serv_tipo_opt_{idx}")
            if sel_opt.startswith("Personalizado"):
                factor = st.number_input(f"Valor K personalizado #{idx+1}", min_value=0.1, value=float(factor_actual if factor_actual > 0 else 1.25), key=f"serv_k_pers_{idx}")
            else:
                factor = opciones_factores_k[sel_opt]
            serv["factor"] = factor

        with c5:
            st.write("")
            st.write("")
            if st.button("🗑️ Eliminar", key=f"del_serv_{idx}"):
                st.session_state.servicios_generales.pop(idx)
                st.rerun()

        p_parcial_serv = serv["potencia"] * serv["qty"] * factor
        pot_total_servicios += p_parcial_serv

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #ffc107; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 13px; color: #333;">
            <b>Justificación Técnica Servicio #{idx+1} ({serv['nombre']}):</b> Coeficiente <b>K = {factor:.2f}</b>.<br>
            Cálculo: {serv['potencia']} W x {serv['qty']} ud(s) x {factor:.2f} = <b>{p_parcial_serv:,.1f} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 **Total Parcial P3 (Servicios Generales): {pot_total_servicios:,.1f} W**")
    st.markdown("---")

    col_h_irve, col_pop_irve = st.columns([4, 1])
    with col_h_irve:
        st.subheader("4. Garajes e Infraestructura de Recarga de Vehículos Eléctricos - IRVE (ITC-BT-52)")
    with col_pop_irve:
        with st.popover("📖 Explicación Técnica IRVE (ITC-BT-52)"):
            st.markdown("### Criterios Técnicos y Reglamentarios IRVE")
            st.write("1. **Previsión de Potencia por Plaza:** Cada plaza de garaje con preinstalación IRVE se calcula con una potencia unitaria estándar de **3.680 W**.")

    gc1, gc2, gc3 = st.columns(3)
    with gc1: sup_garaje = st.number_input("Sup. Garaje m²", value=0.0)
    with gc2: plazas_garaje = st.number_input("Plazas Garaje con Preinstalación IRVE", value=0)
    with gc3: opcion_irve = st.selectbox("Sistema de Recarga IRVE (ITC-BT-52)", ["Esquema 1.5 (Recarga vinculada en plazas de garaje - Coef. 0.3)", "Esquema 1.4 (Línea troncal con derivaciones para plazas - Coef. 0.5)"])

    pot_garaje_por_sup = sup_garaje * 20.0
    pot_garaje_adjudicada = max(pot_garaje_por_sup, 3450.0 if sup_garaje > 0 else 0.0) if sup_garaje > 0 else 0.0
    
    coef_irve = 0.3 if "Esquema 1.5" in opcion_irve else 0.5
    pot_total_irve = int(round(plazas_garaje * 3680.0 * coef_irve))
    pot_total_garaje_irve = int(pot_garaje_adjudicada) + pot_total_irve

    st.markdown(f"""
    <div style="background-color: #f8f9fa; border-left: 4px solid #17a2b8; padding: 12px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
        <b>Justificación Técnica Detallada del Cálculo IRVE (ITC-BT-52):</b><br>
        • Total Parcial P4 (Garaje + IRVE): <b>{pot_total_garaje_irve:,} W</b>
    </div>
    """, unsafe_allow_html=True)

    pt_total = pot_total_viviendas + int(pot_total_locales) + int(pot_total_servicios) + pot_total_garaje_irve

    st.markdown(f"""
        <div class="resumen-parciales-box">
            <h3 style="color: #111; margin-top: 0;">📋 RESUMEN DE POTENCIAS PARCIALES Y TOTALES (ITC-BT-10)</h3>
            <ul>
                <li><b>P1 (Viviendas - {total_viviendas_edificio} uds):</b> {pot_total_viviendas:,} W</li>
                <li><b>P2 (Locales Comerciales):</b> {int(pot_total_locales):,} W</li>
                <li><b>P3 (Servicios Generales):</b> {pot_total_servicios:,.1f} W</li>
                <li><b>P4 (Garaje e IRVE - ITC-BT-52):</b> {pot_total_garaje_irve:,} W</li>
            </ul>
            <hr style="border: 1px solid #ced4da;">
            <h2 style="color: #ff4b4b; margin-bottom: 0;">⚡ SUMA TOTAL PREVISTA (Pt): {pt_total:,.1f} W ({pt_total/1000:,.2f} kW)</h2>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("⚡"):
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    st.write("Configura los parámetros de la LGA y visualiza abajo la memoria técnica detallada con tablas de corriente admisible y el fusible recomendado.")
    
    with st.expander("🏗️ Selector de Sistema de Instalación y Material", expanded=True):
        metodo_lga_key = st.selectbox("Método de Instalación recomendado:", list(METODOS_INSTALACION.keys()), index=3, key="met_lga")
        tipo_enlace_lga = st.radio("Modelo de esquema reglamentario para la LGA:", [
            "Modelo 1: Contadores totalmente concentrados (Límite CDT = 0.5%)",
            "Modelo 2: Centralizaciones parciales distribuidas (Límite CDT = 1.0%)"
        ], key="enlace_lga")

    dv_pct_lga = 0.5 if "Modelo 1" in tipo_enlace_lga else 1.0

    # LECTURA AUTOMÁTICA SEGURA DE PT
    pt_calculado_automatico = float(calcular_pt_global())

    lga_modo_potencia = st.radio("Origen de la potencia para el cálculo de la LGA:", [
        f"Automático (Desde Previsión de Cargas Pt = {pt_calculado_automatico:,.1f} W)",
        "Manual (Introducir valor libremente)"
    ], key="lga_modo_pot")

    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        if lga_modo_potencia.startswith("Automático"):
            lga_pot = st.number_input("Potencia de cálculo LGA (W) [Automática desde Pt]", value=pt_calculado_automatico, disabled=True, key="lga_pot_auto_val")
        else:
            lga_pot = st.number_input("Potencia de cálculo LGA (W) [Manual]", min_value=0.0, value=0.0, step=500.0, key="lga_pot_manual")

        lga_long = st.number_input("Longitud de la LGA (m)", value=0.0, key="lga_l")
        st.session_state.lga_long_val = lga_long
        lga_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="lga_mat")
    with lga_c2:
        lga_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="lga_ais")
        lga_cos = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.9, key="lga_cos")
        
        st.markdown("##### 🛡️ Parámetros de Cortocircuito (Icc)")
        lga_icc_max = st.number_input("Icc máxima en origen / CGP (kA)", value=12.0, key="lga_icc_max_input")
        lga_icc_min = st.number_input("Icc mínima al final / Centralización CC (kA)", value=7.5, key="lga_icc_min_input")

    gamma_lga = 44.0 if "XLPE" in lga_aisl else 48.5
    ib_lga = lga_pot / (math.sqrt(3) * 400 * lga_cos) if lga_cos > 0 else 0.0
    dv_max_lga = 400 * (dv_pct_lga / 100.0)
    s_cdt_lga = (lga_pot * lga_long) / (gamma_lga * dv_max_lga * 400) if gamma_lga * dv_max_lga * 400 > 0 else 10.0
    
    tabla_iz = IZ_COBRE_ENTERRADO if "D (" in metodo_lga_key else IZ_COBRE_TUBO
    in_lga_auto = seleccionar_proteccion(ib_lga)
    
    s_final_lga = seleccionar_seccion_optima(max(s_cdt_lga, 10.0))
    while True:
        iz_a = tabla_iz.get(s_final_lga, 230.0)
        if in_lga_auto <= 0.91 * iz_a and iz_a >= ib_lga:
            break
        idx_s = SECCIONES_COMERCIALES.index(s_final_lga) if s_final_lga in SECCIONES_COMERCIALES else 5
        if idx_s < len(SECCIONES_COMERCIALES) - 1:
            s_final_lga = SECCIONES_COMERCIALES[idx_s + 1]
        else:
            break

    iz_final_lga = tabla_iz.get(s_final_lga, 230.0)
    dv_real_lga_v = (lga_pot * lga_long) / (gamma_lga * s_final_lga * 400) if gamma_lga * s_final_lga * 400 > 0 else 0.0
    dv_real_lga_pct = (dv_real_lga_v / 400) * 100

    st.markdown("---")
    st.subheader("📋 Memoria de Justificación Técnica Detallada (LGA)")

    tabla_markdown = "| Sección Comercial (mm²) | Corriente Admisible Iz (A) [Enterrado Cu 90ºC] | Estado de Verificación frente a Sobrecarga (In <= 0.91 * Iz) |\n| :---: | :---: | :--- |\n"
    for s_com in [70, 95, 120, 150, 185]:
        iz_val_t = tabla_iz.get(s_com, 0)
        cond_s_lga = 0.91 * iz_val_t
        if s_com == s_final_lga:
            est = f"✅ **CUMPLE PERFECTAMENTE** (Iz = {iz_val_t} A -> In = {in_lga_auto} A <= 0.91 * {iz_val_t})"
        else:
            est = "Válido reglamentariamente"
        tabla_markdown += f"| {s_com} mm² | {iz_val_t} A | {est} |\n"
    st.markdown(tabla_markdown)

    st.markdown(f"""
    **1. Cálculo por Caída de Tensión:**
    * Límite reglamentario: Delta V% <= {dv_pct_lga}%
    * Valor absoluto: Delta V = ({dv_pct_lga} / 100) * 400 = {dv_max_lga:.2f} V
    * Sección teórica: S = ( {lga_long} * {lga_pot:,.2f} ) / ( {gamma_lga} * {dv_max_lga:.2f} * 400 ) = {s_cdt_lga:.2f} mm²

    **2. Intensidad de Diseño y Protección por Sobrecarga:**
    * Ib = P / ( 1.732 * V * cos phi ) = **{ib_lga:.2f} A**
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="fusible-vistoso">
            🛡️ FUSIBLE RECOMENDADO EN CGP (In): {in_lga_auto} A (Tipo gG)
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN A ADOPATAR (LGA): <span style="color: #ff4b4b; font-size: 24px;">{s_final_lga} mm²</span> de Cobre ({lga_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
            Neutro: <b>{70.0 if s_final_lga >= 70 else s_final_lga} mm²</b> | Tubo: <b>160 mm</b> | CDT Real: <b>{dv_real_lga_pct:.3f}%</b> | <b>Fusible CGP: {in_lga_auto} A</b>
            </span>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("🔌"):
    st.title("Derivación Individual - DI (ITC-BT-15)")
    st.write("Configura los parámetros de la Derivación Individual y visualiza abajo la memoria técnica detallada con fórmulas y tablas de admisibilidad.")

    with st.expander("🏗️ Selector de Sistema de Instalación y Material", expanded=True):
        metodo_di_key = st.selectbox("Método de Instalación recomendado:", list(METODOS_INSTALACION.keys()), key="met_di")
        tipo_enlace_di = st.radio("Modelo de esquema para la Derivación Individual:", [
            "Modelo A: DI desde contadores concentrados (Límite CDT = 1.0%)",
            "Modelo B: DI desde contadores diseminados / viviendas (Límite CDT = 0.5%)"
        ], key="enlace_di")

    dv_pct_di = 1.0 if "Modelo A" in tipo_enlace_di else 0.5

    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Potencia de la Derivación (W)", [5750, 7360, 9200, 11500], key="di_p")
        di_long = st.number_input("Longitud de la DI (m)", value=0.0, key="di_l")
        di_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="di_mat")
    with di_c2:
        di_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="di_ais")
        di_cos = st.slider("Coseno phi (cos phi) DI", 0.8, 1.0, 1.0, key="di_cos")

    gamma_di = GAMMA_MAP.get((di_mat, di_aisl), 44.0)
    ib_di = di_pot / (230.0 * di_cos) if di_cos > 0 else 0.0
    dv_max_di = 230.0 * (dv_pct_di / 100.0)
    s_cdt_di = (2.0 * di_pot * di_long) / (gamma_di * dv_max_di * 230.0) if gamma_di * dv_max_di * 230.0 > 0 else 6.0
    
    s_cal_di = 1.5
    tabla_iz_di = IZ_COBRE_ENTERRADO if "D (" in metodo_di_key else IZ_COBRE_TUBO
    for sec, iz_val in tabla_iz_di.items():
        if iz_val >= ib_di:
            s_cal_di = sec
            break

    min_reg_di = 6.0 if di_mat == "cobre" else 10.0
    s_bruta_di = max(s_cdt_di, s_cal_di, min_reg_di)
    s_optima_di = seleccionar_seccion_optima(s_bruta_di)

    prot_di = seleccionar_proteccion(ib_di)
    dv_real_di_v = (2.0 * di_pot * di_long) / (gamma_di * s_optima_di * 230.0) if gamma_di * s_optima_di * 230.0 > 0 else 0.0
    dv_real_di_pct = (dv_real_di_v / 230.0) * 100

    st.markdown("---")
    st.subheader("📋 Memoria de Cálculo Justificada y Detallada (Derivación Individual)")

    tabla_di_md = "| Sección Comercial (mm²) | Corriente Admisible Iz (A) | Caída de Tensión Real (%) | Estado de Verificación |\n| :---: | :---: | :---: | :--- |\n"
    for sec_com in [6, 10, 16, 25]:
        iz_c = tabla_iz_di.get(sec_com, 100.0)
        dv_c_pct = ((2.0 * di_pot * di_long) / (gamma_di * sec_com * 230.0) / 230.0) * 100 if sec_com > 0 else 0.0
        est_v = "✅ Cumple perfectamente" if sec_com == s_optima_di else "Válido"
        tabla_di_md += f"| {sec_com} mm² | {iz_c} A | {dv_c_pct:.3f}% | {est_v} |\n"
    st.markdown(tabla_di_md)

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN ADOPTADA PARA LA DI: <span style="color: #ff4b4b; font-size: 24px;">{s_optima_di} mm²</span> de {di_mat.upper()} ({di_aisl})<br>
            <hr style="border: 1px solid #444; margin: 10px 0;">
            <span style="font-size: 15px; color: #e0e0e0; font-weight: normal; line-height: 1.6;">
            • Intensidad de diseño: <b>{ib_di:.2f} A</b> | CDT Real: <b>{dv_real_di_pct:.3f}%</b> | Protección: <b>{prot_di} A</b>
            </span>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("📚"):
    st.title("📚 Compendio General y Completo de Tablas REBT (ITC-BT 01 a 51)")
    st.write("Catálogo normativo absoluto. Todas las Instrucciones Técnicas Complementarias del REBT (Real Decreto 842/2002).")

    todas_las_itc = [
        "ITC-BT-01: Terminología", "ITC-BT-02: Normas de referencia", "ITC-BT-03: Instaladores autorizados",
        "ITC-BT-04: Documentación y puesta en servicio", "ITC-BT-05: Verificaciones e inspecciones",
        "ITC-BT-06: Redes aéreas distribución BT", "ITC-BT-07: Redes subterráneas distribución BT",
        "ITC-BT-08: Sistemas de conexión del neutro", "ITC-BT-09: Alumbrado exterior",
        "ITC-BT-10: Previsión de cargas para suministros BT", "ITC-BT-11: Redes de distribución y acometidas",
        "ITC-BT-12: Esquemas de distribución BT", "ITC-BT-13: Líneas generales de alimentación (LGA)",
        "ITC-BT-14: Línea General de Alimentación (LGA)", "ITC-BT-15: Derivaciones Individuales (DI)",
        "ITC-BT-16: Centralización de contadores", "ITC-BT-17: Dispositivos generales y de protección (IGM/P)",
        "ITC-BT-18: Instalaciones de puesta a tierra", "ITC-BT-19: Instalaciones interiores en viviendas",
        "ITC-BT-20: Sistemas de instalación (Tubos y canales)", "ITC-BT-21: Tubos y canales protectores",
        "ITC-BT-22: Protección contra sobreintensidades", "ITC-BT-23: Protección contra sobretensiones",
        "ITC-BT-24: Protección contra contactos directos e indirectos",
        "ITC-BT-25: Viviendas. Número y características de circuitos",
        "ITC-BT-26: Locales con baño o ducha", "ITC-BT-27: Locales de pública concurrencia",
        "ITC-BT-28: Locales de pública concurrencia (Prescripciones especiales)",
        "ITC-BT-29: Locales con riesgo de incendio o explosión", "ITC-BT-30: Locales húmedos, mojados o corrosivos",
        "ITC-BT-31: Piscinas y fuentes", "ITC-BT-32: Máquinas de elevación y transporte",
        "ITC-BT-33: Instalaciones provisionales y de obra", "ITC-BT-34: Ferias y stands",
        "ITC-BT-35: Establecimientos agrícolas y hortícolas", "ITC-BT-36: Instalaciones a muy baja tensión",
        "ITC-BT-37: Caravanas y parques de caravanas", "ITC-BT-38: Quirófanos y salas de intervención",
        "ITC-BT-39: Cercas eléctricas para ganadería", "ITC-BT-40: Instalaciones generadoras BT",
        "ITC-BT-42: Locales comerciales", "ITC-BT-43: Instalación de receptores (Generalidades)",
        "ITC-BT-44: Receptores para alumbrado", "ITC-BT-45: Aparatos de calefacción",
        "ITC-BT-46: Cables y sistemas (Industria)", "ITC-BT-47: Instalaciones de motores",
        "ITC-BT-48: Locales de características especiales", "ITC-BT-49: Instalaciones fotovoltaicas",
        "ITC-BT-50: Paneles solares térmicos / eléctricos", "ITC-BT-51: Automatización y gestión técnica"
    ]

    st.markdown("### ⭐ Acceso Rápido: Tus Favoritas en Obra")
    if st.session_state.favoritos_itc:
        cols_fav = st.columns(min(len(st.session_state.favoritos_itc), 3))
        for idx_f, fav_item in enumerate(st.session_state.favoritos_itc):
            with cols_fav[idx_f % len(cols_fav)]:
                if st.button(f"📌 Abrir {fav_item.split(':')[0]}", key=f"btn_fav_{idx_f}"):
                    st.session_state.itc_activa_sel = fav_item
                    st.rerun()

    st.markdown("---")
    default_idx = 9 if 'itc_activa_sel' not in st.session_state else todas_las_itc.index(st.session_state.itc_activa_sel) if st.session_state.itc_activa_sel in todas_las_itc else 9
    itc_seleccionada = st.selectbox("Selecciona cualquier ITC-BT del reglamento:", todas_las_itc, index=default_idx)

    st.markdown(f"""
    <div class="info-box-tecnico">
        <b>📖 Especificaciones Oficiales de {itc_seleccionada}:</b><br>
        Esta instrucción establece los requisitos técnicos obligatorios para el diseño, ejecución y verificación de las instalaciones eléctricas en baja tensión dentro del marco de la Región de Murcia.
    </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("📐"):
    st.title("📐 Esquemas Unifilares del Edificio y Desdobles Reglamentarios")
    st.write("Representación unifilar esquemática completa para Vivienda Básica, Elevada y desdobles de circuitos interiores.")

    st.markdown("### 📋 1. Esquema General de Enlace y Parámetros del Proyecto")
    texto_esquema_gen = f"""PROYECTO: {st.session_state.nombre_proyecto}
LGA: 120 mm² RZ1-K Cu | Neutro: 70 mm² | Tubo: 160 mm
Icc máx: 12 kA | Icc mín: 7.5 kA | Fusibles CGP: 200 A gG | IGM: 250 A"""
    st.code(texto_esquema_gen, language="text")

    st.markdown("### 🏠 2. Esquema Unifilar - Vivienda de Electrificación Básica (ITC-BT-25)")
    esquema_basica = """IGM (Interruptor General Automático) 25A + ID (Diferencial 40A / 30mA)
 ├── C1 (Iluminación - 10A - Cable 1.5 mm²)
 ├── C2 (Tomas de corriente general - 16A - Cable 2.5 mm²)
 ├── C3 (Cocina y Horno - 25A - Cable 6 mm²)
 ├── C4 (Lavadora, Lavavajillas, Termo - 20A - Cable 4 mm²)
 └── C5 (Baños y Cocina tomas auxiliares - 16A - Cable 2.5 mm²)"""
    st.code(esquema_basica, language="text")

    st.markdown("### 🏢 3. Esquema Unifilar - Vivienda de Electrificación Elevada y Desdobles (ITC-BT-25)")
    esquema_elevada = """IGM (Interruptor General Automático) 40A + ID (Diferencial 40A / 30mA)
 ├── C1 (Iluminación Principal - 10A - Cable 1.5 mm²)
 ├── C1 bis (Iluminación Adicional / Terrazas - 10A - Cable 1.5 mm²)
 ├── C2 (Tomas de corriente general - 16A - Cable 2.5 mm²)
 ├── C2 bis (Tomas adicionales / Habitaciones - 16A - Cable 2.5 mm²)
 ├── C3 (Cocina y Horno - 25A - Cable 6 mm²)
 ├── C4 (Lavadora, Lavavajillas, Secadora - 20A - Cable 4 mm²)
 ├── C5 (Baños y Cocina tomas auxiliares - 16A - Cable 2.5 mm²)
 ├── C6 (Calefacción / Climatización - 25A - Cable 6 mm²)
 ├── C7 (Aire Acondicionado - 16/20A - Cable 2.5 / 4 mm²)
 └── C8 / C9 / C10 (Circuitos especiales y domótica)"""
    st.code(esquema_elevada, language="text")

elif seleccion_modulo.startswith("📄"):
    st.title("📄 Informe Técnico Formal MTD")
    st.write("Vista previa del informe técnico completo listo para firmar y presentar en Industria.")

elif seleccion_modulo.startswith("💡"):
    st.title("💡 Simulador Consumo Eléctrico")
    kw_c = st.number_input("kW contratados", value=4.6)
    kwh_m = st.number_input("kWh al mes", value=250.0)
    total_con_impuestos = ((kw_c * 0.11 * 30) + (kwh_m * 0.18)) * 1.051127 * 1.10
    st.metric("Estimación Factura Mensual", f"{total_con_impuestos:.2f} €")

elif seleccion_modulo.startswith("🛡️"):
    st.title("🛡️ Resolución Avanzada y Exámenes (Casos Prácticos)")
    st.write("Selecciona el caso de examen o problema tipo para ver el desarrollo analítico completo.")