# -*- coding: utf-8 -*-
"""
Componente reutilizable de Barra de Cliente y Guardado Rápido de Proyectos
Se inserta en la cabecera de cualquier módulo de cálculo para asociar datos al cliente en 1 clic
o guardarlo como cálculo independiente/suelto.
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
            opciones_cli = [0] + [c["id"] for c in clientes]
            nombres_cli = {0: "⚪ Sin asignar (Cálculo Suelto / Independiente)"}
            for c in clientes:
                nombres_cli[c["id"]] = f"👤 {c['nombre_completo']} ({c.get('localidad', 'Murcia')})"

            cli_ses = st.session_state.get("cliente_activo_proyecto")
            def_idx = 0
            if cli_ses and cli_ses.get("id") in opciones_cli:
                def_idx = opciones_cli.index(cli_ses["id"])
                
            cliente_activo_id = st.selectbox(
                "Asignar a Cliente (Opcional):",
                options=opciones_cli,
                format_func=lambda x: nombres_cli[x],
                index=def_idx,
                key=f"bar_sel_cli_{modulo_nombre}"
            )
            
            if cliente_activo_id != 0:
                cliente_obj = db_manager.obtener_cliente_por_id(cliente_activo_id, usuario_id)
                st.session_state["cliente_activo_proyecto"] = cliente_obj
            else:
                st.session_state["cliente_activo_proyecto"] = None

        with col_b2:
            nom_def_proy = st.session_state.get("proyecto_cargado_nombre", f"Cálculo {modulo_nombre}")
            nom_proy_in = st.text_input("Nombre / Referencia del Cálculo:", value=nom_def_proy, key=f"bar_nom_proy_{modulo_nombre}")

        with col_b3:
            st.write("")
            btn_txt = "💾 Guardar en Cliente" if cliente_activo_id != 0 else "💾 Guardar Cálculo Suelto"
            if st.button(btn_txt, key=f"btn_save_proy_{modulo_nombre}", type="primary", use_container_width=True):
                if nom_proy_in:
                    c_id_save = cliente_activo_id if cliente_activo_id != 0 else None
                    ok, p_id = db_manager.guardar_proyecto(
                        usuario_id=usuario_id,
                        cliente_id=c_id_save,
                        nombre_proyecto=nom_proy_in,
                        modulo=modulo_nombre,
                        datos=datos_actuales,
                        resumen=resumen_actual
                    )
                    if ok:
                        st.session_state["proyecto_cargado_nombre"] = nom_proy_in
                        if c_id_save:
                            st.success(f"✅ ¡Guardado y asignado a la ficha del cliente!")
                        else:
                            st.success(f"✅ ¡Cálculo '{nom_proy_in}' guardado como independiente!")
                    else:
                        st.error("Error al guardar el cálculo.")
                else:
                    st.warning("Introduce un nombre para el cálculo.")
