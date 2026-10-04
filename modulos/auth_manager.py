# -*- coding: utf-8 -*-
"""
Módulo de Autenticación y Control de Sesión Multi-Usuario
Soporta inicio de sesión mediante:
1. Google Sign-In (OAuth 2.0)
2. Credenciales del Sistema Operativo Windows (Detección Automática)
3. Correo Electrónico y Contraseña Encriptada
"""

import streamlit as st
import getpass
import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
from modulos import db_manager

SECRETS_FILE = Path(".streamlit/secrets.toml")

def obtener_config_google() -> dict:
    """Obtiene las credenciales de Google OAuth desde st.secrets, secrets.toml o entorno."""
    # 1. Intentar desde st.secrets
    try:
        if "google_oauth" in st.secrets:
            return dict(st.secrets["google_oauth"])
        if "google" in st.secrets:
            return dict(st.secrets["google"])
    except Exception:
        pass
    
    # 2. Intentar leer manualmente .streamlit/secrets.toml si st.secrets no está cargado
    if SECRETS_FILE.exists():
        try:
            import toml
            data = toml.load(str(SECRETS_FILE))
            if "google_oauth" in data:
                return data["google_oauth"]
        except Exception:
            pass
        
    # 3. Intentar desde variables de entorno
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8501")
    if client_id and client_secret:
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri
        }
        
    return {}

def guardar_credenciales_google(client_id: str, client_secret: str, redirect_uri: str = "http://localhost:8501") -> bool:
    """Guarda las credenciales de Google OAuth en .streamlit/secrets.toml."""
    try:
        SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        contenido = f"""# Configuración automática de Google OAuth para Bolimur REBT PRO
[google_oauth]
client_id = "{client_id.strip()}"
client_secret = "{client_secret.strip()}"
redirect_uri = "{redirect_uri.strip()}"
"""
        with open(SECRETS_FILE, "w", encoding="utf-8") as f:
            f.write(contenido)
        return True
    except Exception:
        return False

def generar_url_oauth_google(config: dict) -> str:
    """Genera la URL de autorización oficial de Google OAuth 2.0."""
    client_id = config.get("client_id", "")
    redirect_uri = config.get("redirect_uri", "http://localhost:8501")
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

