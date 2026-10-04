# -*- coding: utf-8 -*-
"""
Módulo Oficial de Memoria Técnica de Diseño (MTD) para la Dirección General de Energía
y Actividad Industrial y Minera de la Región de Murcia (DGEAIM - Código Provincial 30)
Permite el llenado profesional, el auto-rellenado inteligente a partir de cálculos REBT
y el guardado/recuperación persistente vinculado a las fichas de clientes en el CRM.
"""

import streamlit as st
import datetime
import math
import json
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
        st.session_state["mtd_in_pot_inst"] = 7360.0
        st.session_state["mtd_in_pot_max"] = 7360.0
        st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Centralización de Contadores (Esquema 2)"
        st.session_state["mtd_in_di_cable"] = "3G6 mm² Cu RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"
        st.session_state["mtd_in_di_tubo"] = "Tubo M32 libre de halógenos (IK08)"
        st.session_state["mtd_in_di_long"] = 25.0
        st.session_state["mtd_in_di_cdt"] = 0.86
        st.session_state["mtd_in_grado"] = "Específica IRVE (ITC-BT-52)"
        st.session_state["mtd_in_iga"] = 32
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 6.0
        st.session_state["mtd_in_dif"] = "Diferencial 2P 40A / 30mA Clase A con detección DC 6mA (IEC 62955)"
        st.session_state["mtd_in_vtp"] = "Permanentes (POP/VTP) + Transitorias Tipo 2 (DPS/VSP) con bobina de disparo"
        st.session_state["mtd_in_tierra"] = "Conductor PE 1x6 mm² Cu | Resistencia bucle tierra Rt ≤ 15 Ω"
        st.session_state["mtd_in_spl"] = "Sensor toroidal CT para modulación dinámica en tiempo real"
        st.session_state["mtd_in_emp_uso"] = "Garaje Comunitario / Punto de Recarga VE"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "Línea Específica IRVE (Wallbox)", "potencia": 7360, "pia": 32, "seccion": "2x6.0+TT6.0", "tubo": "M32", "longitud": 25, "cdt": 0.86, "norma": "ITC-BT-52"}
        ]

    elif "Vivienda" in tipo or "Residencial" in tipo:
        st.session_state["mtd_in_pot_inst"] = 5750.0
        st.session_state["mtd_in_pot_max"] = 5750.0
        st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Derivación Individual desde Centralización (ITC-BT-15)"
        st.session_state["mtd_in_di_cable"] = "2x10 mm² Cu + TT 1x10 mm² RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"
        st.session_state["mtd_in_di_tubo"] = "Tubo M32 libre de halógenos (ITC-BT-15)"
        st.session_state["mtd_in_di_long"] = 15.0
        st.session_state["mtd_in_di_cdt"] = 0.72
        st.session_state["mtd_in_grado"] = "Básica"
        st.session_state["mtd_in_iga"] = 25
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 6.0
        st.session_state["mtd_in_dif"] = "Interruptor Diferencial 2P 40A / 30mA Clase A / Superinmunizado"
        st.session_state["mtd_in_vtp"] = "Permanentes (VTP) + Transitorias Tipo 2 con reconexión"
        st.session_state["mtd_in_tierra"] = "Conductor PE 1x10 mm² Cu | Picas en anillo Rt ≤ 15 Ω"
        st.session_state["mtd_in_spl"] = "No aplica"
        st.session_state["mtd_in_emp_uso"] = "Vivienda Residencial Unifamiliar"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "C1 - Alumbrado General", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas de Uso General", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina / Horno", "potencia": 5400, "pia": 25, "seccion": "2x6.0+TT6.0", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C4 - Lavadora / Termo", "potencia": 3450, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M20", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"},
            {"nombre": "C5 - Baños y Auxiliares", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 14, "cdt": 0.98, "norma": "ITC-BT-25"}
        ]

    elif "Local" in tipo or "Comercial" in tipo or "Nave" in tipo:
        st.session_state["mtd_in_pot_inst"] = 11500.0
        st.session_state["mtd_in_pot_max"] = 14490.0
        st.session_state["mtd_in_tension"] = "Trifásico (400 V) - 50 Hz"
        st.session_state["mtd_in_origen"] = "Línea General de Alimentación (LGA / CPM)"
        st.session_state["mtd_in_di_cable"] = "4x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV"
        st.session_state["mtd_in_di_tubo"] = "Tubo M40 libre de halógenos"
        st.session_state["mtd_in_di_long"] = 20.0
        st.session_state["mtd_in_di_cdt"] = 0.65
        st.session_state["mtd_in_grado"] = "Comercial / Servicios"
        st.session_state["mtd_in_iga"] = 40
        st.session_state["mtd_in_curva"] = "Curva C (General)"
        st.session_state["mtd_in_icn"] = 10.0
        st.session_state["mtd_in_dif"] = "Diferencial Tetrapolar 4P 40A / 30mA Clase A / Superinmunizado"
        st.session_state["mtd_in_vtp"] = "Permanentes + Transitorias Tipo 2 con bobina de emisión"
        st.session_state["mtd_in_tierra"] = "Conductor PE 1x16 mm² Cu | Anillo cimentación Rt ≤ 10 Ω"
        st.session_state["mtd_in_spl"] = "No aplica"
        st.session_state["mtd_in_emp_uso"] = "Local Comercial / Actividad Terciaria"
        st.session_state["mtd_circuitos"] = [
            {"nombre": "C1 - Alumbrado Comercial", "potencia": 3000, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 22, "cdt": 1.10, "norma": "ITC-BT-28"},
            {"nombre": "C2 - Alumbrado Emergencia", "potencia": 500, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 30, "cdt": 0.45, "norma": "ITC-BT-28"},
            {"nombre": "C3 - Tomas Fuerza General", "potencia": 4000, "pia": 20, "seccion": "2x4.0+TT4.0", "tubo": "M25", "longitud": 18, "cdt": 1.12, "norma": "ITC-BT-28"},
            {"nombre": "C4 - Climatización / Bomba Calor", "potencia": 6000, "pia": 25, "seccion": "4x6.0+TT6.0", "tubo": "M32", "longitud": 15, "cdt": 0.85, "norma": "ITC-BT-28"}
        ]

