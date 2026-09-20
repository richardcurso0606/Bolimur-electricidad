# -*- coding: utf-8 -*-
"""
Módulo Profesional de Presupuestos Eléctricos: Desglose por Estancias
Autor: Richard Orlando Choque Tejerina (Bolimur Instalaciones y Reformas)

Vista 1 (interna): coste real para ti, con precios sacados de tu Excel de materiales.
Vista 2 (comercial): presupuesto para el cliente, menos detallado, con tus precios de venta.
Incluye: guardado/carga de presupuestos anteriores y exportación a PDF profesional.
"""

import streamlit as st
import pandas as pd
import openpyxl
import os
import json
import io
import sqlite3
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

st.set_page_config(page_title="Presupuestos Bolimur", layout="wide")

# ==========================================================
# 0. CONSTANTES Y RUTAS
# ==========================================================

COL_GAMA = "Nivel de Gama / Aplicación"
COL_FAMILIA = "Familia / Categoria"
COL_DESC = "Descripción Exacta del Artículo"
COL_PRECIO = "Precio S/IVA (€)"
COL_UNIDAD = "Unidad"

ARCHIVO_GUARDADOS = "presupuestos.db"


# ==========================================================
# 1. PRECIOS
# ==========================================================

@st.cache_data(show_spinner=False)
def cargar_precios():
    nombres_posibles = [
        "base_datos_precio_oficial.xlsx",
        "Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy_v2.xlsx",
        "Base_Datos_Precios_Master_Exhaustiva_Obramat_Leroy.xlsx",
    ]
    for f in os.listdir("."):
        if f.endswith(".xlsx") and (
            "precio" in f.lower() or "master" in f.lower() or "oficial" in f.lower()
        ):
            nombres_posibles.insert(0, f)

    for nombre in nombres_posibles:
        if os.path.exists(nombre):
            try:
                wb = openpyxl.load_workbook(nombre, data_only=True)
                hoja_activa = wb.sheetnames[0]
                for h in wb.sheetnames:
                    if "maestra" in h.lower() or "completa" in h.lower() or "tarifa" in h.lower():
                        hoja_activa = h
                        break
                ws = wb[hoja_activa]
                data = list(ws.iter_rows(values_only=True))
                df = pd.DataFrame(data[1:], columns=data[0])
                df[COL_PRECIO] = pd.to_numeric(df[COL_PRECIO], errors="coerce")
                return df, nombre
            except Exception:
                continue
    return None, None


def precio_medio(df, familia, gama=None, keywords=None, unidad=None):
    """Precio medio (S/IVA) para una familia de artículos, filtrando por
    gama, unidad y una lista de palabras clave que deben aparecer TODAS en
    la descripción (texto plano, no regex). Si el filtro por gama no da
    resultados, cae a la familia completa (cable, tubo y cajas no tienen
    nivel de gama)."""
    f = df[df[COL_FAMILIA] == familia]
    if unidad:
        f = f[f[COL_UNIDAD] == unidad]
    if keywords:
        for kw in keywords:
            f = f[f[COL_DESC].str.contains(kw, case=False, na=False, regex=False)]

    f_gama = f
    if gama:
        f_gama = f[f[COL_GAMA] == gama]

    objetivo = f_gama if len(f_gama) > 0 else f
    if len(objetivo) == 0:
        return None
    return round(float(objetivo[COL_PRECIO].mean()), 4)


# ==========================================================
# 2. GUARDADO / CARGA DE PRESUPUESTOS (SQLite)
# ==========================================================
# SQLite en vez de un .json: soporta mejor varios presupuestos, permite
# consultar/filtrar más adelante, y es igual de "gratis" (viene con Python,
# no necesita instalar ni contratar nada). Eso sí: al igual que el .json,
# es un archivo en el disco de donde ejecutes la app — si algún día la
# despliegas en un hosting gratuito con disco temporal (p.ej. Streamlit
# Community Cloud), ese archivo puede perderse al reiniciarse el contenedor.
# Mientras la pruebas en tu ordenador, no tienes ese problema.

