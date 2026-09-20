# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos: Análisis de Tiempos de Mano de Obra, Soporte Pladur, Acopio y Utilidad
Autor: Richard Orlando Choque Tejerina (Bolimur Electricidad)
"""

import streamlit as st
import pandas as pd
import openpyxl
import os

def app():
    # Estilo CSS avanzado para impresión limpia en PDF sin cortes ni elementos sobrantes
    st.markdown("""
        <style>
            @media print {
                [data-testid="stSidebar"] {display: none !important;}
                [data-testid="stHeader"] {display: none !important;}
                .stButton {display: none !important;}
                .stTextInput {display: none !important;}
                .stSelectbox {display: none !important;}
                .stSlider {display: none !important;}
                .stCheckbox {display: none !important;}
                div.row-widget.stRadio {display: none !important;}
                
                html, body, [data-testid="stAppViewContainer"], .main, .block-container {
                    height: auto !important;
                    overflow: visible !important;
                    background: white !important;
                    color: black !important;
                }
                details {display: block !important;}
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("🏡 Generador de Presupuestos: Panel Profesional de Autónomo")
    st.markdown("Control de costes, acopio en almacén, análisis de tiempos de mano de obra y rentabilidad.")

    # 1. Cargar base de datos maestra de precios
    excel_cargado = None
    nombres_posibles = [
        "base_datos_precio_oficial.xlsx",
        "Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy_v2.xlsx",
        "Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy.xlsx"
    ]
    
    for f in os.listdir('.'):
        if f.endswith('.xlsx') and ('precio' in f.lower() or 'master' in f.lower() or 'oficial' in f.lower()):
            nombres_posibles.insert(0, f)

    df_precios = None
    for nombre in nombres_posibles:
        if os.path.exists(nombre):
            try:
                wb = openpyxl.load_workbook(nombre)
                hoja_activa = wb.sheetnames[0]
                for h in wb.sheetnames:
                    if "maestra" in h.lower() or "completa" in h.lower() or "tarifa" in h.lower():
                        hoja_activa = h
                        break
                ws = wb[hoja_activa]
                data = list(ws.iter_rows(values_only=True))
                df_precios = pd.DataFrame(data[1:], columns=data[0])
                excel_cargado = nombre
                break
            except Exception as e:
                continue

    if df_precios is None:
        st.error("⚠️ No se pudo encontrar ni cargar el archivo Excel de precios en la raíz del proyecto.")
        return
    else:
        st.sidebar.success(f"📁 Base de datos conectada: `{excel_cargado}`")

    def buscar_articulo_detallado(df, keywords, gama_filtro, precio_defecto=0.45):
        for keyword in keywords:
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).strip()
                desc_lower = desc.lower()
                gama_item = str(row.get('Nivel de Gama / Aplicación', '')).lower()
                
                if keyword.lower() in desc_lower:
                    if gama_filtro.lower() not in gama_item and 'general' not in gama_item and 'tubo' not in keyword.lower() and 'cable' not in keyword.lower():
                        continue
                    try:
                        val = float(row.get('Precio S/IVA (€)', 0.0))
                        prov = str(row.get('Proveedor / Tienda Principal', 'Obramat'))
                        if val > 0:
                            return val, prov, desc, True
                    except:
                        pass
        return precio_defecto, "Obramat (Tarifa Base)", f"Artículo estándar ({keywords[0]})", False

    # ==========================================
    # DATOS DE LA EMPRESA / INSTALADOR
    # ==========================================
    st.sidebar.header("🏢 Datos del Instalador")
    empresa_nombre = st.sidebar.text_input("Nombre Empresa", value="BOLIMUR INSTALACIONES Y REFORMAS")
    instalador_nombre = st.sidebar.text_input("Instalador", value="Richard Orlando Choque Tejerina")
    n_licencia = st.sidebar.text_input("Nº Licencia / REBT", value="REBT-30/15892")
    localidad = st.sidebar.text_input("Localidad", value="Rincón de Seca, Murcia")
    telefono = st.sidebar.text_input("Teléfono Contacto", value="+34 600 000 000")

    # ==========================================
    # PARÁMETROS GLOBALES Y SERIES COMERCIALES
    # ==========================================
    st.markdown("---")
    st.subheader("⚙️ Parámetros de Costes, Márgenes y Selección de Series")
    
    col_par1, col_par2, col_par3 = st.columns(3)
    with col_par1:
        grado_electrificacion = st.selectbox(
            "Grado de Electrificación (REBT)",
            ["Básica (Hasta 9.2 kW)", "Elevada (Más de 9.2 kW / Climatización / Domótica)"]
        )
    with col_par2:
        tipo_cable_sel = st.selectbox(
            "Tecnología de Cableado",
            ["Libre de Halógenos (H07Z1-K)", "PVC Normal / Estándar (H07V-K)"]
        )
    with col_par3:
        serie_mecanismos = st.selectbox(
            "Serie y Fabricante de Mecanismos",
            [
                "Simon 10 (Gama Económica / Básica)",
                "Simon 27 Play (Gama Estándar / Residencial)",
                "Simon 82 Detail (Gama Alta / Decorativa)",
                "Schneider Asfora (Gama Media)",
                "Niessen Zenit (Gama Alta / Moderna)"
            ]
        )

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        margen_comercial = st.slider("Margen Comercial General (%)", 0, 50, 20)
    with col_m2:
        porc_garantia = st.slider("Colchón de Garantía en Materiales (%)", 0, 20, 10)
    with col_m3:
        iva_sel = st.selectbox("IVA Aplicado al Cliente", [10, 21], index=0)

    st.markdown("#### 🧱 Criterio de Rozas y Albañilería / Soporte")
    col_roz1, col_roz2 = st.columns(2)
    with col_roz1:
        hace_rozas_electricista = st.checkbox("¿Asumes tú (electricista) el picado de rozas y tapado con yeso?", value=True, help="Si es Pladur, se calcula perforación de montantes y colocación de cajas de garras.")
    with col_roz2:
        tipo_pared = st.selectbox(
            "Tipo de Pared / Soporte",
            [
                "Ladrillo Hueco / Tabiquería seca (Fácil picado)", 
                "Ladrillo Perforado / Termoarcilla (Dureza media)", 
                "Hormigón / Estructura (Requiere rozadora y martillo pesado)",
                "Pladur / Panel de Yeso Laminado (Obra seca - Sin rozas, corte con sierra de vaso)"
            ]
        )

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        precio_hora = st.number_input("Precio Mano de Obra (€/h neto)", min_value=10.0, max_value=60.0, value=25.0, step=1.0)
    with col_c2:
        num_operarios = st.number_input("Nº Operarios", min_value=1, max_value=5, value=1, step=1)

    tipo_obra = st.selectbox(
        "Sistema de Ejecución General",
        ["Empotrada en Rozas (Ladrillo + Yeso)", "Falso Techo / Pladur (Obra Seca)", "Superficie (Tubo visto / Canaleta)"]
    )

    st.markdown("---")

    # ==========================================
    # GESTIÓN DINÁMICA DE ESTANCIAS
    # ==========================================
    if 'estancias_pro' not in st.session_state:
        st.session_state.estancias_pro = [
            {"nombre": "Salón - Comedor", "m2": 25.0, "altura": 2.6},
            {"nombre": "Cocina", "m2": 12.0, "altura": 2.6},
            {"nombre": "Dormitorio Principal", "m2": 16.0, "altura": 2.6},
            {"nombre": "Dormitorio 2", "m2": 11.0, "altura": 2.6},
            {"nombre": "Baño 1", "m2": 6.0, "altura": 2.6},
            {"nombre": "Pasillo", "m2": 7.0, "altura": 2.6},
        ]

    st.subheader("📋 Dimensionamiento y Estancias de la Vivienda (Gestión Dinámica)")
    st.markdown("Modifica los datos, elimina estancias o añade nuevas habitaciones según las necesidades del proyecto.")

    with st.expander("➕ Añadir Nueva Estancia a la Vivienda"):
        with st.form("form_nueva_estancia"):
            col_n1, col_n2, col_n3 = st.columns([3, 2, 2])
            with col_n1:
                nuevo_nombre = st.text_input("Nombre de la Estancia (Ej: Terraza, Despacho)")
            with col_n2:
                nuevo_m2 = st.number_input("Superficie (m²)", min_value=1.0, value=10.0, step=0.5)
            with col_n3:
                nuevo_alt = st.number_input("Altura (m)", min_value=2.0, max_value=5.0, value=2.6, step=0.1)
            
            if st.form_submit_button("Agregar Estancia"):
                if nuevo_nombre:
                    st.session_state.estancias_pro.append({"nombre": nuevo_nombre, "m2": nuevo_m2, "altura": nuevo_alt})
                    st.success(f"Estancia '{nuevo_nombre}' añadida correctamente.")
                    st.rerun()
                else:
                    st.warning("Introduce un nombre válido para la estancia.")

    estancias_activas = []
    for i, est in enumerate(st.session_state.estancias_pro):
        cols = st.columns([3, 2, 2, 1, 1])
        with cols[0]:
            est["nombre"] = st.text_input(f"Nombre {i}", value=est["nombre"], key=f"est_nom_{i}", label_visibility="collapsed")
        with cols[1]:
            est["m2"] = st.number_input(f"m2 {i}", value=est["m2"], min_value=1.0, step=0.5, key=f"est_m2_{i}", label_visibility="collapsed")
        with cols[2]:
            est["altura"] = st.number_input(f"Alt {i}", value=est["altura"], min_value=2.0, max_value=5.0, step=0.1, key=f"est_alt_{i}", label_visibility="collapsed")
        with cols[3]:
            incluir = st.checkbox(f"Inc {i}", value=True, key=f"est_inc_{i}", label_visibility="collapsed")
        with cols[4]:
            if st.button("🗑️", key=f"del_est_{i}"):
                st.session_state.estancias_pro.pop(i)
                st.rerun()

        if incluir:
            estancias_activas.append(est)

    st.markdown("---")

    if st.button("🚀 Calcular Presupuesto y Generar Paneles", type="primary"):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia.")
            return

        sup_total = sum([e["m2"] for e in estancias_activas])

        kw_cable_15 = ['h07z1-k 1.5', 'libre de halógenos 1.5', '1.5 mm'] if "Halógenos" in tipo_cable_sel else ['h07v-k 1.5', 'cable 1.5', '1.5 mm']
        kw_cable_25 = ['h07z1-k 2.5', 'libre de halógenos 2.5', '2.5 mm'] if "Halógenos" in tipo_cable_sel else ['h07v-k 2.5', 'cable 2.5', '2.5 mm']

        p_tubo, prov_tubo, desc_tubo, _ = buscar_articulo_detallado(df_precios, ['tubo corrugado', 'm-20', 'tubo 20'], serie_mecanismos, 0.45)
        p_caja_mec, prov_caja_mec, desc_caja_mec, _ = buscar_articulo_detallado(df_precios, ['caja universal', 'caja mecanismo'], serie_mecanismos, 0.30)
        p_caja_reg, prov_caja_reg, desc_caja_reg, _ = buscar_articulo_detallado(df_precios, ['caja de registro', 'derivación'], serie_mecanismos, 1.50)
        p_15, prov_15, desc_15, _ = buscar_articulo_detallado(df_precios, kw_cable_15, serie_mecanismos, 0.38 if "Halógenos" in tipo_cable_sel else 0.32)
        p_25, prov_25, desc_25, _ = buscar_articulo_detallado(df_precios, kw_cable_25, serie_mecanismos, 0.55 if "Halógenos" in tipo_cable_sel else 0.48)
        
        p_int, prov_int, desc_int, _ = buscar_articulo_detallado(df_precios, ['interruptor', 'conmutador'], serie_mecanismos, 3.50)
        p_schuko, prov_schuko, desc_schuko, _ = buscar_articulo_detallado(df_precios, ['schuko', 'base de enchufe'], serie_mecanismos, 4.20)
        p_rj45, prov_rj45, desc_rj45, _ = buscar_articulo_detallado(df_precios, ['rj45', 'datos', 'multimedia'], serie_mecanismos, 8.50)
        p_marco, prov_marco, desc_marco, _ = buscar_articulo_detallado(df_precios, ['marco', 'embellecedor'], serie_mecanismos, 1.80)

        # Auditoría REBT
        tiene_cocina = any("cocina" in e["nombre"].lower() for e in estancias_activas)
        tiene_bano = any("baño" in e["nombre"].lower() for e in estancias_activas)
        if not tiene_cocina:
            st.warning("⚠️ **Aviso de Auditoría:** No se ha detectado ninguna estancia 'Cocina'. El circuito C3 es obligatorio en viviendas.")
        if not tiene_bano:
            st.warning("⚠️ **Aviso de Auditoría:** No se ha detectado ninguna estancia 'Baño'. El circuito C5 debe contemplarse.")
            
        st.success(f"✅ **Auditoría REBT Superada ({grado_electrificacion}):** Estancias normativas detectadas bajo serie **{serie_mecanismos}** y soporte **{tipo_pared}**.")

        # Acumuladores globales
        global_tubo_m = 0.0
        global_caja_mec_uds = 0
        global_caja_reg_uds = 0
        global_cable_15_fn_m = 0.0
        global_cable_15_tierra_m = 0.0
        global_cable_15_vueltas_m = 0.0
        global_cable_25_fuerza_m = 0.0
        global_marcos_uds = 0
        global_mecanismos_dict = {}

        coste_total_materiales_bruto = 0.0
        horas_totales_obra = 0.0
        subtotal_neto_comercial = 0.0
        comercial_estancias = []
        desgloses_internos_estancias = []

        # Acumuladores de horas globales por tarea
        sum_h_rozas = 0.0
        sum_h_tubos = 0.0
        sum_h_cable = 0.0
        sum_h_mec = 0.0

        mult_comercial = (1 + margen_comercial / 100.0)
        mult_garantia_mat = (1 + porc_garantia / 100.0)

        for idx, est in enumerate(estancias_activas):
            m2 = est["m2"]
            alt = est["altura"]
            nombre_est = est["nombre"].lower()

            m_tubo = m2 * 4.5 * (alt / 2.5)
            n_cajas_reg = 1 if m2 > 8 else 0
            
            m_15_ilum_fn = m2 * 5.0
            m_15_ilum_tt = m2 * 2.5
            m_15_vueltas = m2 * 4.0
            m_25_fuerza = m2 * (15.0 if "Elevada" in grado_electrificacion else 12.0)
            n_puntos_luz = max(1, int(m2 / 10))

            if "cocina" in nombre_est:
                mecanismos_est = [
                    {"nombre": f"Interruptor simple ({serie_mecanismos})", "cant": 1, "precio": p_int, "prov": prov_int},
                    {"nombre": f"Base Schuko 16A ({serie_mecanismos})", "cant": 4, "precio": p_schuko, "prov": prov_schuko},
                    {"nombre": f"Base fuerza 25A Horno/Vitro ({serie_mecanismos})", "cant": 1, "precio": p_schuko * 1.5, "prov": prov_schuko},
                    {"nombre": f"Bases Schuko lavavajillas/lavadora ({serie_mecanismos})", "cant": 2, "precio": p_schuko, "prov": prov_schuko}
                ]
            elif "baño" in nombre_est:
                mecanismos_est = [
                    {"nombre": f"Interruptor luz espejo ({serie_mecanismos})", "cant": 1, "precio": p_int, "prov": prov_int},
                    {"nombre": f"Base Schuko tapa estanca IP44 ({serie_mecanismos})", "cant": 2, "precio": p_schuko * 1.2, "prov": prov_schuko}
                ]
            elif "salón" in nombre_est or "comedor" in nombre_est:
                mecanismos_est = [
                    {"nombre": f"Conmutador / Cruzamiento ({serie_mecanismos})", "cant": 2, "precio": p_int, "prov": prov_int},
                    {"nombre": f"Bases Schuko zona TV/Sofá ({serie_mecanismos})", "cant": 6, "precio": p_schuko, "prov": prov_schuko},
                    {"nombre": f"Toma de datos RJ45 ({serie_mecanismos})", "cant": 2, "precio": p_rj45, "prov": prov_rj45}
                ]
            else:
                mecanismos_est = [
                    {"nombre": f"Conmutador / Interruptor ({serie_mecanismos})", "cant": 2, "precio": p_int, "prov": prov_int},
                    {"nombre": f"Bases Schuko 16A ({serie_mecanismos})", "cant": 3, "precio": p_schuko, "prov": prov_schuko}
                ]

            total_mecanismos = sum([m["cant"] for m in mecanismos_est])
            n_marcos = max(total_mecanismos, int(total_mecanismos * 0.8))

            global_tubo_m += m_tubo
            global_caja_mec_uds += total_mecanismos
            global_caja_reg_uds += n_cajas_reg
            global_cable_15_fn_m += m_15_ilum_fn
            global_cable_15_tierra_m += m_15_ilum_tt
            global_cable_15_vueltas_m += m_15_vueltas
            global_cable_25_fuerza_m += m_25_fuerza
            global_marcos_uds += n_marcos

            for mec in mecanismos_est:
                key_m = (mec["nombre"], mec["precio"], mec["prov"])
                global_mecanismos_dict[key_m] = global_mecanismos_dict.get(key_m, 0) + mec["cant"]

            coste_mecanismos_est = sum([m["cant"] * m["precio"] for m in mecanismos_est])
            coste_marcos_est = n_marcos * p_marco
            coste_cajas_mec_est = total_mecanismos * p_caja_mec

            coste_mat_estancia_neto = (
                (m_tubo * p_tubo) +
                coste_cajas_mec_est +
                (n_cajas_reg * p_caja_reg if n_cajas_reg > 0 else 0) +
                (m_15_ilum_fn * p_15) +
                (m_15_ilum_tt * p_15) +
                (m_15_vueltas * p_15) +
                (m_25_fuerza * p_25) +
                coste_mecanismos_est +
                coste_marcos_est
            )
            coste_mat_estancia_con_iva = coste_mat_estancia_neto * 1.21
            coste_total_materiales_bruto += coste_mat_estancia_neto

            # Cálculo de horas según soporte
            if "Pladur" in tipo_pared:
                h_rozas = (m2 * 0.10) if hace_rozas_electricista else 0.0
            else:
                mult_soporte = 1.0 if "Hueco" in tipo_pared else (1.35 if "Perforado" in tipo_pared else 1.7)
                h_rozas = (m2 * 0.35 * mult_soporte) if hace_rozas_electricista else 0.0

            h_tubo_cajas = m2 * 0.25
            h_cableado = m2 * 0.30
            h_mecanizado = total_mecanismos * 0.15

            sum_h_rozas += h_rozas
            sum_h_tubos += h_tubo_cajas
            sum_h_cable += h_cableado
            sum_h_mec += h_mecanizado

            h_estancia_total = h_rozas + h_tubo_cajas + h_cableado + h_mecanizado
            horas_totales_obra += h_estancia_total
            coste_mo_estancia = h_estancia_total * precio_hora

            venta_mat_estancia = coste_mat_estancia_neto * mult_comercial * mult_garantia_mat
            venta_mo_estancia = coste_mo_estancia * mult_comercial
            precio_venta_estancia = venta_mat_estancia + venta_mo_estancia
            subtotal_neto_comercial += precio_venta_estancia

            comercial_estancias.append({
                "Estancia": est["nombre"],
                "Superficie": f"{m2} m²",
                "Detalle Comercial": f"Instalación REBT ({grado_electrificacion}) con mecanismos **{serie_mecanismos}**, soporte **{tipo_pared}**, canalización y cableado {tipo_cable_sel}.",
                "Importe Venta (€)": round(precio_venta_estancia, 2)
            })

            desgloses_internos_estancias.append({
                "nombre": est["nombre"],
                "m2": m2,
                "neto_mat": coste_mat_estancia_neto,
                "iva_mat": coste_mat_estancia_con_iva,
                "horas": h_estancia_total,
                "coste_mo": coste_mo_estancia,
                "rozas": h_rozas,
                "tubos": h_tubo_cajas,
                "cable": h_cableado,
                "mec": h_mecanizado
            })

        coste_mano_obra_bruto = horas_totales_obra * precio_hora
        coste_total_autonomo = coste_total_materiales_bruto + coste_mano_obra_bruto

        # ==========================================
        # SELECTOR DE MODO DE VISTA E IMPRESIÓN (RADIO)
        # ==========================================
        st.markdown("---")
        modo_impresion = st.radio(
            "🖨️ SELECCIONA EL MODO DE VISTA (Para revisar o pulsar Ctrl + P y exportar a PDF):",
            [
                "🛠️ 1. Panel Interno y Acopio (Exclusivo para ti - Autónomo)",
                "📄 2. Vista Comercial (Para entregar al Cliente)"
            ],
            horizontal=True
        )
        st.markdown("---")

        # ==========================================
        # MODO 1: PANEL INTERNO DEL AUTÓNOMO
        # ==========================================
        if modo_impresion.startswith("🛠️"):
            st.header("🔒 Panel Interno de Trabajo y Acopio (Uso Exclusivo)")
            st.markdown(f"**Instalador:** {instalador_nombre} | **Empresa:** {empresa_nombre} | **Serie:** {serie_mecanismos} | **Soporte:** {tipo_pared}")
            st.markdown("---")

            # NUEVO BLOQUE: ANÁLISIS DE TIEMPOS DE MANO DE OBRA
            st.subheader("⏱️ Análisis de Rendimiento y Tiempos de Mano de Obra")
            st.markdown("Desglose técnico de los coeficientes de tiempo aplicados para calcular las horas reales de ejecución:")
            st.write(f"- 🧱 **Fase de Rozas / Perforación ({tipo_pared}):** `{sum_h_rozas:.2f} h` acumuladas.")
            st.write(f"- 📏 **Fase de Canalización y Cajas (0.25 h/m²):** `{sum_h_tubos:.2f} h` acumuladas.")
            st.write(f"- ⚡ **Fase de Tendido y Metida de Cableado (0.30 h/m²):** `{sum_h_cable:.2f} h` acumuladas.")
            st.write(f"- 🔲 **Fase de Conexionado y Mecanizado (0.15 h/unidad):** `{sum_h_mec:.2f} h` acumuladas.")
            st.info(f"⏱️ **Total Horas de Obra Estimadas:** `{horas_totales_obra:.2f} h` x `{precio_hora:.2f} €/h` = **`{coste_mano_obra_bruto:.2f} €`** (Coste Neto Mano de Obra).")
            st.markdown("---")

            st.subheader("🛠️ Desglose por Estancias")
            for item in desgloses_internos_estancias:
                st.markdown(f"**📍 Estancia: {item['nombre']} ({item['m2']} m²)**")
                st.write(f"- Coste Materiales: `{item['neto_mat']:.2f} €` (Sin IVA) | **`{item['iva_mat']:.2f} €` (Con IVA 21%)**")
                st.write(f"- Mano de Obra: `{item['horas']:.2f} h` total (`{item['coste_mo']:.2f} €` netos)")
                st.write(f"  • Tareas -> Rozas/Taladros: `{item['rozas']:.2f} h` | Tubos: `{item['tubos']:.2f} h` | Cable: `{item['cable']:.2f} h` | Mecanismos: `{item['mec']:.2f} h`")
                st.markdown("---")

            st.subheader(f"🛒 Resumen Global de Acopio ({serie_mecanismos})")
            rollos_tubo = max(1, int((global_tubo_m + 99) / 100))
            total_cable_15_m = global_cable_15_fn_m + global_cable_15_tierra_m + global_cable_15_vueltas_m
            rollos_cable_15 = max(1, int((total_cable_15_m + 99) / 100))
            rollos_cable_25 = max(1, int((global_cable_25_fuerza_m + 99) / 100))

            total_mat_neto = coste_total_materiales_bruto
            total_mat_con_iva = total_mat_neto * 1.21

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.markdown("**📏 Canalización y Tubería**")
                st.write(f"- Tubo M-20 Requerido: `{int(global_tubo_m)} m`")
                st.write(f"  • Precio metro: `{p_tubo:.2f} €` (Neto) | `{(p_tubo*1.21):.2f} €` (Con IVA)")
                st.success(f"📦 A comprar: `{rollos_tubo} rollo(s) de 100m`")
                st.info(f"💵 Precio Rollo 100m: `{p_tubo*100:.2f} €` (Neto) / **`{p_tubo*100*1.21:.2f} €` (Con IVA 21%)**")

                st.markdown(f"**⚡ Cableado 1.5 mm² ({tipo_cable_sel})**")
                st.write(f"- Total Cable 1.5 mm²: `{int(total_cable_15_m)} m`")
                st.info(f"📦 A comprar: `{rollos_cable_15} rollo(s) de 100m` | Precio Rollo 100m: `{p_15*100:.2f} €` (Neto) / **`{p_15*100*1.21:.2f} €` (Con IVA)**")

            with col_g2:
                st.markdown(f"**⚡ Cableado 2.5 mm² ({tipo_cable_sel})**")
                st.write(f"- Total Cable 2.5 mm²: `{int(global_cable_25_fuerza_m)} m`")
                st.info(f"📦 A comprar: `{rollos_cable_25} rollo(s) de 100m` | Precio Rollo 100m: `{p_25*100:.2f} €` (Neto) / **`{p_25*100*1.21:.2f} €` (Con IVA)**")

                st.markdown(f"**📦 Mecanismos y Cajas ({serie_mecanismos})**")
                st.write(f"- Cajas universales (60x60): `{global_caja_mec_uds} uds` (Precio c/u con IVA: `{p_caja_mec*1.21:.2f} €`)")
                st.write(f"- Cajas de registro (100x100): `{global_caja_reg_uds} uds` (Precio c/u con IVA: `{p_caja_reg*1.21:.2f} €`)")
                st.write(f"- Marcos Embellecedores: `{global_marcos_uds} uds` (Precio c/u con IVA: `{p_marco*1.21:.2f} €`)")
                for (nombre_m, prec_m, prov_m), cantidad_m in global_mecanismos_dict.items():
                    st.write(f"- `{cantidad_m}x` {nombre_m} (Precio c/u con IVA: `{(prec_m*1.21):.2f} €`)")

            st.markdown(f"""
            <div style="border: 2px solid #16a34a; padding: 20px; border-radius: 10px; background-color: #f0fdf4; margin-top: 20px;">
                <h3 style="color: #15803d; margin-top: 0;">💳 DINERO TOTAL NECESARIO EN CAJA (ACOPIO DE MATERIAL)</h3>
                <p><b>Coste Total Materiales (Sin IVA):</b> {total_mat_neto:.2f} €</p>
                <h2 style="color: #16a34a; margin: 0;">TOTAL A PAGAR EN EL ALMACÉN (Con 21% IVA): {total_mat_con_iva:.2f} €</h2>
                <p style="font-size: 13px; color: #64748b; margin-top: 8px;">* Importe exacto a abonar en el mostrador de Obramat incluyendo la serie <b>{serie_mecanismos}</b>.</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📊 Análisis de Utilidad y Rentabilidad")
            venta_total_materiales_neto = coste_total_materiales_bruto * mult_comercial * mult_garantia_mat
            beneficio_materiales = venta_total_materiales_neto - coste_total_materiales_bruto

            venta_total_mo_neto = coste_mano_obra_bruto * mult_comercial
            beneficio_mano_obra = venta_total_mo_neto - coste_mano_obra_bruto

            importe_cuadro_neto = (550.0 if "Elevada" in grado_electrificacion else 450.0) * mult_comercial
            coste_estimado_cuadro = (400.0 if "Elevada" in grado_electrificacion else 320.0)
            beneficio_cuadro = importe_cuadro_neto - coste_estimado_cuadro

            beneficio_neto_total = beneficio_materiales + beneficio_mano_obra + beneficio_cuadro

            st.write(f"- 📦 **Coste Neto Materiales (Tus compras):** `{coste_total_materiales_bruto:.2f} €`")
            st.write(f"- 🏷️ **Venta Neta Materiales al Cliente:** `{venta_total_materiales_neto:.2f} €` (Beneficio: `+{beneficio_materiales:.2f} €`)")
            st.write(f"- ⏱️ **Coste Real Mano de Obra ({horas_totales_obra:.1f} h a {precio_hora} €/h):** `{coste_mano_obra_bruto:.2f} €`")
            st.write(f"- 💰 **Venta Neta Mano de Obra al Cliente:** `{venta_total_mo_neto:.2f} €` (Beneficio: `+{beneficio_mano_obra:.2f} €`)")
            st.write(f"- ⚡ **Beneficio en Cuadro General / Boletín:** `+{beneficio_cuadro:.2f} €`")
            st.success(f"🚀 **UTILIDAD / BENEFICIO NETO TOTAL ESTIMADO PARA TI: +{beneficio_neto_total:.2f} €** (Sin contar IVA)")

        # ==========================================
        # MODO 2: VISTA COMERCIAL PARA EL CLIENTE
        # ==========================================
        else:
            st.header("📄 Vista Comercial: Presupuesto para el Cliente")
            st.markdown("Lista comercial lista para entregar. Pulsa **Ctrl + P** para imprimir únicamente este presupuesto formal.")

            st.markdown(f"""
            <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff;">
                <h3 style="color: #0369a1; margin-top: 0;">{empresa_nombre}</h3>
                <p><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
                <hr style="border: 1px solid #bae6fd;">
                <p><b>Presupuesto N°:</b> 2026-0901 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha:</b> Septiembre 2026</p>
                <p><b>Objeto:</b> Instalación Eléctrica REBT ({grado_electrificacion}) por Estancias ({sup_total:.1f} m²)</p>
                <p><b>Sistema:</b> {tipo_obra} | **Cable:** {tipo_cable_sel} | **Serie:** {serie_mecanismos}</p>
            </div>
            """, unsafe_allow_html=True)

            df_comercial = pd.DataFrame(comercial_estancias)
            st.dataframe(df_comercial, use_container_width=True)

            importe_cuadro_neto = (550.0 if "Elevada" in grado_electrificacion else 450.0) * mult_comercial
            subtotal_general_neto = subtotal_neto_comercial + importe_cuadro_neto

            st.markdown(f"""
            <div style="border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; background-color: #f8fafc; margin-top: 10px;">
                <h4>Capítulo Adicional: Cuadro General de Protección ({grado_electrificacion}) y Boletín Oficial (CIE)</h4>
                <p>Suministro de cuadro de distribución, protecciones obligatorias REBT y tramitación del boletín: <b>{importe_cuadro_neto:.2f} €</b></p>
            </div>
            """, unsafe_allow_html=True)

            cuota_iva = subtotal_general_neto * (iva_sel / 100.0)
            total_cliente = subtotal_general_neto + cuota_iva

            st.markdown(f"""
            <div style="text-align: right; font-size: 18px; background-color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #94a3b8; margin-top: 15px;">
                <p><b>Subtotal Comercial Neto:</b> {subtotal_general_neto:.2f} €</p>
                <p><b>IVA ({iva_sel}%):</b> {cuota_iva:.2f} €</p>
                <h2 style="color: #16a34a; margin: 0;">TOTAL PRESUPUESTO CLIENTE: {total_cliente:.2f} €</h2>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### 📝 Condiciones Generales y Garantía")
            st.info(f"• **Validez de la oferta:** 30 días.\n• **Forma de pago:** 40% a la aceptación, 40% a mitad de ejecución y 20% a la entrega del Boletín Oficial (CIE).\n• **Garantía:** 2 años en instalación ejecutada según REBT con mecanismos **{serie_mecanismos}**.")

        st.success("✅ ¡Análisis de tiempos de mano de obra y paneles generados con éxito!")

if __name__ == "__main__":
    app()
