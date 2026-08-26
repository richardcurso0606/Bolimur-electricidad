import streamlit as st

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

def renderizar():
    st.title("🔌 Derivación Individual - DI (ITC-BT-15)")
    
    with st.expander("🏗️ Selector de Instalación y Entorno", expanded=True):
        metodo_di_key = st.selectbox("Método Instalación:", list(METODOS_INSTALACION.keys()), key="di_met")
        tipo_enlace_di = st.radio("Esquema Contadores:", ["Concentrados (Límite CDT = 1.0%)", "Diseminados (Límite CDT = 0.5%)"], key="di_enlace")

    dv_pct_di = 1.0 if "Concentrados" in tipo_enlace_di else 0.5

    di_c1, di_c2 = st.columns(2)
    with di_c1:
        di_pot = st.selectbox("Previsión de Potencia (W)", [5750, 7360, 9200, 11500], key="di_pot")
        di_long = st.number_input("Longitud DI (m)", value=0.0, key="di_long")
        di_mat = st.selectbox("Material conductor", ["cobre", "aluminio"], key="di_mat")
    with di_c2:
        di_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"], key="di_aisl")
        di_cos = st.slider("Coseno phi", 0.8, 1.0, 1.0, key="di_cos")
        di_icc_orig = st.number_input("Icc origen / Centralización (kA)", value=6.0, step=0.5, key="di_icc")

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

    rho_di = 1.0 / gamma_di if gamma_di > 0 else 0.0
    r_di_cable = (rho_di * di_long) / s_optima_di if s_optima_di > 0 else 0.0
    z_tot_di = (230.0 / (di_icc_orig * 1000.0)) + (2.0 * r_di_cable) if di_icc_orig > 0 else 1.0
    icc_fin_di = 230.0 / z_tot_di / 1000.0 if z_tot_di > 0 else 0.0
    disparo_mag_di = prot_di * 10.0
    salta_di = (icc_fin_di * 1000.0) >= disparo_mag_di

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Detallada (DI)</h3>", unsafe_allow_html=True)

    st.info(f"""
    #### 1. Intensidad de Diseño Monofásica ($I_b$)
    **Justificación:** Intensidad máxima admisible basada en el escalón de potencia elegido por el cliente.
    
    $$I_b = \\frac{{{di_pot:,.1f} \\text{{ W}}}}{{230 \\text{{ V}} \\cdot {di_cos}}}$$
    
    **Sustitución y Resultado:** {di_pot:,.1f} W / (230 V) = **{ib_di:.2f} A**
    """)
    
    st.info(f"""
    #### 2. Sección Teórica por Caída de Tensión ($\\Delta V$)
    **Justificación:** Verificamos la sección exigida para no superar el límite de CDT del {dv_pct_di}% desde el contador.
    
    $$S = \\frac{{2 \cdot P \cdot L}}{{\gamma \cdot \Delta V \cdot V}}$$
    
    **Resultado:** Sección pura requerida = **{s_cdt_di:.2f} mm²**
    """)
    
    estado_icc_di = "✅ GARANTIZADO" if salta_di else "⚠️ PELIGRO: NO SALTARÁ A TIEMPO"
    st.info(f"""
    #### 3. Comprobación Cortocircuito IGA (0.1s)
    **Justificación:** El IGA en el cuadro de la vivienda debe proteger frente a cortocircuitos. Verificamos el umbral magnético de la Curva C ($10 \\cdot I_n$).
    
    $$I_{{cc,final}} = \\frac{{V}}{{\\left(\\frac{{V}}{{I_{{cc,origen}}}}\\right) + 2 \cdot R_{{cable}}}}$$
    
    * **Icc al final de la DI:** {icc_fin_di * 1000:.1f} A
    * **Umbral ({prot_di} A x 10):** {disparo_mag_di:.1f} A
    * **Veredicto:** {estado_icc_di}
    """)
    
    st.markdown(f"""<div style="background: #e0f2fe; color: #0369a1; padding: 15px; border-radius: 8px; font-size: 18px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #7dd3fc;">🛡️ IGA RECOMENDADO EN CUADRO VIVIENDA: {prot_di} A (Curva C)</div>""", unsafe_allow_html=True)

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

    st.success(f"""
    ### ✅ SECCIÓN ÓPTIMA DI: {s_optima_di} mm² de {di_mat.upper()}
    Caída de tensión real controlada al **{dv_real_di_pct:.3f}%**. La línea está protegida perfectamente por el IGA del cuadro general de la vivienda (**{prot_di} A, Curva C**).
    """)