def get_conn():
    conn = sqlite3.connect(ARCHIVO_GUARDADOS)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS presupuestos (
            id TEXT PRIMARY KEY,
            fecha TEXT,
            cliente_nombre TEXT,
            cliente_json TEXT,
            parametros_json TEXT,
            estancias_json TEXT,
            resultados_json TEXT,
            filas_cliente_json TEXT,
            filas_internas_json TEXT
        )
    """)
    return conn


def cargar_presupuestos_guardados():
    conn = get_conn()
    filas = conn.execute(
        "SELECT id, fecha, cliente_json, parametros_json, estancias_json, "
        "resultados_json, filas_cliente_json, filas_internas_json "
        "FROM presupuestos ORDER BY id"
    ).fetchall()
    conn.close()
    registros = []
    for r in filas:
        registros.append({
            "id": r[0],
            "fecha": r[1],
            "cliente": json.loads(r[2]),
            "parametros": json.loads(r[3]),
            "estancias": json.loads(r[4]),
            "resultados": json.loads(r[5]),
            "filas_cliente": json.loads(r[6]) if r[6] else [],
            "filas_internas": json.loads(r[7]) if r[7] else [],
        })
    return registros


def guardar_presupuesto(record):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO presupuestos "
        "(id, fecha, cliente_nombre, cliente_json, parametros_json, estancias_json, "
        "resultados_json, filas_cliente_json, filas_internas_json) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (
            record["id"], record["fecha"], record["cliente"].get("nombre", ""),
            json.dumps(record["cliente"], ensure_ascii=False),
            json.dumps(record["parametros"], ensure_ascii=False),
            json.dumps(record["estancias"], ensure_ascii=False),
            json.dumps(record["resultados"], ensure_ascii=False),
            json.dumps(record.get("filas_cliente", []), ensure_ascii=False),
            json.dumps(record.get("filas_internas", []), ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def borrar_presupuesto(id_presupuesto):
    conn = get_conn()
    conn.execute("DELETE FROM presupuestos WHERE id=?", (id_presupuesto,))
    conn.commit()
    conn.close()


def siguiente_numero_presupuesto():
    registros = cargar_presupuestos_guardados()
    anio = date.today().year
    del_anio = [r for r in registros if r["id"].startswith(str(anio))]
    return f"{anio}-{len(del_anio) + 1:04d}"


# ==========================================================
# 3. GENERACIÓN DE PDF PROFESIONAL (VISTA CLIENTE)
# ==========================================================

def generar_pdf_cliente(datos_empresa, datos_cliente, num_presupuesto, fecha_str,
                         tipo_obra, gama_sel, filas_cliente, precio_venta_cuadro,
                         num_circuitos, subtotal, cuota_iva, iva_sel, total_cliente):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Empresa", fontSize=16, leading=19, textColor=colors.HexColor("#0369a1"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12, textColor=colors.HexColor("#334155")))
    styles.add(ParagraphStyle(name="SmallRight", fontSize=9, leading=12, alignment=TA_RIGHT, textColor=colors.HexColor("#334155")))
    styles.add(ParagraphStyle(name="Total", fontSize=14, leading=18, alignment=TA_RIGHT, textColor=colors.HexColor("#16a34a"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SeccionTitulo", fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"), spaceBefore=10, spaceAfter=4))

    elementos = []

    # --- Cabecera ---
    elementos.append(Paragraph(datos_empresa["nombre"], styles["Empresa"]))
    elementos.append(Paragraph(
        f"Instalador Autorizado REBT ({datos_empresa['licencia']}) &nbsp;|&nbsp; "
        f"{datos_empresa['localidad']} &nbsp;|&nbsp; Tel: {datos_empresa['telefono']}",
        styles["Small"]))
    elementos.append(Spacer(1, 6))
    elementos.append(HRFlowable(width="100%", color=colors.HexColor("#bae6fd"), thickness=1))
    elementos.append(Spacer(1, 8))

    tabla_cab = Table(
        [[Paragraph(f"<b>Presupuesto Nº:</b> {num_presupuesto}<br/><b>Fecha:</b> {fecha_str}", styles["Small"]),
          Paragraph(f"<b>Cliente:</b> {datos_cliente['nombre']}<br/>"
                    f"{datos_cliente.get('direccion','')}<br/>"
                    f"Tel: {datos_cliente.get('telefono','')}", styles["SmallRight"])]],
        colWidths=[90 * mm, 82 * mm],
    )
    elementos.append(tabla_cab)
    elementos.append(Spacer(1, 6))
    elementos.append(Paragraph(f"<b>Sistema de ejecución:</b> {tipo_obra} &nbsp;|&nbsp; <b>Gama de mecanismos:</b> {gama_sel}", styles["Small"]))
    elementos.append(Spacer(1, 12))

    # --- Tabla de estancias ---
    elementos.append(Paragraph("Desglose por Estancias", styles["SeccionTitulo"]))
    data_tabla = [["Estancia", "Superficie", "Importe (€)"]]
    for f in filas_cliente:
        data_tabla.append([f["Estancia"], f["Superficie"], f"{f['Precio (€)']:.2f} €"])
    data_tabla.append([f"Cuadro General, Protecciones ({num_circuitos} circuitos) y Boletín", "", f"{precio_venta_cuadro:.2f} €"])

    t = Table(data_tabla, colWidths=[100 * mm, 35 * mm, 37 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0369a1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elementos.append(t)
    elementos.append(Spacer(1, 10))

    # --- Totales ---
    tabla_totales = Table(
        [["Subtotal Neto:", f"{subtotal:.2f} €"],
         [f"IVA ({iva_sel}%):", f"{cuota_iva:.2f} €"],
         ["TOTAL PRESUPUESTO:", f"{total_cliente:.2f} €"]],
        colWidths=[135 * mm, 37 * mm],
    )
    tabla_totales.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, 1), 10),
        ("FONTSIZE", (0, 2), (-1, 2), 13),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 2), (-1, 2), colors.HexColor("#16a34a")),
        ("LINEABOVE", (0, 2), (-1, 2), 0.75, colors.HexColor("#16a34a")),
        ("TOPPADDING", (0, 2), (-1, 2), 6),
    ]))
    elementos.append(tabla_totales)
    elementos.append(Spacer(1, 16))

    # --- Condiciones ---
    elementos.append(Paragraph("Condiciones Generales", styles["SeccionTitulo"]))
    condiciones = (
        "• Validez de la oferta: 30 días.<br/>"
        "• Forma de pago: 40% a la aceptación, 40% a mitad de ejecución y 20% a la "
        "finalización y entrega del Boletín Oficial (CIE).<br/>"
        "• Garantía: 2 años en instalación ejecutada según REBT."
    )
    elementos.append(Paragraph(condiciones, styles["Small"]))
    elementos.append(Spacer(1, 24))

    tabla_firmas = Table(
        [["_________________________", "_________________________"],
         ["El Instalador", "El Cliente (Conforme)"]],
        colWidths=[86 * mm, 86 * mm],
    )
    tabla_firmas.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
    ]))
    elementos.append(tabla_firmas)

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


def generar_pdf_interno(datos_empresa, num_presupuesto, fecha_str, cliente_nombre,
                         precios_usados, filas_internas, coste_total_materiales,
                         horas_totales_obra, num_operarios, coste_mano_obra, coste_total_real):
    """PDF de uso interno: coste real detallado por estancia. No incluye
    margen ni precios de venta — es solo para ti, no para el cliente."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=14 * mm, rightMargin=14 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="EmpresaInt", fontSize=15, leading=18, textColor=colors.HexColor("#7c2d12"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SmallInt", fontSize=8.5, leading=11, textColor=colors.HexColor("#334155")))
    styles.add(ParagraphStyle(name="SeccionInt", fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a"), spaceBefore=10, spaceAfter=4))

    elementos = []
    elementos.append(Paragraph("USO INTERNO — NO ENTREGAR AL CLIENTE", ParagraphStyle(
        name="Aviso", fontSize=9, textColor=colors.white, backColor=colors.HexColor("#7c2d12"),
        alignment=TA_CENTER, spaceAfter=10, borderPadding=4)))
    elementos.append(Paragraph(f"{datos_empresa['nombre']} — Coste Real de Ejecución", styles["EmpresaInt"]))
    elementos.append(Paragraph(f"Presupuesto Nº: {num_presupuesto} &nbsp;|&nbsp; Fecha: {fecha_str} &nbsp;|&nbsp; Cliente: {cliente_nombre or '—'}", styles["SmallInt"]))
    elementos.append(Spacer(1, 6))
    elementos.append(HRFlowable(width="100%", color=colors.HexColor("#fed7aa"), thickness=1))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("Precios unitarios usados (de tu Excel de materiales)", styles["SeccionInt"]))
    data_precios = [["Concepto", "Precio (€)"]]
    for k, v in precios_usados.items():
        data_precios.append([k, f"{v:.3f} €"])
    tp = Table(data_precios, colWidths=[130 * mm, 40 * mm])
    tp.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c2d12")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff7ed")]),
    ]))
    elementos.append(tp)
    elementos.append(Spacer(1, 12))

    elementos.append(Paragraph("Desglose de Coste Real por Estancia", styles["SeccionInt"]))
    cabecera = ["Estancia", "m²", "Tubo(m)", "Fase(m)", "Neutro(m)", "Tierra(m)", "Mec.", "Materiales", "Horas", "M.Obra", "COSTE REAL"]
    data_int = [cabecera]
    for f in filas_internas:
        data_int.append([
            f["Estancia"], f["m²"], f["Tubo (m)"], f["Cable Fase (m)"], f["Cable Neutro (m)"],
            f["Cable Tierra (m)"], f["Mecanismos (ud)"], f"{f['Coste Materiales (€)']:.2f}",
            f["Horas MO"], f"{f['Coste MO (€)']:.2f}", f"{f['TU COSTE REAL (€)']:.2f}",
        ])
    ti = Table(data_int, colWidths=[26 * mm, 9 * mm, 13 * mm, 13 * mm, 14 * mm, 13 * mm, 9 * mm, 17 * mm, 12 * mm, 15 * mm, 19 * mm])
    ti.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c2d12")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 6.8),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff7ed")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elementos.append(ti)
    elementos.append(Spacer(1, 14))

    tabla_totales = Table(
        [["Total Materiales:", f"{coste_total_materiales:.2f} €"],
         [f"Total Horas MO ({num_operarios} operario/s):", f"{horas_totales_obra:.1f} h"],
         ["Total Mano de Obra:", f"{coste_mano_obra:.2f} €"],
         ["TU COSTE TOTAL DE EJECUCIÓN:", f"{coste_total_real:.2f} €"]],
        colWidths=[135 * mm, 40 * mm],
    )
    tabla_totales.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, 2), 9.5),
        ("FONTSIZE", (0, 3), (-1, 3), 12),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 3), (-1, 3), colors.HexColor("#7c2d12")),
        ("LINEABOVE", (0, 3), (-1, 3), 0.75, colors.HexColor("#7c2d12")),
        ("TOPPADDING", (0, 3), (-1, 3), 6),
    ]))
    elementos.append(tabla_totales)

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================================
# 4. APP
# ==========================================================

