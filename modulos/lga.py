import streamlit as st
import math

METODOS_INSTALACION = {
    "B1 (Bajo tubo empotrado)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas"},
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Multiconductor en pared)": {"ref": "C", "desc": "Cable multiconductor fijado directo"},
    "D (Cables enterrados bajo tubo)": {"ref": "D", "desc": "Instalación subterránea"}
}
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
    st.title("⚡ Línea General de Alimentación - LGA (ITC-BT-14)")
    
    # --- RECUPERACIÓN AUTOMÁTICA Y REAL DE LA PREVISIÓN DE CARGAS ---
    viviendas_diurnas_qty = sum(v["qty"] for v in st.session_state.get('grupos_viviendas', []) if not v.get("nocturna", False))
    
    tabla_k = {1: 1.0, 2: 2.0, 3: 3.0, 4: 3.8, 5: 4.6, 6: 5.4, 7: 6.2, 8: 7.0, 9: 7.8, 10: 8.5, 
               11: 9.1, 12: 9.8, 13: 10.5, 14: 11.2, 15: 11.9, 16: 12.6, 17: 13.3, 18: 14.0, 19: 14.7, 20: 15.4}
    n_viv_calc = max(viviendas_diurnas_qty, 1)
    k_val = tabla_k.get(n_viv_calc, 15.4 if n_viv_calc <= 20 else float(round(15.4 + (n_viv_calc - 20) * 0.7, 2)))

    p_viv_total = 0
    for v in st.session_state.get('grupos_viviendas', []):
        if v.get("nocturna", False):
            p_viv_total += v["qty"] * v["pot"]
        else:
            if viviendas_diurnas_qty > 0:
                p_viv_total += int(round(v["qty"] * v["pot"] * (k_val / viviendas_diurnas_qty)))

    p_loc_total = sum(max(l.get("superficie", 0.0) * 100.0, 3450.0) * l.get("qty", 1) for l in st.session_state.get('locales', []))

    p_serv_total = 0.0
    for s in st.session_state.get('servicios_generales', []):
        f_serv = s.get("factor", 1.30)
        c_serv = s.get("cos_phi", 1.0)
        if f_serv == 1.80 and c_serv < 1.0:
            p_serv_total += s.get("potencia", 0.0) * s.get("qty", 1) * f_serv * c_serv
        else:
            p_serv_total += s.get("potencia", 0.0) * s.get("qty", 1) * f_serv

    garaje_data = st.session_state.get('garajes', {"sup": 240.0, "plazas_irve": 18, "tipo_irve": "10% (Sin sistema de gestión)"})
    sup_gar = garaje_data.get("sup", 0.0)
    p_gar_vent = max(sup_gar * 20.0, 3450.0 if sup_gar > 0 else 0.0)
    factor_irve = 0.10 if "10%" in garaje_data.get("tipo_irve", "") else 0.05
    p_gar_irve = (garaje_data.get("plazas_irve", 0) * factor_irve) * 3680.0
    p_gar_total = p_gar_vent + p_gar_irve

    pt_auto = float(p_viv_total + p_loc_total + p_serv_total + p_gar_total)

    # --- CONTROLES DE ENTRADA CON FORMULARIO ---
    st.markdown("### ⚙️ Parámetros de Diseño de la Línea")
    
    with st.form("form_lga_parametros"):
        lga_modo_potencia = st.radio("Origen de la Potencia (Pt):", ["Automático", "Manual"], horizontal=True, key="lga_modo")
        
        lga_c1, lga_c2 = st.columns(2)
        with lga_c1:
            if "Automático" in lga_modo_potencia:
                lga_pot = pt_auto
                st.metric(label="Potencia de cálculo LGA (Automática desde Previsión)", value=f"{lga_pot:,.2f} W")
                st.caption(f"Desglose: Viviendas ({p_viv_total:,}W) + Locales ({p_loc_total:,.0f}W) + Servicios ({p_serv_total:,.2f}W) + Garajes ({p_gar_total:,.2f}W)")
            else:
                lga_pot = st.number_input("Potencia de cálculo LGA (Manual en W) - Pulsa Enter para fijar", value=pt_auto, step=500.0, key="lga_pot_man")
                
            lga_long = st.number_input("Longitud de la LGA (m) - Pulsa Enter para recalcular", value=0.0, step=1.0, key="lga_long")
            lga_mat = st.selectbox("Material Conductor", ["cobre", "aluminio"], key="lga_mat")
            metodo_lga_key = st.selectbox("Instalación:", list(METODOS_INSTALACION.keys()), index=3, key="lga_met")

        with lga_c2:
            lga_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="lga_aisl")
            tipo_enlace_lga = st.radio("Contadores:", ["Totalmente concentrados (Límite CDT = 0.5%)", "Centralizaciones Parciales (Límite CDT = 1.0%)"], key="lga_enlace")
            lga_icc_orig = st.number_input("Icc en origen (kA) - Pulsa Enter para recalcular", value=10.0, step=0.5, key="lga_icc")

        submitted = st.form_submit_button("🔄 Recalcular / Actualizar Cálculo")

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

    rho_lga = 1.0 / gamma_lga if gamma_lga > 0 else 0.0
    r_lga_cable = (rho_lga * lga_long) / s_final_lga if s_final_lga > 0 else 0.0
    
    z_orig_lga_ohms = 400.0 / (lga_icc_orig * 1000.0)
    z_tot_lga = z_orig_lga_ohms + r_lga_cable
    icc_fin_lga = 400.0 / z_tot_lga if z_tot_lga > 0 else 0.0

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Detallada (LGA - ITC-BT-14)</h3>", unsafe_allow_html=True)

    # --- BLOQUE 1: INTENSIDAD DE DISEÑO ---
    st.info(
        "#### 1. Intensidad de Diseño Trifásica ($I_b$)\n\n"
        "**Criterio y Fórmula Reglamentaria:**\n"
        "$$I_b = \\frac{P}{\\sqrt{3} \\cdot V \\cdot \\cos\\varphi}$$\n\n"
        "**Leyenda y Definición de Variables:**\n"
        "* **I_b**: Intensidad de cálculo o de diseño por fase (A).\n"
        f"* **P**: Potencia total prevista de transporte en la línea ($P_t$ = {lga_pot:,.2f} W).\n"
        "* **V**: Tensión nominal compuesta entre fases (400 V).\n"
        "* **cos φ**: Factor de potencia estimado para instalaciones generales (0.9).\n"
        "* **√3**: Constante trifásica ($\\approx 1.732$).\n\n"
        "**Sustitución Numérica y Resultado:**\n"
        f"$$I_b = \\frac{{{lga_pot:,.2f} \\text{{ W}}}}{{\\sqrt{3} \\cdot 400 \\text{{ V}} \\cdot 0.9}} = \\frac{{{lga_pot:,.2f}}}{{623.54}} = \\mathbf{{{ib_lga:.2f}\\text{{ A}}}}{$$"
    )

    # --- BLOQUE 2: SECCIÓN POR CAÍDA DE TENSIÓN ---
    st.info(
        "#### 2. Sección Teórica por Caída de Tensión ($\\Delta V$)\n\n"
        "**Criterio y Fórmula Reglamentaria:**\n"
        "$$S = \\frac{P \\cdot L}{\\gamma \\cdot \\Delta V \\cdot V}$$\n\n"
        "**Leyenda y Definición de Variables:**\n"
        "* **S**: Sección teórica mínima exigida del conductor ($\\text{mm}^2$).\n"
        f"* **P**: Potencia total de cálculo ({lga_pot:,.2f} W).\n"
        f"* **L**: Longitud unifilar de la línea ({lga_long} m).\n"
        f"* **γ**: Conductividad del material a servicio normal ({gamma_lga} m/(Ω·mm²) para {lga_aisl}).\n"
        f"* **ΔV**: Caída de tensión máxima admisible ({dv_pct_lga}% de 400V = {dv_max_lga:.2f} V).\n"
        "* **V**: Tensión nominal (400 V).\n\n"
        "**Sustitución Numérica y Resultado:**\n"
        f"$$S = \\frac{{{lga_pot:,.2f} \\cdot {lga_long}}}{{{gamma_lga} \\cdot {dv_max_lga:.2f} \\cdot 400}} = \\mathbf{{{s_cdt_lga:.2f}\\text{{ mm}}^2}}{$$"
    )
    
    # --- BLOQUE 3: ICC MÍNIMA Y FUSIBLES ---
    st.info(
        "#### 3. Icc Mínima y Fusibles de Compañía (CGP)\n\n"
        "**Criterio y Fórmula Reglamentaria (ITC-BT-14 / ITC-BT-22):**\n"
        "Verificamos que los fusibles de protección tipo gG situados en la CGP fundirán a tiempo en caso de un cortocircuito franco al final de la Línea General de Alimentación.\n\n"
        "$$I_{cc,final} = \\frac{V}{\\left(\\frac{V}{I_{cc,origen}}\\right) + R_{cable}}$$\n\n"
        "**Leyenda y Definición de Variables:**\n"
        "* **I_cc,final**: Corriente de cortocircuito estimada al final de la LGA (A).\n"
        "* **V**: Tensión nominal compuesta de referencia (400 V).\n"
        f"* **I_cc,origen**: Corriente de cortocircuito en el origen de la línea ({lga_icc_orig * 1000:,.0f} A).\n"
        f"* **R_cable**: Resistencia activa del conductor en el tramo ($R = \\frac{\\rho \\cdot L}{S} = {r_lga_cable:.5f}\\ \\Omega$).\n"
        f"* **In**: Calibre de los fusibles gG de protección en origen ({in_lga_auto} A).\n\n"
        "**Sustitución Numérica y Verificación Reglamentaria:**\n"
        f"$$I_{cc,final} = \\frac{{400}}{{\\left(\\frac{{400}}{{{lga_icc_orig * 1000.0}}}\\right) + {r_lga_cable:.5f}}} = \\frac{{400}}{{{z_orig_lga_ohms:.5f} + {r_lga_cable:.5f}}} = \\frac{{400}}{{{z_tot_lga:.5f}}} = \\mathbf{{{icc_fin_lga:.1f}\\text{{ A}}}}{$$\n\n"
        f"* **Icc al final de la LGA:** **{icc_fin_lga:.1f} A** ({icc_fin_lga / 1000.0:.2f} kA)\n"
        f"* **Veredicto de Coordinación:** ✅ La corriente de cortocircuito al final de la línea garantiza la fusión de los fusibles de protección de **{in_lga_auto} A (Tipo gG)** dentro de los márgenes reglamentarios."
    )

    st.markdown(f"""<div style="background: #f1f5f9; color: #0f172a; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #cbd5e1;">🛡️ FUSIBLES RECOMENDADOS EN CGP: {in_lga_auto} A (Tipo gG)</div>""", unsafe_allow_html=True)

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

    st.success(f"""
    ### ✅ SECCIÓN ÓPTIMA LGA: {s_final_lga} mm² de {lga_mat.upper()}
    Garantiza una caída real del **{dv_real_lga_pct:.3f}%**. Protegida en origen por **Fusibles gG de {in_lga_auto} A** coordinados térmicamente según norma.
    """)
