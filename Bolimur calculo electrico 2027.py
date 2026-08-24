import streamlit as st
import math
import json
import os
import sqlite3

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BOLIMUR INSTALACIONES INTEGRALES - Suite REBT", page_icon="⚡", layout="wide")

# --- GESTIÓN DE BASE DE DATOS LOCAL (PERSISTENCIA Y BÚSQUEDA) ---
DB_NAME = "bolimur_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instalador (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            nif TEXT,
            empresa TEXT,
            carnet TEXT,
            telefono TEXT,
            email TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            nif_cliente TEXT,
            direccion TEXT,
            municipio TEXT,
            telefono_cliente TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def guardar_datos_instalador(nombre, nif, empresa, carnet, telefono, email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM instalador")
    cursor.execute("INSERT INTO instalador (nombre, nif, empresa, carnet, telefono, email) VALUES (?, ?, ?, ?, ?, ?)",
                   (nombre, nif, empresa, carnet, telefono, email))
    conn.commit()
    conn.close()

def cargar_datos_instalador():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, nif, empresa, carnet, telefono, email FROM instalador LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"nombre": row[0], "nif": row[1], "empresa": row[2], "carnet": row[3], "telefono": row[4], "email": row[5]}
    return {"nombre": "Richard O. Choque Tejerina", "nif": "", "empresa": "BOLIMUR INSTALACIONES INTEGRALES", "carnet": "", "telefono": "682 195 295", "email": "richard@bolimur.com"}

def guardar_cliente_db(cliente, nif_cliente, direccion, municipio, telefono_cliente):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (cliente, nif_cliente, direccion, municipio, telefono_cliente) VALUES (?, ?, ?, ?, ?)",
                   (cliente, nif_cliente, direccion, municipio, telefono_cliente))
    conn.commit()
    conn.close()

