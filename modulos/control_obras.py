# -*- coding: utf-8 -*-
"""
Módulo de Control y Planificación de Obras, Calendario y Cuadrilla de Instaladores.
Permite gestionar todos los proyectos habilitados, fechas de ejecución, asignación
de cuadrilla (Yo solo vs. Con mi compañero), tickets de obra y balances limpios.
"""

import streamlit as st
import datetime
import json
import base64
from typing import List, Dict, Any, Optional

from modulos import db_manager, auth_manager
from modulos.herramientas_presupuesto import (
    listar_presupuestos,
    cargar_presupuesto_por_id,
    actualizar_presupuesto,
    eliminar_presupuesto,
    guardar_presupuesto
)


def asegurar_columnas_control_obras():
    """Garantiza que la tabla SQLite disponga de las columnas necesarias para el planning."""
    try:
        conn = db_manager.obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(presupuestos_guardados)")
        cols = [r[1] for r in cursor.fetchall()]
        nuevas = [
            ("fecha_ejecucion", "TEXT"),
            ("asignado_a", "TEXT"),
            ("notas_planificacion", "TEXT"),
            ("prioridad", "TEXT")
        ]
        for col_name, col_type in nuevas:
            if col_name not in cols:
                cursor.execute(f"ALTER TABLE presupuestos_guardados ADD COLUMN {col_name} {col_type}")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al verificar columnas de control de obras: {e}")


def parsear_fecha_segura(fecha_str: str) -> Optional[datetime.date]:
    """Convierte cadenas en formatos DD/MM/YYYY o YYYY-MM-DD a objeto datetime.date."""
    if not fecha_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(fecha_str.strip()[:10], fmt).date()
        except Exception:
            continue
    return None


def obtener_mapa_redireccion_modulo(modulo_origen: str) -> str:
    """Mapea el nombre del módulo del presupuesto a la opción del menú lateral de Bolimur."""
    mod_lower = modulo_origen.lower()
    if "di" in mod_lower or "derivaci" in mod_lower:
        return "🔌 Derivación Individual (DI)"
    elif "irve" in mod_lower or "recarga" in mod_lower:
        return "🚗 Línea Recarga (IRVE)"
    elif "lga" in mod_lower:
        return "⚡ Línea General (LGA)"
    elif "vivienda" in mod_lower:
        return "🏡 Presupuesto Vivienda"
    elif "autónomo" in mod_lower or "autonomo" in mod_lower:
        return "🧑‍🔧 Presupuesto Autónomo"
    elif "previsi" in mod_lower or "pt" in mod_lower:
        return "🏢 Previsión de Cargas (Pt)"
    elif "rápido" in mod_lower or "rapido" in mod_lower or "cdt" in mod_lower:
        return "🧮 Cálculo Rápido (CDT & Icc)"
    elif "solar" in mod_lower or "foto" in mod_lower:
        return "☀️ Solar Fotovoltaica"
    elif "mtd" in mod_lower or "memoria" in mod_lower:
        return "🏛️ Memoria Técnica (MTD 30)"
    elif "unifilar" in mod_lower:
        return "📸 Unifilar por Foto (IA)"
    return "🔌 Derivación Individual (DI)"


