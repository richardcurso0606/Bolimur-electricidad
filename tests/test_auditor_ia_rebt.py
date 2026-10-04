# -*- coding: utf-8 -*-
"""
Pruebas unitarias para el módulo de auditoría con IA y reglas REBT (auditor_ia_rebt.py).
"""

import pytest
from modulos import auditor_ia_rebt

def test_limpiar_b64_imagen():
    raw_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    data_uri = f"data:image/png;base64,{raw_b64}"
    
    mime, clean = auditor_ia_rebt._limpiar_b64_imagen(data_uri)
    assert mime == "image/png"
    assert clean == raw_b64

    mime2, clean2 = auditor_ia_rebt._limpiar_b64_imagen(raw_b64)
    assert mime2 == "image/jpeg"
    assert clean2 == raw_b64

def test_auditar_con_motor_reglas_cuadro():
    res = auditor_ia_rebt._auditar_con_motor_reglas_rebt(
        tipo_evidencia="Cuadro General (CGMP) montado y rotulado",
        descripcion_usuario="Cuadro de electrificación básica con IGA 25A y diferencial 30mA"
    )
    assert res["estado"] in ("conforme", "advertencia", "no_conforme")
    assert "ITC-BT-17" in res["normas_aplicadas"]
    assert len(res["elementos_identificados"]) >= 3
    assert len(res["comprobaciones"]) >= 3
    assert res["origen_auditoria"] == "motor_reglas_rebt"

def test_auditar_con_motor_reglas_tierra():
    res = auditor_ia_rebt._auditar_con_motor_reglas_rebt(
        tipo_evidencia="Punto de Puesta a Tierra (Pica, Arqueta y Borna)",
        descripcion_usuario="Pica de tierra y arqueta de registro"
    )
    assert "ITC-BT-18" in res["normas_aplicadas"]
    assert any("pica" in e.lower() or "electrodo" in e.lower() for e in res["elementos_identificados"])

def test_auditar_con_motor_reglas_multifuncion():
    res = auditor_ia_rebt._auditar_con_motor_reglas_rebt(
        tipo_evidencia="Display Comprobador Multifunción (Medida Rt / PE)",
        descripcion_usuario="Resistencia de tierra 14.2 ohmios"
    )
    assert "ITC-BT-05" in res["normas_aplicadas"]
    assert res["estado"] == "conforme"

def test_auditar_evidencia_multimodal_fallback():
    # Sin API key configurada, debe retornar el dictamen del motor experto de reglas sin fallar
    res = auditor_ia_rebt.auditar_evidencia_multimodal(
        imagen_b64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        tipo_evidencia="Cuadro General (CGMP)",
        descripcion_usuario="Prueba unitaria cuadro",
        api_key=None
    )
    assert res["estado"] == "conforme"
    assert res["origen_auditoria"] == "motor_reglas_rebt"
