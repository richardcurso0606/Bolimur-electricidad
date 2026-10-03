import streamlit as st
import math
import datetime
from modulos import rebt_tablas as rebt
from modulos import pdf_irve

METODOS_INSTALACION_IRVE = {
    "B1 (Bajo tubo empotrado)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas"},
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Multiconductor en pared)": {"ref": "C", "desc": "Cable multiconductor fijado directo"}
}
SECCIONES_COMERCIALES_IRVE = [2.5, 4, 6, 10, 16, 25, 35, 50]
CALIBRES_PI = [10, 16, 20, 25, 32, 40]

def seleccionar_seccion_optima_irve(s_necesaria):
    return rebt.seleccionar_seccion_optima(s_necesaria, material="cobre", s_minima=2.5)

def seleccionar_proteccion_irve(ib):
    return rebt.seleccionar_proteccion(ib, tipo="pia")

def reset_valores_irve():
    st.session_state['irve_long'] = 25.0
    st.session_state['irve_custom_w'] = 7360.0

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

    col_tit_irve, col_b1_i = st.columns([4, 1])
    with col_tit_irve:
        st.title("🚗 Línea Específica de Recarga IRVE (ITC-BT-52)")
    with col_b1_i:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.button("🔄 Restablecer", on_click=reset_valores_irve, use_container_width=True)

    with st.expander("📖 Guía Técnica: Criterios de Diseño del Circuito IRVE"):
        st.markdown("""
        Esta sección dimensiona el circuito terminal o derivación específica que alimenta el punto de recarga del vehículo eléctrico desde el origen elegido (centralización de contadores o cuadro general de la vivienda).
        
        * **Normativa:** ITC-BT-52 del REBT.
        * **Caída de Tensión Máxima Admisible:** Limitada al **1.0%** para circuitos de recarga alimentados desde centralización o contadores principales.
        * **Protecciones Obligatorias:** Magnetotérmico (PIA Curva C), Diferencial Tipo A (6mA DC) / Tipo B y Sobretensiones (VSP/VTP).
        """)

    st.markdown("### ⚙️ Parámetros de Diseño del Circuito de Recarga")
    
    with st.form("form_irve_parametros"):
        irve_c1, irve_c2 = st.columns(2)
        with irve_c1:
            irve_pot = st.selectbox("Potencia del Cargador (Wallbox)", ["3.680 W (16A - Monofásico Lento)", "7.360 W (32A - Monofásico Estándar)", "11.000 W (16A - Trifásico)", "22.000 W (32A - Trifásico)", "✏️ Personalizada (W)"], index=1, key="irve_pot_sel")
            if "Personalizada" in irve_pot:
                p_cargador_val = st.number_input("Introduce Potencia (W)", value=7360.0, step=500.0, key="irve_custom_w")
            else:
                p_cargador_val = float(irve_pot.split(" ")[0].replace(".", ""))
                
            irve_long = st.number_input("Longitud real del cable hasta la plaza (m)", value=25.0, step=1.0, key="irve_long")
            
            opciones_esquema_movil = [
                "Esquema 3a (Centralización contadores)",
                "Esquema 3b (Cuadro CGMP vivienda)",
                "Esquema 1 / 2 (Instalación colectiva / exclusiva)"
            ]
            esquema_orig = st.selectbox("Origen de la línea (Esquema ITC-BT-52):", opciones_esquema_movil, key="irve_esq")
            
        with irve_c2:
            irve_mat = st.selectbox("Material Conductor", ["cobre"], key="irve_mat")
            metodo_irve_key = st.selectbox("Instalación:", list(METODOS_INSTALACION_IRVE.keys()), index=0, key="irve_met")
            irve_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="irve_aisl")
            tipo_red_irve = st.radio("Tipo de Alimentación:", ["Monofásico (230 V)", "Trifásico (400 V)"], key="irve_red")

        submitted_irve = st.form_submit_button("🔄 Recalcular / Actualizar Circuito IRVE")

    es_trif_irve = "Trifásico" in tipo_red_irve
    v_t_irve = 400.0 if es_trif_irve else 230.0
    cos_phi_irve = 1.0
    
    ib_irve = rebt.calcular_intensidad_diseno(p_cargador_val, v_t_irve, cos_phi_irve, es_trif_irve)
    
    dv_pct_irve = 1.0
    gamma_irve = rebt.obtener_gamma(irve_mat, irve_aisl)
    dv_max_irve = v_t_irve * (dv_pct_irve / 100.0)
    
    s_cdt_irve = rebt.calcular_seccion_por_cdt(p_cargador_val, irve_long, gamma_irve, dv_pct_irve, v_t_irve, es_trif_irve)

    in_pi_auto = seleccionar_proteccion_irve(ib_irve)
    s_final_irve = seleccionar_seccion_optima_irve(max(s_cdt_irve, 2.5)) 
    
    tabla_iz_irve = rebt.obtener_tabla_iz(irve_mat, irve_aisl, metodo_irve_key)
    while True:
        iz_a_irve = tabla_iz_irve.get(s_final_irve, 61.0)
        if in_pi_auto <= iz_a_irve and iz_a_irve >= ib_irve: break
        idx_s = SECCIONES_COMERCIALES_IRVE.index(s_final_irve) if s_final_irve in SECCIONES_COMERCIALES_IRVE else 1
        if idx_s < len(SECCIONES_COMERCIALES_IRVE) - 1: s_final_irve = SECCIONES_COMERCIALES_IRVE[idx_s + 1]
        else: break

    dv_real_irve_v = rebt.calcular_caida_tension_v(p_cargador_val, irve_long, gamma_irve, s_final_irve, v_t_irve, es_trif_irve)
    dv_real_irve_pct = rebt.calcular_caida_tension_pct(dv_real_irve_v, v_t_irve)

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Específica (Circuito IRVE - ITC-BT-52)</h3>", unsafe_allow_html=True)

    if es_trif_irve:
        f_ib_irve = r"I_b = \frac{P}{\sqrt{3} \cdot V \cdot \cos\varphi}"
        s_ib_irve = f"I_b = \\frac{{{p_cargador_val:,.1f} \\text{{ W}}}}{{\\sqrt{3} \\cdot 400 \\text{{ V}} \\cdot 1.0}} = \\mathbf{{{ib_irve:.2f}\\text{{ A}}}}"
    else:
        f_ib_irve = r"I_b = \frac{P}{V \cdot \cos\varphi}"
        s_ib_irve = f"I_b = \\frac{{{p_cargador_val:,.1f} \\text{{ W}}}}{{230 \\text{{ V}} \\cdot 1.0}} = \\mathbf{{{ib_irve:.2f}\\text{{ A}}}}"

    st.info(f"""
    #### 1. Intensidad de Diseño del Punto de Recarga ($I_b$)
    
    **Fórmula Reglamentaria:**
    $${f_ib_irve}$$
    
    **Sustitución y Resultado:**
    $${s_ib_irve}$$
    """)

    if es_trif_irve:
        f_s_irve = r"S = \frac{P \cdot L}{\gamma \cdot \Delta V \cdot V}"
        s_s_irve = f"S = \\frac{{{p_cargador_val:,.1f} \\cdot {irve_long}}}{{{gamma_irve} \\cdot {dv_max_irve:.2f} \\cdot 400}} = \\mathbf{{{s_cdt_irve:.2f}\\text{{ mm}}^2}}"
    else:
        f_s_irve = r"S = \frac{2 \cdot P \cdot L}{\gamma \cdot \Delta V \cdot V}"
        s_s_irve = f"S = \\frac{{2 \\cdot {p_cargador_val:,.1f} \\cdot {irve_long}}}{{{gamma_irve} \\cdot {dv_max_irve:.2f} \\cdot 230}} = \\mathbf{{{s_cdt_irve:.2f}\\text{{ mm}}^2}}"

    st.info(f"""
    #### 2. Sección Teórica por Caída de Tensión (Línea IRVE)
    
    **Fórmula Reglamentaria (máx. 1.0% CDT):**
    $${f_s_irve}$$
    
    **Sustitución y Resultado:**
    $${s_s_irve}$$
    """)

    st.markdown("### 🛡️ Protecciones Obligatorias en el Origen y Destino del Circuito (ITC-BT-52)")
    st.markdown(f"""
    <div style="background: #f8fafc; border: 2px solid #0284c7; padding: 20px; border-radius: 8px; color: #0f172a; margin-bottom: 20px;">
        <h4 style="margin-top: 0; color: #0284c7;">Esquema de Protecciones Exigido:</h4>
        <ul>
            <li><strong>Interruptor Magnetotérmico:</strong> Calibre de <strong>{in_pi_auto} A (Curva C)</strong> adaptado para la protección del circuito de recarga.</li>
            <li><strong>Protección Diferencial:</strong> Obligatorio <strong>Diferencial Tipo A (6mA DC)</strong> o <strong>Tipo B</strong>.</li>
            <li><strong>Protección Sobretensiones:</strong> VSP/VTP transitorias y permanentes obligatorias.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if s_final_irve <= 6:
        tubo_irve = "Ø 25 mm o Ø 32 mm"
    elif s_final_irve <= 16:
        tubo_irve = "Ø 40 mm"
    else:
        tubo_irve = "Ø 50 mm"

    st.success(f"""
    ### ✅ SECCIÓN ÓPTIMA LÍNEA IRVE: {s_final_irve} mm² de {irve_mat.upper()}
    * **Origen seleccionado:** {esquema_orig}
    * **Caída de tensión estimada:** **{dv_real_irve_pct:.3f}%** (dentro del límite del 1.0%).
    * **Protección recomendada:** Magnetotérmico **PIA {in_pi_auto} A (Curva C)** + **Diferencial Tipo A / B** bajo tubo **{tubo_irve}**.
    """)

    # --- SECCIÓN DE EXPORTACIÓN A PDF IRVE ---
    st.markdown("---")
    st.subheader("🖨️ Generar Reporte Técnico e Impresión IRVE en PDF")
    
    with st.expander("📄 Configurar Datos del Proyecto y Exportar PDF Profesional (ReportLab / Impresión)", expanded=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            p_nombre = st.text_input("Nombre de la Obra / Edificio", "Instalación Recarga IRVE Bolimur", key="irve_pdf_nombre")
            p_emplazamiento = st.text_input("Emplazamiento / Dirección", "Plaza de Garaje nº 18", key="irve_pdf_emp")
        with col_m2:
            p_proyectista = st.text_input("Técnico / Instalador Autorizado", "Ingeniero Electrónico / Instalador REBT", key="irve_pdf_proy")
            p_expediente = st.text_input("Nº Expediente / Referencia", "EXP-IRVE-2026", key="irve_pdf_exp")

        proyecto_info = {
            "nombre": p_nombre,
            "emplazamiento": p_emplazamiento,
            "proyectista": p_proyectista,
            "expediente": p_expediente,
            "fecha": datetime.date.today().strftime("%d/%m/%Y")
        }

        irve_params = {
            "pot_wallbox": p_cargador_val,
            "long": irve_long,
            "mat": irve_mat,
            "aisl": irve_aisl,
            "metodo": metodo_irve_key,
            "esquema": esquema_orig,
            "red": tipo_red_irve,
            "es_trifasico": es_trif_irve
        }

        irve_results = {
            "ib": ib_irve,
            "dv_max": dv_max_irve,
            "s_cdt": s_cdt_irve,
            "s_final": s_final_irve,
            "in_pi": in_pi_auto,
            "dv_real_v": dv_real_irve_v,
            "dv_real_pct": dv_real_irve_pct,
            "tubo_irve": tubo_irve,
            "gamma": gamma_irve
        }

        try:
            pdf_bytes_irve = pdf_irve.generar_pdf_irve(proyecto_info, irve_params, irve_results)
            from modulos import visor_pdf
            visor_pdf.mostrar_visor_pdf(
                pdf_bytes=pdf_bytes_irve,
                nombre_archivo=f"Reporte_IRVE_{p_expediente}.pdf",
                label_boton="📥 Descargar Reporte PDF Oficial IRVE"
            )
        except Exception as err:
            st.error(f"⚠️ Ocurrió un error al generar el archivo PDF de IRVE: {err}")
