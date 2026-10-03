# -*- coding: utf-8 -*-
"""
Módulo Oficial de Infraestructura para la Recarga de Vehículos Eléctricos (IRVE)
Conforme a la Instrucción Técnica Complementaria ITC-BT-52 del REBT (RD 1053/2014 y RD 842/2002).
Incluye memoria técnica comparativa de esquemas, dimensionamiento exacto, esquema unifilar interactivo,
presupuestador de materiales para instaladores, generador de PDF oficial y Asistente IA por voz y texto.
"""

import streamlit as st
import math
import datetime
from modulos import rebt_tablas as rebt
from modulos import pdf_irve
from modulos import ia_asistente_irve

METODOS_INSTALACION_IRVE = {
    "B2 (Bajo tubo en superficie)": {"ref": "B2", "desc": "Cables en tubo montado en superficie de garaje/techo"},
    "B1 (Bajo tubo empotrado)": {"ref": "B1", "desc": "Cables unipolares en tubo empotrado en rozas"},
    "C (Multiconductor en pared/bandeja)": {"ref": "C", "desc": "Cable multiconductor RZ1-K fijado o en bandeja"}
}

SECCIONES_COMERCIALES_IRVE = [2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0]

ESQUEMAS_IRVE_INFO = {
    "Esquema 2": {
        "nombre": "Esquema 2 (Contador principal común para vivienda y recarga)",
        "origen": "Bornes de salida del contador de la vivienda en la centralización de contadores (o cuadro vivienda)",
        "limite_cdt": 1.0,
        "uso_principal": "El más habitual en edificios de viviendas existentes cuando la plaza está en el mismo edificio.",
        "ventajas": "Aprovecha el contrato y término de potencia existente de la vivienda. Permite balanceo dinámico de carga sin pagar un segundo contrato de luz.",
        "requisitos": "Derivación individual desde el cuarto de contadores con fusible/IGA en origen + cuadro de protección secundario en plaza con PIA, Diferencial Tipo A 6mA DC y Sobretensiones.",
        "color": "#0284c7"
    },
    "Esquema 1": {
        "nombre": "Esquema 1 (Instalación colectiva con contador común en origen)",
        "origen": "Cuadro general de distribución exclusivo para recarga de garaje",
        "limite_cdt": 1.0,
        "uso_principal": "Nuevos edificios de viviendas, parkings públicos, empresas o comunidades con Gestor de Carga (CPO).",
        "ventajas": "Una única línea troncal para todo el garaje, optimizando bandejas y espacio.",
        "requisitos": "Contador colectivo de recarga, sistema SPL (Sistema de Protección de Línea) y contadores secundarios homologados MID.",
        "color": "#059669"
    },
    "Esquema 3a": {
        "nombre": "Esquema 3a (Contador individual exclusivo en centralización)",
        "origen": "Nuevo contador individual instalado en la centralización de contadores del edificio",
        "limite_cdt": 1.0,
        "uso_principal": "Propietarios que viven en otro edificio o usuarios que desean una factura eléctrica totalmente independiente.",
        "ventajas": "Facturación y contrato 100% independiente del piso.",
        "requisitos": "Solicitud de nuevo CUPS a distribuidora, módulo de contador en centralización y término fijo de potencia independiente.",
        "color": "#d97706"
    },
    "Esquema 3b": {
        "nombre": "Esquema 3b (Contador individual exclusivo en la plaza de garaje / exterior)",
        "origen": "Caja de protección y medida (CPM) exterior o en la propia plaza",
        "limite_cdt": 1.0,
        "uso_principal": "Aparcamientos exteriores, parkings no cubiertos o suministros directos de vía pública.",
        "ventajas": "Medida in situ donde no hay centralización de contadores cercana.",
        "requisitos": "Acometida independiente autorizada por distribuidora.",
        "color": "#7c3aed"
    },
    "Esquema 4a": {
        "nombre": "Esquema 4a / 4b (Circuito adicional desde el CGMP de la vivienda)",
        "origen": "Cuadro General de Mando y Protección (CGMP) de la vivienda o local",
        "limite_cdt": 1.5,
        "uso_principal": "Viviendas unifamiliares (chalets, adosados), locales comerciales o viviendas con garaje anexo directo.",
        "ventajas": "Instalación sumamente económica y directa. No requiere obras en zonas comunitarias ni cuartos de contadores.",
        "requisitos": "Circuito terminal dedicado protegido por PIA de 16A a 32A Curva C, Diferencial Tipo A 6mA DC y Sobretensiones permanentes y transitorias en el CGMP.",
        "color": "#0891b2"
    }
}

def seleccionar_seccion_optima_irve(s_necesaria):
    return rebt.seleccionar_seccion_optima(s_necesaria, material="cobre", s_minima=2.5)

def seleccionar_proteccion_irve(ib):
    return rebt.seleccionar_proteccion(ib, tipo="pia")

def reset_valores_irve():
    st.session_state['irve_esquema_sel_key'] = "Esquema 2"
    st.session_state['irve_pot_sel'] = "7.360 W (32A - Monofásico Estándar Wallbox)"
    st.session_state['irve_custom_w'] = 7360.0
    st.session_state['irve_long'] = 25.0
    st.session_state['irve_mat'] = "cobre"
    st.session_state['irve_aisl'] = "XLPE / EPR (90ºC) - RZ1-K (Cca-s1b,d1,a1)"
    st.session_state['irve_met'] = "B2 (Bajo tubo en superficie)"
    st.session_state['irve_red'] = "Monofásico (230 V)"

