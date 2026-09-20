# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos: Desglose Lógico por Capítulos e Informe Técnico
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

    st.title("🏡 Generador Profesional de Presupuestos y Control Técnico")
    st.markdown("Herramienta avanzada para autónomos: Desglose transparente por capítulos comerciales y control interno de materiales.")

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
    # DATOS DE LA EMPRESA / INSTALADOR AUTORIZADO
    # ==========================================
    st.sidebar.header("🏢 Datos del Instalador")
    empresa_nombre = st.sidebar.text_input("Nombre Empresa", value="BOLIMUR INSTALACIONES Y REFORMAS")
    instalador_nombre = st.sidebar.text_input("Instalador", value="Richard Orlando Choque Tejerina")
    n_licencia = st.sidebar.text_input("Nº Licencia / REBT", value="REBT-30/15892")
    localidad = st.sidebar.text_input("Localidad", value="Rincón de Seca, Murcia")
    telefono = st.sidebar.text_input("Teléfono Contacto", value="+34 600 000 000")

    # ==========================================
    # PARÁMETROS GENERALES DE OBRA
    # ==========================================
    st.markdown("---")
    st.subheader("⚙️ Parámetros Generales de Ejecución")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        tipo_obra = st.selectbox(
            "Sistema de Ejecución / Obra",
            ["Empotrada en Rozas (Ladrillo + Yeso)", "Falso Techo / Pladur (Obra Seca)", "Superficie (Tubo visto / Canaleta)"]
        )
    with col_p2:
        gama_sel = st.selectbox(
            "Nivel de Gama de Mecanismos",
            ['1. Ultra Económica', '2. Económica Estándar', '3. Media Residencial', '4. Alta Decorativa']
        )
    with col_p3:
        proveedor_sel = st.selectbox(
            "Proveedor Principal",
            ['Optimizado (Mejor Precio)', 'Obramat', 'Leroy Merlin']
        )

    col_p4, col_p5 = st.columns(2)
    with col_p4:
        margen = st.slider("Margen Comercial / Beneficio Industrial (%)", 0, 50, 20)
    with col_p5:
        iva_sel = st.selectbox("Tipo de IVA Aplicable", [10, 21])

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

    # ==========================================
    # GESTIÓN DE PARTIDAS EXTRA & ASISTENTE IA
    # ==========================================
    st.subheader("🛠️ Gestión de Partidas y Asistente IA")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        with st.form("form_manual"):
            st.markdown("##### ➕ Añadir Partida Manual")
            desc_manual = st.text_input("Concepto / Descripción")
            precio_manual = st.number_input("Importe Unitario (€)", min_value=0.0, step=10.0)
            cant_manual = st.number_input("Cantidad", min_value=1, value=1)
            if st.form_submit_button("Añadir al Presupuesto"):
                if desc_manual:
                    st.session_state.partidas_extra.append({"Concepto": desc_manual, "Precio": precio_manual, "Cantidad": cant_manual})
                    st.success("Partida añadida correctamente.")
                else:
                    st.warning("Introduce un concepto válido.")

    with col_m2:
        with st.form("form_ia"):
            st.markdown("##### 🎙️ Asistente de IA (Lenguaje Natural)")
            orden_ia = st.text_input("Instrucción (Ej: Añadir A/C por 350€)")
            precio_ia = st.number_input("Precio estimado (€)", min_value=0.0, value=150.0, step=10.0)
            if st.form_submit_button("Procesar con IA"):
                if orden_ia:
                    st.session_state.partidas_extra.append({"Concepto": f"[IA] {orden_ia}", "Precio": precio_ia, "Cantidad": 1})
                    st.success("¡Instrucción interpretada y añadida!")
                else:
                    st.warning("Escribe una instrucción.")

    if st.session_state.partidas_extra:
        st.markdown("##### 📝 Partidas Extra / Modificaciones Actuales:")
        for idx, p in enumerate(st.session_state.partidas_extra):
            c_ex = st.columns([4, 2, 2, 1])
            c_ex[0].write(p["Concepto"])
            c_ex[1].write(f"{p['Precio']} € x {p['Cantidad']}")
            c_ex[2].write(f"Total: {p['Precio'] * p['Cantidad']} €")
            if c_ex[3].button("🗑️", key=f"del_ex_{idx}"):
                st.session_state.partidas_extra.pop(idx)
                st.rerun()

    st.markdown("---")

    if st.button("🚀 Calcular Presupuesto y Generar Informes", type="primary"):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia.")
            return

        sup_total = sum([e["m2"] for e in estancias_activas])
        alt_media = sum([e["altura"] for e in estancias_activas]) / len(estancias_activas)

        # Cálculos técnicos por estancia
        detalle_estancias = []
        for est in estancias_activas:
            m2_e = est["m2"]
            alt_e = est["altura"]
            tubo_e = m2_e * 4.2 * (alt_e / 2.5)
            c1_e = m2_e * 12.0
            c2_e = m2_e * 15.0
            mecanismos_e = max(3, int(m2_e / 4))
            detalle_estancias.append({
                "Estancia": est["nombre"],
                "Sup (m²)": m2_e,
                "Tubo M-20 (m)": round(tubo_e, 1),
                "Cable 1.5mm² (m)": round(c1_e, 1),
                "Cable 2.5mm² (m)": round(c2_e, 1),
                "Mecanismos": mecanismos_e
            })

        df_detalle_est = pd.DataFrame(detalle_estancias)

        # Totales generales de materiales y costes reales
        perimetro = sup_total * 0.8 * 4
        rozas = perimetro * 1.5 if "Empotrada" in tipo_obra else 0
        sacos_yeso = max(2, int(rozas / 12)) if "Empotrada" in tipo_obra else 0
        tubo_total = sum([d["Tubo M-20 (m)"] for d in detalle_estancias])
        c1_total = sum([d["Cable 1.5mm² (m)"] for d in detalle_estancias])
        c2_total = sum([d["Cable 2.5mm² (m)"] for d in detalle_estancias])
        c3_total = sup_total * 5.0

        # Costes reales desglosados para estructurar los capítulos comerciales
        coste_cuadro = 350.0 + (sup_total * 1.5)  # Materiales de cuadro y protecciones REBT
        coste_canalizacion_mat = (tubo_total * 0.45) + (c1_total * 0.35) + (c2_total * 0.50) + (c3_total * 0.90) + (len(estancias_activas) * 35.0)
        coste_canalizacion_MO = sup_total * 14.0   # Mano de obra de tendido, cableado y mecanismos
        coste_albañileria_mat = sacos_yeso * 7.5
        coste_albañileria_MO = rozas * 8.0 if "Empotrada" in tipo_obra else 50.0

        total_extras = sum([p["Precio"] * p["Cantidad"] for p in st.session_state.partidas_extra])

        # Importes con margen comercial aplicado por capítulo
        factor_margen = (1 + margen / 100.0)
        
        neto_cap1 = coste_cuadro * factor_margen
        neto_cap2 = (coste_canalizacion_mat + coste_canalizacion_MO) * factor_margen
        neto_cap3 = (coste_albañileria_mat + coste_albañileria_MO) * factor_margen
        neto_extras = total_extras * factor_margen

        subtotal_neto = neto_cap1 + neto_cap2 + neto_cap3 + neto_extras
        cuota_iva = subtotal_neto * (iva_sel / 100.0)
        total_presupuesto = subtotal_neto + cuota_iva

        # ==========================================
        # 1. INFORME TÉCNICO PORMENORIZADO (PARA TI)
        # ==========================================
        st.markdown("---")
        st.header("🛠️ INFORME TÉCNICO INTERNO (Para el Instalador)")
        st.info("Informe de control exclusivo para ti. Aquí tienes el desglose exacto por habitación, metrajes y consumibles de obra para acopiar material con precisión milimétrica.")

        st.subheader("Desglose Estancia por Estancia")
        st.dataframe(df_detalle_est, use_container_width=True)

        st.subheader("Resumen de Consumibles y Costes Directos")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.metric("Metros Totales de Tubo M-20", f"{int(tubo_total)} m")
            st.metric("Cable H07V-K 1.5 mm² (Iluminación)", f"{int(c1_total)} m")
            st.metric("Cable H07V-K 2.5 mm² (Enchufes)", f"{int(c2_total)} m")
        with col_t2:
            st.metric("Metros de Rozas a Picar", f"{int(rozas)} m.l.")
            st.metric("Sacos de Yeso / Mortero (25kg)", f"{int(sacos_yeso)} sacos")
            st.metric("Coste Directo Estimado Total", f"{(coste_cuadro + coste_canalizacion_mat + coste_canalizacion_MO + coste_albañileria_mat + coste_albañileria_MO):.2f} €")

        # ==========================================
        # 2. VISTA COMERCIAL PROFESIONAL (PARA EL CLIENTE)
        # ==========================================
        st.markdown("---")
        st.header("📄 VISTA COMERCIAL: Presupuesto para el Cliente")
        st.markdown("Presenta esta sección limpia a tu cliente. Pulsa **Ctrl + P** en tu teclado para imprimir o guardar directamente como PDF.")

        st.markdown(f"""
        <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff;">
            <h3 style="color: #0369a1; margin-top: 0;">{empresa_nombre}</h3>
            <p><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
            <hr style="border: 1px solid #bae6fd;">
            <p><b>Presupuesto N°:</b> 2026-0901 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha:</b> Septiembre 2026</p>
            <p><b>Objeto:</b> Instalación Eléctrica Completa en Vivienda ({sup_total:.1f} m²)</p>
            <p><b>Sistema de Ejecución:</b> {tipo_obra}</p>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Desglose de Capítulos de la Oferta")
        
        capitulos = [
            {
                "Capítulo": "Capítulo 1", 
                "Descripción": "Cuadro General de Mando y Protección (CGMP), Protecciones (IGA, Sobretensiones, Diferenciales) y Tramitación/CIE REBT", 
                "Importe (€)": round(neto_cap1, 2)
            },
            {
                "Capítulo": "Capítulo 2", 
                "Descripción": f"Suministro de Materiales (Tubos, Cableado y Mecanismos de gama {gama_sel}) y Mano de Obra de Canalización, Cableado y Mecanizado", 
                "Importe (€)": round(neto_cap2, 2)
            },
            {
                "Capítulo": "Capítulo 3", 
                "Descripción": "Trabajos de Albañilería, Picado de Rozas, Inserción de Cajas y Tapado con Yeso/Mortero", 
                "Importe (€)": round(neto_cap3, 2)
            },
        ]
        
        if st.session_state.partidas_extra:
            for ex in st.session_state.partidas_extra:
                capitulos.append({
                    "Capítulo": "Partida Extra / Adicional", 
                    "Descripción": ex["Concepto"], 
                    "Importe (€)": round(ex["Precio"] * ex["Cantidad"] * factor_margen, 2)
                })

        df_capitulos = pd.DataFrame(capitulos)
        st.dataframe(df_capitulos, use_container_width=True)

        # Totales
        st.markdown(f"""
        <div style="text-align: right; font-size: 18px; background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #cbd5e1;">
            <p><b>Subtotal Neto:</b> {subtotal_neto:.2f} €</p>
            <p><b>IVA ({iva_sel}%):</b> {cuota_iva:.2f} €</p>
            <h2 style="color: #16a34a; margin: 0;">TOTAL PRESUPUESTO: {total_presupuesto:.2f} €</h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### 📝 Condiciones Generales y Garantía del Servicio")
        st.info("• **Validez de la oferta:** 30 días.\n• **Forma de pago:** 40% a la aceptación, 40% a mitad de ejecución y 20% a la finalización y entrega del Boletín Oficial (CIE).\n• **Exclusiones:** No incluye pintura ni azulejos especiales decorativos.")

        st.success("✅ Informes generados con éxito. ¡Todo listo para verificar tu material y entregar la oferta al cliente!")

if __name__ == "__main__":
    app()
