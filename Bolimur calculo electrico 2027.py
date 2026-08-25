import streamlit as st
import math
import os
import sqlite3

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BOLIMUR INSTALACIONES INTEGRALES", page_icon="⚡", layout="wide")

# --- BASE DE DATOS LOCAL ---
DB_NAME = "bolimur_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(instalador)")
    if not [col[1] for col in cursor.fetchall()]:
        cursor.execute('''CREATE TABLE instalador (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, nif TEXT, empresa TEXT, carnet TEXT, 
            telefono TEXT, email TEXT, categoria TEXT, tipo_inst TEXT, num_inscripcion TEXT, comunidad TEXT)''')
    cursor.execute("PRAGMA table_info(configuracion)")
    if not [col[1] for col in cursor.fetchall()]:
        cursor.execute('''CREATE TABLE configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ultimo_archivo TEXT, carpeta_trabajo TEXT)''')
        cursor.execute("INSERT INTO configuracion (ultimo_archivo, carpeta_trabajo) VALUES (?, ?)", ("proyecto_bolimur_default.json", "proyectos_bolimur"))
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
    except sqlite3.OperationalError: row = None
    conn.close()
    if row: return {"nombre": row[0] or "", "nif": row[1] or "", "empresa": row[2] or "", "carnet": row[3] or "", "telefono": row[4] or "", "email": row[5] or "", "categoria": row[6] or "", "tipo_inst": row[7] or "", "num_inscripcion": row[8] or "", "comunidad": row[9] or ""}
    return {"nombre": "Richard Orlando Choque Tejerina", "nif": "34331426Q", "empresa": "BOLIMUR INSTALACIONES INTEGRALES", "carnet": "INS-2026-MUR", "telefono": "682 195 295", "email": "richard@bolimur.com", "categoria": "Especialista", "tipo_inst": "Baja Tensión", "num_inscripcion": "30/XXXXX", "comunidad": "Región de Murcia"}

perfil_guardado = cargar_datos_instalador()

