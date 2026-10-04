# -*- coding: utf-8 -*-
"""
Módulo de Gestión de Base de Datos SQLite y Persistencia Local / Nube
Gestiona usuarios, perfiles de instalador, clientes y proyectos guardados.
"""

import sqlite3
import hashlib
import json
import os
import getpass
import base64
from typing import Optional, Dict, Any, List

DB_PATH = "bolimur_data.db"

def obtener_conexion() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_bd():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Tabla de Usuarios / Instaladores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        username_windows TEXT,
        password_hash TEXT,
        nombre_instalador TEXT,
        nombre_empresa TEXT,
        nif_cif TEXT,
        num_licencia_rebt TEXT,
        categoria_rebt TEXT,
        registro_industrial TEXT,
        direccion TEXT,
        localidad TEXT,
        telefono TEXT,
        email_contacto TEXT,
        logo_base64 TEXT,
        iban TEXT,
        google_id TEXT,
        avatar_url TEXT,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Comprobar columnas adicionales si la tabla ya existía
    cursor.execute("PRAGMA table_info(usuarios)")
    cols_existentes = [row[1] for row in cursor.fetchall()]
    if "google_id" not in cols_existentes:
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN google_id TEXT")
        except Exception:
            pass
    if "avatar_url" not in cols_existentes:
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN avatar_url TEXT")
        except Exception:
            pass
    
    # Tabla de Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
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
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
    )
    """)
    
    # Comprobar columnas adicionales en tabla clientes
    cursor.execute("PRAGMA table_info(clientes)")
    cols_cli_existentes = [row[1] for row in cursor.fetchall()]
    cols_cli_nuevas = [
        ("usuario_email", "TEXT"),
        ("codigo_postal", "TEXT"),
        ("municipio", "TEXT"),
        ("provincia", "TEXT"),
        ("distribuidora", "TEXT"),
        ("potencia_contratada_kw", "TEXT"),
        ("tension_suministro", "TEXT")
    ]
    for col_nom, col_tipo in cols_cli_nuevas:
        if col_nom not in cols_cli_existentes:
            try:
                cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col_nom} {col_tipo}")
            except Exception:
                pass

    # Tabla de Proyectos y Cálculos Guardados por Cliente
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        usuario_email TEXT,
        cliente_id INTEGER,
        nombre_proyecto TEXT NOT NULL,
        modulo TEXT NOT NULL,
        datos_json TEXT NOT NULL,
        resumen_potencia_o_importe TEXT,
        fecha_guardado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
        FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
    )
    """)



def inicializar_bd():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Tabla de Usuarios / Instaladores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        username_windows TEXT,
        password_hash TEXT,
        nombre_instalador TEXT,
        nombre_empresa TEXT,
        nif_cif TEXT,
        num_licencia_rebt TEXT,
        categoria_rebt TEXT,
        registro_industrial TEXT,
        direccion TEXT,
        localidad TEXT,
        telefono TEXT,
        email_contacto TEXT,
        logo_base64 TEXT,
        iban TEXT,
        google_id TEXT,
        avatar_url TEXT,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Comprobar columnas adicionales si la tabla ya existía
    cursor.execute("PRAGMA table_info(usuarios)")
    cols_existentes = [row[1] for row in cursor.fetchall()]
    if "google_id" not in cols_existentes:
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN google_id TEXT")
        except Exception:
            pass
    if "avatar_url" not in cols_existentes:
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN avatar_url TEXT")
        except Exception:
            pass
    
    # Tabla de Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
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
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
    )
    """)
    
    # Comprobar columnas adicionales en tabla clientes
    cursor.execute("PRAGMA table_info(clientes)")
    cols_cli_existentes = [row[1] for row in cursor.fetchall()]
    cols_cli_nuevas = [
        ("usuario_email", "TEXT"),
        ("codigo_postal", "TEXT"),
        ("municipio", "TEXT"),
        ("provincia", "TEXT"),
        ("distribuidora", "TEXT"),
        ("potencia_contratada_kw", "TEXT"),
        ("tension_suministro", "TEXT")
    ]
    for col_nom, col_tipo in cols_cli_nuevas:
        if col_nom not in cols_cli_existentes:
            try:
                cursor.execute(f"ALTER TABLE clientes ADD COLUMN {col_nom} {col_tipo}")
            except Exception:
                pass

    # Tabla de Proyectos y Cálculos Guardados por Cliente
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        usuario_email TEXT,
        cliente_id INTEGER,
        nombre_proyecto TEXT NOT NULL,
        modulo TEXT NOT NULL,
        datos_json TEXT NOT NULL,
        resumen_potencia_o_importe TEXT,
        fecha_guardado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
        FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE CASCADE
    )
    """)

    cursor.execute("PRAGMA table_info(proyectos)")
    cols_pro_existentes = [row[1] for row in cursor.fetchall()]
    if "usuario_email" not in cols_pro_existentes:
        try:
            cursor.execute("ALTER TABLE proyectos ADD COLUMN usuario_email TEXT")
        except Exception:
            pass
    
    conn.commit()
    conn.close()

