import streamlit as st
import math
import datetime
from modulos import rebt_tablas as rebt
from modulos import pdf_calculo_rapido

METODOS_INSTALACION = {
    "B1 (Bajo tubo empotrado)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas"},
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Multiconductor en pared)": {"ref": "C", "desc": "Cable multiconductor fijado directo"},
    "D (Cables enterrados bajo tubo)": {"ref": "D", "desc": "Instalación subterránea"}
}
SECCIONES_COMERCIALES = rebt.SECCIONES_COMERCIALES
CALIBRES_INTERRUPTORES = rebt.CALIBRES_INTERRUPTORES_GENERALES

def seleccionar_seccion_optima(s_necesaria, material="cobre", s_minima=1.5):
    return rebt.seleccionar_seccion_optima(s_necesaria, material, s_minima)

def seleccionar_proteccion(ib):
    return rebt.seleccionar_proteccion(ib, tipo="general")

def renderizar():
    st.title("🧮 Cálculo Rápido Avanzado")

    st.markdown("""
    <style>
    @media print {
        [data-testid="stSidebar"], header, footer, .stButton, div.row-widget.stRadio, div.stSelectbox, div.stNumberInput, div[data-testid="stHorizontalBlock"], details { 
            display: none !important; 
        }
        h1 { display: none !important; }
        @page { size: A4 portrait; margin: 10mm; }
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, div[data-testid="stVerticalBlock"] {
            background-color: white !important; color: black !important; font-family: "Helvetica", "Arial", sans-serif !important; font-size: 10pt !important;
            height: auto !important; min-height: auto !important; max-height: none !important; overflow: visible !important;
        }
        .stInfo, div[style*="background-color"], .pia-destacado, table, tr { break-inside: avoid !important; page-break-inside: avoid !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    rc1, rc2 = st.columns(2)
    with rc1:
        modo_carga = st.radio("Entrada:", ["Por Potencia (W)", "Por Intensidad Directa (A)"])
        tipo_red_q = st.selectbox("Sistema eléctrico", ["Monofásico (230V)", "Trifásico (400V)"])
        
        if modo_carga == "Por Potencia (W)":
            val_pot_q = st.number_input("Potencia (W)", value=0.0, step=100.0)
            cos_q = st.slider("Coseno phi (cos φ)", 0.7, 1.0, 0.85)
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q: ib_q = val_pot_q / (v_nom_calc * cos_q) if v_nom_calc * cos_q > 0 else 0.0
            else: ib_q = val_pot_q / (math.sqrt(3) * v_nom_calc * cos_q) if math.sqrt(3) * v_nom_calc * cos_q > 0 else 0.0
        else:
            ib_q = st.number_input("Intensidad Ib (A)", value=0.0, step=1.0)
            cos_q = st.slider("Coseno phi (cos φ)", 0.7, 1.0, 0.85)
            v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
            if "Monofásico" in tipo_red_q: val_pot_q = ib_q * v_nom_calc * cos_q
            else: val_pot_q = ib_q * math.sqrt(3) * v_nom_calc * cos_q

        long_q = st.number_input("Longitud del circuito (m)", value=0.0, step=5.0)

    with rc2:
        ayuda_metodo = "B1: Empotrado en pared. \nB2: En superficie bajo tubo. \nC: Multiconductor directo. \nD: Enterrado bajo tubo."
        metodo_q_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), index=0, help=ayuda_metodo)
        mat_q = st.selectbox("Material conductor", ["cobre", "aluminio"])
        ais_q = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"])
        cdt_lim_q = st.number_input("Caída de Tensión máxima (%)", value=3.0, step=0.5)
        icc_orig_q = st.number_input("Icc en origen (kA)", value=10.0, step=0.5)

    gamma_q = rebt.obtener_gamma(mat_q, ais_q)
    dv_max_q = v_nom_calc * (cdt_lim_q / 100.0) if cdt_lim_q > 0 else 1.0
    es_trifasico_q = "Trifásico" in tipo_red_q
    
    s_cdt_q = rebt.calcular_seccion_por_cdt(val_pot_q, long_q, gamma_q, cdt_lim_q, v_nom_calc, es_trifasico_q)
    tabla_iz_q = rebt.obtener_tabla_iz(mat_q, ais_q, metodo_q_key)
    min_reg_q = 1.5 if mat_q == "cobre" else 10.0

    s_cal_q = min_reg_q
    for sec, iz_val in tabla_iz_q.items():
        if iz_val >= ib_q and sec >= min_reg_q:
            s_cal_q = sec
            break

    s_bruta_q = max(s_cdt_q, s_cal_q, min_reg_q)
    s_opt_q = rebt.seleccionar_seccion_optima(s_bruta_q, material=mat_q, s_minima=min_reg_q)
    iz_opt_val = tabla_iz_q.get(s_opt_q, 0.0)

    dv_real_v_q = rebt.calcular_caida_tension_v(val_pot_q, long_q, gamma_q, s_opt_q, v_nom_calc, es_trifasico_q)
    dv_real_pct_q = rebt.calcular_caida_tension_pct(dv_real_v_q, v_nom_calc)

    rho_q = 1.0 / gamma_q if gamma_q > 0 else 0.0
    r_cable_unitario = (rho_q * long_q) / s_opt_q if s_opt_q > 0 else 0.0
    
    if not es_trifasico_q:
        r_cable_total = 2.0 * r_cable_unitario
    else:
        r_cable_total = r_cable_unitario

    z_origen = v_nom_calc / (icc_orig_q * 1000.0) if icc_orig_q > 0 else 0
    z_tot_q = z_origen + r_cable_total
    icc_fin_q = (v_nom_calc / z_tot_q / 1000.0) if z_tot_q > 0 else 0.0
    prot_q = seleccionar_proteccion(ib_q)
    corriente_disparo = prot_q * 10.0
    salta_proteccion = (icc_fin_q * 1000.0) >= corriente_disparo

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Detallada</h3>", unsafe_allow_html=True)

    if "Monofásico" in tipo_red_q:
        f_ib = r"$$I_b = \frac{P}{V \cdot \cos\varphi}$$"
        r_ib = f"{val_pot_q:,.1f} W / ({v_nom_calc} V $\cdot$ {cos_q})"
    else:
        f_ib = r"$$I_b = \frac{P}{\sqrt{3} \cdot V \cdot \cos\varphi}$$"
        r_ib = f"{val_pot_q:,.1f} W / (1.732 $\cdot$ {v_nom_calc} V $\cdot$ {cos_q})"

    st.info(
        f"#### 1. Intensidad de Diseño ($I_b$)\n"
        f"**Justificación:** Se calcula la corriente nominal base de la carga ($I_z \ge I_b$).\n\n"
        f"{f_ib}\n\n"
        f"**Sustitución y Resultado:** {r_ib} = **{ib_q:.2f} A**"
    )

    st.info(
        f"#### 2. Determinación de Sección por Calentamiento ($I_z$)\n"
        f"* **Corriente de diseño ($I_b$):** {ib_q:.2f} A\n"
        f"* **Sección requerida:** **{s_cal_q} mm²** (Admite $I_z =$ {tabla_iz_q.get(s_cal_q, 0)} A)."
    )

    if "Monofásico" in tipo_red_q:
        f_cdt = r"$$S = \frac{2 \cdot P \cdot L}{\gamma \cdot \Delta V \cdot V}$$"
        r_cdt = f"(2 $\cdot$ {val_pot_q:,.1f} $\cdot$ {long_q}) / ({gamma_q} $\cdot$ {dv_max_q:.2f} $\cdot$ {v_nom_calc})"
    else:
        f_cdt = r"$$S = \frac{P \cdot L}{\gamma \cdot \Delta V \cdot V}$$"
        r_cdt = f"({val_pot_q:,.1f} $\cdot$ {long_q}) / ({gamma_q} $\cdot$ {dv_max_q:.2f} $\cdot$ {v_nom_calc})"

    st.info(
        f"#### 3. Sección Teórica por Caída de Tensión ($\Delta V$)\n"
        f"{f_cdt}\n\n"
        f"**Sustitución y Resultado:** {r_cdt} = **{s_cdt_q:.2f} mm²**"
    )

    estado_icc = "✅ GARANTIZADO" if salta_proteccion else "⚠️ PELIGRO: NO SALTARÁ A TIEMPO"
    st.info(
        f"#### 4. Comprobación Cortocircuito y Disparo Magnético (0.1s)\n"
        f"* **Icc final estimada:** **{icc_fin_q * 1000:.1f} A** ({icc_fin_q:.2f} kA)\n"
        f"* **Umbral disparo PIA ({prot_q} A $\\times$ 10):** {corriente_disparo:.1f} A\n"
        f"* **Veredicto:** {estado_icc}"
    )

    st.markdown(f"""<div style="background: #f1f5f9; color: #0f172a; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #cbd5e1;">🛡️ PROTECCIÓN MAGNETOTÉRMICA: PIA {prot_q} A (Curva C)</div>""", unsafe_allow_html=True)

    tubo_diam_q, razon_tubo_q = rebt.dimensionar_tubo_di(s_opt_q)

    st.success(f"""
    ### ✅ SECCIÓN ÓPTIMA ADOPTADA: {s_opt_q} mm² ({mat_q.upper()})
    Garantiza una caída de tensión real del **{dv_real_pct_q:.3f}%**. Coordinada con **PIA {prot_q} A (Curva C)**.
    """)

    # --- SECCIÓN DE EXPORTACIÓN A PDF ---
    st.markdown("---")
    st.subheader("🖨️ Generar Reporte Técnico e Impresión en PDF")
    
    with st.expander("📄 Configurar Datos del Proyecto y Exportar PDF Profesional (ReportLab / Impresión)", expanded=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            p_nombre = st.text_input("Nombre de la Obra / Edificio", "Instalación Eléctrica General", key="cr_pdf_nombre")
            p_emplazamiento = st.text_input("Emplazamiento / Dirección", "Calle Principal nº 1", key="cr_pdf_emp")
        with col_m2:
            p_proyectista = st.text_input("Técnico / Instalador Autorizado", "Ingeniero Electrónico / Instalador REBT", key="cr_pdf_proy")
            p_expediente = st.text_input("Nº Expediente / Referencia", "EXP-CR-2026", key="cr_pdf_exp")

        proyecto_info = {
            "nombre": p_nombre,
            "emplazamiento": p_emplazamiento,
            "proyectista": p_proyectista,
            "expediente": p_expediente,
            "fecha": datetime.date.today().strftime("%d/%m/%Y")
        }

        calc_params = {
            "pot": val_pot_q,
            "long": long_q,
            "mat": mat_q,
            "aisl": ais_q,
            "metodo": metodo_q_key,
            "red": tipo_red_q,
            "cdt_lim": cdt_lim_q,
            "icc_orig": icc_orig_q,
            "cos_phi": cos_q
        }

        calc_results = {
            "ib": ib_q,
            "s_cal": s_cal_q,
            "s_cdt": s_cdt_q,
            "s_opt": s_opt_q,
            "iz_opt": iz_opt_val,
            "dv_real_v": dv_real_v_q,
            "dv_real_pct": dv_real_pct_q,
            "z_tot": z_tot_q,
            "icc_fin": icc_fin_q,
            "prot": prot_q,
            "salta_proteccion": salta_proteccion
        }

        try:
            pdf_bytes_cr = pdf_calculo_rapido.generar_pdf_calculo_rapido(proyecto_info, calc_params, calc_results)
            from modulos import visor_pdf
            visor_pdf.mostrar_visor_pdf(
                pdf_bytes=pdf_bytes_cr,
                nombre_archivo=f"Reporte_Calculo_Rapido_{p_expediente}.pdf",
                label_boton="📥 Descargar Reporte PDF Oficial Cálculo Rápido"
            )
        except Exception as err:
            st.error(f"⚠️ Ocurrió un error al generar el archivo PDF: {err}")
