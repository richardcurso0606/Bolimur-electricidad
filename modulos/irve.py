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
    /* Ajustes responsivos para selectbox y campos de entrada en pantallas pequeñas */
    div[data-baseweb="select"] {
        width: 100% !important;
    }
    div[data-baseweb="select"] * {
        white-space: normal !important;
        word-break: break-word !important;
        text-overflow: unset !important;
    }
    div[data-baseweb="select"] > div {
        min-height: 42px !important;
        height: auto !important;
        padding: 4px 8px !important;
    }
    div[data-testid="stSelectbox"] label {
        font-weight: 600 !important;
        font-size: 13.5px !important;
        color: #1e293b !important;
    }

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
    with st.expander("📖 GUÍA TÉCNICA Y MEMORIA: ¿Cuál Esquema de Instalación en Origen debo Elegir?", expanded=True):
        st.markdown("""
        ### ❓ ¿Qué significa el "Origen de la Línea"?
        El **origen** es simplemente **el punto físico exacto donde vas a conectar tus cables** para alimentar el cargador del coche.
        En una instalación real no se puede "empalmar de cualquier sitio o caja de luz del garaje". La normativa **ITC-BT-52 (RD 1053/2014)** define **5 esquemas oficiales**.
        
        Aquí tienes la explicación detallada y práctica para saber **cuál elegir en cada obra**:
        """)

        # Árbol de decisión rápido
        st.markdown("""
        <div style="background: #f1f5f9; border: 2px solid #0284c7; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px;">
            <h4 style="margin: 0 0 8px 0; color: #0369a1;">⚡ GUÍA RÁPIDA DE DECISIÓN (En 5 Segundos):</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 13.5px; color: #1e293b; line-height: 1.6;">
                <li>🏡 <b>¿Es un chalet, adosado o casa unifamiliar?</b> &rarr; Elige <b>ESQUEMA 4a</b> (directo desde el cuadro general de la casa).</li>
                <li>⭐ <b>¿Es un garaje comunitario y el cliente vive en el mismo bloque?</b> &rarr; Elige <b>ESQUEMA 2</b> (salida de su contador en centralización). <i>¡Es el más rentable y el 90% de los casos!</i></li>
                <li>🏢 <b>¿Es un garaje comunitario pero el cliente vive en otro edificio?</b> &rarr; Elige <b>ESQUEMA 3a</b> (solicitar contador nuevo independiente).</li>
                <li>👥 <b>¿Es un garaje comunitario nuevo con infraestructura colectiva?</b> &rarr; Elige <b>ESQUEMA 1</b> (contador colectivo troncal con gestor CPO).</li>
                <li>🔌 <b>¿Es un parking exterior o en vía pública sin portal?</b> &rarr; Elige <b>ESQUEMA 3b</b> (caja exterior CPM junto a la plaza).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        tab_e2, tab_e4, tab_e3a, tab_e1, tab_e3b, tab_resumen = st.tabs([
            "⭐ Esquema 2 (El más habitual)",
            "🏡 Esquema 4a/4b (Chalets y Unifamiliares)",
            "🏢 Esquema 3a (Contador Exclusivo)",
            "👥 Esquema 1 (Colectivo Comunitario)",
            "🔌 Esquema 3b (Exteriores)",
            "📊 Tabla Resumen Comparativa"
        ])

        with tab_e2:
            st.markdown(f"""
            ### ⭐ ESQUEMA 2: Contador Principal Común para Vivienda y Recarga
            > **El que vas a realizar en más del 90% de las instalaciones en garajes comunitarios.**

            * **📍 ¿Dónde te conectas físicamente?**  
              Bajas al **cuarto de centralización de contadores del edificio**. Localizas el contador correspondiente al piso de tu cliente (por ejemplo, el *3º B*). Te conectas **justo en los bornes de salida de su contador**, antes de que su cable suba hacia la vivienda. Desde allí tiras el tubo libre de halógenos y cable *RZ1-K* por las zonas comunes (bandejas o techo del garaje) hasta su plaza.
            
            * **💡 ¿Por qué es el mejor y el más recomendado?**
              1. **Ahorro total para el cliente:** **NO paga un segundo recibo de luz**. Toda la recarga del coche entra en la misma factura mensual de su vivienda.
              2. **Ahorro brutal en término de potencia:** No necesita contratar 7,4 kW adicionales. Le instalas un **balanceador dinámico de potencia (pinza amperimétrica CT)** en la centralización o en el cuadro de su casa. Si durante el día la casa está consumiendo energía (horno, aire acondicionado), el cargador modula y baja la potencia para que nunca salte el limitador (ICP). De noche, cuando la casa duerme, el coche carga a máxima potencia.
              3. **Permiso legal garantizado (Art. 17.5 Ley de Propiedad Horizontal):** El propietario solo tiene que entregar una **comunicación previa por escrito** al Presidente de la Comunidad o Administrador de Fincas con 30 días de antelación. **¡NO requiere votación ni aprobación en junta de vecinos!**
            
            * **🛡️ Protecciones requeridas:**
              * En el cuarto de contadores: Fusible o IGA de protección de la derivación.
              * En la plaza de garaje: Cuadro estanco modular con cerradura, **PIA Curva C**, **Diferencial Clase A (con 6mA DC) o Clase B** y **Protector contra sobretensiones permanentes y transitorias (VTP+VSP)**.
            * **📏 Caída de tensión máxima permitida:** **1,0%** (desde el cuarto de contadores hasta el cargador).
            """)

        with tab_e4:
            st.markdown("""
            ### 🏡 ESQUEMA 4a / 4b: Circuito Adicional Directo desde el Cuadro (CGMP)
            > **El esquema ideal para chalets, adosados y viviendas unifamiliares con garaje propio.**

            * **📍 ¿Dónde te conectas físicamente?**  
              Directamente en el **Cuadro General de Mando y Protección (CGMP)** de la propia casa. Colocas un magnetotérmico y diferencial nuevos en el carril DIN (circuito terminal dedicado C13 / IRVE) y llevas el cable hasta la pared donde va el Wallbox.
            
            * **💡 ¿Cuándo se utiliza?**  
              En cualquier vivienda donde el garaje esté dentro de la propiedad privada o anexo directamente a la vivienda.
            
            * **👍 Ventajas para el instalador y cliente:**
              * Es la instalación **más rápida, económica y limpia**, ya que no requiere pasar por zonas comunes de vecinos ni cuartos de contadores.
              * El balanceo de carga se conecta directamente en el mismo cuadro de la casa.
            * **📏 Caída de tensión máxima permitida:** **1,5%** (desde el cuadro de la vivienda).
            """)

        with tab_e3a:
            st.markdown("""
            ### 🏢 ESQUEMA 3a: Contador Individual Exclusivo en Centralización
            > **Para el cliente que tiene plaza en el garaje pero vive en otro edificio o quiere factura 100% separada.**

            * **📍 ¿Dónde te conectas físicamente?**  
              En la centralización de contadores del garaje, pero instalando un **contador nuevo e independiente** tramitado y contratado con la distribuidora eléctrica (Iberdrola, Endesa, etc.).
            
            * **💡 ¿Cuándo se utiliza?**
              1. El cliente compró o alquiló la plaza en ese garaje, pero **vive en otra calle o en otro edificio** (no tiene piso en esa finca de donde derivar la corriente).
              2. Es una empresa, autónomo o vehículo de renting que necesita que la factura del coche vaya a nombre societario separada de la vivienda particular.
            
            * **👎 Desventaja para el cliente:**
              * Tiene que pagar el **término fijo de potencia de un segundo contrato de luz** todos los meses (unos 15 € a 25 € fijos al mes solo por tener el contrato dado de alta, cargue o no cargue el vehículo).
            * **📏 Caída de tensión máxima permitida:** **1,0%**.
            """)

        with tab_e1:
            st.markdown("""
            ### 👥 ESQUEMA 1: Colectivo Troncal con Contador Principal
            > **Un único contador principal en cabecera para todos los coches del garaje comunitario.**

            * **📍 ¿Dónde te conectas físicamente?**  
              La comunidad de propietarios o una empresa gestora de carga (CPO) contrata un suministro general de gran potencia. Se instala una bandeja metálica troncal por todo el garaje. Cada vecino que quiera recargar se deriva de esa bandeja y se le monta un contador secundario homologado MID en su plaza para refacturar lo que consume.
            
            * **💡 ¿Cuándo se utiliza?**  
              En **edificios de nueva construcción**, parkings públicos de rotación, centros comerciales o flotas de empresa.
            * **⚙️ Requisito indispensable:** Sistema de Protección de Línea (SPL) centralizado para repartir dinámicamente la potencia entre todos los coches conectados.
            """)

        with tab_e3b:
            st.markdown("""
            ### 🔌 ESQUEMA 3b: Contador en Plaza de Aparcamiento o Exterior
            > **Contador exclusivo situado en la propia plaza o en fachada exterior.**

            * **📍 ¿Dónde te conectas físicamente?**  
              En una Caja de Protección y Medida (CPM) instalada en la pared exterior del parking o en un monolito al aire libre.
            
            * **💡 ¿Cuándo se utiliza?**  
              En aparcamientos en superficie o descubiertos donde no hay ningún portal ni cuarto de contadores centralizado cerca.
            """)

        with tab_resumen:
            st.markdown("""
            | Esquema | Origen Físico de la Conexión | ¿Segundo Contrato / CUPS? | Límite Caída Tensión (ΔV) | ¿Cuándo debes elegirlo en la calle? |
            | :--- | :--- | :---: | :---: | :--- |
            | **⭐ Esquema 2 (Por Defecto)** | Salida del contador del piso en centralización | ❌ NO (Misma factura del piso) | **1,0%** | **Garaje comunitario en el mismo edificio que la vivienda (El 90% de los casos)** |
            | **🏡 Esquema 4a / 4b** | Cuadro General CGMP de la vivienda | ❌ NO (Misma factura del piso) | **1,5%** | **Chalets, adosados y viviendas unifamiliares con garaje privado** |
            | **🏢 Esquema 3a** | Centralización (Módulo de contador nuevo) |  SÍ (Contrato y término fijo nuevo) | **1,0%** | **Cliente que vive en otro edificio / Factura de empresa separada** |
            | **👥 Esquema 1** | Cuadro general exclusivo de recarga colectiva |  SÍ (Contador comunitario CPO) | **1,0%** | **Edificios nuevos, parkings públicos y flotas de empresa** |
            | **🔌 Esquema 3b** | Caja exterior CPM junto a la plaza |  SÍ (Acometida exterior nueva) | **1,0%** | **Parkings al aire libre / Suministros en vía pública** |
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
    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🚗 SECCIÓN 1: Selección del Origen de la Línea y Parámetros del Wallbox (ITC-BT-52)</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        # 1. Selector de Esquema en Origen (100% visible, claro y con Esquema 2 por defecto)
        st.markdown("##### 🔌 1. Elige el Origen de la Línea (Esquema ITC-BT-52):")
        
        opciones_esquemas_map = {
            "Esquema 2": "⭐ ESQUEMA 2: Contador común de la vivienda (Garaje comunitario en mismo edificio) - RECOMENDADO (90% de los casos)",
            "Esquema 4a": "🏡 ESQUEMA 4a/4b: Directo desde el Cuadro CGMP (Chalets, adosados y viviendas unifamiliares)",
            "Esquema 3a": "🏢 ESQUEMA 3a: Contador nuevo exclusivo en centralización (El cliente no vive en este edificio o quiere factura separada)",
            "Esquema 1": "👥 ESQUEMA 1: Colectivo comunitario con contador principal (Parkings nuevos o empresas con gestor CPO)",
            "Esquema 3b": "🔌 ESQUEMA 3b: Contador exclusivo en exterior / plaza (Parkings al aire libre sin cuarto de contadores)"
        }
        
        # Limpieza de claves obsoletas y forzar Esquema 2 por defecto
        val_actual = st.session_state.get("irve_esquema_sel_key")
        if not val_actual or val_actual not in opciones_esquemas_map:
            st.session_state["irve_esquema_sel_key"] = "Esquema 2"
            val_actual = "Esquema 2"

        lista_keys = list(opciones_esquemas_map.keys())
        idx_actual = lista_keys.index(st.session_state["irve_esquema_sel_key"])

        esq_key_sel = st.radio(
            "Selecciona la situación real de tu cliente en la obra:",
            options=lista_keys,
            format_func=lambda k: opciones_esquemas_map[k],
            index=idx_actual,
            key="irve_esquema_sel_key"
        )
        
        info_esq = ESQUEMAS_IRVE_INFO.get(esq_key_sel, ESQUEMAS_IRVE_INFO["Esquema 2"])
        
        # Ficha Explicativa Completa y Siempre Visible del Esquema Seleccionado
        st.markdown(f"""
        <div style="background: #f0f9ff; border: 2px solid #0284c7; border-radius: 8px; padding: 14px 16px; margin: 10px 0 16px 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap;">
                <b style="color: #0369a1; font-size: 15px;">📋 FICHA TÉCNICA DEL ORIGEN: {info_esq['nombre'].upper()}</b>
                <span style="background: #0284c7; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11.5px; font-weight: bold;">
                    Límite Caída Tensión: {info_esq['limite_cdt']}%
                </span>
            </div>
            <div style="font-size: 13px; color: #1e293b; line-height: 1.5;">
                <p style="margin: 4px 0;"><b>📍 ¿Dónde conectar los cables en la obra?</b><br/>
                {info_esq['origen']}.</p>
                <p style="margin: 4px 0;"><b>💡 ¿Por qué debes elegir este esquema?</b><br/>
                {info_esq['ventajas']}</p>
                <p style="margin: 4px 0;"><b>🛡️ Protecciones y Requisitos:</b><br/>
                {info_esq['requisitos']}</p>
                <p style="margin: 4px 0; color: #047857;"><b>📜 Permiso Comunidad de Propietarios:</b><br/>
                {'Conforme al <b>Art. 17.5 de la Ley de Propiedad Horizontal</b>, solo requiere <b>comunicación previa por escrito</b> con 30 días de antelación. <b>¡No requiere votación ni aprobación en junta!</b>' if esq_key_sel == 'Esquema 2' else 'Instalación dentro de la propiedad privada sin trámites comunitarios.' if esq_key_sel == 'Esquema 4a' else 'Requiere solicitud de nuevo punto de suministro (CUPS) a la distribuidora eléctrica.'}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### ⚡ 2. Parámetros Eléctricos del Circuito:")
        c1_i, c2_i = st.columns([1, 1])
        with c1_i:
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
                p_cargador_val = st.number_input("Introduce Potencia del Wallbox (W):", value=st.session_state.get("irve_custom_w", 7360.0), step=250.0, key="irve_custom_w")
            else:
                p_cargador_val = float(irve_pot.split(" ")[0].replace(".", ""))

            irve_long = st.number_input("Longitud del cable hasta la plaza de garaje (m):", value=st.session_state.get("irve_long", 25.0), min_value=1.0, max_value=500.0, step=1.0, key="irve_long")

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
            
            st.info("⚡ **Sistema de Balanceo Inteligente (SPL):** Recomendado siempre para modular la carga en tiempo real con el consumo de la vivienda sin tener que subir el término de potencia contratada.")

    # =========================================================================
    # MOTOR DE CÁLCULO REGLAMENTARIO ITC-BT-52
    # =========================================================================
    es_trif_irve = "Trifásico" in tipo_red_irve
    v_t_irve = 400.0 if es_trif_irve else 230.0
    cos_phi_irve = 1.0 # Régimen de carga resistiva/electrónica factor unidad
    
    # Intensidad de diseño Ib
    ib_irve = rebt.calcular_intensidad_diseno(p_cargador_val, v_t_irve, cos_phi_irve, es_trif_irve)
    
    # Límite de caída de tensión según esquema (1.0% en Esquema 1, 2, 3a, 3b / 1.5% en Esquema 4a/4b)
    info_esq_actual = ESQUEMAS_IRVE_INFO.get(esq_key_sel, ESQUEMAS_IRVE_INFO["Esquema 2"])
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
