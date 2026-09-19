# -*- coding: utf-8 -*-
"""
Módulo de Presupuesto Inteligente por Estancias, Superficie y Altura
Autor: Richard Orlando Choque Tejerina (Bolimur Electricidad)
"""

import streamlit as st
import pandas as pd
import openpyxl

def app():
    st.title("🏡 Generador de Presupuestos Inteligentes por Estancias")
    st.markdown("Calcula el material exacto y el presupuesto desglosado introduciendo los metros cuadrados y la altura de cada estancia.")

    # Cargar base de datos maestra
    try:
        wb = openpyxl.load_workbook("base_datos_precio_oficial.xlsx")
        ws = wb["Tarifa Maestra Completa"]
        data = list(ws.iter_rows(values_only=True))
        df = pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        st.error(f"No se pudo cargar la base de datos maestra: {e}")
        return

    st.sidebar.header("⚙️ Parámetros Generales")
    gama_seleccionada = st.sidebar.selectbox(
        "Nivel de Gama / Calidad",
        ['1. Ultra Económica', '2. Económica Estándar', '3. Media Residencial', '4. Alta Decorativa']
    )
    
    proveedor_filtro = st.sidebar.selectbox(
        "Proveedor Principal / Tienda",
        ['Optimizado (Mejor Precio Global)', 'Obramat', 'Leroy Merlin']
    )

    st.subheader("📋 Configuración de Estancias de la Vivienda")
    st.markdown("Modifica los metros cuadrados y la altura de cada estancia para una estimación milimétrica.")

    # Inicializar estado de estancias si no existe
    if 'estancias_data' not in st.session_state:
        st.session_state.estancias_data = [
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

    estancias_usuario = []

    # Mostrar estancias de forma limpia y estable
    for i, est in enumerate(st.session_state.estancias_data):
        cols = st.columns([3, 2, 2, 1])
        with cols[0]:
            est["nombre"] = st.text_input(f"Estancia {i}", value=est["nombre"], key=f"nombre_{i}", label_visibility="collapsed")
        with cols[1]:
            est["m2"] = st.number_input(f"m2 {i}", value=est["m2"], min_value=1.0, step=0.5, key=f"m2_{i}", label_visibility="collapsed")
        with cols[2]:
            est["altura"] = st.number_input(f"Altura {i}", value=est["altura"], min_value=2.0, max_value=5.0, step=0.1, key=f"alt_{i}", label_visibility="collapsed")
        with cols[3]:
            est["incluir"] = st.checkbox(f"Incluir {i}", value=est["incluir"], key=f"inc_{i}", label_visibility="collapsed")
        
        if est["incluir"]:
            estancias_usuario.append(est)

    st.markdown("---")

    if st.button("🚀 Calcular Presupuesto y Materiales", type="primary"):
        if not estancias_usuario:
            st.warning("Por favor, selecciona al menos una estancia para calcular.")
            return

        superficie_total = sum([e["m2"] for e in estancias_usuario])
        altura_promedio = sum([e["altura"] for e in estancias_usuario]) / len(estancias_usuario)

        st.success(f"Superficie útil total calculada: **{superficie_total:.1f} m²** | Altura media: **{altura_promedio:.2f} m**")

        # Estimación de materiales
        metros_tubo = superficie_total * 4.2 * (altura_promedio / 2.5)
        metros_cable_15 = superficie_total * 12.0
        metros_cable_25 = superficie_total * 15.0
        metros_cable_4 = superficie_total * 4.5

        df_gama = df[df['Nivel de Gama / Aplicación'] == gama_seleccionada]

        st.subheader("📦 Desglose Automático de Materiales y Presupuesto")

        partidas = [
            {"Concepto": "Tubo Corrugado M-20 (Corona 50m)", "Cantidad": max(1, int(metros_tubo / 50)), "Unidad": "Rollos"},
            {"Concepto": "Cable H07V-K 1.5 mm² (Iluminación)", "Cantidad": int(metros_cable_15), "Unidad": "Metros"},
            {"Concepto": "Cable H07V-K 2.5 mm² (Enchufes)", "Cantidad": int(metros_cable_25), "Unidad": "Metros"},
            {"Concepto": "Cable H07V-K 4 mm² (Cocina/Horno)", "Cantidad": int(metros_cable_4), "Unidad": "Metros"},
            {"Concepto": "Cajas de Registro Derivación", "Cantidad": max(3, int(superficie_total / 15)), "Unidad": "Unidades"},
            {"Concepto": "Mecanismos Interruptores / Conmutadores", "Cantidad": len(estancias_usuario) * 3, "Unidad": "Unidades"},
            {"Concepto": "Bases de Enchufe Schuko 16A", "Cantidad": int(superficie_total / 4), "Unidad": "Unidades"},
        ]

        df_partidas = pd.DataFrame(partidas)
        st.dataframe(df_partidas, use_container_width=True)

        st.subheader("🛒 Artículos Seleccionados de la Base de Datos")
        if not df_gama.empty:
            st.dataframe(df_gama[['ID', 'Familia / Categoria', 'Marca', 'Proveedor / Tienda', 'Descripción Exacta del Artículo', 'Precio S/IVA (€)']], use_container_width=True)
        else:
            st.dataframe(df.head(15)[['ID', 'Familia / Categoria', 'Marca', 'Proveedor / Tienda', 'Descripción Exacta del Artículo']], use_container_width=True)

if __name__ == "__main__":
    app()
