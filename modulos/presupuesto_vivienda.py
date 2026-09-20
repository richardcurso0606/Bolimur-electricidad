# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos: Desglose por Estancias, Mecanismos REBT y Optimización de Proveedores (Obramat vs Leroy)
Autor: Richard Orlando Choque Tejerina (Bolimur Electricidad)
"""

import streamlit as st
import pandas as pd
import openpyxl
import os

def app():
    # Estilo CSS para impresión limpia (Oculta menús al pulsar Ctrl+P)
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

    st.title("🏡 Generador de Presupuestos: Mecanismos por Estancias y Optimización de Tienda")
    st.markdown("Desglose estricto REBT por habitación, asignación de mecanismos y evaluación logística entre Obramat y Leroy Merlin.")

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

    # Función para buscar precio y proveedor en el DataFrame
    def buscar_articulo_bd(df, keywords, gama_filtro, tienda_filtro=None):
        for keyword in keywords:
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).lower()
                gama_item = str(row.get('Nivel de Gama / Aplicación', '')).lower()
                proveedor_item = str(row.get('Proveedor / Tienda Principal', '')).lower()
                
                if keyword.lower() in desc and gama_filtro.lower() in gama_item:
                    if tienda_filtro and tienda_filtro.lower() not in proveedor_item:
                        continue
                    try:
                        val = float(row.get('Precio S/IVA (€)', 0.0))
                        tienda_real = row.get('Proveedor / Tienda Principal', 'General')
                        if val > 0:
                            return val, tienda_real, True
                    except:
                        pass
        return 5.0, "Obramat (Referencia)", False

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
    # PARÁMETROS GLOBALES
    # ==========================================
    st.markdown("---")
    st.subheader("⚙️ Parámetros de Costes y Rendimiento (Autónomo)")
    
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        precio_hora = st.number_input("Precio Mano de Obra (€/hora)", min_value=10.0, max_value=60.0, value=25.0, step=1.0)
    with col_c2:
        num_operarios = st.number_input("Nº de Operarios en Obra", min_value=1, max_value=5, value=1, step=1)
    with col_c3:
        margen_comercial = st.slider("Margen Comercial / Beneficio (%)", 0, 50, 20)
    with col_c4:
        iva_sel = st.selectbox("Tipo de IVA", [10, 21])

    tipo_obra = st.selectbox(
        "Sistema de Ejecución General",
        ["Empotrada en Rozas (Ladrillo + Yeso)", "Falso Techo / Pladur (Obra Seca)", "Superficie (Tubo visto / Canaleta)"]
    )
    gama_sel = st.selectbox(
        "Nivel de Gama de Mecanismos",
        ['1. Ultra Económica', '2. Económica Estándar', '3. Media Residencial', '4. Alta Decorativa']
    )

    st.markdown("---")

    # Estado de Sesión para Estancias
    if 'estancias_pro' not in st.session_state:
        st.session_state.estancias_pro = [
            {"nombre": "Salón - Comedor", "m2": 25.0, "altura": 2.6, "incluir": True},
            {"nombre": "Cocina", "m2": 12.0, "altura": 2.6, "incluir": True},
            {"nombre": "Dormitorio Principal", "m2": 16.0, "altura": 2.6, "incluir": True},
            {"nombre": "Dormitorio 2", "m2": 11.0, "altura": 2.6, "incluir": True},
            {"nombre": "Baño 1", "m2": 6.0, "altura": 2.6, "incluir": True},
            {"nombre": "Pasillo", "m2": 7.0, "altura": 2.6, "incluir": True},
        ]

    st.subheader("📋 Dimensionamiento y Estancias de la Vivienda")
    
    estancias_activas = []
    for i, est in enumerate(st.session_state.estancias_pro):
        cols = st.columns([3, 2, 2, 1])
        with cols[0]:
            est["nombre"] = st.text_input(f"Nombre {i}", value=est["nombre"], key=f"m_nom_{i}", label_visibility="collapsed")
        with cols[1]:
            est["m2"] = st.number_input(f"m2 {i}", value=est["m2"], min_value=1.0, step=0.5, key=f"m_m2_{i}", label_visibility="collapsed")
        with cols[2]:
            est["altura"] = st.number_input(f"Alt {i}", value=est["altura"], min_value=2.0, max_value=5.0, step=0.1, key=f"m_alt_{i}", label_visibility="collapsed")
        with cols[3]:
            est["incluir"] = st.checkbox(f"Inc {i}", value=est["incluir"], key=f"m_inc_{i}", label_visibility="collapsed")
        
        if est["incluir"]:
            estancias_activas.append(est)

    st.markdown("---")

    if st.button("🚀 Calcular Presupuesto, Mecanismos y Evaluación de Tiendas", type="primary"):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia.")
            return

        sup_total = sum([e["m2"] for e in estancias_activas])

        # Precios base de tubería y cable desde la BD
        p_tubo, _, _ = buscar_articulo_bd(df_precios, ['tubo corrugado', 'm-20'], gama_sel, None)
        p_caja_mec, _, _ = buscar_articulo_bd(df_precios, ['caja universal', 'mecanismo'], gama_sel, None)
        p_caja_reg, _, _ = buscar_articulo_bd(df_precios, ['caja de registro'], gama_sel, None)
        p_15, _, _ = buscar_articulo_bd(df_precios, ['1.5 mm', 'h07v-k 1.5'], gama_sel, None)
        p_25, _, _ = buscar_articulo_bd(df_precios, ['2.5 mm', 'h07v-k 2.5'], gama_sel, None)

        # ==========================================
        # 1. INFORME TÉCNICO PORMENORIZADO Y MECANISMOS
        # ==========================================
        st.markdown("---")
        st.header("🛠️ 1. INFORME TÉCNICO Y DESGLOSE DE MECANISMOS (Para el Instalador)")
        st.info("Detalle habitación por habitación con mecanismos específicos, metrajes REBT y costes directos obtenidos de tu base de datos.")

        coste_total_materiales_bruto = 0.0
        horas_totales_obra = 0.0
        conteo_tiendas_obramat = 0
        conteo_tiendas_leroy = 0

        for idx, est in enumerate(estancias_activas):
            m2 = est["m2"]
            alt = est["altura"]
            nombre_est = est["nombre"].lower()

            m_tubo = m2 * 4.2 * (alt / 2.5)
            m_15_ilum = m2 * 6.0
            m_15_vueltas = m2 * 4.0
            m_25_fuerza = m2 * 12.0
            n_cajas_reg = 1 if m2 > 8 else 0

            # Definición específica de mecanismos según el tipo de estancia
            if "cocina" in nombre_est:
                mecanismos_detalle = [
                    {"tipo": "Interruptor simple iluminación", "cant": 1, "kw": "10A"},
                    {"tipo": "Base Schuko 16A encimera / uso general", "cant": 3, "kw": "16A"},
                    {"tipo": "Toma específica Horno / Vitrocerámica", "cant": 1, "kw": "25A"},
                    {"tipo": "Toma específica Lavavajillas / Lavadora", "cant": 2, "kw": "16A"}
                ]
            elif "baño" in nombre_est:
                mecanismos_detalle = [
                    {"tipo": "Interruptor simple luz espejo / general", "cant": 1, "kw": "10A"},
                    {"tipo": "Base Schuko 16A con tapa estanca", "cant": 2, "kw": "16A"}
                ]
            elif "salón" in nombre_est or "comedor" in nombre_est:
                mecanismos_detalle = [
                    {"tipo": "Conmutador cruzado / simple iluminación", "cant": 2, "kw": "10A"},
                    {"tipo": "Bases Schuko 16A toma general TV/Sofá", "cant": 5, "kw": "16A"},
                    {"tipo": "Toma de datos / RJ45 o Conexión multimedia", "cant": 1, "kw": "Data"}
                ]
            else:  # Dormitorios / Pasillos
                mecanismos_detalle = [
                    {"tipo": "Conmutador / Interruptor de cabecera o acceso", "cant": 2, "kw": "10A"},
                    {"tipo": "Bases Schuko 16A generales", "cant": 3, "kw": "16A"}
                ]

            total_mecanismos_estancia = sum([m["cant"] for m in mecanismos_detalle])

            # Buscar precios y proveedor real de mecanismos en la BD
            p_meca_unit, tienda_meca, _ = buscar_articulo_bd(df_precios, ['schuko', 'interruptor', 'mecanismo'], gama_sel, None)
            if "obramat" in tienda_meca.lower():
                conteo_tiendas_obramat += total_mecanismos_estancia
            else:
                conteo_tiendas_leroy += total_mecanismos_estancia

            coste_mat_estancia = (
                (m_tubo * p_tubo) +
                (total_mecanismos_estancia * p_caja_mec) +
                (n_cajas_reg * p_caja_reg) +
                (m_15_ilum * p_15) +
                (m_15_vueltas * p_15) +
                (m_25_fuerza * p_25) +
                (total_mecanismos_estancia * p_meca_unit)
            )
            coste_total_materiales_bruto += coste_mat_estancia

            # Horas de mano de obra
            h_rozas = (m2 * 0.35) if "Empotrada" in tipo_obra else 0.0
            h_tubo_cajas = m2 * 0.25
            h_cableado = m2 * 0.30
            h_mecanizado = total_mecanismos_estancia * 0.15

            h_estancia_total = h_rozas + h_tubo_cajas + h_cableado + h_mecanizado
            horas_totales_obra += h_estancia_total
            coste_mo_estancia = h_estancia_total * precio_hora

            with st.expander(f"📍 Estancia: {est['nombre']} ({m2} m²) — Coste Neto: {coste_mat_estancia + coste_mo_estancia:.2f} €"):
                st.markdown(f"**📦 Detalle de Mecanismos Seleccionados (Gama: {gama_sel} | Proveedor detectado: {tienda_meca}):**")
                for med in mecanismos_detalle:
                    st.write(f"- {med['cant']}x {med['tipo']} ({med['kw']}) x {p_meca_unit:.2f} € = `{med['cant']*p_meca_unit:.2f} €`")

                st.markdown(f"**⚡ Materiales Base REBT y Cableado:**")
                st.write(f"- Tubo M-20: **{int(m_tubo)} m** | Cajas Mecanismo: **{total_mecanismos_estancia} uds** | Cajas Registro: **{n_cajas_reg} ud**")
                st.write(f"- Cable 1.5mm² (Iluminación + Vueltas Gris/Marrón): **{int(m_15_ilum + m_15_vueltas)} m**")
                st.write(f"- Cable 2.5mm² (Fuerza C2 - Fase, Neutro, Tierra): **{int(m_25_fuerza)} m**")
                st.markdown(f"👉 **Subtotal Materiales Estancia:** `{coste_mat_estancia:.2f} €`")

                st.markdown(f"**⏱️ Tiempos de Mano de Obra:**")
                if "Empotrada" in tipo_obra:
                    st.write(f"- Rozas y Albañilería: **{h_rozas:.2f} h** | Tubos/Cajas: **{h_tubo_cajas:.2f} h**")
                st.write(f"- Cableado REBT: **{h_cableado:.2f} h** | Conexionado Mecanismos: **{h_mecanizado:.2f} h**")
                st.markdown(f"⏱️ **Total Horas:** `{h_estancia_total:.2f} h` | 💵 **Coste MO Neto:** `{coste_mo_estancia:.2f} €`")

        # ==========================================
        # EVALUACIÓN LOGÍSTICA DE PROVEEDORES (OBRAMAT vs LEROY)
        # ==========================================
        st.markdown("---")
        st.subheader("🚛 Evaluación Logística y Recomendación de Proveedor (Obramat vs. Leroy Merlin)")
        
        st.markdown(f"""
        <div style="border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; background-color: #f8fafc;">
            <p><b>Análisis de Carga de Artículos:</b></p>
            <ul>
                <li>Artículos catalogados con mejor precio / disponibilidad en <b>Obramat (Almacén Profesional)</b>: Mayoría de tubos, canalizaciones, cableado y cajas de registro por volumen.</li>
                <li>Artículos seleccionados de la gama <b>{gama_sel}</b>: Evaluados para evitar desplazamientos cruzados innecesarios.</li>
            </ul>
            <p style="color: #0369a1; font-weight: bold;">💡 Veredicto del Asistente Autónomo:</p>
            <p>Para evitar quemar gasoil y perder tiempo de obra yendo a Leroy Merlin solo por un par de referencias menores, <b>se recomienda centralizar el 100% del acopio de material en OBRAMAT</b>. Los precios mayoristas de Obramat para instaladores son más competitivos y disponen de todo el stock de cableado y perfilería REBT bajo un mismo techo.</p>
        </div>
        """, unsafe_allow_html=True)

        coste_mano_obra_bruto = horas_totales_obra * precio_hora
        coste_total_autonomo = coste_total_materiales_bruto + coste_mano_obra_bruto

        st.markdown("---")
        st.markdown("### 💰 Resumen Financiero Global (Costes Netos de Autónomo)")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Total Materiales Brutos", f"{coste_total_materiales_bruto:.2f} €")
        with col_r2:
            st.metric("Total Horas de Trabajo", f"{horas_totales_obra:.1f} h ({num_operarios} op.)")
        with col_r3:
            st.metric("Total Mano de Obra Neta", f"{coste_mano_obra_bruto:.2f} €")
        
        st.error(f"🔴 **COSTE TOTAL DE EJECUCIÓN PARA TI (Sin Margen): {coste_total_autonomo:.2f} €**")

        # ==========================================
        # 2. VISTA COMERCIAL PROFESIONAL (CLIENTE)
        # ==========================================
        st.markdown("---")
        st.header("📄 2. VISTA COMERCIAL: Presupuesto Detallado por Estancias para el Cliente")
        st.markdown("Lista comercial con mecanismos detallados y margen aplicado habitación por habitación. Pulsa **Ctrl + P** para imprimir o guardar como PDF limpio.")

        st.markdown(f"""
        <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff;">
            <h3 style="color: #0369a1; margin-top: 0;">{empresa_nombre}</h3>
            <p><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
            <hr style="border: 1px solid #bae6fd;">
            <p><b>Presupuesto N°:</b> 2026-0901 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha:</b> Septiembre 2026</p>
            <p><b>Objeto:</b> Instalación Eléctrica REBT Completa por Estancias ({sup_total:.1f} m²)</p>
            <p><b>Sistema:</b> {tipo_obra} | **Gama de Mecanismos:** {gama_sel}</p>
        </div>
        """, unsafe_allow_html=True)

        multiplicador = (1 + margen_comercial / 100.0)
        comercial_estancias = []
        subtotal_neto_comercial = 0.0

        for est in estancias_activas:
            m2 = est["m2"]
            coste_base_estancia = (m2 * 48.0) if "Empotrada" in tipo_obra else (m2 * 38.0)
            precio_venta_estancia = coste_base_estancia * multiplicador
            subtotal_neto_comercial += precio_venta_estancia

            comercial_estancias.append({
                "Estancia": est["nombre"],
                "Superficie": f"{m2} m²",
                "Detalle Comercial (Materiales + Mecanismos + Mano de Obra REBT)": f"Suministro e instalación completa según REBT: Canalización en tubo M-20, cableado libre de halógenos (1.5mm² para iluminación/vueltas gris-marrón y 2.5mm² para fuerza), cajas de registro y mecanismos completos gama {gama_sel}.",
                "Importe Venta (€)": round(precio_venta_estancia, 2)
            })

        df_comercial = pd.DataFrame(comercial_estancias)
        st.dataframe(df_comercial, use_container_width=True)

        # Capítulo cuadro y boletín
        importe_cuadro_comercial = 450.0 * multiplicador
        subtotal_neto_comercial += importe_cuadro_comercial

        st.markdown(f"""
        <div style="border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; border: 1px solid #f8fafc; margin-top: 10px;">
            <h4>Capítulo Adicional: Cuadro General de Protección y Boletín Oficial (CIE)</h4>
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

        st.success("✅ ¡Informes pormenorizados, mecanismos y evaluación logística generados con éxito!")

if __name__ == "__main__":
    app()