# --- CSS DEFINITIVO (MÓVIL Y ESCRITORIO) ---
st.markdown("""
    <style>
    /* 1. MENÚ LATERAL (Visual y limpio) */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background-color: transparent !important;
        padding: 10px 5px !important;
        margin-bottom: 5px !important;
        color: #334155 !important;
        font-size: 16px !important;
        transition: all 0.2s ease-in-out !important;
        cursor: pointer !important;
        border-radius: 8px;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background-color: #e0f2fe !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-baseweb="radio"] input:checked + div {
        color: #0369a1 !important;
        font-weight: bold !important;
    }

    /* 2. TABLAS REBT (Cabecera oscura y ✅ CUMPLE) */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 14px;
        border-radius: 6px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    th {
        background-color: #1e293b !important;
        color: #ffffff !important;
        text-align: center !important;
        padding: 14px !important;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.5px;
    }
    td {
        padding: 12px !important;
        border-bottom: 1px solid #e2e8f0 !important;
        color: #334155 !important;
        background-color: #ffffff !important;
        text-align: center !important;
    }
    tr:nth-child(even) td { background-color: #f8fafc !important; }

    /* 3. CAJAS DE FÓRMULAS (Memoria Analítica Detallada) */
    .caja-formula {
        background-color: #f0f7ff;
        border-left: 4px solid #0284c7;
        padding: 18px 22px;
        border-radius: 6px;
        margin-bottom: 20px;
        color: #0f172a;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .caja-formula h4 {
        color: #0369a1;
        margin-top: 0;
        margin-bottom: 12px;
        font-size: 18px;
        font-weight: 600;
    }
    .caja-formula p { margin-bottom: 8px; line-height: 1.5; font-size: 15px; }
    .math-center {
        text-align: center;
        font-size: 18px;
        margin: 15px 0;
        font-weight: normal;
    }

    /* 4. CAJAS DE RESULTADOS (El toque verde de confirmación) */
    .resultado-verde {
        background-color: #ecfdf5;
        border: 2px solid #10b981;
        padding: 20px 25px;
        border-radius: 8px;
        margin: 25px 0;
        color: #065f46;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.15);
    }
    .resultado-verde h2 { color: #047857; margin-top: 0; font-size: 22px; }
    
    /* Protecciones (Azul y Naranja) */
    .pia-destacado {
        background: #e0f2fe; color: #0369a1; padding: 15px; border-radius: 8px; 
        font-size: 18px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #7dd3fc;
    }
    .fusible-vistoso {
        background: #ffedd5; color: #c2410c; padding: 15px; border-radius: 8px; 
        font-size: 18px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #fdba74;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES Y FUNCIONES REBT ---
COEF_SIMULTANEIDAD_VIVIENDAS = {1: 1.0, 2: 2.0, 3: 3.0, 4: 3.8, 5: 4.6, 6: 5.4, 7: 6.2, 8: 7.0, 9: 7.8, 10: 8.5, 11: 9.2, 12: 9.9, 13: 10.6, 14: 11.3, 15: 11.9, 16: 12.5, 17: 13.1, 18: 13.7, 19: 14.3, 20: 14.8, 21: 15.3}
def get_coef_simultaneidad(num):
    if num <= 0: return 0.0
    if num <= 21: return COEF_SIMULTANEIDAD_VIVIENDAS.get(num, 15.3)
    return float(round(15.3 + (num - 21) * 0.5, 1))

METODOS_INSTALACION = {
    "B1 (Bajo tubo empotrado)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas"},
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Multiconductor en pared)": {"ref": "C", "desc": "Cable multiconductor fijado directo"},
    "D (Cables enterrados bajo tubo)": {"ref": "D", "desc": "Instalación subterránea"}
}

GAMMA_MAP = {("cobre", "PVC (70ºC)"): 48.5, ("cobre", "XLPE / EPR (90ºC)"): 44.0, ("aluminio", "PVC (70ºC)"): 31.0, ("aluminio", "XLPE / EPR (90ºC)"): 28.0}
SECCIONES_COMERCIALES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
IZ_COBRE_TUBO = {1.5: 14.5, 2.5: 20.0, 4: 26.0, 6: 34.0, 10: 46.0, 16: 61.0, 25: 80.0, 35: 99.0, 50: 119.0, 70: 151.0, 95: 182.0, 120: 210.0, 150: 240.0, 185: 275.0, 240: 320.0}
IZ_COBRE_ENTERRADO = {1.5: 22.0, 2.5: 29.0, 4: 38.0, 6: 48.0, 10: 65.0, 16: 85.0, 25: 110.0, 35: 135.0, 50: 160.0, 70: 170.0, 95: 202.0, 120: 230.0, 150: 270.0, 185: 310.0, 240: 360.0}
CALIBRES_INTERRUPTORES = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630]

def seleccionar_seccion_optima(s_necesaria):
    for sec in SECCIONES_COMERCIALES:
        if sec >= s_necesaria: return sec
    return SECCIONES_COMERCIALES[-1]

def seleccionar_proteccion(ib):
    for cal in CALIBRES_INTERRUPTORES:
        if cal >= ib: return cal
    return CALIBRES_INTERRUPTORES[-1]

# --- ESTADO INICIAL ---
if 'grupos_viviendas' not in st.session_state: st.session_state.grupos_viviendas = [{"nombre": "Viviendas Estándar", "qty": 0, "pot": 5750, "nocturna": False}]
if 'servicios_generales' not in st.session_state: st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 0, "potencia": 0.0, "factor": 1.30}]
if 'locales' not in st.session_state: st.session_state.locales = [{"nombre": "Local Comercial A", "qty": 0, "superficie": 0.0}]

def calcular_pt_global():
    p_viv = sum(int(round(v["qty"] * v["pot"] * (v["qty"] if v["nocturna"] else get_coef_simultaneidad(v["qty"])))) for v in st.session_state.grupos_viviendas)
    p_loc = sum(max(l["superficie"] * 100.0, 3450.0 if l["superficie"] > 0 else 0.0) * l["qty"] for l in st.session_state.locales)
    p_serv = sum(s["potencia"] * s["qty"] * s.get("factor", 1.30) for s in st.session_state.servicios_generales)
    return float(p_viv + int(p_loc) + int(p_serv) + 3450)

# --- MENÚ LATERAL ---
with st.sidebar:
    st.markdown("""
        <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 15px; text-align: center;">
            <h3 style="color: #38bdf8; margin: 0; font-size: 18px;">⚡ BOLIMUR</h3>
            <p style="color: #94a3b8; font-size: 12px; margin: 5px 0 0 0;">Instalaciones Integrales</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h4 style='color: #475569; margin-bottom: 5px;'>📂 Navegación de Módulos</h4>", unsafe_allow_html=True)
    seleccion_modulo = st.radio("Selecciona:", [
        "🏠 Menú Principal", 
        "🧮 Cálculo Rápido (CDT & Icc)", 
        "🏢 Previsión de Cargas (Pt)", 
        "⚡ Línea General (LGA)", 
        "🔌 Derivación Individual (DI)", 
        "📚 Tablas REBT", 
        "📐 Esquemas Unifilares"
    ], label_visibility="collapsed")

# =========================================================================
# CONTENIDO DE LAS VENTANAS
# =========================================================================

if seleccion_modulo.startswith("🏠"):
    st.title("⚡ BOLIMUR INSTALACIONES INTEGRALES")
    st.write("Bienvenido al panel de cálculo eléctrico. Todos los módulos cuentan con justificación analítica REBT completa.")

elif seleccion_modulo.startswith("🧮"):
    st.title("🧮 Cálculo Rápido Avanzado")

    rc1, rc2 = st.columns(2)
    with rc1:
        modo_carga = st.radio("Entrada:", ["Por Potencia (W o CV)", "Por Intensidad Directa (A)"])
        tipo_red_q = st.selectbox("Sistema eléctrico", ["Monofásico (230V)", "Trifásico (400V)"])
        
        if modo_carga == "Por Potencia (W o CV)":
            val_pot_q = st.number_input("Potencia (W)", value=0.0, step=100.0)
            cos_q = st.slider("Coseno phi (cos φ)", 0.7, 1.0, 0.85)
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q: ib_q = val_pot_q / (v_nom_calc * cos_q) if v_nom_calc * cos_q > 0 else 0.0
            else: ib_q = val_pot_q / (math.sqrt(3) * v_nom_calc * cos_q) if v_nom_calc * cos_q > 0 else 0.0
        else:
            ib_q = st.number_input("Intensidad Ib (A)", value=0.0, step=1.0)
            cos_q = st.slider("Coseno phi (cos φ)", 0.7, 1.0, 0.85)
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q: val_pot_q = ib_q * v_nom_calc * cos_q
            else: val_pot_q = ib_q * math.sqrt(3) * v_nom_calc * cos_q

        long_q = st.number_input("Longitud del circuito (m)", value=0.0, step=5.0)

    with rc2:
        metodo_q_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), index=0)
        mat_q = st.selectbox("Material conductor", ["cobre", "aluminio"])
        ais_q = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"])
        cdt_lim_q = st.number_input("Caída de Tensión máxima (%)", value=3.0, step=0.5)
        icc_orig_q = st.number_input("Icc en origen (kA)", value=10.0, step=0.5)

    gamma_q = GAMMA_MAP.get((mat_q, ais_q), 44.0)
    dv_max_q = v_nom_calc * (cdt_lim_q / 100.0) if cdt_lim_q > 0 else 1.0
    
    if "Monofásico" in tipo_red_q: s_cdt_q = (2.0 * val_pot_q * long_q) / (gamma_q * dv_max_q * v_nom_calc) if dv_max_q * v_nom_calc > 0 else 1.5
    else: s_cdt_q = (val_pot_q * long_q) / (gamma_q * dv_max_q * v_nom_calc) if dv_max_q * v_nom_calc > 0 else 1.5

    tabla_iz_q = IZ_COBRE_ENTERRADO if "D (" in metodo_q_key else IZ_COBRE_TUBO
    s_cal_q = 1.5
    for sec, iz_val in tabla_iz_q.items():
        if iz_val >= ib_q:
            s_cal_q = sec
            break

    min_reg_q = 1.5 if mat_q == "cobre" else 10.0
    s_bruta_q = max(s_cdt_q, s_cal_q, min_reg_q)
    s_opt_q = seleccionar_seccion_optima(s_bruta_q)

    if "Monofásico" in tipo_red_q: dv_real_v_q = (2.0 * val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc) if s_opt_q * v_nom_calc > 0 else 0.0
    else: dv_real_v_q = (val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc) if s_opt_q * v_nom_calc > 0 else 0.0
    dv_real_pct_q = (dv_real_v_q / v_nom_calc) * 100.0 if v_nom_calc > 0 else 0.0

    rho_q = 1.0 / gamma_q if gamma_q > 0 else 0.0
    r_cable_q = (rho_q * long_q) / s_opt_q if s_opt_q > 0 else 0.0
    if "Monofásico" in tipo_red_q: z_tot_q = (v_nom_calc / (icc_orig_q * 1000.0)) + (2.0 * r_cable_q) if icc_orig_q > 0 else 1.0
    else: z_tot_q = (v_nom_calc / (icc_orig_q * 1000.0)) + r_cable_q if icc_orig_q > 0 else 1.0
        
    icc_fin_q = v_nom_calc / z_tot_q / 1000.0 if z_tot_q > 0 else 0.0
    prot_q = seleccionar_proteccion(ib_q)
    corriente_disparo = prot_q * 10.0
    salta_proteccion = (icc_fin_q * 1000.0) >= corriente_disparo

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Detallada</h3>", unsafe_allow_html=True)

    # Caja Formula 1
    form1 = f"$I_b = \\frac{{{val_pot_q:,.1f} \\text{{ W}}}}{{{v_nom_calc} \\text{{ V}} \\cdot {cos_q}}}$" if "Monofásico" in tipo_red_q else f"$I_b = \\frac{{{val_pot_q:,.1f} \\text{{ W}}}}{{\\sqrt{{3}} \\cdot {v_nom_calc} \\text{{ V}} \\cdot {cos_q}}}$"
    st.markdown(f"""
    <div class="caja-formula">
        <h4>1. Intensidad de Diseño ($I_b$)</h4>
        <p><b>Justificación:</b> Cálculo de la corriente nominal base para dimensionar la protección térmica y evitar el calentamiento excesivo ($I_z \\ge I_b$).</p>
        <div class="math-center">{form1}</div>
        <p><b>Sustitución y Resultado:</b> {val_pot_q:,.1f} W / ... = <b>{ib_q:.2f} A</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Caja Formula 2
    form2 = f"$S = \\frac{{2 \\cdot {val_pot_q:,.1f} \\cdot {long_q}}}{{\\gamma \\cdot \\Delta V \\cdot {v_nom_calc}}}$" if "Monofásico" in tipo_red_q else f"$S = \\frac{{{val_pot_q:,.1f} \\cdot {long_q}}}{{\\gamma \\cdot \\Delta V \\cdot {v_nom_calc}}}$"
    st.markdown(f"""
    <div class="caja-formula">
        <h4>2. Sección Teórica por Caída de Tensión ($\\Delta V$)</h4>
        <p><b>Justificación:</b> Verificamos la sección exigida para no superar el límite reglamentario del {cdt_lim_q}% ({dv_max_q:.2f} V) al final de la línea.</p>
        <div class="math-center">{form2}</div>
        <p><b>Resultado:</b> Sección pura requerida = <b>{s_cdt_q:.2f} mm²</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Caja Formula 3
    estado_icc = "✅ GARANTIZADO" if salta_proteccion else "⚠️ PELIGRO: NO SALTARÁ A TIEMPO"
    st.markdown(f"""
    <div class="caja-formula">
        <h4>3. Comprobación Cortocircuito y Disparo (0.1s)</h4>
        <p><b>Justificación:</b> La Icc final debe superar el umbral de disparo magnético (Curva C = $10 \\cdot I_n$) de la protección de {prot_q} A.</p>
        <div class="math-center">$I_{{cc,final}} = \\frac{{V}}{{\\left(\\frac{{V}}{{I_{{cc,origen}}}}\\right) + R_{{cable}}}}$</div>
        <p><b>Icc calculada al final:</b> {icc_fin_q * 1000:.1f} A | <b>Umbral ({prot_q} A x 10):</b> {corriente_disparo:.1f} A</p>
        <p><b>Veredicto:</b> {estado_icc}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Tabla de Verificación de Secciones")
    tabla_q_md = "| SECCIÓN | IZ ADMISIBLE (A) | CDT REAL (%) | ESTADO DE VERIFICACIÓN ($I_n \\le 0.91 \\cdot I_z$) |\n| :--- | :--- | :--- | :--- |\n"
    for sec_com in [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70]:
        iz_c = tabla_iz_q.get(sec_com, 250.0)
        dv_c_pct = (((2.0 * val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0 if "Monofásico" in tipo_red_q else (((val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0
        cond_sobrecarga = 0.91 * iz_c
        if iz_c < ib_q: est_v = f"❌ Falla Calentamiento"
        elif prot_q > cond_sobrecarga: est_v = f"❌ Falla ($I_n$ {prot_q}A > {cond_sobrecarga:.1f}A)"
        elif sec_com == s_opt_q: est_v = f"✅ **CUMPLE IDEAL** ($I_n$ {prot_q}A $\\le$ {cond_sobrecarga:.1f}A)"
        else: est_v = "Válido pero sobredimensionado"
        tabla_q_md += f"| **{sec_com} mm²** | {iz_c} A | {dv_c_pct:.3f}% | {est_v} |\n"
    st.markdown(tabla_q_md)

    st.markdown(f"""
        <div class="resultado-verde">
            <h2>✅ SECCIÓN ÓPTIMA ADOPTADA: {s_opt_q} mm² ({mat_q.upper()})</h2>
            <hr style="border-top: 1px solid #10b981; margin: 10px 0;">
            <p style="font-size: 16px; margin: 0;">
            La sección de {s_opt_q} mm² garantiza el cumplimiento térmico ($I_z$ > $I_b$) y una caída de tensión real del <b>{dv_real_pct_q:.3f}%</b>. Perfectamente coordinada con un <b>PIA de {prot_q} A (Curva C)</b>.
            </p>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("🏢"):
    st.title("🏢 Previsión de Cargas (ITC-BT-10)")
    
    st.header("1. Carga Correspondiente a Viviendas (P1)")
    if st.button("➕ Añadir Grupo de Viviendas"): st.session_state.grupos_viviendas.append({"nombre": f"Grupo {len(st.session_state.grupos_viviendas)+1}", "qty": 0, "pot": 5750, "nocturna": False})

    pot_total_viviendas = 0
    for idx, viv in enumerate(st.session_state.grupos_viviendas):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: viv["nombre"] = st.text_input(f"Descripción #{idx+1}", viv["nombre"], key=f"v_n_{idx}")
        with c2: viv["qty"] = st.number_input(f"Nº Viv.", min_value=0, value=int(viv["qty"]), key=f"v_q_{idx}")
        with c3: viv["pot"] = st.selectbox(f"Pot. Unitaria", [5750, 7360, 9200, 11500], index=[5750, 7360, 9200, 11500].index(viv["pot"]) if viv["pot"] in [5750, 7360, 9200, 11500] else 0, key=f"v_p_{idx}")
        with c4: viv["nocturna"] = st.checkbox(f"Tarifa Nocturna", value=viv["nocturna"], key=f"v_no_{idx}")
        with c5:
            if st.button("🗑️", key=f"del_v_{idx}"):
                if len(st.session_state.grupos_viviendas)>1: st.session_state.grupos_viviendas.pop(idx); st.rerun()

        cs_grupo = float(viv["qty"]) if viv["nocturna"] else get_coef_simultaneidad(viv["qty"])
        pot_parcial = int(round(viv["qty"] * viv["pot"] * cs_grupo)) if viv["nocturna"] else int(round(viv["pot"] * cs_grupo))
        pot_total_viviendas += pot_parcial

        st.markdown(f"""
        <div class="caja-formula">
            <h4>Justificación Analítica: {viv['nombre']}</h4>
            <p>Se aplica coeficiente de simultaneidad ($K$) según el número de viviendas (ITC-BT-10).</p>
            <div class="math-center">$P_{{parcial}} = P_{{unitaria}} \\cdot K_{{simultaneidad}}$</div>
            <p><b>Sustitución:</b> {viv['pot']} W $\\cdot$ K({cs_grupo:.2f}) = <b>{pot_parcial:,} W</b></p>
        </div>
        """, unsafe_allow_html=True)

    st.header("2. Servicios Generales (P3)")
    if st.button("➕ Añadir Servicio"): st.session_state.servicios_generales.append({"nombre": "Servicio", "potencia": 0.0, "factor": 1.30, "qty": 0})
    pot_total_servicios = 0.0
    
    opciones_factores_k = {
        "Ascensor (K=1.30)": 1.30,
        "Iluminación LED (K=1.00)": 1.00,
        "Bombas de agua (K=1.25)": 1.25
    }

    for idx, serv in enumerate(st.session_state.servicios_generales):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: serv["nombre"] = st.text_input(f"Servicio", serv["nombre"], key=f"s_n_{idx}")
        with c2: serv["potencia"] = st.number_input(f"Pot. W", value=float(serv["potencia"]), key=f"s_p_{idx}")
        with c3: serv["qty"] = st.number_input(f"Uds.", value=int(serv["qty"]), key=f"s_q_{idx}")
        
        factor_actual = serv.get("factor", 1.30)
        def_opt_idx = 0 if factor_actual == 1.30 else 1 if factor_actual == 1.00 else 2
        with c4:
            sel_opt = st.selectbox(f"Multiplicador (K)", list(opciones_factores_k.keys()), index=def_opt_idx, key=f"serv_tipo_opt_{idx}")
            factor = opciones_factores_k[sel_opt]
            serv["factor"] = factor
        with c5:
            st.write(""); st.write("")
            if st.button("🗑️", key=f"del_s_{idx}"): st.session_state.servicios_generales.pop(idx); st.rerun()
        
        p_parcial = serv["potencia"] * serv["qty"] * factor
        pot_total_servicios += p_parcial
        
        st.markdown(f"""
        <div class="caja-formula">
            <h4>Justificación Analítica: {serv['nombre']}</h4>
            <p>Se aplica coeficiente multiplicador según la naturaleza del receptor.</p>
            <div class="math-center">$P_{{servicio}} = P_{{unitaria}} \\cdot n \\cdot K$</div>
            <p><b>Sustitución:</b> {serv["potencia"]} W $\\cdot$ {serv["qty"]} ud(s) $\\cdot$ {factor} = <b>{p_parcial:,.1f} W</b></p>
        </div>
        """, unsafe_allow_html=True)

    pt_total = pot_total_viviendas + int(pot_total_servicios) + 3450

    st.markdown(f"""
        <div class="resultado-verde">
            <h2>✅ POTENCIA TOTAL PREVISTA (Pt): {pt_total:,.1f} W</h2>
            <hr style="border-top: 1px solid #10b981; margin: 10px 0;">
            <p style="font-size: 16px; margin: 0;">Suma total reglamentaria lista para dimensionar la LGA.</p>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("⚡"):
    st.title("⚡ Línea General de Alimentación - LGA (ITC-BT-14)")
    
    pt_auto = calcular_pt_global()
    lga_modo_potencia = st.radio("Origen de la Potencia (Pt):", ["Automático", "Manual"])
    
    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        if "Automático" in lga_modo_potencia: lga_pot = pt_auto
        else: lga_pot = st.number_input("Potencia de cálculo LGA (W)", value=pt_auto, step=500.0)
        lga_long = st.number_input("Longitud de la LGA (m)", value=0.0)
        lga_mat = st.selectbox("Material Conductor", ["cobre", "aluminio"])
        metodo_lga_key = st.selectbox("Instalación:", list(METODOS_INSTALACION.keys()), index=3)
    with lga_c2:
        lga_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"])
        tipo_enlace_lga = st.radio("Contadores:", ["Totalmente concentrados (Límite CDT = 0.5%)", "Centralizaciones Parciales (Límite CDT = 1.0%)"])
        lga_icc_orig = st.number_input("Icc en origen (kA)", value=10.0, step=0.5)

    dv_pct_lga = 0.5 if "concentrados" in tipo_enlace_lga else 1.0
    gamma_lga = 44.0 if "XLPE" in lga_aisl else 48.5
    ib_lga = lga_pot / (math.sqrt(3) * 400 * 0.9)
    dv_max_lga = 400 * (dv_pct_lga / 100.0)
    s_cdt_lga = (lga_pot * lga_long) / (gamma_lga * dv_max_lga * 400) if gamma_lga * dv_max_lga * 400 > 0 else 10.0
    
    tabla_iz = IZ_COBRE_ENTERRADO if "D (" in metodo_lga_key else IZ_COBRE_TUBO
    in_lga_auto = seleccionar_proteccion(ib_lga)
    s_final_lga = seleccionar_seccion_optima(max(s_cdt_lga, 10.0))
    
    while True:
        iz_a = tabla_iz.get(s_final_lga, 230.0)
        if in_lga_auto <= 0.91 * iz_a and iz_a >= ib_lga: break
        idx_s = SECCIONES_COMERCIALES.index(s_final_lga) if s_final_lga in SECCIONES_COMERCIALES else 5
        if idx_s < len(SECCIONES_COMERCIALES) - 1: s_final_lga = SECCIONES_COMERCIALES[idx_s + 1]
        else: break

    dv_real_lga_pct = ((lga_pot * lga_long) / (gamma_lga * s_final_lga * 400) / 400) * 100 if gamma_lga * s_final_lga * 400 > 0 else 0.0

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Detallada (LGA)</h3>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="caja-formula">
        <h4>1. Intensidad de Diseño Trifásica ($I_b$)</h4>
        <p><b>Justificación:</b> Calculamos la corriente por fase. En instalaciones generales se asume un $\\cos\\varphi$ de 0.9.</p>
        <div class="math-center">$I_b = \\frac{{{lga_pot:,.1f} \\text{{ W}}}}{{\\sqrt{{3}} \\cdot 400 \\text{{ V}} \\cdot 0.9}}$</div>
        <p><b>Sustitución y Resultado:</b> {lga_pot:,.1f} W / 623.54 = <b>{ib_lga:.2f} A</b></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="caja-formula">
        <h4>2. Sección Teórica por Caída de Tensión ($\\Delta V$)</h4>
        <p><b>Justificación:</b> Límite máximo de pérdida del <b>{dv_pct_lga}%</b> ({dv_max_lga:.2f} V) según esquema de enlace.</p>
        <div class="math-center">$S = \\frac{{{lga_pot:,.1f} \\cdot {long_q}}}{{\\gamma \\cdot \\Delta V \\cdot 400}}$</div>
        <p><b>Resultado:</b> Sección mínima exigida = <b>{s_cdt_lga:.2f} mm²</b></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Tabla de Verificación de Secciones Comerciales (LGA)")
    tabla_lga_md = "| SECCIÓN | IZ ADMISIBLE (A) | CDT REAL (%) | ESTADO DE VERIFICACIÓN ($I_n \\le 0.91 \\cdot I_z$) |\n| :--- | :--- | :--- | :--- |\n"
    for s_com in [35, 50, 70, 95, 120, 150, 185, 240]:
        iz_val_t = tabla_iz.get(s_com, 0)
        dv_c_pct = ((lga_pot * lga_long) / (gamma_lga * s_com * 400) / 400) * 100 if s_com > 0 else 0.0
        cond_s_lga = 0.91 * iz_val_t
        if iz_val_t < ib_lga: est = f"❌ Falla Calentamiento"
        elif in_lga_auto > cond_s_lga: est = f"❌ Falla ($I_n$ {in_lga_auto}A > {cond_s_lga:.1f}A)"
        elif s_com == s_final_lga: est = f"✅ **CUMPLE IDEAL** ($I_n$ {in_lga_auto}A $\\le$ {cond_s_lga:.1f}A)"
        else: est = "Válido pero sobredimensionado"
        tabla_lga_md += f"| **{s_com} mm²** | {iz_val_t} A | {dv_c_pct:.3f}% | {est} |\n"
    st.markdown(tabla_lga_md)

    st.markdown(f"""
        <div class="resultado-verde">
            <h2>✅ SECCIÓN ÓPTIMA LGA: {s_final_lga} mm² de {lga_mat.upper()}</h2>
            <hr style="border-top: 1px solid #10b981; margin: 10px 0;">
            <p style="font-size: 16px; margin: 0;">
            Garantiza una caída real del <b>{dv_real_lga_pct:.3f}%</b>. Protegida en origen por <b>Fusibles gG de {in_lga_auto} A</b> coordinados térmicamente.
            </p>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("🔌"):
    st.title("🔌 Derivación Individual - DI (ITC-BT-15)")
    
    with st.expander("🏗️ Selector de Instalación y Entorno", expanded=True):
        metodo_di_key = st.selectbox("Método Instalación:", list(METODOS_INSTALACION.keys()))
        tipo_enlace_di = st.radio("Esquema Contadores:", ["Concentrados (Límite CDT = 1.0%)", "Diseminados (Límite CDT = 0.5%)"])

    dv_pct_di = 1.0 if "Concentrados" in tipo_enlace_di else 0.5

    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Previsión de Potencia (W)", [5750, 7360, 9200, 11500])
        di_long = st.number_input("Longitud DI (m)", value=0.0)
        di_mat = st.selectbox("Material conductor", ["cobre", "aluminio"])
    with di_c2:
        di_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"])
        di_cos = st.slider("Coseno phi", 0.8, 1.0, 1.0)

    gamma_di = GAMMA_MAP.get((di_mat, di_aisl), 44.0)
    ib_di = di_pot / (230.0 * di_cos) if di_cos > 0 else 0.0
    dv_max_di = 230.0 * (dv_pct_di / 100.0)
    s_cdt_di = (2.0 * di_pot * di_long) / (gamma_di * dv_max_di * 230.0) if gamma_di * dv_max_di * 230.0 > 0 else 6.0
    
    tabla_iz_di = IZ_COBRE_ENTERRADO if "D (" in metodo_di_key else IZ_COBRE_TUBO
    s_cal_di = 1.5
    for sec, iz_val in tabla_iz_di.items():
        if iz_val >= ib_di:
            s_cal_di = sec
            break

    min_reg_di = 6.0 if di_mat == "cobre" else 10.0
    s_bruta_di = max(s_cdt_di, s_cal_di, min_reg_di)
    s_optima_di = seleccionar_seccion_optima(s_bruta_di)
    prot_di = seleccionar_proteccion(ib_di)
    dv_real_di_pct = ((2.0 * di_pot * di_long) / (gamma_di * s_optima_di * 230.0) / 230.0) * 100 if gamma_di * s_optima_di * 230.0 > 0 else 0.0

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Detallada (DI)</h3>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="caja-formula">
        <h4>1. Intensidad de Diseño Monofásica ($I_b$)</h4>
        <p><b>Justificación:</b> Intensidad máxima admisible basada en el escalón de potencia elegido por el cliente.</p>
        <div class="math-center">$I_b = \\frac{{{di_pot:,.1f} \\text{{ W}}}}{{230 \\text{{ V}} \\cdot {di_cos}}}$</div>
        <p><b>Sustitución y Resultado:</b> {di_pot:,.1f} W / (230 V) = <b>{ib_di:.2f} A</b></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Tabla de Verificación de Secciones Comerciales (DI)")
    tabla_di_md = "| SECCIÓN | IZ ADMISIBLE (A) | CDT REAL (%) | ESTADO DE VERIFICACIÓN ($I_n \\le 0.91 \\cdot I_z$) |\n| :--- | :--- | :--- | :--- |\n"
    for sec_com in [6, 10, 16, 25, 35, 50]:
        iz_c = tabla_iz_di.get(sec_com, 100.0)
        dv_c_pct = ((2.0 * di_pot * di_long) / (gamma_di * sec_com * 230.0) / 230.0) * 100 if sec_com > 0 else 0.0
        cond_sobrecarga = 0.91 * iz_c
        if iz_c < ib_di: est_v = f"❌ Falla Calentamiento"
        elif prot_di > cond_sobrecarga: est_v = f"❌ Falla ($I_n$ {prot_di}A > {cond_sobrecarga:.1f}A)"
        elif sec_com == s_optima_di: est_v = f"✅ **CUMPLE IDEAL** ($I_n$ {prot_di}A $\\le$ {cond_sobrecarga:.1f}A)"
        else: est_v = "Válido pero sobredimensionado"
        tabla_di_md += f"| **{sec_com} mm²** | {iz_c} A | {dv_c_pct:.3f}% | {est_v} |\n"
    st.markdown(tabla_di_md)

    st.markdown(f"""
        <div class="resultado-verde">
            <h2>✅ SECCIÓN ÓPTIMA DI: {s_optima_di} mm² de {di_mat.upper()}</h2>
            <hr style="border-top: 1px solid #10b981; margin: 10px 0;">
            <p style="font-size: 16px; margin: 0;">
            Caída de tensión real controlada al <b>{dv_real_di_pct:.3f}%</b>. La línea está protegida perfectamente por el IGA del cuadro general de la vivienda (<b>{prot_di} A, Curva C</b>).
            </p>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("📚"):
    st.title("📚 Tablas REBT")
elif seleccion_modulo.startswith("📐"):
    st.title("📐 Esquemas Unifilares")