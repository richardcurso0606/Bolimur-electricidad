# -*- coding: utf-8 -*-
"""
Módulo de Presupuesto Rápido con IA y Dictado por Micrófono (Bolimur Instant Work).
Diseñado para el instalador electricista de calle que necesita cotizar un trabajo
urgente en segundos a pie de obra o en la furgoneta.
Permite dictar por voz, ver la transcripción en pantalla, modificarla,
visualizar la memoria técnica completa determinada por la IA y generar
el presupuesto detallado con escandallo de materiales, mano de obra y régimen de IVA.
"""

import streamlit as st
import pandas as pd
import datetime
import base64
import json
import re
import os
import io
import unicodedata
import urllib.parse
import requests
from modulos import auditor_ia_rebt
from modulos import asistente_ia_rebt


def normalizar_texto(s: str) -> str:
    """Normaliza texto eliminando tildes y caracteres especiales para búsqueda tolerante."""
    return "".join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn').lower()


def es_servicio_o_logistica(texto: str) -> bool:
    """Detecta si una partida representa un servicio, tiempo invertido, transporte, desplazamiento o gestión,
    para evitar tratarlo como un material físico de ferretería."""
    if not texto:
        return False
    t = normalizar_texto(texto)
    frases_clave = [
        "tiempo invertido", "comprar material", "compra de material", "compra material",
        "desplazamiento", "kilometraje", "portes", "tramitacion", "gestion de compra",
        "gestion de acopio", "servicio tecnico", "mano de obra", "visita tecnica",
        "boletin electrico", "certificado de instalacion", "hora extra", "ayudante",
        "furgoneta", "dietas", "foco cambiado", "punto colocado", "tiempo y transporte",
        "transporte y tiempo", "recogida de material", "viaje", "gasoil"
    ]
    if any(k in t for k in frases_clave):
        return True
    
    palabras = set(re.findall(r'\b[a-z]+\b', t))
    claves_aisladas = {"transporte", "porte", "portes", "desplazamiento", "kilometraje", "gestion", "acopio", "tiempo"}
    if palabras.intersection(claves_aisladas):
        no_es_material = not any(m in t for m in ["tubo", "cable", "manguera", "diferencial", "magnetotermico", "caja", "cuadro", "enchufe", "interruptor", "foco", "downlight", "led", "canal"])
        if no_es_material:
            return True
    return False


def generar_excel_orden_compra(filas_compra: list, nom_cliente: str, concepto_obra: str) -> bytes:
    """Genera un archivo Excel (.xlsx) estructurado con la Orden de Compra y Acopio agrupado por proveedor."""
    output = io.BytesIO()
    solo_mats = [f for f in filas_compra if not (f.get("es_servicio") or es_servicio_o_logistica(f.get("mat", "")))]
    datos = solo_mats if solo_mats else filas_compra
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export = pd.DataFrame([
            {
                "Proveedor / Tienda": f.get("proveedor", "Obramat"),
                "Descripción del Material": f.get("mat", ""),
                "Cantidad": f.get("cant", 1.0),
                "Unidad": f.get("unid", "ud"),
                "P. Unitario S/IVA (€)": round(float(f.get("p_u", 0.0)), 2),
                "Subtotal S/IVA (€)": round(float(f.get("subtotal", 0.0)), 2),
                "A Pagar Mostrador c/21% IVA (€)": round(float(f.get("subtotal", 0.0)) * 1.21, 2),
                "Origen de Tarifa": f.get("origen", "Base de Datos"),
                "Estado de Compra": "⏳ Pendiente"
            }
            for f in datos
        ])
        if not df_export.empty:
            df_export = df_export.sort_values(by=["Proveedor / Tienda", "Descripción del Material"])
        df_export.to_excel(writer, sheet_name="Orden de Compra Bolimur", index=False)
    return output.getvalue()


def generar_texto_whatsapp_compra(filas_compra: list, nom_cliente: str, concepto_obra: str, total_mat: float) -> str:
    """Genera un mensaje de texto formateado listo para enviar por WhatsApp o SMS con la lista de compras."""
    texto = f"📋 *ORDEN DE COMPRA & ACOPIO - BOLIMUR*\n"
    texto += f"📅 Fecha: {datetime.date.today().strftime('%d/%m/%Y')}\n"
    texto += f"👤 Cliente / Aviso: {nom_cliente}\n"
    texto += f"⚡ Trabajo: {concepto_obra}\n"
    texto += f"-----------------------------------------\n"

    solo_mats = [f for f in filas_compra if not (f.get("es_servicio") or es_servicio_o_logistica(f.get("mat", "")))]
    datos = solo_mats if solo_mats else filas_compra

    por_prov = {}
    for f in datos:
        p = f.get("proveedor", "Obramat")
        por_prov.setdefault(p, []).append(f)

    tot_compra_siva = 0.0
    for prov_name, items in por_prov.items():
        sub_p = sum(float(x.get("subtotal", 0.0)) for x in items)
        sub_p_civa = round(sub_p * 1.21, 2)
        tot_compra_siva += sub_p
        texto += f"\n🏬 *{prov_name.upper()}* (Base: {sub_p:,.2f} € | 💳 Caja: {sub_p_civa:,.2f} € c/IVA):\n"
        for it in items:
            s_it = float(it.get('subtotal', 0.0))
            texto += f"  • {float(it.get('cant', 1.0)):.1f} {it.get('unid', 'ud')} - {it.get('mat', '')} (~{s_it:,.2f} € S/IVA · {s_it*1.21:,.2f} € c/IVA)\n"

    texto += f"\n-----------------------------------------\n"
    texto += f"💰 *Gasto Total en Mostrador:* {tot_compra_siva:,.2f} € (S/IVA) | *{tot_compra_siva * 1.21:,.2f} € (C/IVA 21% a pagar en caja)*\n"
    return texto


def generar_texto_whatsapp_presupuesto(nom_cliente: str, concepto_obra: str, subtotal_siva: float, total_civa: float, iva_pct: float, horas_mo: float, precio_mo: float, coste_mo: float, total_mat: float, filas_mats: list, desplazamiento: float = 0.0, tipo_tarifa: str = "Estándar") -> str:
    """Genera un mensaje formal de presupuesto para enviar al cliente por WhatsApp."""
    texto = "⚡ *PRESUPUESTO ELÉCTRICO OFICIAL - BOLIMUR*\n"
    texto += f"📅 Fecha: {datetime.date.today().strftime('%d/%m/%Y')}\n"
    texto += f"👤 Cliente: {nom_cliente}\n"
    texto += f"🛠️ Trabajo: {concepto_obra}\n"
    if tipo_tarifa:
        texto += f"🏷️ Régimen / Tarifa: {tipo_tarifa}\n"
    texto += "-----------------------------------------\n"
    
    mats_solo = [it for it in filas_mats if not (it.get("es_servicio") or es_servicio_o_logistica(it.get("mat", "")))]
    serv_solo = [it for it in filas_mats if (it.get("es_servicio") or es_servicio_o_logistica(it.get("mat", "")))]
    
    texto += f"📦 *Materiales y Aparamenta:* {total_mat:,.2f} € (S/IVA)\n"
    for it in mats_solo[:5]:
        texto += f"  • {float(it.get('cant', 1.0)):.1f} {it.get('unid', 'ud')} {it.get('mat', '')[:30]} ({float(it.get('subtotal', 0.0)):,.2f} €)\n"
    if len(mats_solo) > 5:
        texto += f"  • ... y {len(mats_solo) - 5} partidas adicionales de material.\n"
    
    if serv_solo:
        tot_serv = sum(float(x.get("subtotal", 0.0)) for x in serv_solo)
        texto += f"\n🚚 *Logística y Tiempo de Compras:* {tot_serv:,.2f} € (S/IVA)\n"
        for it in serv_solo:
            texto += f"  • {it.get('mat', '')[:35]} ({float(it.get('subtotal', 0.0)):,.2f} €)\n"

    texto += f"\n⏱️ *Mano de Obra Instalador REBT:* {horas_mo:.1f}h × {precio_mo:.2f} €/h = {coste_mo:,.2f} €\n"
    if desplazamiento > 0:
        texto += f"🚗 *Desplazamiento / Salida:* {desplazamiento:,.2f} €\n"
    texto += "-----------------------------------------\n"
    texto += f"💶 *Base Imponible (S/IVA):* {subtotal_siva:,.2f} €\n"
    if iva_pct == 0.0:
        texto += f"💰 *TOTAL FACTURA (0% IVA ISP):* {subtotal_siva:,.2f} €\n"
    else:
        texto += f"💰 *TOTAL CLIENTE (IVA {iva_pct:.0f}% Inc.):* {total_civa:,.2f} €\n"
    texto += "-----------------------------------------\n"
    texto += "✅ Instalación realizada según normativa REBT (RD 842/2002) con garantía oficial.\n"
    texto += "📞 Bolimur Instalaciones Eléctricas Autorizadas."
    return texto


def generar_pdf_orden_compra_rapida(filas_compra: list, nom_cliente: str, concepto: str, total_mat: float, iva_pct: float, usuario: dict = None) -> bytes:
    """Genera el PDF oficial de la Orden de Compra clasificado por proveedor excluyendo servicios internos."""
    from modulos import pdf_presupuesto
    usuario = usuario or {}
    proyecto_info = {
        'empresa': usuario.get('nombre_empresa') or 'BOLIMUR INSTALACIONES Y REFORMAS',
        'proyectista': usuario.get('nombre_instalador') or 'Richard Orlando Choque Tejerina',
        'nif_cif': usuario.get('nif_cif') or 'B-73000000',
        'num_licencia_rebt': usuario.get('num_licencia_rebt') or 'REBT-30/15892',
        'telefono': usuario.get('telefono') or '+34 600 000 000',
        'cliente': nom_cliente or 'Cliente Particular',
        'direccion': usuario.get('direccion') or 'Murcia, España',
        'expediente': f"{datetime.date.today().strftime('%Y%m%d')}-OC",
        'fecha': datetime.date.today().strftime('%d/%m/%Y')
    }
    solo_mats = [f for f in filas_compra if not (f.get("es_servicio") or es_servicio_o_logistica(f.get("mat", "")))]
    datos = solo_mats if solo_mats else filas_compra
    cats = {}
    tot_compra_puro = sum(float(f.get('subtotal', 0.0)) for f in datos)
    for f in datos:
        p_name = f.get('proveedor', 'Obramat')
        cat_key = f"PROVEEDOR / TIENDA: {p_name.upper()}"
        if cat_key not in cats:
            cats[cat_key] = []
        cats[cat_key].append({
            'cantidad': float(f.get('cant', 1.0)),
            'cant': float(f.get('cant', 1.0)),
            'unidad': f.get('unid', 'ud'),
            'desc_exacta': f.get('mat', 'Material Eléctrico'),
            'articulo': f.get('mat', 'Material Eléctrico'),
            'descripcion': f.get('mat', 'Material Eléctrico'),
            'mat': f.get('mat', 'Material Eléctrico'),
            'proveedor': p_name,
            'tienda': p_name,
            'precio_unitario': float(f.get('p_u', 0.0)),
            'p_unit': float(f.get('p_u', 0.0)),
            'subtotal': float(f.get('subtotal', 0.0))
        })
    cuota = round(tot_compra_puro * 0.21, 2)
    oc_data = {
        'total_neto': tot_compra_puro,
        'iva_pct': 21.0,
        'cuota_iva': cuota,
        'total_con_iva': round(tot_compra_puro + cuota, 2),
        'categorias': cats
    }
    return pdf_presupuesto.generar_pdf_orden_compra(proyecto_info, oc_data)


