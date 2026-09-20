# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos: Desglose por Estancia de Cables, Colores, UTP/RJ45 y Acopio Real
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
    st.markdown("Conectado con tu Base de Datos Maestra Oficial Actualizada (`base_datos_precio_oficial.xlsx`).")

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
        st.sidebar.success(f"📁 Base de datos conectada: `{excel_cargado}` ({len(df_precios)} artículos)")

    # ==========================================
    # FUNCIONES DE BÚSQUEDA PRECISA EN EXCEL
    # ==========================================
    def buscar_general(df, main_kw, sub_kw=None):
        for idx, row in df.iterrows():
            desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
            if main_kw in desc:
                if sub_kw is None or sub_kw in desc:
                    return float(row['Precio S/IVA (€)']), str(row['Proveedor / Tienda']), str(row['Descripción Exacta del Artículo']), True, idx + 2
        return 0.45, "Obramat", "Artículo estándar", False, -1

    def buscar_mecanismo(df, tipo, serie_sel):
        serie_lower = serie_sel.lower()
        
        kw_map = {
            'interruptor': ['interruptor', 'conmutador'],
            'schuko': ['schuko', 'enchufe'],
            'rj45': ['rj45', 'datos'],
            'marco': ['marco 1 elemento', 'marco']
        }
        keywords = kw_map.get(tipo, ['interruptor'])

        for kw in keywords:
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                serie_item = str(row.get('Serie / Gama', '')).strip().lower()
                
                if kw in desc:
                    if any(term in serie_item or term in desc for term in ['simon 10', 'simon 27 play', 'simon 82', 'zenit', 'asfora', 'ovalis', 'miluz', 'niloé step', 'suno', 'new unica', 'valena next', 'simon 270'] if term in serie_lower):
                        if any(t in serie_item for t in serie_lower.split() if len(t) > 3):
                            return float(row['Precio S/IVA (€)']), str(row['Proveedor / Tienda']), str(row['Descripción Exacta del Artículo']), True, idx + 2

        brand_terms = [t for t in ['simon', 'schneider', 'niessen', 'legrand', 'solera', 'lexman'] if t in serie_lower]
        for kw in keywords:
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                serie_item = str(row.get('Serie / Gama', '')).strip().lower()
                marca_item = str(row.get('Marca', '')).strip().lower()
                
                if kw in desc:
                    if any(bt in marca_item or bt in serie_item for bt in brand_terms):
                        return float(row['Precio S/IVA (€)']), str(row['Proveedor / Tienda']), str(row['Descripción Exacta del Artículo']), True, idx + 2

        for kw in keywords:
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                if kw in desc and row['Familia / Categoria'] in ['Mecanismos', 'Bases de Enchufe', 'Tomas / Datos', 'Marcos / Placas']:
                    return float(row['Precio S/IVA (€)']), str(row['Proveedor / Tienda']), str(row['Descripción Exacta del Artículo']), True, idx + 2

        return 3.50, "Obramat", "Artículo estándar", False, -1

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

    tipo_conexion = st.radio(
        "🔌 Sistema de Conexión en Cajas de Registro y Mecanismos:",
        ["Conectores Rápidos Wago 221 (Profesional / Alta Calidad)", "Fichas de Empalme / Clemas Tradicionales de Tornillo"],
        horizontal=True
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
        hace_rozas_electricista = st.checkbox("¿Asumes tú (electricista) el picado de rozas y tapado con yeso?", value=True)
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

        # Búsquedas precisas en Excel
        p_tubo20, prov_tubo20, desc_tubo20, _, fila_tubo20 = buscar_general(df_precios, 'm20', 'corrugado')
        p_tubo25, prov_tubo25, desc_tubo25, _, fila_tubo25 = buscar_general(df_precios, 'm25', 'corrugado')

        p_caja_mec, prov_caja_mec, desc_caja_mec, _, fila_caja_mec = buscar_general(df_precios, '67mm', 'mecanismos')
        p_caja_reg, prov_caja_reg, desc_caja_reg, _, fila_caja_reg = buscar_general(df_precios, '100x100', 'registro')
        
        # Cables 1.5mm²
        p_15_az, prov_15_az, desc_15_az, _, fila_15_az = buscar_general(df_precios, '1.5 mm²', 'azul')
        p_15_ma, prov_15_ma, desc_15_ma, _, fila_15_ma = buscar_general(df_precios, '1.5 mm²', 'marrón')
        p_15_tt, prov_15_tt, desc_15_tt, _, fila_15_tt = buscar_general(df_precios, '1.5 mm²', 'amarillo')

        # Cables 2.5mm²
        p_25_az, prov_25_az, desc_25_az, _, fila_25_az = buscar_general(df_precios, '2.5 mm²', 'azul')
        p_25_ma, prov_25_ma, desc_25_ma, _, fila_25_ma = buscar_general(df_precios, '2.5 mm²', 'marrón')
        p_25_tt, prov_25_tt, desc_25_tt, _, fila_25_tt = buscar_general(df_precios, '2.5 mm²', 'amarillo')

        # Cable de Datos UTP (RJ45)
        p_utp, prov_utp, desc_utp, _, fila_utp = buscar_general(df_precios, 'utp', 'cat.6')
        if not prov_utp or p_utp == 0.45:
            p_utp, prov_utp, desc_utp, _, fila_utp = buscar_general(df_precios, 'cable de red', 'cat.6')

        # Conexión seleccionada (Wago o Clemas)
        if "Wago" in tipo_conexion:
            p_con, prov_con, desc_con, _, fila_con = buscar_general(df_precios, 'wago 221', '3 conductores')
            nombre_conexion_txt = "Conectores Rápidos Wago 221 (Caja 50ud)"
        else:
            p_con, prov_con, desc_con, _, fila_con = buscar_general(df_precios, 'clema', '10mm')
            nombre_conexion_txt = "Regleta / Clema de Conexión 12 Polos"

        p_int, prov_int, desc_int, _, fila_int = buscar_mecanismo(df_precios, 'interruptor', serie_mecanismos)
        p_schuko, prov_schuko, desc_schuko, _, fila_schuko = buscar_mecanismo(df_precios, 'schuko', serie_mecanismos)
        p_rj45, prov_rj45, desc_rj45, _, fila_rj45 = buscar_mecanismo(df_precios, 'rj45', serie_mecanismos)
        p_marco, prov_marco, desc_marco, _, fila_marco = buscar_mecanismo(df_precios, 'marco', serie_mecanismos)

        # Acumuladores globales
        global_tubo20_m = 0.0
        global_tubo25_m = 0.0
        global_caja_mec_uds = 0
        global_caja_reg_uds = 0
        
        global_15_az_m = 0.0
        global_15_ma_m = 0.0
        global_15_tt_m = 0.0
        
        global_25_az_m = 0.0
        global_25_ma_m = 0.0
        global_25_tt_m = 0.0

        global_utp_m = 0.0

        global_marcos_uds = 0
        global_mecanismos_dict = {}

        coste_total_materiales_bruto = 0.0
        horas_totales_obra = 0.0
        subtotal_neto_comercial = 0.0
        comercial_estancias = []
        desgloses_internos_estancias = []

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
            m_tubo_20 = m_tubo * 0.75
            m_tubo_25 = m_tubo * 0.25
            
            n_cajas_reg = 1 if m2 > 8 else 0
            
            # Cálculo de metros por color específicos para esta estancia
            m_15_ilum_fn = m2 * 5.0
            m_15_ilum_tt = m2 * 2.5
            m_15_vueltas = m2 * 4.0
            
            est_15_az = m_15_ilum_fn
            est_15_ma = m_15_ilum_fn + m_15_vueltas
            est_15_tt = m_15_ilum_tt

            est_25_fuerza = m2 * (15.0 if "Elevada" in grado_electrificacion else 12.0)
            est_25_az = est_25_fuerza * 0.5
            est_25_ma = est_25_fuerza * 0.5
            est_25_tt = est_25_fuerza

            # Cable UTP Cat6 para estancias con toma de datos
            est_utp = 0.0
            if "salón" in nombre_est or "comedor" in nombre_est or "despacho" in nombre_est:
                est_utp = 15.0  # Promedio de tirada desde cuadro/registro al punto de red

            if "cocina" in nombre_est:
                mecanismos_est = [
                    {"nombre": "Interruptor simple", "desc_real": desc_int, "cant": 1, "precio": p_int, "prov": prov_int, "fila": fila_int},
                    {"nombre": "Base Schuko 16A", "desc_real": desc_schuko, "cant": 4, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko},
                    {"nombre": "Base fuerza 25A Horno/Vitro", "desc_real": desc_schuko, "cant": 1, "precio": p_schuko * 1.5, "prov": prov_schuko, "fila": fila_schuko},
                    {"nombre": "Bases Schuko lavavajillas/lavadora", "desc_real": desc_schuko, "cant": 2, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko}
                ]
            elif "baño" in nombre_est:
                mecanismos_est = [
                    {"nombre": "Interruptor luz espejo", "desc_real": desc_int, "cant": 1, "precio": p_int, "prov": prov_int, "fila": fila_int},
                    {"nombre": "Base Schuko tapa estanca IP44", "desc_real": desc_schuko, "cant": 2, "precio": p_schuko * 1.2, "prov": prov_schuko, "fila": fila_schuko}
                ]
            elif "salón" in nombre_est or "comedor" in nombre_est:
                mecanismos_est = [
                    {"nombre": "Conmutador / Cruzamiento", "desc_real": desc_int, "cant": 2, "precio": p_int, "prov": prov_int, "fila": fila_int},
                    {"nombre": "Bases Schuko zona TV/Sofá", "desc_real": desc_schuko, "cant": 6, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko},
                    {"nombre": "Toma de datos RJ45", "desc_real": desc_rj45, "cant": 2, "precio": p_rj45, "prov": prov_rj45, "fila": fila_rj45}
                ]
            else:
                mecanismos_est = [
                    {"nombre": "Conmutador / Interruptor", "desc_real": desc_int, "cant": 2, "precio": p_int, "prov": prov_int, "fila": fila_int},
                    {"nombre": "Bases Schuko 16A", "desc_real": desc_schuko, "cant": 3, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko}
                ]

            total_mecanismos = sum([m["cant"] for m in mecanismos_est])
            n_marcos = max(total_mecanismos, int(total_mecanismos * 0.8))

            # Acumular globales
            global_tubo20_m += m_tubo_20
            global_tubo25_m += m_tubo_25
            global_caja_mec_uds += total_mecanismos
            global_caja_reg_uds += n_cajas_reg
            
            global_15_az_m += est_15_az
            global_15_ma_m += est_15_ma
            global_15_tt_m += est_15_tt
            
            global_25_az_m += est_25_az
            global_25_ma_m += est_25_ma
            global_25_tt_m += est_25_tt
            global_utp_m += est_utp

            global_marcos_uds += n_marcos

            for mec in mecanismos_est:
                key_m = (mec["nombre"], mec["desc_real"], mec["precio"], mec["prov"], mec["fila"])
                global_mecanismos_dict[key_m] = global_mecanismos_dict.get(key_m, 0) + mec["cant"]

            coste_mecanismos_est = sum([m["cant"] * m["precio"] for m in mecanismos_est])
            coste_marcos_est = n_marcos * p_marco
            coste_cajas_mec_est = total_mecanismos * p_caja_mec

            coste_mat_estancia_neto = (
                (m_tubo_20 * p_tubo20) +
                (m_tubo_25 * p_tubo25) +
                coste_cajas_mec_est +
                (n_cajas_reg * p_caja_reg if n_cajas_reg > 0 else 0) +
                (est_15_az * p_15_az) + (est_15_ma * p_15_ma) + (est_15_tt * p_15_tt) +
                (est_25_az * p_25_az) + (est_25_ma * p_25_ma) + (est_25_tt * p_25_tt) +
                (est_utp * p_utp) +
                coste_mecanismos_est +
                coste_marcos_est
            )
            coste_mat_estancia_con_iva = coste_mat_estancia_neto * 1.21
            coste_total_materiales_bruto += coste_mat_estancia_neto

            # Horas
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
                "mec": h_mecanizado,
                "mecanismos_detalle": mecanismos_est,
                "m_tubo_20": m_tubo_20,
                "m_tubo_25": m_tubo_25,
                "n_cajas_reg": n_cajas_reg,
                "cable_15_az": est_15_az,
                "cable_15_ma": est_15_ma,
                "cable_15_tt": est_15_tt,
                "cable_25_az": est_25_az,
                "cable_25_ma": est_25_ma,
                "cable_25_tt": est_25_tt,
                "cable_utp": est_utp
            })

        coste_mano_obra_bruto = horas_totales_obra * precio_hora

        # ==========================================
        # SELECTOR DE MODO DE VISTA E IMPRESIÓN
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

            st.subheader("⏱️ Análisis de Rendimiento y Tiempos de Mano de Obra")
            st.write(f"- 🧱 **Fase de Rozas / Perforación ({tipo_pared}):** `{sum_h_rozas:.2f} h` acumuladas.")
            st.write(f"- 📏 **Fase de Canalización y Cajas (0.25 h/m²):** `{sum_h_tubos:.2f} h` acumuladas.")
            st.write(f"- ⚡ **Fase de Tendido y Cableado (0.30 h/m²):** `{sum_h_cable:.2f} h` acumuladas.")
            st.write(f"- 🔲 **Fase de Conexionado y Mecanizado (0.15 h/u):** `{sum_h_mec:.2f} h` acumuladas.")
            st.info(f"⏱️ **Total Horas de Obra Estimadas:** `{horas_totales_obra:.2f} h` x `{precio_hora:.2f} €/h` = **`{coste_mano_obra_bruto:.2f} €`** (Coste Neto Mano de Obra).")
            st.markdown("---")

            # DESGLOSE DETALLADO POR ESTANCIAS (INCLUYENDO METROS DE CABLE Y UTP)
            st.subheader("🛠️ Desglose Detallado por Estancias (Enlazado con Excel y Metros de Cable)")
            for item in desgloses_internos_estancias:
                st.markdown(f"### 📍 {item['nombre']} ({item['m2']} m²)")
                st.markdown(f"⏱️ **Mano de Obra Estancia:** `{item['horas']:.2f} h` netas (`{item['coste_mo']:.2f} €`) — Tareas: Rozas `{item['rozas']:.2f}h`, Tubos `{item['tubos']:.2f}h`, Cable `{item['cable']:.2f}h`, Mecanizado `{item['mec']:.2f}h`")
                
                st.markdown("📦 **Materiales y Metraje de la Estancia:**")
                st.write(f"  - **Tubo M-20:** `{int(item['m_tubo_20'])} m` | Proveedor: `{prov_tubo20}` | `[Fila Excel: #{fila_tubo20}]`")
                st.write(f"  - **Tubo M-25:** `{int(item['m_tubo_25'])} m` | Proveedor: `{prov_tubo25}` | `[Fila Excel: #{fila_tubo25}]`")
                st.write(f"  - **Cajas Universales (67mm):** Proveedor: `{prov_caja_mec}` | `[Fila Excel: #{fila_caja_mec}]`")
                if item['n_cajas_reg'] > 0:
                    st.write(f"  - **Caja de Registro (100x100):** Proveedor: `{prov_caja_reg}` | `[Fila Excel: #{fila_caja_reg}]`")

                # CABLES 1.5 mm² POR ESTANCIA
                st.markdown(f"  - **Cables 1.5 mm² ({tipo_cable_sel}):**")
                st.write(f"    • Azul (Neutro): `{int(item['cable_15_az'])} m` | `[Fila Excel: #{fila_15_az}]` | `{prov_15_az}`")
                st.write(f"    • Marrón/Negro (Fase): `{int(item['cable_15_ma'])} m` | `[Fila Excel: #{fila_15_ma}]` | `{prov_15_ma}`")
                st.write(f"    • Amarillo/Verde (Tierra): `{int(item['cable_15_tt'])} m` | `[Fila Excel: #{fila_15_tt}]` | `{prov_15_tt}`")

                # CABLES 2.5 mm² POR ESTANCIA
                st.markdown(f"  - **Cables 2.5 mm² ({tipo_cable_sel}):**")
                st.write(f"    • Azul (Neutro): `{int(item['cable_25_az'])} m` | `[Fila Excel: #{fila_25_az}]` | `{prov_25_az}`")
                st.write(f"    • Marrón/Negro (Fase): `{int(item['cable_25_ma'])} m` | `[Fila Excel: #{fila_25_ma}]` | `{prov_25_ma}`")
                st.write(f"    • Amarillo/Verde (Tierra): `{int(item['cable_25_tt'])} m` | `[Fila Excel: #{fila_25_tt}]` | `{prov_25_tt}`")

                # CABLE UTP SI APLICA
                if item['cable_utp'] > 0:
                    st.markdown(f"  - **Cable de Datos UTP Cat.6:** `{int(item['cable_utp'])} m` | Proveedor: `{prov_utp}` | `[Fila Excel: #{fila_utp}]` | Ref: `{desc_utp}`")

                for mec in item['mecanismos_detalle']:
                    st.write(f"  - `{mec['cant']}x` **{mec['nombre']}** ({serie_mecanismos}) — Ref. Excel: `{mec['desc_real']}` | Proveedor: `{mec['prov']}` | `[Fila Excel: #{mec['fila']}]` | S/IVA c/u: `{mec['precio']:.2f} €`")

                st.markdown(f"👉 **Subtotal Materiales Estancia:** Sin IVA: `{item['neto_mat']:.2f} €` &nbsp;|&nbsp; **Con IVA (21%): `{item['iva_mat']:.2f} €`**")
                st.markdown("---")

            # RESUMEN GLOBAL DE ACOPIO
            st.subheader(f"🛒 Resumen Global de Acopio ({serie_mecanismos}) — Dónde Comprar y Trazabilidad Excel")
            st.markdown("Lista oficial para compras en almacén organizada en formato vertical continuo con indicación exacta de rollos y metros.")

            rollos_tubo20 = max(1, int((global_tubo20_m + 49) / 50))
            rollos_tubo25 = max(1, int((global_tubo25_m + 49) / 50))

            rollos_15_az = max(1, int((global_15_az_m + 99) / 100))
            rollos_15_ma = max(1, int((global_15_ma_m + 99) / 100))
            rollos_15_tt = max(1, int((global_15_tt_m + 99) / 100))

            rollos_25_az = max(1, int((global_25_az_m + 99) / 100))
            rollos_25_ma = max(1, int((global_25_ma_m + 99) / 100))
            rollos_25_tt = max(1, int((global_25_tt_m + 99) / 100))

            rollos_utp = max(1, int((global_utp_m + 99) / 100)) if global_utp_m > 0 else 0

            total_mat_neto = coste_total_materiales_bruto
            total_mat_con_iva = total_mat_neto * 1.21

            # BLOQUE 1: TUBERÍA
            st.markdown("#### 📏 1. Canalización y Tubería (M-20 y M-25)")
            st.write(f"- **Tubo M-20:** `{int(global_tubo20_m)} m` | Proveedor: **{prov_tubo20}** | `[Fila Excel: #{fila_tubo20}]` | Ref: `{desc_tubo20}`")
            st.success(f"  📦 A comprar: `{rollos_tubo20} rollo(s) de 50m` — Precio: `{p_tubo20*50*1.21:.2f} €` (Con IVA)")
            st.write(f"- **Tubo M-25:** `{int(global_tubo25_m)} m` | Proveedor: **{prov_tubo25}** | `[Fila Excel: #{fila_tubo25}]` | Ref: `{desc_tubo25}`")
            st.success(f"  📦 A comprar: `{rollos_tubo25} rollo(s) de 50m` — Precio: `{p_tubo25*50*1.21:.2f} €` (Con IVA)")

            st.markdown("---")

            # BLOQUE 2: CABLEADO POR COLORES
            st.markdown(f"#### ⚡ 2. Cableado por Colores ({tipo_cable_sel})")
            st.markdown("##### 🔹 Cables de 1.5 mm²:")
            st.write(f"  - **Azul (Neutro):** `{int(global_15_az_m)} m` | Proveedor: **{prov_15_az}** | `[Fila Excel: #{fila_15_az}]` | Ref: `{desc_15_az}`")
            st.info(f"    📦 A comprar: `{rollos_15_az} rollo(s) de 100m` | Precio: `{p_15_az*100*1.21:.2f} €` (Con IVA)")
            st.write(f"  - **Marrón/Negro (Fase):** `{int(global_15_ma_m)} m` | Proveedor: **{prov_15_ma}** | `[Fila Excel: #{fila_15_ma}]` | Ref: `{desc_15_ma}`")
            st.info(f"    📦 A comprar: `{rollos_15_ma} rollo(s) de 100m` | Precio: `{p_15_ma*100*1.21:.2f} €` (Con IVA)")
            st.write(f"  - **Amarillo/Verde (Tierra):** `{int(global_15_tt_m)} m` | Proveedor: **{prov_15_tt}** | `[Fila Excel: #{fila_15_tt}]` | Ref: `{desc_15_tt}`")
            st.info(f"    📦 A comprar: `{rollos_15_tt} rollo(s) de 100m` | Precio: `{p_15_tt*100*1.21:.2f} €` (Con IVA)")

            st.markdown("##### 🔹 Cables de 2.5 mm²:")
            st.write(f"  - **Azul (Neutro):** `{int(global_25_az_m)} m` | Proveedor: **{prov_25_az}** | `[Fila Excel: #{fila_25_az}]` | Ref: `{desc_25_az}`")
            st.info(f"    📦 A comprar: `{rollos_25_az} rollo(s) de 100m` | Precio: `{p_25_az*100*1.21:.2f} €` (Con IVA)")
            st.write(f"  - **Marrón/Negro (Fase):** `{int(global_25_ma_m)} m` | Proveedor: **{prov_25_ma}** | `[Fila Excel: #{fila_25_ma}]` | Ref: `{desc_25_ma}`")
            st.info(f"    📦 A comprar: `{rollos_25_ma} rollo(s) de 100m` | Precio: `{p_25_ma*100*1.21:.2f} €` (Con IVA)")
            st.write(f"  - **Amarillo/Verde (Tierra):** `{int(global_25_tt_m)} m` | Proveedor: **{prov_25_tt}** | `[Fila Excel: #{fila_25_tt}]` | Ref: `{desc_25_tt}`")
            st.info(f"    📦 A comprar: `{rollos_25_tt} rollo(s) de 100m` | Precio: `{p_25_tt*100*1.21:.2f} €` (Con IVA)")

            if global_utp_m > 0:
                st.markdown("##### 🌐 Cable de Red / Datos:")
                st.write(f"  - **Cable UTP Cat.6:** `{int(global_utp_m)} m` | Proveedor: **{prov_utp}** | `[Fila Excel: #{fila_utp}]` | Ref: `{desc_utp}`")
                st.info(f"    📦 Metros totales calculados para tomas de datos en Salón/Comedor/Despacho.")

            st.markdown("---")

            # BLOQUE 3: MECANISMOS Y CONEXIONES
            st.markdown(f"#### 📦 3. Mecanismos, Cajas, Conexiones y Marcos ({serie_mecanismos})")
            st.write(f"- Cajas universales (67mm): `{global_caja_mec_uds} uds` | Proveedor: **{prov_caja_mec}** | `[Fila Excel: #{fila_caja_mec}]`")
            st.write(f"- Cajas de registro (100x100): `{global_caja_reg_uds} uds` | Proveedor: **{prov_caja_reg}** | `[Fila Excel: #{fila_caja_reg}]`")
            
            cant_con = max(1, int((global_caja_reg_uds + global_caja_mec_uds) / 15))
            st.write(f"- **{nombre_conexion_txt}:** `{cant_con} unidad(es)` | Proveedor: **{prov_con}** | `[Fila Excel: #{fila_con}]` | Ref: `{desc_con}`")

            st.write(f"- Marcos Embellecedores: `{global_marcos_uds} uds` | Proveedor: **{prov_marco}** | `[Fila Excel: #{fila_marco}]`")
            for (nombre_m, desc_m, prec_m, prov_m, fila_m), cantidad_m in global_mecanismos_dict.items():
                st.write(f"- `{cantidad_m}x` **{nombre_m}** ({serie_mecanismos}) | Proveedor: **{prov_m}** | `[Fila Excel: #{fila_m}]` | Ref: `{desc_m}`")

            st.markdown(f"""
            <div style="border: 2px solid #16a34a; padding: 20px; border-radius: 10px; background-color: #f0fdf4; margin-top: 20px;">
                <h3 style="color: #15803d; margin-top: 0;">💳 DINERO TOTAL NECESARIO EN CAJA (ACOPIO DE MATERIAL)</h3>
                <p><b>Coste Total Materiales (Sin IVA):</b> {total_mat_neto:.2f} €</p>
                <h2 style="color: #16a34a; margin: 0;">TOTAL A PAGAR EN EL ALMACÉN (Con 21% IVA): {total_mat_con_iva:.2f} €</h2>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📊 Análisis de Utilidad y Rentabilidad")
            venta_mat_neto = coste_total_materiales_bruto * mult_comercial * mult_garantia_mat
            benef_mat = venta_mat_neto - coste_total_materiales_bruto
            venta_mo_neto = coste_mano_obra_bruto * mult_comercial
            benef_mo = venta_mo_neto - coste_mano_obra_bruto
            benef_cuadro = ((550.0 if "Elevada" in grado_electrificacion else 450.0) * mult_comercial) - (400.0 if "Elevada" in grado_electrificacion else 320.0)
            benef_neto_total = benef_mat + benef_mo + benef_cuadro

            st.write(f"- 📦 **Coste Neto Materiales:** `{coste_total_materiales_bruto:.2f} €` (Venta: `{venta_mat_neto:.2f} €` | Beneficio: `+{benef_mat:.2f} €`)")
            st.write(f"- ⏱️ **Coste Mano de Obra:** `{coste_mano_obra_bruto:.2f} €` (Venta: `{venta_mo_neto:.2f} €` | Beneficio: `+{benef_mo:.2f} €`)")
            st.success(f"🚀 **UTILIDAD / BENEFICIO NETO TOTAL ESTIMADO: +{benef_neto_total:.2f} €** (Sin contar IVA)")

        # ==========================================
        # MODO 2: VISTA COMERCIAL
        # ==========================================
        else:
            st.header("📄 Vista Comercial: Presupuesto para el Cliente")
            st.markdown(f"""
            <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff;">
                <h3 style="color: #0369a1; margin-top: 0;">{empresa_nombre}</h3>
                <p><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
                <hr style="border: 1px solid #bae6fd;">
                <p><b>Presupuesto N°:</b> 2026-0901 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha:</b> Septiembre 2026</p>
                <p><b>Objeto:</b> Instalación Eléctrica REBT ({grado_electrificacion}) por Estancias ({sup_total:.1f} m²)</p>
            </div>
            """, unsafe_allow_html=True)

            df_comercial = pd.DataFrame(comercial_estancias)
            st.dataframe(df_comercial, use_container_width=True)

            importe_cuadro_neto = (550.0 if "Elevada" in grado_electrificacion else 450.0) * mult_comercial
            subtotal_general_neto = subtotal_neto_comercial + importe_cuadro_neto
            cuota_iva = subtotal_general_neto * (iva_sel / 100.0)
            total_cliente = subtotal_general_neto + cuota_iva

            st.markdown(f"""
            <div style="text-align: right; font-size: 18px; background-color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #94a3b8; margin-top: 15px;">
                <p><b>Subtotal Comercial Neto:</b> {subtotal_general_neto:.2f} €</p>
                <p><b>IVA ({iva_sel}%):</b> {cuota_iva:.2f} €</p>
                <h2 style="color: #16a34a; margin: 0;">TOTAL PRESUPUESTO CLIENTE: {total_cliente:.2f} €</h2>
            </div>
            """, unsafe_allow_html=True)

        st.success("✅ ¡Desglose por estancias actualizado con metros de cable por color y cable UTP / RJ45!")

if __name__ == "__main__":
    app()
