# -*- coding: utf-8 -*-
"""
Pruebas unitarias para el módulo asistente_ia_rebt.py
"""

import pytest
from modulos import asistente_ia_rebt

def test_buscar_respuesta_offline_proyecto_vs_mtd():
    resp = asistente_ia_rebt.buscar_respuesta_offline("¿Cuándo necesito un proyecto de ingeniero en vez de MTD para un bar?")
    assert "ITC-BT-04" in resp
    assert "Pública Concurrencia" in resp or "Proyecto" in resp
    assert "bar" in resp.lower() or "restaurante" in resp.lower()

def test_buscar_respuesta_offline_diferenciales():
    resp = asistente_ia_rebt.buscar_respuesta_offline("¿Cuántos circuitos puedo poner por cada diferencial de 30 mA?")
    assert "5 circuitos" in resp or "ITC-BT-25" in resp

def test_buscar_respuesta_offline_derivacion_individual():
    resp = asistente_ia_rebt.buscar_respuesta_offline("¿Cuál es la caída de tensión máxima en una derivación individual DI?")
    assert "1,5%" in resp or "ITC-BT-15" in resp
    assert "M32" in resp or "6" in resp

def test_buscar_respuesta_offline_tierra():
    resp = asistente_ia_rebt.buscar_respuesta_offline("¿Cuál es la resistencia máxima de la toma de tierra en viviendas?")
    assert "ITC-BT-18" in resp
    assert "50" in resp or "15" in resp or "tensión de contacto" in resp.lower()

def test_responder_consulta_rebt_sin_clave():
    # Cuando no hay clave API configurada, debe responder con el motor offline de inmediato sin excepción
    resp = asistente_ia_rebt.responder_consulta_rebt("¿Qué exige el cuadro de obra provisional?")
    assert "ITC-BT-33" in resp or "cuadro" in resp.lower()
