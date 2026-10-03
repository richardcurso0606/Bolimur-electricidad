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
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
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
    
    # Tabla de Proyectos y Cálculos Guardados por Cliente
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
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
    
    conn.commit()
    
    # Crear usuario por defecto de Windows si no existe ninguno
    usuario_win_actual = getpass.getuser()
    cursor.execute("SELECT id FROM usuarios WHERE username_windows = ?", (usuario_win_actual,))
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO usuarios (
            email, username_windows, password_hash, nombre_instalador, nombre_empresa,
            nif_cif, num_licencia_rebt, categoria_rebt, registro_industrial,
            direccion, localidad, telefono, email_contacto
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"{usuario_win_actual}@bolimur.local",
            usuario_win_actual,
            hashear_password("123456"),
            "Richard Orlando Choque Tejerina",
            "BOLIMUR INSTALACIONES Y REFORMAS",
            "B-73000000",
            "REBT-30/15892",
            "Instalador Especialista (IBTE)",
            "RII-30/004521",
            "C/ Principal, 1",
            "Rincón de Seca, Murcia",
            "+34 600 000 000",
            "info@bolimur.com"
        ))
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

# =========================================================================
# FUNCIONES DE CLIENTES (CRM)
# =========================================================================
def listar_clientes(usuario_id: int) -> List[Dict[str, Any]]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE usuario_id = ? ORDER BY nombre_completo ASC", (usuario_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def obtener_cliente_por_id(cliente_id: int, usuario_id: int) -> Optional[Dict[str, Any]]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE id = ? AND usuario_id = ?", (cliente_id, usuario_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def crear_cliente(usuario_id: int, datos: Dict[str, Any]) -> tuple[bool, int]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO clientes (
            usuario_id, nombre_completo, nif_cif, telefono, email,
            direccion_suministro, localidad, cups, referencia_catastral,
            tipo_inmueble, notas
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario_id,
            datos.get("nombre_completo", "").strip(),
            datos.get("nif_cif", "").strip(),
            datos.get("telefono", "").strip(),
            datos.get("email", "").strip(),
            datos.get("direccion_suministro", "").strip(),
            datos.get("localidad", "").strip(),
            datos.get("cups", "").strip(),
            datos.get("referencia_catastral", "").strip(),
            datos.get("tipo_inmueble", "Vivienda").strip(),
            datos.get("notas", "").strip()
        ))
        conn.commit()
        nuevo_id = cursor.lastrowid
        conn.close()
        return True, nuevo_id
    except Exception:
        conn.close()
        return False, -1

def actualizar_cliente(cliente_id: int, usuario_id: int, datos: Dict[str, Any]) -> bool:
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
            notas = ?
        WHERE id = ? AND usuario_id = ?
        """, (
            datos.get("nombre_completo", "").strip(),
            datos.get("nif_cif", "").strip(),
            datos.get("telefono", "").strip(),
            datos.get("email", "").strip(),
            datos.get("direccion_suministro", "").strip(),
            datos.get("localidad", "").strip(),
            datos.get("cups", "").strip(),
            datos.get("referencia_catastral", "").strip(),
            datos.get("tipo_inmueble", "Vivienda").strip(),
            datos.get("notas", "").strip(),
            cliente_id,
            usuario_id
        ))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False

def eliminar_cliente(cliente_id: int, usuario_id: int) -> bool:
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM clientes WHERE id = ? AND usuario_id = ?", (cliente_id, usuario_id))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False

# =========================================================================
# FUNCIONES DE PROYECTOS Y CÁLCULOS GUARDADOS
# =========================================================================
def guardar_proyecto(usuario_id: int, cliente_id: Optional[int], nombre_proyecto: str, modulo: str, datos: Dict[str, Any], resumen: str = "") -> tuple[bool, int]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        datos_str = json.dumps(datos, ensure_ascii=False)
        cursor.execute("""
        INSERT INTO proyectos (usuario_id, cliente_id, nombre_proyecto, modulo, datos_json, resumen_potencia_o_importe)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_id, cliente_id, nombre_proyecto.strip(), modulo, datos_str, resumen))
        conn.commit()
        p_id = cursor.lastrowid
        conn.close()
        return True, p_id
    except Exception:
        conn.close()
        return False, -1

