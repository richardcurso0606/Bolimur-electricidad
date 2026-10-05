# -*- coding: utf-8 -*-
"""
Punto de entrada compatible para Streamlit Cloud y despliegues automáticos.
Permite que la aplicación arranque tanto si Streamlit Cloud busca 'main.py', 'app.py' como 'inicio.py'.
"""
import runpy
import os
import sys

_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

_inicio_path = os.path.join(_dir, "inicio.py")
runpy.run_path(_inicio_path, run_name="__main__")
