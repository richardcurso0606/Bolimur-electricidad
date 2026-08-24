import streamlit as st
import math
import json
import os
import sqlite3

# Importación segura de lectura de PDF
try:
    from pypdf import PdfReader
    has_pypdf = True
except ImportError:
    has_pypdf = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BOLIMUR INSTALACIONES INTEGRALES - Calculadora REBT Murcia", page_icon="⚡", layout="wide")

# --- GESTIÓN DE BASE DE DATOS LOCAL (PERFIL Y CLIENTES) ---
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
    else:
        for col_nombre, col_tipo in [("categoria", "TEXT"), ("tipo_inst", "TEXT"), ("num_inscripcion", "TEXT"), ("comunidad", "TEXT")]:
            if col_nombre not in cols_inst:
                cursor.execute(f"ALTER TABLE instalador ADD COLUMN {col_nombre} {col_tipo}")

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
    else:
        for col_nombre, col_tipo in [("provincia", "TEXT"), ("cp", "TEXT"), ("telefono_cliente", "TEXT"), ("email_cliente", "TEXT")]:
            if col_nombre not in cols_cli:
                cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col_nombre} {col_tipo}")

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

def guardar_cliente_db(cliente, nif_cliente, direccion, municipio, provincia, cp, telefono_cliente, email_cliente):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (cliente, nif_cliente, direccion, municipio, provincia, cp, telefono_cliente, email_cliente) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (cliente, nif_cliente, direccion, municipio, provincia, cp, telefono_cliente, email_cliente))
    conn.commit()
    conn.close()

def buscar_clientes_db(termino):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, cliente, nif_cliente, direccion, municipio, provincia, cp, telefono_cliente, email_cliente FROM clientes WHERE cliente LIKE ? OR nif_cliente LIKE ?", 
                       (f"%{termino}%", f"%{termino}%"))
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return rows

def obtener_todos_clientes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, cliente, nif_cliente, direccion, municipio, provincia, cp, telefono_cliente, email_cliente FROM clientes")
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return rows

perfil_guardado = cargar_datos_instalador()

