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

import json
import datetime
import urllib.parse
from typing import Dict, Any, List, Optional
import streamlit as st

try:
    from modulos import db_manager
except ImportError:
    import db_manager


# =========================================================================
# 1. GESTIÓN DE MATERIALES PERSONALIZADOS EN BD
# =========================================================================

def guardar_material_personalizado(nombre: str, precio_coste: float, unidad: str = "ud", proveedor: str = "Obramat", categoria: str = "General") -> bool:
    """Guarda o actualiza un material y su precio de compra en la base de datos local SQLite."""
    try:
        conn = db_manager.obtener_conexion()
        cursor = conn.cursor()
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
    precio_h_coste_def = float(datos_presupuesto.get("precio_hora_coste", 35.0))
    recargo_emp_def = float(datos_presupuesto.get("recargo_empresa_mo_pct", 40.0))
    coste_tramitacion = float(datos_presupuesto.get("coste_tramitacion", 120.0))
    desplazamiento = float(datos_presupuesto.get("desplazamiento", 0.0))
    iva_pct = float(datos_presupuesto.get("iva_pct", 21.0))
    filas_materiales = datos_presupuesto.get("filas_materiales", [])
    nom_cliente_def = datos_presupuesto.get("cliente", "Cliente Particular")
    nom_obra_def = datos_presupuesto.get("concepto", f"Presupuesto de {modulo_nombre}")

    # Contenedor visual del panel comercial
    st.markdown("---")
    st.markdown(f"### 💼 Gestión Comercial, Balance y Auditor Financiero ({modulo_nombre})")
    st.caption("Herramienta de control financiero para el instalador de calle: ajusta tus márgenes, compara tarifas Empresa vs. Autónomo y audita ofertas del cliente.")

    # ---------------------------------------------------------------------
    # AJUSTES INTERACTIVOS DE MÁRGENES Y MANO DE OBRA (ESTILO VIVIENDA)
    # ---------------------------------------------------------------------
    with st.expander("⚙️ Ajustar Márgenes Comerciales y Mano de Obra en Tiempo Real", expanded=True):
        st.markdown("<div style='font-size:13.5px; color:#475569; margin-bottom:10px;'>Ajusta libremente tus márgenes y tu tarifa horaria para ver el impacto inmediato en el presupuesto, tus beneficios limpios y el semáforo comercial:</div>", unsafe_allow_html=True)
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
                max_value=120.0,
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
                <b>💡 Estrategia Modo Autónomo:</b> Al mantener el recargo MO en <b>{margen_mo_auto_pct:.0f}%</b>, garantizas cobrar el 100% de tus horas (<b>{horas_mo * precio_h_coste:,.2f} €</b>) y tu ganancia de materiales (<b>{coste_mat_orig * (margen_mat_pct / 100.0):,.2f} €</b>), ofreciendo un precio de calle que las constructoras no pueden igualar.
            </div>
            """, unsafe_allow_html=True)

    # Recálculo dinámico con los parámetros interactivos
    coste_mat = coste_mat_orig
    benef_mat = round(coste_mat * (margen_mat_pct / 100.0), 2)
    pvp_mat = round(coste_mat + benef_mat, 2)

    coste_mo_directo = round(horas_mo * precio_h_coste, 2)
    g_mo_empresa = round(coste_mo_directo * (recargo_empresa_pct / 100.0), 2)
    g_mo_autonomo = round(coste_mo_directo * (margen_mo_auto_pct / 100.0), 2)

    # Totales Modo Empresa
    base_empresa = round(pvp_mat + coste_mo_directo + g_mo_empresa + coste_tramitacion + desplazamiento, 2)
    iva_empresa = round(base_empresa * (iva_pct / 100.0), 2)
    total_empresa = round(base_empresa + iva_empresa, 2)

    # Totales Modo Autónomo (g_mo ajustable)
    base_autonomo = round(pvp_mat + coste_mo_directo + g_mo_autonomo + coste_tramitacion + desplazamiento, 2)
    iva_autonomo = round(base_autonomo * (iva_pct / 100.0), 2)
    total_autonomo = round(base_autonomo + iva_autonomo, 2)

    diferencia_ahorro = round(total_empresa - total_autonomo, 2)
    sueldo_limpio_autonomo = round(coste_mo_directo + g_mo_autonomo + benef_mat + coste_tramitacion, 2)

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

        # Tabla de desglose transparente interna
        st.markdown("##### 🔍 Desglose Partida a Partida (¿A dónde va cada euro?)")
        filas_balance = [
            {"Concepto Económico": "📦 1. Compra Materiales (Almacén)", "🏢 Empresa": f"{coste_mat:,.2f} €", "👤 Autónomo": f"{coste_mat:,.2f} €", "Diferencia": "0,00 €", "Destino": "Salida de caja a Obramat/Leroy"},
            {"Concepto Económico": f"📈 2. Beneficio s/ Materiales ({margen_mat_pct:.0f}%)", "🏢 Empresa": f"{benef_mat:,.2f} €", "👤 Autónomo": f"{benef_mat:,.2f} €", "Diferencia": "0,00 €", "Destino": "Ganancia limpia por suministrar material"},
            {"Concepto Económico": f"🔨 3. Tu Jornal Directo ({horas_mo:.1f}h x {precio_h_coste:.0f}€)", "🏢 Empresa": f"{coste_mo_directo:,.2f} €", "👤 Autónomo": f"{coste_mo_directo:,.2f} €", "Diferencia": "0,00 €", "Destino": "Tu sueldo profesional por trabajar"},
            {"Concepto Económico": f"🏢 4. Recargo Oficina Empresa ({recargo_empresa_pct:.0f}% vs {margen_mo_auto_pct:.0f}%)", "🏢 Empresa": f"{g_mo_empresa:,.2f} €", "👤 Autónomo": f"{g_mo_autonomo:,.2f} €", "Diferencia": f"-{g_mo_empresa - g_mo_autonomo:,.2f} €", "Destino": "Sobrecoste retirado para ganar al cliente"},
            {"Concepto Económico": "📋 5. Tramitación CIE / Boletín", "🏢 Empresa": f"{coste_tramitacion:,.2f} €", "👤 Autónomo": f"{coste_tramitacion:,.2f} €", "Diferencia": "0,00 €", "Destino": "Honorarios técnicos de legalización"},
        ]
        if desplazamiento > 0:
            filas_balance.append({"Concepto Económico": "🚗 6. Desplazamiento y Dietas", "🏢 Empresa": f"{desplazamiento:,.2f} €", "👤 Autónomo": f"{desplazamiento:,.2f} €", "Diferencia": "0,00 €", "Destino": "Combustible y vehículo"})

        st.dataframe(filas_balance, use_container_width=True, hide_index=True)

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
        col_ac1, col_ac2 = st.columns([1.8, 1.2])
        with col_ac1:
            st.markdown("##### 🛒 Lista de Compra de Materiales para el Mostrador")
            st.caption("Lista ordenada para enseñar en Obramat / Leroy Merlin o enviar por WhatsApp al almacén:")

            lineas_texto_compra = []
            if filas_materiales:
                for idx, m in enumerate(filas_materiales):
                    c_nom = m.get("mat") or m.get("concepto") or m.get("nombre") or f"Partida {idx+1}"
                    c_cant = m.get("cant") or m.get("cantidad") or 1.0
                    c_unid = m.get("unid") or m.get("unidad") or "ud"
                    c_pu = m.get("p_u") or m.get("precio_ud") or m.get("precio") or 0.0
                    c_sub = float(c_cant) * float(c_pu)
                    lineas_texto_compra.append(f"• {c_cant} {c_unid} - {c_nom} (Coste aprox: {c_sub:,.2f} €)")
            else:
                lineas_texto_compra.append(f"• Materiales generales normalizados de {modulo_nombre}: {coste_mat:,.2f} €")

            txt_lista_mostrador = "📦 *LISTA DE ACOPIO DE MATERIALES - BOLIMUR*\n" + f"Trabajo: {nom_obra_def}\n" + "---------------------------------------\n" + "\n".join(lineas_texto_compra) + f"\n---------------------------------------\nCoste Total Materiales Estimado: {coste_mat:,.2f} € (S/IVA)"
            st.text_area("Lista de Materiales:", value=txt_lista_mostrador, height=220, key=f"{key_prefix}_txt_lista_compra")

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
