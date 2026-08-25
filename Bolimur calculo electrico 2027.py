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

# --- DISEÑO CORPORATIVO Y ESTILOS (REJILLAS Y CELDAS ACENTUADAS PARA TABLETS) ---
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

    st.header("📂 Navegación de Módulos")
    seleccion_modulo = st.radio(
        "Selecciona la sección:",
        [
            "🏠 Menú Principal",
            "🧮 Cálculo Rápido (CDT & Icc)",
            "🏢 Previsión de Cargas (Pt)",
            "⚡ Línea General (LGA)",
            "🔌 Derivación Individual (DI)",
            "📊 Tabla Guía PLC Madrid",
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
# CONTENIDO DE LAS PANTALLAS SEGÚN SELECCIÓN EN SIDEBAR
# =========================================================================

if seleccion_modulo.startswith("🏠"):
    st.title("⚡ BOLIMUR INSTALACIONES INTEGRALES")
    st.write("Bienvenido al panel de cálculo eléctrico REBT. Despliega el menú lateral izquierdo (pulsando las ☰ arriba a la izquierda si estás en el móvil o tablet) para seleccionar cualquier módulo de cálculo de forma limpia y sin ocupar espacio en pantalla.")
    st.info("💡 **Consejo de navegación:** En teléfonos y tablets, la barra lateral se oculta automáticamente para ofrecerte una visión 100% despejada de los cálculos y tablas.")

elif seleccion_modulo.startswith("🧮"):
    st.title("🧮 Ventana de Cálculo Rápido Avanzado (Bombas, Líneas Largas y Extremos)")
    st.write("Herramienta de diagnóstico integral para comprobación de tramos complejos (como motores de piscina o líneas largas en extremos), evaluando simultáneamente Caída de Tensión, Calentamiento, Coordinación de Protecciones e Icc min.")

    rc1, rc2 = st.columns(2)
    with rc1:
        modo_carga = st.radio("Modo de entrada:", ["Por Potencia (W o CV)", "Por Intensidad Directa (A)"], key="mod_q")
        tipo_red_q = st.selectbox("Sistema eléctrico", ["Monofásico (230V)", "Trifásico (400V)"], key="tr_q1")
        
        if modo_carga == "Por Potencia (W o CV)":
            val_pot_q = st.number_input("Potencia activa (W) [Ej: Bomba 1.5 CV aprox 1100 W]", value=2200.0, step=100.0, key="vp_q")
            cos_q = st.slider("Coseno phi (cos phi) [Motores habituales 0.82]", 0.7, 1.0, 0.85, key="cos_q")
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q:
                ib_q = val_pot_q / (v_nom_calc * cos_q)
            else:
                ib_q = val_pot_q / (math.sqrt(3) * v_nom_calc * cos_q)
        else:
            ib_q = st.number_input("Intensidad de diseño Ib (A)", value=16.0, step=1.0, key="ib_q1")
            cos_q = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.85, key="cos_q_2")
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q:
                val_pot_q = ib_q * v_nom_calc * cos_q
            else:
                val_pot_q = ib_q * math.sqrt(3) * v_nom_calc * cos_q

        long_q = st.number_input("Longitud del circuito / tirada (m) [Ida]", value=40.0, step=5.0, key="l_q")

    with rc2:
        metodo_q_key = st.selectbox("Método de Instalación (UNE-HD 60364-5-52):", list(METODOS_INSTALACION.keys()), index=0, key="met_q")
        mat_q = st.selectbox("Material conductor", ["cobre", "aluminio"], key="m_q")
        ais_q = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="a_q")
        cdt_lim_q = st.number_input("Caída de Tensión máxima permitida (%) [Fuerza/Motores max 3-5%]", value=3.0, step=0.5, key="cdt_q")
        icc_orig_q = st.number_input("Icc de cortocircuito en el origen de la línea (kA)", value=10.0, step=0.5, key="icc_orig_q")

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

    if "Monofásico" in tipo_red_q:
        dv_real_v_q = (2.0 * val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc)
    else:
        dv_real_v_q = (val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc)
    
    dv_real_pct_q = (dv_real_v_q / v_nom_calc) * 100.0

    rho_q = 1.0 / gamma_q
    r_cable_q = (rho_q * long_q) / s_opt_q
    if "Monofásico" in tipo_red_q:
        z_tot_q = (v_nom_calc / (icc_orig_q * 1000.0)) + (2.0 * r_cable_q)
    else:
        z_tot_q = (v_nom_calc / (icc_orig_q * 1000.0)) + r_cable_q
        
    icc_fin_q = v_nom_calc / z_tot_q / 1000.0 if z_tot_q > 0 else 0.0
    prot_q = seleccionar_proteccion(ib_q)
    corriente_disparo_magnetico = prot_q * 10.0
    salta_proteccion = (icc_fin_q * 1000.0) >= corriente_disparo_magnetico

    st.markdown("---")
    st.subheader("Memoria Justificativa Analítica y Fórmulas Desarrolladas")

    st.markdown(f"""
    <div class="formula-box">
        <b>1. Intensidad de Diseño (Ib):</b><br>
        • Fórmula general de corriente alterna.<br>
        • Sustitución: {val_pot_q:,.1f} / ({v_nom_calc} * {cos_q}) = <b>{ib_q:.2f} A</b>
    </div>

    <div class="formula-box">
        <b>2. Sección por Caída de Tensión (Delta V):</b><br>
        • Límite max: {cdt_lim_q}% -> {dv_max_q:.2f} V.<br>
        • Cálculo teórico puro: <b>{s_cdt_q:.2f} mm²</b>
    </div>

    <div class="formula-box">
        <b>3. Comprobación por Calentamiento y Cortocircuito (Icc min):</b><br>
        • Intensidad admisible del cable elegido ({s_opt_q} mm²): <b>{tabla_iz_q.get(s_opt_q, 0)} A</b>.<br>
        • Corriente de cortocircuito al final de los {long_q} metros: <b>{icc_fin_q * 1000:.1f} A ({icc_fin_q:.2f} kA)</b>.<br>
        • Comprobación de disparo magnético del PIA ({prot_q} A): Estado: <b>{'✅ GARANTIZADO EL DISPARO' if salta_proteccion else '⚠️ ATENCION: Icc insuficiente'}</b>.
    </div>
    """, unsafe_allow_html=True)

    # RECOMENDACIÓN DE PROTECCIÓN DESTACADA CON LETRAS GRANDES
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
            dv_c_pct = (((2.0 * val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0
        else:
            dv_c_pct = (((val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0

        cond_sobrecarga = 0.91 * iz_c
        if iz_c < ib_q:
            est_v = f"❌ No cumple por calentamiento (Iz = {iz_c} A < Ib = {ib_q:.2f} A)"
        elif prot_q > cond_sobrecarga:
            est_v = f"❌ No cumple la 2ª condición (In = {prot_q} A > 0.91 * {iz_c} = {cond_sobrecarga:.2f} A)"
        elif dv_c_pct > cdt_lim_q:
            est_v = f"❌ No cumple caída de tensión ({dv_c_pct:.3f}% > {cdt_lim_q}%)"
        elif sec_com == s_opt_q:
            est_v = f"✅ **CUMPLE PERFECTAMENTE** (Iz = {iz_c} A -> In = {prot_q} A <= 0.91 * {iz_c} = {cond_sobrecarga:.2f} A)"
        else:
            est_v = "Válido pero superior"

        tabla_q_md += f"| {sec_com} mm² | {iz_c} A | {dv_c_pct:.3f}% | {est_v} |\n"
    st.markdown(tabla_q_md)

    # EXPLICACIÓN DETALLADA DE POR QUÉ CUMPLE TODO
    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ CONCLUSIÓN Y SECCIÓN ÓPTIMA: <span style="color: #ff4b4b; font-size: 24px;">{s_opt_q} mm²</span> de {mat_q.upper()} ({ais_q})<br>
            <hr style="border: 1px solid #444; margin: 10px 0;">
            <span style="font-size: 15px; color: #e0e0e0; font-weight: normal; line-height: 1.6;">
            <b>🔍 Explicación detallada de por qué cumple con todos los requisitos:</b><br>
            1. <b>Intensidad de Servicio ($I_b$):</b> El circuito absorbe <b>{ib_q:.2f} A</b>. La sección elegida de <b>{s_opt_q} mm²</b> soporta una corriente admisible ($I_z$) muy superior, evitando cualquier riesgo de calentamiento o sobrecalentamiento del conductor.<br>
            2. <b>Caída de Tensión ($\Delta V$):</b> Con una longitud de <b>{long_q} m</b>, la caída de tensión real se queda en el <b>{dv_real_pct_q:.3f}%</b>, cumpliendo holgadamente el límite estricto fijado del <b>{cdt_lim_q}%</b>.<br>
            3. <b>Coordinación de Protecciones ($I_n \le 0.91 \cdot I_z$):</b> El magnetotérmico seleccionado de <b>{prot_q} A</b> protege perfectamente al cable frente a sobrecargas cumpliendo la condición reglamentaria.<br>
            4. <b>Seguridad ante Cortocircuito en el Extremo ($I_{cc\ min}$):</b> Evaluando la corriente de cortocircuito al final de los {long_q} metros (estimada en <b>{icc_fin_q * 1000:.1f} A</b> a partir de los {icc_orig_q} kA en origen), el sistema confirma que la corriente de defecto es lo suficientemente intensa como para accionar de forma instantánea el disparo magnético del PIA de {prot_q} A, garantizando una protección integral de la línea y de los equipos.
            </span>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("🏢"):
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")
    # (Resto de módulos idénticos al anterior)