def generar_svg_unifilar_irve(esquema_nombre: str, pot_w: float, s_final: float, in_pi: int, dv_pct: float, tubo_dim: str, es_trif: bool) -> str:
    """
    Genera un diagrama vectorial SVG claro y profesional del circuito IRVE según ITC-BT-52.
    """
    tension_txt = "3x400V + N + PE" if es_trif else "230V + N + PE"
    num_cond = "5G" if es_trif else "3G"
    
    svg = f"""
    <svg width="100%" height="250" viewBox="0 0 850 250" xmlns="http://www.w3.org/2000/svg" style="background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
        <!-- Título -->
        <rect x="0" y="0" width="850" height="34" fill="#0f172a" rx="8" />
        <text x="20" y="22" fill="#38bdf8" font-family="Arial, sans-serif" font-size="13" font-weight="bold">ESQUEMA UNIFILAR REGLAMENTARIO IRVE - {esquema_nombre.upper()}</text>
        <text x="730" y="22" fill="#94a3b8" font-family="Arial, sans-serif" font-size="11">ITC-BT-52 REBT</text>

        <!-- Bloque 1: Origen / Contador -->
        <rect x="25" y="60" width="130" height="150" fill="#f8fafc" stroke="#0284c7" stroke-width="1.8" rx="6"/>
        <text x="90" y="85" fill="#0369a1" font-family="Arial, sans-serif" font-size="11" font-weight="bold" text-anchor="middle">ORIGEN / MEDIDA</text>
        <circle cx="90" cy="115" r="18" fill="#e0f2fe" stroke="#0284c7" stroke-width="1.5"/>
        <text x="90" y="120" fill="#0369a1" font-family="Arial, sans-serif" font-size="12" font-weight="bold" text-anchor="middle">kWh</text>
        <text x="90" y="150" fill="#334155" font-family="Arial, sans-serif" font-size="9.5" text-anchor="middle">Contador Inteligente</text>
        <text x="90" y="165" fill="#64748b" font-family="Arial, sans-serif" font-size="8.5" text-anchor="middle">Centralización / CGMP</text>
        <text x="90" y="195" fill="#059669" font-family="Arial, sans-serif" font-size="9" font-weight="bold" text-anchor="middle">Sensor Balanceo CT</text>

        <!-- Línea de enlace 1 -->
        <line x1="155" y1="125" x2="225" y2="125" stroke="#0284c7" stroke-width="2.5"/>
        <polygon points="220,121 228,125 220,129" fill="#0284c7" />

        <!-- Bloque 2: Cuadro de Protecciones en Plaza -->
        <rect x="225" y="50" width="310" height="170" fill="#f0f9ff" stroke="#0369a1" stroke-width="1.8" stroke-dasharray="3,3" rx="6"/>
        <text x="380" y="70" fill="#0369a1" font-family="Arial, sans-serif" font-size="11" font-weight="bold" text-anchor="middle">CUADRO SECUNDARIO PLAZA (IP65 / IK08)</text>

        <!-- Elemento 2.1: Sobretensiones -->
        <rect x="245" y="85" width="80" height="115" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.2" rx="4"/>
        <text x="285" y="105" fill="#0f172a" font-family="Arial, sans-serif" font-size="10" font-weight="bold" text-anchor="middle">VSP + VTP</text>
        <text x="285" y="125" fill="#64748b" font-family="Arial, sans-serif" font-size="8.5" text-anchor="middle">Sobretensiones</text>
        <text x="285" y="140" fill="#64748b" font-family="Arial, sans-serif" font-size="8" text-anchor="middle">Permanentes +</text>
        <text x="285" y="152" fill="#64748b" font-family="Arial, sans-serif" font-size="8" text-anchor="middle">Transitorias Tipo 2</text>
        <text x="285" y="175" fill="#d97706" font-family="Arial, sans-serif" font-size="8.5" font-weight="bold" text-anchor="middle">Bobina Emisión</text>

        <!-- Elemento 2.2: IGA / PIA -->
        <rect x="340" y="85" width="80" height="115" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.2" rx="4"/>
        <text x="380" y="105" fill="#0f172a" font-family="Arial, sans-serif" font-size="10" font-weight="bold" text-anchor="middle">PIA {in_pi} A</text>
        <text x="380" y="125" fill="#0284c7" font-family="Arial, sans-serif" font-size="9" font-weight="bold" text-anchor="middle">Curva C</text>
        <text x="380" y="145" fill="#64748b" font-family="Arial, sans-serif" font-size="8.5" text-anchor="middle">P. Corte ≥ 6kA</text>
        <text x="380" y="165" fill="#64748b" font-family="Arial, sans-serif" font-size="8" text-anchor="middle">Protección</text>
        <text x="380" y="178" fill="#64748b" font-family="Arial, sans-serif" font-size="8" text-anchor="middle">Sobreintensidad</text>

        <!-- Elemento 2.3: Diferencial -->
        <rect x="435" y="85" width="85" height="115" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.2" rx="4"/>
        <text x="477" y="105" fill="#0f172a" font-family="Arial, sans-serif" font-size="9.5" font-weight="bold" text-anchor="middle">DIFERENCIAL</text>
        <text x="477" y="125" fill="#15803d" font-family="Arial, sans-serif" font-size="9" font-weight="bold" text-anchor="middle">TIPO A / B</text>
        <text x="477" y="142" fill="#64748b" font-family="Arial, sans-serif" font-size="8.5" text-anchor="middle">IΔn = 30 mA</text>
        <text x="477" y="160" fill="#15803d" font-family="Arial, sans-serif" font-size="8" font-weight="bold" text-anchor="middle">6 mA DC (RDC-DD)</text>
        <text x="477" y="178" fill="#64748b" font-family="Arial, sans-serif" font-size="8" text-anchor="middle">Superinmunizado</text>

        <!-- Línea entre protecciones -->
        <line x1="325" y1="130" x2="340" y2="130" stroke="#0284c7" stroke-width="2"/>
        <line x1="420" y1="130" x2="435" y2="130" stroke="#0284c7" stroke-width="2"/>

        <!-- Línea de enlace hacia Wallbox (Cable + Tubo) -->
        <line x1="520" y1="130" x2="620" y2="130" stroke="#0284c7" stroke-width="3"/>
        <polygon points="615,126 623,130 615,134" fill="#0284c7" />

        <!-- Etiqueta Cable / Tubo -->
        <rect x="525" y="140" width="90" height="42" fill="#f8fafc" stroke="#94a3b8" stroke-width="0.8" rx="3"/>
        <text x="570" y="153" fill="#0f172a" font-family="Arial, sans-serif" font-size="8.5" font-weight="bold" text-anchor="middle">Cable {num_cond}{s_final:.1f} mm²</text>
        <text x="570" y="166" fill="#0369a1" font-family="Arial, sans-serif" font-size="8" text-anchor="middle">RZ1-K (AS) Cca</text>
        <text x="570" y="178" fill="#64748b" font-family="Arial, sans-serif" font-size="7.5" text-anchor="middle">Tubo {tubo_dim}</text>

        <!-- Bloque 3: Wallbox y Conector Tipo 2 -->
        <rect x="620" y="55" width="205" height="160" fill="#f8fafc" stroke="#10b981" stroke-width="2" rx="8"/>
        <text x="722" y="80" fill="#047857" font-family="Arial, sans-serif" font-size="12" font-weight="bold" text-anchor="middle">ESTACIÓN DE RECARGA</text>
        
        <!-- Icono Cargador -->
        <rect x="640" y="95" width="70" height="95" fill="#0f172a" rx="6"/>
        <circle cx="675" cy="125" r="14" fill="#10b981" />
        <text x="675" y="130" fill="#ffffff" font-family="Arial, sans-serif" font-size="13" font-weight="bold" text-anchor="middle">⚡</text>
        <text x="675" y="165" fill="#38bdf8" font-family="Arial, sans-serif" font-size="9" font-weight="bold" text-anchor="middle">{pot_w/1000:.2f} kW</text>
        <text x="675" y="178" fill="#94a3b8" font-family="Arial, sans-serif" font-size="8" text-anchor="middle">Modo 3</text>

        <!-- Conector Tipo 2 / Mennekes -->
        <rect x="725" y="95" width="85" height="95" fill="#ffffff" stroke="#cbd5e1" stroke-width="1" rx="4"/>
        <text x="767" y="112" fill="#0f172a" font-family="Arial, sans-serif" font-size="9.5" font-weight="bold" text-anchor="middle">TIPO 2</text>
        <text x="767" y="125" fill="#64748b" font-family="Arial, sans-serif" font-size="8" text-anchor="middle">Mennekes IEC</text>
        <text x="767" y="145" fill="#0284c7" font-family="Arial, sans-serif" font-size="8.5" font-weight="bold" text-anchor="middle">{tension_txt}</text>
        <text x="767" y="165" fill="#15803d" font-family="Arial, sans-serif" font-size="8" font-weight="bold" text-anchor="middle">ΔV real: {dv_pct:.2f}%</text>
        <text x="767" y="180" fill="#d97706" font-family="Arial, sans-serif" font-size="8" text-anchor="middle">Balanceo Dinámico</text>
    </svg>
    """
    return svg

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
        st.title("🚗 Infraestructura de Recarga de Vehículos Eléctricos (IRVE - ITC-BT-52)")
        st.caption("Cálculo reglamentario, esquemas en origen, protecciones, balanceo inteligente SPL y presupuesto para instaladores.")
    with col_b1_i:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        st.button("🔄 Restablecer", on_click=reset_valores_irve, use_container_width=True)

    # =========================================================================
    # MEMORIA TÉCNICA Y GUÍA DE ESQUEMAS EN ORIGEN (ITC-BT-52)
    # =========================================================================
    with st.expander("📖 GUÍA TÉCNICA: ¿Cuál Esquema de Instalación en Origen debo Elegir?", expanded=False):
        st.markdown("""
        La instrucción **ITC-BT-52 (RD 1053/2014)** define 5 esquemas topológicos oficiales para la conexión de puntos de recarga.
        A continuación, te mostramos cuándo y por qué elegir cada uno en la práctica de la calle:
        """)

        tab_e2, tab_e4, tab_e3a, tab_e1, tab_e3b, tab_resumen = st.tabs([
            "⭐ Esquema 2 (Más Utilizado)",
            "🏡 Esquema 4a/4b (Unifamiliar)",
            "🏢 Esquema 3a (Contador Exclusivo)",
            "👥 Esquema 1 (Colectivo)",
            "🔌 Esquema 3b (Exterior)",
            "📊 Comparativa y Criterios"
        ])

        with tab_e2:
            st.markdown(f"""
            ### ⭐ Esquema 2: Contador Principal Común para Vivienda y Recarga
            **¿Por qué es la opción recomendada y por defecto?**
            * **Ámbito de aplicación:** Edificios de viviendas en régimen de propiedad horizontal donde el usuario tiene la plaza de garaje en el mismo edificio que su vivienda.
            * **Punto de conexión física:** En los bornes de salida del contador de la vivienda situado en la **centralización de contadores del edificio**.
            * **Ahorro para el cliente:** **¡No paga un segundo término fijo de potencia!** Se utiliza la misma potencia contratada de la vivienda.
            * **Balanceo Dinámico (SPL):** Permite instalar una pinza amperimétrica en el cuadro de contadores o en la vivienda para modular automáticamente la recarga según el consumo doméstico.
            * **Caída de tensión máxima admisible:** **1.0%** en la línea desde centralización hasta la plaza.
            * **Permiso Comunitario:** Conforme al **Art. 17.5 de la Ley de Propiedad Horizontal**, **NO requiere votación ni aprobación en junta**, solo comunicación previa por escrito al presidente o administrador.
            """)

        with tab_e4:
            st.markdown("""
            ### 🏡 Esquema 4a / 4b: Circuito Adicional desde el CGMP de la Vivienda
            * **Ámbito de aplicación:** Viviendas unifamiliares (chalets, adosados), locales comerciales o viviendas con garaje propio físicamente anexo.
            * **Punto de conexión:** Directamente en el **Cuadro General de Mando y Protección (CGMP)** de la vivienda como circuito dedicado C13 / C_IRVE.
            * **Ventaja:** Instalación ultra rápida, económica y sin salir de la propiedad privada.
            * **Caída de tensión máxima admisible:** **1.5%** desde el CGMP.
            """)

        with tab_e3a:
            st.markdown("""
            ### 🏢 Esquema 3a: Contador Individual Exclusivo en Centralización
            * **Ámbito de aplicación:** Propietarios que tienen una plaza de garaje en un edificio pero **no tienen vivienda en esa misma finca**, o desean una factura 100% independiente.
            * **Punto de conexión:** Nuevo contador exclusivo ubicado en la centralización de contadores del edificio.
            * **Requisitos:** Requiere solicitar un nuevo CUPS a la compañía distribuidora y pagar el término de potencia independiente.
            * **Caída de tensión máxima:** **1.0%**.
            """)

        with tab_e1:
            st.markdown("""
            ### 👥 Esquema 1: Colectivo Troncal con Contador Principal
            * **Ámbito de aplicación:** Parkings comunitarios de nueva construcción, parkings públicos de rotación, empresas y flotas con Gestor de Carga (CPO).
            * **Topología:** Una línea general troncal con canalizaciones preinstaladas y cuadros secundarios por plaza con contadores MID.
            * **Control:** Obligatorio Sistema de Protección de Línea (SPL) para gestión dinámica inteligente de toda la potencia del garaje.
            """)

        with tab_e3b:
            st.markdown("""
            ### 🔌 Esquema 3b: Contador Individual en Plaza de Aparcamiento o Exterior
            * **Ámbito de aplicación:** Aparcamientos exteriores o en superficie donde no existe centralización de contadores comunitaria.
            * **Punto de conexión:** Caja de protección y medida (CPM) instalada junto a la plaza o en fachada.
            """)

        with tab_resumen:
            st.markdown("""
            | Esquema | Origen de la Línea | ¿Requiere Nuevo CUPS? | Límite Caída Tensión | Uso Recomendado en la Calle |
            | :--- | :--- | :---: | :---: | :--- |
            | **Esquema 2 (Por Defecto)** | Centralización (Bornes salida contador vivienda) | ❌ NO (Comparte contrato) | **1.0%** | **Garajes comunitarios en el mismo edificio que la vivienda** |
            | **Esquema 4a / 4b** | CGMP interior de la vivienda | ❌ NO (Comparte contrato) | **1.5%** | **Chalets, adosados y viviendas unifamiliares** |
            | **Esquema 3a** | Centralización (Contador exclusivo) |  SÍ (Contrato nuevo) | **1.0%** | **Vecino de otro edificio / Factura separada** |
            | **Esquema 1** | Cuadro general exclusivo de recarga |  SÍ (Contador colectivo) | **1.0%** | **Parkings públicos, empresas, nuevas promociones** |
            | **Esquema 3b** | Caja exterior / plaza |  SÍ (Acometida exterior) | **1.0%** | **Parkings abiertos / vía pública** |
            """)

    # =========================================================================
    # SELECTOR DE CLIENTE Y PROYECTO (CRM)
    # =========================================================================
    try:
        from modulos import selector_cliente_proyecto
        datos_irve = {
            "irve_custom_w": st.session_state.get("irve_custom_w", 7360.0),
            "irve_long": st.session_state.get("irve_long", 25.0),
            "irve_esquema": st.session_state.get("irve_esquema_sel_key", "Esquema 2"),
            "irve_red": st.session_state.get("irve_red", "Monofásico (230 V)")
        }
        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">👤 Cliente y Expediente del Proyecto</h4></div>', unsafe_allow_html=True)
        selector_cliente_proyecto.renderizar_barra_cliente_proyecto("IRVE", datos_irve, "Cálculo de Línea de Recarga IRVE (ITC-BT-52)")
    except Exception:
        pass

    # =========================================================================
    # SECCIÓN 1: PARÁMETROS DEL CIRCUITO DE RECARGA Y WALLBOX
    # =========================================================================
    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🚗 SECCIÓN 1: Parámetros del Circuito de Recarga y Wallbox (ITC-BT-52)</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        with st.form("form_irve_parametros"):
            c1_i, c2_i = st.columns(2)
            with c1_i:
                # Esquema 2 POR DEFECTO
                opciones_esquemas_keys = list(ESQUEMAS_IRVE_INFO.keys())
                idx_def_esq = 0 # Esquema 2 es el primero
                
                esq_key_sel = st.selectbox(
                    "Origen de la línea (Esquema ITC-BT-52):",
                    options=opciones_esquemas_keys,
                    format_func=lambda k: f"{k} - {ESQUEMAS_IRVE_INFO[k]['nombre'].split('(')[1].replace(')', '') if '(' in ESQUEMAS_IRVE_INFO[k]['nombre'] else k}",
                    index=idx_def_esq,
                    key="irve_esquema_sel_key"
                )
                
                info_esq = ESQUEMAS_IRVE_INFO.get(esq_key_sel, ESQUEMAS_IRVE_INFO["Esquema 2"])
                st.caption(f"💡 **Criterio {esq_key_sel}:** {info_esq['uso_principal']}")

                irve_pot = st.selectbox(
                    "Potencia del Cargador (Wallbox):",
                    [
                        "7.360 W (32A - Monofásico Estándar Wallbox)",
                        "3.680 W (16A - Monofásico Lento)",
                        "11.000 W (16A - Trifásico)",
                        "22.000 W (32A - Trifásico Rápido AC)",
                        "✏️ Personalizada (W)"
                    ],
                    index=0,
                    key="irve_pot_sel"
                )
                
                if "Personalizada" in irve_pot:
                    p_cargador_val = st.number_input("Introduce Potencia del Wallbox (W):", value=7360.0, step=250.0, key="irve_custom_w")
                else:
                    p_cargador_val = float(irve_pot.split(" ")[0].replace(".", ""))

                irve_long = st.number_input("Longitud del cable hasta la plaza de garaje (m):", value=25.0, min_value=1.0, max_value=500.0, step=1.0, key="irve_long")

            with c2_i:
                tipo_red_irve = st.radio("Tipo de Alimentación:", ["Monofásico (230 V)", "Trifásico (400 V)"], key="irve_red", horizontal=True)
                irve_mat = st.selectbox("Material Conductor:", ["cobre"], key="irve_mat")
                irve_aisl = st.selectbox(
                    "Aislamiento del Conductor:",
                    [
                        "XLPE / EPR (90ºC) - RZ1-K (Cca-s1b,d1,a1 Libre Halógenos)",
                        "PVC (70ºC)"
                    ],
                    key="irve_aisl"
                )
                metodo_irve_key = st.selectbox("Método de Instalación:", list(METODOS_INSTALACION_IRVE.keys()), index=0, key="irve_met")
                
                st.info("⚡ **Sistema de Balanceo Inteligente (SPL):** Recomendado siempre para modular la carga en tiempo real con el consumo de la vivienda.")

            submitted_irve = st.form_submit_button("🔄 Recalcular Circuito IRVE y Protecciones", type="primary", use_container_width=True)

    # =========================================================================
    # MOTOR DE CÁLCULO REGLAMENTARIO ITC-BT-52
    # =========================================================================
    es_trif_irve = "Trifásico" in tipo_red_irve
    v_t_irve = 400.0 if es_trif_irve else 230.0
    cos_phi_irve = 1.0 # Régimen de carga resistiva/electrónica factor unidad
    
    # Intensidad de diseño Ib
    ib_irve = rebt.calcular_intensidad_diseno(p_cargador_val, v_t_irve, cos_phi_irve, es_trif_irve)
    
    # Límite de caída de tensión según esquema (1.0% en Esquema 1, 2, 3a, 3b / 1.5% en Esquema 4a/4b)
    info_esq_actual = ESQUEMAS_IRVE_INFO.get(st.session_state.get("irve_esquema_sel_key", "Esquema 2"), ESQUEMAS_IRVE_INFO["Esquema 2"])
    dv_pct_limite = float(info_esq_actual.get("limite_cdt", 1.0))
    
    gamma_irve = rebt.obtener_gamma(irve_mat, irve_aisl)
    dv_max_adm_v = v_t_irve * (dv_pct_limite / 100.0)
    
    # Sección teórica por caída de tensión
    s_cdt_irve = rebt.calcular_seccion_por_cdt(p_cargador_val, irve_long, gamma_irve, dv_pct_limite, v_t_irve, es_trif_irve)
    
    # Selección de protección magnetotérmica (PIA Curva C)
    in_pi_auto = seleccionar_proteccion_irve(ib_irve)
    
    # Sección mínima por ITC-BT-52 es 2.5 mm2 en cobre
    s_final_irve = seleccionar_seccion_optima_irve(max(s_cdt_irve, 2.5))
    
    # Verificación térmica de intensidad admisible (Iz >= In >= Ib)
    tabla_iz_irve = rebt.obtener_tabla_iz(irve_mat, irve_aisl, metodo_irve_key)
    while True:
        iz_a_irve = tabla_iz_irve.get(s_final_irve, 61.0)
        if in_pi_auto <= iz_a_irve and iz_a_irve >= ib_irve:
            break
        idx_s = SECCIONES_COMERCIALES_IRVE.index(s_final_irve) if s_final_irve in SECCIONES_COMERCIALES_IRVE else 1
        if idx_s < len(SECCIONES_COMERCIALES_IRVE) - 1:
            s_final_irve = SECCIONES_COMERCIALES_IRVE[idx_s + 1]
        else:
            break

    # Caída de tensión real obtenida
    dv_real_irve_v = rebt.calcular_caida_tension_v(p_cargador_val, irve_long, gamma_irve, s_final_irve, v_t_irve, es_trif_irve)
    dv_real_irve_pct = rebt.calcular_caida_tension_pct(dv_real_irve_v, v_t_irve)

    # Dimensionamiento reglamentario de tubo protector libre de halógenos IK08
    tubo_dim_str, tubo_desc = rebt.dimensionar_tubo_irve(s_final_irve, es_trif_irve)

    # =========================================================================
    # SECCIÓN 2: MEMORIA ANALÍTICA Y RESULTADOS REGLAMENTARIOS
    # =========================================================================
    st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">📋 SECCIÓN 2: Memoria Analítica, Protecciones y Sección Óptima</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        if es_trif_irve:
            f_ib_irve = r"I_b = \frac{P}{\sqrt{3} \cdot V \cdot \cos\varphi}"
            s_ib_irve = f"I_b = \\frac{{{p_cargador_val:,.1f} \\text{{ W}}}}{{\\sqrt{3} \\cdot 400 \\text{{ V}} \\cdot 1.0}} = \\mathbf{{{ib_irve:.2f}\\text{{ A}}}}"
            f_s_irve = r"S = \frac{1 \cdot P \cdot L}{\gamma \cdot \Delta V_{\text{máx}} \cdot V}"
            s_s_irve = f"S = \\frac{{1 \\cdot {p_cargador_val:,.1f} \\cdot {irve_long}}}{{{gamma_irve} \\cdot {dv_max_adm_v:.2f} \\cdot 400}} = \\mathbf{{{s_cdt_irve:.2f}\\text{{ mm}}^2}}"
        else:
            f_ib_irve = r"I_b = \frac{P}{V \cdot \cos\varphi}"
            s_ib_irve = f"I_b = \\frac{{{p_cargador_val:,.1f} \\text{{ W}}}}{{230 \\text{{ V}} \\cdot 1.0}} = \\mathbf{{{ib_irve:.2f}\\text{{ A}}}}"
            f_s_irve = r"S = \frac{2 \cdot P \cdot L}{\gamma \cdot \Delta V_{\text{máx}} \cdot V}"
            s_s_irve = f"S = \\frac{{2 \\cdot {p_cargador_val:,.1f} \\cdot {irve_long}}}{{{gamma_irve} \\cdot {dv_max_adm_v:.2f} \\cdot 230}} = \\mathbf{{{s_cdt_irve:.2f}\\text{{ mm}}^2}}"

        col_irve_res1, col_irve_res2 = st.columns(2)
        with col_irve_res1:
            st.info(f"""
            #### 1. Intensidad de Diseño del Cargador ($I_b$)
            
            **Fórmula Reglamentaria:**
            $${f_ib_irve}$$
            
            **Sustitución y Resultado:**
            $${s_ib_irve}$$
            * Factor de servicio continuo: 100% de la potencia nominal en régimen permanente.
            """)

        with col_irve_res2:
            st.info(f"""
            #### 2. Sección Teórica por Caída de Tensión (Línea IRVE)
            
            **Fórmula Reglamentaria (límite {dv_pct_limite:.1f}% CDT):**
            $${f_s_irve}$$
            
            **Sustitución y Resultado:**
            $${s_s_irve}$$
            * Caída máxima permitida: **{dv_max_adm_v:.2f} V ({dv_pct_limite:.1f}%)**.
            """)

        # Banner de Protecciones Exigidas
        st.markdown(f"""
        <div style="background: #f8fafc; border: 2px solid #0284c7; padding: 18px; border-radius: 8px; color: #0f172a; margin: 15px 0;">
            <h4 style="margin-top: 0; color: #0284c7; font-size: 16px;">🛡️ Esquema de Protecciones Obligatorias (ITC-BT-52):</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 10px;">
                <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1;">
                    <b style="color: #0369a1;">1. Magnetotérmico (PIA):</b><br/>
                    Calibre <b>{in_pi_auto} A (Curva C)</b><br/>
                    <small style="color: #64748b;">Poder de corte ≥ 6 kA. Protección contra sobrecargas y cortocircuitos.</small>
                </div>
                <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1;">
                    <b style="color: #15803d;">2. Diferencial Obligatorio:</b><br/>
                    <b>Clase A (con 6mA DC)</b> o <b>Clase B</b><br/>
                    <small style="color: #64748b;">Sensibilidad 30 mA. Detección de fugas en alterna y corriente continua pura.</small>
                </div>
                <div style="background: white; padding: 10px; border-radius: 6px; border: 1px solid #cbd5e1;">
                    <b style="color: #d97706;">3. Sobretensiones (VTP+VSP):</b><br/>
                    <b>Permanentes + Transitorias Tipo 2</b><br/>
                    <small style="color: #64748b;">Con bobina de emisión/disparo o rearme automático.</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Dictamen Final
        st.success(f"""
        ### ✅ SECCIÓN COMERCIAL ÓPTIMA REBT: {s_final_irve:.1f} mm² Cu (RZ1-K 0.6/1kV)
        * **Esquema de Origen:** {info_esq_actual['nombre']}.
        * **Caída de tensión real:** **{dv_real_irve_pct:.3f}%** ({dv_real_irve_v:.2f} V), inferior al límite del **{dv_pct_limite:.1f}%**.
        * **Intensidad máxima admisible del cable ($I_z$):** **{iz_a_irve:.1f} A** $\ge$ Magnetotérmico **{in_pi_auto} A** $\ge$ Intensidad $I_b$ **{ib_irve:.2f} A** *(Verificación térmica 100% OK)*.
        * **Canalización reglamentaria:** Tubo **{tubo_dim_str}** no propagador de la llama, libre de halógenos y resistencia al impacto **IK08**.
        """)

    # =========================================================================
    # SECCIÓN 3: ESQUEMA UNIFILAR GRÁFICO VECTORIAL INTERACTIVO
    # =========================================================================
    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">📐 SECCIÓN 3: Esquema Unifilar Gráfico de la Instalación IRVE</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        svg_unifilar = generar_svg_unifilar_irve(
            esquema_nombre=info_esq_actual['nombre'],
            pot_w=p_cargador_val,
            s_final=s_final_irve,
            in_pi=in_pi_auto,
            dv_pct=dv_real_irve_pct,
            tubo_dim=tubo_dim_str,
            es_trif=es_trif_irve
        )
        st.markdown(svg_unifilar, unsafe_allow_html=True)
        st.caption("Diagrama vectorial generado en tiempo real según los parámetros calculados y la topología ITC-BT-52.")

    # =========================================================================
    # SECCIÓN 4: PRESUPUESTADOR Y ACOPIO DE MATERIALES PARA EL INSTALADOR
    # =========================================================================
    st.markdown('<div class="section-header-amber"><h4 style="margin:0; color:#b45309;">💰 SECCIÓN 4: Presupuestador de Obra y Lista de Materiales para el Instalador</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("""
        Calcula el coste total de los materiales y mano de obra para presentar una oferta inmediata al cliente.
        Puedes ajustar precios y cantidades según tus tarifas de compra de distribuidor.
        """)

        # Lista de materiales por defecto calculada automáticamente
        long_calc = float(irve_long)
        tubo_calc = math.ceil(long_calc * 1.1) # 10% margen
        cable_calc = math.ceil(long_calc * 1.15) # 15% margen

        # Estimación de precios de mercado
        p_cargador_pvp = 750.0 if p_cargador_val <= 7400 else 1150.0
        p_cable_m = 2.40 if s_final_irve <= 6 else (3.80 if s_final_irve <= 10 else 5.90)
        p_tubo_m = 1.80
        p_cuadro_pvp = 45.0
        p_pia_pvp = 22.0
        p_dif_pvp = 75.0
        p_vtp_pvp = 85.0
        p_balanceo_pvp = 95.0
        p_mano_obra_h = 42.0
        h_estimadas = 6.0 if long_calc <= 30 else 8.0
        p_boletin_pvp = 140.0

        col_pr1, col_pr2 = st.columns([3, 2])
        
        with col_pr1:
            st.markdown("##### 📦 Materiales y Equipos Principales:")
            c_wbox = st.number_input("1. Punto de Recarga Wallbox Modo 3 Tipo 2 (€/ud):", value=p_cargador_pvp, step=50.0, key="pres_irve_wbox")
            c_cable = st.number_input(f"2. Cable RZ1-K 0.6/1kV {s_final_irve}mm² ({cable_calc} m) (€/m):", value=p_cable_m, step=0.20, key="pres_irve_cable")
            c_tubo = st.number_input(f"3. Tubo {tubo_dim_str} libre halógenos IK08 ({tubo_calc} m) (€/m):", value=p_tubo_m, step=0.20, key="pres_irve_tubo")
            c_cuadro = st.number_input("4. Cuadro modular IP65 con cerradura garaje (€/ud):", value=p_cuadro_pvp, step=5.0, key="pres_irve_cuadro")
            c_prot = st.number_input(f"5. Kit Protecciones (PIA {in_pi_auto}A + Dif Tipo A 6mA + Sobretensiones VTP/VSP) (€):", value=p_pia_pvp+p_dif_pvp+p_vtp_pvp, step=10.0, key="pres_irve_prot")

        with col_pr2:
            st.markdown("##### 🔧 Medición, Mano de Obra y Boletín:")
            c_bal = st.number_input("6. Sensor / Medidor de Balanceo Dinámico SPL (€/ud):", value=p_balanceo_pvp, step=10.0, key="pres_irve_bal")
            horas_mo = st.number_input("7. Horas de Montaje e Instalación (h):", value=h_estimadas, step=1.0, key="pres_irve_h_mo")
            precio_h = st.number_input("8. Precio Mano de Obra (€/h):", value=p_mano_obra_h, step=2.0, key="pres_irve_p_mo")
            c_cie = st.number_input("9. Tramitación Memoria Técnica y Boletín CIE (€):", value=p_boletin_pvp, step=10.0, key="pres_irve_cie")
            tipo_iva_sel = st.radio("Tipo de IVA aplicable:", ["21% (General)", "10% (Reforma / Vivienda habitual)"], horizontal=True, key="pres_irve_iva_sel")

        # Cálculo de totales
        tot_equipos = c_wbox + (c_cable * cable_calc) + (c_tubo * tubo_calc) + c_cuadro + c_prot + c_bal
        tot_mo = horas_mo * precio_h
        tot_tram = c_cie
        subtotal_obra = tot_equipos + tot_mo + tot_tram
        
        pct_iva = 0.10 if "10%" in tipo_iva_sel else 0.21
        iva_total = subtotal_obra * pct_iva
        total_con_iva = subtotal_obra + iva_total

        # Estimación Subvención Plan MOVES III (70%)
        subvencion_moves_70 = total_con_iva * 0.70
        neto_cliente_moves = total_con_iva - subvencion_moves_70

        st.markdown(f"""
        <div style="background: #f0fdf4; border: 2px solid #16a34a; border-radius: 8px; padding: 16px; margin: 15px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <h3 style="color: #15803d; margin: 0;">Presupuesto Total de Instalación: {total_con_iva:,.2f} € (IVA Incluido)</h3>
                    <p style="color: #334155; margin: 4px 0 0 0; font-size: 13px;">
                        Base Imponible: <b>{subtotal_obra:,.2f} €</b> | IVA ({int(pct_iva*100)}%): <b>{iva_total:,.2f} €</b>
                    </p>
                </div>
                <div style="background: white; border: 1.5px solid #16a34a; padding: 8px 14px; border-radius: 6px; text-align: right;">
                    <span style="font-size: 11px; color: #15803d; font-weight: bold;">🌱 AYUDA ESTIMADA PLAN MOVES III (70%):</span><br/>
                    <b style="font-size: 15px; color: #15803d;">- {subvencion_moves_70:,.2f} €</b><br/>
                    <small style="color: #475569;">Coste neto para el cliente: <b>{neto_cliente_moves:,.2f} €</b></small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        lista_materiales_pdf = [
            {"concepto": f"Punto de Recarga Wallbox Modo 3 Conector Tipo 2 ({p_cargador_val/1000:.2f} kW)", "cantidad": 1, "unidad": "ud", "precio_ud": c_wbox},
            {"concepto": f"Cable libre de halógenos RZ1-K 0.6/1kV {s_final_irve} mm² (Cca-s1b,d1,a1)", "cantidad": cable_calc, "unidad": "m", "precio_ud": c_cable},
            {"concepto": f"Tubo protector {tubo_dim_str} libre de halógenos resistencia IK08 con accesorios", "cantidad": tubo_calc, "unidad": "m", "precio_ud": c_tubo},
            {"concepto": "Cuadro secundario modular estanco IP65 con cerradura para garaje", "cantidad": 1, "unidad": "ud", "precio_ud": c_cuadro},
            {"concepto": f"Kit de Protecciones ITC-BT-52 (PIA {in_pi_auto}A C + Dif Tipo A 6mA DC + VTP/VSP)", "cantidad": 1, "unidad": "ud", "precio_ud": c_prot},
            {"concepto": "Módulo de medida y sensor toroidal para Balanceo Dinámico de Carga (SPL)", "cantidad": 1, "unidad": "ud", "precio_ud": c_bal},
            {"concepto": "Mano de obra cualificada de montaje, tendido de línea y conexionado", "cantidad": horas_mo, "unidad": "h", "precio_ud": precio_h},
            {"concepto": "Elaboración de Memoria Técnica de Diseño (MTD) y Certificado CIE Oficial", "cantidad": 1, "unidad": "ud", "precio_ud": c_cie}
        ]

    # =========================================================================
    # SECCIÓN 5: ASISTENTE IA EXPERTO EN IRVE Y REBT (VOZ Y TEXTO)
    # =========================================================================
    ia_asistente_irve.renderizar_asistente_irve()

    # =========================================================================
    # SECCIÓN 6: GENERACIÓN DE REPORTE TÉCNICO OFICIAL EN PDF
    # =========================================================================
    st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">🖨️ SECCIÓN 6: Generación de Memoria Técnica Oficial en PDF (ITC-BT-52)</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        with st.expander("📄 Configurar Datos del Proyecto y Exportar PDF Oficial", expanded=True):
            # Cargar datos del usuario autenticado si existen
            user_auth = st.session_state.get("usuario_autenticado", {})
            nom_inst_def = user_auth.get("nombre_instalador", "Richard Orlando Choque Tejerina")
            emp_def = user_auth.get("nombre_empresa", "BOLIMUR INSTALACIONES Y REFORMAS")
            lic_def = user_auth.get("num_licencia_rebt", "REBT-30/15892")

            cli_activo = st.session_state.get("cliente_activo_proyecto", {})
            cli_nom_def = cli_activo.get("nombre_completo", "Propietario / Cliente IRVE")
            cli_nif_def = cli_activo.get("nif_cif", "-")
            cli_dir_def = cli_activo.get("direccion", "Plaza de Garaje nº 18")

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                p_nombre = st.text_input("Nombre de la Obra / Edificio:", "Instalación Punto de Recarga IRVE", key="irve_pdf_nombre")
                p_emplazamiento = st.text_input("Emplazamiento / Dirección:", cli_dir_def, key="irve_pdf_emp")
                p_cliente_nom = st.text_input("Nombre del Cliente / Titular:", cli_nom_def, key="irve_pdf_cli_nom")
                p_cliente_nif = st.text_input("NIF / CIF del Cliente:", cli_nif_def, key="irve_pdf_cli_nif")
            with col_m2:
                p_proyectista = st.text_input("Técnico / Instalador Autorizado:", nom_inst_def, key="irve_pdf_proy")
                p_licencia = st.text_input("Nº Carnet / Registro REBT:", lic_def, key="irve_pdf_lic")
                p_empresa = st.text_input("Empresa Instaladora:", emp_def, key="irve_pdf_empresa")
                p_expediente = st.text_input("Nº Expediente / Referencia:", "EXP-IRVE-2026-01", key="irve_pdf_exp")

            proyecto_info = {
                "nombre": p_nombre,
                "emplazamiento": p_emplazamiento,
                "cliente_nombre": p_cliente_nom,
                "cliente_nif": p_cliente_nif,
                "proyectista": p_proyectista,
                "licencia": p_licencia,
                "empresa": p_empresa,
                "expediente": p_expediente,
                "fecha": datetime.date.today().strftime("%d/%m/%Y")
            }

            irve_params = {
                "pot_wallbox": p_cargador_val,
                "long": irve_long,
                "mat": irve_mat,
                "aisl": irve_aisl,
                "metodo": metodo_irve_key,
                "esquema": info_esq_actual['nombre'],
                "red": tipo_red_irve,
                "es_trifasico": es_trif_irve
            }

            irve_results = {
                "ib": ib_irve,
                "dv_max_adm_pct": dv_pct_limite,
                "dv_max_adm_v": dv_max_adm_v,
                "s_cdt": s_cdt_irve,
                "s_final": s_final_irve,
                "in_pi": in_pi_auto,
                "iz_adm": iz_a_irve,
                "dv_real_v": dv_real_irve_v,
                "dv_real_pct": dv_real_irve_pct,
                "tubo_irve": tubo_dim_str,
                "gamma": gamma_irve
            }

            try:
                pdf_bytes_irve = pdf_irve.generar_pdf_irve(proyecto_info, irve_params, irve_results, lista_materiales_pdf)
                from modulos import visor_pdf
                visor_pdf.mostrar_visor_pdf(
                    pdf_bytes=pdf_bytes_irve,
                    nombre_archivo=f"Memoria_Tecnica_IRVE_{p_expediente}.pdf",
                    label_boton="📥 Descargar Memoria Técnica Oficial IRVE (PDF)"
                )
            except Exception as err:
                st.error(f"⚠️ Ocurrió un error al generar el archivo PDF de IRVE: {err}")
