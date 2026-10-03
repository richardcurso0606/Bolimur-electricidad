# -*- coding: utf-8 -*-
"""
Módulo de Gestión de Clientes (CRM Eléctrico) y Gestor de Proyectos
Permite almacenar fichas de clientes y asociarles proyectos y cálculos para recuperarlos en 1 clic.
"""

import streamlit as st
import pandas as pd
import datetime
from modulos import db_manager, auth_manager

def renderizar():
    usuario = auth_manager.obtener_usuario_actual()
    if not usuario:
        st.warning("Debes iniciar sesión para gestionar clientes.")
        return

    usuario_id = usuario["id"]
    clientes = db_manager.listar_clientes(usuario_id)

    st.title("👥 Gestión de Clientes y Proyectos (CRM Eléctrico)")
    st.markdown("Administra los datos de tus clientes y recupera sus presupuestos y cálculos técnicos guardados en un solo clic.")

    tab_clientes_lista, tab_nuevo_cliente, tab_todos_proyectos = st.tabs([
        "📋 Lista de Clientes y Proyectos",
        "➕ Alta de Nuevo Cliente",
        "📂 Historial Global de Proyectos"
    ])

    # =========================================================================
    # TAB 1: LISTADO DE CLIENTES Y SUS PROYECTOS
    # =========================================================================
    with tab_clientes_lista:
        if not clientes:
            st.info("ℹ️ Todavía no tienes clientes registrados. Utiliza la pestaña **'➕ Alta de Nuevo Cliente'** para crear tu primer cliente.")
        else:
            nombres_clientes = {c["id"]: f"{c['nombre_completo']} ({c.get('nif_cif', 'Sin NIF')}) - {c.get('localidad', '')}" for c in clientes}
            
            col_sel1, col_sel2 = st.columns([3, 1])
            with col_sel1:
                cliente_sel_id = st.selectbox(
                    "🔍 Selecciona un Cliente para ver su expediente y proyectos:",
                    options=list(nombres_clientes.keys()),
                    format_func=lambda x: nombres_clientes[x],
                    key="crm_sel_cliente"
                )
            with col_sel2:
                st.metric("Total Clientes", f"{len(clientes)} fichas")

            cliente_actual = db_manager.obtener_cliente_por_id(cliente_sel_id, usuario_id)
            if cliente_actual:
                st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">👤 Ficha Técnica del Cliente</h4></div>', unsafe_allow_html=True)
                with st.container(border=True):
                    col_cf1, col_cf2, col_cf3 = st.columns(3)
                    with col_cf1:
                        st.markdown(f"**Nombre / Razón Social:**  \n`{cliente_actual['nombre_completo']}`")
                        st.markdown(f"**NIF / DNI / CIF:**  \n`{cliente_actual.get('nif_cif', '-')}`")
                        st.markdown(f"**Teléfono:**  \n`{cliente_actual.get('telefono', '-')}`")
                    with col_cf2:
                        st.markdown(f"**Dirección del Suministro:**  \n`{cliente_actual.get('direccion_suministro', '-')}`")
                        st.markdown(f"**Localidad:**  \n`{cliente_actual.get('localidad', '-')}`")
                        st.markdown(f"**Email:**  \n`{cliente_actual.get('email', '-')}`")
                    with col_cf3:
                        st.markdown(f"**Código CUPS:**  \n`{cliente_actual.get('cups', '-')}`")
                        st.markdown(f"**Ref. Catastral:**  \n`{cliente_actual.get('referencia_catastral', '-')}`")
                        st.markdown(f"**Tipo Inmueble:**  \n`{cliente_actual.get('tipo_inmueble', 'Vivienda')}`")

                    if cliente_actual.get("notas"):
                        st.info(f"📝 **Notas Técnicas:** {cliente_actual['notas']}")

                    # Botón editar / borrar cliente
                    with st.expander("✏️ Editar o Eliminar este Cliente"):
                        with st.form(f"form_edit_cli_{cliente_actual['id']}"):
                            ce1, ce2 = st.columns(2)
                            with ce1:
                                enom = st.text_input("Nombre Completo:", value=cliente_actual["nombre_completo"])
                                enif = st.text_input("NIF / DNI:", value=cliente_actual.get("nif_cif", ""))
                                etel = st.text_input("Teléfono:", value=cliente_actual.get("telefono", ""))
                                eemail = st.text_input("Email:", value=cliente_actual.get("email", ""))
                            with ce2:
                                edir = st.text_input("Dirección Suministro:", value=cliente_actual.get("direccion_suministro", ""))
                                eloc = st.text_input("Localidad:", value=cliente_actual.get("localidad", ""))
                                ecups = st.text_input("CUPS:", value=cliente_actual.get("cups", ""))
                                eref = st.text_input("Ref Catastral:", value=cliente_actual.get("referencia_catastral", ""))
                            
                            enotas = st.text_area("Notas Técnicas:", value=cliente_actual.get("notas", ""))
                            
                            col_ebtn1, col_ebtn2 = st.columns(2)
                            with col_ebtn1:
                                if st.form_submit_button("💾 Guardar Modificaciones", type="primary", use_container_width=True):
                                    db_manager.actualizar_cliente(cliente_actual["id"], usuario_id, {
                                        "nombre_completo": enom, "nif_cif": enif, "telefono": etel, "email": eemail,
                                        "direccion_suministro": edir, "localidad": eloc, "cups": ecups, "referencia_catastral": eref,
                                        "tipo_inmueble": cliente_actual.get("tipo_inmueble", "Vivienda"), "notas": enotas
                                    })
                                    st.success("✅ Ficha actualizada.")
                                    st.rerun()
                        
                        if st.button("🗑️ Eliminar Definitivamente este Cliente", key=f"btn_del_cli_{cliente_actual['id']}"):
                            db_manager.eliminar_cliente(cliente_actual["id"], usuario_id)
                            st.warning("Cliente eliminado.")
                            st.rerun()

                # Listado de Proyectos del Cliente
                st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">📁 Proyectos y Cálculos Guardados de este Cliente</h4></div>', unsafe_allow_html=True)
                proyectos_cliente = db_manager.listar_proyectos_por_cliente(cliente_sel_id, usuario_id)
                
                if not proyectos_cliente:
                    st.info("No hay proyectos guardados aún para este cliente. Realiza un cálculo en cualquiera de los módulos y presiona **'Guardar en Cliente'**.")
                else:
                    for proj in proyectos_cliente:
                        with st.container(border=True):
                            col_p1, col_p2, col_p3, col_p4 = st.columns([3, 2, 2, 1.5])
                            with col_p1:
                                st.markdown(f"**📌 {proj['nombre_proyecto']}**")
                                st.caption(f"Módulo: `{proj['modulo']}` | Fecha: {proj.get('fecha_guardado', '')[:16]}")
                            with col_p2:
                                st.markdown(f"**Resumen:**  \n{proj.get('resumen_potencia_o_importe', '-')}")
                            with col_p3:
                                if st.button(f"🚀 Cargar en {proj['modulo']}", key=f"btn_load_p_{proj['id']}", type="primary", use_container_width=True):
                                    # Cargar datos en session_state y redirigir
                                    datos_p = db_manager.cargar_proyecto_por_id(proj["id"], usuario_id)
                                    if datos_p:
                                        cargar_proyecto_en_session(proj["modulo"], datos_p.get("datos", {}), cliente_actual)
                                        st.session_state.menu_activo = obtener_label_menu_por_modulo(proj["modulo"])
                                        st.success(f"✅ ¡Proyecto cargado! Redirigiendo a {proj['modulo']}...")
                                        st.rerun()
                            with col_p4:
                                if st.button("🗑️ Borrar", key=f"btn_del_p_{proj['id']}", use_container_width=True):
                                    db_manager.eliminar_proyecto(proj["id"], usuario_id)
                                    st.rerun()

    # =========================================================================
    # TAB 2: ALTA DE NUEVO CLIENTE
    # =========================================================================
    with tab_nuevo_cliente:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">➕ Crear Nueva Ficha de Cliente</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("form_nuevo_cliente_crm"):
                col_nc1, col_nc2 = st.columns(2)
                with col_nc1:
                    n_nom = st.text_input("Nombre y Apellidos o Razón Social (*):", placeholder="Ej: Francisco Martínez Gómez")
                    n_nif = st.text_input("NIF / DNI / CIF:", placeholder="Ej: 48555123K")
                    n_tel = st.text_input("Teléfono de Contacto:", placeholder="Ej: 611 22 33 44")
                    n_email = st.text_input("Email:", placeholder="Ej: cliente@correo.com")
                with col_nc2:
                    n_dir = st.text_input("Dirección de la Vivienda / Suministro:", placeholder="Ej: Calle Mayor, nº 14, 2ºA")
                    n_loc = st.text_input("Localidad y Provincia:", value="Murcia, España")
                    n_cups = st.text_input("Código CUPS (20-22 caracteres):", placeholder="Ej: ES0021000000000000AB1P")
                    n_ref = st.text_input("Referencia Catastral:", placeholder="Ej: 9872023VH5797S0001WX")
                
                n_tipo = st.selectbox("Tipo de Inmueble:", ["Vivienda Residencial", "Local Comercial", "Nave Industrial", "Garaje Comunitario / IRVE", "Edificio de Viviendas"])
                n_notas = st.text_area("Observaciones y Notas Técnicas:", placeholder="Ej: Reforma integral de cuadro, cambio de potencia de 3.45kW a 5.75kW con boletín CIE.")
                
                btn_crear_c = st.form_submit_button("✨ Guardar y Registrar Cliente", type="primary", use_container_width=True)
                if btn_crear_c:
                    if not n_nom:
                        st.error("El nombre del cliente es obligatorio.")
                    else:
                        ok, nuevo_c_id = db_manager.crear_cliente(usuario_id, {
                            "nombre_completo": n_nom,
                            "nif_cif": n_nif,
                            "telefono": n_tel,
                            "email": n_email,
                            "direccion_suministro": n_dir,
                            "localidad": n_loc,
                            "cups": n_cups,
                            "referencia_catastral": n_ref,
                            "tipo_inmueble": n_tipo,
                            "notas": n_notas
                        })
                        if ok:
                            st.success(f"✅ ¡Cliente '{n_nom}' registrado correctamente!")
                            st.rerun()
                        else:
                            st.error("Error al registrar cliente.")

    # =========================================================================
    # TAB 3: HISTORIAL GLOBAL DE PROYECTOS
    # =========================================================================
    with tab_todos_proyectos:
        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">📂 Todos los Proyectos Guardados en tu Base de Datos</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            todos_proy = db_manager.listar_proyectos_usuario(usuario_id)
            if not todos_proy:
                st.info("No hay proyectos guardados todavía.")
            else:
                filas_tabla_proy = []
                for p in todos_proy:
                    filas_tabla_proy.append({
                        "Proyecto": p["nombre_proyecto"],
                        "Cliente": p.get("cliente_nombre") or "General / Sin asignar",
                        "Módulo": p["modulo"],
                        "Resumen": p.get("resumen_potencia_o_importe", "-"),
                        "Fecha Guardado": p.get("fecha_guardado", "")[:16]
                    })
                st.dataframe(pd.DataFrame(filas_tabla_proy), use_container_width=True, hide_index=True)


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

def obtener_label_menu_por_modulo(modulo: str) -> str:
    if "Presupuesto" in modulo:
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
