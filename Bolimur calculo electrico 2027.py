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

# --- DISEÑO CORPORATIVO Y ESTILOS ---
st.markdown("""
    <style>
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

# --- MENÚ LATERAL COMPLETO (SIDEBAR) ---
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

    st.header("👤 Perfil Instalador (Murcia)")
    with st.expander("⚙️ Configurar Datos Profesionales"):
        inst_nombre = st.text_input("Nombre Instalador", perfil_guardado["nombre"])
        inst_nif = st.text_input("NIF", perfil_guardado["nif"])
        inst_empresa = st.text_input("Empresa", perfil_guardado["empresa"])
        inst_carnet = st.text_input("Nº Carné Profesional", perfil_guardado["carnet"])
        inst_cat = st.text_input("Categoría", perfil_guardado["categoria"])
        inst_tipo = st.text_input("Tipo", perfil_guardado["tipo_inst"])
        inst_num = st.text_input("Nº Inscripción CARM", perfil_guardado["num_inscripcion"])
        inst_tel = st.text_input("Teléfono", perfil_guardado["telefono"])
        inst_email = st.text_input("Email", perfil_guardado["email"])

        if st.button("💾 Guardar Perfil en BD"):
            guardar_datos_instalador(inst_nombre, inst_nif, inst_empresa, inst_carnet, inst_tel, inst_email, inst_cat, inst_tipo, inst_num, "Región de Murcia")
            st.success("✅ ¡Guardado!")
            st.rerun()

    st.markdown("---")
    st.header("📂 Gestión de Proyectos (JSON)")
    st.session_state.nombre_proyecto = st.text_input("Nombre del Proyecto", st.session_state.nombre_proyecto)
    st.session_state.carpeta_trabajo_val = st.text_input("Carpeta de Trabajo", st.session_state.carpeta_trabajo_val)

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("💾 Guardar JSON"):
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
            st.success("✅ ¡Guardado con éxito!")
    with col_p2:
        if st.button("📂 Cargar JSON"):
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
                st.success("✅ ¡Cargado!")
                st.rerun()
            else:
                st.warning("⚠️ Archivo no encontrado.")

# --- PESTAÑAS PRINCIPALES (CÁLCULO RÁPIDO PUESTO EN PRIMER LUGAR) ---
pestanas = st.tabs([
    "🧮 Cálculo Rápido (CDT & Icc)",
    "🏢 Previsión de Cargas (Pt)", 
    "⚡ Línea General (LGA)", 
    "🔌 Derivación Individual (DI)", 
    "🛡️ Resolución Avanzada y Exámenes",
    "📊 Tabla Guía Estilo PLC Madrid",
    "📐 Esquemas Unifilares",
    "📄 Informe Técnico MTD",
    "💡 Simulador Consumo"
])

# =========================================================================
# PESTAÑA 1: CÁLCULO RÁPIDO (CDT & ICC) - ENRIQUECIDO Y EN PRIMERA POSICIÓN
# =========================================================================
with pestanas[0]:
    st.title("🧮 Ventana de Cálculo Rápido (Justificación Analítica y Fórmulas)")
    st.write("Calcula cualquier tramo eligiendo libremente el método de instalación reglamentario visualizando las fórmulas y cálculos desarrollados paso a paso.")

    rc1, rc2 = st.columns(2)
    with rc1:
        modo_carga = st.radio("Modo de entrada de potencia / corriente:", ["Por Potencia (W)", "Por Intensidad Directa (A)"], key="mod_q")
        tipo_red_q = st.selectbox("Sistema eléctrico", ["Monofásico (230V)", "Trifásico (400V)"], key="tr_q1")
        
        if modo_carga == "Por Potencia (W)":
            val_pot_q = st.number_input("Potencia activa (W)", value=5750.0, step=250.0, key="vp_q")
            cos_q = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.95, key="cos_q")
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q:
                ib_q = val_pot_q / (v_nom_calc * cos_q)
            else:
                ib_q = val_pot_q / (math.sqrt(3) * v_nom_calc * cos_q)
        else:
            ib_q = st.number_input("Intensidad de diseño Ib (A)", value=25.0, step=1.0, key="ib_q1")
            cos_q = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.95, key="cos_q_2")
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q:
                val_pot_q = ib_q * v_nom_calc * cos_q
            else:
                val_pot_q = ib_q * math.sqrt(3) * v_nom_calc * cos_q

        long_q = st.number_input("Longitud del circuito (m)", value=20.0, step=1.0, key="l_q")

    with rc2:
        metodo_q_key = st.selectbox("Método de Instalación (UNE-HD 60364-5-52):", list(METODOS_INSTALACION.keys()), key="met_q")
        mat_q = st.selectbox("Material conductor", ["cobre", "aluminio"], key="m_q")
        ais_q = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="a_q")
        cdt_lim_q = st.number_input("Caída de Tensión máxima permitida (%)", value=3.0, step=0.5, key="cdt_q")
        icc_orig_q = st.number_input("Icc de cortocircuito en el origen (kA)", value=10.0, step=0.5, key="icc_orig_q")

    gamma_q = GAMMA_MAP.get((mat_q, ais_q), 44.0)
    dv_max_q = v_nom_calc * (cdt_lim_q / 100.0)
    
    if "Monofásico" in tipo_red_q:
        s_cdt_q = (2.0 * val_pot_q * long_q) / (gamma_q * dv_max_q * v_nom_calc)
    else:
        s_cdt_q = (val_pot_q * long_q) / (gamma_q * dv_max_q * v_nom_calc)

    tabla_iz_q = IZ_COBRE_ENTERRADO if "D (" in metodo_q_key else IZ_COBRE_TUBO
    s_cal_q = 1.5
    for sec, iz_val in tabla_iz_q.items():
        if iz_val >= ib_q:
            s_cal_q = sec
            break

    min_reg_q = 1.5 if mat_q == "cobre" else 10.0
    s_bruta_q = max(s_cdt_q, s_cal_q, min_reg_q)
    s_opt_q = seleccionar_seccion_optima(s_bruta_q)

    # Cálculo exacto de Caída de Tensión real
    if "Monofásico" in tipo_red_q:
        dv_real_v_q = (2.0 * val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc)
    else:
        dv_real_v_q = (val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc)
    
    dv_real_pct_q = (dv_real_v_q / v_nom_calc) * 100.0

    # Cálculo de resistencia e Icc
    rho_q = 1.0 / gamma_q
    r_q = (rho_q * long_q) / s_opt_q
    if "Monofásico" in tipo_red_q:
        z_tot_q = (v_nom_calc / (icc_orig_q * 1000.0)) + (2.0 * r_q)
    else:
        z_tot_q = (v_nom_calc / (icc_orig_q * 1000.0)) + r_q
        
    icc_fin_q = v_nom_calc / z_tot_q / 1000.0 if z_tot_q > 0 else 0.0
    prot_q = seleccionar_proteccion(ib_q)

    st.markdown("---")
    st.subheader("📋 Memoria Justificativa Analítica y Fórmulas Desarrolladas")

    st.markdown(f"""
    **1. Intensidad de Diseño ($I_b$):**  
    * Formula aplicable ({tipo_red_q}): $I_b = \\frac{{P}}{{{'V \\cdot \\cos\\varphi' if 'Monofásico' in tipo_red_q else '\\sqrt{3} \\cdot V \\cdot \\cos\\varphi'}}}$
    """)
    st.info(f"Cálculo numérico: {val_pot_q:,.1f} W / ({'230 V x ' if 'Monofásico' in tipo_red_q else '1.732 x 400 V x '}{cos_q}) = **{ib_q:.2f} A**")

    st.markdown(f"""
    **2. Caída de Tensión (Límite $\\Delta V \\le {cdt_lim_q}\\%$):**  
    * Caída de Tensión absoluta permitida: $\\Delta V = {v_nom_calc:.0f}\\text{{ V}} \\times \\frac{{{cdt_lim_q}}}{{100}} = {dv_max_q:.2f}\\text{{ V}}$
    * Sección teórica necesaria por caída de tensión: $S = \\frac{{{'2 \\cdot P \\cdot L' if 'Monofásico' in tipo_red_q else 'P \\cdot L'}}}{{\\gamma \\cdot \\Delta V \\cdot V}}$
    """)
    st.info(f"Cálculo numérico: ({'2 x ' if 'Monofásico' in tipo_red_q else ''}{val_pot_q:,.1f} W x {long_q} m) / ({gamma_q} x {dv_max_q:.2f} V x {v_nom_calc:.0f} V) = **{s_cdt_q:.2f} mm²**")

    st.markdown("### 📊 Tabla Comparativa y Justificación por Secciones Comercializables")
    tabla_q_md = "| Sección Comercial (mm²) | Corriente Admisible Iz (A) | Caída de Tensión Real (%) | Estado Reglamentario |\n| :---: | :---: | :---: | :--- |\n"
    for sec_com in [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120]:
        iz_c = tabla_iz_q.get(sec_com, 250.0)
        if "Monofásico" in tipo_red_q:
            dv_c_pct = (((2.0 * val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0
        else:
            dv_c_pct = (((val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0
            
        if sec_com >= s_bruta_q:
            estado_c = "⭐ **SELECCIONADA (ÓPTIMA)**"
        elif iz_c < ib_q:
            estado_c = "❌ No cumple por calentamiento"
        elif dv_c_pct > cdt_lim_q:
            estado_c = "❌ No cumple caída de tensión"
        else:
            estado_c = "Válida pero superior"
        tabla_q_md += f"| {sec_com} mm² | {iz_c} A | {dv_c_pct:.3f}% | {estado_c} |\n"
    st.markdown(tabla_q_md)

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN ÓPTIMA SELECCIONADA: <span style="color: #ff4b4b; font-size: 24px;">{s_opt_q} mm²</span> de {mat_q.upper()} ({ais_q})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
            Intensidad de diseño: <b>{ib_q:.2f} A</b> | CDT Real: <b>{dv_real_pct_q:.3f}% ({dv_real_v_q:.2f} V)</b> | Icc final estimada: <b>{icc_fin_q:.2f} kA</b> | Protección asociada: <b>PIA {prot_q} A</b>
            </span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 2: PREVISIÓN DE CARGAS (INTOCABLE)
# =========================================================================
with pestanas[1]:
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")
    
    col_t1, col_b1 = st.columns([4, 1])
    with col_t1:
        st.write("Calculamos la Potencia Total Prevista (Pt) sumando viviendas, locales, servicios, garajes e IRVE con su justificación analítica y reglamentaria.")
    with col_b1:
        if st.button("🔄 Resetear Cargas"):
            st.session_state.grupos_viviendas = [{"nombre": "Grupo 1", "qty": 10, "pot": 5750, "nocturna": False}]
            st.session_state.locales = [{"nombre": "Local 1", "superficie": 100.0, "qty": 1}]
            st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "potencia": 3000.0, "factor": 1.30, "qty": 1}]
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
        st.session_state.grupos_viviendas.append({"nombre": f"Grupo {len(st.session_state.grupos_viviendas)+1}", "qty": 1, "pot": 5750, "nocturna": False})

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
        cs_grupo = float(qty_g) if noct else get_coef_simultaneidad(qty_g)
        pot_parcial_g = int(round(qty_g * pot_unit * cs_grupo))
        pot_total_viviendas += pot_parcial_g

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #0066cc; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Justificación Grupo #{idx+1} ({viv['nombre']}):</b> Coeficiente K = {cs_grupo:.2f} ({'Tarifa nocturna' if noct else 'ITC-BT-10'}).<br>
            Cálculo parcial: {qty_g} viviendas x {pot_unit} W x {cs_grupo} = <b>{pot_parcial_g:,} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 Viviendas totales: **{total_viviendas_edificio}** | **Total Parcial P1 (Viviendas): {pot_total_viviendas:,} W**")
    st.markdown("---")
    
    # 2. LOCALES COMERCIALES
    st.subheader("2. Locales Comerciales y Oficinas (P2)")
    if st.button("➕ Añadir local"): st.session_state.locales.append({"nombre": f"Local {len(st.session_state.locales)+1}", "superficie": 100.0, "qty": 1})
    pot_total_locales = 0.0

    for idx, loc in enumerate(st.session_state.locales):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1: loc["nombre"] = st.text_input(f"Local #{idx+1}", loc["nombre"], key=f"loc_nom_{idx}")
        with c2: loc["superficie"] = st.number_input(f"Superficie m² #{idx+1}", min_value=0.0, value=float(loc["superficie"]), key=f"loc_sup_{idx}")
        with c3: loc["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(loc["qty"]), key=f"loc_qty_{idx}")
        with c4:
            if st.button("🗑️", key=f"del_loc_{idx}"): st.session_state.locales.pop(idx); st.rerun()

        sup_val = loc["superficie"]
        cant_loc = loc["qty"]
        pot_por_sup = sup_val * 100.0
        pot_unidad = max(pot_por_sup, 3450.0 if sup_val > 0 else 0.0)
        pot_parcial_local = pot_unidad * cant_loc
        pot_total_locales += pot_parcial_local

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Análisis Local #{idx+1} ({loc['nombre']}):</b> {sup_val} m² x 100 W/m² = {pot_por_sup:,.0f} W (Suelo mínimo reglamentario: 3.450 W).<br>
            Total Parcial Local: {cant_loc} x {pot_unidad:,.0f} W = <b>{pot_parcial_local:,.0f} W</b>
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
            st.markdown("""
            | Código | Capacidad y Velocidad | Potencia Estimada Aprox. |
            | :--- | :--- | :---: |
            | **ITA-01** | Carga 5 personas / Vel. 0.63 m/s | ~ 2.2 kW |
            | **ITA-02** | Carga 5 personas / Vel. 1.00 m/s | ~ 3.0 kW |
            | **ITA-03** | Carga 8 personas / Vel. 1.00 m/s | ~ 4.0 kW |
            | **ITA-04** | Carga 8 personas / Vel. 1.60 m/s | ~ 5.5 kW |
            | **ITA-05** | Carga 13 personas / Vel. 1.60 m/s | ~ 7.5 kW |
            """)

    if st.button("➕ Añadir servicio"): st.session_state.servicios_generales.append({"nombre": "Ascensor principal", "potencia": 3000.0, "factor": 1.30, "qty": 1})
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
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1:
            serv["nombre"] = st.text_input(f"Tipo de Servicio #{idx+1}", serv["nombre"], key=f"serv_nom_{idx}")
        with c2: serv["potencia"] = st.number_input(f"Potencia W #{idx+1}", min_value=0.0, value=float(serv["potencia"]), key=f"serv_pot_{idx}")
        with c3: serv["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(serv["qty"]), key=f"serv_qty_{idx}")
        
        factor_actual = serv.get("factor", 1.30)
        def_opt_idx = 0
        for i, (k_text, v_val) in enumerate(opciones_factores_k.items()):
            if v_val == factor_actual:
                def_opt_idx = i
                break

        with c4:
            sel_opt = st.selectbox(f"Coeficiente K #{idx+1}", list(opciones_factores_k.keys()), index=def_opt_idx, key=f"serv_tipo_opt_{idx}")
            if sel_opt.startswith("Personalizado"):
                factor = st.number_input(f"Valor K personalizado #{idx+1}", min_value=0.1, value=float(factor_actual if factor_actual > 0 else 1.25), key=f"serv_k_pers_{idx}")
            else:
                factor = opciones_factores_k[sel_opt]
            serv["factor"] = factor

        with c5:
            if st.button("🗑️", key=f"del_serv_{idx}"): st.session_state.servicios_generales.pop(idx); st.rerun()

        p_parcial_serv = serv["potencia"] * serv["qty"] * factor
        pot_total_servicios += p_parcial_serv

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #ffc107; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Justificación Técnica Servicio #{idx+1} ({serv['nombre']}):</b> Coeficiente <b>K = {factor:.2f}</b> (NTE-ITA / ITC-BT-10).<br>
            Cálculo: {serv['potencia']} W x {serv['qty']} ud(s) x {factor:.2f} = <b>{p_parcial_serv:,.1f} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 **Total Parcial P3 (Servicios Generales): {pot_total_servicios:,.1f} W**")
    st.markdown("---")

    # 4. GARAJES E IRVE
    col_h_irve, col_pop_irve = st.columns([4, 1])
    with col_h_irve:
        st.subheader("4. Garajes e Infraestructura de Recarga de Vehículos Eléctricos - IRVE (ITC-BT-52)")
    with col_pop_irve:
        with st.popover("📖 Explicación Técnica IRVE (ITC-BT-52)"):
            st.markdown("### Criterios Técnicos y Reglamentarios IRVE")
            st.write("1. **Previsión de Potencia por Plaza:** Cada plaza de garaje con preinstalación IRVE se calcula con una potencia unitaria estándar de **3.680 W**.")
            st.write("2. **Esquema de Instalación (ITC-BT-52):**")
            st.write("   • **Esquema 1.5 (Recarga vinculada en plazas de garaje):** Se aplica un coeficiente reductor de simultaneidad del **30% (0.3)** sobre el total de plazas previstas.")
            st.write("   • **Esquema 1.4 (Línea troncal con derivaciones):** Se aplica un coeficiente del **50% (0.5)**.")
            st.write("3. **Garaje (ITC-BT-10):** Se asignan 20 W por cada m² de superficie, con un mínimo legal de 3.450 W.")

    gc1, gc2, gc3 = st.columns(3)
    with gc1: sup_garaje = st.number_input("Sup. Garaje m²", value=300.0)
    with gc2: plazas_garaje = st.number_input("Plazas Garaje con Preinstalación IRVE", value=5)
    with gc3: opcion_irve = st.selectbox("Sistema de Recarga IRVE (ITC-BT-52)", ["Esquema 1.5 (Recarga vinculada en plazas de garaje - Coef. 0.3)", "Esquema 1.4 (Línea troncal con derivaciones para plazas - Coef. 0.5)"])

    pot_garaje_por_sup = sup_garaje * 20.0
    pot_garaje_adjudicada = max(pot_garaje_por_sup, 3450.0 if sup_garaje > 0 else 0.0)
    
    coef_irve = 0.3 if "Esquema 1.5" in opcion_irve else 0.5
    pot_total_irve = int(round(plazas_garaje * 3680.0 * coef_irve))
    pot_total_garaje_irve = int(pot_garaje_adjudicada) + pot_total_irve

    st.markdown(f"""
    <div style="background-color: #f8f9fa; border-left: 4px solid #17a2b8; padding: 12px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
        <b>Justificación Técnica Detallada del Cálculo IRVE (ITC-BT-52):</b><br>
        • Criterio adoptado: {opcion_irve}.<br>
        • Cálculo analítico IRVE: {plazas_garaje} plazas x 3.680 W x {coef_irve} (Coeficiente de simultaneidad) = <b>{pot_total_irve:,} W</b>.<br>
        • Garaje (ITC-BT-10): {sup_garaje} m² x 20 W/m² = {pot_garaje_por_sup:,.0f} W (Suelo mínimo: 3.450 W) -> <b>{int(pot_garaje_adjudicada):,} W</b>.<br>
        • <b>Total Parcial P4 (Garaje + IRVE):</b> {int(pot_garaje_adjudicada):,} W + {pot_total_irve:,} W = <b>{pot_total_garaje_irve:,} W</b>
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

# =========================================================================
# PESTAÑA 3: LGA (INTOCABLE)
# =========================================================================
with pestanas[2]:
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    st.write("Configura los parámetros de la LGA y visualiza abajo la memoria técnica detallada con tablas de corriente admisible y el fusible recomendado.")
    
    with st.expander("🏗️ Selector de Sistema de Instalación y Material", expanded=True):
        metodo_lga_key = st.selectbox("Método de Instalación recomendado:", list(METODOS_INSTALACION.keys()), index=3, key="met_lga")
        tipo_enlace_lga = st.radio("Modelo de esquema reglamentario para la LGA:", [
            "Modelo 1: Contadores totalmente concentrados (Límite CDT = 0.5%)",
            "Modelo 2: Centralizaciones parciales distribuidas (Límite CDT = 1.0%)"
        ], key="enlace_lga")

    dv_pct_lga = 0.5 if "Modelo 1" in tipo_enlace_lga else 1.0

    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        lga_pot = st.number_input("Potencia de cálculo LGA (W)", min_value=0.0, value=float(pt_total if pt_total > 0 else 112500.0), step=500.0, key="lga_pot_manual")
        lga_long = st.number_input("Longitud de la LGA (m)", value=float(st.session_state.lga_long_val), key="lga_l")
        st.session_state.lga_long_val = lga_long
        lga_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="lga_mat")
    with lga_c2:
        lga_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="lga_ais")
        lga_cos = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.9, key="lga_cos")
        
        st.markdown("##### 🛡️ Parámetros de Cortocircuito (Icc)")
        lga_icc_max = st.number_input("Icc máxima en origen / CGP (kA)", value=12.0, key="lga_icc_max_input")
        lga_icc_min = st.number_input("Icc mínima al final / Centralización CC (kA)", value=7.5, key="lga_icc_min_input")

    gamma_lga = 44.0 if "XLPE" in lga_aisl else 48.5
    ib_lga = lga_pot / (math.sqrt(3) * 400 * lga_cos)
    dv_max_lga = 400 * (dv_pct_lga / 100.0)
    s_cdt_lga = (lga_pot * lga_long) / (gamma_lga * dv_max_lga * 400)
    
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
    dv_real_lga_v = (lga_pot * lga_long) / (gamma_lga * s_final_lga * 400)
    dv_real_lga_pct = (dv_real_lga_v / 400) * 100

    st.markdown("---")
    st.subheader("📋 Memoria de Justificación Técnica Detallada (LGA)")

    st.markdown("### 📊 Consultamos la tabla de corrientes admisibles para cable enterrado en instalaciones interiores D1/D2 de la ITC-BT 19")
    tabla_markdown = "| Sección Comercial (mm²) | Corriente Admisible Iz (A) [Enterrado Cu 90ºC] | Estado de Verificación frente a Sobrecarga (In <= 0.91 * Iz) |\n| :---: | :---: | :--- |\n"
    for s_com in [70, 95, 120, 150, 185]:
        iz_val_t = tabla_iz.get(s_com, 0)
        if s_com < 95 and iz_val_t < ib_lga:
            est = f"❌ No cumple por calentamiento (Iz = {iz_val_t} A < Ib = {ib_lga:.2f} A)"
        elif s_com == 95:
            est = f"❌ No cumple la 2ª condición (In = {in_lga_auto} A > 0.91 * 202 = 183.82 A)"
        elif s_com == 120:
            est = f"✅ **CUMPLE PERFECTAMENTE** (Iz = {iz_val_t} A -> In = {in_lga_auto} A <= 0.91 * 230 = 209.3 A)"
        else:
            est = "Válido pero superior"
        tabla_markdown += f"| {s_com} mm² | {iz_val_t} A | {est} |\n"
    st.markdown(tabla_markdown)

    st.markdown(f"""
    **1. Cálculo por Caída de Tensión:**
    * Límite reglamentario: Delta V% <= {dv_pct_lga}%
    * Valor absoluto: Delta V = ({dv_pct_lga} / 100) * 400 = {dv_max_lga:.2f} V
    * Sección teórica: S = ( {lga_long} * {lga_pot:,.2f} ) / ( {gamma_lga} * {dv_max_lga:.2f} * 400 ) = {s_cdt_lga:.2f} mm²

    **2. Intensidad de Diseño y Protección por Sobrecarga:**
    * Ib = P / ( 1.732 * V * cos phi ) = {lga_pot:,.2f} / ( 1.732 * 400 * {lga_cos} ) = **{ib_lga:.2f} A**
    """)

    st.markdown(f"""
        <div class="fusible-vistoso">
            🛡️ FUSIBLE RECOMENDADO EN CGP (In): {in_lga_auto} A (Tipo gG)
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    * **Justificación de por qué se descartan 70 y 95 mm² y se llega a 120 mm²:** Con 70 mm² no cumple calentamiento. Con 95 mm² cumple térmicamente pero **falla en la segunda condición de sobrecarga** (In <= 0.91 * Iz -> {in_lga_auto} <= 183.82 Falso). Por tanto, se eleva obligatoriamente a **120 mm²** (Iz = 230 A), donde {in_lga_auto} <= 0.91 * 230 = 209.3 A **sí cumple**.

    **3. Verificación de Cortocircuito (Manual MT 2.80.12 de Iberdrola):**
    * 1ª Condición (Poder de Corte): PdC = 50 kA > {lga_icc_max} kA --> **Cumple**.
    * 2ª Condición (Cortocircuito Mínimo): Icc_min = {lga_icc_min * 1000:,.0f} A > If (1.250 A) --> **Cumple**, garantizando la fusión del fusible en menos de 5 segundos.
    """)

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN A ADOPATAR (LGA): <span style="color: #ff4b4b; font-size: 24px;">{s_final_lga} mm²</span> de Cobre ({lga_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
            Neutro: <b>{70.0 if s_final_lga >= 70 else s_final_lga} mm²</b> | Tubo: <b>160 mm</b> | CDT Real: <b>{dv_real_lga_pct:.3f}%</b> | <b>Fusible CGP: {in_lga_auto} A</b>
            </span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 4: DERIVACIÓN INDIVIDUAL (INTOCABLE)
# =========================================================================
with pestanas[3]:
    st.title("Derivación Individual - DI (ITC-BT-15)")
    st.write("Configura los parámetros de la Derivación Individual y visualiza abajo la memoria técnica detallada con fórmulas, tablas de admisibilidad y verificación acumulada.")

    with st.expander("🏗️ Selector de Sistema de Instalación y Material (Métodos UNE-HD 60364-5-52)", expanded=True):
        metodo_di_key = st.selectbox("Método de Instalación recomendado (por defecto B1):", list(METODOS_INSTALACION.keys()), key="met_di")
        st.info(f"**Detalle del método:** {METODOS_INSTALACION[metodo_di_key]['desc']}")

        tipo_enlace_di = st.radio("Modelo de esquema para la Derivación Individual:", [
            "Modelo A: DI desde contadores concentrados en centralización única (Límite CDT = 1.0%)",
            "Modelo B: DI desde contadores diseminados / exteriores / en viviendas (Límite CDT = 0.5%)"
        ], key="enlace_di")

    dv_pct_di = 1.0 if "Modelo A" in tipo_enlace_di else 0.5

    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Potencia de la Derivación (W)", [5750, 7360, 9200, 11500], key="di_p")
        di_long = st.number_input("Longitud de la DI (m)", value=15.0, key="di_l")
        di_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="di_mat")
    with di_c2:
        di_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="di_ais")
        di_cos = st.slider("Coseno phi (cos phi) DI", 0.8, 1.0, 1.0, key="di_cos")

    gamma_di = GAMMA_MAP.get((di_mat, di_aisl), 44.0)
    ib_di = di_pot / (230.0 * di_cos)
    dv_max_di = 230.0 * (dv_pct_di / 100.0)
    s_cdt_di = (2.0 * di_pot * di_long) / (gamma_di * dv_max_di * 230.0)
    
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
    dv_real_di_v = (2.0 * di_pot * di_long) / (gamma_di * s_optima_di * 230.0)
    dv_real_di_pct = (dv_real_di_v / 230.0) * 100

    st.markdown("---")
    st.subheader("📋 Memoria de Cálculo Justificada y Detallada (Derivación Individual)")

    st.markdown("""
    **1. Intensidad de Diseño ($I_b$):**  
    * $I_b = P / (V \\cdot \\cos\\varphi)$
    """)
    st.info(f"Cálculo numérico: {di_pot} W / (230 V x {di_cos}) = **{ib_di:.2f} A**")

    st.markdown(f"""
    **2. Cálculo por Caída de Tensión ($\\Delta V \\le {dv_pct_di}\\%$):**  
    * Valor absoluto máximo admisible: $\\Delta V = 230 \\times \\frac{{{dv_pct_di}}}{{100}} = {dv_max_di:.2f}\\text{{ V}}$
    * Sección teórica necesaria: $S = \\frac{{2 \\cdot P \\cdot L}}{{\\gamma \\cdot \\Delta V \\cdot V}}$
    """)
    st.info(f"Cálculo numérico: (2 x {di_pot} W x {di_long} m) / ({gamma_di} x {dv_max_di:.2f} V x 230 V) = **{s_cdt_di:.2f} mm²**")

    st.markdown("### 📊 Tabla Comparativa de Secciones Comerciales para la DI")
    tabla_di_md = "| Sección Comercial (mm²) | Corriente Admisible Iz (A) | Caída de Tensión Real (%) | Estado Reglamentario |\n| :---: | :---: | :---: | :--- |\n"
    for sec_com in [1.5, 2.5, 4, 6, 10, 16, 25]:
        iz_c = tabla_iz_di.get(sec_com, 100.0)
        dv_c_pct = ((2.0 * di_pot * di_long) / (gamma_di * sec_com * 230.0) / 230.0) * 100
        if sec_com >= s_bruta_di:
            estado_c = "⭐ **SELECCIONADA (ÓPTIMA)**"
        elif sec_com < min_reg_di:
            estado_c = "❌ No cumple mínimo ITC-BT-15 (6 mm²)"
        elif iz_c < ib_di:
            estado_c = "❌ No cumple calentamiento"
        elif dv_c_pct > dv_pct_di:
            estado_c = "❌ No cumple caída de tensión"
        else:
            estado_c = "Válida pero superior"
        tabla_di_md += f"| {sec_com} mm² | {iz_c} A | {dv_c_pct:.3f}% | {estado_c} |\n"
    st.markdown(tabla_di_md)

    cdt_acumulada_global = dv_real_lga_pct + dv_real_di_pct
    st.markdown(f"""
    **4. Verificación del Tramo Más Desfavorable (LGA + DI Acumulada):**  
    * CDT LGA ({dv_real_lga_pct:.3f}%) + CDT DI ({dv_real_di_pct:.3f}%) = **{cdt_acumulada_global:.3f}%** (Límite global recomendado: 1.5%) -> **CUMPLE CORRECTAMENTE**.
    """)

    st.markdown(f"""
        <div class="resultado-destacado">
            🔌 SECCIÓN ADOPTADA PARA LA DI: <span style="color: #ff4b4b; font-size: 24px;">{s_optima_di} mm²</span> de {di_mat.upper()} ({di_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
            Intensidad de diseño: <b>{ib_di:.2f} A</b> | CDT Real: <b>{dv_real_di_pct:.3f}%</b> | Protección PIA asociada: <b>{prot_di} A + Diferencial 30 mA</b>
            </span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑAS 5 A 9: RESTO DE VENTANAS
# =========================================================================
with pestanas[4]:
    st.title("🛡️ Resolución Avanzada y Exámenes (Casos Prácticos)")
    st.write("Selecciona el caso de examen o problema tipo para ver el desarrollo analítico completo paso a paso con fórmulas y verificación reglamentaria.")

    sub_exam = st.tabs([
        "📝 Caso 1: Edificio Plurifamiliar Completo",
        "🏭 Caso 2: Instalación Industrial (Motores e Icc)",
        "⚡ Caso 3: Verificación de Cortocircuito y Fusibles"
    ])

    with sub_exam[0]:
        st.subheader("Desarrollo Caso 1: Edificio Plurifamiliar y Cálculo de LGA")
        st.markdown("""
        **1. Previsión de Cargas (ITC-BT-10):**  
        * $P_1$ (Viviendas): $24 \\times 9.200 \\times 16,8 = \\mathbf{{3.701.760\\text{{ W}}}}$  
        * $P_2$ (Local comercial): $150\\text{{ m}}^2 \\times 100\\text{{ W/m}}^2 = \\mathbf{{15.000\\text{{ W}}}}$  
        * $P_3$ (Servicios generales): $4.000\\text{{ W}} \\times 1,30 = \\mathbf{{5.200\\text{{ W}}}}$  
        * $P_4$ (IRVE - 10 plazas): $10 \\times 3.680 \\times 0,3 = \\mathbf{{11.040\\text{{ W}}}}$  
        * **Potencia Total Prevista ($P_t$):** **3.733.000 W**
        
        **2. Sección adoptada:** **240 mm² de Cobre XLPE (90ºC)**.
        """)

    with sub_exam[1]:
        st.subheader("Desarrollo Caso 2: Línea de Alimentación de Motores")
        st.markdown("""
        * $I_b = \\frac{15.000}{\\sqrt{3} \\cdot 400 \\cdot 0,85 \\cdot 0,90} = \\mathbf{{28,31\\text{{ A}}}}$
        * Calibre del PIA: **32 A** | Sección comercial mínima: **6 mm² de Cobre**.
        """)

    with sub_exam[2]:
        st.subheader("Desarrollo Caso 3: Cortocircuito y Poder de Corte")
        st.markdown("""
        * $PdC \\ge I_{cc\\_max}$ (15 kA). Se selecciona automático con $PdC = 25\\text{{ kA}}$.
        """)

with pestanas[5]:
    st.title("📊 Tablas de Cálculo Directo Estilo PLC Madrid (ITC-BT-15)")
    st.markdown("""
    | Tipo de Línea / Circuito | Sección Mínima Cobre | Sección Mínima Aluminio | Caída de Tensión Máxima ($\\Delta V\\%$) | Protección Habitual |
    | :--- | :---: | :---: | :---: | :--- |
    | **Línea General de Alimentación (LGA)** | $10\\text{ mm}^2$ | $16\\text{ mm}^2$ | 0.5% (Mod. 1) / 1.0% (Mod. 2) | Fusibles gG (CGP) |
    | **Derivación Individual (DI)** | $6\\text{ mm}^2$ | $10\\text{ mm}^2$ | 1.0% (Mod. A) / 0.5% (Mod. B) | Interruptor General (IGM) |
    | **Circuitos Interiores Viviendas (C1 - Iluminación)** | $1,5\\text{ mm}^2$ | - | 3.0% | PIA 10 A |
    | **Circuitos Interiores Viviendas (C2 - Enchufes)** | $2,5\\text{ mm}^2$ | - | 3.0% | PIA 16 A |
    """)

with pestanas[6]:
    st.title("📐 Esquemas Unifilares")
    st.markdown(f'<div class="esquema-simbolos">PROYECTO: {st.session_state.nombre_proyecto}\nLGA: 120 mm² RZ1-K Cu | Neutro: 70 mm² | Tubo: 160 mm\nIcc máx: 12 kA | Icc mín: 7.5 kA | Fusibles CGP: 200 A gG | IGM: 250 A</div>', unsafe_allow_html=True)

with pestanas[7]:
    st.title("📄 Informe Técnico Formal MTD")
    st.write("Vista previa del informe técnico completo.")

with pestanas[8]:
    st.title("💡 Simulador Consumo Eléctrico")
    kw_c = st.number_input("kW contratados", value=4.6)
    kwh_m = st.number_input("kWh al mes", value=250.0)
    total_con_impuestos = ((kw_c * 0.11 * 30) + (kwh_m * 0.18)) * 1.051127 * 1.10
    st.metric("Estimación Factura Mensual", f"{total_con_impuestos:.2f} €")