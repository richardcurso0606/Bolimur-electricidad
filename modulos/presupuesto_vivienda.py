# -*- coding: utf-8 -*-
"""
Módulo Avanzado de Presupuesto Inteligente por Estancias, Tipo de Obra y REBT
Autor: Richard Orlando Choque Tejerina (Bolimur Electricidad)
"""

import streamlit as st
import pandas as pd
import openpyxl

def app():
    st.title("🏡 Generador Profesional de Presupuestos y Materiales")
    st.markdown("Calcula instalaciones eléctricas completas adaptadas al REBT, especificando tipos de obra (rozas/yeso), superficies y alturas.")

    # Cargar base de datos maestra de precios
    try:
        wb = openpyxl.load_workbook("Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy_v2.xlsx")
        ws = wb["Tarifa Maestra Completa"]
        data = list(ws.iter_rows(values_only=True))
        df = pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        st.error(f"No se pudo cargar la base de datos maestra de precios: {e}")
        return

    # Sidebar: Parámetros de Configuración de Obra
    st.sidebar.header("⚙️ Parámetros de Instalación")
    
    tipo_obra = st.sidebar.selectbox(
        "Tipo de Ejecución / Instalación",
        [
            "Empotrada en Rozas (Ladrillo + Yeso)",
            "Falso Techo / Pladur (Obra Seca)",
            "Superficie (Tubo visto / Canaleta)"
        ]
    )

    gama_seleccionada = st.sidebar.selectbox(
        "Nivel de Gama / Calidad de Mecanismos",
        ['1. Ultra Económica', '2. Económica Estándar', '3. Media Residencial', '4. Alta Decorativa']
    )
    
    incluir_mano_obra = st.sidebar.checkbox("Incluir Estimación de Mano de Obra", value=True)
    margen_comercial = st.sidebar.slider("Margen Comercial / Beneficio (%)", 0, 40, 15)

    st.subheader("📋 Configuración de Estancias, Superficies y Alturas")
    st.markdown("Ajusta los metros cuadrados y la altura libre de cada estancia para calcular con exactitud rozas, metros de tubo y cableado.")

    # Estado inicial de estancias
    if 'estancias_pro' not in st.session_state:
        st.session_state.estancias_pro = [
            {"nombre": "Salón - Comedor", "m2": 25.0, "altura": 2.6, "incluir": True},
            {"nombre": "Cocina", "m2": 12.0, "altura": 2.6, "incluir": True},
            {"nombre": "Dormitorio Principal", "m2": 16.0, "altura": 2.6, "incluir": True},
            {"nombre": "Dormitorio 2", "m2": 11.0, "altura": 2.6, "incluir": True},
            {"nombre": "Dormitorio 3", "m2": 10.0, "altura": 2.6, "incluir": True},
            {"nombre": "Baño 1 (Principal)", "m2": 6.0, "altura": 2.6, "incluir": True},
            {"nombre": "Baño 2", "m2": 4.5, "altura": 2.6, "incluir": True},
            {"nombre": "Pasillo / Distribuidor", "m2": 8.0, "altura": 2.6, "incluir": True},
            {"nombre": "Terraza / Exterior", "m2": 10.0, "altura": 2.6, "incluir": False},
        ]

    estancias_activas = []

    # Renderizado de la tabla de estancias
    cols_h = st.columns([3, 2, 2, 1])
    cols_h[0].markdown("**Estancia**")
    cols_h[1].markdown("**Superficie ($m^2$)**")
    cols_h[2].markdown("**Altura (m)**")
    cols_h[3].markdown("**Incluir**")

    for i, est in enumerate(st.session_state.estancias_pro):
        c = st.columns([3, 2, 2, 1])
        with c[0]:
            est["nombre"] = st.text_input(f"Est {i}", value=est["nombre"], key=f"p_nom_{i}", label_visibility="collapsed")
        with c[1]:
            est["m2"] = st.number_input(f"m2 {i}", value=est["m2"], min_value=1.0, step=0.5, key=f"p_m2_{i}", label_visibility="collapsed")
        with c[2]:
            est["altura"] = st.number_input(f"Alt {i}", value=est["altura"], min_value=2.0, max_value=5.0, step=0.1, key=f"p_alt_{i}", label_visibility="collapsed")
        with c[3]:
            est["incluir"] = st.checkbox(f"Inc {i}", value=est["incluir"], key=f"p_inc_{i}", label_visibility="collapsed")
        
        if est["incluir"]:
            estancias_activas.append(est)

    st.markdown("---")

    if st.button("🚀 Calcular Presupuesto Técnico y Materiales", type="primary"):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia para realizar el cálculo.")
            return

        superficie_total = sum([e["m2"] for e in estancias_activas])
        altura_media = sum([e["altura"] for e in estancias_activas]) / len(estancias_activas)

        st.success(f"📊 **Resumen Dimensional:** Superficie Total: **{superficie_total:.1f} m²** | Altura Media de Paramentos: **{altura_media:.2f} m** | Sistema: **{tipo_obra}**")

        # --- CÁLCULOS TÉCNICOS DE MATERIALES ---
        # Tubos y cables basados en coeficientes REBT y perímetro estimado
        perimetro_estimado = superficie_total * 0.8 * 4  # Estimación geométrica de muros
        metros_rozas = perimetro_estimado * 1.5 if "Empotrada" in tipo_obra else 0
        sacos_yeso = max(2, int(metros_rozas / 12)) if "Empotrada" in tipo_obra else 0

        metros_tubo = superficie_total * 4.5 * (altura_media / 2.5)
        cable_15 = superficie_total * 12.0  # C1 Iluminación
        cable_25 = superficie_total * 16.0  # C2 Enchufes
        cable_40 = superficie_total * 5.0   # C3 Cocina / Horno
        cable_60 = 25.0                     # C4 Lavadora / Termo / AACC

        # Filtrar gama de mecanismos
        df_gama = df[df['Nivel de Gama / Aplicación'] == gama_seleccionada]

        st.subheader("📦 Partidas de Materiales y Obra Civil")

        partidas_tecnicas = [
            {"Partida / Material", "Cantidad", "Unidad", "Observaciones"},
        ]
        
        datos_tabla = [
            {"Partida / Material": f"Tubo Corrugado M-20 (Corona 50m) - [{tipo_obra}]", "Cantidad": max(1, int(metros_tubo / 50)), "Unidad": "Rollos", "Observaciones": "Canalización protegida"},
            {"Partida / Material": "Cable H07V-K 1.5 mm² (Libre Halógenos / Marfil/Azul/Verde)", "Cantidad": int(cable_15), "Unidad": "Metros", "Observaciones": "Circuito C1 (Iluminación)"},
            {"Partida / Material": "Cable H07V-K 2.5 mm² (Fase/Neutro/Tierra)", "Cantidad": int(cable_25), "Unidad": "Metros", "Observaciones": "Circuito C2 (Tomacorrientes)"},
            {"Partida / Material": "Cable H07V-K 4 mm² (Potencia)", "Cantidad": int(cable_40), "Unidad": "Metros", "Observaciones": "Circuito C3 (Cocina / Horno)"},
            {"Partida / Material": "Cable H07V-K 6 mm² (Alta Potencia)", "Cantidad": int(cable_60), "Unidad": "Metros", "Observaciones": "Circuito C4 (Termo / Lavadora)"},
            {"Partida / Material": "Cajas de Registro Derivación empotradas", "Cantidad": max(3, int(superficie_total / 15)), "Unidad": "Unidades", "Observaciones": "Repartidas por estancias"},
            {"Partida / Material": "Mecanismos (Interruptores / Conmutadores)", "Cantidad": len(estancias_activas) * 3, "Unidad": "Unidades", "Observaciones": f"Gama: {gama_seleccionada}"},
            {"Partida / Material": "Bases de Enchufe Schuko 16A con Tierra", "Cantidad": int(superficie_total / 3.5), "Unidad": "Unidades", "Observaciones": f"Gama: {gama_seleccionada}"},
        ]

        if "Empotrada" in tipo_obra:
            datos_tabla.append({"Partida / Material": "Picado y Ejecución de Rozas en Pared", "Cantidad": int(metros_rozas), "Unidad": "Metros", "Observaciones": "Rozas para canalización"})
            datos_tabla.append({"Partida / Material": "Sacos de Yeso / Pasta de Agarre (25 kg)", "Cantidad": int(sacos_yeso), "Unidad": "Sacos", "Observaciones": "Tapado de rozas y cajas"})

        df_resumen = pd.DataFrame(datos_tabla)
        st.dataframe(df_resumen, use_container_width=True)

        st.subheader("🛒 Referencias de la Base de Datos Oficial (Obramat / Leroy Merlin)")
        if not df_gama.empty:
            st.dataframe(df_gama[['ID', 'Familia / Categoria', 'Marca', 'Proveedor / Tienda', 'Descripción Exacta del Artículo', 'Precio S/IVA (€)']], use_container_width=True)
        else:
            st.dataframe(df.head(15)[['ID', 'Familia / Categoria', 'Marca', 'Proveedor / Tienda', 'Descripción Exacta del Artículo']], use_container_width=True)

        st.success("✅ Presupuesto y desglose técnico calculados con éxito. ¡Dime si quieres añadir partidas adicionales!")

if __name__ == "__main__":
    app()
