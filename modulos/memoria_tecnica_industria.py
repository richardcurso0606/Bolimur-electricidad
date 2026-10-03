# -*- coding: utf-8 -*-
"""
Módulo Oficial de Memoria Técnica de Diseño (MTD) para la Dirección General de Energía
y Actividad Industrial y Minera de la Región de Murcia (DGEAIM - Código Provincial 30)
Permite el llenado profesional y el auto-rellenado inteligente a partir de los cálculos REBT
para generar el documento oficial reglamentario para su tramitación telemática.
"""

import streamlit as st
import datetime
import math
from modulos import rebt_tablas as rebt
from modulos import pdf_memoria_tecnica
from modulos import db_manager, auth_manager

MUNICIPIOS_MURCIA_OFICIALES = [
    "Murcia (Capital / Pedanías)", "Cartagena", "Lorca", "Molina de Segura", 
    "Alcantarilla", "Torre Pacheco", "Águilas", "Cieza", "Yecla", 
    "San Javier", "Mazarrón", "Totana", "Caravaca de la Cruz", "Jumilla",
    "San Pedro del Pinatar", "Las Torres de Cotillas", "Alhama de Murcia",
    "Archena", "Fuente Álamo", "Santomera", "Puerto Lumbreras", "Abarán",
    "Cehegín", "Bullas", "Beniel", "Calasparra", "Fortuna", "Alguazas",
    "Moratalla", "Lorquí", "Abanilla", "Blanca", "Librilla", "Pliego",
    "Villanueva del Río Segura", "Campos del Río", "Ricote", "Ulea", "Ojós"
]

def cargar_plantilla_por_tipo(tipo: str):
    """
    Rellena automáticamente los parámetros técnicos y circuitos según el tipo de instalación reglamentaria.
    """
    if "IRVE" in tipo or "Recarga" in tipo or "Vehículo" in tipo:
        st.session_state["mtd_pot_inst"] = 7360.0
        st.session_state["mtd_pot_max"] = 7360.0
        st.session_state["mtd_tension"] = "Monofásico (230 V)"
        st.session_state["mtd_origen"] = "Centralización de Contadores (Esquema 2)"
        st.session_state["mtd_di_cable"] = "3G6 mm² Cu RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"
        st.session_state["mtd_di_tubo"] = "Tubo M32 libre de halógenos (IK08)"
        st.session_state["mtd_di_long"] = 25.0
        st.session_state["mtd_di_cdt"] = 0.86
        st.session_state["mtd_iga_amp"] = 32
        st.session_state["mtd_dif_txt"] = "Diferencial 2P 40A / 30mA Clase A con detección DC 6mA (IEC 62955)"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "Línea Específica IRVE (Wallbox)", "potencia": 7360, "pia": 32, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 25, "cdt": 0.86, "norma": "ITC-BT-52"}
        ]

    elif "Vivienda" in tipo or "Residencial" in tipo:
        st.session_state["mtd_pot_inst"] = 5750.0
        st.session_state["mtd_pot_max"] = 5750.0
        st.session_state["mtd_tension"] = "Monofásico (230 V)"
        st.session_state["mtd_origen"] = "Derivación Individual desde Centralización (ITC-BT-15)"
        st.session_state["mtd_di_cable"] = "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"
        st.session_state["mtd_di_tubo"] = "Tubo M32 libre de halógenos (ITC-BT-15)"
        st.session_state["mtd_di_long"] = 15.0
        st.session_state["mtd_di_cdt"] = 0.72
        st.session_state["mtd_iga_amp"] = 25
        st.session_state["mtd_dif_txt"] = "Interruptor Diferencial 2P 40A / 30mA Clase A / Superinmunizado"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora / Termo", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Auxiliares", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"}
        ]

    elif "Local" in tipo or "Comercial" in tipo or "Nave" in tipo:
        st.session_state["mtd_pot_inst"] = 11500.0
        st.session_state["mtd_pot_max"] = 14490.0
        st.session_state["mtd_tension"] = "Trifásico (400 V)"
        st.session_state["mtd_origen"] = "Línea General de Alimentación (LGA / CPM)"
        st.session_state["mtd_di_cable"] = "4x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV"
        st.session_state["mtd_di_tubo"] = "Tubo M40 libre de halógenos"
        st.session_state["mtd_di_long"] = 20.0
        st.session_state["mtd_di_cdt"] = 0.65
        st.session_state["mtd_iga_amp"] = 40
        st.session_state["mtd_dif_txt"] = "Diferencial Tetrapolar 4P 40A / 30mA Clase A / Superinmunizado"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "C1 - Alumbrado Comercial", "potencia": 3000, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 22, "cdt": 1.10, "norma": "ITC-BT-28"},
            {"nombre": "C2 - Alumbrado Emergencia", "potencia": 500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 30, "cdt": 0.45, "norma": "ITC-BT-28"},
            {"nombre": "C3 - Tomas Fuerza General", "potencia": 4000, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M25", "longitud": 18, "cdt": 1.12, "norma": "ITC-BT-28"},
            {"nombre": "C4 - Climatización / Bomba Calor", "potencia": 6000, "pia": 25, "seccion": "4x6.0+TT6.0", "tubo": "M32", "longitud": 15, "cdt": 0.85, "norma": "ITC-BT-28"}
        ]