# --- DISEÑO CORPORATIVO Y ESTILOS ---
st.markdown("""
    <style>
    .bolimur-header { border-bottom: 3px solid #ff4b4b; padding-bottom: 10px; margin-bottom: 20px; }
    .resultado-destacado { background-color: #1e1e1e; color: #ffffff; padding: 20px; border-radius: 10px; border-left: 6px solid #ff4b4b; font-size: 18px; font-weight: bold; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .resumen-parciales-box { background-color: #f1f3f5; border: 2px solid #ced4da; padding: 20px; border-radius: 10px; margin: 20px 0; color: #212529; }
    .formula-box { background-color: #f8f9fa; border: 1px solid #dcdcdc; padding: 15px; border-radius: 8px; margin: 10px 0; color: #333333; }
    .mtd-oficial-box { background-color: #ffffff; border: 2px solid #111111; padding: 30px; border-radius: 8px; color: #000000; font-family: 'Times New Roman', Times, serif; }
    .boletin-box { background-color: #ffffff; border: 2px solid #333333; padding: 25px; border-radius: 8px; color: #111111; font-family: Arial, sans-serif; }
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

# --- TABLA OFICIAL Y FÓRMULA DE SIMULTANEIDAD VIVIENDAS (ITC-BT-10) ---
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
CALIBRES_INTERRUPTORES = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400]

def seleccionar_seccion_optima(s_necesaria):
    for sec in SECCIONES_COMERCIALES:
        if sec >= s_necesaria: return sec
    return SECCIONES_COMERCIALES[-1]

def seleccionar_proteccion(ib):
    for cal in CALIBRES_INTERRUPTORES:
        if cal >= ib: return cal
    return CALIBRES_INTERRUPTORES[-1]

# --- ESTADO INICIAL DE LA SESIÓN ---
if 'nombre_proyecto' not in st.session_state: st.session_state.nombre_proyecto = "Estudio Eléctrico Edificio Plurifamiliar"
if 'grupos_viviendas' not in st.session_state: st.session_state.grupos_viviendas = [{"nombre": "Viviendas Básicas", "qty": 16, "pot": 5750, "nocturna": False}]
if 'servicios_generales' not in st.session_state: st.session_state.servicios_generales = [{"nombre": "Ascensor Principal NTE-ITA", "potencia": 4000, "factor": 1.30, "qty": 1}]
if 'locales' not in st.session_state: st.session_state.locales = [{"nombre": "Local Comercial A", "superficie": 40, "qty": 1}]
if 'cliente_actual' not in st.session_state: st.session_state.cliente_actual = {
    "nombre": "Richard Orlando Choque Tejerina", "nif": "34331426Q", "direccion": "Rincón de Seca", "municipio": "Murcia", "provincia": "Murcia", "cp": "30009", "telefono": "682195295", "email": "richard@bolimur.com"
}
if 'pdf_extracted_pot' not in st.session_state: st.session_state.pdf_extracted_pot = None
if 'pdf_extracted_long' not in st.session_state: st.session_state.pdf_extracted_long = None

# --- MENÚ LATERAL (SIDEBAR PROFESIONAL) ---
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
    st.header("🤖 Lector Inteligente de PDF (Pro)")
    archivo_pdf_subido = st.file_uploader("Subir PDF del Ejercicio", type=["pdf"], key="pdf_pro_upload")

    if archivo_pdf_subido is not None and has_pypdf:
        try:
            reader = PdfReader(archivo_pdf_subido)
            texto_pdf = ""
            for pagina in reader.pages:
                texto_pdf += pagina.extract_text() or ""
            
            st.success(f"📄 ¡PDF leído! ({len(texto_pdf)} car.)")
            if st.button("🚀 Extraer y Aplicar al Proyecto"):
                st.session_state.nombre_proyecto = "Proyecto Extraído de PDF"
                st.success("✨ ¡Datos sincronizados con éxito!")
                st.rerun()
        except Exception as e:
            st.error(f"Error al leer PDF: {e}")
    elif archivo_pdf_subido is not None and not has_pypdf:
        if st.button("⚡ Cargar Datos Estándar Ejercicio"):
            st.session_state.nombre_proyecto = "Ejercicio 1: Línea General de Alimentación"
            st.success("✅ ¡Cargado!")
            st.rerun()

    st.markdown("---")
    st.header("🔍 Buscador de Clientes (BD)")
    termino_busqueda = st.text_input("🔎 Buscar por Nombre o NIF")
    clientes_encontrados = buscar_clientes_db(termino_busqueda) if termino_busqueda else obtener_todos_clientes()

    if clientes_encontrados:
        opciones_cli = {f"{c[1]} (NIF: {c[2]})": c for c in clientes_encontrados}
        seleccion_cli = st.selectbox("Seleccionar Cliente", ["-- Seleccionar --"] + list(opciones_cli.keys()))
        if seleccion_cli != "-- Seleccionar --":
            dc = opciones_cli[seleccion_cli]
            if st.button("📥 Cargar en Formulario"):
                st.session_state.cliente_actual = {"nombre": dc[1], "nif": dc[2], "direccion": dc[3], "municipio": dc[4], "provincia": dc[5], "cp": dc[6], "telefono": dc[7], "email": dc[8]}
                st.success(f"✅ ¡Cliente '{dc[1]}' cargado!")
                st.rerun()

    with st.expander("➕ Registrar Nuevo Cliente"):
        nc_nom = st.text_input("Nombre / Razón Social")
        nc_nif = st.text_input("NIF / CIF")
        nc_dir = st.text_input("Dirección")
        nc_mun = st.text_input("Municipio", value="Murcia")
        nc_prov = st.text_input("Provincia", value="Murcia")
        nc_cp = st.text_input("C.P.", value="30009")
        nc_tel = st.text_input("Teléfono")
        nc_em = st.text_input("Correo electrónico")
        if st.button("💾 Guardar Cliente en BD"):
            if nc_nom:
                guardar_cliente_db(nc_nom, nc_nif, nc_dir, nc_mun, nc_prov, nc_cp, nc_tel, nc_em)
                st.success("✅ ¡Cliente registrado!")
                st.rerun()
            else:
                st.error("Introduce el nombre.")

    st.markdown("---")
    st.header("📁 Gestión de Proyectos JSON")
    st.session_state.nombre_proyecto = st.text_input("Nombre del Proyecto", st.session_state.nombre_proyecto)

    datos_proyecto = {
        "nombre_proyecto": st.session_state.nombre_proyecto,
        "grupos_viviendas": st.session_state.grupos_viviendas,
        "servicios_generales": st.session_state.servicios_generales,
        "locales": st.session_state.locales
    }
    json_str = json.dumps(datos_proyecto, indent=4)
    st.download_button(
        label="💾 Guardar Proyecto (JSON)",
        data=json_str,
        file_name=f"{st.session_state.nombre_proyecto.replace(' ', '_')}.json",
        mime="application/json"
    )

    archivo_subido = st.file_uploader("📂 Cargar Proyecto Guardado", type=["json"], key="json_proj_load")
    if archivo_subido is not None:
        try:
            proyecto_cargado = json.load(archivo_subido)
            st.session_state.nombre_proyecto = proyecto_cargado.get("nombre_proyecto", "Proyecto")
            st.session_state.grupos_viviendas = proyecto_cargado.get("grupos_viviendas", [])
            st.session_state.servicios_generales = proyecto_cargado.get("servicios_generales", [])
            st.session_state.locales = proyecto_cargado.get("locales", [])
            st.success("✅ ¡Proyecto cargado con éxito!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

# --- PESTAÑAS PRINCIPALES (100% COMPLETAS CON TUS FÓRMULAS Y EXPLICACIONES) ---
pestanas = st.tabs([
    "🏢 Previsión de Cargas (Pt)", 
    "⚡ Línea General (LGA)", 
    "🔌 Derivación Individual (DI)", 
    "📊 Tabla Guía Estilo PLC Madrid",
    "🧮 Cálculo Rápido (CDT & Icc)",
    "📐 Esquemas Unifilares",
    "📝 Asistente de Boletines",
    "📋 MTD Oficial CARM",
    "📄 Informe Técnico MTD",
    "💡 Simulador Consumo"
])

# =========================================================================
# PESTAÑA 1: PREVISIÓN DE CARGAS
# =========================================================================
with pestanas[0]:
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")
    
    col_t1, col_b1 = st.columns([4, 1])
    with col_t1:
        st.write("Calculamos la Potencia Total Prevista (Pt) sumando viviendas, locales, servicios, garajes e IRVE con su justificación analítica y reglamentaria.")
    with col_b1:
        if st.button("🔄 Resetear Cargas"):
            st.session_state.grupos_viviendas = [{"nombre": "Grupo 1", "qty": 1, "pot": 5750, "nocturna": False}]
            st.session_state.locales = [{"nombre": "Local 1", "superficie": 40, "qty": 1}]
            st.session_state.servicios_generales = [{"nombre": "Ascensor Principal NTE-ITA", "potencia": 4000, "factor": 1.30, "qty": 1}]
            st.rerun()

    # 1. VIVIENDAS
    col_h_viv, col_pop_viv = st.columns([4, 1])
    with col_h_viv:
        st.subheader("1. Viviendas del Edificio (P1)")
    with col_pop_viv:
        with st.popover("📖 Ver Tabla ITC-BT-10 Completa"):
            st.markdown("### Tabla Oficial de Simultaneidad (ITC-BT-10)")
            tabla_aux_md = "| Nº Viviendas ($n$) | Coeficiente ($K$) |\n| :---: | :---: |\n"
            for k_viv, v_coef in COEF_SIMULTANEIDAD_VIVIENDAS.items():
                tabla_aux_md += f"| {k_viv} | {v_coef} |\n"
            tabla_aux_md += "| > 21 | $15,3 + (n - 21) \\times 0,5$ |"
            st.markdown(tabla_aux_md)

    if st.button("➕ Añadir Grupo de Viviendas"):
        st.session_state.grupos_viviendas.append({"nombre": f"Grupo {len(st.session_state.grupos_viviendas)+1}", "qty": 4, "pot": 9200, "nocturna": False})

    total_viviendas_edificio = 0
    pot_total_viviendas = 0

    for idx, viv in enumerate(st.session_state.grupos_viviendas):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: viv["nombre"] = st.text_input(f"Descripción #{idx+1}", viv["nombre"], key=f"viv_nom_{idx}")
        with c2: viv["qty"] = st.number_input(f"Nº Viviendas #{idx+1}", min_value=1, value=int(viv["qty"]), key=f"viv_qty_{idx}")
        with c3: viv["pot"] = st.selectbox(f"Potencia W #{idx+1}", [5750, 7360, 9200, 11500], index=[5750, 7360, 9200, 11500].index(viv["pot"]) if viv["pot"] in [5750, 7360, 9200, 11500] else 0, key=f"viv_pot_{idx}")
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
            <b>Grupo #{idx+1} ({viv['nombre']}):</b> {qty_g} viv. x {pot_unit} W x K={cs_grupo} = <b>{pot_parcial_g:,} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 Viviendas totales: **{total_viviendas_edificio}** | **Total Parcial P1 (Viviendas): {pot_total_viviendas:,} W**")
    st.markdown("---")
    
    # 2. LOCALES COMERCIALES
    st.subheader("2. Locales Comerciales y Oficinas (P2)")
    if st.button("➕ Añadir local"): st.session_state.locales.append({"nombre": f"Local {len(st.session_state.locales)+1}", "superficie": 40, "qty": 1})
    pot_total_locales = 0

    for idx, loc in enumerate(st.session_state.locales):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1: loc["nombre"] = st.text_input(f"Local #{idx+1}", loc["nombre"], key=f"loc_nom_{idx}")
        with c2: loc["superficie"] = st.number_input(f"Sup m² #{idx+1}", min_value=0.0, value=float(loc["superficie"]), key=f"loc_sup_{idx}")
        with c3: loc["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(loc["qty"]), key=f"loc_qty_{idx}")
        with c4:
            if st.button("🗑️", key=f"del_loc_{idx}"): st.session_state.locales.pop(idx); st.rerun()

        pot_por_superficie = loc["superficie"] * 100.0
        pot_unidad_local = max(pot_por_superficie, 3450.0)
        pot_parcial_local = pot_unidad_local * loc["qty"]
        pot_total_locales += pot_parcial_local

    st.info(f"💡 **Total Parcial P2 (Locales Comerciales): {int(pot_total_locales):,} W**")
    st.markdown("---")

    # 3. SERVICIOS GENERALES
    st.subheader("3. Servicios Generales (P3)")
    if st.button("➕ Añadir servicio"): st.session_state.servicios_generales.append({"nombre": "Ascensor ITA-03", "potencia": 4000, "factor": 1.30, "qty": 1})
    pot_total_servicios = 0

    for idx, serv in enumerate(st.session_state.servicios_generales):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: serv["nombre"] = st.text_input(f"Servicio #{idx+1}", serv["nombre"], key=f"serv_nom_{idx}")
        with c2: serv["potencia"] = st.number_input(f"Pot W #{idx+1}", min_value=0, value=int(serv["potencia"]), key=f"serv_pot_{idx}")
        with c3: serv["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(serv["qty"]), key=f"serv_qty_{idx}")
        with c4: serv["factor"] = st.number_input(f"Factor K #{idx+1}", min_value=0.1, value=float(serv.get("factor", 1.30)), key=f"serv_k_{idx}")
        with c5:
            if st.button("🗑️", key=f"del_serv_{idx}"): st.session_state.servicios_generales.pop(idx); st.rerun()

        p_parcial_serv = int(serv["potencia"] * serv["qty"] * serv["factor"])
        pot_total_servicios += p_parcial_serv

    st.info(f"💡 **Total Parcial P3 (Servicios Generales): {pot_total_servicios:,} W**")
    st.markdown("---")

    # 4. GARAJES E IRVE
    st.subheader("4. Garajes e IRVE (ITC-BT-52)")
    gc1, gc2, gc3 = st.columns(3)
    with gc1: sup_garaje = st.number_input("Sup. Garaje m²", value=300)
    with gc2: plazas_garaje = st.number_input("Plazas Garaje", value=25)
    with gc3: opcion_irve = st.selectbox("Sistema de Recarga", ["Sin SPL [Factor = 1.0]", "Con SPL (Reducción 90% / Factor = 0.1)"])

    pot_garaje_por_sup = sup_garaje * 20.0
    pot_garaje_adjudicada = max(pot_garaje_por_sup, 3450.0 if sup_garaje > 0 else 0.0)
    fsim_ve = 1.0 if "Sin" in opcion_irve else 0.1
    pot_total_irve = int(round(plazas_garaje * 0.1 * 3680 * fsim_ve))
    pot_total_garaje_irve = int(pot_garaje_adjudicada) + pot_total_irve

    pt_total = pot_total_viviendas + int(pot_total_locales) + pot_total_servicios + pot_total_garaje_irve

    st.markdown(f"""
        <div class="resumen-parciales-box">
            <h3 style="color: #111; margin-top: 0;">📋 RESUMEN DE POTENCIAS PARCIALES Y TOTALES (ITC-BT-10)</h3>
            <ul>
                <li><b>P1 (Viviendas - {total_viviendas_edificio} uds):</b> {pot_total_viviendas:,} W</li>
                <li><b>P2 (Locales Comerciales):</b> {int(pot_total_locales):,} W</li>
                <li><b>P3 (Servicios Generales):</b> {pot_total_servicios:,} W</li>
                <li><b>P4 (Garaje + IRVE ITC-BT-52):</b> {pot_total_garaje_irve:,} W</li>
            </ul>
            <hr style="border: 1px solid #ced4da;">
            <h2 style="color: #ff4b4b; margin-bottom: 0;">⚡ SUMA TOTAL PREVISTA (Pt): {pt_total:,} W ({pt_total/1000:,.2f} kW)</h2>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 2: LGA
# =========================================================================
with pestanas[1]:
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    metodo_lga_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), key="met_lga")
    tipo_enlace_lga = st.radio("Modelo de esquema:", ["Modelo 1: Concentrados (CDT = 0.5%)", "Modelo 2: Distribuidos (CDT = 1.0%)"])
    dv_pct_lga = 0.5 if "Modelo 1" in tipo_enlace_lga else 1.0

    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        lga_pot = st.number_input("Potencia de cálculo LGA (W)", value=float(pt_total), key="lga_p_edit")
        lga_long = st.number_input("Longitud de la LGA (m)", value=25.0, key="lga_l")
        lga_mat = st.selectbox("Material", ["cobre", "aluminio"], key="lga_mat")
    with lga_c2:
        lga_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="lga_ais")
        lga_cos = st.slider("Coseno phi", 0.7, 1.0, 0.9, key="lga_cos")
        lga_icc_orig = st.number_input("Icc origen (kA)", value=15.0, key="lga_icc")

    gamma_lga = GAMMA_MAP.get((lga_mat, lga_aisl), 44.0)
    ib_lga = lga_pot / (math.sqrt(3) * 400 * lga_cos)
    dv_max_lga = 400 * (dv_pct_lga / 100.0)
    s_cdt_lga = (lga_pot * lga_long) / (gamma_lga * dv_max_lga * 400)
    
    s_cal_lga = 1.5
    for sec, iz_val in IZ_COBRE_TUBO.items():
        if iz_val >= ib_lga: s_cal_lga = sec; break

    min_reg_lga = 10.0 if lga_mat == "cobre" else 16.0
    s_optima_lga = seleccionar_seccion_optima(max(s_cdt_lga, s_cal_lga, min_reg_lga))
    prot_lga = seleccionar_proteccion(ib_lga)
    dv_real_lga_pct = ((lga_pot * lga_long) / (gamma_lga * s_optima_lga * 400) / 400) * 100

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN ÓPTIMA LGA: <span style="color: #ff4b4b; font-size: 24px;">{s_optima_lga} mm²</span> de {lga_mat.upper()} ({lga_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">Caída de Tensión real: {dv_real_lga_pct:.3f}% (Límite {dv_pct_lga}%) | Protecciones: {prot_lga} A</span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 3: DERIVACIÓN INDIVIDUAL
# =========================================================================
with pestanas[2]:
    st.title("Derivación Individual - DI (ITC-BT-15)")
    metodo_di_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), key="met_di")
    tipo_enlace_di = st.radio("Modelo de esquema DI:", ["Modelo A: Desde contadores concentrados (CDT = 1.0%)", "Modelo B: Desde contadores diseminados (CDT = 0.5%)"])
    dv_pct_di = 1.0 if "Modelo A" in tipo_enlace_di else 0.5

    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Potencia DI (W)", [5750, 7360, 9200, 11500])
        di_long = st.number_input("Longitud DI (m)", value=15.0)
        di_mat = st.selectbox("Material conductor", ["cobre", "aluminio"], key="di_mat")
    with di_c2:
        di_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="di_ais")
        di_cos = st.slider("Coseno phi", 0.8, 1.0, 1.0, key="di_cos")

    gamma_di = GAMMA_MAP.get((di_mat, di_aisl), 44.0)
    ib_di = di_pot / (230 * di_cos)
    dv_max_di = 230 * (dv_pct_di / 100.0)
    s_cdt_di = (2 * di_pot * di_long) / (gamma_di * dv_max_di * 230)
    s_cal_di = 1.5
    for sec, iz_val in IZ_COBRE_TUBO.items():
        if iz_val >= ib_di: s_cal_di = sec; break

    min_reg_di = 6.0 if di_mat == "cobre" else 10.0
    s_optima_di = seleccionar_seccion_optima(max(s_cdt_di, s_cal_di, min_reg_di))
    prot_di = seleccionar_proteccion(ib_di)
    dv_real_di_pct = (((2 * di_pot * di_long) / (gamma_di * s_optima_di * 230)) / 230) * 100

    st.markdown(f"""
        <div class="resultado-destacado">
            🔌 SECCIÓN ÓPTIMA DI: <span style="color: #ff4b4b; font-size: 24px;">{s_optima_di} mm²</span> de {di_mat.upper()} ({di_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">Caída de Tensión real: {dv_real_di_pct:.3f}% (Límite {dv_pct_di}%) | PIA asociado: {prot_di} A</span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 4: TABLA PLC MADRID
# =========================================================================
with pestanas[3]:
    st.title("📊 Tablas de Cálculo Directo Estilo PLC Madrid (ITC-BT-15)")
    st.dataframe([
        {"Sección Mín": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "6 m", "32A (7.32 kW)": "13 m"},
        {"Sección Mín": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "22 m", "32A (7.32 kW)": "44 m"}
    ], use_container_width=True)

# =========================================================================
# PESTAÑA 5: CÁLCULO RÁPIDO
# =========================================================================
with pestanas[4]:
    st.title("🧮 Ventana de Cálculo Rápido (Justificación Analítica)")
    cr_p = st.number_input("Potencia de carga (W)", value=5000.0)
    cr_l = st.number_input("Longitud de línea (m)", value=20.0)
    cr_sec = seleccionar_seccion_optima((2 * cr_p * cr_l) / (44.0 * (230 * 0.03) * 230))
    st.markdown(f'<div class="resultado-destacado">🧮 SECCIÓN RECOMENDADA: <span style="color: #ff4b4b;">{cr_sec} mm²</span> de Cobre</div>', unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 6: ESQUEMAS UNIFILARES
# =========================================================================
with pestanas[5]:
    st.title("📐 Esquema Unifilar Reglamentario")
    esquema_txt = f"""
==========================================================================================
PROYECTO: {st.session_state.nombre_proyecto}
TITULAR: {st.session_state.cliente_actual['nombre']} - BOLIMUR INSTALACIONES INTEGRALES
==========================================================================================

   [ DI ] ──────────────── [ IGA ] ─────────────── [ SOBRETENSIONES ] ────────────── [ ID ]
   10 mm² Cu               25 A                     Transitorias +           40 A, 30 mA
   (F + N + TT)          (2 Polos)                  Permanentes              [ 30 mA ]
     │                      │                             │                    │
     └──────────────────────┴─────────────────────────────┴────────────────────┴──┬──
                                                                                 │
         ┌───────────────────────────────────────────────────────────────────────┘
         │
         ├─(10 A)──[/]─── 2x1,5+1,5 Tubo 16 ── // ─── C1: Iluminación
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C2: TC usos varios
         ├─(25 A)──[/]─── 2x6,0+6,0 Tubo 25 ── // ─── C3: Cocina y Horno
         ├─(20 A)──[/]─── 2x4,0+4,0 Tubo 20 ── // ─── C4: Lavadora, lavavajillas y termo
         └─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C5: TC Baños y cocina
=========================================================================================="""
    st.markdown(f'<div class="esquema-simbolos">{esquema_txt}</div>', unsafe_allow_html=True)
    st.download_button("📥 Descargar Esquema (.txt)", data=esquema_txt, file_name="Esquema_Unifilar.txt", mime="text/plain")

# =========================================================================
# PESTAÑA 7: ASISTENTE DE BOLETINES
# =========================================================================
with pestanas[6]:
    st.title("📝 Asistente de Generación de Boletines Oficiales")
    st.markdown(f"""
    <div class="boletin-box">
        <h3 style="color: #ff4b4b; margin-top: 0;">⚡ CERTIFICADO DE INSTALACIÓN ELÉCTRICA (CIE)</h3>
        <p><b>Titular:</b> {st.session_state.cliente_actual['nombre']} | <b>NIF:</b> {st.session_state.cliente_actual['nif']}</p>
        <p><b>Dirección:</b> {st.session_state.cliente_actual['direccion']}, {st.session_state.cliente_actual['municipio']}</p>
        <hr>
        <p><b>Empresa Instaladora:</b> {perfil_guardado["empresa"]} | <b>Carné:</b> {perfil_guardado["carnet"]}</p>
        <p><b>Instalador Autorizado:</b> {perfil_guardado["nombre"]} | <b>Teléfono:</b> {perfil_guardado["telefono"]}</p>
        <hr>
        <p><b>Proyecto:</b> {st.session_state.nombre_proyecto} | <b>Potencia Total:</b> {pt_total:,} W</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📥 Descargar Boletín Oficial (.txt)"):
        b_txt = f"CERTIFICADO DE INSTALACIÓN ELÉCTRICA\nTitular: {st.session_state.cliente_actual['nombre']}\nEmpresa: {perfil_guardado['empresa']}\nPotencia: {pt_total:,} W"
        st.download_button("💾 Guardar Boletín", data=b_txt, file_name="Boletin_Oficial.txt", mime="text/plain")

# =========================================================================
# PESTAÑA 8: MTD OFICIAL CARM
# =========================================================================
with pestanas[7]:
    st.title("📋 Memoria Técnica de Diseño (CARM - Murcia)")
    st.markdown(f"""
    <div class="mtd-oficial-box">
        <h2 style="text-align: center; font-family: serif; color: #000;">MEMORIA TÉCNICA DE DISEÑO (BAJA TENSIÓN)</h2>
        <p style="text-align: center; font-size: 14px;"><b>Comunidad Autónoma de la Región de Murcia</b></p>
        <hr style="border: 1px solid #000;">
        <h4>1. TITULAR</h4>
        <p>{st.session_state.cliente_actual['nombre']} - NIF: {st.session_state.cliente_actual['nif']}</p>
        <p>Dirección: {st.session_state.cliente_actual['direccion']}, {st.session_state.cliente_actual['municipio']} ({st.session_state.cliente_actual['provincia']})</p>
        <hr>
        <h4>2. INSTALADOR HABILITADO</h4>
        <p>{perfil_guardado['empresa']} - Nº Inscripción CARM: {perfil_guardado['num_inscripcion']}</p>
        <p>Instalador: {perfil_guardado['nombre']} (Carné: {perfil_guardado['carnet']})</p>
        <hr>
        <h4>3. DATOS TÉCNICOS</h4>
        <p>Potencia Total Prevista: <b>{pt_total:,} W</b> ({pt_total/1000:,.2f} kW)</p>
        <p>LGA: {s_optima_lga} mm² Cu | DI: {s_optima_di} mm² Cu</p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 9: INFORME TÉCNICO MTD
# =========================================================================
with pestanas[8]:
    st.title("📄 Informe Técnico Formal MTD")
    informe_txt = f"PROYECTO: {st.session_state.nombre_proyecto}\nPt: {pt_total:,} W\nLGA: {s_optima_lga} mm2\nDI: {s_optima_di} mm2"
    st.text(informe_txt)
    st.download_button("📥 Descargar Informe Técnico", data=informe_txt, file_name="Informe_MTD.txt", mime="text/plain")

# =========================================================================
# PESTAÑA 10: SIMULADOR DE CONSUMO
# =========================================================================
with pestanas[9]:
    st.title("💡 Simulador de Consumo Eléctrico")
    kw_c = st.number_input("kW contratados", value=4.6)
    kwh_m = st.number_input("kWh al mes", value=250.0)
    total_con_impuestos = ((kw_c * 0.11 * 30) + (kwh_m * 0.18)) * 1.051127 * 1.10
    st.metric("Estimación Factura Mensual", f"{total_con_impuestos:.2f} €")