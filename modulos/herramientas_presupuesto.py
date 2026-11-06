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


def interpretar_gasto_voz(texto: str) -> dict:
    """Extrae automáticamente concepto, comercio, importe y pagador de una frase hablada o escrita."""
    import re
    t = (texto or "").lower().strip()
    if not t:
        return {}

    # 1. Extraer importe
    m_imp = re.search(r'(\d+[\.,]?\d*)\s*(?:€|euros?|pavos?)', t)
    if not m_imp:
        m_imp = re.search(r'(?:por|de|importe|gastado|cuenta)\s*(\d+[\.,]?\d*)', t)
    if not m_imp:
        m_imp = re.search(r'\b(\d+[\.,]?\d*)\b', t)

    try:
        importe = float(m_imp.group(1).replace(',', '.')) if m_imp else 25.0
    except Exception:
        importe = 25.0

    # 2. Pagador
    if any(k in t for k in ['compañero', 'socio', 'lo pagó él', 'él', 'companero']):
        pagador = '👥 Mi Compañero'
    elif any(k in t for k in ['bote', 'caja', 'de la obra', 'común', 'comun']):
        pagador = '💳 Bote Común de la Obra'
    else:
        pagador = '🧑‍🔧 Yo (Titular)'

    # 3. Establecimiento / Centro comercial
    comercios_conocidos = [
        'repsol', 'cepsa', 'bp', 'galp', 'shell', 'plenoil', 'ballenoil',
        'obramat', 'bricomart', 'leroy merlin', 'leroy', 'brico depot', 'bricodepot', 'bauhaus', 
        'saltoki', 'peisa', 'sonepar', 'electro stocks', 'salvador escoda',
        'mercadona', 'carrefour', 'dia', 'lidl', 'mcdonalds', 'burger king'
    ]
    comercio = ''
    for c in comercios_conocidos:
        if c in t:
            comercio = c.title()
            break

    if not comercio:
        m_com = re.search(r'en\s+(?:el\s+|la\s+)?([a-záéíóúñ0-9\s]+?)(?:\s+y\s+|\s+por\s+|\s+de\s+|\s+lo\s+|$)', t)
        if m_com:
            comercio = m_com.group(1).strip().title()[:30]

    # 4. Tipo y Concepto
    if any(k in t for k in ['gasoil', 'gasolina', 'combustible', 'diesel', 'diésel', 'repostar', 'llenar']):
        icono = '⛽'
        concepto = 'Gasoil / Combustible'
    elif any(k in t for k in ['comida', 'comer', 'menu', 'menú', 'almuerzo', 'desayuno', 'cena', 'bocadillo', 'restaurante', 'bar']):
        icono = '🍽️'
        concepto = 'Comida / Menú de obra'
    elif any(k in t for k in ['parking', 'aparcamiento', 'ora', 'peaje', 'autopista', 'zona azul']):
        icono = '🅿️'
        concepto = 'Parking / Peaje'
    elif any(k in t for k in ['broca', 'espuma', 'disco', 'tornillo', 'taco', 'cinta', 'silicona', 'ferreteria', 'ferretería']):
        icono = '🔨'
        concepto = 'Consumibles / Ferretería'
    else:
        icono = '🧾'
        concepto = texto.strip().capitalize()[:40]

    return {
        'concepto': concepto,
        'comercio': comercio or 'Comercio local',
        'importe': importe,
        'pagador': pagador,
        'icono': icono,
        'fecha': datetime.date.today(),
        'notas': f'Dictado por voz: "{texto.strip()}"'
    }


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
    p_cargado = st.session_state.get(f"presupuesto_cargado_{key_prefix}")
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

    if p_cargado:
        d_c = p_cargado.get("datos", {})
        margen_mat_def = float(d_c.get("margen_materiales_pct", margen_mat_def))
        horas_mo_def = float(d_c.get("horas_mano_obra", horas_mo_def))
        precio_h_coste_def = float(d_c.get("precio_hora_coste", precio_h_coste_def))
        recargo_emp_def = float(d_c.get("recargo_empresa_mo_pct", recargo_emp_def))
        if "coste_tramitacion" in d_c:
            coste_tramitacion = float(d_c.get("coste_tramitacion", coste_tramitacion))
        if "desplazamiento" in d_c:
            desplazamiento = float(d_c.get("desplazamiento", desplazamiento))
        nom_cliente_def = p_cargado.get("nombre_cliente", nom_cliente_def)
        nom_obra_def = p_cargado.get("nombre_presupuesto", nom_obra_def)

    # Contenedor visual del panel comercial
    st.markdown("---")
    st.markdown(f"### 💼 Gestión Comercial, Balance y Auditor Financiero ({modulo_nombre})")
    st.caption("Herramienta de control financiero para el instalador de calle: ajusta tus márgenes, compara tarifas Empresa vs. Autónomo y audita ofertas del cliente.")

    if p_cargado:
        key_tks_check = f"{key_prefix}_lista_tickets_obra"
        n_tks = len(st.session_state.get(key_tks_check, []))
        tot_tks = sum(float(tk.get("importe", 0.0)) for tk in st.session_state.get(key_tks_check, []))
        with st.container(border=True):
            col_b_act1, col_b_act2 = st.columns([3.8, 1.2])
            with col_b_act1:
                st.markdown(f"📂 **Presupuesto Cargado:** `#{p_cargado['id']}` - **{p_cargado.get('nombre_presupuesto', '')}** | Cliente: **{p_cargado.get('nombre_cliente', '')}** | Estado: **{p_cargado.get('estado', 'Pendiente')}**")
                st.caption(f"Gastos de obra registrados: **{n_tks} tickets** ({tot_tks:,.2f} €). Puedes añadir más tickets o modificar partidas y guardar los cambios sobre esta misma obra.")
            with col_b_act2:
                if st.button("🔄 Cerrar / Nuevo", key=f"{key_prefix}_btn_cerrar_pres_cargado", use_container_width=True, help="Desvincula este presupuesto para empezar un cálculo nuevo"):
                    if f"presupuesto_cargado_{key_prefix}" in st.session_state:
                        del st.session_state[f"presupuesto_cargado_{key_prefix}"]
                    st.session_state[key_tks_check] = []
                    st.rerun()

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
        # GASTOS OPERATIVOS Y TICKETS DE OBRA (GASOIL, DIETAS, COMIDAS, PARKING, ETC.)
        # -----------------------------------------------------------------
        key_tickets_obra = f"{key_prefix}_lista_tickets_obra"
        if key_tickets_obra not in st.session_state:
            st.session_state[key_tickets_obra] = []

        with st.expander("🧾 Tickets y Gastos Operativos de Obra (Gasoil, Dietas, Comidas, Parking, etc.)", expanded=True):
            st.caption("Apunta los gastos reales de la jornada (gasoil, menús, parking, consumibles de ferretería...). Se deducirán del dinero cobrado antes del reparto entre vosotros:")

            # Lista de tickets registrados
            if st.session_state[key_tickets_obra]:
                st.markdown("###### 📋 Gastos Registrados en esta Obra:")
                for idx_tk, tk in enumerate(st.session_state[key_tickets_obra]):
                    with st.container(border=True):
                        col_tk1, col_tk2, col_tk3, col_tk4, col_tk5 = st.columns([2.5, 1.2, 1.5, 1.2, 0.6])
                        with col_tk1:
                            st.markdown(f"**{tk.get('icono', '🧾')} {tk.get('concepto', 'Gasto')}**")
                            comercio_txt = tk.get('comercio', '')
                            fecha_txt = tk.get('fecha', '')
                            notas_txt = tk.get('notas', '')
                            sub_info = []
                            if comercio_txt:
                                sub_info.append(f"🏢 {comercio_txt}")
                            if fecha_txt:
                                sub_info.append(f"📅 {fecha_txt}")
                            if sub_info:
                                st.caption(" | ".join(sub_info))
                            if notas_txt:
                                st.caption(f"📝 *{notas_txt}*")
                        with col_tk2:
                            st.markdown(f"**{float(tk.get('importe', 0.0)):,.2f} €**")
                        with col_tk3:
                            pagador_str = tk.get('pagador', 'Bote Común')
                            st.markdown(f"Pagó: **{pagador_str}**")
                        with col_tk4:
                            if tk.get('foto_b64'):
                                with st.popover("📷 Ver Foto Ticket"):
                                    st.image(f"data:image/jpeg;base64,{tk['foto_b64']}", caption=f"{tk.get('concepto')} - {tk.get('comercio', '')}")
                            else:
                                st.caption("Sin foto")
                        with col_tk5:
                            if st.button("🗑️", key=f"{key_prefix}_btn_del_tk_{idx_tk}", help="Eliminar este gasto"):
                                st.session_state[key_tickets_obra].pop(idx_tk)
                                st.rerun()

                if p_cargado:
                    col_sync1, col_sync2 = st.columns([3, 1.8])
                    with col_sync1:
                        st.caption(f"💾 Guardado activo en obra: **#{p_cargado['id']}** ({p_cargado.get('nombre_presupuesto')})")
                    with col_sync2:
                        if st.button("💾 Sincronizar Gastos en BD", key=f"{key_prefix}_btn_sync_tks_bd", use_container_width=True, help="Guarda los tickets actuales directamente en la base de datos de esta obra"):
                            d_sync = dict(p_cargado.get("datos", {}))
                            d_sync["lista_tickets_obra"] = st.session_state.get(key_tickets_obra, [])
                            d_sync["total_tickets_obra"] = sum(float(tk.get("importe", 0.0)) for tk in st.session_state.get(key_tickets_obra, []))
                            d_sync["total_adelantado_yo"] = sum(float(tk.get("importe", 0.0)) for tk in st.session_state.get(key_tickets_obra, []) if "Yo" in tk.get("pagador", ""))
                            d_sync["total_adelantado_comp"] = sum(float(tk.get("importe", 0.0)) for tk in st.session_state.get(key_tickets_obra, []) if "Compañero" in tk.get("pagador", ""))
                            actualizar_presupuesto(p_cargado["id"], {"datos": d_sync})
                            p_cargado["datos"] = d_sync
                            st.session_state[f"presupuesto_cargado_{key_prefix}"] = p_cargado
                            st.toast(f"✅ ¡{len(st.session_state.get(key_tickets_obra, []))} tickets sincronizados en la base de datos!", icon="💾")

            st.markdown("---")
            st.markdown("###### ➕ Registrar Nuevo Ticket o Gasto:")

            # 🎙️ Dictado por voz / Asistente IA
            col_v_txt, col_v_btn = st.columns([3.2, 1.2])
            with col_v_txt:
                frase_dictado = st.text_input(
                    "🎙️ Dicta o escribe tu gasto con tus propias palabras:",
                    placeholder="Ej: He gastado 35 euros de gasoil en Repsol y lo pagué yo",
                    key=f"{key_prefix}_input_dictado_gasto"
                )
            with col_v_btn:
                btn_interpretar = st.button("🤖 Rellenar con IA", key=f"{key_prefix}_btn_interpretar_gasto", help="Analiza la frase y rellena el importe, comercio, categoría y quién pagó", use_container_width=True)

            if btn_interpretar and frase_dictado.strip():
                gasto_ia = interpretar_gasto_voz(frase_dictado)
                if gasto_ia:
                    st.session_state[f"{key_prefix}_tk_in_concepto"] = gasto_ia.get("concepto", "Gasto de Obra")
                    st.session_state[f"{key_prefix}_tk_in_comercio"] = gasto_ia.get("comercio", "")
                    st.session_state[f"{key_prefix}_tk_in_importe"] = float(gasto_ia.get("importe", 25.0))
                    st.session_state[f"{key_prefix}_tk_in_pagador"] = gasto_ia.get("pagador", "🧑‍🔧 Yo (Titular)")
                    st.session_state[f"{key_prefix}_tk_in_notas"] = gasto_ia.get("notas", "")
                    st.success(f"✅ Gasto interpretado: {gasto_ia.get('concepto')} ({gasto_ia.get('importe'):,.2f} € en {gasto_ia.get('comercio')})")
                    st.rerun()

            # Botones de categorías rápidas para facilitar la introducción en furgoneta
            col_cat1, col_cat2, col_cat3, col_cat4 = st.columns(4)
            with col_cat1:
                if st.button("⛽ Gasoil Furgoneta", key=f"{key_prefix}_cat_gasoil", use_container_width=True):
                    st.session_state[f"{key_prefix}_tk_in_concepto"] = "Gasoil / Combustible furgoneta"
                    st.session_state[f"{key_prefix}_tk_in_comercio"] = "Repsol / Gasolinera"
                    st.session_state[f"{key_prefix}_tk_in_importe"] = 35.0
                    st.rerun()
            with col_cat2:
                if st.button("🍽️ Menús Comida", key=f"{key_prefix}_cat_comida", use_container_width=True):
                    st.session_state[f"{key_prefix}_tk_in_concepto"] = "Comida / Menú del día en obra"
                    st.session_state[f"{key_prefix}_tk_in_comercio"] = "Bar / Restaurante"
                    st.session_state[f"{key_prefix}_tk_in_importe"] = 24.0
                    st.rerun()
            with col_cat3:
                if st.button("🅿️ Parking / Peaje", key=f"{key_prefix}_cat_parking", use_container_width=True):
                    st.session_state[f"{key_prefix}_tk_in_concepto"] = "Ticket Parking / Peaje ORA"
                    st.session_state[f"{key_prefix}_tk_in_comercio"] = "Parking Centro"
                    st.session_state[f"{key_prefix}_tk_in_importe"] = 8.50
                    st.rerun()
            with col_cat4:
                if st.button("🔨 Ferretería / Brocas", key=f"{key_prefix}_cat_ferreteria", use_container_width=True):
                    st.session_state[f"{key_prefix}_tk_in_concepto"] = "Consumibles / Broca / Espuma"
                    st.session_state[f"{key_prefix}_tk_in_comercio"] = "Obramat / Bricomart"
                    st.session_state[f"{key_prefix}_tk_in_importe"] = 15.0
                    st.rerun()

            # Campos detallados del gasto
            col_f1, col_f2, col_f3 = st.columns([1.5, 2.0, 1.5])
            with col_f1:
                tk_fecha = st.date_input("📅 Fecha del Gasto:", value=datetime.date.today(), key=f"{key_prefix}_tk_in_fecha")
            with col_f2:
                tk_comercio = st.text_input(
                    "🏢 Centro Comercial / Comercio / Bar:",
                    value=st.session_state.get(f"{key_prefix}_tk_in_comercio", ""),
                    placeholder="Ej: Obramat, Repsol, Bar El Cruce, Leroy Merlin...",
                    key=f"{key_prefix}_tk_in_comercio"
                )
            with col_f3:
                tk_importe = st.number_input(
                    "💶 Importe (€):",
                    min_value=0.0,
                    value=float(st.session_state.get(f"{key_prefix}_tk_in_importe", 25.0)),
                    step=5.0,
                    key=f"{key_prefix}_tk_in_importe"
                )

            col_c1, col_c2 = st.columns([2.5, 2.0])
            with col_c1:
                tk_concepto = st.text_input(
                    "📝 Concepto / Motivo del gasto:",
                    value=st.session_state.get(f"{key_prefix}_tk_in_concepto", "Gasoil furgoneta"),
                    placeholder="Ej: Gasoil furgoneta, Menú del día 2 personas, Broca SDS...",
                    key=f"{key_prefix}_tk_in_concepto"
                )
            with col_c2:
                pagador_default = st.session_state.get(f"{key_prefix}_tk_in_pagador", "💳 Bote Común de la Obra")
                pagador_opts = ["💳 Bote Común de la Obra", "🧑‍🔧 Yo (Titular)", "👥 Mi Compañero"]
                idx_pag_def = pagador_opts.index(pagador_default) if pagador_default in pagador_opts else 0
                tk_pagador = st.selectbox(
                    "👤 ¿Quién adelantó el dinero?",
                    pagador_opts,
                    index=idx_pag_def,
                    key=f"{key_prefix}_tk_in_pagador",
                    help="Si lo pagó uno de los dos de su bolsillo, el sistema le devolverá este dinero antes de repartir los beneficios."
                )

            col_sub_not, col_sub_fot = st.columns([2.5, 2.0])
            with col_sub_not:
                tk_notas = st.text_area(
                    "📋 Notas / Observaciones (opcional):",
                    value=st.session_state.get(f"{key_prefix}_tk_in_notas", ""),
                    placeholder="Ej: Ticket guardado para desgravar IVA / Factura pendiente con CIF de empresa...",
                    height=70,
                    key=f"{key_prefix}_tk_in_notas"
                )
            with col_sub_fot:
                tk_foto = st.file_uploader(
                    "📷 Subir Foto del Ticket o Factura (opcional):",
                    type=["jpg", "jpeg", "png"],
                    key=f"{key_prefix}_upload_ticket"
                )

            btn_add_tk = st.button("➕ Añadir Gasto a la Obra", type="primary", use_container_width=True, key=f"{key_prefix}_btn_guardar_gasto")
            if btn_add_tk:
                final_concepto = tk_concepto.strip() if tk_concepto.strip() else (f"Gasto en {tk_comercio.strip()}" if tk_comercio.strip() else "Gasto Operativo de Obra")
                if tk_importe > 0:
                    foto_b64 = None
                    if tk_foto is not None:
                        try:
                            foto_b64 = base64.b64encode(tk_foto.read()).decode("utf-8")
                        except Exception:
                            pass

                    icono_g = "⛽" if any(k in final_concepto.lower() for k in ["gasoil", "gasolina", "combustible"]) else (
                        "🍽️" if any(k in final_concepto.lower() for k in ["comida", "menu", "almuerzo", "cena", "bocadillo"]) else (
                            "🅿️" if any(k in final_concepto.lower() for k in ["parking", "aparcamiento", "ora", "peaje"]) else (
                                "🔨" if any(k in final_concepto.lower() for k in ["broca", "espuma", "disco", "herramienta"]) else "🧾"
                            )
                        )
                    )
                    fecha_str = tk_fecha.strftime("%d/%m/%Y") if hasattr(tk_fecha, "strftime") else str(tk_fecha)
                    st.session_state[key_tickets_obra].append({
                        "concepto": final_concepto,
                        "comercio": tk_comercio.strip() if tk_comercio.strip() else "Comercio local",
                        "importe": float(tk_importe),
                        "pagador": tk_pagador,
                        "fecha": fecha_str,
                        "notas": tk_notas.strip(),
                        "icono": icono_g,
                        "foto_b64": foto_b64
                    })
                    st.success(f"✅ Gasto '{final_concepto}' de {tk_importe:,.2f} € guardado correctamente.")
                    st.rerun()
                else:
                    st.warning("⚠️ El importe del gasto debe ser mayor a 0,00 €.")

        total_tickets_obra = sum(float(tk.get("importe", 0.0)) for tk in st.session_state.get(key_tickets_obra, []))
        total_adelantado_yo = sum(float(tk.get("importe", 0.0)) for tk in st.session_state.get(key_tickets_obra, []) if "Yo" in tk.get("pagador", ""))
        total_adelantado_comp = sum(float(tk.get("importe", 0.0)) for tk in st.session_state.get(key_tickets_obra, []) if "Compañero" in tk.get("pagador", ""))

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

            # Gastos duros de la obra: Materiales almacén + Portes + Tasas + Tickets Varios
            gastos_duros_obra = round(coste_mat + desplazamiento_auto + coste_tramitacion_auto + total_tickets_obra, 2)
            # Bote limpio a repartir tras pagar materiales, gasolina, tasas y tickets
            bote_limpio_obra = round(base_autonomo - gastos_duros_obra, 2)

            h_reloj = round(horas_mo / 2.0, 1)

            if "A Medias" in sel_modo_reparto:
                beneficio_mitad = round(bote_limpio_obra / 2.0, 2)
                pago_tu = round(beneficio_mitad + total_adelantado_yo, 2)
                pago_comp = round((bote_limpio_obra - beneficio_mitad) + total_adelantado_comp, 2)
                modo_rep_txt = "⚖️ 50% / 50% A Medias (Socios)"
            else:
                p_hora_comp = float(st.session_state.get(f"{key_prefix}_p_hora_comp", 20.0))
                sueldo_comp = round(h_reloj * p_hora_comp, 2)
                pago_comp = round(sueldo_comp + total_adelantado_comp, 2)
                pago_tu = round((bote_limpio_obra - sueldo_comp) + total_adelantado_yo, 2)
                modo_rep_txt = f"🧑‍🔧 Ayudante por horas ({p_hora_comp:.0f} €/h)"

            r_hora_tu = round((pago_tu - total_adelantado_yo) / h_reloj, 2) if h_reloj > 0 else 0.0
            r_hora_comp = round((pago_comp - total_adelantado_comp) / h_reloj, 2) if h_reloj > 0 else 0.0

            with st.container(border=True):
                st.markdown(f"""
                <div style="background-color:#f0fdf4; border-left:4px solid #16a34a; padding:10px 14px; border-radius:4px; margin-bottom:12px; font-size:13px; color:#14532d;">
                    <b>📊 Balance de Obra en Pareja:</b> Para esta obra se facturan <b>{horas_mo:.1f} horas de mano de obra</b> al cliente, pero al ir los 2 se termina en <b>{h_reloj:.1f} horas de reloj</b>.<br/>
                    <b>Deducción de Gastos ({gastos_duros_obra:,.2f} €):</b> Materiales almacén (<b>{coste_mat:,.2f} €</b>) + Portes (<b>{desplazamiento_auto:,.2f} €</b>) + Tasas (<b>{coste_tramitacion_auto:,.2f} €</b>) + Tickets/Dietas (<b>{total_tickets_obra:,.2f} €</b>).<br/>
                    El <b>bote limpio de {bote_limpio_obra:,.2f} €</b> se liquida en modalidad: <b>{modo_rep_txt}</b>.
                </div>
                """, unsafe_allow_html=True)

                col_rc1, col_rc2, col_rc3, col_rc4 = st.columns(4)
                with col_rc1:
                    st.metric("🧾 Gastos Deducidos", f"{gastos_duros_obra:,.2f} €", help="Materiales de compra + Vehículo/Portes + Tasas + Tickets dietas/gasoil")
                    st.caption(f"Mat: {coste_mat:,.2f}€ | Tickets: {total_tickets_obra:,.2f}€")
                with col_rc2:
                    st.metric("💰 Bote Neto Limpio", f"{bote_limpio_obra:,.2f} €", help="Total disponible para repartir entre ambos tras pagar todos los gastos")
                    st.caption(f"Tiempo obra: {h_reloj:.1f}h de reloj")
                with col_rc3:
                    txt_det_tu = f"Beneficio: {pago_tu - total_adelantado_yo:,.2f}€" + (f" + {total_adelantado_yo:,.2f}€ ticket" if total_adelantado_yo > 0 else "")
                    st.metric("🧑‍🔧 Tu Cobro Total", f"{pago_tu:,.2f} €", delta=f"{r_hora_tu:,.2f} €/h real")
                    st.caption(txt_det_tu)
                with col_rc4:
                    txt_det_comp = f"Beneficio: {pago_comp - total_adelantado_comp:,.2f}€" + (f" + {total_adelantado_comp:,.2f}€ ticket" if total_adelantado_comp > 0 else "")
                    st.metric("👥 Cobro Compañero", f"{pago_comp:,.2f} €", delta=f"{r_hora_comp:,.2f} €/h real")
                    st.caption(txt_det_comp)

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
        p_activo = st.session_state.get(f"presupuesto_cargado_{key_prefix}")
        col_g1, col_g2 = st.columns([1.5, 1.5])

        with col_g1:
            if p_activo:
                st.markdown(f"##### 🔄 Obra Activa: Presupuesto #{p_activo['id']}")
                st.caption(f"Estás trabajando sobre **'{p_activo.get('nombre_presupuesto')}'** de **{p_activo.get('nombre_cliente')}**. Puedes actualizarlo directamente con nuevos gastos o crear una copia.")
            else:
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
                "sueldo_limpio_autonomo": sueldo_limpio_autonomo,
                "lista_tickets_obra": st.session_state.get(key_tickets_obra, []),
                "secuencia_partidas": st.session_state.get(key_sec_part, ["mat", "mo", "cie", "desp"]),
                "dict_partidas_extras": st.session_state.get(key_dict_extra, {}),
                "lista_materiales": st.session_state.get(key_lista_mat, []),
                "modo_cuadrilla": st.session_state.get(f"{key_prefix}_sel_cuadrilla", "1 Oficial (Trabajo yo solo)"),
                "modo_reparto": st.session_state.get(f"{key_prefix}_sel_modo_reparto", "Al 50% Limpio (A medias tras deducir gastos/tickets)"),
                "p_hora_comp": float(st.session_state.get(f"{key_prefix}_p_hora_comp", 20.0)),
                "inc_desp": inc_desp,
                "desplazamiento": float(desplazamiento),
                "inc_cie": inc_cie,
                "coste_tramitacion": float(coste_tramitacion),
                "total_tickets_obra": float(total_tickets_obra),
                "total_adelantado_yo": float(total_adelantado_yo),
                "total_adelantado_comp": float(total_adelantado_comp)
            })

            if p_activo:
                if st.button(f"🔄 Actualizar Presupuesto #{p_activo['id']} con Gastos y Partidas", type="primary", use_container_width=True, key=f"{key_prefix}_btn_act_p_bd"):
                    up_ok = actualizar_presupuesto(p_activo["id"], {
                        "nombre_presupuesto": in_nom_pres,
                        "nombre_cliente": in_cli_pres,
                        "fecha_presupuesto": in_fecha_pres,
                        "validez_dias": in_validez,
                        "modo_tarifa": sel_modo_guardar,
                        "total_sin_iva": tot_siva_g,
                        "total_con_iva": tot_civa_g,
                        "datos": datos_guardar
                    })
                    if up_ok:
                        p_activo["nombre_presupuesto"] = in_nom_pres
                        p_activo["nombre_cliente"] = in_cli_pres
                        p_activo["total_sin_iva"] = tot_siva_g
                        p_activo["total_con_iva"] = tot_civa_g
                        p_activo["datos"] = datos_guardar
                        st.session_state[f"presupuesto_cargado_{key_prefix}"] = p_activo
                        st.success(f"✅ ¡Presupuesto #{p_activo['id']} actualizado con éxito! Se han guardado todos los gastos ({len(st.session_state.get(key_tickets_obra, []))} tickets) y cambios económicos.")
                    else:
                        st.error("Error al actualizar el presupuesto.")

                st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
                if st.button("💾 Guardar como NUEVA Copia / Versión", type="secondary", use_container_width=True, key=f"{key_prefix}_btn_guardar_nuevo_bd"):
                    ok_g, pid = guardar_presupuesto(
                        usuario_id=1,
                        cliente_id=None,
                        nombre_cliente=in_cli_pres,
                        nombre_presupuesto=f"{in_nom_pres} (Copia)",
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
                    if ok_g:
                        p_rec_n = cargar_presupuesto_por_id(pid)
                        if p_rec_n:
                            st.session_state[f"presupuesto_cargado_{key_prefix}"] = p_rec_n
                        st.success(f"✅ ¡Guardado como nuevo presupuesto Nº #{pid}!")
                        st.rerun()
                    else:
                        st.error("Error al guardar nueva copia.")
            else:
                if st.button("💾 Guardar en Base de Datos de Bolimur", type="primary", use_container_width=True, key=f"{key_prefix}_btn_guardar_bd"):
                    ok_g, pid = guardar_presupuesto(
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
                    if ok_g:
                        p_rec_n = cargar_presupuesto_por_id(pid)
                        if p_rec_n:
                            st.session_state[f"presupuesto_cargado_{key_prefix}"] = p_rec_n
                        st.success(f"✅ ¡Presupuesto Nº #{pid} guardado con éxito! Ha quedado vinculado para que puedas añadir gastos y tickets en cualquier momento.")
                        st.rerun()
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
                            d_rec = p_rec.get("datos", {})
                            st.session_state[key_tickets_obra] = list(d_rec.get("lista_tickets_obra", []))
                            st.session_state[key_sec_part] = list(d_rec.get("secuencia_partidas", ["mat", "mo", "cie", "desp"]))
                            st.session_state[key_dict_extra] = dict(d_rec.get("dict_partidas_extras", {}))
                            if d_rec.get("lista_materiales"):
                                st.session_state[key_lista_mat] = list(d_rec["lista_materiales"])
                                st.session_state[key_mat_hash] = curr_mat_hash
                                if f"{key_prefix}_editor_materiales_interactivo" in st.session_state:
                                    del st.session_state[f"{key_prefix}_editor_materiales_interactivo"]
                            if "modo_cuadrilla" in d_rec:
                                st.session_state[f"{key_prefix}_sel_cuadrilla"] = d_rec["modo_cuadrilla"]
                            if "modo_reparto" in d_rec:
                                st.session_state[f"{key_prefix}_sel_modo_reparto"] = d_rec["modo_reparto"]
                            if "p_hora_comp" in d_rec:
                                st.session_state[f"{key_prefix}_p_hora_comp"] = float(d_rec["p_hora_comp"])
                            if "margen_materiales_pct" in d_rec:
                                st.session_state[f"{key_prefix}_slider_margen_mat"] = float(d_rec["margen_materiales_pct"])
                            if "precio_hora_coste" in d_rec:
                                st.session_state[f"{key_prefix}_num_precio_hora"] = float(d_rec["precio_hora_coste"])
                            if "horas_mano_obra" in d_rec:
                                st.session_state[f"{key_prefix}_num_horas_mo"] = float(d_rec["horas_mano_obra"])
                            if "recargo_empresa_mo_pct" in d_rec:
                                st.session_state[f"{key_prefix}_slider_recargo_emp"] = float(d_rec["recargo_empresa_mo_pct"])
                            if "margen_mo_auto_pct" in d_rec:
                                st.session_state[f"{key_prefix}_slider_margen_auto"] = float(d_rec["margen_mo_auto_pct"])
                            if p_rec.get("nombre_presupuesto"):
                                st.session_state[f"{key_prefix}_in_nom_pres"] = p_rec["nombre_presupuesto"]
                            if p_rec.get("nombre_cliente"):
                                st.session_state[f"{key_prefix}_in_cli_pres"] = p_rec["nombre_cliente"]
                            st.success(f"Presupuesto #{id_elegido} cargado con éxito. Se han recuperado todos los materiales, gastos y configuración de cuadrilla.")
                            st.rerun()
                with col_b_rec2:
                    if st.button("📋 Duplicar", use_container_width=True, key=f"{key_prefix}_btn_dup_p"):
                        ok_d, id_d = duplicar_presupuesto(id_elegido, f"{sel_p_recup[:25]} (Copia)", "Nuevo Cliente")
                        if ok_d:
                            st.success(f"¡Presupuesto duplicado como #{id_d}!")
                            st.rerun()
                with col_b_rec3:
                    if st.button("🗑️ Borrar", use_container_width=True, key=f"{key_prefix}_btn_del_p"):
                        if eliminar_presupuesto(id_elegido):
                            if p_activo and p_activo.get("id") == id_elegido:
                                if f"presupuesto_cargado_{key_prefix}" in st.session_state:
                                    del st.session_state[f"presupuesto_cargado_{key_prefix}"]
                                st.session_state[key_tickets_obra] = []
                            st.warning(f"Presupuesto #{id_elegido} eliminado.")
                            st.rerun()

                # Si hay uno cargado en sesión, permitir edición de parámetros en vivo
                if p_activo and p_activo.get("id") == id_elegido:
                    st.markdown("---")
                    st.markdown(f"###### ✏️ Editar Estado y Cliente del Presupuesto #{p_activo['id']}:")
                    ed_col1, ed_col2 = st.columns(2)
                    with ed_col1:
                        nuevo_f = st.text_input("Fecha:", value=datetime.date.today().strftime("%d/%m/%Y"), key=f"{key_prefix}_ed_fecha")
                        nuevo_est = st.selectbox("Estado del presupuesto:", ["Pendiente", "Aceptado", "Terminado y Cobrado", "Rechazado"], index=0, key=f"{key_prefix}_ed_est")
                    with ed_col2:
                        nuevo_cli = st.text_input("Cliente:", value=p_activo.get("nombre_cliente", ""), key=f"{key_prefix}_ed_cli")
                        nuevo_tot = st.number_input("Total (IVA incl.):", value=float(p_activo.get("total_con_iva", 0.0)), step=50.0, key=f"{key_prefix}_ed_tot")

                    if st.button("💾 Guardar Cambios Rápidos", type="secondary", use_container_width=True, key=f"{key_prefix}_btn_save_ed"):
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
