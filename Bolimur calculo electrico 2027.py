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
    st.session_state.servicios_generales = []
if 'locales' not in st.session_state:
    st.session_state.locales = []
if 'cliente_actual' not in st.session_state:
    st.session_state.cliente_actual = {
        "nombre": "Richard Orlando Choque Tejerina", "nif": "34331426Q", "direccion": "Rincón de Seca", "municipio": "Murcia", "provincia": "Murcia", "cp": "30009", "telefono": "682195295", "email": "richard@bolimur.com"
    }

if 'lga_long_val' not in st.session_state: st.session_state.lga_long_val = 25.0
if 'di_long_val' not in st.session_state: st.session_state.di_long_val = 15.0

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
            lga_ext = float(match_lga.group(1)) if match_lga else 25.0

            if st.button("🚀 Extraer y Aplicar Datos del PDF"):
                st.session_state.nombre_proyecto = "Proyecto Extraído de PDF"
                st.session_state.grupos_viviendas = [{"nombre": "Viviendas PDF", "qty": qty_ext, "pot": pot_ext, "nocturna": False}]
                st.session_state.lga_long_val = lga_ext
                st.success(f"✨ ¡Cargado! ({qty_ext} viv. de {pot_ext}W, LGA: {lga_ext}m)")
                st.rerun()
        except Exception as e:
            st.error(f"Error al leer PDF: {e}")
    elif archivo_pdf_subido is not None and not has_pypdf:
        st.info("ℹ️ Librería pypdf no disponible. Usa el selector rápido de abajo para cargar tus casos instantáneamente.")

    # Selector manual de respaldo (funciona siempre 100%)
    st.markdown("##### ⚡ Carga Rápida de Enunciados Típicos")
    tipo_caso = st.selectbox("Selecciona caso de estudio:", [
        "-- Seleccionar caso --",
        "Edificio 10 viviendas (LGA: 25m, DI: 15m)",
        "Edificio 20 viviendas (LGA: 35m, DI: 20m)",
        "Edificio 5 viviendas (LGA: 15m, DI: 10m)"
    ])
    if tipo_caso != "-- Seleccionar --":
        if st.button("📥 Cargar Configuración Seleccionada"):
            if "10 viviendas" in tipo_caso:
                st.session_state.grupos_viviendas = [{"nombre": "Bloc 10 Viviendas", "qty": 10, "pot": 5750, "nocturna": False}]
                st.session_state.lga_long_val = 25.0
                st.session_state.di_long_val = 15.0
            elif "20 viviendas" in tipo_caso:
                st.session_state.grupos_viviendas = [{"nombre": "Bloc 20 Viviendas", "qty": 20, "pot": 5750, "nocturna": False}]
                st.session_state.lga_long_val = 35.0
                st.session_state.di_long_val = 20.0
            elif "5 viviendas" in tipo_caso:
                st.session_state.grupos_viviendas = [{"nombre": "Bloc 5 Viviendas", "qty": 5, "pot": 5750, "nocturna": False}]
                st.session_state.lga_long_val = 15.0
                st.session_state.di_long_val = 10.0
            st.success("✅ ¡Datos del caso cargados con éxito!")
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
    st.header("📁 Gestión de Proyectos")
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
            st.session_state.lga_long_val = 0.0
            st.session_state.di_long_val = 0.0
            st.rerun()

    # 1. VIVIENDAS
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
            just_str = "Tarifa Nocturna activada: Coeficiente K = 1.0."
        else:
            cs_grupo = get_coef_simultaneidad(qty_g)
            just_str = f"Aplicación ITC-BT-10 para {qty_g} viviendas: Coeficiente K = {cs_grupo:.2f}."

        pot_parcial_g = int(round(qty_g * pot_unit * cs_grupo))
        pot_total_viviendas += pot_parcial_g

        st.info(f"Justificación Grupo #{idx+1} ({viv['nombre']}): {just_str} | Cálculo parcial: {qty_g} x {pot_unit}W x {cs_grupo} = {pot_parcial_g:,} W")

    st.success(f"💡 Viviendas totales: **{total_viviendas_edificio}** | **Total Parcial P1 (Viviendas): {pot_total_viviendas:,} W**")
    st.markdown("---")
    
    # 2. LOCALES COMERCIALES
    col_h_loc, col_pop_loc = st.columns([4, 1])
    with col_h_loc:
        st.subheader("2. Locales Comerciales y Oficinas (P2)")
    with col_pop_loc:
        with st.popover("📖 Ver Criterio Locales"):
            st.markdown("### Criterio ITC-BT-10 (Locales Comerciales)")
            st.write("• Potencia mínima por superficie: 100 W por cada m².")
            st.write("• Suelo reglamentario absoluto: Ningún local se calculará por debajo de 3.450 W.")

    if st.button("➕ Añadir local"): 
        st.session_state.locales.append({"nombre": f"Local {len(st.session_state.locales)+1}", "superficie": 0.0, "qty": 1})
    
    pot_total_locales = 0
    for idx, loc in enumerate(st.session_state.locales):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1: loc["nombre"] = st.text_input(f"Local #{idx+1}", loc["nombre"], key=f"loc_nom_{idx}")
        with c2: loc["superficie"] = st.number_input(f"Superficie m² #{idx+1}", min_value=0.0, value=float(loc["superficie"]), key=f"loc_sup_{idx}")
        with c3: loc["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(loc["qty"]), key=f"loc_qty_{idx}")
        with c4:
            if st.button("🗑️", key=f"del_loc_{idx}"): 
                st.session_state.locales.pop(idx)
                st.rerun()

        sup_val = loc["superficie"]
        cant_loc = loc["qty"]
        pot_por_superficie = sup_val * 100.0

        if sup_val == 0:
            pot_unidad_local = 0.0
        elif pot_por_superficie < 3450.0:
            pot_unidad_local = 3450.0
        else:
            pot_unidad_local = pot_por_superficie

        pot_parcial_local = pot_unidad_local * cant_loc
        pot_total_locales += pot_parcial_local

    st.info(f"💡 **Total Parcial P2 (Locales Comerciales): {int(pot_total_locales):,} W**")
    st.markdown("---")

    # 3. SERVICIOS GENERALES
    col_h_serv, col_pop_serv = st.columns([4, 1])
    with col_h_serv:
        st.subheader("3. Servicios Generales (P3)")
    with col_pop_serv:
        with st.popover("📖 Clasificación NTE-ITA (Ascensores)"):
            st.markdown("### Tabla Oficial NTE-ITA")
            st.write("• ITA-01 (5 pers. 0.63 m/s): ~2.2 kW\n• ITA-02 (5 pers. 1.0 m/s): ~3.0 kW\n• ITA-03 (8 pers. 1.0 m/s): ~4.0 kW")

    if st.button("➕ Añadir servicio"): 
        st.session_state.servicios_generales.append({"nombre": "Nuevo Servicio", "potencia": 0, "factor": 1.30, "qty": 1})
    
    pot_total_servicios = 0
    opciones_factores_k = {
        "Ascensor Principal (K = 1.30)": 1.30,
        "Motores / Bombas (K = 1.25)": 1.25,
        "Ascensor Secundario (K = 1.15)": 1.15,
        "Servicios directos / LED (K = 1.00)": 1.00
    }

    for idx, serv in enumerate(st.session_state.servicios_generales):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: serv["nombre"] = st.text_input(f"Servicio #{idx+1}", serv["nombre"], key=f"serv_nom_{idx}")
        with c2: serv["potencia"] = st.number_input(f"Potencia W #{idx+1}", min_value=0, value=int(serv["potencia"]), key=f"serv_pot_{idx}")
        with c3: serv["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(serv["qty"]), key=f"serv_qty_{idx}")
        with c4:
            sel_opt = st.selectbox(f"Coeficiente K #{idx+1}", list(opciones_factores_k.keys()), key=f"serv_tipo_opt_{idx}")
            serv["factor"] = opciones_factores_k[sel_opt]
        with c5:
            if st.button("🗑️", key=f"del_serv_{idx}"): 
                st.session_state.servicios_generales.pop(idx)
                st.rerun()

        p_parcial_serv = int(serv["potencia"] * serv["qty"] * serv["factor"])
        pot_total_servicios += p_parcial_serv

    st.info(f"💡 **Total Parcial P3 (Servicios Generales): {pot_total_servicios:,} W**")
    st.markdown("---")

    # 4. GARAJES E IRVE
    col_h_irve, col_pop_irve = st.columns([4, 1])
    with col_h_irve:
        st.subheader("4. Garajes e IRVE (ITC-BT-52)")
    with col_pop_irve:
        with st.popover("📖 Explicación IRVE"):
            st.write("20 W/m² para garaje (mín. 3.450 W). Plazas de recarga con 3.680 W y factor de simultaneidad.")

    gc1, gc2, gc3 = st.columns(3)
    with gc1: sup_garaje = st.number_input("Sup. Garaje m²", value=0.0)
    with gc2: plazas_garaje = st.number_input("Plazas Garaje", value=0)
    with gc3: opcion_irve = st.selectbox("Sistema de Recarga IRVE", ["Sin SPL [Factor = 1.0]", "Con SPL [Factor = 0.1]"])

    pot_garaje_por_sup = sup_garaje * 20.0
    pot_garaje_adjudicada = max(pot_garaje_por_sup, 3450.0 if sup_garaje > 0 else 0.0)
    fsim_ve = 1.0 if "Sin" in opcion_irve else 0.1
    pot_total_irve = int(round(plazas_garaje * 0.1 * 3680 * fsim_ve))
    pot_total_garaje_irve = int(pot_garaje_adjudicada) + pot_total_irve

    st.markdown("---")
    pt_total = pot_total_viviendas + int(pot_total_locales) + pot_total_servicios + int(pot_garaje_adjudicada) + pot_total_irve

    st.markdown(f"""
        <div class="resumen-parciales-box">
            <h3 style="color: #111; margin-top: 0;">📋 RESUMEN DE POTENCIAS PARCIALES Y TOTALES (ITC-BT-10)</h3>
            <ul>
                <li><b>P1 (Viviendas - {total_viviendas_edificio} uds):</b> {pot_total_viviendas:,} W</li>
                <li><b>P2 (Locales Comerciales):</b> {int(pot_total_locales):,} W</li>
                <li><b>P3 (Servicios Generales):</b> {pot_total_servicios:,} W</li>
                <li><b>P4 (Garaje):</b> {int(pot_garaje_adjudicada):,} W</li>
                <li><b>P5 (IRVE):</b> {pot_total_irve:,} W</li>
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
    
    with st.expander("🏗️ Selector de Sistema de Instalación y Material", expanded=True):
        metodo_lga_key = st.selectbox("Método de Instalación recomendado:", list(METODOS_INSTALACION.keys()), key="met_lga")
        tipo_enlace_lga = st.radio("Modelo de esquema reglamentario para la LGA:", [
            "Modelo 1: Contadores totalmente concentrados (Límite CDT = 0.5%)",
            "Modelo 2: Centralizaciones parciales distribuidas (Límite CDT = 1.0%)"
        ], key="enlace_lga")

    dv_pct_lga = 0.5 if "Modelo 1" in tipo_enlace_lga else 1.0

    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        lga_pot = float(pt_total)
        st.metric("Potencia de cálculo LGA (W) [Automática desde Previsión]", f"{lga_pot:,.2f} W")
        lga_long = st.number_input("Longitud de la LGA (m)", value=float(st.session_state.lga_long_val), key="lga_l")
        st.session_state.lga_long_val = lga_long
        lga_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="lga_mat")
    with lga_c2:
        lga_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="lga_ais")
        lga_cos = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.9, key="lga_cos")
        lga_icc_orig = st.number_input("Icc en el origen (kA)", value=15.0, key="lga_icc")

    if lga_pot <= 0 or lga_long <= 0:
        st.warning("⚠️ Introduce potencia y longitud válidas.")
    else:
        gamma_lga = GAMMA_MAP.get((lga_mat, lga_aisl), 44.0)
        ib_lga = lga_pot / (math.sqrt(3) * 400 * lga_cos) if lga_cos > 0 else 0.0
        dv_max_lga = 400 * (dv_pct_lga / 100.0)
        s_cdt_lga = (lga_pot * lga_long) / (gamma_lga * dv_max_lga * 400) if dv_max_lga > 0 and gamma_lga > 0 else 0.0
        
        s_cal_lga = 1.5
        for sec, iz_val in IZ_COBRE_TUBO.items():
            if iz_val >= ib_lga:
                s_cal_lga = sec
                break

        min_reg_lga = 10.0 if lga_mat == "cobre" else 16.0
        s_bruta_lga = max(s_cdt_lga, s_cal_lga, min_reg_lga)
        s_optima_lga = seleccionar_seccion_optima(s_bruta_lga)

        r_lga = (0.018 * lga_long) / s_optima_lga if s_optima_lga > 0 else 0.0
        z_lga_tot = (400 / (lga_icc_orig * 1000)) + (2 * r_lga) if lga_icc_orig > 0 else 1.0
        icc_fin_lga = 400 / z_lga_tot / 1000 if z_lga_tot > 0 else 0
        prot_lga = seleccionar_proteccion(ib_lga)

        dv_real_lga_v = (lga_pot * lga_long) / (gamma_lga * s_optima_lga * 400) if gamma_lga > 0 and s_optima_lga > 0 else 0.0
        dv_real_lga_pct = (dv_real_lga_v / 400) * 100

        st.markdown("---")
        st.subheader("📋 Memoria de Justificación Técnica y Criterio de Selección (LGA)")
        
        # JUSTIFICACIÓN TÉCNICA LIMPIA CON MARKDOWN NATIVO (SIN HTML RARO)
        st.markdown(f"""
        **1. Cálculo de la Intensidad de Diseño ($I_b$):**  
        Para una red trifásica, la corriente se calcula mediante la fórmula:  
        $$I_b = \\frac{{P}}{{\\sqrt{3} \\cdot V \\cdot \\cos\\varphi}} = \\frac{{{lga_pot:,.2f}}}{{\\sqrt{3} \\cdot 400 \\cdot {lga_cos}}} = **{ib_lga:.2f}\\text{ A}$$

        **2. Criterio de Calentamiento ($I_z \\ge I_b$):**  
        El conductor debe soportar al menos la corriente de diseño. Según tablas para **{lga_mat.upper()}** en tubo (**{lga_aisl}**), se requiere una sección térmica mínima de **{s_cal_lga} mm²**.

        **3. Criterio de Caída de Tensión ($\\Delta U \\le {dv_pct_lga}\\%$):**  
        Aplicando la fórmula analítica trifásica de caída de tensión:  
        $$S = \\frac{{P \\cdot L}}{{\\gamma \\cdot \\Delta U \\cdot V}} = \\frac{{{lga_pot:,.2f} \\cdot {lga_long}}}{{{gamma_lga} \\cdot {dv_max_lga} \\cdot 400}} = **{s_cdt_lga:.2f}\\text{{ mm²}}$$

        **4. Lógica de Descarte y Selección de la Sección Óptima:**  
        * Se **descartan** las secciones comerciales inferiores que no cumplan con el límite de caída de tensión del {dv_pct_lga}% o el mínimo reglamentario de **{min_reg_lga} mm²** (exigido por ITC-BT-14).  
        * Se adopta definitivamente **{s_optima_lga} mm²** de **{lga_mat.upper()} ({lga_aisl})**, logrando una caída de tensión real del **{dv_real_lga_pct:.3f}%**.
        """)

        st.markdown(f"""
            <div class="resultado-destacado">
                ⚡ SECCIÓN A ADOPTAR (LGA): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_lga} mm²</span> de {lga_mat.upper()} ({lga_aisl})<br>
                <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
                Justificación Analítica: S CDT = <b>{s_cdt_lga:.2f} mm²</b> | Calentamiento = <b>{s_cal_lga} mm²</b> | Mínimo REBT = <b>{min_reg_lga} mm²</b>. Protección: {prot_lga} A.
                </span>
            </div>
        """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 3: DERIVACIÓN INDIVIDUAL
# =========================================================================
with pestanas[2]:
    st.title("Derivación Individual - DI (ITC-BT-15)")
    
    with st.expander("🏗️ Selector de Sistema de Instalación y Material", expanded=True):
        metodo_di_key = st.selectbox("Método de Instalación recomendado:", list(METODOS_INSTALACION.keys()), key="met_di")
        tipo_enlace_di = st.radio("Modelo de esquema para la Derivación Individual:", [
            "Modelo A: DI desde contadores concentrados (Límite CDT = 1.0%)",
            "Modelo B: DI desde contadores diseminados / exteriores (Límite CDT = 0.5%)"
        ], key="enlace_di")

    dv_pct_di = 1.0 if "Modelo A" in tipo_enlace_di else 0.5

    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Potencia de la Derivación (W)", [5750, 7360, 9200, 11500], key="di_p")
        di_long = st.number_input("Longitud de la DI (m)", value=float(st.session_state.di_long_val), key="di_l")
        st.session_state.di_long_val = di_long
        di_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="di_mat")
    with di_c2:
        di_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="di_ais")
        di_cos = st.slider("Coseno phi (cos phi)", 0.8, 1.0, 1.0, key="di_cos")

    if di_long <= 0:
        st.warning("⚠️ Introduce una longitud válida para la DI.")
    else:
        gamma_di = GAMMA_MAP.get((di_mat, di_aisl), 44.0)
        ib_di = di_pot / (230 * di_cos) if di_cos > 0 else 0.0
        dv_max_di = 230 * (dv_pct_di / 100.0)
        s_cdt_di = (2 * di_pot * di_long) / (gamma_di * dv_max_di * 230) if dv_max_di > 0 and gamma_di > 0 else 0.0
        
        s_cal_di = 1.5
        for sec, iz_val in IZ_COBRE_TUBO.items():
            if iz_val >= ib_di:
                s_cal_di = sec
                break

        min_reg_di = 6.0 if di_mat == "cobre" else 10.0
        s_bruta_di = max(s_cdt_di, s_cal_di, min_reg_di)
        s_optima_di = seleccionar_seccion_optima(s_bruta_di)

        r_di = (0.018 * di_long) / s_optima_di if s_optima_di > 0 else 0.0
        z_di_tot = (230 / 10000) + (2 * r_di)
        icc_fin_di = 230 / z_di_tot / 1000 if z_di_tot > 0 else 0
        prot_di = seleccionar_proteccion(ib_di)

        dv_real_di_v = (2 * di_pot * di_long) / (gamma_di * s_optima_di * 230) if gamma_di > 0 and s_optima_di > 0 else 0.0
        dv_real_di_pct = (dv_real_di_v / 230) * 100

        st.markdown("---")
        st.subheader("📋 Memoria de Justificación Técnica y Criterio de Selección (DI)")
        
        # JUSTIFICACIÓN TÉCNICA LIMPIA CON MARKDOWN NATIVO (SIN HTML RARO)
        st.markdown(f"""
        **1. Cálculo de la Intensidad de Diseño ($I_b$ monofásica):**  
        Para una derivación monofásica, la corriente se calcula mediante la fórmula:  
        $$I_b = \\frac{{P}}{{V \\cdot \\cos\\varphi}} = \\frac{{{di_pot}}}{{230 \\cdot {di_cos}}} = **{ib_di:.2f}\\text{ A}$$

        **2. Criterio de Calentamiento ($I_z \\ge I_b$):**  
        El conductor debe soportar al menos la corriente de diseño. Según tablas para **{di_mat.upper()}** en tubo (**{di_aisl}**), se requiere una sección térmica mínima de **{s_cal_di} mm²**.

        **3. Criterio de Caída de Tensión ($\\Delta U \\le {dv_pct_di}\\%$):**  
        Aplicando la fórmula analítica monofásica de caída de tensión:  
        $$S = \\frac{{2 \\cdot P \\cdot L}}{{\\gamma \\cdot \\Delta U \\cdot V}} = \\frac{{2 \\cdot {di_pot} \\cdot {di_long}}}{{{gamma_di} \\cdot {dv_max_di} \\cdot 230}} = **{s_cdt_di:.2f}\\text{{ mm²}}$$

        **4. Lógica de Descarte y Selección de la Sección Óptima:**  
        * Se **descartan** las secciones comerciales inferiores que no alcancen el valor analítico de caída de tensión requerido o el mínimo reglamentario de **{min_reg_di} mm²** (exigido por ITC-BT-15 para viviendas).  
        * Se adopta definitivamente **{s_optima_di} mm²** de **{di_mat.upper()} ({di_aisl})**, logrando una caída de tensión real del **{dv_real_di_pct:.3f}%**.
        """)

        st.markdown(f"""
            <div class="resultado-destacado">
                🔌 SECCIÓN A ADOPTAR (DI): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_di} mm²</span> de {di_mat.upper()} ({di_aisl})<br>
                <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
                Justificación Analítica: S CDT = <b>{s_cdt_di:.2f} mm²</b> | Calentamiento = <b>{s_cal_di} mm²</b> | Mínimo REBT = <b>{min_reg_di} mm²</b>. PIA: {prot_di} A.
                </span>
            </div>
        """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 4: TABLA GUÍA ESTILO PLC MADRID
# =========================================================================
with pestanas[3]:
    st.title("📊 Tablas de Cálculo Directo Estilo PLC Madrid (ITC-BT-15)")
    st.write("Consulta horizontal rápida y orientativa de longitudes máximas admisibles para Derivaciones Individuales:")
    tabla_plc_data = [
        {"Sección Mín": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "6 m", "32A (7.32 kW)": "13 m", "40A (9.20 kW)": "10 m", "50A (11.5 kW)": "8 m"},
        {"Sección Mín": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "11 m", "32A (7.32 kW)": "26 m", "40A (9.20 kW)": "20 m", "50A (11.5 kW)": "16 m"},
        {"Sección Mín": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "11 m", "32A (7.32 kW)": "22 m", "40A (9.20 kW)": "17 m", "50A (11.5 kW)": "14 m"},
        {"Sección Mín": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "22 m", "32A (7.32 kW)": "44 m", "40A (9.20 kW)": "34 m", "50A (11.5 kW)": "27 m"}
    ]
    st.dataframe(tabla_plc_data, use_container_width=True)

# =========================================================================
# PESTAÑA 5: CÁLCULO RÁPIDO
# =========================================================================
with pestanas[4]:
    st.title("🧮 Ventana de Cálculo Rápido")
    rc1, rc2 = st.columns(2)
    with rc1:
        modo_carga = st.radio("Modo de entrada:", ["Por Potencia (W)", "Por Intensidad Directa (A)"], key="mod_q")
        if modo_carga == "Por Potencia (W)":
            val_pot_q = st.number_input("Potencia (W)", value=5000.0, key="vp_q")
            tipo_red_q = st.selectbox("Red", ["Monofásica (230V)", "Trifásica (400V)"], key="tr_q1")
            cos_q = st.slider("Coseno phi", 0.7, 1.0, 0.9, key="cos_q")
            ib_q = val_pot_q / (230 * cos_q) if "Monofásica" in tipo_red_q else val_pot_q / (math.sqrt(3) * 400 * cos_q)
        else:
            ib_q = st.number_input("Intensidad Ib (A)", value=25.0, key="ib_q1")
            tipo_red_q = st.selectbox("Red", ["Monofásica (230V)", "Trifásica (400V)"], key="tr_q2")
            val_pot_q = ib_q * 230 if "Monofásica" in tipo_red_q else ib_q * math.sqrt(3) * 400 * 0.9

        long_q = st.number_input("Longitud (m)", value=20.0, key="l_q")

    with rc2:
        metodo_q_key = st.selectbox("Método:", list(METODOS_INSTALACION.keys()), key="met_q")
        mat_q = st.selectbox("Material", ["cobre", "aluminio"], key="m_q")
        ais_q = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="a_q")
        cdt_lim_q = st.number_input("CDT máx (%)", value=3.0, key="cdt_q")
        icc_orig_q = st.number_input("Icc origen (kA)", value=10.0, key="icc_orig_q")

    gamma_q = GAMMA_MAP.get((mat_q, ais_q), 44.0)
    v_nominal_q = 230 if "Monofásica" in tipo_red_q else 400
    dv_max_q = v_nominal_q * (cdt_lim_q / 100.0)
    s_cdt_q = (2 * val_pot_q * long_q) / (gamma_q * dv_max_q * v_nominal_q) if "Monofásica" in tipo_red_q else (val_pot_q * long_q) / (gamma_q * dv_max_q * v_nominal_q)

    s_cal_q = 1.5
    for sec, iz_val in IZ_COBRE_TUBO.items():
        if iz_val >= ib_q:
            s_cal_q = sec
            break

    s_opt_q = seleccionar_seccion_optima(max(s_cdt_q, s_cal_q))
    r_q = (0.018 * long_q) / s_opt_q
    z_tot_q = (v_nominal_q / (icc_orig_q * 1000)) + (2 * r_q) if "Monofásica" in tipo_red_q else (v_nominal_q / (icc_orig_q * 1000)) + r_q
    icc_fin_q = v_nominal_q / z_tot_q / 1000 if z_tot_q > 0 else 0
    prot_q = seleccionar_proteccion(ib_q)

    st.markdown(f"""
        <div class="resultado-destacado">
            🧮 SECCIÓN ÓPTIMA: <span style="color: #ff4b4b; font-size: 24px;">{s_opt_q} mm²</span> de {mat_q.upper()} ({ais_q})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">Protección: {prot_q} A | Icc final: {icc_fin_q:.2f} kA</span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 6: ESQUEMAS UNIFILARES
# =========================================================================
with pestanas[5]:
    st.title("📐 Esquema Unifilar")
    esquema_simbolos_txt = f"""
==========================================================================================
PROYECTO: {st.session_state.nombre_proyecto}
TITULAR: {st.session_state.cliente_actual['nombre']} - BOLIMUR INSTALACIONES INTEGRALES
==========================================================================================
   [ DI ] ──────────────── [ IGA ] ─────────────── [ SOBRETENSIONES ] ────────────── [ ID ]
   10 mm² Cu               25 A                     Transitorias +           40 A, 30 mA
==========================================================================================
"""
    st.markdown(f'<div class="esquema-simbolos">{esquema_simbolos_txt}</div>', unsafe_allow_html=True)
    st.download_button("📥 Descargar Esquema (.txt)", data=esquema_simbolos_txt, file_name="Esquema_Simbolos.txt", mime="text/plain")

# =========================================================================
# PESTAÑA 7: ASISTENTE DE BOLETINES
# =========================================================================
with pestanas[6]:
    st.title("📝 Asistente de Generación de Boletines Oficiales")
    st.markdown(f"""
    <div class="boletin-box">
        <h3 style="color: #ff4b4b; margin-top: 0;">⚡ CERTIFICADO DE INSTALACIÓN ELÉCTRICA (CIE)</h3>
        <p><b>Titular:</b> {st.session_state.cliente_actual['nombre']} | <b>NIF:</b> {st.session_state.cliente_actual['nif']}</p>
        <p><b>Empresa Instaladora:</b> {perfil_guardado["empresa"]} | <b>Carné:</b> {perfil_guardado["carnet"]}</p>
        <p><b>Potencia Total:</b> {pt_total:,} W</p>
    </div>
    """, unsafe_allow_html=True)

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
        <p>Potencia Total Prevista: <b>{pt_total:,} W</b> ({pt_total/1000:,.2f} kW)</p>
    </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 9: INFORME TÉCNICO MTD
# =========================================================================
with pestanas[8]:
    st.title("📄 Informe Técnico Formal MTD")
    informe_txt = f"PROYECTO: {st.session_state.nombre_proyecto}\nPt: {pt_total:,} W"
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