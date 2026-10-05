# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from modulos import control_salida

class TestControlSalida(unittest.TestCase):
    def test_inyectar_control_escape(self):
        """Verifica que el componente HTML con el script de escape se genere correctamente."""
        with patch("streamlit.components.v1.html") as mock_html:
            control_salida.inyectar_control_escape()
            mock_html.assert_called_once()
            args, kwargs = mock_html.call_args
            codigo = args[0]
            self.assertIn("bolimur-exit-confirm-modal", codigo)
            self.assertIn("Escape", codigo)
            self.assertIn("beforeunload", codigo)
            self.assertIn("Permanecer", codigo)
            self.assertEqual(kwargs.get("height"), 0)
            self.assertEqual(kwargs.get("width"), 0)

    def test_procesar_salida_url(self):
        """Verifica que procesar_salida_url detecte '?salir=1' y cierre sesión."""
        mock_auth = MagicMock()
        with patch.object(st, "query_params", {"salir": "1"}):
            control_salida.procesar_salida_url(mock_auth)
            mock_auth.cerrar_sesion.assert_called_once()

    def test_procesar_salida_url_sin_parametro(self):
        """Si no viene el parámetro salir, no debe cerrar sesión."""
        mock_auth = MagicMock()
        with patch.object(st, "query_params", {}):
            control_salida.procesar_salida_url(mock_auth)
            mock_auth.cerrar_sesion.assert_not_called()
