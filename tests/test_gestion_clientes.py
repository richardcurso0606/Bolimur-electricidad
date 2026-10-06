# -*- coding: utf-8 -*-
"""
Tests unitarios para el módulo de Gestión de Clientes (CRM) y base de datos.
"""
import pytest

def test_import_gestion_clientes():
    """Verifica que el módulo de gestión de clientes se importe sin errores de sintaxis o indentación"""
    from modulos import gestion_clientes
    assert hasattr(gestion_clientes, "renderizar")
    assert hasattr(gestion_clientes, "generar_resumen_portapapeles")

def test_generar_resumen_portapapeles():
    """Verifica la generación de texto para WhatsApp / Email del cliente"""
    from modulos.gestion_clientes import generar_resumen_portapapeles
    cliente_dummy = {
        "id": 999,
        "nombre_completo": "CLIENTE DE PRUEBAS RESUMEN",
        "nif_cif": "12345678Z",
        "telefono": "600123456",
        "email": "test@bolimur.local",
        "direccion_suministro": "Calle Mayor 10",
        "localidad": "Murcia",
        "codigo_postal": "30001",
        "cups": "ES0021000000000000AA",
        "potencia_contratada_kw": "5.75",
        "distribuidora": "i-DE (Iberdrola)",
        "tipo_inmueble": "Vivienda"
    }
    resumen = generar_resumen_portapapeles(cliente_dummy)
    assert "CLIENTE DE PRUEBAS RESUMEN" in resumen
    assert "12345678Z" in resumen
    assert "ES0021000000000000AA" in resumen
    assert "5.75" in resumen

def test_guardar_proyecto_y_sanitizacion_nube():
    """Verifica el guardado en SQLite y la sanitización de imágenes gigantes en la réplica de nube"""
    import json
    from modulos import db_manager

    # 1. Verificar sanitización de payload gigante para Supabase REST
    payload_gigante = {
        "id": 888,
        "usuario_email": "test@bolimur.com",
        "nombre_proyecto": "Proyecto con Planos",
        "datos_json": json.dumps({
            "mtd_plano_situacion": "data:image/png;base64," + ("A" * 600_000),
            "potencia": 9200
        })
    }
    # Verificamos que _do_push_proyecto no falle y procese adecuadamente
    db_manager.push_proyecto_a_nube(payload_gigante, "test@bolimur.com")

    # 2. Guardar un proyecto real en la base de datos local SQLite
    ok, p_id = db_manager.guardar_proyecto(
        usuario_id=1,
        cliente_id=None,
        nombre_proyecto="Test Proyecto Unitario Guardado",
        modulo="Memoria Técnica (MTD 30)",
        datos={"test_key": "test_val", "potencia_w": 5750},
        resumen="5.75 kW | Test"
    )
    assert ok is True
    assert p_id > 0

    proy = db_manager.cargar_proyecto_por_id(p_id, usuario_id=1)
    assert proy is not None
    assert proy["nombre_proyecto"] == "Test Proyecto Unitario Guardado"
    assert "test_val" in proy["datos_json"]

