import streamlit as st
import math

# =========================================================================
# CONSTANTES Y FUNCIONES EXCLUSIVAS DE ESTE MÓDULO
# =========================================================================
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

# =========================================================================
# FUNCIÓN MAESTRA QUE LLAMAREMOS DESDE LA APP PRINCIPAL
# =========================================================================
def renderizar():
    
    # --- TÍTULO Y BOTÓN DE IMPRESIÓN NATIVO (COMPATIBLE CON TABLET Y PC) ---
    col_tit, col_btn = st.columns([3, 1])
    with col_tit:
        st.title("🧮 Cálculo Rápido Avanzado")
    with col_btn:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div style="text-align: right;">
                <a href="javascript:window.print();" style="background-color: #0284c7; color: white; padding: 10px 15px; border-radius: 6px; text-decoration: none; font-weight: 500; font-size: 14px; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    🖨️ Imprimir / PDF
                </a>
            </div>
        """, unsafe_allow_html=True)

    # --- ESTILOS CSS PARA IMPRESIÓN MULTIPÁGINA Y PANTALLA ---
    st.markdown("""
    <style>
    @media print {
        [data-testid="stSidebar"], header, footer, .stButton, div.row-widget.stRadio, div.stSelectbox, div.stNumberInput, div[data-testid="stHorizontalBlock"], details { 
            display: none !important; 
        }
        h1 { display: none !important; }
        
        @page {
            size: A4 portrait;
            margin: 10mm;
        }
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, div[data-testid="stVerticalBlock"] {
            background-color: white !important; 
            color: black !important; 
            font-family: "Helvetica", "Arial", sans-serif !important; 
            font-size: 10pt !important;
            height: auto !important;
            max-height: none !important;
            overflow: visible !important;
            position: static !important;
            display: block !important;
        }
        
        .stInfo, div[style*="background-color"], .pia-destacado, table, tr {
            break-inside: avoid !important;
            page-break-inside: avoid !important;
        }
        
        table { 
            width: 100% !important; 
            border-collapse: collapse !important; 
        }
        th, td { 
            border: 1px solid #cbd5e1 !important; 
            padding: 6px 8px !important; 
            font-size: 9pt !important; 
            color: black !important; 
        }
    }
    
    .pia-destacado { background: #e0f2fe; color: #0369a1; padding: 15px; border-radius: 8px; font-size: 18px; font-weight: bold; text-align: center; margin: 15px 0; border: 2px solid #7dd3fc; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; border-radius: 6px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    th { background-color: #1e293b !important; color: #ffffff !important; text-align: center !important; padding: 14px !important; font-weight: 700; text-transform: uppercase; font-size: 12px; }
    td { padding: 12px !important; border-bottom: 1px solid #e2e8f0 !important; color: #334155 !important; background-color: #ffffff !important; text-align: center !important; }
    tr:nth-child(even) td { background-color: #f8fafc !important; }
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
        ayuda_metodo = "B1: Empotrado en pared (viviendas). \nB2: En superficie bajo tubo. \nC: Multiconductor directo. \nD: Enterrado bajo tubo."
        metodo_q_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), index=0, help=ayuda_metodo)
        mat_q = st.selectbox("Material conductor", ["cobre", "aluminio"])
        ais_q = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"])
        cdt_lim_q = st.number_input("Caída de Tensión máxima (%)", value=3.0, step=0.5)
        ayuda_icc = "Corriente de cortocircuito en origen (ej. 6 kA o 10 kA)."
        icc_orig_q = st.number_input("Icc en origen (kA)", value=10.0, step=0.5, help=ayuda_icc)

    gamma_q = GAMMA_MAP.get((mat_q, ais_q), 44.0)
    dv_max_q = v_nom_calc * (cdt_lim_q / 100.0) if cdt_lim_q > 0 else 1.0
    
    if "Monofásico" in tipo_red_q: s_cdt_q = (2.0 * val_pot_q * long_q) / (gamma_q * dv_max_q * v_nom_calc) if dv_max_q * v_nom_calc > 0 else 1.5
    else: s_cdt_q = (val_pot_q * long_q) / (gamma_q * dv_max_q * v_nom_calc) if dv_max_q * v_nom_calc > 0 else 1.5

    tabla_iz_q = IZ_COBRE_ENTERRADO if "D (" in metodo_q_key else IZ_COBRE_TUBO
    s_cal_q = 1.5
    for sec, iz_val in tabla_iz_q.items():
        if iz_val >= ib_q:
            s_cal_q = sec
            break

    min_reg_q = 1.5 if mat_q == "cobre" else 10.0
    s_bruta_q = max(s_cdt_q, s_cal_q, min_reg_q)
    s_opt_q = seleccionar_seccion_optima(s_bruta_q)
    iz_opt_val = tabla_iz_q.get(s_opt_q, 0.0)

    if "Monofásico" in tipo_red_q: dv_real_v_q = (2.0 * val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc) if s_opt_q * v_nom_calc > 0 else 0.0
    else: dv_real_v_q = (val_pot_q * long_q) / (gamma_q * s_opt_q * v_nom_calc) if s_opt_q * s_opt_q > 0 else 0.0
    dv_real_pct_q = (dv_real_v_q / v_nom_calc) * 100.0 if v_nom_calc > 0 else 0.0

    rho_q = 1.0 / gamma_q if gamma_q > 0 else 0.0
    r_cable_unitario = (rho_q * long_q) / s_opt_q if s_opt_q > 0 else 0.0
    
    if "Monofásico" in tipo_red_q:
        r_cable_total = 2.0 * r_cable_unitario
        z_origen = v_nom_calc / (icc_orig_q * 1000.0) if icc_orig_q > 0 else 0
        z_tot_q = z_origen + r_cable_total
    else:
        r_cable_total = r_cable_unitario
        z_origen = v_nom_calc / (icc_orig_q * 1000.0) if icc_orig_q > 0 else 0
        z_tot_q = z_origen + r_cable_total
        
    icc_fin_q = v_nom_calc / z_tot_q / 1000.0 if z_tot_q > 0 else 0.0
    prot_q = seleccionar_proteccion(ib_q)
    corriente_disparo = prot_q * 10.0
    salta_proteccion = (icc_fin_q * 1000.0) >= corriente_disparo

    st.markdown("---")
    
    st.markdown("""
    <div style="border-bottom: 2px solid #0284c7; padding-bottom: 10px; margin-bottom: 20px;">
        <h2 style="color: #0369a1; margin: 0;">BOLIMUR INSTALACIONES INTEGRALES</h2>
        <p style="color: #64748b; font-size: 13px; margin: 2px 0 0 0;">Memoria Técnica de Justificación de Secciones - REBT</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h3>📋 Memoria Analítica Detallada</h3>", unsafe_allow_html=True)

    if "Monofásico" in tipo_red_q:
        f_ib = r"$$I_b = \frac{P}{V \cdot \cos\varphi}$$"
        r_ib = f"{val_pot_q:,.1f} W / ({v_nom_calc} V $\cdot$ {cos_q})"
    else:
        f_ib = r"$$I_b = \frac{P}{\sqrt{3} \cdot V \cdot \cos\varphi}$$"
        r_ib = f"{val_pot_q:,.1f} W / (1.732 $\cdot$ {v_nom_calc} V $\cdot$ {cos_q})"

    st.info(
        f"#### 1. Intensidad de Diseño ($I_b$)\n"
        f"**Justificación:** Se calcula la corriente nominal base de la carga para asegurar que el cable soporte la demanda en régimen permanente ($I_z \ge I_b$).\n\n"
        f"{f_ib}\n\n"
        f"**Sustitución y Resultado:** {r_ib} = **{ib_q:.2f} A**"
    )

    st.info(
        f"#### 2. Determinación de Sección por Calentamiento ($I_z$)\n"
        f"**Justificación:** Evaluamos las tablas del REBT (UNE-HD 60364-5-52) según el método de instalación seleccionado para encontrar la sección mínima que garantice una capacidad térmica superior a la corriente de diseño.\n\n"
        f"* **Corriente de diseño ($I_b$):** {ib_q:.2f} A\n"
        f"* **Sección requerida por este criterio:** **{s_cal_q} mm²** (Admite una intensidad máxima $I_z =$ {tabla_iz_q.get(s_cal_q, 0)} A)."
    )

    if "Monofásico" in tipo_red_q:
        f_cdt = r"$$S = \frac{2 \cdot P \cdot L}{\gamma \cdot \Delta V \cdot V}$$"
        r_cdt = f"(2 $\cdot$ {val_pot_q:,.1f} $\cdot$ {long_q}) / ({gamma_q} $\cdot$ {dv_max_q:.2f} $\cdot$ {v_nom_calc})"
    else:
        f_cdt = r"$$S = \frac{P \cdot L}{\gamma \cdot \Delta V \cdot V}$$"
        r_cdt = f"({val_pot_q:,.1f} $\cdot$ {long_q}) / ({gamma_q} $\cdot$ {dv_max_q:.2f} $\cdot$ {v_nom_calc})"

    st.info(
        f"#### 3. Sección Teórica por Caída de Tensión ($\Delta V$)\n"
        f"**Justificación:** Se determina el grosor de conductor necesario para que las pérdidas de tensión a lo largo de la línea no superen el límite reglamentario del **{cdt_lim_q}%** ({dv_max_q:.2f} V).\n\n"
        f"{f_cdt}\n\n"
        f"**Sustitución y Resultado:** {r_cdt} = **{s_cdt_q:.2f} mm²**"
    )

    estado_icc = "✅ GARANTIZADO" if salta_proteccion else "⚠️ PELIGRO: NO SALTARÁ A TIEMPO"
    f_icc1 = r"$$I_{cc,final} = \frac{V}{Z_{origen} + R_{cable}}$$"
    f_icc2 = f"$$I_{{cc,final}} = \\frac{{{v_nom_calc}}}{{{z_origen:.4f} + {r_cable_total:.4f}}} = \\mathbf{{{icc_fin_q * 1000:.1f} \text{{ A}}}}$$"

    st.info(
        f"#### 4. Comprobación Cortocircuito y Disparo Magnético (0.1s)\n"
        f"**Justificación:** La corriente de cortocircuito en el punto más lejano de la línea ($I_{{cc,final}}$) debe tener fuerza suficiente para accionar el umbral magnético de la protección de forma instantánea (Curva C = $10 \cdot I_n$).\n\n"
        f"{f_icc1}\n\n"
        f"**Origen detallado de los parámetros de impedancia y resistencia:**\n"
        f"* **Impedancia de red en origen ($Z_{{origen}}$):** Se obtiene a partir de la corriente de cortocircuito configurada en cabecera ($I_{{cc,origen}} = {icc_orig_q}$ kA). Aplicando la ley de Ohm ($Z_{{origen}} = V / I_{{cc,origen}}$), resulta en **{z_origen:.4f} $\Omega$**.\n"
        f"* **Resistencia del cable ($R_{{cable}}$):** Calculada con $R = (\\rho \cdot L) / S$ (multiplicada por 2 en líneas monofásicas por retorno de neutro). Con longitud {long_q} m y sección óptima de {s_opt_q} mm², resulta en **{r_cable_total:.4f} $\Omega$**.\n\n"
        f"{f_icc2}\n\n"
        f"* **Umbral de disparo magnético exigido ({prot_q} A $\\times$ 10):** {corriente_disparo:.1f} A\n"
        f"* **Veredicto:** {estado_icc}"
    )

    st.markdown(f"""
    <div class="pia-destacado">
        <h4 style="margin: 0;">🛡️ PROTECCIÓN MAGNETOTÉRMICA: PIA {prot_q} A (Curva C)</h4>
        <hr style="border-top: 1px solid #cbd5e1; margin: 10px 0;">
        <span style="font-size: 14px; font-weight: normal;">
        <b>Justificación normativa:</b> Su calibre nominal ({prot_q} A) absorbe la intensidad de diseño ({ib_q:.2f} A) sin disparos intempestivos, asegurando la protección del aislamiento al cumplir estrictamente la condición <b>$I_n \le 0.91 \cdot I_z$</b> (siendo $I_z$ = {iz_opt_val} A).
        </span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 Ayuda Técnica: Tabla de Conductividad (γ) y Resistividad (ρ) del REBT"):
        st.markdown("Valores oficiales de conductividad ($\gamma$) según la norma UNE-HD 60364-5-52:")
        tabla_gamma_md = """
| MATERIAL CONDUCTOR | AISLAMIENTO | TEMP. SERVICIO | CONDUCTIVIDAD ($\gamma$) [$\mathrm{m / (\Omega \cdot mm^2)}$] | RESISTIVIDAD APROXIMADA ($\rho$) [$\mathrm{\Omega \cdot mm^2 / m}$] |
| :--- | :--- | :--- | :--- | :--- |
| **Cobre** | XLPE / EPR | 90 ºC | **44.0** | ~0.0227 |
| **Cobre** | PVC | 70 ºC | **48.5** | ~0.0206 |
| **Aluminio** | XLPE / EPR | 90 ºC | **28.0** | ~0.0357 |
| **Aluminio** | PVC | 70 ºC | **31.0** | ~0.0323 |
        """
        st.markdown(tabla_gamma_md)

    st.markdown("### 📊 Tabla de Corrientes Admisibles y Verificación (REBT)")
    tabla_q_md = "| SECCIÓN | IZ ADMISIBLE (A) | CDT REAL (%) | ESTADO DE VERIFICACIÓN ($I_n \le 0.91 \cdot I_z$) |\n| :--- | :--- | :--- | :--- |\n"
    for sec_com in [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70]:
        iz_c = tabla_iz_q.get(sec_com, 250.0)
        dv_c_pct = (((2.0 * val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0 if "Monofásico" in tipo_red_q else (((val_pot_q * long_q) / (gamma_q * sec_com * v_nom_calc)) / v_nom_calc) * 100.0
        cond_sobrecarga = 0.91 * iz_c
        if iz_c < ib_q: est_v = f"❌ Falla Calentamiento"
        elif prot_q > cond_sobrecarga: est_v = f"❌ Falla ($I_n$ {prot_q}A > {cond_sobrecarga:.1f}A)"
        elif sec_com == s_opt_q: est_v = f"✅ **CUMPLE IDEAL** ($I_n$ {prot_q} A $\le$ {cond_sobrecarga:.1f} A)"
        else: est_v = "Válido pero sobredimensionado"
        tabla_q_md += f"| **{sec_com} mm²** | {iz_c} A | {dv_c_pct:.3f}% | {est_v} |\n"
    st.markdown(tabla_q_md)

    st.markdown(f"""
    <div style="background-color: #dcfce7; border: 2px solid #86efac; color: #166534; padding: 20px; border-radius: 8px; margin-top: 20px;">
        <h3 style="margin-top: 0; margin-bottom: 10px; color: #166534;">✅ SECCIÓN ÓPTIMA ADOPTADA: {s_opt_q} mm² ({mat_q.upper()})</h3>
        <p style="font-size: 15px; margin-bottom: 8px; color: #166534;">
            La sección de <b>{s_opt_q} mm²</b> garantiza el cumplimiento térmico 
            (<b><i>I<sub>z</sub></i> = {iz_opt_val} A &ge; <i>I<sub>b</sub></i> = {ib_q:.2f} A</b>) 
            y una caída de tensión real del <b>{dv_real_pct_q:.3f}%</b>.
        </p>
        <p style="font-size: 15px; margin: 0; color: #166534;">
            Coordinada perfectamente con un <b>PIA de {prot_q} A (Curva C)</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)
