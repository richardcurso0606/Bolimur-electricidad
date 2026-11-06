"""
Módulo de Herramientas Comerciales, Balance Económico y Auditor de Ofertas para Instaladores.
Proporciona:
1. Balance Económico Transparente (Modo Empresa vs. Modo Autónomo).
2. Semáforo de Negociación y Suelo Mínimo de Seguridad.
3. Auditor de Contraofertas ("¿Pierdo dinero?") con recomendación y WhatsApp de respuesta.
4. Calculadora de Anticipo Seguro (sin financiar obra de tu bolsillo).
5. Lista de Compra / Acopio para Mostrador de Almacén (Obramat / Leroy).
6. Gestor Persistente de Presupuestos (Guardar, Recuperar, Editar fecha/datos y Duplicar).
7. Aviso de Material Faltante con guardado automático en Base de Datos.
"""

import os
import re
import json
import uuid
import datetime
import urllib.parse
from typing import Dict, Any, List, Optional
import pandas as pd
import streamlit as st

try:
    from modulos import db_manager
except ImportError:
    import db_manager

try:
    from modulos import pdf_comercial_cliente
except ImportError:
    import pdf_comercial_cliente


# =========================================================================
# 1. GESTIÓN DE MATERIALES PERSONALIZADOS EN BD
# =========================================================================

def guardar_material_personalizado(nombre: str, precio_coste: float, unidad: str = "ud", proveedor: str = "Obramat", categoria: str = "General") -> bool:
    """Guarda o actualiza un material y su precio de compra en la base de datos local SQLite."""
    try:
        conn = db_manager.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materiales_personalizados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                precio_coste REAL NOT NULL,
                unidad TEXT DEFAULT 'ud',
                proveedor TEXT DEFAULT 'Obramat',
                categoria TEXT DEFAULT 'General',
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO materiales_personalizados (nombre, precio_coste, unidad, proveedor, categoria, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(nombre) DO UPDATE SET 
                precio_coste = excluded.precio_coste,
                unidad = excluded.unidad,
                proveedor = excluded.proveedor,
                categoria = excluded.categoria,
                fecha_actualizacion = CURRENT_TIMESTAMP
        """, (nombre.strip(), float(precio_coste), unidad.strip(), proveedor.strip(), categoria.strip()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al guardar material personalizado: {e}")
        return False


def buscar_material_personalizado(nombre: str) -> Optional[Dict[str, Any]]:
    """Busca un material por coincidencia en la tabla de materiales personalizados."""
    try:
        conn = db_manager.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materiales_personalizados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                precio_coste REAL NOT NULL,
                unidad TEXT DEFAULT 'ud',
                proveedor TEXT DEFAULT 'Obramat',
                categoria TEXT DEFAULT 'General',
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        nom_clean = nombre.strip().lower()
        cursor.execute("SELECT id, nombre, precio_coste, unidad, proveedor, categoria FROM materiales_personalizados")
        filas = cursor.fetchall()
        conn.close()
        for f in filas:
            if f[1].lower() in nom_clean or nom_clean in f[1].lower():
                return {
                    "id": f[0],
                    "nombre": f[1],
                    "precio_coste": float(f[2]),
                    "unidad": f[3],
                    "proveedor": f[4],
                    "categoria": f[5]
                }
        return None
    except Exception as e:
        print(f"Error al buscar material personalizado: {e}")
        return None


@st.cache_data(show_spinner=False)
def cargar_base_datos_oficial_excel():
    """Carga y cachea en memoria la base de datos oficial de materiales de almacén (base_datos_precio_oficial.xlsx)."""
    rutas = [
        "base_datos_precio_oficial.xlsx",
        os.path.join(os.path.dirname(__file__), "..", "base_datos_precio_oficial.xlsx"),
        os.path.join(os.getcwd(), "base_datos_precio_oficial.xlsx")
    ]
    for r in rutas:
        if os.path.exists(r):
            try:
                import pandas as pd
                df = pd.read_excel(r)
                return df
            except Exception as e:
                print(f"Error cargando base_datos_precio_oficial.xlsx: {e}")
    return None


def vincular_materiales_con_bd(filas_materiales: list) -> list:
    """
    Cruza cada partida técnica con la base de datos oficial de almacén (base_datos_precio_oficial.xlsx)
    y los materiales personalizados de SQLite. Determina proveedor (Obramat, Leroy Merlin, etc.),
    código SKU, estado de registro y genera enlaces de búsqueda para partidas con tarifa web.
    """
    df_oficial = cargar_base_datos_oficial_excel()
    lista_vinculada = []

    for idx, m in enumerate(filas_materiales):
        item = dict(m)
        c_nom = item.get("mat") or item.get("concepto") or item.get("nombre") or f"Partida {idx+1}"
        c_cant = float(item.get("cant") or item.get("cantidad") or 1.0)
        c_unid = item.get("unid") or item.get("unidad") or "ud"
        c_pu_orig = float(item.get("p_u") or item.get("precio_ud") or item.get("precio") or 0.0)

        # 1. Comprobar en SQLite de materiales personalizados del instalador
        mat_sql = buscar_material_personalizado(c_nom)
        if mat_sql:
            item["en_bd"] = True
            item["proveedor"] = mat_sql.get("proveedor", "Obramat")
            item["sku"] = f"BD-SQL#{mat_sql['id']}"
            item["estado_bd"] = f"✅ Registrado en tu BD ({item['proveedor']})"
            item["p_u"] = mat_sql.get("precio_coste", c_pu_orig)
            item["subtotal"] = round(c_cant * float(item["p_u"]), 2)
            lista_vinculada.append(item)
            continue

        # 2. Comprobar en base de datos oficial Excel
        encontrado_excel = False
        if df_oficial is not None and not df_oficial.empty:
            nom_clean = c_nom.lower()
            palabras = [w for w in re.split(r'[\s,/\-\+]+', nom_clean) if len(w) > 2 and w not in ['para', 'con', 'del', 'los', 'las', 'por', 'libre', 'mm2', 'mm²']]

            mejor_fila = None
            max_score = 0
            for _, row in df_oficial.iterrows():
                desc = str(row.get('Descripción Exacta del Artículo', '')).lower() + ' ' + str(row.get('Observaciones / Aplicación Técnica', '')).lower()
                sc = sum(1 for p in palabras if p in desc)
                if sc > max_score and sc >= min(2, len(palabras)):
                    max_score = sc
                    mejor_fila = row

            if mejor_fila is not None:
                tienda = str(mejor_fila.get('Proveedor / Tienda', 'Obramat'))
                item["en_bd"] = True
                item["proveedor"] = tienda
                item["sku"] = str(mejor_fila.get('Código SKU / Ref', 'S/Ref'))
                item["estado_bd"] = f"✅ En BD Oficial ({tienda})"
                if c_pu_orig <= 0:
                    item["p_u"] = float(mejor_fila.get('Precio S/IVA (€)', 0.0))
                else:
                    item["p_u"] = c_pu_orig
                item["subtotal"] = round(c_cant * float(item["p_u"]), 2)
                item["articulo_oficial"] = str(mejor_fila.get('Descripción Exacta del Artículo', ''))
                encontrado_excel = True

        if not encontrado_excel:
            item["en_bd"] = False
            item["proveedor"] = "🌐 Tarifa Web / Almacén"
            item["sku"] = "S/Ref"
            item["estado_bd"] = "⚠️ No en BD (Tarifa Web Estimada)"
            item["p_u"] = c_pu_orig
            item["subtotal"] = round(c_cant * c_pu_orig, 2)
            item["url_google"] = f"https://www.google.com/search?q=comprar+material+electrico+{urllib.parse.quote_plus(c_nom)}"
            item["url_obramat"] = f"https://www.obramat.es/catalogsearch/result/?q={urllib.parse.quote_plus(c_nom)}"

        lista_vinculada.append(item)

    return lista_vinculada


# =========================================================================
# 2. AUDITOR DE CONTRAOFERTAS Y ESCUDO FINANCIERO ("¿PIERDO DINERO?")
# =========================================================================

def auditar_contraoferta(
    precio_ofertado: float,
    coste_materiales: float,
    coste_boletin: float = 0.0,
    horas_estimadas: float = 8.0,
    precio_hora_objetivo: float = 35.0,
    gastos_vehiculo: float = 0.0,
    iva_pct: float = 21.0,
    oferta_con_iva: bool = True
) -> Dict[str, Any]:
    """
    Audita la contraoferta recibida de un cliente.
    Determina si el instalador pierde dinero, trabaja a coste o si es una oferta rentable,
    indicando el suelo mínimo admisible y el texto formal de contraoferta.
    """
    horas_obra = max(float(horas_estimadas), 0.5)
    p_hora_obj = max(float(precio_hora_objetivo), 15.0)

    # Convertir oferta a Base Imponible (sin IVA) para comparar costes netos
    if oferta_con_iva and iva_pct > 0:
        base_ofertada = round(precio_ofertado / (1.0 + iva_pct / 100.0), 2)
    else:
        base_ofertada = round(float(precio_ofertado), 2)

    costes_duros = round(coste_materiales + coste_boletin + gastos_vehiculo, 2)
    dinero_para_horas = round(base_ofertada - costes_duros, 2)
    precio_hora_real = round(dinero_para_horas / horas_obra, 2)

    # Suelo mínimo de seguridad (Costes fijos + 20 €/h sueldo mínimo de supervivencia)
    suelo_minimo_seguridad_base = round(costes_duros + (20.0 * horas_obra), 2)
    suelo_minimo_seguridad_civa = round(suelo_minimo_seguridad_base * (1.0 + iva_pct / 100.0), 2)

    # Precio Autónomo Competitivo Recomendado (Materiales + Margen 20% + Horas a precio objetivo)
    precio_autonomo_base = round((coste_materiales * 1.20) + coste_boletin + gastos_vehiculo + (p_hora_obj * horas_obra), 2)
    precio_autonomo_civa = round(precio_autonomo_base * (1.0 + iva_pct / 100.0), 2)

    # Precio Empresa (con recargo comercial general del 40% en mano de obra)
    precio_empresa_base = round((coste_materiales * 1.25) + coste_boletin + gastos_vehiculo + (p_hora_obj * horas_obra * 1.40), 2)
    precio_empresa_civa = round(precio_empresa_base * (1.0 + iva_pct / 100.0), 2)

    beneficio_neto_real = round(dinero_para_horas, 2)
    perdida_respecto_objetivo = round((p_hora_obj * horas_obra) - dinero_para_horas, 2)

    # Diagnóstico del semáforo
    if dinero_para_horas <= 0:
        estado = "PELIGRO_PERDIDA_TOTAL"
        color_badge = "#dc2626" # Rojo oscuro
        alerta_titulo = "🚨 ¡PELIGRO CRÍTICO: PIERDES DINERO DIRECTAMENTE!"
        alerta_detalle = (
            f"Con esta oferta de {precio_ofertado:,.2f} € ({base_ofertada:,.2f} € sin IVA), "
            f"**ni siquiera cubres los materiales de compra y tasas ({costes_duros:,.2f} €)**. "
            f"Tendrías que poner de tu propio bolsillo {-dinero_para_horas:,.2f} € y además trabajar {horas_obra:.1f} horas gratis. "
            f"¡RECHAZA O RECTIFICA INMEDIATAMENTE!"
        )
    elif precio_hora_real < 18.0:
        estado = "PELIGRO_SUELDO_MISERIA"
        color_badge = "#ef4444" # Rojo
        alerta_titulo = "🚨 ¡ALERTA: TRABAJAS A PÉRDIDA DE TU JORNAL!"
        alerta_detalle = (
            f"Tras pagar materiales ({costes_duros:,.2f} €), solo te sobran {dinero_para_horas:,.2f} € para {horas_obra:.1f} horas. "
            f"Estarías cobrando tu hora de trabajo a **{precio_hora_real:,.2f} €/h** (muy por debajo de tu tarifa objetivo de {p_hora_obj:.0f} €/h). "
            f"Estás perdiendo {perdida_respecto_objetivo:,.2f} € de tu sueldo profesional."
        )
    elif precio_hora_real < p_hora_obj:
        estado = "RIESGO_COSTE"
        color_badge = "#f59e0b" # Ámbar
        alerta_titulo = "🟡 ZONA DE RIESGO: TRABAJAS POR LO JUSTO (SIN MARGEN)"
        alerta_detalle = (
            f"La oferta cubre materiales y te deja un jornal de **{precio_hora_real:,.2f} €/h** (algo inferior a tus {p_hora_obj:.0f} €/h deseados). "
            f"Te deja {dinero_para_horas:,.2f} € limpios, pero con **cero colchón para averías, rotura de brocas o imprevistos**. "
            f"Aceptable solo si no tienes otra obra mejor en agenda."
        )
    else:
        estado = "RENTABLE"
        color_badge = "#16a34a" # Verde
        alerta_titulo = "🟢 OFERTA RENTABLE Y CON RENDIMIENTO DIGNO"
        alerta_detalle = (
            f"La oferta cubre al 100% los materiales de almacén, asegura tu jornal íntegro a **{precio_hora_real:,.2f} €/h** "
            f"y te deja un beneficio neto de **{beneficio_neto_real:,.2f} €**. "
            f"¡Adelante, puedes aceptar con total seguridad y pedir el anticipo de materiales!"
        )

    # Texto de contraoferta educado y formal para WhatsApp
    txt_whatsapp_contra = (
        f"Hola. He revisado con detalle la propuesta económica de {precio_ofertado:,.2f} €.\n\n"
        f"Por normativa técnica REBT y seguridad, la instalación requiere canalizaciones normalizadas, "
        f"conductores ignífugos libres de halógenos y protecciones oficiales que suman un coste directo de {costes_duros:,.2f} € en almacén.\n\n"
        f"Para garantizar un montaje certificado con garantía oficial y tramitación de boletín, "
        f"el importe mínimo ajustado al que puedo realizar el trabajo con la máxima calidad es de "
        f"*{suelo_minimo_seguridad_civa:,.2f} € (IVA incl.)* [Base: {suelo_minimo_seguridad_base:,.2f} €].\n\n"
        f"Si te parece bien con este ajuste, te reservo fecha esta semana para iniciarlo. Un saludo."
    )

    return {
        "estado": estado,
        "color_badge": color_badge,
        "alerta_titulo": alerta_titulo,
        "alerta_detalle": alerta_detalle,
        "base_ofertada": base_ofertada,
        "precio_ofertado_civa": precio_ofertado if oferta_con_iva else round(base_ofertada * (1.0 + iva_pct / 100.0), 2),
        "costes_duros": costes_duros,
        "dinero_para_horas": dinero_para_horas,
        "precio_hora_real": precio_hora_real,
        "suelo_minimo_base": suelo_minimo_seguridad_base,
        "suelo_minimo_civa": suelo_minimo_seguridad_civa,
        "precio_autonomo_base": precio_autonomo_base,
        "precio_autonomo_civa": precio_autonomo_civa,
        "precio_empresa_base": precio_empresa_base,
        "precio_empresa_civa": precio_empresa_civa,
        "beneficio_neto_real": beneficio_neto_real,
        "texto_contraoferta_whatsapp": txt_whatsapp_contra
    }


# =========================================================================
# 3. GESTOR DE PRESUPUESTOS GUARDADOS EN BD (SQLITE)
# =========================================================================

def guardar_presupuesto(
    usuario_id: Optional[int],
    cliente_id: Optional[int],
    nombre_cliente: str,
    nombre_presupuesto: str,
    modulo_origen: str,
    datos_presupuesto: Dict[str, Any],
    estado: str = "Pendiente",
    total_sin_iva: float = 0.0,
    total_con_iva: float = 0.0,
    iva_pct: float = 21.0,
    modo_tarifa: str = "Autónomo",
    validez_dias: int = 30,
    fecha_presupuesto: Optional[str] = None
) -> tuple[bool, int]:
    """Guarda un presupuesto completo con sus partidas, parámetros y estado en SQLite."""
    try:
        conn = db_manager.obtener_conexion()
        cursor = conn.cursor()
        f_pres = fecha_presupuesto or datetime.date.today().strftime("%d/%m/%Y")
        datos_str = json.dumps(datos_presupuesto, ensure_ascii=False)

        cursor.execute("""
            INSERT INTO presupuestos_guardados (
                usuario_id, cliente_id, nombre_cliente, nombre_presupuesto, modulo_origen,
                estado, total_sin_iva, total_con_iva, iva_pct, modo_tarifa, datos_json,
                validez_dias, fecha_presupuesto, fecha_actualizacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            usuario_id, cliente_id, nombre_cliente.strip(), nombre_presupuesto.strip(), modulo_origen.strip(),
            estado.strip(), float(total_sin_iva), float(total_con_iva), float(iva_pct), modo_tarifa.strip(),
            datos_str, int(validez_dias), f_pres
        ))
        pres_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return True, pres_id
    except Exception as e:
        print(f"Error al guardar presupuesto: {e}")
        return False, 0