def hashear_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# =========================================================================
# FUNCIONES DE USUARIOS Y AUTENTICACIÓN
# =========================================================================
def autenticar_usuario_email(email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    p_hash = hashear_password(password)
    cursor.execute("SELECT * FROM usuarios WHERE LOWER(email) = LOWER(?) AND password_hash = ?", (email.strip(), p_hash))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def autenticar_usuario_windows(username_win: str) -> Optional[Dict[str, Any]]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE LOWER(username_windows) = LOWER(?)", (username_win.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def autenticar_o_crear_usuario_google(email: str, nombre: str = "", google_id: str = "", avatar_url: str = "") -> Optional[Dict[str, Any]]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    email_clean = email.strip().lower()
    cursor.execute("SELECT * FROM usuarios WHERE LOWER(email) = ?", (email_clean,))
    row = cursor.fetchone()
    if row:
        user_dict = dict(row)
        # Actualizar google_id o avatar_url si están disponibles
        if google_id or avatar_url:
            cursor.execute("""
            UPDATE usuarios SET 
                google_id = COALESCE(NULLIF(?, ''), google_id),
                avatar_url = COALESCE(NULLIF(?, ''), avatar_url)
            WHERE id = ?
            """, (google_id, avatar_url, user_dict["id"]))
            conn.commit()
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_dict["id"],))
            user_dict = dict(cursor.fetchone())
        conn.close()
        return user_dict
    else:
        # Registrar nuevo usuario desde Google
        try:
            p_hash = hashear_password(f"google_oauth_{google_id or email_clean}")
            nom_instalador = nombre.strip() if nombre and nombre.strip() else email_clean.split('@')[0].capitalize()
            cursor.execute("""
            INSERT INTO usuarios (
                email, password_hash, nombre_instalador, nombre_empresa, username_windows, 
                num_licencia_rebt, localidad, telefono, google_id, avatar_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_clean, p_hash, nom_instalador, 
                "BOLIMUR INSTALACIONES", email_clean.split('@')[0],
                "REBT-30/00000", "España", "+34 600 000 000", google_id, avatar_url
            ))
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (new_id,))
            new_row = cursor.fetchone()
            conn.close()
            return dict(new_row) if new_row else None
        except Exception:
            conn.close()
            return None

def registrar_nuevo_usuario(email: str, password: str, nombre_instalador: str, nombre_empresa: str, username_win: str = "") -> tuple[bool, str]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        p_hash = hashear_password(password)
        cursor.execute("""
        INSERT INTO usuarios (email, password_hash, nombre_instalador, nombre_empresa, username_windows, num_licencia_rebt, localidad, telefono)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (email.strip().lower(), p_hash, nombre_instalador.strip(), nombre_empresa.strip(), username_win.strip() or email.split('@')[0], "REBT-30/00000", "Murcia, España", "+34 600 000 000"))
        conn.commit()
        conn.close()
        return True, "Usuario registrado con éxito."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Ya existe un usuario con este correo electrónico."
    except Exception as ex:
        conn.close()
        return False, f"Error al registrar: {ex}"

def actualizar_perfil_instalador(usuario_id: int, datos: Dict[str, Any]) -> bool:
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE usuarios SET
            nombre_instalador = ?,
            nombre_empresa = ?,
            nif_cif = ?,
            num_licencia_rebt = ?,
            categoria_rebt = ?,
            registro_industrial = ?,
            direccion = ?,
            localidad = ?,
            telefono = ?,
            email_contacto = ?,
            logo_base64 = ?,
            iban = ?
        WHERE id = ?
        """, (
            datos.get("nombre_instalador", ""),
            datos.get("nombre_empresa", ""),
            datos.get("nif_cif", ""),
            datos.get("num_licencia_rebt", ""),
            datos.get("categoria_rebt", "Instalador Especialista (IBTE)"),
            datos.get("registro_industrial", ""),
            datos.get("direccion", ""),
            datos.get("localidad", ""),
            datos.get("telefono", ""),
            datos.get("email_contacto", ""),
            datos.get("logo_base64", ""),
            datos.get("iban", ""),
            usuario_id
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False

def obtener_usuario_por_id(usuario_id: int) -> Optional[Dict[str, Any]]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def listar_todos_usuarios() -> List[Dict[str, Any]]:
    """Devuelve la lista de usuarios registrados para el selector de cuentas"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, nombre_instalador, nombre_empresa, avatar_url, google_id FROM usuarios ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# =========================================================================
