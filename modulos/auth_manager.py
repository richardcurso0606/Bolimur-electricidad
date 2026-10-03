# -*- coding: utf-8 -*-
"""
Módulo de Autenticación y Control de Sesión Multi-Usuario
Soporta inicio de sesión mediante credenciales de Windows o Correo/Contraseña.
"""

import streamlit as st
import getpass
from modulos import db_manager

def inicializar_sesion_auth():
    db_manager.inicializar_bd()
    if "usuario_autenticado" not in st.session_state:
        st.session_state["usuario_autenticado"] = None

def renderizar_pantalla_login():
    inicializar_sesion_auth()
    
    st.markdown("""
    <style>
        .login-card {
            max-width: 540px;
            margin: 2rem auto;
            background: #ffffff;
            border: 2px solid #0284c7;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 25px rgba(2, 132, 199, 0.12);
        }
        .login-title {
            text-align: center;
            color: #0369a1;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .login-subtitle {
            text-align: center;
            color: #64748b;
            font-size: 14px;
            margin-bottom: 25px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2.2, 1])
    with col_l2:
        st.markdown("""
        <div class="login-card">
            <div style="text-align: center; font-size: 42px; margin-bottom: 10px;">⚡</div>
            <div class="login-title">BOLIMUR REBT PRO</div>
            <div class="login-subtitle">Software de Ingeniería Eléctrica, Presupuestos y Certificaciones</div>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login_win, tab_login_email, tab_registro = st.tabs([
            "🪟 Iniciar con Windows",
            "📧 Iniciar con Correo",
            "✨ Registrar Nuevo Instalador"
        ])
        
        # 1. Login Rápido con Windows
        with tab_login_win:
            win_user_actual = getpass.getuser()
            st.markdown(f"Usuario del sistema operativo detectado: **`{win_user_actual}`**")
            st.info("🔒 Accede directamente con tu sesión de Windows para cargar tu base de datos personal.")
            if st.button("🚀 Iniciar Sesión con mi Cuenta de Windows", type="primary", use_container_width=True, key="btn_login_win"):
                usuario = db_manager.autenticar_usuario_windows(win_user_actual)
                if usuario:
                    st.session_state["usuario_autenticado"] = usuario
                    st.success(f"¡Bienvenido de nuevo, {usuario.get('nombre_instalador', win_user_actual)}!")
                    st.rerun()
                else:
                    # Crear usuario automáticamente
                    ok, _ = db_manager.registrar_nuevo_usuario(
                        email=f"{win_user_actual}@bolimur.local",
                        password="password123",
                        nombre_instalador=win_user_actual,
                        nombre_empresa="BOLIMUR INSTALACIONES",
                        username_win=win_user_actual
                    )
                    usuario = db_manager.autenticar_usuario_windows(win_user_actual)
                    st.session_state["usuario_autenticado"] = usuario
                    st.success(f"¡Perfil creado e iniciado con éxito para {win_user_actual}!")
                    st.rerun()
                    
        # 2. Login con Correo y Contraseña
        with tab_login_email:
            with st.form("form_login_email"):
                st.markdown("##### Acceso con Credenciales:")
                email_in = st.text_input("Correo Electrónico:", placeholder="ejemplo@empresa.com", key="login_email_in")
                pass_in = st.text_input("Contraseña:", type="password", key="login_pass_in")
                
                btn_login_email = st.form_submit_button("🔑 Entrar a la Aplicación", type="primary", use_container_width=True)
                if btn_login_email:
                    if email_in and pass_in:
                        usuario = db_manager.autenticar_usuario_email(email_in, pass_in)
                        if usuario:
                            st.session_state["usuario_autenticado"] = usuario
                            st.success(f"¡Bienvenido {usuario.get('nombre_instalador', '')}!")
                            st.rerun()
                        else:
                            st.error("❌ Correo o contraseña incorrectos.")
                    else:
                        st.warning("Por favor completa todos los campos.")
                        
        # 3. Registro de Nuevo Usuario / Instalador
        with tab_registro:
            with st.form("form_registro_nuevo"):
                st.markdown("##### Alta de Nuevo Instalador Autorizado:")
                r_nombre = st.text_input("Nombre y Apellidos del Instalador:", placeholder="Ej: Juan Pérez Martínez", key="reg_nom")
                r_empresa = st.text_input("Nombre de la Empresa o Razón Social:", placeholder="Ej: ELECTRO SERVICIOS S.L.", key="reg_emp")
                r_email = st.text_input("Correo Electrónico:", placeholder="instalador@empresa.com", key="reg_email")
                r_pass1 = st.text_input("Contraseña:", type="password", key="reg_pass1")
                r_pass2 = st.text_input("Confirmar Contraseña:", type="password", key="reg_pass2")
                
                btn_registrar = st.form_submit_button("✨ Crear Cuenta y Comenzar", type="primary", use_container_width=True)
                if btn_registrar:
                    if not (r_nombre and r_empresa and r_email and r_pass1):
                        st.warning("Todos los campos son obligatorios.")
                    elif r_pass1 != r_pass2:
                        st.error("Las contraseñas no coinciden.")
                    elif len(r_pass1) < 4:
                        st.error("La contraseña debe tener al menos 4 caracteres.")
                    else:
                        ok, msg = db_manager.registrar_nuevo_usuario(
                            email=r_email,
                            password=r_pass1,
                            nombre_instalador=r_nombre,
                            nombre_empresa=r_empresa,
                            username_win=getpass.getuser()
                        )
                        if ok:
                            usuario = db_manager.autenticar_usuario_email(r_email, r_pass1)
                            st.session_state["usuario_autenticado"] = usuario
                            st.success("✅ ¡Cuenta creada exitosamente!")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

def cerrar_sesion():
    st.session_state["usuario_autenticado"] = None
    st.rerun()

def obtener_usuario_actual() -> dict:
    inicializar_sesion_auth()
    usuario = st.session_state.get("usuario_autenticado")
    if not usuario:
        # Fallback de conveniencia: cargar usuario de Windows actual
        db_manager.inicializar_bd()
        win_user = getpass.getuser()
        usuario = db_manager.autenticar_usuario_windows(win_user)
        if not usuario:
            # Crear perfil automático por defecto
            db_manager.registrar_nuevo_usuario(
                email=f"{win_user}@bolimur.local",
                password="password123",
                nombre_instalador="Richard Orlando Choque Tejerina",
                nombre_empresa="BOLIMUR INSTALACIONES Y REFORMAS",
                username_win=win_user
            )
            usuario = db_manager.autenticar_usuario_windows(win_user)
        st.session_state["usuario_autenticado"] = usuario
    return usuario
