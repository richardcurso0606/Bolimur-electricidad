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

PRESETS_CIRCUITOS_REBT = {
    "Personalizado (Manual)": {
        "potencia": 0.0,
        "longitud": 0.0,
        "cos_phi": 0.85,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": None
    },
    "C1 - Alumbrado General (10A - 1.5 mm²)": {
        "potencia": 2300.0,
        "longitud": 18.0,
        "cos_phi": 0.90,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "💡 **ITC-BT-25:** Máximo 30 puntos de luz por circuito. PIA 10A, sección mínima 1.5 mm² Cu, tubo M20."
    },
    "C2 - Tomas de Uso General (16A - 2.5 mm²)": {
        "potencia": 3450.0,
        "longitud": 20.0,
        "cos_phi": 0.85,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "🔌 **ITC-BT-25:** Máximo 20 tomas por circuito. PIA 16A, sección mínima 2.5 mm² Cu, tubo M20."
    },
    "C3 - Cocina y Horno (25A - 6.0 mm²)": {
        "potencia": 5400.0,
        "longitud": 14.0,
        "cos_phi": 0.90,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "🍳 **ITC-BT-25:** Toma o caja de bornas 25A. Sección mínima 6.0 mm² Cu, tubo M25, PIA 25A."
    },
    "C4 - Lavadora / Lavavajillas / Termo (20A - 4.0 mm²)": {
        "potencia": 3450.0,
        "longitud": 15.0,
        "cos_phi": 0.85,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "🧺 **ITC-BT-25:** Puede subdividirse en C4.1 (Lavadora 16A), C4.2 (Lavavajillas 16A) y C4.3 (Termo 16A)."
    },
    "C8.1 - Calefacción Eléctrica Línea 1 (25A - 6.0 mm²)": {
        "potencia": 5000.0,
        "longitud": 18.0,
        "cos_phi": 1.0,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "🔥 **ITC-BT-25 (Calefacción > 5.750 W):** La potencia máxima admisible por circuito C8 es 5.750 W. Si la instalación supera dicha carga, es **obligatorio desdoblar** en circuitos C8.1, C8.2... con PIA individual de 25A y tubo independiente M25."
    },
    "C8.2 - Calefacción Eléctrica Línea 2 (25A - 6.0 mm²)": {
        "potencia": 4500.0,
        "longitud": 20.0,
        "cos_phi": 1.0,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "🔥 **ITC-BT-25:** Segunda línea desdoblada de calefacción. Implica paso a electrificación elevada (≥9.200 W) e IGA 40A."
    },
    "C9 - Climatización / Bomba Calor Conductos Inverter (25A - 6.0 mm²)": {
        "potencia": 5750.0,
        "longitud": 16.0,
        "cos_phi": 0.85,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "❄️ **ITC-BT-25 y Guía Técnica (Climatización Inverter):** Las unidades Inverter modulan mediante variadores de frecuencia (PWM) produciendo fugas de corriente continua y componentes de alta frecuencia. Se prescribe obligatoriamente **Interruptor Diferencial Clase A Superinmunizado (30mA)** para evitar disparos intempestivos o bloqueo del diferencial."
    },
    "C9 - Split Climatización Individual (16A - 2.5 mm²)": {
        "potencia": 2500.0,
        "longitud": 15.0,
        "cos_phi": 0.85,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "❄️ **ITC-BT-25:** Split mural independiente. PIA 16A, sección 2.5 mm² Cu, tubo M20."
    },
    "C11 - Domótica Inalámbrica / WiFi / Zigbee / Shelly (10A - 1.5 mm²)": {
        "potencia": 1500.0,
        "longitud": 20.0,
        "cos_phi": 0.90,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "🧠 **ITC-BT-25 e ITC-BT-51 (Domótica Inalámbrica):** Se requiere instalar **cajas de mecanismo profundas (60 mm)** en lugar de las estándar (40 mm) para alojar micromódulos y pastillas de relé. Es **obligatorio llevar hilo neutro azul** a cada caja de interruptor/pulsador."
    },
    "C11 - Domótica Cableada por Bus KNX (10A - 1.5 mm²)": {
        "potencia": 1500.0,
        "longitud": 25.0,
        "cos_phi": 0.90,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "🧠 **ITC-BT-51 (Domótica KNX):** El cable de bus verde KNX (SELV) debe discurrir por **tubo independiente M20** respecto a los cables de fuerza 230V (a menos que tenga tensión de aislamiento 4 kV). Requiere fuente de alimentación DIN 30V DC con bobina desacoplo en cuadro."
    },
    "C13 - Recarga Vehículo Eléctrico IRVE (32A - 7.4 kW / ITC-BT-52)": {
        "potencia": 7360.0,
        "longitud": 25.0,
        "cos_phi": 1.0,
        "sistema": "Monofásico (230V)",
        "metodo": "B1 (Bajo tubo empotrado)",
        "cdt_lim": 3.0,
        "nota": "🚗 **ITC-BT-52:** Circuito dedicado con interruptor diferencial exclusivo Tipo A (o Tipo B si el cargador carece de detector RDC-DD 6mA DC). Tubo M32 y sección mínima 6 mm² Cu."
    }
}

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

    try:
        from modulos import selector_cliente_proyecto
        datos_cr = {
            "val_pot_q": st.session_state.get("cr_pot", 0.0),
            "long_q": st.session_state.get("cr_long", 0.0)
        }
        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">👤 Asignar a Cliente o Guardar Cálculo Independiente</h4></div>', unsafe_allow_html=True)
        selector_cliente_proyecto.renderizar_barra_cliente_proyecto("Cálculo Rápido", datos_cr, "Cálculo Rápido de Sección y Protecciones")
    except Exception:
        pass

    class _NullContext:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    col_nav_info, col_nav_mode = st.columns([2.8, 1.2])
    with col_nav_info:
        st.caption("🚀 **Navegación Rápida:** Cambia de sección al instante sin desplazarte por la pantalla.")
    with col_nav_mode:
        modo_vista_cr = st.radio(
            "Modo de Navegación:",
            ["📑 Pestañas Rápidas (Sin scroll)", "📜 Vista Continua (Todo en 1)"],
            horizontal=True,
            label_visibility="collapsed",
            key="modo_vista_cr"
        )

    if modo_vista_cr.startswith("📑"):
        tab_cr1, tab_cr2, tab_cr3 = st.tabs([
            "⚡ 1. Parámetros del Circuito",
            "📋 2. Memoria & Resultados REBT",
            "🖨️ 3. Reporte PDF Oficial"
        ])
    else:
        tab_cr1 = _NullContext()
        tab_cr2 = _NullContext()
        tab_cr3 = _NullContext()

    with tab_cr1:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">⚡ SECCIÓN 1: Parámetros del Circuito y Método de Instalación (ITC-BT-19)</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_pres1, col_pres2 = st.columns([2.2, 1.3])
            with col_pres1:
                lista_presets = list(PRESETS_CIRCUITOS_REBT.keys())
                preset_previo = st.session_state.get("cr_preset_sel", lista_presets[0])
                idx_pres_def = lista_presets.index(preset_previo) if preset_previo in lista_presets else 0
            
                preset_elegido = st.selectbox(
                    "🎯 Plantilla de Circuito Típico REBT (Autocompletar):",
                    lista_presets,
                    index=idx_pres_def,
                    key="cr_preset_selector"
                )
            with col_pres2:
                st.caption("Carga automática de potencia, longitud de cálculo, cos φ y prescripciones según ITC-BT-25 / 51 / 52.")

            if "cr_ultimo_preset" not in st.session_state:
                st.session_state["cr_ultimo_preset"] = lista_presets[0]

            if preset_elegido != st.session_state["cr_ultimo_preset"]:
                st.session_state["cr_ultimo_preset"] = preset_elegido
                st.session_state["cr_preset_sel"] = preset_elegido
                if preset_elegido in PRESETS_CIRCUITOS_REBT and preset_elegido != "Personalizado (Manual)":
                    cfg_p = PRESETS_CIRCUITOS_REBT[preset_elegido]
                    st.session_state["cr_pot_val"] = float(cfg_p["potencia"])
                    st.session_state["cr_long_val"] = float(cfg_p["longitud"])
                    st.session_state["cr_cos_val"] = float(cfg_p["cos_phi"])
                    st.session_state["cr_cdt_lim_val"] = float(cfg_p["cdt_lim"])
                    st.session_state["cr_modo_carga"] = "Por Potencia (W)"
                    if "sistema" in cfg_p:
                        st.session_state["cr_red_val"] = cfg_p["sistema"]
                    st.rerun()

            info_preset = PRESETS_CIRCUITOS_REBT.get(preset_elegido, {}).get("nota")
            if info_preset:
                st.info(info_preset)

            rc1, rc2 = st.columns(2)
            with rc1:
                modo_def = st.session_state.get("cr_modo_carga", "Por Potencia (W)")
                modo_carga = st.radio("Entrada:", ["Por Potencia (W)", "Por Intensidad Directa (A)"], index=0 if modo_def == "Por Potencia (W)" else 1, horizontal=True)
            
                red_def = st.session_state.get("cr_red_val", "Monofásico (230V)")
                idx_red = 0 if "Monofásico" in red_def else 1
                tipo_red_q = st.selectbox("Sistema eléctrico", ["Monofásico (230V)", "Trifásico (400V)"], index=idx_red)
            
                pot_def = float(st.session_state.get("cr_pot_val", 0.0))
                long_def = float(st.session_state.get("cr_long_val", 0.0))
                cos_def = float(st.session_state.get("cr_cos_val", 0.85))
                cdt_lim_def = float(st.session_state.get("cr_cdt_lim_val", 3.0))

                if modo_carga == "Por Potencia (W)":
                    val_pot_q = st.number_input("Potencia (W)", value=pot_def, step=100.0)
                    cos_q = st.slider("Coseno phi (cos φ)", 0.7, 1.0, cos_def)
                    v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
                    if "Monofásico" in tipo_red_q: ib_q = val_pot_q / (v_nom_calc * cos_q) if v_nom_calc * cos_q > 0 else 0.0
                    else: ib_q = val_pot_q / (math.sqrt(3) * v_nom_calc * cos_q) if math.sqrt(3) * v_nom_calc * cos_q > 0 else 0.0
                else:
                    ib_q = st.number_input("Intensidad Ib (A)", value=0.0, step=1.0)
                    cos_q = st.slider("Coseno phi (cos φ)", 0.7, 1.0, cos_def)
                    v_nom_calc = 230.0 if "Monofásico" in tipo_red_q else 400.0
                    if "Monofásico" in tipo_red_q: val_pot_q = ib_q * v_nom_calc * cos_q
                    else: val_pot_q = ib_q * math.sqrt(3) * v_nom_calc * cos_q

                long_q = st.number_input("Longitud del circuito (m)", value=long_def, step=5.0)

            with rc2:
                ayuda_metodo = "B1: Empotrado en pared. \nB2: En superficie bajo tubo. \nC: Multiconductor directo. \nD: Enterrado bajo tubo."
                metodo_q_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION.keys()), index=0, help=ayuda_metodo)
                mat_q = st.selectbox("Material conductor", ["cobre", "aluminio"])
                ais_q = st.selectbox("Aislamiento", ["XLPE / EPR (90ºC)", "PVC (70ºC)"])
                cdt_lim_q = st.number_input("Caída de Tensión máxima (%)", value=cdt_lim_def, step=0.5)
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

    with tab_cr2:
        st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">📋 SECCIÓN 2: Memoria Analítica y Resultados Técnicos REBT</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            if "Monofásico" in tipo_red_q:
                f_ib = r"$$I_b = \frac{P}{V \cdot \cos\varphi}$$"
                r_ib = f"{val_pot_q:,.1f} W / ({v_nom_calc} V $\cdot$ {cos_q})"
            else:
                f_ib = r"$$I_b = \frac{P}{\sqrt{3} \cdot V \cdot \cos\varphi}$$"
                r_ib = f"{val_pot_q:,.1f} W / (1.732 $\cdot$ {v_nom_calc} V $\cdot$ {cos_q})"

            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.info(
                    f"#### 1. Intensidad de Diseño ($I_b$)\n"
                    f"**Justificación:** Se calcula la corriente nominal base de la carga ($I_z \\ge I_b$).\n\n"
                    f"{f_ib}\n\n"
                    f"**Sustitución y Resultado:** {r_ib} = **{ib_q:.2f} A**"
                )

                st.info(
                    f"#### 2. Determinación de Sección por Calentamiento ($I_z$)\n"
                    f"* **Corriente de diseño ($I_b$):** {ib_q:.2f} A\n"
                    f"* **Sección requerida:** **{s_cal_q} mm²** (Admite $I_z =$ {tabla_iz_q.get(s_cal_q, 0)} A)."
                )

            with col_res2:
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
            Garantiza una caída de tensión real del **{dv_real_pct_q:.3f}%**. Coordinada con **PIA {prot_q} A (Curva C)**. Tubo recomendado: **M{tubo_diam_q}**.
            """)

            col_t_cr1, col_t_cr2 = st.columns([1.5, 1])
            with col_t_cr1:
                if st.button("📥 Traspasar este circuito a la Memoria Técnica (MTD)", type="primary", use_container_width=True, key="btn_transfer_cr_mtd"):
                    if "mtd_circuitos" not in st.session_state or not isinstance(st.session_state["mtd_circuitos"], list):
                        st.session_state["mtd_circuitos"] = []
                
                    if preset_elegido != "Personalizado (Manual)":
                        c_nom_prop = preset_elegido.split("(")[0].strip()
                    else:
                        c_nom_prop = f"Circuito Alimentador ({val_pot_q/1000.0:.2f} kW - {long_q}m)"
                
                    sec_format = f"{'4' if es_trifasico_q else '2'}x{s_opt_q:.0f}+TT{s_opt_q:.0f}"
                    st.session_state["mtd_circuitos"].append({
                        "nombre": c_nom_prop,
                        "potencia": int(val_pot_q),
                        "pia": int(prot_q),
                        "seccion": sec_format,
                        "tubo": f"M{tubo_diam_q}",
                        "longitud": int(long_q),
                        "cdt": float(f"{dv_real_pct_q:.2f}"),
                        "norma": "ITC-BT-52" if "IRVE" in preset_elegido else "ITC-BT-25"
                    })
                    st.session_state.menu_activo = "🏛️ Memoria Técnica (MTD 30)"
                    st.success("✅ ¡Circuito traspasado a la Memoria Técnica de Diseño! Redirigiendo...")
                    st.rerun()
            with col_t_cr2:
                st.caption("Inserta este circuito calculado en el cuadro de circuitos de la Memoria Técnica Oficial.")

    with tab_cr3:
        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">🖨️ SECCIÓN 3: Generación de Reporte Técnico Oficial en PDF</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
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
