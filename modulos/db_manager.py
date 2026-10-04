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
    
    # Cuentas pre-configuradas de Google del instalador (Richard Orlando / Bolimur)
    cuentas_google_base = [
        ("Euforiamix0606@gmail.com", "Richard Orlando (Euforia)", "BOLIMUR ELECTRICIDAD", "REBT-30/15892"),
        ("13789477@alu.murciaeduca.es", "Richard Orlando Choque", "FREMM / Murcia Educa", "REBT-30/15892"),
        ("richardcurso0606@gmail.com", "Richard (RC0606)", "BOLIMUR INSTALACIONES Y REFORMAS", "REBT-30/15892"),
        ("richard.emprende@gmail.com", "Richard Emprende", "BOLIMUR INSTALACIONES", "REBT-30/15892"),
        ("fremm.instalador@gmail.com", "Richard FREMM", "FREMM INSTALADORES MURCIA", "REBT-30/15892")
    ]
    for email_g, nom_g, emp_g, lic_g in cuentas_google_base:
        cursor.execute("SELECT id FROM usuarios WHERE LOWER(email) = LOWER(?)", (email_g,))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO usuarios (
                email, username_windows, password_hash, nombre_instalador, nombre_empresa,
                num_licencia_rebt, categoria_rebt, localidad, telefono, email_contacto
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_g.strip().lower(),
                email_g.split('@')[0],
                hashear_password("123456"),
                nom_g,
                emp_g,
                lic_g,
                "Instalador Especialista (IBTE)",
                "Murcia, España",
                "+34 600 000 000",
                email_g
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

def buscar_cliente_duplicado(usuario_id: int, nif_cif: str, nombre_completo: str) -> Optional[Dict[str, Any]]:
    """Comprueba si ya existe un cliente con el mismo NIF o nombre exacto"""
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
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO clientes (
            usuario_id, nombre_completo, nif_cif, telefono, email,
            direccion_suministro, localidad, cups, referencia_catastral,
            tipo_inmueble, notas, codigo_postal, municipio, provincia,
            distribuidora, potencia_contratada_kw, tension_suministro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario_id,
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

def limpiar_duplicados_clientes(usuario_id: int) -> int:
    """Busca clientes duplicados por NIF o Nombre, reasigna sus proyectos y elimina los repetidos."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE usuario_id = ? ORDER BY id ASC", (usuario_id,))
    todos = [dict(r) for r in cursor.fetchall()]
    
    agrupados: Dict[str, List[Dict[str, Any]]] = {}
    for c in todos:
        # Clave de agrupamiento: NIF si existe, o Nombre normalizado
        nif = (c.get("nif_cif") or "").strip().upper()
        nom = (c.get("nombre_completo") or "").strip().lower()
        clave = nif if len(nif) >= 4 else nom
        if not clave:
            continue
        agrupados.setdefault(clave, []).append(c)
        
    borrados = 0
    for clave, lista in agrupados.items():
        if len(lista) > 1:
            # Mantener el primero (principal)
            principal = lista[0]
            duplicados = lista[1:]
            for dup in duplicados:
                # Reasignar proyectos al principal
                cursor.execute("UPDATE proyectos SET cliente_id = ? WHERE cliente_id = ? AND usuario_id = ?", (principal["id"], dup["id"], usuario_id))
                # Borrar duplicado
                cursor.execute("DELETE FROM clientes WHERE id = ? AND usuario_id = ?", (dup["id"], usuario_id))
                borrados += 1
                
    conn.commit()
    conn.close()
    return borrados

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