def aplicar_datos_cliente_a_formulario(cli_obj: dict):
    """Vuelca los datos del cliente de CRM en los campos del formulario"""
    if not cli_obj:
        return
    st.session_state["mtd_in_tit_nom"] = cli_obj.get("nombre_completo", "")
    st.session_state["mtd_in_tit_nif"] = cli_obj.get("nif_cif", "")
    st.session_state["mtd_in_tit_tel"] = cli_obj.get("telefono", "")
    st.session_state["mtd_in_tit_email"] = cli_obj.get("email", "")
    st.session_state["mtd_in_emp_dir"] = cli_obj.get("direccion_suministro", cli_obj.get("direccion", ""))
    st.session_state["mtd_in_emp_cups"] = cli_obj.get("cups", "")
    
    loc = cli_obj.get("localidad", "Murcia")
    for m in MUNICIPIOS_MURCIA_OFICIALES:
        if m.lower() in loc.lower() or loc.lower() in m.lower():
            st.session_state["mtd_in_emp_muni"] = m
            break
    
    tipo_inm = cli_obj.get("tipo_inmueble", "")
    if tipo_inm:
        st.session_state["mtd_in_emp_uso"] = tipo_inm

def renderizar():
    st.markdown("""
    <style>
    div[data-baseweb="select"] { width: 100% !important; }
    div[data-baseweb="select"] * { white-space: normal !important; word-break: break-word !important; }
    </style>
    """, unsafe_allow_html=True)

    col_tit_mtd, col_b1_m = st.columns([4, 1])
    with col_tit_mtd:
        st.title("🏛️ Memoria Técnica de Diseño (MTD) Oficial - DGEAIM Región de Murcia")
        st.caption("Formulario oficial normalizado para tramitación telemática de instalaciones en Baja Tensión ante la Dirección General de Energía (Código Provincial 30 - Murcia).")
    with col_b1_m:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Restablecer MTD", key="btn_reset_mtd_mod", use_container_width=True):
            st.session_state.pop("mtd_circuitos", None)
            st.rerun()

    # Usuario autenticado
    user_auth = auth_manager.obtener_usuario_actual() or {
        "id": 1,
        "nombre_instalador": "Richard Orlando Choque Tejerina",
        "nombre_empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
        "num_licencia_rebt": "REBT-30/15892",
        "localidad": "Murcia, España",
        "telefono": "+34 600 000 000"
    }

    # =========================================================================
    # 1. EXPEDIENTE, CLIENTE (CRM) Y GUARDADO / CARGA DE MEMORIAS
    # =========================================================================
    st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">👤 1. Expediente, Cliente (CRM) y Gestión de Memorias Guardadas</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        col_t1, col_t2 = st.columns([1.5, 2.5])
        
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
            
            if st.button("⚡ Auto-Rellenar Plantilla Técnica", type="secondary", use_container_width=True):
                cargar_plantilla_por_tipo(tipo_inst_sel)
                st.success("✅ ¡Datos técnicos y circuitos auto-rellenados!")
                st.rerun()

        with col_t2:
            clientes = db_manager.listar_clientes(user_auth["id"])
            if not clientes:
                st.warning("⚠️ No hay clientes registrados en CRM. Puedes crear fichas en el módulo 'Gestión de Clientes'.")
                cli_sel_id = None
                cli_obj = {}
            else:
                nombres_cli = {c["id"]: f"👤 {c['nombre_completo']} - {c.get('nif_cif', '')} ({c.get('localidad', 'Murcia')})" for c in clientes}
                
                # Pre-seleccionar si ya viene en session
                idx_sel = 0
                if "cliente_activo_proyecto" in st.session_state and st.session_state["cliente_activo_proyecto"]:
                    c_act = st.session_state["cliente_activo_proyecto"]
                    if c_act.get("id") in nombres_cli:
                        idx_sel = list(nombres_cli.keys()).index(c_act["id"])

                cli_sel_id = st.selectbox(
                    "Cliente Asignado (CRM):",
                    options=list(nombres_cli.keys()),
                    format_func=lambda x: nombres_cli[x],
                    index=idx_sel,
                    key="mtd_sel_cliente_crm"
                )
                cli_obj = db_manager.obtener_cliente_por_id(cli_sel_id, user_auth["id"]) or {}

                # Acciones sobre el cliente seleccionado
                col_c_act1, col_c_act2 = st.columns(2)
                with col_c_act1:
                    if st.button("📋 Cargar Datos del Cliente al Formulario", use_container_width=True):
                        aplicar_datos_cliente_a_formulario(cli_obj)
                        st.success(f"✅ Datos de {cli_obj.get('nombre_completo')} volcados a la MTD.")
                        st.rerun()

                with col_c_act2:
                    # Comprobar si este cliente tiene MTDs guardadas
                    proyectos_mtd_cli = [
                        p for p in db_manager.listar_proyectos_por_cliente(cli_sel_id, user_auth["id"]) 
                        if "Memoria" in p.get("modulo", "") or "MTD" in p.get("modulo", "")
                    ]
                    if proyectos_mtd_cli:
                        nombres_projs = {p["id"]: f"📂 {p['nombre_proyecto']} ({p.get('fecha_guardado', '')[:10]})" for p in proyectos_mtd_cli}
                        sel_p_id = st.selectbox("MTDs Guardadas del Cliente:", options=list(nombres_projs.keys()), format_func=lambda x: nombres_projs[x], key="sel_mtd_p_cli")
                        if st.button("🚀 Cargar MTD Guardada", use_container_width=True):
                            p_datos = db_manager.cargar_proyecto_por_id(sel_p_id, user_auth["id"])
                            if p_datos and "datos" in p_datos:
                                for k, v in p_datos["datos"].items():
                                    st.session_state[k] = v
                                st.success(f"✅ ¡Memoria '{p_datos.get('nombre_proyecto')}' cargada con éxito!")
                                st.rerun()

    # Inicialización por defecto si no existen
    if "mtd_circuitos" not in st.session_state:
        cargar_plantilla_por_tipo(tipo_inst_sel)
        if cli_obj:
            aplicar_datos_cliente_a_formulario(cli_obj)

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
            tit_nombre = st.text_input("Nombre / Razón Social del Titular:", value=st.session_state.get("mtd_in_tit_nom", cli_obj.get("nombre_completo", "Propietario / Titular")), key="mtd_in_tit_nom")
            tit_nif = st.text_input("NIF / CIF del Titular:", value=st.session_state.get("mtd_in_tit_nif", cli_obj.get("nif_cif", "12345678Z")), key="mtd_in_tit_nif")
            tit_tel = st.text_input("Teléfono del Titular:", value=st.session_state.get("mtd_in_tit_tel", cli_obj.get("telefono", "+34 600 000 000")), key="mtd_in_tit_tel")
            tit_email = st.text_input("Correo Electrónico:", value=st.session_state.get("mtd_in_tit_email", cli_obj.get("email", "cliente@ejemplo.com")), key="mtd_in_tit_email")
        with col_e2:
            emp_dir = st.text_input("Dirección de la Instalación / Plaza:", value=st.session_state.get("mtd_in_emp_dir", cli_obj.get("direccion_suministro", "C/ Mayor, nº 45, Plaza Garaje nº 12")), key="mtd_in_emp_dir")
            emp_cp = st.text_input("Código Postal:", value=st.session_state.get("mtd_in_emp_cp", "30001"), key="mtd_in_emp_cp")
            
            # Buscar index de municipio
            muni_default = st.session_state.get("mtd_in_emp_muni", "Murcia (Capital / Pedanías)")
            idx_muni = MUNICIPIOS_MURCIA_OFICIALES.index(muni_default) if muni_default in MUNICIPIOS_MURCIA_OFICIALES else 0
            emp_muni = st.selectbox("Municipio de la Región de Murcia:", MUNICIPIOS_MURCIA_OFICIALES, index=idx_muni, key="mtd_in_emp_muni")
            
            emp_cups = st.text_input("Código CUPS / Ref. Catastral:", value=st.session_state.get("mtd_in_emp_cups", cli_obj.get("cups", "ES0021000000000000XX")), key="mtd_in_emp_cups")
            emp_uso = st.text_input("Uso del Inmueble / Local:", value=st.session_state.get("mtd_in_emp_uso", "Garaje Comunitario / Residencial"), key="mtd_in_emp_uso")

    # --- TAB 2: EMPRESA E INSTALADOR ---
    with tab_f2:
        st.markdown("##### 👷 Bloque II: Datos de la Empresa Instaladora Habilitada y Técnico (Provincia 30 - Murcia):")
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            inst_empresa = st.text_input("Razón Social Empresa Instaladora:", value=user_auth.get("nombre_empresa", "BOLIMUR INSTALACIONES Y REFORMAS"), key="mtd_in_inst_emp")
            inst_cif = st.text_input("CIF Empresa:", value=user_auth.get("nif_cif", "B-73123456"), key="mtd_in_inst_cif")
            inst_rii = st.text_input("Nº Registro Integrado Industrial (RII Murcia):", value=user_auth.get("registro_industrial", "RII-30/08492"), key="mtd_in_inst_rii")
        with col_i2:
            inst_nom = st.text_input("Nombre del Instalador Habilitado:", value=user_auth.get("nombre_instalador", "Richard Orlando Choque Tejerina"), key="mtd_in_inst_nom")
            inst_lic = st.text_input("Nº Carnet / Certificado Cualificación REBT:", value=user_auth.get("num_licencia_rebt", "REBT-30/15892"), key="mtd_in_inst_lic")
            inst_nif = st.text_input("NIF del Instalador:", value="48500000A", key="mtd_in_inst_nif")

    # --- TAB 3: SUMINISTRO Y POTENCIAS ---
    with tab_f3:
        st.markdown("##### ⚡ Bloque III: Suministro, Potencia de Cálculo y Derivación Individual:")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sum_pot_inst = st.number_input("Potencia de Diseño / Prevista (W):", value=float(st.session_state.get("mtd_in_pot_inst", 7360.0)), step=250.0, key="mtd_in_pot_inst")
            sum_pot_max = st.number_input("Potencia Máxima Admisible de la Línea (W):", value=float(st.session_state.get("mtd_in_pot_max", 7360.0)), step=250.0, key="mtd_in_pot_max")
            
            t_opts = ["Monofásico (230 V) - 50 Hz", "Trifásico (400 V) - 50 Hz"]
            t_def = st.session_state.get("mtd_in_tension", t_opts[0])
            idx_t = t_opts.index(t_def) if t_def in t_opts else 0
            sum_tension = st.selectbox("Tensión Nominal y Fases:", t_opts, index=idx_t, key="mtd_in_tension")
            sum_origen = st.text_input("Origen del Suministro:", value=st.session_state.get("mtd_in_origen", "Centralización de Contadores (Esquema 2)"), key="mtd_in_origen")
        with col_s2:
            sum_di_cable = st.text_input("Conductor de Alimentación / DI:", value=st.session_state.get("mtd_in_di_cable", "3G6 mm² Cu RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"), key="mtd_in_di_cable")
            sum_di_tubo = st.text_input("Tubo Protector:", value=st.session_state.get("mtd_in_di_tubo", "Tubo M32 libre de halógenos (IK08)"), key="mtd_in_di_tubo")
            sum_di_long = st.number_input("Longitud de la Línea (m):", value=float(st.session_state.get("mtd_in_di_long", 25.0)), step=1.0, key="mtd_in_di_long")
            sum_di_cdt = st.number_input("Caída de Tensión Calculada (%):", value=float(st.session_state.get("mtd_in_di_cdt", 0.86)), step=0.05, key="mtd_in_di_cdt")
            
            g_opts = ["Básica", "Elevada", "Específica IRVE (ITC-BT-52)", "Comercial / Servicios"]
            g_def = st.session_state.get("mtd_in_grado", g_opts[2])
            idx_g = g_opts.index(g_def) if g_def in g_opts else 0
            sum_grado = st.selectbox("Grado de Electrificación / Uso:", g_opts, index=idx_g, key="mtd_in_grado")

    # --- TAB 4: CUADRO CGMP Y PROTECCIONES ---
    with tab_f4:
        st.markdown("##### 🛡️ Bloque IV: Dispositivos Generales de Mando y Protección (CGMP):")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            prot_iga = st.number_input("Calibre del Interruptor General (IGA / PIA) (A):", value=int(st.session_state.get("mtd_in_iga", 32)), step=1, key="mtd_in_iga")
            
            c_opts = ["Curva C (General)", "Curva B", "Curva D"]
            c_def = st.session_state.get("mtd_in_curva", c_opts[0])
            idx_c = c_opts.index(c_def) if c_def in c_opts else 0
            prot_curva = st.selectbox("Curva de Disparo IGA:", c_opts, index=idx_c, key="mtd_in_curva")
            
            prot_icn = st.number_input("Poder de Corte Icn (kA):", value=float(st.session_state.get("mtd_in_icn", 6.0)), step=1.0, key="mtd_in_icn")
            prot_dif = st.text_input("Interruptor Diferencial Principal:", value=st.session_state.get("mtd_in_dif", "Diferencial 2P 40A / 30mA Clase A con detección DC 6mA (IEC 62955)"), key="mtd_in_dif")
        with col_p2:
            prot_vtp = st.text_input("Protección Sobretensiones:", value=st.session_state.get("mtd_in_vtp", "Permanentes (POP/VTP) + Transitorias Tipo 2 (DPS/VSP) con bobina de disparo"), key="mtd_in_vtp")
            prot_tierra = st.text_input("Puesta a Tierra (PE):", value=st.session_state.get("mtd_in_tierra", "Conductor PE 1x6 mm² Cu | Resistencia bucle tierra Rt ≤ 15 Ω"), key="mtd_in_tierra")
            prot_spl = st.text_input("Sistema de Balanceo de Carga (SPL):", value=st.session_state.get("mtd_in_spl", "Sensor toroidal CT para modulación dinámica en tiempo real"), key="mtd_in_spl")

    # --- TAB 5: CIRCUITOS DERIVADOS ---
    with tab_f5:
        st.markdown("##### 📋 Bloque V: Cuadro de Circuitos Interiores / Terminales Derivados:")
        
        circs_actuales = st.session_state.get("mtd_circuitos", [])
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

        col_b_mtd1, col_b_mtd2 = st.columns([1.6, 1])
        with col_b_mtd1:
            if st.button("💰 Generar Presupuesto de Obra desde este Cuadro de Circuitos", type="secondary", use_container_width=True, key="btn_gen_presup_from_mtd"):
                st.session_state["presupuesto_circuitos_importados"] = st.session_state.get("mtd_circuitos", [])
                st.session_state.menu_activo = "🏡 Presupuesto Vivienda"
                st.success("✅ ¡Traspasando cuadro de protecciones y líneas al módulo de Presupuestos! Redirigiendo...")
                st.rerun()
        with col_b_mtd2:
            st.caption("Crea automáticamente un presupuesto con las líneas, PIAs, diferenciales y metros de cable.")

    # --- TAB 6: PROTOCOLO DE ENSAYOS (ITC-BT-05) ---
    with tab_f6:
        st.markdown("##### 🧪 Bloque VI: Protocolo de Ensayos y Verificaciones Previas (ITC-BT-05 Murcia):")
        st.markdown("""
        Introduce los valores medidos con el equipo verificador multifunción en la instalación:
        """)
        col_t_1, col_t_2 = st.columns(2)
        with col_t_1:
            med_pe = st.number_input("Continuidad de Conductores PE (Ω) [Límite ≤ 0.50 Ω]:", value=float(st.session_state.get("mtd_in_med_pe", 0.11)), step=0.01, format="%.2f", key="mtd_in_med_pe")
            med_aisl = st.number_input("Resistencia de Aislamiento a 500 Vcc (MΩ) [Límite ≥ 1.0 MΩ]:", value=float(st.session_state.get("mtd_in_med_aisl", 100.0)), step=1.0, format="%.1f", key="mtd_in_med_aisl")
            med_rt = st.number_input("Resistencia de Bucle / Toma de Tierra Rt (Ω) [Límite ≤ 15 Ω]:", value=float(st.session_state.get("mtd_in_med_rt", 11.8)), step=0.1, format="%.1f", key="mtd_in_med_rt")
        with col_t_2:
            med_dif_ma = st.number_input("Corriente de Disparo Diferencial (mA) [Límite ≤ 30 mA]:", value=float(st.session_state.get("mtd_in_med_dif_ma", 22.0)), step=1.0, format="%.1f", key="mtd_in_med_dif_ma")
            med_dif_ms = st.number_input("Tiempo de Disparo Diferencial (ms) [Límite ≤ 300 ms]:", value=float(st.session_state.get("mtd_in_med_dif_ms", 26.0)), step=1.0, format="%.1f", key="mtd_in_med_dif_ms")
            med_vsp = st.selectbox("Comprobación Disparo de Sobretensiones (VTP + DPS):", ["Conforme (Disparo y señalización verificados)", "No Conforme"], key="mtd_in_med_vsp")

        # Semáforo de verificación ITC-BT-05
        cumple_ensayos = (med_pe <= 0.50) and (med_aisl >= 1.0) and (med_rt <= 15.0) and (med_dif_ma <= 30.0) and (med_dif_ms <= 300.0) and ("Conforme" in med_vsp)
        if cumple_ensayos:
            st.success("✅ **TODAS LAS VERIFICACIONES PREVIAS ITC-BT-05 SON CONFORMES CON EL REBT.** Instalación apta para puesta en servicio.")
        else:
            st.error("⚠️ **HAY MEDIDAS QUE SUPERAN LOS LÍMITES REGLAMENTARIOS DEL REBT.** Subsanar anomalías antes de la tramitación ante Industria.")

    # =========================================================================
    # 3. GUARDAR VINCULADO AL CLIENTE (CRM) Y GENERACIÓN DE DOCUMENTACIÓN OFICIAL
    # =========================================================================
    st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">💾 3. Guardar en Ficha del Cliente y Exportar Documentación Oficial (Murcia / REBT)</h4></div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        col_s_name, col_s_btn = st.columns([3, 1.5])
        with col_s_name:
            nom_proy_default = f"MTD - {tipo_inst_sel.split('(')[0].replace('🚗', '').replace('🏡', '').replace('🏢', '').replace('⚡', '').replace('🔌', '').strip()} - {tit_nombre}"
            nom_proy_mtd = st.text_input("Nombre / Referencia del Expediente para Guardar:", value=nom_proy_default, key="mtd_nom_guardar")
        with col_s_btn:
            st.write("")
            st.write("")
            if st.button("💾 Guardar en Ficha de Cliente", type="primary", use_container_width=True):
                if not cli_sel_id:
                    st.error("Debes seleccionar un cliente del CRM arriba para asociar la memoria técnica.")
                else:
                    datos_guardar = {
                        "mtd_tipo_inst_sel": tipo_inst_sel,
                        "mtd_in_tit_nom": tit_nombre,
                        "mtd_in_tit_nif": tit_nif,
                        "mtd_in_tit_tel": tit_tel,
                        "mtd_in_tit_email": tit_email,
                        "mtd_in_emp_dir": emp_dir,
                        "mtd_in_emp_cp": emp_cp,
                        "mtd_in_emp_muni": emp_muni,
                        "mtd_in_emp_cups": emp_cups,
                        "mtd_in_emp_uso": emp_uso,
                        "mtd_in_pot_inst": sum_pot_inst,
                        "mtd_in_pot_max": sum_pot_max,
                        "mtd_in_tension": sum_tension,
                        "mtd_in_origen": sum_origen,
                        "mtd_in_di_cable": sum_di_cable,
                        "mtd_in_di_tubo": sum_di_tubo,
                        "mtd_in_di_long": sum_di_long,
                        "mtd_in_di_cdt": sum_di_cdt,
                        "mtd_in_grado": sum_grado,
                        "mtd_in_iga": prot_iga,
                        "mtd_in_curva": prot_curva,
                        "mtd_in_icn": prot_icn,
                        "mtd_in_dif": prot_dif,
                        "mtd_in_vtp": prot_vtp,
                        "mtd_in_tierra": prot_tierra,
                        "mtd_in_spl": prot_spl,
                        "mtd_circuitos": st.session_state.get("mtd_circuitos", []),
                        "mtd_in_med_pe": med_pe,
                        "mtd_in_med_aisl": med_aisl,
                        "mtd_in_med_rt": med_rt,
                        "mtd_in_med_dif_ma": med_dif_ma,
                        "mtd_in_med_dif_ms": med_dif_ms
                    }
                    resumen_txt = f"{sum_pot_inst/1000:.2f} kW | {sum_tension} | {emp_muni}"
                    ok, p_id = db_manager.guardar_proyecto(
                        usuario_id=user_auth["id"],
                        cliente_id=cli_sel_id,
                        nombre_proyecto=nom_proy_mtd,
                        modulo="Memoria Técnica (MTD 30)",
                        datos=datos_guardar,
                        resumen=resumen_txt
                    )
                    if ok:
                        st.success(f"✅ ¡Memoria Técnica '{nom_proy_mtd}' guardada exitosamente en la ficha de {cli_obj.get('nombre_completo', 'Cliente')}!")
                        st.rerun()
                    else:
                        st.error("Error al guardar la memoria técnica en la base de datos.")

        st.divider()

        # DOCUMENTOS OFICIALES PARA INDUSTRIA Y CLIENTE
        col_g1, col_g2 = st.columns([3, 2])
        with col_g1:
            exp_in = st.text_input("Nº de Expediente Oficial (DGEAIM Murcia):", value=f"EXP-MTD-{emp_muni[:3].upper()}-2026-01", key="mtd_exp_final")
        with col_g2:
            st.write("")
            st.caption("Generación simultánea de toda la documentación requerida por Industria y el REBT.")

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
            "ensayos": {
                "pe_ohm": med_pe,
                "aisl_mohm": med_aisl,
                "rt_ohm": med_rt,
                "dif_ma": med_dif_ma,
                "dif_ms": med_dif_ms
            },
            "circuitos": st.session_state.get("mtd_circuitos", [])
        }

        tab_doc1, tab_doc2, tab_doc3 = st.tabs([
            "🏛️ Memoria Técnica Oficial (MTD 30)",
            "📑 Certificado de Instalación (CIE / Boletín)",
            "📘 Manual de Instrucciones (ITC-BT-04)"
        ])

        from modulos import visor_pdf

        with tab_doc1:
            try:
                pdf_bytes_mtd = pdf_memoria_tecnica.generar_pdf_mtd_industria_murcia(datos_para_pdf)
                visor_pdf.mostrar_visor_pdf(
                    pdf_bytes=pdf_bytes_mtd,
                    nombre_archivo=f"MTD_Oficial_DGEAIM_Murcia_{exp_in}.pdf",
                    label_boton="📥 Descargar Memoria Técnica Oficial MTD (PDF Murcia)"
                )
            except Exception as err:
                st.error(f"⚠️ Error al generar el PDF de la MTD: {err}")

        with tab_doc2:
            try:
                pdf_bytes_cie = pdf_memoria_tecnica.generar_pdf_cie_oficial(datos_para_pdf)
                visor_pdf.mostrar_visor_pdf(
                    pdf_bytes=pdf_bytes_cie,
                    nombre_archivo=f"CIE_Boletin_Oficial_{exp_in}.pdf",
                    label_boton="📥 Descargar Certificado de Instalación CIE (Boletín Eléctrico)"
                )
            except Exception as err:
                st.error(f"⚠️ Error al generar el Certificado CIE: {err}")

        with tab_doc3:
            try:
                pdf_bytes_man = pdf_memoria_tecnica.generar_pdf_manual_usuario(datos_para_pdf)
                visor_pdf.mostrar_visor_pdf(
                    pdf_bytes=pdf_bytes_man,
                    nombre_archivo=f"Manual_Instrucciones_Usuario_{tit_nombre.replace(' ', '_')}.pdf",
                    label_boton="📥 Descargar Manual de Instrucciones de Usuario (ITC-BT-04)"
                )
            except Exception as err:
                st.error(f"⚠️ Error al generar el Manual de Usuario: {err}")