def listar_proyectos_usuario(usuario_id: int, modulo: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    if modulo:
        cursor.execute("""
        SELECT p.*, c.nombre_completo as cliente_nombre 
        FROM proyectos p 
        LEFT JOIN clientes c ON p.cliente_id = c.id 
        WHERE p.usuario_id = ? AND p.modulo = ? 
        ORDER BY p.fecha_guardado DESC
        """, (usuario_id, modulo))
    else:
        cursor.execute("""
        SELECT p.*, c.nombre_completo as cliente_nombre 
        FROM proyectos p 
        LEFT JOIN clientes c ON p.cliente_id = c.id 
        WHERE p.usuario_id = ? 
        ORDER BY p.fecha_guardado DESC
        """, (usuario_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def listar_proyectos_por_cliente(cliente_id: int, usuario_id: int) -> List[Dict[str, Any]]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM proyectos 
    WHERE cliente_id = ? AND usuario_id = ? 
    ORDER BY fecha_guardado DESC
    """, (cliente_id, usuario_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def cargar_proyecto_por_id(proyecto_id: int, usuario_id: int) -> Optional[Dict[str, Any]]:
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id = ? AND usuario_id = ?", (proyecto_id, usuario_id))
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

def eliminar_proyecto(proyecto_id: int, usuario_id: int) -> bool:
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM proyectos WHERE id = ? AND usuario_id = ?", (proyecto_id, usuario_id))
        conn.commit()
        conn.close()
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
        "version": "1.0",
        "usuario": usuario,
        "clientes": clientes,
        "proyectos": proyectos
    }
    return json.dumps(backup_data, indent=2, ensure_ascii=False)

def importar_copia_seguridad_nube(usuario_id: int, json_str: str) -> tuple[bool, str]:
    try:
        data = json.loads(json_str)
        clientes_in = data.get("clientes", [])
        proyectos_in = data.get("proyectos", [])
        
        conn = obtener_conexion()
        cursor = conn.cursor()
        
        mapa_clientes_antiguos_nuevos = {}
        for c in clientes_in:
            old_id = c.get("id")
            cursor.execute("""
            INSERT INTO clientes (usuario_id, nombre_completo, nif_cif, telefono, email, direccion_suministro, localidad, cups, referencia_catastral, tipo_inmueble, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usuario_id, c.get("nombre_completo"), c.get("nif_cif"), c.get("telefono"),
                c.get("email"), c.get("direccion_suministro"), c.get("localidad"),
                c.get("cups"), c.get("referencia_catastral"), c.get("tipo_inmueble"), c.get("notas")
            ))
            nuevo_id = cursor.lastrowid
            if old_id:
                mapa_clientes_antiguos_nuevos[old_id] = nuevo_id
                
        for p in proyectos_in:
            c_id_orig = p.get("cliente_id")
            c_id_nuevo = mapa_clientes_antiguos_nuevos.get(c_id_orig, None)
            cursor.execute("""
            INSERT INTO proyectos (usuario_id, cliente_id, nombre_proyecto, modulo, datos_json, resumen_potencia_o_importe)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                usuario_id, c_id_nuevo, p.get("nombre_proyecto"), p.get("modulo"),
                p.get("datos_json"), p.get("resumen_potencia_o_importe")
            ))
            
        conn.commit()
        conn.close()
        return True, f"Se han importado {len(clientes_in)} clientes y {len(proyectos_in)} proyectos correctamente."
    except Exception as ex:
        return False, f"Error al importar archivo de respaldo: {ex}"
