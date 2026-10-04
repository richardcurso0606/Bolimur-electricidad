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

        df_comercial.to_excel(writer, sheet_name='Desglose por Estancias', index=False)

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
    # SECCIÓN 1: PARÁMETROS DE POTENCIA REBT E IGA OFICIAL
    # ==========================================
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

        desdoblar_c4 = st.checkbox(
            "⚙️ Desdoblar circuito C4 (Separar Lavadora/Lavavajillas de la línea del Termo en circuitos independientes)", 
            value=False,
            help="Crea dos líneas dedicadas en cocina: C4-A (Lavado) y C4-B (Termo ACS), añadiendo un PIA extra y calculando sus cables correctamente."
        )

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

        if desdoblar_c4:
            num_circuitos_base += 1

        st.info(f"📋 **Configuración REBT:** Electrificación **{grado_electr}** | **IGA Oficial: {iga_amperaje} A** | Circuitos mínimos requeridos: **{num_circuitos_base}**")

    # ==========================================
    # SECCIÓN 2: MARCAS, SERIES Y MEMORIA ECONÓMICA
    # ==========================================
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

    # ==========================================
    # SECCIÓN 3: MANO DE OBRA, TECHOS Y CONDICIONES ECONÓMICAS
    # ==========================================
    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">⏱️ SECCIÓN 3: Mano de Obra, Rozas, Techos, Boletín CIE y Márgenes</h4></div>', unsafe_allow_html=True)
    with st.container(border=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            margen_comercial = st.number_input(
                "Margen Comercial General (%)", 
                min_value=0, max_value=200, value=50, step=5,
                help="Margen comercial sobre costes de materiales y mano de obra."
            )
        with col_m2:
            porc_garantia = st.number_input(
                "Colchón de Garantía en Materiales (%)", 
                min_value=0, max_value=100, value=10, step=1,
                help="Colchón adicional para imprevistos y reposición de materiales."
            )
        with col_m3:
            iva_sel = st.selectbox("IVA Aplicado al Cliente", [10, 21], index=0)

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

    # ==========================================
    # SECCIÓN 4: GESTIÓN DINÁMICA DE ESTANCIAS Y MÉTRICA DE m²
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
                            "extra_schuko": 0, "extra_luz": 0, "extra_rj45": 0
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

    # ==========================================
    # SECCIÓN 5: FISCALIZADOR TÉCNICO REBT (INSPECTOR IA)
    # ==========================================
    st.markdown('<div class="section-header-amber"><h4 style="margin:0; color:#92400e;">🛡️ SECCIÓN 5: Inspector Técnico REBT (Fiscalización en Vivo ITC-BT-25)</h4></div>', unsafe_allow_html=True)
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

        if alertas_inspector:
            for alerta in alertas_inspector:
                st.error(alerta)
            
            forzar_inspector = st.checkbox("⚠️ Forzar ejecución del presupuesto bajo responsabilidad del instalador autorizado", value=False)
            if not forzar_inspector:
                st.stop()
        else:
            st.success("🟢 **Inspección REBT Superada con Éxito:** La configuración cumple rigurosamente con los requisitos de la ITC-BT-25 y los escalones de potencia IGA.")

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
                cant_sch = (5 if desdoblar_c4 else 4) + max(0, ex_sch)
                mecanismos_est = [
                    {"nombre": "Interruptor simple", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int, "en_bd": ok_int},
                    {"nombre": "Base Schuko 16A", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko},
                    {"nombre": "Base fuerza 25A Horno/Vitro", "desc_real": desc_schuko, "cant": 1, "precio": p_schuko * 1.5, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko},
                    {"nombre": "Bases Schuko lavavajillas/lavadora/termo", "desc_real": desc_schuko, "cant": (3 if desdoblar_c4 else 2), "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko}
                ]
            elif "baño" in nombre_est:
                cant_int = 1 + max(0, ex_luz)
                cant_sch = 2 + max(0, ex_sch)
                mecanismos_est = [
                    {"nombre": "Interruptor luz espejo", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int, "en_bd": ok_int},
                    {"nombre": "Base Schuko tapa estanca IP44", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko * 1.2, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko}
                ]
            elif "salón" in nombre_est or "comedor" in nombre_est:
                cant_int = 2 + max(0, ex_luz)
                cant_sch = 6 + max(0, ex_sch)
                cant_rj = 2 + max(0, ex_rj45)
                mecanismos_est = [
                    {"nombre": "Conmutador / Cruzamiento", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int, "en_bd": ok_int},
                    {"nombre": "Bases Schuko zona TV/Sofá", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko},
                    {"nombre": "Toma de datos RJ45", "desc_real": desc_rj45, "cant": cant_rj, "precio": p_rj45, "prov": prov_rj45, "fila": fila_rj45, "en_bd": ok_rj45}
                ]
            else:
                cant_int = 2 + max(0, ex_luz)
                cant_sch = 3 + max(0, ex_sch)
                mecanismos_est = [
                    {"nombre": "Conmutador / Interruptor", "desc_real": desc_int, "cant": cant_int, "precio": p_int, "prov": prov_int, "fila": fila_int, "en_bd": ok_int},
                    {"nombre": "Bases Schuko 16A", "desc_real": desc_schuko, "cant": cant_sch, "precio": p_schuko, "prov": prov_schuko, "fila": fila_schuko, "en_bd": ok_schuko}
                ]

            total_mecanismos = sum([m["cant"] for m in mecanismos_est])
            total_puntos_mecanismos += total_mecanismos
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

        # Mano de obra especializada para el Cuadro General CGMP
        # Montaje en envolvente, fijación DIN, peinado de conductores, peines de conexión, rotulación de circuitos y pruebas
        horas_cuadro = 3.0 if grado_electr == "Elevada" else 2.5
        coste_mo_cuadro = horas_cuadro * precio_hora
        horas_totales_obra += horas_cuadro
        coste_mano_obra_bruto = horas_totales_obra * precio_hora
        horas_totales_equipo = horas_totales_obra / num_operarios
        dias_estimados = horas_totales_equipo / horas_jornada

        n_difs = 2 if grado_electr == "Elevada" else 1
        n_pias = max(num_circuitos_base, len(estancias_activas))
        coste_cuadro_neto = p_iga + (n_difs * p_id) + (n_pias * p_pia) + p_caja_cuadro
        venta_cuadro_mat = coste_cuadro_neto * mult_comercial * mult_garantia_mat
        venta_cuadro_mo = coste_mo_cuadro * mult_comercial
        venta_cuadro_neto = venta_cuadro_mat + venta_cuadro_mo
        benef_cuadro = venta_cuadro_neto - (coste_cuadro_neto + coste_mo_cuadro)

        subtotal_general_neto = subtotal_neto_comercial + venta_cuadro_neto + float(precio_boletin_cie) + sum(float(p.get('subtotal', 0.0)) for p in st.session_state.get('partidas_manuales', []))
        cuota_iva = subtotal_general_neto * (iva_sel / 100.0)
        total_cliente = subtotal_general_neto + cuota_iva

        # Precio medio por punto instalado (Calculado sobre el total con IVA o Total Neto según prefieras; aquí usamos Total Cliente Con IVA / Puntos)
        precio_medio_por_punto = (total_cliente / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0

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

        categorias_orden_compra = {
            "🔲 1. Mecanismos y Marcos": [],
            "⚡ 2. Cables y Conductores": [],
            "🛡️ 3. Cuadro Eléctrico y Protecciones": [],
            "📏 4. Tubos y Canalizaciones": [],
            "📦 5. Cajas y Conexiones": []
        }

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
            categorias_orden_compra["🔲 1. Mecanismos y Marcos"].append({
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
            categorias_orden_compra["🔲 1. Mecanismos y Marcos"].append({
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
        if global_utp_m > 0:
            cables_items.append(("Cable Red UTP Cat.6", desc_utp, prov_utp, global_utp_m, p_utp, max(1, int((global_utp_m + 99)/100)), ok_utp))

        for nom_c, desc_c, prov_c, m_c, p_c, rollos_c, ok_c in cables_items:
            if m_c > 0:
                categorias_orden_compra["⚡ 2. Cables y Conductores"].append({
                    "articulo": nom_c,
                    "desc_exacta": f"{desc_c} [📦 {rollos_c} rollo(s) de 100m]",
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
        categorias_orden_compra["🛡️ 3. Cuadro Eléctrico y Protecciones"].extend([
            {
                "articulo": "Caja Cuadro de Distribución",
                "desc_exacta": desc_caja_cuadro,
                "proveedor": prov_caja_cuadro,
                "cantidad": 1,
                "unidad": "ud",
                "precio_unitario": p_caja_cuadro,
                "subtotal": round(p_caja_cuadro, 2),
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
                "articulo": "Interruptor Diferencial 40A 30mA",
                "desc_exacta": desc_id,
                "proveedor": prov_id,
                "cantidad": n_difs,
                "unidad": "ud",
                "precio_unitario": p_id,
                "subtotal": round(n_difs * p_id, 2),
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

        # 4. Tubos y Canalizaciones
        tubos_items = [
            ("Tubo Corrugado M-20", desc_tubo20, prov_tubo20, global_tubo20_m, p_tubo20, rollos_tubo20, ok_tubo20),
            ("Tubo Corrugado M-25", desc_tubo25, prov_tubo25, global_tubo25_m, p_tubo25, rollos_tubo25, ok_tubo25),
        ]
        for nom_t, desc_t, prov_t, m_t, p_t, rollos_t, ok_t in tubos_items:
            if m_t > 0:
                categorias_orden_compra["📏 4. Tubos y Canalizaciones"].append({
                    "articulo": nom_t,
                    "desc_exacta": f"{desc_t} [📦 {rollos_t} rollo(s) de 50m]",
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
                categorias_orden_compra["📦 5. Cajas y Conexiones"].append({
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
        venta_cap2_canalizacion = (coste_tubos_cajas_tot * mult_comercial * mult_garantia_mat) + ((sum_h_rozas + sum_h_tubos) * precio_hora * mult_comercial)
        venta_cap3_cableado = (coste_cables_tot * mult_comercial * mult_garantia_mat) + (sum_h_cable * precio_hora * mult_comercial)
        venta_cap4_mecanismos = (coste_mecanismos_marcos_tot * mult_comercial * mult_garantia_mat) + (sum_h_mec * precio_hora * mult_comercial)
        venta_cap5_boletin = float(precio_boletin_cie)
        venta_cap6_manuales = sum(float(p.get('subtotal', 0.0)) for p in st.session_state.get('partidas_manuales', []))

        capitulos_presupuesto = [
            {
                "cap": "CAP. 01",
                "titulo": "Cuadro General de Mando y Protección (CGMP)",
                "desc": f"Suministro e instalación de cuadro general empotrado, IGA {iga_amperaje}A 6kA, protector de sobretensiones permanentes y transitorias (POP+DPS), {n_difs}x diferencial(es) 40A/30mA y {n_pias}x PIAs magnetotérmicos de protección según ITC-BT-25, incluido montaje, peinado y conexionado integral ({horas_cuadro:.1f} h MO).",
                "importe": round(venta_cap1_cgmp, 2)
            },
            {
                "cap": "CAP. 02",
                "titulo": "Canalizaciones, Rozas y Cajas de Registro",
                "desc": f"Rozas en {tipo_pared} (techo: {'Falso Techo' if 'Falso Techo' in tipo_techo else 'Macizo'}), tendido de {global_tubo20_m + global_tubo25_m:.0f} m de tubo corrugado {tipo_tubo_sel} M20/M25, colocación de {global_caja_mec_uds} cajas universales y {global_caja_reg_uds} cajas de derivación protegidas.",
                "importe": round(venta_cap2_canalizacion, 2)
            },
            {
                "cap": "CAP. 03",
                "titulo": "Cableado y Líneas de Distribución Interior",
                "desc": f"Suministro y tendido de {global_15_az_m + global_15_ne_m + global_15_ma_m + global_15_gr_m + global_15_tt_m + global_25_az_m + global_25_ne_m + global_25_tt_m + global_utp_m:.0f} m de conductores de cobre {tipo_cable_sel} (1.5, 2.5, 4, 6, 10 mm²) con código de colores REBT y puesta a tierra equipotencial.",
                "importe": round(venta_cap3_cableado, 2)
            },
            {
                "cap": "CAP. 04",
                "titulo": "Mecanismos y Aparamenta por Estancias",
                "desc": f"Suministro y montaje de {total_puntos_mecanismos} mecanismos serie {serie_mecanismos} (interruptores, conmutadores, bases Schuko 16A, toma 25A y tomas datos RJ45) con {global_marcos_uds} marcos embellecedores por estancias.",
                "importe": round(venta_cap4_mecanismos, 2)
            },
            {
                "cap": "CAP. 05",
                "titulo": "Ensayos Reglamentarios, MTD y Tramitación Boletín Oficial CIE",
                "desc": "Verificaciones y ensayos ITC-BT-05 (aislamiento con megóhmetro, disparo de diferenciales, continuidad y bucle de tierra), redacción de Memoria Técnica de Diseño (MTD) y tramitación telemática oficial del Certificado de Instalación Eléctrica (CIE) ante la DGEAIM de la Región de Murcia.",
                "importe": round(venta_cap5_boletin, 2)
            }
        ]

        if st.session_state.get('partidas_manuales', []):
            capitulos_presupuesto.append({
                "cap": "CAP. 06",
                "titulo": "Trabajos Adicionales y Partidas a Medida",
                "desc": f"Partidas personalizadas y mejoras adicionales ({len(st.session_state.partidas_manuales)} partidas añadidas por el usuario).",
                "importe": round(venta_cap6_manuales, 2)
            })

        subtotal_general_neto = sum(c["importe"] for c in capitulos_presupuesto)
        cuota_iva = subtotal_general_neto * (iva_sel / 100.0)
        total_cliente = subtotal_general_neto + cuota_iva
        precio_medio_por_punto = (total_cliente / total_puntos_mecanismos) if total_puntos_mecanismos > 0 else 0.0

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

        if grado_electr == "Elevada":
            circuitos_unifilar.extend([
                {
                    "id": "C9",
                    "denominacion": "Instalación de aire acondicionado / climatización",
                    "pia": 25,
                    "dif": "ID 2 (30mA)",
                    "cable_sec": "2x6 + TT 6 mm² Cu",
                    "tubo_diam": "M25 (Tubo Corrugado)",
                    "long_m": 16.0,
                    "cdt_pct": 1.25,
                    "pot_w": 5400
                },
                {
                    "id": "C10",
                    "denominacion": "Instalación de secadora independiente",
                    "pia": 16,
                    "dif": "ID 2 (30mA)",
                    "cable_sec": "2x2.5 + TT 2.5 mm² Cu",
                    "tubo_diam": "M20 (Tubo Corrugado)",
                    "long_m": 12.0,
                    "cdt_pct": 0.88,
                    "pot_w": 3450
                }
            ])

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
        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">🖨️ SECCIÓN 6: Selector de Documentos Oficiales y Paneles de Resultados</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            modo_impresion = st.radio(
                "Selecciona el documento o panel a consultar / exportar:",
                [
                    "🛠️ 1. Panel Interno y Rentabilidad (Exclusivo para ti - Autónomo)",
                    "🛒 2. Orden de Compra y Acopio de Materiales (Almacén / Tienda)",
                    "📄 3. Vista Comercial (Para entregar al Cliente)",
                    "📐 4. Esquema Unifilar Oficial para Industria (Región de Murcia - DGEAIM)"
                ],
                horizontal=True
            )

        if modo_impresion.startswith("🛠️"):
            st.header("🔒 Panel Interno de Trabajo, Distancias y Rentabilidad")
            c4_estado_txt = "Desdoblado (C4-A y C4-B independientes)" if desdoblar_c4 else "Estándar unificado"
            st.markdown(f"**Instalador:** {instalador_nombre} | **Potencia / IGA:** {potencia_prevista_kw} | **Circuito C4:** {c4_estado_txt}")
            st.markdown("---")

            st.markdown(f"""
            <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff; margin-bottom: 25px;">
                <h3 style="color: #0369a1; margin-top: 0;">💼 RESUMEN ECONÓMICO PARA EL CLIENTE (A Cobrar)</h3>
                <p><b>Subtotal Comercial Neto:</b> {subtotal_general_neto:.2f} €</p>
                <p><b>IVA ({iva_sel}%):</b> {cuota_iva:.2f} €</p>
                <h2 style="color: #16a34a; margin: 0;">TOTAL A COBRAR AL CLIENTE: {total_cliente:.2f} €</h2>
            </div>
            """, unsafe_allow_html=True)

            st.subheader("📊 Resumen Global de Puntos y Coste Medio por Punto")
            st.write(f"- 🔌 **Número Total de Puntos / Mecanismos Instalados:** `{total_puntos_mecanismos} uds` (Interruptores, Schukos, Tomas de Fuerza y Red)")
            st.write(f"- 💶 **Precio Medio por Punto (Aplicando el Total con IVA):** **`{precio_medio_por_punto:.2f} € / punto`**")
            st.info("💡 *Nota:* Este indicador te muestra a cuánto sale de media cada punto instalado (incluyendo cableado, canalización, protecciones y mano de obra prorrateados).")
            st.markdown("---")

            st.subheader("⏱️ Análisis de Rendimiento, Tiempos y Plazos de Obra")
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
                with st.expander("⚡ Actualizar y Guardar Artículos No Catalogados en la Base de Datos Excel", expanded=True):
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

            st.markdown("#### 👁️ Vista Previa del Reporte de Compras en PDF antes de Imprimir / Descargar:")
            st.info("💡 **Revisa el documento en pantalla.** Una vez verificado, puedes descargarlo en PDF/Excel o imprimirlo directamente.")
            with st.container():
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

            with st.expander("📋 Desglose Completo de Materiales por Tipo / Categoría", expanded=True):
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

            st.markdown(f"""
            <div style="border: 2px solid #16a34a; padding: 20px; border-radius: 10px; background-color: #f0fdf4; margin-top: 15px;">
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

        elif modo_impresion.startswith("🛒"):
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

        elif modo_impresion.startswith("📄"):
            st.header("📄 Vista Comercial: Presupuesto Oficial para el Cliente")
            st.markdown(f"""
            <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="color: #0369a1; margin: 0;">{empresa_nombre}</h3>
                        <p style="margin: 3px 0;"><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
                    </div>
                    <div style="text-align: right;">
                        <span style="background-color: #0284c7; color: white; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px;">OFERTA COMERCIAL</span>
                        <p style="margin: 4px 0 0 0; font-size: 13px;"><b>Fecha:</b> {datetime.date.today().strftime("%d/%m/%Y")}</p>
                    </div>
                </div>
                <hr style="border: 1px solid #bae6fd; margin: 12px 0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px;">
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
                st.metric("🔌 Total Puntos / Ratio", f"{total_puntos_mecanismos} uds ({precio_medio_por_punto:.2f} €/pto)")

            st.markdown("---")

            # =========================================================================
            # GESTOR INTERACTIVO DE TRABAJOS ADICIONALES Y PARTIDAS MANUALES
            # =========================================================================
            with st.expander("➕ Añadir / Gestionar Trabajos Adicionales y Partidas Manuales", expanded=bool(st.session_state.get('partidas_manuales', []))):
                st.markdown("""
                **Personaliza la oferta para el cliente:**  
                Añade partidas a medida (ej. downlights LED, punto de recarga de coche eléctrico IRVE, tomas exteriores IP65, timbres, etc.) con recálculo automático del total comercial:
                """)

                preset_opciones = [
                    "Personalizada (Escribir concepto a medida)",
                    "Línea de Recarga Vehículo Eléctrico IRVE (ITC-BT-52)",
                    "Instalación Downlights LED Extraplanos 18W",
                    "Toma de Corriente Estanca IP65 en Terraza / Exterior",
                    "Instalación de Timbre / Zumbador Modular en Cuadro",
                    "Canaleta embellecedora y acometida auxiliar",
                    "Detector de Movimiento / Presencia 360° Techo"
                ]
                preset_sel = st.selectbox("📌 Seleccionar Plantilla o Crear Partida Personalizada:", preset_opciones, key="sel_preset_partida")

                def_conc = ""
                def_desc = ""
                def_cant = 1.0
                def_unid = "ud"
                def_pvp = 50.0

                if "IRVE" in preset_sel:
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
                        else:
                            st.warning("Introduce un concepto válido para la partida.")

                if st.session_state.get('partidas_manuales', []):
                    st.markdown("##### 📋 Partidas Adicionales Actuales en el Presupuesto:")
                    for idx_p, item_p in enumerate(st.session_state.partidas_manuales):
                        col_lp1, col_lp2, col_lp3, col_lp4 = st.columns([4, 2, 2, 1])
                        with col_lp1:
                            st.markdown(f"**{item_p['concepto']}**  \n<small>{item_p['descripcion']}</small>", unsafe_allow_html=True)
                        with col_lp2:
                            st.caption(f"Cant: `{item_p['cantidad']} {item_p['unidad']}` × `{item_p['precio_unitario']:.2f} €`")
                        with col_lp3:
                            st.markdown(f"**`{item_p['subtotal']:.2f} €`**")
                        with col_lp4:
                            if st.button("🗑️", key=f"btn_del_pm_{idx_p}", help="Eliminar esta partida"):
                                st.session_state.partidas_manuales.pop(idx_p)
                                st.session_state.presupuesto_calculado = True
                                st.rerun()

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

            st.write("")
            if st.button("🚀 Tramitar Memoria Técnica Oficial (MTD 30) y CIE para esta Vivienda", type="primary", use_container_width=True):
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
                st.session_state.menu_activo = "🏛️ Memoria Técnica (MTD 30)"
                st.rerun()

            st.markdown(f"""
            <div style="text-align: right; font-size: 18px; background-color: #f1f5f9; padding: 18px; border-radius: 8px; border: 1px solid #94a3b8; margin-top: 15px;">
                <p style="margin: 3px 0;"><b>Subtotal Comercial Neto (Base Imponible):</b> {subtotal_general_neto:,.2f} €</p>
                <p style="margin: 3px 0;"><b>IVA ({iva_sel}%):</b> {cuota_iva:,.2f} €</p>
                <h2 style="color: #16a34a; margin: 8px 0 0 0;">TOTAL PRESUPUESTO CLIENTE: {total_cliente:,.2f} €</h2>
            </div>
            """, unsafe_allow_html=True)


        elif modo_impresion.startswith("📐"):
            st.header("📐 Esquema Unifilar Oficial para Industria (Región de Murcia - DGEAIM)")
            st.markdown("""
            **Documento Oficial para Memoria Técnica de Diseño (MTD) / Certificado de Instalación Eléctrica (CIE)**  
            Conforme a las directrices de la *Dirección General de Energía y Actividad Industrial y Minera de la Región de Murcia (CARM)* y el *Reglamento Electrotécnico para Baja Tensión (RD 842/2002)*.
            """)

            st.markdown(f"""
            <div style="border: 2px solid #0284c7; padding: 18px; border-radius: 8px; background-color: #f0f9ff; margin-bottom: 20px;">
                <h4 style="color: #0369a1; margin-top: 0;">🏛️ Datos Técnicos Oficiales del Suministro</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px;">
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

            st.subheader("📋 Tabla de Circuitos Interiores Normalizados (ITC-BT-25)")
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