def generar_pdf_presupuesto_rapido(res: dict, filas_compra: list, nom_cliente: str, horas_mo: float, precio_mo: float, coste_mo: float, total_mat: float, subtotal_siva: float, total_civa: float, iva_pct: float, usuario: dict = None, desplazamiento: float = 0.0, tipo_tarifa: str = "Estándar") -> bytes:
    """Genera el presupuesto oficial comercial en PDF con desglose REBT completo."""
    from modulos import pdf_presupuesto
    usuario = usuario or {}
    proyecto_info = {
        'empresa': usuario.get('nombre_empresa') or 'BOLIMUR INSTALACIONES Y REFORMAS',
        'proyectista': usuario.get('nombre_instalador') or 'Richard Orlando Choque Tejerina',
        'nif_cif': usuario.get('nif_cif') or 'B-73000000',
        'num_licencia_rebt': usuario.get('num_licencia_rebt') or 'REBT-30/15892',
        'telefono': usuario.get('telefono') or '+34 600 000 000',
        'cliente': nom_cliente or 'Cliente Particular',
        'direccion': usuario.get('direccion') or 'Murcia, España',
        'expediente': f"{datetime.date.today().strftime('%Y%m%d')}-PR",
        'fecha': datetime.date.today().strftime('%d/%m/%Y')
    }
    tarifa_limpia = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\ufe00-\ufe0f]', '', str(tipo_tarifa)).strip()

    cap_mats = [f for f in filas_compra if not (f.get("es_servicio") or es_servicio_o_logistica(f.get("mat", "")))]
    cap_serv = [f for f in filas_compra if (f.get("es_servicio") or es_servicio_o_logistica(f.get("mat", "")))]
    tot_mats_val = sum(float(x.get("subtotal", 0.0)) for x in cap_mats)
    tot_serv_val = sum(float(x.get("subtotal", 0.0)) for x in cap_serv)

    capitulos = [
        {
            'cap': 'CAP-01',
            'titulo': 'Materiales y Suministro Eléctrico Certificado',
            'desc': f"Suministro de {len(cap_mats)} partidas normalizadas de conductores, protecciones y canalizaciones.",
            'importe': tot_mats_val
        }
    ]
    if tot_serv_val > 0:
        capitulos.append({
            'cap': f"CAP-0{len(capitulos) + 1}",
            'titulo': 'Logística, Gestión de Acopio y Servicios Técnicos',
            'desc': f"Tiempo invertido en acopio y transporte de materiales, coordinación técnica y gestiones operativas.",
            'importe': tot_serv_val
        })
    capitulos.append({
        'cap': f"CAP-0{len(capitulos) + 1}",
        'titulo': f"Mano de Obra e Instalación Profesional ({tarifa_limpia})" if tarifa_limpia else "Mano de Obra e Instalación Profesional",
        'desc': f"Montaje técnico ({horas_mo:.1f} h a {precio_mo:.2f} €/h), tendido, conexionado, timbrado y ensayos reglamentarios según {res.get('norma', 'REBT RD 842/2002')}.",
        'importe': coste_mo
    })
    if desplazamiento > 0:
        capitulos.append({
            'cap': f"CAP-0{len(capitulos) + 1}",
            'titulo': 'Desplazamiento y Salida de Furgón Taller',
            'desc': f"Transporte técnico, kilometraje y puesta a disposición de furgón taller e instrumental reglamentario ({tarifa_limpia})." if tarifa_limpia else "Transporte técnico, kilometraje y puesta a disposición de furgón taller.",
            'importe': desplazamiento
        })

    # Partidas desglosadas completas para que el cliente vea cada artículo en el PDF
    partidas_desglose = []
    for f in filas_compra:
        es_s = f.get('es_servicio') or es_servicio_o_logistica(f.get('mat', ''))
        origen_limpio = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\ufe00-\ufe0f]', '', str(f.get('origen', 'Tarifa Oficial'))).strip()
        mat_limpio = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\ufe00-\ufe0f]', '', str(f.get('mat', 'Material Eléctrico'))).strip()
        desc_linea = f"Gestión logística y coordinación técnica ({f.get('proveedor', 'Servicio Propio')})" if es_s else f"Suministro oficial ({f.get('proveedor', 'Obramat')}) - {origen_limpio}"
        partidas_desglose.append({
            'concepto': mat_limpio,
            'descripcion': desc_linea,
            'cantidad': float(f.get('cant', 1.0)),
            'unidad': f.get('unid', 'ud'),
            'precio_unitario': float(f.get('p_u', 0.0)),
            'subtotal': float(f.get('subtotal', 0.0))
        })

    partidas_desglose.append({
        'concepto': f"Mano de Obra Oficial REBT ({tarifa_limpia})" if tarifa_limpia else "Mano de Obra Oficial REBT",
        'descripcion': f"Ejecución técnica ({horas_mo:.1f} h), fijaciones, conexionado, verificación y ensayos reglamentarios.",
        'cantidad': horas_mo,
        'unidad': 'h',
        'precio_unitario': precio_mo,
        'subtotal': coste_mo
    })
    if desplazamiento > 0:
        partidas_desglose.append({
            'concepto': f"Desplazamiento / Salida Furgón Taller ({tarifa_limpia})" if tarifa_limpia else "Desplazamiento / Salida Furgón Taller",
            'descripcion': "Transporte técnico, desplazamiento de personal especializado e instrumental de verificación de averías.",
            'cantidad': 1.0,
            'unidad': 'salida',
            'precio_unitario': desplazamiento,
            'subtotal': desplazamiento
        })

    cuota = round(subtotal_siva * (iva_pct / 100.0), 2)
    pres_data = {
        'total_neto': subtotal_siva,
        'subtotal_neto': subtotal_siva,
        'iva_pct': iva_pct,
        'cuota_iva': cuota,
        'total_con_iva': total_civa,
        'total_cliente': total_civa,
        'potencia_kw': '9.2 kW',
        'grado_electr': 'Básica',
        'plazo_dias': max(1.0, round(horas_mo / 8.0, 1)),
        'total_puntos': len(filas_compra),
        'precio_medio_punto': round(total_civa / len(filas_compra), 2) if filas_compra else 0.0,
        'precio_medio_punto_neto': round(subtotal_siva / len(filas_compra), 2) if filas_compra else 0.0,
        'capitulos': capitulos,
        'partidas_manuales': partidas_desglose,
        'partidas_adicionales': partidas_desglose
    }
    return pdf_presupuesto.generar_pdf_presupuesto(proyecto_info, pres_data)


@st.cache_data
def cargar_df_bd_oficial():
    """Carga la base de datos oficial maestra de precios y proveedores de Bolimur."""
    posibles = [
        "base_datos_precio_oficial.xlsx",
        "Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy_v2.xlsx",
        "Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy.xlsx"
    ]
    for f in posibles:
        if os.path.exists(f):
            try:
                return pd.read_excel(f)
            except Exception:
                pass
    return None


def normalizar_texto(s: str) -> str:
    """Normaliza texto eliminando tildes y caracteres especiales para búsqueda tolerante."""
    return "".join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn').lower()


def contrastar_con_bd_oficial(nombre_mat: str, df_bd: pd.DataFrame = None) -> dict:
    """Contrasta un material con la base de datos oficial y determina el proveedor más económico y su origen."""
    if es_servicio_o_logistica(nombre_mat):
        return {
            "en_bd": False,
            "origen": "🚚 Logística / Gestión",
            "proveedor": "Servicio Técnico Propio",
            "art_bd": "",
            "precio_bd": None
        }

    if df_bd is None:
        df_bd = cargar_df_bd_oficial()

    mat_norm = normalizar_texto(nombre_mat)
    prov_defecto = "Obramat"
    if any(k in mat_norm for k in ["reloj", "contactor", "telegestion", "pop+dps", "sobretensiones", "horario"]):
        prov_defecto = "Sumidelec"

    if df_bd is None or df_bd.empty:
        return {
            "en_bd": False,
            "origen": "🤖 Estimación IA",
            "proveedor": prov_defecto,
            "art_bd": "",
            "precio_bd": None
        }

    tokens = [t for t in re.sub(r'[^a-z0-9]', ' ', mat_norm).split() if len(t) >= 2 and t not in ["para", "con", "del", "las", "los", "una", "uno", "curva", "tipo", "cobre"]]

    candidatos = []
    for idx, row in df_bd.iterrows():
        desc = normalizar_texto(row.get('Descripción Exacta del Artículo', ''))
        score = sum(1 for t in tokens if t in desc)
        if score >= 2:
            try:
                p = float(row.get('Precio S/IVA (€)', 0.0))
                prov = str(row.get('Proveedor / Tienda', prov_defecto))
                art = str(row.get('Descripción Exacta del Artículo', ''))
                candidatos.append((score, prov, p, art))
            except Exception:
                pass

    if candidatos:
        # Priorizar mejor coincidencia de texto, y a igualdad de coincidencia, el PRECIO MÁS ECONÓMICO
        candidatos.sort(key=lambda x: (-x[0], x[2]))
        best = candidatos[0]
        return {
            "en_bd": True,
            "origen": "🏷️ BD Oficial Bolimur",
            "proveedor": best[1],
            "art_bd": best[3],
            "precio_bd": best[2]
        }

    return {
        "en_bd": False,
        "origen": "🤖 Estimación IA",
        "proveedor": prov_defecto,
        "art_bd": "",
        "precio_bd": None
    }


def obtener_precio_por_tienda(nombre_mat: str, tienda: str, p_base: float, df_bd: pd.DataFrame = None) -> tuple:
    """Busca en la BD o calcula el precio diferencial según la tienda o distribuidor seleccionado."""
    if df_bd is None or df_bd.empty:
        df_bd = cargar_df_bd_oficial()

    tienda_norm = normalizar_texto(tienda)
    mat_norm = normalizar_texto(nombre_mat)

    # Intentar búsqueda exacta de ese material en esa tienda en la base de datos
    if df_bd is not None and not df_bd.empty:
        tokens = [t for t in re.sub(r'[^a-z0-9]', ' ', mat_norm).split() if len(t) >= 2 and t not in ["para", "con", "del", "las", "los", "una", "uno", "curva", "tipo", "cobre"]]
        candidatos = []
        for idx, row in df_bd.iterrows():
            prov_row = normalizar_texto(row.get('Proveedor / Tienda', ''))
            if tienda_norm in prov_row or prov_row in tienda_norm:
                desc = normalizar_texto(row.get('Descripción Exacta del Artículo', ''))
                score = sum(1 for t in tokens if t in desc)
                if score >= 2:
                    try:
                        p_val = float(row.get('Precio S/IVA (€)', 0.0))
                        candidatos.append((score, p_val))
                    except Exception:
                        pass
        if candidatos:
            # Mejor coincidencia y menor precio en esa tienda
            candidatos.sort(key=lambda x: (-x[0], x[1]))
            return round(candidatos[0][1], 2), "Precio Oficial BD"

    # Factores reales de mercado comparativo entre cadenas de distribución
    factores = {
        "obramat": 1.00,
        "leroy merlin": 1.14,
        "sumidelec": 1.02,
        "sonepar / rexel": 0.94,
        "mayorista electrico": 0.95,
        "suministro especializado": 1.08
    }
    factor = factores.get(tienda_norm, 1.00)
    return round(float(p_base) * factor, 2), f"Tarifa comparativa ({factor:.2f}x)"


def comparar_precios_proveedores(nombre_mat: str, tienda_actual: str, precio_base: float, df_bd: pd.DataFrame = None) -> dict:
    """Compara en tiempo real los precios entre tiendas para alertar al instalador si hay ahorro en CUALQUIER otro proveedor."""
    if es_servicio_o_logistica(nombre_mat):
        return {
            "hay_ahorro": False,
            "tienda_min": tienda_actual or "Servicio Técnico Propio",
            "precio_min": precio_base,
            "precio_actual": precio_base,
            "ahorro_ud": 0.0,
            "ahorro_pct": 0.0,
            "todas_mas_baratas": [],
            "precios_todos": {}
        }

    tiendas_evaluar = ["Obramat", "Leroy Merlin", "Sumidelec", "Sonepar / Rexel", "Mayorista Eléctrico"]
    tienda_actual_norm = normalizar_texto(tienda_actual)
    precios = {}

    for t in tiendas_evaluar:
        p_t, _ = obtener_precio_por_tienda(nombre_mat, t, precio_base, df_bd)
        precios[t] = p_t

    p_actual = precios.get(tienda_actual, precio_base)
    if not p_actual or p_actual <= 0:
        p_actual = precio_base

    # Identificar todas las tiendas que ofrecen un precio menor al seleccionado actualmente
    mas_baratas = []
    for t, p_t in precios.items():
        if normalizar_texto(t) != tienda_actual_norm and p_t < (p_actual - 0.04):
            dif = round(p_actual - p_t, 2)
            pct = round((dif / p_actual) * 100, 1)
            mas_baratas.append({
                "tienda": t,
                "precio": p_t,
                "ahorro_ud": dif,
                "ahorro_pct": pct
            })

    mas_baratas.sort(key=lambda x: x["precio"])  # Las más baratas primero

    tienda_min = mas_baratas[0]["tienda"] if mas_baratas else tienda_actual
    p_min = mas_baratas[0]["precio"] if mas_baratas else p_actual
    dif_min = mas_baratas[0]["ahorro_ud"] if mas_baratas else 0.0
    pct_min = mas_baratas[0]["ahorro_pct"] if mas_baratas else 0.0

    return {
        "hay_ahorro": bool(len(mas_baratas) > 0),
        "tienda_min": tienda_min,
        "precio_min": p_min,
        "precio_actual": p_actual,
        "ahorro_ud": dif_min,
        "ahorro_pct": pct_min,
        "todas_mas_baratas": mas_baratas,
        "precios_todos": precios
    }


def buscar_marcas_alternativas(nombre_mat: str, df_bd: pd.DataFrame = None) -> list:
    """Busca en la base de datos oficial alternativas de marcas reconocidas y gamas superiores (Schneider, Simon, Legrand, Niessen, Zemper, Hager, etc.)."""
    if es_servicio_o_logistica(nombre_mat):
        return []
    if df_bd is None or df_bd.empty:
        df_bd = cargar_df_bd_oficial()
    if df_bd is None or df_bd.empty:
        return []

    mat_norm = normalizar_texto(nombre_mat)
    tokens = [t for t in re.sub(r'[^a-z0-9]', ' ', mat_norm).split() if len(t) >= 3 and t not in ['para', 'con', 'del', 'las', 'los', 'una', 'uno', 'tipo', 'color', 'pack']]

    matches = []
    for idx, row in df_bd.iterrows():
        desc = normalizar_texto(row.get('Descripción Exacta del Artículo', ''))
        score = sum(1 for t in tokens if t in desc)
        if score >= 2:
            marca = str(row.get('Marca', '')).strip()
            if marca and marca.lower() not in ['nan', 'general', 'varios', 'none']:
                try:
                    p = float(row.get('Precio S/IVA (€)', 0.0))
                    gama = str(row.get('Nivel de Gama / Aplicación', 'Estándar'))
                    prov = str(row.get('Proveedor / Tienda', 'Obramat'))
                    art = str(row.get('Descripción Exacta del Artículo', ''))
                    matches.append((score, marca, p, gama, prov, art))
                except Exception:
                    pass

    # Agrupar por marca única conservando la opción más completa o de mayor calidad
    by_marca = {}
    for m in matches:
        marca = m[1]
        if marca not in by_marca or m[0] > by_marca[marca][0] or (m[0] == by_marca[marca][0] and m[2] > by_marca[marca][2]):
            by_marca[marca] = m

    res = []
    for marca, m in by_marca.items():
        res.append({
            'marca': marca,
            'precio': m[2],
            'gama': m[3],
            'tienda': m[4],
            'art': m[5]
        })
    res.sort(key=lambda x: x['precio'])
    return res