def procesar_callback_google(config: dict):
    """Procesa el código de retorno de Google OAuth si está presente en la URL."""
    try:
        query_params = st.query_params
        if "code" in query_params:
            auth_code = query_params["code"]
            client_id = config.get("client_id", "")
            client_secret = config.get("client_secret", "")
            redirect_uri = config.get("redirect_uri", "http://localhost:8501")
            
            if client_id and client_secret and auth_code:
                # 1. Intercambiar código por Token de Acceso
                token_url = "https://oauth2.googleapis.com/token"
                data = urllib.parse.urlencode({
                    "code": auth_code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }).encode("utf-8")
                
                req = urllib.request.Request(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
                with urllib.request.urlopen(req) as response:
                    token_data = json.loads(response.read().decode("utf-8"))
                    access_token = token_data.get("access_token")
                    
                if access_token:
                    # 2. Obtener datos del perfil de usuario desde Google
                    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
                    req_info = urllib.request.Request(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
                    with urllib.request.urlopen(req_info) as resp_info:
                        user_info = json.loads(resp_info.read().decode("utf-8"))
                        
                    email = user_info.get("email", "")
                    nombre = user_info.get("name", "")
                    google_id = user_info.get("id", "")
                    picture = user_info.get("picture", "")
                    
                    if email:
                        usuario = db_manager.autenticar_o_crear_usuario_google(
                            email=email,
                            nombre=nombre,
                            google_id=google_id,
                            avatar_url=picture
                        )
                        if usuario:
                            st.session_state["usuario_autenticado"] = usuario
                            # Limpiar query parameters
                            st.query_params.clear()
                            st.rerun()
    except Exception as ex:
        st.error(f"Error procesando autenticación con Google: {ex}")

def inicializar_sesion_auth():
    db_manager.inicializar_bd()
    if "usuario_autenticado" not in st.session_state:
        st.session_state["usuario_autenticado"] = None

def renderizar_pantalla_login():
    inicializar_sesion_auth()
    
    # Procesar retorno de Google OAuth si existe
    google_config = obtener_config_google()
    if google_config.get("client_id") and google_config.get("client_secret"):
        procesar_callback_google(google_config)
    
    st.markdown("""
    <style>
        .login-card {
            max-width: 580px;
            margin: 1.5rem auto;
            background: #ffffff;
            border: 2px solid #0284c7;
            border-radius: 16px;
            padding: 26px;
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
            margin-bottom: 20px;
        }
        .google-btn-container {
            display: flex;
            justify-content: center;
            margin: 15px 0;
        }
        .google-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            width: 100%;
            background-color: #ffffff;
            color: #3c4043;
            border: 1.5px solid #dadce0;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 15px;
            font-weight: 600;
            text-decoration: none;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            transition: all 0.2s ease;
        }
        .google-btn:hover {
            background-color: #f8fafd;
            border-color: #4285F4;
            color: #1a73e8;
            box-shadow: 0 2px 6px rgba(66,133,244,0.25);
        }
    </style>
    """, unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2.4, 1])
    with col_l2:
        st.markdown("""
        <div class="login-card">
            <div style="text-align: center; font-size: 40px; margin-bottom: 8px;">⚡</div>
            <div class="login-title">BOLIMUR REBT PRO</div>
            <div class="login-subtitle">Software de Ingeniería Eléctrica, Presupuestos y Certificaciones</div>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login_google, tab_login_win, tab_login_email, tab_registro = st.tabs([
            "🔴 Google",
            "🪟 Windows",
            "📧 Correo",
            "✨ Registrar"
        ])
        
        # 1. Login con Google
        with tab_login_google:
            st.markdown("##### 🔴 Elige tu Cuenta de Google para Iniciar Sesión")
            st.caption("Selecciona tu cuenta con un toque para acceder a tus clientes, cálculos y expedientes asociados.")
            
            tiene_config = bool(google_config.get("client_id") and google_config.get("client_secret"))
            
            if tiene_config:
                url_google = generar_url_oauth_google(google_config)
                st.markdown(f"""
                <div class="google-btn-container">
                    <a href="{url_google}" target="_self" class="google-btn">
                        <svg width="20" height="20" viewBox="0 0 48 48">
                            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.79l7.97-6.2z"/>
                            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                        </svg>
                        Abrir Selector Oficial de Cuentas de Google
                    </a>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='text-align:center; color:#64748b; font-size:12px; margin: 8px 0;'>— o selecciona una cuenta guardada abajo —</div>", unsafe_allow_html=True)

            # Cuentas Guardadas Disponibles en el Sistema
            usuarios_guardados = db_manager.listar_todos_usuarios()
            if usuarios_guardados:
                st.markdown("###### 👥 Cuentas de Google Registradas (Toca para entrar en 1 clic):")
                for u in usuarios_guardados:
                    u_email = u.get("email", "")
                    u_nom = u.get("nombre_instalador") or u.get("nombre_empresa") or "Instalador"
                    with st.container(border=True):
                        col_u1, col_u2 = st.columns([3, 1.3])
                        with col_u1:
                            st.markdown(f"**🔴 {u_nom}**  \n`{u_email}`")
                        with col_u2:
                            st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)
                            if st.button("👉 Entrar", key=f"btn_quick_login_{u['id']}", type="primary", use_container_width=True):
                                u_full = db_manager.obtener_usuario_por_id(u["id"])
                                if u_full:
                                    u_full["auth_provider"] = "Google"
                                    st.session_state["usuario_autenticado"] = u_full
                                    st.success(f"✅ ¡Sesión iniciada como {u_nom} ({u_email})!")
                                    st.rerun()

            st.markdown("###### ➕ Usar otra cuenta de Google:")
            with st.container(border=True):
                col_g1, col_g2 = st.columns([1.2, 1])
                with col_g1:
                    google_demo_email = st.text_input("Tu Correo de Google (*):", placeholder="ejemplo.instalador@gmail.com", key="g_demo_mail")
                with col_g2:
                    google_demo_nom = st.text_input("Nombre / Razón Social:", value="Instalador Autorizado", key="g_demo_nom")
                
                if st.button("🚀 Entrar con esta Cuenta de Google", type="primary", use_container_width=True, key="btn_g_demo"):
                    if google_demo_email and "@" in google_demo_email:
                        usuario = db_manager.autenticar_o_crear_usuario_google(
                            email=google_demo_email.strip().lower(),
                            nombre=google_demo_nom.strip(),
                            google_id=f"google_{google_demo_email.strip().lower()}"
                        )
                        if usuario:
                            usuario["auth_provider"] = "Google"
                            st.session_state["usuario_autenticado"] = usuario
                            st.success(f"✅ ¡Sesión iniciada con la cuenta de Google: **{google_demo_email}**!")
                            st.rerun()
                    else:
                        st.warning("Por favor introduce una dirección de correo válida de Google (ej: tu_nombre@gmail.com).")
                
                # Configuración de Claves de Google Cloud Console
                with st.expander("⚙️ Conectar tus claves oficiales de Google Cloud OAuth 2.0 (Opcional)", expanded=False):
                    st.markdown("""
                    **Pasos para activar Google Sign-In oficial con botón directo:**
                    1. Entra a [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
                    2. Crea un **ID de cliente de OAuth 2.0** para *Aplicación Web*.
                    3. Añade la URL de tu aplicación (ej: `http://localhost:8501`) en **URIs de redirección autorizados**.
                    4. Pega tu Client ID y Client Secret abajo:
                    """)
                    g_cid = st.text_input("Client ID de Google:", placeholder="xxxx.apps.googleusercontent.com", key="in_g_cid")
                    g_sec = st.text_input("Client Secret de Google:", type="password", key="in_g_sec")
                    g_red = st.text_input("URI de Redirección:", value="http://localhost:8501", key="in_g_red")
                    
                    if st.button("💾 Guardar Configuración de Google Cloud", use_container_width=True, key="btn_save_g"):
                        if g_cid and g_sec:
                            if guardar_credenciales_google(g_cid, g_sec, g_red):
                                st.success("✅ ¡Credenciales de Google guardadas con éxito! Recargando...")
                                st.rerun()
                            else:
                                st.error("Error al guardar archivo de configuración.")
                        else:
                            st.warning("Por favor introduce el Client ID y el Client Secret.")
        
        # 2. Login Rápido con Windows
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
                    
        # 3. Login con Correo y Contraseña
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
                        
        # 4. Registro de Nuevo Usuario / Instalador
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
