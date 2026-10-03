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

def exportar_excel_presupuesto(df_comercial, subtotal, iva_pct, cuota_iva, total, instalador_info, df_orden_compra=None, total_compra_neto=0.0, total_compra_con_iva=0.0):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_comercial.to_excel(writer, sheet_name='Presupuesto Comercial', index=False)
        df_resumen = pd.DataFrame([
            {"Concepto": "Subtotal Comercial Neto", "Importe (€)": round(subtotal, 2)},
            {"Concepto": f"IVA ({iva_pct}%)", "Importe (€)": round(cuota_iva, 2)},
            {"Concepto": "TOTAL PRESUPUESTO", "Importe (€)": round(total, 2)}
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

def exportar_excel_orden_compra(df_orden_compra, total_neto, cuota_iva, total_con_iva, proyecto_info):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_orden_compra.to_excel(writer, sheet_name='Orden de Compra Acopio', index=False)
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
    with st.sidebar.expander("🌐 Asistente Web para Actualizar Precios"):
        st.markdown("""
        **¿Falta algún artículo o deseas actualizar precios desde la web?**
        
        Puedes instruirme directamente en el chat en cualquier momento:
        - 🛒 *"Busca en la web de Obramat el precio actual de [artículo] y actualízalo en el Excel"*
        - 🏬 *"Revisa en la web de Leroy Merlin el precio de [artículo] e incorpóralo a la base de datos"*
        
        Consultaré la tienda oficial en tiempo real, obtendré la referencia (SKU), descripción exacta y precio real, y lo añadiré automáticamente a `base_datos_precio_oficial.xlsx`.
        """)
        art_solic = st.text_input("Artículo que deseas actualizar:", placeholder="Ej: Tubo corrugado M25 libre de halógenos", key="input_web_update")
        tienda_solic = st.selectbox("Tienda oficial a consultar:", ["Obramat", "Leroy Merlin", "Sonepar", "Electro Material"], key="sel_tienda_web")
        if st.button("🔍 Solicitar Búsqueda Web al Asistente", key="btn_pedir_web"):
            if art_solic:
                st.info(f"💡 **Indícamelo en el chat:** `Actualiza en la base de datos el artículo '{art_solic}' buscando en la web de {tienda_solic}` y lo actualizaré de inmediato.")
            else:
                st.warning("Escribe el nombre del artículo que deseas consultar.")

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
    st.subheader("⚙️ Parámetros de Potencia, Escalones IGA y Configuración de Circuitos")

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

    st.info(f"📋 **Configuración REBT:** Electrificación **{grado_electr}** | **IGA Oficial: {iga_amperaje} A** | Circuitos mínimos: **{num_circuitos_base}**")

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

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        margen_comercial = st.number_input(
            "Margen Comercial General (%)", 
            min_value=0, max_value=200, value=50, step=5,
            help="Puedes escribir directamente el número o usar las flechas para subir/bajar de 5 en 5."
        )
    with col_m2:
        porc_garantia = st.number_input(
            "Colchón de Garantía en Materiales (%)", 
            min_value=0, max_value=100, value=10, step=1,
            help="Colchón adicional para imprevistos en materiales."
        )
    with col_m3:
        iva_sel = st.selectbox("IVA Aplicado al Cliente", [10, 21], index=0)

    st.markdown("#### 🧱 Criterio de Rozas, Techos, Operarios y Jornadas de Trabajo")
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

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        precio_hora = st.number_input("Precio Mano de Obra (€/h neto)", min_value=10.0, max_value=60.0, value=25.0, step=1.0)
    with col_c2:
        num_operarios = st.number_input("Nº Operarios", min_value=1, max_value=5, value=1, step=1)
    with col_c3:
        horas_jornada = st.number_input("Horas por Jornada / Día", min_value=4.0, max_value=12.0, value=8.0, step=0.5)

    st.markdown("---")

    # ==========================================
    # GESTIÓN DINÁMICA DE ESTANCIAS Y MÉTRICA DE m²
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

    # Encabezados de las columnas de estancias
    col_hdr = st.columns([3, 1.5, 1.5, 2, 0.8, 0.8])
    with col_hdr[0]:
        st.markdown("**🏠 Estancia**")
    with col_hdr[1]:
        st.markdown("**📐 Superficie (m²)**")
    with col_hdr[2]:
        st.markdown("**📏 Altura (m)**")
    with col_hdr[3]:
        st.markdown("**⚡ Distancia al Cuadro (m)**")
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

    st.markdown("---")

    # ==========================================
    # FISCALIZADOR TÉCNICO REBT (INSPECTOR IA)
    # ==========================================
    st.subheader("🛡️ Inspector Técnico REBT (Fiscalización en Vivo - ITC-BT-25)")

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

    if st.button("🚀 Calcular Presupuesto, Distancias y Generar Paneles", type="primary"):
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

            comercial_estancias.append({
                "Estancia": est["nombre"],
                "Superficie": f"{m2} m²",
                "Detalle Comercial": f"Instalación REBT ({potencia_prevista_kw}) | Techo: {'Falso Techo' if 'Falso Techo' in tipo_techo else 'Macizo'}",
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
        horas_totales_equipo = horas_totales_obra / num_operarios
        dias_estimados = horas_totales_equipo / horas_jornada

        n_difs = 2 if grado_electr == "Elevada" else 1
        n_pias = max(num_circuitos_base, len(estancias_activas))
        coste_cuadro_neto = p_iga + (n_difs * p_id) + (n_pias * p_pia) + p_caja_cuadro
        venta_cuadro_neto = coste_cuadro_neto * mult_comercial * mult_garantia_mat
        benef_cuadro = venta_cuadro_neto - coste_cuadro_neto

        subtotal_general_neto = subtotal_neto_comercial + venta_cuadro_neto
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

        # 1. Mecanismos
        for (nom_m, desc_m, p_m, prov_m, fila_m, ok_m), cant_m in global_mecanismos_dict.items():
            if cant_m > 0:
                categorias_orden_compra["🔲 1. Mecanismos y Marcos"].append({
                    "articulo": nom_m,
                    "desc_exacta": desc_m,
                    "proveedor": prov_m,
                    "cantidad": cant_m,
                    "unidad": "ud",
                    "precio_unitario": p_m,
                    "subtotal": round(cant_m * p_m, 2),
                    "en_bd": ok_m,
                    "categoria_bd": "Mecanismos",
                    "marca_bd": "Efapel" if ("efapel" in str(serie_mecanismos).lower() or "racional" in str(serie_mecanismos).lower()) else str(serie_mecanismos).split()[0]
                })
        if global_marcos_uds > 0:
            categorias_orden_compra["🔲 1. Mecanismos y Marcos"].append({
                "articulo": "Marcos Embellecedores",
                "desc_exacta": desc_marco,
                "proveedor": prov_marco,
                "cantidad": global_marcos_uds,
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
            "marca_protecciones": marca_protecciones
        }

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

        # ==========================================
        # SELECTOR DE MODO DE VISTA E IMPRESIÓN
        # ==========================================
        st.markdown("---")
        modo_impresion = st.radio(
            "🖨️ SELECCIONA EL MODO DE VISTA:",
            [
                "🛠️ 1. Panel Interno y Rentabilidad (Exclusivo para ti - Autónomo)",
                "🛒 2. Orden de Compra y Acopio de Materiales (Almacén / Tienda)",
                "📄 3. Vista Comercial (Para entregar al Cliente)"
            ],
            horizontal=True
        )
        st.markdown("---")

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
                    st.markdown("Ingresa los datos reales de compra para incorporarlos permanentemente a `base_datos_precio_oficial.xlsx`:")
                    with st.form("form_actualizar_no_catalogados_panel"):
                        articulos_a_guardar = []
                        for idx_no, art_no in enumerate(items_no_catalogados):
                            st.markdown(f"**Artículo:** `{art_no['articulo']}`")
                            col_u1, col_u2, col_u3, col_u4 = st.columns([3, 2, 2, 2])
                            with col_u1:
                                desc_edit = st.text_input("Descripción Real / Nombre Comercial", value=art_no['articulo'], key=f"desc_nc_{idx_no}")
                            with col_u2:
                                prov_edit = st.selectbox("Tienda / Proveedor", ["Obramat", "Leroy Merlin", "Sonepar", "Electro Material", "General"], key=f"prov_nc_{idx_no}")
                            with col_u3:
                                precio_edit = st.number_input("Precio S/IVA (€)", value=float(art_no['precio_unitario']), min_value=0.01, step=0.05, format="%.2f", key=f"p_nc_{idx_no}")
                            with col_u4:
                                sku_edit = st.text_input("Ref / SKU", value=f"REF-{art_no['articulo'][:4].upper()}", key=f"sku_nc_{idx_no}")
                            
                            articulos_a_guardar.append({
                                "Nivel de Gama / Aplicación": "Estándar",
                                "Familia / Categoria": art_no.get("categoria_bd", "General"),
                                "Marca": art_no.get("marca_bd", prov_edit),
                                "Serie / Gama": "Estándar",
                                "Proveedor / Tienda": prov_edit,
                                "Código SKU / Ref": sku_edit,
                                "Descripción Exacta del Artículo": desc_edit,
                                "Unidad": art_no.get("unidad", "ud"),
                                "Precio S/IVA (€)": precio_edit,
                                "IVA (%)": 21,
                                "Precio C/IVA (€)": round(precio_edit * 1.21, 2),
                                "Observaciones / Aplicación Técnica": "Registrado desde actualizador de acopio"
                            })
                            st.markdown("---")
                        
                        btn_guardar_bd = st.form_submit_button("💾 Guardar Todos en Excel y Recalcular Presupuesto", type="primary")
                        if btn_guardar_bd:
                            try:
                                df_act = pd.read_excel('base_datos_precio_oficial.xlsx')
                                for nuevo_art in articulos_a_guardar:
                                    nuevo_art["ID"] = f"ART-{len(df_act)+1:04d}"
                                    df_act = pd.concat([df_act, pd.DataFrame([nuevo_art])], ignore_index=True)
                                df_act.to_excel('base_datos_precio_oficial.xlsx', index=False)
                                cargar_precios_excel.clear()
                                st.success("✅ ¡Artículos guardados en Excel correctamente! Recalculando...")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error al guardar en Excel: {ex}")

            col_btn_ac1, col_btn_ac2 = st.columns(2)
            with col_btn_ac1:
                st.download_button(
                    label="📄 Descargar Reporte de Compras en PDF",
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
                                st.success(f"✅ ¡Artículo '{m_desc}' añadido con ID `{n_id}`!")
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

            # Filtro por tienda/proveedor
            tiendas_unicas = sorted(list(df_orden_compra["Tienda / Proveedor"].dropna().unique()))
            filtro_tienda = st.selectbox("🏬 Filtrar por Tienda / Proveedor:", ["Todos los Proveedores"] + tiendas_unicas)

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

        else:
            st.header("📄 Vista Comercial: Presupuesto para el Cliente")
            st.markdown(f"""
            <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff;">
                <h3 style="color: #0369a1; margin-top: 0;">{empresa_nombre}</h3>
                <p><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
                <hr style="border: 1px solid #bae6fd;">
                <p><b>Presupuesto N°:</b> 2026-0901 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Fecha:</b> {datetime.date.today().strftime("%B %Y")}</p>
                <p><b>Objeto:</b> Instalación Eléctrica REBT ({potencia_prevista_kw}) con Mecanismos <b>{serie_mecanismos}</b> y Protecciones <b>{marca_protecciones}</b></p>
            </div>
            """, unsafe_allow_html=True)

            df_comercial = pd.DataFrame(comercial_estancias)
            st.dataframe(df_comercial, use_container_width=True)

            excel_bytes = exportar_excel_presupuesto(
                df_comercial, subtotal_general_neto, iva_sel, cuota_iva, total_cliente,
                {"empresa": empresa_nombre, "instalador": instalador_nombre, "licencia": n_licencia},
                df_orden_compra=df_orden_compra,
                total_compra_neto=total_mat_global_neto,
                total_compra_con_iva=total_mat_con_iva
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
                    "df_comercial": df_comercial,
                    "subtotal_neto": subtotal_general_neto,
                    "iva_pct": iva_sel,
                    "cuota_iva": cuota_iva,
                    "total_cliente": total_cliente,
                    "total_puntos": total_puntos_mecanismos,
                    "precio_medio_punto": precio_medio_por_punto,
                    "serie_mecanismos": serie_mecanismos,
                    "marca_protecciones": marca_protecciones,
                    "potencia_kw": potencia_prevista_kw
                }
            )

            st.markdown("#### 👁️ Vista Previa en Pantalla del Presupuesto Oficial PDF:")
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
                    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)

            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                st.download_button(
                    label="📥 Descargar Presupuesto en Excel (.xlsx)",
                    data=excel_bytes,
                    file_name="Presupuesto_Electrico_Bolimur.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with col_exp2:
                st.download_button(
                    label="📥 Descargar Presupuesto Oficial en PDF",
                    data=pdf_bytes_pres,
                    file_name="Presupuesto_Oficial_Bolimur.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            st.markdown(f"""
            <div style="text-align: right; font-size: 18px; background-color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #94a3b8; margin-top: 15px;">
                <p><b>Subtotal Comercial Neto:</b> {subtotal_general_neto:.2f} €</p>
                <p><b>IVA ({iva_sel}%):</b> {cuota_iva:.2f} €</p>
                <h2 style="color: #16a34a; margin: 0;">TOTAL PRESUPUESTO CLIENTE: {total_cliente:.2f} €</h2>
            </div>
            """, unsafe_allow_html=True)

        st.success("✅ ¡Cálculos, Orden de Compra y Presupuesto Comercial sincronizados con éxito!")

def renderizar():
    app()

if __name__ == "__main__":
    app()
