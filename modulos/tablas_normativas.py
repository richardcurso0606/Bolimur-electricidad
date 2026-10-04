# -*- coding: utf-8 -*-
"""
Módulo Integral de Tablas Normativas y Reglamentarias Oficiales
Para Instaladores Autorizados en Baja Tensión, Proyectistas y Tramitación ante Industria
Fuentes: REBT (RD 842/2002), Guías Técnicas MITECO, Normas UNE (UNE-HD 60364-5-52, UNE-EN 50575 CPR),
Distribuidoras Eléctricas (i-DE, Endesa, UFD, E-Redes), CTE (DB-HE, DB-SI, DB-SUA) y DGEAIM Murcia.
"""

import streamlit as st
import pandas as pd
from modulos import rebt_tablas as rebt

CATEGORIAS_TABLAS = {
    "🔥 1. Intensidades Admisibles e Instalación (UNE-HD 60364-5-52 / BT-19)": [
        "tab_iz_cobre_aluminio",
        "tab_factores_temperatura",
        "tab_factores_agrupamiento",
        "tab_conductividad_resistividad",
        "tab_cpr_reaccion_fuego"
    ],
    "🛡️ 2. Protecciones, Aparamenta y Tierras (UNE-EN 60898, IEC 62955, BT-18/23)": [
        "tab_curvas_disparo_magneto",
        "tab_tipos_diferenciales",
        "tab_sobretensiones_vtp_dps",
        "tab_dimensionado_conductor_pe",
        "tab_resistencias_tierra_maximas"
    ],
    "🚗 3. Recarga Vehículo Eléctrico IRVE (ITC-BT-52 / CTE DB-HE 6)": [
        "tab_esquemas_irve_bt52",
        "tab_modos_recarga_conectores",
        "tab_dotaciones_minimas_cte_he6",
        "tab_tubos_canalizaciones_irve"
    ],
    "⚡ 4. Distribuidora i-DE (Grupo Iberdrola) y Enlace (NI 42.73, NI 76.01, NI 72.30)": [
        "tab_ide_cgp_cpm_enlace_ni76",
        "tab_ide_centralizaciones_armarios_ni42",
        "tab_ide_medida_indirecta_trafor_ni42",
        "tab_fusibles_bases_buc",
        "tab_cerraduras_llaves_ide"
    ],
    "🏢 5. Edificación y Previsión de Cargas (ITC-BT-10, BT-14, BT-15, BT-25)": [
        "tab_potencias_normalizadas_espana",
        "tab_coeficientes_simultaneidad_k",
        "tab_prevision_locales_servicios_garajes",
        "tab_tubos_lga_di_interiores",
        "tab_factor_llenado_tubos_bt21"
    ],
    "🚨 6. Seguridad Contra Incendios y Emergencias (CTE DB-SI / DB-SUA 4)": [
        "tab_cables_resistentes_fuego_as_plus",
        "tab_alumbrado_emergencia_luxes",
        "tab_locales_publica_concurrencia_bt28"
    ],
    "📋 7. Industria Murcia DGEAIM: Trámites e Inspecciones (ITC-BT-04 y BT-05)": [
        "tab_instalaciones_precisan_proyecto_bt04",
        "tab_inspecciones_periodicas_oca_bt05",
        "tab_protocolo_medidas_previas_bt05",
        "tab_municipios_codigo30_murcia"
    ],
    "🛠️ 8. Instalación en Obra: Puntos de Luz, Alturas, Baños y Zanjas": [
        "tab_puntos_luz_tomas_maximas",
        "tab_alturas_mecanismos_cuadros",
        "tab_volumenes_banos_duchas",
        "tab_distancias_cruzamientos_servicios",
        "tab_zanjas_canalizaciones_subterraneas",
        "tab_codigo_colores_conductores"
    ],
    "☀️ 9. Autoconsumo Solar Fotovoltaico y Grados IP/IK (RD 244/2019, BT-40, UNE-EN 60529)": [
        "tab_autoconsumo_fotovoltaico_bt40",
        "tab_grados_proteccion_ip_ik"
    ]
}



