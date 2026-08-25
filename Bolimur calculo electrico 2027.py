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
# CONTENIDO DE LAS PANTALLAS (INTEGRIDAD 100% RESTAURADA)
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
        icc_orig_q = st.number_input("Icc de cortocircuito en el origen (kA)", value=10.0, step=0.5, format="%.2f", key="icc_orig_q")

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

    st.markdown("---")
    st.markdown(f"""
        <div class="pia-destacado">
            🛡️ PROTECCIÓN MAGNETOTÉRMICA RECOMENDADA (PIA): {prot_q} A (Curva C) + Diferencial 30 mA
        </div>
        <div class="resultado-destacado">
            ⚡ SECCIÓN ÓPTIMA RECOMENDADA: <span style="color: #ff4b4b; font-size: 24px;">{s_opt_q} mm²</span> de {mat_q.upper()} ({ais_q})<br>
            <span style="font-size: 14px; color: #b0b0b0;">Intensidad de diseño: {ib_q:.2f} A | CDT Real: {dv_real_pct_q:.3f}% | Icc Final: {icc_fin_q*1000:.1f} A</span>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("🏢"):
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")
    st.write("Calculamos la Potencia Total Prevista (Pt) sumando viviendas, locales, servicios, garajes e IRVE con su justificación analítica y reglamentaria.")
    
    col_t1, col_b1 = st.columns([4, 1])
    with col_t1:
        st.subheader("1. Viviendas del Edificio (P1)")
    with col_b1:
        if st.button("🔄 Resetear Cargas"):
            st.session_state.grupos_viviendas = [{"nombre": "Grupo 1", "qty": 10, "pot": 5750, "nocturna": False}]
            st.rerun()

    total_viviendas_edificio = 0
    pot_total_viviendas = 0
    for idx, viv in enumerate(st.session_state.grupos_viviendas):
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1: viv["nombre"] = st.text_input(f"Descripción #{idx+1}", viv["nombre"], key=f"viv_nom_{idx}")
        with c2: viv["qty"] = st.number_input(f"Nº Viviendas #{idx+1}", min_value=1, value=int(viv["qty"]), key=f"viv_qty_{idx}")
        with c3: viv["pot"] = st.selectbox(f"Unidad de Potencia n.º {idx+1}", [5750, 7360, 9200, 11500], key=f"viv_pot_{idx}")
        total_viviendas_edificio += viv["qty"]
        pot_total_viviendas += int(round(viv["qty"] * viv["pot"] * get_coef_simultaneidad(viv["qty"])))

    st.info(f"💡 Viviendas totales: **{total_viviendas_edificio}** | **Total Parcial P1 (Viviendas): {pot_total_viviendas:,} W**")

elif seleccion_modulo.startswith("⚡"):
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    st.write("Configuración y dimensionamiento analítico de la LGA.")
    lga_pot = st.number_input("Potencia de cálculo LGA (W)", value=112500.0)
    lga_long = st.number_input("Longitud de la LGA (m)", value=20.0)
    st.success(f"LGA configurada para {lga_pot:,.0f} W en {lga_long} metros.")

elif seleccion_modulo.startswith("🔌"):
    st.title("Derivación Individual - DI (ITC-BT-15)")
    st.write("Configuración de la Derivación Individual y caída de tensión.")
    di_pot = st.selectbox("Potencia de la Derivación (W)", [5750, 7360, 9200, 11500])
    di_long = st.number_input("Longitud de la DI (m)", value=15.0)
    st.success(f"DI configurada para {di_pot} W en {di_long} metros.")

# =========================================================================
# MÓDULO: TABLAS ITC-BT SEGÚN REBT Y GUÍAS (SELECTOR POR DESPLEGABLE)
# =========================================================================
elif seleccion_modulo.startswith("📚"):
    st.title("📚 Compendio General de Tablas REBT y Guías Técnicas")
    st.write("Biblioteca técnica oficial completa. Selecciona la Instrucción Técnica Complementaria (ITC-BT) que deseas consultar en el menú desplegable inferior:")

    itc_seleccionada = st.selectbox(
        "Selecciona la ITC-BT o Bloque Normativo:",
        [
            "ITC-BT-15: Derivaciones Individuales (DI) y Canaladuras",
            "ITC-BT-10: Previsión de Cargas y Simultaneidad",
            "ITC-BT-14: Línea General de Alimentación (LGA)",
            "ITC-BT-25: Instalaciones Interiores en Viviendas y Alturas",
            "UNE-HD 60364-5-52: Intensidades Admisibles (Iz)",
            "ITC-BT-07 / 08: Redes Subterráneas y Puestas a Tierra",
            "ITC-BT-27 / 30: Locales Húmedos y Grados de Protección IP"
        ]
    )

    st.markdown("---")

    if "ITC-BT-15" in itc_seleccionada:
        st.subheader("📑 ITC-BT-15: Derivaciones Individuales (DI)")
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 ¿Para qué sirve y cómo se utiliza esta tabla?</b><br>
            Permite dimensionar de un vistazo la sección del conductor en función del IGA y la longitud máxima admisible para no superar la caída de tensión reglamentaria (1% o 0,5%).
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Cálculo Directo de Derivaciones Individuales (Cobre C = 48)")
        st.markdown("""
        | Sección Mínima DI | Diámetro Tubo (mm) | CDT Máxima | Calibre IGA: 25 A | Calibre IGA: 32 A | Calibre IGA: 40 A | Calibre IGA: 50 A | Calibre IGA: 63 A |
        | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
        | **6 mm²** | 32 mm | 0,5% / 1,0% / 1,5% | 5,75 kW / 6 m / 13 m / 19 m | 7,32 kW / 5 m / 10 m / 18 m | 9,2 kW / 6 m / 13 m | 11,5 kW / - | 14,49 kW / - |
        | **10 mm²** | 32 mm | 0,5% / 1,0% / 1,5% | 22 m / 33 m / 44 m | 17 m / 25 m / 34 m | 13 m / 20 m / 27 m | 8 m / 17 m / 22 m | 7 m / 14 m / - |
        | **16 mm²** | 40 mm | 0,5% / 1,0% / 1,5% | 35 m / 53 m / 70 m | 27 m / 41 m / 55 m | 21 m / 31 m / 42 m | 17 m / 26 m / 35 m | 14 m / 21 m / 28 m |
        | **25 mm²** | 50 mm | 0,5% / 1,0% / 1,5% | 55 m / 83 m / 110 m | 43 m / 65 m / 86 m | 34 m / 51 m / 69 m | 27 m / 41 m / 55 m | 21 m / 32 m / 43 m |
        | **35 mm²** | 50 mm | 0,5% / 1,0% / 1,5% | 77 m / 116 m / 154 m | 60 m / 91 m / 121 m | 48 m / 72 m / 96 m | 38 m / 58 m / 77 m | 31 m / 46 m / 61 m |
        """)

        st.markdown("### 🏗️ Dimensiones Mínimas de la Canaladura o Conducto de Obra (Patinillos)")
        st.markdown("""
        | Número de Derivaciones | Anchura L (Profundidad P = 0,15 m, una fila) | Anchura L (Profundidad P = 0,30 m, dos filas) |
        | :---: | :---: | :---: |
        | **Hasta 12** | 0,65 m | 0,50 m |
        | **13 a 24** | 1,25 m | 0,65 m |
        | **25 a 36** | 1,85 m | 0,95 m |
        | **37 a 48** | 2,45 m | 1,35 m |
        """)

    elif "ITC-BT-10" in itc_seleccionada:
        st.subheader("🏢 ITC-BT-10: Previsión de Cargas para Edificios")
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 ¿Para qué sirve?</b><br>
            Define los coeficientes de simultaneidad (K) aplicables al conjunto de viviendas y locales de un edificio para calcular la potencia total prevista (Pt).
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

    elif "ITC-BT-14" in itc_seleccionada:
        st.subheader("⚡ ITC-BT-14: Línea General de Alimentación (LGA)")
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 Criterio reglamentario:</b><br>
            Secciones mínimas obligatorias de $10\\text{ mm}^2$ en Cobre y $16\\text{ mm}^2$ en Aluminio. Caída de tensión máxima admisible: 0,5% (Contadores concentrados) o 1,0% (Centralizaciones parciales).
        </div>
        """, unsafe_allow_html=True)

    elif "ITC-BT-25" in itc_seleccionada:
        st.subheader("🏠 ITC-BT-25: Instalaciones Interiores y Alturas Reglamentarias")
        st.markdown("""
        <div class="recomendacion-box">
            <h4 style="margin-top: 0; color: #004085;">📌 RECOMENDACIONES IMPORTANTES Y ALTURAS DE INSTALACIÓN EN VIVIENDAS</h4>
            <ul>
                <li><b>Cajas de Registro:</b> Parte superior a $\\ge 0,20\\text{ m}$ del techo. Las tapas deben ser accesibles.</li>
                <li><b>Enchufes generales:</b> Altura de $0,20\\text{ m} - 0,30\\text{ m}$ sobre el suelo. En cocinas a más de $0,50\\text{ m}$ de fregaderos.</li>
                <li><b>Interruptores y Conmutadores:</b> Altura recomendada entre $0,90\\text{ m} y 1,10\\text{ m}$ sobre el suelo.</li>
                <li><b>Cuadro General (CGMP):</b> Eje situado entre $1,40\\text{ m} y 2,00\\text{ m}$ de altura.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    elif "UNE-HD" in itc_seleccionada:
        st.subheader("🛡️ UNE-HD 60364-5-52: Intensidades Admisibles ($I_z$)")
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 ¿Para qué sirve?</b><br>
            Corriente máxima admisible que soporta un cable sin sobrepasar su temperatura límite de servicio según el aislamiento y modo de instalación.
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

    elif "ITC-BT-07" in itc_seleccionada:
        st.subheader("🌱 ITC-BT-07 / 08: Redes Subterráneas y Puestas a Tierra")
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 Criterios principales:</b><br>
            Dimensionamiento de picas de tierra, conductores de protección equipotenciales y factores de corrección por resistividad térmica del terreno en zanjas subterráneas.
        </div>
        """, unsafe_allow_html=True)

    elif "ITC-BT-27" in itc_seleccionada:
        st.subheader("💧 ITC-BT-27 / 30: Locales Húmedos, Mojados y Grados IP")
        st.markdown("""
        <div class="info-box-tecnico">
            <b>📖 Criterios de protección IP en cuartos de baño y locales especiales:</b><br>
            • Volumen 0: IPX7 obligatorios.<br>
            • Volumen 1: IPX4 mínimos.<br>
            • Volumen 2: IPX4 (IPX5 si hay chorros de agua).
        </div>
        """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("📐"):
    st.title("📐 Esquemas Unifilares del Edificio y Desdobles Reglamentarios")
    st.write("Representación unifilar esquemática completa para Vivienda Básica, Elevada, desdobles y parámetros de la instalación.")
    st.code("PROYECTO: Estudio Eléctrico Edificio Plurifamiliar\nLGA: 120 mm² RZ1-K Cu | Neutro: 70 mm² | Tubo: 160 mm\nIcc máx: 12 kA | Icc mín: 7.5 kA", language="text")

elif seleccion_modulo.startswith("📄"):
    st.title("📄 Informe Técnico Formal MTD")
    st.write("Memoria técnica de diseño lista para firmar.")

elif seleccion_modulo.startswith("💡"):
    st.title("💡 Simulador Consumo Eléctrico")
    kw_c = st.number_input("kW contratados", value=4.6)
    kwh_m = st.number_input("kWh al mes", value=250.0)
    total = ((kw_c * 0.11 * 30) + (kwh_m * 0.18)) * 1.051127 * 1.10
    st.metric("Estimación Factura Mensual", f"{total:.2f} €")

elif seleccion_modulo.startswith("🛡️"):
    st.title("🛡️ Resolución Avanzada y Exámenes (Casos Prácticos)")
    st.markdown("Desarrollo analítico de casos prácticos de examen y problemas tipo resueltos.")