def listar_presupuestos(modulo_origen: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista todos los presupuestos guardados ordenados por fecha descendente."""
    try:
        conn = db_manager.obtener_conexion()
        cursor = conn.cursor()
        if modulo_origen:
            cursor.execute("""
                SELECT id, nombre_presupuesto, nombre_cliente, modulo_origen, estado,
                       total_sin_iva, total_con_iva, modo_tarifa, fecha_presupuesto, validez_dias, fecha_creacion
                FROM presupuestos_guardados
                WHERE modulo_origen = ?
                ORDER BY id DESC
            """, (modulo_origen.strip(),))
        else:
            cursor.execute("""
                SELECT id, nombre_presupuesto, nombre_cliente, modulo_origen, estado,
                       total_sin_iva, total_con_iva, modo_tarifa, fecha_presupuesto, validez_dias, fecha_creacion
                FROM presupuestos_guardados
                ORDER BY id DESC
            """)
        filas = cursor.fetchall()
        conn.close()

        lista = []
        for r in filas:
            lista.append({
                "id": r[0],
                "nombre_presupuesto": r[1],
                "nombre_cliente": r[2] or "Cliente General",
                "modulo_origen": r[3],
                "estado": r[4] or "Pendiente",
                "total_sin_iva": float(r[5] or 0.0),
                "total_con_iva": float(r[6] or 0.0),
                "modo_tarifa": r[7] or "Autónomo",
                "fecha_presupuesto": r[8] or "",
                "validez_dias": int(r[9] or 30),
                "fecha_creacion": str(r[10])[:16]
            })
        return lista
    except Exception as e:
        print(f"Error al listar presupuestos: {e}")
        return []


def cargar_presupuesto_por_id(presupuesto_id: int) -> Optional[Dict[str, Any]]:
    """Recupera un presupuesto completo con todos sus datos y partidas desde SQLite."""
    try:
        conn = db_manager.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, usuario_id, cliente_id, nombre_cliente, nombre_presupuesto, modulo_origen,
                   estado, total_sin_iva, total_con_iva, iva_pct, modo_tarifa, datos_json,
                   validez_dias, fecha_presupuesto, fecha_creacion, fecha_actualizacion
            FROM presupuestos_guardados
            WHERE id = ?
        """, (presupuesto_id,))
        r = cursor.fetchone()
        conn.close()

        if not r:
            return None

        datos_obj = json.loads(r[11]) if r[11] else {}
        return {
            "id": r[0],
            "usuario_id": r[1],
            "cliente_id": r[2],
            "nombre_cliente": r[3] or "Cliente General",
            "nombre_presupuesto": r[4],
            "modulo_origen": r[5],
            "estado": r[6] or "Pendiente",
            "total_sin_iva": float(r[7] or 0.0),
            "total_con_iva": float(r[8] or 0.0),
            "iva_pct": float(r[9] or 21.0),
            "modo_tarifa": r[10] or "Autónomo",
            "datos": datos_obj,
            "validez_dias": int(r[12] or 30),
            "fecha_presupuesto": r[13] or "",
            "fecha_creacion": str(r[14]),
            "fecha_actualizacion": str(r[15])
        }
    except Exception as e:
        print(f"Error al cargar presupuesto {presupuesto_id}: {e}")
        return None


def actualizar_presupuesto(presupuesto_id: int, datos_nuevos: Dict[str, Any]) -> bool:
    """Actualiza datos editables de un presupuesto existente (fecha, estado, totales, cliente)."""
    try:
        conn = db_manager.obtener_conexion()
        cursor = conn.cursor()

        campos_update = []
        valores = []

        if "nombre_presupuesto" in datos_nuevos:
            campos_update.append("nombre_presupuesto = ?")
            valores.append(datos_nuevos["nombre_presupuesto"])
        if "nombre_cliente" in datos_nuevos:
            campos_update.append("nombre_cliente = ?")
            valores.append(datos_nuevos["nombre_cliente"])
        if "estado" in datos_nuevos:
            campos_update.append("estado = ?")
            valores.append(datos_nuevos["estado"])
        if "fecha_presupuesto" in datos_nuevos:
            campos_update.append("fecha_presupuesto = ?")
            valores.append(datos_nuevos["fecha_presupuesto"])
        if "validez_dias" in datos_nuevos:
            campos_update.append("validez_dias = ?")
            valores.append(int(datos_nuevos["validez_dias"]))
        if "total_sin_iva" in datos_nuevos:
            campos_update.append("total_sin_iva = ?")
            valores.append(float(datos_nuevos["total_sin_iva"]))
        if "total_con_iva" in datos_nuevos:
            campos_update.append("total_con_iva = ?")
            valores.append(float(datos_nuevos["total_con_iva"]))
        if "modo_tarifa" in datos_nuevos:
            campos_update.append("modo_tarifa = ?")
            valores.append(datos_nuevos["modo_tarifa"])
        if "datos" in datos_nuevos:
            campos_update.append("datos_json = ?")
            valores.append(json.dumps(datos_nuevos["datos"], ensure_ascii=False))

        campos_update.append("fecha_actualizacion = CURRENT_TIMESTAMP")
        valores.append(presupuesto_id)

        sql = f"UPDATE presupuestos_guardados SET {', '.join(campos_update)} WHERE id = ?"
        cursor.execute(sql, tuple(valores))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al actualizar presupuesto {presupuesto_id}: {e}")
        return False


def duplicar_presupuesto(presupuesto_id: int, nuevo_nombre: str, nuevo_cliente: str = "") -> tuple[bool, int]:
    """Duplica un presupuesto existente para otro cliente o trabajo similar en 1 clic."""
    p_orig = cargar_presupuesto_por_id(presupuesto_id)
    if not p_orig:
        return False, 0

    cli_nom = nuevo_cliente.strip() if nuevo_cliente else f"{p_orig['nombre_cliente']} (Copia)"
    return guardar_presupuesto(
        usuario_id=p_orig.get("usuario_id"),
        cliente_id=p_orig.get("cliente_id"),
        nombre_cliente=cli_nom,
        nombre_presupuesto=nuevo_nombre.strip(),
        modulo_origen=p_orig.get("modulo_origen", "General"),
        datos_presupuesto=p_orig.get("datos", {}),
        estado="Pendiente",
        total_sin_iva=p_orig.get("total_sin_iva", 0.0),
        total_con_iva=p_orig.get("total_con_iva", 0.0),
        iva_pct=p_orig.get("iva_pct", 21.0),
        modo_tarifa=p_orig.get("modo_tarifa", "Autónomo"),
        validez_dias=p_orig.get("validez_dias", 30),
        fecha_presupuesto=datetime.date.today().strftime("%d/%m/%Y")
    )


def eliminar_presupuesto(presupuesto_id: int) -> bool:
    """Elimina un presupuesto de la base de datos."""
    try:
        conn = db_manager.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM presupuestos_guardados WHERE id = ?", (presupuesto_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al eliminar presupuesto: {e}")
        return False


# =========================================================================
# 4. COMPONENTE VISUAL REUTILIZABLE PARA TODOS LOS MÓDULOS DE BOLIMUR
# =========================================================================

