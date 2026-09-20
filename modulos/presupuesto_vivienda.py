# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos: Control Técnico por Estancias y Vista Comercial por Habitaciones
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

    st.title("🏡 Generador de Presupuestos: Control por Estancias y Costes de Autónomo")
    st.markdown("Desglose pormenorizado por habitación (Materiales, Colores de Cable con Conmutadas en Gris/Marrón, Horas de Mano de Obra y Vista Comercial por Estancias).")

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

    # 3. Estado de Sesión para Estancias y Partidas Extra
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
            est["m2"] = st.number_input(f"m2 {i}", value=est["m2"], min_value=1.0, step=0.5, key=f"m2_est_{i}", label_visibility="collapsed")
        with cols[2]:
            est["altura"] = st.number_input(f"Alt {i}", value=est["altura"], min_value=2.0, max_value=5.0, step=0.1, key=f"alt_est_{i}", label_visibility="collapsed")
        with cols[3]:
            est["incluir"] = st.checkbox(f"Inc {i}", value=est["incluir"], key=f"inc_est_{i}", label_visibility="collapsed")
        
        if est["incluir"]:
            estancias_activas.append(est)

    st.markdown("---")

    # GESTIÓN DE PARTIDAS EXTRA
    st.subheader("🛠️ Partidas Extra / Imprevistos")
    with st.form("form_extra"):
        c_ex1, c_ex2, c_ex3 = st.columns([3, 2, 1])
        with c_ex1:
            desc_ext = st.text_input("Concepto (Ej: Punto de luz terraza)")
        with c_ex2:
            precio_ext = st.number_input("Coste Neto (€)", min_value=0.0, step=10.0)
        with c_ex3:
            cant_ext = st.number_input("Cantidad", min_value=1, value=1)
        if st.form_submit_button("Añadir Partida Extra"):
            if desc_ext:
                st.session_state.partidas_extra.append({"Concepto": desc_ext, "Precio": precio_ext, "Cantidad": cant_ext})
                st.success("Añadido correctamente.")

    if st.session_state.partidas_extra:
        for idx, p in enumerate(st.session_state.partidas_extra):
            st.write(f"- {p['Concepto']} | {p['Precio']}€ x {p['Cantidad']}")
            if st.button("Eliminar", key=f"del_{idx}"):
                st.session_state.partidas_extra.pop(idx)
                st.rerun()

    st.markdown("---")

    if st.button("🚀 Calcular Presupuesto y Desgloses", type="primary"):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia.")
            return

        sup_total = sum([e["m2"] for e in estancias_activas])
        
        # ---------------------------------------------------------
        # CÁLCULO PORMENORIZADO POR ESTANCIA (COSTES DE AUTÓNOMO)
        # ---------------------------------------------------------
        detalle_tecnico = []
        coste_total_materiales_bruto = 0.0
        horas_totales_obra = 0.0

        for est in estancias_activas:
            m2 = est["m2"]
            alt = est["altura"]
            
            m_tubo = m2 * 4.2 * (alt / 2.5)
            m_c1 = m2 * 12.0  # 1.5mm² (Iluminación y Vueltas)
            m_c2 = m2 * 15.0  # 2.5mm² (Enchufes y Fuerza)
            mecanismos = max(3, int(m2 / 4))
            
            mat_coste = (m_tubo * 0.45) + (m_c1 * 0.35) + (m_c2 * 0.50) + (mecanismos * 6.5)
            coste_total_materiales_bruto += mat_coste
            
            horas_est = round(m2 * 0.75, 1)
            horas_totales_obra += horas_est

            detalle_tecnico.append({
                "Estancia": est["nombre"],
                "Sup (m²)": m2,
                "Tubo M-20": f"{int(m_tubo)} m",
                "Cable 1.5mm² (Fases, Neutro y Vueltas Gris/Marrón)": f"{int(m_c1)} m",
                "Cable 2.5mm² (Fases, Neutro y Tierra)": f"{int(m_c2)} m",
                "Mecanismos": f"{mecanismos} uds",
                "Horas Trab.": f"{horas_est} h",
                "Coste Mat. Neto (€)": round(mat_coste, 2)
            })

        df_tecnico = pd.DataFrame(detalle_tecnico)

        perimetro = sup_total * 0.8 * 4
        rozas_ml = perimetro * 1.5 if "Empotrada" in tipo_obra else 0
        sacos_yeso = max(2, int(rozas_ml / 12)) if "Empotrada" in tipo_obra else 0
        coste_albañileria_bruto = (rozas_ml * 3.5) + (sacos_yeso * 7.5)
        coste_total_materiales_bruto += coste_albañileria_bruto

        coste_mano_obra_bruto = horas_totales_obra * precio_hora
        total_extras_neto = sum([p["Precio"] * p["Cantidad"] for p in st.session_state.partidas_extra])

        # ==========================================
        # 1. INFORME TÉCNICO INTERNO (PARA EL AUTÓNOMO)
        # ==========================================
        st.markdown("---")
        st.header("🛠️ 1. INFORME TÉCNICO Y DE COSTES (Para el Instalador)")
        st.info("Desglose milimétrico por habitación con metrajes, colores de cable especificados (incluyendo gris y marrón para conmutadas) y costes netos para ti.")

        st.dataframe(df_tecnico, use_container_width=True)

        st.markdown("### 🎨 Especificación de Colores de Cables (Normativa REBT y Práctica):")
        st.markdown("""
        * **Fase Principal (L):** Marrón / Negro.
        * **Neutro (N):** Azul claro.
        * **Protección / Tierra (PE):** Verde - Amarillo.
        * **Vueltas de Interruptor, Conmutadas y Cruzamientos:** Hilos de color **Gris** y **Marrón** (para identificar claramente las maniobras en registros y mecanismos).
        """)

        st.markdown("### 💰 Resumen Financiero Interno (Lo que te cuesta ejecutar la obra)")
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Coste Neto Materiales", f"{coste_total_materiales_bruto:.2f} €")
        with col_r2:
            st.metric("Horas Totales / Operarios", f"{horas_totales_obra} h ({num_operarios} operarios)")
        with col_r3:
            st.metric("Coste Neto Mano de Obra", f"{coste_mano_obra_bruto:.2f} €")

        coste_total_autonomo = coste_total_materiales_bruto + coste_mano_obra_bruto + total_extras_neto
        st.error(f"🔴 **COSTE TOTAL PARA TI COMO AUTÓNOMO (Sin Margen): {coste_total_autonomo:.2f} €**")

        # ==========================================
        # 2. VISTA COMERCIAL PROFESIONAL (PARA EL CLIENTE)
        # ==========================================
        st.markdown("---")
        st.header("📄 2. VISTA COMERCIAL: Presupuesto Detallado por Estancias para el Cliente")
        st.markdown("Lista comercial con materiales y margen aplicado habitación por habitación. Pulsa **Ctrl + P** en tu teclado para imprimir o guardar como PDF limpio.")

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

        # Construir tabla comercial detallada por estancias con márgenes
        multiplicador = (1 + margen_comercial / 100.0)
        
        comercial_estancias = []
        subtotal_neto_comercial = 0.0

        for est in estancias_activas:
            m2 = est["m2"]
            coste_base_m2 = 42.0 if "Empotrada" in tipo_obra else 32.0
            precio_comercial_m2 = coste_base_m2 * multiplicador
            importe_estancia = m2 * precio_comercial_m2
            subtotal_neto_comercial += importe_estancia

            comercial_estancias.append({
                "Estancia": est["nombre"],
                "Superficie": f"{m2} m²",
                "Detalle de Suministro, Canalización, Cableado y Mecanismos": f"Instalación completa: Tubo M-20, cableado libre de halógenos (fase, neutro, tierra y hilos de color gris/marrón para conmutadas y vueltas), cajas de registro y mecanismos gama {gama_sel}.",
                "Importe (€)": round(importe_estancia, 2)
            })

        df_comercial = pd.DataFrame(comercial_estancias)
        st.dataframe(df_comercial, use_container_width=True)

        # Capítulo adicional para Cuadro y Boletín (CIE)
        importe_cuadro_comercial = 450.0 * multiplicador
        subtotal_neto_comercial += importe_cuadro_comercial

        if total_extras_neto > 0:
            importe_extras_comercial = total_extras_neto * multiplicador
            subtotal_neto_comercial += importe_extras_comercial

        st.markdown(f"""
        <div style="border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; background-color: #f8fafc; margin-top: 10px;">
            <h4>Capítulo Adicional: Cuadro General de Protección y Boletín Oficial (CIE)</h4>
            <p>Suministro de cuadro de distribución, protecciones obligatorias (IGA, Sobretensiones, Diferenciales) y tramitación de boletín REBT: <b>{importe_cuadro_comercial:.2f} €</b></p>
        </div>
        """, unsafe_allow_html=True)

        cuota_iva = subtotal_neto_comercial * (iva_sel / 100.0)
        total_cliente = subtotal_neto_comercial + cuota_iva

        # Totales finales comerciales
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

        st.success("✅ ¡Presupuesto y desgloses actualizados correctamente con colores de cables y vista comercial por estancias!")

if __name__ == "__main__":
    app()
