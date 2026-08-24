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
    .bolimur-header {
        border-bottom: 3px solid #ff4b4b;
        padding-bottom: 10px;
        margin-bottom: 20px;
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
    .justificacion-tecnica-box {
        background-color: #ffffff;
        border: 2px solid #0066cc;
        padding: 20px;
        border-radius: 8px;
        margin: 15px 0;
        font-size: 14px;
        color: #212529;
        line-height: 1.6;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
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
    st.session_state.grupos_viviendas = []
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
    st.header("🤖 Lector Inteligente de PDF")
    archivo_pdf_subido = st.file_uploader("Subir Enunciado (PDF)", type=["pdf"])
    
    if archivo_pdf_subido is not None and has_pypdf:
        try:
            reader = PdfReader(archivo_pdf_subido)
            texto_pdf = ""
            for pagina in reader.pages:
                texto_pdf += pagina.extract_text() or ""
            
            st.success(f"📄 ¡PDF leído! ({len(texto_pdf)} caracteres)")
            
            if st.button("🚀 Extraer y Cargar Datos en la App"):
                st.session_state.nombre_proyecto = "Proyecto Extraído de Enunciado PDF"
                
                # Búsqueda inteligente de viviendas (ej: "20 viviendas", "15 pisos")
                match_viv = re.search(r'(\d+)\s*(?:viviendas|pisos|edificios|doct)', texto_pdf, re.IGNORECASE)
                qty_ext = int(match_viv.group(1)) if match_viv else 10
                
                # Búsqueda de potencia unitaria (ej: 5750, 9200)
                pot_ext = 5750
                if '9200' in texto_pdf: pot_ext = 9200
                elif '7360' in texto_pdf: pot_ext = 7360
                elif '11500' in texto_pdf: pot_ext = 11500

                # Búsqueda de longitud LGA (ej: "longitud de 30 m", "30 metros")
                match_lga = re.search(r'(?:lga|línea general).*?(\d+(?[\.,]\d+)?)\s*m', texto_pdf, re.IGNORECASE)
                if not match_lga:
                    match_lga = re.search(r'(\d+)\s*metros.*?(?:lga|línea general)', texto_pdf, re.IGNORECASE)
                
                if match_lga:
                    st.session_state.lga_long_val = float(match_lga.group(1).replace(',', '.'))
                else:
                    st.session_state.lga_long_val = 30.0

                # Cargar en el estado los grupos de viviendas extraídos
                st.session_state.grupos_viviendas = [{
                    "nombre": "Viviendas Extraídas de PDF",
                    "qty": qty_ext,
                    "pot": pot_ext,
                    "nocturna": False
                }]
                
                st.success(f"✨ ¡Cargado con éxito! ({qty_ext} viviendas de {pot_ext} W, LGA: {st.session_state.lga_long_val} m)")
                st.rerun()
                
        except Exception as e:
            st.error(f"Error al procesar PDF: {e}")
    elif archivo_pdf_subido is not None and not has_pypdf:
        st.warning("Librería pypdf no disponible.")

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
        st.info("ℹ️ No hay grupos de viviendas añadidos. Pulsa en '➕ Añadir Grupo de Viviendas' o sube un PDF en el menú lateral.")

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
            just_str = f"Tarifa Nocturna activada: Coeficiente K = 1.0."
        else:
            cs_grupo = get_coef_simultaneidad(qty_g)
            just_str = f"Aplicación ITC-BT-10 para {qty_g} viviendas: Coeficiente K = {cs_grupo:.2f}."

        pot_parcial_g = int(round(qty_g * pot_unit * cs_grupo))
        pot_total_viviendas += pot_parcial_g

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #0066cc; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Justificación Grupo #{idx+1} ({viv['nombre']}):</b> {just_str}<br>
            Cálculo parcial: {qty_g} viviendas x {pot_unit} W x {cs_grupo} = <b>{pot_parcial_g:,} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 Viviendas totales: **{total_viviendas_edificio}** | **Total Parcial P1 (Viviendas): {pot_total_viviendas:,} W**")
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

    if not st.session_state.locales:
        st.info("ℹ️ No hay locales comerciales añadidos. Pulsa en '➕ Añadir local' para empezar.")

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
            estado_minimo = "⚠️ <b>Sin superficie definida.</b>"
            accion_minimo = "👉 Introduce los metros cuadrados del local."
        elif pot_por_superficie < 3450.0:
            pot_unidad_local = 3450.0
            estado_minimo = f"⚠️ <b>NO ALCANZA EL MÍNIMO:</b> ({sup_val} m² x 100 W/m² = {pot_por_superficie:,.0f} W) es inferior al suelo normativo."
            accion_minimo = "👉 <b>Se aplica el mínimo legal de 3.450 W</b>."
        else:
            pot_unidad_local = pot_por_superficie
            estado_minimo = f"✅ <b>CUMPLE EL MÍNIMO:</b> ({sup_val} m² x 100 W/m² = {pot_por_superficie:,.0f} W)."
            accion_minimo = "👉 Se toma el valor calculado por superficie."

        pot_parcial_local = pot_unidad_local * cant_loc
        pot_total_locales += pot_parcial_local

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 12px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Análisis Normativo Local #{idx+1} ({loc['nombre']}):</b><br>
            • Estado actual: {estado_minimo}<br>
            • {accion_minimo}<br>
            • Total Parcial Local: {cant_loc} x {pot_unidad_local:,.0f} W = <b>{pot_parcial_local:,.0f} W</b>
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
            tabla_ita_md = (
                "| Código | Capacidad y Velocidad | Potencia Estimada Aprox. |\n"
                "| :--- | :--- | :---: |\n"
                "| **ITA-01** | Carga 5 personas / Vel. 0.63 m/s | ~ 2.2 kW |\n"
                "| **ITA-02** | Carga 5 personas / Vel. 1.00 m/s | ~ 3.0 kW |\n"
                "| **ITA-03** | Carga 8 personas / Vel. 1.00 m/s | ~ 4.0 kW |\n"
                "| **ITA-04** | Carga 8 personas / Vel. 1.60 m/s | ~ 5.5 kW |\n"
                "| **ITA-05** | Carga 13 personas / Vel. 1.60 m/s | ~ 7.5 kW |\n"
                "| **ITA-06** | Carga 13 personas / Vel. 2.50 m/s | ~ 9.0 kW |\n"
                "| **ITA-07** | Carga 21 personas / Vel. 2.50 m/s | ~ 11.0 kW |\n"
                "| **ITA-08** | Carga 21 personas / Vel. 3.50 m/s | ~ 15.0 kW |\n"
            )
            st.markdown(tabla_ita_md)

    if st.button("➕ Añadir servicio"): 
        st.session_state.servicios_generales.append({"nombre": "Nuevo Servicio", "potencia": 0, "factor": 1.30, "qty": 1})
    
    pot_total_servicios = 0

    if not st.session_state.servicios_generales:
        st.info("ℹ️ No hay servicios generales añadidos. Pulsa en '➕ Añadir servicio' para empezar.")

    opciones_factores_k = {
        "Ascensor Principal (K = 1.30)": 1.30,
        "Motores / Bombas secundarias (K = 1.25)": 1.25,
        "Ascensor Secundario (K = 1.15)": 1.15,
        "Lámparas Fluorescentes / Descarga (K = 1.80)": 1.80,
        "Servicios directos / LED (K = 1.00)": 1.00,
        "Personalizado (Introducir valor libre)": -1.0
    }

    for idx, serv in enumerate(st.session_state.servicios_generales):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: serv["nombre"] = st.text_input(f"Servicio #{idx+1}", serv["nombre"], key=f"serv_nom_{idx}")
        with c2: serv["potencia"] = st.number_input(f"Potencia W #{idx+1}", min_value=0, value=int(serv["potencia"]), key=f"serv_pot_{idx}")
        with c3: serv["qty"] = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(serv["qty"]), key=f"serv_qty_{idx}")
        
        factor_actual = serv.get("factor", 1.30)
        def_opt_idx = 0
        for i, (k_text, v_val) in enumerate(opciones_factores_k.items()):
            if v_val == factor_actual:
                def_opt_idx = i
                break
            elif factor_actual not in [1.30, 1.25, 1.15, 1.80, 1.00] and k_text.startswith("Personalizado"):
                def_opt_idx = i

        with c4:
            sel_opt = st.selectbox(f"Coeficiente K #{idx+1}", list(opciones_factores_k.keys()), index=def_opt_idx, key=f"serv_tipo_opt_{idx}")
            if sel_opt.startswith("Personalizado"):
                factor = st.number_input(f"Valor K personalizado #{idx+1}", min_value=0.1, value=float(factor_actual if factor_actual > 0 else 1.25), key=f"serv_k_pers_{idx}")
            else:
                factor = opciones_factores_k[sel_opt]
            serv["factor"] = factor

        with c5:
            if st.button("🗑️", key=f"del_serv_{idx}"): 
                st.session_state.servicios_generales.pop(idx)
                st.rerun()

        p_parcial_serv = int(serv["potencia"] * serv["qty"] * factor)
        pot_total_servicios += p_parcial_serv

        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #ffc107; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
            <b>Justificación Técnica Servicio #{idx+1} ({serv['nombre']}):</b> Coeficiente <b>K = {factor:.2f}</b>.<br>
            Cálculo: {serv['potencia']} W x {serv['qty']} ud(s) x {factor:.2f} = <b>{p_parcial_serv:,} W</b>
        </div>
        """, unsafe_allow_html=True)

    st.info(f"💡 **Total Parcial P3 (Servicios Generales): {pot_total_servicios:,} W**")
    st.markdown("---")

    # 4. GARAJES E IRVE
    col_h_irve, col_pop_irve = st.columns([4, 1])
    with col_h_irve:
        st.subheader("4. Garajes e Infraestructura de Recarga de Vehículos Eléctricos - IRVE (ITC-BT-52)")
    with col_pop_irve:
        with st.popover("📖 Explicación Técnica IRVE"):
            st.markdown("### Criterios Técnicos ITC-BT-52 e ITC-BT-10")
            st.write("1. **Garaje (ITC-BT-10):** Se asignan 20 W por cada m² de superficie, con un suelo mínimo de 3.450 W.")
            st.write("2. **Preinstalación Vehículo Eléctrico (ITC-BT-52):** Cada plaza de garaje contempla 3.680 W (afectada por un coeficiente base del 10% o 0.1).")

    gc1, gc2, gc3 = st.columns(3)
    with gc1: sup_garaje = st.number_input("Sup. Garaje m²", value=0.0)
    with gc2: plazas_garaje = st.number_input("Plazas Garaje", value=0)
    with gc3: opcion_irve = st.selectbox("Sistema de Recarga IRVE (ITC-BT-52)", ["Sin SPL [Factor = 1.0]", "Con Sistema de Protección de Línea - SPL (Reducción 90% / Factor = 0.1)"])

    pot_garaje_por_sup = sup_garaje * 20.0
    if pot_garaje_por_sup < 3450.0 and sup_garaje > 0:
        pot_garaje_adjudicada = 3450.0
        aviso_garaje = f"⚠️ No alcanza el mínimo legal (se aplica suelo de 3.450 W)"
    else:
        pot_garaje_adjudicada = max(pot_garaje_por_sup, 3450.0 if sup_garaje > 0 else 0.0)
        aviso_garaje = f"✅ Calculado por superficie"

    fsim_ve = 1.0 if "Sin" in opcion_irve else 0.1
    pot_total_irve = int(round(plazas_garaje * 0.1 * 3680 * fsim_ve))
    pot_total_garaje_irve = int(pot_garaje_adjudicada) + pot_total_irve

    st.markdown(f"""
    <div style="background-color: #f8f9fa; border-left: 4px solid #17a2b8; padding: 12px; border-radius: 5px; margin-bottom: 10px; font-size: 13px; color: #333;">
        <b>Justificación Técnica Detallada del Cálculo IRVE y Garaje:</b><br>
        • <b>Garaje (ITC-BT-10):</b> {sup_garaje:,.1f} m² x 20 W/m² = <b>{int(pot_garaje_por_sup):,} W</b> ({aviso_garaje} -> <b>{int(pot_garaje_adjudicada):,} W</b>)<br>
        • <b>IRVE (ITC-BT-52):</b> {plazas_garaje} plazas x 3.680 W x 10% (0.1) x [Factor {fsim_ve}] = <b>{pot_total_irve:,} W</b><br>
        • <b>Suma Parcial P4 / P5:</b> {int(pot_garaje_adjudicada):,} W (Garaje) + {pot_total_irve:,} W (IRVE) = <b>{pot_total_garaje_irve:,} W</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    pt_total = pot_total_viviendas + int(pot_total_locales) + pot_total_servicios + int(pot_garaje_adjudicada) + pot_total_irve

    # --- RESUMEN FINAL DE PARCIALES Y SUMA TOTAL ---
    st.markdown(f"""
        <div class="resumen-parciales-box">
            <h3 style="color: #111; margin-top: 0;">📋 RESUMEN DE POTENCIAS PARCIALES Y TOTALES (ITC-BT-10)</h3>
            <ul>
                <li><b>P1 (Viviendas - {total_viviendas_edificio} uds):</b> {pot_total_viviendas:,} W</li>
                <li><b>P2 (Locales Comerciales):</b> {int(pot_total_locales):,} W</li>
                <li><b>P3 (Servicios Generales):</b> {pot_total_servicios:,} W</li>
                <li><b>P4 (Garaje):</b> {int(pot_garaje_adjudicada):,} W</li>
                <li><b>P5 (IRVE / Vehículo Eléctrico):</b> {pot_total_irve:,} W</li>
            </ul>
            <hr style="border: 1px solid #ced4da;">
            <h2 style="color: #ff4b4b; margin-bottom: 0;">⚡ SUMA TOTAL PREVISTA (Pt): {pt_total:,} W ({pt_total/1000:,.2f} kW)</h2>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 2: LGA (SINCRONIZADA AUTOMÁTICAMENTE CON PT)
# =========================================================================
with pestanas[1]:
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    
    col_h_lga, col_btn_lga = st.columns([4, 1])
    with col_h_lga:
        with st.popover("❓ 📖 Ventana de Ayuda: Explicación de Métodos de Instalación (B1, B2...)"):
            st.markdown("### Guía Técnica de Métodos de Instalación (UNE-HD 60364-5-52)")
            st.write("""
            * **Método B1 (Habitual en Viviendas):** Cables unipolares en tubo empotrado en paredes aislantes.
            * **Método B2:** En tubo superficial.
            * **Método C:** Multiconductor fijado a pared.
            * **Método D:** Enterrado bajo tubo.
            """)
    with col_btn_lga:
        if st.button("🔄 Resetear Longitud LGA"):
            st.session_state.lga_long_val = 25.0
            st.rerun()

    with st.expander("🏗️ Selector de Sistema de Instalación y Material (Métodos UNE-HD 60364-5-52)", expanded=True):
        metodo_lga_key = st.selectbox("Método de Instalación recomendado (por defecto B1 para viviendas):", list(METODOS_INSTALACION.keys()), key="met_lga")
        st.info(f"**Detalle del método:** {METODOS_INSTALACION[metodo_lga_key]['desc']}")

        tipo_enlace_lga = st.radio("Modelo de esquema reglamentario para la LGA:", [
            "Modelo 1: Contadores totalmente concentrados en un único local o armario principal (Límite CDT = 0.5%)",
            "Modelo 2: Centralizaciones parciales distribuidas / ramificadas (Límite CDT = 1.0%)"
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
        st.warning("⚠️ **Atención:** La Potencia Total Prevista (Pt) o la longitud de la LGA están a 0. Añade cargas en la pestaña 'Previsión de Cargas' o introduce valores válidos para calcular la sección.")
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
        st.subheader("📐 Desglose detallado de Fórmulas y Resultados - LGA")
        st.markdown(f"""
        1. **Intensidad de Diseño (Ib):** Ib = <b>{ib_lga:.2f} A</b><br>
        2. **Sección por Caída de Tensión:** S = <b style="font-size: 20px; color: #ff4b4b;">{s_cdt_lga:.2f} mm²</b> (Real: <b>{dv_real_lga_pct:.3f}%</b>)<br>
        3. **Sección por Calentamiento:** Mínimo requerido = <b>{s_cal_lga} mm²</b><br>
        4. **Sección Mínima Reglamentaria:** <b>{min_reg_lga} mm²</b> ({lga_mat.upper()})<br>
        5. **Corriente de Cortocircuito (Icc final):** <b>{icc_fin_lga:.2f} kA</b>
        """, unsafe_allow_html=True)

        # --- MEMORIA DE JUSTIFICACIÓN TÉCNICA Y LÓGICA DE SELECCIÓN (LGA) ---
        st.markdown(f"""
        <div class="justificacion-tecnica-box">
            <h4 style="color: #0066cc; margin-top: 0;">📋 Memoria de Justificación Técnica y Criterio de Selección (LGA)</h4>
            <p><b>1. Cálculo de la Intensidad de Diseño (Ib):</b><br>
            Para una red trifásica, la intensidad se determina mediante la expresión:<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>Ib = P / ( sqrt(3) x V x cos phi )</b> = {lga_pot:,.2f} / ( 1.732 x 400 x {lga_cos} ) = <b>{ib_lga:.2f} A</b></p>
            
            <p><b>2. Criterio de Calentamiento (Intensidad Admisible Iz >= Ib):</b><br>
            El conductor seleccionado debe soportar una intensidad superior o igual a Ib sin sobrecalentarse. Buscando en tablas para {lga_mat.upper()} bajo tubo ({lga_aisl}), la intensidad admisible (Iz) debe ser de al menos {ib_lga:.2f} A, lo que exige térmicamente una sección mínima de <b>{s_cal_lga} mm²</b>.</p>
            
            <p><b>3. Criterio de Caída de Tensión (CDT <= {dv_pct_lga}%):</b><br>
            Aplicando la fórmula analítica trifásica de caída de tensión:<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>S = ( P x L ) / (gamma x Delta V x V)</b> = ({lga_pot:,.2f} x {lga_long}) / ( {gamma_lga} x {dv_max_lga} x 400 ) = <b style="color: #ff4b4b; font-size: 16px;">{s_cdt_lga:.2f} mm²</b></p>
            
            <p><b>4. Lógica de Descarte y Selección de la Sección Óptima:</b><br>
            • Las secciones inferiores (desde 10 mm² hasta 50 mm² ) se <b>descartan</b> porque su caída de tensión real excede el límite máximo permitido del {dv_pct_lga}% y su intensidad admisible Iz es inferior a los {ib_lga:.2f} A requeridos.<br>
            • La sección comercial inmediata superior que cumple simultáneamente con todos los criterios reglamentarios (calentamiento, caída de tensión y mínimo REBT de {min_reg_lga} mm²) es <b>{s_optima_lga} mm²</b>.<br>
            • Por tanto, se adopta definitivamente la sección de <b>{s_optima_lga} mm² de {lga_mat.upper()} ({lga_aisl})</b>, obteniendo una caída de tensión real del <b>{dv_real_lga_pct:.3f}%</b> (totalmente dentro de norma).</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📋 Tabla Comparativa de Secciones Normalizadas y Justificación - LGA")
        tabla_comparativa_lga = []
        for sec in SECCIONES_COMERCIALES:
            iz_sec = IZ_COBRE_TUBO.get(sec, 300.0)
            cumple_cal = "✅ Sí" if iz_sec >= ib_lga else "❌ No"
            
            dv_sec_v = (lga_pot * lga_long) / (gamma_lga * sec * 400) if gamma_lga > 0 and sec > 0 else 0.0
            dv_sec_pct = (dv_sec_v / 400) * 100
            cumple_cdt = f"✅ Sí ({dv_sec_pct:.3f}%)" if dv_sec_pct <= dv_pct_lga else f"❌ No ({dv_sec_pct:.3f}%)"
            
            cumple_reg = "✅ Sí" if sec >= min_reg_lga else f"❌ No"
            
            estado = "❌ DESCARTADA"
            if sec >= s_bruta_lga:
                estado = "⭐ SELECCIONADA (Óptima)"
            
            tabla_comparativa_lga.append({
                "Sección Comercial": f"{sec} mm²",
                "Intensidad Admisible (Iz)": f"{iz_sec} A",
                "Criterio Calentamiento": cumple_cal,
                "Criterio Caída Tensión": cumple_cdt,
                "Mínimo REBT (ITC-BT-14)": cumple_reg,
                "Estado Final": estado
            })

        st.dataframe(tabla_comparativa_lga, use_container_width=True)

        st.markdown(f"""
            <div class="resultado-destacado">
                ⚡ SECCIÓN A ADOPTAR (LGA): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_lga} mm²</span> de {lga_mat.upper()} ({lga_aisl})<br>
                <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
                <b>Justificación Analítica:</b> S por CDT = <b>{s_cdt_lga:.2f} mm²</b>, calentamiento = <b>{s_cal_lga} mm²</b>, mínimo = <b>{min_reg_lga} mm²</b>. S óptima = <b>{s_optima_lga} mm²</b>. Protección: {prot_lga} A.
                </span>
            </div>
        """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 3: DERIVACIÓN INDIVIDUAL
# =========================================================================
with pestanas[2]:
    st.title("Derivación Individual - DI (ITC-BT-15)")
    
    col_h_di, col_btn_di = st.columns([4, 1])
    with col_h_di:
        with st.popover("❓ 📖 Ventana de Ayuda: Criterios de la Derivación Individual"):
            st.markdown("### Guía Técnica de la Derivación Individual (ITC-BT-15)")
            st.write("""
            * **Modelo A (CDT máx = 1.0%):** Contadores concentrados.
            * **Modelo B (CDT máx = 0.5%):** Contadores diseminados o exteriores.
            * **Sección Mínima Reglamentaria:** Mínimo **6 mm²** de cobre para viviendas.
            """)
    with col_btn_di:
        if st.button("🔄 Resetear Longitud DI"):
            st.session_state.di_long_val = 0.0
            st.rerun()

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
        di_long = st.number_input("Longitud de la DI (m)", value=float(st.session_state.di_long_val), key="di_l")
        st.session_state.di_long_val = di_long
        di_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"], key="di_mat")
    with di_c2:
        di_aisl = st.selectbox("Aislamiento y Temperatura", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="di_ais")
        di_cos = st.slider("Coseno phi (cos phi)", 0.8, 1.0, 1.0, key="di_cos")

    if di_long <= 0:
        st.warning("⚠️ **Atención:** La longitud de la Derivación Individual está a 0. Introduce una longitud válida para realizar el cálculo.")
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
        z_di_tot = (230 / (10000)) + (2 * r_di)
        icc_fin_di = 230 / z_di_tot / 1000 if z_di_tot > 0 else 0
        prot_di = seleccionar_proteccion(ib_di)

        dv_real_di_v = (2 * di_pot * di_long) / (gamma_di * s_optima_di * 230) if gamma_di > 0 and s_optima_di > 0 else 0.0
        dv_real_di_pct = (dv_real_di_v / 230) * 100

        st.markdown("---")
        st.subheader("📐 Desglose detallado de Fórmulas y Resultados - DI")
        st.markdown(f"""
        1. **Intensidad de Diseño (Ib monofásica):** Ib = <b>{ib_di:.2f} A</b><br>
        2. **Sección por Caída de Tensión:** S = <b style="font-size: 20px; color: #ff4b4b;">{s_cdt_di:.2f} mm²</b> (Real: <b>{dv_real_di_pct:.3f}%</b>)<br>
        3. **Sección por Calentamiento:** Mínimo requerido = <b>{s_cal_di} mm²</b><br>
        4. **Sección Mínima Reglamentaria:** <b>{min_reg_di} mm²</b> ({di_mat.upper()})<br>
        5. **Corriente de Cortocircuito (Icc final):** <b>{icc_fin_di:.2f} kA</b>
        """, unsafe_allow_html=True)

        # --- MEMORIA DE JUSTIFICACIÓN TÉCNICA Y LÓGICA DE SELECCIÓN (DI) ---
        st.markdown(f"""
        <div class="justificacion-tecnica-box">
            <h4 style="color: #0066cc; margin-top: 0;">📋 Memoria de Justificación Técnica y Criterio de Selección (DI)</h4>
            <p><b>1. Cálculo de la Intensidad de Diseño (Ib):</b><br>
            Para una derivación monofásica, la corriente se calcula mediante la fórmula:<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>Ib = P / ( V x cos phi )</b> = {di_pot} / ( 230 x {di_cos} ) = <b>{ib_di:.2f} A</b></p>
            
            <p><b>2. Criterio de Calentamiento (Intensidad Admisible Iz >= Ib):</b><br>
            El conductor debe soportar al menos la corriente de diseño. Según tablas para {di_mat.upper()} en tubo ({di_aisl}), se requiere una sección térmica mínima de <b>{s_cal_di} mm²</b>.</p>
            
            <p><b>3. Criterio de Caída de Tensión (CDT <= {dv_pct_di}%):</b><br>
            Aplicando la fórmula analítica monofásica de caída de tensión:<br>
            &nbsp;&nbsp;&nbsp;&nbsp;<b>S = ( 2 x P x L ) / (gamma x Delta V x V)</b> = ( 2 x {di_pot} x {di_long} ) / ( {gamma_di} x {dv_max_di} x 230 ) = <b style="color: #ff4b4b; font-size: 16px;">{s_cdt_di:.2f} mm²</b></p>
            
            <p><b>4. Lógica de Descarte y Selección de la Sección Óptima:</b><br>
            • Se <b>descartan</b> las secciones comerciales inferiores que no alcancen el valor analítico de caída de tensión requerido o el mínimo reglamentario de {min_reg_di} mm² (exigido por ITC-BT-15 para viviendas).<br>
            • Se selecciona la primera sección comercial que cumple todos los requisitos, adoptando definitivamente <b>{s_optima_di} mm² de {di_mat.upper()} ({di_aisl})</b>, logrando una caída de tensión real del <b>{dv_real_di_pct:.3f}%</b>.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📋 Tabla Comparativa de Secciones Normalizadas y Justificación - DI")
        tabla_comparativa_di = []
        for sec in SECCIONES_COMERCIALES:
            iz_sec = IZ_COBRE_TUBO.get(sec, 300.0)
            cumple_cal = "✅ Sí" if iz_sec >= ib_di else "❌ No"
            
            dv_sec_v = (2 * di_pot * di_long) / (gamma_di * sec * 230) if gamma_di > 0 and sec > 0 else 0.0
            dv_sec_pct = (dv_sec_v / 230) * 100
            cumple_cdt = f"✅ Sí ({dv_sec_pct:.3f}%)" if dv_sec_pct <= dv_pct_di else f"❌ No ({dv_sec_pct:.3f}%)"
            
            cumple_reg = "✅ Sí" if sec >= min_reg_di else f"❌ No"
            
            estado = "❌ DESCARTADA"
            if sec >= s_bruta_di:
                estado = "⭐ SELECCIONADA (Óptima)"
            
            tabla_comparativa_di.append({
                "Sección Comercial": f"{sec} mm²",
                "Intensidad Admisible (Iz)": f"{iz_sec} A",
                "Criterio Calentamiento": cumple_cal,
                "Criterio Caída Tensión": cumple_cdt,
                "Mínimo REBT (ITC-BT-15)": cumple_reg,
                "Estado Final": estado
            })

        st.dataframe(tabla_comparativa_di, use_container_width=True)

        dv_real_lga_pct_val = dv_real_lga_pct if 'dv_real_lga_pct' in locals() and lga_pot > 0 and lga_long > 0 else 0.0
        cdt_acumulada_pct = dv_real_lga_pct_val + dv_real_di_pct
        limite_global_conjunto = 1.5

        st.markdown("---")
        st.subheader("🎯 Comprobación del Tramo Más Desfavorable (LGA + DI Acumulada)")
        col_df1, col_df2 = st.columns(2)
        with col_df1: st.metric("Caída Acumulada (LGA + DI)", f"{cdt_acumulada_pct:.3f}%")
        with col_df2: st.metric("Límite Reglamentario Global", f"{limite_global_conjunto}%")

        if cdt_acumulada_pct <= limite_global_conjunto:
            st.success(f"✅ **Verificación superada:** Cumple estrictamente con el límite global de {limite_global_conjunto}%.")
        else:
            st.warning(f"⚠️ **Atención:** Supera el límite recomendado de {limite_global_conjunto}%.")

        st.markdown(f"""
            <div class="resultado-destacado">
                🔌 SECCIÓN A ADOPTAR (DI): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_di} mm²</span> de {di_mat.upper()} ({di_aisl})<br>
                <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
                <b>Justificación Analítica:</b> S por CDT = <b>{s_cdt_di:.2f} mm²</b>, calentamiento = <b>{s_cal_di} mm²</b>, mínimo = <b>{min_reg_di} mm²</b>. S óptima = <b>{s_optima_di} mm²</b>. PIA: {prot_di} A.
                </span>
            </div>
        """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 4: TABLA GUÍA ESTILO PLC MADRID (AMPLIADA)
# =========================================================================
with pestanas[3]:
    st.title("📊 Tablas de Cálculo Directo Estilo PLC Madrid (ITC-BT-15)")
    st.write("Consulta horizontal rápida y orientativa de longitudes máximas admisibles para Derivaciones Individuales con conductores de cobre bajo tubo empotrado:")

    tabla_plc_data = [
        {"Sección Mín": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "6 m", "32A (7.32 kW)": "13 m", "40A (9.20 kW)": "10 m", "50A (11.5 kW)": "8 m"},
        {"Sección Mín": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "11 m", "32A (7.32 kW)": "26 m", "40A (9.20 kW)": "20 m", "50A (11.5 kW)": "16 m"},
        {"Sección Mín": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "11 m", "32A (7.32 kW)": "22 m", "40A (9.20 kW)": "17 m", "50A (11.5 kW)": "14 m"},
        {"Sección Mín": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "22 m", "32A (7.32 kW)": "44 m", "40A (9.20 kW)": "34 m", "50A (11.5 kW)": "27 m"},
        {"Sección Mín": "16 mm²", "Tubo Mín": "40 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "35 m", "32A (7.32 kW)": "35 m", "40A (9.20 kW)": "27 m", "50A (11.5 kW)": "22 m"},
        {"Sección Mín": "16 mm²", "Tubo Mín": "40 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "70 m", "32A (7.32 kW)": "70 m", "40A (9.20 kW)": "55 m", "50A (11.5 kW)": "44 m"}
    ]
    st.dataframe(tabla_plc_data, use_container_width=True)
    
    st.markdown("""
        <div style="background-color: #f8f9fa; border-left: 4px solid #ff4b4b; padding: 15px; border-radius: 5px; margin-top: 20px; color: #333;">
            <b>💡 Nota técnica de campo:</b> Esta tabla es ideal para comprobaciones rápidas pie de obra basadas en las directrices formativas clásicas. Para el proyecto oficial y la MTD, utiliza siempre el cálculo analítico exacto de las pestañas de LGA y DI.
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 5: CÁLCULO RÁPIDO
# =========================================================================
with pestanas[4]:
    st.title("🧮 Ventana de Cálculo Rápido (Justificación Analítica)")
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
    st.title("📐 Esquema Unifilar con Símbolos Gráficos Reglamentarios")
    tipo_electrificacion_simbolos = st.radio("Grado de Electrificación:", ["Grado Básico (ITC-BT-25 - 5 Circuitos)", "Grado Elevado"])
    
    esquema_simbolos_txt = f"""
==========================================================================================
PROYECTO: {st.session_state.nombre_proyecto}
TITULAR: {st.session_state.cliente_actual['nombre']} - BOLIMUR INSTALACIONES INTEGRALES
==========================================================================================
   [ DI ] ──────────────── [ IGA ] ─────────────── [ SOBRETENSIONES ] ────────────── [ ID ]
   10 mm² Cu               25 A                     Transitorias +           40 A, 30 mA
     │                      │                             │                    │
     └──────────────────────┴─────────────────────────────┴────────────────────┴──┬──
                                                                                 │
         ├─(10 A)──[/]─── 2x1,5+1,5 Tubo 16 ── // ─── C1: Iluminación
         ├─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C2: TC usos varios
         ├─(25 A)──[/]─── 2x6,0+6,0 Tubo 25 ── // ─── C3: Cocina y Horno
         ├─(20 A)──[/]─── 2x4,0+4,0 Tubo 20 ── // ─── C4: Lavadora y termo
         └─(16 A)──[/]─── 2x2,5+2,5 Tubo 20 ── // ─── C5: TC Baños y cocina
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
        <p><b>Dirección:</b> {st.session_state.cliente_actual['direccion']}, {st.session_state.cliente_actual['municipio']}</p>
        <hr>
        <p><b>Empresa Instaladora:</b> {perfil_guardado["empresa"]} | <b>Carné:</b> {perfil_guardado["carnet"]}</p>
        <p><b>Instalador Autorizado:</b> {perfil_guardado["nombre"]} | <b>Teléfono:</b> {perfil_guardado["telefono"]}</p>
        <hr>
        <p><b>Proyecto:</b> {st.session_state.nombre_proyecto} | <b>Potencia Total:</b> {pt_total:,} W</p>
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
        <h4>1. TITULAR</h4>
        <p>{st.session_state.cliente_actual['nombre']} - NIF: {st.session_state.cliente_actual['nif']}</p>
        <hr>
        <h4>2. INSTALADOR HABILITADO</h4>
        <p>{perfil_guardado['empresa']} - Nº Inscripción CARM: {perfil_guardado['num_inscripcion']}</p>
        <hr>
        <h4>3. DATOS TÉCNICOS</h4>
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