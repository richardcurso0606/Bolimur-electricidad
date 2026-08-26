import streamlit as st
import math

METODOS_INSTALACION_DI = {
    "B1 (Bajo tubo empotrado)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas"},
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Multiconductor en pared)": {"ref": "C", "desc": "Cable multiconductor fijado directo"}
}
SECCIONES_COMERCIALES_DI = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95]
IZ_COBRE_TUBO_DI = {1.5: 14.5, 2.5: 20.0, 4: 26.0, 6: 34.0, 10: 46.0, 16: 61.0, 25: 80.0, 35: 99.0, 50: 119.0, 70: 151.0, 95: 182.0}
CALIBRES_IGA = [10, 16, 20, 25, 32, 40, 50, 63]

def seleccionar_seccion_optima_di(s_necesaria):
    for sec in SECCIONES_COMERCIALES_DI:
        if sec >= s_necesaria: return sec
    return SECCIONES_COMERCIALES_DI[-1]

def seleccionar_iga(ib):
    for cal in CALIBRES_IGA:
        if cal >= ib: return cal
    return CALIBRES_IGA[-1]

def renderizar():
    st.title("🏠 Derivación Individual - DI (ITC-BT-15)")
    
    # --- CONTROLES DE ENTRADA CON FORMULARIO (CÁLCULO AL PULSAR ENTER) ---
    st.markdown("### ⚙️ Parámetros de Diseño de la Derivación Individual")
    
    with st.form("form_di_parametros"):
        di_c1, di_c2 = st.columns(2)
        with di_c1:
            di_pot = st.number_input("Potencia de cálculo DI (W) - Ej: 5750", value=5750.0, step=250.0, key="di_pot")
            di_long = st.number_input("Longitud de la DI (m)", value=15.0, step=1.0, key="di_long")
            di_mat = st.selectbox("Material Conductor", ["cobre"], key="di_mat")
            metodo_di_key = st.selectbox("Instalación:", list(METODOS_INSTALACION_DI.keys()), index=0, key="di_met")
        with di_c2:
            di_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="di_aisl")
            tipo_suministro = st.radio("Tipo de Suministro:", ["Monofásico (230 V)", "Trifásico (400 V)"], key="di_sum")
            di_icc_orig = st.number_input("Icc en origen / contador (kA)", value=10.0, step=0.5, key="di_icc")

        submitted_di = st.form_submit_button("🔄 Recalcular / Actualizar Cálculo DI")

    # --- CÁLCULOS TÉCNICOS ---
    es_trifasico = "Trifásico" in tipo_suministro
    v_tension = 400.0 if es_trifasico else 230.0
    cos_phi_di = 1.0 # Habitual en viviendas / suministros en baja tensión
    
    ib_di = di_pot / (math.sqrt(3) * v_tension * cos_phi_di) if es_trifasico else di_pot / (v_tension * cos_phi_di)
    
    dv_pct_di = 1.0 # Límite ITC-BT-15 desde contador hasta cuadro general
    gamma_di = 44.0 if "XLPE" in di_aisl else 48.5
    dv_max_di = v_tension * (dv_pct_di / 100.0)
    
    if es_trifasico:
        s_cdt_di = (di_pot * di_long) / (gamma_di * dv_max_di * v_tension) if gamma_di * dv_max_di * v_tension > 0 else 6.0
    else:
        s_cdt_di = (2.0 * di_pot * di_long) / (gamma_di * dv_max_di * v_tension) if gamma_di * dv_max_di * v_tension > 0 else 6.0

    in_iga_auto = seleccionar_iga(ib_di)
    s_final_di = seleccionar_seccion_optima_di(max(s_cdt_di, 6.0)) # Mínimo reglamentario ITC-BT-15 para viviendas suele ser 6 mm²
    
    tabla_iz_di = IZ_COBRE_TUBO_DI
    while True:
        iz_a_di = tabla_iz_di.get(s_final_di, 61.0)
        if in_iga_auto <= 0.91 * iz_a_di and iz_a_di >= ib_di: break
        idx_s = SECCIONES_COMERCIALES_DI.index(s_final_di) if s_final_di in SECCIONES_COMERCIALES_DI else 3
        if idx_s < len(SECCIONES_COMERCIALES_DI) - 1: s_final_di = SECCIONES_COMERCIALES_DI[idx_s + 1]
        else: break

    dv_real_di_pct = (((math.sqrt(3) if es_trifasico else 2.0) * di_pot * di_long) / (gamma_di * s_final_di * v_tension) / v_tension) * 100 if gamma_di * s_final_di * v_tension > 0 else 0.0

    rho_di = 1.0 / gamma_di if gamma_di > 0 else 0.0
    r_cable_di = (rho_di * di_long) / s_final_di if s_final_di > 0 else 0.0
    
    # Comprobación Icc cortocircuito IGA (Curva C: disparo magnético entre 5 y 10 In -> tomamos 10*In como umbral severo)
    z_tot_di = (v_tension / (di_icc_orig * 1000.0)) + (2.0 * r_cable_di if not es_trifasico else r_cable_di)
    icc_fin_di = v_tension / z_tot_di if z_tot_di > 0 else 0.0
    umbral_magnetico_iga = 10.0 * in_iga_auto

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Detallada (DI - ITC-BT-15)</h3>", unsafe_allow_html=True)

    # --- BLOQUE 1: INTENSIDAD DE DISEÑO ---
    if es_trifasico:
        formula_ib_str = f"I_b = \\frac{{P}}{{\\sqrt{3} \\cdot V \\cdot \\cos\\varphi}}"
        sust_ib_str = f"I_b = \\frac{{{di_pot:,.1f} \\text{{ W}}}}{{\\sqrt{3} \\cdot 400 \\text{{ V}} \\cdot 1.0}} = \\frac{{{di_pot:,.1f}}}{{692.82}} = \\mathbf{{{ib_di:.2f}\\text{{ A}}}}"
    else:
        formula_ib_str = f"I_b = \\frac{{P}}{{V \\cdot \\cos\\varphi}}"
        sust_ib_str = f"I_b = \\frac{{{di_pot:,.1f} \\text{{ W}}}}{{230 \\text{{ V}} \\cdot 1.0}} = \\frac{{{di_pot:,.1f}}}{{230}} = \\mathbf{{{ib_di:.2f}\\text{{ A}}}}"

    st.info(f"""
    #### 1. Intensidad de Diseño {'Trifásica' if es_trifasico else 'Monofásica'} ($I_b$)
    
    **Criterio y Fórmula Reglamentaria:**
    $${formula_ib_str}$$
    
    **Leyenda y Definición de Variables:**
    * **I_b**: Intensidad máxima de cálculo o diseño (A).
    * **P**: Potencia contratada o prevista para el suministro ({di_pot:,.1f} W).
    * **V**: Tensión nominal de alimentación ({v_tension} V).
    * **cos φ**: Factor de potencia (1.0 para viviendas estándar).
    
    **Sustitución Numérica y Resultado:**
    $${sust_ib_str}$$
    """)

    # --- BLOQUE 2: SECCIÓN POR CAÍDA DE TENSIÓN ---
    if es_trifasico:
        formula_s_str = f"S = \\frac{{P \\cdot L}}{{\\gamma \\cdot \\Delta V \\cdot V}}"
        sust_s_str = f"S = \\frac{{{di_pot:,.1f} \\cdot {di_long}}}{{{gamma_di} \\cdot {dv_max_di:.2f} \\cdot 400}} = \\mathbf{{{s_cdt_di:.2f}\\text{{ mm}}^2}}"
    else:
        formula_s_str = f"S = \\frac{{2 \\cdot P \\cdot L}}{{\\gamma \\cdot \\Delta V \\cdot V}}"
        sust_s_str = f"S = \\frac{{2 \\cdot {di_pot:,.1f} \\cdot {di_long}}}{{{gamma_di} \\cdot {dv_max_di:.2f} \\cdot 230}} = \\mathbf{{{s_cdt_di:.2f}\\text{{ mm}}^2}}"

    st.info(f"""
    #### 2. Sección Teórica por Caída de Tensión ($\\Delta V$)
    
    **Criterio y Fórmula Reglamentaria:**
    $${formula_s_str}$$
    
    **Leyenda y Definición de Variables:**
    * **S**: Sección teórica mínima exigida del conductor ($\text{{mm}}^2$).
    * **P**: Potencia de cálculo ({di_pot:,.1f} W).
    * **L**: Longitud de la derivación individual ({di_long} m).
    * **γ**: Conductividad del conductor ({gamma_di} m/(Ω·mm²) para {di_aisl}).
    * **ΔV**: Caída de tensión máxima admisible ({dv_pct_di}% de {v_tension}V = {dv_max_di:.2f} V).
    
    **Sustitución Numérica y Resultado:**
    $${sust_s_str}$$
    """)
    
    # --- BLOQUE 3: COMPROBACIÓN CORTOCIRCUITO IGA ---
    st.info(f"""
    #### 3. Comprobación de Cortocircuito y Protección IGA (Disparo Magnético 0.1s)
    
    **Criterio y Fórmula Reglamentaria (ITC-BT-22 / ITC-BT-15):**
    El Interruptor General Automático (IGA) instalado en el cuadro de vivienda debe garantizar el corte ultra-rápido (< 0.1 s) ante un cortocircuito franco al final de la línea mediante su disparo magnético (Curva C: $10 \\cdot I_n$).
    
    $$I_{{cc,final}} = \\frac{{V}}{{\\left(\\frac{{V}}{{I_{{cc,origen}}}}\\right) + R_{{total,cable}}}}$$
    
    **Leyenda y Definición de Variables:**
    * **I_cc,final**: Corriente de cortocircuito estimada al final de la DI (A).
    * **V**: Tensión nominal de referencia ({v_tension} V).
    * **I_cc,origen**: Corriente de cortocircuito en el origen / contadores ({di_icc_orig * 1000:,.0f} A).
    * **R_total,cable**: Resistencia activa total del bucle de conductors ({'2 · R_cable' if not es_trifasico else 'R_cable'} = {('2 * ' if not es_trifasico else '') + f'{r_cable_di:.5f}'} = { (2.0 if not es_trifasico else 1.0) * r_cable_di:.5f}\\ \\Omega).
    * **Umbral Magnético Curva C ($10 \\cdot I_n$)**: Intensidad requerida para asegurar el disparo instantáneo del IGA de {in_iga_auto} A $\\rightarrow$ $10 \\times {in_iga_auto} = \\mathbf{{{umbral_magnetico_iga:.1f}\\text{{ A}}}}$.
    
    **Sustitución y Verificación Reglamentaria:**
    * **Icc estimada al final de la DI:** **{icc_fin_di:,.1f} A** ({icc_fin_di / 1000:.2f} kA)
    * **Umbral de disparo magnético exigido ($10 \\cdot I_n$):** **{umbral_magnetico_iga:.1f} A**
    * **Veredicto de Protección:** {'✅ **GARANTIZADO** (La Icc final de cortocircuito supera ampliamente el umbral magnético de disparo instantáneo del IGA de ' + str(in_iga_auto) + ' A).' if icc_fin_di >= umbral_magnetico_iga else '⚠️ **REVISAR** (La Icc es inferior al umbral magnético de la curva C).'}
    """)

    st.markdown(f"""<div style="background: #f1f5f9; color: #0f172a; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #cbd5e1;">🛡️ IGA RECOMENDADO EN CUADRO VIVIENDA: {in_iga_auto} A (Curva C)</div>""", unsafe_allow_html=True)

    # --- TABLA DE VERIFICACIÓN DE SECCIONES ---
    st.markdown("### 📊 Tabla de Verificación de Secciones Comerciales (DI)")
    tabla_di_md = "| SECCIÓN | IZ ADMISIBLE (A) | CDT REAL (%) | ESTADO DE VERIFICACIÓN ($I_n \\le 0.91 \\cdot I_z$) |\n| :--- | :--- | :--- | :--- |\n"
    for s_com in [6, 10, 16, 25, 35]:
        iz_val_di = IZ_COBRE_TUBO_DI.get(s_com, 61.0)
        dv_c_di_pct = (((math.sqrt(3) if es_trifasico else 2.0) * di_pot * di_long) / (gamma_di * s_com * v_tension) / v_tension) * 100 if s_com > 0 else 0.0
        cond_s_di = 0.91 * iz_val_di
        if iz_val_di < ib_di: est = f"❌ Falla Calentamiento"
        elif in_iga_auto > cond_s_di: est = f"❌ Falla ($I_n$ {in_iga_auto}A > {cond_s_di:.1f}A)"
        elif s_com == s_final_di: est = f"✅ **CUMPLE IDEAL** ($I_n$ {in_iga_auto}A $\\le$ {cond_s_di:.1f}A)"
        else: est = "Válido pero sobredimensionado"
        tabla_di_md += f"| **{s_com} mm²** | {iz_val_di} A | {dv_c_di_pct:.3f}% | {est} |\n"
    st.markdown(tabla_di_md)

    st.success(f"""
    ### ✅ SECCIÓN ÓPTIMA DI: {s_final_di} mm² de {di_mat.upper()}
    Garantiza una caída de tensión real del **{dv_real_di_pct:.3f}%**. Protegida en origen/cuadro por **IGA de {in_iga_auto} A (Curva C)** con corte efectivo garantizado por cortocircuito.
    """)
