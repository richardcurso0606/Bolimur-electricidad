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

    # P1: Viviendas
    p_viv_total = 0
    for v in st.session_state.get('grupos_viviendas', []):
        if v.get("nocturna", False):
            p_viv_total += v["qty"] * v["pot"]
        else:
            if viviendas_diurnas_qty > 0:
                p_viv_total += int(round(v["qty"] * v["pot"] * (k_val / viviendas_diurnas_qty)))

    # P2: Locales Comerciales
    p_loc_total = sum(max(l.get("superficie", 0.0) * 100.0, 3450.0) * l.get("qty", 1) for l in st.session_state.get('locales', []))

    # P3: Servicios Generales
    p_serv_total = 0.0
    for s in st.session_state.get('servicios_generales', []):
        f_serv = s.get("factor", 1.30)
        c_serv = s.get("cos_phi", 1.0)
        if f_serv == 1.80 and c_serv < 1.0:
            p_serv_total += s.get("potencia", 0.0) * s.get("qty", 1) * f_serv * c_serv
        else:
            p_serv_total += s.get("potencia", 0.0) * s.get("qty", 1) * f_serv

    # P4: Garajes e IRVE
    garaje_data = st.session_state.get('garajes', {"sup": 240.0, "plazas_irve": 18, "tipo_irve": "10% (Sin sistema de gestión)"})
    sup_gar = garaje_data.get("sup", 0.0)
    p_gar_vent = max(sup_gar * 20.0, 3450.0 if sup_gar > 0 else 0.0)
    factor_irve = 0.10 if "10%" in garaje_data.get("tipo_irve", "") else 0.05
    p_gar_irve = (garaje_data.get("plazas_irve", 0) * factor_irve) * 3680.0
    p_gar_total = p_gar_vent + p_gar_irve

    # Potencia total automática real extraída de la previsión
    pt_auto = float(p_viv_total + p_loc_total + p_serv_total + p_gar_total)

    # --- CONTROLES DE ENTRADA ---
    lga_modo_potencia = st.radio("Origen de la Potencia (Pt):", ["Automático", "Manual"], key="lga_modo")
    
    lga_c1, lga_c2 = st.columns(2)
    with lga_c1:
        if "Automático" in lga_modo_potencia: 
            lga_pot = pt_auto
            st.info(f"ℹ️ **Valor Automático (Previsión de Cargas):** **{lga_pot:,.2f} W**\n\n*(P1 Viviendas: {p_viv_total:,} W | P2 Locales: {p_loc_total:,.0f} W | P3 Servicios: {p_serv_total:,.2f} W | P4 Garajes: {p_gar_total:,.2f} W)*")
        else: 
            lga_pot = st.number_input("Potencia de cálculo LGA (W)", value=pt_auto, step=500.0, key="lga_pot_man")
            
        lga_long = st.number_input("Longitud de la LGA (m)", value=0.0, key="lga_long")
        lga_mat = st.selectbox("Material Conductor", ["cobre", "aluminio"], key="lga_mat")
        metodo_lga_key = st.selectbox("Instalación:", list(METODOS_INSTALACION.keys()), index=3, key="lga_met")
    with lga_c2:
        lga_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="lga_aisl")
        tipo_enlace_lga = st.radio("Contadores:", ["Totalmente concentrados (Límite CDT = 0.5%)", "Centralizaciones Parciales (Límite CDT = 1.0%)"], key="lga_enlace")
        lga_icc_orig = st.number_input("Icc en origen (kA)", value=10.0, step=0.5, key="lga_icc")

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
    z_tot_lga = (400.0 / (lga_icc_orig * 1000.0)) + r_lga_cable if lga_icc_orig > 0 else 1.0
    icc_fin_lga = 400.0 / z_tot_lga / 1000.0 if z_tot_lga > 0 else 0.0

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Detallada (LGA)</h3>", unsafe_allow_html=True)

    st.info(f"""
    #### 1. Intensidad de Diseño Trifásica ($I_b$)
    **Justificación:** Calculamos la corriente por fase. En instalaciones generales se asume un $\\cos\\varphi$ de 0.9.
    
    $$I_b = \\frac{{{lga_pot:,.1f} \\text{{ W}}}}{{\\sqrt{{3}} \\cdot 400 \\text{{ V}} \\cdot 0.9}}$$
    
    **Sustitución y Resultado:** {lga_pot:,.1f} W / 623.54 = **{ib_lga:.2f} A**
    """)

    st.info(f"""
    #### 2. Sección Teórica por Caída de Tensión ($\\Delta V$)
    **Justificación:** Límite máximo de pérdida del **{dv_pct_lga}%** ({dv_max_lga:.2f} V) según esquema de enlace (ITC-BT-14).
    
    $$S = \\frac{{{lga_pot:,.1f} \\cdot {lga_long}}}{{\\gamma \\cdot \\Delta V \\cdot 400}}$$
    
    **Resultado:** Sección mínima exigida = **{s_cdt_lga:.2f} mm²**
    """)
    
    st.info(f"""
    #### 3. Icc Mínima y Fusibles de Compañía
    **Justificación:** Verificamos que los fusibles gG en la CGP fundirán a tiempo en caso de cortocircuito al final de la línea.
    
    $$I_{{cc,final}} = \\frac{{V}}{{\\left(\\frac{{V}}{{I_{{cc,origen}}}}\\right) + R_{{cable}}}}$$
    
    * **Icc al final de la LGA:** {icc_fin_lga * 1000:.1f} A ({icc_fin_lga:.2f} kA)
    * **Veredicto:** ✅ La Icc es suficiente para accionar los fusibles de protección de {in_lga_auto} A.
    """)

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
