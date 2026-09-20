# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos: Desglose Pormenorizado por Estancias (Costes Internos y Vista Comercial)
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

    st.title("🏡 Generador de Presupuestos: Desglose Detallado por Estancias")
    st.markdown("Control milimétrico por habitación: Materiales, Colores de Cable (Fase, Neutro, Tierra y Vueltas Gris/Marrón), Costes y Horas de Mano de Obra desglosadas.")

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
    # PARÁMETROS GLOBALES DE MANO DE OBRA Y MARGEN
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

    if 'partidas_extra' not in st.session_state:
        st.session_state.partidas_extra = []

    st.subheader("📋 Dimensionamiento y Estancias de la Vivienda")
    
    estancias_activas = []
    for i, est in enumerate(st.session_state.estancias_pro):
        cols = st.columns([3, 2, 2, 1])
        with cols[0]:
            est["nombre"] = st.text_input(f"Nombre {i}", value=est["nombre"], key=f"nombre_est_{i}", label_visibility="collapsed")
        with cols[1]:
            est["m2"] = st.number_input(f"m2 {i}", value=est["m2"], min_value=1.0, step=0.5, key=f"m2_m2_{i}", label_visibility="collapsed")
        with cols[2]:
            est["altura"] = st.number_input(f"Alt {i}", value=est["altura"], min_value=2.0, max_value=5.0, step=0.1, key=f"m2_alt_{i}", label_visibility="collapsed")
        with cols[3]:
            est["incluir"] = st.checkbox(f"Inc {i}", value=est["incluir"], key=f"m2_inc_{i}", label_visibility="collapsed")
        
        if est["incluir"]:
            estancias_activas.append(est)

    st.markdown("---")

    if st.button("🚀 Calcular Presupuesto y Desgloses Pormenorizados", type="primary"):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia.")
            return

        sup_total = sum([e["m2"] for e in estancias_activas])

        # ==========================================
        # 1. INFORME TÉCNICO PORMENORIZADO (AUTÓNOMO)
        # ==========================================
        st.markdown("---")
        st.header("🛠️ 1. INFORME TÉCNICO Y DE COSTES (Para el Instalador)")
        st.info("Desglose detallado estancia por estancia con materiales, colores de cable específicos y desglose de horas de mano de obra.")

        coste_total_materiales_bruto = 0.0
        horas_totales_obra = 0.0

        for idx, est in enumerate(estancias_activas):
            m2 = est["m2"]
            alt = est["altura"]

            # Cálculos técnicos por estancia
            m_tubo = m2 * 4.2 * (alt / 2.5)
            m_fase = m2 * 5.0      # Cable Fase (Marrón/Negro)
            m_neutro = m2 * 5.0    # Cable Neutro (Azul)
            m_tierra = m2 * 5.0    # Cable Tierra (Verde-Amarillo)
            m_vuelta = m2 * 4.0    # Cable Vueltas / Conmutadas (Gris / Marrón)
            mecanismos = max(3, int(m2 / 4))

            # Costes netos de materiales por estancia
            coste_mat_estancia = (
                (m_tubo * 0.45) +
                (m_fase * 0.35) +
                (m_neutro * 0.35) +
                (m_tierra * 0.40) +
                (m_vuelta * 0.35) +
                (mecanismos * 6.50)
            )
            coste_total_materiales_bruto += coste_mat_estancia

            # Horas de mano de obra desglosadas por estancia
            h_rozas = (m2 * 0.35) if "Empotrada" in tipo_obra else 0.0  # Rozas y albañilería / tapado
            h_tubo = m2 * 0.20       # Colocación de tubo y cajas
            h_cableado = m2 * 0.25   # Metida de cables y colores
            h_mecanizado = mecanismos * 0.15 # Conexión de mecanismos

            h_estancia_total = h_rozas + h_tubo + h_cableado + h_mecanizado
            horas_totales_obra += h_estancia_total
            coste_mo_estancia = h_estancia_total * precio_hora

            # Mostrar bloque por estancia
            with st.expander(f"📍 Estancia {idx+1}: {est['nombre']} ({m2} m²)"):
                st.markdown(f"**Materiales requeridos:**")
                st.write(f"- Tubo Corrugado M-20: **{int(m_tubo)} m** (Coste aprox: {m_tubo*0.45:.2f} €)")
                st.write(f"- Cable Fase (Marrón/Negro): **{int(m_fase)} m** (Coste aprox: {m_fase*0.35:.2f} €)")
                st.write(f"- Cable Neutro (Azul): **{int(m_neutro)} m** (Coste aprox: {m_neutro*0.35:.2f} €)")
                st.write(f"- Cable Protección / Tierra (Verde-Amarillo): **{int(m_tierra)} m** (Coste aprox: {m_tierra*0.40:.2f} €)")
                st.write(f"- Cable Vueltas / Conmutadas (Gris / Marrón): **{int(m_vuelta)} m** (Coste aprox: {m_vuelta*0.35:.2f} €)")
                st.write(f"- Mecanismos de superf/empotar ({gama_sel}): **{mecanismos} uds** (Coste aprox: {mecanismos*6.50:.2f} €)")
                st.markdown(f"👉 **Total Gastos Materiales en esta estancia:** `{coste_mat_estancia:.2f} €`")

                st.markdown(f"**Mano de Obra y Tiempos estimados:**")
                if "Empotrada" in tipo_obra:
                    st.write(f"- Picado de Rozas y Albañilería (Yeso/Mortero): **{h_rozas:.2f} horas**")
                st.write(f"- Colocación de Tubo y Cajas de Registro: **{h_tubo:.2f} horas**")
                st.write(f"- Cableado y Etiquetado de Colores: **{h_cableado:.2f} horas**")
                st.write(f"- Conexionado y Mecanizado final: **{h_mecanizado:.2f} horas**")
                st.markdown(f"⏱️ **Total Horas Estancia:** `{h_estancia_total:.2f} h` | 💵 **Coste Mano de Obra Neto:** `{coste_mo_estancia:.2f} €`")

        # Resumen general de costes para el autónomo
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
        st.markdown("Oferta comercial con el margen aplicado por habitación. Pulsa **Ctrl + P** para imprimir o guardar como PDF limpio.")

        st.markdown(f"""
        <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff;">
            <h3 style="color: #0369a1; margin-top: 0;">{empresa_nombre}</h3>
            <p><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
            <hr style="border: 1px solid #bae6fd;">
            <p><b>Presupuesto N°:</b> 2026-0901 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha:</b> Septiembre 2026</p>
            <p><b>Objeto:</b> Instalación Eléctrica Completa por Estancias ({sup_total:.1f} m²)</p>
            <p><b>Sistema:</b> {tipo_obra} | **Gama:** {gama_sel}</p>
        </div>
        """, unsafe_allow_html=True)

        multiplicador = (1 + margen_comercial / 100.0)
        comercial_estancias = []
        subtotal_neto_comercial = 0.0

        for est in estancias_activas:
            m2 = est["m2"]
            coste_base_estancia = (m2 * 42.0) if "Empotrada" in tipo_obra else (m2 * 32.0)
            precio_venta_estancia = coste_base_estancia * multiplicador
            subtotal_neto_comercial += precio_venta_estancia

            comercial_estancias.append({
                "Estancia": est["nombre"],
                "Superficie": f"{m2} m²",
                "Detalle Comercial (Materiales + Mano de Obra y Conexionado)": f"Suministro e instalación completa: Canalización con tubo M-20, cableado de seguridad libre de halógenos (fases, neutro, tierra y hilos de color gris/marrón para conmutadas), cajas de registro y mecanismos gama {gama_sel}.",
                "Importe Venta (€)": round(precio_venta_estancia, 2)
            })

        df_comercial = pd.DataFrame(comercial_estancias)
        st.dataframe(df_comercial, use_container_width=True)

        # Capítulo cuadro y boletín
        importe_cuadro_comercial = 450.0 * multiplicador
        subtotal_neto_comercial += importe_cuadro_comercial

        st.markdown(f"""
        <div style="border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; background-color: #f8fafc; margin-top: 10px;">
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

        st.success("✅ ¡Informes pormenorizados generados con éxito!")

if __name__ == "__main__":
    app()