# CONFIGURACIÓN Y SINCRONIZACIÓN CON BASE DE DATOS EN LA NUBE (SUPABASE / REST)
# =========================================================================
from pathlib import Path
import urllib.request
import urllib.parse

SECRETS_FILE = Path(".streamlit/secrets.toml")

def obtener_config_nube() -> Dict[str, str]:
    """Obtiene la configuración de conexión a la Nube (Supabase / Postgres / REST)"""
    # 1. Intentar desde st.secrets si está disponible
    try:
        import streamlit as st
        if "supabase" in st.secrets:
            return dict(st.secrets["supabase"])
        if "database" in st.secrets:
            return dict(st.secrets["database"])
    except Exception:
        pass
    
    # 2. Intentar leer manualmente .streamlit/secrets.toml
    if SECRETS_FILE.exists():
        try:
            import toml
            data = toml.load(str(SECRETS_FILE))
            if "supabase" in data:
                return data["supabase"]
        except Exception:
            pass
            
    # 3. Intentar desde variables de entorno
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if url and key:
        return {"url": url, "key": key}
        
    return {}

def guardar_config_nube(url: str, key: str) -> bool:
    """Guarda las claves de la nube en .streamlit/secrets.toml para persistencia automática"""
    try:
        SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if SECRETS_FILE.exists():
            try:
                import toml
                data = toml.load(str(SECRETS_FILE))
            except Exception:
                pass
        data["supabase"] = {
            "url": url.strip(),
            "key": key.strip()
        }
        import toml
        with open(SECRETS_FILE, "w", encoding="utf-8") as f:
            toml.dump(data, f)
        return True
    except Exception:
        return False

def testear_conexion_nube(url: str, key: str) -> tuple[bool, str]:
    """Verifica si la URL y Key de Supabase conectan correctamente"""
    try:
        url_clean = url.strip().rstrip("/")
        req_url = f"{url_clean}/rest/v1/clientes?select=id&limit=1"
        req = urllib.request.Request(req_url, headers={
            "apikey": key.strip(),
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json"
        })
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status in (200, 206):
                return True, "Conexión con la Base de Datos Nube (Supabase) establecida con éxito."
            return False, f"Código de respuesta del servidor: {response.status}"
    except Exception as ex:
        return False, f"Error al conectar con la Nube: {ex}"

def push_cliente_a_nube(cliente_dict: Dict[str, Any], user_email: str = ""):
    """Envía un cliente a la nube Supabase en segundo plano, asociado estrictamente al correo del usuario"""
    config = obtener_config_nube()
    if not config.get("url") or not config.get("key"):
        return
    try:
        url_base = config["url"].strip().rstrip("/")
        key = config["key"].strip()
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        payload_item = dict(cliente_dict)
        if user_email:
            payload_item["usuario_email"] = user_email.strip().lower()
        payload = [payload_item]
        req = urllib.request.Request(
            f"{url_base}/rest/v1/clientes",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass

def push_proyecto_a_nube(proyecto_dict: Dict[str, Any], user_email: str = ""):
    """Envía un proyecto a la nube Supabase en segundo plano, asociado estrictamente al correo del usuario"""
    config = obtener_config_nube()
    if not config.get("url") or not config.get("key"):
        return
    try:
        url_base = config["url"].strip().rstrip("/")
        key = config["key"].strip()
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        payload_item = dict(proyecto_dict)
        if user_email:
            payload_item["usuario_email"] = user_email.strip().lower()
        payload = [payload_item]
        req = urllib.request.Request(
            f"{url_base}/rest/v1/proyectos",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass

def delete_cliente_de_nube(cliente_id: int, user_email: str = ""):
    """Elimina un cliente de la nube Supabase de la cuenta del usuario"""
    config = obtener_config_nube()
    if not config.get("url") or not config.get("key"):
        return
    try:
        url_base = config["url"].strip().rstrip("/")
        key = config["key"].strip()
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}"
        }
        url_del = f"{url_base}/rest/v1/clientes?id=eq.{cliente_id}"
        if user_email:
            url_del += f"&usuario_email=eq.{urllib.parse.quote(user_email.strip().lower())}"
        req = urllib.request.Request(url_del, headers=headers, method="DELETE")
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass

def delete_proyecto_de_nube(proyecto_id: int, user_email: str = ""):
    """Elimina un proyecto de la nube Supabase de la cuenta del usuario"""
    config = obtener_config_nube()
    if not config.get("url") or not config.get("key"):
        return
    try:
        url_base = config["url"].strip().rstrip("/")
        key = config["key"].strip()
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}"
        }
        url_del = f"{url_base}/rest/v1/proyectos?id=eq.{proyecto_id}"
        if user_email:
            url_del += f"&usuario_email=eq.{urllib.parse.quote(user_email.strip().lower())}"
        req = urllib.request.Request(url_del, headers=headers, method="DELETE")
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass

def sincronizar_con_nube(usuario_id: int) -> tuple[bool, str]:
    """
    Sincroniza bidireccionalmente la base de datos local con la base de datos en la Nube (Supabase)
    estrictamente para la cuenta del usuario activo (Aislamiento Total por Cuenta de Google).
    """
    config = obtener_config_nube()
    if not config.get("url") or not config.get("key"):
        return False, "No se ha configurado ninguna base de datos en la nube (Supabase)."
    
    usuario = obtener_usuario_por_id(usuario_id)
    if not usuario or not usuario.get("email"):
        return False, "No se encontró el usuario activo para sincronizar."
        
    user_email = usuario["email"].strip().lower()
    
    try:
        url_base = config["url"].strip().rstrip("/")
        key = config["key"].strip()
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        # 1. PULL CLIENTES DESDE LA NUBE (Solo de esta cuenta Google)
        try:
            url_pull_cli = f"{url_base}/rest/v1/clientes?usuario_email=eq.{urllib.parse.quote(user_email)}&select=*"
            req_cli = urllib.request.Request(url_pull_cli, headers=headers)
            with urllib.request.urlopen(req_cli, timeout=8) as resp:
                nube_clientes = json.loads(resp.read().decode("utf-8"))
                for nc in nube_clientes:
                    cursor.execute("""
                    INSERT INTO clientes (
                        id, usuario_id, usuario_email, nombre_completo, nif_cif, telefono, email,
                        direccion_suministro, localidad, cups, referencia_catastral,
                        tipo_inmueble, notas, codigo_postal, municipio, provincia,
                        distribuidora, potencia_contratada_kw, tension_suministro
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        usuario_id = excluded.usuario_id,
                        usuario_email = excluded.usuario_email,
                        nombre_completo = excluded.nombre_completo,
                        nif_cif = excluded.nif_cif,
                        telefono = excluded.telefono,
                        email = excluded.email,
                        direccion_suministro = excluded.direccion_suministro,
                        localidad = excluded.localidad,
                        cups = excluded.cups,
                        referencia_catastral = excluded.referencia_catastral,
                        tipo_inmueble = excluded.tipo_inmueble,
                        notas = excluded.notas,
                        codigo_postal = excluded.codigo_postal,
                        municipio = excluded.municipio,
                        provincia = excluded.provincia,
                        distribuidora = excluded.distribuidora,
                        potencia_contratada_kw = excluded.potencia_contratada_kw,
                        tension_suministro = excluded.tension_suministro
                    """, (
                        nc.get("id"), usuario_id, user_email, nc.get("nombre_completo", ""),
                        nc.get("nif_cif", ""), nc.get("telefono", ""), nc.get("email", ""),
                        nc.get("direccion_suministro", ""), nc.get("localidad", ""), nc.get("cups", ""),
                        nc.get("referencia_catastral", ""), nc.get("tipo_inmueble", "Vivienda"),
                        nc.get("notas", ""), nc.get("codigo_postal", ""), nc.get("municipio", ""),
                        nc.get("provincia", "Murcia"), nc.get("distribuidora", "i-DE (Iberdrola)"),
                        nc.get("potencia_contratada_kw", ""), nc.get("tension_suministro", "Monofásica 230V")
                    ))
        except Exception:
            pass
        
        # 2. PULL PROYECTOS DESDE LA NUBE (Solo de esta cuenta Google)
        try:
            url_pull_pro = f"{url_base}/rest/v1/proyectos?usuario_email=eq.{urllib.parse.quote(user_email)}&select=*"
            req_pro = urllib.request.Request(url_pull_pro, headers=headers)
            with urllib.request.urlopen(req_pro, timeout=8) as resp:
                nube_proyectos = json.loads(resp.read().decode("utf-8"))
                for np in nube_proyectos:
                    cursor.execute("""
                    INSERT INTO proyectos (
                        id, usuario_id, usuario_email, cliente_id, nombre_proyecto, modulo, datos_json, resumen_potencia_o_importe
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        usuario_id = excluded.usuario_id,
                        usuario_email = excluded.usuario_email,
                        cliente_id = excluded.cliente_id,
                        nombre_proyecto = excluded.nombre_proyecto,
                        modulo = excluded.modulo,
                        datos_json = excluded.datos_json,
                        resumen_potencia_o_importe = excluded.resumen_potencia_o_importe
                    """, (
                        np.get("id"), usuario_id, user_email, np.get("cliente_id"),
                        np.get("nombre_proyecto", ""), np.get("modulo", ""),
                        np.get("datos_json", "{}"), np.get("resumen_potencia_o_importe", "")
                    ))
        except Exception:
            pass
        
        # 3. PUSH LOCAL A NUBE (Solo de este usuario_id)
        cursor.execute("SELECT * FROM clientes WHERE usuario_id = ?", (usuario_id,))
        local_clientes = [dict(r) for r in cursor.fetchall()]
        if local_clientes:
            for c in local_clientes:
                c["usuario_email"] = user_email
            req_push_cli = urllib.request.Request(
                f"{url_base}/rest/v1/clientes",
                data=json.dumps(local_clientes, ensure_ascii=False).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req_push_cli, timeout=8):
                    pass
            except Exception:
                pass
                
        cursor.execute("SELECT * FROM proyectos WHERE usuario_id = ?", (usuario_id,))
        local_proyectos = [dict(r) for r in cursor.fetchall()]
        if local_proyectos:
            for p in local_proyectos:
                p["usuario_email"] = user_email
            req_push_pro = urllib.request.Request(
                f"{url_base}/rest/v1/proyectos",
                data=json.dumps(local_proyectos, ensure_ascii=False).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            try:
                with urllib.request.urlopen(req_push_pro, timeout=8):
                    pass
            except Exception:
                pass
                
        conn.commit()
        conn.close()
        return True, f"Sincronización completada con éxito para {user_email}: {len(local_clientes)} clientes y {len(local_proyectos)} proyectos."
    except Exception as ex:
        return False, f"Error durante la sincronización con la nube: {ex}"

# =========================================================================
# FUNCIONES DE CLIENTES (CRM) - AISLAMIENTO ESTRICTO POR USUARIO
# =========================================================================
def listar_clientes(usuario_id: int) -> List[Dict[str, Any]]:
    """Devuelve la lista de clientes registrados por este usuario o asociados a su cuenta"""
    usuario = obtener_usuario_por_id(usuario_id)
    user_email = (usuario.get("email") or "").strip().lower() if usuario else ""

    conn = obtener_conexion()
    cursor = conn.cursor()

    # Auto-asociación inteligente: si existen clientes huérfanos o creados en modo local/invitado (id=1),
    # y el usuario actual está autenticado con Google u otra cuenta, vincularlos para que nunca se pierdan
    try:
        if user_email:
            cursor.execute("""
            UPDATE clientes 
            SET usuario_id = ?, usuario_email = ? 
            WHERE (usuario_email IS NOT NULL AND LOWER(usuario_email) = LOWER(?))
               OR (usuario_id = 1 AND (usuario_email IS NULL OR usuario_email = '' OR usuario_email LIKE '%bolimur.local'))
            """, (usuario_id, user_email, user_email))
            conn.commit()
    except Exception:
        pass

    cursor.execute("""
    SELECT * FROM clientes 
    WHERE usuario_id = ? 
       OR (usuario_email IS NOT NULL AND LOWER(usuario_email) = LOWER(?))
    ORDER BY nombre_completo ASC
    """, (usuario_id, user_email))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def recuperar_todos_clientes_locales(usuario_id: int) -> int:
    """Reasigna absolutamente todos los clientes huérfanos o de sesiones previas al usuario activo"""
    usuario = obtener_usuario_por_id(usuario_id)
    user_email = (usuario.get("email") or "").strip().lower() if usuario else ""
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM clientes WHERE usuario_id != ? OR usuario_id IS NULL", (usuario_id,))
    total_pendientes = cursor.fetchone()["total"]
    
    if total_pendientes > 0:
        cursor.execute("UPDATE clientes SET usuario_id = ?, usuario_email = ? WHERE usuario_id != ? OR usuario_id IS NULL", (usuario_id, user_email, usuario_id))
        cursor.execute("UPDATE proyectos SET usuario_id = ?, usuario_email = ? WHERE usuario_id != ? OR usuario_id IS NULL", (usuario_id, user_email, usuario_id))
        conn.commit()
    conn.close()
    return total_pendientes

def obtener_cliente_por_id(cliente_id: int, usuario_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Devuelve un cliente específico comprobando la pertenencia al usuario si se especifica"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    if usuario_id is not None:
        cursor.execute("SELECT * FROM clientes WHERE id = ? AND usuario_id = ?", (cliente_id, usuario_id))
    else:
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def buscar_cliente_duplicado(usuario_id: int, nif_cif: str, nombre_completo: str) -> Optional[Dict[str, Any]]:
    """Comprueba si ya existe un cliente con el mismo NIF o nombre exacto dentro de la cuenta del usuario"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    nif_clean = nif_cif.strip().upper() if nif_cif else ""
    nom_clean = nombre_completo.strip()
    
    if nif_clean:
        cursor.execute("SELECT * FROM clientes WHERE usuario_id = ? AND UPPER(nif_cif) = ?", (usuario_id, nif_clean))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)
            
    if nom_clean:
        cursor.execute("SELECT * FROM clientes WHERE usuario_id = ? AND LOWER(nombre_completo) = LOWER(?)", (usuario_id, nom_clean))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row)
            
    conn.close()
    return None

def crear_cliente(usuario_id: int, datos: Dict[str, Any]) -> tuple[bool, int]:
    """Crea un nuevo cliente asociado estrictamente al usuario_id y a su correo Google"""
    usuario = obtener_usuario_por_id(usuario_id)
    user_email = (usuario.get("email") or "").strip().lower() if usuario else ""
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO clientes (
            usuario_id, usuario_email, nombre_completo, nif_cif, telefono, email,
            direccion_suministro, localidad, cups, referencia_catastral,
            tipo_inmueble, notas, codigo_postal, municipio, provincia,
            distribuidora, potencia_contratada_kw, tension_suministro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario_id,
            user_email,
            datos.get("nombre_completo", "").strip(),
            datos.get("nif_cif", "").strip().upper(),
            datos.get("telefono", "").strip(),
            datos.get("email", "").strip(),
            datos.get("direccion_suministro", "").strip(),
            datos.get("localidad", "").strip(),
            datos.get("cups", "").strip().upper(),
            datos.get("referencia_catastral", "").strip().upper(),
            datos.get("tipo_inmueble", "Vivienda").strip(),
            datos.get("notas", "").strip(),
            datos.get("codigo_postal", "").strip(),
            datos.get("municipio", "").strip(),
            datos.get("provincia", "Murcia").strip(),
            datos.get("distribuidora", "i-DE (Iberdrola)").strip(),
            datos.get("potencia_contratada_kw", "").strip(),
            datos.get("tension_suministro", "Monofásica 230V").strip()
        ))
        conn.commit()
        nuevo_id = cursor.lastrowid
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (nuevo_id,))
        cli_nuevo_row = cursor.fetchone()
        conn.close()
        
        # Enviar automáticamente a la nube si está configurada
        if cli_nuevo_row:
            push_cliente_a_nube(dict(cli_nuevo_row), user_email=user_email)
            
        return True, nuevo_id
    except Exception:
        conn.close()
        return False, -1

def actualizar_cliente(cliente_id: int, usuario_id: int, datos: Dict[str, Any]) -> bool:
    """Actualiza los datos de un cliente del usuario activo"""
    usuario = obtener_usuario_por_id(usuario_id)
    user_email = (usuario.get("email") or "").strip().lower() if usuario else ""
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE clientes SET
            nombre_completo = ?,
            nif_cif = ?,
            telefono = ?,
            email = ?,
            direccion_suministro = ?,
            localidad = ?,
            cups = ?,
            referencia_catastral = ?,
            tipo_inmueble = ?,
            notas = ?,
            codigo_postal = ?,
            municipio = ?,
            provincia = ?,
            distribuidora = ?,
            potencia_contratada_kw = ?,
            tension_suministro = ?
        WHERE id = ? AND usuario_id = ?
        """, (
            datos.get("nombre_completo", "").strip(),
            datos.get("nif_cif", "").strip().upper(),
            datos.get("telefono", "").strip(),
            datos.get("email", "").strip(),
            datos.get("direccion_suministro", "").strip(),
            datos.get("localidad", "").strip(),
            datos.get("cups", "").strip().upper(),
            datos.get("referencia_catastral", "").strip().upper(),
            datos.get("tipo_inmueble", "Vivienda").strip(),
            datos.get("notas", "").strip(),
            datos.get("codigo_postal", "").strip(),
            datos.get("municipio", "").strip(),
            datos.get("provincia", "Murcia").strip(),
            datos.get("distribuidora", "i-DE (Iberdrola)").strip(),
            datos.get("potencia_contratada_kw", "").strip(),
            datos.get("tension_suministro", "Monofásica 230V").strip(),
            cliente_id,
            usuario_id
        ))
        conn.commit()
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        cli_up_row = cursor.fetchone()
        conn.close()
        
        if cli_up_row:
            push_cliente_a_nube(dict(cli_up_row), user_email=user_email)
            
        return True
    except Exception:
        conn.close()
        return False

def eliminar_cliente(cliente_id: int, usuario_id: int) -> bool:
    """Elimina un cliente perteneciente a este usuario"""
    usuario = obtener_usuario_por_id(usuario_id)
    user_email = (usuario.get("email") or "").strip().lower() if usuario else ""
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM clientes WHERE id = ? AND usuario_id = ?", (cliente_id, usuario_id))
        conn.commit()
        conn.close()
        
        delete_cliente_de_nube(cliente_id, user_email=user_email)
        return True
    except Exception:
        conn.close()
        return False

def limpiar_duplicados_clientes(usuario_id: int) -> int:
    """Busca clientes duplicados por NIF o Nombre dentro de la cuenta del usuario, reasigna sus proyectos y elimina los repetidos."""
    usuario = obtener_usuario_por_id(usuario_id)
    user_email = (usuario.get("email") or "").strip().lower() if usuario else ""
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE usuario_id = ? ORDER BY id ASC", (usuario_id,))
    todos = [dict(r) for r in cursor.fetchall()]
    
    agrupados: Dict[str, List[Dict[str, Any]]] = {}
    for c in todos:
        nif = (c.get("nif_cif") or "").strip().upper()
        nom = (c.get("nombre_completo") or "").strip().lower()
        clave = nif if len(nif) >= 4 else nom
        if not clave:
            continue
        agrupados.setdefault(clave, []).append(c)
        
    borrados = 0
    for clave, lista in agrupados.items():
        if len(lista) > 1:
            principal = lista[0]
            duplicados = lista[1:]
            for dup in duplicados:
                cursor.execute("UPDATE proyectos SET cliente_id = ? WHERE cliente_id = ? AND usuario_id = ?", (principal["id"], dup["id"], usuario_id))
                cursor.execute("DELETE FROM clientes WHERE id = ? AND usuario_id = ?", (dup["id"], usuario_id))
                delete_cliente_de_nube(dup["id"], user_email=user_email)
                borrados += 1
                
    conn.commit()
    conn.close()
    return borrados

# =========================================================================
# FUNCIONES DE PROYECTOS Y CÁLCULOS GUARDADOS - AISLAMIENTO POR USUARIO
# =========================================================================
def guardar_proyecto(usuario_id: int, cliente_id: Optional[int], nombre_proyecto: str, modulo: str, datos: Dict[str, Any], resumen: str = "") -> tuple[bool, int]:
    """Guarda un cálculo o proyecto asociado estrictamente a la cuenta del usuario"""
    usuario = obtener_usuario_por_id(usuario_id)
    user_email = (usuario.get("email") or "").strip().lower() if usuario else ""
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        datos_str = json.dumps(datos, ensure_ascii=False)
        cursor.execute("""
        INSERT INTO proyectos (usuario_id, usuario_email, cliente_id, nombre_proyecto, modulo, datos_json, resumen_potencia_o_importe)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario_id, user_email, cliente_id, nombre_proyecto.strip(), modulo, datos_str, resumen))
        conn.commit()
        p_id = cursor.lastrowid
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (p_id,))
        p_row = cursor.fetchone()
        conn.close()
        
        if p_row:
            push_proyecto_a_nube(dict(p_row), user_email=user_email)
            
        return True, p_id
    except Exception:
        conn.close()
        return False, -1

def listar_proyectos_usuario(usuario_id: int, modulo: Optional[str] = None) -> List[Dict[str, Any]]:
    """Devuelve los proyectos pertenecientes a este usuario o a su cuenta Google"""
    usuario = obtener_usuario_por_id(usuario_id)
    user_email = (usuario.get("email") or "").strip().lower() if usuario else ""

    conn = obtener_conexion()
    cursor = conn.cursor()

    try:
        if user_email:
            cursor.execute("""
            UPDATE proyectos 
            SET usuario_id = ?, usuario_email = ? 
            WHERE (usuario_email IS NOT NULL AND LOWER(usuario_email) = LOWER(?))
               OR (usuario_id = 1 AND (usuario_email IS NULL OR usuario_email = '' OR usuario_email LIKE '%bolimur.local'))
            """, (usuario_id, user_email, user_email))
            conn.commit()
    except Exception:
        pass

    if modulo:
        cursor.execute("""
        SELECT p.*, c.nombre_completo as cliente_nombre 
        FROM proyectos p 
        LEFT JOIN clientes c ON p.cliente_id = c.id 
        WHERE (p.usuario_id = ? OR (p.usuario_email IS NOT NULL AND LOWER(p.usuario_email) = LOWER(?)))
          AND p.modulo = ? 
        ORDER BY p.fecha_guardado DESC
        """, (usuario_id, user_email, modulo))
    else:
        cursor.execute("""
        SELECT p.*, c.nombre_completo as cliente_nombre 
        FROM proyectos p 
        LEFT JOIN clientes c ON p.cliente_id = c.id 
        WHERE p.usuario_id = ? OR (p.usuario_email IS NOT NULL AND LOWER(p.usuario_email) = LOWER(?))
        ORDER BY p.fecha_guardado DESC
        """, (usuario_id, user_email))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def listar_proyectos_por_cliente(cliente_id: int, usuario_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Devuelve los proyectos de un cliente verificando pertenencia al usuario"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    if usuario_id is not None:
        cursor.execute("""
        SELECT * FROM proyectos 
        WHERE cliente_id = ? AND usuario_id = ? 
        ORDER BY fecha_guardado DESC
        """, (cliente_id, usuario_id))
    else:
        cursor.execute("""
        SELECT * FROM proyectos 
        WHERE cliente_id = ? 
        ORDER BY fecha_guardado DESC
        """, (cliente_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def cargar_proyecto_por_id(proyecto_id: int, usuario_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Carga un proyecto específico verificando el usuario si se provee"""
    conn = obtener_conexion()
    cursor = conn.cursor()
    if usuario_id is not None:
        cursor.execute("SELECT * FROM proyectos WHERE id = ? AND usuario_id = ?", (proyecto_id, usuario_id))
    else:
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        res = dict(row)
        try:
            res["datos"] = json.loads(res["datos_json"])
        except:
            res["datos"] = {}
        return res
    return None

def eliminar_proyecto(proyecto_id: int, usuario_id: Optional[int] = None) -> bool:
    """Elimina un proyecto del usuario activo"""
    user_email = ""
    if usuario_id is not None:
        usuario = obtener_usuario_por_id(usuario_id)
        user_email = (usuario.get("email") or "").strip().lower() if usuario else ""
        
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        if usuario_id is not None:
            cursor.execute("DELETE FROM proyectos WHERE id = ? AND usuario_id = ?", (proyecto_id, usuario_id))
        else:
            cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
        conn.commit()
        conn.close()
        
        delete_proyecto_de_nube(proyecto_id, user_email=user_email)
        return True
    except Exception:
        conn.close()
        return False

# =========================================================================
# FUNCIONES DE RESPALDO Y EXPORTACIÓN / IMPORTACIÓN NUBE (JSON/ZIP)
# =========================================================================
def exportar_copia_seguridad_nube(usuario_id: int) -> str:
    usuario = obtener_usuario_por_id(usuario_id)
    clientes = listar_clientes(usuario_id)
    proyectos = listar_proyectos_usuario(usuario_id)
    
    backup_data = {
        "version": "2.0",
        "usuario": usuario,
        "clientes": clientes,
        "proyectos": proyectos
    }
    return json.dumps(backup_data, indent=2, ensure_ascii=False)

def importar_copia_seguridad_nube(usuario_id: int, json_str: str) -> tuple[bool, str]:
    try:
        usuario = obtener_usuario_por_id(usuario_id)
        user_email = (usuario.get("email") or "").strip().lower() if usuario else ""
        
        data = json.loads(json_str)
        clientes_in = data.get("clientes", [])
        proyectos_in = data.get("proyectos", [])
        
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        mapa_clientes_antiguos_nuevos = {}
        for c in clientes_in:
            old_id = c.get("id")
            cursor.execute("""
            INSERT INTO clientes (
                usuario_id, usuario_email, nombre_completo, nif_cif, telefono, email,
                direccion_suministro, localidad, cups, referencia_catastral,
                tipo_inmueble, notas, codigo_postal, municipio, provincia,
                distribuidora, potencia_contratada_kw, tension_suministro
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usuario_id,
                user_email,
                c.get("nombre_completo", ""),
                c.get("nif_cif", ""),
                c.get("telefono", ""),
                c.get("email", ""),
                c.get("direccion_suministro", ""),
                c.get("localidad", ""),
                c.get("cups", ""),
                c.get("referencia_catastral", ""),
                c.get("tipo_inmueble", "Vivienda"),
                c.get("notas", ""),
                c.get("codigo_postal", ""),
                c.get("municipio", ""),
                c.get("provincia", "Murcia"),
                c.get("distribuidora", "i-DE (Iberdrola)"),
                c.get("potencia_contratada_kw", ""),
                c.get("tension_suministro", "Monofásica 230V")
            ))
            nuevo_id = cursor.lastrowid
            if old_id:
                mapa_clientes_antiguos_nuevos[old_id] = nuevo_id
                
        for p in proyectos_in:
            c_id_orig = p.get("cliente_id")
            c_id_nuevo = mapa_clientes_antiguos_nuevos.get(c_id_orig, None)
            cursor.execute("""
            INSERT INTO proyectos (usuario_id, usuario_email, cliente_id, nombre_proyecto, modulo, datos_json, resumen_potencia_o_importe)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                usuario_id, user_email, c_id_nuevo, p.get("nombre_proyecto"), p.get("modulo"),
                p.get("datos_json"), p.get("resumen_potencia_o_importe")
            ))
            
        conn.commit()
        conn.close()
        return True, f"Se han importado {len(clientes_in)} clientes y {len(proyectos_in)} proyectos en tu cuenta privada."
    except Exception as ex:
        return False, f"Error al importar archivo de respaldo: {ex}"