def app():
    st.markdown(
        """
        <style>
            @media print {
                [data-testid="stSidebar"] {display: none;}
                [data-testid="stHeader"] {display: none;}
                .stButton {display: none;}
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🏡 Presupuestos Eléctricos por Estancias")
    st.caption("Cálculo interno con tus precios reales de materiales + vista comercial para el cliente, guardado de presupuestos y PDF profesional.")

    df_precios, excel_cargado = cargar_precios()
    if df_precios is None:
        st.error(
            "⚠️ No se encontró el Excel de precios. Colócalo en la misma carpeta que esta "
            "app (`base_datos_precio_oficial.xlsx`)."
        )
        return
    st.sidebar.success(f"📁 Base de datos: `{excel_cargado}` ({len(df_precios)} artículos)")

    # ------------------------------------------------------
    # SIDEBAR: DATOS DE LA EMPRESA
    # ------------------------------------------------------
    st.sidebar.header("🏢 Datos del Instalador")
    empresa_nombre = st.sidebar.text_input("Nombre Empresa", value="BOLIMUR INSTALACIONES Y REFORMAS")
    n_licencia = st.sidebar.text_input("Nº Licencia / REBT", value="REBT-30/15892")
    localidad = st.sidebar.text_input("Localidad", value="Rincón de Seca, Murcia")
    telefono = st.sidebar.text_input("Teléfono Contacto", value="+34 600 000 000")

    # ------------------------------------------------------
    # SIDEBAR: PRESUPUESTOS GUARDADOS
    # ------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Presupuestos Guardados")
    registros = cargar_presupuestos_guardados()
    if registros:
        opciones = {f"{r['id']} — {r['cliente']['nombre']} ({r['fecha']})": r for r in reversed(registros)}
        elegido = st.sidebar.selectbox("Presupuestos anteriores", list(opciones.keys()))
        col_load, col_del = st.sidebar.columns(2)
        with col_load:
            cargar_click = st.button("📂 Cargar", use_container_width=True)
        with col_del:
            borrar_click = st.button("🗑️ Borrar", use_container_width=True)

        if cargar_click:
            registro = opciones[elegido]

            # Limpia las claves de widget de las estancias actuales, para que
            # no "pisen" con su valor viejo a los datos que vamos a cargar.
            n_actual = len(st.session_state.get("estancias_pro", []))
            for i in range(n_actual):
                for prefijo in ("nombre_est_", "m2_est_", "inc_est_"):
                    st.session_state.pop(f"{prefijo}{i}", None)

            st.session_state.estancias_pro = registro["estancias"]
            for k, v in registro["parametros"].items():
                st.session_state[k] = v
            st.session_state.cliente_nombre_input = registro["cliente"].get("nombre", "")
            st.session_state.cliente_direccion_input = registro["cliente"].get("direccion", "")
            st.session_state.cliente_telefono_input = registro["cliente"].get("telefono", "")
            st.session_state.num_presupuesto_cargado = registro["id"]
            st.sidebar.success(f"Cargado {registro['id']}")
            st.rerun()

        if borrar_click:
            registro = opciones[elegido]
            borrar_presupuesto(registro["id"])
            st.sidebar.success("Presupuesto borrado.")
            st.rerun()
    else:
        st.sidebar.caption("Todavía no has guardado ningún presupuesto.")

    # ------------------------------------------------------
    # DATOS DEL CLIENTE Y Nº DE PRESUPUESTO
    # ------------------------------------------------------
    st.markdown("---")
    st.subheader("🧾 Datos del Cliente y Presupuesto")
    num_presupuesto = st.session_state.get("num_presupuesto_cargado") or siguiente_numero_presupuesto()
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        cliente_nombre = st.text_input("Nombre del Cliente", key="cliente_nombre_input")
    with col_c2:
        cliente_direccion = st.text_input("Dirección de la Obra", key="cliente_direccion_input")
    with col_c3:
        cliente_telefono = st.text_input("Teléfono del Cliente", key="cliente_telefono_input")
    st.caption(f"Presupuesto Nº **{num_presupuesto}** — Fecha: {date.today().strftime('%d/%m/%Y')}")

    # ------------------------------------------------------
    # PARÁMETROS DE MATERIALES
    # ------------------------------------------------------
    st.markdown("---")
    st.subheader("⚙️ Parámetros de la Instalación")

    col1, col2, col3 = st.columns(3)
    with col1:
        tipo_obra = st.selectbox(
            "Sistema de Ejecución",
            ["Empotrada en Rozas (Ladrillo + Yeso)", "Falso Techo / Pladur (Obra Seca)", "Superficie (Tubo visto / Canaleta)"],
            key="tipo_obra",
        )
    with col2:
        gama_sel = st.selectbox(
            "Gama de Mecanismos",
            ["1. Ultra Económica", "2. Económica Estándar", "3. Media Residencial", "4. Alta Decorativa"],
            key="gama_sel",
        )
    with col3:
        diametro_tubo = st.selectbox("Diámetro de tubo corrugado", ["M16 LH", "M20 LH", "M25 LH", "M32 LH"], index=1, key="diametro_tubo")

    col4, col5 = st.columns(2)
    with col4:
        seccion_cable = st.selectbox("Sección de cable (circuitos estancia)", ["1.5mm²", "2.5mm²"], index=0, key="seccion_cable")
    with col5:
        proveedor_pref = st.selectbox("Proveedor preferente para precios", ["Media (Obramat + Leroy Merlin)", "Solo Obramat", "Solo Leroy Merlin"], key="proveedor_pref")

    df_trabajo = df_precios
    if proveedor_pref == "Solo Obramat":
        df_trabajo = df_precios[df_precios["Proveedor / Tienda"] == "Obramat"]
    elif proveedor_pref == "Solo Leroy Merlin":
        df_trabajo = df_precios[df_precios["Proveedor / Tienda"] == "Leroy Merlin"]

    # ------------------------------------------------------
    # MANO DE OBRA (EDITABLE)
    # ------------------------------------------------------
    st.markdown("---")
    st.subheader("👷 Mano de Obra: Precio y Rendimientos (editable)")
    st.caption("Ajusta el precio/hora y las horas que realmente tardas en cada tarea por m². Estos valores alimentan todos los cálculos siguientes.")

    col_mo1, col_mo2 = st.columns(2)
    with col_mo1:
        precio_hora = st.number_input("Precio Mano de Obra (€/hora)", min_value=5.0, max_value=100.0, value=25.0, step=1.0, key="precio_hora")
    with col_mo2:
        num_operarios = st.number_input("Nº de Operarios en Obra", min_value=1, max_value=5, value=1, step=1, key="num_operarios")

    with st.expander("⏱️ Rendimientos por tarea (horas por m², editable)", expanded=False):
        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            h_rozas_m2 = st.number_input("Rozas y albañilería (h/m²)", min_value=0.0, max_value=2.0, value=0.35, step=0.05, key="h_rozas_m2",
                                          help="Solo se aplica si el sistema es Empotrada en Rozas")
        with rc2:
            h_tubo_m2 = st.number_input("Tubo y cajas (h/m²)", min_value=0.0, max_value=2.0, value=0.20, step=0.05, key="h_tubo_m2")
        with rc3:
            h_cableado_m2 = st.number_input("Cableado y colores (h/m²)", min_value=0.0, max_value=2.0, value=0.25, step=0.05, key="h_cableado_m2")
        with rc4:
            h_mecanizado_ud = st.number_input("Mecanizado (h/mecanismo)", min_value=0.0, max_value=1.0, value=0.15, step=0.05, key="h_mecanizado_ud")

    # ------------------------------------------------------
    # MARGEN E IVA
    # ------------------------------------------------------
    st.markdown("---")
    st.subheader("💼 Precio de Venta al Cliente")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        margen_comercial = st.slider("Margen sobre tu coste real (%)", 0, 100, 35, key="margen_comercial",
                                      help="Se aplica sobre TU coste real (materiales del Excel + mano de obra), no sobre una tarifa fija.")
    with col_v2:
        iva_sel = st.selectbox("Tipo de IVA a aplicar al cliente", [10, 21], key="iva_sel")

    st.markdown("---")

    # ------------------------------------------------------
    # ESTANCIAS
    # ------------------------------------------------------
    if "estancias_pro" not in st.session_state:
        st.session_state.estancias_pro = [
            {"nombre": "Salón - Comedor", "m2": 25.0, "incluir": True},
            {"nombre": "Cocina", "m2": 12.0, "incluir": True},
            {"nombre": "Dormitorio Principal", "m2": 16.0, "incluir": True},
            {"nombre": "Dormitorio 2", "m2": 11.0, "incluir": True},
            {"nombre": "Baño 1", "m2": 6.0, "incluir": True},
            {"nombre": "Pasillo", "m2": 7.0, "incluir": True},
        ]

    st.subheader("📋 Estancias de la Vivienda")

    col_add, col_del = st.columns(2)
    with col_add:
        if st.button("➕ Añadir estancia"):
            st.session_state.estancias_pro.append({"nombre": f"Estancia {len(st.session_state.estancias_pro)+1}", "m2": 10.0, "incluir": True})
    with col_del:
        if st.button("➖ Quitar última estancia") and len(st.session_state.estancias_pro) > 1:
            st.session_state.estancias_pro.pop()

    estancias_activas = []
    for i, est in enumerate(st.session_state.estancias_pro):
        cols = st.columns([3, 2, 1])
        with cols[0]:
            est["nombre"] = st.text_input(f"Nombre {i}", value=est["nombre"], key=f"nombre_est_{i}", label_visibility="collapsed")
        with cols[1]:
            est["m2"] = st.number_input(f"m2 {i}", value=est["m2"], min_value=1.0, step=0.5, key=f"m2_est_{i}", label_visibility="collapsed")
        with cols[2]:
            est["incluir"] = st.checkbox("Incluir", value=est["incluir"], key=f"inc_est_{i}")
        if est["incluir"]:
            estancias_activas.append(est)

    st.markdown("---")

    calcular_click = st.button("🚀 Calcular Presupuesto", type="primary")

    if calcular_click or st.session_state.get("ultimo_calculo"):
        if not estancias_activas:
            st.warning("Selecciona al menos una estancia.")
            return

        # --- Precios unitarios reales ---
        seccion_num = seccion_cable.replace("mm²", "")
        diametro_num = diametro_tubo.split()[0]

        p_tubo = precio_medio(df_trabajo, "Canalización Tubos", keywords=["Corrugado", diametro_num], unidad="m") or 0.5
        p_fase = precio_medio(df_trabajo, "Conductores", keywords=[seccion_num, "Marrón"]) or 0.3
        p_neutro = precio_medio(df_trabajo, "Conductores", keywords=[seccion_num, "Azul"]) or 0.3
        p_tierra = precio_medio(df_trabajo, "Conductores", keywords=["Amarillo/Verde"]) or 0.3
        p_vuelta = p_fase

        p_mecanismo = precio_medio(df_trabajo, "Mecanismos", gama=gama_sel) or 3.0

        texto_caja = "Pladur" if "Pladur" in tipo_obra else "Universal"
        p_caja = precio_medio(df_trabajo, "Cajas de Registro", keywords=[texto_caja]) or 0.3

        precios_usados = {
            "Tubo corrugado " + diametro_tubo + " (€/m)": p_tubo,
            "Cable Fase/Vuelta " + seccion_cable + " (€/m)": p_fase,
            "Cable Neutro " + seccion_cable + " (€/m)": p_neutro,
            "Cable Tierra (€/m)": p_tierra,
            "Mecanismo " + gama_sel + " (€/ud)": p_mecanismo,
            "Caja de registro " + texto_caja + " (€/ud)": p_caja,
        }

        # --- Cálculo por estancia ---
        coste_total_materiales = 0.0
        horas_totales_obra = 0.0
        filas_internas = []
        filas_cliente = []

        for est in estancias_activas:
            m2 = est["m2"]
            m_tubo = m2 * 4.2
            m_fase = m2 * 5.0
            m_neutro = m2 * 5.0
            m_tierra = m2 * 5.0
            m_vuelta = m2 * 4.0
            mecanismos = max(3, int(m2 / 4))

            coste_mat_estancia = (
                m_tubo * p_tubo
                + m_fase * p_fase
                + m_neutro * p_neutro
                + m_tierra * p_tierra
                + m_vuelta * p_vuelta
                + mecanismos * p_mecanismo
                + mecanismos * p_caja
            )
            coste_total_materiales += coste_mat_estancia

            h_rozas = (m2 * h_rozas_m2) if "Empotrada" in tipo_obra else 0.0
            h_tubo = m2 * h_tubo_m2
            h_cableado = m2 * h_cableado_m2
            h_mecanizado = mecanismos * h_mecanizado_ud
            h_estancia = h_rozas + h_tubo + h_cableado + h_mecanizado
            horas_totales_obra += h_estancia
            coste_mo_estancia = h_estancia * precio_hora

            coste_real_estancia = coste_mat_estancia + coste_mo_estancia
            precio_venta_estancia = coste_real_estancia * (1 + margen_comercial / 100.0)

            filas_internas.append({
                "Estancia": est["nombre"], "m²": m2,
                "Tubo (m)": round(m_tubo, 1), "Cable Fase (m)": round(m_fase, 1),
                "Cable Neutro (m)": round(m_neutro, 1), "Cable Tierra (m)": round(m_tierra, 1),
                "Mecanismos (ud)": mecanismos,
                "Coste Materiales (€)": round(coste_mat_estancia, 2),
                "Horas MO": round(h_estancia, 2),
                "Coste MO (€)": round(coste_mo_estancia, 2),
                "TU COSTE REAL (€)": round(coste_real_estancia, 2),
            })
            filas_cliente.append({
                "Estancia": est["nombre"], "Superficie": f"{m2} m²",
                "Precio (€)": round(precio_venta_estancia, 2),
            })

        coste_mano_obra = horas_totales_obra * precio_hora
        coste_total_real = coste_total_materiales + coste_mano_obra

        # ==========================================
        # VISTA 1: INTERNA (PARA TI)
        # ==========================================
        st.header("🛠️ 1. Tu Coste Real (Vista Interna)")
        with st.expander("💶 Precios unitarios usados en este cálculo (de tu Excel)"):
            for k, v in precios_usados.items():
                st.write(f"- {k}: **{v:.3f} €**")

        df_interna = pd.DataFrame(filas_internas)
        st.dataframe(df_interna, use_container_width=True, hide_index=True)

        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Total Materiales", f"{coste_total_materiales:.2f} €")
        col_r2.metric("Total Horas MO", f"{horas_totales_obra:.1f} h ({num_operarios} op.)")
        col_r3.metric("Total Mano de Obra", f"{coste_mano_obra:.2f} €")
        st.error(f"🔴 **TU COSTE TOTAL DE EJECUCIÓN: {coste_total_real:.2f} €**")

        # ==========================================
        # VISTA 2: COMERCIAL (PARA EL CLIENTE)
        # ==========================================
        st.markdown("---")
        st.header("📄 2. Presupuesto para el Cliente (Vista Comercial)")
        st.caption("Menos detallado que la vista interna, con tus precios de venta.")

        st.markdown(f"""
        <div style="border: 2px solid #0284c7; padding: 20px; border-radius: 10px; background-color: #f0f9ff;">
            <h3 style="color: #0369a1; margin-top: 0;">{empresa_nombre}</h3>
            <p><b>Instalador Autorizado REBT ({n_licencia})</b> | {localidad} | Tel: {telefono}</p>
            <hr style="border: 1px solid #bae6fd;">
            <p><b>Presupuesto Nº:</b> {num_presupuesto} &nbsp;|&nbsp; <b>Fecha:</b> {date.today().strftime('%d/%m/%Y')}</p>
            <p><b>Cliente:</b> {cliente_nombre or '—'} {('· ' + cliente_direccion) if cliente_direccion else ''}</p>
            <p><b>Objeto:</b> Instalación Eléctrica Completa por Estancias ({sum(e['m2'] for e in estancias_activas):.1f} m²)</p>
            <p><b>Sistema:</b> {tipo_obra} | <b>Gama:</b> {gama_sel}</p>
        </div>
        """, unsafe_allow_html=True)

        df_cliente = pd.DataFrame(filas_cliente)
        st.dataframe(df_cliente, use_container_width=True, hide_index=True)

        subtotal_neto_comercial = sum(f["Precio (€)"] for f in filas_cliente)

        st.markdown("##### Capítulo Adicional: Cuadro General de Protección y Boletín")
        num_circuitos = st.number_input("Nº de circuitos estimado (para el cuadro)", min_value=3, max_value=20,
                                         value=max(6, len(estancias_activas) + 2), key="num_circuitos")
        p_iga = precio_medio(df_trabajo, "Protecciones", keywords=["Magnetotérmico", "2P", "40A"]) or 12.0
        p_dif = precio_medio(df_trabajo, "Protecciones", keywords=["Diferencial", "40A"]) or 15.0
        p_magneto = precio_medio(df_trabajo, "Protecciones", keywords=["Magnetotérmico", "1P"]) or 4.0
        p_caja_modular = precio_medio(df_trabajo, "Cuadros y Envolventes") or 25.0

        coste_real_cuadro = p_iga + 2 * p_dif + num_circuitos * p_magneto + p_caja_modular
        precio_venta_cuadro = coste_real_cuadro * (1 + margen_comercial / 100.0)
        subtotal_neto_comercial += precio_venta_cuadro

        st.markdown(f"""
        <div style="border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; background-color: #f8fafc;">
            <p>Cuadro de distribución, IGA, 2 diferenciales, {num_circuitos} magnetotérmicos y tramitación del boletín:
            <b>{precio_venta_cuadro:.2f} €</b></p>
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

        margen_real_obtenido = total_cliente - cuota_iva - coste_total_real
        st.caption(f"Margen bruto real sobre tu coste (sin IVA): {margen_real_obtenido:.2f} € "
                    f"({(margen_real_obtenido / coste_total_real * 100) if coste_total_real else 0:.1f}%)")

        st.markdown("---")
        st.markdown("##### 📝 Condiciones Generales")
        st.info("• Validez de la oferta: 30 días.\n"
                "• Forma de pago: 40% a la aceptación, 40% a mitad de ejecución, 20% a la entrega del Boletín (CIE).\n"
                "• Garantía: 2 años en instalación ejecutada según REBT.")

        st.success("✅ Presupuesto generado con éxito.")

        # ==========================================
        # GUARDAR Y EXPORTAR
        # ==========================================
        st.markdown("---")
        st.subheader("💾 Guardar y Exportar")

        col_g1, col_g2, col_g3 = st.columns(3)

        with col_g1:
            if st.button("💾 Guardar este presupuesto", type="secondary"):
                record = {
                    "id": num_presupuesto,
                    "fecha": date.today().strftime("%d/%m/%Y"),
                    "cliente": {"nombre": cliente_nombre, "direccion": cliente_direccion, "telefono": cliente_telefono},
                    "parametros": {
                        "tipo_obra": tipo_obra, "gama_sel": gama_sel, "diametro_tubo": diametro_tubo,
                        "seccion_cable": seccion_cable, "proveedor_pref": proveedor_pref,
                        "precio_hora": precio_hora, "num_operarios": num_operarios,
                        "h_rozas_m2": h_rozas_m2, "h_tubo_m2": h_tubo_m2,
                        "h_cableado_m2": h_cableado_m2, "h_mecanizado_ud": h_mecanizado_ud,
                        "margen_comercial": margen_comercial, "iva_sel": iva_sel,
                        "num_circuitos": num_circuitos,
                    },
                    "estancias": estancias_activas,
                    "resultados": {
                        "coste_total_materiales": round(coste_total_materiales, 2),
                        "coste_mano_obra": round(coste_mano_obra, 2),
                        "coste_total_real": round(coste_total_real, 2),
                        "subtotal_neto_comercial": round(subtotal_neto_comercial, 2),
                        "cuota_iva": round(cuota_iva, 2),
                        "total_cliente": round(total_cliente, 2),
                    },
                    "filas_cliente": filas_cliente,
                    "filas_internas": filas_internas,
                }
                guardar_presupuesto(record)
                st.session_state.num_presupuesto_cargado = None
                st.success(f"Presupuesto {num_presupuesto} guardado. Aparecerá en 'Presupuestos Guardados' en la barra lateral.")

        with col_g2:
            pdf_cliente_bytes = generar_pdf_cliente(
                datos_empresa={"nombre": empresa_nombre, "licencia": n_licencia, "localidad": localidad, "telefono": telefono},
                datos_cliente={"nombre": cliente_nombre or "—", "direccion": cliente_direccion, "telefono": cliente_telefono},
                num_presupuesto=num_presupuesto,
                fecha_str=date.today().strftime("%d/%m/%Y"),
                tipo_obra=tipo_obra, gama_sel=gama_sel,
                filas_cliente=filas_cliente, precio_venta_cuadro=precio_venta_cuadro,
                num_circuitos=num_circuitos,
                subtotal=subtotal_neto_comercial, cuota_iva=cuota_iva, iva_sel=iva_sel,
                total_cliente=total_cliente,
            )
            st.download_button(
                "📄 PDF para el Cliente",
                data=pdf_cliente_bytes,
                file_name=f"Presupuesto_{num_presupuesto}_{(cliente_nombre or 'cliente').replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

        with col_g3:
            pdf_interno_bytes = generar_pdf_interno(
                datos_empresa={"nombre": empresa_nombre},
                num_presupuesto=num_presupuesto,
                fecha_str=date.today().strftime("%d/%m/%Y"),
                cliente_nombre=cliente_nombre,
                precios_usados=precios_usados,
                filas_internas=filas_internas,
                coste_total_materiales=coste_total_materiales,
                horas_totales_obra=horas_totales_obra,
                num_operarios=num_operarios,
                coste_mano_obra=coste_mano_obra,
                coste_total_real=coste_total_real,
            )
            st.download_button(
                "📕 PDF Interno (para ti)",
                data=pdf_interno_bytes,
                file_name=f"Interno_{num_presupuesto}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        st.session_state.ultimo_calculo = True


if __name__ == "__main__":
    app()