def render_panel_herramientas_presupuesto(
    datos_presupuesto: Dict[str, Any],
    modulo_nombre: str,
    key_prefix: str = "hp"
):
    """
    Renderiza el panel comercial integral:
    - Ajustes en tiempo real de márgenes (%) y precio/hora (€/h)
    - Balance Económico (Modo Empresa vs Modo Autónomo)
    - Semáforo de Negociación y Calculadora de Anticipo
    - Auditor de Contraofertas ("¿Pierdo dinero?")
    - Lista de Compra de Almacén para Mostrador
    - Guardar, Recuperar, Editar y Duplicar Presupuesto
    """
    # Extracción de parámetros con valores por defecto seguros
    coste_mat_orig = float(datos_presupuesto.get("coste_materiales", 0.0))
    margen_mat_def = float(datos_presupuesto.get("margen_materiales_pct", 25.0))
    horas_mo_def = float(datos_presupuesto.get("horas_mano_obra", 8.0))
    precio_h_coste_def = float(datos_presupuesto.get("precio_hora_coste", 28.0))
    recargo_emp_def = float(datos_presupuesto.get("recargo_empresa_mo_pct", 35.0))
    coste_tramitacion = float(datos_presupuesto.get("coste_tramitacion", 120.0))
    desplazamiento = float(datos_presupuesto.get("desplazamiento", 0.0))
    iva_pct = float(datos_presupuesto.get("iva_pct", 21.0))
    filas_materiales = datos_presupuesto.get("filas_materiales", [])
    nom_cliente_def = datos_presupuesto.get("cliente", "Cliente Particular")
    nom_obra_def = datos_presupuesto.get("concepto", f"Presupuesto de {modulo_nombre}")
    obra_longitud = float(datos_presupuesto.get("longitud", 0.0))
    obra_seccion = float(datos_presupuesto.get("seccion", 0.0))
    obra_trifasico = bool(datos_presupuesto.get("es_trifasico", False))

    # Contenedor visual del panel comercial
    st.markdown("---")
    st.markdown(f"### 💼 Gestión Comercial, Balance y Auditor Financiero ({modulo_nombre})")
    st.caption("Herramienta de control financiero para el instalador de calle: ajusta tus márgenes, compara tarifas Empresa vs. Autónomo y audita ofertas del cliente.")

    # ---------------------------------------------------------------------
    # 1. LISTA DE MATERIALES EDITABLE Y REORDENABLE (ADELANTE, EN MEDIO O AL FINAL)
    # ---------------------------------------------------------------------
    key_lista_mat = f"{key_prefix}_lista_materiales_maestra"
    key_mat_hash = f"{key_prefix}_mat_hash_check"
    curr_mat_hash = f"{modulo_nombre}_{coste_mat_orig}_{len(filas_materiales)}"

    if key_lista_mat not in st.session_state or st.session_state.get(key_mat_hash) != curr_mat_hash:
        lista_vinculada = vincular_materiales_con_bd(filas_materiales) if filas_materiales else []
        init_mats = []
        if lista_vinculada:
            for idx, m in enumerate(lista_vinculada, start=1):
                init_mats.append({
                    "orden": idx,
                    "incluir": True,
                    "material": str(m.get("mat") or m.get("concepto") or f"Material {idx}"),
                    "cant": float(m.get("cant", 1.0)),
                    "unid": str(m.get("unid", "ud")),
                    "precio_unit": float(m.get("p_u", 0.0)),
                    "proveedor": str(m.get("proveedor", "Obramat")),
                    "sku": str(m.get("sku", "S/Ref")),
                    "en_bd": ("Tarifa Web" not in str(m.get("proveedor", "")) and "Pendiente" not in str(m.get("proveedor", "")))
                })
        else:
            init_mats.append({
                "orden": 1,
                "incluir": True,
                "material": f"Materiales normalizados de {modulo_nombre}",
                "cant": 1.0,
                "unid": "partida",
                "precio_unit": coste_mat_orig,
                "proveedor": "Obramat / Almacén",
                "sku": "GEN-01",
                "en_bd": True
            })
        st.session_state[key_lista_mat] = init_mats
        st.session_state[key_mat_hash] = curr_mat_hash
        if f"{key_prefix}_editor_materiales_interactivo" in st.session_state:
            del st.session_state[f"{key_prefix}_editor_materiales_interactivo"]

    with st.expander("📦 1. Lista de Materiales de la Instalación (Modificar Precios, Cantidades, Reordenar y Añadir Nuevos)", expanded=True):
        st.markdown(
            "<div style='font-size:13.5px; color:#1e293b; margin-bottom:8px;'>"
            "<b>💡 ¿El cliente ya tiene algún material o la obra ya está canalizada?</b> Desmarca la casilla <b>'Comprar'</b> o ajusta sus metros/precio. "
            "Puedes <b>colocar cualquier material nuevo adelante, en medio o al final</b>, o reordenar la lista a tu gusto con los botones o editando la columna <b>Nº Orden</b>.</div>",
            unsafe_allow_html=True
        )

        df_mat_init = pd.DataFrame(st.session_state[key_lista_mat])
        if "orden" not in df_mat_init.columns:
            df_mat_init.insert(0, "orden", range(1, len(df_mat_init) + 1))

        df_mat_editado = st.data_editor(
            df_mat_init,
            key=f"{key_prefix}_editor_materiales_interactivo",
            column_config={
                "orden": st.column_config.NumberColumn(
                    "Nº Orden",
                    min_value=1,
                    step=1,
                    format="%d",
                    help="Cambia el número de orden para colocar el material arriba, en medio o abajo.",
                    width="small"
                ),
                "incluir": st.column_config.CheckboxColumn(
                    "Comprar [X]",
                    help="Marca con una X para comprar en almacén. Desmarca la X si el cliente ya lo tiene o ya está canalizado para que NO se cobre (0,00 €).",
                    default=True
                ),
                "material": st.column_config.TextColumn("Denominación del Material / Especificación Técnica", width="large", required=True),
                "cant": st.column_config.NumberColumn("Cantidad", min_value=0.0, step=0.5, format="%.1f"),
                "unid": st.column_config.TextColumn("Unidad", width="small"),
                "precio_unit": st.column_config.NumberColumn("P. Unit Coste (€)", min_value=0.0, step=0.1, format="%.2f €"),
                "proveedor": st.column_config.TextColumn("Dónde Comprar (Tienda)", width="medium"),
                "sku": st.column_config.TextColumn("Ref. SKU", width="small")
            },
            use_container_width=True,
            num_rows="dynamic"
        )

        # Si el usuario modificó datos o el orden en la tabla
        if "orden" in df_mat_editado.columns:
            df_mat_editado = df_mat_editado.sort_values(by="orden").reset_index(drop=True)

        filas_mat_activas = []
        filas_mat_en_obra = []
        coste_mat_calculado = 0.0
        coste_mat_en_obra = 0.0
        lista_actualizada = []

        for idx_row, r in df_mat_editado.iterrows():
            c_nom = str(r["material"]) if pd.notnull(r["material"]) else ""
            if not c_nom.strip():
                continue
            c_cant = float(r["cant"]) if pd.notnull(r["cant"]) else 0.0
            c_unid = str(r["unid"]) if pd.notnull(r["unid"]) else "ud"
            c_pu = float(r["precio_unit"]) if pd.notnull(r["precio_unit"]) else 0.0
            c_sub = round(c_cant * c_pu, 2)
            c_prov = str(r["proveedor"]) if pd.notnull(r["proveedor"]) else "Obramat"
            c_sku = str(r["sku"]) if pd.notnull(r["sku"]) else "S/Ref"
            c_inc = bool(r["incluir"]) if pd.notnull(r["incluir"]) else True
            c_ord = idx_row + 1

            item_dict = {
                "orden": c_ord,
                "mat": c_nom,
                "material": c_nom,
                "cant": c_cant,
                "unid": c_unid,
                "p_u": c_pu,
                "precio_unit": c_pu,
                "subtotal": c_sub,
                "proveedor": c_prov,
                "sku": c_sku,
                "incluir": c_inc,
                "en_bd": ("Tarifa Web" not in c_prov and "Pendiente" not in c_prov),
                "url_obramat": f"https://www.obramat.es/catalogsearch/result/?q={urllib.parse.quote_plus(c_nom)}",
                "url_google": f"https://www.google.com/search?q={urllib.parse.quote_plus('comprar ' + c_nom)}"
            }
            lista_actualizada.append(item_dict)

            if c_inc and c_cant > 0:
                coste_mat_calculado += c_sub
                filas_mat_activas.append(item_dict)
            else:
                coste_mat_en_obra += c_sub
                item_dict["motivo"] = "Aportado por cliente / Ya instalado en obra"
                filas_mat_en_obra.append(item_dict)

        st.session_state[key_lista_mat] = lista_actualizada
        coste_mat = round(coste_mat_calculado, 2)

        col_mres1, col_mres2, col_mres3, col_mres4 = st.columns([1.5, 1.3, 1.1, 1.1])
        with col_mres1:
            st.success(f"🛒 **Materiales a Comprar:** {coste_mat:,.2f} € ({len(filas_mat_activas)} partidas)")
        with col_mres2:
            if filas_mat_en_obra:
                st.info(f"🏠 **En Obra / Canalizado (0 €):** {coste_mat_en_obra:,.2f} € ({len(filas_mat_en_obra)} partidas)")
            else:
                st.caption("ℹ️ Todos los materiales seleccionados para compra.")
        with col_mres3:
            with st.popover("➕ Añadir Material"):
                st.markdown("##### 📝 Añadir Material a la Lista")
                st.caption("Introduce un nuevo material e indica en qué posición colocarlo:")
                with st.form(f"{key_prefix}_form_add_extra_mat", clear_on_submit=True):
                    in_mat_nom = st.text_input("Denominación / Especificación:", placeholder="Ej: Piqueta de tierra cobreada 2m con grapa")
                    c_em1, c_em2 = st.columns(2)
                    with c_em1:
                        in_mat_cant = st.number_input("Cantidad:", min_value=0.1, value=1.0, step=0.5)
                        in_mat_pu = st.number_input("Precio Coste Unitario (€):", min_value=0.0, value=15.0, step=1.0)
                    with c_em2:
                        in_mat_unid = st.selectbox("Unidad:", ["ud", "m", "rollo", "partida", "kit", "caja"], index=0)
                        in_mat_prov = st.text_input("Dónde Comprar:", value="Obramat / Distribuidor")
                    in_mat_sku = st.text_input("Ref. SKU (opcional):", placeholder="Ej: REF-00123")

                    n_items_actual = len(st.session_state[key_lista_mat])
                    sel_pos_tipo = st.selectbox(
                        "📍 ¿Dónde deseas colocar este material en la lista?",
                        [
                            "🔚 Al final de la lista (abajo del todo)",
                            "🔝 Al principio de la lista (arriba del todo)",
                            "🎯 En una posición específica (en medio)"
                        ],
                        index=0
                    )
                    pos_especifica = 1
                    if "específica" in sel_pos_tipo:
                        pos_especifica = st.number_input("Nº de posición donde insertarlo:", min_value=1, max_value=n_items_actual + 1, value=min(2, n_items_actual + 1), step=1)

                    in_mat_save_bd = st.checkbox("💾 Guardar también en mi Base de Datos para futuros presupuestos", value=True)
                    btn_add_mat = st.form_submit_button("➕ Añadir Material a la Lista", type="primary", use_container_width=True)
                    if btn_add_mat:
                        if in_mat_nom.strip():
                            nuevo_item = {
                                "orden": 1,
                                "incluir": True,
                                "material": in_mat_nom.strip(),
                                "mat": in_mat_nom.strip(),
                                "cant": float(in_mat_cant),
                                "unid": str(in_mat_unid),
                                "precio_unit": float(in_mat_pu),
                                "p_u": float(in_mat_pu),
                                "subtotal": round(float(in_mat_cant) * float(in_mat_pu), 2),
                                "proveedor": in_mat_prov.strip() if in_mat_prov.strip() else "Obramat",
                                "sku": in_mat_sku.strip() if in_mat_sku.strip() else "MANUAL",
                                "en_bd": True,
                                "url_obramat": f"https://www.obramat.es/catalogsearch/result/?q={urllib.parse.quote_plus(in_mat_nom.strip())}",
                                "url_google": f"https://www.google.com/search?q={urllib.parse.quote_plus('comprar ' + in_mat_nom.strip())}"
                            }
                            if "principio" in sel_pos_tipo:
                                st.session_state[key_lista_mat].insert(0, nuevo_item)
                            elif "específica" in sel_pos_tipo:
                                idx_ins = max(0, min(len(st.session_state[key_lista_mat]), int(pos_especifica) - 1))
                                st.session_state[key_lista_mat].insert(idx_ins, nuevo_item)
                            else:
                                st.session_state[key_lista_mat].append(nuevo_item)

                            for i, it in enumerate(st.session_state[key_lista_mat], start=1):
                                it["orden"] = i

                            if in_mat_save_bd:
                                try:
                                    guardar_material_personalizado(
                                        nombre=in_mat_nom.strip(),
                                        precio_coste=float(in_mat_pu),
                                        unidad=str(in_mat_unid),
                                        categoria="Personalizado",
                                        proveedor=in_mat_prov.strip() if in_mat_prov.strip() else "Obramat",
                                        sku=nuevo_item["sku"]
                                    )
                                except Exception:
                                    pass
                            if f"{key_prefix}_editor_materiales_interactivo" in st.session_state:
                                del st.session_state[f"{key_prefix}_editor_materiales_interactivo"]
                            st.rerun()

        with col_mres4:
            with st.popover("↕️ Reordenar"):
                st.markdown("##### ↕️ Cambiar Posición de Materiales")
                st.caption("Selecciona un material y muévelo arriba, abajo, al principio o al final:")
                mats_noms = [f"{m.get('orden', i+1)}. {m.get('material', 'Material')[:35]}" for i, m in enumerate(st.session_state[key_lista_mat])]
                if mats_noms:
                    idx_sel_reord = st.selectbox("Material a desplazar:", range(len(mats_noms)), format_func=lambda x: mats_noms[x], key=f"{key_prefix}_sel_reord_mat")
                    c_b_top, c_b_up, c_b_dn, c_b_end = st.columns(4)
                    with c_b_top:
                        if st.button("🔝 Inicio", key=f"{key_prefix}_btn_top_m", disabled=(idx_sel_reord == 0)):
                            item = st.session_state[key_lista_mat].pop(idx_sel_reord)
                            st.session_state[key_lista_mat].insert(0, item)
                            for i, it in enumerate(st.session_state[key_lista_mat], start=1): it["orden"] = i
                            if f"{key_prefix}_editor_materiales_interactivo" in st.session_state:
                                del st.session_state[f"{key_prefix}_editor_materiales_interactivo"]
                            st.rerun()
                    with c_b_up:
                        if st.button("⬆️ Subir", key=f"{key_prefix}_btn_up_m", disabled=(idx_sel_reord == 0)):
                            st.session_state[key_lista_mat][idx_sel_reord], st.session_state[key_lista_mat][idx_sel_reord - 1] = st.session_state[key_lista_mat][idx_sel_reord - 1], st.session_state[key_lista_mat][idx_sel_reord]
                            for i, it in enumerate(st.session_state[key_lista_mat], start=1): it["orden"] = i
                            if f"{key_prefix}_editor_materiales_interactivo" in st.session_state:
                                del st.session_state[f"{key_prefix}_editor_materiales_interactivo"]
                            st.rerun()
                    with c_b_dn:
                        if st.button("⬇️ Bajar", key=f"{key_prefix}_btn_dn_m", disabled=(idx_sel_reord >= len(st.session_state[key_lista_mat]) - 1)):
                            st.session_state[key_lista_mat][idx_sel_reord], st.session_state[key_lista_mat][idx_sel_reord + 1] = st.session_state[key_lista_mat][idx_sel_reord + 1], st.session_state[key_lista_mat][idx_sel_reord]
                            for i, it in enumerate(st.session_state[key_lista_mat], start=1): it["orden"] = i
                            if f"{key_prefix}_editor_materiales_interactivo" in st.session_state:
                                del st.session_state[f"{key_prefix}_editor_materiales_interactivo"]
                            st.rerun()
                    with c_b_end:
                        if st.button("🔚 Final", key=f"{key_prefix}_btn_end_m", disabled=(idx_sel_reord >= len(st.session_state[key_lista_mat]) - 1)):
                            item = st.session_state[key_lista_mat].pop(idx_sel_reord)
                            st.session_state[key_lista_mat].append(item)
                            for i, it in enumerate(st.session_state[key_lista_mat], start=1): it["orden"] = i
                            if f"{key_prefix}_editor_materiales_interactivo" in st.session_state:
                                del st.session_state[f"{key_prefix}_editor_materiales_interactivo"]
                            st.rerun()

    # ---------------------------------------------------------------------
    # 2. MODIFICAR PARTIDAS COMERCIALES (DESPLAZAMIENTO, SIEM Y MANO DE OBRA)
    # ---------------------------------------------------------------------
    with st.expander("⚙️ 2. Modificar Partidas Comerciales: Desplazamiento, SIEM / Boletín y Mano de Obra", expanded=True):
        st.markdown("<div style='font-size:13.5px; color:#475569; margin-bottom:10px;'>Ajusta las partidas de desplazamiento, tramitación de boletín y tus tarifas. Al aumentar el desplazamiento o el SIEM, el importe se actualiza directamente en ambos modos (Empresa y Autónomo):</div>", unsafe_allow_html=True)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            inc_desp = st.checkbox(
                "🚗 [X] Incluir Desplazamiento y Portes (Desmarca la X para que NO salga en el presupuesto)",
                value=(desplazamiento > 0),
                key=f"{key_prefix}_chk_desp",
                help="Desmarca esta casilla con la X para que no figure desplazamiento ni se cobre al cliente."
            )
            if inc_desp:
                val_desp_input = st.number_input(
                    "🚗 Importe Desplazamiento (€) [Aumenta en ambos: Empresa y Autónomo]:",
                    min_value=0.0,
                    max_value=3000.0,
                    value=float(desplazamiento) if desplazamiento > 0 else 30.0,
                    step=5.0,
                    key=f"{key_prefix}_num_desp_base",
                    help="Al modificar este importe se incrementa directamente en la columna de Empresa y en la de Autónomo."
                )
                val_desp_base = float(val_desp_input) if val_desp_input is not None else 0.0
                dif_desp = st.checkbox("Diferenciar tarifa de desplazamiento para Empresa", value=False, key=f"{key_prefix}_chk_dif_desp")
                if dif_desp:
                    col_dd1, col_dd2 = st.columns(2)
                    with col_dd1:
                        desp_emp_in = st.number_input("🏢 Desplazamiento Empresa (€):", min_value=0.0, value=float(val_desp_base * 1.3), step=5.0, key=f"{key_prefix}_num_desp_emp")
                        desplazamiento_emp = float(desp_emp_in) if desp_emp_in is not None else val_desp_base
                    with col_dd2:
                        desp_auto_in = st.number_input("🧑‍🔧 Desplazamiento Autónomo (€):", min_value=0.0, value=float(val_desp_base), step=5.0, key=f"{key_prefix}_num_desp_auto")
                        desplazamiento_auto = float(desp_auto_in) if desp_auto_in is not None else val_desp_base
                else:
                    desplazamiento_emp = float(val_desp_base)
                    desplazamiento_auto = float(val_desp_base)
            else:
                desplazamiento_emp = 0.0
                desplazamiento_auto = 0.0
                st.caption("ℹ️ *Partida de desplazamiento DESMARCADA (0,00 € - NO saldrá en el presupuesto ni en el PDF).*")

        with col_d2:
            inc_cie = st.checkbox(
                "📋 [X] Incluir Tramitación CIE / Boletín / SIEM (Desmarca la X para que NO salga en el presupuesto)",
                value=(coste_tramitacion > 0),
                key=f"{key_prefix}_chk_inc_cie",
                help="Desmarca esta casilla con la X si el cliente ya dispone de boletín o si no te vas a encargar de tramitarlo ante Industria / SIEM."
            )
            if inc_cie:
                val_cie_input = st.number_input(
                    "📋 Importe Tramitación SIEM / CIE (€) [Aplica en ambos: Empresa y Autónomo]:",
                    min_value=0.0,
                    max_value=3000.0,
                    value=float(coste_tramitacion) if coste_tramitacion > 0 else 120.0,
                    step=10.0,
                    key=f"{key_prefix}_num_cie_base",
                    help="Honorarios de visado y presentación oficial ante Industria / SIEM."
                )
                val_cie_base = float(val_cie_input) if val_cie_input is not None else 0.0
                dif_cie = st.checkbox("Diferenciar tarifa de tramitación para Empresa", value=False, key=f"{key_prefix}_chk_dif_cie")
                if dif_cie:
                    col_cc1, col_cc2 = st.columns(2)
                    with col_cc1:
                        cie_emp_in = st.number_input("🏢 SIEM Empresa (€):", min_value=0.0, value=float(val_cie_base * 1.25), step=10.0, key=f"{key_prefix}_num_cie_emp")
                        coste_tramitacion_emp = float(cie_emp_in) if cie_emp_in is not None else val_cie_base
                    with col_cc2:
                        cie_auto_in = st.number_input("🧑‍🔧 SIEM Autónomo (€):", min_value=0.0, value=float(val_cie_base), step=10.0, key=f"{key_prefix}_num_cie_auto")
                        coste_tramitacion_auto = float(cie_auto_in) if cie_auto_in is not None else val_cie_base
                else:
                    coste_tramitacion_emp = float(val_cie_base)
                    coste_tramitacion_auto = float(val_cie_base)
            else:
                coste_tramitacion_emp = 0.0
                coste_tramitacion_auto = 0.0
                st.caption("ℹ️ *Partida de Boletín/SIEM DESMARCADA (0,00 € - NO saldrá en el presupuesto ni en el PDF).*")

        # -----------------------------------------------------------------
        # AJUSTES DE MANO DE OBRA, HORAS Y MÁRGENES
        # -----------------------------------------------------------------
        st.markdown("---")
        st.markdown("##### ⏱️ Ajustar Mano de Obra, Horas y Márgenes:")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            margen_mat_pct = st.slider(
                "📈 Margen s/ Materiales (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(margen_mat_def),
                step=5.0,
                key=f"{key_prefix}_slider_margen_mat",
                help="Beneficio comercial que aplicas sobre el precio de compra en almacén (Obramat/distribuidor)."
            )
        with col_m2:
            precio_h_coste = st.number_input(
                "🔨 Tu Sueldo / Hora (€/h)",
                min_value=15.0,
                max_value=150.0,
                value=float(precio_h_coste_def),
                step=2.5,
                key=f"{key_prefix}_num_precio_hora",
                help="Tu retribución profesional limpia por hora trabajada en obra."
            )
        with col_m3:
            horas_mo = st.number_input(
                "⏱️ Horas de Trabajo (h)",
                min_value=0.5,
                max_value=300.0,
                value=float(horas_mo_def),
                step=0.5,
                key=f"{key_prefix}_num_horas_mo",
                help="Horas estimadas totales dedicadas al montaje e instalación física."
            )
        with col_m4:
            recargo_empresa_pct = st.slider(
                "🏢 Recargo Empresa MO (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(recargo_emp_def),
                step=5.0,
                key=f"{key_prefix}_slider_recargo_emp",
                help="Sobrecoste de estructura, oficina y gestión para el Modo Empresa (G_mo)."
            )

        col_sub1, col_sub2 = st.columns([1.5, 2.5])
        with col_sub1:
            margen_mo_auto_pct = st.slider(
                "👤 Margen Extra MO Autónomo (%)",
                min_value=0.0,
                max_value=float(max(recargo_empresa_pct, 50.0)),
                value=0.0,
                step=5.0,
                key=f"{key_prefix}_slider_margen_auto",
                help="Recargo extra sobre tu mano de obra para autónomo. En 0% (Modo Autónomo puro) eres ultra competitivo cobrando tu jornal íntegro."
            )
        with col_sub2:
            st.markdown(f"""
            <div style="background-color:#f8fafc; border-left:3px solid #0284c7; padding:8px 12px; border-radius:4px; font-size:12.5px; color:#334155; margin-top:14px;">
                <b>💡 Estrategia Modo Autónomo:</b> Al mantener el recargo MO en <b>{margen_mo_auto_pct:.0f}%</b>, garantizas cobrar el 100% de tus horas (<b>{horas_mo * precio_h_coste:,.2f} €</b>) y tu ganancia de materiales (<b>{coste_mat * (margen_mat_pct / 100.0):,.2f} €</b>), ofreciendo un precio de calle que las constructoras no pueden igualar.
            </div>
            """, unsafe_allow_html=True)

        # Cálculos económicos base
        benef_mat = round(coste_mat * (margen_mat_pct / 100.0), 2)
        pvp_mat = round(coste_mat + benef_mat, 2)
        coste_mo_directo = round(horas_mo * precio_h_coste, 2)
        g_mo_empresa = round(coste_mo_directo * (recargo_empresa_pct / 100.0), 2)
        g_mo_autonomo = round(coste_mo_directo * (margen_mo_auto_pct / 100.0), 2)

        # -----------------------------------------------------------------
        # PLANIFICACIÓN DE TIEMPOS, CUADRILLA (1 O 2 PERSONAS) Y REPARTO
        # -----------------------------------------------------------------
        st.markdown("---")
        st.markdown("##### 👥 Planificación de Tiempos y Cuadrilla de Instaladores:")

        es_cable_pesado = (obra_seccion >= 16.0 or obra_longitud >= 15.0 or obra_trifasico)
        es_roza_obra = any("roza" in str(m.get("mat", "")).lower() for m in filas_materiales)
        if es_cable_pesado:
            rec_cuadrilla_idx = 1
            badge_rec_html = f"""<div style="background-color:#fef2f2; border:1.5px solid #dc2626; border-radius:6px; padding:10px 14px; margin-bottom:12px;">
                <span style="font-weight:700; color:#b91c1c;">🔴 RECOMENDACIÓN TÉCNICA: Se requiere Cuadrilla de 2 personas obligatoriamente</span><br/>
                <span style="font-size:12.5px; color:#475569;">Tirada de cable con longitud de <b>{obra_longitud:.0f} m</b> y sección de <b>{obra_seccion:.0f} mm²</b>: es indispensable un instalador en cuadro/contadores guiando y aplicando gel tiracables y otro tirando de la guía en vivienda para evitar rotura de guía, rozaduras o atascos.</span>
            </div>"""
        elif es_roza_obra or horas_mo >= 7.0:
            rec_cuadrilla_idx = 1
            badge_rec_html = """<div style="background-color:#fffbeb; border:1.5px solid #f59e0b; border-radius:6px; padding:10px 14px; margin-bottom:12px;">
                <span style="font-weight:700; color:#b45309;">🟡 RECOMENDACIÓN TÉCNICA: Cuadrilla de 2 personas muy aconsejable</span><br/>
                <span style="font-size:12.5px; color:#475569;">Trabajos de canalización/rozas o jornada extensa: mientras uno pica y aspira, el otro coloca tubo y yeso rápido, finalizando el tajo en la mitad de tiempo sin fatiga física.</span>
            </div>"""
        else:
            rec_cuadrilla_idx = 0
            badge_rec_html = """<div style="background-color:#f0fdf4; border:1.5px solid #16a34a; border-radius:6px; padding:10px 14px; margin-bottom:12px;">
                <span style="font-weight:700; color:#15803d;">🟢 RECOMENDACIÓN TÉCNICA: Viable para 1 instalador solo</span><br/>
                <span style="font-size:12.5px; color:#475569;">Tirada accesible y volumen de trabajo manejable para ejecutar de forma autónoma con total seguridad y buen rendimiento.</span>
            </div>"""

        st.markdown(badge_rec_html, unsafe_allow_html=True)

        col_cuad1, col_cuad2 = st.columns([1.8, 2.2])
        with col_cuad1:
            sel_cuadrilla = st.radio(
                "👥 ¿Cómo ejecutaréis esta obra?",
                ["👤 1 Instalador Solo", "👥 Cuadrilla de 2 Personas (Tú y tu Compañero)"],
                index=rec_cuadrilla_idx,
                horizontal=True,
                key=f"{key_prefix}_sel_cuadrilla"
            )
            es_cuadrilla_2 = ("2 Personas" in sel_cuadrilla)

        with col_cuad2:
            if es_cuadrilla_2:
                sel_modo_reparto = st.radio(
                    "🤝 Modalidad de Reparto de Beneficios:",
                    ["⚖️ A Medias (50% / 50% Socios - Deduciendo Gastos)", "🧑‍🔧 Oficial + Ayudante / Tarifa por horas"],
                    horizontal=True,
                    key=f"{key_prefix}_sel_modo_reparto"
                )
            else:
                sel_modo_reparto = "1_solo"

        if es_cuadrilla_2:
            h_reloj_obra = round(horas_mo / 2.0, 1)
            jornadas_txt = f"**{h_reloj_obra:.1f} horas de reloj** (¡Media jornada de mañana, termináis antes de comer!)" if h_reloj_obra <= 4.5 else f"**{h_reloj_obra:.1f} horas de reloj** (1 jornada completa entre los 2)"
            if "A Medias" in sel_modo_reparto:
                st.info(f"⏱️ **Tiempo de presencia en la obra:** {jornadas_txt}. Se deducen todos los gastos reales de la obra (materiales de almacén, gasolina/portes y tasas de boletín) y el **beneficio neto limpio restante se divide al 50% exacto para cada uno**.")
            else:
                col_ay1, col_ay2 = st.columns([1.5, 2.5])
                with col_ay1:
                    p_hora_comp = st.number_input("Precio/Hora Compañero (€/h):", min_value=12.0, max_value=80.0, value=20.0, step=1.0, key=f"{key_prefix}_p_hora_comp")
                with col_ay2:
                    st.caption(f"⏱️ **Tiempo de presencia:** {jornadas_txt}. Tu compañero cobrará **{h_reloj_obra * p_hora_comp:,.2f} €** ({h_reloj_obra:.1f}h a {p_hora_comp:.0f}€/h) y tú como instalador titular asumes tus horas y el beneficio de materiales y gestión.")
        else:
            es_cuadrilla_2 = False
            h_reloj_obra = float(horas_mo)

        # -----------------------------------------------------------------
        # GESTIÓN Y ORDEN DE PARTIDAS (ADELANTE, EN MEDIO O AL FINAL)
        # -----------------------------------------------------------------
        key_sec_part = f"{key_prefix}_secuencia_partidas"
        key_dict_extra = f"{key_prefix}_dict_partidas_extras"

        if key_dict_extra not in st.session_state:
            st.session_state[key_dict_extra] = {}

        if key_sec_part not in st.session_state:
            st.session_state[key_sec_part] = ["mat", "mo", "cie", "desp"]

        # Detalle de materiales para el texto descriptivo
        noms_mat_act_txt = [m['mat'] for m in filas_mat_activas[:3]]
        txt_resumen_mat = ", ".join(noms_mat_act_txt) if noms_mat_act_txt else "Materiales normalizados según memoria técnica REBT"
        if filas_mat_en_obra:
            txt_resumen_mat += " (Canalización/elementos en obra aportados por el cliente)"

        def _get_partida_info(pid):
            if pid == "mat":
                return {
                    "id": "mat",
                    "tipo": "sistema",
                    "concepto": "Materiales Normalizados y Canalización",
                    "icono": "📦",
                    "desc": f"Suministro de materiales homologados conforme a REBT ({txt_resumen_mat}).",
                    "importe_auto": pvp_mat,
                    "importe_emp": pvp_mat,
                    "activo": (pvp_mat > 0)
                }
            elif pid == "mo":
                return {
                    "id": "mo",
                    "tipo": "sistema",
                    "concepto": "Mano de Obra Especializada y Montaje",
                    "icono": "🔨",
                    "desc": f"Tendido, fijación y conexionado profesional ({horas_mo:.1f} horas estimadas de instalador cualificado).",
                    "importe_auto": round(coste_mo_directo + g_mo_autonomo, 2),
                    "importe_emp": round(coste_mo_directo + g_mo_empresa, 2),
                    "activo": (coste_mo_directo > 0)
                }
            elif pid == "cie":
                return {
                    "id": "cie",
                    "tipo": "sistema",
                    "concepto": "Ensayos ITC-BT-05 y Certificado CIE / SIEM",
                    "icono": "📋",
                    "desc": "Medidas de aislamiento con megóhmetro, continuidad, disparo diferencial y tramitación oficial de boletín eléctrico ante Industria / SIEM.",
                    "importe_auto": coste_tramitacion_auto,
                    "importe_emp": coste_tramitacion_emp,
                    "activo": (inc_cie and (coste_tramitacion_auto > 0 or coste_tramitacion_emp > 0))
                }
            elif pid == "desp":
                return {
                    "id": "desp",
                    "tipo": "sistema",
                    "concepto": "Desplazamiento y Medios Auxiliares",
                    "icono": "🚗",
                    "desc": "Vehículo de taller, acopio y portes al centro de trabajo.",
                    "importe_auto": desplazamiento_auto,
                    "importe_emp": desplazamiento_emp,
                    "activo": (inc_desp and (desplazamiento_auto > 0 or desplazamiento_emp > 0))
                }
            elif pid in st.session_state[key_dict_extra]:
                ex = st.session_state[key_dict_extra][pid]
                return {
                    "id": pid,
                    "tipo": "personalizada",
                    "concepto": ex.get("concepto", "Partida de Obra"),
                    "icono": "🛠️",
                    "desc": ex.get("descripcion", "Partida complementaria acordada con el cliente."),
                    "importe_auto": float(ex.get("importe_auto", ex.get("importe", 0.0))),
                    "importe_emp": float(ex.get("importe_emp", ex.get("importe", 0.0))),
                    "activo": True
                }
            return None

        # Obtener lista activa y ordenada
        partidas_activas_ordenadas = []
        for pid in st.session_state[key_sec_part]:
            dp = _get_partida_info(pid)
            if dp and dp.get("activo"):
                partidas_activas_ordenadas.append(dp)

        st.markdown("---")
        st.markdown("##### 🛠️ Organización y Orden de Partidas del Presupuesto")
        st.caption("Reordena cualquier partida con los botones ⬆️ / ⬇️ para colocarla **adelante, en medio o al final**, o añade nuevas partidas de obra:")

        for idx_po, part in enumerate(partidas_activas_ordenadas, start=1):
            col_po1, col_po2, col_po3, col_po4 = st.columns([2.8, 3.4, 1.6, 1.2])
            with col_po1:
                st.markdown(f'<div translate="no" class="notranslate" style="font-weight:700; font-size:14px;">PART. {idx_po:02d}: {part.get("icono", "📌")} {part.get("concepto", "Partida")}</div>', unsafe_allow_html=True)
            with col_po2:
                desc_p = str(part.get('desc', ''))
                txt_corta = desc_p[:65] + ("..." if len(desc_p) > 65 else "")
                st.markdown(f'<div translate="no" class="notranslate" style="font-size:12.5px; color:#64748b; line-height:1.3;">{txt_corta}</div>', unsafe_allow_html=True)
            with col_po3:
                try:
                    imp_a = float(part.get('importe_auto', 0.0) or 0.0)
                    imp_e = float(part.get('importe_emp', 0.0) or 0.0)
                    if round(imp_a, 2) == round(imp_e, 2):
                        txt_p_fmt = f"{imp_a:,.2f} €"
                    else:
                        txt_p_fmt = f"Aut: {imp_a:,.2f} € | Emp: {imp_e:,.2f} €"
                    st.markdown(f'<div translate="no" class="notranslate" style="font-weight:700; color:#0f172a; font-size:13.5px;">{txt_p_fmt}</div>', unsafe_allow_html=True)
                except Exception:
                    st.markdown('<div translate="no" class="notranslate" style="font-weight:700; color:#0f172a; font-size:13.5px;">0,00 €</div>', unsafe_allow_html=True)
            with col_po4:
                col_sub_u, col_sub_d, col_sub_del = st.columns(3)
                with col_sub_u:
                    if st.button("⬆️", key=f"{key_prefix}_btn_up_part_{part.get('id', idx_po)}", disabled=(idx_po == 1), help="Subir una posición hacia adelante"):
                        curr_sec = st.session_state.get(key_sec_part, [])
                        if part.get('id') in curr_sec and (idx_po - 2) >= 0:
                            prev_pid = partidas_activas_ordenadas[idx_po - 2].get('id')
                            if prev_pid in curr_sec:
                                idx_in_sec = curr_sec.index(part['id'])
                                prev_in_sec = curr_sec.index(prev_pid)
                                curr_sec[idx_in_sec], curr_sec[prev_in_sec] = curr_sec[prev_in_sec], curr_sec[idx_in_sec]
                                st.rerun()
                with col_sub_d:
                    if st.button("⬇️", key=f"{key_prefix}_btn_dn_part_{part.get('id', idx_po)}", disabled=(idx_po == len(partidas_activas_ordenadas)), help="Bajar una posición hacia atrás"):
                        curr_sec = st.session_state.get(key_sec_part, [])
                        if part.get('id') in curr_sec and idx_po < len(partidas_activas_ordenadas):
                            next_pid = partidas_activas_ordenadas[idx_po].get('id')
                            if next_pid in curr_sec:
                                idx_in_sec = curr_sec.index(part['id'])
                                next_in_sec = curr_sec.index(next_pid)
                                curr_sec[idx_in_sec], curr_sec[next_in_sec] = curr_sec[next_in_sec], curr_sec[idx_in_sec]
                                st.rerun()
                with col_sub_del:
                    if part.get('tipo') == "personalizada":
                        if st.button("🗑️", key=f"{key_prefix}_btn_del_part_{part.get('id', idx_po)}", help="Eliminar esta partida"):
                            if part.get('id') in st.session_state.get(key_sec_part, []):
                                st.session_state[key_sec_part].remove(part['id'])
                            if part.get('id') in st.session_state.get(key_dict_extra, {}):
                                del st.session_state[key_dict_extra][part['id']]
                            st.rerun()

        with st.popover("➕ Añadir Nueva Partida de Obra o Servicio"):
            st.markdown("##### 🛠️ Nueva Partida Complementaria")
            with st.form(f"{key_prefix}_form_nueva_partida", clear_on_submit=True):
                nuevo_part_concepto = st.text_input(
                    "Concepto / Título de la partida:",
                    placeholder="Ej: Apertura y sellado de rozas por albañilería / Andamio homologado"
                )
                nuevo_part_desc = st.text_area(
                    "Descripción técnica detallada (aparecerá en el PDF del cliente):",
                    placeholder="Ej: Apertura de rozas en tabiquería para paso de tubos corrugados y posterior sellado con yeso y pasta de agarre...",
                    height=70
                )
                col_npi1, col_npi2 = st.columns(2)
                with col_npi1:
                    nuevo_part_imp = st.number_input(
                        "Importe Base (€) [Aplica a Empresa y Autónomo]:",
                        min_value=0.0,
                        value=150.0,
                        step=10.0
                    )
                with col_npi2:
                    dif_part_precio = st.checkbox("Diferenciar precio para Empresa", value=False)

                nuevo_part_imp_emp = nuevo_part_imp
                if dif_part_precio:
                    nuevo_part_imp_emp = st.number_input(
                        "Importe Empresa (€):",
                        min_value=0.0,
                        value=float(nuevo_part_imp * 1.25),
                        step=10.0
                    )

                n_part_actual = len(partidas_activas_ordenadas)
                sel_pos_part = st.selectbox(
                    "📍 ¿Dónde deseas colocar esta nueva partida en el presupuesto?",
                    [
                        "🔝 Al principio de todo (1ª posición - antes de los materiales)",
                        "🔚 Al final de todo (última posición)",
                        "🎯 En una posición específica (en medio)"
                    ],
                    index=1
                )
                pos_especifica_part = 1
                if "específica" in sel_pos_part:
                    pos_especifica_part = st.number_input("Nº de posición donde insertarla:", min_value=1, max_value=n_part_actual + 1, value=min(2, n_part_actual + 1), step=1)

                btn_crear_part = st.form_submit_button("➕ Añadir Partida al Presupuesto", type="primary", use_container_width=True)
                if btn_crear_part:
                    if nuevo_part_concepto.strip():
                        nueva_clave = f"extra_{uuid.uuid4().hex[:6]}"
                        st.session_state[key_dict_extra][nueva_clave] = {
                            "concepto": nuevo_part_concepto.strip(),
                            "descripcion": nuevo_part_desc.strip() if nuevo_part_desc.strip() else f"Trabajos auxiliares de {nuevo_part_concepto.strip()}",
                            "importe": float(nuevo_part_imp),
                            "importe_auto": float(nuevo_part_imp),
                            "importe_emp": float(nuevo_part_imp_emp)
                        }

                        if "principio" in sel_pos_part:
                            st.session_state[key_sec_part].insert(0, nueva_clave)
                        elif "específica" in sel_pos_part:
                            idx_ins_part = max(0, min(len(st.session_state[key_sec_part]), int(pos_especifica_part) - 1))
                            st.session_state[key_sec_part].insert(idx_ins_part, nueva_clave)
                        else:
                            st.session_state[key_sec_part].append(nueva_clave)

                        st.success(f"Partida '{nuevo_part_concepto}' añadida al presupuesto.")
                        st.rerun()

    # Recalcular partidas activas ordenadas para totales y balance
    partidas_activas_ordenadas = []
    for pid in st.session_state[key_sec_part]:
        dp = _get_partida_info(pid)
        if dp and dp.get("activo"):
            partidas_activas_ordenadas.append(dp)

    # Totales Modo Empresa
    base_empresa = round(sum(p["importe_emp"] for p in partidas_activas_ordenadas), 2)
    iva_empresa = round(base_empresa * (iva_pct / 100.0), 2)
    total_empresa = round(base_empresa + iva_empresa, 2)

    # Totales Modo Autónomo
    base_autonomo = round(sum(p["importe_auto"] for p in partidas_activas_ordenadas), 2)
    iva_autonomo = round(base_autonomo * (iva_pct / 100.0), 2)
    total_autonomo = round(base_autonomo + iva_autonomo, 2)

    diferencia_ahorro = round(total_empresa - total_autonomo, 2)
    total_extras_auto = sum(p["importe_auto"] for p in partidas_activas_ordenadas if p["tipo"] == "personalizada")
    sueldo_limpio_autonomo = round(coste_mo_directo + g_mo_autonomo + benef_mat + coste_tramitacion_auto + total_extras_auto, 2)

    anticipo_mat = round(coste_mat * (1.0 + iva_pct / 100.0), 2)
    pct_anticipo_rec = round((coste_mat / base_autonomo * 100), 0) if base_autonomo > 0 else 40.0
    pct_anticipo_rec = max(35.0, min(50.0, pct_anticipo_rec))
    anticipo_recomendado = round(total_autonomo * (pct_anticipo_rec / 100.0), 2)

    tab_bal, tab_audit, tab_acopio, tab_guardar = st.tabs([
        "⚖️ Balance Económico (Empresa vs Autónomo)",
        "🛡️ Semáforo & Auditor de Contraofertas",
        "🛒 Lista Mostrador & Anticipo",
        "📂 Guardar / Recuperar Presupuesto"
    ])

    # ---------------------------------------------------------------------
    # TAB 1: BALANCE ECONÓMICO Y COMPARATIVA DE TARIFAS
    # ---------------------------------------------------------------------
    with tab_bal:
        col_t1, col_t2, col_t3 = st.columns([1.5, 1.5, 1.2])
        with col_t1:
            st.metric(
                "🏢 Modo Empresa (Pyme/Constructora)",
                f"{total_empresa:,.2f} €",
                help="Tarifa formal con recargo de estructura de empresa (G_mo 40%)."
            )
            st.caption(f"Base: {base_empresa:,.2f} € | IVA ({iva_pct:.0f}%): {iva_empresa:,.2f} €")
        with col_t2:
            st.metric(
                "🧑‍🔧 Modo Autónomo",
                f"{total_autonomo:,.2f} €",
                delta=f"-{diferencia_ahorro:,.2f} € Ahorro",
                delta_color="inverse",
                help="Tarifa competitiva de calle cobrando tu jornal al 100% y retirando recargo fantasma de oficina."
            )
            st.caption(f"Base: {base_autonomo:,.2f} € | IVA ({iva_pct:.0f}%): {iva_autonomo:,.2f} €")
        with col_t3:
            st.metric(
                "💰 Tu Beneficio Limpio",
                f"{sueldo_limpio_autonomo:,.2f} €",
                help="Lo que te queda neto en el bolsillo: Tu sueldo de horas + margen de materiales + honorarios boletín."
            )
            st.caption(f"Ganas: {horas_mo:.1f}h x {precio_h_coste:.0f}€ + {benef_mat:.2f}€ mat.")

        # Si está activada la cuadrilla de 2 personas, mostrar el desglose de reparto y deducción de gastos
        if es_cuadrilla_2:
            st.markdown("---")
            st.markdown("##### 🤝 Reparto Económico y Rentabilidad de la Cuadrilla (Deduciendo Gastos)")

            # Gastos duros de la obra
            gastos_duros_obra = round(coste_mat + desplazamiento_auto + coste_tramitacion_auto, 2)
            # Bote limpio a repartir tras pagar materiales, gasolina y tasas
            bote_limpio_obra = round(base_autonomo - gastos_duros_obra, 2)

            h_reloj = round(horas_mo / 2.0, 1)

            if "A Medias" in sel_modo_reparto:
                pago_tu = round(bote_limpio_obra / 2.0, 2)
                pago_comp = round(bote_limpio_obra - pago_tu, 2)
                modo_rep_txt = "⚖️ 50% / 50% A Medias (Socios)"
            else:
                p_hora_comp = float(st.session_state.get(f"{key_prefix}_p_hora_comp", 20.0))
                pago_comp = round(h_reloj * p_hora_comp, 2)
                pago_tu = round(bote_limpio_obra - pago_comp, 2)
                modo_rep_txt = f"🧑‍🔧 Ayudante por horas ({p_hora_comp:.0f} €/h)"

            r_hora_tu = round(pago_tu / h_reloj, 2) if h_reloj > 0 else 0.0
            r_hora_comp = round(pago_comp / h_reloj, 2) if h_reloj > 0 else 0.0

            with st.container(border=True):
                st.markdown(f"""
                <div style="background-color:#f0fdf4; border-left:4px solid #16a34a; padding:10px 14px; border-radius:4px; margin-bottom:12px; font-size:13px; color:#14532d;">
                    <b>📊 Balance de Obra en Pareja:</b> Para esta obra se facturan <b>{horas_mo:.1f} horas de mano de obra</b> al cliente, pero al ir los 2 se termina en <b>{h_reloj:.1f} horas de reloj</b>. 
                    Primero se pagan los materiales de almacén (<b>{coste_mat:,.2f} €</b>), combustible/portes (<b>{desplazamiento_auto:,.2f} €</b>) y tasas (<b>{coste_tramitacion_auto:,.2f} €</b>). 
                    El <b>bote limpio de {bote_limpio_obra:,.2f} €</b> se reparte en modalidad: <b>{modo_rep_txt}</b>.
                </div>
                """, unsafe_allow_html=True)

                col_rc1, col_rc2, col_rc3, col_rc4 = st.columns(4)
                with col_rc1:
                    st.metric("🧾 Gastos Deducidos", f"{gastos_duros_obra:,.2f} €", help="Materiales de compra + Vehículo/Portes + Tasas")
                    st.caption(f"Material almacén: {coste_mat:,.2f} €")
                with col_rc2:
                    st.metric("💰 Bote Neto Limpio", f"{bote_limpio_obra:,.2f} €", help="Total disponible para repartir entre ambos")
                    st.caption(f"Tiempo obra: {h_reloj:.1f}h de reloj")
                with col_rc3:
                    st.metric("🧑‍🔧 Tu Ganancia Limpia", f"{pago_tu:,.2f} €", delta=f"{r_hora_tu:,.2f} €/h real")
                    st.caption(f"Por tus {h_reloj:.1f} horas trabajadas")
                with col_rc4:
                    st.metric("👥 Ganancia Compañero", f"{pago_comp:,.2f} €", delta=f"{r_hora_comp:,.2f} €/h real")
                    st.caption(f"Por sus {h_reloj:.1f} horas trabajadas")

        # Tabla de desglose transparente interna en el orden exacto configurado por el usuario
        st.markdown("##### 🔍 Desglose Partida a Partida (¿A dónde va cada euro?)")
        filas_balance = []
        for idx_b, part_b in enumerate(partidas_activas_ordenadas, start=1):
            imp_e = part_b["importe_emp"]
            imp_a = part_b["importe_auto"]
            dif_p = round(imp_e - imp_a, 2)
            dest_txt = part_b["desc"][:48] + ("..." if len(part_b["desc"]) > 48 else "")
            filas_balance.append({
                "Concepto Económico": f"{part_b['icono']} {idx_b}. {part_b['concepto']}",
                "🏢 Empresa": f"{imp_e:,.2f} €",
                "🧑‍🔧 Autónomo": f"{imp_a:,.2f} €",
                "Diferencia": f"-{dif_p:,.2f} €" if dif_p > 0 else "0,00 €",
                "Destino": dest_txt
            })

        # FILAS DE TOTALES CLAVE AL FINAL DE LA TABLA (PARA VER CON TOTAL CLARIDAD EL TOTAL DE CADA COLUMNA):
        diferencia_base = round(base_empresa - base_autonomo, 2)
        diferencia_iva = round(iva_empresa - iva_autonomo, 2)

        filas_balance.extend([
            {
                "Concepto Económico": "🏁 TOTAL BASE IMPONIBLE (S/IVA)",
                "🏢 Empresa": f"{base_empresa:,.2f} €",
                "🧑‍🔧 Autónomo": f"{base_autonomo:,.2f} €",
                "Diferencia": f"-{diferencia_base:,.2f} €",
                "Destino": f"Ahorro neto de {(diferencia_base / base_empresa * 100) if base_empresa > 0 else 0:.1f}% para el cliente"
            },
            {
                "Concepto Económico": f"🏛️ IVA Oficial ({iva_pct:.0f}%)",
                "🏢 Empresa": f"{iva_empresa:,.2f} €",
                "🧑‍🔧 Autónomo": f"{iva_autonomo:,.2f} €",
                "Diferencia": f"-{diferencia_iva:,.2f} €",
                "Destino": "Cuota de impuestos para Hacienda"
            },
            {
                "Concepto Económico": "🏆 TOTAL FINAL FACTURA CLIENTE (CON IVA)",
                "🏢 Empresa": f"{total_empresa:,.2f} €",
                "🧑‍🔧 Autónomo": f"{total_autonomo:,.2f} €",
                "Diferencia": f"-{diferencia_ahorro:,.2f} €",
                "Destino": f"Ahorro total final de {diferencia_ahorro:,.2f} € para cerrar la obra"
            },
            {
                "Concepto Económico": "💰 DINERO LIMPIO EN TU BOLSILLO",
                "🏢 Empresa": f"{sueldo_limpio_autonomo:,.2f} €",
                "🧑‍🔧 Autónomo": f"{sueldo_limpio_autonomo:,.2f} €",
                "Diferencia": "0,00 €",
                "Destino": "Cobras íntegros tus horas y el beneficio de materiales"
            }
        ])

        st.dataframe(filas_balance, use_container_width=True, hide_index=True)

        # Tarjetas de Totales de Columna destacados
        col_res_tot1, col_res_tot2, col_res_tot3 = st.columns(3)
        with col_res_tot1:
            st.success(f"🏢 **TOTAL COLUMNA EMPRESA:**  \n**{total_empresa:,.2f} €**  \n*Base: {base_empresa:,.2f} € + IVA: {iva_empresa:,.2f} €*")
        with col_res_tot2:
            st.info(f"🧑‍🔧 **TOTAL COLUMNA AUTÓNOMO:**  \n**{total_autonomo:,.2f} €**  \n*Base: {base_autonomo:,.2f} € + IVA: {iva_autonomo:,.2f} €*")
        with col_res_tot3:
            st.warning(f"🎯 **DIFERENCIA / AHORRO CLIENTE:**  \n**-{diferencia_ahorro:,.2f} €**  \n*Rebaja comercial del {(diferencia_ahorro / total_empresa * 100) if total_empresa > 0 else 0:.1f}%*")

        # -------------------------------------------------------------
        # GENERADOR DE PRESUPUESTO OFICIAL EN PDF PARA EL CLIENTE
        # -------------------------------------------------------------
        st.markdown("---")
        st.markdown("##### 📄 Presupuesto Oficial para Enviar al Cliente (PDF Imprimible)")
        st.caption("Emite y descarga la oferta formal para entregar al cliente o mandar por WhatsApp, disponible en Modo Autónomo o Modo Empresa:")

        # Sugerencias inteligentes de condiciones de pago según el presupuesto
        resto_autonomo = max(0.0, round(total_autonomo - anticipo_recomendado, 2))
        p50_autonomo = round(total_autonomo * 0.50, 2)
        h1_40 = round(total_autonomo * 0.40, 2)
        h2_30 = round(total_autonomo * 0.30, 2)
        h3_30 = max(0.0, round(total_autonomo - h1_40 - h2_30, 2))

        sugerencias_fpago = {
            f"💡 Anticipo Materiales ({pct_anticipo_rec:.0f}%) + Resto al Finalizar": (
                f"Anticipo para acopio de materiales ({pct_anticipo_rec:.0f}% = {anticipo_recomendado:,.2f} €) a la aceptación, "
                f"y resto ({resto_autonomo:,.2f} €) a la finalización y entrega de la instalación / boletín"
            ),
            "⚖️ 50% al Inicio y 50% a la Entrega": (
                f"50% al inicio de los trabajos ({p50_autonomo:,.2f} €) y 50% restante ({p50_autonomo:,.2f} €) a la terminación y conformidad"
            ),
            "🏗️ Por Hitos de Obra (40% Acopio / 30% Montaje / 30% Fin)": (
                f"40% al aceptar ({h1_40:,.2f} €) para acopio de material, 30% al finalizar canalizaciones y cableado ({h2_30:,.2f} €), "
                f"y 30% ({h3_30:,.2f} €) a la prueba de tensión y entrega de boletín"
            ),
            "🏁 100% al Finalizar el Trabajo": (
                f"100% ({total_autonomo:,.2f} €) al finalizar completamente la instalación y entrega de certificación"
            ),
            "🏦 Transferencia Bancaria (30 Días)": (
                "Transferencia bancaria a 30 días tras emisión de factura oficial"
            ),
            "✏️ Personalizada (Escribir manualmente)": ""
        }

        col_cfg_pdf1, col_cfg_pdf2 = st.columns([1.7, 1.3])
        with col_cfg_pdf1:
            mostrar_forma_pago = st.checkbox(
                "💳 [X] Incluir Forma de Pago en el Presupuesto (Desmarca la X para que NO salga escrita en el PDF)",
                value=True,
                key=f"{key_prefix}_chk_ver_fpago",
                help="Si desmarcas esta casilla con una X, la forma de pago quedará 100% oculta y no figurará en el presupuesto que entregues al cliente."
            )
        with col_cfg_pdf2:
            with st.popover("⚙️ Configurar Datos del Cliente y Condiciones"):
                cli_nombre_pdf = st.text_input("Nombre del Cliente / Destinatario:", value=nom_cliente_def, key=f"{key_prefix}_in_clipdf_nom")
                cli_dir_pdf = st.text_input("Dirección de la Obra:", value="Calle Mayor nº 45", key=f"{key_prefix}_in_clipdf_dir")
                cli_tel_pdf = st.text_input("Teléfono del Cliente:", value="+34 600 000 000", key=f"{key_prefix}_in_clipdf_tel")
                cli_validez_pdf = st.text_input("Validez del Presupuesto:", value="30 días naturales", key=f"{key_prefix}_in_clipdf_val")
                cli_plazo_pdf = st.text_input("Plazo Estimado de Ejecución:", value="1-2 días laborables", key=f"{key_prefix}_in_clipdf_plz")

        if mostrar_forma_pago:
            col_sug_f1, col_sug_f2 = st.columns([1.5, 2.5])
            with col_sug_f1:
                sel_sug_fpago = st.selectbox(
                    "💡 Sugerencia Forma de Pago:",
                    list(sugerencias_fpago.keys()),
                    index=0,
                    key=f"{key_prefix}_sel_sug_fpago",
                    help="Elige una modalidad recomendada calculada con los importes de esta obra."
                )
                val_sug_txt = sugerencias_fpago[sel_sug_fpago]
            with col_sug_f2:
                cli_forma_pago = st.text_area(
                    "Texto de la Forma de Pago a imprimir (editable):",
                    value=val_sug_txt,
                    height=68,
                    key=f"{key_prefix}_in_clipdf_fpago",
                    help="Puedes modificar libremente el texto que saldrá impreso en el PDF del cliente."
                )
        else:
            cli_forma_pago = ""
            st.info("🙈 **Forma de pago OCULTA:** Has desmarcado la casilla con la X. NO aparecerá ninguna condición de pago en el presupuesto ni en el PDF del cliente.")

        proyecto_info_pdf = {
            "cliente": cli_nombre_pdf if 'cli_nombre_pdf' in locals() else nom_cliente_def,
            "direccion": cli_dir_pdf if 'cli_dir_pdf' in locals() else "Calle Mayor nº 45",
            "telefono": cli_tel_pdf if 'cli_tel_pdf' in locals() else "+34 600 000 000",
            "validez": cli_validez_pdf if 'cli_validez_pdf' in locals() else "30 días naturales",
            "plazo": cli_plazo_pdf if 'cli_plazo_pdf' in locals() else "1-2 días laborables",
            "mostrar_forma_pago": mostrar_forma_pago,
            "forma_pago": cli_forma_pago if mostrar_forma_pago else "",
            "concepto": nom_obra_def,
            "empresa": "BOLIMUR ELECTRICIDAD",
            "licencia": "Instalador Autorizado REBT (DGEAIM Murcia)",
            "fecha": datetime.date.today().strftime("%d/%m/%Y")
        }

        # Detalle de materiales para el PDF
        noms_mat_act = [m['mat'] for m in filas_mat_activas[:3]]
        txt_det_mat = ", ".join(noms_mat_act) if noms_mat_act else "Materiales homologados REBT según memoria técnica"
        if filas_mat_en_obra:
            txt_det_mat += " (Canalización y elementos preexistentes en obra aportados por el cliente)"

        # Preparar todas las partidas ordenadas para el PDF del cliente
        partidas_pdf_auto = [
            {
                "num": f"PART. {idx:02d}",
                "titulo": p["concepto"],
                "desc": p["desc"],
                "importe": p["importe_auto"]
            }
            for idx, p in enumerate(partidas_activas_ordenadas, start=1)
        ]
        partidas_pdf_emp = [
            {
                "num": f"PART. {idx:02d}",
                "titulo": p["concepto"],
                "desc": p["desc"],
                "importe": p["importe_emp"]
            }
            for idx, p in enumerate(partidas_activas_ordenadas, start=1)
        ]

        # Preparar datos específicos para Modo Autónomo
        presupuesto_data_auto = {
            "base_imponible": base_autonomo,
            "iva_pct": iva_pct,
            "cuota_iva": iva_autonomo,
            "total_cliente": total_autonomo,
            "coste_materiales": coste_mat,
            "coste_materiales_venta": round(coste_mat + benef_mat, 2),
            "horas_mo": horas_mo,
            "coste_mo_venta": round(coste_mo_directo + g_mo_autonomo, 2),
            "coste_tramitacion": coste_tramitacion_auto,
            "desplazamiento": desplazamiento_auto,
            "detalle_materiales": txt_det_mat,
            "partidas": partidas_pdf_auto
        }

        # Preparar datos específicos para Modo Empresa
        presupuesto_data_emp = {
            "base_imponible": base_empresa,
            "iva_pct": iva_pct,
            "cuota_iva": iva_empresa,
            "total_cliente": total_empresa,
            "coste_materiales": coste_mat,
            "coste_materiales_venta": round(coste_mat + benef_mat, 2),
            "horas_mo": horas_mo,
            "coste_mo_venta": round(coste_mo_directo + g_mo_empresa, 2),
            "coste_tramitacion": coste_tramitacion_emp,
            "desplazamiento": desplazamiento_emp,
            "detalle_materiales": txt_det_mat,
            "partidas": partidas_pdf_emp
        }

        try:
            pdf_bytes_auto = pdf_comercial_cliente.generar_pdf_oferta_comercial(
                proyecto_info_pdf, presupuesto_data_auto, modo="autonomo"
            )
            pdf_bytes_emp = pdf_comercial_cliente.generar_pdf_oferta_comercial(
                proyecto_info_pdf, presupuesto_data_emp, modo="empresa"
            )

            col_btn_auto, col_btn_emp = st.columns(2)
            with col_btn_auto:
                st.download_button(
                    label=f"🧑‍🔧 🖨️ Descargar Presupuesto MODO AUTÓNOMO ({total_autonomo:,.2f} €)",
                    data=pdf_bytes_auto,
                    file_name=f"Presupuesto_{nom_obra_def.replace(' ', '_')}_Autonomo.pdf",
                    mime="application/pdf",
                    type="primary",
                    key=f"{key_prefix}_btn_descarga_pdf_auto",
                    use_container_width=True
                )
                st.caption(f"Tarifa competitiva de calle (Base: {base_autonomo:,.2f} € + IVA: {iva_autonomo:,.2f} €)")

            with col_btn_emp:
                st.download_button(
                    label=f"🏢 🖨️ Descargar Presupuesto MODO EMPRESA ({total_empresa:,.2f} €)",
                    data=pdf_bytes_emp,
                    file_name=f"Presupuesto_{nom_obra_def.replace(' ', '_')}_Empresa.pdf",
                    mime="application/pdf",
                    type="secondary",
                    key=f"{key_prefix}_btn_descarga_pdf_emp",
                    use_container_width=True
                )
                st.caption(f"Tarifa formal con estructura de empresa (Base: {base_empresa:,.2f} € + IVA: {iva_empresa:,.2f} €)")

            with st.popover("👁️ Vista Previa en Pantalla del Presupuesto (PDF)"):
                sel_prev_modo = st.radio("¿Qué modelo deseas visualizar?", ["🧑‍🔧 Modo Autónomo", "🏢 Modo Empresa"], horizontal=True, key=f"{key_prefix}_rad_prev_modo")
                pdf_mostrar = pdf_bytes_auto if "Autónomo" in sel_prev_modo else pdf_bytes_emp
                try:
                    import pymupdf
                    doc_prev = pymupdf.open(stream=pdf_mostrar, filetype="pdf")
                    for pag_num, pag in enumerate(doc_prev, start=1):
                        pix = pag.get_pixmap(dpi=130)
                        st.image(pix.tobytes("png"), caption=f"Página {pag_num} ({sel_prev_modo})", use_container_width=True)
                except Exception:
                    import base64
                    b64 = base64.b64encode(pdf_mostrar).decode('utf-8')
                    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="500"></iframe>', unsafe_allow_html=True)
        except Exception as e_pdf_cli:
            st.warning(f"Generador PDF disponible: {e_pdf_cli}")

    # ---------------------------------------------------------------------
    # TAB 2: SEMÁFORO DE NEGOCIACIÓN Y AUDITOR DE CONTRAOFERTAS
    # ---------------------------------------------------------------------
    with tab_audit:
        st.markdown("##### 🚦 Semáforo de Precios y Negociación de Calle")
        suelo_seguridad = round(coste_mat + coste_tramitacion + desplazamiento + (20.0 * horas_mo), 2)
        suelo_seguridad_civa = round(suelo_seguridad * (1.0 + iva_pct / 100.0), 2)

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown(f"""
            <div style="background-color:#f0fdf4; border:2px solid #16a34a; border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#16a34a; font-weight:bold; font-size:14px;">🟢 PRECIO ÓPTIMO (EMPRESA)</div>
                <div style="color:#0f172a; font-size:22px; font-weight:800; margin:4px 0;">{total_empresa:,.2f} €</div>
                <div style="color:#64748b; font-size:12px;">Máximo beneficio comercial</div>
            </div>
            """, unsafe_allow_html=True)
        with col_s2:
            st.markdown(f"""
            <div style="background-color:#eff6ff; border:2px solid #0284c7; border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#0284c7; font-weight:bold; font-size:14px;">🔵 PRECIO AUTÓNOMO (RECOMENDADO)</div>
                <div style="color:#0f172a; font-size:22px; font-weight:800; margin:4px 0;">{total_autonomo:,.2f} €</div>
                <div style="color:#64748b; font-size:12px;">Tu jornal íntegro + margen material</div>
            </div>
            """, unsafe_allow_html=True)
        with col_s3:
            st.markdown(f"""
            <div style="background-color:#fef2f2; border:2px solid #dc2626; border-radius:8px; padding:12px; text-align:center;">
                <div style="color:#dc2626; font-weight:bold; font-size:14px;">🔴 SUELO MÍNIMO DE SEGURIDAD</div>
                <div style="color:#0f172a; font-size:22px; font-weight:800; margin:4px 0;">{suelo_seguridad_civa:,.2f} €</div>
                <div style="color:#dc2626; font-weight:bold; font-size:12px;">¡No bajar de aquí o pierdes dinero!</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 🛡️ Auditor de Contraofertas («El cliente me ofrece...»)")
        st.info("💡 Si el cliente o contratista te pide una rebaja o te ofrece una cantidad cerrada para hacer la obra, indícala abajo para que el sistema audite si pierdes dinero o qué contraoferta responderle.")

        col_in_of1, col_in_of2 = st.columns([2, 1.5])
        with col_in_of1:
            contraoferta_input = st.number_input(
                "Introduce la cantidad ofertada por el cliente (€):",
                min_value=0.0,
                max_value=100000.0,
                value=round(total_autonomo * 0.85, 2),
                step=50.0,
                key=f"{key_prefix}_num_contraoferta"
            )
        with col_in_of2:
            tipo_oferta_iva = st.radio(
                "¿La oferta del cliente incluye IVA?",
                ["Sí, con IVA incluido", "No, Base Imponible (Sin IVA)"],
                horizontal=True,
                key=f"{key_prefix}_rad_iva_of"
            )
            incluye_iva_val = ("Sí" in tipo_oferta_iva)

        # Análisis instantáneo de la contraoferta
        res_auditoria = auditar_contraoferta(
            precio_ofertado=contraoferta_input,
            coste_materiales=coste_mat,
            coste_boletin=coste_tramitacion,
            horas_estimadas=horas_mo,
            precio_hora_objetivo=precio_h_coste,
            gastos_vehiculo=desplazamiento,
            iva_pct=iva_pct,
            oferta_con_iva=incluye_iva_val
        )

        # Mostrar caja de alerta
        bg_alert = "#fee2e2" if "PELIGRO" in res_auditoria["estado"] else ("#fef3c7" if "RIESGO" in res_auditoria["estado"] else "#dcfce7")
        st.markdown(f"""
        <div style="background-color:{bg_alert}; border:2px solid {res_auditoria['color_badge']}; border-radius:8px; padding:15px; margin-top:10px;">
            <h4 style="color:{res_auditoria['color_badge']}; margin:0 0 8px 0;">{res_auditoria['alerta_titulo']}</h4>
            <div style="font-size:14px; color:#1e293b; line-height:1.5;">{res_auditoria['alerta_detalle']}</div>
        </div>
        """, unsafe_allow_html=True)

        col_res_a1, col_res_a2, col_res_a3 = st.columns(3)
        with col_res_a1:
            st.metric("Cobras por hora trabajada", f"{res_auditoria['precio_hora_real']:,.2f} €/h", help="Lo que te queda limpio por hora tras pagar materiales y boletín.")
        with col_res_a2:
            st.metric("Beneficio neto en el bolsillo", f"{res_auditoria['beneficio_neto_real']:,.2f} €")
        with col_res_a3:
            st.metric("Lo mínimo para no perder", f"{res_auditoria['suelo_minimo_civa']:,.2f} €")

        # Texto para WhatsApp listo para copiar
        with st.expander("📲 Ver Mensaje de Contraoferta redactado para WhatsApp (Copiar y Enviar)", expanded=True):
            st.text_area("Mensaje formal de respuesta al cliente:", value=res_auditoria["texto_contraoferta_whatsapp"], height=160, key=f"{key_prefix}_txt_wa_contra")
            st.caption("Copia este texto y pégalo directamente en WhatsApp para responder con criterio técnico sin perder la venta ni tu dinero.")

    # ---------------------------------------------------------------------
    # TAB 3: LISTA DE COMPRA PARA ALMACÉN Y CALCULADORA DE ANTICIPO
    # ---------------------------------------------------------------------
    with tab_acopio:
        items_en_bd = [m for m in filas_mat_activas if m.get("en_bd")]
        items_web = [m for m in filas_mat_activas if not m.get("en_bd")]

        col_ac1, col_ac2 = st.columns([1.9, 1.1])
        with col_ac1:
            st.markdown("##### 🛒 Lista de Compra de Materiales para el Mostrador y Almacén")
            st.caption("Solo incluye las partidas seleccionadas para compra (excluye canalizaciones o materiales ya existentes en obra):")

            # Banners informativos de procedencia
            col_sbd1, col_sbd2 = st.columns(2)
            with col_sbd1:
                st.success(f"✅ **{len(items_en_bd)} de {len(filas_mat_activas)} artículos en BD Oficial** (Obramat / Leroy)")
            with col_sbd2:
                if items_web:
                    st.warning(f"🌐 **{len(items_web)} artículos con Tarifa Web** (Enlaces directos abajo)")
                else:
                    st.info("🎯 **100% de materiales catalogados en almacén oficial**")

            # Tabla interactiva con Dónde Comprar, Ref SKU y Estado
            if filas_mat_activas:
                filas_display = []
                for m in filas_mat_activas:
                    c_nom = m.get("mat") or m.get("concepto") or m.get("nombre") or ""
                    c_cant = m.get("cant") or 1.0
                    c_unid = m.get("unid") or "ud"
                    c_pu = float(m.get("p_u") or 0.0)
                    c_sub = float(m.get("subtotal") or (float(c_cant) * c_pu))
                    prov = m.get("proveedor", "Obramat")
                    sku = m.get("sku", "S/Ref")
                    est = "✅ En BD" if m.get("en_bd") else "🌐 Tarifa Web"

                    filas_display.append({
                        "Estado": est,
                        "Cant.": c_cant,
                        "Unid.": c_unid,
                        "Denominación del Material": c_nom,
                        "Dónde Comprar (Proveedor)": prov,
                        "Ref. SKU": sku,
                        "P. Unit (€)": f"{c_pu:,.2f} €",
                        "Subtotal (€)": f"{c_sub:,.2f} €"
                    })
                st.dataframe(filas_display, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ No hay materiales seleccionados para compra (todo aportado por cliente o preexistente en obra).")

            # Mostrar aviso de materiales en obra si los hay
            if filas_mat_en_obra:
                st.markdown(f"""
                <div style="background-color:#f8fafc; border-left:4px solid #0284c7; padding:10px 14px; border-radius:4px; margin-top:8px; font-size:12.5px; color:#1e293b;">
                    <b>🏠 Materiales ya en obra o canalizados (NO comprar en almacén):</b><br/>
                    {' • '.join([f"<b>{m['mat']}</b> ({m['cant']} {m['unid']})" for m in filas_mat_en_obra])}
                </div>
                """, unsafe_allow_html=True)

            # Investigar en la Web y Guardar en BD para los artículos no registrados
            if items_web:
                with st.expander(f"🔍 Investigar Artículos con Tarifa Web ({len(items_web)}) y Guardar en tu Base de Datos", expanded=False):
                    st.markdown("<div style='font-size:12.5px; color:#475569;'>Haz clic en las tiendas para comprobar el precio real online y regístralo con 1 clic para que ya quede guardado en tu base de datos:</div>", unsafe_allow_html=True)
                    for idx_w, iw in enumerate(items_web):
                        col_iw1, col_iw2, col_iw3 = st.columns([2.5, 1.2, 1.3])
                        w_nom = iw.get("mat") or iw.get("material") or iw.get("concepto") or iw.get("nombre") or f"Artículo {idx_w+1}"
                        url_obr = iw.get("url_obramat") or f"https://www.obramat.es/catalogsearch/result/?q={urllib.parse.quote_plus(w_nom)}"
                        url_goo = iw.get("url_google") or f"https://www.google.com/search?q={urllib.parse.quote_plus('comprar material electrico ' + w_nom)}"
                        with col_iw1:
                            st.markdown(f"**{w_nom}**")
                        with col_iw2:
                            st.markdown(f"[🏪 Buscar en Obramat]({url_obr})")
                        with col_iw3:
                            st.markdown(f"[🔍 Buscar en Google]({url_goo})")

                    st.markdown("---")
                    st.markdown("###### ➕ Registrar Precio Real en tu Base de Datos Local:")
                    col_reg1, col_reg2, col_reg3, col_reg4 = st.columns([2.2, 1.0, 1.4, 0.9])
                    with col_reg1:
                        def_nom_w = items_web[0].get("mat") or items_web[0].get("material") or ""
                        reg_nom = st.text_input("Artículo:", value=def_nom_w, key=f"{key_prefix}_in_reg_mat_nom")
                    with col_reg2:
                        def_pu_w = float(items_web[0].get("p_u") or items_web[0].get("precio_unit") or 10.0)
                        reg_pu = st.number_input("Precio (€):", min_value=0.01, value=def_pu_w, step=0.5, key=f"{key_prefix}_in_reg_mat_pu")
                    with col_reg3:
                        reg_prov = st.selectbox("Tienda / Almacén:", ["Obramat", "Leroy Merlin", "Sumidelec", "Saltoki", "Electro Stocks", "Otro Almacén"], key=f"{key_prefix}_sel_reg_mat_prov")
                    with col_reg4:
                        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                        if st.button("💾 Guardar", key=f"{key_prefix}_btn_save_mat_bd"):
                            def_unid_w = items_web[0].get("unid") or "ud"
                            ok_g = guardar_material_personalizado(reg_nom, reg_pu, unidad=def_unid_w, proveedor=reg_prov)
                            if ok_g:
                                st.success(f"¡'{reg_nom}' guardado en tu base de datos!")
                                st.rerun()

            # Resumen de texto para WhatsApp
            lineas_texto_compra = []
            lista_para_pdf = filas_mat_activas if filas_mat_activas else [{"mat": f"Materiales normalizados de {modulo_nombre}", "cant": 1, "unid": "partida", "p_u": coste_mat, "proveedor": "Obramat"}]
            for idx, m in enumerate(lista_para_pdf):
                c_nom = m.get("mat") or m.get("concepto") or m.get("nombre") or f"Partida {idx+1}"
                c_cant = m.get("cant") or m.get("cantidad") or 1.0
                c_unid = m.get("unid") or m.get("unidad") or "ud"
                c_pu = m.get("p_u") or m.get("precio_ud") or m.get("precio") or 0.0
                c_sub = float(c_cant) * float(c_pu)
                c_prv = m.get("proveedor", "Almacén")
                lineas_texto_compra.append(f"• {c_cant} {c_unid} - {c_nom} [{c_prv}] (Aprox: {c_sub:,.2f} €)")

            if filas_mat_en_obra:
                lineas_texto_compra.append("\n[MATERIALES YA EXISTENTES EN OBRA / CANALIZADOS - NO COMPRAR]:")
                for m in filas_mat_en_obra:
                    lineas_texto_compra.append(f"• {m['cant']} {m['unid']} - {m['mat']} (En obra)")

            txt_lista_mostrador = "📦 *LISTA DE ACOPIO DE MATERIALES - BOLIMUR*\n" + f"Trabajo: {nom_obra_def}\n" + "---------------------------------------\n" + "\n".join(lineas_texto_compra) + f"\n---------------------------------------\nCoste Total Materiales Estimado: {coste_mat:,.2f} € (S/IVA)"
            with st.expander("📲 Ver Lista en Formato Texto para WhatsApp / Mostrador", expanded=False):
                st.text_area("Lista para enviar:", value=txt_lista_mostrador, height=180, key=f"{key_prefix}_txt_lista_compra")

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            try:
                pdf_bytes_acopio = pdf_comercial_cliente.generar_pdf_lista_materiales_almacen(
                    proyecto_info={"concepto": nom_obra_def, "instalador": "Instalador Autorizado REBT", "fecha": datetime.date.today().strftime("%d/%m/%Y")},
                    filas_materiales=lista_para_pdf,
                    coste_total_neto=coste_mat,
                    iva_pct=iva_pct
                )
                st.download_button(
                    label="📦 🖨️ Descargar Lista de Materiales en PDF (Imprimir para Almacén / Acopio)",
                    data=pdf_bytes_acopio,
                    file_name=f"Lista_Materiales_{nom_obra_def.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"{key_prefix}_btn_descarga_pdf_acopio",
                    use_container_width=True
                )
            except Exception as e_pdf_mat:
                st.info(f"PDF de acopio disponible: {e_pdf_mat}")

        with col_ac2:
            st.markdown("##### 💵 Calculadora de Anticipo Seguro")
            st.caption("Evita financiar la obra de tu propio bolsillo:")
            anticipo_mat = round(coste_mat * (1.0 + iva_pct / 100.0), 2)
            pct_anticipo_rec = round((coste_mat / base_autonomo * 100), 0) if base_autonomo > 0 else 40.0
            pct_anticipo_rec = max(35.0, min(50.0, pct_anticipo_rec))
            anticipo_recomendado = round(total_autonomo * (pct_anticipo_rec / 100.0), 2)

            st.markdown(f"""
            <div style="background-color:#f8fafc; border:1.5px solid #cbd5e1; border-radius:8px; padding:12px;">
                <div style="font-size:12.5px; color:#475569;"><b>Señal recomendada ({pct_anticipo_rec:.0f}%):</b></div>
                <div style="font-size:20px; font-weight:bold; color:#0369a1; margin:4px 0;">{anticipo_recomendado:,.2f} €</div>
                <div style="font-size:11.5px; color:#64748b; line-height:1.4;">
                    Cubre el <b>100% de la compra de materiales en almacén</b> ({coste_mat:,.2f} €). Pídelo al cliente antes de comprar el cable y los cuadros.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            txt_condicion_pago = (
                f"💳 *Condiciones de Pago Sugeridas:*\n"
                f"• Anticipo al aceptar (materiales): *{anticipo_recomendado:,.2f} €* ({pct_anticipo_rec:.0f}%)\n"
                f"• Resto a la entrega y puesta en marcha: *{total_autonomo - anticipo_recomendado:,.2f} €*"
            )
            st.text_area("Condiciones de cobro:", value=txt_condicion_pago, height=105, key=f"{key_prefix}_txt_cond_cobro")

    # ---------------------------------------------------------------------
    # TAB 4: GUARDAR, RECUPERAR, EDITAR Y DUPLICAR PRESUPUESTO
    # ---------------------------------------------------------------------
    with tab_guardar:
        col_g1, col_g2 = st.columns([1.5, 1.5])

        with col_g1:
            st.markdown("##### 💾 Guardar Presupuesto Actual")
            in_nom_pres = st.text_input("Nombre identificativo del Presupuesto:", value=nom_obra_def, key=f"{key_prefix}_in_nom_pres")
            in_cli_pres = st.text_input("Nombre / Teléfono del Cliente:", value=nom_cliente_def, key=f"{key_prefix}_in_cli_pres")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                in_fecha_pres = st.text_input("Fecha:", value=datetime.date.today().strftime("%d/%m/%Y"), key=f"{key_prefix}_in_f_pres")
            with col_f2:
                in_validez = st.number_input("Validez (días):", min_value=7, max_value=120, value=30, step=5, key=f"{key_prefix}_in_validez")

            sel_modo_guardar = st.radio("Tarifa a registrar por defecto:", ["Autónomo", "Empresa"], horizontal=True, key=f"{key_prefix}_rad_modo_g")
            tot_siva_g = base_autonomo if sel_modo_guardar == "Autónomo" else base_empresa
            tot_civa_g = total_autonomo if sel_modo_guardar == "Autónomo" else total_empresa

            if st.button("💾 Guardar en Base de Datos de Bolimur", type="primary", use_container_width=True, key=f"{key_prefix}_btn_guardar_bd"):
                datos_guardar = dict(datos_presupuesto)
                datos_guardar.update({
                    "margen_materiales_pct": margen_mat_pct,
                    "precio_hora_coste": precio_h_coste,
                    "horas_mano_obra": horas_mo,
                    "recargo_empresa_mo_pct": recargo_empresa_pct,
                    "margen_mo_auto_pct": margen_mo_auto_pct,
                    "base_empresa": base_empresa,
                    "total_empresa": total_empresa,
                    "base_autonomo": base_autonomo,
                    "total_autonomo": total_autonomo,
                    "sueldo_limpio_autonomo": sueldo_limpio_autonomo
                })
                ok, pid = guardar_presupuesto(
                    usuario_id=1,
                    cliente_id=None,
                    nombre_cliente=in_cli_pres,
                    nombre_presupuesto=in_nom_pres,
                    modulo_origen=modulo_nombre,
                    datos_presupuesto=datos_guardar,
                    estado="Pendiente",
                    total_sin_iva=tot_siva_g,
                    total_con_iva=tot_civa_g,
                    iva_pct=iva_pct,
                    modo_tarifa=sel_modo_guardar,
                    validez_dias=in_validez,
                    fecha_presupuesto=in_fecha_pres
                )
                if ok:
                    st.success(f"✅ ¡Presupuesto Nº #{pid} guardado con éxito! Ya puedes recuperarlo, editarlo o duplicarlo cuando quieras.")
                else:
                    st.error("Error al guardar el presupuesto en la base de datos.")

        with col_g2:
            st.markdown("##### 📂 Presupuestos Guardados en este Módulo")
            lista_guardados = listar_presupuestos(modulo_origen=modulo_nombre)
            if not lista_guardados:
                # Si no hay de este módulo, mostrar los generales
                lista_guardados = listar_presupuestos()

            if lista_guardados:
                opciones_pres = {f"#{p['id']} - {p['nombre_presupuesto']} ({p['nombre_cliente']}) - {p['total_con_iva']:,.2f} € [{p['estado']}]": p["id"] for p in lista_guardados}
                sel_p_recup = st.selectbox("Selecciona un presupuesto para recuperar o duplicar:", list(opciones_pres.keys()), key=f"{key_prefix}_sel_recup")
                id_elegido = opciones_pres[sel_p_recup]

                col_b_rec1, col_b_rec2, col_b_rec3 = st.columns(3)
                with col_b_rec1:
                    if st.button("📂 Cargar", use_container_width=True, key=f"{key_prefix}_btn_cargar_p"):
                        p_rec = cargar_presupuesto_por_id(id_elegido)
                        if p_rec:
                            st.session_state[f"presupuesto_cargado_{key_prefix}"] = p_rec
                            st.success(f"Presupuesto #{id_elegido} cargado. Revisa los parámetros modificables.")
                with col_b_rec2:
                    if st.button("📋 Duplicar", use_container_width=True, key=f"{key_prefix}_btn_dup_p"):
                        ok_d, id_d = duplicar_presupuesto(id_elegido, f"{sel_p_recup[:25]} (Copia)", "Nuevo Cliente")
                        if ok_d:
                            st.success(f"¡Presupuesto duplicado como #{id_d}!")
                            st.rerun()
                with col_b_rec3:
                    if st.button("🗑️ Borrar", use_container_width=True, key=f"{key_prefix}_btn_del_p"):
                        if eliminar_presupuesto(id_elegido):
                            st.warning(f"Presupuesto #{id_elegido} eliminado.")
                            st.rerun()

                # Si hay uno cargado en sesión, permitir edición de parámetros en vivo
                p_activo = st.session_state.get(f"presupuesto_cargado_{key_prefix}")
                if p_activo and p_activo.get("id") == id_elegido:
                    st.markdown("---")
                    st.markdown(f"###### ✏️ Editar Parámetros del Presupuesto #{p_activo['id']}:")
                    ed_col1, ed_col2 = st.columns(2)
                    with ed_col1:
                        nuevo_f = st.text_input("Fecha:", value=datetime.date.today().strftime("%d/%m/%Y"), key=f"{key_prefix}_ed_fecha")
                        nuevo_est = st.selectbox("Estado del presupuesto:", ["Pendiente", "Aceptado", "Terminado y Cobrado", "Rechazado"], index=0, key=f"{key_prefix}_ed_est")
                    with ed_col2:
                        nuevo_cli = st.text_input("Cliente:", value=p_activo.get("nombre_cliente", ""), key=f"{key_prefix}_ed_cli")
                        nuevo_tot = st.number_input("Total (IVA incl.):", value=float(p_activo.get("total_con_iva", 0.0)), step=50.0, key=f"{key_prefix}_ed_tot")

                    if st.button("💾 Guardar Cambios en este Presupuesto", type="secondary", use_container_width=True, key=f"{key_prefix}_btn_save_ed"):
                        up_ok = actualizar_presupuesto(id_elegido, {
                            "fecha_presupuesto": nuevo_f,
                            "estado": nuevo_est,
                            "nombre_cliente": nuevo_cli,
                            "total_con_iva": nuevo_tot,
                            "total_sin_iva": round(nuevo_tot / 1.21, 2)
                        })
                        if up_ok:
                            st.success(f"Presupuesto #{id_elegido} actualizado correctamente.")
                            st.rerun()
            else:
                st.info("Aún no tienes presupuestos guardados en este módulo. Pulsa el botón 'Guardar en Base de Datos' a la izquierda para registrar el primero.")
