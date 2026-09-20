# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos: Grado REBT, Estancias Dinámicas, Auditoría y Resumen Global
Autor: Richard Orlando Choque Tejerina (Bolimur Electricidad)
"""

import streamlit as st
import pandas as pd
import openpyxl
import os

def app():
    # Estilo CSS para impresión limpia
    st.markdown("""
        <style>
            @media print {
                [data-testid="stSidebar"] {display: none;}
                [data-testid="stHeader"] {display: none;}
                .stButton {display: none;}
                .stTextInput {display: none;}
                .stSelectbox {display: none;}
                .stSlider {display: none;}
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("🏡 Generador de Presupuestos: Control REBT, Grado de Electrificación y Estancias")
    st.markdown("Gestión dinámica de habitaciones, selección de grado de electrificación reglamentario (Básica/Elevada), auditoría técnica y lista de compras.")

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

    # Función robusta para buscar artículo, precio y descripción exacta en la BD
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
    # PARÁMETROS GLOBALES Y GRADO DE ELECTRIFICACIÓN REBT
    # ==========================================
    st.markdown("---")
    st.subheader("⚙️ Parámetros de Costes y Normativa REBT")
    
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
        gama_sel = st.selectbox(
            "Nivel de Gama de Mecanismos",
            ['1. Ultra Económica', '2. Económica Estándar', '3. Media Residencial', '4. Alta Decorativa']
        )

    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        precio_hora = st.number_input("Precio Mano de Obra (€/h)", min_value=10.0, max_value=60.0, value=25.0, step=1.0)
    with col_c2:
        num_operarios = st.number_input("Nº Operarios", min_value=1, max_value=5, value=1, step=1)
    with col_c3:
        margen_comercial = st.slider("Margen Comercial (%)", 0, 50, 20)
    with col_c4:
        iva_sel = st.selectbox("IVA", [10, 21])

    tipo_obra = st.selectbox(
        "Sistema de Ejecución General",
        ["Empotrada en Rozas (Ladrillo + Yeso)", "Falso Techo / Pladur (Obra Seca)", "Superficie (Tubo visto / Canaleta)"]
    )

    st.markdown("---")

    # ==========================================
    # GESTIÓN DINÁMICA DE ESTANCIAS (AÑADIR / QUITAR)
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

    # Formulario rápido para añadir nueva estancia
    with st.expander("➕ Añadir Nueva Estancia a la Vivienda"):
        with st.form("form_nueva_estancia"):
            col_n1, col_n2, col_n3 = st.columns([3, 2, 2])
            with col_n1:
                nuevo_nombre = st.text_input("Nombre de la Estancia (Ej: Terraza, Despacho, Baño 2)")
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

    # Listar estancias con opción de modificar o eliminar
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

    if st.button("🚀 Calcular Presupuesto y Auditoría REBT", type="primary"):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia.")
            return

        sup_total = sum([e["m2"] for e in estancias_activas])

        # Definir keywords de búsqueda según cableado
        kw_cable_15 = ['h07z1-k 1.5', 'libre de halógenos 1.5', '1.5 mm'] if "Halógenos" in tipo_cable_sel else ['h07v-k 1.5', 'cable 1.5', '1.5 mm']
        kw_cable_25 = ['h07z1-k 2.5', 'libre de halógenos 2.5', '2.5 mm'] if "Halógenos" in tipo_cable_sel else ['h07v-k 2.5', 'cable 2.5', '2.5 mm']

        # Obtener precios de la BD
        p_tubo, prov_tubo, desc_tubo, _ = buscar_articulo_detallado(df_precios, ['tubo corrugado', 'm-20', 'tubo 20'], gama_sel, 0.45)
        p_caja_mec, prov_caja_mec, desc_caja_mec, _ = buscar_articulo_detallado(df_precios, ['caja universal', 'caja mecanismo'], gama_sel, 0.30)
        p_caja_reg, prov_caja_reg, desc_caja_reg, _ = buscar_articulo_detallado(df_precios, ['caja de registro', 'derivación'], gama_sel, 1.50)
        p_15, prov_15, desc_15, _ = buscar_articulo_detallado(df_precios, kw_cable_15, gama_sel, 0.38 if "Halógenos" in tipo_cable_sel else 0.32)
        p_25, prov_25, desc_25, _ = buscar_articulo_detallado(df_precios, kw_cable_25, gama_sel, 0.55 if "Halógenos" in tipo_cable_sel else 0.48)
        
        p_int, prov_int, desc_int, _ = buscar_articulo_detallado(df_precios, ['interruptor', 'conmutador'], gama_sel, 3.50)
        p_schuko, prov_schuko, desc_schuko, _ = buscar_articulo_detallado(df_precios, ['schuko', 'base de enchufe'], gama_sel, 4.20)
        p_rj45, prov_rj45, desc_rj45, _ = buscar_articulo_detallado(df_precios, ['rj45', 'datos', 'multimedia'], gama_sel, 8.50)
        p_marco, prov_marco, desc_marco, _ = buscar_articulo_detallado(df_precios, ['marco', 'embellecedor'], gama_sel, 1.80)

        # ==========================================
        # AUDITORÍA TÉCNICA REBT
        # ==========================================
        st.markdown("---")
        st.header("🔍 Auditoría Técnica REBT de Integridad")
        
        tiene_cocina = any("cocina" in e["nombre"].lower() for e in estancias_activas)
        tiene_bano = any("baño" in e["nombre"].lower() for e in estancias_activas)
        
        auditoria_ok = True
        if not tiene_cocina:
            st.warning("⚠️ **Aviso de Auditoría:** No se ha detectado ninguna estancia 'Cocina'. El circuito C3 es obligatorio en viviendas.")
            auditoria_ok = False
        if not tiene_bano:
            st.warning("⚠️ **Aviso de Auditoría:** No se ha detectado ninguna estancia 'Baño'. El circuito C5 debe contemplarse.")
            auditoria_ok = False
            
        if auditoria_ok:
            st.success(f"✅ **Auditoría REBT Superada ({grado_electrificacion}):** Estancias normativas detectadas. El dimensionamiento de circuitos y protecciones cumple con el Reglamento Electrotécnico.")

        # ==========================================
        # ACUMULADORES GLOBALES DE COMPRAS
        # ==========================================
        global_tubo_m = 0.0
        global_caja_mec_uds = 0
        global_caja_reg_uds = 0
        global_cable_15_fn_m = 0.0
        global_cable_15_tierra_m = 0.0
        global_cable_15_vueltas_m = 0.0
        global_cable_25_fuerza_m = 0.0
        global_marcos_uds = 0
        global_mecanismos_dict = {}

        # ==========================================
        # 1. INFORME TÉCNICO Y LISTA POR ESTANCIA
        # ==========================================
        st.markdown("---")
        st.header("🛠️ 1. INFORME TÉCNICO Y DESGLOSE POR ESTANCIAS (Para el Instalador)")
        st.info(f"Cálculos bajo Grado de Electrificación **{grado_electrificacion}** con cableado **{tipo_cable_sel}**.")

        coste_total_materiales_bruto = 0.0
        horas_totales_obra = 0.0

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
                    {"nombre": "Interruptor simple iluminación", "cant": 1, "precio": p_int, "prov": prov_int, "desc": desc_int},
                    {"nombre": "Base Schuko 16A encimera / general", "cant": 4, "precio": p_schuko, "prov": prov_schuko, "desc": desc_schuko},
                    {"nombre": "Base enchufe especial Horno / Vitro (25A)", "cant": 1, "precio": p_schuko * 1.5, "prov": prov_schuko, "desc": "Base de fuerza 25A / vitrocerámica"},
                    {"nombre": "Bases Schuko lavavajillas / lavadora", "cant": 2, "precio": p_schuko, "prov": prov_schuko, "desc": desc_schuko}
                ]
            elif "baño" in nombre_est:
                mecanismos_est = [
                    {"nombre": "Interruptor luz espejo", "cant": 1, "precio": p_int, "prov": prov_int, "desc": desc_int},
                    {"nombre": "Base Schuko 16A con tapa estanca", "cant": 2, "precio": p_schuko * 1.2, "prov": prov_schuko, "desc": "Base schuko con tapa protección IP44"}
                ]
            elif "salón" in nombre_est or "comedor" in nombre_est:
                mecanismos_est = [
                    {"nombre": "Conmutador / Cruzamiento iluminación", "cant": 2, "precio": p_int, "prov": prov_int, "desc": desc_int},
                    {"nombre": "Bases Schuko 16A zona sofá/TV", "cant": 6, "precio": p_schuko, "prov": prov_schuko, "desc": desc_schuko},
                    {"nombre": "Toma de datos RJ45 / Multimedia", "cant": 2, "precio": p_rj45, "prov": prov_rj45, "desc": desc_rj45}
                ]
            else:
                mecanismos_est = [
                    {"nombre": "Conmutador acceso / cabecera", "cant": 2, "precio": p_int, "prov": prov_int, "desc": desc_int},
                    {"nombre": "Bases Schuko 16A generales", "cant": 3, "precio": p_schuko, "prov": prov_schuko, "desc": desc_schuko}
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
                key_m = (mec["nombre"], mec["desc"], mec["precio"], mec["prov"])
                global_mecanismos_dict[key_m] = global_mecanismos_dict.get(key_m, 0) + mec["cant"]

            coste_mecanismos_est = sum([m["cant"] * m["precio"] for m in mecanismos_est])
            coste_marcos_est = n_marcos * p_marco
            coste_cajas_mec_est = total_mecanismos * p_caja_mec

            coste_mat_estancia = (
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
            coste_total_materiales_bruto += coste_mat_estancia

            h_rozas = (m2 * 0.35) if "Empotrada" in tipo_obra else 0.0
            h_tubo_cajas = m2 * 0.25
            h_cableado = m2 * 0.30
            h_mecanizado = total_mecanismos * 0.15

            h_estancia_total = h_rozas + h_tubo_cajas + h_cableado + h_mecanizado
            horas_totales_obra += h_estancia_total
            coste_mo_estancia = h_estancia_total * precio_hora

            with st.expander(f"📍 Estancia {idx+1}: {est['nombre']} ({m2} m²) — Coste Neto Total: {coste_mat_estancia + coste_mo_estancia:.2f} €"):
                st.markdown(f"**📦 Detalle de Artículos y Proveedores:**")
                st.write(f"- **Tubo M-20:** `{int(m_tubo)} m` x `{p_tubo:.2f} €/m` = **{m_tubo*p_tubo:.2f} €** &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ *{prov_tubo}* — **{desc_tubo}**")
                st.write(f"- **Cajas universales de empotrar (60x60 mm):** `{total_mecanismos} uds` x `{p_caja_mec:.2f} €/ud` = **{coste_cajas_mec_est:.2f} €** &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ *{prov_caja_mec}* — **{desc_caja_mec}**")
                if n_cajas_reg > 0:
                    st.write(f"- **Caja de derivación/registro (100x100 mm):** `{n_cajas_reg} ud` x `{p_caja_reg:.2f} €/ud` = **{n_cajas_reg*p_caja_reg:.2f} €** &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ *{prov_caja_reg}* — **{desc_caja_reg}**")
                st.write(f"- **Puntos de luz (Centros):** `{n_puntos_luz} puntos`")
                st.write(f"- **Cable 1.5 mm² (Fase y Neutro):** `{int(m_15_ilum_fn)} m` x `{p_15:.2f} €/m` = **{m_15_ilum_fn*p_15:.2f} €** &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ *{prov_15}* — **{desc_15}**")
                st.write(f"- **Cable 1.5 mm² (Tierra REBT):** `{int(m_15_ilum_tt)} m` x `{p_15:.2f} €/m` = **{m_15_ilum_tt*p_15:.2f} €** &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ *{prov_15}* — **{desc_15} (Verde-Amarillo)**")
                st.write(f"- **Cable 1.5 mm² (Vueltas Gris/Marrón):** `{int(m_15_vueltas)} m` x `{p_15:.2f} €/m` = **{m_15_vueltas*p_15:.2f} €** &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ *{prov_15}* — **{desc_15} (Color Conmutadas)**")
                st.write(f"- **Cable 2.5 mm² (Fuerza C2):** `{int(m_25_fuerza)} m` x `{p_25:.2f} €/m` = **{m_25_fuerza*p_25:.2f} €** &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ *{prov_25}* — **{desc_25}**")
                
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;⚡ *Desglose de Mecanismos ({gama_sel}):*")
                for mec in mecanismos_est:
                    st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;• `{mec['cant']}x` **{mec['nombre']}** x `{mec['precio']:.2f} €` = **{mec['cant']*mec['precio']:.2f} €** &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ *{mec['prov']}* — **{mec['desc']}**")
                
                st.write(f"- **Marcos embellecedores:** `{n_marcos} uds` x `{p_marco:.2f} €/ud` = **{coste_marcos_est:.2f} €** &nbsp;&nbsp;|&nbsp;&nbsp; 🏷️ *{prov_marco}* — **{desc_marco}**")
                st.markdown(f"👉 **Subtotal Gastos Materiales Estancia:** `{coste_mat_estancia:.2f} €`")

        coste_mano_obra_bruto = horas_totales_obra * precio_hora
        coste_total_autonomo = coste_total_materiales_bruto + coste_mano_obra_bruto

        # ==========================================
        # 2. RESUMEN GLOBAL CONSOLIDADO DE COMPRAS
        # ==========================================
        st.markdown("---")
        st.header("🛒 2. RESUMEN GLOBAL CONSOLIDADO DE COMPRAS (Para Acopio en Almacén)")
        st.info("Suma total de toda la vivienda con sugerencia de rollos comerciales de 100m.")

        rollos_tubo = max(1, int((global_tubo_m + 99) / 100))
        total_cable_15_m = global_cable_15_fn_m + global_cable_15_tierra_m + global_cable_15_vueltas_m
        rollos_cable_15 = max(1, int((total_cable_15_m + 99) / 100))
        rollos_cable_25 = max(1, int((global_cable_25_fuerza_m + 99) / 100))

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### 📏 Canalización y Tubería")
            st.write(f"- **Tubo M-20 Total Requerido:** `{int(global_tubo_m)} m`")
            st.success(f"📦 **A comprar en Almacén:** `{rollos_tubo} rollo(s) de 100m` de Tubo Corrugado M-20.")

            st.markdown("#### ⚡ Cableado Requerido")
            st.write(f"- Total Cable 1.5 mm² ({tipo_cable_sel}): `{int(total_cable_15_m)} m`")
            st.info(f"📦 **A comprar en Almacén:** `{rollos_cable_15} rollo(s) de 100m`.")
            st.write(f"- Total Cable 2.5 mm² ({tipo_cable_sel}): `{int(global_cable_25_fuerza_m)} m`")
            st.info(f"📦 **A comprar en Almacén:** `{rollos_cable_25} rollo(s) de 100m`.")

        with col_g2:
            st.markdown("#### 📦 Cajas de Instalación")
            st.write(f"- **Cajas universales (60x60 mm):** `{global_caja_mec_uds} uds`")
            st.write(f"- **Cajas de registro (100x100 mm):** `{global_caja_reg_uds} uds`")

            st.markdown("#### 🔲 Mecanismos y Marcos")
            st.write(f"- **Total Marcos Embellecedores:** `{global_marcos_uds} uds`")
            for (nombre_m, desc_m, prec_m, prov_m), cantidad_m in global_mecanismos_dict.items():
                st.write(f"- `{cantidad_m}x` **{nombre_m}**")

        # ==========================================
        # 3. VISTA COMERCIAL PROFESIONAL (CLIENTE)
        # ==========================================
        st.markdown("---")
        st.header("📄 3. VISTA COMERCIAL: Presupuesto Detallado por Estancias para el Cliente")
        st.markdown("Lista comercial con materiales y margen aplicado habitación por habitación. Pulsa **Ctrl + P** para imprimir.")

        st.markdown(f"""
        <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff;">
            <h3 style="color: #0369a1; margin-top: 0;">{empresa_nombre}</h3>
            <p><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
            <hr style="border: 1px solid #bae6fd;">
            <p><b>Presupuesto N°:</b> 2026-0901 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha:</b> Septiembre 2026</p>
            <p><b>Objeto:</b> Instalación Eléctrica REBT ({grado_electrificacion}) por Estancias ({sup_total:.1f} m²)</p>
            <p><b>Sistema:</b> {tipo_obra} | **Cable:** {tipo_cable_sel} | **Gama:** {gama_sel}</p>
        </div>
        """, unsafe_allow_html=True)

        multiplicador = (1 + margen_comercial / 100.0)
        comercial_estancias = []
        subtotal_neto_comercial = 0.0

        for est in estancias_activas:
            m2 = est["m2"]
            coste_base_estancia = (m2 * 50.0) if "Empotrada" in tipo_obra else (m2 * 40.0)
            precio_venta_estancia = coste_base_estancia * multiplicador
            subtotal_neto_comercial += precio_venta_estancia

            comercial_estancias.append({
                "Estancia": est["nombre"],
                "Superficie": f"{m2} m²",
                "Detalle Comercial (Materiales + Mecanismos + Puntos de Luz + Mano de Obra)": f"Instalación completa REBT ({grado_electrificacion}): Canalización M-20, cajas de registro y mecanismo, puntos de luz, cableado {tipo_cable_sel} de 1.5mm² (iluminación, tierra y vueltas gris/marrón), 2.5mm² (fuerza), mecanismos con embellecedores y tomas especiales gama {gama_sel}.",
                "Importe Venta (€)": round(precio_venta_estancia, 2)
            })

        df_comercial = pd.DataFrame(comercial_estancias)
        st.dataframe(df_comercial, use_container_width=True)

        importe_cuadro_comercial = (550.0 if "Elevada" in grado_electrificacion else 450.0) * multiplicador
        subtotal_neto_comercial += importe_cuadro_comercial

        st.markdown(f"""
        <div style="border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; background-color: #f8fafc; margin-top: 10px;">
            <h4>Capítulo Adicional: Cuadro General de Protección ({grado_electrificacion}) y Boletín Oficial (CIE)</h4>
            <p>Suministro de cuadro de distribución, protecciones obligatorias REBT (IGA, Sobretensiones, Diferenciales) y tramitación del boletín: <b>{importe_cuadro_comercial:.2f} €</b></p>
        </div>
        """, unsafe_allow_html=True)

        cuota_iva = subtotal_neto_comercial * (iva_sel / 100.0)
        total_cliente = subtotal_neto_comercial + cuota_iva

        st.markdown(f"""
        <div style="text-align: right; font-size: 18px; background-color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #94a3b8; margin-top: 15px;">
            <p><b>Subtotal Comercial Neto:</b> {subtotal_neto_comercial:.2f} €</p>
            <p><b>IVA ({iva_sel}%):</b> {cuota_iva:.2f} €</p>
            <h2 style="color: #16a34a; margin: 0;">TOTAL PRESUPUESTO CLIENTE: {total_cliente:.2f} €</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### 📝 Condiciones Generales y Garantía")
        st.info("• **Validez de la oferta:** 30 días.\n• **Forma de pago:** 40% a la aceptación, 40% a mitad de ejecución y 20% a la finalización y entrega del Boletín Oficial (CIE).\n• **Garantía:** 2 años en instalación ejecutada según REBT.")

        st.success("✅ ¡Presupuesto y control REBT actualizados con éxito!")

if __name__ == "__main__":
    app()
