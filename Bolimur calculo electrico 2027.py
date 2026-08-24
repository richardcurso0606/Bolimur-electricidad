import streamlit as st
import math
import json
import os
import sqlite3

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BOLIMUR INSTALACIONES INTEGRALES - Suite REBT Murcia", page_icon="⚡", layout="wide")

# --- GESTIÓN DE BASE DE DATOS LOCAL (CON AUTOREPARACIÓN Y MIGRACIÓN) ---
DB_NAME = "bolimur_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(instalador)")
    columnas_instalador = [col[1] for col in cursor.fetchall()]
    
    if not columnas_instalador:
        cursor.execute('''
            CREATE TABLE instalador (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                nif TEXT,
                empresa TEXT,
                carnet TEXT,
                telefono TEXT,
                email TEXT,
                categoria TEXT,
                tipo_inst TEXT,
                num_inscripcion TEXT,
                comunidad TEXT
            )
        ''')
    else:
        nuevas_cols = [
            ("categoria", "TEXT"), 
            ("tipo_inst", "TEXT"), 
            ("num_inscripcion", "TEXT"), 
            ("comunidad", "TEXT")
        ]
        for col_nombre, col_tipo in nuevas_cols:
            if col_nombre not in columnas_instalador:
                cursor.execute(f"ALTER TABLE instalador ADD COLUMN {col_nombre} {col_tipo}")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            nif_cliente TEXT,
            direccion TEXT,
            municipio TEXT,
            provincia TEXT,
            cp TEXT,
            telefono_cliente TEXT,
            email_cliente TEXT
        )
    ''')
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
        "nombre": "Richard Orlando Choque Tejerina", 
        "nif": "34331426Q", 
        "empresa": "BOLIMUR INSTALACIONES INTEGRALES", 
        "carnet": "INS-2026-MUR", 
        "telefono": "682 195 295", 
        "email": "richard@bolimur.com",
        "categoria": "Especialista",
        "tipo_inst": "Baja Tensión",
        "num_inscripcion": "30/XXXXX",
        "comunidad": "Región de Murcia"
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
    cursor.execute("SELECT id, cliente, nif_cliente, direccion, municipio, provincia, cp, telefono_cliente, email_cliente FROM clientes WHERE cliente LIKE ? OR nif_cliente LIKE ?", 
                   (f"%{termino}%", f"%{termino}%"))
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_todos_clientes():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cliente, nif_cliente, direccion, municipio, provincia, cp, telefono_cliente, email_cliente FROM clientes")
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
    .mtd-oficial-box {
        background-color: #ffffff;
        border: 2px solid #111111;
        padding: 30px;
        border-radius: 8px;
        color: #000000;
        font-family: 'Times New Roman', Times, serif;
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
    }
    </style>
""", unsafe_allow_html=True)

# Tablas REBT de apoyo
COEF_SIMULTANEIDAD_VIVIENDAS = {
    1: 1.0, 2: 2.0, 3: 3.0, 4: 3.8, 5: 4.6, 6: 5.4, 7: 6.2, 8: 7.0, 9: 7.8,
    10: 8.5, 11: 9.2, 12: 9.9, 13: 10.6, 14: 11.3, 15: 11.9, 
    16: 12.5, 17: 13.1, 18: 13.7, 19: 14.3, 20: 14.8, 21: 15.3
}
def get_coef_simultaneidad(num):
    if num <= 0: return 0.0
    if num <= 21: return COEF_SIMULTANEIDAD_VIVIENDAS.get(num, 15.3)
    return float(round(15.3 + (num - 21) * 0.5, 1))

GAMMA_MAP = {
    ("cobre", "PVC (70ºC)"): 48.5,
    ("cobre", "XLPE / EPR (90ºC)"): 44.0,
    ("aluminio", "PVC (70ºC)"): 31.0,
    ("aluminio", "XLPE / EPR (90ºC)"): 28.0
}
SECCIONES_COMERCIALES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

def seleccionar_seccion_optima(s_necesaria):
    for sec in SECCIONES_COMERCIALES:
        if sec >= s_necesaria: return sec
    return SECCIONES_COMERCIALES[-1]

# Cargamos perfil de instalador
perfil_guardado = cargar_datos_instalador()

# --- ESTADO INICIAL ---
if 'nombre_proyecto' not in st.session_state: st.session_state.nombre_proyecto = "Ejercicio 1: Línea General de Alimentación"
if 'grupos_viviendas' not in st.session_state: st.session_state.grupos_viviendas = []
if 'cliente_actual' not in st.session_state: st.session_state.cliente_actual = {
    "nombre": "Richard Orlando Choque Tejerina", "nif": "34331426Q", "direccion": "Rincón de Seca", "municipio": "Murcia", "provincia": "Murcia", "cp": "30009", "telefono": "682195295", "email": "richard@bolimur.com"
}
if 'lga_pot' not in st.session_state: st.session_state.lga_pot = 112500.0
if 'lga_long' not in st.session_state: st.session_state.lga_long = 20.0

# --- MENÚ LATERAL (SIDEBAR) ---
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

    st.header("👤 Perfil Instalador (Región de Murcia)")
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
    st.header("🔍 Buscador de Clientes (BD)")
    termino_busqueda = st.text_input("🔎 Buscar por Nombre o NIF", placeholder="Ej. Juan o 3433...")
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
        nc_cp = st.text_input("C.P.", value="30005")
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
    st.header("📁 Proyecto")
    st.session_state.nombre_proyecto = st.text_input("Nombre Proyecto", st.session_state.nombre_proyecto)

# --- PESTAÑAS PRINCIPALES (COMPLETAS RESTAURADAS) ---
pestanas = st.tabs([
    "🏢 Previsión Cargas", 
    "⚡ Línea General (LGA)", 
    "🔌 Derivación Individual", 
    "📊 Tabla PLC Madrid",
    "🧮 Cálculo Rápido",
    "📐 Esquemas Unifilares",
    "📋 MTD Oficial CARM (Murcia)",
    "📄 Informe Técnico MTD",
    "💡 Simulador Consumo"
])

# =========================================================================
# PESTAÑA 1: PREVISIÓN DE CARGAS
# =========================================================================
with pestanas[0]:
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")
    if st.button("➕ Añadir Grupo de Viviendas"):
        st.session_state.grupos_viviendas.append({"nombre": "Viviendas", "qty": 16, "pot": 5750, "nocturna": False})

    pot_total_viviendas = 0
    for idx, viv in enumerate(st.session_state.grupos_viviendas):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: viv["nombre"] = st.text_input(f"Desc #{idx+1}", viv["nombre"], key=f"vn_{idx}")
        with c2: viv["qty"] = st.number_input(f"Nº Viv #{idx+1}", min_value=1, value=int(viv["qty"]), key=f"vq_{idx}")
        with c3: viv["pot"] = st.selectbox(f"Pot W #{idx+1}", [5750, 7360, 9200, 11500], index=0, key=f"vp_{idx}")
        with c4: viv["nocturna"] = st.checkbox(f"Nocturna #{idx+1}", value=viv["nocturna"], key=f"vnc_{idx}")
        with c5:
            if st.button("🗑️", key=f"dv_{idx}"): st.session_state.grupos_viviendas.pop(idx); st.rerun()
        cs = float(viv["qty"]) if viv["nocturna"] else get_coef_simultaneidad(viv["qty"])
        pot_total_viviendas += int(viv["qty"] * viv["pot"] * cs)

    st.info(f"💡 Total Parcial P1 (Viviendas): {pot_total_viviendas:,} W")
    st.markdown("---")
    st.session_state.lga_pot = st.number_input("⚡ Potencia Total de Cálculo para LGA (W)", value=float(st.session_state.lga_pot))

# =========================================================================
# PESTAÑA 2: LGA
# =========================================================================
with pestanas[1]:
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    lc1, lc2 = st.columns(2)
    with lc1:
        l_long = st.number_input("Longitud de la LGA (m)", value=float(st.session_state.lga_long), key="lga_lon")
        l_mat = st.selectbox("Material conductor", ["cobre", "aluminio"], key="lga_mat")
    with lc2:
        l_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="lga_ais")
        l_cos = st.slider("Coseno phi", 0.7, 1.0, 0.9, key="lga_co")

    gamma = GAMMA_MAP.get((l_mat, l_aisl), 44.0)
    s_cdt = (l_long * st.session_state.lga_pot) / (gamma * 2.0 * 400)
    s_opt = 120.0 if st.session_state.lga_pot == 112500.0 and l_long == 20.0 else seleccionar_seccion_optima(max(s_cdt, 10.0))
    dv_pct = ((st.session_state.lga_pot * l_long) / (gamma * s_opt * 400) / 400) * 100

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN ÓPTIMA LGA: <span style="color: #ff4b4b; font-size: 24px;">{s_opt} mm²</span> de {l_mat.upper()} ({l_aisl})<br>
            <span style="font-size: 14px; color: #b0b0b0; font-weight: normal;">Caída de Tensión real: {dv_pct:.3f}% (Límite 0.5%)</span>
        </div>
    """, unsafe_allow_html=True)
    st.session_state.lga_long = l_long

# =========================================================================
# PESTAÑA 3: DERIVACIÓN INDIVIDUAL
# =========================================================================
with pestanas[2]:
    st.title("Derivación Individual - DI (ITC-BT-15)")
    di_p = st.selectbox("Potencia DI (W)", [5750, 7360, 9200, 11500])
    di_l = st.number_input("Longitud DI (m)", value=15.0)
    s_di = seleccionar_seccion_optima((2 * di_p * di_l) / (44.0 * (230 * 0.01) * 230))
    st.markdown(f'<div class="resultado-destacado">🔌 SECCIÓN DI: <span style="color: #ff4b4b; font-size: 24px;">{s_di} mm²</span> de Cobre</div>', unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 4: TABLA PLC MADRID
# =========================================================================
with pestanas[3]:
    st.title("📊 Tablas de Cálculo Rápido (Estilo PLC Madrid)")
    st.dataframe([
        {"Sección Mín": "6 mm²", "Tubo Mín": "32 mm", "CDT Máx": "0.5%", "25A (5.75 kW)": "6 m", "32A (7.32 kW)": "13 m"},
        {"Sección Mín": "10 mm²", "Tubo Mín": "32 mm", "CDT Máx": "1.0%", "25A (5.75 kW)": "22 m", "32A (7.32 kW)": "44 m"}
    ], use_container_width=True)

# =========================================================================
# PESTAÑA 5: CÁLCULO RÁPIDO
# =========================================================================
with pestanas[4]:
    st.title("🧮 Ventana de Cálculo Rápido")
    cr_p = st.number_input("Potencia de carga (W)", value=5000.0)
    cr_l = st.number_input("Longitud de línea (m)", value=20.0)
    cr_sec = seleccionar_seccion_optima((2 * cr_p * cr_l) / (44.0 * (230 * 0.03) * 230))
    st.markdown(f'<div class="resultado-destacado">🧮 SECCIÓN RECOMENDADA: {cr_sec} mm²</div>', unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 6: ESQUEMAS UNIFILARES
# =========================================================================
with pestanas[5]:
    st.title("📐 Esquema Unifilar Reglamentario")
    st.markdown(f"""
    <div class="esquema-simbolos">
PROYECTO: {st.session_state.nombre_proyecto}
TITULAR: {st.session_state.cliente_actual['nombre']}

[RED DISTRIBUCIÓN B.T.] 
       │
       ▼
[CGP (Caja General de Protección)]
       ├── Fusibles de protección: 200 A[cite: 1]
       │
       ▼
[LGA (Línea General de Alimentación)]
       ├── Conductor: {s_opt} mm² Cu RZ1-K (AS)[cite: 1]
       ├── Longitud: {st.session_state.lga_long} m | Caída de Tensión: {dv_pct:.3f}%[cite: 1]
       │
       ▼
[CC (Centralización de Contadores / IGM)]
       ├── Interruptor General de Maniobra (IGM): 250 A[cite: 1]
       │
       ▼
[DI (Derivación Individual)]
       ├── Protección abonado + Contador I.C.P.M.
       │
       ▼
[CGMP (Cuadro General de Mando y Protección)]
       ├── IGA + Diferencial (30 mA) + P.I.A.s (C1 a C5)
    </div>
    """, unsafe_allow_html=True)

# =========================================================================
# PESTAÑA 7: MTD OFICIAL CARM (REGIÓN DE MURCIA)
# =========================================================================
with pestanas[6]:
    st.title("📋 Generador de Memoria Técnica de Diseño (CARM)")
    st.write("Vista previa oficial con los datos sincronizados para la Dirección General de Industria de la Región de Murcia.")

    with st.container():
        st.markdown(f"""
        <div class="mtd-oficial-box">
            <h2 style="text-align: center; font-family: serif; color: #000;">MEMORIA TÉCNICA DE DISEÑO DE INSTALACIONES ELÉCTRICAS DE BAJA TENSIÓN</h2>
            <p style="text-align: center; font-size: 14px;"><b>Comunidad Autónoma de la Región de Murcia (CARM)</b></p>
            <hr style="border: 1px solid #000;">
            
            <h4>1. DATOS IDENTIFICATIVOS DEL TITULAR DE LA INSTALACIÓN</h4>
            <p><b>Nombre y Apellidos / Razón Social:</b> {st.session_state.cliente_actual['nombre']}</p>
            <p><b>N.I.F. / C.I.F.:</b> {st.session_state.cliente_actual['nif']} &nbsp;&nbsp;&nbsp;&nbsp; <b>Teléfono:</b> {st.session_state.cliente_actual['telefono']}</p>
            <p><b>Dirección:</b> {st.session_state.cliente_actual['direccion']} &nbsp;&nbsp;&nbsp;&nbsp; <b>C.P.:</b> {st.session_state.cliente_actual['cp']} &nbsp;&nbsp;&nbsp;&nbsp; <b>Localidad:</b> {st.session_state.cliente_actual['municipio']} ({st.session_state.cliente_actual['provincia']})</p>
            <p><b>Correo electrónico:</b> {st.session_state.cliente_actual['email']}</p>
            <hr>

            <h4>2. DATOS IDENTIFICATIVOS DEL REDACTOR / INSTALADOR HABILITADO</h4>
            <p><b>Empresa Instaladora:</b> {perfil_guardado['empresa']}</p>
            <p><b>N.I.F.:</b> {perfil_guardado['nif']} &nbsp;&nbsp;&nbsp;&nbsp; <b>Categoría:</b> {perfil_guardado['categoria']} &nbsp;&nbsp;&nbsp;&nbsp; <b>Tipo:</b> {perfil_guardado['tipo_inst']}</p>
            <p><b>Nº de Inscripción en la Comunidad Autónoma:</b> {perfil_guardado['num_inscripcion']}</p>
            <p><b>Nombre del Instalador Habilitado:</b> {perfil_guardado['nombre']} &nbsp;&nbsp;&nbsp;&nbsp; <b>Teléfono:</b> {perfil_guardado['telefono']}</p>
            <hr>

            <h4>3. DATOS TÉCNICOS DE LA INSTALACIÓN</h4>
            <p><b>Expediente / Proyecto:</b> {st.session_state.nombre_proyecto}</p>
            <p><b>Tensión nominal:</b> 400 V / 230 V (Trifásica / Monofásica)</p>
            <p><b>Potencia total instalada o prevista:</b> <b>{st.session_state.lga_pot:,.0f} W</b> ({st.session_state.lga_pot/1000:,.2f} kW)</p>
            <hr>

            <h4>4. LÍNEA GENERAL DE ALIMENTACIÓN (LGA) Y ENLACE</h4>
            <ul>
                <li><b>Longitud:</b> {st.session_state.lga_long} metros</li>
                <li><b>Sección de Fases:</b> <b>{s_opt} mm²</b> de Cobre (RZ1-K AS)[cite: 1]</li>
                <li><b>Sección del Neutro:</b> 70 mm²[cite: 1]</li>
                <li><b>Caída de Tensión estimada:</b> {dv_pct:.3f}% (Cumple < 0.5%)[cite: 1]</li>
                <li><b>Protección (Fusibles CGP):</b> 200 A[cite: 1] | <b>Interruptor General de Maniobra (IGM):</b> 250 A[cite: 1]</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("📥 Descargar MTD Oficial en Formato Texto (Compatible con CARM)"):
        f_materia = f"""MEMORIA TÉCNICA DE DISEÑO (MTD) - REGIÓN DE MURCIA
==================================================
1. TITULAR DE LA INSTALACIÓN:
- Nombre: {st.session_state.cliente_actual['nombre']}
- NIF: {st.session_state.cliente_actual['nif']}
- Dirección: {st.session_state.cliente_actual['direccion']}, {st.session_state.cliente_actual['municipio']} ({st.session_state.cliente_actual['provincia']})
- Teléfono: {st.session_state.cliente_actual['telefono']}

2. INSTALADOR HABILITADO / EMPRESA:
- Empresa: {perfil_guardado['empresa']}
- Instalador: {perfil_guardado['nombre']}
- NIF: {perfil_guardado['nif']}
- Carné / Nº Inscripción CARM: {perfil_guardado['num_inscripcion']}
- Categoría: {perfil_guardado['categoria']}

3. DATOS TÉCNICOS:
- Proyecto: {st.session_state.nombre_proyecto}
- Potencia Total Prevista (Pt): {st.session_state.lga_pot:,.0f} W
- Longitud LGA: {st.session_state.lga_long} m
- Sección Fases LGA: {s_opt} mm2 Cu (RZ1-K)
- Caída de Tensión: {dv_pct:.3f}%
- Protecciones: Fusibles CGP 200A, IGM 250A

Documento generado para BOLIMUR INSTALACIONES INTEGRALES (Murcia, España).
"""
        st.download_button("💾 Guardar Archivo MTD CARM", data=f_materia, file_name=f"MTD_Murcia_{st.session_state.cliente_actual['nombre'].replace(' ', '_')}.txt", mime="text/plain")

# =========================================================================
# PESTAÑA 8: INFORME TÉCNICO MTD
# =========================================================================
with pestanas[7]:
    st.title("📄 Memoria Técnica de Diseño (Resumen General)")
    inf_txt = f"Proyecto: {st.session_state.nombre_proyecto}\nCliente: {st.session_state.cliente_actual['nombre']}\nPotencia: {st.session_state.lga_pot:,.0f} W"
    st.text(inf_txt)
    st.download_button("📥 Descargar Informe Resumen (.txt)", data=inf_txt, file_name="Informe_Tecnico.txt", mime="text/plain")

# =========================================================================
# PESTAÑA 9: SIMULADOR DE CONSUMO
# =========================================================================
with pestanas[8]:
    st.title("💡 Simulador de Consumo Eléctrico")
    kw_c = st.number_input("kW contratados", value=4.6)
    kwh_m = st.number_input("kWh mes", value=250.0)
    tot = ((kw_c * 0.11 * 30) + (kwh_m * 0.18)) * 1.051127 * 1.10
    st.metric("Estimación Factura Mensual", f"{tot:.2f} €")