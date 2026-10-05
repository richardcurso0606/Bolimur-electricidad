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