def renderizar():
    st.markdown("""
    <style>
    /* Ajustes visuales profesionales para Memoria Técnica */
    div[data-baseweb="select"] { width: 100% !important; }
    div[data-baseweb="select"] * { white-space: normal !important; word-break: break-word !important; }
    </style>
    """, unsafe_allow_html=True)

    col_tit_mtd, col_b1_m = st.columns([4, 1])
    with col_tit_mtd:
        st.title("🏛️ Memoria Técnica de Diseño (MTD) Oficial - DGEAIM Región de Murcia")
        st.caption("Formulario oficial normalizado para tramitación de instalaciones eléctricas en Baja Tensión ante la Dirección General de Energía (Código 30 - Murcia).")
    with col_b1_m:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Restablecer MTD", key="btn_reset_mtd_mod", use_container_width=True):
            st.session_state.pop("mtd_circuitos", None)
            st.rerun()

    # Obtener datos de usuario autenticado
    user_auth = auth_manager.obtener_usuario_actual() or {
        "id": 1,
        "nombre_instalador": "Richard Orlando Choque Tejerina",
        "nombre_empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
        "num_licencia_rebt": "REBT-30/15892",
        "localidad": "Murcia, España",
        "telefono": "+34 600 000 000"
    }

    # =========================================================================
    # BARRA SUPERIOR: SELECCIÓN DE CLIENTE Y TIPO DE INSTALACIÓN REGLAMENTARIA
    # =========================================================================
    st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">👤 1. Expediente, Cliente y Tipo de Instalación REBT</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        col_t1, col_t2, col_t3 = st.columns([2.5, 2.5, 2])
        
        with col_t1:
            tipo_inst_sel = st.selectbox(
                "Tipo de Instalación Reglamentaria (REBT):",
                [
                    "🚗 Recarga Vehículo Eléctrico IRVE (ITC-BT-52)",
                    "🏡 Vivienda Unifamiliar / Piso Residencial (ITC-BT-25)",
                    "🏢 Local Comercial / Nave Industrial (ITC-BT-28)",
                    "⚡ Línea General de Alimentación LGA (ITC-BT-14)",
                    "🔌 Derivación Individual DI (ITC-BT-15)"
                ],
                index=0,
                key="mtd_tipo_inst_sel"
            )

        with col_t2:
            # Lista de clientes de CRM
            clientes = db_manager.listar_clientes(user_auth["id"])
            if not clientes:
                st.caption("💡 *No hay clientes registrados en CRM.*")
                cli_sel_id = None
                cli_obj = {}
            else:
                nombres_cli = {c["id"]: f"👤 {c['nombre_completo']} ({c.get('localidad', 'Murcia')})" for c in clientes}
                cli_sel_id = st.selectbox(
                    "Asignar Ficha de Cliente (CRM):",
                    options=list(nombres_cli.keys()),
                    format_func=lambda x: nombres_cli[x],
                    index=0,
                    key="mtd_sel_cliente_crm"
                )
                cli_obj = db_manager.obtener_cliente_por_id(cli_sel_id, user_auth["id"]) or {}

        with col_t3:
            st.write("")
            if st.button("⚡ Auto-Rellenar Plantilla", type="primary", use_container_width=True):
                cargar_plantilla_por_tipo(tipo_inst_sel)
                st.success("✅ ¡Datos técnicos y circuitos auto-rellenados automáticamente!")
                st.rerun()

    # Inicialización por defecto si no existen en session_state
    if "mtd_circuitos" not in st.session_state:
        cargar_plantilla_por_tipo(tipo_inst_sel)

    # =========================================================================
    # FORMULARIO TÉCNICO OFICIAL DGEAIM REGIÓN DE MURCIA (CÓDIGO 30)
    # =========================================================================
    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🏛️ 2. Formulario Oficial Normalizado de la Memoria Técnica de Diseño (DGEAIM Murcia)</h4></div>', unsafe_allow_html=True)
    
    tab_f1, tab_f2, tab_f3, tab_f4, tab_f5, tab_f6 = st.tabs([
        "📍 Titular y Emplazamiento",
        "👷 Empresa e Instalador",
        "⚡ Suministro y Potencias",
        "🛡️ Cuadro CGMP y Protecciones",
        "📋 Circuitos Derivados",
        "🧪 Protocolo Ensayos (BT-05)"
    ])

    # --- TAB 1: TITULAR Y EMPLAZAMIENTO ---
    with tab_f1:
        st.markdown("##### 📍 Bloque I: Datos del Titular y Emplazamiento en la Región de Murcia:")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            tit_nombre = st.text_input("Nombre / Razón Social del Titular:", value=cli_obj.get("nombre_completo", "Propietario / Titular"), key="mtd_in_tit_nom")
            tit_nif = st.text_input("NIF / CIF del Titular:", value=cli_obj.get("nif_cif", "12345678Z"), key="mtd_in_tit_nif")
            tit_tel = st.text_input("Teléfono del Titular:", value=cli_obj.get("telefono", "+34 600 000 000"), key="mtd_in_tit_tel")
            tit_email = st.text_input("Correo Electrónico:", value=cli_obj.get("email", "cliente@ejemplo.com"), key="mtd_in_tit_email")
        with col_e2:
            emp_dir = st.text_input("Dirección de la Instalación / Plaza:", value=cli_obj.get("direccion", "C/ Mayor, nº 45, Plaza Garaje nº 12"), key="mtd_in_emp_dir")
            emp_cp = st.text_input("Código Postal:", value=cli_obj.get("codigo_postal", "30001"), key="mtd_in_emp_cp")
            emp_muni = st.selectbox("Municipio de la Región de Murcia:", MUNICIPIOS_MURCIA_OFICIALES, index=0, key="mtd_in_emp_muni")
            emp_cups = st.text_input("Código CUPS / Ref. Catastral:", value=cli_obj.get("cups", "ES0021000000000000XX"), key="mtd_in_emp_cups")
            emp_uso = st.text_input("Uso del Inmueble / Local:", value="Garaje Comunitario / Residencial", key="mtd_in_emp_uso")

    # --- TAB 2: EMPRESA E INSTALADOR ---
    with tab_f2:
        st.markdown("##### 👷 Bloque II: Datos de la Empresa Instaladora Habilitada y Técnico (Provincia 30 - Murcia):")
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            inst_empresa = st.text_input("Razón Social Empresa Instaladora:", value=user_auth.get("nombre_empresa", "BOLIMUR INSTALACIONES Y REFORMAS"), key="mtd_in_inst_emp")
            inst_cif = st.text_input("CIF Empresa:", value="B-73123456", key="mtd_in_inst_cif")
            inst_rii = st.text_input("Nº Registro Integrado Industrial (RII Murcia):", value="RII-30/08492", key="mtd_in_inst_rii")
        with col_i2:
            inst_nom = st.text_input("Nombre del Instalador Habilitado:", value=user_auth.get("nombre_instalador", "Richard Orlando Choque Tejerina"), key="mtd_in_inst_nom")
            inst_lic = st.text_input("Nº Carnet / Certificado Cualificación REBT:", value=user_auth.get("num_licencia_rebt", "REBT-30/15892"), key="mtd_in_inst_lic")
            inst_nif = st.text_input("NIF del Instalador:", value="48500000A", key="mtd_in_inst_nif")

    # --- TAB 3: SUMINISTRO Y POTENCIAS ---
    with tab_f3:
        st.markdown("##### ⚡ Bloque III: Suministro, Potencia de Cálculo y Derivación Individual:")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sum_pot_inst = st.number_input("Potencia de Diseño / Prevista (W):", value=float(st.session_state.get("mtd_pot_inst", 7360.0)), step=250.0, key="mtd_in_pot_inst")
            sum_pot_max = st.number_input("Potencia Máxima Admisible de la Línea (W):", value=float(st.session_state.get("mtd_pot_max", 7360.0)), step=250.0, key="mtd_in_pot_max")
            sum_tension = st.selectbox("Tensión Nominal y Fases:", ["Monofásico (230 V) - 50 Hz", "Trifásico (400 V) - 50 Hz"], index=0, key="mtd_in_tension")
            sum_origen = st.text_input("Origen del Suministro:", value=st.session_state.get("mtd_origen", "Centralización de Contadores (Esquema 2)"), key="mtd_in_origen")
        with col_s2:
            sum_di_cable = st.text_input("Conductor de Alimentación / DI:", value=st.session_state.get("mtd_di_cable", "3G6 mm² Cu RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"), key="mtd_in_di_cable")
            sum_di_tubo = st.text_input("Tubo Protector:", value=st.session_state.get("mtd_di_tubo", "Tubo M32 libre de halógenos (IK08)"), key="mtd_in_di_tubo")
            sum_di_long = st.number_input("Longitud de la Línea (m):", value=float(st.session_state.get("mtd_di_long", 25.0)), step=1.0, key="mtd_in_di_long")
            sum_di_cdt = st.number_input("Caída de Tensión Calculada (%):", value=float(st.session_state.get("mtd_di_cdt", 0.86)), step=0.05, key="mtd_in_di_cdt")
            sum_grado = st.selectbox("Grado de Electrificación / Uso:", ["Básica", "Elevada", "Específica IRVE (ITC-BT-52)", "Comercial / Servicios"], index=2, key="mtd_in_grado")

    # --- TAB 4: CUADRO CGMP Y PROTECCIONES ---
    with tab_f4:
        st.markdown("##### 🛡️ Bloque IV: Dispositivos Generales de Mando y Protección (CGMP):")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            prot_iga = st.number_input("Calibre del Interruptor General (IGA / PIA) (A):", value=int(st.session_state.get("mtd_iga_amp", 32)), step=1, key="mtd_in_iga")
            prot_curva = st.selectbox("Curva de Disparo IGA:", ["Curva C (General)", "Curva B", "Curva D"], index=0, key="mtd_in_curva")
            prot_icn = st.number_input("Poder de Corte Icn (kA):", value=6.0, step=1.0, key="mtd_in_icn")
            prot_dif = st.text_input("Interruptor Diferencial Principal:", value=st.session_state.get("mtd_dif_txt", "Diferencial 2P 40A / 30mA Clase A con detección DC 6mA (IEC 62955)"), key="mtd_in_dif")
        with col_p2:
            prot_vtp = st.text_input("Protección Sobretensiones:", value="Permanentes (POP/VTP) + Transitorias Tipo 2 (DPS/VSP) con bobina de disparo", key="mtd_in_vtp")
            prot_tierra = st.text_input("Puesta a Tierra (PE):", value="Conductor PE 1x6 mm² Cu | Resistencia bucle tierra Rt ≤ 15 Ω", key="mtd_in_tierra")
            prot_spl = st.text_input("Sistema de Balanceo de Carga (SPL):", value="Sensor toroidal CT para modulación dinámica en tiempo real", key="mtd_in_spl")

    # --- TAB 5: CIRCUITOS DERIVADOS ---
    with tab_f5:
        st.markdown("##### 📋 Bloque V: Cuadro de Circuitos Interiores / Terminales Derivados:")
        
        circs_actuales = st.session_state.get("mtd_circuitos", [])
        
        # Mostrar tabla de circuitos actuales
        if circs_actuales:
            st.dataframe(circs_actuales, use_container_width=True)

        with st.expander("➕ Añadir / Modificar Circuito Terminal:", expanded=False):
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1:
                nc_nom = st.text_input("Nombre Circuito:", "C13 - Recarga IRVE", key="mtd_in_nc_nom")
                nc_pot = st.number_input("Potencia (W):", value=7360, step=250, key="mtd_in_nc_pot")
            with col_c2:
                nc_pia = st.number_input("PIA (A):", value=32, step=1, key="mtd_in_nc_pia")
                nc_sec = st.text_input("Conductor:", "2x6.0+TT6.0", key="mtd_in_nc_sec")
            with col_c3:
                nc_tubo = st.text_input("Tubo:", "M32", key="mtd_in_nc_tubo")
                nc_long = st.number_input("Longitud (m):", value=25, step=1, key="mtd_in_nc_long")
            with col_c4:
                nc_cdt = st.number_input("ΔV (%):", value=0.86, step=0.05, key="mtd_in_nc_cdt")
                nc_norma = st.text_input("Norma ITC:", "ITC-BT-52", key="mtd_in_nc_norma")
                
            if st.button("➕ Insertar Circuito a la Lista", key="btn_add_circ_mtd"):
                st.session_state["mtd_circuitos"].append({
                    "nombre": nc_nom, "potencia": nc_pot, "pia": nc_pia,
                    "seccion": nc_sec, "tubo": nc_tubo, "longitud": nc_long,
                    "cdt": nc_cdt, "norma": nc_norma
                })
                st.success("Circuito añadido.")
                st.rerun()

    # --- TAB 6: PROTOCOLO DE ENSAYOS (ITC-BT-05) ---
    with tab_f6:
        st.markdown("##### 🧪 Bloque VI: Protocolo de Ensayos y Verificaciones Previas (ITC-BT-05 Murcia):")
        st.markdown("""
        Valores de verificación obligatorios según el REBT y las normas técnicas de la Región de Murcia:
        """)
        col_t_1, col_t_2 = st.columns(2)
        with col_t_1:
            st.info("""
            * **Continuidad de conductores PE:** $\le 0,5\ \Omega$ (Medido: **0,11 Ω** - Conforme)
            * **Resistencia de aislamiento a 500 Vcc:** $\ge 1,0\ \text{M}\Omega$ (Medido: **> 100 MΩ** - Conforme)
            * **Resistencia de bucle de tierra:** $R_t \cdot I_{\Delta n} \le 24\text{ V}$ (Medido: **11,8 Ω** - Conforme)
            """)
        with col_t_2:
            st.info("""
            * **Sensibilidad del Diferencial:** $I_{\Delta n} \le 30\text{ mA}$ (Medido: **22 mA** - Conforme)
            * **Tiempo de Disparo Diferencial:** $t \le 300\text{ ms}$ (Medido: **26 ms** - Conforme)
            * **Protector de Sobretensiones:** VSP + VTP verificado con disparo correcto.
            """)

    # =========================================================================
    # 3. GENERACIÓN DEL DOCUMENTO PDF OFICIAL DGEAIM REGIÓN DE MURCIA
    # =========================================================================
    st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">🖨️ 3. Generación del Documento Oficial MTD (DGEAIM Región de Murcia)</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        col_g1, col_g2 = st.columns([3, 2])
        with col_g1:
            exp_in = st.text_input("Nº de Referencia / Expediente Oficial:", value=f"EXP-MTD-{emp_muni[:3].upper()}-2026-01", key="mtd_exp_final")
        with col_g2:
            st.write("")
            btn_generar_mtd = st.button("📄 Generar Memoria Técnica Oficial (PDF)", type="primary", use_container_width=True)

        datos_para_pdf = {
            "tipo_instalacion": tipo_inst_sel,
            "expediente": exp_in,
            "fecha": datetime.date.today().strftime("%d/%m/%Y"),
            "titular": {
                "nombre": tit_nombre,
                "nif": tit_nif,
                "telefono": tit_tel,
                "email": tit_email
            },
            "emplazamiento": {
                "direccion": emp_dir,
                "cp": emp_cp,
                "municipio": emp_muni,
                "cups": emp_cups,
                "uso": emp_uso
            },
            "instalador": {
                "empresa": inst_empresa,
                "cif": inst_cif,
                "nombre": inst_nom,
                "licencia": inst_lic,
                "nif": inst_nif,
                "registro_rii": inst_rii,
                "telefono": user_auth.get("telefono", "+34 600 000 000")
            },
            "suministro": {
                "potencia_instalada_w": sum_pot_inst,
                "potencia_max_admisible_w": sum_pot_max,
                "tension": sum_tension,
                "origen": sum_origen,
                "di_cable": sum_di_cable,
                "di_tubo": sum_di_tubo,
                "di_long_m": sum_di_long,
                "di_cdt_pct": sum_di_cdt,
                "grado_electrif": sum_grado
            },
            "protecciones": {
                "iga_amperaje": prot_iga,
                "iga_curva": prot_curva,
                "iga_icn_ka": prot_icn,
                "diferenciales": prot_dif,
                "sobretensiones": prot_vtp,
                "puesta_a_tierra": prot_tierra
            },
            "circuitos": st.session_state.get("mtd_circuitos", [])
        }

        try:
            pdf_bytes_mtd = pdf_memoria_tecnica.generar_pdf_mtd_industria_murcia(datos_para_pdf)
            from modulos import visor_pdf
            visor_pdf.mostrar_visor_pdf(
                pdf_bytes=pdf_bytes_mtd,
                nombre_archivo=f"MTD_Oficial_DGEAIM_Murcia_{exp_in}.pdf",
                label_boton="📥 Descargar Memoria Técnica Oficial MTD (PDF para Industria Murcia)"
            )
        except Exception as err:
            st.error(f"⚠️ Error al generar el PDF de la Memoria Técnica: {err}")
