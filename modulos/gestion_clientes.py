# -*- coding: utf-8 -*-
"""
Módulo de Gestión de Clientes (CRM Eléctrico) y Gestor de Proyectos de Obra
Diseñado para Instaladores Electricistas Autorizados en Baja Tensión y Tramitación ante Industria
Permite almacenar expedientes de clientes, suministros, CUPS, distribuidoras y asociar cálculos técnicos.
"""

import streamlit as st
import pandas as pd
from modulos import db_manager, auth_manager

def renderizar():
    usuario = auth_manager.obtener_usuario_actual()
    if not usuario:
        st.warning("Debes iniciar sesión para gestionar tus clientes y proyectos.")
        return

    usuario_id = usuario["id"]
    user_email = (usuario.get("email") or "").strip().lower()
    user_nom = usuario.get("nombre_instalador") or usuario.get("nombre_empresa") or "Instalador"

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

    # Cabecera Principal y Métricas
    col_t1, col_t2, col_t3, col_t4 = st.columns([2.8, 1, 1, 1.2])
    with col_t1:
        st.title("👥 Expedientes de Clientes y Obras")
        if tiene_nube:
            st.markdown(f"🟢 **Nube Sincronizada (Supabase)** — Base de datos privada de `{user_email}`.")
        else:
            st.markdown(f"🔒 **Base de Datos Privada e Independiente** — Cuenta: `{user_email}`.")
    with col_t2:
        st.metric("Tus Clientes", f"{len(clientes)} clientes")
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
            if st.button("🧹 Limpiar Duplicados", key="btn_limpiar_dup_top", use_container_width=True, help="Si registraste un cliente varias veces por error en tu cuenta, este botón unifica sus fichas automáticamente"):
                num_borrados = db_manager.limpiar_duplicados_clientes(usuario_id)
                if num_borrados > 0:
                    st.success(f"✅ Se han unificado y eliminado {num_borrados} fichas duplicadas.")
                    st.rerun()
                else:
                    st.info("No se encontraron clientes duplicados en tu cuenta.")

    tab_clientes_lista, tab_nuevo_cliente, tab_todos_proyectos, tab_sincro = st.tabs([
        "📋 Expediente y Ficha del Cliente",
        "➕ Alta de Nuevo Cliente",
        "📂 Historial Global de Proyectos",
        "☁️ Sincronización y Base de Datos Nube"
    ])

    # =========================================================================
    # TAB 1: EXPEDIENTE Y FICHA TÉCNICA DEL CLIENTE
    # =========================================================================
    with tab_clientes_lista:
        if not clientes:
            st.info("ℹ️ Todavía no tienes clientes visibles bajo esta cuenta.")
            with st.container(border=True):
                st.markdown("##### 🔍 ¿Tenías clientes creados anteriormente?")
                st.write("Si diste de alta clientes antes de iniciar sesión con tu cuenta de Google (`richardcurso0606@gmail.com`) o en una sesión previa, puedes buscarlos en la base de datos para vincularlos a tu cuenta actual:")
                if st.button("🔄 Recuperar y Vincular Clientes Anteriores a mi Cuenta", key="btn_recup_clientes_empty", type="primary"):
                    recup = db_manager.recuperar_todos_clientes_locales(usuario_id)
                    if recup > 0:
                        st.success(f"✅ ¡Se han recuperado y vinculado {recup} expedientes a tu cuenta!")
                        st.rerun()
                    else:
                        st.warning("⚠️ No se encontraron clientes en el almacenamiento de este servidor. En Streamlit Cloud (`*.streamlit.app`), el servidor web es temporal y reinicia su disco cada vez que se actualiza el código desde GitHub. Para que tus clientes y obras queden guardados **de forma permanente 24/7**, conecta Supabase en la pestaña **'☁️ Sincronización y Base de Datos Nube'**.")
        else:
            # Buscador en tiempo real de clientes
            col_b1, col_b2 = st.columns([2, 3])
            with col_b1:
                filtro_cli = st.text_input("🔍 Buscar cliente (Nombre, NIF, Teléfono, CUPS o Población):", key="filtro_crm_cli", placeholder="Escribe aquí...")

            clientes_filtrados = clientes
            if filtro_cli:
                q = filtro_cli.strip().lower()
                clientes_filtrados = [
                    c for c in clientes
                    if q in (c.get("nombre_completo") or "").lower()
                    or q in (c.get("nif_cif") or "").lower()
                    or q in (c.get("telefono") or "").lower()
                    or q in (c.get("cups") or "").lower()
                    or q in (c.get("direccion_suministro") or "").lower()
                    or q in (c.get("localidad") or "").lower()
                ]

            if not clientes_filtrados:
                st.warning(f"No se encontraron clientes que coincidan con '{filtro_cli}'. Mostrando todos.")
                clientes_filtrados = clientes

            nombres_dict = {
                c["id"]: f"👤 {c['nombre_completo']} | NIF: {c.get('nif_cif', '-')} | 📍 {c.get('localidad', c.get('municipio', ''))}"
                for c in clientes_filtrados
            }

            with col_b2:
                cliente_sel_id = st.selectbox(
                    "Selecciona el Cliente a gestionar:",
                    options=list(nombres_dict.keys()),
                    format_func=lambda x: nombres_dict[x],
                    key="crm_sel_cliente_activo"
                )

            cliente_actual = db_manager.obtener_cliente_por_id(cliente_sel_id, usuario_id)
            if cliente_actual:
                # Guardar cliente activo en session_state para que otros módulos lo tomen
                st.session_state["cliente_activo_proyecto"] = cliente_actual

                st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">👤 Ficha Técnica 360º del Cliente</h4></div>', unsafe_allow_html=True)
                
                with st.container(border=True):
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        st.markdown("##### 🏷️ Titular y Contacto:")
                        st.markdown(f"**Nombre / Razón Social:** `{cliente_actual['nombre_completo']}`")
                        st.markdown(f"**NIF / DNI / CIF:** `{cliente_actual.get('nif_cif') or '-'}`")
                        st.markdown(f"**Teléfono:** `{cliente_actual.get('telefono') or '-'}`")
                        st.markdown(f"**Email:** `{cliente_actual.get('email') or '-'}`")

                    with col_f2:
                        st.markdown("##### ⚡ Datos del Punto de Suministro:")
                        st.markdown(f"**Dirección:** `{cliente_actual.get('direccion_suministro') or '-'}`")
                        st.markdown(f"**Población / CP:** `{cliente_actual.get('localidad') or cliente_actual.get('municipio') or '-'} {('(' + cliente_actual.get('codigo_postal') + ')') if cliente_actual.get('codigo_postal') else ''}`")
                        st.markdown(f"**Provincia:** `{cliente_actual.get('provincia') or 'Murcia'}`")
                        st.markdown(f"**Distribuidora:** `{cliente_actual.get('distribuidora') or 'i-DE (Iberdrola)'}`")

                    with col_f3:
                        st.markdown("##### 🏛️ Datos para Industria / Compañía:")
                        st.markdown(f"**Código CUPS:** `{cliente_actual.get('cups') or '-'}`")
                        st.markdown(f"**Ref. Catastral:** `{cliente_actual.get('referencia_catastral') or '-'}`")
                        st.markdown(f"**Potencia y Tensión:** `{cliente_actual.get('potencia_contratada_kw') or '-'} kW | {cliente_actual.get('tension_suministro') or '230V'}`")
                        st.markdown(f"**Tipo Inmueble:** `{cliente_actual.get('tipo_inmueble') or 'Vivienda'}`")

                    if cliente_actual.get("notas"):
                        st.info(f"📝 **Notas y Observaciones de Obra:** {cliente_actual['notas']}")

                # Botonera de Acciones Rápidas para el Instalador de Calle
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
                proyectos_cliente = db_manager.listar_proyectos_por_cliente(cliente_sel_id, usuario_id)
                
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
                                if st.button(f"🚀 Cargar y Modificar", key=f"btn_load_p_{proj['id']}", type="primary", use_container_width=True):
                                    datos_p = db_manager.cargar_proyecto_por_id(proj["id"], usuario_id)
                                    if datos_p:
                                        cargar_proyecto_en_session(proj["modulo"], datos_p.get("datos", {}), cliente_actual)
                                        st.session_state.menu_activo = obtener_label_menu_por_modulo(proj["modulo"])
                                        st.success(f"✅ ¡Proyecto cargado! Redirigiendo...")
                                        st.rerun()
                            with col_p4:
                                if st.button("🗑️ Borrar", key=f"btn_del_p_{proj['id']}", use_container_width=True):
                                    db_manager.eliminar_proyecto(proj["id"], usuario_id)
                                    st.rerun()

                # Editar / Eliminar Ficha
                with st.expander("✏️ Editar o Eliminar la Ficha de este Cliente"):
                    with st.form(f"form_edit_cli_{cliente_actual['id']}"):
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            enom = st.text_input("Nombre y Apellidos o Razón Social (*):", value=cliente_actual["nombre_completo"])
                            enif = st.text_input("NIF / DNI / CIF:", value=cliente_actual.get("nif_cif", ""))
                            etel = st.text_input("Teléfono de Contacto:", value=cliente_actual.get("telefono", ""))
                            eemail = st.text_input("Email:", value=cliente_actual.get("email", ""))
                            etipo = st.selectbox("Tipo de Inmueble:", ["Vivienda Residencial", "Local Comercial", "Nave Industrial", "Garaje Comunitario / IRVE", "Edificio de Viviendas"], index=0)
                        with ce2:
                            edir = st.text_input("Dirección del Suministro:", value=cliente_actual.get("direccion_suministro", ""))
                            ecp = st.text_input("Código Postal:", value=cliente_actual.get("codigo_postal", "30000"))
                            eloc = st.text_input("Municipio / Población:", value=cliente_actual.get("localidad") or cliente_actual.get("municipio") or "Murcia")
                            eprov = st.text_input("Provincia:", value=cliente_actual.get("provincia", "Murcia"))
                            ecups = st.text_input("Código CUPS:", value=cliente_actual.get("cups", ""))
                            eref = st.text_input("Referencia Catastral:", value=cliente_actual.get("referencia_catastral", ""))
                            edist = st.selectbox("Distribuidora:", ["i-DE (Iberdrola)", "Endesa e-distribución", "UFD (Naturgy)", "E-Redes (EDP)", "Otras Distribuidoras"], index=0)
                            epot = st.text_input("Potencia Contratada (kW):", value=cliente_actual.get("potencia_contratada_kw", "5.75"))
                        
                        enotas = st.text_area("Observaciones y Notas Técnicas de Obra:", value=cliente_actual.get("notas", ""))
                        
                        col_ebtn1, col_ebtn2 = st.columns(2)
                        with col_ebtn1:
                            if st.form_submit_button("💾 Guardar Modificaciones", type="primary", use_container_width=True):
                                if not enom.strip():
                                    st.error("El nombre del cliente no puede estar vacío.")
                                else:
                                    db_manager.actualizar_cliente(cliente_actual["id"], usuario_id, {
                                        "nombre_completo": enom, "nif_cif": enif, "telefono": etel, "email": eemail,
                                        "direccion_suministro": edir, "localidad": eloc, "codigo_postal": ecp,
                                        "municipio": eloc, "provincia": eprov, "cups": ecups, "referencia_catastral": eref,
                                        "distribuidora": edist, "potencia_contratada_kw": epot, "tipo_inmueble": etipo,
                                        "notas": enotas
                                    })
                                    st.success("✅ Ficha técnica del cliente actualizada.")
                                    st.rerun()
                    
                    if st.button("🗑️ Eliminar Definitivamente este Cliente", key=f"btn_del_cli_{cliente_actual['id']}"):
                        db_manager.eliminar_cliente(cliente_actual["id"], usuario_id)
                        st.warning("Cliente y proyectos asociados eliminados.")
                        st.rerun()

    # =========================================================================
    # TAB 2: ALTA RÁPIDA DE NUEVO CLIENTE CON PREVENCIÓN DE DUPLICADOS
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
                
                btn_crear_c = st.form_submit_button("✨ Guardar y Registrar Ficha del Cliente", type="primary", use_container_width=True)
                if btn_crear_c:
                    if not n_nom.strip():
                        st.error("El nombre del cliente es obligatorio.")
                    else:
                        # Comprobar si ya existe un cliente duplicado
                        dup = db_manager.buscar_cliente_duplicado(usuario_id, n_nif, n_nom)
                        if dup:
                            st.warning(f"⚠️ Ya existe una ficha registrada con este NIF o Nombre: **'{dup['nombre_completo']}'** (ID: {dup['id']}). Hemos actualizado sus datos para no duplicar fichas.")
                            db_manager.actualizar_cliente(dup["id"], usuario_id, {
                                "nombre_completo": n_nom, "nif_cif": n_nif, "telefono": n_tel, "email": n_email,
                                "direccion_suministro": n_dir, "localidad": n_loc, "codigo_postal": n_cp,
                                "municipio": n_loc, "provincia": n_prov, "cups": n_cups, "referencia_catastral": n_ref,
                                "distribuidora": n_dist, "potencia_contratada_kw": n_pot, "tipo_inmueble": n_tipo,
                                "notas": n_notas
                            })
                            st.session_state["cliente_activo_proyecto"] = dup
                            st.rerun()
                        else:
                            ok, nuevo_c_id = db_manager.crear_cliente(usuario_id, {
                                "nombre_completo": n_nom, "nif_cif": n_nif, "telefono": n_tel, "email": n_email,
                                "direccion_suministro": n_dir, "localidad": n_loc, "codigo_postal": n_cp,
                                "municipio": n_loc, "provincia": n_prov, "cups": n_cups, "referencia_catastral": n_ref,
                                "distribuidora": n_dist, "potencia_contratada_kw": n_pot, "tipo_inmueble": n_tipo,
                                "notas": n_notas
                            })
                            if ok:
                                st.success(f"✅ ¡Cliente '{n_nom}' registrado correctamente con ID #{nuevo_c_id}!")
                                st.rerun()
                            else:
                                st.error("Error al registrar cliente en la base de datos.")

    # =========================================================================
    # TAB 3: HISTORIAL GLOBAL DE PROYECTOS
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
    # TAB 4: SINCRONIZACIÓN Y BASE DE DATOS EN LA NUBE (SUPABASE / REST / MULTI-DEVICE)
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
                st.caption("ℹ️ **IMPORTANTE:** No introduzcas la contraseña que inventaste al crear el proyecto. La clave requerida es la **API Key `anon` / `public`** (una cadena muy larga que empieza por `eyJ...` o `sb_publishable_...`). La encuentras en Supabase en: **⚙️ Project Settings ➔ API ➔ Project API keys ➔ `anon` `public`**.")

                col_btn_s1, col_btn_s2 = st.columns(2)
                with col_btn_s1:
                    if st.button("🔌 Probar y Guardar Conexión", type="primary", use_container_width=True, key="btn_save_supa"):
                        if in_supa_url and in_supa_key:
                            ok_test, msg_test = db_manager.testear_conexion_nube(in_supa_url, in_supa_key)
                            if ok_test:
                                db_manager.guardar_config_nube(in_supa_url, in_supa_key)
                                st.success("✅ ¡Conectado con éxito a Supabase Cloud! Se ha guardado la configuración.")
                                # Ejecutar sincronización inicial
                                ok_s, msg_s = db_manager.sincronizar_con_nube(usuario_id)
                                if ok_s:
                                    st.info(f"🔄 {msg_s}")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg_test}")
                                st.warning("Asegúrate de que creaste las tablas en Supabase ejecutando el script SQL que se muestra abajo.")
                        else:
                            st.warning("Introduce la URL y Key de tu proyecto Supabase.")

                with col_btn_s2:
                    if st.button("⚡ Sincronizar Ahora (Local ⇄ Nube)", use_container_width=True, key="btn_manual_sync_tab4"):
                        ok_s, msg_s = db_manager.sincronizar_con_nube(usuario_id)
                        if ok_s:
                            st.success(f"✅ {msg_s}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg_s}")

                with st.expander("📋 Ver Script SQL para Crear Tablas en Supabase (Copiar y Pegar)", expanded=False):
                    st.markdown("""
                    **Pasos para configurar Supabase gratis en 2 minutos:**
                    1. Entra a [supabase.com](https://supabase.com) y crea un proyecto gratuito.
                    2. Ve al menú **SQL Editor** en Supabase, pega el siguiente script y pulsa **Run**:
                    """)
                    sql_script = """-- Tablas para Bolimur REBT PRO en Supabase Cloud (Aislamiento por Cuenta Google)
CREATE TABLE IF NOT EXISTS clientes (
    id BIGINT PRIMARY KEY,
    usuario_id BIGINT,
    usuario_email TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    nif_cif TEXT,
    telefono TEXT,
    email TEXT,
    direccion_suministro TEXT,
    localidad TEXT,
    cups TEXT,
    referencia_catastral TEXT,
    tipo_inmueble TEXT,
    notas TEXT,
    codigo_postal TEXT,
    municipio TEXT,
    provincia TEXT,
    distribuidora TEXT,
    potencia_contratada_kw TEXT,
    tension_suministro TEXT,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS proyectos (
    id BIGINT PRIMARY KEY,
    usuario_id BIGINT,
    usuario_email TEXT NOT NULL,
    cliente_id BIGINT,
    nombre_proyecto TEXT NOT NULL,
    modulo TEXT,
    datos_json TEXT,
    resumen_potencia_o_importe TEXT,
    fecha_guardado TIMESTAMPTZ DEFAULT NOW()
);

-- Índices de búsqueda por cuenta de usuario
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes (usuario_email);
CREATE INDEX IF NOT EXISTS idx_proyectos_email ON proyectos (usuario_email);

-- Desactivar RLS y otorgar permisos de lectura y escritura
ALTER TABLE clientes DISABLE ROW LEVEL SECURITY;
ALTER TABLE proyectos DISABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE clientes TO anon, authenticated, service_role;
GRANT ALL ON TABLE proyectos TO anon, authenticated, service_role;
"""
                    st.code(sql_script, language="sql")
                    st.markdown("3. Ve a **Project Settings -> API** y copia la **Project URL** y la clave **anon / public**.")

        with col_estado_nube:
            with st.container(border=True):
                st.markdown("#### 🔒 Privacidad y Aislamiento de Cuenta")
                st.markdown(f"**Cuenta Activa:** `{user_email}`")
                st.info("🛡️ **Aislamiento Total:** Tus clientes, expedientes y cálculos pertenecen única y exclusivamente a esta cuenta Google. Si otro instalador entra con su cuenta, accederá a su propia base de datos sin ver la tuya.")

                st.markdown("---")
                st.markdown("#### 📊 Estado de Persistencia")
                if tiene_nube:
                    st.success(f"🟢 **Nube Activa**\n\nLos datos de `{user_email}` se guardan y sincronizan automáticamente en la nube 24/7.")
                else:
                    st.warning("🟡 **Modo Local Privado**\n\nTus datos se guardan en este dispositivo bajo tu cuenta privada. Conecta Supabase arriba para sincronización 24/7 en la nube.")

        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">📦 Copia de Seguridad Rápida JSON (Sin Conexión)</h4></div>', unsafe_allow_html=True)
        col_sync1, col_sync2 = st.columns(2)

        with col_sync1:
            with st.container(border=True):
                st.markdown("##### 📥 Exportar Respaldo Completo")
                st.write("Descarga un archivo JSON con todos tus clientes registrados y proyectos para guardarlo o transferirlo manualmente.")
                
                json_backup = db_manager.exportar_copia_seguridad_nube(usuario_id)
                st.download_button(
                    label="💾 Descargar Respaldo JSON",
                    data=json_backup,
                    file_name="Copia_Seguridad_Clientes_Bolimur.json",
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

        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">📱 Cómo Usar la Aplicación en tu Teléfono Móvil o Tablet</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("""
                **🌐 Opción 1: En la misma red Wi-Fi (Taller / Oficina / Casa)**
                1. Asegúrate de que tu PC y tu teléfono móvil están conectados a la **misma red Wi-Fi**.
                2. En tu PC, abre la terminal y arranca la aplicación:
                   `streamlit run inicio.py --server.address=0.0.0.0`
                3. Abre el navegador de tu móvil o tablet e introduce la dirección IP de tu ordenador (ej: `http://192.168.1.50:8501`).
                4. **¡Listo!** Verás exactamente los mismos clientes y proyectos en tu móvil.
                """)
            with col_m2:
                st.markdown("""
                **☁️ Opción 2: En la Nube (24/7 desde la calle con datos 4G/5G)**
                1. Tu código ya está en GitHub en el repositorio `Bolimur-electricidad`.
                2. Entra en [share.streamlit.io](https://share.streamlit.io) y conéctalo gratis con tu cuenta de GitHub.
                3. Obtendrás un enlace web oficial seguro (`https://bolimur.streamlit.app`) accesible desde cualquier lugar del mundo.
                4. Al iniciar sesión con tu cuenta de Google en cualquier teléfono o PC, accederás a todos tus clientes al instante.
                """)


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
