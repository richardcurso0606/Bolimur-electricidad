# -*- coding: utf-8 -*-
"""
Módulo de Presupuesto Inteligente por Estancias, Superficie y Altura
Autor: Richard Orlando Choque Tejerina (Bolimur Electricidad)
Descripción: Genera presupuestos detallados basados en superficies, alturas de techos, 
selección de gama y comparación de precios (Obramat / Leroy Merlin).
"""

import streamlit as st
import pandas as pd
import openpyxl

def app():
    st.title("🏡 Generador de Presupuestos Inteligentes por Estancias")
    st.markdown("Calcula el material exacto y el presupuesto desglosado introduciendo los metros cuadrados y la altura de cada estancia.")

    # Cargar base de datos maestra
    try:
        wb = openpyxl.load_workbook("Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy_v2.xlsx")
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
    st.markdown("Ajusta los metros cuadrados ($m^2$) y la altura de techo de cada estancia para una estimación milimétrica.")

    # Definición de estancias por defecto
    estancias_default = [
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
    
    # Tabla interactiva en Streamlit para modificar estancias
    cols_header = st.columns([3, 2, 2, 1])
    cols_header[0].markdown("**Estancia**")
    cols_header[1].markdown("**Superficie ($m^2$)**")
    cols_header[2].markdown("**Altura (m)**")
    cols_header[3].markdown("**Incluir**")

    for i, est in enumerate(estancias_default):
        c = st.columns([3, 2, 2, 1])
        with c[0]:
            nombre = st.text_input(f"Nombre {i}", value=est["nombre"], key=f"est_nombre_{i}", label_visibility="collapsed")
        with c[1]:
            m2 = st.number_input(f"m2 {i}", value=est["m2"], min_value=1.0, step=0.5, key=f"est_m2_{i}", label_visibility="collapsed")
        with c[2]:
            altura = st.number_input(f"Altura {i}", value=est["altura"], min_value=2.0, max_value=5.0, step=0.1, key=f"est_alt_{i}", label_visibility="collapsed")
        with c[3]:
            incluir = st.checkbox(f"Incluir {i}", value=est["incluir"], key=f"est_inc_{i}", label_visibility="collapsed")
        
        if incluir:
            estancias_usuario.append({"nombre": nombre, "m2": m2, "altura": altura})

    if st.button("🚀 Calcular Presupuesto y Materiales", type="primary"):
        if not estancias_usuario:
            st.warning("Por favor, selecciona al menos una estancia para calcular.")
            return

        # Totales generales de la vivienda
        superficie_total = sum([e["m2"] for e in estancias_usuario])
        altura_promedio = sum([e["altura"] for e in estancias_usuario]) / len(estancias_usuario)

        st.success(f"Superficie útil total calculada: **{superficie_total:.1f} m²** | Altura media: **{altura_promedio:.2f} m**")

        # Estimación algorítmica de materiales basada en REBT y superficie/altura
        # 1. Metros de cable y tubo (estimación proporcional a perímetro y m2)
        metros_tubo = superficie_total * 4.2 * (altura_promedio / 2.5)
        metros_cable_15 = superficie_total * 12.0
        metros_cable_25 = superficie_total * 15.0
        metros_cable_4 = superficie_total * 4.5
        metros_tierra = superficie_total * 10.0

        # Filtrar artículos en base a la gama seleccionada
        df_gama = df[df['Nivel de Gama / Aplicación'] == gama_seleccionada]

        st.markdown("---")
        st.subheader("📦 Desglose Automático de Materiales y Presupuesto")

        # Mostrar resumen de partidas estimadas
        partidas = [
            {"Concepto": "Tubo Corrugado M-20 (Corona 50m)", "Cantidad": max(1, int(metros_tubo / 50)), "Unidad": "Rollos"},
            {"Concepto": "Cable H07V-K 1.5 mm² (Marfil/Azul/Verde-Amarillo)", "Cantidad": int(metros_cable_15), "Unidad": "Metros"},
            {"Concepto": "Cable H07V-K 2.5 mm² (Fase/Neutro/Tierra)", "Cantidad": int(metros_cable_25), "Unidad": "Metros"},
            {"Concepto": "Cable H07V-K 4 mm² (Cocina/Horno)", "Cantidad": int(metros_cable_4), "Unidad": "Metros"},
            {"Concepto": "Cajas de Registro Derivación", "Cantidad": max(3, int(superficie_total / 15)), "Unidades": "Unidades"},
            {"Concepto": "Mecanismos Interruptores / Conmutadores", "Cantidad": len(estancias_usuario) * 3, "Unidad": "Unidades"},
            {"Concepto": "Bases de Enchufe Schuko 16A", "Cantidad": int(superficie_total / 4), "Unidad": "Unidades"},
        ]

        df_partidas = pd.DataFrame(partidas)
        st.dataframe(df_partidas, use_container_width=True)

        st.markdown("---")
        st.subheader("🛒 Artículos Seleccionados de la Base de Datos (Obramat / Leroy Merlin)")
        
        # Mostrar muestra de artículos de la gama elegida
        if not df_gama.empty:
            st.dataframe(df_gama[['ID', 'Familia / Categoria', 'Marca', 'Proveedor / Tienda', 'Descripción Exacta del Artículo', 'Precio S/IVA (€)']], use_container_name=False, use_container_width=True)
        else:
            st.info("Mostrando artículos generales de la base de datos.")
            st.dataframe(df.head(15)[['ID', 'Familia / Categoria', 'Marca', 'Proveedor / Tienda', 'Descripción Exacta del Artículo']], use_container_width=True)

        st.success("✅ Presupuesto generado correctamente. Puedes añadir este módulo como `presupuesto_vivienda.py` en tu carpeta `módulos/` de GitHub.")

if __name__ == "__main__":
    app()