def transcribir_audio_gemini(raw_bytes: bytes, mime_type: str = "audio/wav", api_key: str = "") -> dict:
    """Envía el audio a Gemini 2.0 Flash para transcribir la voz del instalador a texto en español."""
    if not api_key:
        return {"exito": False, "error": "Falta la clave API de Google Gemini."}

    b64_data = base64.b64encode(raw_bytes).decode("utf-8")
    clean_mime = mime_type or "audio/wav"
    if ";" in clean_mime:
        clean_mime = clean_mime.split(";")[0].strip()

    prompt = (
        "Eres un transcriptor técnico de campo para instaladores electricistas en España (normativa REBT).\n"
        "Escucha atentamente este audio grabado por el instalador y transcribe con máxima exactitud "
        "lo que dice sobre el trabajo eléctrico a realizar (cables, metros, tubos, automáticos, cuadros, "
        "relojes, enchufes, etc.).\n"
        "Devuelve ÚNICAMENTE el texto en español transcrito en lenguaje natural limpio, sin saludos, "
        "sin comillas ni explicaciones adicionales."
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": clean_mime,
                            "data": b64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 800
        }
    }

    modelos = ["gemini-3.5-transcribe", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
    ultimo_error = "Error desconocido de conexión."
    for modelo in modelos:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        try:
            resp = requests.post(endpoint, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands:
                    partes = cands[0].get("content", {}).get("parts", [])
                    if partes:
                        texto = partes[0].get("text", "").strip()
                        if texto:
                            return {"exito": True, "texto": texto}
            else:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", resp.text[:250])
                except Exception:
                    err_msg = resp.text[:250]
                ultimo_error = f"HTTP {resp.status_code} ({modelo}): {err_msg}"
        except Exception as e:
            ultimo_error = str(e)
            continue

    return {"exito": False, "error": ultimo_error}


def analizar_trabajo_ia_gemini(descripcion: str, api_key: str, precio_hora: float = 25.0) -> dict:
    """Utiliza Gemini para desglosar el trabajo en memoria técnica REBT exhaustiva, partidas y materiales."""
    if not api_key:
        return {"exito": False}

    prompt = f"""Actúa como un Maestro Instalador Electricista Autorizado e Ingeniero Eléctrico en España con 25 años de experiencia y dominio exhaustivo del REBT (RD 842/2002) y normativa de Industria (DGEAIM Murcia).
Analiza detalladamente el siguiente trabajo eléctrico explicado por el instalador:
"{descripcion}"

Redacta un dictamen técnico riguroso, completo y profesional.
Devuelve EXCLUSIVAMENTE un objeto JSON válido con la siguiente estructura exacta (sin texto previo ni posterior, sin formato markdown adicional):
{{
  "concepto": "Título técnico oficial conciso de la obra",
  "norma": "Instrucciones técnicas REBT y normas UNE de aplicación directa (ej: ITC-BT-25, ITC-BT-31, UNE-HD 60364)",
  "descripcion_detallada": "Memoria descriptiva y exhaustiva del trabajo (3 párrafos técnicos completos describiendo el alcance, canalizaciones, trazado, protecciones y envolventes apta para el presupuesto o factura formal)",
  "justificacion_tecnica": "Justificación técnica de ingeniería: por qué se han seleccionado esas secciones de cable, caídas de tensión calculadas, tipo de diferencial (Clase A/AC/Superinmunizado), curvas de disparo y grados de protección IP/IK requeridos",
  "pasos_ejecucion": [
    "Paso 1: Consignación de la instalación y comprobación de ausencia de tensión",
    "Paso 2: Instalación de canalizaciones y fijaciones",
    "Paso 3: Tendido de conductores y conexionado",
    "Paso 4: Montaje y rotulado de aparamenta en cuadro",
    "Paso 5: Ensayos reglamentarios finales y puesta en servicio"
  ],
  "pruebas_rebt": [
    "Medida de continuidad de conductores de protección y equipotenciales (R < 1 Ohm)",
    "Medida de resistencia de aislamiento entre conductores activos y tierra (> 0.5 MOhm a 500V DC)",
    "Comprobación de tiempo y corriente de disparo del interruptor diferencial (t < 200 ms)",
    "Verificación de polaridad y correspondencia de neutro y fase"
  ],
  "horas": 3.5,
  "materiales": [
    {{"mat": "Nombre comercial y especificación técnica del material", "cant": 1.0, "unid": "ud"|"m"|"pack", "p_u": 32.50}}
  ]
}}"""

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2500
        }
    }

    modelos = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]
    for modelo in modelos:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        try:
            resp = requests.post(endpoint, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands:
                    texto = cands[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    if "```json" in texto:
                        texto = texto.split("```json")[1].split("```")[0].strip()
                    elif "```" in texto:
                        texto = texto.split("```")[1].split("```")[0].strip()
                    obj = json.loads(texto)
                    if "concepto" in obj and "materiales" in obj and "descripcion_detallada" in obj:
                        return {"exito": True, "resultado": obj}
        except Exception:
            continue

    return {"exito": False}


def motor_reglas_rebt_rapido(prompt_consulta: str) -> dict:
    """Motor reglamentario REBT exhaustivo cuando se opera sin conexión IA o clave API."""
    p_low = prompt_consulta.lower().strip()

    if "depuradora" in p_low or "piscina" in p_low:
        concepto = "Línea Dedicada Protegida y Automatismo Horario para Depuradora de Piscina (ITC-BT-31)"
        norma = "ITC-BT-31 (Piscinas y Fuentes), ITC-BT-30 (Locales Húmedos/Mojados), ITC-BT-24 (Protección contra Contactos)"
        descripcion = (
            "Instalación de línea eléctrica independiente desde el Cuadro General de Mando y Protección (CGMP) "
            "hasta la caseta técnica o arqueta de depuración de piscina. Incluye tendido de línea monofásica con conductor "
            "unipolar de cobre Cu RZ1-K 0.6/1kV de sección 3G2.5 mm² libre de halógenos y no propagador del incendio (Cca-s1b,d1,a1), "
            "instalado bajo tubo corrugado reforzado flexible M25 libre de halógenos de 750N de resistencia a la compresión.\n\n"
            "Montaje de cuadro modular de mando estanco con envolvente de policarbonato IP65 e impacto IK08. En su interior se "
            "instala un interruptor magnetotérmico 1P+N de 16A curva C (6kA) para protección contra sobrecargas y cortocircuitos, "
            "junto con un reloj programador horario modular carril DIN con esfera analógica/digital y reserva de marcha de 100 horas, "
            "más selector manual-automático-paro. Conexionado del motor de bomba de impulsión con prensaestopas estancos y puente "
            "de equipotencialidad con la red de tierra general de la instalación."
        )
        justificacion = (
            "La ITC-BT-31 clasifica los volúmenes de piscinas y exige envolventes mínimas IPX5 para equipos exteriores expuestos a proyecciones. "
            "Se prescribe cable de aislamiento 0.6/1kV RZ1-K debido a la presencia constante de humedad y agentes desinfectantes (cloro/sal). "
            "La protección magnetotérmica calibrada a 16A curva C absorbe la punta de arranque inductiva del motor ($I_a \\approx 5\\text{ a }7 \\times I_n$) "
            "sin disparos intempestivos, manteniendo la caída de tensión calculada por debajo del 1.5%."
        )
        pasos = [
            "Consignación eléctrica y verificación de ausencia de tensión en CGMP.",
            "Replanteo del trazado exterior y fijación de canalización con grapas de acero inoxidable.",
            "Tendido de conductores RZ1-K 3G2.5 mm² y conexionado de conductor de protección PE.",
            "Fijación mecánica de cuadro estanco IP65, montaje de PIA 16A y reloj horario en carril DIN.",
            "Conexionado borne a borne del motor de la bomba y ajuste de caballetes horarios.",
            "Ensayos finales reglamentarios (continuidad, aislamiento y disparo diferencial) y rotulación."
        ]
        pruebas = [
            "Medida de continuidad del conductor de protección equipotencial PE (R < 1 Ohm)",
            "Medida de resistencia de aislamiento con generador de 500V DC (> 0.5 MOhm)",
            "Comprobación de sensibilidad y tiempo de corte diferencial (t < 200 ms a 30 mA)",
            "Verificación de estanqueidad de prensaestopas y sellado de cuadro IP65"
        ]
        horas = 3.5
        materiales = [
            {"mat": "Reloj Programador Horario Modular Carril DIN con Reserva", "cant": 1.0, "unid": "ud", "p_u": 34.50},
            {"mat": "PIA Magnetotérmico 1P+N 16A Curva C 6kA", "cant": 1.0, "unid": "ud", "p_u": 8.40},
            {"mat": "Cable Cu RZ1-K 0.6/1kV 3x2.5 mm² Libre Halógenos Cca", "cant": 20.0, "unid": "m", "p_u": 1.15},
            {"mat": "Tubo Corrugado Libre de Halógenos M25 750N", "cant": 20.0, "unid": "m", "p_u": 0.85},
            {"mat": "Cuadro Modular Estanco IP65 4-6 Módulos con Tapa Fumé", "cant": 1.0, "unid": "ud", "p_u": 16.80},
            {"mat": "Prensaestopas M25 IP68 y Bridas de Nylon UV", "cant": 1.0, "unid": "pack", "p_u": 6.50}
        ]

    elif "aire" in p_low or "clima" in p_low or "split" in p_low:
        concepto = "Circuito Independiente de Climatización C9 bajo ITC-BT-25 con Diferencial Superinmunizado"
        norma = "ITC-BT-25 (Instalaciones Interiores de Viviendas), ITC-BT-19 (Prescripciones Generales)"
        descripcion = (
            "Instalación de circuito independiente de climatización C9 según prescripciones de la ITC-BT-25 para alimentación "
            "de equipo de aire acondicionado / bomba de calor. Comprende la derivación directa desde el Cuadro General con conductor "
            "unipolar H07Z1-K (AS) 3G2.5 mm² bajo canaleta decorativa de superficie blanca con tapa de clipado rápido de 20x40 mm "
            "o tubo corrugado empotrado según configuración de paramentos.\n\n"
            "Incorporación en cuadro de interruptor magnetotérmico 1P+N de 16A curva C (6kA) exclusivo para el circuito C9, junto a "
            "un interruptor diferencial de cabecera bipolar de 40A / 30mA Clase A Superinmunizado para protección contra contactos "
            "indirectos y corrientes de fuga generadas por la electrónica de potencia del compresor inverter. En el extremo receptor se instala "
            "caja de mecanismo de superficie con base Schuko de 16A 2P+T con tapa o interruptor de corte en carga bipolar de proximidad."
        )
        justificacion = (
            "La ITC-BT-25 exige que los equipos de aire acondicionado dispongan de circuito C9 propio e independiente. Dado que los equipos "
            "modernos incorporan rectificadores y variadores de frecuencia (tecnología inverter), generan componentes de corriente continua "
            "y armónicos de alta frecuencia que saturan los núcleos magnéticos de diferenciales estándar Tipo AC provocando disparos intempestivos "
            "o ceguera ante defectos. El diferencial Tipo A Superinmunizado garantiza seguridad absoluta."
        )
        pasos = [
            "Desconexión y consignación del Cuadro General CGMP.",
            "Instalación y nivelación de canaleta decorativa blanca de 20x40 mm con accesorios de esquina.",
            "Tendido de conductores H07Z1-K 3G2.5 mm² (marrón, azul, amarillo-verde).",
            "Montaje de PIA 16A y diferencial Tipo A Superinmunizado en el CGMP.",
            "Fijación de caja de mecanismo o base Schuko reforzada junto a la unidad interior/exterior.",
            "Medida de caída de tensión (< 3%), resistencia de aislamiento y prueba de disparo de diferencial."
        ]
        pruebas = [
            "Verificación del calibre de la protección magnetotérmica adecuada a la sección de 2.5 mm² (16A)",
            "Ensayo de disparo diferencial Clase A (prueba de rampa y test a 30 mA, t < 200 ms)",
            "Medida de aislamiento entre conductores y tierra (> 0.5 MOhm a 500V DC)",
            "Comprobación de continuidad del conductor de tierra PE"
        ]
        horas = 3.0
        materiales = [
            {"mat": "PIA Magnetotérmico 1P+N 16A Curva C 6kA", "cant": 1.0, "unid": "ud", "p_u": 8.40},
            {"mat": "Diferencial 2x40A / 30mA Clase A Superinmunizado", "cant": 1.0, "unid": "ud", "p_u": 42.00},
            {"mat": "Cable Cu H07Z1-K 3x2.5 mm² (Fase, Neutro, Tierra)", "cant": 15.0, "unid": "m", "p_u": 0.95},
            {"mat": "Canaleta Decorativa Blanca con Tapa 20x40mm", "cant": 12.0, "unid": "m", "p_u": 2.20},
            {"mat": "Base Schuko Superficie 16A 2P+T Mecanismo", "cant": 1.0, "unid": "ud", "p_u": 6.80},
            {"mat": "Accesorios de Canaleta (Ángulos y Empalmes)", "cant": 1.0, "unid": "pack", "p_u": 5.50}
        ]

    elif "recarga" in p_low or "coche" in p_low or "vehículo" in p_low or "irve" in p_low:
        concepto = "Infraestructura para Recarga de Vehículo Eléctrico IRVE (ITC-BT-52 Esquema 2)"
        norma = "ITC-BT-52 (Infraestructura para Recarga de Vehículos Eléctricos), ITC-BT-23 (Sobretensiones)"
        descripcion = (
            "Instalación de línea eléctrica dedicada exclusiva para punto de recarga de vehículo eléctrico (IRVE) conforme a la "
            "ITC-BT-52, modo de recarga 3. Tendido de línea monofásica de 32A con conductores unipolares de cobre RZ1-K 0.6/1kV "
            "3G6 mm² (o 3G10 mm² según distancia para limitar la caída de tensión estricta al 1%) bajo tubo rígido blindado o curvable "
            "libre de halógenos de M32 con grado de resistencia al impacto IK08 y aplastamiento de 1250N.\n\n"
            "Cuadro secundario estanco de protección IRVE con envolvente IP65 dotado de: Interruptor General Automático IGA 2P 32A "
            "curva C, Interruptor Diferencial Clase A Superinmunizado 2P 40A / 30mA con filtro contra fugas de componente continua "
            "(> 6mA DC), y protector combinado de sobretensiones transitorias y permanentes con reconexión automática según ITC-BT-23."
        )
        justificacion = (
            "La ITC-BT-52 establece que la caída de tensión en la línea de recarga no debe superar el 1% para potencia nominal del punto "
            "de recarga (7.4 kW en monofásico a 32A). Se exige obligatoriamente protección diferencial Clase A o Tipo B con detección de "
            "fuga DC > 6mA para salvaguardar las baterías y el cargador embarcado del vehículo, así como protección contra sobretensiones permanentes."
        )
        pasos = [
            "Comprobación de la derivación o acometida y potencia contratada disponible.",
            "Trazado y anclaje de tubo rígido libre de halógenos M32 mediante abrazaderas metálicas cada 50 cm.",
            "Tendido de conductores Cu RZ1-K 3x6 mm² y comprobación de sección por caída de tensión al 1%.",
            "Montaje de cuadro de protecciones IRVE con diferencial Tipo A, IGA y protector de sobretensiones.",
            "Conexionado al cargador Wallbox o toma Mennekes y prueba funcional de protocolo de comunicación PWM.",
            "Ensayos reglamentarios ITC-BT-52 y redacción de certificado para tramitación de subvención Plan MOVES."
        ]
        pruebas = [
            "Medida de caída de tensión en carga a 32A (verificación de deltaV <= 1%)",
            "Disparo diferencial con inyección de corrientes pulsantes y rampa de 30 mA",
            "Comprobación de resistencia de la toma de tierra (Ra < 15 Ohm recomendada)",
            "Verificación de aislamiento de conductores a 500V DC (> 0.5 MOhm)"
        ]
        horas = 5.0
        materiales = [
            {"mat": "Interruptor General Automático IGA 2P 32A Curva C 10kA", "cant": 1.0, "unid": "ud", "p_u": 14.50},
            {"mat": "Diferencial Superinmunizado Clase A 2P 40A / 30mA (6mA DC)", "cant": 1.0, "unid": "ud", "p_u": 48.00},
            {"mat": "Protector Sobretensiones Transitorias y Permanentes POP+DPS", "cant": 1.0, "unid": "ud", "p_u": 52.00},
            {"mat": "Cable Cu RZ1-K 0.6/1kV 3x6 mm² Libre Halógenos Cca", "cant": 25.0, "unid": "m", "p_u": 2.25},
            {"mat": "Tubo Rígido Enchufable Libre de Halógenos M32 1250N", "cant": 20.0, "unid": "m", "p_u": 1.55},
            {"mat": "Cuadro Modular Estanco IP65 8 Módulos Garaje", "cant": 1.0, "unid": "ud", "p_u": 28.50}
        ]

    elif "derivación" in p_low or "di" in p_low or "contador" in p_low:
        concepto = "Sustitución y Adecuación de Derivación Individual Monofásica (ITC-BT-15)"
        norma = "ITC-BT-15 (Instalaciones de Enlace: Derivaciones Individuales), UNE 20460"
        descripcion = (
            "Renovación completa de la Derivación Individual monofásica desde la centralización de contadores del edificio hasta "
            "el Cuadro General de Mando y Protección (CGMP) de la vivienda, dando cumplimiento estricto a la ITC-BT-15.\n\n"
            "Tendido de conductores unipolares de cobre de alta seguridad Cu RZ1-K 0.6/1kV de sección 2x10 mm² (fase y neutro) más "
            "conductor de protección de 1x10 mm² con aislamiento amarillo-verde, clase de reacción al fuego Cca-s1b,d1,a1. Se incluye "
            "hilo rojo de mando de 1.5 mm² para telegestión de la distribuidora. Alojado en canalización independiente bajo tubo corrugado "
            "o rígido libre de halógenos de diámetro mínimo normalizado M40 (750N de resistencia), sin empalmes intermedios y con caja de "
            "seccionamiento y fusibles de protección reglamentaria en la centralización."
        )
        justificacion = (
            "La ITC-BT-15 estipula que la caída de tensión máxima admisible para contadores totalmente concentrados es del 1.5%. Con sección de "
            "10 mm² se garantiza alimentar hasta 9.200W (40A) en previsión de electrificación elevada manteniendo la caída de tensión inferior al 1.2% "
            "y una temperatura de servicio controlada en cables termoestables (90ºC de régimen continuo)."
        )
        pasos = [
            "Coordinación de corte de suministro con la compañía distribuidora o técnico autorizado.",
            "Desmontaje de la derivación antigua fuera de normativa.",
            "Guíado y tendido de los nuevos conductores RZ1-K de 10 mm² e hilo de mando por la canaladura vertical.",
            "Conexionado en el embarrado del contador con bornas seccionables y apriete dinamométrico.",
            "Entrada en la vivienda y conexión a los bornes superiores del nuevo IGA de cabecera.",
            "Comprobación de rigidez dieléctrica, continuidad y precintado oficial."
        ]
        pruebas = [
            "Medida de continuidad y resistencia de paso de la derivación",
            "Ensayo de aislamiento entre conductores fase-neutro y contra tierra (> 0.5 MOhm a 500V DC)",
            "Comprobación de calibre de fusibles en módulo de contadores (GL/GG según potencia)",
            "Verificación de sección de tubo normalizada (mínimo M40 según ITC-BT-15)"
        ]
        horas = 4.5
        materiales = [
            {"mat": "Cable Cu RZ1-K 0.6/1kV 2x10 mm² + TT 1x10 mm² Cca", "cant": 22.0, "unid": "m", "p_u": 4.35},
            {"mat": "Hilo de Mando Rojo 1.5 mm² para Telegestión", "cant": 22.0, "unid": "m", "p_u": 0.28},
            {"mat": "Tubo Corrugado Libre de Halógenos M40 750N", "cant": 22.0, "unid": "m", "p_u": 1.35},
            {"mat": "Bornas de Conexión Seccionables de Entrada en CGMP", "cant": 2.0, "unid": "ud", "p_u": 4.50},
            {"mat": "Base Fusible Unipolar y Cartucho Fusible Calibrado", "cant": 1.0, "unid": "ud", "p_u": 9.80}
        ]

    elif "cuadro" in p_low or "automático" in p_low or "térmico" in p_low or "diferencial" in p_low or "sobretension" in p_low:
        concepto = "Sustitución, Ampliación y Normalización de Cuadro General de Mando y Protección (CGMP)"
        norma = "ITC-BT-17 (Dispositivos Generales de Mando y Protección), ITC-BT-23 (Sobretensiones), ITC-BT-24"
        descripcion = (
            "Desmontaje de cuadro eléctrico obsoleto o fuera de norma y suministro e instalación de nuevo Cuadro General de Mando "
            "y Protección (CGMP) empotrado o de superficie con envolvente aislante autoextinguible clase II de 18 a 24 módulos DIN.\n\n"
            "Estructuración de aparamenta de primeras marcas (Schneider / Hager / Legrand): Interruptor General Automático (IGA) bipolar "
            "de 25A o 32A curva C con poder de corte de 6kA; Protector combinado contra Sobretensiones Permanentes y Transitorias (POP+DPS) "
            "según normativa autonómica; dos o más Interruptores Diferenciales bipolares de 40A / 30mA (garantizando un máximo reglamentario "
            "de 5 circuitos por diferencial según ITC-BT-25); peines de conexión bipolares aislados con cubrenormas y rotulación normalizada "
            "indeleble de cada uno de los circuitos terminales."
        )
        justificacion = (
            "La ITC-BT-17 y las resoluciones de la Dirección General de Industria (Murcia) obligan a la instalación de protectores de "
            "sobretensiones en cualquier reforma o alta de suministro. Asimismo, la ITC-BT-25 prohíbe conectar más de 5 circuitos a un mismo "
            "diferencial para evitar acumulaciones de corrientes de fuga y garantizar la selectividad del suministro."
        )
        pasos = [
            "Identificación, timbrado y etiquetado provisional de todos los circuitos existentes.",
            "Corte general de suministro y desmontaje de envolvente y aparamenta antigua.",
            "Adecuación del hueco o fijación de nueva envolvente de 18-24 módulos en paramento.",
            "Montaje en carril DIN de IGA, protector de sobretensiones POP+DPS y diferenciales.",
            "Distribución mediante peines bipolares aislados y reordenación de cableado con punteras huecas.",
            "Pruebas de disparo diferencial en rampa, medida de aislamiento general y rotulación definitiva."
        ]
        pruebas = [
            "Medida de disparo individual de cada interruptor diferencial (tiempo < 200 ms y corriente < 30 mA)",
            "Comprobación del led de estado del cartucho de sobretensiones transitorias (verde = OK)",
            "Verificación de apriete dinamométrico en todos los bornes de conexión (par recomendado por fabricante)",
            "Resistencia de aislamiento general con aparamenta bajada (> 0.5 MOhm a 500V DC)"
        ]
        horas = 4.0
        materiales = [
            {"mat": "Envolvente Empotrada CGMP 18-24 Módulos con Puerta Blanca", "cant": 1.0, "unid": "ud", "p_u": 28.50},
            {"mat": "Interruptor General Automático IGA 2P 32A Curva C 6kA", "cant": 1.0, "unid": "ud", "p_u": 12.50},
            {"mat": "Protector Sobretensiones Permanentes y Transitorias POP+DPS", "cant": 1.0, "unid": "ud", "p_u": 49.00},
            {"mat": "Interruptores Diferenciales 2x40A / 30mA Tipo A (x2)", "cant": 2.0, "unid": "ud", "p_u": 24.50},
            {"mat": "Peines de Conexión Bipolares y Punteras Aisladas", "cant": 1.0, "unid": "pack", "p_u": 16.00}
        ]

    else:
        concepto = f"Trabajo Eléctrico Especializado a Medida: {prompt_consulta[:45]}" if prompt_consulta else "Trabajo Eléctrico Especializado a Medida (REBT)"
        norma = "REBT (RD 842/2002), ITC-BT-19, ITC-BT-24 (Protección contra Contactos Directos e Indirectos)"
        descripcion = (
            f"Ejecución técnica de los trabajos eléctricos correspondientes a: \"{prompt_consulta or 'Reforma y adecuación eléctrica puntual'}\".\n\n"
            "Comprende el suministro e instalación de canalizaciones normalizadas, conductores de cobre unipolar termoestable o termoplástico "
            "de alta seguridad libres de halógenos y no propagadores de la llama, aparamenta modular de corte y protección calibrada para la potencia "
            "solicitada, conexionado en cajas estancas o mecanismos homologados y puesta a tierra reglamentaria de todos los elementos metálicos accesibles."
        )
        justificacion = (
            "Todos los componentes y materiales seleccionados cumplen con el Reglamento Electrotécnico para Baja Tensión (RD 842/2002) y sus "
            "Instrucciones Técnicas Complementarias, garantizando la coordinación estricta entre sección de cable y calibre de protección "
            "para evitar calentamientos y garantizar el corte automático ante cualquier defecto de aislamiento."
        )
        pasos = [
            "Inspección previa del circuito y verificación de seguridad eléctrica.",
            "Tendido de canalización y conductores normalizados.",
            "Conexionado de aparamenta y borneros de derivación.",
            "Ensayos reglamentarios de continuidad y aislamiento."
        ]
        pruebas = [
            "Medida de resistencia de aislamiento (> 0.5 MOhm a 500V DC)",
            "Comprobación de continuidad de tierra y equipotencialidad (R < 1 Ohm)",
            "Verificación de disparo de protecciones ante defectos simulados"
        ]
        horas = 2.5
        materiales = [
            {"mat": "Conductores de Cobre Normalizados y Canalización", "cant": 1.0, "unid": "partida", "p_u": 35.00},
            {"mat": "Aparamenta de Maniobra y Protección Calibrada", "cant": 1.0, "unid": "partida", "p_u": 25.00},
            {"mat": "Menudencia, Borneros de Conexión y Fijaciones", "cant": 1.0, "unid": "pack", "p_u": 12.00}
        ]

    return {
        "concepto": concepto,
        "norma": norma,
        "descripcion_detallada": descripcion,
        "justificacion_tecnica": justificacion,
        "pasos_ejecucion": pasos,
        "pruebas_rebt": pruebas,
        "horas": horas,
        "materiales": materiales
    }


def renderizar():
    st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">⚡ Presupuesto Rápido con IA y Dictado por Voz</h3></div>', unsafe_allow_html=True)
    st.caption("Diseñado para calle y furgoneta: habla por el micrófono o escribe el trabajo. La IA transcribirá tus palabras, las mostrará en pantalla, generará la memoria técnica detallada y estructurará el escandallo en segundos.")

    # Inicializar variables en session_state de forma segura
    if "pr_texto_input" not in st.session_state:
        st.session_state["pr_texto_input"] = ""
    if "pr_txt_key_counter" not in st.session_state:
        st.session_state["pr_txt_key_counter"] = 0
    if "pr_last_audio_bytes" not in st.session_state:
        st.session_state["pr_last_audio_bytes"] = None
    if "pr_precio_hora" not in st.session_state:
        st.session_state["pr_precio_hora"] = 25.0
    if "pr_desplazamiento" not in st.session_state:
        st.session_state["pr_desplazamiento"] = 0.0
    if "pr_tipo_tarifa_sel" not in st.session_state:
        st.session_state["pr_tipo_tarifa_sel"] = "☀️ Estándar Laboral"

    # Callback para cambio automático de precios según la tarifa seleccionada
    def cb_cambio_tarifa():
        t = st.session_state.get("pr_tipo_tarifa_sel", "")
        if "Nocturno" in t:
            st.session_state["pr_precio_hora"] = 38.0
            st.session_state["pr_desplazamiento"] = 35.0
        elif "Urgencias" in t:
            st.session_state["pr_precio_hora"] = 50.0
            st.session_state["pr_desplazamiento"] = 45.0
        elif "RyC" in t:
            st.session_state["pr_precio_hora"] = 30.0
            st.session_state["pr_desplazamiento"] = 25.0
        elif "Estándar" in t:
            st.session_state["pr_precio_hora"] = 25.0
            st.session_state["pr_desplazamiento"] = 0.0

    # Estado de la API de Gemini
    api_key = auditor_ia_rebt.obtener_gemini_api_key()
    tiene_gemini = bool(api_key and len(api_key) > 10)

    # Panel de Configuración de Clave API si no está configurada
    if not tiene_gemini:
        with st.expander("🔑 Activar Transcripción de Voz IA Directa con Google Gemini (Gratuito)", expanded=True):
            st.info("Para que la IA transcriba directamente tu voz a texto en la pantalla, introduce tu clave gratuita de Google Gemini (se obtiene gratis en 1 minuto en [Google AI Studio](https://aistudio.google.com/)).")
            nueva_key = st.text_input("Pega tu Clave API de Gemini aquí:", type="password", placeholder="AIzaSy...", key="pr_input_gemini_key")
            if st.button("💾 Guardar Clave API para Siempre", key="btn_save_gemini_pr", type="primary"):
                if nueva_key.strip():
                    auditor_ia_rebt.guardar_gemini_api_key(nueva_key.strip())
                    st.success("✅ Clave API guardada con éxito en secrets.toml de forma permanente.")
                    st.rerun()

    # 1. Configuración de Tarifa, Mano de Obra, Desplazamiento y Cliente Rápido
    col_cfg1, col_cfg2, col_cfg3, col_cfg4, col_cfg5 = st.columns([2.0, 1.8, 1.1, 1.1, 1.2])
    with col_cfg1:
        nom_cliente = st.text_input("👤 Cliente / Referencia:", value="Cliente Particular / Urgencia", key="pr_cliente_nom")
    with col_cfg2:
        tipo_tarifa = st.selectbox(
            "⚡ Régimen / Tarifa:",
            [
                "☀️ Estándar Laboral",
                "🔧 RyC (Averías y Reparación)",
                "🌙 Nocturno (22:00-06:00)",
                "🚨 Urgencias 24h / Festivo",
                "⚙️ Tarifa Personalizada"
            ],
            key="pr_tipo_tarifa_sel",
            on_change=cb_cambio_tarifa
        )
    with col_cfg3:
        precio_hora_mo = st.number_input("⏱️ M.O. (€/h):", min_value=15.0, max_value=150.0, step=1.0, key="pr_precio_hora")
    with col_cfg4:
        desplazamiento_val = st.number_input("🚗 Salida (€):", min_value=0.0, max_value=300.0, step=5.0, key="pr_desplazamiento")
    with col_cfg5:
        iva_pct = st.selectbox("🏛️ Régimen IVA:", [21.0, 10.0, 0.0], format_func=lambda x: f"{x:.0f}% (General)" if x == 21.0 else (f"{x:.0f}% (Reducido)" if x == 10.0 else "0% (ISP)"), key="pr_iva_sel")

    desc_tarifa = {
        "☀️ Estándar Laboral": "Horario ordinario L-V (08:00 a 19:00). Tarifa base de instalador autorizado sin recargos.",
        "🔧 RyC (Averías y Reparación)": "Reparación y Conservación de averías. Incluye salida de furgón taller con reposición y mano de obra ágil.",
        "🌙 Nocturno (22:00-06:00)": "Trabajos nocturnos reglamentarios (+50% mano de obra y plus por salida nocturna).",
        "🚨 Urgencias 24h / Festivo": "Atención prioritaria inmediata (< 2h), festivos y fines de semana (+100% recargo urgente y guardia).",
        "⚙️ Tarifa Personalizada": "Precios libres configurados directamente por el instalador para este presupuesto."
    }
    st.caption(f"ℹ️ **{tipo_tarifa}:** {desc_tarifa.get(tipo_tarifa, '')}")

    st.markdown("---")

    # 2. Entrada Multimodal: Micrófono de Voz y Texto
    st.markdown("#### 🎙️ Paso 1: Dicta o escribe el trabajo a realizar")
    st.info(
        "💡 **Dictado directo por voz más rápido y fiable:**\n\n"
        "• **En PC (Windows):** Haz clic en la caja de texto izquierda de abajo y pulsa **`Tecla Windows + H`**. Windows activará el micrófono y escribirá en tiempo real lo que digas.\n"
        "• **En Móvil o Tablet:** Toca la caja de texto y pulsa el **icono de micrófono del teclado** de tu teléfono.\n"
        "• **Con el grabador web (`Graba tu voz`):** Si usas el botón web inferior, accede mediante `http://localhost:8501` para que el navegador autorice la subida del audio sin restricciones de seguridad de red."
    )

    col_input1, col_input2 = st.columns([3, 2])

    with col_input2:
        with st.container(border=True):
            st.markdown("🎤 **1. Dictado por Micrófono:**")
            st.caption("Pulsa el botón de grabar, explica el trabajo y pulsa detener:")
            audio_in = st.audio_input("Graba tu voz", key="pr_mic_audio")

            # Procesamiento de audio capturado
            if audio_in is not None:
                raw_bytes = audio_in.getvalue()
                audio_hash = hash(raw_bytes)
                btn_transcribir_manual = st.button("🎙️ Transcribir este audio a texto con IA", type="primary", use_container_width=True, key="btn_transcribir_force")

                # Transcribir si es un audio nuevo o si se pulsa el botón
                debe_transcribir = (st.session_state.get("pr_audio_transcrito_hash") != audio_hash) or btn_transcribir_manual

                if debe_transcribir:
                    if tiene_gemini:
                        with st.spinner("🎧 Escuchando y transcribiendo tu voz a texto con IA Gemini..."):
                            res_trans = transcribir_audio_gemini(raw_bytes, audio_in.type or "audio/wav", api_key)
                            if res_trans.get("exito"):
                                texto_transcrito = res_trans.get("texto", "")
                                st.session_state["pr_audio_transcrito_hash"] = audio_hash
                                st.session_state["pr_texto_input"] = texto_transcrito
                                st.session_state["pr_txt_key_counter"] = st.session_state.get("pr_txt_key_counter", 0) + 1
                                st.toast("✅ ¡Dictado transcrito con éxito!", icon="🎙️")
                                st.rerun()
                            else:
                                st.error(f"Error al transcribir: {res_trans.get('error')}")
                    else:
                        st.warning("⚠️ Clave Gemini no detectada. Por favor introduce tu clave de Google Gemini abajo para activar la transcripción.")

            if not tiene_gemini:
                st.markdown("---")
                with st.container(border=True):
                    st.markdown("🔑 **Pega tu clave gratuita de Google Gemini aquí:**")
                    st.caption("Obtén tu clave gratis en 1 minuto en [Google AI Studio](https://aistudio.google.com/)")
                    c_k1, c_k2 = st.columns([2.5, 1.2])
                    with c_k1:
                        inline_key = st.text_input("Clave Gemini:", type="password", placeholder="AIzaSy...", key="pr_inline_key_box", label_visibility="collapsed")
                    with c_k2:
                        if st.button("💾 Guardar", key="btn_save_inline_box", type="primary", use_container_width=True):
                            if inline_key.strip():
                                auditor_ia_rebt.guardar_gemini_api_key(inline_key.strip())
                                st.success("✅ ¡Guardada para siempre!")
                                st.rerun()

            st.markdown(
                """
                <div style='background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; padding: 8px 10px; font-size: 12px; margin-top: 8px;'>
                    💡 <b>Atajos de dictado rápido sin configuración:</b><br/>
                    • En PC: Pulsa <b>Tecla Windows + H</b> para dictar directamente en el texto.<br/>
                    • En Móvil/Tablet: Toca el icono de micrófono en tu teclado virtual.
                </div>
                """,
                unsafe_allow_html=True
            )

    with col_input1:
        txt_key = f"pr_texto_area_{st.session_state.get('pr_txt_key_counter', 0)}"
        txt_descripcion = st.text_area(
            "✍️ **2. Texto transcrito del trabajo (revísalo o modifícalo aquí):**",
            value=st.session_state.get("pr_texto_input", ""),
            placeholder="Aquí aparecerá lo que digas por el micrófono. También puedes escribirlo directamente:\nEj: Instalar línea para depuradora de piscina con reloj horario en cuadro estanco exterior y 15 metros de cable 3x2.5mm² con tubo corrugado M25.",
            height=135,
            key=txt_key
        )
        st.session_state["pr_texto_input"] = txt_descripcion

        col_txt_actions = st.columns([1, 1])
        with col_txt_actions[0]:
            if st.button("🧹 Borrar texto para nuevo dictado", key="btn_limpiar_pr_texto", use_container_width=True):
                st.session_state["pr_texto_input"] = ""
                st.session_state["pr_last_audio_bytes"] = None
                st.session_state["pr_audio_transcrito_hash"] = None
                st.session_state["pr_txt_key_counter"] = st.session_state.get("pr_txt_key_counter", 0) + 1
                st.rerun()

    # Atajos de 1 Clic para avisos habituales
    st.markdown("**⚡ O pulsa una plantilla rápida si es un aviso habitual:**")
    col_at1, col_at2, col_at3, col_at4, col_at5, col_at6 = st.columns(6)
    if col_at1.button("🏊 Piscina", key="btn_at_dep", use_container_width=True):
        txt = "Instalación de línea protegida para depuradora de piscina con reloj programador horario modular carril DIN y magnetotérmico de 16A."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_txt_key_counter"] = st.session_state.get("pr_txt_key_counter", 0) + 1
        st.rerun()
    if col_at2.button("❄️ Clima", key="btn_at_clima", use_container_width=True):
        txt = "Línea independiente de climatización C9 de 16A bajo canaleta blanca con cable 3x2.5mm² y protección en cuadro con diferencial superinmunizado."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_txt_key_counter"] = st.session_state.get("pr_txt_key_counter", 0) + 1
        st.rerun()
    if col_at3.button("🚗 Recarga VE", key="btn_at_irve", use_container_width=True):
        txt = "Línea dedicada IRVE para recarga de coche eléctrico con cable 3x6mm², tubo M32, diferencial clase A e IGA 32A."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_txt_key_counter"] = st.session_state.get("pr_txt_key_counter", 0) + 1
        st.rerun()
    if col_at4.button("🔌 Derivación DI", key="btn_at_di", use_container_width=True):
        txt = "Derivación individual monofásica desde contadores hasta vivienda con cable libre de halógenos 2x10mm²+TT y tubo M40."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_txt_key_counter"] = st.session_state.get("pr_txt_key_counter", 0) + 1
        st.rerun()
    if col_at5.button("🍳 Horno/Vitro", key="btn_at_vitro", use_container_width=True):
        txt = "Circuito independiente C3 de 25A para horno y vitrocerámica con cable de 6mm² y base de enchufe de fuerza de 25A."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_txt_key_counter"] = st.session_state.get("pr_txt_key_counter", 0) + 1
        st.rerun()
    if col_at6.button("⚡ Cuadro CGMP", key="btn_at_cgmp", use_container_width=True):
        txt = "Sustitución de cuadro general de mando y protección con nuevo IGA 32A, protector de sobretensiones permanente y transitoria y 2 diferenciales de 40A."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_txt_key_counter"] = st.session_state.get("pr_txt_key_counter", 0) + 1
        st.rerun()

    st.markdown("")
    btn_calcular = st.button("🚀 Calcular Presupuesto Inmediato con IA", type="primary", use_container_width=True, key="btn_pr_calcular")

    # 3. Procesamiento y Generación de Partidas
    if btn_calcular or ("pr_resultado_escandallo" in st.session_state and not btn_calcular):
        prompt_consulta = st.session_state.get("pr_texto_input", "").strip()

        if btn_calcular:
            if not prompt_consulta:
                st.warning("⚠️ Escribe o dicta el trabajo antes de pulsar en calcular.")
                return

            with st.spinner("⚙️ Estructurando memoria técnica oficial y escandallo REBT..."):
                resultado_final = None
                if tiene_gemini:
                    res_ia = analizar_trabajo_ia_gemini(prompt_consulta, api_key, precio_hora_mo)
                    if res_ia.get("exito"):
                        resultado_final = res_ia.get("resultado")

                if not resultado_final:
                    resultado_final = motor_reglas_rebt_rapido(prompt_consulta)

                resultado_final["consulta_orig"] = prompt_consulta
                st.session_state["pr_resultado_escandallo"] = resultado_final

                # Limpiar cualquier clave residual de la tabla anterior
                for k in list(st.session_state.keys()):
                    if k.startswith("prm_") or k == "pr_target_round":
                        del st.session_state[k]

        # 4. Visualización del Presupuesto Dinámico, Memoria Técnica y Escandallo
        res = st.session_state.get("pr_resultado_escandallo", {})
        if res:
            st.markdown("---")
            st.markdown(f"## 📋 Dictamen Oficial: **{res.get('concepto', 'Trabajo Eléctrico')}**")
            st.markdown(f"**Normativa REBT Aplicable:** `{res.get('norma', 'REBT RD 842/2002')}`")

            # SECCIÓN DESTACADA: MEMORIA TÉCNICA ESCRITA DETERMINADA POR LA IA
            st.markdown("#### 📄 Memoria y Determinación Técnica Escrita de la IA")
            tab_mem1, tab_mem2, tab_mem3 = st.tabs([
                "📝 Memoria y Alcance de Obra (Editable para Cliente)",
                "⚖️ Justificación Técnica e Ingeniería REBT",
                "🛠️ Protocolo de Montaje y Ensayos Oficiales (ITC-BT-05)"
            ])

            with tab_mem1:
                st.markdown("<div style='font-size: 15px; font-weight: 600; color: #334155; margin-bottom: 8px;'>Descripción exhaustiva formal generada por la IA para factura o memoria de presupuesto (editable):</div>", unsafe_allow_html=True)
                memoria_val = st.text_area(
                    "Texto descriptivo formal para factura o presupuesto:",
                    value=res.get("descripcion_detallada", ""),
                    height=200,
                    key="pr_memoria_editable",
                    label_visibility="collapsed"
                )
                res["descripcion_detallada"] = memoria_val

            with tab_mem2:
                just_txt = res.get('justificacion_tecnica', 'Conforme a los criterios generales del REBT RD 842/2002.')
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 12px; padding: 24px 28px; margin: 10px 0; box-shadow: 0 2px 6px rgba(0,0,0,0.06);">
                        <div style="font-size: 20px; font-weight: 800; color: #1e40af; margin-bottom: 14px;">
                            ⚖️ Criterio Técnico y Reglamentario Oficial (REBT RD 842/2002):
                        </div>
                        <div style="font-size: 17px; line-height: 1.85; color: #1e3a8a; font-weight: 500; text-align: justify;">
                            {just_txt}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with tab_mem3:
                c_pas1, c_pas2 = st.columns(2)
                with c_pas1:
                    pasos_list = res.get("pasos_ejecucion", [])
                    items_pasos_html = ''.join(f'<div style="margin-bottom:10px;"><b>{idx_p}.</b> {p_item}</div>' for idx_p, p_item in enumerate(pasos_list, 1))
                    st.markdown(
                        f"""
                        <div style="background-color: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 20px 22px; height: 100%;">
                            <div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 12px;">🔧 Pasos de Ejecución en Obra:</div>
                            <div style="font-size: 16px; line-height: 1.75; color: #334155;">
                                {items_pasos_html}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with c_pas2:
                    pruebas_list = res.get("pruebas_rebt", [])
                    items_pruebas_html = ''.join(f'<div style="margin-bottom:10px;">🧪 <b>{p_test}</b></div>' for p_test in pruebas_list)
                    st.markdown(
                        f"""
                        <div style="background-color: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 10px; padding: 20px 22px; height: 100%;">
                            <div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 12px;">✅ Ensayos Reglamentarios Obligatorios (ITC-BT-05):</div>
                            <div style="font-size: 16px; line-height: 1.75; color: #334155;">
                                {items_pruebas_html}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            st.markdown("---")
            st.markdown("#### 📦 Escandallo Económico Desglosado")

            col_esc1, col_esc2 = st.columns([3.3, 1.7])

            with col_esc1:
                st.markdown("##### 📦 Materiales, Dónde Comprar y Comparativa de Precios:")
                st.caption("Visualiza la descripción completa del material, dónde comprar más barato y edita precios en tiempo real:")
                df_bd = cargar_df_bd_oficial()
                mats = res.get("materiales", [])
                total_mat_calc = 0.0

                filas_mats_edit = []
                acopio_por_tienda = {}
                servicios_internos = []

                def cb_cambiar_tienda(idx: int, p_base_calculado: float):
                    t_sel = st.session_state.get(f"prm_prov_{idx}", "Obramat")
                    m_txt = st.session_state.get(f"prm_n_{idx}", "")
                    df_local = cargar_df_bd_oficial()
                    n_p, n_org = obtener_precio_por_tienda(m_txt, t_sel, p_base_calculado, df_local)
                    st.session_state[f"prm_p_{idx}"] = float(n_p)
                    st.session_state[f"prm_orig_{idx}"] = n_org

                for idx_m, m_item in enumerate(mats):
                    tipo_m = m_item.get("tipo", "")
                    n_mat_inicial = m_item.get("mat", "")
                    key_n = f"prm_n_{idx_m}"
                    key_prov = f"prm_prov_{idx_m}"
                    key_c = f"prm_c_{idx_m}"
                    key_p = f"prm_p_{idx_m}"
                    key_orig = f"prm_orig_{idx_m}"

                    texto_eval = st.session_state.get(key_n, n_mat_inicial)
                    es_serv = (tipo_m == "servicio") or es_servicio_o_logistica(texto_eval)

                    info_bd = contrastar_con_bd_oficial(texto_eval, df_bd)
                    base_p = float(info_bd["precio_bd"]) if (info_bd["en_bd"] and info_bd["precio_bd"]) else float(m_item.get("p_u", 35.0 if es_serv else 10.0))

                    if key_n not in st.session_state:
                        st.session_state[key_n] = m_item.get("mat", "")
                    if key_c not in st.session_state:
                        st.session_state[key_c] = float(m_item.get("cant", 1.0))
                    if key_prov not in st.session_state:
                        st.session_state[key_prov] = "Servicio Técnico Propio" if es_serv else info_bd.get("proveedor", "Obramat")
                    if key_p not in st.session_state:
                        st.session_state[key_p] = float(base_p)
                    if key_orig not in st.session_state:
                        st.session_state[key_orig] = "🚚 Logística / Gestión Interna" if es_serv else info_bd["origen"]

                    with st.container(border=True):
                        # Fila 1: Descripción completa al 100% de ancho + Borrar
                        c_desc, c_del = st.columns([9.2, 0.8])
                        with c_desc:
                            lbl_partida = f"Partida #{idx_m + 1} - 🚚 Gestión / Servicio Técnico / Desplazamiento:" if es_serv else f"Partida #{idx_m + 1} - 📦 Descripción Completa del Material:"
                            n_mat = st.text_input(
                                lbl_partida,
                                value=st.session_state[key_n],
                                key=key_n,
                                help="Descripción completa. Se muestra a todo el ancho sin recortar texto tanto en móvil como en PC."
                            )
                        with c_del:
                            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                            if st.button("🗑️", key=f"btn_del_mat_{idx_m}", help="Eliminar partida"):
                                mats.pop(idx_m)
                                for k in list(st.session_state.keys()):
                                    if k.startswith("prm_"):
                                        del st.session_state[k]
                                res["materiales"] = mats
                                st.session_state["pr_resultado_escandallo"] = res
                                st.rerun()

                        # Origen en base de datos y enlaces
                        prov_actual = st.session_state.get(key_prov, "Servicio Técnico Propio" if es_serv else "Obramat")
                        origen_actual = st.session_state.get(key_orig, "🚚 Gestión Interna" if es_serv else info_bd["origen"])
                        pu_actual = float(st.session_state.get(key_p, base_p))

                        if es_serv:
                            st.markdown(
                                f"<div style='margin-top:-8px; margin-bottom:8px; font-size:11px; color:#4f46e5; font-weight:700;'>"
                                f"🚚 SERVICIO / GESTIÓN INTERNA · Sin compra en almacén de ferretería · {pu_actual:.2f} €/ud</div>",
                                unsafe_allow_html=True
                            )
                        elif "BD Oficial" in origen_actual or info_bd["en_bd"]:
                            art_tit = info_bd.get("art_bd", "")
                            query_q = urllib.parse.quote(f"precio {n_mat} {prov_actual}")
                            url_search = f"https://www.google.com/search?q={query_q}"
                            st.markdown(
                                f"<div style='margin-top:-8px; margin-bottom:8px; font-size:11px; color:#15803d; font-weight:700;' title='Artículo en BD: {art_tit}'>"
                                f"🏷️ {origen_actual} ({prov_actual}) · {pu_actual:.2f} € · <a href='{url_search}' target='_blank' style='color:#15803d; text-decoration:underline;'>🔍 Comprobar en web</a></div>",
                                unsafe_allow_html=True
                            )
                        else:
                            query_q = urllib.parse.quote(f"precio {n_mat} {prov_actual}")
                            url_search = f"https://www.google.com/search?q={query_q}"
                            st.markdown(
                                f"<div style='margin-top:-8px; margin-bottom:8px; font-size:11px; color:#0284c7; font-weight:600;'>"
                                f"🤖 {origen_actual} ({prov_actual}) · {pu_actual:.2f} € · <a href='{url_search}' target='_blank' style='color:#0284c7; text-decoration:underline;'>🔍 Verificar en la red</a></div>",
                                unsafe_allow_html=True
                            )

                        # Fila 2: Selector de Tienda / Canal, Cantidad, Precio Unitario y Subtotal
                        c_m1, c_m2, c_m3, c_m4 = st.columns([2.5, 1.2, 1.3, 1.4])
                        with c_m1:
                            if es_serv:
                                opciones_tiendas = ["Servicio Técnico Propio", "Logística y Transporte", "Gestión Externa / Subcontrata"]
                            else:
                                opciones_tiendas = ["Obramat", "Leroy Merlin", "Sumidelec", "Sonepar / Rexel", "Mayorista Eléctrico", "Suministro Especializado"]

                            if st.session_state[key_prov] not in opciones_tiendas:
                                st.session_state[key_prov] = opciones_tiendas[0]

                            prov_sel = st.selectbox(
                                "🏬 Canal / Proveedor:" if es_serv else "🏬 Dónde Comprar:",
                                opciones_tiendas,
                                key=key_prov,
                                on_change=cb_cambiar_tienda if not es_serv else None,
                                args=(idx_m, base_p) if not es_serv else None
                            )
                        with c_m2:
                            unid_lbl = m_item.get("unid", "servicio" if es_serv else "ud")
                            n_cnt = st.number_input(f"Cantidad ({unid_lbl}):", min_value=0.1, step=1.0, key=key_c)
                        with c_m3:
                            n_pu = st.number_input("PVP Unit. (€):", min_value=0.01, step=0.5, format="%.2f", key=key_p)
                        with c_m4:
                            sub_m = round(n_cnt * n_pu, 2)
                            sub_m_civa = round(sub_m * 1.21, 2)
                            if es_serv:
                                st.markdown(f"<div style='font-size:11px; color:#64748b; font-weight:600; margin-top:2px;'>Subtotal S/IVA:</div><div style='font-size:17px; font-weight:800; color:#0f172a; margin-top:4px;'>{sub_m:,.2f} €</div><div style='font-size:11px; color:#4f46e5; font-weight:600;'>c/21% IVA: {sub_m_civa:,.2f} €</div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='font-size:11px; color:#64748b; font-weight:600; margin-top:2px;'>Subtotal S/IVA:</div><div style='font-size:17px; font-weight:800; color:#0f172a; margin-top:4px;'>{sub_m:,.2f} €</div><div style='font-size:11px; color:#0284c7; font-weight:600;'>💳 En caja: {sub_m_civa:,.2f} €</div>", unsafe_allow_html=True)
                            total_mat_calc += sub_m

                        # Fila 3 y 4: Comparativa de Ahorro y Marcas SOLO para materiales físicos
                        if not es_serv:
                            comp = comparar_precios_proveedores(n_mat, prov_sel, base_p, df_bd)
                            if comp["hay_ahorro"]:
                                ahorro_tot = round(comp["ahorro_ud"] * n_cnt, 2)
                                st.markdown(
                                    f"""
                                    <div style="background: linear-gradient(135deg, #fefce8 0%, #fef9c3 100%); border: 2px solid #eab308; border-radius: 10px; padding: 14px 18px; margin: 10px 0;">
                                        <div style="font-size: 16px; font-weight: 800; color: #854d0e;">
                                            💡 ¡AVISO DE PRECIO MÁS BARATO DISPONIBLE!
                                        </div>
                                        <div style="font-size: 15px; color: #713f12; margin-top: 6px; line-height: 1.5;">
                                            En <b>{prov_sel}</b> cuesta <b>{pu_actual:.2f} €/ud</b>, pero tienes distribuidores con precios más económicos:<br/>
                                            👉 <b>La opción más barata es {comp['tienda_min']} a {comp['precio_min']:.2f} €/ud</b> (ahorras <b>{comp['ahorro_ud']:.2f} €/ud</b> · Total: <b>{ahorro_tot:,.2f} €</b>).
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                st.caption("🛒 **Proveedores más baratos disponibles (pulsa para comprar de ahí):**")
                                c_cheap_cols = st.columns(min(len(comp["todas_mas_baratas"]), 3) or 1)
                                for i_tb, tb in enumerate(comp["todas_mas_baratas"]):
                                    tot_ah = round(tb["ahorro_ud"] * n_cnt, 2)
                                    with c_cheap_cols[i_tb % len(c_cheap_cols)]:
                                        btn_type = "primary" if i_tb == 0 else "secondary"
                                        if st.button(
                                            f"🛒 Comprar en {tb['tienda']} ({tb['precio']:.2f} €)",
                                            key=f"btn_apply_store_{idx_m}_{tb['tienda']}_{i_tb}",
                                            use_container_width=True,
                                            type=btn_type,
                                            help=f"Cambiar a {tb['tienda']} a {tb['precio']:.2f} €/ud. Ahorras {tot_ah:,.2f} € para {n_cnt:.0f} uds."
                                        ):
                                            st.session_state[key_prov] = tb['tienda']
                                            st.session_state[key_p] = float(tb['precio'])
                                            st.session_state[key_orig] = f"🏷️ Tarifa Optimizada ({tb['tienda']})"
                                            st.rerun()
                            else:
                                st.markdown(
                                    f"<div style='font-size:13px; color:#15803d; font-weight:700; margin-top:6px;'>"
                                    f"✅ <b>{prov_sel}</b> es el proveedor con el mejor precio disponible para esta partida ({pu_actual:.2f} €/ud).</div>",
                                    unsafe_allow_html=True
                                )

                            # Fila 4: Opción para clientes que quieren más calidad o cambiar de marca
                            with st.expander(f"⭐ ¿El cliente quiere más calidad o cambiar a primeras marcas? (Schneider, Simon, Legrand, Niessen, Zemper...)"):
                                st.caption("Si el cliente pide mayor categoría estética, primeras marcas o gama premium, selecciona una opción oficial del catálogo:")
                                alts_marcas = buscar_marcas_alternativas(n_mat, df_bd)
                                if alts_marcas:
                                    st.markdown("**Marcas de calidad catalogadas para este material:**")
                                    cols_marcas = st.columns(min(len(alts_marcas), 3) or 1)
                                    for i_m, m_alt in enumerate(alts_marcas):
                                        dif_m = round(m_alt['precio'] - pu_actual, 2)
                                        signo_m = f"+{dif_m:.2f} €" if dif_m >= 0 else f"{dif_m:.2f} €"
                                        with cols_marcas[i_m % len(cols_marcas)]:
                                            st.markdown(f"**🏷️ {m_alt['marca']}** (`{m_alt['precio']:.2f} €`)")
                                            st.caption(f"Gama: {m_alt['gama']} · {m_alt['tienda']}\n\n*{m_alt['art'][:36]}*")
                                            if st.button(f"Elegir {m_alt['marca']} ({signo_m})", key=f"btn_alt_m_{idx_m}_{m_alt['marca']}_{i_m}", use_container_width=True):
                                                st.session_state[key_n] = m_alt['art']
                                                st.session_state[key_p] = float(m_alt['precio'])
                                                st.session_state[key_prov] = m_alt['tienda']
                                                st.session_state[key_orig] = f"🏷️ {m_alt['marca']} ({m_alt['gama']})"
                                                st.rerun()

                                st.markdown("---")
                                st.markdown("**Opciones rápidas de salto de gama:**")
                                col_g1, col_g2 = st.columns(2)
                                with col_g1:
                                    p_media = round(pu_actual * 1.35, 2)
                                    if st.button(f"🔵 Calidad Profesional (+35%): ~{p_media:.2f} €/ud", key=f"btn_gama_media_{idx_m}", help="Marcas profesionales: Simon 27, Schneider Ovalis, Legrand Niloé"):
                                        st.session_state[key_n] = f"{n_mat} (Gama Calidad Profesional - Schneider / Simon / Legrand)"
                                        st.session_state[key_p] = float(p_media)
                                        st.session_state[key_orig] = "🏷️ Calidad Profesional (+35%)"
                                        st.rerun()
                                with col_g2:
                                    p_alta = round(pu_actual * 1.75, 2)
                                    if st.button(f"⭐ Calidad Premium (+75%): ~{p_alta:.2f} €/ud", key=f"btn_gama_alta_{idx_m}", help="Marcas premium: Niessen Zenit, Simon 82, Schneider Acti9, Zemper"):
                                        st.session_state[key_n] = f"{n_mat} (Gama Alta Premium - Niessen Zenit / Simon 82 / Schneider Acti9)"
                                        st.session_state[key_p] = float(p_alta)
                                        st.session_state[key_orig] = "⭐ Calidad Alta Premium (+75%)"
                                        st.rerun()
                        else:
                            st.markdown(
                                "<div style='font-size:12px; color:#475569; font-style:italic; margin-top:4px;'>"
                                "🚚 Concepto de logística, compras o desplazamiento técnico (no requiere compra de material físico en almacén).</div>",
                                unsafe_allow_html=True
                            )

                    # Sincronización continua con la lista maestra
                    m_item["mat"] = n_mat
                    m_item["cant"] = n_cnt
                    m_item["p_u"] = n_pu
                    m_item["subtotal"] = sub_m
                    m_item["proveedor"] = prov_sel
                    m_item["origen"] = origen_actual
                    m_item["tipo"] = "servicio" if es_serv else "material"

                    filas_mats_edit.append({
                        "mat": n_mat,
                        "cant": n_cnt,
                        "unid": unid_lbl,
                        "p_u": n_pu,
                        "subtotal": sub_m,
                        "proveedor": prov_sel,
                        "en_bd": ("BD Oficial" in origen_actual),
                        "origen": origen_actual,
                        "es_servicio": es_serv,
                        "tipo": "servicio" if es_serv else "material"
                    })

                    if not es_serv:
                        if prov_sel not in acopio_por_tienda:
                            acopio_por_tienda[prov_sel] = []
                        acopio_por_tienda[prov_sel].append({"mat": n_mat, "cant": n_cnt, "unid": unid_lbl, "p_u": n_pu, "subtotal": sub_m})
                    else:
                        servicios_internos.append({"mat": n_mat, "cant": n_cnt, "unid": unid_lbl, "p_u": n_pu, "subtotal": sub_m, "prov": prov_sel})

                # Botones interactivos para añadir nuevas líneas al escandallo
                st.markdown("")
                c_ins1, c_ins2, _ = st.columns([2.5, 2.8, 2.7])
                with c_ins1:
                    if st.button("➕ 📦 Insertar Material Físico", key="btn_add_mat_row", use_container_width=True):
                        mats.append({
                            "mat": "Nueva Partida de Material Eléctrico",
                            "cant": 1.0,
                            "unid": "ud",
                            "p_u": 10.00,
                            "tipo": "material"
                        })
                        res["materiales"] = mats
                        st.session_state["pr_resultado_escandallo"] = res
                        st.rerun()
                with c_ins2:
                    if st.button("➕ 🚚 Insertar Gestión / Tiempo / Portes", key="btn_add_serv_row", use_container_width=True):
                        mats.append({
                            "mat": "Tiempo invertido en acopio y compra de materiales + transporte",
                            "cant": 1.0,
                            "unid": "servicio",
                            "p_u": 35.00,
                            "proveedor": "Servicio Técnico Propio",
                            "tipo": "servicio"
                        })
                        res["materiales"] = mats
                        st.session_state["pr_resultado_escandallo"] = res
                        st.rerun()

                # Lista de Acopio y Compra por Proveedor
                st.markdown("")
                with st.container(border=True):
                    st.markdown("##### 🛒 Lista de la Compra y Acopio por Proveedor:")
                    st.caption("Materiales físicos organizados por tienda con precio base S/IVA y total real en mostrador (c/21% IVA):")
                    if acopio_por_tienda:
                        cols_tiendas = st.columns(min(len(acopio_por_tienda), 3) or 1)
                        for idx_t, (tienda_k, items_t) in enumerate(acopio_por_tienda.items()):
                            subt_tienda = sum(x["subtotal"] for x in items_t)
                            subt_tienda_civa = round(subt_tienda * 1.21, 2)
                            with cols_tiendas[idx_t % len(cols_tiendas)]:
                                st.markdown(f"**🏬 {tienda_k}**")
                                st.markdown(f"- Base: `{subt_tienda:,.2f} €` S/IVA\n- 💳 **A pagar en caja:** `{subt_tienda_civa:,.2f} €` (c/21% IVA)")
                                for it_c in items_t:
                                    s_it = it_c['subtotal']
                                    st.markdown(f"• `{it_c['cant']:.0f} {it_c['unid']}` {it_c['mat'][:28]} (`{s_it:,.2f} €` · c/IVA: `{s_it*1.21:,.2f} €`)")
                    else:
                        st.info("No hay materiales físicos pendientes de compra en ferretería.")

                    if servicios_internos:
                        st.markdown("---")
                        st.markdown("**🚚 Gestión, Logística y Desplazamiento Interno (Sin compra en ferretería):**")
                        for si in servicios_internos:
                            st.markdown(f"• **{si['mat']}**: `{si['cant']:.1f} {si['unid']}` × `{si['p_u']:.2f} €` = **`{si['subtotal']:,.2f} €`** S/IVA (`{si['subtotal']*1.21:,.2f} €` c/IVA)")

            with col_esc2:
                with st.container(border=True):
                    st.markdown("##### ⏱️ Mano de Obra, Desplazamiento y Totales:")
                    horas_default = float(res.get("horas", 2.5))
                    horas_mo_val = st.number_input("Horas de Mano de Obra (h):", value=horas_default, min_value=0.5, step=0.5, key="pr_horas_mo_in")
                    coste_mo_calc = round(horas_mo_val * precio_hora_mo, 2)
                    desp_calc = float(desplazamiento_val)

                    # Margen Comercial sobre materiales
                    margen_mat_pct = st.slider(
                        "📈 Margen Comercial sobre Materiales (%):",
                        min_value=0, max_value=100,
                        value=int(st.session_state.get("pr_margen_mat_pct", 0)),
                        step=5,
                        key="pr_margen_mat_pct",
                        help="Margen de beneficio comercial aplicado sobre el coste de compra de los materiales para el cliente."
                    )

                    # Desglose claro de costes: Materiales Físicos vs Servicios Logísticos
                    coste_mat_siva = sum(float(x.get("subtotal", 0.0)) for x in filas_mats_edit if not x.get("es_servicio"))
                    coste_mat_civa = round(coste_mat_siva * 1.21, 2)
                    coste_serv_siva = sum(float(x.get("subtotal", 0.0)) for x in filas_mats_edit if x.get("es_servicio"))

                    beneficio_mat = round(coste_mat_siva * (margen_mat_pct / 100.0), 2)
                    pvp_mat_siva = round(coste_mat_siva + beneficio_mat, 2)
                    pvp_mat_civa = round(pvp_mat_siva * 1.21, 2)

                    st.markdown(f"- **Mano de Obra ({tipo_tarifa.split('(')[0].strip()}):** `{horas_mo_val:.1f} h` × `{precio_hora_mo:.2f} €/h` = **`{coste_mo_calc:,.2f} €`**")
                    if margen_mat_pct > 0:
                        st.markdown(f"- **Coste Compra Materiales:** `{coste_mat_siva:,.2f} €` S/IVA (💳 `{coste_mat_civa:,.2f} €` en caja mostrador)")
                        st.markdown(f"- **Margen Comercial (+{margen_mat_pct}%):** `+{beneficio_mat:,.2f} €`")
                        st.markdown(f"- **Materiales Facturados (Cliente):** **`{pvp_mat_siva:,.2f} €`** S/IVA (`{pvp_mat_civa:,.2f} €` c/IVA)")
                    else:
                        st.markdown(f"- **Total Materiales:** **`{coste_mat_siva:,.2f} €`** S/IVA (💳 `{coste_mat_civa:,.2f} €` en mostrador caja)")

                    if coste_serv_siva > 0:
                        st.markdown(f"- **🚚 Gestión / Tiempo de Compras:** **`{coste_serv_siva:,.2f} €`** S/IVA")

                    if desp_calc > 0:
                        st.markdown(f"- **🚗 Salida / Desplazamiento:** **`{desp_calc:,.2f} €`**")

                    subtotal_siva = round(pvp_mat_siva + coste_serv_siva + coste_mo_calc + desp_calc, 2)
                    cuota_iva = round(subtotal_siva * (iva_pct / 100.0), 2)
                    total_civa = round(subtotal_siva + cuota_iva, 2)

                    st.markdown("---")
                    st.markdown(f"#### **Base Imponible (S/IVA):** `{subtotal_siva:,.2f} €`")
                    if iva_pct == 0.0:
                        st.markdown(f"#### **Total a Facturar (0% IVA):** <span style='color:#059669; font-size:24px; font-weight:bold;'>{subtotal_siva:,.2f} €</span>", unsafe_allow_html=True)
                        st.caption("ℹ️ Inversión de Sujeto Pasivo (Art. 84.Uno.2º.f LIVA) o Subcontrata.")
                    else:
                        st.markdown(f"#### **Total Cliente (C/IVA {iva_pct:.0f}%):** <span style='color:#0284c7; font-size:24px; font-weight:bold;'>{total_civa:,.2f} €</span>", unsafe_allow_html=True)

                # Calculadora de Cobro por Foco Cambiado / Punto de Luz Colocado
                with st.container(border=True):
                    st.markdown("##### 💡 Cobro por Foco Cambiado / Punto de Luz:")
                    st.caption("Cálculo instantáneo del coste unitario y precio de venta por foco instalado:")
                    focos_detectados = 0.0
                    for m_it in mats:
                        n_lower = normalizar_texto(m_it.get("mat", ""))
                        if any(w in n_lower for w in ["foco", "downlight", "lampara", "bombilla", "panel led", "pantalla", "ojo de buey", "aplique", "proyector", "punto"]):
                            focos_detectados += float(m_it.get("cant", 1.0))
                    val_init_focos = max(1.0, focos_detectados if focos_detectados > 0 else 1.0)
                    num_focos = st.number_input("Nº de Focos / Puntos de Luz:", min_value=1.0, value=val_init_focos, step=1.0, key="pr_num_focos_in")

                    coste_mat_ud = round(coste_mat_siva / num_focos, 2)
                    pvp_foco_siva = round(subtotal_siva / num_focos, 2)
                    pvp_foco_civa = round(total_civa / num_focos, 2)

                    st.markdown(f"""
                    <div style="background-color: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
                        <div style="font-weight: 700; color: #166534; font-size: 14px;">📊 Desglose por Foco / Punto ({num_focos:.0f} uds):</div>
                        <div style="font-size: 13px; color: #14532d; margin-top: 4px;">
                            • <b>Coste compra material por foco:</b> <code>{coste_mat_ud:,.2f} €</code> S/IVA (<code>{coste_mat_ud * 1.21:,.2f} €</code> en mostrador caja)<br/>
                            • <b>PVP recomendado por foco colocado:</b> <b style="color: #15803d; font-size: 15px;">{pvp_foco_siva:,.2f} € S/IVA</b> ({pvp_foco_civa:,.2f} € C/IVA)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    c_f1, c_f2 = st.columns([1.5, 1.5])
                    with c_f1:
                        tar_foco = st.number_input("🎯 Fijar Precio por Foco (€ S/IVA):", min_value=1.0, value=float(round(pvp_foco_siva, 0)), step=5.0, key="pr_tar_foco_input")
                    with c_f2:
                        tot_f_siva = round(tar_foco * num_focos, 2)
                        tot_f_civa = round(tot_f_siva * (1 + (iva_pct / 100.0)), 2)
                        st.markdown(f"<div style='font-size:11px; color:#64748b; margin-top:4px;'>Total Resultante ({num_focos:.0f} focos):</div><div style='font-size:15px; font-weight:700; color:#0f172a;'>{tot_f_siva:,.2f} € S/IVA ({tot_f_civa:,.2f} € C/IVA)</div>", unsafe_allow_html=True)

                    if st.button(f"🎯 Aplicar {tar_foco:.2f} €/foco al Presupuesto", key="btn_apply_foco_pvp", use_container_width=True):
                        base_aplicar = tot_f_civa if iva_pct > 0 else tot_f_siva
                        st.session_state["pr_target_round"] = float(base_aplicar)
                        st.rerun()

            # 5. Opciones de Negociación y Ajuste a Precio Cerrado
            st.markdown("---")
            col_neg1, col_neg2, col_neg3 = st.columns([1.5, 1.5, 2])
            with col_neg1:
                precio_base_redondeo = total_civa if iva_pct > 0 else subtotal_siva
                if "pr_target_round" not in st.session_state:
                    st.session_state["pr_target_round"] = float(round(precio_base_redondeo, 0))
                target_quick = st.number_input("🎯 Ajustar a Precio Redondo Cerrado (€):", step=10.0, format="%.2f", key="pr_target_round")
            with col_neg2:
                dif_quick = target_quick - precio_base_redondeo
                signo = "+" if dif_quick > 0 else ""
                st.caption(f"Ajuste comercial aplicado: `{signo}{dif_quick:,.2f} €`")
                st.markdown(f"**Precio Final Acordado:** `{target_quick:,.2f} €`")
            with col_neg3:
                if st.button("📥 Incorporar a Presupuesto Vivienda", type="primary", use_container_width=True, key="btn_transfer_to_vivienda"):
                    if "partidas_manuales" not in st.session_state:
                        st.session_state.partidas_manuales = []
                    sub_final_siva = round(target_quick / (1 + (iva_pct / 100.0)), 2)
                    st.session_state.partidas_manuales.append({
                        "id": f"PM-{len(st.session_state.partidas_manuales) + 1:02d}",
                        "concepto": res.get("concepto", "Trabajo Eléctrico"),
                        "descripcion": res.get("descripcion_detallada", f"Instalación según {res.get('norma', 'REBT')}: {res.get('consulta_orig', '')}") + (f" [Tarifa: {tipo_tarifa}]" if tipo_tarifa else ""),
                        "cantidad": 1.0,
                        "unidad": "partida",
                        "precio_unitario": sub_final_siva,
                        "subtotal": sub_final_siva
                    })
                    st.session_state.presupuesto_calculado = True
                    st.success(f"✅ Trabajo '{res.get('concepto')}' transferido con su memoria completa al Presupuesto de Vivienda.")

            # 6. Orden Oficial de Compra y Acopio para Almacén / Tienda
            st.markdown("---")
            st.markdown("### 🛒 Orden Oficial de Compra y Acopio de Materiales")
            st.caption("Detalle consolidado de compras organizado por proveedor y listo para mostrador de tienda o almacén:")

            usuario_actual = st.session_state.get("usuario_autenticado") or {}

            # Descargas en PDF y Excel
            st.markdown("##### 📥 Descargas Oficiales en PDF y Excel:")
            c_pdf1, c_pdf2, c_xlsx = st.columns(3)
            with c_pdf1:
                pdf_pres_bytes = generar_pdf_presupuesto_rapido(
                    res, filas_mats_edit, nom_cliente, horas_mo_val, precio_hora_mo,
                    coste_mo_calc, pvp_mat_siva, subtotal_siva, total_civa, iva_pct, usuario_actual,
                    desplazamiento=desp_calc, tipo_tarifa=tipo_tarifa
                )
                st.download_button(
                    label="📄 Descargar Presupuesto (PDF)",
                    data=pdf_pres_bytes,
                    file_name=f"Presupuesto_{datetime.date.today().strftime('%Y%m%d')}_{nom_cliente[:15].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                    key="btn_descargar_presupuesto_pdf_rapido"
                )
            with c_pdf2:
                pdf_oc_bytes = generar_pdf_orden_compra_rapida(
                    filas_mats_edit, nom_cliente, res.get("concepto", "Aviso"),
                    coste_mat_siva, iva_pct, usuario_actual
                )
                st.download_button(
                    label="📦 Descargar Orden Compra (PDF)",
                    data=pdf_oc_bytes,
                    file_name=f"Orden_Compra_{datetime.date.today().strftime('%Y%m%d')}_{nom_cliente[:15].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="btn_descargar_orden_compra_pdf_rapido"
                )
            with c_xlsx:
                excel_bytes = generar_excel_orden_compra(filas_mats_edit, nom_cliente, res.get("concepto", "Aviso Urgente"))
                st.download_button(
                    label="📊 Descargar Compra (Excel)",
                    data=excel_bytes,
                    file_name=f"Orden_Compra_{datetime.date.today().strftime('%Y%m%d')}_{nom_cliente[:15].replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="btn_descargar_orden_compra_xlsx_rapido"
                )

            # Vista Previa Interactiva en Pantalla del PDF Oficial
            with st.expander("👁️ Vista Previa del Presupuesto Oficial en Pantalla antes de Descargar", expanded=True):
                st.info("💡 **Vista previa en tiempo real.** Revisa que los importes, capítulos REBT y datos del instalador coinciden al 100%:")
                try:
                    import pymupdf
                    doc_pv = pymupdf.open(stream=pdf_pres_bytes, filetype="pdf")
                    for num_p, pag in enumerate(doc_pv, start=1):
                        pix = pag.get_pixmap(dpi=140)
                        if len(doc_pv) > 1:
                            st.caption(f"📄 Página {num_p} de {len(doc_pv)}")
                        st.image(pix.tobytes("png"), use_container_width=True)
                except Exception:
                    pass


            # Panel Comercial Integral: Balance Empresa vs Autónomo, Semáforo y Auditor de Contraofertas
            try:
                from modulos import herramientas_presupuesto
                datos_pr_hp = {
                    "coste_materiales": coste_mat_siva,
                    "margen_materiales_pct": 25.0,
                    "horas_mano_obra": horas_mo_val,
                    "precio_hora_coste": precio_hora_mo,
                    "recargo_empresa_mo_pct": 40.0,
                    "coste_tramitacion": 0.0,
                    "desplazamiento": desp_calc,
                    "iva_pct": iva_pct,
                    "cliente": nom_cliente,
                    "concepto": res.get("concepto", "Aviso Urgente"),
                    "filas_materiales": filas_mats_edit
                }
                herramientas_presupuesto.render_panel_herramientas_presupuesto(datos_pr_hp, modulo_nombre="Presupuesto Rápido IA", key_prefix="pr_hp")
            except Exception as e:
                st.info(f"Herramientas de presupuesto disponibles: {e}")
            # Envío Directo por WhatsApp solicitando teléfono
            st.markdown("")
            with st.container(border=True):
                st.markdown("##### 📲 Enviar por WhatsApp con 1 Clic:")
                st.caption("Introduce el número de teléfono móvil al que deseas enviar la orden de compra o el presupuesto (puedes poner los 9 dígitos o incluir prefijo internacional):")
                
                txt_wsp_compra = generar_texto_whatsapp_compra(filas_mats_edit, nom_cliente, res.get("concepto", "Aviso"), coste_mat_siva)
                txt_wsp_presup = generar_texto_whatsapp_presupuesto(
                    nom_cliente, res.get("concepto", "Aviso"), subtotal_siva, total_civa, iva_pct,
                    horas_mo_val, precio_hora_mo, coste_mo_calc, pvp_mat_siva, filas_mats_edit,
                    desplazamiento=desp_calc, tipo_tarifa=tipo_tarifa
                )
                
                col_w_tel, col_w_b1, col_w_b2 = st.columns([1.8, 1.3, 1.3])
                with col_w_tel:
                    tel_wsp_in = st.text_input(
                        "📱 Número de Teléfono / WhatsApp de Destino:",
                        placeholder="Ej: 600123456 (o vacío para elegir chat)",
                        key="pr_tel_wsp_input_box",
                        help="Escribe el móvil del compañero, tienda de suministros o cliente."
                    )
                
                num_digits = re.sub(r'[^0-9]', '', str(tel_wsp_in).strip())
                if len(num_digits) == 9 and not num_digits.startswith("34"):
                    num_digits = "34" + num_digits

                url_wa_compra = f"https://api.whatsapp.com/send?phone={num_digits}&text={urllib.parse.quote(txt_wsp_compra)}" if num_digits else f"https://api.whatsapp.com/send?text={urllib.parse.quote(txt_wsp_compra)}"
                url_wa_presup = f"https://api.whatsapp.com/send?phone={num_digits}&text={urllib.parse.quote(txt_wsp_presup)}" if num_digits else f"https://api.whatsapp.com/send?text={urllib.parse.quote(txt_wsp_presup)}"

                with col_w_b1:
                    st.markdown(
                        f"<a href='{url_wa_compra}' target='_blank' style='display:block; text-align:center; background-color:#25D366; color:white; font-weight:bold; padding:8px 10px; border-radius:6px; text-decoration:none; margin-top:24px; box-shadow:0 1px 3px rgba(0,0,0,0.12);'>"
                        f"🛒 Enviar Compra a WhatsApp</a>",
                        unsafe_allow_html=True
                    )
                with col_w_b2:
                    st.markdown(
                        f"<a href='{url_wa_presup}' target='_blank' style='display:block; text-align:center; background-color:#0284c7; color:white; font-weight:bold; padding:8px 10px; border-radius:6px; text-decoration:none; margin-top:24px; box-shadow:0 1px 3px rgba(0,0,0,0.12);'>"
                        f"⚡ Enviar Presupuesto al Cliente</a>",
                        unsafe_allow_html=True
                    )

                with st.popover("📋 Ver texto formateado de WhatsApp para copiar", use_container_width=True):
                    st.text_area("Texto Orden de Compra para Tienda / Mostrador:", value=txt_wsp_compra, height=180, key="pr_wsp_compra_copy")
                    st.text_area("Texto Presupuesto Oficial para Cliente:", value=txt_wsp_presup, height=180, key="pr_wsp_presup_copy")

            # Tabla formal consolidada de la orden de compra ordenada por proveedor
            st.markdown("")
            st.markdown("### 🛒 Orden Consolidada de Materiales y Acopio en Tiendas")
            st.caption(f"Coste Total Materiales Físicos en Mostrador: **{coste_mat_siva:,.2f} € S/IVA** · 💳 **{coste_mat_civa:,.2f} € (c/21% IVA en caja)**")
            filas_orden_ordenadas = sorted(filas_mats_edit, key=lambda x: (x.get("proveedor", ""), x.get("mat", "")))
            df_orden_view = pd.DataFrame([
                {
                    "🏬 Tienda / Proveedor": f["proveedor"],
                    "📦 Material / Partida": f["mat"],
                    "Cant.": f"{f['cant']:.1f} {f['unid']}",
                    "P. Unit S/IVA (€)": f"{f['p_u']:.2f} €",
                    "Subtotal S/IVA (€)": f"{f['subtotal']:.2f} €",
                    "💳 Mostrador c/21% IVA (€)": f"{f['subtotal'] * 1.21:.2f} €" if not f.get("es_servicio") else "— (Servicio Propio)",
                    "Naturaleza": "🚚 Servicio / Logística" if f.get("es_servicio") else "📦 Material Físico",
                    "Origen Tarifa": f["origen"],
                    "Estado Acopio": "⏳ Pendiente"
                }
                for f in filas_orden_ordenadas
            ])
            st.dataframe(df_orden_view, use_container_width=True, hide_index=True)