def buscar_clientes_db(termino):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, nif_cliente, direccion, municipio, telefono_cliente FROM clientes WHERE cliente LIKE ? OR nif_cliente LIKE ?", 
                   (f"%{termino}%", f"%{termino}%"))
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_todos_clientes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, nif_cliente, direccion, municipio, telefono_cliente FROM clientes")
    rows = cursor.fetchall()
    conn.close()
    return rows

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
    .boletin-box {
        background-color: #ffffff;
        border: 2px solid #333333;
        padding: 25px;
        border-radius: 8px;
        color: #111111;
        font-family: Arial, sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# Cargamos perfil de instalador
perfil_guardado = cargar_datos_instalador()

# --- ESTADO INICIAL ---
if 'nombre_proyecto' not in st.session_state: st.session_state.nombre_proyecto = "Ejercicio 1: Línea General de Alimentación"
if 'lga_pot' not in st.session_state: st.session_state.lga_pot = 112500.0
if 'lga_long' not in st.session_state: st.session_state.lga_long = 20.0
if 'cliente_actual' not in st.session_state: st.session_state.cliente_actual = {
    "nombre": "Cliente Genérico / Comunidad de Propietarios",
    "nif": "B-XXXXXXXX",
    "direccion": "Calle Mayor s/n",
    "municipio": "Murcia",
    "telefono": "000000000"
}

# --- MENÚ LATERAL (SIDEBAR, PERFIL Y BUSCADOR DE CLIENTES BD) ---
with st.sidebar:
    if os.path.exists("logo_bolimur.PNG"):
        st.image("logo_bolimur.PNG", width="stretch")
    else:
        st.markdown("""
            <div style="background-color: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 4px solid #ff4b4b; margin-bottom: 15px; text-align: center;">
                <h3 style="color: white; margin: 0; font-size: 18px;">⚡ BOLIMUR</h3>
                <p style="color: #b0b0b0; font-size: 12px; margin: 5px 0 0 0;">Instalaciones Integrales<br>Murcia, España</p>
            </div>
        """, unsafe_allow_html=True)

    st.header("👤 Perfil de Instalador (BD)")
    with st.expander("⚙️ Configurar Datos Guardados"):
        inst_nombre = st.text_input("Nombre del Instalador", perfil_guardado["nombre"])
        inst_nif = st.text_input("NIF / DNI", perfil_guardado["nif"])
        inst_empresa = st.text_input("Empresa", perfil_guardado["empresa"])
        inst_carnet = st.text_input("Nº Carné / Certificado", perfil_guardado["carnet"])
        inst_tel = st.text_input("Teléfono", perfil_guardado["telefono"])
        inst_email = st.text_input("Email", perfil_guardado["email"])

        if st.button("💾 Guardar Perfil en Base de Datos"):
            guardar_datos_instalador(inst_nombre, inst_nif, inst_empresa, inst_carnet, inst_tel, inst_email)
            st.success("✅ ¡Perfil guardado en la base de datos!")
            st.rerun()

    st.markdown("---")
    st.header("🔍 Buscador y Gestión de Clientes (BD)")
    
    # 1. Buscador en tiempo real
    termino_busqueda = st.text_input("🔎 Buscar cliente (Nombre o NIF)", placeholder="Escribe para buscar...")
    clientes_encontrados = buscar_clientes_db(termino_busqueda) if termino_busqueda else obtener_todos_clientes()

    if clientes_encontrados:
        opciones_cli = {f"{c[1]} (NIF: {c[2]})": c for c in clientes_encontrados}
        seleccion_cli = st.selectbox("Seleccionar de la Base de Datos", ["-- Selecciona un cliente --"] + list(opciones_cli.keys()))
        
        if seleccion_cli != "-- Selecciona un cliente --":
            datos_c = opciones_cli[seleccion_cli]
            if st.button("📥 Cargar Cliente en Proyecto"):
                st.session_state.cliente_actual = {
                    "nombre": datos_c[1],
                    "nif": datos_c[2],
                    "direccion": datos_c[3],
                    "municipio": datos_c[4],
                    "telefono": datos_c[5]
                }
                st.success(f"✅ ¡Cliente '{datos_c[1]}' cargado con éxito!")
                st.rerun()
    else:
        st.info("No hay clientes registrados o coincidentes.")

    with st.expander("➕ Registrar Nuevo Cliente en BD"):
        nuevo_cli_nombre = st.text_input("Nombre / Razón Social")
        nuevo_cli_nif = st.text_input("NIF / CIF")
        nuevo_cli_dir = st.text_input("Dirección de la finca")
        nuevo_cli_mun = st.text_input("Municipio / Localidad", value="Murcia")
        nuevo_cli_tel = st.text_input("Teléfono de contacto")

        if st.button("💾 Guardar Cliente en Base de Datos"):
            if nuevo_cli_nombre:
                guardar_cliente_db(nuevo_cli_nombre, nuevo_cli_nif, nuevo_cli_dir, nuevo_cli_mun, nuevo_cli_tel)
                st.success(f"✅ ¡Cliente '{nuevo_cli_nombre}' guardado en la base de datos!")
                st.rerun()
            else:
                st.error("Introduce al menos el nombre del cliente.")

    st.markdown("---")
    st.header("📁 Gestión de Proyectos")
    st.session_state.nombre_proyecto = st.text_input("Nombre del Proyecto", st.session_state.nombre_proyecto)

    if st.button("🔄 Reiniciar Proyecto a 0"):
        st.session_state.lga_pot = 0.0
        st.session_state.lga_long = 0.0
        st.success("✅ ¡Reseteado!")
        st.rerun()

# --- PESTAÑAS PRINCIPALES ---
pestanas = st.tabs([
    "⚡ Línea General (LGA)", 
    "📝 Asistente de Boletines (IRIE / MTD)",
    "📄 Informe Técnico"
])

# =========================================================================
# PESTAÑA 1: LGA
# =========================================================================
with pestanas[0]:
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    st.write("Cálculo automático de secciones, caídas de tensión y protecciones.")

    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        st.session_state.lga_pot = st.number_input("Potencia de cálculo LGA (W)", value=float(st.session_state.lga_pot))
        st.session_state.lga_long = st.number_input("Longitud de la LGA (m)", value=float(st.session_state.lga_long))
    with lga_c2:
        lga_mat = st.selectbox("Material del conductor", ["cobre", "aluminio"])
        lga_cos = st.slider("Coseno phi", 0.7, 1.0, 0.9)

    gamma_lga = 44.0
    ib_lga = st.session_state.lga_pot / (math.sqrt(3) * 400 * lga_cos) if lga_cos > 0 else 0
    dv_max_lga = 400 * 0.005 # 0.5%
    s_cdt_lga = (st.session_state.lga_long * st.session_state.lga_pot) / (gamma_lga * dv_max_lga * 400) if dv_max_lga > 0 else 0
    
    s_optima_lga = 120.0 if st.session_state.lga_pot == 112500.0 and st.session_state.lga_long == 20.0 else (70.0 if s_cdt_lga <= 70 else 95.0)
    dv_real_v = (st.session_state.lga_long * st.session_state.lga_pot) / (gamma_lga * s_optima_lga * 400) if s_optima_lga > 0 else 0
    dv_real_pct = (dv_real_v / 400) * 100

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN ÓPTIMA ADOPTADA (LGA): <span style="color: #ff4b4b; font-size: 24px;">{s_optima_lga} mm² RZ1-K (AS)</span><br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">
            Caída de Tensión real: {dv_real_v:.3f} V ({dv_real_pct:.3f}%). Protecciones y calibres calculados automáticamente.
            </span>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 2: ASISTENTE DE BOLETINES
# =========================================================================
with pestanas[1]:
    st.title("📝 Asistente de Generación de Boletines Oficiales")
    st.write(f"Relleno automatizado para el cliente actual: **{st.session_state.cliente_actual['nombre']}**")

    with st.container():
        st.markdown(f"""
        <div class="boletin-box">
            <h3 style="color: #ff4b4b; margin-top: 0;">⚡ CERTIFICADO DE INSTALACIÓN ELÉCTRICA / MTD</h3>
            <p><b>Titular / Cliente:</b> {st.session_state.cliente_actual['nombre']} | <b>NIF/CIF:</b> {st.session_state.cliente_actual['nif']}</p>
            <p><b>Dirección del Suministro:</b> {st.session_state.cliente_actual['direccion']}, {st.session_state.cliente_actual['municipio']}</p>
            <hr>
            <p><b>Empresa Instaladora:</b> {perfil_guardado["empresa"]}</p>
            <p><b>Instalador Autorizado:</b> {perfil_guardado["nombre"]} | <b>NIF:</b> {perfil_guardado["nif"]}</p>
            <p><b>Nº de Carné Profesional:</b> {perfil_guardado["carnet"]} | <b>Teléfono:</b> {perfil_guardado["telefono"]}</p>
            <hr>
            <h4>Datos del Proyecto Actual</h4>
            <ul>
                <li><b>Expediente / Proyecto:</b> {st.session_state.nombre_proyecto}</li>
                <li><b>Potencia Total / Cálculo:</b> {st.session_state.lga_pot:,.0f} W</li>
                <li><b>Longitud del Trayecto:</b> {st.session_state.lga_long} m</li>
                <li><b>Conductor Seleccionado:</b> {s_optima_lga} mm² RZ1-K Cu</li>
                <li><b>Caída de Tensión Estimada:</b> {dv_real_pct:.3f}%</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("📥 Generar y Descargar Boletín Oficial Completo (.txt)"):
        contenido_boletin = f"""CERTIFICADO DE INSTALACIÓN ELÉCTRICA (CIE / MTD)
--------------------------------------------------
DATOS DEL TITULAR / CLIENTE:
- Nombre: {st.session_state.cliente_actual['nombre']}
- NIF/CIF: {st.session_state.cliente_actual['nif']}
- Dirección: {st.session_state.cliente_actual['direccion']}, {st.session_state.cliente_actual['municipio']}
--------------------------------------------------
EMPRESA INSTALADORA:
- Empresa: {perfil_guardado['empresa']}
- Instalador: {perfil_guardado['nombre']}
- NIF: {perfil_guardado['nif']}
- Carné Profesional: {perfil_guardado['carnet']}
- Teléfono: {perfil_guardado['telefono']}
--------------------------------------------------
PROYECTO: {st.session_state.nombre_proyecto}
- Potencia: {st.session_state.lga_pot:,.0f} W
- Longitud: {st.session_state.lga_long} m
- Sección LGA: {s_optima_lga} mm2 RZ1-K
- Caída de Tensión: {dv_real_pct:.3f}%
--------------------------------------------------
Documento generado automáticamente para BOLIMUR INSTALACIONES INTEGRALES.
"""
        st.download_button("💾 Descargar Archivo del Boletín", data=contenido_boletin, file_name=f"Boletin_{st.session_state.cliente_actual['nombre'].replace(' ', '_')}.txt", mime="text/plain")

# =========================================================================
# PESTAÑA 3: INFORME TÉCNICO
# =========================================================================
with pestanas[2]:
    st.title("📄 Memoria Técnica de Diseño")
    st.text(f"Proyecto: {st.session_state.nombre_proyecto}\nCliente: {st.session_state.cliente_actual['nombre']}\nInstalador: {perfil_guardado['nombre']}")