# -*- coding: utf-8 -*-
"""
Tests unitarios para el módulo modulos.radar_normativo (Radar y Vigilancia Normativa BOE)
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock
from modulos import radar_normativo

def test_normas_monitorizadas_estructura():
    """Verifica que las normas clave estén registradas con sus campos obligatorios."""
    assert len(radar_normativo.NORMAS_MONITORIZADAS) >= 5
    ids = list(radar_normativo.NORMAS_MONITORIZADAS.keys())
    assert "BOE-A-2019-5089" in ids  # RD 244/2019 Autoconsumo
    assert "BOE-A-2002-18099" in ids  # REBT RD 842/2002
    assert "BOE-A-2014-13679" in ids  # ITC-BT-52 IRVE
    assert "BOE-A-2022-9988" in ids   # RD 450/2022 CTE DB-HE

    for id_norma, datos in radar_normativo.NORMAS_MONITORIZADAS.items():
        assert "codigo" in datos
        assert "titulo" in datos
        assert "materia" in datos
        assert "impacto_bolimur" in datos
        assert "nivel_importancia" in datos
        assert datos["nivel_importancia"] in ["CRÍTICA", "ALTA", "MEDIA"]
        assert "prioridad" in datos
        assert isinstance(datos["prioridad"], int)
        assert "motivo_criticidad" in datos
        assert len(datos["impacto_bolimur"]) > 0

def test_cargar_y_guardar_cache(tmp_path):
    """Verifica la persistencia y recuperación de datos en la caché local."""
    test_cache_file = tmp_path / "test_radar_cache.json"
    
    with patch.object(radar_normativo, 'CACHE_FILE', str(test_cache_file)):
        datos = {"BOE-TEST-001": {"titulo": "Norma Prueba", "estado": "Vigente"}}
        radar_normativo.guardar_cache_normativa(datos)
        
        assert test_cache_file.exists()
        recuperados = radar_normativo.cargar_cache_normativa()
        assert "BOE-TEST-001" in recuperados
        assert recuperados["BOE-TEST-001"]["titulo"] == "Norma Prueba"

def test_analizar_impacto_cambio_con_ia_sin_api_key():
    """Verifica que el generador de dictamen de impacto funcione correctamente en modo offline."""
    dictamen = radar_normativo.analizar_impacto_cambio_con_ia(
        norma_codigo="RD 244/2019",
        norma_titulo="Real Decreto 244/2019 de Autoconsumo",
        modificacion_texto="Aumento de distancia máxima en autoconsumo colectivo a través de red a 5.000 metros.",
        api_key=None
    )
    assert isinstance(dictamen, str)
    assert "Dictamen de Impacto Técnico" in dictamen or "DICTAMEN" in dictamen.upper()
    assert "RD 244/2019" in dictamen
    assert "Autoconsumo" in dictamen or "autoconsumo" in dictamen

def test_consultar_norma_boe_live_con_mock():
    """Verifica el procesamiento de respuestas de la API del BOE."""
    mock_payload_meta = {
        "data": [
            {
                "titulo": "Real Decreto 244/2019, de 5 de abril",
                "fecha_actualizacion": "2024-01-15"
            }
        ]
    }
    mock_payload_ana = {
        "data": [
            {
                "referencias": {
                    "posteriores": [
                        {
                            "posterior": [
                                {
                                    "id_norma": "BOE-A-2023-12345",
                                    "relacion": {"texto": "MODIFICA"},
                                    "texto": "el art. 4, por Real Decreto-ley 5/2023"
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_cm1 = MagicMock()
        mock_cm1.status = 200
        mock_cm1.read.return_value = json.dumps(mock_payload_meta).encode('utf-8')
        mock_cm1.__enter__.return_value = mock_cm1

        mock_cm2 = MagicMock()
        mock_cm2.status = 200
        mock_cm2.read.return_value = json.dumps(mock_payload_ana).encode('utf-8')
        mock_cm2.__enter__.return_value = mock_cm2

        # Retornar mock_cm1 para metadatos y mock_cm2 para análisis
        mock_urlopen.side_effect = [mock_cm1, mock_cm2]
        
        info = radar_normativo.consultar_norma_boe_live("BOE-A-2019-5089")
        assert info["ok"] is True
        assert "Real Decreto 244/2019" in info.get("titulo", "")
        assert len(info.get("modificaciones", [])) == 1
        assert info["modificaciones"][0]["id_mod"] == "BOE-A-2023-12345"
