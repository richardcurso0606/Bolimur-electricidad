# -*- coding: utf-8 -*-
"""
Módulo de Gestión de Clientes (CRM Eléctrico) y Gestor de Proyectos de Obra
Bolimur REBT PRO
Diseñado para Instaladores Electricistas Autorizados en Baja Tensión y Tramitación ante Industria.
Permite visualizar, registrar, editar, duplicar, grabar y borrar clientes y proyectos técnicos de forma ágil y visual.
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

    # Conteo de proyectos por cada cliente para badges informativos
    conteo_proyectos_por_cli = {}
    for p in todos_proyectos:
        c_id = p.get("cliente_id")
        if c_id:
            conteo_proyectos_por_cli[c_id] = conteo_proyectos_por_cli.get(c_id, 0) + 1

    # =========================================================================
    # CABECERA PRINCIPAL Y MÉTRICAS
    # =========================================================================
    col_t1, col_t2, col_t3, col_t4 = st.columns([2.6, 1.1, 1.1, 1.2])
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
        if tiene_nube:
            if st.button("⚡ Sincronizar Mi Nube", key="btn_sync_top", use_container_width=True, type="primary"):
                ok_s, msg_s = db_manager.sincronizar_con_nube(usuario_id)
                if ok_s:
                    st.success(f"✅ {msg_s}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg_s}")
        else:
            if st.button("🧹 Limpiar Duplicados", key="btn_limpiar_dup_top", use_container_width=True, help="Unifica clientes duplicados"):
                num_borrados = db_manager.limpiar_duplicados_clientes(usuario_id)
                if num_borrados > 0:
                    st.success(f"✅ Se han unificado y eliminado {num_borrados} fichas duplicadas.")
                    st.rerun()
                else:
                    st.info("No se encontraron clientes duplicados en tu cuenta.")

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

    # Notificaciones flotantes de acciones (si existen)
    if "crm_alerta_exito" in st.session_state:
        st.success(st.session_state["crm_alerta_exito"])
        del st.session_state["crm_alerta_exito"]

    # =========================================================================
    # PESTAÑAS PRINCIPALES DE GESTIÓN (ACCESIBLES Y MODERNAS)
    # =========================================================================
    nombre_cli_tab = f": {cliente_activo['nombre_completo'][:22]}..." if (cliente_activo and len(cliente_activo['nombre_completo']) > 22) else (f": {cliente_activo['nombre_completo']}" if cliente_activo else "")

    tab_directorio, tab_ficha, tab_editor, tab_nuevo_cliente, tab_todos_proyectos, tab_sincro = st.tabs([
        f"🗂️ Directorio de Clientes ({len(clientes)})",
        f"📋 Ficha Técnica 360°{nombre_cli_tab}",
        "✏️ Editar y Grabar",
        "➕ Alta de Nuevo Cliente",
        f"📂 Historial de Proyectos ({len(todos_proyectos)})",
        "☁️ Sincronización Nube"
    ])

    # =========================================================================
    # TAB 1: DIRECTORIO VISUAL DE CLIENTES (MÁS AMIGABLE, ACCIONES DIRECTAS)
    # =========================================================================
    with tab_directorio:
        if not clientes:
            st.info("ℹ️ Todavía no tienes clientes registrados bajo esta cuenta.")
            with st.container(border=True):
                st.markdown("##### 🔍 ¿Tenías clientes creados anteriormente o en el Servidor Nube?")
                st.write("Si diste de alta clientes en una sesión previa o en la base de datos de Supabase, puedes recuperarlos inmediatamente:")
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
            # Barra superior de búsqueda, filtros y modo de vista
            with st.container(border=True):
                col_b1, col_b2, col_b3, col_b4 = st.columns([2.8, 1.4, 1.4, 1.4])
                with col_b1:
                    filtro_txt = st.text_input(
                        "🔍 Buscar cliente:",
                        placeholder="Escribe nombre, NIF, teléfono, CUPS, población...",
                        key="crm_dir_search",
                        label_visibility="collapsed"
                    )
                with col_b2:
                    filtro_tipo = st.selectbox(
                        "Tipo Inmueble:",
                        options=["Todos los tipos", "Vivienda", "Local Comercial", "Nave Industrial", "Garaje / IRVE", "Edificio"],
                        key="crm_dir_filter_tipo",
                        label_visibility="collapsed"
                    )
                with col_b3:
                    orden_sel = st.selectbox(
                        "Ordenar por:",
                        options=["Nombre (A ➔ Z)", "Nombre (Z ➔ A)", "Más recientes", "Más antiguos"],
                        key="crm_dir_order",
                        label_visibility="collapsed"
                    )
                with col_b4:
                    modo_vista = st.radio(
                        "Vista:",
                        options=["🗂️ Tarjetas", "📊 Tabla"],
                        horizontal=True,
                        key="crm_dir_view_mode",
                        label_visibility="collapsed"
                    )

            # Filtrado en tiempo real
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

            # Ordenación
            if orden_sel == "Nombre (A ➔ Z)":
                clientes_filtrados.sort(key=lambda x: (x.get("nombre_completo") or "").lower())
            elif orden_sel == "Nombre (Z ➔ A)":
                clientes_filtrados.sort(key=lambda x: (x.get("nombre_completo") or "").lower(), reverse=True)
            elif orden_sel == "Más recientes":
                clientes_filtrados.sort(key=lambda x: x.get("id", 0), reverse=True)
            elif orden_sel == "Más antiguos":
                clientes_filtrados.sort(key=lambda x: x.get("id", 0))

            # Resumen de resultados
            col_info_c, col_info_btn = st.columns([3, 1])
            with col_info_c:
                st.caption(f"Mostrando **{len(clientes_filtrados)}** de **{len(clientes)}** clientes registrados en tu cuenta.")
            with col_info_btn:
                if filtro_txt or filtro_tipo != "Todos los tipos":
                    if st.button("✖️ Quitar Filtros", key="btn_clear_crm_filters", use_container_width=True):
                        st.session_state["crm_dir_search"] = ""
                        st.session_state["crm_dir_filter_tipo"] = "Todos los tipos"
                        st.rerun()

            # Confirmación de borrado pendiente en el Directorio
            cli_a_borrar_id = st.session_state.get("confirmar_borrado_cli_id")
            if cli_a_borrar_id:
                cli_del_obj = next((c for c in clientes if c["id"] == cli_a_borrar_id), None)
                if cli_del_obj:
                    st.error(f"⚠️ **¿Confirmas que deseas eliminar definitivamente a '{cli_del_obj['nombre_completo']}'?**")
                    st.write("Esta acción borrará al cliente de tu base de datos y de la nube Supabase, junto con sus proyectos asociados.")
                    c_del_b1, c_del_b2 = st.columns(2)
                    with c_del_b1:
                        if st.button("🔴 Sí, Eliminar Definitivamente", key="btn_conf_del_directorio", type="primary", use_container_width=True):
                            db_manager.eliminar_cliente(cli_a_borrar_id, usuario_id)
                            del st.session_state["confirmar_borrado_cli_id"]
                            if st.session_state.get("crm_cliente_seleccionado_id") == cli_a_borrar_id:
                                st.session_state["crm_cliente_seleccionado_id"] = None
                                st.session_state["cliente_activo_proyecto"] = None
                            st.session_state["crm_alerta_exito"] = f"🗑️ Cliente '{cli_del_obj['nombre_completo']}' eliminado correctamente."
                            st.rerun()
                    with c_del_b2:
                        if st.button("🛡️ Cancelar", key="btn_cancel_del_directorio", use_container_width=True):
                            del st.session_state["confirmar_borrado_cli_id"]
                            st.rerun()
                    st.divider()

            # -------------------------------------------------------------
            # MODO 1: VISTA DE TARJETAS VISUALES (RECOMENDADO / AMIGABLE)
            # -------------------------------------------------------------
            if modo_vista == "🗂️ Tarjetas":
                if not clientes_filtrados:
                    st.warning("No se encontraron clientes que coincidan con los criterios de búsqueda.")
                else:
                    for c in clientes_filtrados:
                        es_seleccionado = (cliente_activo and cliente_activo["id"] == c["id"])
                        num_proys = conteo_proyectos_por_cli.get(c["id"], 0)
                        
                        # Borde destacado si es el cliente activo
                        borde_estilo = "border: 2px solid #0284c7; background: #f0f9ff;" if es_seleccionado else "border: 1.5px solid #e2e8f0; background: #ffffff;"
                        
                        with st.container(border=True):
                            # Cabecera de la tarjeta: Nombre + Badges + Obras
                            col_card_t1, col_card_t2 = st.columns([3.2, 1.3])
                            with col_card_t1:
                                badge_sel = " ⭐ **ACTIVO**" if es_seleccionado else ""
                                st.markdown(f"### 👤 {c['nombre_completo']}{badge_sel}")
                                
                                chips = []
                                chips.append(f"🏷️ `{c.get('tipo_inmueble') or 'Vivienda'}`")
                                if c.get("nif_cif"):
                                    chips.append(f"🆔 `{c['nif_cif']}`")
                                loc = c.get('localidad') or c.get('municipio') or c.get('provincia') or ''
                                if loc:
                                    chips.append(f"📍 `{loc}`")
                                st.markdown(" ".join(chips))
                            
                            with col_card_t2:
                                st.markdown(
                                    f"<div style='text-align:right; margin-top:4px;'>"
                                    f"<span style='background:#e0f2fe; color:#0369a1; padding:6px 12px; border-radius:12px; font-weight:700; font-size:13px;'>"
                                    f"📁 {num_proys} obra{'s' if num_proys != 1 else ''}</span></div>",
                                    unsafe_allow_html=True
                                )

                            # Datos clave en 3 columnas
                            col_d1, col_d2, col_d3 = st.columns(3)
                            with col_d1:
                                st.markdown("**📞 Contacto:**")
                                st.markdown(f"Teléfono: `{c.get('telefono') or '-'}`")
                                st.markdown(f"Email: `{c.get('email') or '-'}`")
                            with col_d2:
                                st.markdown("**📍 Emplazamiento:**")
                                st.markdown(f"Dirección: `{c.get('direccion_suministro') or '-'}`")
                                st.markdown(f"CP / Prov: `{c.get('codigo_postal') or '-'} | {c.get('provincia') or 'Murcia'}`")
                            with col_d3:
                                st.markdown("**⚡ Suministro Eléctrico:**")
                                st.markdown(f"CUPS: `{c.get('cups') or '-'}`")
                                st.markdown(f"Potencia: `{c.get('potencia_contratada_kw') or '-'} kW` ({c.get('tension_suministro') or '230V'})")

                            # Botonera de acciones directas (Ver, Editar, Copiar/Duplicar, Borrar)
                            st.markdown("<hr style='margin: 8px 0 10px 0;'>", unsafe_allow_html=True)
                            c_btn1, c_btn2, c_btn3, c_btn4 = st.columns([1.5, 1.2, 1.3, 1])
                            
                            with c_btn1:
                                if st.button("📋 Ver Ficha 360°", key=f"btn_ver_card_{c['id']}", use_container_width=True, type="primary" if not es_seleccionado else "secondary"):
                                    st.session_state["crm_cliente_seleccionado_id"] = c["id"]
                                    st.session_state["cliente_activo_proyecto"] = c
                                    st.rerun()
                            with c_btn2:
                                if st.button("✏️ Editar", key=f"btn_edit_card_{c['id']}", use_container_width=True):
                                    st.session_state["crm_cliente_seleccionado_id"] = c["id"]
                                    st.session_state["cliente_activo_proyecto"] = c
                                    st.session_state["crm_abrir_editor_directo"] = True
                                    st.rerun()
                            with c_btn3:
                                if st.button("📋 Duplicar", key=f"btn_dup_card_{c['id']}", use_container_width=True, help="Clona esta ficha para registrar un nuevo suministro o local del mismo titular"):
                                    copia_data = dict(c)
                                    copia_data.pop("id", None)
                                    copia_data["nombre_completo"] = f"{c['nombre_completo']} (Nuevo Suministro)"
                                    ok_dup, nuevo_id = db_manager.crear_cliente(usuario_id, copia_data)
                                    if ok_dup:
                                        st.session_state["crm_cliente_seleccionado_id"] = nuevo_id
                                        st.session_state["crm_alerta_exito"] = f"✅ Ficha duplicada con éxito como '{copia_data['nombre_completo']}'. Ahora puedes editar su dirección y CUPS."
                                        st.rerun()
                            with c_btn4:
                                if st.button("🗑️ Borrar", key=f"btn_del_card_{c['id']}", use_container_width=True):
                                    st.session_state["confirmar_borrado_cli_id"] = c["id"]
                                    st.rerun()

            # -------------------------------------------------------------
            # MODO 2: VISTA TABLA COMPACTA
            # -------------------------------------------------------------
            else:
                filas_tabla = []
                for c in clientes_filtrados:
                    filas_tabla.append({
                        "ID": c["id"],
                        "Titular": c["nombre_completo"],
                        "NIF": c.get("nif_cif", "-"),
                        "Teléfono": c.get("telefono", "-"),
                        "Población": c.get("localidad") or c.get("municipio") or "-",
                        "CUPS": c.get("cups", "-"),
                        "Potencia": f"{c.get('potencia_contratada_kw', '-')} kW",
                        "Distribuidora": c.get("distribuidora", "-"),
                        "Obras": conteo_proyectos_por_cli.get(c["id"], 0)
                    })
                st.dataframe(pd.DataFrame(filas_tabla), use_container_width=True, hide_index=True)
                st.caption("ℹ️ Para editar o consultar la ficha completa de un cliente, utiliza el selector de cliente arriba o la vista '🗂️ Tarjetas'.")

    # =========================================================================
    # TAB 2: FICHA TÉCNICA 360° DEL CLIENTE ACTIVO
    # =========================================================================
    with tab_ficha:
        if not clientes:
            st.info("No hay clientes registrados para mostrar su expediente.")
        else:
            # Selector rápido accesible en la parte superior
            nombres_dict = {
                c["id"]: f"👤 {c['nombre_completo']} | 🆔 {c.get('nif_cif', '-')} | 📍 {c.get('localidad', c.get('municipio', ''))}"
                for c in clientes
            }
            cliente_sel_idx = list(nombres_dict.keys()).index(st.session_state["crm_cliente_seleccionado_id"]) if st.session_state["crm_cliente_seleccionado_id"] in nombres_dict else 0
            
            col_sel_c1, col_sel_c2 = st.columns([3, 1.2])
            with col_sel_c1:
                nuevo_sel = st.selectbox(
                    "Expediente activo actual:",
                    options=list(nombres_dict.keys()),
                    index=cliente_sel_idx,
                    format_func=lambda x: nombres_dict[x],
                    key="crm_sel_combo_ficha"
                )
                if nuevo_sel != st.session_state["crm_cliente_seleccionado_id"]:
                    st.session_state["crm_cliente_seleccionado_id"] = nuevo_sel
                    st.session_state["cliente_activo_proyecto"] = db_manager.obtener_cliente_por_id(nuevo_sel, usuario_id)
                    st.rerun()

            cliente_actual = db_manager.obtener_cliente_por_id(st.session_state["crm_cliente_seleccionado_id"], usuario_id)
            if cliente_actual:
                st.session_state["cliente_activo_proyecto"] = cliente_actual

                # Barra de herramientas superior del cliente (Editar, Copiar, Grabar, Borrar)
                with st.container(border=True):
                    col_act_top1, col_act_top2, col_act_top3, col_act_top4 = st.columns([1.5, 1.5, 1.5, 1.2])
                    with col_act_top1:
                        if st.button("✏️ Editar Ficha", key="btn_go_edit_ficha_top", type="primary", use_container_width=True):
                            st.session_state["crm_abrir_editor_directo"] = True
                            st.rerun()
                    with col_act_top2:
                        if st.button("📋 Duplicar Suministro", key="btn_dup_ficha_top", use_container_width=True):
                            copia_data = dict(cliente_actual)
                            copia_data.pop("id", None)
                            copia_data["nombre_completo"] = f"{cliente_actual['nombre_completo']} (Nuevo Suministro)"
                            ok_dup, nuevo_id = db_manager.crear_cliente(usuario_id, copia_data)
                            if ok_dup:
                                st.session_state["crm_cliente_seleccionado_id"] = nuevo_id
                                st.session_state["crm_alerta_exito"] = f"✅ Ficha duplicada como '{copia_data['nombre_completo']}'. Pasa a la pestaña '✏️ Editar y Grabar' para modificarla."
                                st.rerun()
                    with col_act_top3:
                        with st.popover("📋 Copiar Resumen", use_container_width=True):
                            st.markdown("##### 📋 Resumen Listo para Copiar (WhatsApp / Email):")
                            texto_portapapeles = generar_resumen_portapapeles(cliente_actual)
                            st.code(texto_portapapeles, language="text")
                            st.caption("Haz clic en el icono superior derecho del cuadro para copiar todo el texto al portapapeles en 1 clic.")
                    with col_act_top4:
                        if st.button("🗑️ Borrar", key="btn_del_ficha_top", use_container_width=True):
                            st.session_state["confirmar_borrado_cli_id"] = cliente_actual["id"]
                            st.rerun()

                # Confirmación de borrado en Ficha 360° si está activa
                if st.session_state.get("confirmar_borrado_cli_id") == cliente_actual["id"]:
                    st.error(f"⚠️ ¿Confirmas la eliminación definitiva de '{cliente_actual['nombre_completo']}'?")
                    cb_f1, cb_f2 = st.columns(2)
                    with cb_f1:
                        if st.button("🔴 Confirmar Eliminación", key="btn_conf_del_ficha_360", type="primary", use_container_width=True):
                            db_manager.eliminar_cliente(cliente_actual["id"], usuario_id)
                            del st.session_state["confirmar_borrado_cli_id"]
                            st.session_state["crm_cliente_seleccionado_id"] = None
                            st.session_state["cliente_activo_proyecto"] = None
                            st.session_state["crm_alerta_exito"] = "🗑️ Cliente eliminado correctamente."
                            st.rerun()
                    with cb_f2:
                        if st.button("🛡️ Cancelar", key="btn_cancel_del_ficha_360", use_container_width=True):
                            del st.session_state["confirmar_borrado_cli_id"]
                            st.rerun()

                # Tarjetas de Información 360°
                st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">👤 Ficha Técnica 360º del Cliente</h4></div>', unsafe_allow_html=True)
                with st.container(border=True):
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        st.markdown("##### 🏷️ Titular y Contacto:")
                        st.markdown(f"**Nombre / Razón Social:** `{cliente_actual['nombre_completo']}`")
                        st.markdown(f"**NIF / DNI / CIF:** `{cliente_actual.get('nif_cif') or '-'}`")
                        st.markdown(f"**Teléfono:** `{cliente_actual.get('telefono') or '-'}`")
                        st.markdown(f"**Email:** `{cliente_actual.get('email') or '-'}`")
                        st.markdown(f"**Tipo Inmueble:** `{cliente_actual.get('tipo_inmueble') or 'Vivienda'}`")

                    with col_f2:
                        st.markdown("##### ⚡ Datos del Punto de Suministro:")
                        st.markdown(f"**Dirección:** `{cliente_actual.get('direccion_suministro') or '-'}`")
                        st.markdown(f"**Población / CP:** `{cliente_actual.get('localidad') or cliente_actual.get('municipio') or '-'} ({cliente_actual.get('codigo_postal') or ''})`")
                        st.markdown(f"**Provincia:** `{cliente_actual.get('provincia') or 'Murcia'}`")
                        st.markdown(f"**Distribuidora:** `{cliente_actual.get('distribuidora') or 'i-DE (Iberdrola)'}`")

                    with col_f3:
                        st.markdown("##### 🏛️ Datos para Industria / Compañía:")
                        st.markdown(f"**Código CUPS:** `{cliente_actual.get('cups') or '-'}`")
                        st.markdown(f"**Ref. Catastral:** `{cliente_actual.get('referencia_catastral') or '-'}`")
                        st.markdown(f"**Potencia Contratada:** `{cliente_actual.get('potencia_contratada_kw') or '-'} kW`")
                        st.markdown(f"**Tensión:** `{cliente_actual.get('tension_suministro') or 'Monofásica 230V'}`")

                    if cliente_actual.get("notas"):
                        st.info(f"📝 **Notas y Observaciones de Obra:** {cliente_actual['notas']}")

                # Botonera de Lanzamiento Directo a Cálculos (1 Clic)
                st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🚀 Acciones Rápidas con este Cliente (1 Clic)</h4></div>', unsafe_allow_html=True)
                with st.container(border=True):
                    c_act1, c_act2, c_act3, c_act4 = st.columns(4)
                    with c_act1:
                        if st.button("🏛️ Iniciar Boletín CIE / MTD", key=f"btn_act_cie_{cliente_actual['id']}", use_container_width=True, type="primary"):
                            st.session_state["cliente_activo_proyecto"] = cliente_actual
                            st.session_state["menu_activo"] = "🏛️ Memoria Técnica (MTD 30)"
                            st.rerun()
                    with c_act2:
                        if st.button("🏡 Iniciar Presupuesto", key=f"btn_act_pres_{cliente_actual['id']}", use_container_width=True):
                            st.session_state["cliente_activo_proyecto"] = cliente_actual
                            st.session_state["menu_activo"] = "🏡 Presupuesto Vivienda"
                            st.rerun()
                    with c_act3:
                        if st.button("🚗 Iniciar Recarga IRVE", key=f"btn_act_irve_{cliente_actual['id']}", use_container_width=True):
                            st.session_state["cliente_activo_proyecto"] = cliente_actual
                            st.session_state["menu_activo"] = "🚗 Línea Recarga (IRVE)"
                            st.rerun()
                    with c_act4:
                        if st.button("🔌 Calcular DI / LGA", key=f"btn_act_di_{cliente_actual['id']}", use_container_width=True):
                            st.session_state["cliente_activo_proyecto"] = cliente_actual
                            st.session_state["menu_activo"] = "🔌 Derivación Individual (DI)"
                            st.rerun()

                # Listado de Proyectos del Cliente
                st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">📁 Proyectos y Cálculos Guardados de este Cliente</h4></div>', unsafe_allow_html=True)
                proyectos_cliente = db_manager.listar_proyectos_por_cliente(cliente_actual["id"], usuario_id)
                
                if not proyectos_cliente:
                    st.info("ℹ️ No hay cálculos ni presupuestos guardados todavía para este cliente. Realiza un cálculo en cualquiera de los módulos y guárdalo asociándolo a esta ficha.")
                else:
                    for proj in proyectos_cliente:
                        with st.container(border=True):
                            col_p1, col_p2, col_p3, col_p4 = st.columns([3.5, 2.5, 2, 1.2])
                            with col_p1:
                                st.markdown(f"**📌 {proj['nombre_proyecto']}**")
                                st.caption(f"Módulo: `{proj['modulo']}` | Fecha: {proj.get('fecha_guardado', '')[:16]}")
                            with col_p2:
                                st.markdown(f"**Resumen Técnico:**  \n{proj.get('resumen_potencia_o_importe', '-')}")
                            with col_p3:
                                if st.button("🚀 Cargar y Modificar", key=f"btn_load_p_{proj['id']}", type="primary", use_container_width=True):
                                    datos_p = db_manager.cargar_proyecto_por_id(proj["id"], usuario_id)
                                    if datos_p:
                                        cargar_proyecto_en_session(proj["modulo"], datos_p.get("datos", {}), cliente_actual)
                                        st.session_state.menu_activo = obtener_label_menu_por_modulo(proj["modulo"])
                                        st.rerun()
                            with col_p4:
                                if st.button("🗑️ Borrar", key=f"btn_del_p_{proj['id']}", use_container_width=True):
                                    db_manager.eliminar_proyecto(proj["id"], usuario_id)
                                    st.rerun()

    # =========================================================================
    # TAB 3: EDITOR DE FICHA DEDICADO ("EDITAR Y GRABAR" ACCESIBLE)
    # =========================================================================
    with tab_editor:
        if not clientes:
            st.info("No hay clientes registrados para editar.")
        else:
            # Selector del cliente a editar
            nombres_edit_dict = {c["id"]: c["nombre_completo"] for c in clientes}
            cliente_edit_id = st.session_state.get("crm_cliente_seleccionado_id")
            if cliente_edit_id not in nombres_edit_dict:
                cliente_edit_id = list(nombres_edit_dict.keys())[0]

            col_ed_sel, col_ed_btns = st.columns([3, 2])
            with col_ed_sel:
                cliente_edit_id = st.selectbox(
                    "Selecciona el cliente a editar:",
                    options=list(nombres_edit_dict.keys()),
                    index=list(nombres_edit_dict.keys()).index(cliente_edit_id),
                    format_func=lambda x: nombres_edit_dict[x],
                    key="crm_sel_edit_client"
                )
                st.session_state["crm_cliente_seleccionado_id"] = cliente_edit_id

            c_edit = db_manager.obtener_cliente_por_id(cliente_edit_id, usuario_id)
            if c_edit:
                st.markdown(f'<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">✏️ Editando Expediente de: {c_edit["nombre_completo"]} (ID: #{c_edit["id"]})</h4></div>', unsafe_allow_html=True)
                st.caption("Modifica cualquiera de los datos del titular o del punto de suministro y pulsa **'💾 Grabar Cambios'** para actualizarlo de inmediato.")

                with st.form(f"form_editor_cliente_crm_{c_edit['id']}"):
                    # 1. DATOS DEL TITULAR
                    st.markdown("##### 👤 1. Datos del Titular y Contacto:")
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        enom = st.text_input("Nombre y Apellidos o Razón Social (*):", value=c_edit["nombre_completo"])
                        enif = st.text_input("NIF / DNI / CIF:", value=c_edit.get("nif_cif", ""))
                        etel = st.text_input("Teléfono de Contacto:", value=c_edit.get("telefono", ""))
                    with col_e2:
                        eemail = st.text_input("Email:", value=c_edit.get("email", ""))
                        tipos_inm = ["Vivienda Residencial", "Local Comercial", "Nave Industrial", "Garaje Comunitario / IRVE", "Edificio de Viviendas"]
                        tipo_actual = c_edit.get("tipo_inmueble", "Vivienda Residencial")
                        idx_tipo = 0
                        for i, t in enumerate(tipos_inm):
                            if t.lower() in tipo_actual.lower() or tipo_actual.lower() in t.lower():
                                idx_tipo = i
                                break
                        etipo = st.selectbox("Tipo de Inmueble / Suministro:", tipos_inm, index=idx_tipo)

                    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

                    # 2. UBICACIÓN Y DIRECCIÓN
                    st.markdown("##### 📍 2. Emplazamiento del Suministro:")
                    col_e3, col_e4 = st.columns(2)
                    with col_e3:
                        edir = st.text_input("Dirección del Suministro:", value=c_edit.get("direccion_suministro", ""))
                        ecp = st.text_input("Código Postal:", value=c_edit.get("codigo_postal", "30000"))
                    with col_e4:
                        eloc = st.text_input("Municipio / Población:", value=c_edit.get("localidad") or c_edit.get("municipio") or "Murcia")
                        eprov = st.text_input("Provincia:", value=c_edit.get("provincia", "Murcia"))

                    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

                    # 3. DATOS ELÉCTRICOS REBT
                    st.markdown("##### ⚡ 3. Parámetros Técnicos REBT e Industria:")
                    col_e5, col_e6 = st.columns(2)
                    with col_e5:
                        ecups = st.text_input("Código CUPS (20-22 caracteres):", value=c_edit.get("cups", ""))
                        eref = st.text_input("Referencia Catastral (20 caracteres):", value=c_edit.get("referencia_catastral", ""))
                        dists = ["i-DE (Iberdrola)", "Endesa e-distribución", "UFD (Naturgy)", "E-Redes (EDP)", "Otras Distribuidoras"]
                        dist_act = c_edit.get("distribuidora", "i-DE (Iberdrola)")
                        idx_dist = 0
                        for i, d in enumerate(dists):
                            if d.lower() in dist_act.lower() or dist_act.lower() in d.lower():
                                idx_dist = i
                                break
                        edist = st.selectbox("Distribuidora Eléctrica:", dists, index=idx_dist)
                    with col_e6:
                        epot = st.text_input("Potencia Contratada / Prevista (kW):", value=c_edit.get("potencia_contratada_kw", "5.75"))
                        tensiones = ["Monofásica 230V", "Trifásica 400V", "Trifásica 230V"]
                        tens_act = c_edit.get("tension_suministro", "Monofásica 230V")
                        idx_tens = 0
                        for i, tn in enumerate(tensiones):
                            if tn.lower() in tens_act.lower() or tens_act.lower() in tn.lower():
                                idx_tens = i
                                break
                        etens = st.selectbox("Tensión de Suministro:", tensiones, index=idx_tens)

                    enotas = st.text_area("Observaciones y Notas Técnicas de Obra:", value=c_edit.get("notas", ""))

                    # BOTONERA DE GRABAR CAMBIOS
                    st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)
                    col_sav1, col_sav2 = st.columns([2.5, 1])
                    with col_sav1:
                        btn_grabar = st.form_submit_button("💾 Grabar y Guardar Cambios en este Cliente", type="primary", use_container_width=True)
                    with col_sav2:
                        btn_cancel = st.form_submit_button("✖️ Descartar Cambios", use_container_width=True)

                    if btn_grabar:
                        if not enom.strip():
                            st.error("El nombre del cliente no puede estar vacío.")
                        else:
                            ok_up = db_manager.actualizar_cliente(c_edit["id"], usuario_id, {
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
                                "tension_suministro": etens,
                                "tipo_inmueble": etipo,
                                "notas": enotas.strip()
                            })
                            if ok_up:
                                st.session_state["crm_cliente_seleccionado_id"] = c_edit["id"]
                                st.session_state["crm_alerta_exito"] = f"💾 ¡Ficha de '{enom}' grabada y sincronizada correctamente!"
                                st.rerun()
                            else:
                                st.error("Error al guardar los cambios en la base de datos.")

                    if btn_cancel:
                        st.info("Cambios descartados.")
                        st.rerun()

    # =========================================================================
    # TAB 4: ALTA RÁPIDA DE NUEVO CLIENTE (CON PREVENCIÓN DE DUPLICADOS)
    # =========================================================================
    with tab_nuevo_cliente:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">➕ Alta Rápida de Nueva Ficha de Cliente</h4></div>', unsafe_allow_html=True)
        st.caption("Introduce los datos del titular y del punto de suministro. Se utilizarán automáticamente en los presupuestos, memorias técnicas MTD y boletines CIE oficiales.")

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
    # TAB 5: HISTORIAL GLOBAL DE PROYECTOS Y OBRAS
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
    # TAB 6: SINCRONIZACIÓN Y BASE DE DATOS EN LA NUBE (SUPABASE)
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
