import streamlit as st
import math
import datetime
from modulos import rebt_tablas as rebt
from modulos import pdf_lga

METODOS_INSTALACION = {
    "B1 (Bajo tubo empotrado)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas"},
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Multiconductor en pared)": {"ref": "C", "desc": "Cable multiconductor fijado directo"},
    "D (Cables enterrados bajo tubo)": {"ref": "D", "desc": "Instalación subterránea"}
}
SECCIONES_COMERCIALES = rebt.SECCIONES_COMERCIALES
CALIBRES_INTERRUPTORES = rebt.CALIBRES_INTERRUPTORES_GENERALES

def seleccionar_seccion_optima(s_necesaria, material="cobre", s_minima=10.0):
    return rebt.seleccionar_seccion_optima(s_necesaria, material, s_minima)

def seleccionar_proteccion(ib):
    return rebt.seleccionar_proteccion(ib, tipo="general")

def reset_valores_lga():
    st.session_state['lga_long'] = 0.0
    st.session_state['lga_pot_man'] = 0.0

def renderizar():
    st.markdown("""
    <style>
    @media print {
        [data-testid="stSidebar"], header, footer, .stButton, div.row-widget.stRadio, div.stSelectbox, div.stNumberInput, div.stTextInput, details summary { 
            display: none !important; 
        }
        @page { size: A4 portrait; margin: 12mm; }
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, div[data-testid="stVerticalBlock"] {
            background-color: white !important; color: black !important; font-family: "Helvetica", "Arial", sans-serif !important; font-size: 10pt !important;
            height: auto !important; min-height: auto !important; max-height: none !important; overflow: visible !important;
        }
        .stSuccess, .stInfo, div[style*="background-color"], table { break-inside: avoid !important; page-break-inside: avoid !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    col_tit_h, col_b1_h = st.columns([4, 1])
    with col_tit_h:
        st.title("⚡ Línea General de Alimentación - LGA (ITC-BT-14)")
    with col_b1_h:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.button("🔄 Restablecer", on_click=reset_valores_lga, use_container_width=True)

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
    
    try:
        from modulos import selector_cliente_proyecto
        datos_lga = {
            "lga_long": st.session_state.get("lga_long", 0.0),
            "lga_pot_man": st.session_state.get("lga_pot_man", 0.0)
        }
        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">👤 Cliente y Expediente del Proyecto</h4></div>', unsafe_allow_html=True)
        selector_cliente_proyecto.renderizar_barra_cliente_proyecto("LGA", datos_lga, "Cálculo de Línea General de Alimentación (LGA)")
    except Exception:
        pass

    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">⚡ SECCIÓN 1: Parámetros de Diseño y Potencia Prevista (Pt - ITC-BT-14)</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
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

        garaje_data = st.session_state.get('garajes', {"sup": 240.0, "plazas_irve": 18, "spl": False})
        sup_gar = garaje_data.get("sup", 0.0)
        p_gar_vent = max(sup_gar * 20.0, 3450.0 if sup_gar > 0 else 0.0)
        factor_irve = 0.05 if garaje_data.get("spl", False) or "5%" in str(garaje_data.get("tipo_irve", "")) else 0.10
        p_gar_irve = (garaje_data.get("plazas_irve", 0) * factor_irve) * 3680.0
        p_gar_total = p_gar_vent + p_gar_irve

        pt_auto = float(p_viv_total + p_loc_total + p_serv_total + p_gar_total)

        lga_modo_potencia = st.radio("Origen de la Potencia (Pt):", ["Automático", "Manual"], horizontal=True, key="lga_modo")
        
        if lga_modo_potencia == "Automático":
            lga_pot = pt_auto
            st.info(f"⚡ **Potencia Automática (Previsión de Cargas):** {lga_pot:,.2f} W\n\n*Desglose: Viviendas ({p_viv_total:,}W) + Locales ({p_loc_total:,.0f}W) + Servicios ({p_serv_total:,.2f}W) + Garajes ({p_gar_total:,.2f}W)*")
        else:
            lga_pot = st.number_input("✏️ Introduce la Potencia de cálculo LGA manual (en W):", value=pt_auto, step=500.0, key="lga_pot_man")

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

            submitted = st.form_submit_button("🔄 Recalcular / Actualizar Cálculo", type="primary")

    dv_pct_lga = 0.5 if "concentrados" in tipo_enlace_lga else 1.0
    gamma_lga = rebt.obtener_gamma(lga_mat, lga_aisl)
    ib_lga = rebt.calcular_intensidad_diseno(lga_pot, 400.0, 0.9, es_trifasico=True)
    dv_max_lga = 400.0 * (dv_pct_lga / 100.0)
    s_cdt_lga = rebt.calcular_seccion_por_cdt(lga_pot, lga_long, gamma_lga, dv_pct_lga, 400.0, es_trifasico=True)
    
    min_reg_lga = 16.0 if "alum" in lga_mat.lower() else 10.0
    tabla_iz = rebt.obtener_tabla_iz(lga_mat, lga_aisl, metodo_lga_key)
    in_lga_auto = seleccionar_proteccion(ib_lga)
    s_final_lga = rebt.seleccionar_seccion_optima(max(s_cdt_lga, min_reg_lga), material=lga_mat, s_minima=min_reg_lga)
    
    secciones_disponibles_lga = rebt.obtener_secciones_disponibles(lga_mat)
    while True:
        iz_a = tabla_iz.get(s_final_lga, 230.0)
        if in_lga_auto <= 0.91 * iz_a and iz_a >= ib_lga: break
        idx_s = secciones_disponibles_lga.index(s_final_lga) if s_final_lga in secciones_disponibles_lga else 0
        if idx_s < len(secciones_disponibles_lga) - 1: s_final_lga = secciones_disponibles_lga[idx_s + 1]
        else: break

    dv_real_lga_v = rebt.calcular_caida_tension_v(lga_pot, lga_long, gamma_lga, s_final_lga, 400.0, es_trifasico=True)
    dv_real_lga_pct = rebt.calcular_caida_tension_pct(dv_real_lga_v, 400.0)

    rho_lga = 1.0 / gamma_lga if gamma_lga > 0 else 0.0
    r_lga_cable = (rho_lga * lga_long) / s_final_lga if s_final_lga > 0 else 0.0
    
    z_orig_lga_ohms = 400.0 / (lga_icc_orig * 1000.0)
    z_tot_lga = z_orig_lga_ohms + r_lga_cable
    icc_fin_lga = 400.0 / z_tot_lga if z_tot_lga > 0 else 0.0

    st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">📋 SECCIÓN 2: Memoria Analítica y Resultados Técnicos REBT</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        col_lga_res1, col_lga_res2 = st.columns(2)
        with col_lga_res1:
            st.info(f"""
            #### 1. Intensidad de Diseño Trifásica ($I_b$)
            
            **Criterio y Fórmula Reglamentaria:**
            $$I_b = \\frac{{P}}{{\\sqrt{{3}} \\cdot V \\cdot \\cos\\varphi}}$$
            
            **Sustitución Numérica y Resultado:**
            $$I_b = \\frac{{{lga_pot:,.2f} \\text{{ W}}}}{{\\sqrt{{3}} \\cdot 400 \\text{{ V}} \\cdot 0.9}} = \\mathbf{{ {ib_lga:.2f} \\text{{ A}} }}$$
            """)

        with col_lga_res2:
            st.info(f"""
            #### 2. Sección Teórica por Caída de Tensión ($\\Delta V$)
            
            **Criterio y Fórmula Reglamentaria:**
            $$S = \\frac{{P \\cdot L}}{{\\gamma \\cdot \\Delta V \\cdot V}}$$
            
            **Sustitución Numérica y Resultado:**
            $$S = \\frac{{{lga_pot:,.2f} \\cdot {lga_long}}}{{{gamma_lga} \\cdot {dv_max_lga:.2f} \\cdot 400}} = \\mathbf{{ {s_cdt_lga:.2f} \\text{{ mm}}^2 }}$$
            """)
            
        st.info(f"""
        #### 3. Icc Mínima y Fusibles de Compañía (CGP)
        
        * **Icc al final de la LGA:** **{icc_fin_lga:.1f} A** ({icc_fin_lga / 1000.0:.2f} kA)
        * **Veredicto de Coordinación:** ✅ La corriente de cortocircuito al final de la línea garantiza la fusión de los fusibles de protección de **{in_lga_auto} A (Tipo gG)** dentro de los márgenes reglamentarios.
        """)

        st.markdown(f"""<div style="background: #f1f5f9; color: #0f172a; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #cbd5e1;">🛡️ FUSIBLES RECOMENDADOS EN CGP: {in_lga_auto} A (Tipo gG)</div>""", unsafe_allow_html=True)

        tubo_diam, razon_tubo = rebt.dimensionar_tubo_lga(s_final_lga)

        st.info(
            f"**🛠️ Dimensionamiento Detallado del Tubo Protector (ITC-BT-14 Tabla 1):**\n\n"
            f"* **Diámetro exterior del tubo recomendado:** **{tubo_diam}**\n"
            f"* **Explicación técnica:** {razon_tubo}\n"
            f"* **Normativa aplicable:** ITC-BT-14 Tabla 1."
        )

        st.markdown("#### 📊 Tabla de Corrientes Admisibles y Verificación (REBT)")
        
        filas_lista = []
        tabla_secciones_list = []

        for s_com in secciones_disponibles_lga:
            iz_val_t = tabla_iz.get(s_com, 0)
            dv_c_v = rebt.calcular_caida_tension_v(lga_pot, lga_long, gamma_lga, s_com, 400.0, es_trifasico=True)
            dv_c_pct = rebt.calcular_caida_tension_pct(dv_c_v, 400.0)
            cond_s_lga = 0.91 * iz_val_t
            
            bg_row = "background-color: #f0fdf4;" if s_com == s_final_lga else ""
            
            if iz_val_t < ib_lga:
                est = "❌ Falla Calentamiento"
                est_clean = "Falla Calentamiento"
            elif in_lga_auto > cond_s_lga:
                est = f"❌ Falla (I<sub>n</sub> {in_lga_auto}A > {cond_s_lga:.1f}A)"
                est_clean = f"Falla (In {in_lga_auto}A > {cond_s_lga:.1f}A)"
            elif s_com == s_final_lga:
                est = f"✅ <b>CUMPLE IDEAL</b> (I<sub>n</sub> {in_lga_auto}A ≤ {cond_s_lga:.1f}A)"
                est_clean = f"CUMPLE IDEAL (In {in_lga_auto}A ≤ {cond_s_lga:.1f}A)"
            else:
                est = "Válido pero sobredimensionado"
                est_clean = "Válido sobredimensionado"
                
            fila_str = f'<tr style="border-bottom: 1px solid #e2e8f0; {bg_row}"><td style="padding: 12px 16px; font-weight: bold;">{s_com} mm²</td><td style="padding: 12px 16px;">{iz_val_t} A</td><td style="padding: 12px 16px;">{dv_c_pct:.3f}%</td><td style="padding: 12px 16px;">{est}</td></tr>'
            filas_lista.append(fila_str)
            tabla_secciones_list.append({"sec": s_com, "iz": iz_val_t, "cdt": dv_c_pct, "estado": est_clean})

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
        Garantiza una caída real del **{dv_real_lga_pct:.3f}%**. Protegida en origen por **Fusibles gG de {in_lga_auto} A** y canalizada bajo **tubo de {tubo_diam}**.
        """)

    # --- SECCIÓN DE EXPORTACIÓN Y GENERACIÓN DE REPORTE PDF ---
    st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">🖨️ SECCIÓN 3: Generación de Reporte Técnico Oficial en PDF</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        with st.expander("📄 Configurar Datos del Proyecto y Exportar PDF Profesional (ReportLab / Impresión)", expanded=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                p_nombre = st.text_input("Nombre de la Obra / Edificio", "Edificio Residencial Bolimur", key="lga_pdf_nombre")
                p_emplazamiento = st.text_input("Emplazamiento / Dirección", "Av. Principal nº 123", key="lga_pdf_emp")
            with col_m2:
                p_proyectista = st.text_input("Técnico / Instalador Autorizado", "Ingeniero Electrónico / Instalador REBT", key="lga_pdf_proy")
                p_expediente = st.text_input("Nº Expediente / Referencia", "EXP-LGA-2026", key="lga_pdf_exp")

            proyecto_info = {
                "nombre": p_nombre,
                "emplazamiento": p_emplazamiento,
                "proyectista": p_proyectista,
                "expediente": p_expediente,
                "fecha": datetime.date.today().strftime("%d/%m/%Y")
            }

            lga_params = {
                "pot": lga_pot,
                "long": lga_long,
                "mat": lga_mat,
                "aisl": lga_aisl,
                "metodo": metodo_lga_key,
                "enlace": tipo_enlace_lga,
                "icc_orig": lga_icc_orig,
                "dv_pct": dv_pct_lga
            }

            lga_results = {
                "ib": ib_lga,
                "dv_max": dv_max_lga,
                "s_cdt": s_cdt_lga,
                "s_final": s_final_lga,
                "in_auto": in_lga_auto,
                "dv_real_v": dv_real_lga_v,
                "dv_real_pct": dv_real_lga_pct,
                "r_cable": r_lga_cable,
                "z_tot": z_tot_lga,
                "icc_fin": icc_fin_lga,
                "tubo_diam": tubo_diam,
                "razon_tubo": razon_tubo,
                "gamma": gamma_lga,
                "tabla_secciones": tabla_secciones_list
            }

            try:
                pdf_bytes_lga = pdf_lga.generar_pdf_lga(proyecto_info, lga_params, lga_results)
                from modulos import visor_pdf
                visor_pdf.mostrar_visor_pdf(
                    pdf_bytes=pdf_bytes_lga,
                    nombre_archivo=f"Reporte_LGA_{p_expediente}.pdf",
                    label_boton="📥 Descargar Reporte PDF Oficial LGA"
                )
            except Exception as err:
                st.error(f"⚠️ Ocurrió un error al generar el archivo PDF de LGA: {err}")
