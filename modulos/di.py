import streamlit as st
import math
import datetime
from modulos import rebt_tablas as rebt
from modulos import pdf_di

METODOS_INSTALACION_DI = {
    "B1 (Bajo tubo empotrado)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas"},
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Multiconductor en pared)": {"ref": "C", "desc": "Cable multiconductor fijado directo"}
}
SECCIONES_COMERCIALES_DI = [6, 10, 16, 25, 35, 50, 70, 95]
CALIBRES_IGA = [16, 20, 25, 32, 40, 50, 63]

def seleccionar_seccion_optima_di(s_necesaria):
    return rebt.seleccionar_seccion_optima(s_necesaria, material="cobre", s_minima=6.0)

def seleccionar_iga(ib):
    return rebt.seleccionar_proteccion(ib, tipo="pia")

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

    st.title("🏠 Derivación Individual - DI (ITC-BT-15)")

    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">⚡ SECCIÓN 1: Parámetros de Diseño de la Derivación Individual (ITC-BT-15)</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        with st.form("form_di_parametros"):
            di_c1, di_c2 = st.columns(2)
            with di_c1:
                di_pot = st.number_input("Potencia de cálculo DI (W) - Ej: 5750", value=5750.0, step=250.0, key="di_pot")
                di_long = st.number_input("Longitud de la DI (m)", value=15.0, step=1.0, key="di_long")
                di_mat = st.selectbox("Material Conductor", ["cobre"], key="di_mat")
                metodo_di_key = st.selectbox("Instalación:", list(METODOS_INSTALACION_DI.keys()), index=0, key="di_met")
            with di_c2:
                di_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="di_aisl")
                tipo_suministro = st.radio("Tipo de Suministro:", ["Monofásico (230 V)", "Trifásico (400 V)"], key="di_sum", horizontal=True)
                di_icc_orig = st.number_input("Icc en origen / contador (kA)", value=10.0, step=0.5, key="di_icc")

            submitted_di = st.form_submit_button("🔄 Recalcular / Actualizar Cálculo DI", type="primary")

    es_trifasico = "Trifásico" in tipo_suministro
    v_tension = 400.0 if es_trifasico else 230.0
    cos_phi_di = 1.0 
    
    ib_di = rebt.calcular_intensidad_diseno(di_pot, v_tension, cos_phi_di, es_trifasico)
    
    dv_pct_di = 1.0 
    gamma_di = rebt.obtener_gamma(di_mat, di_aisl)
    dv_max_di = v_tension * (dv_pct_di / 100.0)
    
    s_cdt_di = rebt.calcular_seccion_por_cdt(di_pot, di_long, gamma_di, dv_pct_di, v_tension, es_trifasico)

    in_iga_auto = seleccionar_iga(ib_di)
    s_final_di = seleccionar_seccion_optima_di(max(s_cdt_di, 6.0)) 
    
    tabla_iz_di = rebt.obtener_tabla_iz(di_mat, di_aisl, metodo_di_key)
    while True:
        iz_a_di = tabla_iz_di.get(s_final_di, 61.0)
        if in_iga_auto <= iz_a_di and iz_a_di >= ib_di: break
        idx_s = SECCIONES_COMERCIALES_DI.index(s_final_di) if s_final_di in SECCIONES_COMERCIALES_DI else 0
        if idx_s < len(SECCIONES_COMERCIALES_DI) - 1: s_final_di = SECCIONES_COMERCIALES_DI[idx_s + 1]
        else: break

    dv_real_di_v = rebt.calcular_caida_tension_v(di_pot, di_long, gamma_di, s_final_di, v_tension, es_trifasico)
    dv_real_di_pct = rebt.calcular_caida_tension_pct(dv_real_di_v, v_tension)

    rho_di = 1.0 / gamma_di if gamma_di > 0 else 0.0
    r_cable_di = (rho_di * di_long) / s_final_di if s_final_di > 0 else 0.0
    
    z_orig_ohms = v_tension / (di_icc_orig * 1000.0)
    r_total_cable = (2.0 if not es_trifasico else 1.0) * r_cable_di
    z_tot_di = z_orig_ohms + r_total_cable
    icc_fin_di = v_tension / z_tot_di if z_tot_di > 0 else 0.0
    umbral_magnetico_iga = 10.0 * in_iga_auto

    st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">📋 SECCIÓN 2: Memoria Analítica y Resultados Técnicos REBT</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        if es_trifasico:
            formula_ib_str = r"I_b = \frac{P}{\sqrt{3} \cdot V \cdot \cos\varphi}"
            sust_ib_str = f"I_b = \\frac{{{di_pot:,.1f} \\text{{ W}}}}{{\\sqrt{3} \\cdot 400 \\text{{ V}} \\cdot 1.0}} = \\mathbf{{{ib_di:.2f}\\text{{ A}}}}"
        else:
            formula_ib_str = r"I_b = \frac{P}{V \cdot \cos\varphi}"
            sust_ib_str = f"I_b = \\frac{{{di_pot:,.1f} \\text{{ W}}}}{{230 \\text{{ V}} \\cdot 1.0}} = \\mathbf{{{ib_di:.2f}\\text{{ A}}}}"

        col_di_res1, col_di_res2 = st.columns(2)
        with col_di_res1:
            st.info(f"""
            #### 1. Intensidad de Diseño {'Trifásica' if es_trifasico else 'Monofásica'} ($I_b$)
            
            **Criterio y Fórmula Reglamentaria:**
            $${formula_ib_str}$$
            
            **Sustitución Numérica y Resultado:**
            $${sust_ib_str}$$
            """)

        with col_di_res2:
            if es_trifasico:
                formula_s_str = r"S = \frac{P \cdot L}{\gamma \cdot \Delta V \cdot V}"
                sust_s_str = f"S = \\frac{{{di_pot:,.1f} \\cdot {di_long}}}{{{gamma_di} \\cdot {dv_max_di:.2f} \\cdot 400}} = \\mathbf{{{s_cdt_di:.2f}\\text{{ mm}}^2}}"
            else:
                formula_s_str = r"S = \frac{2 \cdot P \cdot L}{\gamma \cdot \Delta V \cdot V}"
                sust_s_str = f"S = \\frac{{2 \\cdot {di_pot:,.1f} \\cdot {di_long}}}{{{gamma_di} \\cdot {dv_max_di:.2f} \\cdot 230}} = \\mathbf{{{s_cdt_di:.2f}\\text{{ mm}}^2}}"

            st.info(f"""
            #### 2. Sección Teórica por Caída de Tensión ($\\Delta V$)
            
            **Criterio y Fórmula Reglamentaria:**
            $${formula_s_str}$$
            
            **Sustitución Numérica y Resultado:**
            $${sust_s_str}$$
            """)
            
        st.info(f"""
        #### 3. Comprobación de Cortocircuito y Protección IGA (Disparo Magnético 0.1s)
        
        * **Icc estimada al final de la DI:** **{icc_fin_di:,.1f} A** ({icc_fin_di / 1000:.2f} kA)
        * **Umbral de disparo magnético exigido ($10 \\cdot I_n$):** **{umbral_magnetico_iga:.1f} A**
        * **Veredicto de Protección:** {'✅ **GARANTIZADO** (La Icc final de cortocircuito de ' + f'{icc_fin_di:.1f} A' + ' supera ampliamente el umbral magnético de disparo instantáneo del IGA de ' + str(in_iga_auto) + ' A).' if icc_fin_di >= umbral_magnetico_iga else '⚠️ **REVISAR** (La Icc es inferior al umbral magnético de la curva C).'}
        """)

        st.markdown(f"""<div style="background: #f1f5f9; color: #0f172a; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #cbd5e1;">🛡️ IGA RECOMENDADO EN CUADRO VIVIENDA: {in_iga_auto} A (Curva C)</div>""", unsafe_allow_html=True)

        st.markdown("#### 📊 Tabla de Verificación de Secciones Comerciales (DI)")
        tabla_di_md = "| SECCIÓN | IZ ADMISIBLE (A) | CDT REAL (%) | ESTADO DE VERIFICACIÓN ($I_n \\le I_z$) |\n| :--- | :--- | :--- | :--- |\n"
        tabla_secciones_di_list = []

        for s_com in [6, 10, 16, 25, 35]:
            iz_val_di = tabla_iz_di.get(s_com, 61.0)
            dv_c_v = rebt.calcular_caida_tension_v(di_pot, di_long, gamma_di, s_com, v_tension, es_trifasico)
            dv_c_di_pct = rebt.calcular_caida_tension_pct(dv_c_v, v_tension)
            cond_s_di = iz_val_di
            if iz_val_di < ib_di:
                est = "❌ Falla Calentamiento"
                est_clean = "Falla Calentamiento"
            elif in_iga_auto > cond_s_di:
                est = f"❌ Falla ($I_n$ {in_iga_auto}A > {cond_s_di:.1f}A)"
                est_clean = f"Falla (In {in_iga_auto}A > {cond_s_di:.1f}A)"
            elif s_com == s_final_di:
                est = f"✅ **CUMPLE IDEAL** ($I_n$ {in_iga_auto}A $\\le$ {cond_s_di:.1f}A)"
                est_clean = f"CUMPLE IDEAL (In {in_iga_auto}A ≤ {cond_s_di:.1f}A)"
            else:
                est = "Válido pero sobredimensionado"
                est_clean = "Válido sobredimensionado"
            
            tabla_di_md += f"| **{s_com} mm²** | {iz_val_di} A | {dv_c_di_pct:.3f}% | {est} |\n"
            tabla_secciones_di_list.append({"sec": s_com, "iz": iz_val_di, "cdt": dv_c_di_pct, "estado": est_clean})
            
        st.markdown(tabla_di_md)

        tubo_diam_di, razon_tubo_di = rebt.dimensionar_tubo_di(s_final_di)

        st.info(
            f"**🛠️ Dimensionamiento Detallado del Tubo Protector (ITC-BT-15 / ITC-BT-21):**\n\n"
            f"* **Diámetro exterior del tubo recomendado:** **{tubo_diam_di}**\n"
            f"* **Explicación técnica:** {razon_tubo_di}\n"
            f"* **Normativa aplicable:** ITC-BT-15 apdo. 3 (Ø 32 mm reserva del 100%)."
        )

        st.success(f"""
        ### ✅ SECCIÓN ÓPTIMA DI: {s_final_di} mm² de COBRE (CPR ES07Z1-K)
        Garantiza una caída de tensión real del **{dv_real_di_pct:.3f}%**. Protegida en cuadro por **IGA de {in_iga_auto} A (Curva C)** y tubo de **{tubo_diam_di}**.
        """)

    # --- SECCIÓN DE EXPORTACIÓN Y GENERACIÓN DE REPORTE PDF DI ---
    st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">🖨️ SECCIÓN 3: Generación de Reporte Técnico Oficial en PDF</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        with st.expander("📄 Configurar Datos del Proyecto y Exportar PDF Profesional (ReportLab / Impresión)", expanded=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                p_nombre = st.text_input("Nombre de la Obra / Edificio", "Vivienda Unifamiliar Bolimur", key="di_pdf_nombre")
                p_emplazamiento = st.text_input("Emplazamiento / Dirección", "Calle Mayor nº 45", key="di_pdf_emp")
            with col_m2:
                p_proyectista = st.text_input("Técnico / Instalador Autorizado", "Ingeniero Electrónico / Instalador REBT", key="di_pdf_proy")
                p_expediente = st.text_input("Nº Expediente / Referencia", "EXP-DI-2026", key="di_pdf_exp")

            proyecto_info = {
                "nombre": p_nombre,
                "emplazamiento": p_emplazamiento,
                "proyectista": p_proyectista,
                "expediente": p_expediente,
                "fecha": datetime.date.today().strftime("%d/%m/%Y")
            }

            di_params = {
                "pot": di_pot,
                "long": di_long,
                "mat": di_mat,
                "aisl": di_aisl,
                "metodo": metodo_di_key,
                "suministro": tipo_suministro,
                "icc_orig": di_icc_orig,
                "dv_pct": dv_pct_di,
                "es_trifasico": es_trifasico
            }

            di_results = {
                "ib": ib_di,
                "dv_max": dv_max_di,
                "s_cdt": s_cdt_di,
                "s_final": s_final_di,
                "in_iga": in_iga_auto,
                "dv_real_v": dv_real_di_v,
                "dv_real_pct": dv_real_di_pct,
                "r_cable": r_cable_di,
                "icc_fin": icc_fin_di,
                "umbral_mag": umbral_magnetico_iga,
                "tubo_diam": tubo_diam_di,
                "razon_tubo": razon_tubo_di,
                "gamma": gamma_di,
                "tabla_secciones": tabla_secciones_di_list
            }

            try:
                pdf_bytes_di = pdf_di.generar_pdf_di(proyecto_info, di_params, di_results)
                from modulos import visor_pdf
                visor_pdf.mostrar_visor_pdf(
                    pdf_bytes=pdf_bytes_di,
                    nombre_archivo=f"Reporte_DI_{p_expediente}.pdf",
                    label_boton="📥 Descargar Reporte PDF Oficial DI"
                )
            except Exception as err:
                st.error(f"⚠️ Ocurrió un error al generar el archivo PDF de DI: {err}")
