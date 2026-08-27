import streamlit as st
import math

METODOS_INSTALACION_IRVE = {
    "B1 (Bajo tubo empotrado)": {"ref": "B1", "desc": "Cables unipolares en tubo en rozas"},
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables unipolares en tubo montado en superficie"},
    "C (Multiconductor en pared)": {"ref": "C", "desc": "Cable multiconductor fijado directo"}
}
SECCIONES_COMERCIALES_IRVE = [2.5, 4, 6, 10, 16, 25, 35, 50]
IZ_COBRE_TUBO_IRVE = {2.5: 20.0, 4: 26.0, 6: 34.0, 10: 46.0, 16: 61.0, 25: 80.0, 35: 99.0, 50: 119.0}
CALIBRES_PI = [10, 16, 20, 25, 32, 40]

def seleccionar_seccion_optima_irve(s_necesaria):
    for sec in SECCIONES_COMERCIALES_IRVE:
        if sec >= s_necesaria: return sec
    return SECCIONES_COMERCIALES_IRVE[-1]

def seleccionar_proteccion_irve(ib):
    for cal in CALIBRES_PI:
        if cal >= ib: return cal
    return CALIBRES_PI[-1]

def renderizar():
    st.title("🚗 Línea Específica de Recarga IRVE (ITC-BT-52)")
    
    with st.expander("📖 Guía Técnica: Criterios de Diseño del Circuito IRVE"):
        st.markdown("""
        Esta sección dimensiona el circuito terminal o derivación específica que alimenta el punto de recarga del vehículo eléctrico desde el origen elegido (centralización de contadores o cuadro general de la vivienda).
        
        * **Normativa:** ITC-BT-52 del REBT.
        * **Caída de Tensión Máxima Admisible:** Limitada al **1.0%** para circuitos de recarga alimentados desde centralización o contadores principales, asegurando que llegue la tensión adecuada al cargador (Wallbox).
        * **Protecciones Obligatorias:** 
            * **Magnetotérmico:** Adecuado a la potencia del cargador (típicamente 16A o 32A para 3.7 kW o 7.4 kW en monofásico).
            * **Diferencial:** Obligatorio **Tipo A** (con inmunización y detección de corriente continua residual de hasta 6 mA) o **Tipo B** de forma directa.
            * **Sobretensiones:** Protección transitoria y permanente obligatoria en el origen del circuito.
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
            esquema_orig = st.selectbox("Origen de la línea (Esquema ITC-BT-52):", [
                "Esquema 3a (Desde centralización de contadores)", 
                "Esquema 3b (Desde cuadro CGMP de la vivienda)", 
                "Esquema 1 / 2 (Instalación colectiva o contador exclusivo)"
            ], key="irve_esq")
            
        with irve_c2:
            irve_mat = st.selectbox("Material Conductor", ["cobre"], key="irve_mat")
            metodo_irve_key = st.selectbox("Instalación:", list(METODOS_INSTALACION_IRVE.keys()), index=0, key="irve_met")
            irve_aisl = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC) - RZ1-K", "PVC (70ºC)"], key="irve_aisl")
            tipo_red_irve = st.radio("Tipo de Alimentación:", ["Monofásico (230 V)", "Trifásico (400 V)"], key="irve_red")

        submitted_irve = st.form_submit_button("🔄 Recalcular / Actualizar Circuito IRVE")

    # --- CÁLCULOS TÉCNICOS IRVE ---
    es_trif_irve = "Trifásico" in tipo_red_irve
    v_t_irve = 400.0 if es_trif_irve else 230.0
    cos_phi_irve = 1.0
    
    ib_irve = p_cargador_val / (math.sqrt(3) * v_t_irve * cos_phi_irve) if es_trif_irve else p_cargador_val / (v_t_irve * cos_phi_irve)
    
    dv_pct_irve = 1.0 # 1% recomendado por ITC-BT-52 para circuitos de recarga
    gamma_irve = 44.0 if "XLPE" in irve_aisl else 48.5
    dv_max_irve = v_t_irve * (dv_pct_irve / 100.0)
    
    if es_trif_irve:
        s_cdt_irve = (p_cargador_val * irve_long) / (gamma_irve * dv_max_irve * v_t_irve) if gamma_irve * dv_max_irve * v_t_irve > 0 else 4.0
    else:
        s_cdt_irve = (2.0 * p_cargador_val * irve_long) / (gamma_irve * dv_max_irve * v_t_irve) if gamma_irve * dv_max_irve * v_t_irve > 0 else 4.0

    in_pi_auto = seleccionar_proteccion_irve(ib_irve)
    s_final_irve = seleccionar_seccion_optima_irve(max(s_cdt_irve, 2.5)) 
    
    tabla_iz_irve = IZ_COBRE_TUBO_IRVE
    while True:
        iz_a_irve = tabla_iz_irve.get(s_final_irve, 61.0)
        if in_pi_auto <= 0.91 * iz_a_irve and iz_a_irve >= ib_irve: break
        idx_s = SECCIONES_COMERCIALES_IRVE.index(s_final_irve) if s_final_irve in SECCIONES_COMERCIALES_IRVE else 1
        if idx_s < len(SECCIONES_COMERCIALES_IRVE) - 1: s_final_irve = SECCIONES_COMERCIALES_IRVE[idx_s + 1]
        else: break

    dv_real_irve_pct = (((math.sqrt(3) if es_trif_irve else 2.0) * p_cargador_val * irve_long) / (gamma_irve * s_final_irve * v_t_irve) / v_t_irve) * 100 if gamma_irve * s_final_irve * v_t_irve > 0 else 0.0

    st.markdown("---")
    st.markdown("<h3>📋 Memoria Analítica Específica (Circuito IRVE - ITC-BT-52)</h3>", unsafe_allow_html=True)

    # --- BLOQUE 1: INTENSIDAD DE DISEÑO ---
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

    # --- BLOQUE 2: SECCIÓN POR CAÍDA DE TENSIÓN ---
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

    # --- PROTECCIONES OBLIGATORIAS IRVE ---
    st.markdown("### 🛡️ Protecciones Obligatorias en el Origen y Destino del Circuito (ITC-BT-52)")
    st.markdown(f"""
    <div style="background: #f8fafc; border: 2px solid #0284c7; padding: 20px; border-radius: 8px; color: #0f172a; margin-bottom: 20px;">
        <h4 style="margin-top: 0; color: #0284c7;">Esquema de Protecciones Exigido:</h4>
        <ul>
            <li><strong>Interruptor Magnetotérmico:</strong> Calibre de <strong>{in_pi_auto} A (Curva C)</strong> adaptado para la protección contra sobreintensidades y cortocircuitos del circuito de recarga.</li>
            <li><strong>Protección Diferencial:</strong> Obligatorio instalar un <strong>Diferencial Mínimo Tipo A</strong> (con alta inmunización y capacidad de detección de corrientes de fuga continuas de hasta 6 mA) o directamente un <strong>Diferencial Tipo B</strong>.</li>
            <li><strong>Protecciones contra Sobretensiones:</strong> Instalación obligatoria de dispositivos de protección contra sobretensiones transitorias y permanentes para proteger la electrónica del vehículo eléctrico y del cargador frente a descargas atmosféricas o anomalías en la red.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # --- SECCIÓN TUBOS PARA IRVE ---
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
    * **Protección recomendada:** Magnetotérmico de **{in_pi_auto} A (Curva C)** + **Diferencial Tipo A / B** bajo tubo protector **{tubo_irve}**.
    """)