def renderizar():
    st.markdown("""
    <style>
    .indice-card {
        background: #f8fafc;
        border: 1.5px solid #cbd5e1;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 8px;
        transition: all 0.2s ease;
    }
    .indice-card:hover {
        border-color: #0284c7;
        background: #f0f9ff;
    }
    .badge-norma {
        display: inline-block;
        background: #0284c7;
        color: white;
        font-size: 11px;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 10px;
        margin-left: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    col_t_tab, col_b_tab = st.columns([4, 1])
    with col_t_tab:
        st.title("📚 Biblioteca Integral de Tablas Normativas y Reglamentarias")
        st.caption("Compendio oficial para Instaladores Habilitados: REBT (RD 842/2002), Normas UNE, Guías Técnicas MITECO, Normas de Distribuidoras (i-DE, Endesa, UFD, E-Redes), CTE y DGEAIM Industria Murcia.")
    with col_b_tab:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Restablecer Filtros", key="btn_reset_tablas", use_container_width=True):
            st.session_state.pop("tabla_activa_sel", None)
            st.session_state.pop("filtro_busqueda_tablas", None)
            st.rerun()

    # Buscador Inteligente
    busqueda = st.text_input("🔍 Buscar tabla normativa o parámetro (ej: 'Iz', 'temperatura', 'IK08', 'Cca', 'i-DE', 'Diferencial', '32 mm', '6 mA', 'Simultaneidad', 'Picas'):", key="filtro_busqueda_tablas", placeholder="Escribe aquí para filtrar tablas al instante...")

    # Estado de selección
    if "tabla_activa_sel" not in st.session_state:
        st.session_state.tabla_activa_sel = "tab_iz_cobre_aluminio"

    # =========================================================================
    # ÍNDICE INTERACTIVO DE NAVEGACIÓN RÁPIDA
    # =========================================================================
    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">📑 Índice Interactivo de Tablas (Toca un botón para ver la tabla)</h4></div>', unsafe_allow_html=True)

    with st.expander("📂 Desplegar / Ocultar Índice Completo de Tablas Normativas", expanded=not bool(busqueda)):
        cols_ind = st.columns(2)
        idx_c = 0
        for cat_nombre, lista_tabs in CATEGORIAS_TABLAS.items():
            col_target = cols_ind[idx_c % 2]
            with col_target:
                with st.container(border=True):
                    st.markdown(f"**{cat_nombre}**")
                    for t_id in lista_tabs:
                        t_label = _obtener_titulo_tabla(t_id)
                        is_active = (st.session_state.tabla_activa_sel == t_id)
                        btn_label = f"{'👉 ' if is_active else '📄 '}{t_label}"
                        if st.button(btn_label, key=f"btn_ind_{t_id}", use_container_width=True, type="primary" if is_active else "secondary"):
                            st.session_state.tabla_activa_sel = t_id
                            st.rerun()
            idx_c += 1

    # Si hay búsqueda activa, mostrar resultados directos
    if busqueda:
        st.info(f"🔍 Resultados de búsqueda para: **'{busqueda}'**")
        encontrados = _buscar_tablas(busqueda)
        if encontrados:
            cols_res = st.columns(min(len(encontrados), 3))
            for i, (t_id, t_tit) in enumerate(encontrados.items()):
                with cols_res[i % 3]:
                    if st.button(f"📌 {t_tit}", key=f"btn_search_{t_id}", use_container_width=True, type="primary" if st.session_state.tabla_activa_sel == t_id else "secondary"):
                        st.session_state.tabla_activa_sel = t_id
                        st.rerun()
        else:
            st.warning("No se encontraron tablas que coincidan exactamente con la búsqueda. Mostrando tabla seleccionada.")

    st.divider()

    # =========================================================================
    # VISOR OFICIAL Y ASISTENTE INTELIGENTE IA
    # =========================================================================
    t_actual = st.session_state.tabla_activa_sel
    t_titulo = _obtener_titulo_tabla(t_actual)

    st.markdown(f"### 📋 {t_titulo}")

    tab_tabla, tab_ia_explicacion, tab_ia_consultor = st.tabs([
        "📊 Visor Técnico Oficial",
        "🤖 Explicación Didáctica IA (Paso a Paso)",
        "💡 Consultor Experto IA en Obra"
    ])

    with tab_tabla:
        _renderizar_tabla_especifica(t_actual)

    with tab_ia_explicacion:
        _renderizar_explicacion_ia(t_actual)

    with tab_ia_consultor:
        _renderizar_consultor_ia(t_actual)


def _obtener_titulo_tabla(tabla_id: str) -> str:
    titulos = {
        "tab_iz_cobre_aluminio": "Intensidades Admisibles Iz (UNE-HD 60364-5-52 / BT-19)",
        "tab_factores_temperatura": "Factores de Corrección por Temperatura Ambiente (ft)",
        "tab_factores_agrupamiento": "Factores de Corrección por Agrupamiento de Circuitos (fa)",
        "tab_conductividad_resistividad": "Conductividades (γ) y Resistividades (ρ) de Servicio",
        "tab_cpr_reaccion_fuego": "Clasificación CPR Reacción al Fuego de Cables (UNE-EN 50575)",
        "tab_curvas_disparo_magneto": "Curvas de Disparo Magnetotérmico B, C, D (UNE-EN 60898)",
        "tab_tipos_diferenciales": "Clases de Diferenciales AC, A, F, B y RDC-DD (IEC 62955)",
        "tab_sobretensiones_vtp_dps": "Protectores de Sobretensiones VTP y DPS (UNE-EN 50550)",
        "tab_dimensionado_conductor_pe": "Dimensionamiento de Conductor de Tierra PE (BT-19 Tabla 2)",
        "tab_resistencias_tierra_maximas": "Resistencia Máxima de Toma de Tierra Rt (ITC-BT-18)",
        "tab_esquemas_irve_bt52": "Esquemas de Instalación IRVE 1, 2, 3a, 3b, 4a (ITC-BT-52)",
        "tab_modos_recarga_conectores": "Modos de Carga (Modo 1-4) y Conectores (Tipo 2, CCS)",
        "tab_dotaciones_minimas_cte_he6": "Dotaciones Mínimas de Recarga VE en Parkings (CTE DB-HE 6)",
        "tab_tubos_canalizaciones_irve": "Tubos y Canalizaciones con Protección IK08 (ITC-BT-52)",
        "tab_cajas_cgp_cpm_distribuidoras": "Cajas CGP, CPM y Esquemas de Enlace (i-DE, Endesa, UFD)",
        "tab_modulos_centralizaciones_contadores": "Módulos de Centralización de Contadores (NI 42.73.01)",
        "tab_medida_indirecta_trafor": "Equipos de Medida Indirecta TT/II para P > 50 kW",
        "tab_ide_cgp_cpm_enlace_ni76": "Cajas CGP, CPM y Acometidas i-DE Iberdrola (Norma NI 76.01 / NI 72.30)",
        "tab_ide_centralizaciones_armarios_ni42": "Centralizaciones y Cuartos de Contadores i-DE Iberdrola (Norma NI 42.73)",
        "tab_ide_medida_indirecta_trafor_ni42": "Medida Indirecta y Transformadores de Intensidad TI i-DE (P > 43.6 kW)",
        "tab_cerraduras_llaves_ide": "Cerraduras y Llaves Normalizadas i-DE Iberdrola (JIS / AGA / Triangular)",
        "tab_fusibles_bases_buc": "Bases Tripolares BUC y Fusibles de Acometida NH00 / NH1",
        "tab_potencias_normalizadas_espana": "Potencias Normalizadas en España Monofásicas (230V) y Trifásicas (400V)",
        "tab_coeficientes_simultaneidad_k": "Coeficientes de Simultaneidad K en Edificios (ITC-BT-10)",
        "tab_prevision_locales_servicios_garajes": "Previsión de Cargas: Locales, Servicios y Garajes",
        "tab_tubos_lga_di_interiores": "Diámetros Exteriores Mínimos de Tubos (LGA, DI, Interior)",
        "tab_factor_llenado_tubos_bt21": "Diámetro de Tubos según Nº de Conductores (ITC-BT-21)",
        "tab_circuitos_vivienda_bt25": "Previsión de Circuitos y Tomas en Vivienda (ITC-BT-25)",
        "tab_cables_resistentes_fuego_as_plus": "Cables Resistentes al Fuego AS+ SZ1-K (CTE DB-SI)",
        "tab_alumbrado_emergencia_luxes": "Niveles de Iluminancia de Emergencia en Luxes (CTE DB-SUA 4)",
        "tab_locales_publica_concurrencia_bt28": "Prescripciones en Locales de Pública Concurrencia (BT-28)",
        "tab_instalaciones_precisan_proyecto_bt04": "Instalaciones que precisan Proyecto Técnico (ITC-BT-04)",
        "tab_inspecciones_periodicas_oca_bt05": "Inspecciones Iniciales y Periódicas por OCA (ITC-BT-05)",
        "tab_protocolo_medidas_previas_bt05": "Valores Reglamentarios de Medidas Previas (ITC-BT-05)",
        "tab_municipios_codigo30_murcia": "Municipios Oficiales y Tramitación DGEAIM Murcia (Código 30)",
        "tab_puntos_luz_tomas_maximas": "Puntos de Luz y Tomas Máximas por Circuito (ITC-BT-25)",
        "tab_alturas_mecanismos_cuadros": "Alturas Reglamentarias de Mecanismos y Cuadro CGMP",
        "tab_volumenes_banos_duchas": "Volúmenes de Prohibición y Protección en Baños (ITC-BT-27)",
        "tab_distancias_cruzamientos_servicios": "Distancias de Separación con Agua, Gas y Calefacción (BT-21)",
        "tab_zanjas_canalizaciones_subterraneas": "Zanjas Subterráneas: Profundidades y Señalización (BT-07)",
        "tab_codigo_colores_conductores": "Código de Colores Normalizado de Conductores (ITC-BT-19)",
        "tab_autoconsumo_fotovoltaico_bt40": "Autoconsumo Solar Fotovoltaico y Protecciones (RD 244/2019 / BT-40)",
        "tab_grados_proteccion_ip_ik": "Grados de Protección IP (Agua/Polvo) e Impacto Mecánico IK"
    }
    return titulos.get(tabla_id, tabla_id)


def _buscar_tablas(query: str) -> dict:
    q = query.lower().strip()
    resultados = {}
    for cat, lista in CATEGORIAS_TABLAS.items():
        for tid in lista:
            titulo = _obtener_titulo_tabla(tid)
            if q in tid.lower() or q in titulo.lower() or q in cat.lower():
                resultados[tid] = titulo
            elif q in ["iz", "intensidad", "cobre", "aluminio", "temperatura", "agrupamiento", "ft", "fa"] and "iz" in tid:
                resultados[tid] = titulo
            elif q in ["diferencial", "magneto", "sobretension", "vtp", "dps", "tierra", "pe", "pica"] and ("diferencial" in tid or "magneto" in tid or "pe" in tid or "sobretension" in tid or "tierra" in tid):
                resultados[tid] = titulo
            elif q in ["irve", "cargador", "wallbox", "vehiculo", "he6", "ik08", "spl"] and "irve" in tid:
                resultados[tid] = titulo
            elif q in ["distribuidora", "iberdrola", "i-de", "endesa", "ufd", "cgp", "cpm", "buc", "contador", "trafo", "llave", "jis", "aga", "ni42", "ni76"] and ("distribuidora" in tid or "cgp" in tid or "contador" in tid or "buc" in tid or "ide" in tid or "cerraduras" in tid):
                resultados[tid] = titulo
            elif q in ["vivienda", "simultaneidad", "k", "tubo", "di", "lga", "bt25", "bt10", "bt14", "bt15", "potencia", "potencias", "kw", "llenado"] and ("vivienda" in tid or "simultaneidad" in tid or "tubo" in tid or "bt25" in tid or "potencias" in tid or "llenado" in tid):
                resultados[tid] = titulo
            elif q in ["oca", "proyecto", "murcia", "bt04", "bt05", "medida", "ensayo", "aislamiento", "continuidad"] and ("bt04" in tid or "bt05" in tid or "murcia" in tid):
                resultados[tid] = titulo
            elif q in ["altura", "mecanismo", "enchufe", "interruptor", "punto", "luz", "bano", "ducha", "volumen", "zanja", "gas", "agua", "color", "colores", "c1", "c2", "c3", "c4", "c5"] and ("puntos" in tid or "alturas" in tid or "volumenes" in tid or "distancias" in tid or "zanjas" in tid or "colores" in tid):
                resultados[tid] = titulo
            elif q in ["solar", "fotovoltaica", "autoconsumo", "inversor", "ip", "ik", "estanqueidad", "bt40"] and ("autoconsumo" in tid or "grados" in tid):
                resultados[tid] = titulo
    return resultados




def _renderizar_tabla_especifica(tabla_id: str):
    # =========================================================================
    # 1. INTENSIDADES ADMISIBLES IZ
    # =========================================================================
    if tabla_id == "tab_iz_cobre_aluminio":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">⚡ Intensidades Admisibles en Régimen Permanente (Iz) - UNE-HD 60364-5-52 / ITC-BT-19</h3></div>', unsafe_allow_html=True)
        st.caption("Valores oficiales para temperatura ambiente de 40 ºC al aire (B1/B2) y 25 ºC en terreno enterrado bajo tubo (Método D).")
        
        with st.container(border=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                sel_m = st.selectbox("Material del Conductor:", ["Cobre", "Aluminio"], key="tab_vis_m")
            with col_f2:
                sel_a = st.selectbox("Tipo de Aislamiento:", ["XLPE / EPR (90ºC) - RZ1-K / Afumex", "PVC (70ºC) - H07V-K"], key="tab_vis_a")
            with col_f3:
                sel_met = st.selectbox("Método de Instalación:", ["B1 / B2 (Bajo tubo en pared / superficie)", "D (Subterráneo enterrado bajo tubo)"], key="tab_vis_met")

            tabla = rebt.obtener_tabla_iz(sel_m, sel_a, sel_met)
            df_iz = pd.DataFrame([
                {
                    "Sección Normalizada (mm²)": s,
                    "Intensidad Admisible Iz (A)": iz,
                    "Potencia Máx. Monofásica 230V (kW)": round((iz * 230.0) / 1000.0, 2),
                    "Potencia Máx. Trifásica 400V (kW)": round((1.732 * 400.0 * iz) / 1000.0, 2),
                    "PIA Máximo Recomendado (A)": rebt.seleccionar_proteccion(iz, tipo="pia") if iz <= 63 else rebt.seleccionar_proteccion(iz, tipo="general")
                }
                for s, iz in sorted(tabla.items())
            ])
            st.dataframe(df_iz, use_container_width=True, hide_index=True)

    # =========================================================================
    # 2. FACTORES DE CORRECCIÓN TEMPERATURA
    # =========================================================================
    elif tabla_id == "tab_factores_temperatura":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🌡️ Factores de Corrección por Temperatura Ambiente (ft) - UNE-HD 60364-5-52 Tabla B.52.14</h3></div>', unsafe_allow_html=True)
        st.caption("Coeficiente reductor de la intensidad admisible cuando la temperatura ambiente difiere de la base (40 ºC al aire / 25 ºC en tierra).")
        
        with st.container(border=True):
            df_temp = pd.DataFrame([
                {"Temp. Ambiente (ºC)": "15 ºC", "XLPE / EPR (90ºC) Al aire": 1.25, "PVC (70ºC) Al aire": 1.34, "XLPE Enterrado (25ºC base)": 1.08, "PVC Enterrado (25ºC base)": 1.11},
                {"Temp. Ambiente (ºC)": "20 ºC", "XLPE / EPR (90ºC) Al aire": 1.20, "PVC (70ºC) Al aire": 1.29, "XLPE Enterrado (25ºC base)": 1.04, "PVC Enterrado (25ºC base)": 1.06},
                {"Temp. Ambiente (ºC)": "25 ºC", "XLPE / EPR (90ºC) Al aire": 1.14, "PVC (70ºC) Al aire": 1.22, "XLPE Enterrado (25ºC base)": 1.00, "PVC Enterrado (25ºC base)": 1.00},
                {"Temp. Ambiente (ºC)": "30 ºC", "XLPE / EPR (90ºC) Al aire": 1.10, "PVC (70ºC) Al aire": 1.15, "XLPE Enterrado (25ºC base)": 0.96, "PVC Enterrado (25ºC base)": 0.93},
                {"Temp. Ambiente (ºC)": "35 ºC", "XLPE / EPR (90ºC) Al aire": 1.05, "PVC (70ºC) Al aire": 1.08, "XLPE Enterrado (25ºC base)": 0.92, "PVC Enterrado (25ºC base)": 0.87},
                {"Temp. Ambiente (ºC)": "40 ºC (Base aire)", "XLPE / EPR (90ºC) Al aire": 1.00, "PVC (70ºC) Al aire": 1.00, "XLPE Enterrado (25ºC base)": 0.87, "PVC Enterrado (25ºC base)": 0.79},
                {"Temp. Ambiente (ºC)": "45 ºC", "XLPE / EPR (90ºC) Al aire": 0.96, "PVC (70ºC) Al aire": 0.91, "XLPE Enterrado (25ºC base)": 0.82, "PVC Enterrado (25ºC base)": 0.71},
                {"Temp. Ambiente (ºC)": "50 ºC", "XLPE / EPR (90ºC) Al aire": 0.90, "PVC (70ºC) Al aire": 0.82, "XLPE Enterrado (25ºC base)": 0.76, "PVC Enterrado (25ºC base)": 0.61},
                {"Temp. Ambiente (ºC)": "55 ºC", "XLPE / EPR (90ºC) Al aire": 0.84, "PVC (70ºC) Al aire": 0.71, "XLPE Enterrado (25ºC base)": 0.70, "PVC Enterrado (25ºC base)": 0.50},
                {"Temp. Ambiente (ºC)": "60 ºC", "XLPE / EPR (90ºC) Al aire": 0.76, "PVC (70ºC) Al aire": 0.58, "XLPE Enterrado (25ºC base)": 0.63, "PVC Enterrado (25ºC base)": 0.35},
            ])
            st.dataframe(df_temp, use_container_width=True, hide_index=True)
            st.info("💡 **Fórmula práctica:** $I_z' = I_z \\cdot f_t \\cdot f_a$. El interruptor automático de protección debe elegirse para cumplir $I_b \\le I_n \\le I_z'$.")

    # =========================================================================
    # 3. FACTORES DE CORRECCIÓN AGRUPAMIENTO
    # =========================================================================
    elif tabla_id == "tab_factores_agrupamiento":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">👥 Factores de Corrección por Agrupamiento de Circuitos (fa) - UNE-HD 60364-5-52 Tabla B.52.17</h3></div>', unsafe_allow_html=True)
        st.caption("Factor reductor cuando varios circuitos discurren por el mismo tubo, canal o bandeja en contacto mutuo.")
        
        with st.container(border=True):
            df_agrup = pd.DataFrame([
                {"Nº de Circuitos / Cables en la misma canalización": "1 circuito (Monofásico o Trifásico)", "En tubo empotrado / superficie": 1.00, "En una capa sobre pared / bandeja no perforada": 1.00, "En bandeja perforada horizontal": 1.00},
                {"Nº de Circuitos / Cables en la misma canalización": "2 circuitos", "En tubo empotrado / superficie": 0.80, "En una capa sobre pared / bandeja no perforada": 0.85, "En bandeja perforada horizontal": 0.88},
                {"Nº de Circuitos / Cables en la misma canalización": "3 circuitos", "En tubo empotrado / superficie": 0.70, "En una capa sobre pared / bandeja no perforada": 0.79, "En bandeja perforada horizontal": 0.82},
                {"Nº de Circuitos / Cables en la misma canalización": "4 circuitos", "En tubo empotrado / superficie": 0.65, "En una capa sobre pared / bandeja no perforada": 0.75, "En bandeja perforada horizontal": 0.77},
                {"Nº de Circuitos / Cables en la misma canalización": "5 circuitos", "En tubo empotrado / superficie": 0.60, "En una capa sobre pared / bandeja no perforada": 0.73, "En bandeja perforada horizontal": 0.75},
                {"Nº de Circuitos / Cables en la misma canalización": "6 circuitos", "En tubo empotrado / superficie": 0.57, "En una capa sobre pared / bandeja no perforada": 0.72, "En bandeja perforada horizontal": 0.73},
                {"Nº de Circuitos / Cables en la misma canalización": "7 a 8 circuitos", "En tubo empotrado / superficie": 0.52, "En una capa sobre pared / bandeja no perforada": 0.70, "En bandeja perforada horizontal": 0.72},
                {"Nº de Circuitos / Cables en la misma canalización": "9 a 12 circuitos", "En tubo empotrado / superficie": 0.50, "En una capa sobre pared / bandeja no perforada": 0.66, "En bandeja perforada horizontal": 0.68},
            ])
            st.dataframe(df_agrup, use_container_width=True, hide_index=True)

    # =========================================================================
    # 4. CONDUCTIVIDAD Y RESISTIVIDAD
    # =========================================================================
    elif tabla_id == "tab_conductividad_resistividad":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🌡️ Conductividad (γ) y Resistividad (ρ) a Temperatura de Servicio</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_cond = pd.DataFrame([
                {"Material": "Cobre", "Aislamiento": "XLPE / EPR / Termoestable", "Temp. Máx. Servicio": "90 ºC", "Conductividad γ [m/(Ω·mm²)]": 44.0, "Resistividad ρ [Ω·mm²/m]": 0.0227, "Designación Habitual": "RZ1-K 0.6/1kV (Cca-s1b,d1,a1)"},
                {"Material": "Cobre", "Aislamiento": "PVC / Termoplástico", "Temp. Máx. Servicio": "70 ºC", "Conductividad γ [m/(Ω·mm²)]": 48.5, "Resistividad ρ [Ω·mm²/m]": 0.0206, "Designación Habitual": "H07V-K / H07Z1-K 450/750V"},
                {"Material": "Aluminio", "Aislamiento": "XLPE / EPR / Termoestable", "Temp. Máx. Servicio": "90 ºC", "Conductividad γ [m/(Ω·mm²)]": 28.0, "Resistividad ρ [Ω·mm²/m]": 0.0357, "Designación Habitual": "AL RZ1-K 0.6/1kV (LGA)"},
                {"Material": "Aluminio", "Aislamiento": "PVC / Termoplástico", "Temp. Máx. Servicio": "70 ºC", "Conductividad γ [m/(Ω·mm²)]": 31.0, "Resistividad ρ [Ω·mm²/m]": 0.0323, "Designación Habitual": "AL H07V-K"},
            ])
            st.dataframe(df_cond, use_container_width=True, hide_index=True)

    # =========================================================================
    # 5. REACCIÓN AL FUEGO CPR
    # =========================================================================
    elif tabla_id == "tab_cpr_reaccion_fuego":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🔥 Clasificación CPR de Reacción al Fuego de Cables (Reglamento UE 305/2011 / UNE-EN 50575)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_cpr = pd.DataFrame([
                {"Clase CPR": "Cca-s1b,d1,a1", "Tipo de Cable": "Libre de halógenos de Alta Seguridad (AS)", "Emisión de Humos": "s1b (Opacidad muy reducida)", "Gotas / Partículas": "d1 (Sin caída de gotas inflamadas)", "Acidez / Corrosividad": "a1 (Baja acidez y corrosividad)", "Exigencia REBT Obligatoria": "Derivaciones Individuales (ITC-BT-15), Locales Pública Concurrencia (ITC-BT-28), Enlace LGA (ITC-BT-14)"},
                {"Clase CPR": "B2ca-s1a,d1,a1", "Tipo de Cable": "Máxima seguridad ignífuga", "Emisión de Humos": "s1a (Transmitancia > 80%)", "Gotas / Partículas": "d1 (Extremadamente seguro)", "Acidez / Corrosividad": "a1 (No corrosivo)", "Exigencia REBT Obligatoria": "Túneles, hospitales y zonas de alto riesgo de evacuación"},
                {"Clase CPR": "Eca", "Tipo de Cable": "Termoplástico PVC convencional", "Emisión de Humos": "No declarada (Humos densos)", "Gotas / Partículas": "No declarada", "Acidez / Corrosividad": "No declarada (Emite HCl)", "Exigencia REBT Obligatoria": "Solo permitido en circuitos interiores empotrados de viviendas convencionales"}
            ])
            st.dataframe(df_cpr, use_container_width=True, hide_index=True)

    # =========================================================================
    # 6. CURVAS DE DISPARO MAGNETOTÉRMICO
    # =========================================================================
    elif tabla_id == "tab_curvas_disparo_magneto":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🛡️ Curvas de Disparo de Magnetotérmicos (PIAs / IGAs) - UNE-EN 60898-1 / UNE-EN 60947-2</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_curvas = pd.DataFrame([
                {"Curva": "Curva B", "Rango Disparo Térmico": "1.13 a 1.45 · In", "Rango Disparo Magnético (Im)": "3 a 5 · In", "Aplicación Principal": "Líneas muy largas de gran impedancia, generadores, electrónica o donde la corriente de cortocircuito sea reducida."},
                {"Curva": "Curva C", "Rango Disparo Térmico": "1.13 a 1.45 · In", "Rango Disparo Magnético (Im)": "5 a 10 · In", "Aplicación Principal": "Uso general estándar en viviendas, locales comerciales, tomas de corriente, alumbrado convencional e IRVE."},
                {"Curva": "Curva D", "Rango Disparo Térmico": "1.13 a 1.45 · In", "Rango Disparo Magnético (Im)": "10 a 20 · In", "Aplicación Principal": "Receptores con fuertes puntas de arranque en el encendido: transformadores, motores pesados, bombas y soldadoras."},
                {"Curva": "Curva K / Z", "Rango Disparo Térmico": "1.05 a 1.20 · In", "Rango Disparo Magnético (Im)": "8 a 14 · In (K) / 2 a 3 · In (Z)", "Aplicación Principal": "Protección de semiconductores de potencia, circuitos de control y protección ultra sensible."}
            ])
            st.dataframe(df_curvas, use_container_width=True, hide_index=True)

    # =========================================================================
    # 7. TIPOS DE DIFERENCIALES
    # =========================================================================
    elif tabla_id == "tab_tipos_diferenciales":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">⚡ Tipos de Interruptores Diferenciales (ID) - UNE-EN 61008 / UNE-EN 62423 / IEC 62955</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_difs = pd.DataFrame([
                {"Tipo": "Tipo AC", "Símbolo": "∿ (Senoidal pura)", "Detección de Fugas": "Solo corrientes alternas sinusoidales puras 50 Hz", "Uso Permitido": "Cargas resistivas puras o iluminación simple. En desuso progresivo."},
                {"Tipo": "Tipo A", "Símbolo": "∿ + ⎍ (Alterna + Pulsante)", "Detección de Fugas": "Corriente alterna y continua pulsante rectificada", "Uso Permitido": "Viviendas modernas, electrodomésticos con electrónica (inverter), placas de inducción y alumbrado LED."},
                {"Tipo": "Tipo A con RDC-DD (6mA DC)", "Símbolo": "∿ + ⎍ + ⎓ (6mA DC)", "Detección de Fugas": "Alterna, pulsante y corte automático si fuga DC > 6 mA", "Uso Permitido": "Obligatorio en recarga de Vehículos Eléctricos (ITC-BT-52 / IEC 62955) si no se usa Tipo B."},
                {"Tipo": "Tipo F", "Símbolo": "∿ + ⎍ + Multifrecuencia", "Detección de Fugas": "Frecuencias compuestas hasta 1 kHz y continua pulsante", "Uso Permitido": "Bombas de calor, lavadoras inverter, climatización y variadores monofásicos."},
                {"Tipo": "Tipo B", "Símbolo": "∿ + ⎍ + ⎓ (Continua pura)", "Detección de Fugas": "Alterna, pulsante, alta frecuencia (hasta 100 kHz) y continua pura", "Uso Permitido": "Inversores fotovoltaicos trifásicos, cargadores rápidos DC, variadores de frecuencia trifásicos y ascensores."}
            ])
            st.dataframe(df_difs, use_container_width=True, hide_index=True)

    # =========================================================================
    # 8. SOBRETENSIONES VTP Y DPS
    # =========================================================================
    elif tabla_id == "tab_sobretensiones_vtp_dps":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🛡️ Protectores contra Sobretensiones (ITC-BT-23 / UNE-EN 50550 / UNE-EN 61643-11)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_vtp = pd.DataFrame([
                {"Tipo de Sobretensión": "Transitoria Tipo 1 (DPS T1)", "Origen": "Impacto directo de rayo en red exterior aérea", "Onda de Ensayo": "10/350 µs", "Parámetros Clave": "Iimp ≥ 12.5 kA por polo", "Ubicación Reglamentaria": "Cuadro General / Edificios con pararrayos o acometida aérea en zona de alto nivel ceráunico."},
                {"Tipo de Sobretensión": "Transitoria Tipo 2 (DPS T2)", "Origen": "Conmutaciones de red y rayos indirectos", "Onda de Ensayo": "8/20 µs", "Parámetros Clave": "In ≥ 20 kA | Imax ≥ 40 kA | Up ≤ 1.5 kV", "Ubicación Reglamentaria": "Cuadro General (CGMP) de viviendas, locales, garajes e IRVE (ITC-BT-52)."},
                {"Tipo de Sobretensión": "Permanente (POP / VTP)", "Origen": "Corte o defecto del conductor neutro de la compañía distribuidora", "Onda de Ensayo": "Tensión a frecuencia industrial (50 Hz)", "Parámetros Clave": "Disparo en t < 0.2s a 380V según UNE-EN 50550", "Ubicación Reglamentaria": "Obligatorio en CGMP junto con bobina de emisión asociada al IGA."}
            ])
            st.dataframe(df_vtp, use_container_width=True, hide_index=True)

    # =========================================================================
    # 9. CONDUCTOR PE Y TIERRAS
    # =========================================================================
    elif tabla_id == "tab_dimensionado_conductor_pe":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🌱 Dimensionamiento de Conductores de Protección PE (ITC-BT-19 Tabla 2)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_pe = pd.DataFrame([
                {"Sección Conductor de Fase (S mm²)": "S ≤ 16 mm²", "Sección Mínima Conductor PE (Spe mm²)": "Spe = S (Misma sección de la fase)", "Ejemplo Práctico": "Fase 2.5 mm² → PE 2.5 mm² | Fase 6 mm² → PE 6 mm² | Fase 16 mm² → PE 16 mm²"},
                {"Sección Conductor de Fase (S mm²)": "16 < S ≤ 35 mm²", "Sección Mínima Conductor PE (Spe mm²)": "Spe = 16 mm²", "Ejemplo Práctico": "Fase 25 mm² → PE 16 mm² | Fase 35 mm² → PE 16 mm²"},
                {"Sección Conductor de Fase (S mm²)": "S > 35 mm²", "Sección Mínima Conductor PE (Spe mm²)": "Spe = S / 2 (Sección normalizada superior)", "Ejemplo Práctico": "Fase 50 mm² → PE 25 mm² | Fase 70 mm² → PE 35 mm² | Fase 120 mm² → PE 70 mm²"}
            ])
            st.dataframe(df_pe, use_container_width=True, hide_index=True)

    elif tabla_id == "tab_resistencias_tierra_maximas":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🌱 Resistencias Máximas de Toma de Tierra (ITC-BT-18 / ITC-BT-24)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_rt = pd.DataFrame([
                {"Tipo de Instalación / Diferencial": "Diferencial 30 mA (Sensibilidad alta - Residencial)", "Tensión de Contacto Límite (UL)": "24 V (Locales húmedos / garajes)", "Resistencia Máxima Teórica (Rt)": "Rt ≤ UL / IΔn = 24 / 0.03 = 800 Ω", "Límite Recomendado de Inspección": "Rt ≤ 15 a 20 Ω (Garantiza disipación estática y pararrayos)"},
                {"Tipo de Instalación / Diferencial": "Diferencial 300 mA (Industrial / Distribución)", "Tensión de Contacto Límite (UL)": "50 V (Locales secos)", "Resistencia Máxima Teórica (Rt)": "Rt ≤ 50 / 0.3 = 166 Ω", "Límite Recomendado de Inspección": "Rt ≤ 10 Ω"},
                {"Tipo de Instalación / Diferencial": "Edificio con Pararrayos (CTE DB-SUA 8)", "Tensión de Contacto Límite (UL)": "Descarga de rayo", "Resistencia Máxima Teórica (Rt)": "Rt ≤ 10 Ω (Obligatorio)", "Límite Recomendado de Inspección": "Rt ≤ 10 Ω en todo momento"}
            ])
            st.dataframe(df_rt, use_container_width=True, hide_index=True)

    # =========================================================================
    # 10. RECARGA VEHÍCULO ELÉCTRICO IRVE
    # =========================================================================
    elif tabla_id == "tab_esquemas_irve_bt52":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🚗 Esquemas Oficiales de Instalación IRVE (ITC-BT-52)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_esq = pd.DataFrame([
                {"Esquema ITC-BT-52": "Esquema 2 (Colectivo o individual desde contador vivienda)", "Origen": "Bornes de salida del contador en centralización", "Límite CdT": "1.0 %", "Permiso Comunidad": "Solo comunicación previa escrita (Art 17.5 LPH)", "Uso Habitual": "Garajes comunitarios de edificios existentes."},
                {"Esquema ITC-BT-52": "Esquema 1 (Troncal colectiva)", "Origen": "Cuadro general de garaje con contador colectivo", "Límite CdT": "1.0 %", "Permiso Comunidad": "Acuerdo de comunidad o Gestor de Carga (CPO)", "Uso Habitual": "Parkings públicos y nuevos edificios de obra nueva."},
                {"Esquema ITC-BT-52": "Esquema 3a (Contador nuevo en centralización)", "Origen": "Módulo de contador nuevo en centralización existente", "Límite CdT": "1.0 %", "Permiso Comunidad": "Comunicación previa (requiere nuevo CUPS)", "Uso Habitual": "Usuarios sin vivienda en el mismo inmueble."},
                {"Esquema ITC-BT-52": "Esquema 4a / 4b (Desde CGMP vivienda)", "Origen": "Cuadro General de la Vivienda (CGMP)", "Límite CdT": "1.5 %", "Permiso Comunidad": "No aplica (Privativo)", "Uso Habitual": "Viviendas unifamiliares, chalets o adosados."}
            ])
            st.dataframe(df_esq, use_container_width=True, hide_index=True)

    elif tabla_id == "tab_modos_recarga_conectores":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🔌 Modos de Recarga y Conectores Normalizados (ITC-BT-52)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_modos = pd.DataFrame([
                {"Modo de Carga": "Modo 1", "Tipo de Conexión": "Toma doméstica estándar Schuko (Sin comunicación)", "Potencia Típica": "Hasta 2.3 kW (10A)", "Nivel de Seguridad": "Básico (Desaconsejado para VE diario)"},
                {"Modo de Carga": "Modo 2", "Tipo de Conexión": "Cable con caja de control integrada (ICCB) en toma Schuko/Cekon", "Potencia Típica": "2.3 kW a 3.7 kW (10A a 16A)", "Nivel de Seguridad": "Medio (Carga de emergencia / ocasional)"},
                {"Modo de Carga": "Modo 3 (Wallbox)", "Tipo de Conexión": "Estación de recarga dedicada con piloto de control PWM / ISO 15118", "Potencia Típica": "3.7 kW, 7.4 kW (Monofásico) / 11 kW, 22 kW (Trifásico)", "Nivel de Seguridad": "Máximo (Estándar obligatorio de recarga doméstica y pública AC)"},
                {"Modo de Carga": "Modo 4 (Carga Rápida DC)", "Tipo de Conexión": "Cargador externo en corriente continua (Conector CCS Combo / CHAdeMO)", "Potencia Típica": "50 kW a 350 kW DC", "Nivel de Seguridad": "Ultra Rápido (Electrolineras y estaciones de servicio)"}
            ])
            st.dataframe(df_modos, use_container_width=True, hide_index=True)

    elif tabla_id == "tab_dotaciones_minimas_cte_he6":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🏢 Dotaciones Mínimas de Recarga VE en Parkings (CTE DB-HE 6)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_he6 = pd.DataFrame([
                {"Tipo de Edificio / Parking": "Edificios Residenciales Privados (Obra nueva o reforma)", "Dotación Exigida": "Preinstalación del 100% de las plazas (canalizaciones o bandejas continuas hasta centralización)."},
                {"Tipo de Edificio / Parking": "Edificios Terciarios / Comerciales (Plazas > 20)", "Dotación Exigida": "1 estación de recarga cada 40 plazas o fracción (hasta 1.000 plazas) + 1 cada 100 adicionales."},
                {"Tipo de Edificio / Parking": "Edificios de la Administración Pública", "Dotación Exigida": "1 estación de recarga cada 20 plazas (hasta 500 plazas) + 1 cada 100 adicionales."}
            ])
            st.dataframe(df_he6, use_container_width=True, hide_index=True)

    # =========================================================================
    # 11. DISTRIBUIDORAS Y NORMAS i-DE (GRUPO IBERDROLA)
    # =========================================================================
    elif tabla_id in ["tab_cajas_cgp_cpm_distribuidoras", "tab_ide_cgp_cpm_enlace_ni76"]:
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">⚡ Cajas CGP, CPM y Acometidas i-DE Iberdrola (Normas NI 76.01.01 y NI 72.30.01)</h3></div>', unsafe_allow_html=True)
        st.caption("Especificaciones técnicas oficiales de cajas generales de protección y medida para suministros en zona de distribución i-DE.")
        with st.container(border=True):
            df_cgp = pd.DataFrame([
                {"Modelo Oficial i-DE": "CPM-1 (Monofásica)", "Intensidad Máxima": "Hasta 63 A (P ≤ 14.49 kW)", "Tipo de Acometida": "Aérea posada / tensada / subterránea", "Bases / Fusibles": "1 Base seccionable BTVC NH00 (gG) + Neutro seccionable", "Aplicación": "Viviendas unifamiliares aisladas y suministros individuales monofásicos."},
                {"Modelo Oficial i-DE": "CPM-3 (Trifásica)", "Intensidad Máxima": "Hasta 63 A (P ≤ 43.64 kW)", "Tipo de Acometida": "Aérea o subterránea", "Bases / Fusibles": "3 Bases BTVC NH00 (gG) + Borna neutro seccionable", "Aplicación": "Chalets con clima trifásico, locales comerciales y talleres pequeños en medida directa."},
                {"Modelo Oficial i-DE": "CGP-7-100 / CGP-7-160", "Intensidad Máxima": "100 A a 160 A (P ≤ 110 kW)", "Tipo de Acometida": "Subterránea en nicho / fachada", "Bases / Fusibles": "3 Bases BTVC NH00 tamaño 00 + Neutro amovible", "Aplicación": "Edificios residenciales de 4 a 12 viviendas y locales."},
                {"Modelo Oficial i-DE": "CGP-9-250", "Intensidad Máxima": "250 A (P ≤ 173 kW)", "Tipo de Acometida": "Subterránea en nicho / fachada", "Bases / Fusibles": "3 Bases BTVC NH1 tamaño 1 + Neutro con pletina amovible", "Aplicación": "Edificios residenciales de 12 a 30 viviendas o naves de mediana potencia."},
                {"Modelo Oficial i-DE": "CGP-11-400", "Intensidad Máxima": "400 A (P ≤ 277 kW)", "Tipo de Acometida": "Subterránea / Centro de Transformación", "Bases / Fusibles": "3 Bases BTVC NH2 tamaño 2 + Neutro amovible", "Aplicación": "Grandes bloques de viviendas, complejos comerciales y centros hospitalarios."},
                {"Modelo Oficial i-DE": "CGP-14 (Esquema 14)", "Intensidad Máxima": "100 A a 400 A", "Tipo de Acometida": "Red mallada subterránea", "Bases / Fusibles": "Doble juego de seccionamiento de red y derivación con fusibles NH", "Aplicación": "Entrada y salida de red para distribución en bucle en vía pública."}
            ])
            st.dataframe(df_cgp, use_container_width=True, hide_index=True)
            st.info("📌 **Norma de Montaje:** Las CGP deben ubicarse en la línea de fachada del inmueble a una altura entre **0.50 m y 1.50 m** respecto al suelo, en nicho con puerta de protección resistente al fuego y cerradura homologada JIS/AGA de i-DE.")

    elif tabla_id == "tab_ide_centralizaciones_armarios_ni42" or tabla_id == "tab_modulos_centralizaciones_contadores":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🏢 Centralizaciones y Cuartos de Contadores i-DE Iberdrola (Norma NI 42.73.01)</h3></div>', unsafe_allow_html=True)
        st.caption("Condiciones reglamentarias para la concentración de contadores en edificios residenciales, terciarios e industriales.")
        with st.container(border=True):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.markdown("#### Tipo de Instalación según Número de Suministros:")
                df_cent = pd.DataFrame([
                    {"Nº Contadores": "1 Contador", "Ubicación Permitida": "Módulo CPM en fachada o valla de parcela", "Acceso Exigido": "Directo desde vía pública"},
                    {"Nº Contadores": "Hasta 16 Contadores", "Ubicación Permitida": "Armario prefabricado en planta baja o zonas comunes", "Acceso Exigido": "Acceso libre para lectura y corte"},
                    {"Nº Contadores": "> 16 Contadores", "Ubicación Permitida": "Local o Cuarto exclusivo de contadores (ITC-BT-16)", "Acceso Exigido": "Planta baja, sótano 1 o primera planta"}
                ])
                st.dataframe(df_cent, use_container_width=True, hide_index=True)

            with col_c2:
                st.markdown("#### Requisitos del Cuarto de Contadores (NI 42.73.01):")
                df_req = pd.DataFrame([
                    {"Elemento": "Paredes y Techo", "Exigencia i-DE / REBT": "Resistencia al fuego mínima EI 120 (RF 120)"},
                    {"Elemento": "Puerta de Acceso", "Exigencia i-DE / REBT": "Resistencia al fuego EI2 30-C5 con apertura exterior"},
                    {"Elemento": "Cerradura de la Puerta", "Exigencia i-DE / REBT": "Cerradura JIS / AGA con llave de compañía homologada"},
                    {"Elemento": "Dimensiones Libres", "Exigencia i-DE / REBT": "Altura libre ≥ 2.30 m | Pasillo de maniobra ≥ 1.10 m"},
                    {"Elemento": "Ventilación", "Exigencia i-DE / REBT": "Ventilación natural con rejillas superior e inferior ≥ 200 cm²"},
                    {"Elemento": "Alumbrado", "Exigencia i-DE / REBT": "Iluminación media ≥ 200 lux + Emergencia autónoma ≥ 5 lux"},
                    {"Elemento": "Extintor", "Exigencia i-DE / REBT": "Extintor de CO2 de 5 kg (eficacia 89B) junto a la puerta"}
                ])
                st.dataframe(df_req, use_container_width=True, hide_index=True)

    elif tabla_id in ["tab_ide_medida_indirecta_trafor_ni42", "tab_medida_indirecta_trafor"]:
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">⚡ Medida Indirecta y Transformadores de Intensidad TI i-DE (Norma NI 42.71.01)</h3></div>', unsafe_allow_html=True)
        st.caption("Obligatorio para suministros de potencia contratada superior a 43.64 kW (corriente asignada > 63 A en BT).")
        with st.container(border=True):
            df_ti = pd.DataFrame([
                {"Rango de Potencia Contratada": "43.64 kW a 69.28 kW", "Corriente Nominal (In)": "63 A a 100 A", "Relación Trafo TI Normalizada": "100 / 5 A", "Clase de Precisión": "Clase 0.5S (Facturación)", "Potencia de Precisión": "5 VA a 10 VA"},
                {"Rango de Potencia Contratada": "69.28 kW a 103.9 kW", "Corriente Nominal (In)": "100 A a 150 A", "Relación Trafo TI Normalizada": "150 / 5 A", "Clase de Precisión": "Clase 0.5S (Facturación)", "Potencia de Precisión": "5 VA a 10 VA"},
                {"Rango de Potencia Contratada": "103.9 kW a 138.5 kW", "Corriente Nominal (In)": "150 A a 200 A", "Relación Trafo TI Normalizada": "200 / 5 A", "Clase de Precisión": "Clase 0.5S (Facturación)", "Potencia de Precisión": "5 VA a 10 VA"},
                {"Rango de Potencia Contratada": "138.5 kW a 207.8 kW", "Corriente Nominal (In)": "200 A a 300 A", "Relación Trafo TI Normalizada": "300 / 5 A", "Clase de Precisión": "Clase 0.5S (Facturación)", "Potencia de Precisión": "5 VA a 10 VA"},
                {"Rango de Potencia Contratada": "207.8 kW a 277.1 kW", "Corriente Nominal (In)": "300 A a 400 A", "Relación Trafo TI Normalizada": "400 / 5 A", "Clase de Precisión": "Clase 0.5S (Facturación)", "Potencia de Precisión": "10 VA a 15 VA"},
                {"Rango de Potencia Contratada": "277.1 kW a 415.7 kW", "Corriente Nominal (In)": "400 A a 600 A", "Relación Trafo TI Normalizada": "600 / 5 A", "Clase de Precisión": "Clase 0.5S (Facturación)", "Potencia de Precisión": "15 VA"}
            ])
            st.dataframe(df_ti, use_container_width=True, hide_index=True)
            st.info("⚠️ **Requisitos del Bloque de Pruebas y Cableado:** Se debe instalar una caja de medida con bloque de pruebas precintable de 10 bornas (3 fases de tensión, 6 bornas para los 3 secundarios TI y 1 neutro). El cableado entre los TI y el bloque de pruebas debe ser de cobre aislado de **2.5 mm²** (longitud < 5 m) o **4.0 mm²** (longitud de 5 a 10 m).")

    elif tabla_id == "tab_fusibles_bases_buc":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🔌 Bases Tripolares BUC y Cartuchos Fusibles NH (UNE-EN 60269 / NI 76.50.01)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_buc = pd.DataFrame([
                {"Tamaño Fusible NH": "NH 00 (Tamaño 00)", "Calibres Normalizados (A)": "16, 25, 32, 40, 50, 63, 80, 100, 125, 160 A", "Poder de Corte Mínimo": "120 kA a 500 V", "Curva de Fusión": "gG (Protección general de cables y conductores)", "Base BTVC Utilizada": "Base Tripolar Vertical BTVC-00"},
                {"Tamaño Fusible NH": "NH 1 (Tamaño 1)", "Calibres Normalizados (A)": "125, 160, 200, 250 A", "Poder de Corte Mínimo": "120 kA a 500 V", "Curva de Fusión": "gG (Distribución y redes)", "Base BTVC Utilizada": "Base Tripolar Vertical BTVC-1"},
                {"Tamaño Fusible NH": "NH 2 (Tamaño 2)", "Calibres Normalizados (A)": "250, 315, 355, 400 A", "Poder de Corte Mínimo": "120 kA a 500 V", "Curva de Fusión": "gG / aM (Acometidas pesadas / Motores)", "Base BTVC Utilizada": "Base Tripolar Vertical BTVC-2"},
                {"Tamaño Fusible NH": "NH 3 (Tamaño 3)", "Calibres Normalizados (A)": "400, 500, 630 A", "Poder de Corte Mínimo": "120 kA a 500 V", "Curva de Fusión": "gG (Centros de transformación)", "Base BTVC Utilizada": "Base Tripolar Vertical BTVC-3"}
            ])
            st.dataframe(df_buc, use_container_width=True, hide_index=True)

    elif tabla_id == "tab_cerraduras_llaves_ide":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🔑 Cerraduras y Llaves Normalizadas i-DE Iberdrola</h3></div>', unsafe_allow_html=True)
        st.caption("Modelos oficiales homologados por i-DE Redes Eléctricas Inteligentes para envolventes, armarios y cuartos técnicos.")
        with st.container(border=True):
            df_llaves = pd.DataFrame([
                {"Tipo de Cierre / Cerradura": "Cerradura JIS con Bombillo Homologado i-DE", "Elemento donde se Instala": "Puertas de Cuartos de Contadores y Armarios en fachada", "Acceso Autorizado": "Personal técnico de i-DE, inspectores y presidente/administrador", "Código / Modelo": "Cerradura pomo JIS con amaestramiento oficial i-DE"},
                {"Tipo de Cierre / Cerradura": "Cerradura AGA Modelo Distribuidora", "Elemento donde se Instala": "Cajas CPM, CGP y módulos de medida en intemperie", "Acceso Autorizado": "Instalador electricista autorizado y compañía", "Código / Modelo": "Bombillo AGA estándar para cuadros de distribución"},
                {"Tipo de Cierre / Cerradura": "Llave Triangular Normalizada (11 mm)", "Elemento donde se Instala": "Tapas de Cajas Generales de Protección CGP y arquetas subterráneas", "Acceso Autorizado": "Operarios de maniobra y mantenimiento de red", "Código / Modelo": "Llave de triángulo de 11 mm UNE 20324"},
                {"Tipo de Cierre / Cerradura": "Pestillo con Candado i-DE", "Elemento donde se Instala": "Centros de Transformación de abonado y celdas de Media Tensión", "Acceso Autorizado": "Exclusivo personal autorizado de Iberdrola", "Código / Modelo": "Candado normalizado con clave maestra de zona"}
            ])
            st.dataframe(df_llaves, use_container_width=True, hide_index=True)

    # =========================================================================
    # 12. POTENCIAS NORMALIZADAS EN ESPAÑA
    # =========================================================================
    elif tabla_id == "tab_potencias_normalizadas_espana":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">⚡ Potencias Normalizadas en España (Monofásica 230V y Trifásica 400V)</h3></div>', unsafe_allow_html=True)
        st.caption("Escalones de potencia contratables ante comercializadora/distribuidora según calibres de ICP/IGA reglamentarios.")
        with st.container(border=True):
            col_pn1, col_pn2 = st.columns(2)
            with col_pn1:
                st.markdown("#### Suministros Monofásicos a 230 V:")
                df_mono = pd.DataFrame([
                    {"Calibre ICP / IGA": "5 A", "Potencia Normalizada": "1.150 W (1.15 kW)", "Uso Habitual": "Garajes individuales / Trasteros"},
                    {"Calibre ICP / IGA": "10 A", "Potencia Normalizada": "2.300 W (2.30 kW)", "Uso Habitual": "Apartamentos pequeños / Estudios"},
                    {"Calibre ICP / IGA": "15 A", "Potencia Normalizada": "3.450 W (3.45 kW)", "Uso Habitual": "Electrificación básica reducida"},
                    {"Calibre ICP / IGA": "20 A", "Potencia Normalizada": "4.600 W (4.60 kW)", "Uso Habitual": "Vivienda media estándar"},
                    {"Calibre ICP / IGA": "25 A", "Potencia Normalizada": "5.750 W (5.75 kW)", "Uso Habitual": "Electrificación básica (REBT mínimo)"},
                    {"Calibre ICP / IGA": "32 A", "Potencia Normalizada": "7.360 W (7.36 kW)", "Uso Habitual": "Vivienda con aire / calefacción"},
                    {"Calibre ICP / IGA": "40 A", "Potencia Normalizada": "9.200 W (9.20 kW)", "Uso Habitual": "Electrificación elevada (REBT mín. 9.2 kW)"},
                    {"Calibre ICP / IGA": "50 A", "Potencia Normalizada": "11.500 W (11.50 kW)", "Uso Habitual": "Vivienda grande con aerotermia"},
                    {"Calibre ICP / IGA": "63 A", "Potencia Normalizada": "14.490 W (14.49 kW)", "Uso Habitual": "Máximo monofásico admisible"}
                ])
                st.dataframe(df_mono, use_container_width=True, hide_index=True)

            with col_pn2:
                st.markdown("#### Suministros Trifásicos a 400 V:")
                df_tri = pd.DataFrame([
                    {"Calibre ICP / IGA": "10 A", "Potencia Normalizada": "6.928 W (6.93 kW)", "Tipo de Medida": "Medida Directa"},
                    {"Calibre ICP / IGA": "15 A", "Potencia Normalizada": "10.392 W (10.39 kW)", "Tipo de Medida": "Medida Directa"},
                    {"Calibre ICP / IGA": "20 A", "Potencia Normalizada": "13.856 W (13.86 kW)", "Tipo de Medida": "Medida Directa"},
                    {"Calibre ICP / IGA": "25 A", "Potencia Normalizada": "17.320 W (17.32 kW)", "Tipo de Medida": "Medida Directa"},
                    {"Calibre ICP / IGA": "32 A", "Potencia Normalizada": "22.170 W (22.17 kW)", "Tipo de Medida": "Medida Directa"},
                    {"Calibre ICP / IGA": "40 A", "Potencia Normalizada": "27.712 W (27.71 kW)", "Tipo de Medida": "Medida Directa"},
                    {"Calibre ICP / IGA": "50 A", "Potencia Normalizada": "34.641 W (34.64 kW)", "Tipo de Medida": "Medida Directa"},
                    {"Calibre ICP / IGA": "63 A", "Potencia Normalizada": "43.639 W (43.64 kW)", "Tipo de Medida": "Límite Medida Directa"},
                    {"Calibre ICP / IGA": "80 A", "Potencia Normalizada": "55.425 W (55.43 kW)", "Tipo de Medida": "Medida Indirecta (TI 100/5A)"},
                    {"Calibre ICP / IGA": "100 A", "Potencia Normalizada": "69.282 W (69.28 kW)", "Tipo de Medida": "Medida Indirecta (TI 150/5A)"},
                    {"Calibre ICP / IGA": "125 A", "Potencia Normalizada": "86.602 W (86.60 kW)", "Tipo de Medida": "Medida Indirecta (TI 150/5A)"},
                    {"Calibre ICP / IGA": "160 A", "Potencia Normalizada": "110.851 W (110.85 kW)", "Tipo de Medida": "Medida Indirecta (TI 200/5A)"}
                ])
                st.dataframe(df_tri, use_container_width=True, hide_index=True)

    # =========================================================================
    # 13. TUBOS Y CANALIZACIONES
    # =========================================================================
    elif tabla_id in ["tab_tubos_lga_di_interiores", "tab_tubos_canalizaciones_irve"]:
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🛠️ Diámetros Mínimos de Tubos Protectores Normalizados</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_tb1, col_tb2 = st.columns(2)
            with col_tb1:
                st.markdown("#### Derivaciones Individuales (ITC-BT-15 apdo. 3)")
                st.info("⚠️ **El diámetro mínimo reglamentario para cualquier Derivación Individual es Ø 32 mm**.")
                df_tubo_di = pd.DataFrame([
                    {"Sección Conductor": "Hasta 6 mm²", "Diámetro Tubo": "Ø 32 mm", "Norma": "ITC-BT-15 (Mínimo absoluto)"},
                    {"Sección Conductor": "10 a 16 mm²", "Diámetro Tubo": "Ø 40 mm", "Norma": "ITC-BT-15"},
                    {"Sección Conductor": "25 a 35 mm²", "Diámetro Tubo": "Ø 50 mm", "Norma": "ITC-BT-15"},
                    {"Sección Conductor": "≥ 50 mm²", "Diámetro Tubo": "Ø 63 mm o Bandeja", "Norma": "ITC-BT-15"}
                ])
                st.dataframe(df_tubo_di, use_container_width=True, hide_index=True)

            with col_tb2:
                st.markdown("#### Línea General de Alimentación - LGA (ITC-BT-14 Tabla 1)")
                st.info("⚠️ **El diámetro mínimo reglamentario para LGA trifásica parte de Ø 110 mm**.")
                df_tubo_lga = pd.DataFrame([
                    {"Sección Conductor": "Hasta 25 mm²", "Diámetro Mínimo Tubo": "Ø 110 mm", "Norma": "ITC-BT-14 Tabla 1"},
                    {"Sección Conductor": "35 mm²", "Diámetro Mínimo Tubo": "Ø 125 mm", "Norma": "ITC-BT-14 Tabla 1"},
                    {"Sección Conductor": "50 a 70 mm²", "Diámetro Mínimo Tubo": "Ø 140 mm", "Norma": "ITC-BT-14 Tabla 1"},
                    {"Sección Conductor": "95 a 120 mm²", "Diámetro Mínimo Tubo": "Ø 160 mm", "Norma": "ITC-BT-14 Tabla 1"},
                    {"Sección Conductor": "≥ 150 mm²", "Diámetro Mínimo Tubo": "Ø 180 a 225 mm", "Norma": "ITC-BT-14 Tabla 1"}
                ])
                st.dataframe(df_tubo_lga, use_container_width=True, hide_index=True)

    elif tabla_id == "tab_factor_llenado_tubos_bt21":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">📏 Diámetros Exteriores de Tubos según Nº y Sección de Conductores (ITC-BT-21)</h3></div>', unsafe_allow_html=True)
        st.caption("Tablas 1 y 2 de la ITC-BT-21 para canalizaciones empotradas y superficiales en instalaciones interiores.")
        with st.container(border=True):
            df_bt21 = pd.DataFrame([
                {"Sección Conductor (mm²)": "1.5 mm²", "1 Conductor (Ø mm)": "12 mm", "2 Conductores (Ø mm)": "16 mm", "3 Conductores (Ø mm)": "16 mm", "4 Conductores (Ø mm)": "20 mm", "5 Conductores (Ø mm)": "20 mm"},
                {"Sección Conductor (mm²)": "2.5 mm²", "1 Conductor (Ø mm)": "12 mm", "2 Conductores (Ø mm)": "16 mm", "3 Conductores (Ø mm)": "20 mm", "4 Conductores (Ø mm)": "20 mm", "5 Conductores (Ø mm)": "25 mm"},
                {"Sección Conductor (mm²)": "4.0 mm²", "1 Conductor (Ø mm)": "12 mm", "2 Conductores (Ø mm)": "20 mm", "3 Conductores (Ø mm)": "20 mm", "4 Conductores (Ø mm)": "25 mm", "5 Conductores (Ø mm)": "25 mm"},
                {"Sección Conductor (mm²)": "6.0 mm²", "1 Conductor (Ø mm)": "16 mm", "2 Conductores (Ø mm)": "20 mm", "3 Conductores (Ø mm)": "25 mm", "4 Conductores (Ø mm)": "25 mm", "5 Conductores (Ø mm)": "32 mm"},
                {"Sección Conductor (mm²)": "10.0 mm²", "1 Conductor (Ø mm)": "16 mm", "2 Conductores (Ø mm)": "25 mm", "3 Conductores (Ø mm)": "32 mm", "4 Conductores (Ø mm)": "32 mm", "5 Conductores (Ø mm)": "40 mm"},
                {"Sección Conductor (mm²)": "16.0 mm²", "1 Conductor (Ø mm)": "20 mm", "2 Conductores (Ø mm)": "32 mm", "3 Conductores (Ø mm)": "32 mm", "4 Conductores (Ø mm)": "40 mm", "5 Conductores (Ø mm)": "40 mm"},
                {"Sección Conductor (mm²)": "25.0 mm²", "1 Conductor (Ø mm)": "25 mm", "2 Conductores (Ø mm)": "32 mm", "3 Conductores (Ø mm)": "40 mm", "4 Conductores (Ø mm)": "50 mm", "5 Conductores (Ø mm)": "50 mm"},
                {"Sección Conductor (mm²)": "35.0 mm²", "1 Conductor (Ø mm)": "25 mm", "2 Conductores (Ø mm)": "40 mm", "3 Conductores (Ø mm)": "50 mm", "4 Conductores (Ø mm)": "50 mm", "5 Conductores (Ø mm)": "63 mm"}
            ])
            st.dataframe(df_bt21, use_container_width=True, hide_index=True)
            st.info("💡 **Regla de Ocupación:** La sección interior del tubo protector debe ser como mínimo **3 veces** la sección ocupada por los conductores en canalizaciones empotradas y **2.5 veces** en canalizaciones superficiales.")

    # =========================================================================
    # 14. PREVISIÓN DE CARGAS K Y LOCALES
    # =========================================================================
    elif tabla_id == "tab_coeficientes_simultaneidad_k":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🏢 Coeficientes de Simultaneidad (K) en Edificios de Viviendas (ITC-BT-10)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_k = pd.DataFrame([
                {"Viviendas (1-10)": "1", "Coeficiente K (1-10)": "1.00", "Viviendas (11-20)": "11", "Coeficiente K (11-20)": "9.10"},
                {"Viviendas (1-10)": "2", "Coeficiente K (1-10)": "2.00", "Viviendas (11-20)": "12", "Coeficiente K (11-20)": "9.80"},
                {"Viviendas (1-10)": "3", "Coeficiente K (1-10)": "3.00", "Viviendas (11-20)": "13", "Coeficiente K (11-20)": "10.50"},
                {"Viviendas (1-10)": "4", "Coeficiente K (1-10)": "3.80", "Viviendas (11-20)": "14", "Coeficiente K (11-20)": "11.20"},
                {"Viviendas (1-10)": "5", "Coeficiente K (1-10)": "4.60", "Viviendas (11-20)": "15", "Coeficiente K (11-20)": "11.90"},
                {"Viviendas (1-10)": "6", "Coeficiente K (1-10)": "5.40", "Viviendas (11-20)": "16", "Coeficiente K (11-20)": "12.60"},
                {"Viviendas (1-10)": "7", "Coeficiente K (1-10)": "6.20", "Viviendas (11-20)": "17", "Coeficiente K (11-20)": "13.30"},
                {"Viviendas (1-10)": "8", "Coeficiente K (1-10)": "7.00", "Viviendas (11-20)": "18", "Coeficiente K (11-20)": "14.00"},
                {"Viviendas (1-10)": "9", "Coeficiente K (1-10)": "7.80", "Viviendas (11-20)": "19", "Coeficiente K (11-20)": "14.70"},
                {"Viviendas (1-10)": "10", "Coeficiente K (1-10)": "8.50", "Viviendas (11-20)": "20", "Coeficiente K (11-20)": "15.40"}
            ])
            st.dataframe(df_k, use_container_width=True, hide_index=True)
            st.info("📐 **Fórmula oficial para más de 20 viviendas ($n > 20$):** $K = 15.4 + (n - 20) \\cdot 0.5$.")

    elif tabla_id == "tab_prevision_locales_servicios_garajes":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🏬 Previsión de Cargas: Locales Comerciales, Oficinas y Garajes (ITC-BT-10)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_prev = pd.DataFrame([
                {"Tipo de Emplazamiento": "Locales Comerciales y Oficinas", "Criterio de Cálculo Mínimo": "100 W / m² de superficie útil", "Mínimo Absoluto Exigido": "3.450 W (3.45 kW) por local", "Coeficiente Simultaneidad": "Fs = 1.0 (Sin simultaneidad)"},
                {"Tipo de Emplazamiento": "Garajes con Ventilación Natural", "Criterio de Cálculo Mínimo": "10 W / m² de superficie útil", "Mínimo Absoluto Exigido": "1.000 W (1.0 kW)", "Coeficiente Simultaneidad": "Fs = 1.0"},
                {"Tipo de Emplazamiento": "Garajes con Ventilación Forzada", "Criterio de Cálculo Mínimo": "20 W / m² de superficie útil", "Mínimo Absoluto Exigido": "1.000 W + Potencia de extractores", "Coeficiente Simultaneidad": "Fs = 1.0 (Requiere Proyecto)"},
                {"Tipo de Emplazamiento": "Servicios Generales (Ascensores, Bombas, Alumbrado)", "Criterio de Cálculo Mínimo": "Suma de potencias nominales de los receptores", "Mínimo Absoluto Exigido": "Según placa de características", "Coeficiente Simultaneidad": "Motor mayor x 1.25 + resto de motores"}
            ])
            st.dataframe(df_prev, use_container_width=True, hide_index=True)

    # =========================================================================
    # 15. TRÁMITES E INSPECCIONES INDUSTRIA MURCIA DGEAIM
    # =========================================================================
    elif tabla_id in ["tab_instalaciones_precisan_proyecto_bt04", "tab_inspecciones_periodicas_oca_bt05", "tab_protocolo_medidas_previas_bt05", "tab_municipios_codigo30_murcia"]:
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🏛️ Tramitación Telemática DGEAIM Región de Murcia (Código Provincial 30)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_ind1, col_ind2 = st.columns(2)
            with col_ind1:
                st.markdown("#### Instalaciones que precisan Proyecto Técnico (ITC-BT-04 apdo. 3.1):")
                df_proy = pd.DataFrame([
                    {"Tipo de Instalación": "Industrias en general", "Límite MTD": "P ≤ 20 kW", "Exige Proyecto": "P > 20 kW"},
                    {"Tipo de Instalación": "Locales mojados / Bombas", "Límite MTD": "P ≤ 10 kW", "Exige Proyecto": "P > 10 kW"},
                    {"Tipo de Instalación": "Edificios de viviendas / locales", "Límite MTD": "P ≤ 100 kW por CGP", "Exige Proyecto": "P > 100 kW por CGP"},
                    {"Tipo de Instalación": "Viviendas unifamiliares", "Límite MTD": "P ≤ 50 kW", "Exige Proyecto": "P > 50 kW"},
                    {"Tipo de Instalación": "Garajes ventilación forzada", "Límite MTD": "No permite MTD", "Exige Proyecto": "Cualquier potencia (Siempre Proyecto)"},
                    {"Tipo de Instalación": "Garajes ventilación natural", "Límite MTD": "Hasta 5 plazas", "Exige Proyecto": "> 5 plazas"},
                    {"Tipo de Instalación": "Pública Concurrencia", "Límite MTD": "No permite MTD", "Exige Proyecto": "Siempre Proyecto Técnico"},
                    {"Tipo de Instalación": "Recarga IRVE exterior / interior", "Límite MTD": "Ext ≤ 10 kW / Int ≤ 50 kW", "Exige Proyecto": "Ext > 10 kW / Int > 50 kW"}
                ])
                st.dataframe(df_proy, use_container_width=True, hide_index=True)

            with col_ind2:
                st.markdown("#### Protocolo de Ensayos Previos Reglamentarios (ITC-BT-05):")
                df_ens = pd.DataFrame([
                    {"Ensayo / Verificación": "Continuidad Conductores PE", "Límite REBT": "R ≤ 0.50 Ω", "Estado Conforme": "≤ 0.50 Ω"},
                    {"Ensayo / Verificación": "Resistencia de Aislamiento a 500Vcc", "Límite REBT": "R ≥ 1.00 MΩ", "Estado Conforme": "≥ 1.00 MΩ"},
                    {"Ensayo / Verificación": "Resistencia de Bucle de Tierra Rt", "Límite REBT": "Rt · IΔn ≤ 24 V", "Estado Conforme": "Rt ≤ 15 Ω"},
                    {"Ensayo / Verificación": "Corriente de Disparo Diferencial", "Límite REBT": "IΔn ≤ 30 mA", "Estado Conforme": "15 a 30 mA"},
                    {"Ensayo / Verificación": "Tiempo de Disparo Diferencial", "Límite REBT": "t ≤ 300 ms", "Estado Conforme": "< 40 ms"},
                ])
                st.dataframe(df_ens, use_container_width=True, hide_index=True)

    # =========================================================================
    # 16. PUNTOS DE LUZ Y TOMAS MÁXIMAS POR CIRCUITO (ITC-BT-25)
    # =========================================================================
    elif tabla_id in ["tab_puntos_luz_tomas_maximas", "tab_circuitos_vivienda_bt25"]:
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">💡 Puntos de Luz y Tomas de Corriente Máximas por Circuito (ITC-BT-25 Tabla 1)</h3></div>', unsafe_allow_html=True)
        st.caption("Límites reglamentarios para viviendas residenciales y desdoblamiento obligatorio de circuitos (C12).")
        with st.container(border=True):
            df_pts = pd.DataFrame([
                {"Circuito": "C1 - Iluminación General", "PIA (A)": "10 A", "Sección Mín. (mm²)": "1.5 mm² Cu", "Tubo Mín.": "Ø 16 mm (M16/M20)", "Máximo Puntos Admitidos": "Hasta 30 puntos de luz", "Criterio de Desdoblamiento": "Si se superan 30 puntos de luz, instalar un segundo circuito C1 (o C12)."},
                {"Circuito": "C2 - Tomas de Uso General", "PIA (A)": "16 A", "Sección Mín. (mm²)": "2.5 mm² Cu", "Tubo Mín.": "Ø 20 mm (M20)", "Máximo Puntos Admitidos": "Hasta 20 tomas de corriente", "Criterio de Desdoblamiento": "Si se superan 20 tomas de uso general, desdoblar en otro circuito C2 (o C12)."},
                {"Circuito": "C3 - Cocina y Horno", "PIA (A)": "25 A", "Sección Mín. (mm²)": "6.0 mm² Cu", "Tubo Mín.": "Ø 25 mm (M25)", "Máximo Puntos Admitidos": "Hasta 2 tomas (Vitrocerámica + Horno)", "Criterio de Desdoblamiento": "Circuito exclusivo de gran potencia."},
                {"Circuito": "C4 - Lavadora, Lavavajillas, Termo", "PIA (A)": "20 A (o 3x16A)", "Sección Mín. (mm²)": "4.0 mm² Cu (o 3x2.5mm²)", "Tubo Mín.": "Ø 20 mm (M20)", "Máximo Puntos Admitidos": "Hasta 3 tomas dedicadas", "Criterio de Desdoblamiento": "Recomendable desdoblar en C4.1 (Lavadora), C4.2 (Lavavajillas) y C4.3 (Termo) con PIAs de 16A."},
                {"Circuito": "C5 - Baño y Auxiliar Cocina", "PIA (A)": "16 A", "Sección Mín. (mm²)": "2.5 mm² Cu", "Tubo Mín.": "Ø 20 mm (M20)", "Máximo Puntos Admitidos": "Hasta 6 tomas", "Criterio de Desdoblamiento": "Si se superan 6 tomas entre baños y bancada de cocina, añadir circuito adicional."},
                {"Circuito": "C8 - Calefacción Eléctrica", "PIA (A)": "25 A", "Sección Mín. (mm²)": "6.0 mm² Cu", "Tubo Mín.": "Ø 25 mm (M25)", "Máximo Puntos Admitidos": "Hasta 5.750 W por circuito", "Criterio de Desdoblamiento": "Desdoblar si la potencia total de radiadores/emisores supera 5.750 W."},
                {"Circuito": "C9 - Aire Acondicionado / Clima", "PIA (A)": "25 A (o 16A)", "Sección Mín. (mm²)": "6.0 mm² (o 2.5 mm²)", "Tubo Mín.": "Ø 25 mm (M25)", "Máximo Puntos Admitidos": "Hasta 5.750 W (o 1 unidad)", "Criterio de Desdoblamiento": "1 circuito por unidad exterior centralizada o splits de gran potencia."},
                {"Circuito": "C10 - Secadora Independiente", "PIA (A)": "16 A", "Sección Mín. (mm²)": "2.5 mm² Cu", "Tubo Mín.": "Ø 20 mm (M20)", "Máximo Puntos Admitidos": "1 toma dedicada", "Criterio de Desdoblamiento": "Obligatorio si se instala secadora independiente en grado elevado."},
                {"Circuito": "C11 - Automatización / Domótica", "PIA (A)": "10 A", "Sección Mín. (mm²)": "1.5 mm² Cu", "Tubo Mín.": "Ø 16 mm (M16)", "Máximo Puntos Admitidos": "Sistema domótico / Seguridad", "Criterio de Desdoblamiento": "Circuito de control y gestión energética."},
                {"Circuito": "C12 - Circuitos Adicionales C1-C5", "PIA (A)": "Según circuito", "Sección Mín. (mm²)": "Según circuito", "Tubo Mín.": "M20 / M25", "Máximo Puntos Admitidos": "Apoyo a C1, C2, C3, C4, C5", "Criterio de Desdoblamiento": "Obligatorio en electrificación elevada cuando la vivienda > 160 m² o > 30 puntos de luz."},
                {"Circuito": "C13 - Recarga Vehículo Eléctrico", "PIA (A)": "32 A (o 16A)", "Sección Mín. (mm²)": "6.0 mm² Cu (mín 2.5)", "Tubo Mín.": "Ø 32 mm IK08", "Máximo Puntos Admitidos": "1 punto de recarga Wallbox", "Criterio de Desdoblamiento": "Circuito exclusivo ITC-BT-52 con diferencial Tipo A 6mA DC."}
            ])
            st.dataframe(df_pts, use_container_width=True, hide_index=True)

    # =========================================================================
    # 17. ALTURAS DE MECANISMOS Y CUADRO CGMP
    # =========================================================================
    elif tabla_id == "tab_alturas_mecanismos_cuadros":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">📏 Alturas Reglamentarias y Recomendadas de Mecanismos Eléctricos y Cuadros</h3></div>', unsafe_allow_html=True)
        st.caption("Cotas de replanteo en obra respecto al nivel de suelo terminado (N.S.T.) según REBT y Normativa de Accesibilidad.")
        with st.container(border=True):
            df_alt = pd.DataFrame([
                {"Elemento / Mecanismo": "Interruptores y Conmutadores de Luz", "Altura sobre Suelo Terminado (m)": "1.10 m a 1.20 m", "Distancia a Marco de Puerta": "10 a 15 cm del marco", "Observaciones Normativas": "Accesibles para personas con movilidad reducida (CTE DB-SUA)."},
                {"Elemento / Mecanismo": "Tomas de Corriente de Uso General (C2)", "Altura sobre Suelo Terminado (m)": "0.30 m (30 cm)", "Distancia a Marco de Puerta": "Libre en pared", "Observaciones Normativas": "Mínimo 20 cm sobre el suelo para evitar entrada de agua en fregonas/limpieza."},
                {"Elemento / Mecanismo": "Tomas en Bancada de Cocina (C5)", "Altura sobre Suelo Terminado (m)": "1.10 m a 1.20 m (20 cm sobre encimera)", "Distancia a Marco de Puerta": "≥ 50 cm del fregadero / placas", "Observaciones Normativas": "Prohibido instalar tomas en el plano vertical sobre la placa de cocción o el fregadero."},
                {"Elemento / Mecanismo": "Toma de Campana Extractora", "Altura sobre Suelo Terminado (m)": "1.80 m a 2.00 m", "Distancia a Marco de Puerta": "Centrada sobre eje", "Observaciones Normativas": "Oculta tras el embellecedor de la chimenea de la campana."},
                {"Elemento / Mecanismo": "Toma de Horno y Vitrocerámica (C3)", "Altura sobre Suelo Terminado (m)": "0.30 m a 0.40 m", "Distancia a Marco de Puerta": "Bajo el mueble / Zócalo", "Observaciones Normativas": "Borna de conexión de 25A o base Schuko reforzada de 25A."},
                {"Elemento / Mecanismo": "Tomas de Lavadora, Lavavajillas, Termo (C4)", "Altura sobre Suelo Terminado (m)": "0.30 m a 0.50 m (Termo: 1.60 m)", "Distancia a Marco de Puerta": "Junto a tomas de agua", "Observaciones Normativas": "La toma eléctrica debe situarse por ENCIMA o al lado de la toma de agua, nunca debajo."},
                {"Elemento / Mecanismo": "Tomas en Cabeceros de Dormitorio", "Altura sobre Suelo Terminado (m)": "0.70 m a 0.90 m (Sobre mesita)", "Distancia a Marco de Puerta": "Centradas con mesilla", "Observaciones Normativas": "Comodidad de conexión de lámparas y cargadores sin agacharse."},
                {"Elemento / Mecanismo": "Cuadro General CGMP (Mandos de Protección)", "Altura sobre Suelo Terminado (m)": "1.40 m a 2.00 m", "Distancia a Marco de Puerta": "Junto al acceso principal", "Observaciones Normativas": "El interruptor general IGA no puede estar a más de 2.00 m ni a menos de 1.40 m (ITC-BT-17)."},
                {"Elemento / Mecanismo": "Pulsador de Timbre Exterior", "Altura sobre Suelo Terminado (m)": "1.20 m a 1.40 m", "Distancia a Marco de Puerta": "Junto a jamba exterior", "Observaciones Normativas": "Protección estanca mínima IP44 si está a la intemperie."},
                {"Elemento / Mecanismo": "Termostato de Climatización", "Altura sobre Suelo Terminado (m)": "1.50 m", "Distancia a Marco de Puerta": "Pared interior sin corrientes", "Observaciones Normativas": "Lejos de fuentes de calor directo, radiadores o rayos de sol."}
            ])
            st.dataframe(df_alt, use_container_width=True, hide_index=True)

    # =========================================================================
    # 18. VOLÚMENES EN BAÑOS Y DUCHAS (ITC-BT-27)
    # =========================================================================
    elif tabla_id == "tab_volumenes_banos_duchas":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🚿 Volúmenes de Prohibición y Protección en Cuartos de Baño (ITC-BT-27)</h3></div>', unsafe_allow_html=True)
        st.caption("Requisitos de estanqueidad (IP), mecanismos admitidos y prohibiciones en locales con bañera o ducha.")
        with st.container(border=True):
            df_banos = pd.DataFrame([
                {"Volumen": "Volumen 0 (Interior de la bañera o plato de ducha)", "Grado IP Exigido": "IPX7", "Tensión Máxima Admitida": "MBTS ≤ 12 V ca o ≤ 30 V cc", "Mecanismos Permitidos": "PROHIBIDO todo tipo de interruptores, tomas o empalmes. Solo aparatos fijos sumergibles con fuente MBTS fuera del volumen."},
                {"Volumen": "Volumen 1 (Sobre la bañera hasta 2.25 m de altura)", "Grado IP Exigido": "IPX4 (IPX5 con chorro de agua)", "Tensión Máxima Admitida": "MBTS ≤ 12 V ca o ≤ 30 V cc", "Mecanismos Permitidos": "PROHIBIDO interruptores y tomas de corriente. Solo calentadores de agua fijos o bombas de hidromasaje homologadas."},
                {"Volumen": "Volumen 2 (0.60 m alrededor del Volumen 1 hasta 2.25 m)", "Grado IP Exigido": "IPX4 (IPX5 en baños públicos)", "Tensión Máxima Admitida": "MBTS ≤ 12 V ca / 230 V con trafo", "Mecanismos Permitidos": "PROHIBIDO tomas de corriente convencionales. Solo se admiten tomas para maquinillas de afeitar con transformador de aislamiento (UNE-EN 61558-2-5)."},
                {"Volumen": "Volumen 3 / Zona Exterior (2.40 m más allá del Vol 2)", "Grado IP Exigido": "IPX1 (IPX5 si hay chorros)", "Tensión Máxima Admitida": "230 V ca con protección 30mA", "Mecanismos Permitidos": "PERMITIDO tomas de corriente e interruptores protegidos obligatoriamente por interruptor diferencial de alta sensibilidad (IΔn ≤ 30 mA)."}
            ])
            st.dataframe(df_banos, use_container_width=True, hide_index=True)

    # =========================================================================
    # 19. DISTANCIAS Y CRUZAMIENTOS CON OTROS SERVICIOS (ITC-BT-21)
    # =========================================================================
    elif tabla_id == "tab_distancias_cruzamientos_servicios":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🚰 Distancias Mínimas de Separación y Cruzamiento con Otros Servicios (ITC-BT-21 apdo. 2.4)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_dist = pd.DataFrame([
                {"Servicio Cruzado / Paralelo": "Canalizaciones de Agua", "Distancia Mínima en Paralelo": "≥ 3 cm (30 mm)", "Distancia Mínima en Cruce": "≥ 3 cm (30 mm)", "Regla de Oro en Obra": "El tubo eléctrico debe instalarse SIEMPRE por ENCIMA del tubo de agua para evitar condensaciones y goteos."},
                {"Servicio Cruzado / Paralelo": "Canalizaciones de Calefacción / Vapor", "Distancia Mínima en Paralelo": "≥ 3 cm (con aislamiento térmico) o 20 cm", "Distancia Mínima en Cruce": "≥ 3 cm (aislado térmicamente)", "Regla de Oro en Obra": "Evitar contacto directo; el calor reduce drásticamente la intensidad admisible (Iz) del cable."},
                {"Servicio Cruzado / Paralelo": "Canalizaciones de Gas (Gas Natural / GLP)", "Distancia Mínima en Paralelo": "≥ 20 cm (200 mm)", "Distancia Mínima en Cruce": "≥ 20 cm (200 mm)", "Regla de Oro en Obra": "Separación estricta de 20 cm para evitar ignición ante posibles fugas de gas."},
                {"Servicio Cruzado / Paralelo": "Telecomunicaciones / Datos (ICT)", "Distancia Mínima en Paralelo": "Tubo independiente (≥ 10 cm recomendado)", "Distancia Mínima en Cruce": "Cruce a 90º", "Regla de Oro en Obra": "PROHIBIDO compartir tubo con cables eléctricos (evita inducción y ruido electromagnético en internet/TV)."}
            ])
            st.dataframe(df_dist, use_container_width=True, hide_index=True)

    # =========================================================================
    # 20. ZANJAS SUBTERRÁNEAS (ITC-BT-07)
    # =========================================================================
    elif tabla_id == "tab_zanjas_canalizaciones_subterraneas":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🚜 Zanjas y Canalizaciones Subterráneas en Baja Tensión (ITC-BT-07)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_zanj = pd.DataFrame([
                {"Ubicación de la Zanja": "Bajo Acera o Zonas Peatonales", "Profundidad Mínima al Tubo": "≥ 0.60 m (60 cm)", "Capa de Arena de Río": "10 cm por debajo y 10 cm por encima del tubo", "Protección Mecánica": "Ladrillo macizo o rasilla / Placa de polietileno", "Banda de Señalización": "Cinta amarilla 'ATENCIÓN CABLE ELÉCTRICO' a 20 cm sobre el tubo."},
                {"Ubicación de la Zanja": "Bajo Calzada (Tráfico Rodado / Coches / Camiones)", "Profundidad Mínima al Tubo": "≥ 0.80 m (80 cm)", "Capa de Arena de Río": "10 cm por debajo y 10 cm por encima del tubo", "Protección Mecánica": "Prisma de hormigón HM-20 o tubo reforzado", "Banda de Señalización": "Cinta amarilla 'ATENCIÓN CABLE ELÉCTRICO' a 20 cm sobre el prisma."},
                {"Ubicación de la Zanja": "Cruce con otras canalizaciones subterráneas", "Profundidad Mínima al Tubo": "Separación ≥ 0.20 m (20 cm)", "Capa de Arena de Río": "Relleno compacto libre de piedras", "Protección Mecánica": "Tubo protector de doble pared", "Banda de Señalización": "Señalización en ambos márgenes del cruce."}
            ])
            st.dataframe(df_zanj, use_container_width=True, hide_index=True)

    # =========================================================================
    # 21. CÓDIGO DE COLORES CONDUCTORES (ITC-BT-19)
    # =========================================================================
    elif tabla_id == "tab_codigo_colores_conductores":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🎨 Código de Colores Normalizado para Conductores (ITC-BT-19 / UNE 21089)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            df_col = pd.DataFrame([
                {"Función del Conductor": "Fase 1 (L1)", "Color Obligatorio": "Marrón", "Uso": "Monofásico estándar y Fase 1 en trifásico."},
                {"Función del Conductor": "Fase 2 (L2)", "Color Obligatorio": "Negro", "Uso": "Fase 2 en circuitos trifásicos."},
                {"Función del Conductor": "Fase 3 (L3)", "Color Obligatorio": "Gris", "Uso": "Fase 3 en circuitos trifásicos."},
                {"Función del Conductor": "Conductor Neutro (N)", "Color Obligatorio": "Azul Claro", "Uso": "Retorno de corriente neutro. Prohibido usar para fase."},
                {"Función del Conductor": "Conductor de Protección (PE / Tierra)", "Color Obligatorio": "Verde-Amarillo (Bicolor)", "Uso": "Puesta a tierra de masas. Prohibido usar para cualquier otro fin."},
                {"Función del Conductor": "Vueltas de Conmutada / Cruzamiento", "Color Recomendado": "Marrón, Negro o Gris", "Uso": "Nunca usar Azul ni Verde-Amarillo para retornos o vueltas de pulsador."}
            ])
            st.dataframe(df_col, use_container_width=True, hide_index=True)

    # =========================================================================
    # 22. SEGURIDAD CONTRA INCENDIOS (CTE DB-SI / DB-SUA 4 / ITC-BT-28)
    # =========================================================================
    elif tabla_id in ["tab_cables_resistentes_fuego_as_plus", "tab_alumbrado_emergencia_luxes", "tab_locales_publica_concurrencia_bt28"]:
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🚨 Seguridad Contra Incendios, Cables AS+ y Alumbrado de Emergencia</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_seg1, col_seg2 = st.columns(2)
            with col_seg1:
                st.markdown("#### Cables Resistentes al Fuego AS+ (SZ1-K / UNE-EN 50200):")
                df_as = pd.DataFrame([
                    {"Servicio Crítico": "Bombas contra incendios", "Exigencia": "PH 120 (Resiste 120 min a 840 ºC)", "Tipo de Cable": "SZ1-K (AS+)"},
                    {"Servicio Crítico": "Extracción y ventilación de humos en garaje", "Exigencia": "PH 90 / PH 120", "Tipo de Cable": "SZ1-K (AS+)"},
                    {"Servicio Crítico": "Alumbrado de evacuación centralizado", "Exigencia": "PH 90 (90 minutos de servicio)", "Tipo de Cable": "SZ1-K (AS+)"},
                ])
                st.dataframe(df_as, use_container_width=True, hide_index=True)

            with col_seg2:
                st.markdown("#### Niveles de Iluminancia de Emergencia (CTE DB-SUA 4):")
                df_lux = pd.DataFrame([
                    {"Zona / Emplazamiento": "Rutas de evacuación (Eje central a nivel de suelo)", "Iluminancia Mínima": "≥ 1 lux", "Autonomía Mínima": "1 hora (60 min)"},
                    {"Zona / Emplazamiento": "Puntos de primeros auxilios y extintores", "Iluminancia Mínima": "≥ 5 lux", "Autonomía Mínima": "1 hora (60 min)"},
                    {"Zona / Emplazamiento": "Cuadros Generales CGMP y salas de contadores", "Iluminancia Mínima": "≥ 5 lux", "Autonomía Mínima": "1 hora (60 min)"},
                ])
                st.dataframe(df_lux, use_container_width=True, hide_index=True)

    # =========================================================================
    # 23. AUTOCONSUMO SOLAR FOTOVOLTAICO (RD 244/2019 / ITC-BT-40)
    # =========================================================================
    elif tabla_id == "tab_autoconsumo_fotovoltaico_bt40":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">☀️ Autoconsumo Solar Fotovoltaico y Protecciones (RD 244/2019 / ITC-BT-40)</h3></div>', unsafe_allow_html=True)
        st.caption("Requisitos técnicos reglamentarios para instalaciones generadoras en baja tensión conectadas a red interior.")
        with st.container(border=True):
            col_pv1, col_pv2 = st.columns(2)
            with col_pv1:
                st.markdown("#### Modalidades de Autoconsumo y Trámites:")
                df_pv_mod = pd.DataFrame([
                    {"Modalidad": "Sin Excedentes", "Inyección a Red": "0 W (Inyección Cero)", "Dispositivo Antivertido": "Obligatorio certificado UNE 21721-1", "Tramitación": "Solo MTD / CIE ante Industria"},
                    {"Modalidad": "Con Excedentes (Compensación)", "Inyección a Red": "Permite vertido a red (P ≤ 100 kW)", "Contrato de Compensación": "Acuerdo con Comercializadora", "Tramitación": "CIE + CAU (Código Autoconsumo)"},
                    {"Modalidad": "Con Excedentes (No compensación)", "Inyección a Red": "Venta de energía en mercado", "Representación": "Requiere alta en RAIPRE", "Tramitación": "CIE + RAIPRE + Distribuidora"}
                ])
                st.dataframe(df_pv_mod, use_container_width=True, hide_index=True)

            with col_pv2:
                st.markdown("#### Protecciones Reglamentarias Obligatorias:")
                df_pv_prot = pd.DataFrame([
                    {"Protección": "Interruptor Magnetotérmico (AC)", "Requisito": "Curva C omnipolar dimensionado a corriente máxima de inversor (1.25 · In)."},
                    {"Protección": "Interruptor Diferencial (AC)", "Requisito": "Tipo B para inversores trifásicos o Tipo A superinmunizado con separación galvánica."},
                    {"Protección": "Sobretensiones Transitorias (DPS)", "Requisito": "Tipo 1+2 en continua (DC hasta 1.000 V) y Tipo 2 en alterna (AC 230/400 V)."},
                    {"Protección": "Relé de Interconexión (Anti-isla)", "Requisito": "Protección de frecuencia (81O/81U) y tensión (59/27) integrada según UNE 217001."},
                    {"Protección": "Puesta a Tierra de Estructura", "Requisito": "Conductor de cobre de 16 mm² (desnudo) o 6 mm² (aislado) a la tierra general."}
                ])
                st.dataframe(df_pv_prot, use_container_width=True, hide_index=True)

    # =========================================================================
    # 24. GRADOS DE PROTECCIÓN IP E IMPACTO MECÁNICO IK
    # =========================================================================
    elif tabla_id == "tab_grados_proteccion_ip_ik":
        st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🛡️ Grados de Protección IP (UNE-EN 60529) e Impacto Mecánico IK (UNE-EN 62262)</h3></div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_ip, col_ik = st.columns(2)
            with col_ip:
                st.markdown("#### Grados IP (Protección contra Polvo y Agua):")
                df_ip = pd.DataFrame([
                    {"Grado IP": "IP20", "Protección Polvo / Sólidos": "Objetos > 12.5 mm (Dedos)", "Protección Agua": "Sin protección", "Uso Típico": "Mecanismos interiores de vivienda"},
                    {"Grado IP": "IP44", "Protección Polvo / Sólidos": "Objetos > 1.0 mm (Hilos)", "Protección Agua": "Salpicaduras de agua", "Uso Típico": "Patios cubiertos, cuartos húmedos"},
                    {"Grado IP": "IP54", "Protección Polvo / Sólidos": "Protegido contra polvo", "Protección Agua": "Salpicaduras directas", "Uso Típico": "Cuadros en garajes y naves"},
                    {"Grado IP": "IP55", "Protección Polvo / Sólidos": "Protegido contra polvo", "Protección Agua": "Chorros de agua en boquilla", "Uso Típico": "Cajas y mecanismos de intemperie"},
                    {"Grado IP": "IP65 / IP66", "Protección Polvo / Sólidos": "Totalmente estanco al polvo", "Protección Agua": "Chorros potentes / Olas de mar", "Uso Típico": "Alumbrado exterior e industrial"},
                    {"Grado IP": "IP67 / IP68", "Protección Polvo / Sólidos": "Totalmente estanco al polvo", "Protección Agua": "Inmersión temporal / Continua", "Uso Típico": "Arquetas sumergidas y piscinas"}
                ])
                st.dataframe(df_ip, use_container_width=True, hide_index=True)

            with col_ik:
                st.markdown("#### Grados IK (Resistencia al Impacto Mecánico):")
                df_ik = pd.DataFrame([
                    {"Código IK": "IK02", "Energía de Impacto": "0.20 Joules", "Equivalencia de Golpe": "Caída de 200 g desde 10 cm", "Exigencia": "Mecanismos interiores"},
                    {"Código IK": "IK07", "Energía de Impacto": "2.00 Joules", "Equivalencia de Golpe": "Caída de 500 g desde 40 cm", "Exigencia": "Canalizaciones estándar"},
                    {"Código IK": "IK08", "Energía de Impacto": "5.00 Joules", "Equivalencia de Golpe": "Caída de 1.7 kg desde 30 cm", "Exigencia": "Obligatorio en recarga IRVE y cajas CGP"},
                    {"Código IK": "IK09", "Energía de Impacto": "10.00 Joules", "Equivalencia de Golpe": "Caída de 5.0 kg desde 20 cm", "Exigencia": "Zonas de riesgo de impacto"},
                    {"Código IK": "IK10", "Energía de Impacto": "20.00 Joules", "Equivalencia de Golpe": "Caída de 5.0 kg desde 40 cm", "Exigencia": "Máxima protección antivandálica"}
                ])
                st.dataframe(df_ik, use_container_width=True, hide_index=True)
    else:
        st.info("Selecciona una tabla en el índice superior para ver su contenido técnico detallado.")


# =============================================================================
# 🤖 ASISTENTE DIDÁCTICO IA: EXPLICACIÓN PASO A PASO DE CADA TABLA
# =============================================================================
def _renderizar_explicacion_ia(tabla_id: str):
    explicaciones = {
        "tab_iz_cobre_aluminio": {
            "proposito": "La **Intensidad Admisible ($I_z$)** es la corriente máxima en amperios que un cable puede transportar de forma continuada sin superar su temperatura límite de servicio (90 ºC en XLPE/EPR o 70 ºC en PVC). Proteger el cable es evitar que el aislante se funda y provoque un incendio.",
            "columnas": [
                ("Sección Normalizada (mm²)", "Grosor del alma conductora del cable según la serie normalizada (1.5, 2.5, 4, 6, 10, 16, 25, 35...)."),
                ("Intensidad Admisible Iz (A)", "Amperios máximos que soporta el cable en condiciones de referencia (40 ºC al aire en B1/B2 o 25 ºC en zanja D)."),
                ("Potencia Máx. Monofásica / Trifásica", "Potencia en kW que transporta esa corriente a 230 V ($P = V \\cdot I$) o a 400 V ($P = \\sqrt{3} \\cdot V \\cdot I$)."),
                ("PIA Máximo Recomendado", "Calibre del interruptor automático para cumplir la regla de oro: $I_b \\le I_n \\le I_z$.")
            ],
            "error_tipico": "Elegir el interruptor automático mayor que la $I_z$ corregida del cable. Por ejemplo, si un cable de 2.5 mm² en una roza tiene $I_z = 18.5\\text{ A}$ por calor y se protege con un PIA de 20A, el cable se quemará antes de que el PIA salte.",
            "ejemplo": "En una vivienda con cable de 6 mm² XLPE (RZ1-K) bajo tubo empotrado (B1), su $I_z$ es **40 A**. El PIA reglamentario a instalar es de **25 A** o **32 A** (según el circuito C3 o C9), garantizando que $I_n \\le I_z$ con amplio margen térmico."
        },
        "tab_factores_temperatura": {
            "proposito": "Si la temperatura real del lugar donde discurre el cable es superior a la base (40 ºC en aire o 25 ºC enterrado), el cable disipa menos calor y su capacidad de transporte se reduce mediante el factor $f_t$.",
            "columnas": [
                ("Temp. Ambiente (ºC)", "Temperatura real del aire circundante o del terreno."),
                ("XLPE / EPR (90ºC)", "Factor reductor para cables termoestables (RZ1-K, Afumex). Soportan mejor las altas temperaturas."),
                ("PVC (70ºC)", "Factor reductor para termoplásticos (H07V-K). A 50 ºC pierden casi el 20% de su capacidad.")
            ],
            "error_tipico": "Tirar cables por falsos techos bajo chapa en naves industriales en Murcia o Andalucía donde en verano se alcanzan 50 ºC sin aplicar el factor $f_t = 0.90$ en XLPE o $0.82$ en PVC.",
            "ejemplo": "Un cable RZ1-K de 16 mm² ($I_z = 76\\text{ A}$ a 40 ºC) instalado en una nave a 50 ºC: $I_z' = 76 \\cdot 0.90 = \\mathbf{68.4\\text{ A}}$. Si pones un IGA de 70A o mayor, el cable se sobrecalentará."
        },
        "tab_factores_agrupamiento": {
            "proposito": "Cuando varios circuitos van juntos en el mismo tubo, canal o bandeja, el calor que desprende cada uno calienta a los vecinos. El factor $f_a$ reduce la corriente permitida para evitar sobrecalentamiento colectivo.",
            "columnas": [
                ("Nº de Circuitos agrupados", "Cantidad de líneas que discurren en contacto físico dentro de la misma canalización."),
                ("En tubo empotrado / superficie", "El confinamiento térmico es máximo ($f_a = 0.80$ para 2 circuitos, $0.70$ para 3, $0.65$ para 4)."),
                ("En bandeja perforada", "Al tener mejor ventilación natural, el factor de reducción es más suave ($f_a = 0.88$ para 2 circuitos).")
            ],
            "error_tipico": "Aprovechar un solo tubo corrugado de 25 mm para pasar la línea de la vitrocerámica (C3) y la del horno/lavadora (C4). Al ir juntos, $f_a = 0.80$, reduciendo un 20% la capacidad de ambos cables.",
            "ejemplo": "Línea de 2.5 mm² ($I_z = 21\\text{ A}$). Si metemos 3 circuitos por el mismo tubo: $I_z' = 21 \\cdot 0.70 = \\mathbf{14.7\\text{ A}}$. Como $14.7\\text{ A} < 16\\text{ A}$, un PIA estándar de 16A ya no protegería el cable adecuadamente."
        },
        "tab_curvas_disparo_magneto": {
            "proposito": "Los interruptores automáticos protegen contra sobrecargas (lámina bimetálica lenta) y cortocircuitos (bobina magnética instantánea). La **curva de disparo** define a cuántas veces su corriente nominal ($I_n$) actúa el disparo magnético instantáneo.",
            "columnas": [
                ("Curva B (3 a 5 · In)", "Ultra rápida. Se usa para líneas muy largas con baja corriente de cortocircuito o generadores."),
                ("Curva C (5 a 10 · In)", "Uso general estándar en viviendas, locales comerciales, tomas de corriente y alumbrado."),
                ("Curva D (10 a 20 · In)", "Lenta ante picos de arranque. Diseñada para motores pesados, bombas, compresores y transformadores.")
            ],
            "error_tipico": "Instalar un PIA de Curva C para un compresor de aire acondicionado industrial o bomba de pozo con gran punta de arranque. El automático saltará falsamente cada vez que arranque el motor.",
            "ejemplo": "Una bomba sumergible con $I_n = 10\\text{ A}$ tiene un pico de arranque de $120\\text{ A}$ ($12 \\cdot I_n$). Un automático Curva C (salta entre 50A y 100A) disparará en el arranque; un Curva D (salta entre 100A y 200A) soportará el arranque sin saltar."
        },
        "tab_tipos_diferenciales": {
            "proposito": "Los diferenciales detectan fugas de corriente a tierra para salvar vidas. Los electrodomésticos modernos con electrónica (inverter, placas de inducción, cargadores VE) generan corrientes de fuga no sinusoidales que ciegan a los diferenciales antiguos.",
            "columnas": [
                ("Tipo AC", "Solo detecta fugas de corriente alterna senoidal pura (50 Hz). En desuso progresivo."),
                ("Tipo A", "Detecta alterna y pulsante con componente continua. Obligatorio en viviendas modernas e inducción."),
                ("Tipo A con RDC-DD (6mA DC)", "Obligatorio en recarga de vehículo eléctrico (ITC-BT-52) para evitar saturación del toroide por fugas DC."),
                ("Tipo B", "Detecta alterna, pulsante y corriente continua pura. Exigido en variadores trifásicos y solar trifásica.")
            ],
            "error_tipico": "Poner un diferencial Tipo AC económico para una estación Wallbox de vehículo eléctrico. Industria y las ITCs exigen diferencial Tipo A + 6mA DC o Tipo B; con Tipo AC la instalación queda no conforme.",
            "ejemplo": "En un punto de recarga de 7.4 kW (32A), se instala un diferencial 2P 40A 30mA Tipo A junto con un protector de 6 mA DC (o un Wallbox con sensor RDC-DD integrado certificado IEC 62955)."
        },
        "tab_puntos_luz_tomas_maximas": {
            "proposito": "La **ITC-BT-25 Tabla 1** fija el límite reglamentario de receptores por circuito para evitar que una sobrecarga o avería deje a oscuras o sin servicio toda la vivienda.",
            "columnas": [
                ("Circuito C1 (Iluminación)", "Máximo 30 puntos de luz con cable 1.5 mm² y PIA 10A."),
                ("Circuito C2 (Tomas uso general)", "Máximo 20 tomas de corriente con cable 2.5 mm² y PIA 16A."),
                ("Circuito C5 (Baños y bancada cocina)", "Máximo 6 tomas con cable 2.5 mm² y PIA 16A."),
                ("Circuito C12 (Adicionales)", "Circuito de apoyo obligatorio cuando se superan los límites anteriores o vivienda > 160 m².")
            ],
            "error_tipico": "Conectar 36 ojos de buey LED al mismo circuito C1 creyendo que 'como gastan poco LED no pasa nada'. El REBT limita el **número físico de puntos** (máximo 30), no los vatios. Es falta en inspección.",
            "ejemplo": "Un unifamiliar con 42 puntos de luz y 28 enchufes de uso general requiere: **2 circuitos C1** (o C1 + C12 de 10A con máx. 30 cada uno) y **2 circuitos C2** (o C2 + C12 de 16A con máx. 20 cada uno)."
        },
        "tab_alturas_mecanismos_cuadros": {
            "proposito": "Garantiza la ergonomía, la accesibilidad para personas con movilidad reducida (CTE DB-SUA) y la seguridad frente a inundaciones o fuentes de agua y calor.",
            "columnas": [
                ("Interruptores (1.10 a 1.20 m)", "A 10-15 cm del marco de la puerta para accionamiento intuitivo sin mirar."),
                ("Tomas de corriente (0.30 m)", "Mínimo 20 cm sobre el suelo para evitar entrada de agua de limpieza / fregonas."),
                ("Bancada Cocina (1.10 a 1.20 m)", "A 20 cm sobre encimera y a más de 50 cm de fuegos y fregadero."),
                ("Cuadro General CGMP (1.40 a 2.00 m)", "El interruptor IGA no puede estar a más de 2.00 m ni a menos de 1.40 m (ITC-BT-17).")
            ],
            "error_tipico": "Poner una base de enchufe en el plano vertical sobre la placa de inducción o a menos de 50 cm del grifo del fregadero. El vapor de cocción y el agua degradan el aislamiento y disparan el diferencial.",
            "ejemplo": "En la cocina, el enchufe del horno se monta en zócalo bajo mueble a 0.30 m; los enchufes de batidora y tostador se montan a 1.15 m (sobre encimera); y el enchufe de la campana se coloca a 1.90 m oculto tras el embellecedor."
        },
        "tab_volumenes_banos_duchas": {
            "proposito": "El agua reduce drásticamente la resistencia del cuerpo humano, haciendo que un contacto a 230 V sea mortal. La **ITC-BT-27** divide el baño en 4 volúmenes con protecciones muy estrictas.",
            "columnas": [
                ("Volumen 0 (Interior bañera/ducha)", "Prohibido cualquier mecanismo. Solo aparatos sumergibles MBTS ≤ 12V con fuente fuera."),
                ("Volumen 1 (Sobre bañera hasta 2.25 m)", "Prohibido interruptores y tomas. Solo calentadores fijos homologados IPX4."),
                ("Volumen 2 (0.60 m alrededor del Vol 1)", "Prohibido tomas estándar. Solo tomas con trafo de aislamiento para afeitadora."),
                ("Volumen 3 (2.40 m más allá del Vol 2)", "Permitidas tomas e interruptores si están protegidos con diferencial de 30 mA.")
            ],
            "error_tipico": "Colocar el interruptor del espejo o un enchufe para el secador a 40 cm del borde del plato de ducha (dentro de Volumen 2). Debe estar a más de **60 cm** del borde de la ducha.",
            "ejemplo": "En un baño con plato de ducha a ras de suelo: se mide 0.60 m desde el borde exterior del plato. Toda esa franja es Volumen 2 (IPX4, sin enchufes). A partir de 0.61 m entramos en Volumen 3, donde ya podemos colocar la toma del secador protegida por el diferencial de 30 mA."
        },
        "tab_ide_cgp_cpm_enlace_ni76": {
            "proposito": "La distribuidora **i-DE (Iberdrola)** establece en sus Normas Particulares (NI 76.01.01 y NI 72.30.01) las envolventes y bases fusibles homologadas para conectar la red de distribución con la instalación del usuario.",
            "columnas": [
                ("CPM-1 / CPM-3", "Cajas de Protección y Medida para 1 usuario en fachada (CPM-1 monofásica hasta 63A, CPM-3 trifásica hasta 63A / 43.6 kW)."),
                ("CGP-7 (100A / 160A)", "Caja General con bases BTVC NH00 para edificios pequeños de hasta 12 suministros."),
                ("CGP-9 (250A) y CGP-11 (400A)", "Cajas Generales con bases NH1 / NH2 para medianos y grandes edificios residenciales.")
            ],
            "error_tipico": "Montar la CGP a 2.20 m de altura en fachada o no usar bases tripolares verticales BTVC con maneta de accionamiento en carga. El inspector de Iberdrola rechazará el enganche.",
            "ejemplo": "Un edificio de 10 viviendas con LGA trifásica de 35 mm² Cu: se instala una hornacina en fachada a 0.80 m de altura con una caja **CGP-7-160** equipada con 3 fusibles de **100 A gG tamaño NH00** y cuchilla amovible de neutro."
        },
        "tab_ide_medida_indirecta_trafor_ni42": {
            "proposito": "Cuando la potencia supera los **43.64 kW** (o más de 63 A en 400V), los contadores electrónicos no pueden medir directamente la corriente sin quemarse. Se intercalan **Transformadores de Intensidad (TI)** que reducen la corriente a una escala de 0 a 5 A.",
            "columnas": [
                ("Potencia > 43.64 kW", "Límite reglamentario que obliga al paso de medida directa a medida indirecta."),
                ("Relación TI (100/5A a 600/5A)", "Proporción de transformación. Un trafo 100/5A convierte 100A reales en 5A en el secundario."),
                ("Clase 0.5S", "Clase de precisión obligatoria según UNE-EN 62053-22 para facturación legal de energía."),
                ("Bloque de Pruebas de 10 Bornas", "Dispositivo precintable que permite a Iberdrola puentear la corriente para cambiar el contador sin cortar la luz.")
            ],
            "error_tipico": "Conectar el secundario de los TI con cable de 1.5 mm² o no cortocircuitar los bornes secundarios al desconectar el contador. En circuito abierto, un TI genera miles de voltios y explota.",
            "ejemplo": "Un taller mecánico contratando 60 kW (86.6 A a 400V): se instalan 3 trafos TI de relación **100/5 A Clase 0.5S**, cable de cobre blindado de **2.5 mm²** hasta la caja de medida, y bloque de pruebas de 10 bornas precintable de i-DE."
        },
        "tab_autoconsumo_fotovoltaico_bt40": {
            "proposito": "El **RD 244/2019** y la **ITC-BT-40** regulan la generación distribuida en baja tensión para garantizar que un panel solar no electrocute a los operarios de la distribuidora cuando haya un corte de luz en la calle.",
            "columnas": [
                ("Modalidad Sin Excedentes", "Inyección Cero. Obligatorio sensor de vertido con homologación UNE 21721-1."),
                ("Modalidad Con Excedentes", "Permite verter energía sobrante a la red para compensación en factura o venta en mercado."),
                ("Relé Anti-isla", "Desconecta el inversor en menos de 0.2 segundos si la red de la calle se cae (seguridad para operarios)."),
                ("Diferencial Tipo B o A", "Protege contra corrientes continuas procedentes de los paneles solares fotovoltaicos.")
            ],
            "error_tipico": "Instalar un diferencial convencional Tipo AC en la salida del inversor o no conectar la estructura de aluminio de los paneles solares a la toma de tierra del edificio con cable de 16 mm².",
            "ejemplo": "Instalación de 5 kW monofásica: inversor solar de 5 kW con vertido cero certificado UNE 21721-1, protegido con PIA 2P 25A curva C, Diferencial 2P 40A 30mA Tipo A Superinmunizado, protector de sobretensiones transitorias Tipo 1+2 en DC y tierra equipotencial de 16 mm² a la estructura."
        }
    }

    info = explicaciones.get(tabla_id, None)

    if not info:
        st.info("🤖 **Asistente IA:** Esta tabla contiene parámetros reglamentarios oficiales del REBT y normativas complementarias. Selecciona una tabla en el visor para obtener la guía detallada paso a paso.")
        return

    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🧠 Guía Didáctica Oficial Explicada por el Asistente Experto IA</h4></div>', unsafe_allow_html=True)

    col_e1, col_e2 = st.columns([3, 2])

    with col_e1:
        with st.container(border=True):
            st.markdown(f"#### 🎯 ¿Qué es y para qué sirve esta tabla?\n{info['proposito']}")
            st.markdown("#### 🔍 Cómo interpretar cada columna:")
            for col_nom, col_desc in info["columnas"]:
                st.markdown(f"- **{col_nom}:** {col_desc}")

    with col_e2:
        with st.container(border=True):
            st.error(f"⚠️ **El Fallo Típico en la Calle / Obra:**\n\n{info['error_tipico']}")
            st.success(f"🧮 **Ejemplo de Aplicación Real:**\n\n{info['ejemplo']}")


# =============================================================================
# 💡 CONSULTOR EXPERTO IA: PREGUNTAS FRECUENTES Y CASOS REALES DE OBRA
# =============================================================================
def _renderizar_consultor_ia(tabla_id: str):
    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">💡 Consultor Inteligente de Casos Reales en Obra</h4></div>', unsafe_allow_html=True)
    st.caption("Resuelve tus dudas técnicas de obra al instante con justificación del REBT, Normas UNE, CTE y distribuidoras (i-DE).")

    preguntas_rapidas = {
        "tab_puntos_luz_tomas_maximas": [
            "¿Puedo poner 35 focos LED en un solo circuito C1 si la potencia es muy baja?",
            "¿Cuándo es obligatorio desdoblar el circuito C4 de lavadora, lavavajillas y termo?",
            "¿Qué sección y qué PIA exige el REBT para la toma de horno y vitrocerámica (C3)?"
        ],
        "tab_alturas_mecanismos_cuadros": [
            "¿A qué altura exacta debo colocar los enchufes de la encimera de cocina?",
            "¿Qué distancia mínima debe haber entre una toma eléctrica y el fregadero o placa?",
            "¿Cuál es la altura máxima y mínima permitida para el interruptor general IGA en el cuadro?"
        ],
        "tab_volumenes_banos_duchas": [
            "¿Puedo colocar un enchufe a 45 cm del plato de ducha si tiene tapa estanca IP44?",
            "¿Dónde se puede instalar el termo eléctrico dentro del cuarto de baño?",
            "¿Qué grado de protección IP mínimo se exige para una luminaria sobre el plato de ducha?"
        ],
        "tab_ide_cgp_cpm_enlace_ni76": [
            "¿Qué caja de acometida exige Iberdrola para una vivienda unifamiliar de 9.2 kW?",
            "¿A qué altura se debe montar la caja CGP en la fachada según la norma NI 76.01?",
            "¿Qué diferencia hay entre una CPM-1 y una CGP-7 en una instalación de enlace?"
        ],
        "tab_ide_medida_indirecta_trafor_ni42": [
            "¿A partir de qué potencia contratada exige Iberdrola transformadores de intensidad TI?",
            "¿Qué sección debe tener la manguera que une los TI con el bloque de pruebas?",
            "¿Por qué es obligatorio precintar el bloque de pruebas de 10 bornas?"
        ],
        "tab_autoconsumo_fotovoltaico_bt40": [
            "¿Qué tipo de diferencial es obligatorio instalar para un inversor solar fotovoltaico?",
            "¿Qué exige Industria para tramitar una instalación solar con vertido cero?",
            "¿Cómo se conecta la toma de tierra de los paneles solares según la ITC-BT-40?"
        ]
    }

    faqs = preguntas_rapidas.get(tabla_id, [
        "¿Cómo se aplica el factor de corrección por temperatura y agrupamiento?",
        "¿Qué caída de tensión máxima permite el REBT para esta instalación?",
        "¿Cuándo es obligatorio presentar Proyecto Técnico ante Industria en vez de MTD?"
    ])

    st.markdown("##### ⚡ Consultas Rápidas Frecuentes (Toca para ver la respuesta técnica):")
    cols_f = st.columns(len(faqs))
    for i, preg in enumerate(faqs):
        with cols_f[i]:
            if st.button(f"❓ {preg}", key=f"btn_faq_{tabla_id}_{i}", use_container_width=True):
                st.session_state[f"resp_ia_{tabla_id}"] = _generar_respuesta_ia(preg, tabla_id)

    if f"resp_ia_{tabla_id}" in st.session_state:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(st.session_state[f"resp_ia_{tabla_id}"])

    st.divider()

    # Formulario de Consulta Libre
    st.markdown("##### 💬 Plantea tu Caso o Duda Concreta de Obra al Asistente IA:")
    col_in, col_bt = st.columns([4, 1])
    with col_in:
        duda_usuario = st.text_input("Escribe tu duda técnica (ej: 'Tengo un local de 90 m², ¿qué potencia mínima debo prever?' o '¿Qué tubo pongo para 5 cables de 6 mm²?'):", key=f"input_duda_{tabla_id}")
    with col_bt:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        enviar_duda = st.button("🚀 Consultar IA", key=f"btn_enviar_duda_{tabla_id}", type="primary", use_container_width=True)

    if enviar_duda and duda_usuario:
        resp = _generar_respuesta_ia(duda_usuario, tabla_id)
        st.session_state[f"resp_ia_{tabla_id}"] = resp
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(resp)


def _generar_respuesta_ia(pregunta: str, tabla_id: str) -> str:
    p = pregunta.lower()

    if "35 focos" in p or ("focos" in p and "c1" in p) or ("30 puntos" in p):
        return """
### 🤖 Respuesta del Asistente Técnico REBT:
**No está permitido conectar 35 puntos de luz a un único circuito C1**, aunque sean bombillas LED de 5W.

- **Fundamento Normativo:** La **ITC-BT-25 (Tabla 1, nota 1)** establece taxativamente que el número máximo de puntos de utilización por circuito C1 es de **30 puntos de luz**.
- **Solución Reglamentaria:** Se deben instalar **2 circuitos de iluminación** (un C1 principal y un circuito adicional **C12** de iluminación), cada uno con su propio magnetotérmico de **10 A** y cable de sección mínima **1.5 mm² Cu** bajo tubo de $\\varnothing 16\\text{ mm}$.
- **Criterio de Inspección:** Si un inspector de OCA o técnico de Industria revisa la memoria o la instalación física y cuenta más de 30 puntos asignados a un solo automático, emitirá una **no conformidad reglamentaria**.
"""
    elif "c4" in p or "lavadora" in p or "lavavajillas" in p or "termo" in p:
        return """
### 🤖 Respuesta del Asistente Técnico REBT:
**Desdoblamiento del Circuito C4 (Lavadora, Lavavajillas y Termo):**

- **Regla Tradicional:** El REBT permite un único circuito C4 con cable de **4.0 mm² Cu** protegido con PIA de **20 A** que alimenta las 3 tomas mediante cajas de derivación o tomas Schuko reforzadas.
- **Recomendación Profesional Actual (Guía Técnica ITC-BT-25):** Es altamente recomendable **desdoblar el C4 en 3 circuitos independientes**:
  1. **C4.1 (Lavadora):** Cable 2.5 mm² Cu con PIA de **16 A**.
  2. **C4.2 (Lavavajillas):** Cable 2.5 mm² Cu con PIA de **16 A**.
  3. **C4.3 (Termo Eléctrico):** Cable 2.5 mm² Cu con PIA de **16 A**.
- **Ventajas de Obra:** Evita problemas de apriete con cables de 4 mm² en tomas Schuko convencionales (cuyos bornes están diseñados para 2.5 mm²) y permite aislar averías individuales sin dejar sin agua caliente ni lavado toda la vivienda.
"""
    elif "encimera" in p or "fregadero" in p or "placa" in p or "cocina" in p:
        return """
### 🤖 Respuesta del Asistente Técnico REBT:
**Cotas y Separaciones de Mecanismos en Cocina (ITC-BT-25 / Guía Técnica):**

1. **Tomas de Uso General en Encimera (Circuito C5):**
   - Altura recomendada: **1.10 m a 1.20 m** respecto al suelo terminado (aprox. **15 a 20 cm sobre el plano de trabajo de la encimera**).
   - Cantidad reglamentaria: Mínimo **3 tomas** de uso general en la encimera.
2. **Distancia de Seguridad a Fregadero y Placa de Cocción:**
   - Debe mantenerse una separación horizontal mínima de **50 cm** respecto al borde de la pila del fregadero y del plano de cocción (gas, vitrocerámica o inducción).
   - **Prohibición Expresa:** Está terminantemente prohibido instalar tomas de corriente en el plano vertical situado justo sobre la placa de cocción o sobre el fregadero.
"""
    elif "iga" in p or "cuadro" in p or "altura" in p:
        return """
### 🤖 Respuesta del Asistente Técnico REBT:
**Alturas Reglamentarias del Cuadro General CGMP (ITC-BT-17 apdo. 1):**

- **Límite Superior:** La parte superior del cuadro y los dispositivos generales de mando y protección (especialmente la palanca del **IGA**) no pueden situarse a una altura superior a **2.00 metros** sobre el nivel del suelo terminado.
- **Límite Inferior:** La palanca de los dispositivos no puede estar a menos de **1.40 metros** del suelo (en viviendas accesibles o locales especiales se admite un mínimo de 1.00 m según CTE DB-SUA).
- **Ubicación:** Lo más cerca posible de la puerta de entrada principal a la vivienda o local, nunca en baños, dormitorios ni zonas de difícil acceso.
"""
    elif "45 cm" in p or ("plato" in p and "ducha" in p) or "baño" in p or "bano" in p:
        return """
### 🤖 Respuesta del Asistente Técnico REBT:
**Prohibición Estricta de Tomas a menos de 60 cm de la Ducha (ITC-BT-27):**

- **Clasificación:** El espacio comprendido entre el borde del plato de ducha y una distancia horizontal de **0.60 metros** (hasta 2.25 m de altura) es **Volumen 2**.
- **Prohibición:** En el **Volumen 2 está PROHIBIDO instalar tomas de corriente convencionales**, incluso aunque dispongan de tapa estanca IP44 o IP55. Solo se admiten tomas para máquinas de afeitar alimentadas por un transformador de aislamiento galvánico de muy baja potencia (UNE-EN 61558-2-5).
- **Dónde poner la toma:** A partir de los **0.61 metros** del borde del plato entramos en **Volumen 3**, donde sí está permitido instalar bases Schuko normales siempre que cuenten con protección diferencial de alta sensibilidad ($I_{\\Delta n} \\le 30\\text{ mA}$).
"""
    elif "iberdrola" in p or "i-de" in p or "cpm" in p or "cgp" in p or "unifamiliar" in p:
        return """
### 🤖 Respuesta del Asistente Técnico REBT / Norma i-DE:
**Requisitos de Acometida y Cajas para Unifamiliar en Zona i-DE (Norma NI 76.01.01):**

- **Caja Obligatoria:** Para un suministro individual monofásico (hasta 14.49 kW) o trifásico (hasta 43.64 kW) se instala una **Caja de Protección y Medida (CPM)**:
  - Monofásica: **CPM-1** con base portafusibles seccionable en carga tamaño **NH00** y fusible calibrado al suministro (ej. 40A, 50A o 63A $gG$).
  - Trifásica: **CPM-3** con 3 bases BTVC NH00.
- **Ubicación de Montaje:** En el límite de la propiedad / valla de fachada exterior, empotrada en nicho o adosada con acceso directo y libre desde la vía pública para los inspectores y lectores de Iberdrola.
- **Cerradura:** Obligatorio incorporar cerradura con bombillo homologado por i-DE (tipo **JIS** o **AGA** según zona).
"""
    elif "indirecta" in p or "ti" in p or "43" in p or "transformador" in p:
        return """
### 🤖 Respuesta del Asistente Técnico REBT / Norma i-DE:
**Medida Indirecta con Transformadores de Intensidad TI (Norma NI 42.71.01):**

- **Límite de Aplicación:** Obligatorio para cualquier suministro con **potencia contratada superior a 43.64 kW** (o corriente asignada superior a **63 A** a 400 V).
- **Especificaciones de los TI:**
  - Relación: Según potencia (100/5A, 150/5A, 200/5A, 300/5A, 400/5A, 600/5A).
  - Clase de precisión: **0.5S** según UNE-EN 62053-22 para facturación legal.
- **Cableado y Bloque de Pruebas:**
  - Manguera de conexión de cobre: **2.5 mm² Cu** para longitudes de hasta 5 m, o **4.0 mm² Cu** para longitudes de 5 a 10 m.
  - Bloque de pruebas: Normalizado de **10 bornas precintable** de i-DE (permite comprobaciones de tensión y corriente sin interrumpir el suministro).
"""
    elif "solar" in p or "fotovoltaic" in p or "diferencial" in p or "inversor" in p:
        return """
### 🤖 Respuesta del Asistente Técnico REBT / ITC-BT-40:
**Protecciones Obligatorias en Instalaciones Solares Fotovoltaicas (RD 244/2019):**

1. **Interruptor Magnetotérmico (AC):** Curva C omnipolar dimensionado a $1.25 \\cdot I_{max}$ del inversor.
2. **Interruptor Diferencial (AC):**
   - Para inversores trifásicos: **Tipo B** obligatorio para detectar componentes continuas puras.
   - Para inversores monofásicos: **Tipo A Superinmunizado** si el inversor dispone de aislamiento galvánico o protección integrada contra corrientes de defecto DC superiores a 6 mA (según norma UNE-EN 62109).
3. **Protección contra Sobretensiones:** Protector combinado transitorio (DPS) Tipo 1+2 en la parte continua (DC) y Tipo 2 en la parte alterna (AC).
4. **Puesta a Tierra de Estructuras:** Las estructuras metálicas de los paneles deben unirse mediante conductor de cobre de **16 mm²** (desnudo) o **6 mm²** (aislado bicolor) a la red general de tierra del edificio.
"""
    else:
        return f"""
### 🤖 Análisis Técnico del Asistente Experto IA:
**Consulta:** *"{pregunta}"*

- **Marco Reglamentario de Aplicación:** REBT (RD 842/2002), Instrucciones Técnicas Complementarias (ITC-BT), Código Técnico de la Edificación (CTE) y Normas Particulares de Distribuidora (i-DE Iberdrola).
- **Criterio Técnico del Instalador Autorizado:**
  1. **Dimensionamiento Térmico ($I_z$):** La sección del conductor debe elegirse para que la intensidad máxima admisible $I_z$ (afectada por los factores de temperatura $f_t$ y agrupamiento $f_a$) sea mayor o igual al calibre del interruptor de protección ($I_b \\le I_n \\le I_z'$).
  2. **Verificación de Caída de Tensión:** Comprobar que no se superen los límites reglamentarios (LGA $\\le 0.5\\%$, DI $\\le 1.5\\%$, Alumbrado interior $\\le 3\\%$, Fuerza $\\le 5\\%$, IRVE $\\le 1.0\\% / 1.5\\%$).
  3. **Seguridad y Accesibilidad:** Respetar las cotas de replanteo en obra, grados de protección IP/IK y volúmenes de seguridad exigidos en las tablas normativas oficiales.
- **Tramitación Oficial:** Todo cálculo y justificación debe reflejarse en la Memoria Técnica de Diseño (MTD) y en el Certificado de Instalación Eléctrica (CIE / Boletín) para su legalización telemática ante la Dirección General de Industria (DGEAIM Murcia o CCAA correspondiente).
"""