def renderizar():
    """Punto de entrada principal de la vista de Control de Obras y Planificación."""
    asegurar_columnas_control_obras()

    st.markdown("""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-left: 5px solid #0284c7; padding: 16px 20px; border-radius: 10px; margin-bottom: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        <h2 style="margin:0 0 6px 0; color: #38bdf8; font-size: 24px; font-weight: 800; display:flex; align-items:center; gap:10px;">
            <span>📅</span> Control de Obras, Calendario y Planificación de Cuadrilla
        </h2>
        <div style="color: #cbd5e1; font-size: 14px; line-height: 1.5;">
            Gestiona todas tus obras dadas de alta, controla las <b>fechas de ejecución programadas</b>, planifica el trabajo entre <b>tú y tu compañero</b>, y supervisa los gastos reales y el reparto neto en cada trabajo.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Carga de todas las obras registradas
    todas_obras = listar_presupuestos()

    # Métricas Globales
    n_total = len(todas_obras)
    n_activas = sum(1 for o in todas_obras if o.get("estado") in ("Pendiente", "Aceptado", "En Ejecución"))
    n_cuadrilla = sum(1 for o in todas_obras if "2" in str(o.get("asignado_a", "")) or "Compañero" in str(o.get("asignado_a", "")))
    n_terminadas = sum(1 for o in todas_obras if "Terminad" in str(o.get("estado", "")))

    vol_total_presup = sum(float(o.get("total_con_iva", 0.0)) for o in todas_obras if o.get("estado") != "Rechazado")
    total_gastos_obra = 0.0
    for o in todas_obras:
        d = o.get("datos", {})
        total_gastos_obra += float(d.get("total_tickets_obra", 0.0))

    # KPIs Superiores
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("📋 Total Obras", n_total)
    with k2:
        st.metric("🟢 En Curso / Activas", n_activas)
    with k3:
        st.metric("👥 Con Compañero", n_cuadrilla)
    with k4:
        st.metric("💰 Volumen (€)", f"{vol_total_presup:,.0f} €")
    with k5:
        st.metric("🧾 Gastos / Tickets Ded.", f"{total_gastos_obra:,.2f} €")

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # Pestañas de Gestión
    tab_panel, tab_calendario, tab_nueva = st.tabs([
        "📋 Panel de Obras y Seguimiento",
        "🗓️ Calendario & Agenda de Cuadrilla",
        "➕ Dar de Alta Nueva Obra / Aviso"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: PANEL DE OBRAS Y SEGUIMIENTO
    # -------------------------------------------------------------------------
    with tab_panel:
        col_fil1, col_fil2, col_fil3 = st.columns([2.5, 2, 2])
        with col_fil1:
            filtro_buscar = st.text_input("🔍 Buscar por obra o cliente:", placeholder="Ej: D. Manuel, reforma cocina, DI...", key="co_filtro_buscar")
        with col_fil2:
            filtro_estado = st.selectbox(
                "Filtrar por Estado:",
                ["Todos los Estados", "🟢 En Ejecución / Aceptados", "🟡 Pendientes", "🔵 Terminados y Cobrados", "🔴 Rechazados"],
                key="co_filtro_estado"
            )
        with col_fil3:
            filtro_cuad = st.selectbox(
                "Filtrar por Cuadrilla:",
                ["Todos los Equipos", "👥 Con Mi Compañero (2 Personas)", "🧑‍🔧 Solo Yo (1 Persona)"],
                key="co_filtro_cuad"
            )

        # Aplicar filtros
        obras_filtradas = []
        for o in todas_obras:
            # Filtro texto
            if filtro_buscar.strip():
                txt_b = filtro_buscar.strip().lower()
                if txt_b not in o.get("nombre_presupuesto", "").lower() and txt_b not in o.get("nombre_cliente", "").lower():
                    continue

            # Filtro estado
            est = o.get("estado", "Pendiente")
            if "En Ejecución" in filtro_estado and est not in ("En Ejecución", "Aceptado"):
                continue
            elif "Pendientes" in filtro_estado and est != "Pendiente":
                continue
            elif "Terminados" in filtro_estado and "Terminado" not in est:
                continue
            elif "Rechazados" in filtro_estado and est != "Rechazado":
                continue

            # Filtro cuadrilla
            asig = o.get("asignado_a", "")
            if "Con Mi Compañero" in filtro_cuad and ("2" not in asig and "Compañero" not in asig):
                continue
            elif "Solo Yo" in filtro_cuad and ("Solo Yo" not in asig and "1" not in asig):
                continue

            obras_filtradas.append(o)

        if not obras_filtradas:
            st.info("ℹ️ No hay obras que coincidan con los filtros seleccionados. Puedes dar de alta una nueva obra en la pestaña **'➕ Dar de Alta Nueva Obra / Aviso'** o desde cualquier módulo de cálculo.")
        else:
            st.markdown(f"<div style='font-size:13.5px; color:#64748b; margin-bottom:12px;'>Mostrando <b>{len(obras_filtradas)}</b> obras registradas:</div>", unsafe_allow_html=True)

            hoy = datetime.date.today()

            for obra in obras_filtradas:
                oid = obra["id"]
                nom_p = obra.get("nombre_presupuesto", f"Obra #{oid}")
                cli = obra.get("nombre_cliente", "Cliente")
                mod_orig = obra.get("modulo_origen", "Cálculo")
                est = obra.get("estado", "Pendiente")
                tot_civa = float(obra.get("total_con_iva", 0.0))
                tot_siva = float(obra.get("total_sin_iva", 0.0))
                f_crea = obra.get("fecha_presupuesto") or obra.get("fecha_creacion", "")[:10]
                f_ejec_str = obra.get("fecha_ejecucion", "")
                f_ejec_dt = parsear_fecha_segura(f_ejec_str)
                asig = obra.get("asignado_a", "👥 Con Mi Compañero (Cuadrilla de 2)")
                notas_p = obra.get("notas_planificacion", "")
                datos_int = obra.get("datos", {})

                # Cálculo de días restantes
                if f_ejec_dt:
                    dias_dif = (f_ejec_dt - hoy).days
                    if est in ("Terminado y Cobrado", "Terminado"):
                        badge_fecha = f"<span style='background:#dcfce7; color:#15803d; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>✅ Finalizada ({f_ejec_dt.strftime('%d/%m/%Y')})</span>"
                    elif dias_dif < 0:
                        badge_fecha = f"<span style='background:#fee2e2; color:#b91c1c; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>⚠️ Vencida hace {abs(dias_dif)} días ({f_ejec_dt.strftime('%d/%m/%Y')})</span>"
                    elif dias_dif == 0:
                        badge_fecha = f"<span style='background:#fef08a; color:#854d0e; padding:3px 8px; border-radius:12px; font-weight:800; font-size:12px;'>⚡ ¡SE EJECUTA HOY! ({f_ejec_dt.strftime('%d/%m/%Y')})</span>"
                    elif dias_dif <= 3:
                        badge_fecha = f"<span style='background:#e0f2fe; color:#0369a1; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>⏳ En {dias_dif} días ({f_ejec_dt.strftime('%d/%m/%Y')})</span>"
                    else:
                        badge_fecha = f"<span style='background:#f1f5f9; color:#475569; padding:3px 8px; border-radius:12px; font-weight:600; font-size:12px;'>📅 Prevista: {f_ejec_dt.strftime('%d/%m/%Y')}</span>"
                else:
                    badge_fecha = "<span style='background:#f1f5f9; color:#64748b; padding:3px 8px; border-radius:12px; font-size:12px;'>Sin fecha programada</span>"

                # Cuadrilla badge
                es_cuadrilla_2 = ("2" in asig or "Compañero" in asig) and ("Solo Yo" not in asig)
                if es_cuadrilla_2:
                    badge_cuad = "<span style='background:#ede9fe; color:#6d28d9; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>👥 Cuadrilla 2 (Yo + Compañero)</span>"
                elif "Solo Yo" in asig:
                    badge_cuad = "<span style='background:#e0e7ff; color:#3730a3; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>🧑‍🔧 Solo Yo (1 Oficial)</span>"
                else:
                    badge_cuad = "<span style='background:#f3e8ff; color:#7e22ce; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>🧑‍🔧 Compañero Solo</span>"

                # Estado badge
                if est in ("En Ejecución", "Aceptado"):
                    badge_est = "<span style='background:#dcfce7; color:#166534; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>🟢 En Ejecución</span>"
                elif est == "Pendiente":
                    badge_est = "<span style='background:#fef9c3; color:#854d0e; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>🟡 Pendiente</span>"
                elif "Terminado" in est:
                    badge_est = "<span style='background:#e0f2fe; color:#0369a1; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>🔵 Cobrada</span>"
                else:
                    badge_est = "<span style='background:#fee2e2; color:#991b1b; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>🔴 Cancelada</span>"

                # Gastos de la obra
                tks_lista = datos_int.get("lista_tickets_obra", [])
                tot_tks = sum(float(t.get("importe", 0.0)) for t in tks_lista)
                horas_mo = float(datos_int.get("horas_mano_obra", 8.0))

                # Estimación limpia
                benef_limpio = float(datos_int.get("sueldo_limpio_autonomo", tot_siva * 0.6))
                if es_cuadrilla_2:
                    reparto_txt = f"Aprox. <b>{(benef_limpio / 2.0):,.2f} €</b> para ti | <b>{(benef_limpio / 2.0):,.2f} €</b> para compañero"
                else:
                    reparto_txt = f"Aprox. <b>{benef_limpio:,.2f} €</b> íntegros para ti"

                # Desviación de materiales de almacén si existe albarán conciliado
                aud_desv = datos_int.get("conciliacion_albaran", {}).get("auditoria_desviacion") or datos_int.get("desviacion_materiales")
                badge_desv = ""
                desv_txt = ""
                if aud_desv:
                    d_eur = float(aud_desv.get("desv_neta_eur", 0.0))
                    if d_eur < -0.05:
                        badge_desv = f"<span style='background:#dcfce7; color:#15803d; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>🟢 Ahorro Mat: {d_eur:,.2f} €</span>"
                        desv_txt = f"<div style='font-size:12px; color:#16a34a;'>Ahorro compras: <b>{d_eur:,.2f} €</b></div>"
                    elif d_eur > 0.05:
                        badge_desv = f"<span style='background:#fee2e2; color:#b91c1c; padding:3px 8px; border-radius:12px; font-weight:700; font-size:12px;'>🔴 Sobrecoste Mat: +{d_eur:,.2f} €</span>"
                        desv_txt = f"<div style='font-size:12px; color:#dc2626;'>Sobrecoste compras: <b>+{d_eur:,.2f} €</b></div>"
                    else:
                        badge_desv = "<span style='background:#f1f5f9; color:#475569; padding:3px 8px; border-radius:12px; font-size:12px;'>⚪ Mat. Exacto</span>"

                with st.container(border=True):
                    col_c1, col_c2, col_c3, col_c4 = st.columns([3.2, 1.8, 1.8, 1.8])
                    with col_c1:
                        st.markdown(f"#### ⚡ #{oid} - {nom_p}")
                        st.markdown(f"👤 Cliente: **{cli}** | Especialidad: `{mod_orig}`")
                        badges_linea = f"{badge_est} &nbsp; {badge_cuad} &nbsp; {badge_fecha}"
                        if badge_desv:
                            badges_linea += f" &nbsp; {badge_desv}"
                        st.markdown(badges_linea, unsafe_allow_html=True)
                        if notas_p:
                            st.caption(f"📝 *Nota:* {notas_p}")
                    with col_c2:
                        st.markdown(f"**Presupuesto Total:**")
                        st.markdown(f"<div style='font-size:19px; font-weight:800; color:#0284c7;'>{tot_civa:,.2f} € <span style='font-size:12px; color:#64748b;'>(IVA inc.)</span></div>", unsafe_allow_html=True)
                        st.caption(f"Base: {tot_siva:,.2f} € | Horas: ~{horas_mo:.1f} h")
                    with col_c3:
                        st.markdown(f"**Gastos & Reparto:**")
                        st.markdown(f"<div style='font-size:14px; color:#dc2626;'>Tickets deducidos: <b>{tot_tks:,.2f} €</b> ({len(tks_lista)} gastos)</div>", unsafe_allow_html=True)
                        if desv_txt:
                            st.markdown(desv_txt, unsafe_allow_html=True)
                        st.caption(reparto_txt, unsafe_allow_html=True)
                    with col_c4:
                        # Botones de acción rápida
                        btn_col_a, btn_col_b = st.columns(2)
                        with btn_col_a:
                            if st.button("📂 Abrir", key=f"btn_co_open_{oid}", use_container_width=True, help="Carga esta obra en su módulo de cálculo para ver materiales y cálculos"):
                                p_completo = cargar_presupuesto_por_id(oid)
                                if p_completo:
                                    prefijo_mod = mod_orig.replace(" ", "_")
                                    st.session_state[f"presupuesto_cargado_{prefijo_mod}"] = p_completo
                                    st.session_state[f"{prefijo_mod}_lista_tickets_obra"] = list(p_completo.get("datos", {}).get("lista_tickets_obra", []))
                                    destino_menu = obtener_mapa_redireccion_modulo(mod_orig)
                                    st.session_state["menu_activo"] = destino_menu
                                    st.query_params["modulo"] = destino_menu
                                    st.rerun()
                        with btn_col_b:
                            with st.popover("✏️ Editar"):
                                st.markdown(f"##### ✏️ Planificar Obra #{oid}")
                                nuevo_est = st.selectbox(
                                    "Estado de la obra:",
                                    ["Pendiente", "En Ejecución", "Terminado y Cobrado", "Rechazado"],
                                    index=["Pendiente", "En Ejecución", "Terminado y Cobrado", "Rechazado"].index(est) if est in ["Pendiente", "En Ejecución", "Terminado y Cobrado", "Rechazado"] else 0,
                                    key=f"ed_est_{oid}"
                                )
                                nuevo_asig = st.selectbox(
                                    "¿Quién la ejecuta?:",
                                    ["👥 Con Mi Compañero (Cuadrilla de 2)", "🧑‍🔧 Solo Yo (1 Oficial)", "🧑‍🔧 Mi Compañero Solo"],
                                    index=0 if es_cuadrilla_2 else 1,
                                    key=f"ed_asig_{oid}"
                                )
                                nueva_f_ejec = st.text_input("Fecha Prevista Ejecución:", value=f_ejec_str or datetime.date.today().strftime("%d/%m/%Y"), key=f"ed_fejec_{oid}")
                                nueva_nota = st.text_area("Notas internas / Logística:", value=notas_p, height=80, key=f"ed_nota_{oid}")

                                if st.button("💾 Guardar Planificación", key=f"btn_save_plan_{oid}", type="primary", use_container_width=True):
                                    d_act = dict(datos_int)
                                    d_act["fecha_ejecucion"] = nueva_f_ejec
                                    d_act["asignado_a"] = nuevo_asig
                                    d_act["notas_planificacion"] = nueva_nota
                                    ok_up = actualizar_presupuesto(oid, {
                                        "estado": nuevo_est,
                                        "asignado_a": nuevo_asig,
                                        "fecha_ejecucion": nueva_f_ejec,
                                        "notas_planificacion": nueva_nota,
                                        "datos": d_act
                                    })
                                    if ok_up:
                                        st.success("✅ Obra planificada correctamente.")
                                        st.rerun()

                        # Desplegable de tickets rápidos
                        with st.popover("🧾 Tickets"):
                            st.markdown(f"###### 🧾 Gastos de Obra #{oid}")
                            if tks_lista:
                                for tk_i, tk in enumerate(tks_lista):
                                    st.markdown(f"• **{tk.get('concepto', 'Gasto')}**: {float(tk.get('importe', 0.0)):,.2f} € ({tk.get('pagador', 'Bote')}) - *{tk.get('fecha', '')}*")
                            else:
                                st.caption("No hay gastos registrados en esta obra aún.")

                            st.markdown("---")
                            st.caption("Añadir ticket rápido:")
                            tk_con_rap = st.text_input("Concepto:", placeholder="Ej: Gasoil furgoneta", key=f"co_tk_con_{oid}")
                            tk_imp_rap = st.number_input("Importe (€):", min_value=0.0, value=30.0, step=5.0, key=f"co_tk_imp_{oid}")
                            tk_pag_rap = st.selectbox("Pagó:", ["🧑‍🔧 Yo (Titular)", "👥 Compañero", "💰 Bote Común"], key=f"co_tk_pag_{oid}")
                            if st.button("➕ Añadir Gasto", key=f"btn_add_tk_rap_{oid}", use_container_width=True):
                                if tk_con_rap and tk_imp_rap > 0:
                                    d_tk_up = dict(datos_int)
                                    if "lista_tickets_obra" not in d_tk_up:
                                        d_tk_up["lista_tickets_obra"] = []
                                    d_tk_up["lista_tickets_obra"].append({
                                        "concepto": tk_con_rap,
                                        "importe": tk_imp_rap,
                                        "pagador": tk_pag_rap,
                                        "fecha": datetime.date.today().strftime("%d/%m/%Y"),
                                        "comercio": "Local / Ruta",
                                        "icono": "⛽" if "gasoil" in tk_con_rap.lower() else "🧾"
                                    })
                                    d_tk_up["total_tickets_obra"] = sum(float(t.get("importe", 0.0)) for t in d_tk_up["lista_tickets_obra"])
                                    actualizar_presupuesto(oid, {"datos": d_tk_up})
                                    st.success(f"✅ Gasto de {tk_imp_rap:,.2f} € añadido a la obra.")
                                    st.rerun()

                        if aud_desv:
                            with st.popover("📊 Desvío"):
                                st.markdown(f"###### ⚖️ Auditoría de Materiales #{oid}")
                                st.caption(f"Previsto: {aud_desv.get('tot_previsto', 0):,.2f} € | Real Facturado: {aud_desv.get('tot_real', 0):,.2f} €")
                                d_e = float(aud_desv.get("desv_neta_eur", 0))
                                if d_e < 0:
                                    st.markdown(f"<b style='color:#16a34a;'>Ahorro compras: {d_e:,.2f} € ({aud_desv.get('desv_neta_pct', 0):.1f}%)</b>", unsafe_allow_html=True)
                                elif d_e > 0:
                                    st.markdown(f"<b style='color:#dc2626;'>Sobrecoste compras: +{d_e:,.2f} € (+{aud_desv.get('desv_neta_pct', 0):.1f}%)</b>", unsafe_allow_html=True)
                                else:
                                    st.markdown("<b>Materiales clavados: 0,00 €</b>", unsafe_allow_html=True)
                                st.markdown("---")
                                for p in aud_desv.get("partidas", [])[:6]:
                                    dif_p = p.get('dif_eur', 0)
                                    col_sign = '#16a34a' if dif_p < 0 else ('#dc2626' if dif_p > 0 else '#64748b')
                                    st.caption(f"• **{p['partida'][:32]}**: <span style='color:{col_sign}; font-weight:700;'>{dif_p:+,.2f} €</span>", unsafe_allow_html=True)

                        # Botón borrar
                        if st.button("🗑️", key=f"btn_co_del_{oid}", help="Eliminar obra"):
                            if eliminar_presupuesto(oid):
                                st.warning("Obra eliminada.")
                                st.rerun()

    # -------------------------------------------------------------------------
    # TAB 2: CALENDARIO & AGENDA DE CUADRILLA
    # -------------------------------------------------------------------------
    with tab_calendario:
        st.markdown("##### 🗓️ Agenda Cronológica de Trabajos")
        st.caption("Visualiza las obras ordenadas por su fecha de inicio prevista para saber exactamente qué días trabajas con tu compañero y qué días son individuales:")

        obras_con_fecha = []
        obras_sin_fecha = []
        for o in todas_obras:
            f_dt = parsear_fecha_segura(o.get("fecha_ejecucion", ""))
            if f_dt:
                obras_con_fecha.append((f_dt, o))
            else:
                obras_sin_fecha.append(o)

        obras_con_fecha.sort(key=lambda x: x[0])

        if not obras_con_fecha and not obras_sin_fecha:
            st.info("No hay obras registradas en la agenda.")
        else:
            if obras_con_fecha:
                st.markdown("###### 📅 Obras con Fecha Programada:")
                for f_dt, ob in obras_con_fecha:
                    oid = ob["id"]
                    nom = ob.get("nombre_presupuesto", f"Obra #{oid}")
                    cli = ob.get("nombre_cliente", "")
                    asig = ob.get("asignado_a", "Cuadrilla (2)")
                    est = ob.get("estado", "Pendiente")
                    tot = float(ob.get("total_con_iva", 0.0))
                    dias_d = (f_dt - hoy).days

                    es_conjunto = ("2" in asig or "Compañero" in asig) and ("Solo Yo" not in asig)

                    with st.container(border=True):
                        col_ag1, col_ag2, col_ag3 = st.columns([1.5, 3.5, 2])
                        with col_ag1:
                            st.markdown(f"### 🗓️ {f_dt.strftime('%d/%m/%Y')}")
                            if dias_d == 0:
                                st.markdown("<b style='color:#ca8a04;'>⚡ ¡HOY!</b>", unsafe_allow_html=True)
                            elif dias_d > 0:
                                st.caption(f"Faltan {dias_d} días")
                            else:
                                st.markdown(f"<span style='color:#dc2626; font-size:12px;'>Vencida ({abs(dias_d)} d)</span>", unsafe_allow_html=True)
                        with col_ag2:
                            st.markdown(f"**#{oid} - {nom}** ({cli})")
                            st.markdown(f"Estado: `{est}` | Tipo: `{ob.get('modulo_origen', 'General')}`")
                            if ob.get("notas_planificacion"):
                                st.caption(f"📝 {ob.get('notas_planificacion')}")
                        with col_ag3:
                            if es_conjunto:
                                st.markdown("<span style='background:#ede9fe; color:#6d28d9; padding:4px 8px; border-radius:6px; font-weight:700;'>👥 Cuadrilla 2 (Ambos)</span>", unsafe_allow_html=True)
                            else:
                                st.markdown("<span style='background:#e0e7ff; color:#3730a3; padding:4px 8px; border-radius:6px; font-weight:700;'>🧑‍🔧 1 Solo Instalador</span>", unsafe_allow_html=True)
                            st.markdown(f"Importe: **{tot:,.2f} €**")

            if obras_sin_fecha:
                st.markdown("---")
                st.markdown("###### ⏳ Obras pendientes de fijar fecha:")
                for ob in obras_sin_fecha:
                    oid = ob["id"]
                    st.caption(f"• **#{oid} - {ob.get('nombre_presupuesto')}** ({ob.get('nombre_cliente')}) - Asignado a: *{ob.get('asignado_a', 'Sin asignar')}*")

    # -------------------------------------------------------------------------
    # TAB 3: DAR DE ALTA NUEVA OBRA / AVISO
    # -------------------------------------------------------------------------
    with tab_nueva:
        st.markdown("##### ➕ Registrar Nueva Obra o Aviso de Trabajo")
        st.caption("Si un cliente te llama por teléfono o acuerdas una obra nueva en el taller, regístrala aquí en 1 minuto para agendarla:")

        col_n1, col_n2 = st.columns(2)
        with col_n1:
            nuevo_nom_obra = st.text_input("Nombre de la Obra:", placeholder="Ej: Reforma eléctrica vivienda y cuadro general", key="alta_nom_obra")
            nuevo_nom_cli = st.text_input("Nombre / Teléfono del Cliente:", placeholder="Ej: D. Antonio Ruiz - 612 34 56 78", key="alta_nom_cli")
            nuevo_mod = st.selectbox(
                "Especialidad o Tipo de Trabajo:",
                ["Derivación Individual (DI)", "Presupuesto Vivienda", "Línea Recarga (IRVE)", "Línea General (LGA)", "Previsión de Cargas", "Solar Fotovoltaica", "Memoria Técnica (MTD)", "Reforma General"],
                key="alta_mod_tipo"
            )
        with col_n2:
            nuevo_fecha_ejec = st.date_input("📅 Fecha Prevista de Ejecución:", value=datetime.date.today() + datetime.timedelta(days=2), key="alta_fecha_ejec")
            nuevo_asig_cuad = st.selectbox(
                "👥 ¿Quién ejecutará esta obra?:",
                ["👥 Con Mi Compañero (Cuadrilla de 2)", "🧑‍🔧 Solo Yo (1 Oficial)", "🧑‍🔧 Mi Compañero Solo"],
                key="alta_asig_cuad"
            )
            col_imp1, col_imp2 = st.columns(2)
            with col_imp1:
                nuevo_importe_est = st.number_input("Presupuesto Estimado (€ con IVA):", min_value=0.0, value=850.0, step=50.0, key="alta_imp_est")
            with col_imp2:
                nuevo_horas_est = st.number_input("Horas Estimadas de Trabajo (h):", min_value=1.0, value=8.0, step=1.0, key="alta_horas_est")

        nuevo_notas_obra = st.text_area("Notas iniciales / Materiales clave / Herramientas necesarias:", placeholder="Ej: Llevar escalera telescópica y percutor para rozas. Pasar cable de 16mm².", height=80, key="alta_notas_obra")

        if st.button("💾 Registrar y Agendar Obra", type="primary", use_container_width=True, key="btn_alta_guardar_obra"):
            if not nuevo_nom_obra.strip():
                st.warning("⚠️ Introduce un nombre para identificar la obra.")
            else:
                base_est = round(nuevo_importe_est / 1.21, 2)
                f_ejec_formato = nuevo_fecha_ejec.strftime("%d/%m/%Y")
                datos_nueva_obra = {
                    "concepto": nuevo_nom_obra.strip(),
                    "cliente": nuevo_nom_cli.strip() if nuevo_nom_cli.strip() else "Cliente",
                    "horas_mano_obra": nuevo_horas_est,
                    "precio_hora_coste": 28.0,
                    "fecha_ejecucion": f_ejec_formato,
                    "asignado_a": nuevo_asig_cuad,
                    "notas_planificacion": nuevo_notas_obra.strip(),
                    "lista_tickets_obra": [],
                    "total_tickets_obra": 0.0,
                    "sueldo_limpio_autonomo": round(base_est * 0.65, 2)
                }

                ok_n, pid_n = guardar_presupuesto(
                    usuario_id=1,
                    cliente_id=None,
                    nombre_cliente=nuevo_nom_cli.strip() if nuevo_nom_cli.strip() else "Cliente General",
                    nombre_presupuesto=nuevo_nom_obra.strip(),
                    modulo_origen=nuevo_mod,
                    datos_presupuesto=datos_nueva_obra,
                    estado="Aceptado",
                    total_sin_iva=base_est,
                    total_con_iva=nuevo_importe_est,
                    iva_pct=21.0,
                    modo_tarifa="Autónomo",
                    fecha_presupuesto=datetime.date.today().strftime("%d/%m/%Y")
                )
                if ok_n:
                    st.success(f"✅ ¡Obra #{pid_n} '{nuevo_nom_obra}' registrada y agendada con éxito para el {f_ejec_formato}!")
                    st.rerun()
                else:
                    st.error("Error al registrar la obra en la base de datos.")
