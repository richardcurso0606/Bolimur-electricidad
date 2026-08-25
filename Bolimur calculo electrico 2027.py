import streamlit as st
import math
import json
import os
import sqlite3

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BOLIMUR INSTALACIONES INTEGRALES", page_icon="⚡", layout="wide")

# --- GESTIÓN DE BASE DE DATOS LOCAL (PERFIL Y CONFIGURACIÓN) ---
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
    except sqlite3.OperationalError: row = None
    conn.close()
    if row: return row[0], row[1]
    return "proyecto_bolimur_default.json", "proyectos_bolimur"

perfil_guardado = cargar_datos_instalador()
ultimo_archivo_db, carpeta_trabajo_db = cargar_config_proyecto()

# --- DISEÑO LUMINOSO Y AMIGABLE PARA MÓVILES (Fuerza contraste claro) ---
st.markdown("""
    <style>
    /* Tablas modernas y claras */
    table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 14px; background-color: #ffffff !important; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    th { background-color: #f0f2f6 !important; color: #1f2937 !important; text-align: left; padding: 12px !important; border-bottom: 2px solid #e5e7eb !important; font-weight: bold; }
    td { padding: 12px !important; border-bottom: 1px solid #e5e7eb !important; color: #374151 !important; background-color: #ffffff !important; }
    tr:nth-child(even) td { background-color: #f9fafb !important; }

    /* Cajas de resultados luminosas */
    .resultado-destacado {
        background-color: #ffffff; color: #1f2937; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #ef4444; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-top: 1px solid #f3f4f6; border-right: 1px solid #f3f4f6; border-bottom: 1px solid #f3f4f6;
    }
    .pia-destacado {
        background: #e0f2fe; color: #0369a1; padding: 18px 25px; border-radius: 12px; 
        font-size: 20px; font-weight: bold; text-align: center; margin: 15px 0; 
        border: 2px solid #7dd3fc; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .fusible-vistoso {
        background: #ffedd5; color: #c2410c; padding: 18px 25px; border-radius: 12px; 
        font-size: 20px; font-weight: bold; text-align: center; margin: 15px 0; 
        border: 2px solid #fdba74; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .resumen-parciales-box {
        background-color: #ffffff; border: 2px solid #10b981; padding: 20px; border-radius: 12px; 
        margin: 20px 0; color: #1f2937; box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    .formula-box {
        background-color: #ffffff; border: 1px solid #e5e7eb; border-left: 5px solid #0ea5e9; 
        padding: 18px; border-radius: 10px; margin: 12px 0; color: #374151; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* Panel lateral estilizado */
    [data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# --- CONSTANTES Y TABLAS REBT ---
COEF_SIMULTANEIDAD_VIVIENDAS = {1: 1.0, 2: 2.0, 3: 3.0, 4: 3.8, 5: 4.6, 6: 5.4, 7: 6.2, 8: 7.0, 9: 7.8, 10: 8.5, 11: 9.2, 12: 9.9, 13: 10.6, 14: 11.3, 15: 11.9, 16: 12.5, 17: 13.1, 18: 13.7, 19: 14.3, 20: 14.8, 21: 15.3}
def get_coef_simultaneidad(num):
    if num <= 0: return 0.0
    if num <= 21: return COEF_SIMULTANEIDAD_VIVIENDAS.get(num, 15.3)
    return float(round(15.3 + (num - 21) * 0.5, 1))

METODOS_INSTALACION = {
    "B1 (Bajo tubo empotrado en pared aislante)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas"},
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Cable multiconductor fijado directo)": {"ref": "C", "desc": "Cable multiconductor en superficie o empotrado"},
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
if 'nombre_proyecto' not in st.session_state: st.session_state.nombre_proyecto = "Estudio Eléctrico Edificio"
if 'grupos_viviendas' not in st.session_state: st.session_state.grupos_viviendas = [{"nombre": "Viviendas Estándar", "qty": 0, "pot": 5750, "nocturna": False}]
if 'servicios_generales' not in st.session_state: st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 0, "potencia": 0.0, "factor": 1.30}]
if 'locales' not in st.session_state: st.session_state.locales = [{"nombre": "Local Comercial A", "qty": 0, "superficie": 0.0}]
if 'carpeta_trabajo_val' not in st.session_state: st.session_state.carpeta_trabajo_val = carpeta_trabajo_db

def calcular_pt_global():
    p_viv = sum(int(round(v["qty"] * v["pot"] * (v["qty"] if v["nocturna"] else get_coef_simultaneidad(v["qty"])))) for v in st.session_state.grupos_viviendas)
    p_loc = sum(max(l["superficie"] * 100.0, 3450.0 if l["superficie"] > 0 else 0.0) * l["qty"] for l in st.session_state.locales)
    p_serv = sum(s["potencia"] * s["qty"] * s.get("factor", 1.30) for s in st.session_state.servicios_generales)
    return float(p_viv + int(p_loc) + int(p_serv) + 3450)

# --- MENÚ LATERAL ---
with st.sidebar:
    if os.path.exists("logo_bolimur.PNG"): st.image("logo_bolimur.PNG", use_container_width=True)
    else:
        st.markdown("""
            <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid #ef4444; margin-bottom: 15px; text-align: center;">
                <h3 style="color: white; margin: 0; font-size: 18px;">⚡ BOLIMUR</h3>
                <p style="color: #94a3b8; font-size: 12px; margin: 5px 0 0 0;">Instalaciones Integrales</p>
            </div>
        """, unsafe_allow_html=True)

    st.header("📂 Navegación de Módulos")
    seleccion_modulo = st.radio("Selecciona la sección:", [
        "🏠 Menú Principal", "🧮 Cálculo Rápido (CDT & Icc)", "🏢 Previsión de Cargas (Pt)", 
        "⚡ Línea General (LGA)", "🔌 Derivación Individual (DI)", "📚 Compendio Tablas REBT", 
        "📐 Esquemas Unifilares", "💡 Simulador Consumo"
    ], label_visibility="collapsed")

    st.markdown("---")
    with st.expander("⚙️ Perfil Instalador"):
        inst_nombre = st.text_input("Nombre", perfil_guardado["nombre"])
        inst_empresa = st.text_input("Empresa", perfil_guardado["empresa"])
        if st.button("💾 Guardar"): st.success("Guardado")

# =========================================================================
# CONTENIDO DE LAS VENTANAS
# =========================================================================

if seleccion_modulo.startswith("🏠"):
    st.title("⚡ BOLIMUR INSTALACIONES INTEGRALES")
    st.write("Bienvenido al panel de cálculo eléctrico REBT. Selecciona cualquier módulo en la barra lateral.")
    st.info("💡 **Tip para Móviles:** Si ves el fondo oscuro, puedes cambiarlo al modo luminoso yendo al menú superior derecho de tu navegador (⋮), pulsando en **Settings** y seleccionando **Light Theme**.")

elif seleccion_modulo.startswith("🧮"):
    st.title("🧮 Cálculo Rápido Avanzado (Bombas y Líneas Largas)")

    rc1, rc2 = st.columns(2)
    with rc1:
        modo_carga = st.radio("Modo de entrada:", ["Por Potencia (W o CV)", "Por Intensidad Directa (A)"])
        tipo_red_q = st.selectbox("Sistema eléctrico", ["Monofásico (230V)", "Trifásico (400V)"])
        
        if modo_carga == "Por Potencia (W o CV)":
            val_pot_q = st.number_input("Potencia activa (W)", value=0.0, step=100.0)
            cos_q = st.slider("Coseno phi (cos phi)", 0.7, 1.0, 0.85)
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q: ib_q = val_pot_q / (v_nom_calc * cos_q) if v_nom_calc * cos_q > 0 else 0.0
            else: ib_q = val_pot_q / (math.sqrt(3) * v_nom_calc * cos_q) if v_nom_calc * cos_q > 0 else 0.0
        else:
            ib_q = st.number_input("Intensidad de diseño Ib (A)", value=0.0, step=1.0)
            cos_q = st.slider("Coseno phi", 0.7, 1.0, 0.85)
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q: val_pot_q = ib_q * v_nom_calc * cos_q
            else: val_pot_q = ib_q * math.sqrt(3) * v_nom_calc * cos_q

        long_q = st.number_input("Longitud del circuito / tirada (m) [Ida]", value=0.0, step=5.0)

    with rc2:
        metodo_q_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), index=0)
        mat_q = st.selectbox("Material conductor", ["cobre", "aluminio"])
        ais_q = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"])
        cdt_lim_q = st.number_input("Caída de Tensión máxima (%)", value=3.0, step=0.5)
        icc_orig_q = st.number_input("Icc en origen (kA)", value=10.0, step=0.5, format="%.2f")

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
    corriente_disparo_magnetico = prot_q * 10.0
    salta_proteccion = (icc_fin_q * 1000.0) >= corriente_disparo_magnetico

    st.markdown("---")
    st.subheader("Memoria Justificativa Analítica")

    st.markdown("### 1. Intensidad de Diseño (Ib):")
    st.latex(r"I_b = \frac{P}{V \cdot \cos\varphi} \quad (\text{Monofásico}) \quad \text{o} \quad I_b = \frac{P}{\sqrt{3} \cdot V \cdot \cos\varphi} \quad (\text{Trifásico})")
    st.markdown(f"• Sustitución: **{val_pot_q:,.1f} W / ({v_nom_calc} V * {cos_q}) = {ib_q:.2f} A**")

    st.markdown("### 2. Sección por Caída de Tensión (Delta V):")
    st.latex(r"S = \frac{2 \cdot P \cdot L}{\gamma \cdot \Delta V \cdot V} \quad (\text{Monofásico}) \quad \text{o} \quad S = \frac{P \cdot L}{\gamma \cdot \Delta V \cdot V} \quad (\text{Trifásico})")
    st.markdown(f"• Cálculo teórico puro obtenido: **{s_cdt_q:.2f} mm²**")

    st.markdown("### 3. Comprobación por Cortocircuito y Disparo Magnético:")
    st.latex(r"I_{\text{cc,final}} = \frac{V}{Z_{\text{total}}} = \frac{V}{\left(\frac{V}{I_{\text{cc,origen}}}\right) + R_{\text{cable}}}")
    st.markdown(f"• Icc al final del circuito: **{icc_fin_q * 1000:.1f} A ({icc_fin_q:.2f} kA)**.")
    st.latex(r"I_{\text{disparo}} = 10 \cdot I_n \quad (\text{Curva C standard})")
    st.markdown(f"• Umbral magnético (PIA {prot_q} A): {prot_q} A x 10 = **{corriente_disparo_magnetico:.1f} A**.")
    st.markdown(f"• Estado del disparo: **{'✅ GARANTIZADO INSTANTÁNEO' if salta_proteccion else '⚠️ ATENCIÓN: Icc insuficiente'}**.")

    st.markdown(f"""<div class="pia-destacado">🛡️ PROTECCIÓN RECOMENDADA: {prot_q} A (Curva C) + Diferencial 30 mA</div>""", unsafe_allow_html=True)

    st.markdown("### Tabla Detallada de Verificación (Sobrecarga e Iz >= Ib)")
    tabla_q_md = "| Sección (mm²) | Iz (A) | CDT Real (%) | Verificación ($I_n \le 0.91 \cdot I_z$) |\n| :---: | :---: | :---: | :--- |\n"
    for sec_com in [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70]:
        iz_c = tabla_iz_q.get(sec_com, 250.0)
        dv_c_pct = (((2.0 * val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0 if "Monofásico" in tipo_red_q else (((val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0
        cond_sobrecarga = 0.91 * iz_c
        if iz_c < ib_q: est_v = f"❌ Falla por calentamiento"
        elif prot_q > cond_sobrecarga: est_v = f"❌ Falla 2ª condición"
        elif sec_com == s_opt_q: est_v = f"✅ **CUMPLE IDEAL** (In {prot_q}A <= {cond_sobrecarga:.1f}A)"
        else: est_v = "Válido pero superior"
        tabla_q_md += f"| {sec_com} mm² | {iz_c} A | {dv_c_pct:.3f}% | {est_v} |\n"
    st.markdown(tabla_q_md)

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ CONCLUSIÓN Y SECCIÓN ÓPTIMA: <span style="color: #ef4444; font-size: 22px;">{s_opt_q} mm²</span> de {mat_q.upper()} ({ais_q})<br>
            <span style="font-size: 15px; color: #6b7280; font-weight: normal;"><br>
            1. <b>Calentamiento:</b> Soporta {tabla_iz_q.get(s_opt_q, 0)} A frente a los {ib_q:.2f} A de servicio.<br>
            2. <b>Caída de Tensión:</b> {dv_real_pct_q:.3f}% (límite {cdt_lim_q}%).<br>
            3. <b>Coordinación:</b> PIA de {prot_q} A protege el aislamiento perfectamente.
            </span>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("🏢"):
    st.title("Previsión de Cargas del Edificio (ITC-BT-10)")
    
    col_t1, col_b1 = st.columns([4, 1])
    with col_t1: st.write("Desarrollo analítico de coeficientes y potencias normativas.")
    with col_b1:
        if st.button("🔄 Resetear"): st.session_state.grupos_viviendas = [{"nombre": "Grupo 1", "qty": 0, "pot": 5750, "nocturna": False}]; st.rerun()

    st.subheader("1. Viviendas del Edificio (P1)")
    if st.button("➕ Añadir Viviendas"): st.session_state.grupos_viviendas.append({"nombre": f"Grupo {len(st.session_state.grupos_viviendas)+1}", "qty": 0, "pot": 5750, "nocturna": False})

    pot_total_viviendas = 0
    for idx, viv in enumerate(st.session_state.grupos_viviendas):
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
        with c1: viv["nombre"] = st.text_input(f"Descripción #{idx+1}", viv["nombre"], key=f"v_n_{idx}")
        with c2: viv["qty"] = st.number_input(f"Nº Viv.", min_value=0, value=int(viv["qty"]), key=f"v_q_{idx}")
        with c3: viv["pot"] = st.selectbox(f"Potencia", [5750, 7360, 9200, 11500], index=[5750, 7360, 9200, 11500].index(viv["pot"]) if viv["pot"] in [5750, 7360, 9200, 11500] else 0, key=f"v_p_{idx}")
        with c4: viv["nocturna"] = st.checkbox(f"Nocturna", value=viv["nocturna"], key=f"v_no_{idx}")
        with c5:
            if st.button("🗑️", key=f"del_v_{idx}"):
                if len(st.session_state.grupos_viviendas)>1: st.session_state.grupos_viviendas.pop(idx); st.rerun()

        cs_grupo = float(viv["qty"]) if viv["nocturna"] else get_coef_simultaneidad(viv["qty"])
        pot_parcial = int(round(viv["qty"] * viv["pot"] * cs_grupo)) if viv["nocturna"] else int(round(viv["pot"] * cs_grupo))
        pot_total_viviendas += pot_parcial

        st.markdown(f"**Justificación Grupo #{idx+1}:**")
        st.latex(r"P_{\text{parcial}} = P_{\text{unitaria}} \cdot K_{\text{simultaneidad}}")
        st.markdown(f"• Cálculo: {viv['pot']} W x K({cs_grupo:.2f}) = **{pot_parcial:,} W**")

    st.info(f"💡 **Total P1 (Viviendas): {pot_total_viviendas:,} W**")
    st.markdown("---")
    
    st.subheader("2. Locales Comerciales (P2)")
    if st.button("➕ Añadir Local"): st.session_state.locales.append({"nombre": f"Local {len(st.session_state.locales)+1}", "superficie": 0.0, "qty": 0})
    pot_total_locales = 0.0
    for idx, loc in enumerate(st.session_state.locales):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        with c1: loc["nombre"] = st.text_input(f"Local", loc["nombre"], key=f"l_n_{idx}")
        with c2: loc["superficie"] = st.number_input(f"Sup. m²", value=float(loc["superficie"]), key=f"l_s_{idx}")
        with c3: loc["qty"] = st.number_input(f"Cant.", value=int(loc["qty"]), key=f"l_q_{idx}")
        with c4:
            if st.button("🗑️", key=f"del_l_{idx}"): st.session_state.locales.pop(idx); st.rerun()

        pot_u = max(loc["superficie"] * 100.0, 3450.0 if loc["superficie"] > 0 else 0.0)
        pot_total_locales += pot_u * loc["qty"]
        st.markdown(f"**Justificación:** $P = \max(S \cdot 100, 3450)$ = **{pot_u * loc['qty']:,.0f} W**")

    st.info(f"💡 **Total P2 (Locales): {int(pot_total_locales):,} W**")
    st.markdown("---")

    st.subheader("3. Servicios (P3)")
    if st.button("➕ Añadir Serv."): st.session_state.servicios_generales.append({"nombre": "Servicio", "potencia": 0.0, "factor": 1.30, "qty": 0})
    pot_total_servicios = 0.0
    for idx, serv in enumerate(st.session_state.servicios_generales):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        with c1: serv["nombre"] = st.text_input(f"Servicio", serv["nombre"], key=f"s_n_{idx}")
        with c2: serv["potencia"] = st.number_input(f"W", value=float(serv["potencia"]), key=f"s_p_{idx}")
        with c3: serv["qty"] = st.number_input(f"Uds", value=int(serv["qty"]), key=f"s_q_{idx}")
        with c4:
            if st.button("🗑️", key=f"del_s_{idx}"): st.session_state.servicios_generales.pop(idx); st.rerun()
        
        p_parcial = serv["potencia"] * serv["qty"] * 1.30
        pot_total_servicios += p_parcial
        st.markdown(f"**Justificación:** $P_s = P \cdot n \cdot K(1.30)$ = **{p_parcial:,.1f} W**")
    
    st.info(f"💡 **Total P3 (Servicios): {pot_total_servicios:,.1f} W**")

    st.markdown(f"""
        <div class="resumen-parciales-box">
            <h2 style="color: #059669; margin-bottom: 0;">⚡ SUMA TOTAL PREVISTA (Pt): {calcular_pt_global():,.1f} W</h2>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("⚡"):
    st.title("Línea General de Alimentación - LGA (ITC-BT-14)")
    st.write("Configuración LGA con cálculo automático desde Previsión, análisis de Icc de compañía y fusibles en CGP.")
    
    pt_auto = calcular_pt_global()

    lga_modo_potencia = st.radio("Origen de la Potencia (Pt):", ["Automático (Sincronizado con Previsión)", "Manual"])
    
    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        if "Automático" in lga_modo_potencia:
            st.info(f"⚡ Potencia Total vinculada: **{pt_auto:,.1f} W**")
            lga_pot = pt_auto
        else:
            lga_pot = st.number_input("Potencia (W) [Manual]", value=pt_auto, step=500.0)
            
        lga_long = st.number_input("Longitud de la LGA (m)", value=0.0)
        lga_mat = st.selectbox("Conductor", ["cobre", "aluminio"])
        metodo_lga_key = st.selectbox("Instalación", list(METODOS_INSTALACION.keys()), index=3)
    with lga_c2:
        lga_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"])
        tipo_enlace_lga = st.radio("Modelo de Contadores:", ["Totalmente concentrados (Límite 0.5%)", "Parciales (Límite 1.0%)"])
        lga_icc_orig = st.number_input("Icc en origen / CGP (kA)", value=10.0, step=0.5, format="%.2f")

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

    iz_final_lga = tabla_iz.get(s_final_lga, 230.0)
    dv_real_lga_v = (lga_pot * lga_long) / (gamma_lga * s_final_lga * 400) if gamma_lga * s_final_lga * 400 > 0 else 0.0
    dv_real_lga_pct = (dv_real_lga_v / 400) * 100

    rho_lga = 1.0 / gamma_lga if gamma_lga > 0 else 0.0
    r_lga_cable = (rho_lga * lga_long) / s_final_lga if s_final_lga > 0 else 0.0
    z_tot_lga = (400.0 / (lga_icc_orig * 1000.0)) + r_lga_cable if lga_icc_orig > 0 else 1.0
    icc_fin_lga = 400.0 / z_tot_lga / 1000.0 if z_tot_lga > 0 else 0.0

    st.markdown("---")
    st.subheader("Memoria Analítica Detallada (LGA)")
    
    st.markdown("### 1. Intensidad de Diseño (Ib):")
    st.latex(r"I_b = \frac{P_t}{\sqrt{3} \cdot V \cdot \cos\varphi}")
    st.markdown(f"• Sustitución numérica: **{lga_pot:,.1f} W / (1.732 * 400 V * 0.9) = {ib_lga:.2f} A**")

    st.markdown("### 2. Sección por Caída de Tensión (Delta V):")
    st.latex(r"S = \frac{P \cdot L}{\gamma \cdot \Delta V \cdot V}")
    st.markdown(f"• Límite: **{dv_pct_lga}% ({dv_max_lga:.2f} V)** | Sección teórica pura: **{s_cdt_lga:.2f} mm²**")

    st.markdown("### 3. Icc Mínima al final de la LGA:")
    st.latex(r"I_{\text{cc,final}} = \frac{V}{\left(\frac{V}{I_{\text{cc,origen}}}\right) + R_{\text{cable}}}")
    st.markdown(f"• Icc al final: **{icc_fin_lga * 1000:.1f} A ({icc_fin_lga:.2f} kA)**. Verificado poder de corte.")

    st.markdown(f"""<div class="fusible-vistoso">🛡️ FUSIBLE RECOMENDADO EN CGP: {in_lga_auto} A (Tipo gG)</div>""", unsafe_allow_html=True)

    st.markdown("### Tabla Verificación de Secciones (LGA)")
    tabla_lga_md = "| Sección | Iz (A) | CDT (%) | Verificación ($I_n \le 0.91 \cdot I_z$) |\n| :---: | :---: | :---: | :--- |\n"
    for s_com in [35, 50, 70, 95, 120, 150, 185, 240]:
        iz_val_t = tabla_iz.get(s_com, 0)
        dv_c_pct = ((lga_pot * lga_long) / (gamma_lga * s_com * 400) / 400) * 100 if s_com > 0 else 0.0
        cond_s_lga = 0.91 * iz_val_t
        if iz_val_t < ib_lga: est = f"❌ Falla calentamiento"
        elif in_lga_auto > cond_s_lga: est = f"❌ Falla 2ª condición"
        elif s_com == s_final_lga: est = f"✅ **CUMPLE IDEAL** (In {in_lga_auto}A <= {cond_s_lga:.1f}A)"
        else: est = "Válido pero superior"
        tabla_lga_md += f"| {s_com} mm² | {iz_val_t} A | {dv_c_pct:.3f}% | {est} |\n"
    st.markdown(tabla_lga_md)

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ CONCLUSIÓN LGA: <span style="color: #ef4444; font-size: 24px;">{s_final_lga} mm²</span> de Cobre ({lga_aisl})<br>
            <span style="font-size: 15px; color: #6b7280;"><br>
            La caída real es del <b>{dv_real_lga_pct:.3f}%</b>. Icc final coordinada con los fusibles de <b>{in_lga_auto} A</b>.
            </span>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("🔌"):
    st.title("Derivación Individual - DI (ITC-BT-15)")
    
    with st.expander("🏗️ Selector de Instalación", expanded=True):
        metodo_di_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()))
        tipo_enlace_di = st.radio("Esquema DI:", ["Contadores concentrados (Límite 1.0%)", "Contadores diseminados (Límite 0.5%)"])

    dv_pct_di = 1.0 if "concentrados" in tipo_enlace_di else 0.5

    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Potencia (W)", [5750, 7360, 9200, 11500])
        di_long = st.number_input("Longitud DI (m)", value=0.0)
        di_mat = st.selectbox("Material conductor", ["cobre", "aluminio"])
    with di_c2:
        di_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"])
        di_cos = st.slider("Coseno phi", 0.8, 1.0, 1.0)
        di_icc_orig = st.number_input("Icc origen / Centralización (kA)", value=6.0, step=0.5)

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
    dv_real_di_v = (2.0 * di_pot * di_long) / (gamma_di * s_optima_di * 230.0) if gamma_di * s_optima_di * 230.0 > 0 else 0.0
    dv_real_di_pct = (dv_real_di_v / 230.0) * 100

    rho_di = 1.0 / gamma_di if gamma_di > 0 else 0.0
    r_di_cable = (rho_di * di_long) / s_optima_di if s_optima_di > 0 else 0.0
    z_tot_di = (230.0 / (di_icc_orig * 1000.0)) + (2.0 * r_di_cable) if di_icc_orig > 0 else 1.0
    icc_fin_di = 230.0 / z_tot_di / 1000.0 if z_tot_di > 0 else 0.0
    disparo_mag_di = prot_di * 10.0
    salta_di = (icc_fin_di * 1000.0) >= disparo_mag_di

    st.markdown("---")
    st.subheader("📋 Memoria Analítica (Derivación Individual)")

    st.markdown("### 1. Intensidad de Diseño (Ib):")
    st.latex(r"I_b = \frac{P}{V \cdot \cos\varphi}")
    st.markdown(f"• Sustitución: **{di_pot:,.1f} W / (230 V * {di_cos}) = {ib_di:.2f} A**")

    st.markdown("### 2. Sección por Caída de Tensión:")
    st.latex(r"S = \frac{2 \cdot P \cdot L}{\gamma \cdot \Delta V \cdot V}")
    st.markdown(f"• Límite: **{dv_pct_di}% ({dv_max_di:.2f} V)** | Sección pura: **{s_cdt_di:.2f} mm²**")

    st.markdown("### 3. Comprobación IGA e Icc:")
    st.latex(r"I_{\text{cc,final}} = \frac{V}{\left(\frac{V}{I_{\text{cc,origen}}}\right) + 2 \cdot R_{\text{cable}}}")
    st.markdown(f"• Icc al final ({di_long} m): **{icc_fin_di * 1000:.1f} A ({icc_fin_di:.2f} kA)**")
    st.markdown(f"• Disparo IGA Curva C ({prot_di} A): **{'✅ GARANTIZADO' if salta_di else '⚠️ REVISAR Icc'}**.")

    st.markdown(f"""<div class="pia-destacado">🛡️ IGA RECOMENDADO: {prot_di} A (Curva C)</div>""", unsafe_allow_html=True)

    st.markdown("### Tabla Verificación de Secciones (DI)")
    tabla_di_md = "| Sección | Iz (A) | CDT (%) | Verificación ($I_n \le 0.91 \cdot I_z$) |\n| :---: | :---: | :---: | :--- |\n"
    for sec_com in [6, 10, 16, 25, 35, 50]:
        iz_c = tabla_iz_di.get(sec_com, 100.0)
        dv_c_pct = ((2.0 * di_pot * di_long) / (gamma_di * sec_com * 230.0) / 230.0) * 100 if sec_com > 0 else 0.0
        cond_sobrecarga = 0.91 * iz_c
        if iz_c < ib_di: est_v = f"❌ Falla por calentamiento"
        elif prot_di > cond_sobrecarga: est_v = f"❌ Falla 2ª condición"
        elif sec_com == s_optima_di: est_v = f"✅ **CUMPLE IDEAL** (In {prot_di}A <= {cond_sobrecarga:.1f}A)"
        else: est_v = "Válido pero superior"
        tabla_di_md += f"| {sec_com} mm² | {iz_c} A | {dv_c_pct:.3f}% | {est_v} |\n"
    st.markdown(tabla_di_md)

    st.markdown(f"""
        <div class="resultado-destacado">
            ⚡ SECCIÓN DI: <span style="color: #ef4444; font-size: 24px;">{s_optima_di} mm²</span> de {di_mat.upper()} ({di_aisl})<br>
            <span style="font-size: 15px; color: #6b7280;">Caída de tensión real: <b>{dv_real_di_pct:.3f}%</b> (Límite {dv_pct_di}%)</span>
        </div>
    """, unsafe_allow_html=True)

elif seleccion_modulo.startswith("📚"):
    st.title("📚 Compendio Tablas REBT (ITC-BT 01 al 51)")
elif seleccion_modulo.startswith("📐"):
    st.title("📐 Esquemas Unifilares del Edificio")
elif seleccion_modulo.startswith("💡"):
    st.title("💡 Simulador Consumo Eléctrico")