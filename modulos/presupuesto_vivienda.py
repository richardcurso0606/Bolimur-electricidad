# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos: Inspector REBT (ITC-BT-25), IGA Oficial por Potencia, Distancias Reales y Acopio
Autor: Richard Orlando Choque Tejerina (Bolimur Electricidad)
"""

import streamlit as st
import pandas as pd
import openpyxl
import os

def app():
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

    st.title("🏡 Generador de Presupuestos: Panel de Ingeniería REBT e Inspector IA")
    st.markdown("Cumplimiento estricto de la ITC-BT-25, cálculo de distancias reales al cuadro y acopio en firme.")

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
    # FUNCIONES DE BÚSQUEDA INTELIGENTE
    # ==========================================
    def buscar_mas_economico(df, main_kw, sub_kw=None):
        mejores_candidatos = []
        main_kw_lower = main_kw.lower()
        sub_kw_lower = sub_kw.lower() if sub_kw else None
        
        for idx, row in df.iterrows():
            desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
            if main_kw_lower in desc:
                if sub_kw_lower is None or sub_kw_lower in desc:
                    try:
                        precio = float(row['Precio S/IVA (€)'])
                        prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                        art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                        fila = idx + 2
                        mejores_candidatos.append((precio, prov, art_desc, fila))
                    except:
                        continue
                        
        if mejores_candidatos:
            mejores_candidatos.sort(key=lambda x: x[0])
            p, prov, desc, fila = mejores_candidatos[0]
            return p, prov, desc, True, fila
            
        return 0.45, "Obramat", "Artículo estándar", False, -1

    def buscar_mecanismo_por_filtro(df, tipo, modo_sel, valor_sel):
        kw_map = {
            'interruptor': ['interruptor', 'conmutador'],
            'schuko': ['schuko', 'enchufe'],
            'rj45': ['rj45', 'datos'],
            'marco': ['marco 1 elemento', 'marco']
        }
        keywords = kw_map.get(tipo, ['interruptor'])
        mejores_candidatos = []
        valor_lower = valor_sel.lower()

        for kw in keywords:
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                serie_item = str(row.get('Serie / Gama', '')).strip().lower()
                marca_item = str(row.get('Marca', '')).strip().lower()
                gama_item = str(row.get('Nivel de Gama / Aplicación', '')).strip().lower()
                
                if kw in desc:
                    match = False
                    if modo_sel == "Por Clasificación de Gamas":
                        if valor_lower in serie_item or valor_lower in desc or valor_lower in gama_item:
                            match = True
                    else:
                        if valor_lower in marca_item or valor_lower in serie_item:
                            match = True

                    if match:
                        try:
                            precio = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            fila = idx + 2
                            mejores_candidatos.append((precio, prov, art_desc, fila))
                        except:
                            continue

        if not mejores_candidatos:
            for kw in keywords:
                for idx, row in df.iterrows():
                    desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                    if kw in desc:
                        try:
                            precio = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            fila = idx + 2
                            mejores_candidatos.append((precio, prov, art_desc, fila))
                        except:
                            continue

        if mejores_candidatos:
            mejores_candidatos.sort(key=lambda x: x[0])
            return mejores_candidatos[0][0], mejores_candidatos[0][1], mejores_candidatos[0][2], True, mejores_candidatos[0][3]

        return 3.50, "Obramat", "Artículo estándar", False, -1

    def buscar_proteccion_por_marca(df, tipo_prot, marca_sel):
        marca_lower = marca_sel.lower()
        kw_map = {
            'iga': ['interruptor general automático', 'iga'],
            'diferencial': ['interruptor diferencial', 'diferencial'],
            'pia': ['magnetotérmico', 'interrup.', 'automático']
        }
        keywords = kw_map.get(tipo_prot, ['automático'])
        mejores_candidatos = []

        for kw in keywords:
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                marca_item = str(row.get('Marca', '')).strip().lower()
                
                if kw in desc and marca_lower in marca_item:
                    # Evitar que coja especiales de VE si buscamos IGA general
                    if tipo_prot == 'iga' and 'vehículo' in desc:
                        continue
                    try:
                        precio = float(row['Precio S/IVA (€)'])
                        prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                        art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                        fila = idx + 2
                        mejores_candidatos.append((precio, prov, art_desc, fila))
                    except:
                        continue

        if not mejores_candidatos:
            return buscar_mas_economico(df, keywords[0])

        if mejores_candidatos:
            mejores_candidatos.sort(key=lambda x: x[0])
            return mejores_candidatos[0][0], mejores_candidatos[0][1], mejores_candidatos[0][2], True, mejores_candidatos[0][3]

        return 15.00, "Obramat", "Protección estándar", False, -1

    def buscar_caja_cuadro(df, marca_sel):
        marca_lower = marca_sel.lower()
        mejores_candidatos = []
        for idx, row in df.iterrows():
            desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
            marca_item = str(row.get('Marca', '')).strip().lower()
            if ('caja' in desc or 'automatismos' in desc or 'envolvente' in desc) and marca_lower in marca_item:
                try:
                    precio = float(row['Precio S/IVA (€)'])
                    prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                    art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                    fila = idx + 2
                    mejores_candidatos.append((precio, prov, art_desc, fila))
                except:
                    continue
        if mejores_candidatos:
            mejores_candidatos.sort(key=lambda x: x[0])
            return mejores_candidatos[0][0], mejores_candidatos[0][1], mejores_candidatos[0][2], True, mejores_candidatos[0][3]
        return buscar_mas_economico(df, 'caja de distribución')

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
    # PARÁMETROS DE POTENCIA REBT E IGA OFICIAL
    # ==========================================
    st.markdown("---")
    st.subheader("⚙️ Parámetros de Potencia y Escalones IGA (Guía-BT-10 / ITC-BT-25)")

    col_pot1, col_pot2 = st.columns(2)
    with col_pot1:
        potencia_prevista_kw = st.selectbox(
            "Selecciona la Potencia Prevista / Escalón REBT",
            [
                "5.750 W (Básica - IGA 25A)",
                "7.360 W (Básica Ampliada - IGA 32A)",
                "9.200 W (Elevada - IGA 40A)",
                "11.500 W (Elevada - IGA 50A)",
                "14.490 W (Elevada - IGA 63A)"
            ]
        )
    with col_pot2:
        tipo_cable_sel = st.selectbox(
            "Tecnología de Cableado",
            ["Libre de Halógenos (H07Z1-K)", "PVC Normal / Estándar (H07V-K)"]
        )

    # Traducción automática de potencia e IGA según selección oficial
    if "5.750" in potencia_prevista_kw:
        grado_electr = "Básica"
        iga_amperaje = 25
        num_circuitos_base = 5
    elif "7.360" in potencia_prevista_kw:
        grado_electr = "Básica"
        iga_amperaje = 32
        num_circuitos_base = 6
    elif "9.200" in potencia_prevista_kw:
        grado_electr = "Elevada"
        iga_amperaje = 40
        num_circuitos_base = 8
    elif "11.500" in potencia_prevista_kw:
        grado_electr = "Elevada"
        iga_amperaje = 50
        num_circuitos_base = 10
    else:
        grado_electr = "Elevada"
        iga_amperaje = 63
        num_circuitos_base = 12

    st.info(f"📋 **Configuración Automática REBT:** Electrificación **{grado_electr}** | **IGA Oficial: {iga_amperaje} A** | Circuitos mínimos requeridos: **{num_circuitos_base}**")

    # Selección de Marcas
    st.markdown("#### 🔌 Selección de Marcas y Series Comerciales")
    col_meca1, col_meca2 = st.columns(2)
    with col_meca1:
        st.markdown("**1️⃣ Mecanismos (Enchufes e Interruptores)**")
        modo_seleccion = st.radio("Filtrar mecanismos por:", ["Por Clasificación de Gamas", "Por Marca Directa"], horizontal=True, key="modo_meca")
        if modo_seleccion == "Por Clasificación de Gamas":
            serie_mecanismos = st.selectbox(
                "Selecciona la Gama / Serie:",
                [
                    "Simon 10 (Gama Económica / Básica)",
                    "Simon 27 Play (Gama Estándar / Residencial)",
                    "Simon 82 Detail (Gama Alta / Decorativa)",
                    "Schneider Asfora (Gama Media)",
                    "Niessen Zenit (Gama Alta / Moderna)"
                ]
            )
        else:
            marcas_meca = sorted([str(m) for m in df_precios['Marca'].dropna().unique() if m not in ['Obramat', 'Leroy Merlin', 'General']])
            serie_mecanismos = st.selectbox("Selecciona la Marca de Mecanismos:", marcas_meca if marcas_meca else ["Simon", "Schneider"])

    with col_meca2:
        st.markdown("**2️⃣ Protecciones y Cuadro Eléctrico**")
        marcas_prot = sorted([str(m) for m in df_precios[df_precios['Familia / Categoria'].str.contains('Protecciones', case=False, na=False)]['Marca'].dropna().unique()])
        if not marcas_prot:
            marcas_prot = ["Schneider", "Chint", "Legrand"]
        marca_protecciones = st.selectbox("Selecciona la Marca del Cuadro Eléctrico:", marcas_prot)

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

    st.markdown("---")

    # ==========================================
    # GESTIÓN DINÁMICA DE ESTANCIAS Y DISTANCIAS
    # ==========================================
    if 'estancias_pro' not in st.session_state:
        st.session_state.estancias_pro = [
            {"nombre": "Salón - Comedor", "m2": 25.0, "altura": 2.6, "distancia_cuadro": 12.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0},
            {"nombre": "Cocina", "m2": 12.0, "altura": 2.6, "distancia_cuadro": 8.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0},
            {"nombre": "Dormitorio Principal", "m2": 16.0, "altura": 2.6, "distancia_cuadro": 14.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0},
            {"nombre": "Dormitorio 2", "m2": 11.0, "altura": 2.6, "distancia_cuadro": 10.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0},
            {"nombre": "Baño 1", "m2": 6.0, "altura": 2.6, "distancia_cuadro": 6.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0},
            {"nombre": "Pasillo", "m2": 7.0, "altura": 2.6, "distancia_cuadro": 3.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0},
        ]

    st.subheader("📋 Estancias, Distancia Real al Cuadro (Pasillo) y Puntos")
    st.markdown("Configura la distancia lineal desde el Cuadro General hasta la caja de registro de cada estancia.")

    with st.expander("➕ Añadir Nueva Estancia a la Vivienda"):
        with st.form("form_nueva_estancia"):
            col_n1, col_n2, col_n3, col_n4 = st.columns([3, 2, 2, 2])
            with col_n1:
                nuevo_nombre = st.text_input("Nombre de la Estancia (Ej: Terraza, Despacho)")
            with col_n2:
                nuevo_m2 = st.number_input("Superficie (m²)", min_value=1.0, value=10.0, step=0.5)
            with col_n3:
                nuevo_alt = st.number_input("Altura (m)", min_value=2.0, max_value=5.0, value=2.6, step=0.1)
            with col_n4:
                nueva_dist = st.number_input("Dist. al Cuadro (m)", min_value=1.0, max_value=40.0, value=10.0, step=1.0)
            
            if st.form_submit_button("Agregar Estancia"):
                if nuevo_nombre:
                    st.session_state.estancias_pro.append({
                        "nombre": nuevo_nombre, "m2": nuevo_m2, "altura": nuevo_alt, "distancia_cuadro": nueva_dist,
                        "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0
                    })
                    st.success(f"Estancia '{nuevo_nombre}' añadida correctamente.")
                    st.rerun()
                else:
                    st.warning("Introduce un nombre válido para la estancia.")

    estancias_activas = []
    for i, est in enumerate(st.session_state.estancias_pro):
        nombre_est = est["nombre"].lower()
        es_banio = "baño" in nombre_est or "aseo" in nombre_est
        es_cocina = "cocina" in nombre_est
        
        circuitos_asociados = "C1 (Luz) + C2 (Enchufes generales 16A)"
        if es_banio:
            circuitos_asociados = "C1 (Luz) + C5 (Tomas húmedas baño)"
        elif es_cocina:
            circuitos_asociados = "C1 (Luz) + C3 (Horno/Vitro 25A) + C4 (Lavavajillas/Lavadora/Termo 20A) + C5 (Encimera)"

        with st.container():
            cols = st.columns([3, 1.5, 1.5, 2, 0.8, 0.8])
            with cols[0]:
                est["nombre"] = st.text_input(f"Nombre {i}", value=est["nombre"], key=f"est_nom_{i}", label_visibility="collapsed")
            with cols[1]:
                est["m2"] = st.number_input(f"m2 {i}", value=est["m2"], min_value=1.0, step=0.5, key=f"est_m2_{i}", label_visibility="collapsed")
            with cols[2]:
                est["altura"] = st.number_input(f"Alt {i}", value=est["altura"], min_value=2.0, max_value=5.0, step=0.1, key=f"est_alt_{i}", label_visibility="collapsed")
            with cols[3]:
                est["distancia_cuadro"] = st.number_input(f"Dist {i}", value=est.get("distancia_cuadro", 10.0), min_value=1.0, max_value=40.0, step=1.0, key=f"est_dist_{i}", label_visibility="collapsed")
            with cols[4]:
                incluir = st.checkbox(f"Inc {i}", value=True, key=f"est_inc_{i}", label_visibility="collapsed")
            with cols[5]:
                if st.button("🗑️", key=f"del_est_{i}"):
                    st.session_state.estancias_pro.pop(i)
                    st.rerun()

            with st.expander(f"⚙️ Circuitos REBT y Puntos Extra en: {est['nombre']}"):
                st.info(f"⚡ **Circuitos REBT Asignados:** `{circuitos_asociados}` | 📏 **Distancia al Cuadro:** `{est['distancia_cuadro']} m`")
                
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    est["extra_schuko"] = st.number_input(f"Schukos Extra", min_value=-5, max_value=15, value=est.get("extra_schuko", 0), key=f"ex_sch_{i}")
                with col_p2:
                    est["extra_luz"] = st.number_input(f"Puntos Luz Extra", min_value=-3, max_value=10, value=est.get("extra_luz", 0), key=f"ex_luz_{i}")
                with col_p3:
                    est["extra_rj45"] = st.number_input(f"Tomas Red/TV Extra", min_value=-2, max_value=5, value=est.get("extra_rj45", 0), key=f"ex_rj_{i}")

        if incluir:
            estancias_activas.append(est)

    st.markdown("---")

    # ==========================================
    # FISCALIZADOR TÉCNICO REBT (INSPECTOR IA)
    # ==========================================
    st.subheader("🛡️ Inspector Técnico REBT (Fiscalización en Vivo - ITC-BT-25)")

    sup_total_calculada = sum([e["m2"] for e in estancias_activas])
    tiene_cocina = any("cocina" in e["nombre"].lower() for e in estancias_activas)
    tiene_banio = any("baño" in e["nombre"].lower() or "aseo" in e["nombre"].lower() for e in estancias_activas)

    alertas_inspector = []
    
    # 1. Comprobación de superficie vs grado de electrificación
    if sup_total_calculada > 160.0 and grado_electr == "Básica":
        alertas_inspector.append(f"🔴 **Incumplimiento ITC-BT-25:** La superficie útil total de la vivienda ({sup_total_calculada:.1f} m²) supera los 160 m² estipulados. El reglamento obliga a utilizar **Electrificación Elevada**.")

    # 2. Comprobación de cocina obligatoria
    if not tiene_cocina:
        alertas_inspector.append("🔴 **Incumplimiento ITC-BT-25:** No se ha detectado ninguna estancia catalogada como 'Cocina'. El reglamento exige obligatoriamente los circuitos C3 y C4.")

    # 3. Comprobación de baño obligatorio
    if not tiene_banio:
        alertas_inspector.append("🟠 **Aviso REBT:** No se ha detectado ningún cuarto de baño o aseo. Se recomienda incluir al menos un circuito C5 para zonas húmedas.")

    if alertas_inspector:
        for alerta in alertas_inspector:
            st.error(alerta)
        
        forzar_inspector = st.checkbox("⚠️ Forzar ejecución del presupuesto bajo responsabilidad del instalador autorizado", value=False)
        if not forzar_inspector:
            st.stop()
    else:
        st.success("🟢 **Inspección REBT Superada con Éxito:** La configuración cumple rigurosamente con los requisitos de la ITC-BT-25 y los escalones de potencia IGA.")

    st.markdown("---")

    if st.button("🚀 Calcular Presupuesto, Distancias y Generar Paneles", type="primary"):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia.")
            return

        # Búsqueda inteligente de materiales
        p_tubo20, prov_tubo20, desc_tubo20, _, fila_tubo20 = buscar_mas_economico(df_precios, 'm20', 'corrugado')
        p_tubo25, prov_tubo25, desc_tubo25, _, fila_tubo25 = buscar_mas_economico(df_precios, 'm25', 'corrugado')

        p_caja_mec, prov_caja_mec, desc_caja_mec, _, fila_caja_mec = buscar_mas_economico(df_precios, '67mm', 'mecanismos')
        p_caja_reg, prov_caja_reg, desc_caja_reg, _, fila_caja_reg = buscar_mas_economico(df_precios, '100x100', 'registro')
        
        # Cables 1.5mm² y 2.5mm²
        p_15_az, prov_15_az, desc_15_az, _, fila_15_az = buscar_mas_economico(df_precios, '1.5 mm²', 'azul')
        p_15_ne, prov_15_ne, desc_15_ne, _, fila_15_ne = buscar_mas_economico(df_precios, '1.5 mm²', 'negro')
        p_15_ma, prov_15_ma, desc_15_ma, _, fila_15_ma = buscar_mas_economico(df_precios, '1.5 mm²', 'marrón')
        p_15_gr, prov_15_gr, desc_15_gr, _, fila_15_gr = buscar_mas_economico(df_precios, '1.5 mm²', 'gris')
        p_15_tt, prov_15_tt, desc_15_tt, _, fila_15_tt = buscar_mas_economico(df_precios, '1.5 mm²', 'amarillo')

        p_25_az, prov_25_az, desc_25_az, _, fila_25_az = buscar_mas_economico(df_precios, '2.5 mm²', 'azul')
        p_25_ne, prov_25_ne, desc_25_ne, _, fila_25_ne = buscar_mas_economico(df_precios, '2.5 mm²', 'negro')
        p_25_ma, prov_25_ma, desc_25_ma, _, fila_25_ma = buscar_mas_economico(df_precios, '2.5 mm²', 'marrón')
        if not fila_25_ne or p_25_ne == 0.45:
            p_25_ne, prov_25_ne, desc_25_ne, _, fila_25_ne = p_25_ma, prov_25_ma, desc_25_ma, _, fila_25_ma
        p_25_tt, prov_25_tt, desc_25_tt, _, fila_25_tt = buscar_mas_economico(df_precios, '2.5 mm²', 'amarillo')

        p_utp, prov_utp, desc_utp, _, fila_utp = buscar_mas_economico(df_precios, 'utp', 'cat.6')
        if not prov_utp or p_utp == 0.45:
            p_utp, prov_utp, desc_utp, _, fila_utp = buscar_mas_economico(df_precios, 'cable de red', 'cat.6')

        if "Wago" in tipo_conexion:
            p_con, prov_con, desc_con, _, fila_con = buscar_mas_economico(df_precios, 'wago 221', '3 conductores')
            nombre_conexion_txt = "Conectores Rápidos Wago 221 (Caja 50ud)"
        else:
            p_con, prov_con, desc_con, _, fila_con = buscar_mas_economico(df_precios, 'clema', '10mm')
            nombre_conexion_txt = "Regleta / Clema de Conexión 12 Polos"

        # Mecanismos y Protecciones (buscadores corregidos)
        p_int, prov_int, desc_int, _, fila_int = buscar_mecanismo_por_filtro(df_precios, 'interruptor', modo_seleccion, serie_mecanismos)
        p_schuko, prov_schuko, desc_schuko, _, fila_schuko = buscar_mecanismo_por_filtro(df_precios, 'schuko', modo_seleccion, serie_mecanismos)
        p_rj45, prov_rj45, desc_rj45, _, fila_rj45 = buscar_mecanismo_por_filtro(df_precios, 'rj45', modo_seleccion, serie_mecanismos)
        p_marco, prov_marco, desc_marco, _, fila_marco = buscar_mecanismo_por_filtro(df_precios, 'marco', modo_seleccion, serie_mecanismos)

        p_iga, prov_iga, desc_iga, _, fila_iga = buscar_proteccion_por_marca(df_precios, 'iga', marca_protecciones)
        p_id, prov_id, desc_id, _, fila_id = buscar_proteccion_por_marca(df_precios, 'diferencial', marca_protecciones)
        p_pia, prov_pia, desc_pia, _, fila_pia = buscar_proteccion_por_marca(df_precios, 'pia', marca_protecciones)
        
        # Búsqueda precisa de la caja del cuadro en la categoría correcta de envolventes
        p_caja_cuadro, prov_caja_cuadro, desc_caja_cuadro, _, fila_caja_cuadro = buscar_caja_cuadro(df_precios, marca_protecciones)

        # Acumuladores globales
        global_tubo20_m = 0.0
        global_tubo25_m = 0.0
        global_caja_mec_uds = 0
        global_caja_reg_uds = 0
        
        global_15_az_m = 0.0
        global_15_ne_m = 0.0
        global_15_ma_m = 0.0
        global_15_gr_m = 0.0
        global_15_tt_m = 0.0
        
        global_25_az_m = 0.0
        global_25_ne_m = 0.0
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
            dist_cuadro = est["distancia_cuadro"]
            nombre_est = est["nombre"].lower()

            ex_sch = est.get("extra_schuko", 0)
            ex_luz = est.get("extra_luz", 0)
            ex_rj45 = est.get("extra_rj45", 0)

            # Tubo troncal + rozas
            tubo_troncal = dist_cuadro * 2.0
            m_tubo_rozas = (m2 * 4.5 * (alt / 2.5)) + (ex_sch * 6.0) + (ex_luz * 5.0) + (ex_rj45 * 8.0)
            m_tubo_total_estancia = tubo_troncal + m_tubo_rozas
            
            m_tubo_20 = m_tubo_total_estancia * 0.75
            m_tubo_25 = m_tubo_total_estancia * 0.25
            n_cajas_reg = 1 if m2 > 8 else 0
            
            base_15 = (m2 * 12.0) + (ex_luz * 15.0) + (dist_cuadro * 3.0)
            est_15_az = base_15 * 0.30
            est_15_ne = base_15 * 0.30
            est_15_ma = base_15 * 0.20
            est_15_gr = base_15 * 0.10
            est_15_tt = base_15 * 0.10

            base_25 = (m2 * (15.0 if grado_electr == "Elevada" else 12.0)) + (ex_sch * 18.0) + (dist_cuadro * 3.0)
            est_25_az = base_25 * 0.40
            est_25_ne = base_25 * 0.40
            est_25_tt = base_25 * 0.20

            est_utp = 0.0
            if "salón" in nombre_est or "comedor" in nombre_est or "despacho" in nombre_est:
                est_utp = 15.0 + dist_cuadro
            est_utp += (ex_rj45 * 12.0)

            if "cocina" in nombre_est:
                cant_int = 1 + max(0, ex_luz)
                cant_sch = 4 + max(0, ex_sch)
                mecanismos_est = [
                    {"nombre": "Interruptor simple", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int},
                    {"nombre": "Base Schuko 16A", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko},
                    {"nombre": "Base fuerza 25A Horno/Vitro", "desc_real": desc_schuko, "cant": 1, "precio": p_schuko * 1.5, "prov": prov_schuko, "fila": fila_schuko},
                    {"nombre": "Bases Schuko lavavajillas/lavadora", "desc_real": desc_schuko, "cant": 2, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko}
                ]
            elif "baño" in nombre_est:
                cant_int = 1 + max(0, ex_luz)
                cant_sch = 2 + max(0, ex_sch)
                mecanismos_est = [
                    {"nombre": "Interruptor luz espejo", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int},
                    {"nombre": "Base Schuko tapa estanca IP44", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko * 1.2, "prov": prov_schuko, "fila": fila_schuko}
                ]
            elif "salón" in nombre_est or "comedor" in nombre_est:
                cant_int = 2 + max(0, ex_luz)
                cant_sch = 6 + max(0, ex_sch)
                cant_rj = 2 + max(0, ex_rj45)
                mecanismos_est = [
                    {"nombre": "Conmutador / Cruzamiento", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int},
                    {"nombre": "Bases Schuko zona TV/Sofá", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko},
                    {"nombre": "Toma de datos RJ45", "desc_real": desc_rj45, "cant": cant_rj, "precio": p_rj45, "prov": prov_rj45, "fila": fila_rj45}
                ]
            else:
                cant_int = 2 + max(0, ex_luz)
                cant_sch = 3 + max(0, ex_sch)
                mecanismos_est = [
                    {"nombre": "Conmutador / Interruptor", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int},
                    {"nombre": "Bases Schuko 16A", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko}
                ]

            total_mecanismos = sum([m["cant"] for m in mecanismos_est])
            n_marcos = max(total_mecanismos, int(total_mecanismos * 0.8))

            global_tubo20_m += m_tubo_20
            global_tubo25_m += m_tubo_25
            global_caja_mec_uds += total_mecanismos
            global_caja_reg_uds += n_cajas_reg
            
            global_15_az_m += est_15_az
            global_15_ne_m += est_15_ne
            global_15_ma_m += est_15_ma
            global_15_gr_m += est_15_gr
            global_15_tt_m += est_15_tt
            
            global_25_az_m += est_25_az
            global_25_ne_m += est_25_ne
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
                (est_15_az * p_15_az) + (est_15_ne * p_15_ne) + (est_15_ma * p_15_ma) + (est_15_gr * p_15_gr) + (est_15_tt * p_15_tt) +
                (est_25_az * p_25_az) + (est_25_ne * p_25_ne) + (est_25_tt * p_25_tt) +
                (est_utp * p_utp) +
                coste_mecanismos_est +
                coste_marcos_est
            )
            coste_mat_estancia_con_iva = coste_mat_estancia_neto * 1.21
            coste_total_materiales_bruto += coste_mat_estancia_neto

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
                "Detalle Comercial": f"Instalación REBT ({potencia_prevista_kw}) | Dist. Cuadro: {dist_cuadro}m",
                "Importe Venta (€)": round(precio_venta_estancia, 2)
            })

            desgloses_internos_estancias.append({
                "nombre": est["nombre"],
                "m2": m2,
                "dist_cuadro": dist_cuadro,
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
                "cable_15_ne": est_15_ne,
                "cable_15_ma": est_15_ma,
                "cable_15_gr": est_15_gr,
                "cable_15_tt": est_15_tt,
                "cable_25_az": est_25_az,
                "cable_25_ne": est_25_ne,
                "cable_25_tt": est_25_tt,
                "cable_utp": est_utp
            })

        coste_mano_obra_bruto = horas_totales_obra * precio_hora

        # Protecciones del Cuadro Eléctrico
        n_difs = 2 if grado_electr == "Elevada" else 1
        n_pias = max(num_circuitos_base, len(estancias_activas))
        coste_cuadro_neto = p_iga + (n_difs * p_id) + (n_pias * p_pia) + p_caja_cuadro
        venta_cuadro_neto = coste_cuadro_neto * mult_comercial * mult_garantia_mat
        benef_cuadro = venta_cuadro_neto - coste_cuadro_neto

        subtotal_general_neto = subtotal_neto_comercial + venta_cuadro_neto
        cuota_iva = subtotal_general_neto * (iva_sel / 100.0)
        total_cliente = subtotal_general_neto + cuota_iva

        # ==========================================
        # SELECTOR DE MODO DE VISTA E IMPRESIÓN
        # ==========================================
        st.markdown("---")
        modo_impresion = st.radio(
            "🖨️ SELECCIONA EL MODO DE VISTA:",
            [
                "🛠️ 1. Panel Interno y Acopio (Exclusivo para ti - Autónomo)",
                "📄 2. Vista Comercial (Para entregar al Cliente)"
            ],
            horizontal=True
        )
        st.markdown("---")

        if modo_impresion.startswith("🛠️"):
            st.header("🔒 Panel Interno de Trabajo, Distancias y Acopio")
            st.markdown(f"**Instalador:** {instalador_nombre} | **Potencia / IGA:** {potencia_prevista_kw} | **Cuadro:** {marca_protecciones}")
            st.markdown("---")

            st.markdown(f"""
            <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff; margin-bottom: 25px;">
                <h3 style="color: #0369a1; margin-top: 0;">💼 RESUMEN ECONÓMICO PARA EL CLIENTE (A Cobrar)</h3>
                <p><b>Subtotal Comercial Neto:</b> {subtotal_general_neto:.2f} €</p>
                <p><b>IVA ({iva_sel}%):</b> {cuota_iva:.2f} €</p>
                <h2 style="color: #16a34a; margin: 0;">TOTAL A COBRAR AL CLIENTE: {total_cliente:.2f} €</h2>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("⏱️ Análisis de Rendimiento y Tiempos de Mano de Obra")
            st.write(f"- 🧱 **Fase de Rozas ({tipo_pared}):** `{sum_h_rozas:.2f} h`")
            st.write(f"- 📏 **Fase de Canalización:** `{sum_h_tubos:.2f} h`")
            st.write(f"- ⚡ **Fase de Cableado:** `{sum_h_cable:.2f} h`")
            st.write(f"- 🔲 **Fase de Mecanizado:** `{sum_h_mec:.2f} h`")
            st.info(f"⏱️ **Total Horas:** `{horas_totales_obra:.2f} h` x `{precio_hora:.2f} €/h` = **`{coste_mano_obra_bruto:.2f} €`**")
            st.markdown("---")

            st.subheader("🛒 Resumen Global de Acopio (Con Filas Verificadas del Excel)")
            
            rollos_tubo20 = max(1, int((global_tubo20_m + 49) / 50))
            rollos_tubo25 = max(1, int((global_tubo25_m + 49) / 50))

            rollos_15_az = max(1, int((global_15_az_m + 99) / 100))
            rollos_15_ne = max(1, int((global_15_ne_m + 99) / 100))
            rollos_15_ma = max(1, int((global_15_ma_m + 99) / 100))
            rollos_15_gr = max(1, int((global_15_gr_m + 99) / 100))
            rollos_15_tt = max(1, int((global_15_tt_m + 99) / 100))

            rollos_25_az = max(1, int((global_25_az_m + 99) / 100))
            rollos_25_ne = max(1, int((global_25_ne_m + 99) / 100))
            rollos_25_tt = max(1, int((global_25_tt_m + 99) / 100))

            total_mat_estancias_neto = coste_total_materiales_bruto
            total_mat_global_neto = total_mat_estancias_neto + coste_cuadro_neto
            total_mat_con_iva = total_mat_global_neto * 1.21

            st.markdown("#### 📏 1. Canalización y Tubería")
            st.write(f"- **Tubo M-20:** `{int(global_tubo20_m)} m` | Proveedor: **{prov_tubo20}** | `[Fila Excel: #{fila_tubo20}]` | 📦 `{rollos_tubo20} rollo(s) de 50m`")
            st.write(f"- **Tubo M-25:** `{int(global_tubo25_m)} m` | Proveedor: **{prov_tubo25}** | `[Fila Excel: #{fila_tubo25}]` | 📦 `{rollos_tubo25} rollo(s) de 50m`")

            st.markdown("---")
            st.markdown(f"#### ⚡ 2. Cableado ({tipo_cable_sel})")
            st.write(f"- Azul 1.5mm²: `{int(global_15_az_m)} m` | `[Fila: #{fila_15_az}]` | 📦 `{rollos_15_az} rollo(s)`")
            st.write(f"- Negro 1.5mm²: `{int(global_15_ne_m)} m` | `[Fila: #{fila_15_ne}]` | 📦 `{rollos_15_ne} rollo(s)`")
            st.write(f"- Marrón 1.5mm²: `{int(global_15_ma_m)} m` | `[Fila: #{fila_15_ma}]` | 📦 `{rollos_15_ma} rollo(s)`")
            st.write(f"- Gris 1.5mm²: `{int(global_15_gr_m)} m` | `[Fila: #{fila_15_gr}]` | 📦 `{rollos_15_gr} rollo(s)`")
            st.write(f"- Tierra 1.5mm²: `{int(global_15_tt_m)} m` | `[Fila: #{fila_15_tt}]` | 📦 `{rollos_15_tt} rollo(s)`")
            st.write(f"- Azul 2.5mm²: `{int(global_25_az_m)} m` | `[Fila: #{fila_25_az}]` | 📦 `{rollos_25_az} rollo(s)`")
            st.write(f"- Negro 2.5mm²: `{int(global_25_ne_m)} m` | `[Fila: #{fila_25_ne}]` | 📦 `{rollos_25_ne} rollo(s)`")
            st.write(f"- Tierra 2.5mm²: `{int(global_25_tt_m)} m` | `[Fila: #{fila_25_tt}]` | 📦 `{rollos_25_tt} rollo(s)`")

            st.markdown("---")
            st.markdown(f"#### ⚡ 4. Cuadro Eléctrico y Protecciones (Marca: {marca_protecciones})")
            st.write(f"- **Caja de Distribución:** 1 ud | `[Fila Excel: #{fila_caja_cuadro}]` | Ref: `{desc_caja_cuadro}` | S/IVA: `{p_caja_cuadro:.2f} €`")
            st.write(f"- **IGA Oficial ({iga_amperaje}A):** 1 ud | `[Fila Excel: #{fila_iga}]` | Ref: `{desc_iga}` | S/IVA: `{p_iga:.2f} €`")
            st.write(f"- **Interruptor Diferencial (ID):** `{n_difs} ud(s)` | `[Fila Excel: #{fila_id}]` | Ref: `{desc_id}` | S/IVA c/u: `{p_id:.2f} €`")
            st.write(f"- **PIAs Automáticos:** `{n_pias} uds` | `[Fila Excel: #{fila_pia}]` | Ref: `{desc_pia}` | S/IVA c/u: `{p_pia:.2f} €`")

            st.markdown(f"""
            <div style="border: 2px solid #16a34a; padding: 20px; border-radius: 10px; background-color: #f0fdf4; margin-top: 20px;">
                <h3 style="color: #15803d; margin-top: 0;">💳 DINERO TOTAL NECESARIO EN CAJA (ACOPIO COMPLETO)</h3>
                <p><b>Coste Materiales Estancias:</b> {total_mat_estancias_neto:.2f} € &nbsp;|&nbsp; <b>Coste Cuadro ({marca_protecciones}):</b> {coste_cuadro_neto:.2f} €</p>
                <p><b>Coste Total Materiales Neto (Sin IVA):</b> {total_mat_global_neto:.2f} €</p>
                <h2 style="color: #16a34a; margin: 0;">TOTAL A PAGAR EN EL ALMACÉN (Con 21% IVA): {total_mat_con_iva:.2f} €</h2>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📊 Análisis detallado de Utilidad y Rentabilidad")
            venta_mat_estancias = total_mat_estancias_neto * mult_comercial * mult_garantia_mat
            benef_mat_estancias = venta_mat_estancias - total_mat_estancias_neto
            
            venta_mo_neto = coste_mano_obra_bruto * mult_comercial
            benef_mo = venta_mo_neto - coste_mano_obra_bruto
            
            venta_cuadro_neto_val = coste_cuadro_neto * mult_comercial * mult_garantia_mat
            benef_cuadro = venta_cuadro_neto_val - coste_cuadro_neto
            
            benef_neto_total = benef_mat_estancias + benef_mo + benef_cuadro

            st.write(f"- 📦 **Materiales de Estancias:** Beneficio: `+{benef_mat_estancias:.2f} €`")
            st.write(f"- ⏱️ **Mano de Obra:** Beneficio: `+{benef_mo:.2f} €`")
            st.write(f"- ⚡ **Cuadro Eléctrico ({marca_protecciones}):** Beneficio: `+{benef_cuadro:.2f} €`")
            st.success(f"🚀 **UTILIDAD / BENEFICIO NETO TOTAL ESTIMADO: +{benef_neto_total:.2f} €** (Sin contar IVA)")

        else:
            st.header("📄 Vista Comercial: Presupuesto para el Cliente")
            st.markdown(f"""
            <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff;">
                <h3 style="color: #0369a1; margin-top: 0;">{empresa_nombre}</h3>
                <p><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
                <hr style="border: 1px solid #bae6fd;">
                <p><b>Presupuesto N°:</b> 2026-0901 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha:</b> Septiembre 2026</p>
                <p><b>Objeto:</b> Instalación Eléctrica REBT ({potencia_prevista_kw}) con Mecanismos <b>{serie_mecanismos}</b> y Protecciones <b>{marca_protecciones}</b></p>
            </div>
            """, unsafe_allow_html=True)

            df_comercial = pd.DataFrame(comercial_estancias)
            st.dataframe(df_comercial, use_container_width=True)

            st.markdown(f"""
            <div style="text-align: right; font-size: 18px; background-color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #94a3b8; margin-top: 15px;">
                <p><b>Subtotal Comercial Neto:</b> {subtotal_general_neto:.2f} €</p>
                <p><b>IVA ({iva_sel}%):</b> {cuota_iva:.2f} €</p>
                <h2 style="color: #16a34a; margin: 0;">TOTAL PRESUPUESTO CLIENTE: {total_cliente:.2f} €</h2>
            </div>
            """, unsafe_allow_html=True)

        st.success("✅ ¡Inspector REBT y buscador de cuadro optimizados al 100%!")

if __name__ == "__main__":
    app()
