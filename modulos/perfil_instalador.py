# -*- coding: utf-8 -*-
"""
Módulo de Perfil del Instalador y Configuración de Empresa
Permite gestionar datos fiscales, licencias REBT, logotipo oficial y sincronización en la nube.
"""

import streamlit as st
import base64
import os
from modulos import db_manager, auth_manager

def renderizar():
    usuario = auth_manager.obtener_usuario_actual()
    if not usuario:
        st.warning("Debes iniciar sesión para acceder al perfil.")
        return

    usuario_id = usuario["id"]
    
    # Recargar datos actualizados de la base de datos
    datos_actualizados = db_manager.obtener_usuario_por_id(usuario_id)
    if datos_actualizados:
        usuario = datos_actualizados
        st.session_state["usuario_autenticado"] = usuario

    st.title("👤 Perfil Profesional del Instalador y Empresa")
    st.markdown("Configura tu membrete corporativo, licencias oficiales REBT, logotipo y copias de seguridad en la nube.")

    col_izq, col_der = st.columns([2.5, 1.5])

    with col_izq:
        st.markdown('<div class="section-header-blue"><h4 style="margin:0; color:#0369a1;">🏢 Datos Fiscales y de Contacto</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("form_perfil_instalador"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    nombre_empresa = st.text_input("Nombre de la Empresa / Razón Social:", value=usuario.get("nombre_empresa", "BOLIMUR INSTALACIONES Y REFORMAS"))
                    nombre_instalador = st.text_input("Nombre y Apellidos del Instalador:", value=usuario.get("nombre_instalador", "Richard Orlando Choque Tejerina"))
                    nif_cif = st.text_input("NIF / CIF:", value=usuario.get("nif_cif", "B-73000000"))
                    telefono = st.text_input("Teléfono de Contacto:", value=usuario.get("telefono", "+34 600 000 000"))
                
                with col_f2:
                    email_contacto = st.text_input("Email de Contacto Comercial:", value=usuario.get("email_contacto", usuario.get("email", "")))
                    direccion = st.text_input("Dirección Fiscal / Sede:", value=usuario.get("direccion", "C/ Principal, nº 1"))
                    localidad = st.text_input("Localidad y Provincia:", value=usuario.get("localidad", "Rincón de Seca, Murcia"))
                    iban = st.text_input("Cuenta Bancaria / IBAN (Para presupuestos):", value=usuario.get("iban", "ES00 0000 0000 0000 0000 0000"))

                st.markdown('<div class="section-header-amber"><h4 style="margin:0; color:#92400e;">📜 Acreditaciones Oficiales REBT (DGEAIM Murcia / Industria)</h4></div>', unsafe_allow_html=True)
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    num_licencia = st.text_input("Nº Certificado / Carnet Instalador REBT:", value=usuario.get("num_licencia_rebt", "REBT-30/15892"))
                    registro_ind = st.text_input("Nº Registro Integrado Industrial (RII):", value=usuario.get("registro_industrial", "RII-30/004521"))
                with col_r2:
                    categorias_disp = [
                        "Instalador Especialista (IBTE)",
                        "Instalador Básico (IBTB)",
                        "Ingeniero Técnico Industrial",
                        "Empresa Instaladora Autorizada"
                    ]
                    cat_actual = usuario.get("categoria_rebt", "Instalador Especialista (IBTE)")
                    idx_cat = categorias_disp.index(cat_actual) if cat_actual in categorias_disp else 0
                    categoria_rebt = st.selectbox("Categoría Profesional REBT:", categorias_disp, index=idx_cat)

                btn_guardar_perfil = st.form_submit_button("💾 Guardar Cambios en mi Perfil", type="primary", use_container_width=True)
                if btn_guardar_perfil:
                    nuevos_datos = {
                        "nombre_empresa": nombre_empresa,
                        "nombre_instalador": nombre_instalador,
                        "nif_cif": nif_cif,
                        "telefono": telefono,
                        "email_contacto": email_contacto,
                        "direccion": direccion,
                        "localidad": localidad,
                        "iban": iban,
                        "num_licencia_rebt": num_licencia,
                        "registro_industrial": registro_ind,
                        "categoria_rebt": categoria_rebt,
                        "logo_base64": usuario.get("logo_base64", "")
                    }
                    if db_manager.actualizar_perfil_instalador(usuario_id, nuevos_datos):
                        st.session_state["usuario_autenticado"] = db_manager.obtener_usuario_por_id(usuario_id)
                        st.success("✅ ¡Datos del instalador actualizados correctamente!")
                        st.rerun()
                    else:
                        st.error("Error al guardar los datos.")

    with col_der:
        st.markdown('<div class="section-header-green"><h4 style="margin:0; color:#15803d;">🖼️ Logotipo Oficial</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.caption("Este logo se insertará automáticamente en todos tus Presupuestos Oficiales, Órdenes de Compra y Memorias Técnicas en PDF.")
            
            logo_b64 = usuario.get("logo_base64")
            if logo_b64:
                try:
                    img_bytes = base64.b64decode(logo_b64)
                    st.image(img_bytes, caption="Logotipo Actual", use_container_width=True)
                except Exception:
                    st.image("logo_bolimur.PNG", caption="Logo por defecto", use_container_width=True)
            elif os.path.exists("logo_bolimur.PNG"):
                st.image("logo_bolimur.PNG", caption="Logo corporativo Bolimur", use_container_width=True)

            archivo_logo = st.file_uploader("Subir Nuevo Logotipo (PNG / JPG):", type=["png", "jpg", "jpeg"], key="upload_logo_perfil")
            if archivo_logo is not None:
                if st.button("💾 Aplicar y Guardar Logotipo", type="primary", use_container_width=True):
                    bytes_data = archivo_logo.read()
                    b64_str = base64.b64encode(bytes_data).decode("utf-8")
                    
                    datos_act = dict(usuario)
                    datos_act["logo_base64"] = b64_str
                    if db_manager.actualizar_perfil_instalador(usuario_id, datos_act):
                        st.session_state["usuario_autenticado"] = db_manager.obtener_usuario_por_id(usuario_id)
                        st.success("✅ ¡Nuevo logotipo guardado exitosamente!")
                        st.rerun()

        st.markdown('<div class="section-header-slate"><h4 style="margin:0; color:#334155;">☁️ Copia de Seguridad y Nube</h4></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("""
            **Sincronización Multi-Dispositivo:**  
            Descarga tu copia de seguridad completa con todos tus clientes y proyectos para llevarla a otro ordenador o subirla a la nube.
            """)
            
            backup_json = db_manager.exportar_copia_seguridad_nube(usuario_id)
            st.download_button(
                label="📥 Exportar Copia de Seguridad (.json)",
                data=backup_json,
                file_name=f"Backup_Bolimur_{usuario.get('username_windows', 'usuario')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            with st.expander("📤 Importar Copia de Seguridad"):
                archivo_backup = st.file_uploader("Selecciona archivo de respaldo (.json):", type=["json"], key="upload_backup")
                if archivo_backup is not None:
                    if st.button("🚀 Restaurar e Importar Datos", type="primary", use_container_width=True):
                        contenido = archivo_backup.read().decode("utf-8")
                        ok, msg = db_manager.importar_copia_seguridad_nube(usuario_id, contenido)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
