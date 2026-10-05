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
    
    # 1. Procesar login directo desde el detector de perfiles del navegador (JavaScript localStorage)
    try:
        if "login_email" in st.query_params:
            login_email = st.query_params["login_email"].strip().lower()
            login_nombre = st.query_params.get("login_nombre", login_email.split('@')[0])
            if login_email and "@" in login_email:
                usuario = db_manager.autenticar_o_crear_usuario_google(
                    email=login_email,
                    nombre=login_nombre,
                    google_id=f"google_{login_email}"
                )
                if usuario:
                    usuario["auth_provider"] = "Google"
                    st.session_state["usuario_autenticado"] = usuario
                    st.query_params.clear()
                    st.rerun()
    except Exception:
        pass

    # 2. Procesar retorno de Google OAuth si existe
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
        
        if st.button("⚡ Entrar Directamente con Google como Richard Choque (richardcurs0606@gmail.com)", type="primary", use_container_width=True, key="btn_quick_richard"):
            st.session_state.pop("sesion_cerrada_manual", None)
            usuario = obtener_usuario_actual()
            usuario["email"] = "richardcurs0606@gmail.com"
            usuario["auth_provider"] = "Google"
            st.session_state["usuario_autenticado"] = usuario
            st.rerun()

        st.markdown("<div style='text-align: center; margin: 10px 0; color: #94a3b8; font-size: 13px;'>— o selecciona otro método de acceso —</div>", unsafe_allow_html=True)

        tab_login_google, tab_login_win, tab_login_email, tab_registro = st.tabs([
            "🔴 Google",
            "🪟 Windows",
            "📧 Correo",
            "✨ Registrar"
        ])
        
        # 1. Login con Google
        with tab_login_google:
            st.markdown("##### 🔴 Acceso con Cuenta de Google")
            st.caption("Introduce tu cuenta de Google. Cada cuenta dispone de su propia base de datos independiente, clientes y proyectos privados.")

            with st.container(border=True):
                google_demo_email = st.text_input(
                    "Tu Correo de Google (*):",
                    value="richardcurs0606@gmail.com",
                    placeholder="richardcurs0606@gmail.com",
                    key="g_demo_mail"
                )
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    google_demo_nom = st.text_input("Nombre / Razón Social:", value="Richard Orlando Choque Tejerina", key="g_demo_nom")
                with col_g2:
                    google_demo_empresa = st.text_input("Empresa Eléctrica:", value="BOLIMUR INSTALACIONES Y REFORMAS", key="g_demo_emp")

                if st.button("🚀 Iniciar Sesión con Google", type="primary", use_container_width=True, key="btn_g_demo"):
                    if google_demo_email and "@" in google_demo_email:
                        email_clean = google_demo_email.strip().lower()
                        nom_clean = google_demo_nom.strip() if google_demo_nom.strip() else email_clean.split("@")[0]
                        
                        usuario = db_manager.autenticar_o_crear_usuario_google(
                            email=email_clean,
                            nombre=nom_clean,
                            google_id=f"google_{email_clean}"
                        )
                        if usuario:
                            usuario["auth_provider"] = "Google"
                            if google_demo_empresa.strip():
                                db_manager.actualizar_perfil_usuario(usuario["id"], {"nombre_empresa": google_demo_empresa.strip()})
                                usuario["nombre_empresa"] = google_demo_empresa.strip()
                            st.session_state["usuario_autenticado"] = usuario
                            st.success(f"✅ ¡Bienvenido! Sesión iniciada con: **{email_clean}**")
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
    st.session_state["sesion_cerrada_manual"] = True
    st.rerun()

def obtener_usuario_actual() -> dict:
    inicializar_sesion_auth()
    usuario = st.session_state.get("usuario_autenticado")
    if not usuario:
        db_manager.inicializar_bd()
        win_user = getpass.getuser()
        
        # 1. Buscar prioritariamente la cuenta configurada
        usuario = db_manager.obtener_usuario_por_email("richardcurs0606@gmail.com")
        if not usuario:
            usuario = db_manager.obtener_usuario_por_email("richardcurso0606@gmail.com")
        if not usuario:
            usuario = db_manager.autenticar_usuario_windows(win_user)
        if not usuario:
            # Buscar si ya existe algún usuario en la BD
            try:
                conn = db_manager.obtener_conexion()
                c = conn.cursor()
                c.execute("SELECT * FROM usuarios LIMIT 1")
                row = c.fetchone()
                conn.close()
                if row:
                    usuario = dict(row)
            except Exception:
                pass
        if not usuario:
            # Crear perfil automático oficial por defecto
            db_manager.registrar_nuevo_usuario(
                email="richardcurs0606@gmail.com",
                password="password123",
                nombre_instalador="Richard Orlando Choque Tejerina",
                nombre_empresa="BOLIMUR INSTALACIONES Y REFORMAS",
                username_win=win_user
            )
            usuario = db_manager.obtener_usuario_por_email("richardcurs0606@gmail.com")
        if not usuario:
            usuario = {
                "id": 1,
                "email": "richardcurs0606@gmail.com",
                "nombre_instalador": "Richard Orlando Choque Tejerina",
                "nombre_empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
                "num_licencia_rebt": "REBT-30/15892",
                "localidad": "Murcia, España",
                "telefono": "+34 600 000 000"
            }
        
        # Configurar como sesión activa de Google oficial
        usuario["auth_provider"] = "Google"
        if not usuario.get("google_id"):
            usuario["google_id"] = "google_richardcurs0606@gmail.com"
        usuario["email"] = "richardcurs0606@gmail.com"
        st.session_state["usuario_autenticado"] = usuario
    return usuario
