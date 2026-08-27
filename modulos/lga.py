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
    
    # --- BOTÓN DE RESETEO DE PARÁMETROS DE DISEÑO ---
    col_tit, col_btn = st.columns([3, 1])
    with col_tit:
        st.markdown("### ⚙️ Parámetros de Diseño de la Línea")
    with col_btn:
        if st.button("🔄 Restablecer", use_container_width=True):
            st.session_state.pop('lga_modo', None)
            st.session_state.pop('lga_pot_man', None)
            st.session_state.pop('lga_long', None)
            st.session_state.pop('lga_mat', None)
            st.session_state.pop('lga_met', None)
            st.session_state.pop('lga_aisl', None)
            st.session_state.pop('lga_enlace', None)
            st.session_state.pop('lga_icc', None)
            st.rerun()

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

    # --- CONTROLES DE ENTRADA DINÁMICOS ---
    lga_modo_potencia = st.radio("Origen de la Potencia (Pt):", ["Automático", "Manual"], horizontal=True, key="lga_modo")
    
    if lga_modo_potencia == "Automático":
        lga_pot = pt_auto
        st.info(f"⚡ **Potencia Automática (Previsión de Cargas):** {lga_pot:,.2f} W\n\n*Desglose: Viviendas ({p_viv_total:,}W) + Locales ({p_loc_total:,.0f}W) + Servicios ({p_serv_total:,.2f}W) + Garajes ({p_gar_total:,.2f}W)*")
    else:
        lga_pot = st.number_input("✏️ Introduce la Potencia de cálculo LGA (en W):", value=pt_auto, step=500.0, key="lga_pot_man")

    with st.form("form_lga_parametros"):
        lga_c1, lga_c2 = st.columns(2)
        with lga_c1:
            lga_long = st.number_input("Longitud de la LGA (m)", value=0.0, step=1.0, key="lga_long")
            lga_mat = st.selectbox("Material Conductor", ["cobre", "aluminio"], key="lga_mat")
            metodo_lga_key = st.selectbox("Instalación:", list(METODOS_INSTALACION.keys()), index=3, key="lga_met")

        with lga_c2:
            lga_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="lga_aisl")
            tipo_enlace_lga = st.radio("Contadores:", ["Totalmente concentrados (Límite CDT = 0.5%)", "Centralizaciones Parciales (Límite CDT = 1.0%)"], key="lga_enlace")
            lga_icc_orig = st.number_input("Icc en origen (kA)", value=10.0, step=0.5, key="lga_icc")

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

    # --- BLOQUE 1 ---
    st.markdown(f"""
    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 10px;">
        <h4>1. Intensidad de Diseño Trifásica (Ib)</h4>
        <p><b>Fórmula:</b> I<sub>b</sub> = P / (√3 · V · cos φ)</p>
        <p><b>Sustitución:</b> I<sub>b</sub> = {lga_pot:,.2f} / (1.732 · 400 · 0.9) = <b>{ib_lga:.2f} A</b></p>
    </div>
    """, unsafe_allow_html=True)

    # --- BLOQUE 2 ---
    st.markdown(f"""
    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 10px;">
        <h4>2. Sección Teórica por Caída de Tensión (ΔV)</h4>
        <p><b>Fórmula:</b> S = (P · L) / (γ · ΔV · V)</p>
        <p><b>Sustitución:</b> S = ({lga_pot:,.2f} · {lga_long}) / ({gamma_lga} · {dv_max_lga:.2f} · 400) = <b>{s_cdt_lga:.2f} mm²</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- BLOQUE 3 ---
    st.markdown(f"""
    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 10px;">
        <h4>3. Icc Mínima y Fusibles de Compañía (CGP)</h4>
        <p><b>Icc al final de la línea:</b> <b>{icc_fin_lga:.1f} A</b> ({icc_fin_lga / 1000.0:.2f} kA)</p>
        <p><b>Veredicto:</b> Garantiza la fusión de los protecciones de origen de <b>{in_lga_auto} A (Tipo gG)</b>.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""<div style="background: #f1f5f9; color: #0f172a; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #cbd5e1;">🛡️ FUSIBLES RECOMENDADOS EN CGP: {in_lga_auto} A (Tipo gG)</div>""", unsafe_allow_html=True)

    # --- TABLA DE CORRIENTES ---
    st.markdown("### 📊 Tabla de Corrientes Admisibles y Verificación (REBT)")
    
    filas_lista = []
    for s_com in SECCIONES_COMERCIALES:
        iz_val_t = tabla_iz.get(s_com, 0)
        dv_c_pct = ((lga_pot * lga_long) / (gamma_lga * s_com * 400) / 400) * 100 if s_com > 0 else 0.0
        cond_s_lga = 0.91 * iz_val_t
        
        bg_row = "background-color: #f0fdf4;" if s_com == s_final_lga else ""
        
        if iz_val_t < ib_lga:
            est = "❌ Falla Calentamiento"
        elif in_lga_auto > cond_s_lga:
            est = f"❌ Falla (I<sub>n</sub> {in_lga_auto}A > {cond_s_lga:.1f}A)"
        elif s_com == s_final_lga:
            est = f"✅ <b>CUMPLE IDEAL</b> (I<sub>n</sub> {in_lga_auto}A ≤ {cond_s_lga:.1f}A)"
        else:
            est = "Válido pero sobredimensionado"
            
        fila_str = f'<tr style="border-bottom: 1px solid #e2e8f0; {bg_row}"><td style="padding: 12px 16px; font-weight: bold;">{s_com} mm²</td><td style="padding: 12px 16px;">{iz_val_t} A</td><td style="padding: 12px 16px;">{dv_c_pct:.3f}%</td><td style="padding: 12px 16px;">{est}</td></tr>'
        filas_lista.append(fila_str)

    html_tabla_secciones = f"""
    <div style="overflow-x: auto; margin-bottom: 20px;">
    <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <thead>
            <tr style="background-color: #1e293b; color: #ffffff; text-align: left; font-size: 14px;">
                <th style="padding: 12px 16px;">SECCIÓN</th>
                <th style="padding: 12px 16px;">IZ ADMISIBLE (A)</th>
                <th style="padding: 12px 16px;">CDT REAL (%)</th>
                <th style="padding: 12px 16px;">ESTADO DE VERIFICACIÓN (I<sub>n</sub> ≤ 0.91 · I<sub>z</sub>)</th>
            </tr>
        </thead>
        <tbody style="font-size: 14px; color: #334155;">
            {"".join(filas_lista)}
        </tbody>
    </table>
    </div>
    """
    st.markdown(html_tabla_secciones, unsafe_allow_html=True)

    st.success(f"""
    ### ✅ SECCIÓN ÓPTIMA LGA: {s_final_lga} mm² de {lga_mat.upper()}
    Garantiza una caída real del **{dv_real_lga_pct:.3f}%**. Protegida en origen por **Fusibles gG de {in_lga_auto} A**.
    """)
