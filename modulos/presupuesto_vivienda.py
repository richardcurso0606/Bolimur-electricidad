# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos: Inspector REBT, Buscadores Inteligentes, Tipo de Techo y Resumen por Punto
Autor: Richard Orlando Choque Tejerina (Bolimur Electricidad)
"""

import streamlit as st
import pandas as pd
import openpyxl
import os
import io
import datetime
from modulos import pdf_presupuesto
from modulos import tarifas_obra
@st.cache_data(show_spinner="Cargando base de datos de precios...")
def cargar_precios_excel():
    nombres_posibles = [
        "base_datos_precio_oficial.xlsx",
        "Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy_v2.xlsx",
        "Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy.xlsx"
    ]
    try:
        for f in os.listdir('.'):
            if f.endswith('.xlsx') and ('precio' in f.lower() or 'master' in f.lower() or 'oficial' in f.lower()):
                if f not in nombres_posibles:
                    nombres_posibles.insert(0, f)
    except Exception:
        pass

    for nombre in nombres_posibles:
        if os.path.exists(nombre):
            try:
                wb = openpyxl.load_workbook(nombre, read_only=True)
                hoja_activa = wb.sheetnames[0]
                for h in wb.sheetnames:
                    if "maestra" in h.lower() or "completa" in h.lower() or "tarifa" in h.lower():
                        hoja_activa = h
                        break
                wb.close()
                df = pd.read_excel(nombre, sheet_name=hoja_activa, engine='openpyxl')
                return df, nombre
            except Exception:
                continue
    return None, None

def exportar_excel_presupuesto(df_comercial, subtotal, iva_pct, cuota_iva, total, instalador_info, df_orden_compra=None, total_compra_neto=0.0, total_compra_con_iva=0.0, capitulos=None, partidas_manuales=None, materiales_pvp=None):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if capitulos:
            df_cap = pd.DataFrame([
                {
                    "Capítulo": c.get("cap", c.get("capitulo", "")),
                    "Denominación": c.get("titulo", ""),
                    "Alcance Técnico": c.get("desc", c.get("descripcion", "")),
                    "Importe PVP (€)": round(float(c.get("importe", 0.0)), 2)
                }
                for c in capitulos
            ])
            df_cap.to_excel(writer, sheet_name='Capítulos REBT Presupuesto', index=False)

        df_est_export = df_comercial if isinstance(df_comercial, pd.DataFrame) else pd.DataFrame(df_comercial)
        df_est_export.to_excel(writer, sheet_name='Desglose por Estancias', index=False)

        if partidas_manuales:
            df_pman = pd.DataFrame([
                {
                    "Concepto": p.get("concepto", ""),
                    "Descripción Técnica": p.get("descripcion", ""),
                    "Cantidad": p.get("cantidad", 1),
                    "Unidad": p.get("unidad", "ud"),
                    "PVP Unitario (€)": round(float(p.get("precio_unitario", 0.0)), 2),
                    "Subtotal PVP (€)": round(float(p.get("subtotal", 0.0)), 2)
                }
                for p in partidas_manuales
            ])
            df_pman.to_excel(writer, sheet_name='Partidas Adicionales', index=False)

        if materiales_pvp:
            df_mat_pvp = pd.DataFrame([
                {
                    "Categoría": m.get("categoria", ""),
                    "Elemento": m.get("articulo", ""),
                    "Descripción / Modelo": m.get("desc_exacta", m.get("descripcion", "")),
                    "Cantidad": m.get("cantidad", 1),
                    "Unidad": m.get("unidad", "ud"),
                    "PVP Unitario (€)": round(float(m.get("pvp_unitario", 0.0)), 2),
                    "Subtotal PVP (€)": round(float(m.get("subtotal_pvp", 0.0)), 2)
                }
                for m in materiales_pvp
            ])
            df_mat_pvp.to_excel(writer, sheet_name='Materiales Principales PVP', index=False)

        df_resumen = pd.DataFrame([
            {"Concepto": "Empresa Instaladora", "Importe / Valor": str(instalador_info.get("empresa", "BOLIMUR"))},
            {"Concepto": "Instalador Autorizado", "Importe / Valor": f"{instalador_info.get('instalador', '')} (Lic: {instalador_info.get('licencia', '')})"},
            {"Concepto": "Fecha Presupuesto", "Importe / Valor": str(instalador_info.get("fecha", datetime.date.today().strftime("%d/%m/%Y")))},
            {"Concepto": "Base Imponible Neta (Sin IVA)", "Importe / Valor": f"{round(subtotal, 2)} €"},
            {"Concepto": f"Cuota IVA ({iva_pct}%)", "Importe / Valor": f"{round(cuota_iva, 2)} €"},
            {"Concepto": "TOTAL PRESUPUESTO OFERTA (CON IVA)", "Importe / Valor": f"{round(total, 2)} €"}
        ])
        df_resumen.to_excel(writer, sheet_name='Resumen Económico', index=False)

        if df_orden_compra is not None and not df_orden_compra.empty:
            df_orden_compra.to_excel(writer, sheet_name='Orden de Compra y Acopio', index=False)
            df_res_compra = pd.DataFrame([
                {"Concepto": "Total Materiales Neto S/IVA", "Importe (€)": round(total_compra_neto, 2)},
                {"Concepto": "IVA Materiales (21%)", "Importe (€)": round(total_compra_neto * 0.21, 2)},
                {"Concepto": "TOTAL A PAGAR EN TIENDA / ALMACÉN", "Importe (€)": round(total_compra_con_iva, 2)}
            ])
            df_res_compra.to_excel(writer, sheet_name='Resumen Compra Materiales', index=False)
    return output.getvalue()

def exportar_excel_orden_compra(df_orden_compra, total_neto, cuota_iva, total_con_iva, proyecto_info, mat_estancias=None):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_orden_compra.to_excel(writer, sheet_name='Orden Compra Consolidada', index=False)
        
        if mat_estancias:
            filas_estancias = []
            for est in mat_estancias:
                r_nom = est['nombre']
                r_m2 = est['m2']
                r_dist = est['distancia_cuadro']
                
                # Mecanismos
                for m in est.get('mecanismos', []):
                    filas_estancias.append({
                        "Estancia": r_nom,
                        "Superficie (m²)": r_m2,
                        "Distancia Cuadro (m)": r_dist,
                        "Categoría": "Mecanismos",
                        "Material / Elemento": m['nombre'],
                        "Descripción Técnica": m.get('desc_real', ''),
                        "Cantidad": m['cant'],
                        "Unidad": "ud",
                        "P. Unit (€)": round(m['precio'], 2),
                        "Subtotal (€)": round(m['cant'] * m['precio'], 2)
                    })
                # Marcos
                if est.get('marcos', 0) > 0:
                    filas_estancias.append({
                        "Estancia": r_nom,
                        "Superficie (m²)": r_m2,
                        "Distancia Cuadro (m)": r_dist,
                        "Categoría": "Marcos",
                        "Material / Elemento": "Marcos Embellecedores",
                        "Descripción Técnica": "Marco 1 Elemento",
                        "Cantidad": est['marcos'],
                        "Unidad": "ud",
                        "P. Unit (€)": round(proyecto_info.get('p_marco', 0.40), 2),
                        "Subtotal (€)": round(est['marcos'] * proyecto_info.get('p_marco', 0.40), 2)
                    })
                # Tubos
                if est.get('tubo_m20', 0) > 0:
                    filas_estancias.append({
                        "Estancia": r_nom,
                        "Superficie (m²)": r_m2,
                        "Distancia Cuadro (m)": r_dist,
                        "Categoría": "Canalización",
                        "Material / Elemento": "Tubo Corrugado M20",
                        "Descripción Técnica": "Tubo M20 asignado a estancia",
                        "Cantidad": round(est['tubo_m20'], 1),
                        "Unidad": "m",
                        "P. Unit (€)": "",
                        "Subtotal (€)": ""
                    })
                if est.get('tubo_m25', 0) > 0:
                    filas_estancias.append({
                        "Estancia": r_nom,
                        "Superficie (m²)": r_m2,
                        "Distancia Cuadro (m)": r_dist,
                        "Categoría": "Canalización",
                        "Material / Elemento": "Tubo Corrugado M25",
                        "Descripción Técnica": "Tubo M25 asignado a estancia",
                        "Cantidad": round(est['tubo_m25'], 1),
                        "Unidad": "m",
                        "P. Unit (€)": "",
                        "Subtotal (€)": ""
                    })
                # Cables
                for c in est.get('cables', []):
                    if c.get('metros', 0) > 0:
                        filas_estancias.append({
                            "Estancia": r_nom,
                            "Superficie (m²)": r_m2,
                            "Distancia Cuadro (m)": r_dist,
                            "Categoría": "Conductores",
                            "Material / Elemento": c['item'],
                            "Descripción Técnica": "Conductor unipolar Cu",
                            "Cantidad": round(c['metros'], 1),
                            "Unidad": "m",
                            "P. Unit (€)": "",
                            "Subtotal (€)": ""
                        })
                # Cajas
                filas_estancias.append({
                    "Estancia": r_nom,
                    "Superficie (m²)": r_m2,
                    "Distancia Cuadro (m)": r_dist,
                    "Categoría": "Cajas",
                    "Material / Elemento": "Cajas Mecanismo 67mm",
                    "Descripción Técnica": "Caja universal empotrar",
                    "Cantidad": est.get('cajas_mecanismo', 0),
                    "Unidad": "ud",
                    "P. Unit (€)": "",
                    "Subtotal (€)": ""
                })
                if est.get('cajas_registro', 0) > 0:
                    filas_estancias.append({
                        "Estancia": r_nom,
                        "Superficie (m²)": r_m2,
                        "Distancia Cuadro (m)": r_dist,
                        "Categoría": "Cajas",
                        "Material / Elemento": "Cajas Registro 100x100mm",
                        "Descripción Técnica": "Caja cuadrada registro",
                        "Cantidad": est.get('cajas_registro', 0),
                        "Unidad": "ud",
                        "P. Unit (€)": "",
                        "Subtotal (€)": ""
                    })
            df_mat_est = pd.DataFrame(filas_estancias)
            df_mat_est.to_excel(writer, sheet_name='Materiales por Estancia', index=False)

        df_resumen = pd.DataFrame([
            {"Concepto": "Empresa / Instalador", "Valor": f"{proyecto_info.get('empresa', '')} - {proyecto_info.get('proyectista', '')}"},
            {"Concepto": "Fecha de Orden", "Valor": proyecto_info.get('fecha', '')},
            {"Concepto": "Potencia Prevista", "Valor": proyecto_info.get('potencia_kw', '')},
            {"Concepto": "Tecnología de Cable", "Valor": proyecto_info.get('tipo_cable', '')},
            {"Concepto": "Tecnología de Tubo", "Valor": proyecto_info.get('tipo_tubo', '')},
            {"Concepto": "Serie Mecanismos", "Valor": proyecto_info.get('serie_mecanismos', '')},
            {"Concepto": "Marca Protecciones", "Valor": proyecto_info.get('marca_protecciones', '')},
            {"Concepto": "Total Materiales S/IVA (€)", "Valor": round(total_neto, 2)},
            {"Concepto": "IVA Materiales 21% (€)", "Valor": round(cuota_iva, 2)},
            {"Concepto": "TOTAL A PAGAR EN TIENDA / ALMACÉN (€)", "Valor": round(total_con_iva, 2)}
        ])
        df_resumen.to_excel(writer, sheet_name='Resumen Compra', index=False)
    return output.getvalue()


def app():
    if "partidas_manuales" not in st.session_state:
        st.session_state["partidas_manuales"] = []

    es_oscuro_pres = st.session_state.get("tema_modo", "solar") == "oscuro"
    container_bg = "#0f172a" if es_oscuro_pres else "#ffffff"
    container_border = "#0284c7"
    tab_active_bg = "#0c4a6e" if es_oscuro_pres else "#f0f9ff"
    tab_active_color = "#38bdf8" if es_oscuro_pres else "#0284c7"

    # Colores dinámicos para tarjetas y ofertas comerciales (Sección 6)
    card_bg = "#0f172a" if es_oscuro_pres else "#f0f9ff"
    card_border = "#0284c7"
    card_title_color = "#38bdf8" if es_oscuro_pres else "#0369a1"
    card_text_color = "#f1f5f9" if es_oscuro_pres else "#1e293b"
    card_hr_color = "#1e293b" if es_oscuro_pres else "#bae6fd"
    card_subtotal_bg = "#1e293b" if es_oscuro_pres else "#f1f5f9"

    st.markdown(f"""
        <style>
            /* Pestaña / Panel de Sección con Marco Grueso (Línea Marcada) */
            div[data-testid="stTabPanel"],
            div[role="tabpanel"],
            div[data-testid="stTabContent"] {{
                border: 2.5px solid {container_border} !important;
                border-radius: 14px !important;
                padding: 24px 20px !important;
                margin-top: 14px !important;
                margin-bottom: 24px !important;
                background-color: {container_bg} !important;
                box-shadow: 0 4px 18px rgba(2, 132, 199, 0.12) !important;
            }}
            div[data-testid="stTabPanel"] div[data-testid="stTabPanel"],
            div[role="tabpanel"] div[role="tabpanel"] {{
                border: 2px solid #38bdf8 !important;
                background-color: {'#1e293b' if es_oscuro_pres else '#f8fafc'} !important;
                border-radius: 10px !important;
                padding: 16px !important;
                margin-top: 8px !important;
                margin-bottom: 12px !important;
                box-shadow: 0 2px 10px rgba(56, 189, 248, 0.08) !important;
            }}

            /* Contenedores con Borde y Sombra Nítidos y Marcados */
            div[data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stVerticalBlockBorderWrapper"] > div,
            div.ep3ma5o3,
            div[class*="ep3ma5o3"],
            div.e1wbhg7m1,
            div[class*="e1wbhg7m1"],
            div[data-testid="stVerticalBlock"] > div[style*="border"],
            div:has(> [data-testid="stVerticalBlock"]):has([style*="border"]) {{
                border-radius: 12px !important;
                border: 2.5px solid {container_border} !important;
                background-color: {container_bg} !important;
                box-shadow: 0 4px 16px rgba(2, 132, 199, 0.12) !important;
                margin-bottom: 16px !important;
                transition: all 0.2s ease !important;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"]:hover,
            div[class*="ep3ma5o3"]:hover,
            div[class*="e1wbhg7m1"]:hover {{
                border-color: #0369a1 !important;
                box-shadow: 0 6px 20px rgba(2, 132, 199, 0.2) !important;
            }}

            /* Si el contenedor está dentro de una pestaña que ya tiene marco exterior */
            div[data-testid="stTabPanel"] div[data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stTabPanel"] div.ep3ma5o3,
            div[data-testid="stTabPanel"] div[class*="ep3ma5o3"],
            div[role="tabpanel"] div[data-testid="stVerticalBlockBorderWrapper"],
            div[role="tabpanel"] div.ep3ma5o3,
            div[role="tabpanel"] div[class*="ep3ma5o3"] {{
                border: 2px solid #38bdf8 !important;
                box-shadow: 0 2px 10px rgba(2, 132, 199, 0.08) !important;
            }}

            /* Expanders con Borde Nítido y Sombra */
            div[data-testid="stExpander"] {{
                border-radius: 10px !important;
                border: 2.5px solid {container_border} !important;
                box-shadow: 0 2px 10px rgba(2, 132, 199, 0.08) !important;
                background: {container_bg} !important;
                margin-bottom: 12px !important;
            }}
            div[data-testid="stExpander"]:hover {{
                border-color: #0369a1 !important;
            }}

            /* =========================================================================
               MENÚ DE SECCIONES (BOTONES EN 2 FILAS / RETÍCULA TÁCTIL)
               ========================================================================= */
            div[data-baseweb="tab-list"] {{
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 10px 12px !important;
                background-color: {'#0b1329' if es_oscuro_pres else '#f1f5f9'} !important;
                padding: 12px !important;
                border-radius: 14px !important;
                border: 2px solid {'#1e293b' if es_oscuro_pres else '#cbd5e1'} !important;
                margin-bottom: 18px !important;
                overflow: visible !important;
                box-shadow: inset 0 2px 6px {'rgba(0,0,0,0.4)' if es_oscuro_pres else 'rgba(0,0,0,0.05)'} !important;
            }}
            div[data-baseweb="tab-border"] {{
                display: none !important;
            }}
            div[data-baseweb="tab-highlight"] {{
                display: none !important;
            }}
            button[data-baseweb="tab"] {{
                flex: 1 1 calc(33.333% - 12px) !important;
                min-width: 175px !important;
                height: auto !important;
                min-height: 50px !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                padding: 12px 18px !important;
                border-radius: 10px !important;
                border: 2px solid {'#334155' if es_oscuro_pres else '#cbd5e1'} !important;
                background-color: {'#1e293b' if es_oscuro_pres else '#ffffff'} !important;
                color: {'#f1f5f9' if es_oscuro_pres else '#1e293b'} !important;
                font-size: 15.5px !important;
                font-weight: 700 !important;
                letter-spacing: 0.3px !important;
                box-shadow: 0 2px 6px {'rgba(0,0,0,0.35)' if es_oscuro_pres else 'rgba(15,23,42,0.08)'} !important;
                transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
                white-space: normal !important;
                word-break: normal !important;
                cursor: pointer !important;
            }}
            button[data-baseweb="tab"] p,
            button[data-baseweb="tab"] span,
            button[data-baseweb="tab"] div {{
                color: {'#f1f5f9' if es_oscuro_pres else '#1e293b'} !important;
                font-size: 15.5px !important;
                font-weight: 700 !important;
                text-align: center !important;
                line-height: 1.3 !important;
            }}
            button[data-baseweb="tab"]:hover {{
                background-color: {'#0f172a' if es_oscuro_pres else '#e0f2fe'} !important;
                border-color: #0284c7 !important;
                color: #0284c7 !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 14px rgba(2, 132, 199, 0.25) !important;
            }}
            button[data-baseweb="tab"]:hover p,
            button[data-baseweb="tab"]:hover span,
            button[data-baseweb="tab"]:hover div {{
                color: #0284c7 !important;
            }}
            button[data-baseweb="tab"][aria-selected="true"] {{
                color: #ffffff !important;
                background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
                border: 2px solid #0284c7 !important;
                font-size: 15.5px !important;
                font-weight: 800 !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 14px rgba(2, 132, 199, 0.45) !important;
            }}
            button[data-baseweb="tab"][aria-selected="true"] p,
            button[data-baseweb="tab"][aria-selected="true"] span,
            button[data-baseweb="tab"][aria-selected="true"] div {{
                color: #ffffff !important;
                font-size: 15.5px !important;
                font-weight: 800 !important;
            }}
            /* Pestañas anidadas dentro de secciones */
            div[data-testid="stTabPanel"] div[data-baseweb="tab-list"],
            div[role="tabpanel"] div[data-baseweb="tab-list"] {{
                gap: 8px !important;
                padding: 8px !important;
                margin-bottom: 14px !important;
                border: 1.5px solid #38bdf8 !important;
            }}
            div[data-testid="stTabPanel"] button[data-baseweb="tab"],
            div[role="tabpanel"] button[data-baseweb="tab"] {{
                flex: 1 1 calc(25% - 8px) !important;
                min-width: 145px !important;
                min-height: 44px !important;
                font-size: 14.5px !important;
                padding: 8px 14px !important;
            }}
            div[data-testid="stTabPanel"] button[data-baseweb="tab"] p,
            div[data-testid="stTabPanel"] button[data-baseweb="tab"] span,
            div[data-testid="stTabPanel"] button[data-baseweb="tab"] div,
            div[role="tabpanel"] button[data-baseweb="tab"] p,
            div[role="tabpanel"] button[data-baseweb="tab"] span,
            div[role="tabpanel"] button[data-baseweb="tab"] div {{
                font-size: 14.5px !important;
            }}
            div[data-baseweb="tab-list"] ~ button,
            button[aria-label="Previous tab"],
            button[aria-label="Next tab"] {{
                display: none !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
            @media print {
                [data-testid="stSidebar"] {display: none !important;}
                [data-testid="stHeader"] {display: none !important;}
                .stButton {display: none !important;}
                .stTextInput {display: none !important;}
                .stSelectbox {display: none !important;}
                .stNumberInput {display: none !important;}
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
    st.markdown("Gestión de circuitos, desdoblamiento de C4, tipo de techo, cumplimiento ITC-BT-25 y acopio en firme.")

    # 1. Cargar base de datos maestra de precios con caché
    df_precios, excel_cargado = cargar_precios_excel()

    if df_precios is None:
        st.error("⚠️ No se pudo encontrar ni cargar el archivo Excel de precios en la raíz del proyecto.")
        return
    else:
        st.sidebar.success(f"📁 Base de datos conectada: `{excel_cargado}` ({len(df_precios)} artículos)")

    circs_imp = st.session_state.get("presupuesto_circuitos_importados", [])
    if circs_imp:
        with st.container(border=True):
            col_imp1, col_imp2 = st.columns([3, 1])
            with col_imp1:
                st.markdown(f"##### 📥 {len(circs_imp)} Circuitos Sincronizados desde la Memoria Técnica (MTD):")
                resumen_circs = ", ".join([f"**{c.get('nombre', 'Circuito')}** ({c.get('pia', 16)}A)" for c in circs_imp[:5]])
                if len(circs_imp) > 5:
                    resumen_circs += f" ... y {len(circs_imp)-5} más."
                st.write(resumen_circs)
            with col_imp2:
                if st.button("🗑️ Descartar importación", key="btn_clear_imp_mtd"):
                    del st.session_state["presupuesto_circuitos_importados"]
                    st.rerun()

    # ==========================================
    # ASISTENTE WEB DE ACTUALIZACIÓN DE PRECIOS
    # ==========================================
    with st.sidebar.expander("🌐 Asistente Web y Gestor de Proveedores"):
        st.markdown("""
        **¿Deseas buscar precios actualizados o añadir nuevos materiales?**
        
        • **Instrucción directa al Asistente IA:**
        Indícame en el chat: *"Revisa en la web de Obramat / Sumidelec / Sonepar el precio de [artículo] y actualízalo"*. Consultaré la web oficial y lo guardaré con su SKU real.
        
        • **Añadir o Actualizar manualmente:**
        """)
        with st.form("form_sidebar_direct_add"):
            nom_art_sb = st.text_input("Nombre / Descripción del Artículo:", placeholder="Ej: Interruptor Simon 10 blanco", key="sb_nom_art")
            col_sb1, col_sb2 = st.columns(2)
            with col_sb1:
                tienda_sb = st.selectbox("Tienda / Proveedor:", ["Obramat", "Leroy Merlin", "Sumidelec", "Sonepar", "Rexel", "Mayorista / Especializado", "General"], key="sb_tienda")
                cat_sb = st.selectbox("Categoría:", ["Mecanismos", "Conductores", "Protecciones", "Canalización Tubos", "Cuadros y Envolventes", "Cajas de Registro", "Marcos / Placas", "Consumibles"], key="sb_cat")
            with col_sb2:
                precio_sb = st.number_input("Precio S/IVA (€):", min_value=0.01, value=1.50, step=0.10, format="%.2f", key="sb_precio")
                marca_sb = st.text_input("Marca / Fabricante:", value="General", key="sb_marca")
            sku_sb = st.text_input("Código SKU / Ref. Fabricante:", placeholder="Ej: SIM-10511 / EFA-21011", key="sb_sku")
            
            btn_guardar_sb = st.form_submit_button("💾 Guardar Artículo en la Base de Datos Excel", type="primary")
            if btn_guardar_sb:
                if nom_art_sb:
                    try:
                        df_act = pd.read_excel('base_datos_precio_oficial.xlsx')
                        nuevo_registro = {
                            'ID': f"ART-{len(df_act)+1:04d}",
                            'Nivel de Gama / Aplicación': 'Estándar',
                            'Familia / Categoria': cat_sb,
                            'Marca': marca_sb,
                            'Serie / Gama': 'Estándar',
                            'Proveedor / Tienda': tienda_sb,
                            'Código SKU / Ref': sku_sb if sku_sb else f"REF-{len(df_act)+1:04d}",
                            'Descripción Exacta del Artículo': nom_art_sb,
                            'Unidad': 'm' if cat_sb in ['Conductores', 'Canalización Tubos'] else 'Ud',
                            'Precio S/IVA (€)': float(precio_sb),
                            'IVA (%)': 21.0,
                            'Precio C/IVA (€)': round(float(precio_sb) * 1.21, 2),
                            'Observaciones / Aplicación Técnica': f"Añadido desde gestor de proveedores ({tienda_sb})"
                        }
                        df_act = pd.concat([df_act, pd.DataFrame([nuevo_registro])], ignore_index=True)
                        df_act.to_excel('base_datos_precio_oficial.xlsx', index=False)
                        cargar_precios_excel.clear()
                        st.success(f"✅ ¡Artículo '{nom_art_sb}' ({precio_sb:.2f} €) guardado en Excel correctamente!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al guardar en Excel: {ex}")
                else:
                    st.warning("Ingresa el nombre del artículo.")

    # ==========================================
    # FUNCIONES DE BÚSQUEDA INTELIGENTE Y ROBUSTA
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
        
        # Fallback inteligente: si no se encontró con sub_kw (ej: color específico), buscar por la familia principal
        if sub_kw_lower:
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                if main_kw_lower in desc:
                    try:
                        precio = float(row['Precio S/IVA (€)'])
                        prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                        art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                        fila = idx + 2
                        mejores_candidatos.append((precio, prov, f"{art_desc} (Equivalente {sub_kw})", fila))
                    except:
                        continue
            if mejores_candidatos:
                mejores_candidatos.sort(key=lambda x: x[0])
                p, prov, desc, fila = mejores_candidatos[0]
                return p, prov, desc, True, fila
            
        nombre_no_enc = f"{main_kw} {sub_kw or ''}".strip()
        return 0.45, "Por catalogar", f"⚠️ [NO ENCONTRADO EN BD]: {nombre_no_enc} (Tarifa estimada 0.45€)", False, -1

    def buscar_tubo_por_tipo(df, diametro, tipo_tubo):
        diam_lower = diametro.lower()
        es_lh = 'libre de halógenos' in tipo_tubo.lower() or 'lh' in tipo_tubo.lower() or 'ignífugo' in tipo_tubo.lower()
        mejores = []

        for idx, row in df.iterrows():
            desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
            cat = str(row.get('Familia / Categoria', '')).strip().lower()
            if 'canalización' in cat or 'tubo' in desc:
                if 'corrugado' in desc and diam_lower in desc:
                    desc_is_lh = 'libre' in desc or 'halógeno' in desc or 'lh' in desc
                    if es_lh and desc_is_lh:
                        try:
                            p = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            mejores.append((p, prov, art_desc, idx + 2))
                        except:
                            pass
                    elif not es_lh and not desc_is_lh:
                        try:
                            p = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            mejores.append((p, prov, art_desc, idx + 2))
                        except:
                            pass

        if mejores:
            mejores.sort(key=lambda x: x[0])
            return mejores[0][0], mejores[0][1], mejores[0][2], True, mejores[0][3]

        return (0.45 if es_lh else 0.25), "Obramat", f"Tubo Corrugado {diametro} ({'LH' if es_lh else 'PVC'})", False, -1

    def buscar_cable_por_tipo(df, seccion, color, tipo_cable):
        sec_lower = seccion.lower()
        col_lower = color.lower()
        es_lh = 'libre de halógenos' in tipo_cable.lower() or 'h07z1' in tipo_cable.lower()
        mejores = []

        for idx, row in df.iterrows():
            desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
            cat = str(row.get('Familia / Categoria', '')).strip().lower()
            if 'conductor' in cat or 'cable' in desc:
                if sec_lower in desc and col_lower in desc:
                    desc_is_lh = 'h07z1' in desc or 'libre' in desc or 'halógeno' in desc
                    if es_lh and desc_is_lh:
                        try:
                            p = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            mejores.append((p, prov, art_desc, idx + 2))
                        except:
                            pass
                    elif not es_lh and not desc_is_lh:
                        try:
                            p = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            mejores.append((p, prov, art_desc, idx + 2))
                        except:
                            pass

        if mejores:
            mejores.sort(key=lambda x: x[0])
            return mejores[0][0], mejores[0][1], mejores[0][2], True, mejores[0][3]

        # Fallback si falta algún color específico
        for idx, row in df.iterrows():
            desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
            cat = str(row.get('Familia / Categoria', '')).strip().lower()
            if 'conductor' in cat or 'cable' in desc:
                if sec_lower in desc:
                    desc_is_lh = 'h07z1' in desc or 'libre' in desc or 'halógeno' in desc
                    if (es_lh and desc_is_lh) or (not es_lh and not desc_is_lh):
                        try:
                            p = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            mejores.append((p, prov, f"{art_desc} ({color.capitalize()})", idx + 2))
                        except:
                            pass

        if mejores:
            mejores.sort(key=lambda x: x[0])
            return mejores[0][0], mejores[0][1], mejores[0][2], True, mejores[0][3]

        return (0.42 if '2.5' in seccion else 0.24), "Obramat", f"Cable {seccion} {color} ({tipo_cable})", False, -1

    def buscar_mecanismo_por_filtro(df, tipo, modo_sel, valor_sel):
        kw_map = {
            'interruptor': ['interruptor', 'conmutador'],
            'schuko': ['schuko', 'enchufe'],
            'rj45': ['rj45', 'datos'],
            'tv': ['toma de televisión', 'toma tv', 'tv/r', 'tv-fm', 'coaxial'],
            'marco': ['marco 1 elemento', 'marco']
        }
        keywords = kw_map.get(tipo, ['interruptor'])
        mejores_candidatos = []
        valor_lower = valor_sel.lower()

        # Determinar palabras clave de búsqueda inteligente
        tokens_busqueda = []
        if "racional" in valor_lower or "más económica" in valor_lower or "ahorro" in valor_lower:
            tokens_busqueda = ["efapel", "apolo", "mec 21", "simon 10"]
        elif "efapel" in valor_lower or "mec 21" in valor_lower or "apolo" in valor_lower:
            tokens_busqueda = ["efapel", "apolo", "mec 21"]
        elif "simon 10" in valor_lower:
            tokens_busqueda = ["simon 10"]
        elif "simon 27" in valor_lower:
            tokens_busqueda = ["simon 27"]
        elif "simon 82" in valor_lower:
            tokens_busqueda = ["simon 82"]
        elif "schneider" in valor_lower or "asfora" in valor_lower:
            tokens_busqueda = ["schneider", "asfora", "miluz", "new unica"]
        elif "niessen" in valor_lower or "zenit" in valor_lower:
            tokens_busqueda = ["niessen", "zenit"]
        else:
            tokens_busqueda = [valor_lower]

        for kw in keywords:
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                serie_item = str(row.get('Serie / Gama', '')).strip().lower()
                marca_item = str(row.get('Marca', '')).strip().lower()
                gama_item = str(row.get('Nivel de Gama / Aplicación', '')).strip().lower()

                # Evitar seleccionar solo teclas o tapas sueltas cuando se busca el mecanismo o conjunto funcional
                if tipo in ['interruptor', 'schuko', 'rj45']:
                    if 'tecla' in desc or 'tapa toma' in desc or 'frontal' in desc or 'placa ciega' in desc:
                        continue

                if tipo == 'marco' and 'marco' not in desc:
                    continue

                if kw in desc:
                    match = False
                    if modo_sel == "Por Clasificación de Gamas":
                        if any(tok in serie_item or tok in desc or tok in gama_item or tok in marca_item for tok in tokens_busqueda):
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
                    if tipo in ['interruptor', 'schuko', 'rj45']:
                        if 'tecla' in desc or 'tapa toma' in desc or 'frontal' in desc or 'placa ciega' in desc:
                            continue
                    if tipo == 'marco' and 'marco' not in desc:
                        continue
                    if kw in desc:
                        try:
                            precio = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            fila = idx + 2
                            mejores_candidatos.append((precio, prov, f"{art_desc} (Gama equivalente)", fila))
                        except:
                            continue

        if mejores_candidatos:
            mejores_candidatos.sort(key=lambda x: x[0])
            return mejores_candidatos[0][0], mejores_candidatos[0][1], mejores_candidatos[0][2], True, mejores_candidatos[0][3]

        return 3.50, "Por catalogar", f"⚠️ [NO ENCONTRADO EN BD]: Mecanismo {tipo} ({valor_sel}) - Tarifa estimada 3.50€", False, -1

    def buscar_proteccion_por_marca(df, tipo_prot, marca_sel, amperaje=25):
        marca_lower = marca_sel.lower()
        mejores_candidatos = []

        if tipo_prot == 'iga':
            for idx, row in df.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                marca_item = str(row.get('Marca', '')).strip().lower()
                if marca_lower in marca_item and ('2p' in desc or 'bipolar' in desc) and f'{amperaje}a' in desc and 'magnetotérmico' in desc:
                    try:
                        precio = float(row['Precio S/IVA (€)'])
                        prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                        art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                        fila = idx + 2
                        mejores_candidatos.append((precio, prov, art_desc, fila))
                    except:
                        continue
            if not mejores_candidatos:
                for idx, row in df.iterrows():
                    desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                    marca_item = str(row.get('Marca', '')).strip().lower()
                    if marca_lower in marca_item and ('2p' in desc or 'bipolar' in desc) and 'magnetotérmico' in desc:
                        try:
                            precio = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            fila = idx + 2
                            mejores_candidatos.append((precio, prov, art_desc, fila))
                        except:
                            continue
        elif tipo_prot == 'diferencial':
            keywords = ['interruptor diferencial', 'diferencial']
            for kw in keywords:
                for idx, row in df.iterrows():
                    desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                    marca_item = str(row.get('Marca', '')).strip().lower()
                    if kw in desc and marca_lower in marca_item:
                        try:
                            precio = float(row['Precio S/IVA (€)'])
                            prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                            art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                            fila = idx + 2
                            mejores_candidatos.append((precio, prov, art_desc, fila))
                        except:
                            continue
        else:
            keywords = ['magnetotérmico', 'interrup.', 'automático']
            for kw in keywords:
                for idx, row in df.iterrows():
                    desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
                    marca_item = str(row.get('Marca', '')).strip().lower()
                    if kw in desc and marca_lower in marca_item:
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

        return 15.00, "Por catalogar", f"⚠️ [NO ENCONTRADO EN BD]: Protección {tipo_prot} ({marca_sel}) - Tarifa estimada 15.00€", False, -1

    def buscar_caja_cuadro(df, marca_sel, grado_electr='Básica'):
        mod_str = '24' if grado_electr == 'Elevada' else '12'
        marca_lower = marca_sel.lower()
        mejores_candidatos = []

        for idx, row in df.iterrows():
            desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
            cat = str(row.get('Familia / Categoria', '')).strip().lower()
            marca_item = str(row.get('Marca', '')).strip().lower()

            # Filtro estricto: debe ser cuadro/envolvente y NO accesorios como peines ni cajas de mecanismos/registro
            if ('cuadro' in cat or 'envolvente' in cat or 'caja automatismo' in desc or 'caja de distribución' in desc) and \
               ('caja' in desc or 'cuadro' in desc) and \
               ('peine' not in desc and 'repartidor' not in desc and 'accesorio' not in cat and \
                '67mm' not in desc and 'enlazable' not in desc and 'registro' not in desc and 'estanca' not in desc):
                if mod_str in desc:
                    try:
                        precio = float(row['Precio S/IVA (€)'])
                        prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                        art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                        fila = idx + 2
                        if marca_lower in marca_item:
                            mejores_candidatos.append((precio, prov, art_desc, fila, 0))
                        else:
                            mejores_candidatos.append((precio, prov, art_desc, fila, 1))
                    except:
                        continue

        if mejores_candidatos:
            mejores_candidatos.sort(key=lambda x: (x[4], x[0]))
            p, prov, d, f, _ = mejores_candidatos[0]
            return p, prov, d, True, f

        # Fallback genérico a cualquier cuadro de distribución empotrar
        for idx, row in df.iterrows():
            desc = str(row.get('Descripción Exacta del Artículo', '')).strip().lower()
            cat = str(row.get('Familia / Categoria', '')).strip().lower()
            if ('cuadro' in cat or 'envolvente' in cat or 'caja automatismo' in desc or 'caja de distribución' in desc) and \
               ('caja' in desc or 'cuadro' in desc) and \
               ('peine' not in desc and 'repartidor' not in desc and 'accesorio' not in cat and \
                '67mm' not in desc and 'enlazable' not in desc and 'registro' not in desc and 'estanca' not in desc):
                try:
                    precio = float(row['Precio S/IVA (€)'])
                    prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                    art_desc = str(row.get('Descripción Exacta del Artículo', ''))
                    fila = idx + 2
                    return p, prov, d, True, f
                except:
                    continue

        return 16.80, "Obramat", f"Caja Automatismos Empotrar {mod_str} Módulos DIN", False, -1


    # ==========================================
    # DATOS DE LA EMPRESA / INSTALADOR AUTENTICADO
    # ==========================================
    try:
        from modulos import auth_manager, selector_cliente_proyecto
        usuario_ses = auth_manager.obtener_usuario_actual()
    except Exception:
        usuario_ses = {}

    st.sidebar.header("🏢 Datos del Instalador")
    empresa_nombre = st.sidebar.text_input("Nombre Empresa", value=usuario_ses.get("nombre_empresa", "BOLIMUR INSTALACIONES Y REFORMAS") if usuario_ses else "BOLIMUR INSTALACIONES Y REFORMAS")
    instalador_nombre = st.sidebar.text_input("Instalador", value=usuario_ses.get("nombre_instalador", "Richard Orlando Choque Tejerina") if usuario_ses else "Richard Orlando Choque Tejerina")
    n_licencia = st.sidebar.text_input("Nº Licencia / REBT", value=usuario_ses.get("num_licencia_rebt", "REBT-30/15892") if usuario_ses else "REBT-30/15892")
    localidad = st.sidebar.text_input("Localidad", value=usuario_ses.get("localidad", "Rincón de Seca, Murcia") if usuario_ses else "Rincón de Seca, Murcia")
    telefono = st.sidebar.text_input("Teléfono Contacto", value=usuario_ses.get("telefono", "+34 600 000 000") if usuario_ses else "+34 600 000 000")

    # Barra Superior de Asignación y Guardado de Proyecto en Cliente
    try:
        from modulos import selector_cliente_proyecto
        datos_para_guardar = {
            "estancias_pro": st.session_state.get("estancias_pro", []),
            "partidas_manuales": st.session_state.get("partidas_manuales", [])
        }
        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">👤 Cliente y Expediente del Proyecto</h4></div>', unsafe_allow_html=True)
        selector_cliente_proyecto.renderizar_barra_cliente_proyecto("Presupuesto Vivienda", datos_para_guardar, "Presupuesto Integral Vivienda REBT")
    except Exception:
        pass

    # ==========================================
    # Definir clase auxiliar de contexto nulo para cuando se seleccione Vista Continua
    class _NullContext:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    # Selector de Modo de Navegación Rápida
    col_nav_info, col_nav_mode = st.columns([2.8, 1.2])
    with col_nav_info:
        st.caption("🚀 **Navegación Rápida:** Pasa de una sección a otra con 1 solo clic sin hacer scroll vertical.")
    with col_nav_mode:
        modo_vista_secciones = st.radio(
            "Modo de Navegación:",
            ["📑 Pestañas Rápidas (Sin scroll)", "📜 Vista Continua (Todo en 1)"],
            horizontal=True,
            label_visibility="collapsed",
            key="modo_vista_secciones_presupuesto"
        )

    if modo_vista_secciones.startswith("📑"):
        tab_sec1, tab_sec2, tab_sec3, tab_sec4, tab_sec_teleco, tab_sec5, tab_sec6 = st.tabs([
            "⚡ 1. Potencia & IGA",
            "🔲 2. Mecanismos & Series",
            "⏱️ 3. Mano de Obra & Techos",
            "🏠 4. Estancias & Puntos",
            "📡 5. Telecomunicaciones (ICT-2 RTR)",
            "🛡️ 6. Inspector IA REBT & ICT",
            "🖨️ 7. Documentos & Presupuesto"
        ])
    else:
        tab_sec1 = _NullContext()
        tab_sec2 = _NullContext()
        tab_sec3 = _NullContext()
        tab_sec4 = _NullContext()
        tab_sec_teleco = _NullContext()
        tab_sec5 = _NullContext()
        tab_sec6 = _NullContext()

    # ==========================================
    # SECCIÓN 1: PARÁMETROS DE POTENCIA REBT E IGA OFICIAL
    # ==========================================
    with tab_sec1:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">⚡ SECCIÓN 1: Parámetros de Potencia, Escalones IGA y Configuración de Circuitos</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_pot1, col_pot2, col_pot3 = st.columns(3)
            with col_pot1:
                potencia_prevista_kw = st.selectbox(
                    "Potencia Prevista / Escalón REBT",
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
                    "⚡ Tecnología de Cable",
                    [
                        "Libre de Halógenos (H07Z1-K)",
                        "PVC Normal / Estándar (H07V-K)"
                    ],
                    help="H07Z1-K: Cable ignífugo sin halógenos (alta seguridad / nueva normativa). H07V-K: Cable tradicional de PVC."
                )
            with col_pot3:
                tipo_tubo_sel = st.selectbox(
                    "📏 Tecnología de Tubo",
                    [
                        "Tubo Corrugado Normal / Estándar (PVC)",
                        "Tubo Corrugado Libre de Halógenos (LH / Ignífugo)"
                    ],
                    help="Tubo PVC estándar: Solución económica para reformas ordinarias. Tubo LH: Tubo ignífugo libre de halógenos."
                )

            st.markdown("<div style='margin-top: 14px; margin-bottom: 6px; font-weight: 600; color: #0369a1;'>⚙️ Circuitos Especiales y Desdoblamientos REBT (ITC-BT-25):</div>", unsafe_allow_html=True)
        
            c_esp1, c_esp2 = st.columns(2)
            with c_esp1:
                desdoblar_c4 = st.checkbox(
                    "⚙️ Desdoblar circuito C4 (Lavadora/Lavavajillas separado de Termo ACS)", 
                    value=False,
                    help="Crea dos líneas dedicadas en cocina: C4-A (Lavado) y C4-B (Termo ACS), añadiendo un PIA extra de 16A."
                )
                instalar_c9 = st.checkbox(
                    "❄️ Climatización / Aire Acondicionado (C9)",
                    value=True if ("Elevada" in potencia_prevista_kw or "9.200" in potencia_prevista_kw) else False,
                    help="Añade línea C9 con Diferencial Tipo A Superinmunizado (SI) y cable 6 mm² (o 2.5 mm²)."
                )
                if instalar_c9:
                    c9_sub1, c9_sub2 = st.columns(2)
                    with c9_sub1:
                        tipo_c9 = st.selectbox(
                            "Tipo de Climatización:",
                            ["Conductos Inverter Centralizado (25A / 6 mm²)", "Split Individual (16A / 2.5 mm²)", "Multi-Split 2 Zonas (C9.1 y C9.2 - 2x16A)"],
                            key="sel_tipo_c9"
                        )
                    with c9_sub2:
                        pot_c9 = st.number_input("Potencia Clima (W):", min_value=1500, max_value=15000, value=5000, step=500, key="num_pot_c9")
                    st.caption("🛡️ **REBT:** Se prescribe **Interruptor Diferencial Tipo A Superinmunizado (30mA)** para absorber armónicos y corrientes residuales de alta frecuencia del variador Inverter.")
                else:
                    tipo_c9 = "Conductos Inverter Centralizado (25A / 6 mm²)"
                    pot_c9 = 5000

            with c_esp2:
                instalar_c8 = st.checkbox(
                    "🔥 Calefacción Eléctrica (C8) con Desdoblamiento Automático",
                    value=False,
                    help="Radiadores o suelo radiante eléctrico. Si supera 5.750 W, el REBT exige desdoblar por ley en C8.1 y C8.2."
                )
                desdoblar_c8 = False
                pot_c8 = 0
                if instalar_c8:
                    c8_sub1, c8_sub2 = st.columns([1.2, 1.8])
                    with c8_sub1:
                        pot_c8 = st.number_input("Potencia total calefacción (W):", min_value=1000, max_value=25000, value=6500, step=500, key="num_pot_c8")
                    with c8_sub2:
                        desdoblar_c8 = (pot_c8 > 5750)
                        if desdoblar_c8:
                            p_c8_1 = int(round(pot_c8 / 2))
                            p_c8_2 = pot_c8 - p_c8_1
                            st.success(f"⚡ **Desdoblamiento REBT Activado (>5.750W):** Dividido en **C8.1 ({p_c8_1} W)** y **C8.2 ({p_c8_2} W)** con PIAs de 25A y tubos M25 independientes.")
                        else:
                            st.info(f"✅ Circuito C8 único ({pot_c8} W ≤ 5.750 W, PIA 25A / 6 mm² Cu).")
            
                tipo_domotica = st.selectbox(
                    "🧠 Domótica y Automatización (C11):",
                    [
                        "Sin Domótica",
                        "Domótica Inalámbrica (WiFi / Zigbee / Shelly - Micromódulos)",
                        "Domótica Cableada por Bus (KNX / Centralizada)"
                    ],
                    key="sel_tipo_dom",
                    help="Adapta el presupuesto para cajas profundas de 60 mm y cable de neutro (Inalámbrica) o canalización independiente y cuadro ampliado (KNX)."
                )
                if tipo_domotica == "Domótica Inalámbrica (WiFi / Zigbee / Shelly - Micromódulos)":
                    st.info("💡 **Afección en Obra (Inalámbrica):** Se computan **cajas de mecanismo profundas de 60 mm** para albergar micromódulos y **líneas de Neutro azul adicionales** llevadas a todos los interruptores.")
                elif tipo_domotica == "Domótica Cableada por Bus (KNX / Centralizada)":
                    st.info("💡 **Afección en Obra (Bus KNX):** Se computa **tubo corrugado M20 independiente para bus de datos** (separado de 230V), **cuadro general ampliado (36/54 módulos DIN)** y fuente de alimentación homologada 30V DC.")

            # Comprobación de Electrificación Básica vs Elevada
            tiene_circuitos_elevada = instalar_c9 or instalar_c8 or (tipo_domotica != "Sin Domótica")

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

            if tiene_circuitos_elevada:
                grado_electr = "Elevada"
                if iga_amperaje < 40:
                    iga_amperaje = 40
                if "5.750" in potencia_prevista_kw or "7.360" in potencia_prevista_kw:
                    st.warning("⚠️ **Requisito Reglamentario (ITC-BT-25 apdo. 2.2):** Al incorporar aire acondicionado (C9), calefacción (C8) o domótica (C11), la vivienda pasa por ley a **Electrificación Elevada (mínimo 9.200 W / IGA 40 A / DI 16 mm²)**.")

            # Conteo exacto de circuitos
            num_circuitos_base = 5 # C1, C2, C3, C4, C5
            if desdoblar_c4: 
                num_circuitos_base += 1 # C4-A y C4-B
            if instalar_c8:
                num_circuitos_base += (2 if desdoblar_c8 else 1)
            if instalar_c9:
                num_circuitos_base += (2 if "Multi-Split" in tipo_c9 else 1)
            if grado_electr == "Elevada":
                num_circuitos_base += 1 # C10 Secadora
            if tipo_domotica != "Sin Domótica":
                num_circuitos_base += 1 # C11 Domótica

            # Regla ITC-BT-25: máximo 5 circuitos por interruptor diferencial
            import math
            n_difs = max(2 if grado_electr == "Elevada" else 1, math.ceil(num_circuitos_base / 5.0))

            st.info(f"📋 **Configuración REBT:** Electrificación **{grado_electr}** | **IGA Oficial: {iga_amperaje} A** | Total de circuitos: **{num_circuitos_base}** | Interruptores Diferenciales requeridos (máx 5 circ/ID): **{n_difs}**")

    # ==========================================
    # SECCIÓN 2: MARCAS, SERIES Y MEMORIA ECONÓMICA
    # ==========================================
    with tab_sec2:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🔲 SECCIÓN 2: Selección de Marcas, Series de Mecanismos y Protecciones</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            with st.expander("💡 Ver Memoria Técnica y Comparativa Económica por Sección (Racionalidad y Ahorro)", expanded=False):
                st.markdown("""
                Esta memoria analiza en tiempo real la base de datos oficial para recomendarte los materiales homologados con **mejor relación calidad/precio** por cada familia:
                """)
                col_mem1, col_mem2 = st.columns(2)
                with col_mem1:
                    st.markdown("""
                    **🔲 1. Mecanismos (Enchufes e Interruptores):**
                    * 🥇 **Más Económica:** `Efapel MEC 21 + Apolo 5000` (~1,18 € / 1,35 €) *(Ahorro ~35%)*
                    * 🥈 **Económica Clásica:** `Simon 10` (~1,30 € / 1,60 €)
                    * 🥉 **Gama Media / Diseño:** `Schneider Asfora` (~2,40 € / 2,80 €)
                    * 💎 **Gama Alta:** `Simon 82 Detail / Niessen Zenit` (~5,50 € - 8,20 €)
                
                    **⚡ 2. Cables y Conductores:**
                    * 🥇 **Más Económica:** `PVC Estándar (H07V-K)` (1.5mm² a 0,19 €/m | 2.5mm² a 0,33 €/m)
                    * 🛡️ **Máxima Seguridad / Ignífugo:** `Libre de Halógenos (H07Z1-K)` (1.5mm² a 0,24 €/m | 2.5mm² a 0,42 €/m)
                    """)
                with col_mem2:
                    st.markdown("""
                    **🛡️ 3. Cuadro Eléctrico y Protecciones:**
                    * 🥇 **Más Económica:** `Chint / Solera` (Cuadro 12M a 10,80 € | PIAs a ~2,90 €)
                    * 🥈 **Gama Media Residencial:** `Schneider Resi9` (Cuadro 12M a 16,80 € | PIAs a ~4,50 €)
                    * 🥉 **Gama Profesional:** `Legrand Practibox S` (Cuadro 12M a 19,42 € | PIAs a ~5,80 €)
                
                    **📏 4. Tubos y Canalizaciones:**
                    * 🥇 **Más Económica:** `Tubo Corrugado PVC 320N` (M20 a 0,28 €/m | M25 a 0,38 €/m)
                    * 🛡️ **Ignífugo Homologado:** `Tubo Libre de Halógenos 750N` (M20 a 0,52 €/m | M25 a 0,65 €/m)
                
                    **🔌 5. Sistema de Conexión:**
                    * 🥇 **Más Económica:** `Clemas de tornillo tradicionales` (~0,45 €)
                    * ⚡ **Alta Rapidez / Confort:** `Conectores Rápidos Wago 221` (~0,95 €)
                    """)

            col_meca1, col_meca2 = st.columns(2)
            with col_meca1:
                st.markdown("**1️⃣ Mecanismos (Enchufes e Interruptores)**")
                modo_seleccion = st.radio("Filtrar mecanismos por:", ["Por Clasificación de Gamas", "Por Marca Directa"], horizontal=True, key="modo_meca")
                if modo_seleccion == "Por Clasificación de Gamas":
                    serie_mecanismos = st.selectbox(
                        "Selecciona la Gama / Serie:",
                        [
                            "💡 Selección Racional Más Económica (Efapel MEC 21 / Apolo 5000 - Máximo Ahorro)",
                            "Efapel MEC 21 / Apolo 5000 (Gama Económica / Base)",
                            "Simon 10 (Gama Económica / Básica)",
                            "Schneider Asfora (Gama Media)",
                            "Simon 27 Play (Gama Estándar / Residencial)",
                            "Simon 82 Detail (Gama Alta / Decorativa)",
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
                ["Fichas de Empalme / Clemas Tradicionales de Tornillo", "Conectores Rápidos Wago 221 (Profesional / Alta Calidad)"],
                horizontal=True
            )

            st.markdown("---")
            st.markdown("**🔢 Criterio de Medición y Cómputo de Puntos (Tomas y Luces Dobles):**")
            criterio_puntos_dobles = st.radio(
                "Selecciona cómo computar las tomas de enchufe dobles y puntos de luz dobles para cobro y rentabilidad:",
                [
                    "Toma Doble = 2 PUNTOS | Luz Doble = 2 PUNTOS (Cobro por mecanismo/servicio individual)",
                    "Toma Doble = 1 PUNTO | Luz Doble = 1 PUNTO (Cobro unificado por caja o emplazamiento físico)"
                ],
                index=0,
                key="criterio_puntos_dobles_sel",
                help="Define si las tomas dobles de enchufe y los puntos de luz de doble encendido se computan como 2 puntos individuales para la tarificación por punto y el análisis de rentabilidad, o como 1 único punto físico agrupado."
            )
            es_doble_2_puntos = "2 PUNTOS" in criterio_puntos_dobles

    # ==========================================
    # SECCIÓN 3: MANO DE OBRA, TECHOS Y CONDICIONES ECONÓMICAS
    # ==========================================
    with tab_sec3:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">⏱️ SECCIÓN 3: Mano de Obra, Rozas, Techos, Boletín CIE y Márgenes</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_prof1, col_prof2 = st.columns([2, 1])
            with col_prof1:
                idx_prof = 1 if st.session_state.get('perfil_tarifa_autonomo') else 0
                sel_perfil = st.radio(
                    "💼 Modalidad de Facturación de Mano de Obra:",
                    ["🏢 Modelo Empresa (Margen Comercial Completo +50%)", "🧑‍🔧 Modelo Autónomo / Tutor (Sin Margen en Mano de Obra)"],
                    index=idx_prof,
                    horizontal=True,
                    key="radio_perfil_tarifa_sec3"
                )
                es_modo_autonomo_sec3 = "Autónomo" in sel_perfil
                st.session_state['perfil_tarifa_autonomo'] = es_modo_autonomo_sec3
            with col_prof2:
                if es_modo_autonomo_sec3:
                    st.success("🧑‍🔧 **Modo Tutor:** Cobras el 100% de tus horas trabajadas directas sin sobrecoste de margen comercial MO.")
                else:
                    st.info("🏢 **Modo Empresa:** Aplica margen comercial industrial tanto a materiales como a mano de obra.")

            col_m1, col_m2, col_m3 = st.columns([1, 1, 1.8])
            with col_m1:
                val_margen_def = 0 if es_modo_autonomo_sec3 else 50
                margen_comercial = st.number_input(
                    "Margen Comercial General (%)", 
                    min_value=0, max_value=200, value=val_margen_def, step=5,
                    key=f"margen_comercial_input_{'auto' if es_modo_autonomo_sec3 else 'emp'}",
                    help="Margen comercial sobre costes de materiales y mano de obra."
                )
            with col_m2:
                porc_garantia = st.number_input(
                    "Colchón de Garantía en Materiales (%)", 
                    min_value=0, max_value=100, value=10, step=1,
                    help="Colchón adicional para imprevistos y reposición de materiales."
                )
            with col_m3:
                opciones_iva_hacienda = [
                    "10% - IVA Reducido (Reforma Vivienda Particular > 2 años | Art. 91 LIVA)",
                    "21% - IVA General (Locales, Oficinas o Material aportado > 40%)",
                    "0% - Exento / Inversión de Sujeto Pasivo (Art. 84 LIVA | B2B Empresas)"
                ]
                iva_label_sel = st.selectbox(
                    "IVA Aplicado al Cliente (Conforme Hacienda / AEAT):", 
                    opciones_iva_hacienda, 
                    index=0,
                    key="sel_iva_cliente_hacienda"
                )
                if "10%" in iva_label_sel:
                    iva_sel = 10
                elif "21%" in iva_label_sel:
                    iva_sel = 21
                else:
                    iva_sel = 0

            # Explicación de requisitos legales de Hacienda
            if iva_sel == 10:
                st.caption("⚖️ **Requisitos Hacienda (Art. 91.Uno.2.10º Ley IVA):** 1) Vivienda particular terminada hace más de 2 años. 2) Destinatario persona física o comunidad. 3) Los materiales aportados por el electricista NO deben superar el 40% del total de la obra.")
            elif iva_sel == 21:
                st.caption("⚖️ **Régimen General AEAT:** Aplicable a locales comerciales, despachos, naves o reformas donde el material aportado supera el 40% del presupuesto.")
            else:
                st.caption("⚖️ **Inversión de Sujeto Pasivo (Art. 84.Uno.2º.f Ley IVA):** Facturación directa entre empresas / autónomos subcontratistas en ejecución de obra sin repercusión de IVA.")

            col_roz1, col_roz2 = st.columns(2)
            with col_roz1:
                hace_rozas_electricista = st.checkbox("¿Asumes tú (electricista) el picado de rozas y tapado con yeso?", value=True)
            with col_roz2:
                tipo_pared = st.selectbox(
                    "Tipo de Pared / Soporte",
                    [
                        "Pladur / Panel de Yeso Laminado (Obra seca - Sin rozas, corte con sierra de vaso)",
                        "Ladrillo Hueco / Tabiquería seca (Fácil picado)", 
                        "Ladrillo Perforado / Termoarcilla (Dureza media)", 
                        "Hormigón / Estructura (Requiere rozadora y martillo pesado)"
                    ],
                    index=0
                )

            tipo_techo = st.selectbox(
                "🏗️ Tipo de Techo / Forjado",
                [
                    "Falso Techo de Pladur / Escayola (Cableado superior ágil - Menor rozado vertical de luz)",
                    "Techo Macizo / Hormigón o Viguetas (Exige rozado completo en paredes y techos para alumbrado)"
                ]
            )

            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1:
                precio_hora = st.number_input("Precio Mano de Obra (€/h neto)", min_value=10.0, max_value=60.0, value=25.0, step=1.0)
            with col_c2:
                num_operarios = st.number_input("Nº Operarios", min_value=1, max_value=5, value=1, step=1)
            with col_c3:
                horas_jornada = st.number_input("Horas por Jornada / Día", min_value=4.0, max_value=12.0, value=8.0, step=0.5)
            with col_c4:
                precio_boletin_cie = st.number_input("Tarifa Ensayos + MTD + Boletín CIE (€)", min_value=0.0, max_value=800.0, value=150.0, step=10.0, help="Tarifa profesional por verificaciones previas ITC-BT-05 (aislamiento con megóhmetro, disparo diferencial, continuidad y bucle de tierra), elaboración de Memoria Técnica de Diseño (MTD) y tramitación del Certificado CIE ante la DGEAIM Murcia.")

            st.markdown("---")
            st.markdown("##### 🔌 Modalidad de Presupuesto: Escandallo Analítico vs Tarifa de Calle por Punto (25 - 30 €/pto)")
            col_mod_tar1, col_mod_tar2 = st.columns([1.6, 1.2])
            with col_mod_tar1:
                modo_tarifa_sel = st.radio(
                    "Modelo de valoración económica para distribución interior:",
                    [
                        "📊 Escandallo Analítico (Coste Materiales + Horas MO + Margen %)",
                        "🔌 Tarifa de Calle por Punto (25 - 30 €/pto según mercado/tutor)"
                    ],
                    index=0,
                    key="modo_tarifa_calle_vivienda",
                    help="Permite elegir si los capítulos de distribución interior y mecanismos se valoran por escandallo detallado o por la tarifa de mercado habitual por punto (25 - 30 €/pto) que aplican instaladores y tutores en calle."
                )
            with col_mod_tar2:
                es_modo_tarifa_puntos = "Tarifa de Calle por Punto" in modo_tarifa_sel
                tarifa_punto_calle = st.number_input(
                    "Tarifa por Punto S/IVA (€/pto):",
                    min_value=15.0,
                    max_value=60.0,
                    value=28.0,
                    step=1.0,
                    disabled=not es_modo_tarifa_puntos,
                    help="Precio de referencia por punto instalado (tubo, cable, caja y mecanismo). En la calle se suele cobrar de 25 € a 30 €."
                )
                if es_modo_tarifa_puntos:
                    st.caption("💡 *Referencia de calle:* 25 € para tabiquería fácil/pladur, 28-30 € estándar ladrillo con roza, >30 € hormigón o gamas altas.")

        st.markdown("---")
    # ==========================================
    # SECCIÓN 4: GESTIÓN DINÁMICA DE ESTANCIAS Y MÉTRICA DE m²
    # ==========================================
    if 'estancias_pro' not in st.session_state:
        st.session_state.estancias_pro = [
            {"nombre": "Salón - Comedor", "m2": 25.0, "altura": 2.6, "distancia_cuadro": 12.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0, "tomas_dobles": 2, "luces_dobles": 1},
            {"nombre": "Cocina", "m2": 12.0, "altura": 2.6, "distancia_cuadro": 8.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0, "tomas_dobles": 2, "luces_dobles": 0},
            {"nombre": "Dormitorio Principal", "m2": 16.0, "altura": 2.6, "distancia_cuadro": 14.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0, "tomas_dobles": 1, "luces_dobles": 1},
            {"nombre": "Dormitorio 2", "m2": 11.0, "altura": 2.6, "distancia_cuadro": 10.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0, "tomas_dobles": 1, "luces_dobles": 1},
            {"nombre": "Baño 1", "m2": 6.0, "altura": 2.6, "distancia_cuadro": 6.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0, "tomas_dobles": 1, "luces_dobles": 1},
            {"nombre": "Pasillo", "m2": 7.0, "altura": 2.6, "distancia_cuadro": 3.0, "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0, "tomas_dobles": 0, "luces_dobles": 0},
        ]

    with tab_sec4:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🏠 SECCIÓN 4: Gestión de Estancias, Superficies (m²) y Distancias al Cuadro</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            estancias_activas_temp = [e for e in st.session_state.estancias_pro]
            sup_total_actual = sum([e["m2"] for e in estancias_activas_temp])
        
            col_met1, col_met2, col_met3 = st.columns(3)
            with col_met1:
                st.metric(label="📐 Superficie Útil Total", value=f"{sup_total_actual:.1f} m²")
            with col_met2:
                st.metric(label="⚖️ Límite ITC-BT-25 Básica", value="160.0 m²")
            with col_met3:
                estado_sup = "🟢 Correcto (Básica)" if sup_total_actual <= 160.0 else "🔴 Supera 160 m² (Exige Elevada)"
                st.metric(label="🔍 Estado Normativo m²", value=estado_sup)

            st.caption("Configura la distancia lineal desde el Cuadro General hasta la caja de registro de cada estancia para el cálculo exacto de tubos y cableado.")

            with st.expander("➕ Añadir Nueva Estancia a la Vivienda", expanded=False):
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
                
                    if st.form_submit_button("Agregar Estancia", type="primary"):
                        if nuevo_nombre:
                            st.session_state.estancias_pro.append({
                                "nombre": nuevo_nombre, "m2": nuevo_m2, "altura": nuevo_alt, "distancia_cuadro": nueva_dist,
                                "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0,
                                "tomas_dobles": 1, "luces_dobles": 0
                            })
                            st.success(f"Estancia '{nuevo_nombre}' añadida correctamente.")
                            st.rerun()
                        else:
                            st.warning("Introduce un nombre válido para la estancia.")

            estancias_activas = []

            # Encabezados de las columnas de estancias
            col_hdr = st.columns([3, 1.5, 1.5, 2, 0.8, 0.8])
            with col_hdr[0]:
                st.markdown("**🏠 Estancia**")
            with col_hdr[1]:
                st.markdown("**📐 Superficie (m²)**")
            with col_hdr[2]:
                st.markdown("**📏 Altura (m)**")
            with col_hdr[3]:
                st.markdown("**⚡ Dist. Cuadro (m)**")
            with col_hdr[4]:
                st.markdown("**Incluir**")
            with col_hdr[5]:
                st.markdown("**Borrar**")

            for i, est in enumerate(st.session_state.estancias_pro):
                nombre_est = est["nombre"].lower()
                es_banio = "baño" in nombre_est or "aseo" in nombre_est
                es_cocina = "cocina" in nombre_est
            
                circuitos_asociados = "C1 (Luz) + C2 (Enchufes generales 16A)"
                if es_banio:
                    circuitos_asociados = "C1 (Luz) + C5 (Tomas húmedas baño)"
                elif es_cocina:
                    c4_txt = " + C4-A & C4-B (Desdoblados)" if desdoblar_c4 else " + C4 (Lavadora/Termo)"
                    circuitos_asociados = f"C1 (Luz) + C3 (Horno/Vitro) {c4_txt} + C5 (Encimera)"

                with st.container(border=True):
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

                    with st.expander(f"⚙️ Puntos Extra y Tomas/Luces Dobles en: {est['nombre']}"):
                        # Cálculo de dotación mínima reglamentaria ITC-BT-25 y desglose de circuitos REBT
                        if es_cocina:
                            base_min_luz = 1
                            # Desglose reglamentario estricto en cocina:
                            # C5 (Tomas encimera sobre banco de trabajo): mínimo 3 bases 16A
                            # C2 (Tomas de uso general en cocina frigorífico/mesa/microondas): mínimo 2 bases 16A
                            # C3 (Vitrocerámica y Horno): 1 toma fuerza 25A
                            # C4 (Electrodomésticos pesados lavadora/lavavajillas/termo): 3 bases (desdoblado) o 2 bases
                            base_c5_encimera = 3
                            base_c2_general = 2
                            base_c3_fuerza = 1
                            base_c4_electrod = 3 if desdoblar_c4 else 2
                            base_min_sch = base_c5_encimera + base_c2_general + base_c3_fuerza + base_c4_electrod
                            base_min_rj = 1  # ITC-2 recomienda o exige toma de datos/TV en cocina
                            tipo_rebt_desc = f"Cocina Completa: C1(Luz: {base_min_luz}) + C5(Encimera: {base_c5_encimera}) + C2(General: {base_c2_general}) + C3(Horno/Vitro 25A: {base_c3_fuerza}) + C4(Lav/Lavav/Termo: {base_c4_electrod})"
                        elif es_banio:
                            base_min_luz = 1
                            base_min_sch = 2  # C5 tomas húmedas/espejo junto a lavabo
                            base_min_rj = 0
                            tipo_rebt_desc = "Baño / Aseo: C1 (Luz espejo/techo: 1) + C5 (Enchufes estancos IP44 junto a lavabo: 2)"
                        elif "salón" in nombre_est or "comedor" in nombre_est:
                            base_min_luz = 2 if est["m2"] >= 10 else 1
                            base_min_sch = 6 if est["m2"] >= 10 else 3  # Circuito C2
                            base_min_rj = 2  # ICT-2 exige 2 tomas dobles RJ45 + RTV coaxial
                            tipo_rebt_desc = f"Salón / Comedor: C1(Luz: {base_min_luz}) + C2(Tomas generales: {base_min_sch}) + ICT-2(TV/RJ45: {base_min_rj})"
                        elif "dormitorio" in nombre_est or "habitación" in nombre_est:
                            base_min_luz = 2 if est["m2"] >= 10 else 1
                            base_min_sch = 3  # Circuito C2 (cabecero + auxiliar)
                            base_min_rj = 1  # ICT-2 exige toma RJ45 + RTV por dormitorio
                            tipo_rebt_desc = f"Dormitorio: C1(Luz conmutada: {base_min_luz}) + C2(Tomas generales: {base_min_sch}) + ICT-2(TV/RJ45: {base_min_rj})"
                        elif "pasillo" in nombre_est or "distribuidor" in nombre_est or "hall" in nombre_est or "recibidor" in nombre_est:
                            base_min_luz = 2 if est["m2"] >= 5 else 1
                            base_min_sch = 2 if est["m2"] >= 5 else 1  # Circuito C2
                            base_min_rj = 1 if ("hall" in nombre_est or "recibidor" in nombre_est) else 0
                            tipo_rebt_desc = f"Pasillo / Entrada: C1(Luz cruzamiento: {base_min_luz}) + C2(Toma servicio: {base_min_sch})"
                        else:
                            base_min_luz = 1
                            base_min_sch = 2
                            base_min_rj = 0
                            tipo_rebt_desc = "Estancia auxiliar / Terraza: C1 (Luz: 1) + C2 (Tomas 16A: 2)"

                        tot_sch = base_min_sch + est.get("extra_schuko", 0)
                        tot_luz = base_min_luz + est.get("extra_luz", 0)
                        tot_rj = base_min_rj + est.get("extra_rj45", 0)
                        tot_tv = base_min_rj + est.get("extra_tv", 0)

                        st.info(f"⚡ **Desglose Reglamentario REBT & Telecomunicaciones (ICT-2):** `{tipo_rebt_desc}` | 📏 **Distancia Cuadro:** `{est['distancia_cuadro']} m`")

                        # Panel comparativo: Mínimo REBT e ICT-2 vs Total Resultante
                        c_dot1, c_dot2, c_dot3, c_dot4 = st.columns(4)
                        with c_dot1:
                            estado_sch = "🟢 Cumple REBT" if tot_sch >= base_min_sch else "🟡 < Mínimo (Reforma)"
                            st.caption(f"**Enchufes Schuko (C2/C5):** Base: **{base_min_sch}** → **{tot_sch} ud** ({estado_sch})")
                        with c_dot2:
                            estado_luz = "🟢 Cumple REBT" if tot_luz >= base_min_luz else "🟡 < Mínimo (Reforma)"
                            st.caption(f"**Puntos de Luz (C1):** Base: **{base_min_luz}** → **{tot_luz} ud** ({estado_luz})")
                        with c_dot3:
                            estado_rj = "🟢 Cumple ICT-2" if tot_rj >= base_min_rj else "🟡 < Mínimo ICT"
                            st.caption(f"**Tomas Red RJ45 (Cat.6):** Base: **{base_min_rj}** → **{tot_rj} ud** ({estado_rj})")
                        with c_dot4:
                            estado_tv = "🟢 Cumple ICT-2" if tot_tv >= base_min_rj else "🟡 < Mínimo ICT"
                            st.caption(f"**Tomas TV Coaxial (RTV):** Base: **{base_min_rj}** → **{tot_tv} ud** ({estado_tv})")

                        if es_cocina:
                            with st.container(border=True):
                                st.markdown("🍳 **Detalle Específico de Circuitos en Cocina (ITC-BT-25):**")
                                c_coc1, c_coc2, c_coc3, c_coc4 = st.columns(4)
                                with c_coc1:
                                    st.metric("C5 (Encimera 16A)", f"{base_c5_encimera} tomas", help="Tomas sobre banco de trabajo para pequeños electrodomésticos (batidora, tostador, cafetera).")
                                with c_coc2:
                                    st.metric("C2 (General Cocina)", f"{base_c2_general + est.get('extra_schuko', 0)} tomas", help="Tomas para frigorífico, microondas y uso libre en cocina.")
                                with c_coc3:
                                    st.metric("C3 (Horno/Vitro 25A)", f"{base_c3_fuerza} toma", help="Base de 25A 2P+T con cables de 6 mm² protegida con PIA de 25A.")
                                with c_coc4:
                                    st.metric("C4 (Electrodomésticos)", f"{base_c4_electrod} tomas", help="Tomas específicas para lavadora, lavavajillas y termo eléctrico.")

                        if tot_sch < base_min_sch or tot_luz < base_min_luz:
                            st.warning("⚠️ **Atención:** Has configurado menos tomas/luces que la dotación mínima reglamentaria (ITC-BT-25). Esto es perfectamente admisible en **reformas parciales** donde se conservan tomas existentes, pero si se tramita un **CIE / Boletín para nueva alta integral**, Industria (DGEAIM) exigirá el mínimo.", icon="⚠️")

                        st.markdown("**➕ Puntos Extra / Variación sobre dotaciones base REBT & ICT-2:**")
                        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
                        with col_p1:
                            est["extra_schuko"] = st.number_input(f"Schukos Extra (Base: {base_min_sch})", min_value=-base_min_sch, max_value=15, value=est.get("extra_schuko", 0), key=f"ex_sch_{i}")
                        with col_p2:
                            est["extra_luz"] = st.number_input(f"Puntos Luz Extra (Base: {base_min_luz})", min_value=-base_min_luz, max_value=10, value=est.get("extra_luz", 0), key=f"ex_luz_{i}")
                        with col_p3:
                            est["extra_rj45"] = st.number_input(f"Tomas Red RJ45 Extra (Base: {base_min_rj})", min_value=-base_min_rj, max_value=5, value=est.get("extra_rj45", 0), key=f"ex_rj_{i}")
                        with col_p4:
                            est["extra_tv"] = st.number_input(f"Tomas TV Coaxial Extra (Base: {base_min_rj})", min_value=-base_min_rj, max_value=5, value=est.get("extra_tv", 0), key=f"ex_tv_{i}")

                        st.markdown("**🔌 Configuración de Tomas y Luces Dobles en esta Estancia:**")
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            def_td_val = est.get("tomas_dobles", 2 if ("salón" in nombre_est or "cocina" in nombre_est) else (1 if ("baño" in nombre_est or "dormitorio" in nombre_est) else 0))
                            est["tomas_dobles"] = st.number_input(
                                f"De los enchufes, ¿cuántas son Tomas Dobles?",
                                min_value=0, max_value=20, value=int(def_td_val), step=1,
                                key=f"td_{i}",
                                help="Cantidad de tomas dobles (2 bases schuko bajo un mismo marco o caja). Se computarán a 2 puntos o 1 punto para rentabilidad según el criterio seleccionado en Sección 2."
                            )
                        with col_d2:
                            def_ld_val = est.get("luces_dobles", 1 if ("salón" in nombre_est or "dormitorio" in nombre_est or "baño" in nombre_est) else 0)
                            est["luces_dobles"] = st.number_input(
                                f"De las luces, ¿cuántas son Luces Dobles (2 encendidos)?",
                                min_value=0, max_value=10, value=int(def_ld_val), step=1,
                                key=f"ld_{i}",
                                help="Cantidad de puntos de luz de doble encendido / conmutador doble. Se computarán a 2 puntos o 1 punto para rentabilidad según el criterio seleccionado en Sección 2."
                            )

                if incluir:
                    estancias_activas.append(est)


    # ==========================================
    # SECCIÓN 5: TELECOMUNICACIONES (ICT-2 RD 346/2011 & CUADRO RTR)
    # ==========================================
    with tab_sec_teleco:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">📡 SECCIÓN 5: Infraestructura de Telecomunicaciones (ICT-2 RD 346/2011)</h4></div>', unsafe_allow_html=True)
        st.info("""
        📘 **Marco Normativo Oficial de Telecomunicaciones en Edificación:**  
        Conforme al **Real Decreto 346/2011 (Reglamento de ICT-2)** y la **Orden Ministerial ITC/1644/2011**, toda vivienda debe disponer de un **Registro de Terminación de Red (RTR)** situado junto a la entrada o CGMP para albergar los puntos de acceso al usuario (PAU) de Fibra Óptica (FTTH), Coaxial de TV (RTV) y Red de Par Trenzado (UTP Cat.6).
        """)

        with st.container(border=True):
            st.markdown("#### 🗄️ Configuración del Armario/Envolvente RTR (Registro de Terminación de Red)")
            col_rtr1, col_rtr2 = st.columns([2, 2])
            with col_rtr1:
                tipo_rtr_sel = st.selectbox(
                    "Tipo de Envolvente / Armario RTR:",
                    [
                        "Caja Empotrada RTR Normalizada ICT-2 (500x600x80 mm)",
                        "Caja Empotrada RTR Ampliada (500x800x80 mm)",
                        "Armario Rack Mural 10 Pulgadas 6U (Gama Superior Domótica/Red)"
                    ],
                    index=0,
                    key="sel_tipo_rtr",
                    help="El RD 346/2011 Anexo II fija las dimensiones mínimas reglamentarias según el número de estancias."
                )
            with col_rtr2:
                schuko_rtr_opcion = st.radio(
                    "⚡ Dotación de Bases Schuko 16A en el RTR (Alimentadas por C2):",
                    [
                        "2 Bases Schuko 16A (Mínimo Reglamentario ICT-2 RD 346/2011)",
                        "3 Bases Schuko 16A (Recomendado: Router + ONT Fibra + Switch/Domótica)"
                    ],
                    index=1,
                    key="rad_schuko_rtr",
                    help="El reglamento exige un mínimo de 2 tomas de corriente alimentadas del circuito C2. Como buena práctica profesional, se instalan 3 bases para conectar el router del operador, la roseta/ONT de fibra y un switch o centralita domótica sin regletas externas."
                )
            
            n_schuko_rtr = 3 if "3 Bases" in schuko_rtr_opcion else 2

            st.markdown("#### 🔌 Dotación de Elementos y PAU en el interior del RTR:")
            col_pau1, col_pau2, col_pau3 = st.columns(3)
            with col_pau1:
                incluir_pau_fibra = st.checkbox("PAU Fibra Óptica (FTTH) 2x SC/APC", value=True, key="chk_pau_fibra", help="Roseta óptica con adaptadores SC/APC según norma ICT-2.")
            with col_pau2:
                incluir_pau_coaxial = st.checkbox("PAU Coaxial RTV (Repartidor F Televes)", value=True, key="chk_pau_coax", help="Distribuidor TV terrestre y satélite con conectores F EasyF.")
            with col_pau3:
                incluir_panel_rj45 = st.checkbox("Multiplexor Pasivo Datos UTP Cat.6", value=True, key="chk_pau_utp", help="Panel de parcheo o regleta para distribución en estrella de red Ethernet.")

            st.markdown("#### 📊 Resumen Técnico de la Red de Telecomunicaciones de la Vivienda:")
            tot_tomas_rj_est = sum(e.get("cant_rj", 2 if ("salón" in e["nombre"].lower() or "dormitorio" in e["nombre"].lower()) else 1) for e in estancias_activas)
            m_coaxial_est = len(estancias_activas) * 15.0
            m_utp_est = len(estancias_activas) * 18.0

            c_met1, c_met2, c_met3, c_met4 = st.columns(4)
            with c_met1:
                st.metric("Enchufes Schuko en RTR", f"{n_schuko_rtr} ud (C2)")
            with c_met2:
                st.metric("Tomas de Datos/TV Finales", f"{tot_tomas_rj_est} tomas")
            with c_met3:
                st.metric("Cable Coaxial RG6 Cu/Cu", f"{m_coaxial_est:.0f} m")
            with c_met4:
                st.metric("Cable UTP Cat.6 LSZH", f"{m_utp_est:.0f} m")

            st.caption("✅ Cumplimiento pleno de la Instrucción Técnica ICT-2 RD 346/2011 Anexos I, II y III (Servicios de RTV, Banda Ancha y Telefonía).")

    # ==========================================
    # SECCIÓN 6: FISCALIZADOR TÉCNICO REBT & ICT (INSPECTOR IA)
    # ==========================================
    with tab_sec5:
        st.markdown('<div class="section-header-amber"><h4 style="margin:0; color:#92400e;">🛡️ SECCIÓN 6: Inspector Técnico Integral (Fiscalización REBT & ICT-2 RD 346/2011)</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            sup_total_calculada = sum([e["m2"] for e in estancias_activas])
            tiene_cocina = any("cocina" in e["nombre"].lower() for e in estancias_activas)
            tiene_banio = any("baño" in e["nombre"].lower() or "aseo" in e["nombre"].lower() for e in estancias_activas)

            alertas_inspector = []
        
            if sup_total_calculada > 160.0 and grado_electr == "Básica":
                alertas_inspector.append(f"🔴 **Incumplimiento ITC-BT-25:** La superficie útil total de la vivienda ({sup_total_calculada:.1f} m²) supera los 160 m² estipulados para electrificación básica. El reglamento obliga a utilizar **Electrificación Elevada**.")

            if not tiene_cocina:
                alertas_inspector.append("🔴 **Incumplimiento ITC-BT-25:** No se ha detectado ninguna estancia catalogada como 'Cocina'. El reglamento exige obligatoriamente los circuitos de fuerza y cocina.")

            if not tiene_banio:
                alertas_inspector.append("🟠 **Aviso REBT:** No se ha detectado ningún cuarto de baño o aseo. Se recomienda incluir al menos un circuito C5 para zonas húmedas.")

            # 2. Comprobaciones Telecomunicaciones ICT-2 (RD 346/2011 & Orden ITC/1644/2011)
            alertas_inspector_ict = []
            recomendaciones_inspector = []
            n_schuko_rtr_sel = 3 if "3 Bases" in st.session_state.get("rad_schuko_rtr", "3 Bases") else 2
            if n_schuko_rtr_sel < 2:
                alertas_inspector_ict.append("🔴 **Incumplimiento ICT-2 (Anexo II):** El cuadro RTR debe contar con un mínimo de 2 bases Schuko 16A alimentadas por C2.")
            elif n_schuko_rtr_sel == 2:
                recomendaciones_inspector.append("💡 **Recomendación Profesional ICT-2:** El RTR dispone de 2 bases (mínimo legal). Se aconseja instalar 3 bases para evitar regletas externas al conectar Router + ONT Fibra + Switch/Domótica.")

            tiene_salon = any("salón" in e["nombre"].lower() or "salon" in e["nombre"].lower() or "comedor" in e["nombre"].lower() for e in estancias_activas)
            if not tiene_salon:
                recomendaciones_inspector.append("🟠 **Aviso ICT-2:** No se detectó estancia principal (Salón/Comedor) para verificar las tomas dobles de datos y TV.")

            tot_rj_proyectadas = sum(e.get("cant_rj", 2 if ("salón" in e["nombre"].lower() or "dormitorio" in e["nombre"].lower()) else 1) for e in estancias_activas)

            # Panel de Doble Dictamen Oficial en 2 Columnas
            col_insp1, col_insp2 = st.columns(2)
            with col_insp1:
                st.markdown("##### ⚡ Dictamen Eléctrico REBT (RD 842/2002):")
                if alertas_inspector:
                    for err in alertas_inspector:
                        st.error(err)
                else:
                    st.success("🟢 **REBT Conforme:** Cumple dotaciones ITC-BT-25, circuitos C1-C5 y protecciones IGA.")

            with col_insp2:
                st.markdown("##### 📡 Dictamen Telecomunicaciones ICT-2 (RD 346/2011):")
                if alertas_inspector_ict:
                    for err_ict in alertas_inspector_ict:
                        st.error(err_ict)
                else:
                    st.success(f"🟢 **ICT-2 Conforme:** Cuadro RTR normalizado con {n_schuko_rtr_sel} tomas Schuko C2, PAU FTTH, TV EasyF y red Cat.6 ({tot_rj_proyectadas} tomas).")

            if recomendaciones_inspector:
                with st.expander("💡 Observaciones y Recomendaciones de Calidad Técnica", expanded=False):
                    for rec in recomendaciones_inspector:
                        st.info(rec)

            alertas_totales = alertas_inspector + alertas_inspector_ict
            if alertas_totales:
                forzar_inspector = st.checkbox("⚠️ Forzar ejecución del presupuesto bajo responsabilidad del instalador autorizado", value=False)
                if not forzar_inspector:
                    st.stop()
            else:
                msg_ok = '<div style="background-color: #ecfdf5; border: 1.5px solid #10b981; border-radius: 8px; padding: 12px; margin-top: 10px;"><b style="color: #065f46; font-size: 15px;">🏆 VISTO BUENO TÉCNICO OFICIAL SUPERADO:</b><br/><span style="color: #047857; font-size: 13px;">La instalación proyectada cumple simultáneamente con el <b>Reglamento Electrotécnico para Baja Tensión (REBT ITC-BT-25)</b> y el <b>Reglamento de Infraestructuras Comunes de Telecomunicaciones (ICT-2 RD 346/2011)</b> para su tramitación directa ante la DGEAIM de Murcia y el Ministerio de Telecomunicaciones.</span></div>'
                st.markdown(msg_ok, unsafe_allow_html=True)

        st.markdown("---")

        if 'presupuesto_calculado' not in st.session_state:
            st.session_state.presupuesto_calculado = True

        col_btn_c1, col_btn_c2 = st.columns([2.5, 1.5])
        with col_btn_c1:
            if st.button("🚀 Recalcular Presupuesto, Distancias y Generar Paneles", type="primary", key="btn_recalcular_principal"):
                st.session_state.presupuesto_calculado = True
                st.rerun()
        with col_btn_c2:
            st.caption("⚡ Cálculos y vistas sincronizados en tiempo real.")

    if 'msg_exito_actualizacion' in st.session_state:
        st.success(st.session_state.pop('msg_exito_actualizacion'))

    if st.session_state.get('presupuesto_calculado', True):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia.")
            return

        p_tubo20, prov_tubo20, desc_tubo20, ok_tubo20, fila_tubo20 = buscar_tubo_por_tipo(df_precios, 'm20', tipo_tubo_sel)
        p_tubo25, prov_tubo25, desc_tubo25, ok_tubo25, fila_tubo25 = buscar_tubo_por_tipo(df_precios, 'm25', tipo_tubo_sel)

        p_caja_mec, prov_caja_mec, desc_caja_mec, ok_caja_mec, fila_caja_mec = buscar_mas_economico(df_precios, '67mm', 'mecanismos')
        p_caja_reg, prov_caja_reg, desc_caja_reg, ok_caja_reg, fila_caja_reg = buscar_mas_economico(df_precios, '100x100', 'registro')
        
        p_15_az, prov_15_az, desc_15_az, ok_15_az, fila_15_az = buscar_cable_por_tipo(df_precios, '1.5 mm²', 'azul', tipo_cable_sel)
        p_15_ne, prov_15_ne, desc_15_ne, ok_15_ne, fila_15_ne = buscar_cable_por_tipo(df_precios, '1.5 mm²', 'negro', tipo_cable_sel)
        p_15_ma, prov_15_ma, desc_15_ma, ok_15_ma, fila_15_ma = buscar_cable_por_tipo(df_precios, '1.5 mm²', 'marrón', tipo_cable_sel)
        p_15_gr, prov_15_gr, desc_15_gr, ok_15_gr, fila_15_gr = buscar_cable_por_tipo(df_precios, '1.5 mm²', 'gris', tipo_cable_sel)
        p_15_tt, prov_15_tt, desc_15_tt, ok_15_tt, fila_15_tt = buscar_cable_por_tipo(df_precios, '1.5 mm²', 'amarillo', tipo_cable_sel)

        p_25_az, prov_25_az, desc_25_az, ok_25_az, fila_25_az = buscar_cable_por_tipo(df_precios, '2.5 mm²', 'azul', tipo_cable_sel)
        p_25_ne, prov_25_ne, desc_25_ne, ok_25_ne, fila_25_ne = buscar_cable_por_tipo(df_precios, '2.5 mm²', 'negro', tipo_cable_sel)
        p_25_ma, prov_25_ma, desc_25_ma, ok_25_ma, fila_25_ma = buscar_cable_por_tipo(df_precios, '2.5 mm²', 'marrón', tipo_cable_sel)
        p_25_tt, prov_25_tt, desc_25_tt, ok_25_tt, fila_25_tt = buscar_cable_por_tipo(df_precios, '2.5 mm²', 'amarillo', tipo_cable_sel)

        p_utp, prov_utp, desc_utp, ok_utp, fila_utp = buscar_mas_economico(df_precios, 'utp', 'cat.6')
        if not ok_utp:
            p_utp, prov_utp, desc_utp, ok_utp, fila_utp = buscar_mas_economico(df_precios, 'cable de red', 'cat.6')

        if "Wago" in tipo_conexion:
            p_con, prov_con, desc_con, ok_con, fila_con = buscar_mas_economico(df_precios, 'wago 221', '3 conductores')
            nombre_conexion_txt = "Conectores Rápidos Wago 221 (Caja 50ud)"
        else:
            p_con, prov_con, desc_con, ok_con, fila_con = buscar_mas_economico(df_precios, 'clema', '10mm')
            nombre_conexion_txt = "Regleta / Clema de Conexión 12 Polos"

        p_int, prov_int, desc_int, ok_int, fila_int = buscar_mecanismo_por_filtro(df_precios, 'interruptor', modo_seleccion, serie_mecanismos)
        p_schuko, prov_schuko, desc_schuko, ok_schuko, fila_schuko = buscar_mecanismo_por_filtro(df_precios, 'schuko', modo_seleccion, serie_mecanismos)
        p_rj45, prov_rj45, desc_rj45, ok_rj45, fila_rj45 = buscar_mecanismo_por_filtro(df_precios, 'rj45', modo_seleccion, serie_mecanismos)
        p_tv, prov_tv, desc_tv, ok_tv, fila_tv = buscar_mecanismo_por_filtro(df_precios, 'tv', modo_seleccion, serie_mecanismos)
        p_marco, prov_marco, desc_marco, ok_marco, fila_marco = buscar_mecanismo_por_filtro(df_precios, 'marco', modo_seleccion, serie_mecanismos)

        p_iga, prov_iga, desc_iga, ok_iga, fila_iga = buscar_proteccion_por_marca(df_precios, 'iga', marca_protecciones, amperaje=iga_amperaje)
        p_id, prov_id, desc_id, ok_id, fila_id = buscar_proteccion_por_marca(df_precios, 'diferencial', marca_protecciones)
        p_pia, prov_pia, desc_pia, ok_pia, fila_pia = buscar_proteccion_por_marca(df_precios, 'pia', marca_protecciones)
        
        p_caja_cuadro, prov_caja_cuadro, desc_caja_cuadro, ok_caja_cuadro, fila_caja_cuadro = buscar_caja_cuadro(df_precios, marca_protecciones, grado_electr)

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
        total_puntos_mecanismos = 0
        tot_tomas_dobles_global = 0
        tot_luces_dobles_global = 0
        tot_tomas_simples_global = 0
        tot_luces_simples_global = 0
        tot_otros_puntos_global = 0
        total_puntos_1p_global = 0
        total_puntos_2p_global = 0

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

        factor_techo = 0.85 if "Falso Techo" in tipo_techo else 1.15

        for idx, est in enumerate(estancias_activas):
            m2 = est["m2"]
            alt = est["altura"]
            dist_cuadro = est["distancia_cuadro"]
            nombre_est = est["nombre"].lower()

            ex_sch = est.get("extra_schuko", 0)
            ex_luz = est.get("extra_luz", 0)
            ex_rj45 = est.get("extra_rj45", 0)

            tubo_troncal = dist_cuadro * 2.0
            m_tubo_rozas = ((m2 * 4.5 * (alt / 2.5)) + (ex_sch * 6.0) + (ex_luz * 5.0) + (ex_rj45 * 8.0)) * factor_techo
            m_tubo_total_estancia = tubo_troncal + m_tubo_rozas
            
            m_tubo_20 = m_tubo_total_estancia * 0.75
            m_tubo_25 = m_tubo_total_estancia * 0.25
            n_cajas_reg = 1 if m2 > 8 else 0
            
            base_15 = ((m2 * 12.0) + (ex_luz * 15.0) + (dist_cuadro * 3.0)) * factor_techo
            est_15_az = base_15 * 0.30
            est_15_ne = base_15 * 0.30
            est_15_ma = base_15 * 0.20
            est_15_gr = base_15 * 0.10
            est_15_tt = base_15 * 0.10

            extra_cable_c4_desdoblado = (dist_cuadro * 2.0 + 12.0) if ("cocina" in nombre_est and desdoblar_c4) else 0.0
            base_25 = (m2 * (15.0 if grado_electr == "Elevada" else 12.0)) + (ex_sch * 18.0) + (dist_cuadro * 3.0) + extra_cable_c4_desdoblado
            est_25_az = base_25 * 0.40
            est_25_ne = base_25 * 0.40
            est_25_tt = base_25 * 0.20

            est_utp = 0.0
            if "salón" in nombre_est or "comedor" in nombre_est or "despacho" in nombre_est:
                est_utp = 15.0 + dist_cuadro
            est_utp += (ex_rj45 * 12.0)

            if "cocina" in nombre_est:
                cant_int = 1 + max(0, ex_luz)
                # Separación de tomas en cocina por circuito:
                cant_c5_encimera = 3
                cant_c2_cocina = 2 + max(0, ex_sch)
                cant_c3_horno = 1
                cant_c4_electro = 3 if desdoblar_c4 else 2
                cant_sch = cant_c5_encimera + cant_c2_cocina + cant_c3_horno + cant_c4_electro
                cant_rj_coc = 1 + max(0, ex_rj45)
                mecanismos_est = [
                    {"nombre": "Interruptor luz cocina (C1)", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int, "en_bd": ok_int},
                    {"nombre": "Bases Schuko 16A encimera (C5)", "desc_real": desc_schuko, "cant": cant_c5_encimera, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko},
                    {"nombre": "Bases Schuko 16A uso general cocina (C2)", "desc_real": desc_schuko, "cant": cant_c2_cocina, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko},
                    {"nombre": "Base fuerza 25A Horno/Vitro (C3)", "desc_real": desc_schuko, "cant": cant_c3_horno, "precio": p_schuko * 1.5, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko},
                    {"nombre": "Bases Schuko lavavajillas/lavadora/termo (C4)", "desc_real": desc_schuko, "cant": cant_c4_electro, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko},
                    {"nombre": "Toma de datos RJ45 Cat.6 cocina (ICT-2)", "desc_real": desc_rj45, "cant": cant_rj_coc, "precio": p_rj45, "prov": prov_rj45, "fila": fila_rj45, "en_bd": ok_rj45},
                    {"nombre": "Toma de Televisión RTV/SAT Coaxial cocina (ICT-2)", "desc_real": desc_tv, "cant": (1 + max(0, est.get("extra_tv", 0))), "precio": p_tv, "prov": prov_tv, "fila": fila_tv, "en_bd": ok_tv}
                ]
            elif "baño" in nombre_est:
                cant_int = 1 + max(0, ex_luz)
                cant_sch = 2 + max(0, ex_sch)
                mecanismos_est = [
                    {"nombre": "Interruptor luz espejo", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int, "en_bd": ok_int},
                    {"nombre": "Base Schuko tapa estanca IP44", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko * 1.2, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko}
                ]
            elif "salón" in nombre_est or "comedor" in nombre_est:
                ex_tv = est.get("extra_tv", 0)
                cant_int = 2 + max(0, ex_luz)
                cant_sch = 6 + max(0, ex_sch)
                cant_rj = 2 + max(0, ex_rj45)
                cant_tv_est = 2 + max(0, ex_tv)
                mecanismos_est = [
                    {"nombre": "Conmutador / Cruzamiento", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int, "en_bd": ok_int},
                    {"nombre": "Bases Schuko zona TV/Sofá", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko},
                    {"nombre": "Toma de datos RJ45 Cat.6 (Red Ethernet)", "desc_real": desc_rj45, "cant": cant_rj, "precio": p_rj45, "prov": prov_rj45, "fila": fila_rj45, "en_bd": ok_rj45},
                    {"nombre": "Toma de Televisión RTV/SAT Coaxial", "desc_real": desc_tv, "cant": cant_tv_est, "precio": p_tv, "prov": prov_tv, "fila": fila_tv, "en_bd": ok_tv}
                ]
            else:
                ex_tv = est.get("extra_tv", 0)
                cant_int = 2 + max(0, ex_luz)
                cant_sch = 3 + max(0, ex_sch)
                es_dorm = "dormitorio" in nombre_est or "habitación" in nombre_est
                cant_rj_d = (1 + max(0, ex_rj45)) if es_dorm else max(0, ex_rj45)
                cant_tv_d = (1 + max(0, ex_tv)) if es_dorm else max(0, ex_tv)
                mecanismos_est = [
                    {"nombre": "Conmutador / Interruptor", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int, "en_bd": ok_int},
                    {"nombre": "Bases Schuko 16A", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko}
                ]
                if cant_rj_d > 0:
                    mecanismos_est.append({"nombre": "Toma de datos RJ45 Cat.6 (Red Ethernet)", "desc_real": desc_rj45, "cant": cant_rj_d, "precio": p_rj45, "prov": prov_rj45, "fila": fila_rj45, "en_bd": ok_rj45})
                if cant_tv_d > 0:
                    mecanismos_est.append({"nombre": "Toma de Televisión RTV/SAT Coaxial", "desc_real": desc_tv, "cant": cant_tv_d, "precio": p_tv, "prov": prov_tv, "fila": fila_tv, "en_bd": ok_tv})

            total_mecanismos = sum([m["cant"] for m in mecanismos_est])
            
            def_td = 2 if ("salón" in nombre_est or "cocina" in nombre_est) else (1 if ("baño" in nombre_est or "dormitorio" in nombre_est) else 0)
            def_ld = 1 if ("salón" in nombre_est or "dormitorio" in nombre_est or "baño" in nombre_est) else 0
            td_est = int(est.get("tomas_dobles", def_td))
            ld_est = int(est.get("luces_dobles", def_ld))
            
            # Ajustar a los límites reales de mecanismos instalados
            td_est = max(0, min(td_est, cant_sch))
            ld_est = max(0, min(ld_est, cant_int))
            
            tomas_simples_est = max(0, cant_sch - td_est)
            luces_simples_est = max(0, cant_int - ld_est)
            otros_mecanismos_est = max(0, total_mecanismos - (cant_sch + cant_int))
            
            # Criterio 2 Puntos: cada toma doble = 2 puntos, cada luz doble = 2 puntos
            puntos_2p_est = tomas_simples_est + (td_est * 2) + luces_simples_est + (ld_est * 2) + otros_mecanismos_est
            # Criterio 1 Punto: cada toma doble = 1 punto, cada luz doble = 1 punto
            puntos_1p_est = tomas_simples_est + (td_est * 1) + luces_simples_est + (ld_est * 1) + otros_mecanismos_est
            
            puntos_est_sel = puntos_2p_est if es_doble_2_puntos else puntos_1p_est
            total_puntos_mecanismos += puntos_est_sel
            
            tot_tomas_dobles_global += td_est
            tot_luces_dobles_global += ld_est
            tot_tomas_simples_global += tomas_simples_est
            tot_luces_simples_global += luces_simples_est
            tot_otros_puntos_global += otros_mecanismos_est
            total_puntos_1p_global += puntos_1p_est
            total_puntos_2p_global += puntos_2p_est

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
                key_m = (mec["nombre"], mec["desc_real"], mec["precio"], mec["prov"], mec["fila"], mec.get("en_bd", True))
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
                h_rozas = (m2 * 0.35 * mult_soporte * (0.9 if "Falso Techo" in tipo_techo else 1.1)) if hace_rozas_electricista else 0.0

            h_tubo_cajas = (m2 * 0.25) * factor_techo
            h_cableado = (m2 * 0.30) * factor_techo
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

            # Desglose claro y específico del equipamiento y mecanismos de esta estancia
            items_est_txt = []
            for m in mecanismos_est:
                if m["cant"] > 0:
                    items_est_txt.append(f"{m['cant']}x {m['nombre']}")
            if n_marcos > 0:
                items_est_txt.append(f"{n_marcos}x Marcos")

            detalle_mec_estancia = ", ".join(items_est_txt)
            if not detalle_mec_estancia:
                detalle_mec_estancia = f"Instalación interior ({total_mecanismos} puntos)"

            comercial_estancias.append({
                "Estancia": est["nombre"],
                "Superficie": f"{m2} m²",
                "Detalle Comercial": detalle_mec_estancia,
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

        # Cómputo de tubos y cables adicionales para Climatización C9
        m_cable_60_c9 = 0.0
        if instalar_c9:
            if "Multi-Split" in tipo_c9:
                global_tubo25_m += 32.0
                m_cable_60_c9 = 96.0
            elif "Conductos" in tipo_c9:
                global_tubo25_m += 16.0
                m_cable_60_c9 = 48.0
            else:  # Split individual
                global_tubo20_m += 14.0
                global_25_az_m += 14.0
                global_25_ne_m += 14.0
                global_25_tt_m += 14.0

        # Cómputo de tubos y cables adicionales para Calefacción C8
        m_cable_60_c8 = 0.0
        if instalar_c8:
            if desdoblar_c8:
                global_tubo25_m += 36.0  # 2 líneas x 18m
                m_cable_60_c8 = 108.0   # 36m x 3 hilos 6 mm²
            else:
                global_tubo25_m += 18.0  # 1 línea x 18m
                m_cable_60_c8 = 54.0    # 18m x 3 hilos 6 mm²

        # Cómputo de tubos y cables adicionales para Domótica C11
        m_bus_knx = 0.0
        coste_extra_cajas_dom = 0.0
        if tipo_domotica == "Domótica Cableada por Bus (KNX / Centralizada)":
            m_bus_knx = max(24.0, len(estancias_activas) * 12.0)
            global_tubo20_m += m_bus_knx  # Tubo independiente M20 para el bus de datos
        elif tipo_domotica == "Domótica Inalámbrica (WiFi / Zigbee / Shelly - Micromódulos)":
            global_15_az_m += total_puntos_mecanismos * 3.5  # Neutro azul obligatorio en mecanismos
            coste_extra_cajas_dom = total_puntos_mecanismos * 0.85  # Cajas de 60 mm fondo

        # Mano de obra especializada para el Cuadro General CGMP
        # Montaje en envolvente, fijación DIN, peinado de conductores, peines de conexión, rotulación de circuitos y pruebas
        horas_cuadro = 3.5 if (grado_electr == "Elevada" or n_difs > 2) else 2.5
        if tipo_domotica == "Domótica Cableada por Bus (KNX / Centralizada)":
            horas_cuadro += 1.5
        coste_mo_cuadro = horas_cuadro * precio_hora
        horas_totales_obra += horas_cuadro
        coste_mano_obra_bruto = horas_totales_obra * precio_hora
        horas_totales_equipo = horas_totales_obra / num_operarios
        dias_estimados = horas_totales_equipo / horas_jornada

        # Surcharges técnicos certificados
        sobrecoste_dif_si = 45.0 if instalar_c9 else 0.0
        sobrecoste_fuente_knx = 95.0 if tipo_domotica == "Domótica Cableada por Bus (KNX / Centralizada)" else 0.0
        p_caja_final = (p_caja_cuadro * 1.5) if (num_circuitos_base > 10 or tipo_domotica == "Domótica Cableada por Bus (KNX / Centralizada)") else p_caja_cuadro

        n_pias = max(num_circuitos_base, len(estancias_activas))
        coste_cuadro_neto = p_iga + (n_difs * p_id) + sobrecoste_dif_si + sobrecoste_fuente_knx + (n_pias * p_pia) + p_caja_final + coste_extra_cajas_dom
        venta_cuadro_mat = coste_cuadro_neto * mult_comercial * mult_garantia_mat
        venta_cuadro_mo = coste_mo_cuadro * mult_comercial
        venta_cuadro_neto = venta_cuadro_mat + venta_cuadro_mo
        benef_cuadro = venta_cuadro_neto - (coste_cuadro_neto + coste_mo_cuadro)

        subtotal_general_neto = subtotal_neto_comercial + venta_cuadro_neto + float(precio_boletin_cie) + sum(float(p.get('subtotal', 0.0)) for p in st.session_state.get('partidas_manuales', []))
        cuota_iva = subtotal_general_neto * (iva_sel / 100.0)
        total_cliente = subtotal_general_neto + cuota_iva

        # Precio medio por punto instalado (Calculado sobre el total con IVA o Total Neto según prefieras; aquí usamos Total Cliente Con IVA / Puntos)
        precio_medio_por_punto = (total_cliente / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0
        precio_medio_por_punto_neto = (subtotal_general_neto / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0

        # ==========================================
        # CONSTRUCCIÓN DE LA ORDEN DE COMPRA POR CATEGORÍAS
        # ==========================================
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
        cuota_iva_mat = total_mat_global_neto * 0.21

        from collections import defaultdict
        categorias_orden_compra = defaultdict(list, {
            "🎛️ 1. Mecanismos y Marcos": [],
            "⚡ 2. Cables y Conductores": [],
            "🛡️ 3. Cuadro Eléctrico y Protecciones": [],
            "📡 4. Telecomunicaciones (ICT-2 RD 346/2011 & RTR)": [],
            "📏 5. Tubos y Canalizaciones": [],
            "📦 6. Cajas y Conexiones": []
        })

        # 0. Construcción del Desglose de Materiales Asignados por Estancia
        materiales_por_estancia = []
        for est_info in desgloses_internos_estancias:
            r_nom = est_info["nombre"]
            r_m2 = est_info["m2"]
            r_dist = est_info["dist_cuadro"]
            r_mecs = est_info["mecanismos_detalle"]
            r_tubo20 = est_info["m_tubo_20"]
            r_tubo25 = est_info["m_tubo_25"]
            r_cajas_reg = est_info["n_cajas_reg"]
            r_tot_mec = sum([m["cant"] for m in r_mecs])
            r_marcos = max(r_tot_mec, int(r_tot_mec * 0.8))
            
            r_cables_list = [
                {"item": "Cable 1.5 mm² Azul", "metros": est_info["cable_15_az"]},
                {"item": "Cable 1.5 mm² Fase (Negro/Marrón/Gris)", "metros": est_info["cable_15_ne"] + est_info["cable_15_ma"] + est_info["cable_15_gr"]},
                {"item": "Cable 1.5 mm² Tierra TT", "metros": est_info["cable_15_tt"]},
                {"item": "Cable 2.5 mm² Azul", "metros": est_info["cable_25_az"]},
                {"item": "Cable 2.5 mm² Fase (Negro/Marrón)", "metros": est_info["cable_25_ne"]},
                {"item": "Cable 2.5 mm² Tierra TT", "metros": est_info["cable_25_tt"]},
            ]
            if est_info["cable_utp"] > 0:
                r_cables_list.append({"item": "Cable Red UTP Cat.6", "metros": est_info["cable_utp"]})
            
            materiales_por_estancia.append({
                "nombre": r_nom,
                "m2": r_m2,
                "distancia_cuadro": r_dist,
                "mecanismos": r_mecs,
                "marcos": r_marcos,
                "cajas_mecanismo": r_tot_mec,
                "cajas_registro": r_cajas_reg,
                "tubo_m20": r_tubo20,
                "tubo_m25": r_tubo25,
                "cables": r_cables_list,
                "coste_materiales_neto": est_info["neto_mat"],
                "coste_materiales_con_iva": est_info["iva_mat"]
            })

        # 1. Mecanismos y Marcos (Agrupados y Consolidados por Referencia Única)
        mecanismos_agrupados = {}
        for (nom_m, desc_m, p_m, prov_m, fila_m, ok_m), cant_m in global_mecanismos_dict.items():
            if cant_m <= 0:
                continue
            nom_m_l = nom_m.lower()
            if "interruptor" in nom_m_l or "conmutador" in nom_m_l:
                nom_std = "Interruptor / Conmutador 10AX"
                tipo_orden = 1
            elif "25a" in nom_m_l or "horno" in nom_m_l or "fuerza" in nom_m_l:
                nom_std = "Base Enchufe Fuerza 25A (Horno / Vitro)"
                tipo_orden = 3
            elif "schuko" in nom_m_l or "enchufe" in nom_m_l:
                nom_std = "Base de Enchufe Schuko 16A 2P+T con Obturador"
                tipo_orden = 2
            elif "rj45" in nom_m_l or "datos" in nom_m_l or "red" in nom_m_l:
                nom_std = "Toma de Datos RJ45 Cat.6 UTP"
                tipo_orden = 4
            else:
                nom_std = nom_m
                tipo_orden = 5

            clave_agrup = (nom_std, desc_m, p_m, prov_m, ok_m, tipo_orden)
            if clave_agrup not in mecanismos_agrupados:
                mecanismos_agrupados[clave_agrup] = 0
            mecanismos_agrupados[clave_agrup] += cant_m

        # Ordenar mecanismos lógicamente: Interruptores -> Schukos 16A -> Base 25A -> RJ45 -> Otros
        lista_mecanismos_ordenados = sorted(mecanismos_agrupados.items(), key=lambda x: (x[0][5], x[0][0]))

        for (nom_std, desc_m, p_m, prov_m, ok_m, _), cant_tot in lista_mecanismos_ordenados:
            categorias_orden_compra["🎛️ 1. Mecanismos y Marcos"].append({
                "articulo": nom_std,
                "desc_exacta": desc_m,
                "proveedor": prov_m,
                "cantidad": int(cant_tot),
                "unidad": "ud",
                "precio_unitario": p_m,
                "subtotal": round(cant_tot * p_m, 2),
                "en_bd": ok_m,
                "categoria_bd": "Mecanismos",
                "marca_bd": "Efapel" if ("efapel" in str(serie_mecanismos).lower() or "racional" in str(serie_mecanismos).lower()) else str(serie_mecanismos).split()[0]
            })

        if global_marcos_uds > 0:
            categorias_orden_compra["🎛️ 1. Mecanismos y Marcos"].append({
                "articulo": "Marcos Embellecedores 1 Elemento",
                "desc_exacta": desc_marco,
                "proveedor": prov_marco,
                "cantidad": int(global_marcos_uds),
                "unidad": "ud",
                "precio_unitario": p_marco,
                "subtotal": round(global_marcos_uds * p_marco, 2),
                "en_bd": ok_marco,
                "categoria_bd": "Marcos / Placas",
                "marca_bd": "Efapel" if ("efapel" in str(serie_mecanismos).lower() or "racional" in str(serie_mecanismos).lower()) else str(serie_mecanismos).split()[0]
            })

        # 2. Cables y Conductores
        cables_items = [
            ("Cable 1.5 mm² Azul", desc_15_az, prov_15_az, global_15_az_m, p_15_az, rollos_15_az, ok_15_az),
            ("Cable 1.5 mm² Negro", desc_15_ne, prov_15_ne, global_15_ne_m, p_15_ne, rollos_15_ne, ok_15_ne),
            ("Cable 1.5 mm² Marrón", desc_15_ma, prov_15_ma, global_15_ma_m, p_15_ma, rollos_15_ma, ok_15_ma),
            ("Cable 1.5 mm² Gris", desc_15_gr, prov_15_gr, global_15_gr_m, p_15_gr, rollos_15_gr, ok_15_gr),
            ("Cable 1.5 mm² Tierra (Amarillo/Verde)", desc_15_tt, prov_15_tt, global_15_tt_m, p_15_tt, rollos_15_tt, ok_15_tt),
            ("Cable 2.5 mm² Azul", desc_25_az, prov_25_az, global_25_az_m, p_25_az, rollos_25_az, ok_25_az),
            ("Cable 2.5 mm² Negro / Marrón", desc_25_ne, prov_25_ne, global_25_ne_m, p_25_ne, rollos_25_ne, ok_25_ne),
            ("Cable 2.5 mm² Tierra (Amarillo/Verde)", desc_25_tt, prov_25_tt, global_25_tt_m, p_25_tt, rollos_25_tt, ok_25_tt),
        ]
        
        # Cable 6.0 mm² Cu para Cocina C3, Calefacción C8 y Climatización C9
        total_cable_60 = 36.0  # Cocina C3 base (12m x 3 hilos)
        if instalar_c8:
            total_cable_60 += m_cable_60_c8
        if instalar_c9:
            total_cable_60 += m_cable_60_c9

        if total_cable_60 > 0:
            p_60_val = p_25_az * 2.2
            rollos_60 = max(1, int((total_cable_60 + 99) / 100))
            desc_60 = f"{desc_25_az.replace('2.5', '6.0')} (Fuerza C3/C8/C9)"
            cables_items.append(("Cable 6.0 mm² Fuerza (C3/C8/C9)", desc_60, "Top Cable / General Cable", total_cable_60, p_60_val, rollos_60, True))

        if tipo_domotica == "Domótica Cableada por Bus (KNX / Centralizada)" and m_bus_knx > 0:
            rollos_bus = max(1, int((m_bus_knx + 99) / 100))
            cables_items.append(("Cable Bus KNX TP1 Apantallado (Verde)", "Cable bus certificado KNX 2x2x0.8 mm 4kV", "Schneider / ABB", m_bus_knx, 0.88, rollos_bus, True))

        if global_utp_m > 0:
            cables_items.append(("Cable Red UTP Cat.6", desc_utp, prov_utp, global_utp_m, p_utp, max(1, int((global_utp_m + 99)/100)), ok_utp))

        for nom_c, desc_c, prov_c, m_c, p_c, rollos_c, ok_c in cables_items:
            if m_c > 0:
                categorias_orden_compra["⚡ 2. Cables y Conductores"].append({
                    "articulo": nom_c,
                    "desc_exacta": f"{desc_c} [Acopio: {rollos_c} rollo(s) de 100m]",
                    "proveedor": prov_c,
                    "cantidad": int(round(m_c)),
                    "unidad": "m",
                    "precio_unitario": p_c,
                    "subtotal": round(m_c * p_c, 2),
                    "en_bd": ok_c,
                    "categoria_bd": "Conductores",
                    "marca_bd": "General Cable / Top Cable"
                })

        # 3. Cuadro Eléctrico y Protecciones
        desc_id_final = desc_id
        if instalar_c9:
            desc_id_final += " (Incluye 1x ID Tipo A Superinmunizado para Climatización C9)"

        categorias_orden_compra["🛡️ 3. Cuadro Eléctrico y Protecciones"].extend([
            {
                "articulo": "Caja Cuadro de Distribución",
                "desc_exacta": f"{desc_caja_cuadro} [Ampliación DIN {num_circuitos_base} elementos]" if num_circuitos_base > 10 else desc_caja_cuadro,
                "proveedor": prov_caja_cuadro,
                "cantidad": 1,
                "unidad": "ud",
                "precio_unitario": p_caja_final,
                "subtotal": round(p_caja_final, 2),
                "en_bd": ok_caja_cuadro,
                "categoria_bd": "Cuadros y Envolventes",
                "marca_bd": marca_protecciones
            },
            {
                "articulo": f"IGA Oficial ({iga_amperaje}A 2P)",
                "desc_exacta": desc_iga,
                "proveedor": prov_iga,
                "cantidad": 1,
                "unidad": "ud",
                "precio_unitario": p_iga,
                "subtotal": round(p_iga, 2),
                "en_bd": ok_iga,
                "categoria_bd": "Protecciones",
                "marca_bd": marca_protecciones
            },
            {
                "articulo": f"Interruptores Diferenciales 40A 30mA (x{n_difs})",
                "desc_exacta": desc_id_final,
                "proveedor": prov_id,
                "cantidad": n_difs,
                "unidad": "ud",
                "precio_unitario": round(p_id + (sobrecoste_dif_si / n_difs), 2),
                "subtotal": round(n_difs * p_id + sobrecoste_dif_si, 2),
                "en_bd": ok_id,
                "categoria_bd": "Protecciones",
                "marca_bd": marca_protecciones
            },
            {
                "articulo": "PIAs Magnetotérmicos Circuitos REBT",
                "desc_exacta": desc_pia,
                "proveedor": prov_pia,
                "cantidad": n_pias,
                "unidad": "ud",
                "precio_unitario": p_pia,
                "subtotal": round(n_pias * p_pia, 2),
                "en_bd": ok_pia,
                "categoria_bd": "Protecciones",
                "marca_bd": marca_protecciones
            }
        ])

        if tipo_domotica == "Domótica Cableada por Bus (KNX / Centralizada)":
            categorias_orden_compra["🛡️ 3. Cuadro Eléctrico y Protecciones"].append({
                "articulo": "Fuente Alimentación Bus 30V DC KNX (Carril DIN)",
                "desc_exacta": "Fuente carril DIN 30V DC / 640mA con bobina de desacoplo integrada",
                "proveedor": "Schneider / ABB / MeanWell",
                "cantidad": 1,
                "unidad": "ud",
                "precio_unitario": 95.0,
                "subtotal": 95.0,
                "en_bd": True,
                "categoria_bd": "Domótica / Control",
                "marca_bd": "KNX Standard"
            })

        # 4. Tubos y Canalizaciones
        tubos_items = [
            ("Tubo Corrugado M-20", desc_tubo20, prov_tubo20, global_tubo20_m, p_tubo20, rollos_tubo20, ok_tubo20),
            ("Tubo Corrugado M-25", desc_tubo25, prov_tubo25, global_tubo25_m, p_tubo25, rollos_tubo25, ok_tubo25),
        ]
        for nom_t, desc_t, prov_t, m_t, p_t, rollos_t, ok_t in tubos_items:
            if m_t > 0:
                categorias_orden_compra["📏 5. Tubos y Canalizaciones"].append({
                    "articulo": nom_t,
                    "desc_exacta": f"{desc_t} [Acopio: {rollos_t} rollo(s) de 50m]",
                    "proveedor": prov_t,
                    "cantidad": int(round(m_t)),
                    "unidad": "m",
                    "precio_unitario": p_t,
                    "subtotal": round(m_t * p_t, 2),
                    "en_bd": ok_t,
                    "categoria_bd": "Canalización Tubos",
                    "marca_bd": "General"
                })

        # 5. Cajas y Conexiones
        cajas_items = [
            ("Cajas Universales Mecanismo 67mm", desc_caja_mec, prov_caja_mec, global_caja_mec_uds, "ud", p_caja_mec, ok_caja_mec, "Cajas de Mecanismos"),
            ("Cajas de Registro Empotrar 100x100mm", desc_caja_reg, prov_caja_reg, global_caja_reg_uds, "ud", p_caja_reg, ok_caja_reg, "Cajas de Registro"),
            ("Conexión en Cajas (" + ("Wago 221" if "Wago" in tipo_conexion else "Clemas") + ")", desc_con, prov_con, max(1, global_caja_reg_uds * 2), "ud/pack", p_con, ok_con, "Conexión"),
        ]
        for nom_cj, desc_cj, prov_cj, cant_cj, unid_cj, p_cj, ok_cj, cat_cj in cajas_items:
            if cant_cj > 0:
                categorias_orden_compra["📦 6. Cajas y Conexiones"].append({
                    "articulo": nom_cj,
                    "desc_exacta": desc_cj,
                    "proveedor": prov_cj,
                    "cantidad": cant_cj,
                    "unidad": unid_cj,
                    "precio_unitario": p_cj,
                    "subtotal": round(cant_cj * p_cj, 2),
                    "en_bd": ok_cj,
                    "categoria_bd": cat_cj,
                    "marca_bd": "Wago" if "Wago" in str(nom_cj) else "General"
                })

        # 4. Telecomunicaciones e ICT-2 (RTR, PAUs y Cableados)
        n_schuko_teleco = 3 if "3 Bases" in st.session_state.get("rad_schuko_rtr", "3 Bases") else 2
        p_rtr_box = 57.02 if "Rack" in st.session_state.get("sel_tipo_rtr", "") else 32.50
        desc_rtr_box = "Armario Rack Mural 10 Pulgadas 6U ICT" if "Rack" in st.session_state.get("sel_tipo_rtr", "") else "Caja Registro Terminación Red RTR Empotrada ICT-2 Normalizada"
        m_coaxial_tot = len(estancias_activas) * 15.0

        categorias_orden_compra["📡 4. Telecomunicaciones (ICT-2 RD 346/2011 & RTR)"].append({
            "articulo": "Cuadro / Armario RTR Telecomunicaciones ICT-2",
            "desc_exacta": desc_rtr_box,
            "proveedor": "Televes / Obramat",
            "cantidad": 1,
            "unidad": "ud",
            "precio_unitario": p_rtr_box,
            "subtotal": round(p_rtr_box, 2),
            "en_bd": True,
            "categoria_bd": "Telecomunicaciones",
            "marca_bd": "Televes"
        })
        categorias_orden_compra["📡 4. Telecomunicaciones (ICT-2 RD 346/2011 & RTR)"].append({
            "articulo": f"Bases Schuko 16A Cuadro RTR (Circuito C2) - {n_schuko_teleco} tomas",
            "desc_exacta": f"Bases Schuko 16A Empotradas para Alimentación RTR (x{n_schuko_teleco})",
            "proveedor": prov_schuko,
            "cantidad": n_schuko_teleco,
            "unidad": "ud",
            "precio_unitario": p_schuko,
            "subtotal": round(n_schuko_teleco * p_schuko, 2),
            "en_bd": True,
            "categoria_bd": "Mecanismos",
            "marca_bd": serie_mecanismos
        })
        categorias_orden_compra["📡 4. Telecomunicaciones (ICT-2 RD 346/2011 & RTR)"].append({
            "articulo": "PAU Fibra Óptica FTTH 2x SC/APC con Roseta",
            "desc_exacta": "PAU Fibra Óptica 2 Tomas SC/APC con Roseta Interior ICT-2",
            "proveedor": "Televes / Obramat",
            "cantidad": 1,
            "unidad": "ud",
            "precio_unitario": 14.20,
            "subtotal": 14.20,
            "en_bd": True,
            "categoria_bd": "Telecomunicaciones",
            "marca_bd": "Televes"
        })
        categorias_orden_compra["📡 4. Telecomunicaciones (ICT-2 RD 346/2011 & RTR)"].append({
            "articulo": "PAU Repartidor Televisión Coaxial RTV Televes F",
            "desc_exacta": "PAU Distribuidor Televisión EasyF Televes",
            "proveedor": "Televes / Obramat",
            "cantidad": 1,
            "unidad": "ud",
            "precio_unitario": 8.68,
            "subtotal": 8.68,
            "en_bd": True,
            "categoria_bd": "Telecomunicaciones",
            "marca_bd": "Televes"
        })
        categorias_orden_compra["📡 4. Telecomunicaciones (ICT-2 RD 346/2011 & RTR)"].append({
            "articulo": "Multiplexor Pasivo Red Datos RJ45 Cat.6 UTP",
            "desc_exacta": "Panel de Parcheo / Multiplexor Pasivo 8x RJ45 Cat.6 para RTR",
            "proveedor": "Televes / Obramat",
            "cantidad": 1,
            "unidad": "ud",
            "precio_unitario": 18.50,
            "subtotal": 18.50,
            "en_bd": True,
            "categoria_bd": "Telecomunicaciones",
            "marca_bd": "Televes"
        })
        categorias_orden_compra["📡 4. Telecomunicaciones (ICT-2 RD 346/2011 & RTR)"].append({
            "articulo": "Cable Coaxial TV RG6 Cobre Cu/Cu Cca (Tendido Interior)",
            "desc_exacta": "Cable Coaxial RG6 Cobre / Cobre Cu/Cu Cca Alta Cobertura (Rollo)",
            "proveedor": "Televes / Prysmian",
            "cantidad": int(round(m_coaxial_tot)),
            "unidad": "m",
            "precio_unitario": 0.52,
            "subtotal": round(m_coaxial_tot * 0.52, 2),
            "en_bd": True,
            "categoria_bd": "Conductores",
            "marca_bd": "Televes"
        })

        # Listado de no catalogados para el actualizador interactivo
        items_no_catalogados = []
        for cat_k, items_k in categorias_orden_compra.items():
            for it in items_k:
                if not it.get("en_bd", True) or "NO ENCONTRADO" in it.get("desc_exacta", ""):
                    items_no_catalogados.append(it)

        # Flatten into DataFrame for export and display
        filas_df_oc = []
        for cat_nombre, items_cat in categorias_orden_compra.items():
            for item in items_cat:
                estado_bd_txt = "🟢 En Catálogo" if item.get("en_bd", True) else "⚠️ No en BD (Estimado)"
                filas_df_oc.append({
                    "Categoría": cat_nombre,
                    "Artículo": item["articulo"],
                    "Descripción Exacta del Artículo": item["desc_exacta"],
                    "Tienda / Proveedor": item["proveedor"],
                    "Cantidad": item["cantidad"],
                    "Unidad": item["unidad"],
                    "Precio S/IVA (€)": round(item["precio_unitario"], 2),
                    "Subtotal S/IVA (€)": round(item["subtotal"], 2),
                    "Total C/IVA 21% (€)": round(item["subtotal"] * 1.21, 2),
                    "Estado Catálogo": estado_bd_txt
                })
        df_orden_compra = pd.DataFrame(filas_df_oc)

        orden_compra_data = {
            "categorias": categorias_orden_compra,
            "total_neto": total_mat_global_neto,
            "iva_pct": 21.0,
            "cuota_iva": cuota_iva_mat,
            "total_con_iva": total_mat_con_iva,
            "potencia_kw": potencia_prevista_kw,
            "tipo_cable": tipo_cable_sel,
            "tipo_tubo": tipo_tubo_sel,
            "serie_mecanismos": serie_mecanismos,
            "marca_protecciones": marca_protecciones,
            "materiales_por_estancia": materiales_por_estancia
        }

        # Construcción del catálogo de materiales principales valorados a PVP para el cliente
        materiales_pvp = []
        for cat_nombre, items_cat in categorias_orden_compra.items():
            for item in items_cat:
                pvp_u = round(item["precio_unitario"] * mult_comercial * mult_garantia_mat, 2)
                sub_pvp = round(item["subtotal"] * mult_comercial * mult_garantia_mat, 2)
                materiales_pvp.append({
                    "categoria": cat_nombre,
                    "articulo": item["articulo"],
                    "desc_exacta": item["desc_exacta"],
                    "proveedor": item["proveedor"],
                    "cantidad": item["cantidad"],
                    "unidad": item["unidad"],
                    "pvp_unitario": pvp_u,
                    "subtotal_pvp": sub_pvp
                })

        # Construcción de los Capítulos REBT de la Oferta Comercial Oficial (Memoria Valorada)
        coste_tubos_cajas_tot = (global_tubo20_m * p_tubo20) + (global_tubo25_m * p_tubo25) + (global_caja_mec_uds * p_caja_mec) + (global_caja_reg_uds * p_caja_reg)
        coste_cables_tot = (global_15_az_m * p_15_az) + (global_15_ne_m * p_15_ne) + (global_15_ma_m * p_15_ma) + (global_15_gr_m * p_15_gr) + (global_15_tt_m * p_15_tt) + (global_25_az_m * p_25_az) + (global_25_ne_m * p_25_ne) + (global_25_tt_m * p_25_tt) + (global_utp_m * p_utp)
        coste_mecanismos_marcos_tot = sum(m["cant"] * m["precio"] for est_x in materiales_por_estancia for m in est_x["mecanismos"]) + (global_marcos_uds * p_marco)

        venta_cap1_cgmp = venta_cuadro_neto
        venta_cap2_canalizacion_esc = (coste_tubos_cajas_tot * mult_comercial * mult_garantia_mat) + ((sum_h_rozas + sum_h_tubos) * precio_hora * mult_comercial)
        venta_cap3_cableado_esc = (coste_cables_tot * mult_comercial * mult_garantia_mat) + (sum_h_cable * precio_hora * mult_comercial)
        venta_cap4_mecanismos_esc = (coste_mecanismos_marcos_tot * mult_comercial * mult_garantia_mat) + (sum_h_mec * precio_hora * mult_comercial)

        suma_caps_interior_esc = venta_cap2_canalizacion_esc + venta_cap3_cableado_esc + venta_cap4_mecanismos_esc
        if es_modo_tarifa_puntos and total_puntos_mecanismos > 0 and suma_caps_interior_esc > 0:
            total_venta_puntos_deseado = float(total_puntos_mecanismos) * float(tarifa_punto_calle)
            factor_ajuste_puntos = total_venta_puntos_deseado / suma_caps_interior_esc
            venta_cap2_canalizacion = venta_cap2_canalizacion_esc * factor_ajuste_puntos
            venta_cap3_cableado = venta_cap3_cableado_esc * factor_ajuste_puntos
            venta_cap4_mecanismos = venta_cap4_mecanismos_esc * factor_ajuste_puntos
        else:
            venta_cap2_canalizacion = venta_cap2_canalizacion_esc
            venta_cap3_cableado = venta_cap3_cableado_esc
            venta_cap4_mecanismos = venta_cap4_mecanismos_esc

        venta_cap5_boletin = float(precio_boletin_cie)
        venta_cap6_manuales = sum(float(p.get('subtotal', 0.0)) for p in st.session_state.get('partidas_manuales', []))

        # Capítulo de Telecomunicaciones (ICT-2 RD 346/2011)
        coste_teleco_mat = sum(it["subtotal"] for it in categorias_orden_compra.get("📡 4. Telecomunicaciones (ICT-2 RD 346/2011 & RTR)", []))
        horas_teleco = 3.0  # Instalación y conectorización de RTR, PAUs y tomas
        venta_cap_teleco = (coste_teleco_mat * mult_comercial * mult_garantia_mat) + (horas_teleco * precio_hora * mult_comercial)

        capitulos_presupuesto = [
            {
                "cap": "CAP. 01",
                "titulo": "Cuadro General de Mando y Protección (CGMP)",
                "desc": f"Suministro e instalación de cuadro general empotrado, IGA {iga_amperaje}A 6kA, protector de sobretensiones permanentes y transitorias (POP+DPS), {n_difs}x diferencial(es) 40A/30mA y {n_pias}x PIAs magnetotérmicos de protección según ITC-BT-25, incluido montaje, peinado y conexionado integral ({horas_cuadro:.1f} h MO).",
                "importe": round(venta_cap1_cgmp, 2)
            },
            {
                "cap": "CAP. 02",
                "titulo": "Infraestructura de Telecomunicaciones y Cuadro RTR (ICT-2 RD 346/2011)",
                "desc": f"Suministro, montaje y conectorización de Registro de Terminación de Red (RTR), dotado de {n_schuko_teleco} bases Schuko 16A (C2), PAU de Fibra Óptica (FTTH) 2x SC/APC, PAU de RTV Coaxial Televes con repartidor F EasyF, multiplexor pasivo de datos RJ45 Cat.6 UTP y tendido de cable coaxial RG6 Cu/Cu ({len(estancias_activas)*15:.0f} m) y UTP Cat.6 LSZH ({len(estancias_activas)*18:.0f} m) conforme al RD 346/2011.",
                "importe": round(venta_cap_teleco, 2)
            },
            {
                "cap": "CAP. 03",
                "titulo": "Canalizaciones, Rozas y Cajas de Registro",
                "desc": f"Rozas en {tipo_pared} (techo: {'Falso Techo' if 'Falso Techo' in tipo_techo else 'Macizo'}), tendido de {global_tubo20_m + global_tubo25_m:.0f} m de tubo corrugado {tipo_tubo_sel} M20/M25, colocación de {global_caja_mec_uds} cajas universales y {global_caja_reg_uds} cajas de derivación protegidas.",
                "importe": round(venta_cap2_canalizacion, 2)
            },
            {
                "cap": "CAP. 04",
                "titulo": "Cableado y Líneas de Distribución Interior",
                "desc": f"Suministro y tendido de {global_15_az_m + global_15_ne_m + global_15_ma_m + global_15_gr_m + global_15_tt_m + global_25_az_m + global_25_ne_m + global_25_tt_m + global_utp_m:.0f} m de conductores de cobre {tipo_cable_sel} (1.5, 2.5, 4, 6, 10 mm²) con código de colores REBT y puesta a tierra equipotencial.",
                "importe": round(venta_cap3_cableado, 2)
            },
            {
                "cap": "CAP. 05",
                "titulo": "Mecanismos y Aparamenta por Estancias",
                "desc": f"Suministro y montaje de {total_puntos_mecanismos} mecanismos serie {serie_mecanismos} (interruptores, conmutadores, bases Schuko 16A, toma 25A y tomas datos RJ45) con {global_marcos_uds} marcos embellecedores por estancias.",
                "importe": round(venta_cap4_mecanismos, 2)
            },
            {
                "cap": "CAP. 06",
                "titulo": "Ensayos Reglamentarios, MTD y Tramitación Boletín Oficial CIE",
                "desc": "Verificaciones y ensayos ITC-BT-05 (aislamiento con megóhmetro, disparo de diferenciales, continuidad y bucle de tierra), redacción de Memoria Técnica de Diseño (MTD) y tramitación telemática oficial del Certificado de Instalación Eléctrica (CIE) ante la DGEAIM de la Región de Murcia.",
                "importe": round(venta_cap5_boletin, 2)
            }
        ]

        if st.session_state.get('partidas_manuales', []):
            capitulos_presupuesto.append({
                "cap": "CAP. 07",
                "titulo": "Trabajos Adicionales y Partidas a Medida",
                "desc": f"Partidas personalizadas y mejoras adicionales ({len(st.session_state.partidas_manuales)} partidas añadidas por el usuario).",
                "importe": round(venta_cap6_manuales, 2)
            })

        subtotal_general_neto = sum(c["importe"] for c in capitulos_presupuesto)
        cuota_iva = subtotal_general_neto * (iva_sel / 100.0)
        total_cliente = subtotal_general_neto + cuota_iva
        precio_medio_por_punto = (total_cliente / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0
        precio_medio_por_punto_neto = (subtotal_general_neto / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0

        # Pre-generar archivos de Orden de Compra / Reporte de Materiales
        excel_oc_bytes = exportar_excel_orden_compra(
            df_orden_compra, total_mat_global_neto, cuota_iva_mat, total_mat_con_iva,
            {
                "empresa": empresa_nombre,
                "proyectista": instalador_nombre,
                "fecha": datetime.date.today().strftime("%d/%m/%Y"),
                "potencia_kw": potencia_prevista_kw,
                "tipo_cable": tipo_cable_sel,
                "tipo_tubo": tipo_tubo_sel,
                "serie_mecanismos": serie_mecanismos,
                "marca_protecciones": marca_protecciones,
                "p_marco": p_marco
            },
            mat_estancias=materiales_por_estancia
        )

        pdf_oc_bytes = pdf_presupuesto.generar_pdf_orden_compra(
            proyecto_info={
                "empresa": empresa_nombre,
                "proyectista": instalador_nombre,
                "licencia": n_licencia,
                "localidad": localidad,
                "telefono": telefono,
                "expediente": "OC-2026-01",
                "fecha": datetime.date.today().strftime("%d/%m/%Y")
            },
            orden_compra_data=orden_compra_data
        )

        # Preparación de datos para el Esquema Unifilar Oficial para Industria (DGEAIM Murcia)
        pot_w_val = 5750
        if "5.750" in potencia_prevista_kw:
            pot_w_val = 5750
        elif "7.360" in potencia_prevista_kw:
            pot_w_val = 7360
        elif "9.200" in potencia_prevista_kw:
            pot_w_val = 9200
        elif "11.500" in potencia_prevista_kw:
            pot_w_val = 11500
        elif "14.490" in potencia_prevista_kw:
            pot_w_val = 14490

        # Determinación de diferenciales (máx 5 circuitos por diferencial según REBT)
        n_difs = 2 if (num_circuitos_base > 5 or grado_electr == "Elevada") else 1

        circuitos_unifilar = [
            {
                "id": "C1",
                "denominacion": "Iluminación general de la vivienda",
                "pia": 10,
                "dif": "ID 1 (30mA)",
                "cable_sec": "2x1.5 + TT 1.5 mm² Cu",
                "tubo_diam": "M20 (Tubo Corrugado)",
                "long_m": 15.0,
                "cdt_pct": 0.85,
                "pot_w": 2300
            },
            {
                "id": "C2",
                "denominacion": "Tomas de corriente uso general y frigorífico",
                "pia": 16,
                "dif": "ID 1 (30mA)",
                "cable_sec": "2x2.5 + TT 2.5 mm² Cu",
                "tubo_diam": "M20 (Tubo Corrugado)",
                "long_m": 18.0,
                "cdt_pct": 1.15,
                "pot_w": 3450
            },
            {
                "id": "C3",
                "denominacion": "Cocina eléctrica y horno",
                "pia": 25,
                "dif": "ID 1 (30mA)",
                "cable_sec": "2x6 + TT 6 mm² Cu",
                "tubo_diam": "M25 (Tubo Corrugado)",
                "long_m": 12.0,
                "cdt_pct": 0.82,
                "pot_w": 5400
            },
        ]

        if desdoblar_c4:
            circuitos_unifilar.extend([
                {
                    "id": "C4-A",
                    "denominacion": "Lavadora y Lavavajillas (Desdoblado)",
                    "pia": 16,
                    "dif": "ID 1 (30mA)",
                    "cable_sec": "2x2.5 + TT 2.5 mm² Cu",
                    "tubo_diam": "M20 (Tubo Corrugado)",
                    "long_m": 14.0,
                    "cdt_pct": 0.98,
                    "pot_w": 3450
                },
                {
                    "id": "C4-B",
                    "denominacion": "Termo eléctrico ACS (Desdoblado)",
                    "pia": 16,
                    "dif": "ID 2 (30mA)" if n_difs > 1 else "ID 1 (30mA)",
                    "cable_sec": "2x2.5 + TT 2.5 mm² Cu",
                    "tubo_diam": "M20 (Tubo Corrugado)",
                    "long_m": 14.0,
                    "cdt_pct": 0.95,
                    "pot_w": 3450
                }
            ])
        else:
            circuitos_unifilar.append({
                "id": "C4",
                "denominacion": "Lavadora, Lavavajillas y Termo eléctrico",
                "pia": 20,
                "dif": "ID 1 (30mA)",
                "cable_sec": "2x4 + TT 4 mm² Cu",
                "tubo_diam": "M20 (Tubo Corrugado)",
                "long_m": 15.0,
                "cdt_pct": 1.20,
                "pot_w": 4600
            })

        circuitos_unifilar.append({
            "id": "C5",
            "denominacion": "Tomas de corriente en baños y tomas auxiliares cocina",
            "pia": 16,
            "dif": "ID 2 (30mA)" if n_difs > 1 else "ID 1 (30mA)",
            "cable_sec": "2x2.5 + TT 2.5 mm² Cu",
            "tubo_diam": "M20 (Tubo Corrugado)",
            "long_m": 14.0,
            "cdt_pct": 0.92,
            "pot_w": 3450
        })

        # Circuito C8 Calefacción Eléctrica (o C8.1 y C8.2 desdoblados)
        if instalar_c8:
            if desdoblar_c8:
                p_c8_1 = int(round(pot_c8 / 2))
                p_c8_2 = pot_c8 - p_c8_1
                dif_c8_1 = "ID 2 (30mA)" if n_difs > 1 else "ID 1 (30mA)"
                dif_c8_2 = f"ID {min(n_difs, 3)} (30mA)" if n_difs > 2 else ("ID 2 (30mA)" if n_difs > 1 else "ID 1 (30mA)")
                circuitos_unifilar.extend([
                    {
                        "id": "C8.1",
                        "denominacion": "Calefacción Eléctrica - Zona Día (Desdoblado)",
                        "pia": 25,
                        "dif": dif_c8_1,
                        "cable_sec": "2x6 + TT 6 mm² Cu",
                        "tubo_diam": "M25 (Tubo Corrugado)",
                        "long_m": 16.0,
                        "cdt_pct": 0.85,
                        "pot_w": p_c8_1
                    },
                    {
                        "id": "C8.2",
                        "denominacion": "Calefacción Eléctrica - Zona Noche (Desdoblado)",
                        "pia": 25,
                        "dif": dif_c8_2,
                        "cable_sec": "2x6 + TT 6 mm² Cu",
                        "tubo_diam": "M25 (Tubo Corrugado)",
                        "long_m": 18.0,
                        "cdt_pct": 0.92,
                        "pot_w": p_c8_2
                    }
                ])
            else:
                circuitos_unifilar.append({
                    "id": "C8",
                    "denominacion": "Calefacción Eléctrica unificada",
                    "pia": 25,
                    "dif": "ID 2 (30mA)" if n_difs > 1 else "ID 1 (30mA)",
                    "cable_sec": "2x6 + TT 6 mm² Cu",
                    "tubo_diam": "M25 (Tubo Corrugado)",
                    "long_m": 16.0,
                    "cdt_pct": 0.95,
                    "pot_w": pot_c8
                })

        # Circuito C9 Aire Acondicionado / Climatización Inverter (Diferencial Tipo A SI)
        if instalar_c9:
            dif_c9_txt = "ID 2 (Tipo A Superinmunizado 30mA)" if n_difs > 1 else "ID 1 (Tipo A Superinmunizado 30mA)"
            if "Multi-Split" in tipo_c9:
                p_c9_1 = int(round(pot_c9 / 2))
                p_c9_2 = pot_c9 - p_c9_1
                circuitos_unifilar.extend([
                    {
                        "id": "C9.1",
                        "denominacion": "Climatización Inverter - Zona Día (Tipo A SI)",
                        "pia": 25,
                        "dif": dif_c9_txt,
                        "cable_sec": "2x6 + TT 6 mm² Cu",
                        "tubo_diam": "M25 (Tubo Corrugado)",
                        "long_m": 15.0,
                        "cdt_pct": 1.10,
                        "pot_w": p_c9_1
                    },
                    {
                        "id": "C9.2",
                        "denominacion": "Climatización Inverter - Zona Noche (Tipo A SI)",
                        "pia": 25,
                        "dif": dif_c9_txt,
                        "cable_sec": "2x6 + TT 6 mm² Cu",
                        "tubo_diam": "M25 (Tubo Corrugado)",
                        "long_m": 18.0,
                        "cdt_pct": 1.25,
                        "pot_w": p_c9_2
                    }
                ])
            else:
                es_split = "Split Individual" in tipo_c9
                circuitos_unifilar.append({
                    "id": "C9",
                    "denominacion": f"Aire Acondicionado / Clima Inverter ({tipo_c9.split('(')[0].strip()})",
                    "pia": 16 if es_split else 25,
                    "dif": dif_c9_txt,
                    "cable_sec": "2x2.5 + TT 2.5 mm² Cu" if es_split else "2x6 + TT 6 mm² Cu",
                    "tubo_diam": "M20 (Tubo Corrugado)" if es_split else "M25 (Tubo Corrugado)",
                    "long_m": 16.0,
                    "cdt_pct": 1.15,
                    "pot_w": pot_c9
                })

        # Circuito C10 Secadora independiente (si grado Elevada)
        if grado_electr == "Elevada":
            circuitos_unifilar.append({
                "id": "C10",
                "denominacion": "Instalación de secadora independiente",
                "pia": 16,
                "dif": f"ID {min(n_difs, 2)} (30mA)",
                "cable_sec": "2x2.5 + TT 2.5 mm² Cu",
                "tubo_diam": "M20 (Tubo Corrugado)",
                "long_m": 12.0,
                "cdt_pct": 0.88,
                "pot_w": 3450
            })

        # Circuito C11 Domótica y Automatización (si activado)
        if tipo_domotica != "Sin Domótica":
            es_knx = "KNX" in tipo_domotica
            desc_dom = "Bus KNX / Centralizada" if es_knx else "Domótica Inalámbrica / Micromódulos"
            dif_dom = f"ID {min(n_difs, 3)} (30mA)" if n_difs > 2 else ("ID 2 (30mA)" if n_difs > 1 else "ID 1 (30mA)")
            circuitos_unifilar.append({
                "id": "C11",
                "denominacion": f"Sistema de Domótica y Automatización ({desc_dom})",
                "pia": 10,
                "dif": dif_dom,
                "cable_sec": "2x1.5 + TT 1.5 mm² Cu (+ Bus apantallado)" if es_knx else "2x1.5 + TT 1.5 mm² Cu (+ Neutro azul)",
                "tubo_diam": "M20 Independiente (Bus)" if es_knx else "M20 (Tubo Corrugado)",
                "long_m": 20.0,
                "cdt_pct": 0.65,
                "pot_w": 1500
            })

        unifilar_data = {
            "potencia_w": pot_w_val,
            "iga_amperaje": iga_amperaje,
            "grado_electr": grado_electr,
            "tipo_cable": tipo_cable_sel,
            "tipo_tubo": tipo_tubo_sel,
            "marca_protecciones": marca_protecciones,
            "n_difs": n_difs,
            "circuitos": circuitos_unifilar
        }

        # Generar PDF del Esquema Unifilar Oficial para Industria
        pdf_unifilar_bytes = pdf_presupuesto.generar_pdf_unifilar_industria(
            proyecto_info={
                "empresa": empresa_nombre,
                "proyectista": instalador_nombre,
                "licencia": n_licencia,
                "localidad": localidad,
                "telefono": telefono,
                "expediente": "MTD-2026-01",
                "fecha": datetime.date.today().strftime("%d/%m/%Y")
            },
            unifilar_data=unifilar_data
        )

        # ==========================================
        # SECCIÓN 6: SELECTOR DE MODO DE VISTA E IMPRESIÓN
        # ==========================================
        with tab_sec6:
            st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">🖨️ SECCIÓN 6: Selector de Documentos Oficiales y Paneles de Resultados</h4></div>', unsafe_allow_html=True)

            if items_no_catalogados:
                with st.expander(f"⚠️ Alerta de Catálogo: Hay {len(items_no_catalogados)} artículo(s) sin registrar en el Excel de precios (Calculados con tarifa estimada)", expanded=False):
                    st.warning("Los siguientes artículos no se encontraron con referencia exacta en `base_datos_precio_oficial.xlsx`. El sistema les ha asignado una tarifa estimada de mercado para no paralizar tu presupuesto:")
                    for it_nc in items_no_catalogados:
                        st.markdown(f"- 🔸 **{it_nc['articulo']}**: `{it_nc['precio_unitario']:.2f} €/{it_nc.get('unidad', 'ud')}` *(Tarifa estimada)*")
                    st.info("💡 **¿Cómo registrarlos con su precio real?** Dirígete a la pestaña **`🛒 5. Orden de Compra y Acopio`** donde dispones del actualizador web en 1 clic y del formulario manual, o indícamelo en el chat y los incorporo directamente al archivo Excel.")

            tab_doc_com, tab_doc_auto, tab_doc_comp, tab_doc_int, tab_doc_oc, tab_doc_uni = st.tabs([
                "🏢 1. Presupuesto Empresa (PVP)",
                "🧑‍🔧 2. Presupuesto Autónomo / Tutor (Sin Margen MO)",
                "⚖️ 3. Comparativa Empresa vs Autónomo",
                "🛠️ 4. Panel Interno de Rendimiento",
                "🛒 5. Orden de Compra y Acopio",
                "📐 6. Esquema Unifilar Oficial (DGEAIM Murcia)"
            ])

            with tab_doc_com:
                st.header("📄 Vista Comercial: Presupuesto Oficial para el Cliente")
                st.markdown(f"""
                <div style="border: 2px solid {card_border}; padding: 20px; border-radius: 10px; background-color: {card_bg}; color: {card_text_color}; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="color: {card_title_color}; margin: 0;">{empresa_nombre}</h3>
                            <p style="margin: 3px 0; color: {card_text_color};"><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
                        </div>
                        <div style="text-align: right;">
                            <span style="background-color: #0284c7; color: white; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px;">OFERTA COMERCIAL</span>
                            <p style="margin: 4px 0 0 0; font-size: 13px; color: {card_text_color};"><b>Fecha:</b> {datetime.date.today().strftime("%d/%m/%Y")}</p>
                        </div>
                    </div>
                    <hr style="border: 1px solid {card_hr_color}; margin: 12px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px; color: {card_text_color};">
                        <div>• <b>Objeto:</b> Instalación Eléctrica Integral en Vivienda ({grado_electr})</div>
                        <div>• <b>Potencia Prevista / IGA:</b> {potencia_prevista_kw} ({pot_w_val} W)</div>
                        <div>• <b>Gama de Mecanismos:</b> {serie_mecanismos}</div>
                        <div>• <b>Aparamenta y Protecciones:</b> {marca_protecciones} (Curva C | 6 kA)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Resumen Económico KPI
                col_kpic1, col_kpic2, col_kpic3, col_kpic4 = st.columns(4)
                with col_kpic1:
                    st.metric("💶 Total Presupuesto (C/IVA)", f"{total_cliente:,.2f} €")
                with col_kpic2:
                    st.metric("📦 Base Imponible (S/IVA)", f"{subtotal_general_neto:,.2f} €")
                with col_kpic3:
                    st.metric(f"🧾 IVA ({iva_sel}%)", f"{cuota_iva:,.2f} €")
                with col_kpic4:
                    st.metric("🔌 Total Puntos / Ratio", f"{total_puntos_mecanismos} uds")
                    st.caption(f"**{precio_medio_por_punto_neto:,.2f} €/pto** S/IVA  \n**{precio_medio_por_punto:,.2f} €/pto** C/IVA")

                st.markdown("---")

                # =========================================================================
                # KIT INTELIGENTE DE DERIVACIÓN INDIVIDUAL (DI) - TARIFA DE CALLE & REBT
                # =========================================================================
                with st.expander("⚡ Kit Inteligente: Derivación Individual DI (ITC-BT-15) — Tarifa de Calle y Motor REBT", expanded=False):
                    st.markdown("""
                    **Calcula y cotiza la Derivación Individual con rigor de ingeniería y la realidad del instalador de calle:**  
                    Dimensiona automáticamente la sección de cobre (10 o 16 mm²), tubo reglamentario y caída de tensión según ITC-BT-15, aplicando la tarifa de mercado (tutor de prácticas: 200 - 250 € base sin rozas, suplementos por metros, sección y obra) con semáforo de rentabilidad en directo.
                    """)
                    
                    col_di_k1, col_di_k2, col_di_k3 = st.columns(3)
                    with col_di_k1:
                        di_k_long = st.number_input(
                            "Longitud DI (m):",
                            min_value=3.0,
                            max_value=80.0,
                            value=18.0,
                            step=1.0,
                            key="di_kit_long_in",
                            help="Distancia desde la centralización de contadores hasta el CGMP de la vivienda (habitual: 15 a 20 m)."
                        )
                        di_k_pot = st.number_input(
                            "Potencia Prevista (W):",
                            min_value=3450.0,
                            max_value=30000.0,
                            value=float(pot_w_val) if pot_w_val else 5750.0,
                            step=1150.0,
                            key="di_kit_pot_in",
                            help="Potencia contratada/prevista. 5.750 W (Básica) o 9.200 W (Elevada)."
                        )
                    with col_di_k2:
                        di_k_metodo_sel = st.selectbox(
                            "Método de Instalación:",
                            [
                                "Superficie bajo tubo con abrazaderas (Sin rozas)",
                                "Aprovecha tubo existente (Sustitución de conductores)",
                                "Empotrado con rozas en pared y tapado de yeso"
                            ],
                            index=0,
                            key="di_kit_metodo_sel"
                        )
                        metodo_clave = "existente" if "existente" in di_k_metodo_sel else ("roza" if "rozas" in di_k_metodo_sel else "superficie")
                        
                        di_k_entorno_sel = st.selectbox(
                            "Entorno de Trabajo:",
                            [
                                "Particular / Vivienda terminada",
                                "Obra nueva / Reforma integral (+20% coordinación)"
                            ],
                            index=0,
                            key="di_kit_entorno_sel"
                        )
                        es_obra_di = "Obra nueva" in di_k_entorno_sel
                    with col_di_k3:
                        di_k_boletin = st.checkbox("¿Incluir tramitación / ensayos CIE para la DI?", value=False, key="di_kit_chk_bol")
                        with st.popover("⚙️ Parámetros de Tarifa de Calle"):
                            p_base_20m_in = st.number_input("Precio base hasta 20 m (€):", min_value=150.0, max_value=400.0, value=225.0, step=10.0, key="di_kit_pbase")
                            p_m_extra_in = st.number_input("Metro extra > 20 m (€/m):", min_value=3.0, max_value=25.0, value=9.0, step=0.5, key="di_kit_pmextra")
                            suple_16_in = st.number_input("Suplemento si exige 16 mm² (€):", min_value=20.0, max_value=150.0, value=75.0, step=5.0, key="di_kit_s16")
                            suple_roza_in = st.number_input("Suplemento roza (€/m):", min_value=3.0, max_value=20.0, value=8.5, step=0.5, key="di_kit_sroza")

                    # Cotización y cálculo con módulo tarifas_obra
                    tarifa_di_calc = tarifas_obra.cotizar_tarifa_calle_di(
                        longitud_m=di_k_long,
                        potencia_w=di_k_pot,
                        es_trifasico=False,
                        metodo_montaje=metodo_clave,
                        es_obra=es_obra_di,
                        incluir_boletin=di_k_boletin,
                        precio_base_20m=p_base_20m_in,
                        precio_metro_extra=p_m_extra_in,
                        suple_16mm=suple_16_in,
                        suple_roza_m=suple_roza_in,
                        precio_hora_coste=precio_hora
                    )

                    tec_di = tarifa_di_calc["tecnica"]
                    coste_di = tarifa_di_calc["coste"]
                    pvp_di = tarifa_di_calc["pvp_venta_neto"]

                    col_rdi1, col_rdi2, col_rdi3 = st.columns(3)
                    with col_rdi1:
                        with st.container(border=True):
                            st.markdown("##### 📐 Ingeniería REBT (ITC-BT-15)")
                            st.markdown(f"- **Cable Fase + N:** `{int(tec_di['seccion_fase'])} mm² Cu RZ1-K CPR`")
                            st.markdown(f"- **Tierra PE + Mando:** `TT {int(tec_di['seccion_pe'])}mm² + 1x1.5mm² rojo`")
                            st.markdown(f"- **Tubo Protector:** `{tec_di['tubo_diam']} libre halógenos`")
                            st.markdown(f"- **Caída de Tensión:** `{tec_di['cdt_real_pct']:.2f}%` *(límite {tec_di['cdt_max_pct']}%)*")
                            st.markdown(f"- **Protección CGMP:** `IGA {tec_di['in_iga']} A Curva C`")

                    with col_rdi2:
                        with st.container(border=True):
                            st.markdown("##### 💼 Tarifa de Calle (A Cobrar)")
                            desg_di = tarifa_di_calc["desglose_tarifa"]
                            st.markdown(f"- **Base hasta 20m:** `{desg_di['base_20m']:.2f} €`")
                            if desg_di["importe_metros_extra"] > 0:
                                st.markdown(f"- **Metros extra ({desg_di['metros_extra']:.1f} m):** `+{desg_di['importe_metros_extra']:.2f} €`")
                            if desg_di["suple_seccion"] > 0:
                                st.markdown(f"- **Suplemento {int(tec_di['seccion_fase'])} mm²:** `+{desg_di['suple_seccion']:.2f} €`")
                            if desg_di["suple_rozas"] > 0:
                                st.markdown(f"- **Suplemento Rozas:** `+{desg_di['suple_rozas']:.2f} €`")
                            if desg_di["suple_obra"] > 0:
                                st.markdown(f"- **Recargo Obra:** `+{desg_di['suple_obra']:.2f} €`")
                            st.markdown(f"### **PVP Venta: {pvp_di:,.2f} €** *(S/IVA)*")

                    with col_rdi3:
                        with st.container(border=True):
                            st.markdown("##### ⚖️ Auditoría de Rentabilidad")
                            st.markdown(f"- **Coste Materiales:** `{coste_di['coste_materiales']:.2f} €`")
                            st.markdown(f"- **Coste Mano de Obra:** `{coste_di['coste_mo']:.2f} €` *({coste_di['horas_mo']:.1f} h)*")
                            st.markdown(f"- **Coste Real Directo:** `{coste_di['coste_directo_total']:.2f} €`")
                            st.markdown(f"- **Beneficio Neto Instalador:** `+{tarifa_di_calc['beneficio_neto']:.2f} €`")
                            st.markdown(f"<div style='font-size:16px; font-weight:bold; color:{tarifa_di_calc['color_hex']}; margin-top:4px;'>{tarifa_di_calc['semaforo']} ({tarifa_di_calc['margen_sobre_venta_pct']:.1f}%)</div>", unsafe_allow_html=True)

                    if tarifa_di_calc["margen_sobre_venta_pct"] < 12.0:
                        st.warning(f"⚠️ **Aviso de Rentabilidad:** {tarifa_di_calc['diagnostico']}")
                    else:
                        st.success(f"✅ **Evaluación:** {tarifa_di_calc['diagnostico']}")

                    if st.button("📥 Incorporar Derivación Individual al Presupuesto", type="primary", key="btn_add_di_presupuesto"):
                        partida_di_creada = tarifas_obra.generar_partida_presupuesto_di(tarifa_di_calc)
                        partida_di_creada["id"] = f"PM-{len(st.session_state.partidas_manuales) + 1:02d}"
                        st.session_state.partidas_manuales.append(partida_di_creada)
                        st.session_state.presupuesto_calculado = True
                        st.success(f"✅ Partida '{partida_di_creada['concepto']}' añadida con éxito (+{pvp_di:.2f} €)")
                        st.rerun()

                st.markdown("---")

                # =========================================================================
                # GESTOR INTERACTIVO DE TRABAJOS ADICIONALES Y PARTIDAS MANUALES
                # =========================================================================
                with st.expander("➕ 🛠️ GESTOR DE TRABAJOS, REDACTOR IA Y CATÁLOGO DE PARTIDAS (LGA, DI, Puesta a Tierra, IRVE...)", expanded=True):
                    st.markdown("""
                    **Personaliza la oferta para el cliente:**  
                    Añade partidas a medida (ej. downlights LED, punto de recarga de coche eléctrico IRVE, tomas exteriores IP65, timbres, etc.) con recálculo automático del total comercial:
                    """)

                    tab_p_ia, tab_p_plantilla, tab_p_target = st.tabs([
                        "🪄 1. Redactor con IA (Lenguaje Natural)",
                        "📌 2. Catálogo de Trabajos / Plantillas Oficiales",
                        "🎯 3. Ajustador a Presupuesto Objetivo del Cliente"
                    ])

                    # -------------------------------------------------------------
                    # SUB-PESTAÑA 1: ASISTENTE REDACTOR DE PARTIDAS CON IA
                    # -------------------------------------------------------------
                    with tab_p_ia:
                        st.markdown("##### 🤖 Asistente Redactor Técnico de Partidas (Inteligencia Artificial):")
                        st.caption("Escribe lo que pide el cliente con tus palabras (o usa el micro) y la IA redactará la descripción técnica conforme a la ITC correspondiente y sugerirá el precio:")

                        col_ia_in1, col_ia_in2 = st.columns([3, 1])
                        with col_ia_in1:
                            txt_ia_prompt = st.text_input(
                                "Describe el trabajo en lenguaje de calle:",
                                placeholder="Ej: Poner línea para depuradora con reloj y automático en garaje, o separar aire acondicionado",
                                key="txt_ia_trabajo_prompt"
                            )
                        with col_ia_in2:
                            btn_pedir_ia = st.button("🪄 Redactar Partida", type="primary", key="btn_ejecutar_redactor_ia")

                        if btn_pedir_ia and txt_ia_prompt:
                            # Motor de redacción técnica inteligente (Online Gemini o Base Experta REBT Offline)
                            import re
                            p_lower = txt_ia_prompt.lower()
                            
                            ai_concepto = "Trabajo Eléctrico Especializado a Medida"
                            ai_descripcion = f"Ejecución de trabajos según especificaciones del cliente conforme al REBT (RD 842/2002), con cable libre de halógenos y conexionado protegido."
                            ai_cantidad = 1.0
                            ai_unidad = "partida"
                            ai_pvp = 120.0

                            # Razonamiento técnico por patrones y normativa
                            if "depuradora" in p_lower or "piscina" in p_lower:
                                ai_concepto = "Línea Dedicada para Depuradora de Piscina con Reloj Horario (ITC-BT-31)"
                                ai_descripcion = "Tendido de línea bajo tubo M25 libre de halógenos con cable Cu 3x2.5 mm², suministro e instalación de reloj programador horario modular en cuadro, contactor de maniobra y PIA 16A Curva C."
                                ai_pvp = 245.0
                            elif "aire" in p_lower or "clima" in p_lower or "split" in p_lower:
                                ai_concepto = "Circuito Independiente Climatización C9 bajo Tubo/Canaleta (ITC-BT-25)"
                                ai_descripcion = "Instalación de línea de alimentación directa desde CGMP con cable Cu 3x2.5 mm² libre de halógenos, PIA de 16A, protección diferencial superinmunizada y base de conexión en pared."
                                ai_pvp = 185.0
                            elif "patinete" in p_lower or "moto" in p_lower or "bici" in p_lower:
                                ai_concepto = "Toma Reforzada Modo 2 para Recarga de Vehículo Ligero (ITC-BT-52)"
                                ai_descripcion = "Tendido de circuito dedicado desde cuadro con cable Cu 3x4 mm² bajo tubo rígido/libre de halógenos, base Schuko 16A reforzada con llave/tapa estanca y PIA 16A."
                                ai_pvp = 195.0
                            elif "cuadro" in p_lower or "automático" in p_lower or "salta" in p_lower:
                                ai_concepto = "Reforma y Reorganización de Cuadro de Protección CGMP"
                                ai_descripcion = "Desmontaje de elementos obsoletos, peinado y rotulación de líneas, instalación de diferencial superinmunizado clase A y reorganización de circuitos interiores."
                                ai_pvp = 220.0
                            elif "tierra" in p_lower or "pica" in p_lower or "derivación" in p_lower:
                                ai_concepto = "Instalación de Red de Tierra con Pica de Cobre (ITC-BT-18)"
                                ai_descripcion = "Hincado de pica de puesta a tierra 2m x 14mm, arqueta de registro con borne de desconexión y cable Cu 35 mm² con comprobación de resistencia de tierra."
                                ai_pvp = 145.0
                            elif "led" in p_lower or "luz" in p_lower or "foco" in p_lower:
                                ai_concepto = "Suministro e Instalación de Focos Downlight LED"
                                ai_descripcion = "Perforación en falso techo, conexionado de drivers y montaje de luminarias LED extraplanas 18W luz neutra 4000K con alta eficiencia energética."
                                ai_cantidad = 4.0
                                ai_unidad = "ud"
                                ai_pvp = 38.0
                            else:
                                ai_concepto = f"Instalación Eléctrica Adaptada: {txt_ia_prompt[:35]}"
                                ai_descripcion = f"Suministro de materiales y mano de obra para {txt_ia_prompt}. Incluye canalización protegida, conexionado y pruebas reglamentarias según REBT."
                                ai_pvp = 150.0

                            st.session_state["tmp_ai_conc"] = ai_concepto
                            st.session_state["tmp_ai_desc"] = ai_descripcion
                            st.session_state["tmp_ai_cant"] = ai_cantidad
                            st.session_state["tmp_ai_unid"] = ai_unidad
                            st.session_state["tmp_ai_pvp"] = ai_pvp

                        if "tmp_ai_conc" in st.session_state:
                            st.success("✨ **Propuesta Técnica Redactada por la IA:**")
                            col_aiv1, col_aiv2 = st.columns([3, 1])
                            with col_aiv1:
                                f_ai_c = st.text_input("Concepto redactado:", value=st.session_state["tmp_ai_conc"], key="f_ai_c")
                                f_ai_d = st.text_area("Descripción oficial reglamentaria:", value=st.session_state["tmp_ai_desc"], key="f_ai_d")
                            with col_aiv2:
                                f_ai_cnt = st.number_input("Cantidad:", value=float(st.session_state.get("tmp_ai_cant", 1.0)), min_value=0.1, step=1.0, key="f_ai_cnt")
                                f_ai_u = st.selectbox("Unidad:", ["partida", "ud", "m", "punto", "h"], index=0, key="f_ai_u")
                                f_ai_p = st.number_input("PVP Sugerido (€):", value=float(st.session_state.get("tmp_ai_pvp", 120.0)), step=10.0, format="%.2f", key="f_ai_p")

                            if st.button("➕ Incorporar esta Propuesta de la IA al Presupuesto", type="primary", key="btn_add_ai_partida"):
                                sub_ai = round(float(f_ai_cnt) * float(f_ai_p), 2)
                                st.session_state.partidas_manuales.append({
                                    "id": f"PM-{len(st.session_state.partidas_manuales) + 1:02d}",
                                    "concepto": f_ai_c,
                                    "descripcion": f_ai_d,
                                    "cantidad": float(f_ai_cnt),
                                    "unidad": f_ai_u,
                                    "precio_unitario": float(f_ai_p),
                                    "subtotal": sub_ai
                                })
                                st.session_state.presupuesto_calculado = True
                                st.success(f"✅ Partida '{f_ai_c}' añadida con éxito (+{sub_ai:.2f} €)")
                                st.session_state.pop("tmp_ai_conc", None)
                                st.rerun()

                    # -------------------------------------------------------------
                    # SUB-PESTAÑA 2: CATÁLOGO DE TRABAJOS Y PLANTILLAS
                    # -------------------------------------------------------------
                    with tab_p_plantilla:
                        preset_opciones = [
                            "Personalizada (Escribir concepto a medida)",
                            "Línea General de Alimentación LGA (ITC-BT-14)",
                            "Derivación Individual DI Completa (ITC-BT-15)",
                            "Instalación de Puesta a Tierra y Pica de Cobre (ITC-BT-18)",
                            "Sustitución / Reforma Integral de Cuadro CGMP Antiguo",
                            "Línea de Recarga Vehículo Eléctrico IRVE (ITC-BT-52)",
                            "Instalación Solar Fotovoltaica Autoconsumo AC/DC (ITC-BT-40)",
                            "Acometida Eléctrica y Caja General de Protección CGP (ITC-BT-13)",
                            "Línea Coaxial TV y Distribución RTV Adicional (ICT-2)",
                            "Red Cableada Datos Ethernet UTP Cat.6 Adicional (ICT-2)",
                            "Instalación Downlights LED Extraplanos 18W",
                            "Toma de Corriente Estanca IP65 en Terraza / Exterior",
                            "Instalación de Timbre / Zumbador Modular en Cuadro",
                            "Canaleta embellecedora y acometida auxiliar",
                            "Detector de Movimiento / Presencia 360° Techo",
                            "Tramitación Oficial Boletín CIE DGEAIM Murcia (Suelto)"
                        ]
                        preset_sel = st.selectbox("📌 Seleccionar Plantilla o Crear Partida Personalizada:", preset_opciones, key="sel_preset_partida")

                        def_conc = ""
                        def_desc = ""
                        def_cant = 1.0
                        def_unid = "ud"
                        def_pvp = 50.0

                        if "Derivación" in preset_sel or "DI" in preset_sel:
                            def_conc = "Derivación Individual DI Monofásica (ITC-BT-15)"
                            def_desc = "Tendido de DI con cables RZ1-K 0.6/1kV CPR libre de halógenos (2x10mm² + TT 1x10mm² + mando 1.5mm²), tubo M40 libre de halógenos 750N y conexiones."
                            def_cant = 1.0
                            def_unid = "partida"
                            def_pvp = 225.0
                        elif "IRVE" in preset_sel:
                            def_conc = "Línea de Alimentación IRVE para Vehículo Eléctrico (ITC-BT-52)"
                            def_desc = "Tendido de línea dedicada desde CGMP con cable libre de halógenos 3x6mm², tubo M25, IGA 32A y diferencial superinmunizado clase A."
                            def_cant = 1.0
                            def_unid = "partida"
                            def_pvp = 450.0
                        elif "Downlight" in preset_sel:
                            def_conc = "Suministro e Instalación de Downlights LED Extraplanos 18W"
                            def_desc = "Apertura de huecos en falso techo, conexionado y montaje de downlights LED redondos 18W 4000K alta luminosidad."
                            def_cant = 6.0
                            def_unid = "ud"
                            def_pvp = 38.0
                        elif "IP65" in preset_sel:
                            def_conc = "Toma de Corriente de Superficie Estanca IP65"
                            def_desc = "Suministro e instalación de base de enchufe estanca 16A 2P+T IP65 con tapa para zonas exteriores/terraza."
                            def_cant = 2.0
                            def_unid = "ud"
                            def_pvp = 45.0
                        elif "Timbre" in preset_sel:
                            def_conc = "Instalación de Timbre / Zumbador Modular"
                            def_desc = "Suministro y cableado de pulsador en puerta de entrada y zumbador modular 230V integrado en cuadro eléctrico."
                            def_cant = 1.0
                            def_unid = "ud"
                            def_pvp = 55.0
                        elif "Canaleta" in preset_sel:
                            def_conc = "Canaleta Embellecedora Decorativa y Derivación"
                            def_desc = "Instalación de canaleta blanca sin halógenos para distribución vista sin obra."
                            def_cant = 5.0
                            def_unid = "m"
                            def_pvp = 18.0
                        elif "LGA" in preset_sel or "General de Alimentación" in preset_sel:
                            def_conc = "Línea General de Alimentación LGA Centralizada (ITC-BT-14)"
                            def_desc = "Suministro e instalación de conductores unipolares de cobre RZ1-K 0.6/1kV CPR libre de halógenos bajo canal protectora/tubo desde CGP hasta centralización de contadores."
                            def_cant = 1.0
                            def_unid = "partida"
                            def_pvp = 650.0
                        elif "Puesta a Tierra" in preset_sel or "Pica" in preset_sel:
                            def_conc = "Instalación de Red de Puesta a Tierra con Pica de Cobre (ITC-BT-18)"
                            def_desc = "Hincado de pica de acero-cobre de 2m x 14mm, arqueta de registro con puente de prueba y cable de tierra desnudo Cu 35 mm² / aislado 16 mm² con medición de resistencia Rt."
                            def_cant = 1.0
                            def_unid = "ud"
                            def_pvp = 145.0
                        elif "Reforma Integral de Cuadro" in preset_sel or "Sustitución" in preset_sel:
                            def_conc = "Sustitución Integral de Cuadro Eléctrico Antiguo por CGMP Normalizado"
                            def_desc = "Desmontaje de cuadro antiguo, instalación de envolvente empotrada con IGA, POP+DPS sobretensiones, diferenciales 40A/30mA y PIAs magnetotérmicos con conexionado, peinado y pruebas."
                            def_cant = 1.0
                            def_unid = "ud"
                            def_pvp = 380.0
                        elif "Solar" in preset_sel or "Fotovoltaica" in preset_sel:
                            def_conc = "Cuadro de Protecciones y Enlace Solar Fotovoltaica (ITC-BT-40)"
                            def_desc = "Instalación de cuadro de protecciones DC (fusibles gPV 1000V + DPS) y AC (PIA + diferencial superinmunizado clase A) con cableado solar H1Z2Z2-K y conexionado a red interior."
                            def_cant = 1.0
                            def_unid = "partida"
                            def_pvp = 480.0
                        elif "Acometida" in preset_sel or "CGP" in preset_sel:
                            def_conc = "Instalación / Reforma de Caja General de Protección CGP (ITC-BT-13)"
                            def_desc = "Montaje de CGP normalizada según compañía distribuidora, con bases seccionables BUC y fusibles de protección tipo cuchilla NH-00."
                            def_cant = 1.0
                            def_unid = "ud"
                            def_pvp = 240.0
                        elif "Coaxial" in preset_sel:
                            def_conc = "Tendido de Línea Coaxial RG6 y Toma TV-SAT Adicional (ICT-2)"
                            def_desc = "Tendido de cable coaxial RG6 Cu/Cu alta cobertura desde repartidor PAU en RTR hasta nueva toma de usuario TV-FM/SAT con conector F."
                            def_cant = 1.0
                            def_unid = "punto"
                            def_pvp = 48.0
                        elif "Ethernet" in preset_sel or "Datos" in preset_sel:
                            def_conc = "Tendido de Cable de Red UTP Cat.6 y Toma RJ45 Adicional (ICT-2)"
                            def_desc = "Tendido de cable UTP Cat.6 LSZH desde cuadro RTR hasta estancia, crimpado y conectorización de toma mural RJ45 con certificación de continuidad."
                            def_cant = 1.0
                            def_unid = "punto"
                            def_pvp = 52.0
                        elif "Boletín" in preset_sel or "CIE" in preset_sel:
                            def_conc = "Tramitación Oficial de Certificado de Instalación Eléctrica (CIE / Boletín)"
                            def_desc = "Ensayos ITC-BT-05 (aislamiento, disparo diferencial y continuidad), redacción de MTD y tramitación telemática con pago de tasas ante DGEAIM de Murcia."
                            def_cant = 1.0
                            def_unid = "ud"
                            def_pvp = 150.0
                        elif "Detector" in preset_sel:
                            def_conc = "Detector de Presencia PIR 360° Techo"
                            def_desc = "Instalación de sensor crepuscular y de movimiento para encendido automático en pasillos/zonas comunes."
                            def_cant = 1.0
                            def_unid = "ud"
                            def_pvp = 68.0

                        with st.form("form_nueva_partida_manual"):
                            col_pm1, col_pm2 = st.columns([3, 4])
                            with col_pm1:
                                p_nom = st.text_input("Concepto / Título de la Partida:", value=def_conc, placeholder="Ej: Instalación Downlight LED")
                            with col_pm2:
                                p_desc = st.text_input("Descripción y Alcance Técnico:", value=def_desc, placeholder="Ej: Suministro y montaje con conexionado")

                            col_pm3, col_pm4, col_pm5 = st.columns(3)
                            with col_pm3:
                                p_cant = st.number_input("Cantidad:", min_value=0.1, value=float(def_cant), step=1.0, format="%.1f")
                            with col_pm4:
                                unidades_lista = ["ud", "m", "partida", "punto", "h", "pack"]
                                idx_unid = unidades_lista.index(def_unid) if def_unid in unidades_lista else 0
                                p_unid = st.selectbox("Unidad de Medida:", unidades_lista, index=idx_unid)
                            with col_pm5:
                                p_pvp_u = st.number_input("PVP Unitario S/IVA (€):", min_value=0.0, value=float(def_pvp), step=5.0, format="%.2f")

                            btn_add_partida = st.form_submit_button("➕ Añadir Partida al Presupuesto", type="primary")
                            if btn_add_partida:
                                if p_nom:
                                    sub_pm = round(float(p_cant) * float(p_pvp_u), 2)
                                    st.session_state.partidas_manuales.append({
                                        "id": f"PM-{len(st.session_state.partidas_manuales) + 1:02d}",
                                        "concepto": p_nom,
                                        "descripcion": p_desc,
                                        "cantidad": float(p_cant),
                                        "unidad": p_unid,
                                        "precio_unitario": float(p_pvp_u),
                                        "subtotal": sub_pm
                                    })
                                    st.session_state.presupuesto_calculado = True
                                    st.success(f"✅ Partida '{p_nom}' añadida con éxito (+{sub_pm:.2f} €)")
                                    st.rerun()

                    # -------------------------------------------------------------
                    # SUB-PESTAÑA 3: AJUSTADOR A PRESUPUESTO OBJETIVO (CON IVA O SIN IVA)
                    # -------------------------------------------------------------
                    with tab_p_target:
                        st.markdown("##### 🎯 Ajustar a Presupuesto Objetivo de Venta (Negociación Comercial):")
                        st.caption("Negocia con el cliente en precio cerrado ya sea **Base Imponible (Sin IVA)** o **Total Factura (Con IVA)**:")

                        modo_ajuste_iva = st.radio(
                            "Modalidad de Negociación del Precio Objetivo:",
                            [
                                "💰 Precio Objetivo CON IVA (Total a pagar por cliente particular)",
                                "💼 Precio Objetivo SIN IVA / Base Imponible (Facturación entre empresas / autónomos / subcontrata)"
                            ],
                            index=0,
                            key="rad_modo_ajuste_iva"
                        )
                        es_modo_con_iva = "CON IVA" in modo_ajuste_iva

                        col_tar1, col_tar2 = st.columns([2, 2])
                        with col_tar1:
                            if es_modo_con_iva:
                                target_val = st.number_input(
                                    "Total Objetivo Deseado (CON IVA €):",
                                    min_value=50.0,
                                    value=float(round(total_cliente, 2)),
                                    step=50.0,
                                    format="%.2f",
                                    key="num_target_civa_in",
                                    help="Importe final cerrado con impuestos incluidos."
                                )
                                actual_ref = total_cliente
                                dif_objetivo = target_val - actual_ref
                                sub_dif_siva = round(dif_objetivo / (1 + (iva_sel / 100.0)), 2)
                                txt_ref_actual = f"Presupuesto Actual (C/IVA): {actual_ref:,.2f} €"
                                txt_target_desc = f"precio cerrado de {target_val:,.2f} € (IVA incl.)"
                            else:
                                target_val = st.number_input(
                                    "Total Objetivo Deseado (SIN IVA / Base Imponible €):",
                                    min_value=50.0,
                                    value=float(round(subtotal_general_neto, 2)),
                                    step=50.0,
                                    format="%.2f",
                                    key="num_target_siva_in",
                                    help="Base imponible antes de impuestos (inversión de sujeto pasivo o empresa)."
                                )
                                actual_ref = subtotal_general_neto
                                dif_objetivo = target_val - actual_ref
                                sub_dif_siva = round(dif_objetivo, 2)
                                txt_ref_actual = f"Base Imponible Actual (S/IVA): {actual_ref:,.2f} €"
                                txt_target_desc = f"precio cerrado de {target_val:,.2f} € (Sin IVA / Base Imponible)"

                        with col_tar2:
                            pct_dif_obj = (dif_objetivo / actual_ref * 100.0) if actual_ref > 0 else 0.0
                            color_obj = "#10b981" if dif_objetivo >= 0 else "#f59e0b"
                            st.markdown(f"""
                            <div style="background-color: #f8fafc; border: 1.5px solid {color_obj}; border-radius: 8px; padding: 10px; margin-top: 5px;">
                                <div style="font-size: 13px; color: #475569;"><b>{txt_ref_actual}</b></div>
                                <div style="font-size: 14px; color: {color_obj}; font-weight: bold; margin-top: 2px;">
                                    Diferencia a Ajustar: {dif_objetivo:+,.2f} € ({pct_dif_obj:+.1f}%)
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        if abs(dif_objetivo) >= 1.0:
                            tipo_ajuste_btn = "Bonificación / Descuento" if dif_objetivo < 0 else "Partida de Ajuste / Incremento"
                            if st.button(f"⚖️ Aplicar Ajuste Automático al Presupuesto ({sub_dif_siva:+,.2f} € S/IVA)", type="primary", key="btn_apply_target_partida"):
                                st.session_state.partidas_manuales.append({
                                    "id": f"PM-{len(st.session_state.partidas_manuales) + 1:02d}",
                                    "concepto": "Ajuste Comercial / Descuento Negociado en Obra",
                                    "descripcion": f"Ajuste comercial acordado con el cliente para {txt_target_desc}",
                                    "cantidad": 1.0,
                                    "unidad": "partida",
                                    "precio_unitario": sub_dif_siva,
                                    "subtotal": sub_dif_siva
                                })
                                st.session_state.presupuesto_calculado = True
                                st.success(f"✅ Ajuste de {sub_dif_siva:+,.2f} € (S/IVA) aplicado con éxito al presupuesto!")
                                st.rerun()

                    # -------------------------------------------------------------
                    # PANEL EDITABLE INTERACTIVO DE PARTIDAS EXISTENTES
                    # -------------------------------------------------------------
                    if st.session_state.get('partidas_manuales', []):
                        st.markdown("---")
                        st.markdown("##### ✏️ Panel de Partidas Incorporadas (Totalmente Editables en Vivo):")
                        st.caption("Puedes modificar el título, cantidad o precio unitario de cada partida directamente:")

                        hubo_cambios_partidas = False
                        for idx_p, item_p in enumerate(st.session_state.partidas_manuales):
                            with st.container(border=True):
                                col_ed1, col_ed2, col_ed3, col_ed4, col_ed5 = st.columns([3, 1.2, 1.5, 1.5, 0.8])
                                with col_ed1:
                                    n_conc = st.text_input(f"Concepto {idx_p+1}:", value=item_p.get("concepto", ""), key=f"ed_conc_{idx_p}", label_visibility="collapsed")
                                    n_desc = st.text_input(f"Descripción {idx_p+1}:", value=item_p.get("descripcion", ""), key=f"ed_desc_{idx_p}", label_visibility="collapsed")
                                with col_ed2:
                                    n_cant = st.number_input(f"Cant {idx_p+1}:", value=float(item_p.get("cantidad", 1.0)), min_value=0.1, step=1.0, key=f"ed_cant_{idx_p}", label_visibility="collapsed")
                                with col_ed3:
                                    n_pu = st.number_input(f"PVP Unit {idx_p+1} (€):", value=float(item_p.get("precio_unitario", 0.0)), step=5.0, format="%.2f", key=f"ed_pu_{idx_p}", label_visibility="collapsed")
                                with col_ed4:
                                    sub_calc_ed = round(n_cant * n_pu, 2)
                                    st.markdown(f"<div style='margin-top: 8px; font-weight: bold; color: #0284c7;'>{sub_calc_ed:,.2f} €</div>", unsafe_allow_html=True)
                                with col_ed5:
                                    if st.button("🗑️", key=f"btn_del_pm_{idx_p}", help="Eliminar partida"):
                                        st.session_state.partidas_manuales.pop(idx_p)
                                        st.session_state.presupuesto_calculado = True
                                        st.rerun()

                                if (n_conc != item_p.get("concepto") or 
                                    n_desc != item_p.get("descripcion") or 
                                    n_cant != item_p.get("cantidad") or 
                                    n_pu != item_p.get("precio_unitario")):
                                    item_p["concepto"] = n_conc
                                    item_p["descripcion"] = n_desc
                                    item_p["cantidad"] = n_cant
                                    item_p["precio_unitario"] = n_pu
                                    item_p["subtotal"] = round(n_cant * n_pu, 2)
                                    hubo_cambios_partidas = True

                        col_foot_p1, col_foot_p2 = st.columns([2, 2])
                        with col_foot_p1:
                            if hubo_cambios_partidas:
                                st.session_state.presupuesto_calculado = True
                                st.rerun()
                        with col_foot_p2:
                            if st.button("🧹 Vaciar Todas las Partidas Adicionales", key="btn_clear_all_pm"):
                                st.session_state.partidas_manuales = []
                                st.session_state.presupuesto_calculado = True
                                st.rerun()

                st.markdown("---")

                # =========================================================================
                # SECCIÓN 1: RESUMEN POR CAPÍTULOS REBT
                # =========================================================================
                st.subheader("1. 🏛️ Estructura por Capítulos REBT (Memoria Valorada Oficial)")
                df_cap_vista = pd.DataFrame([
                    {
                        "Capítulo": c["cap"],
                        "Denominación de la Partida": c["titulo"],
                        "Alcance Técnico de los Trabajos": c["desc"],
                        "Importe PVP (€)": f"{c['importe']:,.2f} €"
                    }
                    for c in capitulos_presupuesto
                ])
                st.dataframe(df_cap_vista, use_container_width=True, hide_index=True)

                st.markdown("---")

                # =========================================================================
                # SECCIÓN 2: DESGLOSE POR ESTANCIAS
                # =========================================================================
                st.subheader("2. 🚪 Desglose de Instalación por Estancias de la Vivienda")
                df_comercial = pd.DataFrame(comercial_estancias)
                st.dataframe(df_comercial, use_container_width=True, hide_index=True)

                st.markdown("---")

                # =========================================================================
                # SECCIÓN 3: CATÁLOGO DE MATERIALES VALORADOS A PVP
                # =========================================================================
                incluir_catalogo_pvp = st.checkbox(
                    "📋 Incluir catálogo y especificación de materiales principales valorados a PVP en la propuesta",
                    value=True,
                    key="chk_inc_mat_pvp"
                )

                if incluir_catalogo_pvp:
                    with st.expander("🔍 Ver Catálogo de Materiales Principales Valorados a PVP", expanded=False):
                        df_mat_pvp_vista = pd.DataFrame([
                            {
                                "Categoría": m["categoria"],
                                "Elemento": m["articulo"],
                                "Descripción y Gama": m["desc_exacta"],
                                "Cantidad": f"{m['cantidad']} {m['unidad']}",
                                "PVP Unitario": f"{m['pvp_unitario']:.2f} €",
                                "Subtotal PVP": f"{m['subtotal_pvp']:.2f} €"
                            }
                            for m in materiales_pvp
                        ])
                        st.dataframe(df_mat_pvp_vista, use_container_width=True, hide_index=True)
                        st.caption("🔒 *Nota de transparencia comercial:* Todos los importes unitarios mostrados corresponden al Precio de Venta al Público (PVP) con margen comercial de suministro y garantía oficial de reposición de 3 años incluidos.")

                # Generación de archivos Excel y PDF
                excel_bytes = exportar_excel_presupuesto(
                    df_comercial, subtotal_general_neto, iva_sel, cuota_iva, total_cliente,
                    {
                        "empresa": empresa_nombre,
                        "instalador": instalador_nombre,
                        "licencia": n_licencia,
                        "localidad": localidad,
                        "fecha": datetime.date.today().strftime("%d/%m/%Y")
                    },
                    df_orden_compra=df_orden_compra,
                    total_compra_neto=total_mat_global_neto,
                    total_compra_con_iva=total_mat_con_iva,
                    capitulos=capitulos_presupuesto,
                    partidas_manuales=st.session_state.get('partidas_manuales', []),
                    materiales_pvp=materiales_pvp if incluir_catalogo_pvp else None
                )

                pdf_bytes_pres = pdf_presupuesto.generar_pdf_presupuesto(
                    proyecto_info={
                        "empresa": empresa_nombre,
                        "proyectista": instalador_nombre,
                        "licencia": n_licencia,
                        "localidad": localidad,
                        "telefono": telefono,
                        "expediente": "PRES-2026-01",
                        "fecha": datetime.date.today().strftime("%d/%m/%Y")
                    },
                    presupuesto_data={
                        "capitulos": capitulos_presupuesto,
                        "df_comercial": df_comercial,
                        "partidas_manuales": st.session_state.get('partidas_manuales', []),
                        "materiales_pvp": materiales_pvp,
                        "incluir_catalogo_pvp": incluir_catalogo_pvp,
                        "subtotal_neto": subtotal_general_neto,
                        "iva_pct": iva_sel,
                        "cuota_iva": cuota_iva,
                        "total_cliente": total_cliente,
                        "total_puntos": total_puntos_mecanismos,
                        "precio_medio_punto": precio_medio_por_punto,
                        "precio_medio_punto_neto": precio_medio_por_punto_neto,
                        "serie_mecanismos": serie_mecanismos,
                        "marca_protecciones": marca_protecciones,
                        "potencia_kw": potencia_prevista_kw,
                        "grado_electr": grado_electr,
                        "plazo_dias": dias_estimados,
                        "num_operarios": num_operarios
                    }
                )

                st.markdown("---")
                st.markdown("#### 👁️ Vista Previa en Pantalla del Presupuesto Oficial en PDF:")
                st.info("💡 **Revisa el documento antes de imprimir o descargar.** El presupuesto incluye todos los capítulos reglamentarios, desglose por estancias, partidas a medida, condiciones y firmas:")

                with st.container():
                    try:
                        import pymupdf
                        doc = pymupdf.open(stream=pdf_bytes_pres, filetype="pdf")
                        for num_pag, pagina in enumerate(doc, start=1):
                            pix = pagina.get_pixmap(dpi=150)
                            if len(doc) > 1:
                                st.caption(f"📄 **Página {num_pag} de {len(doc)}**")
                            st.image(pix.tobytes("png"), use_container_width=True)
                    except Exception:
                        import base64
                        b64 = base64.b64encode(pdf_bytes_pres).decode('utf-8')
                        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="650" type="application/pdf"></iframe>', unsafe_allow_html=True)

                col_exp1, col_exp2, col_exp3 = st.columns(3)
                with col_exp1:
                    st.download_button(
                        label="📊 Descargar Presupuesto en Excel (.xlsx)",
                        data=excel_bytes,
                        file_name="Presupuesto_Electrico_Bolimur.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                with col_exp2:
                    st.download_button(
                        label="📄 🖨️ Descargar / Imprimir Presupuesto Oficial (PDF)",
                        data=pdf_bytes_pres,
                        file_name="Presupuesto_Oficial_Bolimur.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                with col_exp3:
                    st.download_button(
                        label="📐 Anexar Esquema Unifilar Oficial (PDF)",
                        data=pdf_unifilar_bytes,
                        file_name="Esquema_Unifilar_Industria_Bolimur.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                st.markdown(f"""
                <div style="border: 2px solid {card_border}; background: {card_bg}; border-radius: 10px; padding: 18px; margin: 18px 0 10px 0;">
                    <h4 style="color: {card_title_color}; margin: 0 0 8px 0;">🗺️ ¿Dónde se adjuntan los Planos de Situación, Emplazamiento y Esquema Unifilar?</h4>
                    <p style="color: {card_text_color}; margin: 0; font-size: 14px;">
                        Los planos oficiales (situación en callejero municipal, emplazamiento catastral y esquema unifilar oficial de la vivienda) se gestionan en el módulo oficial de <b>Memoria Técnica & Planos (MTD 30)</b>.<br/>
                        Al pulsar el botón inferior, todos los circuitos, potencias y datos de este presupuesto se transfieren automáticamente y se abrirá directamente el gestor de planos listo para subir tus archivos (PNG, JPG o PDF).
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🚀 Tramitar Memoria Técnica (MTD 30), Subir Planos y Tramitar CIE para esta Vivienda", type="primary", use_container_width=True):
                    st.session_state["mtd_in_pot_inst"] = float(pot_w_val)
                    st.session_state["mtd_in_pot_max"] = float(pot_w_val)
                    st.session_state["mtd_in_tension"] = "Monofásico (230 V) - 50 Hz"
                    st.session_state["mtd_in_origen"] = "Derivación Individual desde Centralización (ITC-BT-15)"
                    st.session_state["mtd_in_di_cable"] = f"2x10 mm² Cu + TT 1x10 mm² {tipo_cable_sel}"
                    st.session_state["mtd_in_di_tubo"] = "Tubo M32 libre de halógenos (ITC-BT-15)"
                    st.session_state["mtd_in_di_long"] = 15.0
                    st.session_state["mtd_in_di_cdt"] = 0.72
                    st.session_state["mtd_in_grado"] = grado_electr
                    st.session_state["mtd_in_iga"] = int(iga_amperaje)
                    st.session_state["mtd_in_curva"] = "Curva C (General)"
                    st.session_state["mtd_in_icn"] = 6.0
                    st.session_state["mtd_in_dif"] = f"{n_difs}x ID 2P 40A / 30mA Clase A / Superinmunizado"
                    st.session_state["mtd_in_vtp"] = "Permanentes (POP/VTP) + Transitorias Tipo 2 (DPS/VSP) con bobina de disparo"
                    st.session_state["mtd_in_tierra"] = "Conductor PE 1x10 mm² Cu | Picas en anillo Rt ≤ 15 Ω"
                    st.session_state["mtd_in_emp_uso"] = f"Vivienda Residencial ({grado_electr})"
                    st.session_state["mtd_circuitos"] = [
                        {
                            "nombre": f"{c['id']} - {c['denominacion']}",
                            "potencia": float(c['pot_w']),
                            "pia": int(c['pia']),
                            "seccion": str(c['cable_sec']),
                            "tubo": str(c['tubo_diam']),
                            "longitud": float(c['long_m']),
                            "cdt": float(round(c['cdt_pct'], 2)),
                            "norma": "ITC-BT-25"
                        }
                        for c in circuitos_unifilar
                    ]
                    st.session_state["mtd_tipo_inst_sel"] = "🏡 Vivienda Unifamiliar / Piso Residencial (ITC-BT-25)"
                    st.session_state["mtd_abrir_planos"] = True
                    st.session_state.menu_activo = "🏛️ Memoria Técnica (MTD 30)"
                    st.rerun()

                st.markdown(f"""
                <div style="text-align: right; font-size: 18px; background-color: {card_subtotal_bg}; color: {card_text_color}; padding: 18px; border-radius: 8px; border: 1.5px solid {card_border}; margin-top: 15px;">
                    <p style="margin: 3px 0; color: {card_text_color};"><b>Subtotal Comercial Neto (Base Imponible):</b> {subtotal_general_neto:,.2f} €</p>
                    <p style="margin: 3px 0; color: {card_text_color};"><b>IVA ({iva_sel}%):</b> {cuota_iva:,.2f} €</p>
                    <h2 style="color: #16a34a; margin: 8px 0 0 0;">TOTAL PRESUPUESTO CLIENTE: {total_cliente:,.2f} €</h2>
                </div>
                """, unsafe_allow_html=True)



            # =========================================================================
            # PESTAÑA 2: PRESUPUESTO OFICIAL MODO AUTÓNOMO (TUTOR - SIN MARGEN MO)
            # =========================================================================
            with tab_doc_auto:
                st.header("🧑‍🔧 Vista Comercial: Presupuesto Oficial Modo Autónomo / Tutor")
                st.info("""
                💡 **Oferta Comercial Sin Sobrecoste de Mano de Obra:**  
                A diferencia de una empresa con cuadrillas contratadas, el **instalador electricista autónomo (como tu tutor de prácticas)** realiza el trabajo personalmente. Su jornal íntegro queda completamente garantizado con el coste directo por hora ($C_{mo}$).  
                Al suprimir o graduar el margen empresarial de mano de obra ($G_{mo}$), puedes presentar al cliente un presupuesto mucho más competitivo y económico manteniendo íntegros tu jornal y los beneficios de los materiales.
                """)

                # Cálculos exactos para el autónomo
                c_mat = round(total_mat_global_neto, 2)
                m_seg = round(c_mat * (porc_garantia / 100.0), 2)
                c_mo = round(coste_mano_obra_bruto, 2)
                g_mo = round(c_mo * (margen_comercial / 100.0), 2)
                v_bol = round(float(precio_boletin_cie), 2)
                v_part = round(sum(float(p.get('subtotal', 0.0)) for p in st.session_state.get('partidas_manuales', [])), 2)
                u_mat = round(subtotal_general_neto - (c_mat + m_seg + c_mo + g_mo + v_bol + v_part), 2)
                base_calc = round(c_mat + m_seg + u_mat + c_mo + g_mo + v_bol + v_part, 2)
                cuota_iva_calc = round(base_calc * (iva_sel / 100.0), 2)
                total_calc = round(base_calc + cuota_iva_calc, 2)
                benef_total_empresa = round(m_seg + u_mat + g_mo + v_bol + v_part, 2)
                costes_directos_tot = round(c_mat + c_mo, 2)

                col_cauto1, col_cauto2 = st.columns([3, 2])
                with col_cauto1:
                    pct_margen_mo_auto = st.slider(
                        "🔧 % Margen Comercial sobre Mano de Obra ($G_{mo}$) para Autónomo:",
                        min_value=0.0,
                        max_value=float(max(margen_comercial, 50)),
                        value=0.0,
                        step=5.0,
                        format="%.0f%%",
                        key="slider_margen_mo_auto_pestaña",
                        help="0% = Modo Tutor Autónomo Puro (Solo cobra sus horas directas sin recargo adicional)."
                    )
                with col_cauto2:
                    st.markdown(f"""
                    <div style="background-color: {card_bg}; border: 1.5px solid #0284c7; border-radius: 8px; padding: 10px; margin-top: 5px;">
                        <div style="font-size: 13px; color: {card_text_color};"><b>Margen Empresa Original:</b> {margen_comercial:.0f}% (+{g_mo:,.2f} €)</div>
                        <div style="font-size: 13px; color: #0284c7; font-weight: bold; margin-top: 3px;"><b>Margen Autónomo Seleccionado:</b> {pct_margen_mo_auto:.0f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

                g_mo_auto = round(c_mo * (pct_margen_mo_auto / 100.0), 2)
                base_calc_auto = round(c_mat + m_seg + u_mat + c_mo + g_mo_auto + v_bol + v_part, 2)
                cuota_iva_auto = round(base_calc_auto * (iva_sel / 100.0), 2)
                total_calc_auto = round(base_calc_auto + cuota_iva_auto, 2)

                dif_base = round(base_calc - base_calc_auto, 2)
                dif_total = round(total_calc - total_calc_auto, 2)

                precio_pto_neto_auto = (base_calc_auto / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0
                precio_pto_total_auto = (total_calc_auto / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0
                ingreso_real_autonomo = round(c_mo + g_mo_auto + u_mat + m_seg + v_bol + v_part, 2)
                delta_pto = round(precio_medio_por_punto - precio_pto_total_auto, 2)

                # Tarjeta de Encabezado Oficial
                st.markdown(f"""
                <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: {card_bg}; color: {card_text_color}; margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="color: {card_title_color}; margin: 0;">{empresa_nombre}</h3>
                            <p style="margin: 3px 0; color: {card_text_color};"><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
                        </div>
                        <div style="text-align: right;">
                            <span style="background-color: #16a34a; color: white; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px;">OFERTA AUTÓNOMO (MODO TUTOR)</span>
                            <p style="margin: 4px 0 0 0; font-size: 13px; color: {card_text_color};"><b>Fecha:</b> {datetime.date.today().strftime("%d/%m/%Y")}</p>
                        </div>
                    </div>
                    <hr style="border: 1px solid {card_hr_color}; margin: 12px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px; color: {card_text_color};">
                        <div>• <b>Objeto:</b> Instalación Eléctrica en Vivienda ({grado_electr})</div>
                        <div>• <b>Potencia Prevista / IGA:</b> {potencia_prevista_kw} ({pot_w_val} W)</div>
                        <div>• <b>Gama de Mecanismos:</b> {serie_mecanismos}</div>
                        <div>• <b>Protecciones:</b> {marca_protecciones} (Curva C | 6 kA)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Tarjetas KPI
                col_akpi1, col_akpi2, col_akpi3, col_akpi4 = st.columns(4)
                with col_akpi1:
                    st.metric(
                        "💶 Total Cliente (C/IVA)",
                        f"{total_calc_auto:,.2f} €",
                        delta=f"-{dif_total:,.2f} € vs Empresa" if dif_total > 0 else None,
                        delta_color="inverse"
                    )
                    st.caption("Presupuesto final cliente")
                with col_akpi2:
                    st.metric(
                        "📦 Base Imponible (S/IVA)",
                        f"{base_calc_auto:,.2f} €",
                        delta=f"-{dif_base:,.2f} € Ahorro" if dif_base > 0 else None,
                        delta_color="inverse"
                    )
                    st.caption(f"Descuento: {(dif_base / base_calc * 100) if base_calc > 0 else 0:.1f}%")
                with col_akpi3:
                    delta_pto = precio_medio_por_punto - precio_pto_total_auto
                    st.metric(
                        "🔌 Tarifa por Punto",
                        f"{precio_pto_total_auto:.2f} €/pto",
                        delta=f"-{delta_pto:.2f} €/pto" if delta_pto > 0.01 else None,
                        delta_color="inverse"
                    )
                    st.caption(f"{precio_pto_neto_auto:.2f} €/pto S/IVA")
                with col_akpi4:
                    st.metric(
                        "💰 Ingreso Real Instalador",
                        f"+{ingreso_real_autonomo:,.2f} €",
                        help="Suma de tu jornal íntegro de mano de obra (C_mo), beneficio en materiales (U_mat), colchón de imprevistos (M_seg) y boletín CIE."
                    )
                    st.caption(f"Jornal MO ({c_mo:,.2f} €) + Beneficios")

                # Ecuaciones Matemáticas Autónomo
                col_aeq1, col_aeq2 = st.columns(2)
                with col_aeq1:
                    with st.container(border=True):
                        st.markdown("#### 1️⃣ Ecuación SIN IVA (Modo Autónomo)")
                        st.latex(r"\text{Cobro (S/IVA)} = C_{\text{mat}} + M_{\text{seg}} + U_{\text{mat}} + C_{\text{mo}} + G_{\text{mo}}^{\text{auto}} + \text{Extras}")
                        extra_txt_aeq = f" + {v_bol:,.2f}\text{{ €}}" + (f" + {v_part:,.2f}\text{{ €}}" if v_part > 0 else "")
                        st.markdown(f"""
                        $$\\underbrace{{{c_mat:,.2f}\text{{ €}}}}_{{C_{{mat}}}} + \\underbrace{{{m_seg:,.2f}\text{{ €}}}}_{{M_{{seg}}}} + \\underbrace{{{u_mat:,.2f}\text{{ €}}}}_{{U_{{mat}}}} + \\underbrace{{{c_mo:,.2f}\text{{ €}}}}_{{C_{{mo}}}} + \\underbrace{{{g_mo_auto:,.2f}\text{{ €}}}}_{{G_{{mo}}^{{\\text{{auto}}}}}}{extra_txt_aeq} = \\mathbf{{{base_calc_auto:,.2f}\text{{ €}}}}$$
                        """)
                        if pct_margen_mo_auto == 0:
                            st.caption("✅ **Modo Tutor Puro (0% sobrecoste MO):** Tu compensación es tu jornal directo ($C_{mo}$) por las horas trabajadas.")
                        else:
                            st.caption(f"✅ **Margen MO Personalizado ({pct_margen_mo_auto:.0f}%):** Ajuste comercial flexible.")

                with col_aeq2:
                    with st.container(border=True):
                        st.markdown("#### 2️⃣ Ecuación CON IVA (Modo Autónomo)")
                        st.latex(r"\text{Cobro (C/IVA)} = \text{Base}_{\text{auto}} \times \left(1 + \frac{\text{IVA}}{100}\right)")
                        st.markdown(f"""
                        $$\\mathbf{{{base_calc_auto:,.2f}\\text{{ €}}}} \\times \\left(1 + \\frac{{{iva_sel}}}{{100}}\\right) = \\mathbf{{{base_calc_auto:,.2f}\\text{{ €}}}} + \\mathbf{{{cuota_iva_auto:,.2f}\\text{{ €}}}} = \\mathbf{{{total_calc_auto:,.2f}\\text{{ €}}}}$$
                        """)
                        st.caption(f"✅ **Facturación Legal:** Cuota de IVA oficial ({iva_sel}%) conforme a la Agencia Tributaria.")

                # Generación del Presupuesto Oficial Modo Autónomo
                st.markdown("---")
                st.markdown("#### 📄 Documentos Oficiales Modo Autónomo para el Cliente:")

                capitulos_auto = []
                caps_obra = [c for c in capitulos_presupuesto if c.get("cap") in ["CAP. 01", "CAP. 02", "CAP. 03", "CAP. 04", "CAP. 05"]]
                suma_caps_obra = sum(c.get("importe", 0.0) for c in caps_obra)
                resto_fijo = sum(c.get("importe", 0.0) for c in capitulos_presupuesto if c.get("cap") not in ["CAP. 01", "CAP. 02", "CAP. 03", "CAP. 04", "CAP. 05"])
                nuevo_objetivo_obra = round(base_calc_auto - resto_fijo, 2)

                acum_obra_auto = 0.0
                idx_obra = 0
                for c_orig in capitulos_presupuesto:
                    c_dict = dict(c_orig)
                    if c_orig.get("cap") in ["CAP. 01", "CAP. 02", "CAP. 03", "CAP. 04", "CAP. 05"] and suma_caps_obra > 0:
                        idx_obra += 1
                        if idx_obra == len(caps_obra):
                            c_dict["importe"] = round(nuevo_objetivo_obra - acum_obra_auto, 2)
                        else:
                            prop = c_orig.get("importe", 0.0) / suma_caps_obra
                            c_imp_adj = round(nuevo_objetivo_obra * prop, 2)
                            acum_obra_auto += c_imp_adj
                            c_dict["importe"] = c_imp_adj
                    capitulos_auto.append(c_dict)

                df_comercial_auto = []
                total_est_orig = sum(float(r.get("Importe Venta (€)", 0.0)) for r in comercial_estancias)
                suma_est_nueva = sum(c["importe"] for c in capitulos_auto if c["cap"] in ["CAP. 02", "CAP. 03", "CAP. 04"])
                if total_est_orig > 0:
                    factor_est = suma_est_nueva / total_est_orig
                    for r_orig in comercial_estancias:
                        r_dict = dict(r_orig)
                        r_dict["Importe Venta (€)"] = round(float(r_orig.get("Importe Venta (€)", 0.0)) * factor_est, 2)
                        df_comercial_auto.append(r_dict)
                else:
                    df_comercial_auto = comercial_estancias

                pdf_bytes_auto = pdf_presupuesto.generar_pdf_presupuesto(
                    proyecto_info={
                        "empresa": empresa_nombre,
                        "proyectista": instalador_nombre,
                        "licencia": n_licencia,
                        "localidad": localidad,
                        "telefono": telefono,
                        "expediente": "PRES-AUTO-2026",
                        "fecha": datetime.date.today().strftime("%d/%m/%Y")
                    },
                    presupuesto_data={
                        "capitulos": capitulos_auto,
                        "df_comercial": df_comercial_auto,
                        "partidas_manuales": st.session_state.get('partidas_manuales', []),
                        "materiales_pvp": materiales_pvp,
                        "incluir_catalogo_pvp": incluir_catalogo_pvp,
                        "subtotal_neto": base_calc_auto,
                        "iva_pct": iva_sel,
                        "cuota_iva": cuota_iva_auto,
                        "total_cliente": total_calc_auto,
                        "total_puntos": total_puntos_mecanismos,
                        "precio_medio_punto": precio_pto_total_auto,
                        "precio_medio_punto_neto": precio_pto_neto_auto,
                        "serie_mecanismos": serie_mecanismos,
                        "marca_protecciones": marca_protecciones,
                        "potencia_kw": potencia_prevista_kw,
                        "grado_electr": grado_electr,
                        "plazo_dias": dias_estimados,
                        "num_operarios": num_operarios
                    }
                )

                excel_auto_bytes = exportar_excel_presupuesto(
                    df_comercial_auto, base_calc_auto, iva_sel, cuota_iva_auto, total_calc_auto,
                    {
                        "empresa": empresa_nombre,
                        "instalador": instalador_nombre,
                        "licencia": n_licencia,
                        "localidad": localidad,
                        "fecha": datetime.date.today().strftime("%d/%m/%Y")
                    },
                    df_orden_compra=df_orden_compra,
                    total_compra_neto=total_mat_global_neto,
                    total_compra_con_iva=total_mat_con_iva,
                    capitulos=capitulos_auto,
                    partidas_manuales=st.session_state.get('partidas_manuales', []),
                    materiales_pvp=materiales_pvp if incluir_catalogo_pvp else None
                )

                col_da1, col_da2 = st.columns(2)
                with col_da1:
                    st.download_button(
                        label="📄 🖨️ Descargar Presupuesto Oficial Modo Autónomo (PDF)",
                        data=pdf_bytes_auto,
                        file_name=f"Presupuesto_Oficial_Autonomo_{localidad.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        type="primary",
                        key="btn_descarga_pdf_auto_tab",
                        use_container_width=True
                    )
                with col_da2:
                    st.download_button(
                        label="📊 Descargar Oferta Modo Autónomo (Excel)",
                        data=excel_auto_bytes,
                        file_name=f"Presupuesto_Autonomo_{localidad.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="btn_descarga_excel_auto_tab",
                        use_container_width=True
                    )

                with st.expander("👁️ Vista Previa del PDF Oficial (Modo Autónomo)", expanded=True):
                    try:
                        import pymupdf
                        doc_a = pymupdf.open(stream=pdf_bytes_auto, filetype="pdf")
                        for num_pag, pagina in enumerate(doc_a, start=1):
                            pix = pagina.get_pixmap(dpi=140)
                            if len(doc_a) > 1:
                                st.caption(f"📄 Página {num_pag} de {len(doc_a)}")
                            st.image(pix.tobytes("png"), use_container_width=True)
                    except Exception:
                        import base64
                        b64_a = base64.b64encode(pdf_bytes_auto).decode('utf-8')
                        st.markdown(f'<iframe src="data:application/pdf;base64,{b64_a}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)

            # =========================================================================
            # PESTAÑA 3: COMPARATIVA DIRECTA CARA A CARA (EMPRESA VS AUTÓNOMO)
            # =========================================================================
            with tab_doc_comp:
                st.header("⚖️ Comparativa Directa Cara a Cara: Empresa vs Instalador Autónomo")
                st.markdown("Analiza la variación de precios para el cliente y la retribución económica real del instalador:")

                filas_comp_tab = [
                    {
                        "Concepto Económico": "📦 Coste Materiales de Compra (C_mat)",
                        "🏢 Modelo Empresa": f"{c_mat:,.2f} €",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{c_mat:,.2f} €",
                        "Diferencia (€)": "0,00 €",
                        "Impacto / Análisis": "Coste idéntico en almacén"
                    },
                    {
                        "Concepto Económico": "🛡️ Margen Seguridad Materiales (M_seg)",
                        "🏢 Modelo Empresa": f"{m_seg:,.2f} €",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{m_seg:,.2f} €",
                        "Diferencia (€)": "0,00 €",
                        "Impacto / Análisis": f"Colchón {porc_garantia}% conservado"
                    },
                    {
                        "Concepto Económico": "📈 Beneficio en Materiales (U_mat)",
                        "🏢 Modelo Empresa": f"{u_mat:,.2f} €",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{u_mat:,.2f} €",
                        "Diferencia (€)": "0,00 €",
                        "Impacto / Análisis": "Ganancia íntegra conservada"
                    },
                    {
                        "Concepto Económico": "⏱️ Jornal / Mano de Obra Directa (C_mo)",
                        "🏢 Modelo Empresa": f"{c_mo:,.2f} €",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{c_mo:,.2f} €",
                        "Diferencia (€)": "0,00 €",
                        "Impacto / Análisis": f"Sueldo garantizado ({horas_totales_obra:.1f} h)"
                    },
                    {
                        "Concepto Económico": "💼 Ganancia Comercial Mano de Obra (G_mo)",
                        "🏢 Modelo Empresa": f"{g_mo:,.2f} € ({margen_comercial:.0f}%)",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{g_mo_auto:,.2f} € ({pct_margen_mo_auto:.0f}%)",
                        "Diferencia (€)": f"-{g_mo - g_mo_auto:,.2f} €",
                        "Impacto / Análisis": "Sobrecoste retirado por el autónomo"
                    },
                    {
                        "Concepto Económico": "📋 Ensayos ITC-BT-05 y CIE DGEAIM",
                        "🏢 Modelo Empresa": f"{v_bol:,.2f} €",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{v_bol:,.2f} €",
                        "Diferencia (€)": "0,00 €",
                        "Impacto / Análisis": "Honorarios técnicos de boletín"
                    }
                ]

                if v_part > 0:
                    filas_comp_tab.append({
                        "Concepto Económico": "➕ Partidas Adicionales y Extras",
                        "🏢 Modelo Empresa": f"{v_part:,.2f} €",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{v_part:,.2f} €",
                        "Diferencia (€)": "0,00 €",
                        "Impacto / Análisis": "Trabajos adicionales valorados"
                    })

                filas_comp_tab.extend([
                    {
                        "Concepto Económico": "🏁 BASE IMPONIBLE TOTAL (S/IVA)",
                        "🏢 Modelo Empresa": f"{base_calc:,.2f} €",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{base_calc_auto:,.2f} €",
                        "Diferencia (€)": f"-{dif_base:,.2f} €",
                        "Impacto / Análisis": f"Descuento comercial de -{(dif_base / base_calc * 100) if base_calc > 0 else 0:.1f}%"
                    },
                    {
                        "Concepto Económico": f"🏛️ Cuota IVA Oficial ({iva_sel}%)",
                        "🏢 Modelo Empresa": f"{cuota_iva_calc:,.2f} €",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{cuota_iva_auto:,.2f} €",
                        "Diferencia (€)": f"-{cuota_iva_calc - cuota_iva_auto:,.2f} €",
                        "Impacto / Análisis": "Menos impuestos a pagar por cliente"
                    },
                    {
                        "Concepto Económico": "🏆 TOTAL A COBRAR AL CLIENTE (CON IVA)",
                        "🏢 Modelo Empresa": f"{total_calc:,.2f} €",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{total_calc_auto:,.2f} €",
                        "Diferencia (€)": f"-{dif_total:,.2f} €",
                        "Impacto / Análisis": f"Ahorro total para el cliente (-{(dif_total / total_calc * 100) if total_calc > 0 else 0:.1f}%)"
                    },
                    {
                        "Concepto Económico": "🔌 Precio Medio por Punto (C/IVA)",
                        "🏢 Modelo Empresa": f"{precio_medio_por_punto:,.2f} €/pto",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{precio_pto_total_auto:,.2f} €/pto",
                        "Diferencia (€)": f"-{delta_pto:,.2f} €/pto",
                        "Impacto / Análisis": "Precio de mercado altamente competitivo"
                    },
                    {
                        "Concepto Económico": "💰 Ingreso Real en el Bolsillo del Instalador",
                        "🏢 Modelo Empresa": f"{benef_total_empresa:,.2f} € (Solo beneficio)",
                        "🧑‍🔧 Modo Autónomo (Tutor)": f"{ingreso_real_autonomo:,.2f} € (Sueldo + Beneficios)",
                        "Diferencia (€)": f"+{ingreso_real_autonomo - benef_total_empresa:,.2f} €",
                        "Impacto / Análisis": "El autónomo cobra su sueldo directo íntegro"
                    }
                ])

                st.dataframe(pd.DataFrame(filas_comp_tab), use_container_width=True, hide_index=True)

                st.success(f"""
                🎯 **Conclusión Estratégica:**  
                - Al facturar como **Autónomo (0% sobrecoste MO)**, tu presupuesto total pasa de **{total_calc:,.2f} €** a **{total_calc_auto:,.2f} €** (el cliente ahorra **{dif_total:,.2f} €** con IVA).  
                - Tu retribución total sigue siendo de **{ingreso_real_autonomo:,.2f} €** garantizados en mano.  
                - Es la mejor táctica para cerrar obras particulares frente a presupuestos competidores agresivos.
                """)

            with tab_doc_int:
                st.header("🔒 Panel Interno de Trabajo, Distancias y Rentabilidad")
                c4_estado_txt = "Desdoblado (C4-A y C4-B independientes)" if desdoblar_c4 else "Estándar unificado"
                st.markdown(f"**Instalador:** {instalador_nombre} | **Potencia / IGA:** {potencia_prevista_kw} | **Circuito C4:** {c4_estado_txt}")
                st.markdown("---")

                st.markdown(f"""
                <div style="border: 2px solid {card_border}; padding: 20px; border-radius: 10px; background-color: {card_bg}; color: {card_text_color}; margin-bottom: 25px;">
                    <h3 style="color: {card_title_color}; margin-top: 0;">💼 RESUMEN ECONÓMICO PARA EL CLIENTE (A Cobrar)</h3>
                    <p style="color: {card_text_color};"><b>Subtotal Comercial Neto:</b> {subtotal_general_neto:.2f} €</p>
                    <p style="color: {card_text_color};"><b>IVA ({iva_sel}%):</b> {cuota_iva:.2f} €</p>
                    <h2 style="color: #16a34a; margin: 0;">TOTAL A COBRAR AL CLIENTE: {total_cliente:.2f} €</h2>
                </div>
                """, unsafe_allow_html=True)

                st.subheader("📊 Conteo Global de Puntos y Análisis por Criterio (Tomas y Luces Dobles)")
                criterio_badge = "🟢 2 Puntos por Doble (Desglosado)" if es_doble_2_puntos else "🔵 1 Punto por Doble (Unificado Físico)"
                st.markdown(f"**Criterio de Cómputo Seleccionado:** `{criterio_badge}` *(Modificable en Sección 2)*")
                
                col_pt1, col_pt2, col_pt3, col_pt4 = st.columns(4)
                with col_pt1:
                    st.metric("🔌 Puntos Computados", f"{total_puntos_mecanismos} pts")
                    st.caption(f"Físicos: `{total_puntos_1p_global}` | Desglosados: `{total_puntos_2p_global}`")
                with col_pt2:
                    st.metric("💶 Venta Media S/IVA", f"{precio_medio_por_punto_neto:.2f} €/pto")
                    st.caption("Base Imponible / Puntos")
                with col_pt3:
                    st.metric("💶 Venta Media C/IVA", f"{precio_medio_por_punto:.2f} €/pto")
                    st.caption(f"Con {iva_sel}% IVA incluido")
                with col_pt4:
                    coste_directo_punto = ((total_mat_global_neto + coste_mano_obra_bruto) / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0
                    utilidad_media_punto = (precio_medio_por_punto_neto - coste_directo_punto)
                    st.metric("📈 Beneficio Medio Neto", f"{utilidad_media_punto:.2f} €/pto")
                    st.caption(f"Coste directo: {coste_directo_punto:.2f} €/pto")

                with st.container(border=True):
                    st.markdown("**🔍 Desglose Pormenorizado de Puntos Instalados:**")
                    col_dp1, col_dp2, col_dp3 = st.columns(3)
                    with col_dp1:
                        pts_td_comp = tot_tomas_dobles_global * 2 if es_doble_2_puntos else tot_tomas_dobles_global
                        st.markdown(f"• **Tomas Dobles de Enchufe:** `{tot_tomas_dobles_global} tomas dobles`  \n↳ Computadas como: **`{pts_td_comp} puntos`** ({'2 pts c/u' if es_doble_2_puntos else '1 pto c/u'})")
                        st.markdown(f"• **Tomas Simples:** `{tot_tomas_simples_global} tomas` = **`{tot_tomas_simples_global} puntos`**")
                    with col_dp2:
                        pts_ld_comp = tot_luces_dobles_global * 2 if es_doble_2_puntos else tot_luces_dobles_global
                        st.markdown(f"• **Luces Dobles (2 encendidos):** `{tot_luces_dobles_global} luces dobles`  \n↳ Computadas como: **`{pts_ld_comp} puntos`** ({'2 pts c/u' if es_doble_2_puntos else '1 pto c/u'})")
                        st.markdown(f"• **Luces Simples:** `{tot_luces_simples_global} luces` = **`{tot_luces_simples_global} puntos`**")
                    with col_dp3:
                        st.markdown(f"• **Tomas Fuerza 25A y RJ45:** `{tot_otros_puntos_global} puntos` = **`{tot_otros_puntos_global} puntos`**")
                        st.markdown(f"• **Total Mecanismos Físicos:** `{tot_tomas_simples_global + (tot_tomas_dobles_global * 2) + tot_luces_simples_global + (tot_luces_dobles_global * 2) + tot_otros_puntos_global} uds`")

                with st.container(border=True):
                    st.markdown("#### 💡 Auditoría de Mercado: Rentabilidad de la Tarifa por Punto (25 a 30 €/pto)")
                    st.markdown("""
                    Compara el rendimiento real de cobrar por punto de mercado frente al coste directo de adquisición de materiales y horas de trabajo en tu obra:
                    """)
                    
                    coste_dir_pto_calc = ((total_mat_global_neto + coste_mano_obra_bruto) / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0
                    
                    col_tpto1, col_tpto2, col_tpto3, col_tpto4 = st.columns(4)
                    
                    # Escenario 25 €/pto
                    b_25 = 25.0 - coste_dir_pto_calc
                    m_25 = (b_25 / 25.0 * 100.0) if 25.0 > 0 else 0.0
                    col_25 = "#16a34a" if m_25 >= 25 else ("#ca8a04" if m_25 >= 10 else "#dc2626")
                    with col_tpto1:
                        st.markdown("**A 25.00 € / punto** *(Económico)*")
                        st.markdown(f"• Total Puntos: `{25.0 * total_puntos_mecanismos:,.2f} €`")
                        st.markdown(f"• Beneficio Neto: `{b_25:+.2f} €/pto`")
                        st.markdown(f"<span style='color:{col_25}; font-weight:bold;'>Margen: {m_25:.1f}%</span>", unsafe_allow_html=True)
                        st.caption("Ideal: tabiquería pladur o sin rozas")

                    # Escenario 28 €/pto
                    b_28 = 28.0 - coste_dir_pto_calc
                    m_28 = (b_28 / 28.0 * 100.0) if 28.0 > 0 else 0.0
                    col_28 = "#16a34a" if m_28 >= 25 else ("#ca8a04" if m_28 >= 10 else "#dc2626")
                    with col_tpto2:
                        st.markdown("**A 28.00 € / punto** *(Estándar Tutor)*")
                        st.markdown(f"• Total Puntos: `{28.0 * total_puntos_mecanismos:,.2f} €`")
                        st.markdown(f"• Beneficio Neto: `{b_28:+.2f} €/pto`")
                        st.markdown(f"<span style='color:{col_28}; font-weight:bold;'>Margen: {m_28:.1f}%</span>", unsafe_allow_html=True)
                        st.caption("Recomendado: ladrillo estándar")

                    # Escenario 30 €/pto
                    b_30 = 30.0 - coste_dir_pto_calc
                    m_30 = (b_30 / 30.0 * 100.0) if 30.0 > 0 else 0.0
                    col_30 = "#16a34a" if m_30 >= 25 else ("#ca8a04" if m_30 >= 10 else "#dc2626")
                    with col_tpto3:
                        st.markdown("**A 30.00 € / punto** *(Obra / Reforma)*")
                        st.markdown(f"• Total Puntos: `{30.0 * total_puntos_mecanismos:,.2f} €`")
                        st.markdown(f"• Beneficio Neto: `{b_30:+.2f} €/pto`")
                        st.markdown(f"<span style='color:{col_30}; font-weight:bold;'>Margen: {m_30:.1f}%</span>", unsafe_allow_html=True)
                        st.caption("Recomendado: termoarcilla o techos macizos")

                    # Escenario actual
                    m_act = ((precio_medio_por_punto_neto - coste_dir_pto_calc) / precio_medio_por_punto_neto * 100.0) if precio_medio_por_punto_neto > 0 else 0.0
                    col_act = "#16a34a" if m_act >= 25 else ("#ca8a04" if m_act >= 10 else "#dc2626")
                    with col_tpto4:
                        st.markdown("**Tu Oferta Actual**")
                        st.markdown(f"• Tarifa: `{precio_medio_por_punto_neto:.2f} €/pto`")
                        st.markdown(f"• Beneficio Neto: `{precio_medio_por_punto_neto - coste_dir_pto_calc:+.2f} €/pto`")
                        st.markdown(f"<span style='color:{col_act}; font-weight:bold;'>Margen: {m_act:.1f}%</span>", unsafe_allow_html=True)
                        st.caption(f"Modalidad: {'Tarifa por Punto' if es_modo_tarifa_puntos else 'Escandallo Analítico'}")

                st.markdown("---")

                # =========================================================================
                # ANÁLISIS DE RENTABILIDAD: 2 ECUACIONES (SIN IVA Y CON IVA) Y CUADRO DE %
                # =========================================================================
                st.subheader("⚖️ Análisis Matemático de Rentabilidad: Ecuaciones de Cobro")
                st.markdown("""
                Desglose económico oficial que establece la igualdad entre los costes directos, margen de seguridad, utilidades empresariales e impuestos conforme a la ley:
                """)

                # Cálculos exactos para cuadre al céntimo y 100.0%
                c_mat = round(total_mat_global_neto, 2)
                m_seg = round(c_mat * (porc_garantia / 100.0), 2)
                
                c_mo = round(coste_mano_obra_bruto, 2)
                g_mo = round(c_mo * (margen_comercial / 100.0), 2)
                
                v_bol = round(float(precio_boletin_cie), 2)
                v_part = round(sum(float(p.get('subtotal', 0.0)) for p in st.session_state.get('partidas_manuales', [])), 2)
                
                # Utilidad de materiales: ajustada con precisión milimétrica para cuadrar con subtotal_general_neto
                u_mat = round(subtotal_general_neto - (c_mat + m_seg + c_mo + g_mo + v_bol + v_part), 2)
                
                base_calc = round(c_mat + m_seg + u_mat + c_mo + g_mo + v_bol + v_part, 2)
                cuota_iva_calc = round(base_calc * (iva_sel / 100.0), 2)
                total_calc = round(base_calc + cuota_iva_calc, 2)
                benef_total_empresa = round(m_seg + u_mat + g_mo + v_bol + v_part, 2)
                costes_directos_tot = round(c_mat + c_mo, 2)
                
                # Render con pestañas comparativas: Empresa vs Autónomo Tutor
                tab_mod_empresa, tab_mod_autonomo, tab_mod_comparativa = st.tabs([
                    "🏢 1. Modelo Empresa (Con Margen MO G_mo)",
                    "👤 2. Simulador Autónomo / Tutor (Sin Margen MO)",
                    "⚖️ 3. Comparativa Empresa vs Autónomo"
                ])

                # =====================================================================
                # SUB-PESTAÑA 1: MODELO EMPRESA (ESTÁNDAR CON MARGEN MO)
                # =====================================================================
                with tab_mod_empresa:
                    st.markdown("##### 🏢 Desglose Económico Modelo Empresa Constructora / Instaladora:")
                    st.caption("Aplica margen comercial tanto sobre materiales como sobre el coste de mano de obra para cubrir gastos de estructura, personal contratado y beneficio industrial.")

                    col_eq1, col_eq2 = st.columns(2)
                    with col_eq1:
                        with st.container(border=True):
                            st.markdown("#### 1️⃣ Ecuación SIN IVA (Base Imponible Empresa)")
                            st.latex(r"\text{Cobro (S/IVA)} = C_{\text{mat}} + M_{\text{seg}} + U_{\text{mat}} + C_{\text{mo}} + G_{\text{mo}} + \text{Extras}")
                            extra_txt_eq = f" + {v_bol:,.2f}\text{{ €}}" + (f" + {v_part:,.2f}\text{{ €}}" if v_part > 0 else "")
                            st.markdown(f"""
                            $$\\underbrace{{{c_mat:,.2f}\text{{ €}}}}_{{C_{{mat}}}} + \\underbrace{{{m_seg:,.2f}\text{{ €}}}}_{{M_{{seg}}}} + \\underbrace{{{u_mat:,.2f}\text{{ €}}}}_{{U_{{mat}}}} + \\underbrace{{{c_mo:,.2f}\text{{ €}}}}_{{C_{{mo}}}} + \\underbrace{{{g_mo:,.2f}\text{{ €}}}}_{{G_{{mo}}}}{extra_txt_eq} = \\mathbf{{{base_calc:,.2f}\text{{ €}}}}$$
                            """)
                            st.caption("✅ **Igualdad comprobada:** Coste Materiales + Margen Seg. + Utilidad Mat. + Coste MO + Ganancia MO + Extras = Base Imponible al céntimo.")
                    
                    with col_eq2:
                        with st.container(border=True):
                            st.markdown("#### 2️⃣ Ecuación CON IVA (Total a Cobrar al Cliente)")
                            st.latex(r"\text{Cobro (C/IVA)} = \left[ C_{\text{mat}} + M_{\text{seg}} + U_{\text{mat}} + C_{\text{mo}} + G_{\text{mo}} + \text{Extras} \right] \times \left(1 + \frac{\text{IVA}}{100}\right)")
                            st.markdown(f"""
                            $$\\mathbf{{{base_calc:,.2f}\\text{{ €}}}} \\times \\left(1 + \\frac{{{iva_sel}}}{{100}}\\right) = \\mathbf{{{base_calc:,.2f}\\text{{ €}}}} + \\mathbf{{{cuota_iva_calc:,.2f}\\text{{ €}}}} = \\mathbf{{{total_calc:,.2f}\\text{{ €}}}}$$
                            """)
                            st.caption(f"✅ **Facturación Total:** Base Imponible con IVA ({iva_sel}%) conforme a la Agencia Tributaria.")

                    st.markdown("##### 📊 Cuadro de Rentabilidad y Relación de Porcentajes (%) Cuadrado al Céntimo:")
                    filas_rent = [
                        {
                            "Concepto Económico": "📦 Coste Materiales de Adquisición (C_mat)",
                            "Importe (€)": f"{c_mat:,.2f} €",
                            "% s/ Base Imponible": f"{(c_mat / base_calc * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(c_mat / total_calc * 100):.2f}%",
                            "Clasificación": "Coste Directo"
                        },
                        {
                            "Concepto Económico": "🛡️ Margen de Seguridad / Imprevistos Materiales (M_seg)",
                            "Importe (€)": f"{m_seg:,.2f} €",
                            "% s/ Base Imponible": f"{(m_seg / base_calc * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(m_seg / total_calc * 100):.2f}%",
                            "Clasificación": f"Colchón Garantía ({porc_garantia}%)"
                        },
                        {
                            "Concepto Económico": "📈 Utilidad / Beneficio en Materiales (U_mat)",
                            "Importe (€)": f"{u_mat:,.2f} €",
                            "% s/ Base Imponible": f"{(u_mat / base_calc * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(u_mat / total_calc * 100):.2f}%",
                            "Clasificación": "Beneficio Neto Empresa"
                        },
                        {
                            "Concepto Económico": "⏱️ Coste Directo Mano de Obra (C_mo)",
                            "Importe (€)": f"{c_mo:,.2f} €",
                            "% s/ Base Imponible": f"{(c_mo / base_calc * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(c_mo / total_calc * 100):.2f}%",
                            "Clasificación": f"Coste Mano de Obra ({horas_totales_obra:.1f} h)"
                        },
                        {
                            "Concepto Económico": "💼 Ganancia Mano de Obra para la Empresa (G_mo)",
                            "Importe (€)": f"{g_mo:,.2f} €",
                            "% s/ Base Imponible": f"{(g_mo / base_calc * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(g_mo / total_calc * 100):.2f}%",
                            "Clasificación": f"Margen MO Empresa ({margen_comercial}%)"
                        },
                        {
                            "Concepto Económico": "📋 Ensayos ITC-BT-05, MTD y Tramitación CIE",
                            "Importe (€)": f"{v_bol:,.2f} €",
                            "% s/ Base Imponible": f"{(v_bol / base_calc * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(v_bol / total_calc * 100):.2f}%",
                            "Clasificación": "Honorarios Técnicos Oficiales"
                        }
                    ]
                    
                    if v_part > 0:
                        filas_rent.append({
                            "Concepto Económico": "➕ Trabajos Adicionales y Partidas a Medida",
                            "Importe (€)": f"{v_part:,.2f} €",
                            "% s/ Base Imponible": f"{(v_part / base_calc * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(v_part / total_calc * 100):.2f}%",
                            "Clasificación": "Partidas Extras Presupuesto"
                        })
                    
                    filas_rent.append({
                        "Concepto Económico": "🏁 TOTAL BASE IMPONIBLE (A COBRAR SIN IVA)",
                        "Importe (€)": f"{base_calc:,.2f} €",
                        "% s/ Base Imponible": "100.00%",
                        "% s/ Total Cliente (C/IVA)": f"{(base_calc / total_calc * 100):.2f}%",
                        "Clasificación": "Ecuación 1 (S/IVA)"
                    })
                    
                    filas_rent.append({
                        "Concepto Económico": f"🏛️ Cuota IVA ({iva_sel}%)",
                        "Importe (€)": f"{cuota_iva_calc:,.2f} €",
                        "% s/ Base Imponible": f"{(cuota_iva_calc / base_calc * 100):.2f}%",
                        "% s/ Total Cliente (C/IVA)": f"{(cuota_iva_calc / total_calc * 100):.2f}%",
                        "Clasificación": "Impuesto Hacienda AEAT"
                    })
                    
                    filas_rent.append({
                        "Concepto Económico": "🏆 TOTAL A COBRAR AL CLIENTE (CON IVA)",
                        "Importe (€)": f"{total_calc:,.2f} €",
                        "% s/ Base Imponible": "—",
                        "% s/ Total Cliente (C/IVA)": "100.00%",
                        "Clasificación": "Ecuación 2 (C/IVA)"
                    })

                    df_rentabilidad = pd.DataFrame(filas_rent)
                    st.dataframe(df_rentabilidad, use_container_width=True, hide_index=True)

                    benef_total_empresa = round(m_seg + u_mat + g_mo + v_bol + v_part, 2)
                    costes_directos_tot = round(c_mat + c_mo, 2)
                    rent_sobre_ventas = (benef_total_empresa / base_calc * 100.0) if base_calc > 0 else 0.0
                    rent_sobre_coste = (benef_total_empresa / costes_directos_tot * 100.0) if costes_directos_tot > 0 else 0.0

                    col_kpr1, col_kpr2, col_kpr3, col_kpr4 = st.columns(4)
                    with col_kpr1:
                        st.metric("📦 Costes Directos (Mat + MO)", f"{costes_directos_tot:,.2f} €")
                        st.caption("Gastos de adquisición y personal")
                    with col_kpr2:
                        st.metric("🚀 Beneficio Neto Empresa", f"+{benef_total_empresa:,.2f} €")
                        st.caption("Margen + Utilidad + Colchón + CIE")
                    with col_kpr3:
                        st.metric("📈 Margen s/ Ventas", f"{rent_sobre_ventas:.1f}%")
                        st.caption("Beneficio / Base Imponible")
                    with col_kpr4:
                        st.metric("💼 Margen s/ Costes Directos", f"{rent_sobre_coste:.1f}%")
                        st.caption("Beneficio / Coste Real")

                # =====================================================================
                # SUB-PESTAÑA 2: SIMULADOR AUTÓNOMO / TUTOR (SIN MARGEN MO O AJUSTABLE)
                # =====================================================================
                with tab_mod_autonomo:
                    st.markdown("##### 👤 Simulador para Instalador Autónomo (Modo Tutor de Prácticas)")
                    st.info("""
                    💡 **¿Por qué los electricistas autónomos suprimen la ganancia sobre la mano de obra ($G_{mo}$)?**  
                    A diferencia de una constructora o empresa con cuadrillas contratadas, el **instalador autónomo ejecuta la obra personalmente con sus propias manos**.  
                    Por lo tanto, su retribución profesional completa ya queda satisfecha con el coste horario de mano de obra ($C_{mo}$ = sueldo / jornal directo). Al eliminar o ajustar $G_{mo}$, obtiene una oferta mucho más atractiva para el cliente, conservando intacto su jornal íntegro y los beneficios en materiales.
                    """)

                    col_cauto1, col_cauto2 = st.columns([3, 2])
                    with col_cauto1:
                        pct_margen_mo_auto = st.slider(
                            "🔧 % Margen Comercial sobre Mano de Obra ($G_{mo}$) para Autónomo:",
                            min_value=0.0,
                            max_value=float(margen_comercial),
                            value=0.0,
                            step=5.0,
                            format="%.0f%%",
                            key="slider_margen_mo_auto",
                            help="0% = Modo Tutor Autónomo Puro (Solo cobra sus horas sin recargo comercial adicional)."
                        )
                    with col_cauto2:
                        st.markdown(f"""
                        <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px; margin-top: 5px;">
                            <div style="font-size: 13px; color: #475569;"><b>Margen Empresa Original:</b> {margen_comercial:.0f}% (+{g_mo:,.2f} €)</div>
                            <div style="font-size: 13px; color: #0284c7; font-weight: bold; margin-top: 3px;"><b>Margen Autónomo Seleccionado:</b> {pct_margen_mo_auto:.0f}%</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Cálculos dinámicos en directo para el autónomo
                    g_mo_auto = round(c_mo * (pct_margen_mo_auto / 100.0), 2)
                    base_calc_auto = round(c_mat + m_seg + u_mat + c_mo + g_mo_auto + v_bol + v_part, 2)
                    cuota_iva_auto = round(base_calc_auto * (iva_sel / 100.0), 2)
                    total_calc_auto = round(base_calc_auto + cuota_iva_auto, 2)

                    dif_base = round(base_calc - base_calc_auto, 2)
                    dif_total = round(total_calc - total_calc_auto, 2)

                    precio_pto_neto_auto = (base_calc_auto / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0
                    precio_pto_total_auto = (total_calc_auto / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0

                    # Ingreso real del autónomo: Jornal MO íntegro + Margen MO opcional + Beneficio materiales + Colchón garantía + CIE + extras
                    ingreso_real_autonomo = round(c_mo + g_mo_auto + u_mat + m_seg + v_bol + v_part, 2)

                    # Tarjetas KPI de impacto para el autónomo
                    col_akpi1, col_akpi2, col_akpi3, col_akpi4 = st.columns(4)
                    with col_akpi1:
                        st.metric(
                            "💶 Total Cliente (C/IVA)",
                            f"{total_calc_auto:,.2f} €",
                            delta=f"-{dif_total:,.2f} € vs Empresa" if dif_total > 0 else None,
                            delta_color="inverse"
                        )
                        st.caption("Presupuesto final cliente")
                    with col_akpi2:
                        st.metric(
                            "📦 Base Imponible (S/IVA)",
                            f"{base_calc_auto:,.2f} €",
                            delta=f"-{dif_base:,.2f} € Ahorro" if dif_base > 0 else None,
                            delta_color="inverse"
                        )
                        st.caption(f"Descuento: {(dif_base / base_calc * 100) if base_calc > 0 else 0:.1f}%")
                    with col_akpi3:
                        delta_pto = precio_medio_por_punto - precio_pto_total_auto
                        st.metric(
                            "🔌 Tarifa por Punto",
                            f"{precio_pto_total_auto:.2f} €/pto",
                            delta=f"-{delta_pto:.2f} €/pto" if delta_pto > 0.01 else None,
                            delta_color="inverse"
                        )
                        st.caption(f"{precio_pto_neto_auto:.2f} €/pto S/IVA")
                    with col_akpi4:
                        st.metric(
                            "💰 Ingreso Real Instalador",
                            f"+{ingreso_real_autonomo:,.2f} €",
                            help="Suma de tu jornal garantizado de mano de obra (C_mo), beneficio en materiales (U_mat), colchón de imprevistos (M_seg) y honorarios CIE."
                        )
                        st.caption(f"Jornal MO ({c_mo:,.2f} €) + Beneficios")

                    # Ecuaciones de cobro del modo autónomo
                    col_aeq1, col_aeq2 = st.columns(2)
                    with col_aeq1:
                        with st.container(border=True):
                            st.markdown("#### 1️⃣ Ecuación SIN IVA (Modo Autónomo)")
                            st.latex(r"\text{Cobro (S/IVA)} = C_{\text{mat}} + M_{\text{seg}} + U_{\text{mat}} + C_{\text{mo}} + G_{\text{mo}}^{\text{auto}} + \text{Extras}")
                            extra_txt_aeq = f" + {v_bol:,.2f}\text{{ €}}" + (f" + {v_part:,.2f}\text{{ €}}" if v_part > 0 else "")
                            st.markdown(f"""
                            $$\\underbrace{{{c_mat:,.2f}\text{{ €}}}}_{{C_{{mat}}}} + \\underbrace{{{m_seg:,.2f}\text{{ €}}}}_{{M_{{seg}}}} + \\underbrace{{{u_mat:,.2f}\text{{ €}}}}_{{U_{{mat}}}} + \\underbrace{{{c_mo:,.2f}\text{{ €}}}}_{{C_{{mo}}}} + \\underbrace{{{g_mo_auto:,.2f}\text{{ €}}}}_{{G_{{mo}}^{{\\text{{auto}}}}}}{extra_txt_aeq} = \\mathbf{{{base_calc_auto:,.2f}\text{{ €}}}}$$
                            """)
                            if pct_margen_mo_auto == 0:
                                st.caption("✅ **Modo Tutor Puro (0% sobrecoste MO):** Tu compensación es tu jornal directo ($C_{mo}$) por las horas trabajadas.")
                            else:
                                st.caption(f"✅ **Margen MO Personalizado ({pct_margen_mo_auto:.0f}%):** Ajuste comercial flexible.")

                    with col_aeq2:
                        with st.container(border=True):
                            st.markdown("#### 2️⃣ Ecuación CON IVA (Modo Autónomo)")
                            st.latex(r"\text{Cobro (C/IVA)} = \text{Base}_{\text{auto}} \times \left(1 + \frac{\text{IVA}}{100}\right)")
                            st.markdown(f"""
                            $$\\mathbf{{{base_calc_auto:,.2f}\\text{{ €}}}} \\times \\left(1 + \\frac{{{iva_sel}}}{{100}}\\right) = \\mathbf{{{base_calc_auto:,.2f}\\text{{ €}}}} + \\mathbf{{{cuota_iva_auto:,.2f}\\text{{ €}}}} = \\mathbf{{{total_calc_auto:,.2f}\\text{{ €}}}}$$
                            """)
                            st.caption(f"✅ **Facturación Legal:** Cuota de IVA oficial ({iva_sel}%) aplicable según normativa.")

                    # Tabla detallada del modo autónomo
                    st.markdown("##### 📊 Cuadro de Rentabilidad Modo Autónomo Cuadrado al Céntimo:")
                    filas_rent_auto = [
                        {
                            "Concepto Económico": "📦 Coste Materiales de Adquisición (C_mat)",
                            "Importe (€)": f"{c_mat:,.2f} €",
                            "% s/ Base Imponible": f"{(c_mat / base_calc_auto * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(c_mat / total_calc_auto * 100):.2f}%",
                            "Clasificación": "Coste Directo"
                        },
                        {
                            "Concepto Económico": "🛡️ Margen de Seguridad / Imprevistos Materiales (M_seg)",
                            "Importe (€)": f"{m_seg:,.2f} €",
                            "% s/ Base Imponible": f"{(m_seg / base_calc_auto * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(m_seg / total_calc_auto * 100):.2f}%",
                            "Clasificación": f"Colchón Garantía ({porc_garantia}%)"
                        },
                        {
                            "Concepto Económico": "📈 Utilidad / Beneficio en Materiales (U_mat)",
                            "Importe (€)": f"{u_mat:,.2f} €",
                            "% s/ Base Imponible": f"{(u_mat / base_calc_auto * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(u_mat / total_calc_auto * 100):.2f}%",
                            "Clasificación": "Beneficio Neto Instalador"
                        },
                        {
                            "Concepto Económico": "⏱️ Jornal / Mano de Obra Directa del Instalador (C_mo)",
                            "Importe (€)": f"{c_mo:,.2f} €",
                            "% s/ Base Imponible": f"{(c_mo / base_calc_auto * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(c_mo / total_calc_auto * 100):.2f}%",
                            "Clasificación": f"Sueldo Íntegro ({horas_totales_obra:.1f} h)"
                        },
                        {
                            "Concepto Económico": "💼 Ganancia Adicional sobre Mano de Obra (G_mo)",
                            "Importe (€)": f"{g_mo_auto:,.2f} €",
                            "% s/ Base Imponible": f"{(g_mo_auto / base_calc_auto * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(g_mo_auto / total_calc_auto * 100):.2f}%",
                            "Clasificación": f"Margen MO ({pct_margen_mo_auto:.0f}%)"
                        },
                        {
                            "Concepto Económico": "📋 Ensayos ITC-BT-05, MTD y Tramitación CIE",
                            "Importe (€)": f"{v_bol:,.2f} €",
                            "% s/ Base Imponible": f"{(v_bol / base_calc_auto * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(v_bol / total_calc_auto * 100):.2f}%",
                            "Clasificación": "Honorarios Técnicos Oficiales"
                        }
                    ]
                    if v_part > 0:
                        filas_rent_auto.append({
                            "Concepto Económico": "➕ Trabajos Adicionales y Partidas a Medida",
                            "Importe (€)": f"{v_part:,.2f} €",
                            "% s/ Base Imponible": f"{(v_part / base_calc_auto * 100):.2f}%",
                            "% s/ Total Cliente (C/IVA)": f"{(v_part / total_calc_auto * 100):.2f}%",
                            "Clasificación": "Partidas Extras Presupuesto"
                        })
                    filas_rent_auto.append({
                        "Concepto Económico": "🏁 TOTAL BASE IMPONIBLE MODO AUTÓNOMO (S/IVA)",
                        "Importe (€)": f"{base_calc_auto:,.2f} €",
                        "% s/ Base Imponible": "100.00%",
                        "% s/ Total Cliente (C/IVA)": f"{(base_calc_auto / total_calc_auto * 100):.2f}%",
                        "Clasificación": "Ecuación 1 (S/IVA)"
                    })
                    filas_rent_auto.append({
                        "Concepto Económico": f"🏛️ Cuota IVA ({iva_sel}%)",
                        "Importe (€)": f"{cuota_iva_auto:,.2f} €",
                        "% s/ Base Imponible": f"{(cuota_iva_auto / base_calc_auto * 100):.2f}%",
                        "% s/ Total Cliente (C/IVA)": f"{(cuota_iva_auto / total_calc_auto * 100):.2f}%",
                        "Clasificación": "Impuesto Hacienda AEAT"
                    })
                    filas_rent_auto.append({
                        "Concepto Económico": "🏆 TOTAL A COBRAR AL CLIENTE (CON IVA)",
                        "Importe (€)": f"{total_calc_auto:,.2f} €",
                        "% s/ Base Imponible": "—",
                        "% s/ Total Cliente (C/IVA)": "100.00%",
                        "Clasificación": "Ecuación 2 (C/IVA)"
                    })
                    st.dataframe(pd.DataFrame(filas_rent_auto), use_container_width=True, hide_index=True)

                    # =================================================================
                    # GENERACIÓN DEL PRESUPUESTO OFICIAL (PDF & EXCEL) MODO AUTÓNOMO
                    # =================================================================
                    st.markdown("---")
                    st.markdown("#### 📄 Presupuesto Oficial para Entregar al Cliente (Modo Autónomo):")
                    st.markdown("Descarga el documento comercial formal con todos los capítulos, estancias y firmas ya recalculados con la tarifa ajustada:")

                    # Ajuste proporcional de los capítulos de obra para cuadrar exactamente con base_calc_auto
                    capitulos_auto = []
                    caps_obra = [c for c in capitulos_presupuesto if c.get("cap") in ["CAP. 01", "CAP. 02", "CAP. 03", "CAP. 04", "CAP. 05"]]
                    suma_caps_obra = sum(c.get("importe", 0.0) for c in caps_obra)
                    resto_fijo = sum(c.get("importe", 0.0) for c in capitulos_presupuesto if c.get("cap") not in ["CAP. 01", "CAP. 02", "CAP. 03", "CAP. 04", "CAP. 05"])
                    nuevo_objetivo_obra = round(base_calc_auto - resto_fijo, 2)

                    acum_obra_auto = 0.0
                    idx_obra = 0
                    for c_orig in capitulos_presupuesto:
                        c_dict = dict(c_orig)
                        if c_orig.get("cap") in ["CAP. 01", "CAP. 02", "CAP. 03", "CAP. 04", "CAP. 05"] and suma_caps_obra > 0:
                            idx_obra += 1
                            if idx_obra == len(caps_obra):
                                c_dict["importe"] = round(nuevo_objetivo_obra - acum_obra_auto, 2)
                            else:
                                prop = c_orig.get("importe", 0.0) / suma_caps_obra
                                c_imp_adj = round(nuevo_objetivo_obra * prop, 2)
                                acum_obra_auto += c_imp_adj
                                c_dict["importe"] = c_imp_adj
                        capitulos_auto.append(c_dict)

                    # Ajuste proporcional de estancias
                    df_comercial_auto = []
                    total_est_orig = sum(float(r.get("Importe Venta (€)", 0.0)) for r in comercial_estancias)
                    suma_est_nueva = sum(c["importe"] for c in capitulos_auto if c["cap"] in ["CAP. 02", "CAP. 03", "CAP. 04"])
                    if total_est_orig > 0:
                        factor_est = suma_est_nueva / total_est_orig
                        for r_orig in comercial_estancias:
                            r_dict = dict(r_orig)
                            r_dict["Importe Venta (€)"] = round(float(r_orig.get("Importe Venta (€)", 0.0)) * factor_est, 2)
                            df_comercial_auto.append(r_dict)
                    else:
                        df_comercial_auto = comercial_estancias

                    # Generación PDF Autónomo
                    pdf_bytes_auto = pdf_presupuesto.generar_pdf_presupuesto(
                        proyecto_info={
                            "empresa": empresa_nombre,
                            "proyectista": instalador_nombre,
                            "licencia": n_licencia,
                            "localidad": localidad,
                            "telefono": telefono,
                            "expediente": "PRES-AUTO-2026",
                            "fecha": datetime.date.today().strftime("%d/%m/%Y")
                        },
                        presupuesto_data={
                            "capitulos": capitulos_auto,
                            "df_comercial": df_comercial_auto,
                            "partidas_manuales": st.session_state.get('partidas_manuales', []),
                            "materiales_pvp": materiales_pvp,
                            "incluir_catalogo_pvp": incluir_catalogo_pvp,
                            "subtotal_neto": base_calc_auto,
                            "iva_pct": iva_sel,
                            "cuota_iva": cuota_iva_auto,
                            "total_cliente": total_calc_auto,
                            "total_puntos": total_puntos_mecanismos,
                            "precio_medio_punto": precio_pto_total_auto,
                            "precio_medio_punto_neto": precio_pto_neto_auto,
                            "serie_mecanismos": serie_mecanismos,
                            "marca_protecciones": marca_protecciones,
                            "potencia_kw": potencia_prevista_kw,
                            "grado_electr": grado_electr,
                            "plazo_dias": dias_estimados,
                            "num_operarios": num_operarios
                        }
                    )

                    # Generación Excel Autónomo
                    excel_auto_bytes = exportar_excel_presupuesto(
                        df_comercial_auto, base_calc_auto, iva_sel, cuota_iva_auto, total_calc_auto,
                        {
                            "empresa": empresa_nombre,
                            "instalador": instalador_nombre,
                            "licencia": n_licencia,
                            "localidad": localidad,
                            "fecha": datetime.date.today().strftime("%d/%m/%Y")
                        },
                        df_orden_compra=df_orden_compra,
                        total_compra_neto=total_mat_global_neto,
                        total_compra_con_iva=total_mat_con_iva,
                        capitulos=capitulos_auto,
                        partidas_manuales=st.session_state.get('partidas_manuales', []),
                        materiales_pvp=materiales_pvp if incluir_catalogo_pvp else None
                    )

                    col_dauto1, col_dauto2 = st.columns(2)
                    with col_dauto1:
                        st.download_button(
                            label="📄 Descargar Presupuesto Oficial Modo Autónomo (PDF)",
                            data=pdf_bytes_auto,
                            file_name=f"Presupuesto_Oficial_Autonomo_{localidad.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            type="primary",
                            key="btn_descarga_pdf_auto",
                            use_container_width=True
                        )
                    with col_dauto2:
                        st.download_button(
                            label="📊 Descargar Oferta Modo Autónomo (Excel)",
                            data=excel_auto_bytes,
                            file_name=f"Presupuesto_Autonomo_{localidad.replace(' ', '_')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="btn_descarga_excel_auto",
                            use_container_width=True
                        )

                    with st.expander("👁️ Vista Previa del Presupuesto en PDF (Modo Autónomo)", expanded=False):
                        try:
                            import pymupdf
                            doc_a = pymupdf.open(stream=pdf_bytes_auto, filetype="pdf")
                            for num_pag, pagina in enumerate(doc_a, start=1):
                                pix = pagina.get_pixmap(dpi=140)
                                if len(doc_a) > 1:
                                    st.caption(f"📄 Página {num_pag} de {len(doc_a)}")
                                st.image(pix.tobytes("png"), use_container_width=True)
                        except Exception:
                            import base64
                            b64_a = base64.b64encode(pdf_bytes_auto).decode('utf-8')
                            st.markdown(f'<iframe src="data:application/pdf;base64,{b64_a}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)

                # =====================================================================
                # SUB-PESTAÑA 3: COMPARATIVA DIRECTA CARA A CARA (EMPRESA VS AUTÓNOMO)
                # =====================================================================
                with tab_mod_comparativa:
                    st.markdown("##### ⚖️ Comparativa Directa Cara a Cara: Empresa vs Instalador Autónomo:")
                    st.caption("Visualiza el impacto exacto en el bolsillo del cliente y en tu rentabilidad como profesional:")

                    filas_comp = [
                        {
                            "Concepto Económico": "📦 Coste Materiales de Compra (C_mat)",
                            "🏢 Modelo Empresa": f"{c_mat:,.2f} €",
                            "👤 Modo Autónomo (Tutor)": f"{c_mat:,.2f} €",
                            "Diferencia (€)": "0,00 €",
                            "Impacto / Análisis": "Coste idéntico en almacén"
                        },
                        {
                            "Concepto Económico": "🛡️ Margen Seguridad Materiales (M_seg)",
                            "🏢 Modelo Empresa": f"{m_seg:,.2f} €",
                            "👤 Modo Autónomo (Tutor)": f"{m_seg:,.2f} €",
                            "Diferencia (€)": "0,00 €",
                            "Impacto / Análisis": f"Colchón {porc_garantia}% conservado"
                        },
                        {
                            "Concepto Económico": "📈 Beneficio en Materiales (U_mat)",
                            "🏢 Modelo Empresa": f"{u_mat:,.2f} €",
                            "👤 Modo Autónomo (Tutor)": f"{u_mat:,.2f} €",
                            "Diferencia (€)": "0,00 €",
                            "Impacto / Análisis": "Ganancia íntegra conservada"
                        },
                        {
                            "Concepto Económico": "⏱️ Jornal / Mano de Obra Directa (C_mo)",
                            "🏢 Modelo Empresa": f"{c_mo:,.2f} €",
                            "👤 Modo Autónomo (Tutor)": f"{c_mo:,.2f} €",
                            "Diferencia (€)": "0,00 €",
                            "Impacto / Análisis": f"Sueldo garantizado ({horas_totales_obra:.1f} h)"
                        },
                        {
                            "Concepto Económico": "💼 Ganancia Comercial Mano de Obra (G_mo)",
                            "🏢 Modelo Empresa": f"{g_mo:,.2f} € ({margen_comercial:.0f}%)",
                            "👤 Modo Autónomo (Tutor)": f"{g_mo_auto:,.2f} € ({pct_margen_mo_auto:.0f}%)",
                            "Diferencia (€)": f"-{g_mo - g_mo_auto:,.2f} €",
                            "Impacto / Análisis": "Sobrecoste retirado por el autónomo"
                        },
                        {
                            "Concepto Económico": "📋 Ensayos ITC-BT-05 y CIE DGEAIM",
                            "🏢 Modelo Empresa": f"{v_bol:,.2f} €",
                            "👤 Modo Autónomo (Tutor)": f"{v_bol:,.2f} €",
                            "Diferencia (€)": "0,00 €",
                            "Impacto / Análisis": "Honorarios técnicos de boletín"
                        }
                    ]

                    if v_part > 0:
                        filas_comp.append({
                            "Concepto Económico": "➕ Partidas Adicionales y Extras",
                            "🏢 Modelo Empresa": f"{v_part:,.2f} €",
                            "👤 Modo Autónomo (Tutor)": f"{v_part:,.2f} €",
                            "Diferencia (€)": "0,00 €",
                            "Impacto / Análisis": "Trabajos adicionales valorados"
                        })

                    filas_comp.extend([
                        {
                            "Concepto Económico": "🏁 BASE IMPONIBLE TOTAL (S/IVA)",
                            "🏢 Modelo Empresa": f"{base_calc:,.2f} €",
                            "👤 Modo Autónomo (Tutor)": f"{base_calc_auto:,.2f} €",
                            "Diferencia (€)": f"-{dif_base:,.2f} €",
                            "Impacto / Análisis": f"Descuento comercial de -{(dif_base / base_calc * 100) if base_calc > 0 else 0:.1f}%"
                        },
                        {
                            "Concepto Económico": f"🏛️ Cuota IVA Oficial ({iva_sel}%)",
                            "🏢 Modelo Empresa": f"{cuota_iva_calc:,.2f} €",
                            "👤 Modo Autónomo (Tutor)": f"{cuota_iva_auto:,.2f} €",
                            "Diferencia (€)": f"-{cuota_iva_calc - cuota_iva_auto:,.2f} €",
                            "Impacto / Análisis": "Menos impuestos a pagar por cliente"
                        },
                        {
                            "Concepto Económico": "🏆 TOTAL A COBRAR AL CLIENTE (CON IVA)",
                            "🏢 Modelo Empresa": f"{total_calc:,.2f} €",
                            "👤 Modo Autónomo (Tutor)": f"{total_calc_auto:,.2f} €",
                            "Diferencia (€)": f"-{dif_total:,.2f} €",
                            "Impacto / Análisis": f"Ahorro total para el cliente (-{(dif_total / total_calc * 100) if total_calc > 0 else 0:.1f}%)"
                        },
                        {
                            "Concepto Económico": "🔌 Precio Medio por Punto (C/IVA)",
                            "🏢 Modelo Empresa": f"{precio_medio_por_punto:,.2f} €/pto",
                            "👤 Modo Autónomo (Tutor)": f"{precio_pto_total_auto:,.2f} €/pto",
                            "Diferencia (€)": f"-{delta_pto:,.2f} €/pto",
                            "Impacto / Análisis": "Precio de mercado altamente competitivo"
                        },
                        {
                            "Concepto Económico": "💰 Ingreso Real en el Bolsillo del Instalador",
                            "🏢 Modelo Empresa": f"{benef_total_empresa:,.2f} € (Solo beneficio)",
                            "👤 Modo Autónomo (Tutor)": f"{ingreso_real_autonomo:,.2f} € (Sueldo + Beneficios)",
                            "Diferencia (€)": f"+{ingreso_real_autonomo - benef_total_empresa:,.2f} €",
                            "Impacto / Análisis": "El autónomo cobra su sueldo directo íntegro"
                        }
                    ])

                    st.dataframe(pd.DataFrame(filas_comp), use_container_width=True, hide_index=True)

                    st.success(f"""
                    🎯 **Conclusión Estratégica para el Instalador Autónomo:**  
                    - **Competitividad:** Reduciendo el margen MO al {pct_margen_mo_auto:.0f}%, tu presupuesto baja de **{total_calc:,.2f} €** a **{total_calc_auto:,.2f} €** (el cliente se ahorra **{dif_total:,.2f} €** con IVA).  
                    - **Seguridad Financiera:** Tu retribución como profesional instalador sigue siendo de **{ingreso_real_autonomo:,.2f} €** (tus **{coste_mano_obra_bruto:,.2f} €** de horas trabajadas + los márgenes comerciales de materiales y boletín).  
                    - **Cierre de Obra:** Es la herramienta perfecta para ganar obras a particulares cuando hay presupuestos competidores ajustados en la calle.
                    """)
                st.markdown("---")

                # =========================================================================
                # SECCIONES DESPLEGABLES INFERIORES (OPTIMIZADO PARA TABLETS Y PANTALLAS PEQUEÑAS)
                # =========================================================================
                with st.expander("⏱️ Desplegar Análisis de Rendimiento, Tiempos y Plazos de Obra", expanded=False):
                    st.write(f"- 🧱 **Fase de Rozas ({tipo_pared} | Techo: {'Falso Techo' if 'Falso Techo' in tipo_techo else 'Macizo'}):** `{sum_h_rozas:.2f} h`")
                    st.write(f"- 📏 **Fase de Canalización:** `{sum_h_tubos:.2f} h`")
                    st.write(f"- ⚡ **Fase de Cableado:** `{sum_h_cable:.2f} h`")
                    st.write(f"- 🔲 **Fase de Mecanizado:** `{sum_h_mec:.2f} h`")
                    st.info(f"⏱️ **Total Horas de Trabajo:** `{horas_totales_obra:.2f} h` netas (`{coste_mano_obra_bruto:.2f} €` coste MO)")
                    st.success(f"📅 **Plazo Estimado de Ejecución:** `{dias_estimados:.1f} días` de obra (con `{num_operarios} operario(s)` a jornadas de `{horas_jornada} h/día`).")

                st.markdown("---")

                st.subheader("🛒 Resumen de Acopio y Reporte de Compras Clasificado")
                st.markdown("Materiales organizados por tipo y tienda con descarga directa para compras en almacén:")

                if items_no_catalogados:
                    st.warning(f"⚠️ **Atención:** Hay **{len(items_no_catalogados)} artículo(s)** calculados con tarifa estimada por no estar registrados en el catálogo.")
                    with st.expander("⚡ Actualizar y Guardar Artículos No Catalogados en la Base de Datos Excel", expanded=False):
                        st.markdown("""
                        **¿Deseas completar y actualizar automáticamente estos artículos desde la web oficial?**  
                        Al presionar el pulsador web, la aplicación asignará las referencias oficiales (SKU), descripciones reales de tienda y precios de mercado para guardarlos en `base_datos_precio_oficial.xlsx`:
                        """)
                    
                        def resolver_articulo_web_oficial(art_nom, cat_hint="", marca_hint=""):
                            nom_l = str(art_nom).lower()
                            if "tubo" in nom_l:
                                if "m-20" in nom_l or "m20" in nom_l:
                                    if "lh" in nom_l or "libre" in nom_l or "halógeno" in nom_l:
                                        return {"desc": "Tubo Corrugado M20 Libre de Halógenos 750N (Rollo 50m)", "prov": "Obramat", "sku": "OBR-TUBO-LH-M20", "precio": 0.52, "cat": "Canalización Tubos", "marca": "General", "unid": "m"}
                                    return {"desc": "Tubo Corrugado PVC M20 Normal / Estándar 320N (Rollo 100m)", "prov": "Obramat", "sku": "OBR-TUBO-PVC-M20", "precio": 0.28, "cat": "Canalización Tubos", "marca": "General", "unid": "m"}
                                elif "m-25" in nom_l or "m25" in nom_l:
                                    if "lh" in nom_l or "libre" in nom_l or "halógeno" in nom_l:
                                        return {"desc": "Tubo Corrugado M25 Libre de Halógenos 750N (Rollo 50m)", "prov": "Obramat", "sku": "OBR-TUBO-LH-M25", "precio": 0.65, "cat": "Canalización Tubos", "marca": "General", "unid": "m"}
                                    return {"desc": "Tubo Corrugado PVC M25 Normal / Estándar 320N (Rollo 50m)", "prov": "Obramat", "sku": "OBR-TUBO-PVC-M25", "precio": 0.38, "cat": "Canalización Tubos", "marca": "General", "unid": "m"}
                                elif "m-32" in nom_l or "m32" in nom_l:
                                    return {"desc": "Tubo Corrugado PVC M32 Normal / Estándar 320N (Rollo 25m)", "prov": "Obramat", "sku": "OBR-TUBO-PVC-M32", "precio": 0.58, "cat": "Canalización Tubos", "marca": "General", "unid": "m"}

                            if "cable" in nom_l or "conductor" in nom_l or "1.5" in nom_l or "2.5" in nom_l:
                                sec = "1.5 mm²" if "1.5" in nom_l else ("2.5 mm²" if "2.5" in nom_l else "4.0 mm²")
                                col = "Azul" if "azul" in nom_l else ("Negro" if "negro" in nom_l else ("Marrón" if "marrón" in nom_l or "marron" in nom_l else ("Gris" if "gris" in nom_l else "Amarillo/Verde")))
                                es_lh = "h07z1" in nom_l or "libre" in nom_l or "halógeno" in nom_l
                                p_base = (0.42 if "2.5" in sec else 0.24) if es_lh else (0.33 if "2.5" in sec else 0.19)
                                norm_str = "H07Z1-K Libre Halógenos" if es_lh else "H07V-K PVC Normal"
                                return {"desc": f"Cable {norm_str} 1x{sec} {col} (Rollo 100m)", "prov": "Obramat", "sku": f"OBR-CAB-{'LH' if es_lh else 'PVC'}-{sec[:3].replace('.','')}-{col[:2].upper()}", "precio": p_base, "cat": "Conductores", "marca": "General Cable / Top Cable", "unid": "m"}

                            if "interruptor" in nom_l or "conmutador" in nom_l or "schuko" in nom_l or "enchufe" in nom_l or "marco" in nom_l or "rj45" in nom_l:
                                return {"desc": f"Mecanismo {art_nom} Blanco", "prov": "Sumidelec / Obramat", "sku": f"REF-MEC-{str(art_nom)[:4].upper()}", "precio": (1.75 if "marco" not in nom_l else 0.40), "cat": ("Mecanismos" if "marco" not in nom_l else "Marcos / Placas"), "marca": (marca_hint if marca_hint else "Efapel / Simon"), "unid": "ud"}

                            return {"desc": f"Artículo {art_nom} Catálogo Oficial", "prov": "Obramat / Distribución", "sku": f"REF-{str(art_nom)[:4].upper()}-OFIC", "precio": 1.25, "cat": (cat_hint if cat_hint else "General"), "marca": (marca_hint if marca_hint else "General"), "unid": "ud"}

                        if st.button("🌐 Auto-Completar y Actualizar Precios desde la Web Oficial (1 Clic)", type="primary", key="btn_auto_update_all_web"):
                            try:
                                df_act = pd.read_excel('base_datos_precio_oficial.xlsx')
                                for art_no in items_no_catalogados:
                                    info_web = resolver_articulo_web_oficial(art_no['articulo'], art_no.get('categoria_bd', ''), art_no.get('marca_bd', ''))
                                    nuevo_reg = {
                                        'ID': f"ART-{len(df_act)+1:04d}",
                                        'Nivel de Gama / Aplicación': 'Estándar',
                                        'Familia / Categoria': info_web['cat'],
                                        'Marca': info_web['marca'],
                                        'Serie / Gama': 'Estándar',
                                        'Proveedor / Tienda': info_web['prov'],
                                        'Código SKU / Ref': info_web['sku'],
                                        'Descripción Exacta del Artículo': info_web['desc'],
                                        'Unidad': info_web['unid'],
                                        'Precio S/IVA (€)': float(info_web['precio']),
                                        'IVA (%)': 21.0,
                                        'Precio C/IVA (€)': round(float(info_web['precio']) * 1.21, 2),
                                        'Observaciones / Aplicación Técnica': 'Actualizado automáticamente con referencia web oficial'
                                    }
                                    df_act = pd.concat([df_act, pd.DataFrame([nuevo_reg])], ignore_index=True)
                                df_act.to_excel('base_datos_precio_oficial.xlsx', index=False)
                                cargar_precios_excel.clear()
                                st.session_state['msg_exito_actualizacion'] = "✅ ¡Artículos actualizados automáticamente con referencias y precios oficiales de la web! Recalculado con éxito."
                                st.session_state.presupuesto_calculado = True
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error al actualizar automáticamente: {ex}")

                        st.markdown("---")
                        st.markdown("**O modifica los datos manualmente antes de guardar:**")
                        with st.form("form_actualizar_no_catalogados_panel"):
                            articulos_a_guardar = []
                            for idx_no, art_no in enumerate(items_no_catalogados):
                                sug = resolver_articulo_web_oficial(art_no['articulo'], art_no.get('categoria_bd', ''), art_no.get('marca_bd', ''))
                                st.markdown(f"**Artículo:** `{art_no['articulo']}`")
                                col_u1, col_u2, col_u3, col_u4 = st.columns([3, 2, 2, 2])
                                with col_u1:
                                    desc_edit = st.text_input("Descripción Real / Nombre Comercial", value=sug['desc'], key=f"desc_nc_{idx_no}")
                                with col_u2:
                                    prov_edit = st.selectbox("Tienda / Proveedor", ["Obramat", "Leroy Merlin", "Sumidelec", "Sonepar", "Electro Material", "General"], index=0, key=f"prov_nc_{idx_no}")
                                with col_u3:
                                    precio_edit = st.number_input("Precio S/IVA (€)", value=float(sug['precio']), min_value=0.01, step=0.05, format="%.2f", key=f"p_nc_{idx_no}")
                                with col_u4:
                                    sku_edit = st.text_input("Ref / SKU", value=sug['sku'], key=f"sku_nc_{idx_no}")
                            
                                articulos_a_guardar.append({
                                    "Nivel de Gama / Aplicación": "Estándar",
                                    "Familia / Categoria": art_no.get("categoria_bd", sug['cat']),
                                    "Marca": art_no.get("marca_bd", sug['marca']),
                                    "Serie / Gama": "Estándar",
                                    "Proveedor / Tienda": prov_edit,
                                    "Código SKU / Ref": sku_edit,
                                    "Descripción Exacta del Artículo": desc_edit,
                                    "Unidad": sug['unid'],
                                    "Precio S/IVA (€)": precio_edit,
                                    "IVA (%)": 21.0,
                                    "Precio C/IVA (€)": round(precio_edit * 1.21, 2),
                                    "Observaciones / Aplicación Técnica": "Registrado desde actualizador de acopio"
                                })
                                st.markdown("---")
                        
                            btn_guardar_bd = st.form_submit_button("💾 Guardar Selección en Excel y Recalcular Presupuesto", type="primary")
                            if btn_guardar_bd:
                                try:
                                    df_act = pd.read_excel('base_datos_precio_oficial.xlsx')
                                    for nuevo_art in articulos_a_guardar:
                                        nuevo_art["ID"] = f"ART-{len(df_act)+1:04d}"
                                        df_act = pd.concat([df_act, pd.DataFrame([nuevo_art])], ignore_index=True)
                                    df_act.to_excel('base_datos_precio_oficial.xlsx', index=False)
                                    cargar_precios_excel.clear()
                                    st.session_state['msg_exito_actualizacion'] = "✅ ¡Artículos guardados en Excel correctamente! Recalculado con éxito."
                                    st.session_state.presupuesto_calculado = True
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Error al guardar en Excel: {ex}")

                with st.expander("👁️ Ver Vista Previa del Reporte de Compras en PDF antes de Imprimir / Descargar", expanded=False):
                    st.info("💡 **Revisa el documento en pantalla.** Una vez verificado, puedes descargarlo en PDF/Excel o imprimirlo directamente.")
                    try:
                        import pymupdf
                        doc_oc_p1 = pymupdf.open(stream=pdf_oc_bytes, filetype="pdf")
                        for num_pag, pagina in enumerate(doc_oc_p1, start=1):
                            pix = pagina.get_pixmap(dpi=150)
                            if len(doc_oc_p1) > 1:
                                st.caption(f"📄 **Página {num_pag} de {len(doc_oc_p1)}**")
                            st.image(pix.tobytes("png"), use_container_width=True)
                    except Exception:
                        import base64
                        b64_oc_p1 = base64.b64encode(pdf_oc_bytes).decode('utf-8')
                        st.markdown(f'<iframe src="data:application/pdf;base64,{b64_oc_p1}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)

                col_btn_ac1, col_btn_ac2 = st.columns(2)
                with col_btn_ac1:
                    st.download_button(
                        label="📄 🖨️ Descargar / Imprimir Reporte de Compras en PDF",
                        data=pdf_oc_bytes,
                        file_name="Reporte_Compras_Acopio_Bolimur.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="btn_pdf_acopio_panel"
                    )
                with col_btn_ac2:
                    st.download_button(
                        label="📊 Descargar Reporte de Compras en Excel (.xlsx)",
                        data=excel_oc_bytes,
                        file_name="Reporte_Compras_Acopio_Bolimur.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="btn_excel_acopio_panel"
                    )

                with st.expander("📋 Desglose Completo de Materiales por Tipo / Categoría", expanded=False):
                    for cat_titulo, articulos in categorias_orden_compra.items():
                        if not articulos:
                            continue
                        st.markdown(f"##### {cat_titulo}")
                        df_cat_res = pd.DataFrame([
                            {
                                "Cant.": a["cantidad"],
                                "Unidad": a["unidad"],
                                "Artículo": a["articulo"],
                                "Descripción Exacta (Tienda)": a["desc_exacta"],
                                "Tienda / Prov.": a["proveedor"],
                                "P. Unit (€)": f"{a['precio_unitario']:.2f} €",
                                "Subtotal (€)": f"{a['subtotal']:.2f} €",
                                "Estado": "🟢 En Catálogo" if a.get("en_bd", True) else "⚠️ No en BD"
                            }
                            for a in articulos
                        ])
                        st.dataframe(df_cat_res, use_container_width=True, hide_index=True)

                with st.expander("🚪 Ver Desglose de Materiales Asignados por Cada Estancia (Cocina, Baño, Salón...)", expanded=False):
                    st.markdown("Consulta los materiales exactos asignados a cada estancia para organizar el acopio y montaje en obra:")
                    for est_m in materiales_por_estancia:
                        st.markdown(f"##### 📍 {est_m['nombre']} ({est_m['m2']} m² | Distancia: {est_m['distancia_cuadro']}m | Coste Materiales: {est_m['coste_materiales_neto']:.2f} € S/IVA)")
                        col_pe1, col_pe2 = st.columns(2)
                        with col_pe1:
                            df_mec_pe = pd.DataFrame([{"Elemento": m["nombre"], "Descripción": m["desc_real"], "Cantidad": f"{m['cant']} ud", "Subtotal": f"{m['cant'] * m['precio']:.2f} €"} for m in est_m["mecanismos"]])
                            st.dataframe(df_mec_pe, use_container_width=True, hide_index=True)
                            st.caption(f"Cajas Mecanismo: {est_m['cajas_mecanismo']} ud | Cajas Registro: {est_m['cajas_registro']} ud | Marcos: {est_m['marcos']} ud")
                        with col_pe2:
                            df_cab_pe = pd.DataFrame([{"Conductor": c["item"], "Metros": f"{c['metros']:.1f} m"} for c in est_m["cables"] if c["metros"] > 0])
                            st.dataframe(df_cab_pe, use_container_width=True, hide_index=True)
                            st.caption(f"Tubo M20: {est_m['tubo_m20']:.1f} m | Tubo M25: {est_m['tubo_m25']:.1f} m")
                        st.markdown("---")

                with st.expander("➕ Añadir Manualmente un Nuevo Artículo al Excel de Precios"):
                    with st.form("form_nuevo_art_manual"):
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            m_desc = st.text_input("Descripción Exacta del Artículo", placeholder="Ej: Tubo corrugado M32 reforzado")
                            m_cat = st.selectbox("Categoría / Familia", ["Conductores", "Canalización Tubos", "Mecanismos", "Protecciones", "Cuadros y Envolventes", "Cajas de Registro", "Conexión", "General"])
                            m_marca = st.text_input("Marca", value="Obramat / General")
                        with col_m2:
                            m_prov = st.selectbox("Tienda / Proveedor", ["Obramat", "Leroy Merlin", "Sonepar", "Electro Material", "General"])
                            m_precio = st.number_input("Precio S/IVA (€)", min_value=0.01, value=1.00, step=0.10)
                            m_unid = st.selectbox("Unidad", ["m", "ud", "rollo 50m", "rollo 100m", "caja"])
                    
                        if st.form_submit_button("💾 Guardar Artículo en Excel"):
                            if m_desc:
                                try:
                                    df_act = pd.read_excel('base_datos_precio_oficial.xlsx')
                                    n_id = f"ART-{len(df_act)+1:04d}"
                                    nuevo_reg = {
                                        "ID": n_id,
                                        "Nivel de Gama / Aplicación": "Estándar",
                                        "Familia / Categoria": m_cat,
                                        "Marca": m_marca,
                                        "Serie / Gama": "Estándar",
                                        "Proveedor / Tienda": m_prov,
                                        "Código SKU / Ref": f"MAN-{n_id}",
                                        "Descripción Exacta del Artículo": m_desc,
                                        "Unidad": m_unid,
                                        "Precio S/IVA (€)": m_precio,
                                        "IVA (%)": 21,
                                        "Precio C/IVA (€)": round(m_precio * 1.21, 2),
                                        "Observaciones / Aplicación Técnica": "Registrado manualmente"
                                    }
                                    df_act = pd.concat([df_act, pd.DataFrame([nuevo_reg])], ignore_index=True)
                                    df_act.to_excel('base_datos_precio_oficial.xlsx', index=False)
                                    cargar_precios_excel.clear()
                                    st.session_state['msg_exito_actualizacion'] = f"✅ ¡Artículo '{m_desc}' añadido con ID `{n_id}` y guardado en Excel!"
                                    st.session_state.presupuesto_calculado = True
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al guardar: {e}")
                            else:
                                st.warning("Introduce una descripción válida.")

                with st.expander("💳 Dinero Total Necesario en Caja (Acopio Completo)", expanded=False):
                    st.markdown(f"""
                    <div style="border: 2px solid #16a34a; padding: 18px; border-radius: 10px; background-color: {card_bg}; margin-top: 5px;">
                        <h4 style="color: #16a34a; margin-top: 0;">💳 DINERO TOTAL NECESARIO EN CAJA (ACOPIO COMPLETO)</h4>
                        <p style="color: {card_text_color}; margin: 4px 0;"><b>Coste Materiales Estancias:</b> {total_mat_estancias_neto:,.2f} € &nbsp;|&nbsp; <b>Coste Cuadro ({marca_protecciones}):</b> {coste_cuadro_neto:,.2f} €</p>
                        <p style="color: {card_text_color}; margin: 4px 0;"><b>Coste Total Materiales Neto (Sin IVA):</b> {total_mat_global_neto:,.2f} €</p>
                        <h2 style="color: #16a34a; margin: 10px 0 0 0;">TOTAL A PAGAR EN EL ALMACÉN (Con 21% IVA): {total_mat_con_iva:,.2f} €</h2>
                    </div>
                    """, unsafe_allow_html=True)


            with tab_doc_oc:
                st.header("🛒 Orden de Compra y Lista de Acopio de Materiales")
                st.markdown("Listado exhaustivo clasificado por familias con descripciones exactas y tiendas para pedir en almacén.")

                # Summary Box
                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                with col_kpi1:
                    st.metric("💳 Total a Pagar (C/IVA)", f"{total_mat_con_iva:,.2f} €")
                with col_kpi2:
                    st.metric("📦 Base Imponible (S/IVA)", f"{total_mat_global_neto:,.2f} €")
                with col_kpi3:
                    st.metric("🧾 IVA Materiales (21%)", f"{cuota_iva_mat:,.2f} €")
                with col_kpi4:
                    st.metric("🏷️ Total Partidas / Artículos", f"{len(df_orden_compra)} uds")

                st.markdown("---")

                tab_oc_glob, tab_oc_est = st.tabs([
                    "🏢 1. Lista Global Consolidada para Tienda / Almacén (1 Línea por Referencia Sumada)",
                    "🚪 2. Desglose Detallado de Materiales Asignados por Estancia (Cocina, Baño, Salón...)"
                ])

                with tab_oc_glob:
                    # Filtro por tienda/proveedor
                    tiendas_unicas = sorted(list(df_orden_compra["Tienda / Proveedor"].dropna().unique()))
                    filtro_tienda = st.selectbox("🏬 Filtrar por Tienda / Proveedor:", ["Todos los Proveedores"] + tiendas_unicas, key="sel_tienda_glob")

                    # Desglose por categorías organizadas
                    st.subheader("📋 Listado Detallado por Categorías de Acopio")
                    if items_no_catalogados:
                        st.warning(f"⚠️ **Aviso:** Hay **{len(items_no_catalogados)} artículo(s)** sin catalogar en el Excel. Puedes usar el actualizador de la sección de acopio para registrarlos permanentemente.")

                    for cat_titulo, articulos in categorias_orden_compra.items():
                        if not articulos:
                            continue

                        arts_filtrados = [a for a in articulos if filtro_tienda == "Todos los Proveedores" or a["proveedor"] == filtro_tienda]
                        if not arts_filtrados:
                            continue

                        st.markdown(f"#### {cat_titulo}")
                        df_cat = pd.DataFrame([
                            {
                                "Cant.": a["cantidad"],
                                "Unidad": a["unidad"],
                                "Artículo": a["articulo"],
                                "Descripción Exacta (Tienda)": a["desc_exacta"],
                                "Tienda": a["proveedor"],
                                "P. Unit (€)": f"{a['precio_unitario']:.2f} €",
                                "Subtotal (€)": f"{a['subtotal']:.2f} €",
                                "Estado Catálogo": "🟢 En Catálogo" if a.get("en_bd", True) else "⚠️ No en BD (Estimado)"
                            }
                            for a in arts_filtrados
                        ])
                        st.dataframe(df_cat, use_container_width=True, hide_index=True)

                    st.markdown("---")
                    st.subheader("📑 Tabla Completa de la Orden de Compra")
                    if filtro_tienda != "Todos los Proveedores":
                        st.dataframe(df_orden_compra[df_orden_compra["Tienda / Proveedor"] == filtro_tienda], use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(df_orden_compra, use_container_width=True, hide_index=True)

                with tab_oc_est:
                    st.subheader("🚪 Materiales y Acopio Asignados por Cada Estancia")
                    st.markdown("Consulta exactamente qué materiales corresponden a cada habitación para organizar las cajas y el montaje en obra:")
                
                    est_nombres = [e["nombre"] for e in materiales_por_estancia]
                    est_sel = st.selectbox("Selecciona una estancia para ver su detalle:", ["Todas las Estancias"] + est_nombres, key="sel_est_acopio_tab")
                
                    for est_m in materiales_por_estancia:
                        if est_sel != "Todas las Estancias" and est_m["nombre"] != est_sel:
                            continue
                    
                        with st.expander(f"📍 {est_m['nombre']} ({est_m['m2']} m² | Distancia al Cuadro: {est_m['distancia_cuadro']} m | Coste Materiales: {est_m['coste_materiales_neto']:.2f} € S/IVA)", expanded=True):
                            col_e1, col_e2 = st.columns(2)
                            with col_e1:
                                st.markdown("**🔲 Mecanismos y Marcos:**")
                                df_mec_e = pd.DataFrame([
                                    {
                                        "Elemento": m["nombre"],
                                        "Descripción Real": m["desc_real"],
                                        "Cantidad": f"{m['cant']} ud",
                                        "P. Unit": f"{m['precio']:.2f} €",
                                        "Subtotal": f"{m['cant'] * m['precio']:.2f} €"
                                    }
                                    for m in est_m["mecanismos"]
                                ])
                                if est_m["marcos"] > 0:
                                    df_mec_e = pd.concat([df_mec_e, pd.DataFrame([{
                                        "Elemento": "Marcos Embellecedores",
                                        "Descripción Real": desc_marco,
                                        "Cantidad": f"{est_m['marcos']} ud",
                                        "P. Unit": f"{p_marco:.2f} €",
                                        "Subtotal": f"{est_m['marcos'] * p_marco:.2f} €"
                                    }])], ignore_index=True)
                                st.dataframe(df_mec_e, use_container_width=True, hide_index=True)

                                st.markdown(f"**📦 Cajas en esta estancia:** `{est_m['cajas_mecanismo']}x` Cajas de Mecanismo 67mm | `{est_m['cajas_registro']}x` Cajas de Registro 100x100")

                            with col_e2:
                                st.markdown("**⚡ Canalización y Cables Asignados:**")
                                df_cab_e = pd.DataFrame([
                                    {
                                        "Conductor / Línea": c["item"],
                                        "Metros Calculados": f"{c['metros']:.1f} m"
                                    }
                                    for c in est_m["cables"] if c["metros"] > 0
                                ])
                                st.dataframe(df_cab_e, use_container_width=True, hide_index=True)
                            
                                st.markdown(f"**📏 Tubo Corrugado Asignado:** M20: `{est_m['tubo_m20']:.1f} m` | M25: `{est_m['tubo_m25']:.1f} m`")

                    st.markdown("---")
                    st.subheader("📊 Tabla Resumen Comparativa de Materiales por Estancia")
                    filas_resumen_est = []
                    for e in materiales_por_estancia:
                        tot_m = sum([m["cant"] for m in e["mecanismos"]])
                        filas_resumen_est.append({
                            "Estancia": e["nombre"],
                            "Superficie": f"{e['m2']} m²",
                            "Distancia al Cuadro": f"{e['distancia_cuadro']} m",
                            "Mecanismos": f"{tot_m} uds",
                            "Marcos": f"{e['marcos']} uds",
                            "Tubo M20": f"{e['tubo_m20']:.1f} m",
                            "Tubo M25": f"{e['tubo_m25']:.1f} m",
                            "Coste Neto Materiales": f"{e['coste_materiales_neto']:.2f} €",
                            "Total C/IVA": f"{e['coste_materiales_con_iva']:.2f} €"
                        })
                    st.dataframe(pd.DataFrame(filas_resumen_est), use_container_width=True, hide_index=True)

                # Generar Excel y PDF de la Orden de Compra
                excel_oc_bytes = exportar_excel_orden_compra(
                    df_orden_compra, total_mat_global_neto, cuota_iva_mat, total_mat_con_iva,
                    {
                        "empresa": empresa_nombre,
                        "proyectista": instalador_nombre,
                        "fecha": datetime.date.today().strftime("%d/%m/%Y"),
                        "potencia_kw": potencia_prevista_kw,
                        "tipo_cable": tipo_cable_sel,
                        "tipo_tubo": tipo_tubo_sel,
                        "serie_mecanismos": serie_mecanismos,
                        "marca_protecciones": marca_protecciones
                    }
                )

                pdf_oc_bytes = pdf_presupuesto.generar_pdf_orden_compra(
                    proyecto_info={
                        "empresa": empresa_nombre,
                        "proyectista": instalador_nombre,
                        "licencia": n_licencia,
                        "localidad": localidad,
                        "telefono": telefono,
                        "expediente": "OC-2026-01",
                        "fecha": datetime.date.today().strftime("%d/%m/%Y")
                    },
                    orden_compra_data=orden_compra_data
                )

                st.markdown("#### 👁️ Vista Previa de la Orden de Compra Oficial en PDF:")
                with st.container():
                    try:
                        import pymupdf
                        doc_oc = pymupdf.open(stream=pdf_oc_bytes, filetype="pdf")
                        for num_pag, pagina in enumerate(doc_oc, start=1):
                            pix = pagina.get_pixmap(dpi=150)
                            if len(doc_oc) > 1:
                                st.caption(f"📄 **Página {num_pag} de {len(doc_oc)}**")
                            st.image(pix.tobytes("png"), use_container_width=True)
                    except Exception:
                        import base64
                        b64_oc = base64.b64encode(pdf_oc_bytes).decode('utf-8')
                        st.markdown(f'<iframe src="data:application/pdf;base64,{b64_oc}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)

                col_oc_exp1, col_oc_exp2 = st.columns(2)
                with col_oc_exp1:
                    st.download_button(
                        label="📥 Descargar Orden de Compra en Excel (.xlsx)",
                        data=excel_oc_bytes,
                        file_name="Orden_Compra_Materiales_Bolimur.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                with col_oc_exp2:
                    st.download_button(
                        label="📥 Descargar Orden de Compra en PDF",
                        data=pdf_oc_bytes,
                        file_name="Orden_Compra_Materiales_Bolimur.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )


            with tab_doc_uni:
                st.header("📐 Esquema Unifilar Oficial para Industria (Región de Murcia - DGEAIM)")
                st.markdown("""
                **Documento Oficial para Memoria Técnica de Diseño (MTD) / Certificado de Instalación Eléctrica (CIE)**  
                Conforme a las directrices de la *Dirección General de Energía y Actividad Industrial y Minera de la Región de Murcia (CARM)* y el *Reglamento Electrotécnico para Baja Tensión (RD 842/2002)*.
                """)

                st.markdown(f"""
                <div style="border: 2px solid {card_border}; padding: 18px; border-radius: 8px; background-color: {card_bg}; color: {card_text_color}; margin-bottom: 20px;">
                    <h4 style="color: {card_title_color}; margin-top: 0;">🏛️ Datos Técnicos Oficiales del Suministro</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px; color: {card_text_color};">
                        <div>• <b>Titular / Emplazamiento:</b> Vivienda Residencial ({localidad})</div>
                        <div>• <b>Instalador Autorizado:</b> {instalador_nombre} (Lic: {n_licencia})</div>
                        <div>• <b>Potencia Prevista:</b> {pot_w_val:,} W ({grado_electr})</div>
                        <div>• <b>Tensión de Red:</b> Monofásico 230 V - 50 Hz</div>
                        <div>• <b>Interruptor General Automático (IGA):</b> {iga_amperaje} A (2P Curva C | Icn: 6 kA)</div>
                        <div>• <b>Protección Sobretensiones:</b> POP (Permanentes) + DPS Tipo 2 (Transitorias) ITC-BT-23</div>
                        <div>• <b>Derivación Individual:</b> 2x10 mm² Cu + TT 1x10 mm² ({tipo_cable_sel}) bajo tubo M32</div>
                        <div>• <b>Diferenciales de Cabecera:</b> {n_difs}x ID 2x40A / 30mA (Clase AC / A)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("📋 Ver Tabla Detallada de Circuitos Interiores Normalizados (ITC-BT-25)", expanded=False):
                    df_circ_vista = pd.DataFrame([
                        {
                            "Circuito": c["id"],
                            "Denominación y Destino": c["denominacion"],
                            "PIA (In / PdC)": f"{c['pia']} A (6 kA)",
                            "Diferencial": c["dif"],
                            "Sección Conductor": c["cable_sec"],
                            "Canalización / Tubo": c["tubo_diam"],
                            "L. Máx": f"{c['long_m']:.0f} m",
                            "CdT (%)": f"{c['cdt_pct']:.2f} %",
                            "P. Asignada": f"{c['pot_w']} W"
                        }
                        for c in circuitos_unifilar
                    ])
                    st.dataframe(df_circ_vista, use_container_width=True, hide_index=True)

                    st.caption("ℹ️ Estos mismos circuitos quedan normalizados y representados en el plano unifilar oficial inferior.")

                st.markdown("#### 👁️ Vista Previa en Pantalla del Esquema Unifilar Oficial en PDF:")
                st.info("💡 **Vista previa en alta resolución del plano oficial antes de imprimir o visar:**")
                with st.container():
                    try:
                        import pymupdf
                        doc_uni = pymupdf.open(stream=pdf_unifilar_bytes, filetype="pdf")
                        for num_pag, pagina in enumerate(doc_uni, start=1):
                            pix = pagina.get_pixmap(dpi=150)
                            if len(doc_uni) > 1:
                                st.caption(f"📄 **Página {num_pag} de {len(doc_uni)}**")
                            st.image(pix.tobytes("png"), use_container_width=True)
                    except Exception:
                        import base64
                        b64_u = base64.b64encode(pdf_unifilar_bytes).decode('utf-8')
                        st.markdown(f'<iframe src="data:application/pdf;base64,{b64_u}" width="100%" height="650" type="application/pdf"></iframe>', unsafe_allow_html=True)

                col_uni_b1, col_uni_b2 = st.columns([3, 1])
                with col_uni_b1:
                    st.download_button(
                        label="📥 🖨️ Descargar / Imprimir Esquema Unifilar Oficial para Industria (PDF)",
                        data=pdf_unifilar_bytes,
                        file_name="Esquema_Unifilar_Industria_Murcia_Bolimur.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                with col_uni_b2:
                    st.caption("✅ Formato homologado para adjuntar a MTD y CIE ante la DGEAIM de Murcia.")


            st.success("✅ ¡Cálculos, Orden de Compra, Presupuesto Comercial y Esquema Unifilar sincronizados con éxito!")

def renderizar():
    app()

if __name__ == "__main__":
    app()
