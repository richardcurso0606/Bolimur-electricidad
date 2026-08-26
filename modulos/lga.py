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
    
    # --- AYUDA TÉCNICA DESPLEGABLE ---
    with st.expander("📖 Ayuda Técnica: Tabla de Conductividad (γ) y Resistividad (ρ) del REBT"):
        st.markdown("Valores oficiales de conductividad ($\gamma$) y resistividad ($\rho$) según la norma UNE-HD 60364-5-2:")
        
        st.markdown("""
        <div style="overflow-x: auto; margin-top: 10px; margin-bottom: 10px;">
        <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background-color: #1e293b; color: #ffffff; text-align: left; font-size: 13px;">
                    <th style="padding: 10px 14px;">MATERIAL CONDUCTOR</th>
                    <th style="padding: 10px 14px;">AISLAMIENTO</th>
                    <th style="padding: 10px 14px;">TEMP. SERVICIO</th>
                    <th style="padding: 10px 14px;">CONDUCTIVIDAD (γ) [m/(Ω·mm²)]</th>
                    <th style="padding: 10px 14px;">RESISTIVIDAD (ρ) [Ω·mm²/m]</th>
                </tr>
            </thead>
            <tbody style="font-size: 13px; color: #334155;">
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold;">Cobre</td>
                    <td style="padding: 10px 14px;">PVC</td>
                    <td style="padding: 10px 14px;">70 ºC</td>
                    <td style="padding: 10px 14px; font-weight: bold; color: #0284c7;">56.0</td>
                    <td style="padding: 10px 14px;">~0.0179</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
                    <td style="padding: 10px 14px; font-weight: bold;">Cobre</td>
                    <td style="padding: 10px 14px;">XLPE / EPR</td>
                    <td style="padding: 10px 14px;">90 ºC</td>
                    <td style="padding: 10px 14px; font-weight: bold; color: #0284c7;">44.0</td>
                    <td style="padding: 10px 14px;">~0.0227</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold;">Aluminio</td>
                    <td style="padding: 10px 14px;">PVC</td>
                    <td style="padding: 10px 14px;">70 ºC</td>
                    <td style="padding: 10px 14px; font-weight: bold; color: #0284c7;">35.0</td>
                    <td style="padding: 10px 14px;">~0.0286</td>
                </tr>
                <tr style="background-color: #f8fafc;">
                    <td style="padding: 10px 14px; font-weight: bold;">Aluminio</td>
                    <td style="padding: 10px 14px;">XLPE / EPR</td>
                    <td style="padding: 10px 14px;">90 ºC</td>
                    <td style="padding: 10px 14px; font-weight: bold; color: #0284c7;">28.0</td>
                    <td style="padding: 10px 14px;">~0.0357</td>
                </tr>
            </tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)

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
    st.info(f"""
    #### 1. Intensidad de Diseño Trifásica ($I_b$)
    
    **Criterio y Fórmula Reglamentaria:**
    $$I_b = \\frac{{P}}{{\\sqrt{{3}} \\cdot V \\cdot \\cos\\varphi}}$$
    
    **Leyenda y Definición de Variables:**
    * **I_b**: Intensidad de cálculo o de diseño por fase (A).
    * **P**: Potencia total prevista de transporte en la línea ($P_t$ = {lga_pot:,.2f} W).
    * **V**: Tensión nominal compuesta entre fases (400 V).
    * **cos φ**: Factor de potencia estimado para instalaciones generales (0.9).
    * **√3**: Constante trifásica ($\\approx 1.732$).
    
    **Sustitución Numérica y Resultado:**
    $$I_b = \\frac{{{lga_pot:,.2f} \\text{{ W}}}}{{\\sqrt{{3}} \\cdot 400 \\text{{ V}} \\cdot 0.9}} = \\frac{{{lga_pot:,.2f}}}{{623.54}} = \\mathbf{{ {ib_lga:.2f} \\text{{ A}} }}$$
    """)

    # --- BLOQUE 2: SECCIÓN POR CAÍDA DE TENSIÓN ---
    st.info(f"""
    #### 2. Sección Teórica por Caída de Tensión ($\\Delta V$)
    
    **Criterio y Fórmula Reglamentaria:**
    $$S = \\frac{{P \\cdot L}}{{\\gamma \\cdot \\Delta V \\cdot V}}$$
    
    **Leyenda y Definición de Variables:**
    * **S**: Sección teórica mínima exigida del conductor ($\\text{{mm}}^2$).
    * **P**: Potencia total de cálculo ({lga_pot:,.2f} W).
    * **L**: Longitud unifilar de la línea ({lga_long} m).
    * **γ**: Conductividad del material a servicio normal ({gamma_lga} m/(Ω·mm²) para {lga_aisl}).
    * **ΔV**: Caída de tensión máxima admisible ({dv_pct_lga}% de 400V = {dv_max_lga:.2f} V).
    * **V**: Tensión nominal (400 V).
    
    **Sustitución Numérica y Resultado:**
    $$S = \\frac{{{lga_pot:,.2f} \\cdot {lga_long}}}{{{gamma_lga} \\cdot {dv_max_lga:.2f} \\cdot 400}} = \\mathbf{{ {s_cdt_lga:.2f} \\text{{ mm}}^2 }}$$
    """)
    
    # --- BLOQUE 3: ICC MÍNIMA Y FUSIBLES ---
    st.info(f"""
    #### 3. Icc Mínima y Fusibles de Compañía (CGP)
    
    **Criterio y Fórmula Reglamentaria (ITC-BT-14 / ITC-BT-22):**
    Verificamos que los fusibles de protección tipo gG situados en la CGP fundirán a tiempo en caso de un cortocircuito franco al final de la Línea General de Alimentación.
    
    $$I_{{cc,final}} = \\frac{{V}}{{\\left(\\frac{{V}}{{I_{{cc,origen}}}}\\right) + R_{{cable}}}}$$
    
    **Leyenda y Definición de Variables:**
    * **I_cc,final**: Corriente de cortocircuito estimada al final de la LGA (A).
    * **V**: Tensión nominal compuesta de referencia (400 V).
    * **I_cc,origen**: Corriente de cortocircuito en el origen de la línea ({lga_icc_orig * 1000:,.0f} A).
    * **R_cable**: Resistencia activa del conductor en el tramo ($R = \\frac{{\\rho \\cdot L}}{{S}} = {r_lga_cable:.5f}\\ \\Omega$).
    * **In**: Calibre de los fusibles gG de protección en origen ({in_lga_auto} A).
    
    **Sustitución Numérica y Verificación Reglamentaria:**
    $$I_{{cc,final}} = \\frac{{400}}{{\\left(\\frac{{400}}{{{lga_icc_orig * 1000.0}}}\\right) + {r_lga_cable:.5f}}} = \\frac{{400}}{{{z_orig_lga_ohms:.5f} + {r_lga_cable:.5f}}} = \\frac{{400}}{{{z_tot_lga:.5f}}} = \\mathbf{{ {icc_fin_lga:.1f} \\text{{ A}} }}$$
    
    * **Icc al final de la LGA:** **{icc_fin_lga:.1f} A** ({icc_fin_lga / 1000.0:.2f} kA)
    * **Veredicto de Coordinación:** ✅ La corriente de cortocircuito al final de la línea garantiza la fusión de los fusibles de protección de **{in_lga_auto} A (Tipo gG)** dentro de los márgenes reglamentarios exigidos por el REBT.
    """)

    st.markdown(f"""<div style="background: #f1f5f9; color: #0f172a; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #cbd5e1;">🛡️ FUSIBLES RECOMENDADOS EN CGP: {in_lga_auto} A (Tipo gG)</div>""", unsafe_allow_html=True)

    # --- BLOQUE 4: RECOMENDACIÓN DE TUBO Y CANALIZACIÓN (ITC-BT-14) ---
    st.markdown("---")
    st.markdown("### 🛠️ Dimensionamiento Detallado del Tubo Protector (ITC-BT-14 / ITC-BT-21)")

    if s_final_lga <= 16:
        tubo_diam = "Ø 40 mm o Ø 50 mm"
        razon_tubo = "Suficiente para albergar hilos de menor calibre respetando el espacio de llenaje permitido."
    elif s_final_lga <= 35:
        tubo_diam = "Ø 50 mm o Ø 63 mm"
        razon_tubo = "Requerido para alojar sin apretar los 4 conductores unipolares de sección media."
    elif s_final_lga <= 50:
        tubo_diam = "Ø 63 mm"
        razon_tubo = f"Para tus hilos de cobre de {s_final_lga} mm² (sección de cable), se exigen al menos 4 hilos en trifásica. Respetando la ley de llenaje (máximo 30-40% del tubo para que no se ahoguen y se puedan pasar tirando en la obra), el tubo exterior comercial perfecto es el de 63 mm."
    else:
        tubo_diam = "Ø 90 mm, Ø 110 mm o Bandeja técnica"
        razon_tubo = "Secciones muy pesadas que requieren tubos de gran calibre o bandejas registrables debido a la rigidez del cable."

    st.info(
        f"**Análisis del Tubo para tu sección óptima de cable de {s_final_lga} mm²:**\n\n"
        f"* **Diámetro exterior del tubo recomendado:** **{tubo_diam}**\n"
        f"* **¿Por qué se elige este tamaño? (Explicación técnica):** {razon_tubo}\n"
        f"* **Normativa aplicable:** ITC-BT-14 e ITC-BT-21 (Factores de llenaje y protección mecánica IK07)."
    )

    # --- TABLA HTML ESTILADA DE TUBOS ---
    st.markdown("### 📐 Tabla de Referencia Rápida: Sección de Cable vs. Diámetro de Tubo (ITC-BT-14)")
    
    html_tabla_tubos = """
    <div style="overflow-x: auto; margin-bottom: 20px;">
    <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <thead>
            <tr style="background-color: #1e293b; color: #ffffff; text-align: left; font-size: 14px;">
                <th style="padding: 12px 16px;">SECCIÓN DEL CABLE (LGA)</th>
                <th style="padding: 12px 16px;">DIÁMETRO EXTERIOR DEL TUBO</th>
                <th style="padding: 12px 16px;">MOTIVO TÉCNICO / REGLAMENTARIO</th>
            </tr>
        </thead>
        <tbody style="font-size: 14px; color: #334155;">
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px 16px; font-weight: bold;">10 mm² a 16 mm²</td>
                <td style="padding: 12px 16px;">Ø 40 mm o Ø 50 mm</td>
                <td style="padding: 12px 16px;">Espacio adecuado para hilos finos en acometidas pequeñas.</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
                <td style="padding: 12px 16px; font-weight: bold;">25 mm² a 35 mm²</td>
                <td style="padding: 12px 16px;">Ø 50 mm o Ø 63 mm</td>
                <td style="padding: 12px 16px;">Capacidad para 4 conductores de sección media sin sobrepresión.</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f0fdf4;">
                <td style="padding: 12px 16px; font-weight: bold; color: #166534;">50 mm² <span style="font-size: 11px; background: #dcfce7; padding: 2px 6px; border-radius: 4px;">Actual</span></td>
                <td style="padding: 12px 16px; font-weight: bold; color: #166534;">Ø 63 mm</td>
                <td style="padding: 12px 16px; color: #166534; font-weight: bold;">El tamaño ideal para cumplir el factor de llenaje del 30-40%.</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px 16px; font-weight: bold;">70 mm² a 95 mm²</td>
                <td style="padding: 12px 16px;">Ø 90 mm</td>
                <td style="padding: 12px 16px;">Tubo corrugado de gran calibre para hilos pesados y rígidos.</td>
            </tr>
            <tr style="background-color: #f8fafc;">
                <td style="padding: 12px 16px; font-weight: bold;">≥ 120 mm²</td>
                <td style="padding: 12px 16px;">Bandeja / Canaladura</td>
                <td style="padding: 12px 16px;">Canales de obra o bandejas registrables por imposibilidad de curvado en tubo.</td>
            </tr>
        </tbody>
    </table>
    </div>
    """
    st.markdown(html_tabla_tubos, unsafe_allow_html=True)

    # --- TABLA HTML ESTILADA DE CORRIENTES ADMISIBLES (CONSTRUIDA EN UNA SOLA VARIABLE LIMPIA) ---
    st.markdown("### 📊 Tabla de Corrientes Admisibles y Verificación (REBT)")
    
    lineas_filas = []
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
            
        lineas_filas.append(f"""
        <tr style="border-bottom: 1px solid #e2e8f0; {bg_row}">
            <td style="padding: 12px 16px; font-weight: bold;">{s_com} mm²</td>
            <td style="padding: 12px 16px;">{iz_val_t} A</td>
            <td style="padding: 12px 16px;">{dv_c_pct:.3f}%</td>
            <td style="padding: 12px 16px;">{est}</td>
        </tr>
        """)

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
            {"".join(lineas_filas)}
        </tbody>
    </table>
    </div>
    """
    st.markdown(html_tabla_secciones, unsafe_allow_html=True)

    st.success(f"""
    ### ✅ SECCIÓN ÓPTIMA LGA: {s_final_lga} mm² de {lga_mat.upper()}
    Garantiza una caída real del **{dv_real_lga_pct:.3f}%**. Protegida en origen por **Fusibles gG de {in_lga_auto} A** y canalizada bajo **tubo de {tubo_diam}**.
    """)
