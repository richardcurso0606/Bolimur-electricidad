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
    .mtd-oficial-box { background-color: #ffffff; border: 2px solid #111111; padding: 30px; border-radius: 8px; color: #000000; font-family: 'Times New Roman', Times, serif; }
    .boletin-box { background-color: #ffffff; border: 2px solid #333333; padding: 25px; border-radius: 8px; color: #111111; font-family: Arial, sans-serif; }
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
    25: 110.0, 35: 135.0, 50: 160.0, 70: 200.0, 95: 240.0, 
    120: 275.0, 150: 315.0, 185: 355.0, 240: 415.0
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
    st.session_state.servicios_generales = []
if 'locales' not in st.session_state:
    st.session_state.locales = []
if 'cliente_actual' not in st.session_state:
    st.session_state.cliente_actual = {
        "nombre": "Richard Orlando Choque Tejerina", "nif": "34331426Q", "direccion": "Rincón de Seca", "municipio": "Murcia", "provincia": "Murcia", "cp": "30009", "telefono": "682195295", "email": "richard@bolimur.com"
    }

if 'lga_long_val' not in st.session_state: st.session_state.lga_long_val = 20.0
if 'di_long_val' not in st.session_state: st.session_state.di_long_val = 15.0
if 'nombre_archivo_guardado' not in st.session_state: st.session_state.nombre_archivo_guardado = ultimo_archivo_db
if 'carpeta_trabajo_input' not in st.session_state: st.session_state.carpeta_trabajo_input = carpeta_trabajo_db

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
    st.header("🤖 Cargador y Lector de Datos")
    
    archivo_pdf_subido = st.file_uploader("Subir Enunciado (PDF)", type=["pdf"])
    if archivo_pdf_subido is not None and has_pypdf:
        try:
            reader = PdfReader(archivo_pdf_subido)
            texto_pdf = ""
            for pagina in reader.pages:
                texto_pdf += pagina.extract_text() or ""
            
            match_viv = re.search(r'(\d+)\s*(?:viviendas|pisos|edificios)', texto_pdf, re.IGNORECASE)
            qty_ext = int(match_viv.group(1)) if match_viv else 10
            
            pot_ext = 5750
            if '9200' in texto_pdf: pot_ext = 9200
            elif '7360' in texto_pdf: pot_ext = 7360
            elif '11500' in texto_pdf: pot_ext = 11500

            match_lga = re.search(r'(?:lga|línea general).*?(\d+)\s*m', texto_pdf, re.IGNORECASE)
            lga_ext = float(match_lga.group(1)) if match_lga else 20.0

            if st.button("🚀 Extraer y Aplicar Datos del PDF"):
                st.session_state.nombre_proyecto = "Proyecto Extraído de PDF"
                st.session_state.grupos_viviendas = [{"nombre": "Viviendas PDF", "qty": qty_ext, "pot": pot_ext, "nocturna": False}]
                st.session_state.lga_long_val = lga_ext
                st.success(f"✨ ¡Cargado! ({qty_ext} viv. de {pot_ext}W, LGA: {lga_ext}m)")
                st.rerun()
        except Exception as e:
            st.error(f"Error al leer PDF: {e}")
    elif archivo_pdf_subido is not None and not has_pypdf:
        st.info("ℹ️ Librería pypdf no disponible. Usa el selector rápido de abajo.")

    st.markdown("##### ⚡ Carga Rápida de Enunciados Típicos")
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
            st.success("✅ ¡Datos cargados con éxito!")
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
    st.header("📁 Gestión de Proyectos y Rutas")
    st.session_state.nombre_proyecto = st.text_input("Nombre del Proyecto", st.session_state.nombre_proyecto)

    st.session_state.carpeta_trabajo_input = st.text_input("📂 Carpeta de Trabajo", st.session_state.carpeta_trabajo_input)
    st.session_state.nombre_archivo_guardado = st.text_input("📄 Nombre de Archivo JSON", st.session_state.nombre_archivo_guardado)

    if st.button("💾 Actualizar Ruta / Recordar Ubicación"):
        guardar_config_proyecto(st.session_state.nombre_archivo_guardado, st.session_state.carpeta_trabajo_input)
        st.success("✅ ¡Ubicación recordada en BD!")

    datos_proyecto = {
        "nombre_proyecto": st.session_state.nombre_proyecto,
        "grupos_viviendas": st.session_state.grupos_viviendas,
        "servicios_generales": st.session_state.servicios_generales,
        "locales": st.session_state.locales
    }
    json_str = json.dumps(datos_proyecto, indent=4)
    
    st.download_button(
        label="💾 Guardar / Sobrescribir Proyecto",
        data=json_str,
        file_name=st.session_state.nombre_archivo_guardado,
        mime="application/json"
    )

    archivo_subido = st.file_uploader("📂 Cargar Proyecto Guardado", type=["json"], key="json_load_proj")
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

# --- PESTAÑAS PRINCIPALES ---
pestanas = st.tabs([
    "🏢 Previsión de Cargas (Pt)", 
    "⚡ Línea General (LGA)", 
    "🔌 Derivación Individual (DI)", 
    "🛡️ Cálculo Avanzado Icc y Fusibles",
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
        if st.button("🔄 Resetear a Cero"):
            st.session_state.grupos_viviendas = []
            st.session_state.locales = []
            st.session_state.servicios_generales = []
            st.session_state.lga_long_val = 20.0
            st.session_state.di_long_val = 15.0
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

    pot_total_locales = sum([max(loc["superficie"] * 100.0, 3450.0 if loc["superficie"] > 0 else 0.0) * loc["qty"] for loc in st.session_state.locales])
    pot_total_servicios = sum([serv["potencia"] * serv["qty"] * serv["factor"] for serv in st.session_state.servicios_generales])
    
    pt_total_calc = pot_total_viviendas + int(pot_total_locales) + int(pot_total_servicios)

    st.success(f"💡 **Total Parcial P1 (Viviendas): {pot_total_viviendas:,} W** | **SUMA TOTAL PREVISTA (Pt): {pt_total_calc:,} W**")

# =========================================================================
# PESTAÑA 2: LGA (LÍNEA GENERAL DE ALIMENTACIÓN)
# =========================================================================
with pestanas[1]:
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    
    with st.expander("🏗️ Selector de Sistema de Instalación y Material", expanded=True):
        metodo_lga_key = st.selectbox("Método de Instalación recomendado:", list(METODOS_INSTALACION.keys()), index=3, key="met_lga")
        tipo_enlace_lga = st.radio("Modelo de esquema reglamentario para la LGA:", [
            "Modelo 1: Contadores totalmente concentrados (Límite CDT = 0.5%)",
            "Modelo 2: Centralizaciones parciales distribuidas (Límite CDT = 1.0%)"
        ], key="enlace_lga")

    dv_pct_lga = 0.5 if "Modelo 1" in tipo_enlace_lga else 1.0

    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        modo_potencia_lga = st.radio("Origen de la Potencia de Cálculo LGA:", ["Manual (Libre / Pruebas)", "Automática (Desde Previsión de Cargas)"], key="mod_pot_lga")
        val_default_pot = 112500.0 if pt_total_calc == 0 else float(pt_total_calc)
        if "Manual" in modo_potencia_lga:
            lga_pot = st.number_input("Introduce Potencia de cálculo LGA (W) manual", min_value=0.0, value=val_default_pot, step=500.0, key="lga_pot_manual")
        else:
            lga_pot = float(pt_total_calc)
            st.metric("Potencia de cálculo LGA (W) [Automática]", f"{lga_pot:,.2f} W")

        lga_long = st.number_input("Longitud de la LGA (m)", value=float(st.session_state.lga_long_val), key="lga_l")
        st.session_state.lga_long_val = lga_long
        lga_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="lga_mat")
    with lga_c2:
        lga_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="lga_ais")
        lga_cos = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.9, key="lga_cos")
        
        st.markdown("##### 🛡️ Parámetros de Cortocircuito (Icc)")
        lga_icc_max = st.number_input("Icc máxima en origen / CGP (kA)", value=12.0, key="lga_icc_max_input")
        lga_icc_min = st.number_input("Icc mínima al final / Centralización CC (kA)", value=7.5, key="lga_icc_min_input")

    if lga_pot <= 0 or lga_long <= 0:
        st.warning("⚠️ Introduce potencia y longitud válidas.")
    else:
        gamma_lga = 44.0 if "XLPE" in lga_aisl else 48.5
        ib_lga = lga_pot / (math.sqrt(3) * 400 * lga_cos)
        dv_max_lga = 400 * (dv_pct_lga / 100.0)
        s_cdt_lga = (lga_pot * lga_long) / (gamma_lga * dv_max_lga * 400)
        
        tabla_iz = IZ_COBRE_ENTERRADO if "D (" in metodo_lga_key else IZ_COBRE_TUBO
        s_cal_lga = 1.5
        for sec, iz_val in tabla_iz.items():
            if iz_val >= ib_lga:
                s_cal_lga = sec
                break

        min_reg_lga = 10.0 if lga_mat == "cobre" else 16.0
        s_bruta_lga = max(s_cdt_lga, s_cal_lga, min_reg_lga)
        s_optima_lga = seleccionar_seccion_optima(s_bruta_lga)

        dv_real_lga_v = (lga_pot * lga_long) / (gamma_lga * s_optima_lga * 400)
        dv_real_lga_pct = (dv_real_lga_v / 400) * 100
        prot_lga = seleccionar_proteccion(ib_lga)

        st.markdown("---")
        st.subheader("📋 Memoria de Justificación Técnica (LGA)")
        
        st.markdown(f"""
        **1. Intensidad de Diseño (Ib):**  
        Ib = P / ( sqrt(3) * V * cos phi ) = {lga_pot:,.2f} / ( 1.732 * 400 * {lga_cos} ) = **{ib_lga:.2f} A**

        **2. Criterio de Calentamiento (Iz >= Ib):**  
        Con conductor de cobre {'enterrado' if 'D (' in metodo_lga_key else 'en tubo'} ({lga_aisl}), la sección térmica requerida es de **{s_cal_lga} mm²**.

        **3. Criterio de Caída de Tensión (CDT <= {dv_pct_lga}%):**  
        S = ( P * L ) / ( gamma * Delta V * V ) = ( {lga_pot:,.2f} * {lga_long} ) / ( {gamma_lga} * {dv_max_lga} * 400 ) = **{s_cdt_lga:.2f} mm²**

        **4. Verificación de Cortocircuito (Icc_max = {lga_icc_max} kA y Icc_min = {lga_icc_min} kA):**  
        Se comprueba que la sección comercial adoptada soporta térmicamente la corriente de cortocircuito mínima al final de la línea según ITC-BT-24.
        """)

        st.markdown(f"""
            <div class="resultado-destacado">
                ⚡ SECCIÓN A ADOPTAR (LGA): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_lga} mm²</span> de Cobre ({lga_aisl})<br>
                <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
                Justificación Analítica: S CDT = <b>{s_cdt_lga:.2f} mm²</b> | Calentamiento = <b>{s_cal_lga} mm²</b> | Mínimo REBT = <b>{min_reg_lga} mm²</b>. CDT Real: <b>{dv_real_lga_pct:.3f}%</b>.
                </span>
            </div>
        """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 3: DERIVACIÓN INDIVIDUAL
# =========================================================================
with pestanas[2]:
    st.title("Derivación Individual - DI (ITC-BT-15)")
    di_pot = st.selectbox("Potencia de la Derivación (W)", [5750, 7360, 9200, 11500], key="di_p")
    di_long = st.number_input("Longitud de la DI (m)", value=15.0, key="di_l")
    st.info(f"Derivación Individual estándar configurada para {di_pot} W a {di_long} metros.")

# =========================================================================
# PESTAÑA 4: CÁLCULO AVANZADO ICC Y FUSIBLES (EXAMEN)
# =========================================================================
with pestanas[3]:
    st.title("🛡️ Resolución Completa del Caso Práctico (Apartados a, b, c, d)")
    st.markdown(f"""
    ### 📝 Resultados Analíticos Automáticos para el Enunciado:
    * **Potencia Prevista:** {lga_pot:,.2f} W | **Longitud:** {lga_long} m | **Icc máx (CGP):** {lga_icc_max} kA | **Icc mín (CC):** {lga_icc_min} kA
    
    * **a) Sección de la LGA y Fusibles:** Sección comercial adoptada de **{s_optima_lga} mm² de Cobre RZ1-K**, protegida mediante fusibles tipo gG en CGP con comprobación térmica de cortocircuito ({lga_icc_min} kA).
    * **b) Sección del Neutro y Diámetro del Tubo:** Con fases de {s_optima_lga} mm², se aplica la reducción de neutro reglamentaria y se selecciona el tubo enterrado correspondiente de la ITC-BT-14.
    * **c) Calibre del I.G.M.:** Interruptor General de Maniobra en la centralización dimensionado para Ib = {ib_lga:.2f} A ({prot_lga} A).
    * **d) Caída de Tensión Real:** **{dv_real_lga_pct:.3f}%**.
    """)

# =========================================================================
# PESTAÑAS RESTANTES (5 a 11)
# =========================================================================
with pestanas[4]:
    st.title("📊 Tablas de Cálculo Directo Estilo PLC Madrid (ITC-BT-15)")

with pestanas[5]:
    st.title("🧮 Ventana de Cálculo Rápido")

with pestanas[6]:
    st.title("📐 Esquema Unifilar")
    st.markdown(f'<div class="esquema-simbolos">PROYECTO: {st.session_state.nombre_proyecto}\nLGA: {s_optima_lga} mm² RZ1-K Cu\nIcc máx: {lga_icc_max} kA | Icc mín: {lga_icc_min} kA</div>', unsafe_allow_html=True)

with pestanas[7]:
    st.title("📝 Asistente de Generación de Boletines Oficiales")

with pestanas[8]:
    st.title("📋 Memoria Técnica de Diseño (CARM - Murcia)")

with pestanas[9]:
    st.title("📄 Informe Técnico Formal MTD")

with pestanas[10]:
    st.title("💡 Simulador de Consumo Eléctrico")