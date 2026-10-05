# -*- coding: utf-8 -*-
"""
Módulo de Gestión de Clientes (CRM Eléctrico) y Gestor de Proyectos de Obra
Bolimur REBT PRO
Diseñado para Instaladores Electricistas Autorizados en Baja Tensión y Tramitación ante Industria.
Permite visualizar en tabla interactiva, registrar, editar, duplicar, grabar y borrar clientes y proyectos técnicos de forma ágil y visual.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from modulos import db_manager, auth_manager

def generar_resumen_portapapeles(c: Dict[str, Any]) -> str:
    """Genera un bloque de texto limpio y ordenado para copiar y pegar en WhatsApp, Email o Documentos."""
    lineas = [
        "⚡ FICHA DE SUMINISTRO ELÉCTRICO — BOLIMUR REBT",
        "================================================",
        f"👤 TITULAR: {c.get('nombre_completo', '')}",
        f"🆔 NIF / CIF: {c.get('nif_cif') or '-'}",
        f"📞 TELÉFONO: {c.get('telefono') or '-'}",
        f"✉️ EMAIL: {c.get('email') or '-'}",
        f"🏠 TIPO INMUEBLE: {c.get('tipo_inmueble') or 'Vivienda'}",
        "------------------------------------------------",
        f"📍 DIRECCIÓN: {c.get('direccion_suministro') or '-'}",
        f"🏙️ POBLACIÓN: {c.get('localidad') or c.get('municipio') or '-'} ({c.get('codigo_postal') or ''})",
        f"🗺️ PROVINCIA: {c.get('provincia') or 'Murcia'}",
        "------------------------------------------------",
        f"⚡ CÓDIGO CUPS: {c.get('cups') or '-'}",
        f"🏛️ REF. CATASTRAL: {c.get('referencia_catastral') or '-'}",
        f"🏢 DISTRIBUIDORA: {c.get('distribuidora') or 'i-DE (Iberdrola)'}",
        f"🔌 POTENCIA: {c.get('potencia_contratada_kw') or '-'} kW | {c.get('tension_suministro') or '230V'}"
    ]
    if c.get("notas"):
        lineas.append("------------------------------------------------")
        lineas.append(f"📝 OBSERVACIONES: {c['notas']}")
    lineas.append("================================================")
    return "\n".join(lineas)

def renderizar():
    usuario = auth_manager.obtener_usuario_actual()
    if not usuario:
        st.warning("Debes iniciar sesión para gestionar tus clientes y proyectos.")
        return

    usuario_id = usuario["id"]
    user_email = (usuario.get("email") or "").strip().lower()

    config_nube = db_manager.obtener_config_nube()
    tiene_nube = bool(config_nube.get("url") and config_nube.get("key"))

    # Sincronización inicial automática de la cuenta si hay nube configurada
    if tiene_nube and f"crm_sync_done_{usuario_id}" not in st.session_state:
        st.session_state[f"crm_sync_done_{usuario_id}"] = True
        try:
            db_manager.sincronizar_con_nube(usuario_id)
        except Exception:
            pass

    clientes = db_manager.listar_clientes(usuario_id)
    todos_proyectos = db_manager.listar_proyectos_usuario(usuario_id)

    # Conteo de proyectos por cada cliente
    conteo_proyectos_por_cli = {}
    for p in todos_proyectos:
        c_id = p.get("cliente_id")
        if c_id:
            conteo_proyectos_por_cli[c_id] = conteo_proyectos_por_cli.get(c_id, 0) + 1

    # Asegurar cliente seleccionado por defecto
    if "crm_cliente_seleccionado_id" not in st.session_state or not st.session_state["crm_cliente_seleccionado_id"]:
        if clientes:
            st.session_state["crm_cliente_seleccionado_id"] = clientes[0]["id"]
            st.session_state["cliente_activo_proyecto"] = clientes[0]
        else:
            st.session_state["crm_cliente_seleccionado_id"] = None

    # Obtener el cliente activo actual
    cliente_activo = None
    if st.session_state.get("crm_cliente_seleccionado_id"):
        cliente_activo = db_manager.obtener_cliente_por_id(st.session_state["crm_cliente_seleccionado_id"], usuario_id)
        if not cliente_activo and clientes:
            cliente_activo = clientes[0]
            st.session_state["crm_cliente_seleccionado_id"] = cliente_activo["id"]
        if cliente_activo:
            st.session_state["cliente_activo_proyecto"] = cliente_activo

    # =========================================================================
    # CABECERA PRINCIPAL Y MÉTRICAS
    # =========================================================================
    col_t1, col_t2, col_t3, col_t4 = st.columns([2.2, 1.0, 1.0, 1.8])
    with col_t1:
        st.title("👥 Expedientes de Clientes y Obras")
        if tiene_nube:
            st.markdown(f"🟢 **Nube Sincronizada (Supabase)** — Base de datos privada de `{user_email}`.")
        else:
            st.markdown(f"🔒 **Base de Datos Privada e Independiente** — Cuenta: `{user_email}`.")
    with col_t2:
        st.metric("Tus Clientes", f"{len(clientes)} registrados")
    with col_t3:
        st.metric("Tus Obras", f"{len(todos_proyectos)} proyectos")
    with col_t4:
        c_sync, c_dup = st.columns(2)
        with c_sync:
            if tiene_nube:
                if st.button("⚡ Sincronizar", key="btn_sync_top", use_container_width=True, type="primary"):
                    ok_s, msg_s = db_manager.sincronizar_con_nube(usuario_id)
                    if ok_s:
                        st.session_state["crm_alerta_exito"] = f"✅ {msg_s}"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg_s}")
        with c_dup:
            if st.button("🧹 Limpiar Repetidos", key="btn_limpiar_dup_top", use_container_width=True, help="Detecta y unifica fichas y proyectos duplicados"):
                num_borrados = db_manager.limpiar_duplicados_clientes(usuario_id)
                if num_borrados > 0:
                    st.session_state["crm_alerta_exito"] = f"✅ Se han unificado y eliminado {num_borrados} fichas duplicadas."
                    st.rerun()
                else:
                    st.info("No se encontraron fichas duplicadas en tu cuenta.")

    # Notificaciones de acción (si existen)
    if "crm_alerta_exito" in st.session_state:
        st.success(st.session_state["crm_alerta_exito"])
        del st.session_state["crm_alerta_exito"]

    # =========================================================================
    # PESTAÑAS PRINCIPALES (UNIFICADAS: SOLO 4 PESTAÑAS CLARAS)
    # =========================================================================
    tab_clientes, tab_nuevo_cliente, tab_todos_proyectos, tab_sincro = st.tabs([
        f"📊 Clientes y Suministros ({len(clientes)})",
        "➕ Alta de Nuevo Cliente",
        f"📂 Historial de Proyectos ({len(todos_proyectos)})",
        "☁️ Sincronización Nube"
    ])

    # =========================================================================
    # TAB 1: 📊 CLIENTES Y SUMINISTROS (TABLA PRINCIPAL + EDICIÓN IN-SITU)
    # =========================================================================
    with tab_clientes:
        if not clientes:
            st.info("ℹ️ Todavía no tienes clientes registrados bajo esta cuenta.")
            with st.container(border=True):
                st.markdown("##### 🔍 ¿Tenías clientes creados anteriormente o en el Servidor Nube?")
                col_rec1, col_rec2 = st.columns(2)
                with col_rec1:
                    if tiene_nube:
                        if st.button("☁️ Sincronizar y Descargar desde la Nube (Supabase)", key="btn_sync_crm_empty", type="primary", use_container_width=True):
                            ok_s, msg_s = db_manager.sincronizar_con_nube(usuario_id)
                            if ok_s:
                                st.success(f"✅ {msg_s}")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg_s}")
                    else:
                        st.info("Puedes configurar tu base de datos Supabase en la pestaña '☁️ Sincronización Nube'.")
                with col_rec2:
                    if st.button("🔄 Recuperar y Vincular Clientes Locales Anteriores", key="btn_recup_crm_empty", use_container_width=True):
                        recup = db_manager.recuperar_todos_clientes_locales(usuario_id)
                        if recup > 0:
                            st.success(f"✅ ¡Se han recuperado y vinculado {recup} expedientes a tu cuenta!")
                            st.rerun()
                        else:
                            st.info("No se encontraron clientes locales adicionales en este dispositivo.")
        else:
            # 1. Barra de búsqueda y filtros
            with st.container(border=True):
                col_b1, col_b2, col_b3 = st.columns([3, 1.5, 1.5])
                with col_b1:
                    filtro_txt = st.text_input(
                        "🔍 Buscar cliente en la tabla:",
                        placeholder="Escribe nombre, NIF, CUPS, teléfono, población...",
                        key="crm_table_search",
                        label_visibility="collapsed"
                    )
                with col_b2:
                    filtro_tipo = st.selectbox(
                        "Filtrar por tipo:",
                        options=["Todos los tipos", "Vivienda", "Local Comercial", "Nave Industrial", "Garaje / IRVE", "Edificio"],
                        key="crm_table_filter_tipo",
                        label_visibility="collapsed"
                    )
                with col_b3:
                    orden_sel = st.selectbox(
                        "Ordenar por:",
                        options=["Nombre (A ➔ Z)", "Nombre (Z ➔ A)", "Más recientes", "Más antiguos"],
                        key="crm_table_order",
                        label_visibility="collapsed"
                    )

            # Filtrar y ordenar clientes
            clientes_filtrados = list(clientes)
            if filtro_txt:
                q = filtro_txt.strip().lower()
                clientes_filtrados = [
                    c for c in clientes_filtrados
                    if q in (c.get("nombre_completo") or "").lower()
                    or q in (c.get("nif_cif") or "").lower()
                    or q in (c.get("telefono") or "").lower()
                    or q in (c.get("cups") or "").lower()
                    or q in (c.get("direccion_suministro") or "").lower()
                    or q in (c.get("localidad") or c.get("municipio") or "").lower()
                ]

            if filtro_tipo != "Todos los tipos":
                tipo_q = filtro_tipo.lower()
                clientes_filtrados = [
                    c for c in clientes_filtrados
                    if tipo_q in (c.get("tipo_inmueble") or "").lower()
                ]

            if orden_sel == "Nombre (A ➔ Z)":
                clientes_filtrados.sort(key=lambda x: (x.get("nombre_completo") or "").lower())
            elif orden_sel == "Nombre (Z ➔ A)":
                clientes_filtrados.sort(key=lambda x: (x.get("nombre_completo") or "").lower(), reverse=True)
            elif orden_sel == "Más recientes":
                clientes_filtrados.sort(key=lambda x: x.get("id", 0), reverse=True)
            elif orden_sel == "Más antiguos":
                clientes_filtrados.sort(key=lambda x: x.get("id", 0))

            # Crear DataFrame para la tabla interactiva
            filas_tabla = []
            for c in clientes_filtrados:
                filas_tabla.append({
                    "ID": c["id"],
                    "Titular / Razón Social": c["nombre_completo"],
                    "NIF / CIF": c.get("nif_cif") or "-",
                    "Teléfono": c.get("telefono") or "-",
                    "Población": c.get("localidad") or c.get("municipio") or "-",
                    "Dirección": c.get("direccion_suministro") or "-",
                    "CUPS": c.get("cups") or "-",
                    "Potencia": f"{c.get('potencia_contratada_kw') or '-'} kW",
                    "Distribuidora": c.get("distribuidora") or "-",
                    "Tipo Inmueble": c.get("tipo_inmueble") or "Vivienda",
                    "Obras": conteo_proyectos_por_cli.get(c["id"], 0)
                })

            df_clientes = pd.DataFrame(filas_tabla)

            # =========================================================
            # 2. TABLA INTERACTIVA DE CLIENTES (CENTRO DE CONTROL)
            # =========================================================
            st.markdown(f"#### 📊 Directorio de Clientes y Suministros ({len(clientes_filtrados)})")
            st.caption("💡 **Haz clic sobre cualquier fila de la tabla** para seleccionarla y ver o editar sus datos inmediatamente.")

            event_tabla = st.dataframe(
                df_clientes,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="crm_grid_dataframe"
            )

            # Sincronización instantánea al hacer clic en una fila
            ids_filtrados = [c["id"] for c in clientes_filtrados]
            if event_tabla and hasattr(event_tabla, "selection") and event_tabla.selection.rows:
                sel_row_idx = event_tabla.selection.rows[0]
                if 0 <= sel_row_idx < len(clientes_filtrados):
                    clicked_cli = clientes_filtrados[sel_row_idx]
                    clicked_id = clicked_cli["id"]
                    if st.session_state.get("crm_cliente_seleccionado_id") != clicked_id:
                        st.session_state["crm_cliente_seleccionado_id"] = clicked_id
                        st.session_state["cliente_activo_proyecto"] = clicked_cli
                        st.rerun()

            curr_id = st.session_state.get("crm_cliente_seleccionado_id")
            if (curr_id not in ids_filtrados) and ids_filtrados:
                curr_id = ids_filtrados[0]
                st.session_state["crm_cliente_seleccionado_id"] = curr_id

            cliente_sel_obj = db_manager.obtener_cliente_por_id(curr_id, usuario_id) if curr_id else None
            if cliente_sel_obj and st.session_state.get("cliente_activo_proyecto") != cliente_sel_obj:
                st.session_state["cliente_activo_proyecto"] = cliente_sel_obj

            # =========================================================
            # 3. BARRA CONTEXTUAL DE ACCIONES DE LA FILA SELECCIONADA
            # =========================================================
            if cliente_sel_obj:
                with st.container(border=True):
                    col_bar_info, col_bar_btn_edit, col_bar_btn_dup, col_bar_btn_del = st.columns([3.2, 1.4, 1.4, 1.0])
                    with col_bar_info:
                        tipo_ico = "🏠" if "vivienda" in (cliente_sel_obj.get("tipo_inmueble") or "").lower() else "🏢"
                        st.markdown(
                            f"<div style='padding-top: 3px;'>"
                            f"<span style='font-size: 16px; font-weight: 700; color: #0284c7;'>"
                            f"📍 Fila Seleccionada: #{cliente_sel_obj['id']} — {cliente_sel_obj['nombre_completo']}</span>"
                            f"<div style='font-size: 12px; color: #475569; margin-top: 2px;'>"
                            f"NIF/CIF: <b>{cliente_sel_obj.get('nif_cif') or '-'}</b> | "
                            f"📞 <b>{cliente_sel_obj.get('telefono') or '-'}</b> | "
                            f"📍 <b>{cliente_sel_obj.get('localidad') or cliente_sel_obj.get('municipio') or '-'}</b> | "
                            f"⚡ CUPS: <code>{cliente_sel_obj.get('cups') or '-'}</code> | "
                            f"Potencia: <b>{cliente_sel_obj.get('potencia_contratada_kw') or '-'} kW</b>"
                            f"</div></div>",
                            unsafe_allow_html=True
                        )
                    with col_bar_btn_edit:
                        st.write("")
                        if st.session_state.get("crm_modo_edicion"):
                            if st.button("❌ Cerrar Edición", key="btn_toggle_edit_off", use_container_width=True):
                                st.session_state["crm_modo_edicion"] = False
                                st.rerun()
                        else:
                            if st.button("✏️ Editar Fila", key="btn_toggle_edit_on", type="primary", use_container_width=True, help="Modifica los datos del cliente seleccionado en la tabla"):
                                st.session_state["crm_modo_edicion"] = True
                                st.rerun()
                    with col_bar_btn_dup:
                        st.write("")
                        if st.button("📋 Duplicar Ficha", key="btn_dup_crm_cliente_bar", use_container_width=True, help="Clonar datos para un nuevo suministro"):
                            copia_data = dict(cliente_sel_obj)
                            copia_data.pop("id", None)
                            copia_data["nombre_completo"] = f"{cliente_sel_obj['nombre_completo']} (Nuevo Suministro)"
                            ok_dup, nuevo_id = db_manager.crear_cliente(usuario_id, copia_data)
                            if ok_dup:
                                st.session_state["crm_cliente_seleccionado_id"] = nuevo_id
                                st.session_state["cliente_activo_proyecto"] = db_manager.obtener_cliente_por_id(nuevo_id, usuario_id)
                                st.session_state["crm_modo_edicion"] = True
                                st.session_state["crm_alerta_exito"] = f"✅ Ficha duplicada como '{copia_data['nombre_completo']}'. Modifica sus datos a continuación."
                                st.rerun()
                    with col_bar_btn_del:
                        st.write("")
                        if st.button("🗑️ Borrar", key="btn_del_crm_bar", use_container_width=True, help="Eliminar este cliente"):
                            st.session_state["confirmar_borrado_cli_id"] = cliente_sel_obj["id"]
                            st.rerun()

                # Confirmación de borrado seguro
                if st.session_state.get("confirmar_borrado_cli_id") == cliente_sel_obj["id"]:
                    st.error(f"⚠️ **¿Confirmas que deseas eliminar definitivamente a '{cliente_sel_obj['nombre_completo']}' (ID #{cliente_sel_obj['id']})?**")
                    st.write("Esta acción borrará la ficha técnica y todos los proyectos o cálculos asociados a este cliente tanto en local como en la nube.")
                    cb_t1, cb_t2 = st.columns(2)
                    with cb_t1:
                        if st.button("🔴 Sí, Eliminar Definitivamente", key="btn_do_del_crm_ok", type="primary", use_container_width=True):
                            db_manager.eliminar_cliente(cliente_sel_obj["id"], usuario_id)
                            del st.session_state["confirmar_borrado_cli_id"]
                            st.session_state["crm_cliente_seleccionado_id"] = None
                            st.session_state["cliente_activo_proyecto"] = None
                            st.session_state["crm_modo_edicion"] = False
                            st.session_state["crm_alerta_exito"] = f"🗑️ Cliente '{cliente_sel_obj['nombre_completo']}' eliminado correctamente."
                            st.rerun()
                    with cb_t2:
                        if st.button("🛡️ Cancelar", key="btn_cancel_del_crm_abort", use_container_width=True):
                            del st.session_state["confirmar_borrado_cli_id"]
                            st.rerun()

            # =========================================================
            # 4. FORMULARIO DE EDICIÓN IN-SITU DE LA FILA SELECCIONADA
            # =========================================================
            if cliente_sel_obj and st.session_state.get("crm_modo_edicion"):
                st.markdown(f'<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">✏️ Modificando Fila Seleccionada: #{cliente_sel_obj["id"]} — {cliente_sel_obj["nombre_completo"]}</h4></div>', unsafe_allow_html=True)
                st.caption("Modifica cualquiera de los datos del cliente y pulsa **'💾 Grabar Cambios en este Cliente'**:")

                with st.form(f"form_edicion_directa_{cliente_sel_obj['id']}"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        st.markdown("##### 👤 1. Titular y Contacto:")
                        enom = st.text_input("Nombre y Apellidos o Razón Social (*):", value=cliente_sel_obj["nombre_completo"], key=f"f_nom_{cliente_sel_obj['id']}")
                        enif = st.text_input("NIF / DNI / CIF:", value=cliente_sel_obj.get("nif_cif", ""), key=f"f_nif_{cliente_sel_obj['id']}")
                        etel = st.text_input("Teléfono de Contacto:", value=cliente_sel_obj.get("telefono", ""), key=f"f_tel_{cliente_sel_obj['id']}")
                        eemail = st.text_input("Email:", value=cliente_sel_obj.get("email", ""), key=f"f_email_{cliente_sel_obj['id']}")
                        
                        tipos_inm = ["Vivienda Residencial", "Local Comercial", "Nave Industrial", "Garaje Comunitario / IRVE", "Edificio de Viviendas"]
                        tipo_act = cliente_sel_obj.get("tipo_inmueble", "Vivienda Residencial")
                        idx_t = 0
                        for i, t in enumerate(tipos_inm):
                            if t.lower() in tipo_act.lower() or tipo_act.lower() in t.lower():
                                idx_t = i
                                break
                        etipo = st.selectbox("Tipo de Inmueble:", tipos_inm, index=idx_t, key=f"f_tipo_{cliente_sel_obj['id']}")

                    with col_e2:
                        st.markdown("##### 📍 2. Dirección y Suministro:")
                        edir = st.text_input("Dirección del Suministro:", value=cliente_sel_obj.get("direccion_suministro", ""), key=f"f_dir_{cliente_sel_obj['id']}")
                        col_c_p1, col_c_p2 = st.columns(2)
                        with col_c_p1:
                            ecp = st.text_input("Código Postal:", value=cliente_sel_obj.get("codigo_postal", "30000"), key=f"f_cp_{cliente_sel_obj['id']}")
                        with col_c_p2:
                            eloc = st.text_input("Municipio / Población:", value=cliente_sel_obj.get("localidad") or cliente_sel_obj.get("municipio") or "Murcia", key=f"f_loc_{cliente_sel_obj['id']}")
                        eprov = st.text_input("Provincia:", value=cliente_sel_obj.get("provincia", "Murcia"), key=f"f_prov_{cliente_sel_obj['id']}")

                        st.markdown("##### ⚡ 3. Parámetros Eléctricos REBT:")
                        ecups = st.text_input("Código CUPS (20-22 caracteres):", value=cliente_sel_obj.get("cups", ""), key=f"f_cups_{cliente_sel_obj['id']}")
                        col_p_t1, col_p_t2 = st.columns(2)
                        with col_p_t1:
                            epot = st.text_input("Potencia (kW):", value=cliente_sel_obj.get("potencia_contratada_kw", "5.75"), key=f"f_pot_{cliente_sel_obj['id']}")
                        with col_p_t2:
                            dists = ["i-DE (Iberdrola)", "Endesa e-distribución", "UFD (Naturgy)", "E-Redes (EDP)", "Otras Distribuidoras"]
                            dist_act = cliente_sel_obj.get("distribuidora", "i-DE (Iberdrola)")
                            idx_d = 0
                            for i, d in enumerate(dists):
                                if d.lower() in dist_act.lower() or dist_act.lower() in d.lower():
                                    idx_d = i
                                    break
                            edist = st.selectbox("Distribuidora:", dists, index=idx_d, key=f"f_dist_{cliente_sel_obj['id']}")
                        
                        eref = st.text_input("Referencia Catastral:", value=cliente_sel_obj.get("referencia_catastral", ""), key=f"f_ref_{cliente_sel_obj['id']}")

                    enotas = st.text_area("Observaciones y Notas Técnicas de Obra:", value=cliente_sel_obj.get("notas", ""), key=f"f_notas_{cliente_sel_obj['id']}")

                    # BOTONES DEL FORMULARIO DE EDICIÓN
                    col_btn_g1, col_btn_g2 = st.columns([2.5, 1])
                    with col_btn_g1:
                        btn_grabar = st.form_submit_button("💾 Grabar Cambios en este Cliente", type="primary", use_container_width=True)
                    with col_btn_g2:
                        btn_cancel = st.form_submit_button("❌ Salir de Edición", use_container_width=True)

                    if btn_grabar:
                        if not enom.strip():
                            st.error("El nombre del cliente no puede estar vacío.")
                        else:
                            ok_up = db_manager.actualizar_cliente(cliente_sel_obj["id"], usuario_id, {
                                "nombre_completo": enom.strip(),
                                "nif_cif": enif.strip().upper(),
                                "telefono": etel.strip(),
                                "email": eemail.strip(),
                                "direccion_suministro": edir.strip(),
                                "localidad": eloc.strip(),
                                "codigo_postal": ecp.strip(),
                                "municipio": eloc.strip(),
                                "provincia": eprov.strip(),
                                "cups": ecups.strip().upper(),
                                "referencia_catastral": eref.strip().upper(),
                                "distribuidora": edist,
                                "potencia_contratada_kw": epot.strip(),
                                "tension_suministro": cliente_sel_obj.get("tension_suministro", "Monofásica 230V"),
                                "tipo_inmueble": etipo,
                                "notas": enotas.strip()
                            })
                            if ok_up:
                                st.session_state["crm_modo_edicion"] = False
                                st.session_state["cliente_activo_proyecto"] = db_manager.obtener_cliente_por_id(cliente_sel_obj["id"], usuario_id)
                                st.session_state["crm_alerta_exito"] = f"✅ ¡Ficha de '{enom}' (ID #{cliente_sel_obj['id']}) grabada y actualizada con éxito!"
                                st.rerun()
                            else:
                                st.error("Error al guardar los cambios en la base de datos.")

                    if btn_cancel:
                        st.session_state["crm_modo_edicion"] = False
                        st.rerun()


            # =========================================================
            # 5. EXPEDIENTE TÉCNICO 360° (SOLO SI NO ESTÁ EN MODO EDICIÓN)
            # =========================================================
            if cliente_sel_obj and not st.session_state.get("crm_modo_edicion"):
                with st.container(border=True):
                    # Ficha 360° con datos del cliente seleccionado
                    st.markdown(f'<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">👤 Expediente Técnico: #{cliente_sel_obj["id"]} — {cliente_sel_obj["nombre_completo"]}</h4></div>', unsafe_allow_html=True)
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        st.markdown("##### 🏷️ Titular y Contacto:")
                        st.markdown(f"**Nombre / Razón Social:** `{cliente_sel_obj['nombre_completo']}`")
                        st.markdown(f"**NIF / DNI / CIF:** `{cliente_sel_obj.get('nif_cif') or '-'}`")
                        st.markdown(f"**Teléfono:** `{cliente_sel_obj.get('telefono') or '-'}`")
                        st.markdown(f"**Email:** `{cliente_sel_obj.get('email') or '-'}`")
                        st.markdown(f"**Tipo Inmueble:** `{cliente_sel_obj.get('tipo_inmueble') or 'Vivienda'}`")

                    with col_f2:
                        st.markdown("##### ⚡ Punto de Suministro:")
                        st.markdown(f"**Dirección:** `{cliente_sel_obj.get('direccion_suministro') or '-'}`")
                        st.markdown(f"**Población / CP:** `{cliente_sel_obj.get('localidad') or cliente_sel_obj.get('municipio') or '-'} ({cliente_sel_obj.get('codigo_postal') or ''})`")
                        st.markdown(f"**Provincia:** `{cliente_sel_obj.get('provincia') or 'Murcia'}`")
                        st.markdown(f"**Distribuidora:** `{cliente_sel_obj.get('distribuidora') or 'i-DE (Iberdrola)'}`")

                    with col_f3:
                        st.markdown("##### 🏛️ Parámetros REBT:")
                        st.markdown(f"**Código CUPS:** `{cliente_sel_obj.get('cups') or '-'}`")
                        st.markdown(f"**Ref. Catastral:** `{cliente_sel_obj.get('referencia_catastral') or '-'}`")
                        st.markdown(f"**Potencia Contratada:** `{cliente_sel_obj.get('potencia_contratada_kw') or '-'} kW`")
                        st.markdown(f"**Tensión:** `{cliente_sel_obj.get('tension_suministro') or 'Monofásica 230V'}`")

                    if cliente_sel_obj.get("notas"):
                        st.info(f"📝 **Notas y Observaciones de Obra:** {cliente_sel_obj['notas']}")

                    # Botonera de Lanzamiento Directo a Cálculos
                    st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🚀 Acciones Rápidas con este Cliente (1 Clic)</h4></div>', unsafe_allow_html=True)
                    c_act1, c_act2, c_act3, c_act4 = st.columns(4)
                    with c_act1:
                        if st.button("🏛️ Iniciar Boletín CIE / MTD", key=f"btn_act_cie_{cliente_sel_obj['id']}", use_container_width=True, type="primary"):
                            st.session_state["cliente_activo_proyecto"] = cliente_sel_obj
                            st.session_state["menu_activo"] = "🏛️ Memoria Técnica (MTD 30)"
                            st.rerun()
                    with c_act2:
                        if st.button("🏡 Iniciar Presupuesto", key=f"btn_act_pres_{cliente_sel_obj['id']}", use_container_width=True):
                            st.session_state["cliente_activo_proyecto"] = cliente_sel_obj
                            st.session_state["menu_activo"] = "🏡 Presupuesto Vivienda"
                            st.rerun()
                    with c_act3:
                        if st.button("🚗 Iniciar Recarga IRVE", key=f"btn_act_irve_{cliente_sel_obj['id']}", use_container_width=True):
                            st.session_state["cliente_activo_proyecto"] = cliente_sel_obj
                            st.session_state["menu_activo"] = "🚗 Línea Recarga (IRVE)"
                            st.rerun()
                    with c_act4:
                        if st.button("🔌 Calcular DI / LGA", key=f"btn_act_di_{cliente_sel_obj['id']}", use_container_width=True):
                            st.session_state["cliente_activo_proyecto"] = cliente_sel_obj
                            st.session_state["menu_activo"] = "🔌 Derivación Individual (DI)"
                            st.rerun()

                    # Listado de Proyectos del Cliente
                    st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">📁 Proyectos y Cálculos Guardados de este Cliente</h4></div>', unsafe_allow_html=True)
                    proyectos_cliente = db_manager.listar_proyectos_por_cliente(cliente_sel_obj["id"], usuario_id)
                    
                    if not proyectos_cliente:
                        st.info("ℹ️ No hay cálculos ni presupuestos guardados todavía para este cliente. Realiza un cálculo en cualquiera de los módulos y guárdalo asociándolo a esta ficha.")
                    else:
                        for proj in proyectos_cliente:
                            with st.container(border=True):
                                col_p1, col_p2, col_p3, col_p4 = st.columns([3.5, 2.5, 2, 1.2])
                                with col_p1:
                                    st.markdown(f"**📌 {proj['nombre_proyecto']}**")
                                    st.caption(f"Módulo: `{proj['modulo']}` | Fecha: {proj.get('fecha_guardado', '')[:16]}")
                                Jimmy = None
                                with col_p2:
                                    st.markdown(f"**Resumen Técnico:**  \n{proj.get('resumen_potencia_o_importe', '-')}")
                                with col_p3:
                                    if st.button("🚀 Cargar y Modificar", key=f"btn_load_p_{proj['id']}", type="primary", use_container_width=True):
                                        datos_p = db_manager.cargar_proyecto_por_id(proj["id"], usuario_id)
                                        if datos_p:
                                            cargar_proyecto_en_session(proj["modulo"], datos_p.get("datos", {}), cliente_sel_obj)
                                            st.session_state.menu_activo = obtener_label_menu_por_modulo(proj["modulo"])
                                            st.rerun()
                                with col_p4:
                                    if st.button("🗑️ Borrar", key=f"btn_del_p_{proj['id']}", use_container_width=True):
                                        db_manager.eliminar_proyecto(proj["id"], usuario_id)
                                        st.rerun()

    # =========================================================================
    # TAB 2: ➕ ALTA RÁPIDA DE NUEVO CLIENTE (CON PREVENCIÓN DE DUPLICADOS)
    # =========================================================================
    with tab_nuevo_cliente:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">➕ Alta Rápida de Nueva Ficha de Cliente</h4></div>', unsafe_allow_html=True)
        st.caption("Introduce los datos del titular y del punto de suministro. Se utilizarán automáticamente en presupuestos, memorias técnicas MTD y boletines CIE oficiales.")

        with st.container(border=True):
            with st.form("form_nuevo_cliente_crm", clear_on_submit=False):
                col_nc1, col_nc2 = st.columns(2)
                with col_nc1:
                    st.markdown("##### 👤 Datos del Titular:")
                    n_nom = st.text_input("Nombre y Apellidos o Razón Social (*):", placeholder="Ej: Francisco Martínez Gómez")
                    n_nif = st.text_input("NIF / DNI / CIF:", placeholder="Ej: 48555123K")
                    n_tel = st.text_input("Teléfono de Contacto:", placeholder="Ej: 611 22 33 44")
                    n_email = st.text_input("Email:", placeholder="Ej: cliente@correo.com")
                    n_tipo = st.selectbox("Tipo de Suministro / Inmueble:", ["Vivienda Residencial", "Local Comercial", "Nave Industrial", "Garaje Comunitario / IRVE", "Edificio de Viviendas"])

                with col_nc2:
                    st.markdown("##### ⚡ Datos del Punto de Suministro:")
                    n_dir = st.text_input("Dirección de la Vivienda / Local:", placeholder="Ej: Calle Mayor, nº 14, 2ºA")
                    col_cp_loc1, col_cp_loc2 = st.columns(2)
                    with col_cp_loc1:
                        n_cp = st.text_input("Código Postal:", value="30000")
                    with col_cp_loc2:
                        n_loc = st.text_input("Municipio / Población:", value="Murcia")
                    n_prov = st.text_input("Provincia:", value="Murcia")
                    n_cups = st.text_input("Código CUPS (20-22 caracteres):", placeholder="Ej: ES0021000000000000AB1P")
                    n_ref = st.text_input("Referencia Catastral (20 caracteres):", placeholder="Ej: 9872023VH5797S0001WX")
                    col_dis_pot1, col_dis_pot2 = st.columns(2)
                    with col_dis_pot1:
                        n_dist = st.selectbox("Distribuidora Eléctrica:", ["i-DE (Iberdrola)", "Endesa e-distribución", "UFD (Naturgy)", "E-Redes (EDP)", "Otras Distribuidoras"])
                    with col_dis_pot2:
                        n_pot = st.text_input("Potencia Prevista / Contratada (kW):", value="5.75")
                
                n_notas = st.text_area("Observaciones y Notas Técnicas de Obra:", placeholder="Ej: Reforma integral de cuadro eléctrico, ampliación de potencia y boletín de enganche CIE ante Industria.")
                
                btn_crear_c = st.form_submit_button("✨ Grabar y Registrar Ficha del Cliente", type="primary", use_container_width=True)
                if btn_crear_c:
                    if not n_nom.strip():
                        st.error("El nombre del cliente es obligatorio.")
                    else:
                        dup = db_manager.buscar_cliente_duplicado(usuario_id, n_nif, n_nom)
                        if dup:
                            st.warning(f"⚠️ Ya existe una ficha registrada con este NIF o Nombre: **'{dup['nombre_completo']}'** (ID: #{dup['id']}). Hemos actualizado sus datos para no duplicar fichas.")
                            db_manager.actualizar_cliente(dup["id"], usuario_id, {
                                "nombre_completo": n_nom.strip(), "nif_cif": n_nif.strip().upper(), "telefono": n_tel.strip(), "email": n_email.strip(),
                                "direccion_suministro": n_dir.strip(), "localidad": n_loc.strip(), "codigo_postal": n_cp.strip(),
                                "municipio": n_loc.strip(), "provincia": n_prov.strip(), "cups": n_cups.strip().upper(), "referencia_catastral": n_ref.strip().upper(),
                                "distribuidora": n_dist, "potencia_contratada_kw": n_pot.strip(), "tipo_inmueble": n_tipo,
                                "notas": n_notas.strip()
                            })
                            st.session_state["crm_cliente_seleccionado_id"] = dup["id"]
                            st.session_state["cliente_activo_proyecto"] = dup
                            st.rerun()
                        else:
                            ok_c, nuevo_c_id = db_manager.crear_cliente(usuario_id, {
                                "nombre_completo": n_nom.strip(), "nif_cif": n_nif.strip().upper(), "telefono": n_tel.strip(), "email": n_email.strip(),
                                "direccion_suministro": n_dir.strip(), "localidad": n_loc.strip(), "codigo_postal": n_cp.strip(),
                                "municipio": n_loc.strip(), "provincia": n_prov.strip(), "cups": n_cups.strip().upper(), "referencia_catastral": n_ref.strip().upper(),
                                "distribuidora": n_dist, "potencia_contratada_kw": n_pot.strip(), "tipo_inmueble": n_tipo,
                                "notas": n_notas.strip()
                            })
                            if ok_c:
                                st.session_state["crm_cliente_seleccionado_id"] = nuevo_c_id
                                st.session_state["crm_alerta_exito"] = f"✨ ¡Cliente '{n_nom}' registrado y grabado correctamente con ID #{nuevo_c_id}!"
                                st.rerun()
                            else:
                                st.error("Error al registrar cliente en la base de datos.")

    # =========================================================================
    # TAB 3: 📂 HISTORIAL GLOBAL DE PROYECTOS Y OBRAS
    # =========================================================================
    with tab_todos_proyectos:
        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">📂 Expediente Global de Proyectos y Cálculos Guardados</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            if not todos_proyectos:
                st.info("No hay proyectos guardados todavía en tu cuenta.")
            else:
                filas_tabla_proy = []
                for p in todos_proyectos:
                    filas_tabla_proy.append({
                        "ID": p["id"],
                        "Proyecto": p["nombre_proyecto"],
                        "Cliente Asignado": p.get("cliente_nombre") or "General / Sin asignar",
                        "Módulo": p["modulo"],
                        "Resumen Técnico": p.get("resumen_potencia_o_importe", "-"),
                        "Fecha de Guardado": p.get("fecha_guardado", "")[:16]
                    })
                st.dataframe(pd.DataFrame(filas_tabla_proy), use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 4: ☁️ SINCRONIZACIÓN Y BASE DE DATOS EN LA NUBE (SUPABASE)
    # =========================================================================
    with tab_sincro:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">☁️ Base de Datos en la Nube y Acceso 24/7 (PC, Móvil y Tablet)</h4></div>', unsafe_allow_html=True)
        st.caption("Conecta tu base de datos en la nube gratuita (Supabase) para que tus clientes y proyectos se guarden automáticamente y estén accesibles al instante desde cualquier teléfono o PC.")

        col_cfg_nube, col_estado_nube = st.columns([2, 1.2])

        with col_cfg_nube:
            with st.container(border=True):
                st.markdown("#### ⚙️ Conexión a Base de Datos en la Nube (Supabase Cloud)")
                st.write("Configura tu base de datos Supabase gratuita para sincronización automática en tiempo real.")

                actual_url = config_nube.get("url", "")
                actual_key = config_nube.get("key", "")

                in_supa_url = st.text_input("URL de Supabase (*):", value=actual_url, placeholder="https://xyzabcdefg.supabase.co", key="in_supa_url")
                in_supa_key = st.text_input("Anon / Public Key de Supabase (*):", value=actual_key, type="password", placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", key="in_supa_key")
                st.caption("ℹ️ **IMPORTANTE:** La clave requerida es la **API Key `anon` / `public`** (una cadena muy larga que empieza por `eyJ...` o `sb_publishable_...`). La encuentras en Supabase en: **⚙️ Project Settings ➔ API ➔ Project API keys ➔ `anon` `public`**.")

                col_btn_s1, col_btn_s2 = st.columns(2)
                with col_btn_s1:
                    if st.button("🔌 Probar y Guardar Conexión", type="primary", use_container_width=True, key="btn_save_supa"):
                        if in_supa_url and in_supa_key:
                            ok_test, msg_test = db_manager.testear_conexion_nube(in_supa_url, in_supa_key)
                            if ok_test:
                                db_manager.guardar_config_nube(in_supa_url, in_supa_key)
                                st.success("✅ ¡Conectado con éxito a Supabase Cloud! Se ha guardado la configuración.")
                                ok_s, msg_s = db_manager.sincronizar_con_nube(usuario_id)
                                if ok_s:
                                    st.info(f"🔄 {msg_s}")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg_test}")
                        else:
                            st.warning("Introduce la URL y Key de tu proyecto Supabase.")

                with col_btn_s2:
                    if st.button("⚡ Sincronizar Ahora (Local ⇄ Nube)", use_container_width=True, key="btn_manual_sync_tab6"):
                        ok_s, msg_s = db_manager.sincronizar_con_nube(usuario_id)
                        if ok_s:
                            st.success(f"✅ {msg_s}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg_s}")

        with col_estado_nube:
            with st.container(border=True):
                st.markdown("#### 📡 Estado de Sincronización")
                if tiene_nube:
                    st.success("🟢 **Conexión Activa**  \nTus clientes y proyectos se guardan en la nube.")
                    st.write(f"**Cuenta:** `{user_email}`")
                    st.write(f"**Servidor:** `{config_nube.get('url', '')[:35]}...`")
                else:
                    st.warning("🟠 **Solo Local**  \nLos datos se guardan en este dispositivo. Conecta Supabase para acceder desde el móvil.")

        # Copias de seguridad JSON
        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">💾 Copias de Seguridad y Migración Manual (JSON)</h4></div>', unsafe_allow_html=True)
        col_sync1, col_sync2 = st.columns(2)
        with col_sync1:
            with st.container(border=True):
                st.markdown("##### 📥 Descargar Copia de Seguridad Completa")
                st.write("Descarga un archivo con todos tus clientes y proyectos para conservarlos en tu ordenador.")
                backup_json = db_manager.exportar_copia_seguridad_nube(usuario_id)
                st.download_button(
                    label="💾 Descargar Respaldo JSON",
                    data=backup_json,
                    file_name=f"bolimur_respaldo_{user_email.split('@')[0]}.json",
                    mime="application/json",
                    use_container_width=True,
                    type="primary"
                )

        with col_sync2:
            with st.container(border=True):
                st.markdown("##### 📤 Restaurar Respaldo en este Dispositivo")
                st.write("Sube un archivo JSON de respaldo para importar tus clientes y proyectos en 1 segundo.")
                archivo_in = st.file_uploader("Selecciona archivo JSON:", type=["json"], key="upload_crm_backup")
                if archivo_in is not None:
                    contenido_str = archivo_in.getvalue().decode("utf-8")
                    if st.button("🚀 Importar Respaldo", key="btn_do_import_crm", use_container_width=True, type="primary"):
                        ok_imp, msg_imp = db_manager.importar_copia_seguridad_nube(usuario_id, contenido_str)
                        if ok_imp:
                            st.success(f"✅ {msg_imp}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg_imp}")


def cargar_proyecto_en_session(modulo: str, datos: dict, cliente: dict):
    """Carga los parámetros del proyecto en session_state según el módulo correspondiente"""
    st.session_state["cliente_activo_proyecto"] = cliente
    st.session_state["proyecto_cargado_nombre"] = datos.get("nombre_proyecto", "Proyecto Recuperado")

    if "Presupuesto" in modulo:
        if "estancias_pro" in datos:
            st.session_state["estancias_pro"] = datos["estancias_pro"]
        if "partidas_manuales" in datos:
            st.session_state["partidas_manuales"] = datos["partidas_manuales"]
        st.session_state["presupuesto_calculado"] = True

    elif "Previsión" in modulo:
        if "grupos_viviendas" in datos:
            st.session_state["grupos_viviendas"] = datos["grupos_viviendas"]
        if "locales" in datos:
            st.session_state["locales"] = datos["locales"]
        if "servicios_generales" in datos:
            st.session_state["servicios_generales"] = datos["servicios_generales"]
        if "garajes" in datos:
            st.session_state["garajes"] = datos["garajes"]

    elif "LGA" in modulo:
        if "lga_long" in datos:
            st.session_state["lga_long"] = datos["lga_long"]
        if "lga_pot_man" in datos:
            st.session_state["lga_pot_man"] = datos["lga_pot_man"]

    elif "DI" in modulo:
        if "di_pot" in datos:
            st.session_state["di_pot"] = datos["di_pot"]
        if "di_long" in datos:
            st.session_state["di_long"] = datos["di_long"]

    elif "IRVE" in modulo:
        if "irve_custom_w" in datos:
            st.session_state["irve_custom_w"] = datos["irve_custom_w"]
        if "irve_long" in datos:
            st.session_state["irve_long"] = datos["irve_long"]

    elif "Memoria" in modulo or "MTD" in modulo:
        for k, v in datos.items():
            st.session_state[k] = v

def obtener_label_menu_por_modulo(modulo: str) -> str:
    if "Memoria" in modulo or "MTD" in modulo:
        return "🏛️ Memoria Técnica (MTD 30)"
    elif "Presupuesto" in modulo:
        return "🏡 Presupuesto Vivienda"
    elif "Previsión" in modulo:
        return "🏢 Previsión de Cargas (Pt)"
    elif "LGA" in modulo:
        return "⚡ Línea General (LGA)"
    elif "DI" in modulo:
        return "🔌 Derivación Individual (DI)"
    elif "IRVE" in modulo:
        return "🚗 Línea Recarga (IRVE)"
    elif "Cálculo Rápido" in modulo:
        return "🧮 Cálculo Rápido (CDT & Icc)"
    return "🏠 Menú Principal"
