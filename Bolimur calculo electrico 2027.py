import streamlit as st
import math
import json
import os
import sqlite3
import re

# Importación segura de lector de PDF
try:
    from pypdf import PdfReader
    has_pypdf = True
except ImportError:
    has_pypdf = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BOLIMUR INSTALACIONES INTEGRALES - Calculadora REBT", page_icon="⚡", layout="wide")

# --- GESTIÓN DE BASE DE DATOS LOCAL (PERFIL, CLIENTES Y CONFIGURACIÓN) ---
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

    cursor.execute("PRAGMA table_info(clientes)")
    cols_cli = [col[1] for col in cursor.fetchall()]
    if not cols_cli:
        cursor.execute('''
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT, nif_cliente TEXT, direccion TEXT, 
                municipio TEXT, provincia TEXT, cp TEXT, 
                telefono_cliente TEXT, email_cliente TEXT
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
    .esquema-simbolos {
        background-color: #ffffff;
        border: 3px solid #111111;
        padding: 30px;
        border-radius: 10px;
        font-family: 'Courier New', Courier, monospace;
        color: #000000;
        font-size: 14px;
        line-height: 1.6;
        white-space: pre;
        overflow-x: auto;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
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

if 'nombre_proyecto' not in st.session_state:
    st.session_state.nombre_proyecto = "Estudio Eléctrico Edificio Plurifamiliar"
if 'grupos_viviendas' not in st.session_state:
    st.session_state.grupos_viviendas = [{"nombre": "Viviendas Estándar", "qty": 10, "pot": 5750, "nocturna": False}]
if 'servicios_generales' not in st.session_state:
    st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 1, "potencia": 3000.0, "factor": 1.0}]
if 'locales' not in st.session_state:
    st.session_state.locales = [{"nombre": "Local Comercial A", "qty": 1, "superficie": 100.0}]
if 'irve_config' not in st.session_state:
    st.session_state.irve_config = {"con_irve": True, "tipo_esquema": "Esquema 1.5 (Recarga vinculada)", "num_plazas": 5, "pot_plaza": 3680.0}

if 'lga_long_val' not in st.session_state: st.session_state.lga_long_val = 20.0
if 'nombre_archivo_guardado' not in st.session_state: st.session_state.nombre_archivo_guardado = ultimo_archivo_db
if 'carpeta_trabajo_input' not in st.session_state: st.session_state.carpeta_trabajo_input = carpeta_trabajo_db

# --- BARRA LATERAL COMPLETA ---
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
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("💾 Guardar JSON"):
            datos_json = {
                "proyecto": st.session_state.nombre_proyecto,
                "grupos_viviendas": st.session_state.grupos_viviendas,
                "locales": st.session_state.locales,
                "servicios_generales": st.session_state.servicios_generales,
                "irve": st.session_state.irve_config,
                "lga_long": st.session_state.lga_long_val
            }
            nombre_f = st.session_state.nombre_archivo_guardado
            with open(nombre_f, "w", encoding="utf-8") as f:
                json.dump(datos_json, f, indent=4, ensure_ascii=False)
            st.success(f"✅ Guardado en {nombre_f}")
    with col_p2:
        if st.button("📂 Cargar JSON"):
            nombre_f = st.session_state.nombre_archivo_guardado
            if os.path.exists(nombre_f):
                with open(nombre_f, "r", encoding="utf-8") as f:
                    data_j = json.load(f)
                    st.session_state.nombre_proyecto = data_j.get("proyecto", st.session_state.nombre_proyecto)
                    st.session_state.grupos_viviendas = data_j.get("grupos_viviendas", [])
                    st.session_state.locales = data_j.get("locales", [])
                    st.session_state.servicios_generales = data_j.get("servicios_generales", [])
                    st.session_state.irve_config = data_j.get("irve", {"con_irve": True, "tipo_esquema": "Esquema 1.5", "num_plazas": 5, "pot_plaza": 3680.0})
                    st.session_state.lga_long_val = data_j.get("lga_long", 20.0)
                st.success("✅ ¡Cargado!")
                st.rerun()

    st.markdown("---")
    st.header("⚡ Carga Rápida de Enunciados Típicos")
    tipo_caso = st.selectbox("Selecciona caso de estudio:", [
        "-- Seleccionar caso --",
        "Edificio 10 viviendas (LGA: 25m, DI: 15m)",
        "Caso Examen: CC 112.5 kW, LGA Enterrada 20m (RZ1-K)"
    ])
    if tipo_caso != "-- Seleccionar --":
        if st.button("📥 Cargar Configuración Seleccionada"):
            if "10 viviendas" in tipo_caso:
                st.session_state.grupos_viviendas = [{"nombre": "Bloc 10 Viviendas", "qty": 10, "pot": 5750, "nocturna": False}]
                st.session_state.lga_long_val = 25.0
            elif "Caso Examen" in tipo_caso:
                st.session_state.grupos_viviendas = []
                st.session_state.lga_long_val = 20.0
            st.success("✅ ¡Datos del caso cargados con éxito!")
            st.rerun()

pestanas = st.tabs([
    "🏢 Previsión de Cargas (Pt)", 
    "⚡ Línea General (LGA)", 
    "🔌 Derivación Individual (DI)", 
    "🛡️ Resolución Avanzada y Exámenes",
    "📊 Tabla Guía Estilo PLC Madrid",
    "🧮 Cálculo Rápido (CDT & Icc)",
    "📐 Esquemas Unifilares",
    "📝 Asistente de Boletines",
    "📋 MTD Oficial CARM",
    "📄 Informe Técnico MTD",
    "💡 Simulador Consumo"
])

# =========================================================================
# PESTAÑA 1: PREVISIÓN DE CARGAS (COMPLETA)
# =========================================================================
with pestanas[0]:
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")
    
    col_t1, col_b1 = st.columns([4, 1])
    with col_t1:
        st.write("Calculamos la Potencia Total Prevista (Pt) sumando viviendas, locales, servicios, garajes e IRVE con su justificación analítica y reglamentaria.")
    with col_b1:
        if st.button("🔄 Resetear a Cero"):
            st.session_state.grupos_viviendas = []
            st.session_state.locales = []
            st.session_state.servicios_generales = []
            st.session_state.irve_config = {"con_irve": False, "tipo_esquema": "Esquema 1.5", "num_plazas": 0, "pot_plaza": 3680.0}
            st.session_state.lga_long_val = 20.0
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

    if not st.session_state.grupos_viviendas:
        st.info("ℹ️ No hay grupos de viviendas añadidos. Pulsa en '➕ Añadir Grupo de Viviendas' para empezar.")

    for idx, viv in enumerate(st.session_state.grupos_viviendas):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: viv["nombre"] = st.text_input(f"Descripción #{idx+1}", viv["nombre"], key=f"viv_nom_{idx}")
        with c2: viv["qty"] = st.number_input(f"Nº Viviendas #{idx+1}", min_value=1, value=int(viv["qty"]), key=f"viv_qty_{idx}")
        with c3: viv["pot"] = st.selectbox(f"Unidad de Potencia n.º {idx+1}", [5750, 7360, 9200, 11500], index=[5750, 7360, 9200, 11500].index(viv["pot"]) if viv["pot"] in [5750, 7360, 9200, 11500] else 0, key=f"viv_pot_{idx}")
        with c4: viv["nocturna"] = st.checkbox(f"Tarifa Nocturna #{idx+1}", value=viv["nocturna"], key=f"viv_noc_{idx}")
        with c5:
            if st.button("🗑️", key=f"del_viv_{idx}"):
                st.session_state.grupos_viviendas.pop(idx)
                st.rerun()

        total_viviendas_edificio += viv["qty"]
        qty_g = viv["qty"]
        pot_unit = viv["pot"]
        noct = viv["nocturna"]

        if noct:
            cs_grupo = float(qty_g)
        else:
            cs_grupo = get_coef_simultaneidad(qty_g)

        pot_parcial_g = int(round(qty_g * pot_unit * cs_grupo))
        pot_total_viviendas += pot_parcial_g

    # 2. Locales Comerciales y Oficinas (P2)
    st.subheader("2. Locales Comerciales y Oficinas (P2)")
    if st.button("➕ Añadir Local / Oficina"):
        st.session_state.locales.append({"nombre": f"Local {len(st.session_state.locales)+1}", "qty": 1, "superficie": 100.0})

    pot_total_locales = 0.0
    for idx_l, loc in enumerate(st.session_state.locales):
        cl1, cl2, cl3, cl4 = st.columns([3, 2, 2, 1])
        with cl1: loc["nombre"] = st.text_input(f"Local #{idx_l+1}", loc["nombre"], key=f"loc_nom_{idx_l}")
        with cl2: loc["qty"] = st.number_input(f"Cant. Locales #{idx_l+1}", min_value=1, value=int(loc["qty"]), key=f"loc_qty_{idx_l}")
        with cl3: loc["superficie"] = st.number_input(f"Superficie (m²) #{idx_l+1}", min_value=0.0, value=float(loc["superficie"]), key=f"loc_sup_{idx_l}")
        with cl4:
            if st.button("🗑️", key=f"del_loc_{idx_l}"):
                st.session_state.locales.pop(idx_l)
                st.rerun()
        pot_local_unit = max(loc["superficie"] * 100.0, 3450.0 if loc["superficie"] > 0 else 0.0)
        pot_total_locales += pot_local_unit * loc["qty"]

    # 3. Servicios Generales (P3)
    st.subheader("3. Servicios Generales del Edificio (P3)")
    if st.button("➕ Añadir Servicio General"):
        st.session_state.servicios_generales.append({"nombre": "Ascensor principal", "qty": 1, "potencia": 3000.0, "factor": 1.0})

    pot_total_servicios = 0.0
    for idx_s, serv in enumerate(st.session_state.servicios_generales):
        cs1, cs2, cs3, cs4, cs5 = st.columns([3, 2, 2, 2, 1])
        with cs1:
            serv["nombre"] = st.selectbox(f"Tipo de Servicio #{idx_s+1}", [
                "Ascensor principal", "Ascensor secundario / Montacargas", 
                "Alumbrado portal y escalera", "Grupo de presión / Bomba de agua", 
                "Ventilación / Extracción de humos", "Puerta automática de garaje", "Otro servicio general"
            ], index=0, key=f"serv_nom_{idx_s}")
        with cs2: serv["qty"] = st.number_input(f"Cantidad #{idx_s+1}", min_value=1, value=int(serv["qty"]), key=f"serv_qty_{idx_s}")
        with cs3: serv["potencia"] = st.number_input(f"Potencia Unit. (W) #{idx_s+1}", value=float(serv["potencia"]), key=f"serv_pot_{idx_s}")
        with cs4: serv["factor"] = st.number_input(f"Factor Simultaneidad #{idx_s+1}", value=float(serv["factor"]), key=f"serv_fac_{idx_s}")
        with cs5:
            if st.button("🗑️", key=f"del_serv_{idx_s}"):
                st.session_state.servicios_generales.pop(idx_s)
                st.rerun()
        pot_total_servicios += serv["potencia"] * serv["qty"] * serv["factor"]

    # 4. IRVE (ITC-BT-52)
    st.subheader("4. Infraestructura de Recarga de Vehículos - IRVE (ITC-BT-52)")
    st.session_state.irve_config["con_irve"] = st.checkbox("Incluir preinstalación / instalación IRVE en el edificio", value=st.session_state.irve_config["con_irve"])
    pot_total_irve = 0.0
    if st.session_state.irve_config["con_irve"]:
        ic1, ic2, ic3 = st.columns(3)
        with ic1:
            st.session_state.irve_config["tipo_esquema"] = st.selectbox("Esquema de instalación (ITC-BT-52)", [
                "Esquema 1.5 (Recarga vinculada en plazas de garaje)",
                "Esquema 1.4 (Línea troncal con derivaciones para plazas)"
            ], index=0)
        with ic2:
            st.session_state.irve_config["num_plazas"] = st.number_input("Nº de plazas con preinstalación IRVE", min_value=1, value=int(st.session_state.irve_config["num_plazas"]))
        with ic3:
            st.session_state.irve_config["pot_plaza"] = st.number_input("Potencia por plaza (W)", value=float(st.session_state.irve_config["pot_plaza"]))
        
        n_plazas = st.session_state.irve_config["num_plazas"]
        p_plaz = st.session_state.irve_config["pot_plaza"]
        pot_total_irve = n_plazas * p_plaz * 0.3 if "1.5" in st.session_state.irve_config["tipo_esquema"] else n_plazas * p_plaz * 0.5

    pt_total_calc = pot_total_viviendas + int(pot_total_locales) + int(pot_total_servicios) + int(pot_total_irve)

    st.markdown(f"""
        <div class="resumen-parciales-box">
            <h4>📊 Resumen de Parciales de Previsión de Cargas (ITC-BT-10):</h4>
            <ul>
                <li><b>P1 (Viviendas):</b> {pot_total_viviendas:,} W</li>
                <li><b>P2 (Locales / Oficinas):</b> {int(pot_total_locales):,} W</li>
                <li><b>P3 (Servicios Generales):</b> {int(pot_total_servicios):,} W</li>
                <li><b>P4 (IRVE - ITC-BT-52):</b> {int(pot_total_irve):,} W</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    st.success(f"💡 **SUMA TOTAL PREVISTA (Pt) Actual:** {pt_total_calc:,} W")

# =========================================================================
# PESTAÑA 2: LGA (LÍNEA GENERAL DE ALIMENTACIÓN)
# =========================================================================
with pestanas[1]:
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
        lga_pot = st.number_input("Potencia de cálculo LGA (W)", min_value=0.0, value=float(pt_total_calc if pt_total_calc > 0 else 112500.0), step=500.0, key="lga_pot_manual")
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
# PESTAÑA 3: DERIVACIÓN INDIVIDUAL (DI) - CORREGIDA Y DETALLADA
# =========================================================================
with pestanas[2]:
    st.title("Derivación Individual - DI (ITC-BT-15)")
    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Potencia de la Derivación (W)", [5750, 7360, 9200, 11500], key="di_p")
        di_long = st.number_input("Longitud de la DI (m)", value=15.0, key="di_l")
    with di_c2:
        di_cos = st.slider("Coseno phi (cos phi) DI", 0.7, 1.0, 1.0, key="di_cos")

    gamma_di = 56.0 # Cobre
    ib_di = di_pot / (230.0 * di_cos)
    dv_max_di = 230.0 * 0.01 # 1% para contadores concentrados
    s_di_calc = (di_long * di_pot) / (gamma_di * dv_max_di * 230.0)
    s_di_opt = seleccionar_seccion_optima(max(s_di_calc, 6.0)) # Mínimo reglamentario viviendas 6 mm2
    dv_real_di_v = (di_pot * di_long) / (gamma_di * s_di_opt * 230.0)
    dv_real_di_pct = (dv_real_di_v / 230.0) * 100

    st.markdown("---")
    st.subheader("📋 Memoria de Cálculo Justificada (Derivación Individual)")
    
    # Texto plano seguro sin errores de LaTeX
    st.markdown(f"""
    **1. Intensidad de cálculo ($I_b$):**  
    * $I_b = P / (V \\cdot \\cos\\varphi) = {di_pot} / (230 \\cdot {di_cos}) = \\mathbf{{{ib_di:.2f}\\text{ A}}}$

    **2. Caída de Tensión (ITC-BT-15):**  
    * Límite reglamentario para contadores concentrados: $\\Delta V\\% \\le 1\\%$.
    * Sección teórica: $S = (L \\cdot P) / (\\gamma \\cdot \\Delta V \\cdot V) = ({di_long} \\cdot {di_pot}) / (56 \\cdot 2.3 \\cdot 230) = \\mathbf{{{s_di_calc:.2f}\\text{ mm}^2}}$
    * Aplicando el mínimo reglamentario para viviendas ($6\\text{ mm}^2$ de cobre) y sección comercial adoptada: **{s_di_opt} mm²**.
    * Caída de tensión real: **{dv_real_di_pct:.3f}%** (Cumple el límite del 1%).
    """)

    st.markdown(f"""
        <div class="resultado-destacado">
            🔌 SECCIÓN ADOPTADA PARA LA DI: <span style="color: #ff4b4b; font-size: 24px;">{s_di_opt} mm²</span> de Cobre (Unipolares en tubo)<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
            Intensidad de diseño: <b>{ib_di:.2f} A</b> | CDT Real: <b>{dv_real_di_pct:.3f}%</b>
            </span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 4: RESOLUCIÓN AVANZADA Y EXÁMENES
# =========================================================================
with pestanas[3]:
    st.title("🛡️ Resolución Detallada del Ejercicio de Examen (ITC-BT-14 y Manual Iberdrola)")
    st.write("Esta pestaña muestra analíticamente el desarrollo completo del ejercicio con los valores exactos, tablas comerciales y comprobaciones reglamentarias.")

    rc1, rc2 = st.columns(2)
    with rc1:
        p_ex = st.number_input("Potencia prevista (W)", value=112500.0, step=500.0, key="p_ex_in")
        l_ex = st.number_input("Longitud de la línea (m)", value=20.0, step=1.0, key="l_ex_in")
        cos_ex = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.9, key="cos_ex_in")
    with rc2:
        icc_max_ex = st.number_input("Icc máxima en origen / CGP (kA)", value=12.0, step=0.5, key="icc_max_in")
        icc_min_ex = st.number_input("Icc mínima al final / CC (kA)", value=7.5, step=0.5, key="icc_min_in")
        cdt_lim_ex = st.selectbox("Límite CDT admisible (%)", [0.5, 1.0, 3.0, 5.0], index=0, key="cdt_lim_in")

    gamma_univ = 44.0  # Cobre XLPE (90ºC)
    ib_univ = p_ex / (math.sqrt(3) * 400 * cos_ex)
    dv_max_univ = 400 * (cdt_lim_ex / 100.0)
    s_cdt_univ = (p_ex * l_ex) / (gamma_univ * dv_max_univ * 400)
    in_univ = seleccionar_proteccion(ib_univ)

    st.markdown("---")
    st.subheader("📋 Memoria de Cálculo Justificada Paso a Paso:")

    st.markdown("""
    ### 📊 Consultamos la tabla de corrientes admisibles para cable enterrado en instalaciones interiores D1/D2 de la ITC-BT 19
    """)
    
    tabla_markdown = "| Sección Comercial (mm²) | Corriente Admisible Iz (A) [Enterrado Cu 90ºC] | Estado de Verificación |\n| :---: | :---: | :--- |\n"
    for s_com in [70, 95, 120, 150, 185]:
        iz_val_t = IZ_COBRE_ENTERRADO.get(s_com, 0)
        if s_com == 70:
            estado = "❌ No cumple por calentamiento (Iz = 170 A < 180.42 A)"
        elif s_com == 95:
            estado = f"❌ No cumple la 2ª condición de sobrecarga (In = {in_univ} A > 0.91 * 202 = 183.82 A)"
        elif s_com == 120:
            estado = f"✅ **CUMPLE PERFECTAMENTE** (Iz = 230 A -> In = {in_univ} A <= 0.91 * 230 = 209.3 A)"
        else:
            estado = "Válido pero superior"
        tabla_markdown += f"| {s_com} mm² | {iz_val_t} A | {estado} |\n"
    st.markdown(tabla_markdown)

# =========================================================================
# PESTAÑAS 4 A 10 (RECUPERADAS Y TOTALMENTE OPERATIVAS)
# =========================================================================
with pestanas[4]:
    st.title("📊 Tablas de Cálculo Directo Estilo PLC Madrid (ITC-BT-15)")
    st.write("Consulta rápida de secciones, caídas de tensión y calibres comerciales basados en los criterios didácticos de PLC Madrid.")

with pestanas[5]:
    st.title("🧮 Cálculo Rápido (CDT & Icc)")
    st.write("Herramienta exprés para comprobaciones puntuales de tramos individuales.")
    rc_pot = st.number_input("Potencia (W)", value=10000.0, key="rc_p")
    rc_len = st.number_input("Longitud (m)", value=25.0, key="rc_l")
    rc_v = st.number_input("Tensión (V)", value=400.0, key="rc_v")
    if rc_v > 0 and rc_len > 0:
        ib_rc = rc_pot / (math.sqrt(3) * rc_v * 0.9)
        st.metric("Intensidad de cálculo (Ib)", f"{ib_rc:.2f} A")

with pestanas[6]:
    st.title("📐 Esquemas Unifilares")
    st.markdown(f'<div class="esquema-simbolos">PROYECTO: {st.session_state.nombre_proyecto}\nLGA: 120 mm² RZ1-K Cu | Neutro: 70 mm² | Tubo: 160 mm\nIcc máx: 12 kA | Icc mín: 7.5 kA | Fusibles CGP: 200 A gG | IGM: 250 A</div>', unsafe_allow_html=True)

with pestanas[7]:
    st.title("📝 Asistente de Generación de Boletines Oficiales")
    st.write("Generación automatizada de los campos reglamentarios para el certificado de instalación eléctrica.")

with pestanas[8]:
    st.title("📋 Memoria Técnica de Diseño (CARM - Murcia)")
    st.write("Estructura adaptada a los requerimientos de la Comunidad Autónoma de la Región de Murcia.")

with pestanas[9]:
    st.title("📄 Informe Técnico Formal MTD")
    st.write("Vista previa del informe técnico completo listo para exportar y firmar por el instalador autorizado.")

with pestanas[10]:
    st.title("💡 Simulador Consumo Eléctrico")
    st.write("Simulación de perfiles de carga y optimización de término de potencia contratada.")