# -*- coding: utf-8 -*-
"""
Componente reutilizable de Barra de Cliente y Guardado Rápido de Proyectos
Se inserta en la cabecera de cualquier módulo de cálculo para asociar datos al cliente en 1 clic.
"""

import streamlit as st
from modulos import db_manager, auth_manager

def renderizar_barra_cliente_proyecto(modulo_nombre: str, datos_actuales: dict, resumen_actual: str = ""):
    usuario = auth_manager.obtener_usuario_actual()
    if not usuario:
        return

    usuario_id = usuario["id"]
    clientes = db_manager.listar_clientes(usuario_id)

    with st.container(border=True):
        col_b1, col_b2, col_b3 = st.columns([2.5, 2.5, 2])
        
        with col_b1:
            if not clientes:
                st.caption("💡 *No hay clientes registrados.* Ve a **'👥 Gestión de Clientes'** para crear fichas.")
                cliente_activo_id = None
            else:
                nombres = {c["id"]: f"👤 {c['nombre_completo']} ({c.get('localidad', '')})" for c in clientes}
                # Buscar si hay cliente activo en sesión
                cli_ses = st.session_state.get("cliente_activo_proyecto")
                def_idx = 0
                if cli_ses and cli_ses.get("id") in nombres:
                    def_idx = list(nombres.keys()).index(cli_ses["id"])
                    
                cliente_activo_id = st.selectbox(
                    "Cliente Asignado:",
                    options=list(nombres.keys()),
                    format_func=lambda x: nombres[x],
                    index=def_idx,
                    key=f"bar_sel_cli_{modulo_nombre}"
                )
                
                # Actualizar cliente activo en sesión
                cliente_obj = db_manager.obtener_cliente_por_id(cliente_activo_id, usuario_id)
                st.session_state["cliente_activo_proyecto"] = cliente_obj

        with col_b2:
            nom_def_proy = st.session_state.get("proyecto_cargado_nombre", f"Proyecto {modulo_nombre}")
            nom_proy_in = st.text_input("Nombre / Referencia del Proyecto:", value=nom_def_proy, key=f"bar_nom_proy_{modulo_nombre}")

        with col_b3:
            st.write("")
            if st.button(f"💾 Guardar Proyecto en Cliente", key=f"btn_save_proy_{modulo_nombre}", type="primary", use_container_width=True):
                if nom_proy_in:
                    ok, p_id = db_manager.guardar_proyecto(
                        usuario_id=usuario_id,
                        cliente_id=cliente_activo_id,
                        nombre_proyecto=nom_proy_in,
                        modulo=modulo_nombre,
                        datos=datos_actuales,
                        resumen=resumen_actual
                    )
                    if ok:
                        st.session_state["proyecto_cargado_nombre"] = nom_proy_in
                        st.success(f"✅ ¡Proyecto '{nom_proy_in}' guardado en la ficha del cliente!")
                    else:
                        st.error("Error al guardar el proyecto.")
                else:
                    st.warning("Introduce un nombre para el proyecto.")
