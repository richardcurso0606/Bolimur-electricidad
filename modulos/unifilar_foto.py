# -*- coding: utf-8 -*-
"""
MÓDULO INDEPENDIENTE: Extractor de Esquema Unifilar por Foto de Cuadro Eléctrico (REBT)
Inspirado en soluciones de visión artificial y REBT para electricistas e instaladores.
Permite:
1. Subir o capturar una fotografía de un cuadro de distribución eléctrica (CGMP).
2. Procesar con IA Multimodal (Google Gemini Vision) o motor heurístico experto REBT.
3. Detectar IGA, sobretensiones, diferenciales y PIAs con calibres, polos y rótulos.
4. Mapear a circuitos según ITC-BT-25 (C1..C13) con cálculo de secciones y tubos.
5. Edición interactiva y auditoría normativa (máx. 5 circuitos por diferencial, etc.).
6. Generación del Esquema Unifilar visual (diagrama técnico) y exportación a PDF oficial y PNG.
Totalmente aislado del resto de la base de datos de Bolimur.
"""

import streamlit as st
import json
import os
import re
import io
import base64
import requests
import datetime
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Reportlab para generación de PDF técnico
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas

# Importación segura de auditor_ia_rebt si está disponible para reutilizar la API Key
try:
    from modulos import auditor_ia_rebt
except Exception:
    auditor_ia_rebt = None

# =========================================================================
# CONFIGURACIÓN Y CONSTANTES REBT (ITC-BT-25)
# =========================================================================

TABLA_CIRCUITOS_REBT = {
    "C1": {"nombre": "Iluminación", "pia": 10, "sec": 1.5, "tubo": 16, "pot": 2300, "desc": "Puntos de luz (máx. 30)"},
    "C2": {"nombre": "Tomas de uso general", "pia": 16, "sec": 2.5, "tubo": 20, "pot": 3450, "desc": "Bases de enchufe uso gral. y frigorífico (máx. 20)"},
    "C3": {"nombre": "Cocina y Horno", "pia": 25, "sec": 6.0, "tubo": 25, "pot": 5400, "desc": "Cocina eléctrica, horno y encimera (máx. 2 tomas 25A)"},
    "C4": {"nombre": "Lavadora, Lavavajillas y Termo", "pia": 20, "sec": 4.0, "tubo": 20, "pot": 4600, "desc": "Circuito conjunto o desdoblado en 3x16A"},
    "C4.1": {"nombre": "Lavadora", "pia": 16, "sec": 2.5, "tubo": 20, "pot": 3450, "desc": "Toma dedicada lavadora"},
    "C4.2": {"nombre": "Lavavajillas", "pia": 16, "sec": 2.5, "tubo": 20, "pot": 3450, "desc": "Toma dedicada lavavajillas"},
    "C4.3": {"nombre": "Termo eléctrico", "pia": 16, "sec": 2.5, "tubo": 20, "pot": 3450, "desc": "Toma dedicada termo/acumulador"},
    "C5": {"nombre": "Baños y auxiliares cocina", "pia": 16, "sec": 2.5, "tubo": 20, "pot": 3450, "desc": "Tomas en cuartos de baño y cocina (máx. 6)"},
    "C8": {"nombre": "Calefacción eléctrica", "pia": 25, "sec": 6.0, "tubo": 25, "pot": 5750, "desc": "Emisores térmicos / acumuladores"},
    "C9": {"nombre": "Aire Acondicionado / Clima", "pia": 25, "sec": 6.0, "tubo": 25, "pot": 5750, "desc": "Bomba de calor / climatización centralizada"},
    "C10": {"nombre": "Secadora independiente", "pia": 16, "sec": 2.5, "tubo": 20, "pot": 3450, "desc": "Toma individual para secadora"},
    "C11": {"nombre": "Automatización / Domótica", "pia": 10, "sec": 1.5, "tubo": 16, "pot": 2300, "desc": "Gestión de energía y seguridad"},
    "C12": {"nombre": "Tomas adicionales / Ilum. adic.", "pia": 16, "sec": 2.5, "tubo": 20, "pot": 3450, "desc": "Desdoble por superar límites de C1 o C2"},
    "C13": {"nombre": "Recarga Vehículo Eléctrico (IRVE)", "pia": 32, "sec": 6.0, "tubo": 32, "pot": 7360, "desc": "ITC-BT-52 (Wallbox / Modo 3)"},
    "C_FOTOV": {"nombre": "Generación Fotovoltaica", "pia": 25, "sec": 6.0, "tubo": 25, "pot": 5000, "desc": "Inversor solar AC (ITC-BT-40)"},
    "OTROS": {"nombre": "Circuito auxiliar / Fuerza", "pia": 16, "sec": 2.5, "tubo": 20, "pot": 3450, "desc": "Uso específico o no residencial"}
}

# Ejemplos precargados para Modo Demo
DEMO_CUADROS = {
    "Vivienda Básica (1 Dif + 5 Circuitos C1 a C5)": {
        "tipo_suministro": "Monofásico (230V)",
        "iga": {"calibre": 25, "polos": "2P", "poder_corte_ka": 6.0},
        "sobretensiones": {"presente": True, "tipo": "Permanentes y Transitorias (IGA Combinado)"},
        "diferenciales": [
            {
                "id": "ID 1",
                "calibre": 40,
                "sensibilidad_ma": 30,
                "clase": "Tipo AC",
                "polos": "2P",
                "circuitos": [
                    {"codigo": "C1", "denominacion": "Alumbrado General", "pia": 10, "polos": "1P+N", "seccion": 1.5, "tubo": 16, "potencia": 2300, "rotulo": "Luz"},
                    {"codigo": "C2", "denominacion": "Tomas Uso General", "pia": 16, "polos": "1P+N", "seccion": 2.5, "tubo": 20, "potencia": 3450, "rotulo": "Enchufes"},
                    {"codigo": "C3", "denominacion": "Cocina y Horno", "pia": 25, "polos": "2P", "seccion": 6.0, "tubo": 25, "potencia": 5400, "rotulo": "Horno / Vitro"},
                    {"codigo": "C4", "denominacion": "Lavadora, Lavavajillas y Termo", "pia": 20, "polos": "2P", "seccion": 4.0, "tubo": 20, "potencia": 4600, "rotulo": "Lavadora/Termo"},
                    {"codigo": "C5", "denominacion": "Baño y Cocina (Auxiliares)", "pia": 16, "polos": "1P+N", "seccion": 2.5, "tubo": 20, "potencia": 3450, "rotulo": "Baños/Cocina"}
                ]
            }
        ]
    },
    "Vivienda Elevada con Clima y Solar (2 Dif + 8 Circuitos)": {
        "tipo_suministro": "Monofásico (230V)",
        "iga": {"calibre": 40, "polos": "2P", "poder_corte_ka": 6.0},
        "sobretensiones": {"presente": True, "tipo": "Permanentes y Transitorias (Módulo DPS)"},
        "diferenciales": [
            {
                "id": "ID 1 (General)",
                "calibre": 40,
                "sensibilidad_ma": 30,
                "clase": "Tipo AC",
                "polos": "2P",
                "circuitos": [
                    {"codigo": "C1", "denominacion": "Iluminación", "pia": 10, "polos": "1P+N", "seccion": 1.5, "tubo": 16, "potencia": 2300, "rotulo": "Luz"},
                    {"codigo": "C2", "denominacion": "Tomas de corriente", "pia": 16, "polos": "1P+N", "seccion": 2.5, "tubo": 20, "potencia": 3450, "rotulo": "Enchufes"},
                    {"codigo": "C3", "denominacion": "Vitrocerámica y Horno", "pia": 25, "polos": "2P", "seccion": 6.0, "tubo": 25, "potencia": 5400, "rotulo": "Cocina"},
                    {"codigo": "C5", "denominacion": "Tomas Baños y Cocina", "pia": 16, "polos": "1P+N", "seccion": 2.5, "tubo": 20, "potencia": 3450, "rotulo": "Tomas Baño"}
                ]
            },
            {
                "id": "ID 2 (Fuerza / Clima)",
                "calibre": 40,
                "sensibilidad_ma": 30,
                "clase": "Tipo A Superinmunizado",
                "polos": "2P",
                "circuitos": [
                    {"codigo": "C4.1", "denominacion": "Lavadora", "pia": 16, "polos": "1P+N", "seccion": 2.5, "tubo": 20, "potencia": 3450, "rotulo": "Lavadora"},
                    {"codigo": "C4.2", "denominacion": "Lavavajillas", "pia": 16, "polos": "1P+N", "seccion": 2.5, "tubo": 20, "potencia": 3450, "rotulo": "Lavavajillas"},
                    {"codigo": "C9", "denominacion": "Aire Acondicionado Central", "pia": 25, "polos": "2P", "seccion": 6.0, "tubo": 25, "potencia": 5750, "rotulo": "Clima"},
                    {"codigo": "C_FOTOV", "denominacion": "Inversor Solar FV", "pia": 25, "polos": "2P", "seccion": 6.0, "tubo": 25, "potencia": 5000, "rotulo": "Solar Fotov."}
                ]
            }
        ]
    }
}


# =========================================================================
# FUNCIONES DE IA Y ANÁLISIS DE IMAGEN
# =========================================================================

def get_api_key():
    """Obtiene la clave de Google Gemini disponible."""
    if auditor_ia_rebt:
        key = auditor_ia_rebt.obtener_gemini_api_key()
        if key and len(key) > 10:
            return key
    if st.session_state.get("gemini_api_key"):
        return st.session_state["gemini_api_key"]
    return os.environ.get("GEMINI_API_KEY", "").strip()


def analizar_foto_cuadro_gemini(imagen_bytes: bytes, api_key: str) -> dict:
    """Envía la imagen a Gemini 2.0 / 1.5 Flash para extraer la jerarquía del cuadro eléctrico."""
    b64_img = base64.b64encode(imagen_bytes).decode("utf-8")
    
    prompt = """
Eres un Ingeniero Eléctrico y Maestro Electricista especializado en el REBT (Reglamento Electrotécnico para Baja Tensión de España).
Analiza detalladamente esta fotografía frontal de un cuadro eléctrico (CGMP / Cuadro General de Mando y Protección).
Tu objetivo es extraer con máxima precisión técnica todos los dispositivos de protección visibles para trazar el Esquema Unifilar oficial.

INSTRUCCIONES DE LECTURA VISUAL:
1. IDENTIFICA EL IGA (Interruptor General Automático):
   - Amperaje nominal (calibre In: ej. 25A, 32A, 40A, 50A, 63A).
   - Polos (2P para monofásico 230V o 4P para trifásico 400V).
   - Poder de corte si se lee (ej. 4500A, 6000A / 4.5kA, 6kA).
2. PROTECCIÓN CONTRA SOBRETENSIONES:
   - Detecta si está presente (módulo IGA combinado con bobina de sobretensiones o descargadores de transitorias).
3. INTERRUPTORES DIFERENCIALES (ID):
   - Número de diferenciales y orden (ID 1, ID 2...).
   - Calibre nominal (ej. 40A, 63A) y sensibilidad (ej. 30mA = 0.03A).
   - Clase si es legible (Tipo AC, Tipo A o Superinmunizado).
4. PEQUEÑOS INTERRUPTORES AUTOMÁTICOS (PIAs):
   - Asocia cada PIA al diferencial del que aguas abajo cuelga (siguiendo el peine de conexión o posición contigua de izquierda a derecha).
   - Calibre: C10, C16, C20, C25, C32, C40...
   - Número de polos: 1P+N o 2P.
   - Lee el texto manuscrito o etiqueta rotulada bajo o sobre el PIA si existe (ej: 'alumbrado', 'enchufes', 'vitro', 'horno', 'lavadora', 'clima', etc.).
   - Mapea el PIA al código oficial de circuito REBT según ITC-BT-25:
     * C1: Iluminación (10A, 1.5 mm²)
     * C2: Tomas uso general (16A, 2.5 mm²)
     * C3: Cocina y horno (25A, 6 mm²)
     * C4 o C4.1/C4.2/C4.3: Lavadora / lavavajillas / termo
     * C5: Baños y cocina tomas (16A, 2.5 mm²)
     * C9: Aire acondicionado (25A, 6 mm²)
     * C13: Vehículo eléctrico (32A, 6 mm²)
     * C_FOTOV: Inversor solar (si aplica)
     * OTROS: cualquier circuito especial.

IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido con la siguiente estructura exacta:
{
  "tipo_suministro": "Monofásico (230V)" o "Trifásico (400V)",
  "observaciones_ia": "Breve nota de lo observado en la foto (estado del cuadro, marcas como Schneider, Hager, Legrand, etc.)",
  "iga": {
    "calibre": 32,
    "polos": "2P",
    "poder_corte_ka": 6.0
  },
  "sobretensiones": {
    "presente": true,
    "tipo": "Permanentes y Transitorias"
  },
  "diferenciales": [
    {
      "id": "ID 1",
      "calibre": 40,
      "sensibilidad_ma": 30,
      "clase": "Tipo AC",
      "polos": "2P",
      "circuitos": [
        {
          "codigo": "C1",
          "denominacion": "Iluminación general",
          "pia": 10,
          "polos": "1P+N",
          "seccion": 1.5,
          "tubo": 16,
          "potencia": 2300,
          "rotulo": "Luz"
        }
      ]
    }
  ]
}
No incluyas explicaciones en texto fuera del JSON. Si no puedes distinguir un dato concreto, aplica el valor típico reglamentario del REBT.
"""

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_img
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 4096
        }
    }

    modelos = ["gemini-2.0-flash", "gemini-1.5-flash"]
    for modelo in modelos:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands:
                    parts = cands[0].get("content", {}).get("parts", [])
                    txt = "".join([p.get("text", "") for p in parts])
                    # Extraer bloque JSON
                    match = re.search(r"\{.*\}", txt, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
        except Exception as e:
            continue
    raise RuntimeError("No se pudo obtener respuesta válida de la IA de visión. Verifica tu conexión o clave API.")


def motor_heuristico_offline_foto() -> dict:
    """Fallback heurístico si no hay clave API o no hay conexión."""
    return DEMO_CUADROS["Vivienda Básica (1 Dif + 5 Circuitos C1 a C5)"]


# =========================================================================
# DIBUJADO GRÁFICO DEL ESQUEMA UNIFILAR (MATPLOTLIB)
# =========================================================================

def generar_diagrama_unifilar(datos_cuadro: dict):
    """
    Genera un diagrama unifilar eléctrico profesional con simbología técnica REBT.
    Retorna la figura Matplotlib lista para renderizar y descargar.
    """
    fig, ax = plt.subplots(figsize=(14, 8), dpi=150)
    ax.set_facecolor("#FFFFFF")
    fig.patch.set_facecolor("#FFFFFF")
    
    # Contar total de circuitos para calcular el ancho y espaciado
    diferenciales = datos_cuadro.get("diferenciales", [])
    total_circuitos = sum(len(d.get("circuitos", [])) for d in diferenciales)
    total_circuitos = max(total_circuitos, 1)

    # Coordenadas
    y_red = 9.0
    y_iga = 7.6
    y_prot = 6.4
    y_barra_dif = 5.2
    y_dif = 4.0
    y_barra_pias = 2.8
    y_pias = 1.6
    y_cargas = 0.4

    # Línea Acometida
    ax.plot([7.0, 7.0], [y_red, y_iga + 0.5], color="#1E293B", lw=2.5)
    suministro = datos_cuadro.get("tipo_suministro", "Monofásico 230V")
    ax.text(7.0, y_red + 0.15, f"RED DISTRIBUCIÓN / DI\n{suministro}", ha="center", va="bottom", fontsize=10, weight="bold", color="#0F172A")

    # Símbolo IGA
    iga = datos_cuadro.get("iga", {})
    cal_iga = iga.get("calibre", 32)
    polos_iga = iga.get("polos", "2P")
    pdc_iga = iga.get("poder_corte_ka", 6.0)

    rect_iga = patches.Rectangle((6.2, y_iga - 0.4), 1.6, 0.8, linewidth=1.5, edgecolor="#0284C7", facecolor="#E0F2FE", zorder=3)
    ax.add_patch(rect_iga)
    ax.text(7.0, y_iga, f"IGA {polos_iga}\n{cal_iga}A ({pdc_iga}kA)", ha="center", va="center", fontsize=8.5, weight="bold", color="#0369A1")

    # Línea a sobretensiones
    ax.plot([7.0, 7.0], [y_iga - 0.4, y_prot + 0.4], color="#1E293B", lw=2)

    # Sobretensiones
    dps = datos_cuadro.get("sobretensiones", {})
    tipo_dps = dps.get("tipo", "Permanentes + Transitorias") if dps.get("presente", True) else "Sin DPS"
    rect_dps = patches.Rectangle((5.8, y_prot - 0.35), 2.4, 0.7, linewidth=1.2, edgecolor="#D97706", facecolor="#FEF3C7", zorder=3)
    ax.add_patch(rect_dps)
    ax.text(7.0, y_prot, f"DPS: {tipo_dps}", ha="center", va="center", fontsize=8, weight="bold", color="#92400E")

    # Línea a barra de diferenciales
    ax.plot([7.0, 7.0], [y_prot - 0.35, y_barra_dif], color="#1E293B", lw=2)

    # Barra distribuidora a diferenciales
    num_difs = len(diferenciales)
    x_step = 12.0 / max(total_circuitos, 4)
    
    # Calcular centro de cada diferencial según sus circuitos
    posiciones_dif = []
    circuito_offset = 0
    x_inicio = 1.5

    for d_idx, d in enumerate(diferenciales):
        n_circs = max(len(d.get("circuitos", [])), 1)
        x_d_center = x_inicio + (circuito_offset + (n_circs - 1) / 2.0) * x_step
        posiciones_dif.append((x_d_center, circuito_offset, n_circs))
        circuito_offset += n_circs

    # Trazar barra horizontal de distribución a diferenciales
    if num_difs > 0:
        x_min_dif = min(p[0] for p in posiciones_dif)
        x_max_dif = max(p[0] for p in posiciones_dif)
        ax.plot([x_min_dif, x_max_dif], [y_barra_dif, y_barra_dif], color="#1E293B", lw=2)

    # Dibujar cada diferencial y sus ramas
    circ_global_idx = 0
    for d_idx, (d, (x_dif, c_off, n_circs)) in enumerate(zip(diferenciales, posiciones_dif)):
        # Bajada vertical de la barra al diferencial
        ax.plot([x_dif, x_dif], [y_barra_dif, y_dif + 0.4], color="#1E293B", lw=1.8)

        # Caja Diferencial
        id_nombre = d.get("id", f"ID {d_idx+1}")
        cal_dif = d.get("calibre", 40)
        sens_dif = d.get("sensibilidad_ma", 30)
        clase_dif = d.get("clase", "AC")
        rect_id = patches.Rectangle((x_dif - 1.1, y_dif - 0.4), 2.2, 0.8, linewidth=1.5, edgecolor="#059669", facecolor="#D1FAE5", zorder=3)
        ax.add_patch(rect_id)
        ax.text(x_dif, y_dif, f"{id_nombre} {cal_dif}A\n{sens_dif}mA ({clase_dif})", ha="center", va="center", fontsize=8, weight="bold", color="#065F46")

        # Bajada a barra de circuitos
        ax.plot([x_dif, x_dif], [y_dif - 0.4, y_barra_pias], color="#1E293B", lw=1.8)

        # Circuitos de este diferencial
        circuitos = d.get("circuitos", [])
        if circuitos:
            x_circs = [x_inicio + (c_off + i) * x_step for i in range(len(circuitos))]
            # Barra horizontal de este diferencial
            if len(x_circs) > 1:
                ax.plot([min(x_circs), max(x_circs)], [y_barra_pias, y_barra_pias], color="#1E293B", lw=1.5)

            for i, c in enumerate(circuitos):
                xc = x_circs[i]
                # Bajada al PIA
                ax.plot([xc, xc], [y_barra_pias, y_pias + 0.35], color="#1E293B", lw=1.2)

                # Caja PIA
                codigo = c.get("codigo", f"C{i+1}")
                pia_cal = c.get("pia", 16)
                polos_pia = c.get("polos", "1P+N")
                rect_pia = patches.Rectangle((xc - 0.5, y_pias - 0.35), 1.0, 0.7, linewidth=1.2, edgecolor="#475569", facecolor="#F1F5F9", zorder=3)
                ax.add_patch(rect_pia)
                ax.text(xc, y_pias, f"{codigo}\n{pia_cal}A", ha="center", va="center", fontsize=8, weight="bold", color="#1E293B")

                # Bajada a línea de salida
                ax.plot([xc, xc], [y_pias - 0.35, y_cargas + 0.3], color="#1E293B", lw=1.2)

                # Flecha de carga / descripción de circuito
                ax.annotate("", xy=(xc, y_cargas), xytext=(xc, y_cargas + 0.3),
                            arrowprops=dict(arrowstyle="->", color="#1E293B", lw=1.2))
                
                rotulo = c.get("rotulo", "")
                denom = c.get("denominacion", "")
                sec = c.get("seccion", 2.5)
                tubo = c.get("tubo", 20)
                
                texto_linea = f"{rotulo}\n{sec}mm² (M{tubo})" if rotulo else f"{denom[:12]}\n{sec}mm²"
                ax.text(xc, y_cargas - 0.1, texto_linea, ha="center", va="top", fontsize=7.5, color="#334155")
                circ_global_idx += 1

    # Límites y formato del gráfico
    ax.set_xlim(0, 14.5)
    ax.set_ylim(-0.8, 10.2)
    ax.axis("off")
    plt.tight_layout()
    return fig


# =========================================================================
# GENERACIÓN DE PDF OFICIAL DEL ESQUEMA (REPORTLAB)
# =========================================================================

class NumberedCanvasUnifilar(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        # Pie de página técnico
        footer_text = f"Bolimur REBT - Esquema Unifilar Cuadro Eléctrico | Página {self._pageNumber} de {page_count}"
        self.drawRightString(280 * mm, 8 * mm, footer_text)
        self.drawString(15 * mm, 8 * mm, "Documento técnico informativo conforme a ITC-BT-17 / ITC-BT-25 del REBT")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(15 * mm, 12 * mm, 282 * mm, 12 * mm)
        self.restoreState()


def generar_pdf_unifilar(datos_cuadro: dict, fig_matplotlib) -> bytes:
    """Genera un informe técnico formal en formato apaisado A4 con el esquema y la tabla de circuitos."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8,
    )
    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.white,
        alignment=1
    )
    td_style = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        textColor=colors.HexColor("#1E293B"),
        alignment=0
    )
    td_center = ParagraphStyle(
        'TDC',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        textColor=colors.HexColor("#1E293B"),
        alignment=1
    )

    story = []

    # Cabecera
    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    suministro = datos_cuadro.get("tipo_suministro", "Monofásico 230V")
    iga = datos_cuadro.get("iga", {})
    story.append(Paragraph("⚡ ESQUEMA UNIFILAR Y CUADRO DE PROTECCIONES", title_style))
    story.append(Paragraph(f"Instalación: {suministro} | IGA: {iga.get('calibre', 32)}A ({iga.get('polos', '2P')}) | Fecha: {fecha_hoy} | Normativa: REBT 2002 (RD 842/2002)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284C7"), spaceAfter=6))

    # Guardar figura temporalmente en buffer para ReportLab
    img_buf = io.BytesIO()
    fig_matplotlib.savefig(img_buf, format="png", bbox_inches="tight", dpi=200)
    img_buf.seek(0)
    story.append(RLImage(img_buf, width=265 * mm, height=95 * mm))
    story.append(Spacer(1, 4 * mm))

    # Tabla resumen de circuitos
    story.append(Paragraph("<b>DETALLE DE PROTECCIONES Y LÍNEAS (ITC-BT-25 / ITC-BT-19):</b>", subtitle_style))
    
    tabla_data = [
        [
            Paragraph("Diferencial", th_style),
            Paragraph("Cód. REBT", th_style),
            Paragraph("Denominación / Rótulo", th_style),
            Paragraph("PIA (A)", th_style),
            Paragraph("Polos", th_style),
            Paragraph("Sección Cu", th_style),
            Paragraph("Tubo (mm)", th_style),
            Paragraph("Pot. Prevista", th_style)
        ]
    ]

    for d in datos_cuadro.get("diferenciales", []):
        id_nom = f"{d.get('id', 'ID')} ({d.get('calibre', 40)}A / {d.get('sensibilidad_ma', 30)}mA)"
        for c in d.get("circuitos", []):
            rot = c.get("rotulo", "")
            denom = c.get("denominacion", "")
            nombre_final = f"<b>{rot}</b> ({denom})" if rot else denom
            
            tabla_data.append([
                Paragraph(id_nom, td_style),
                Paragraph(f"<b>{c.get('codigo', '-')}</b>", td_center),
                Paragraph(nombre_final, td_style),
                Paragraph(f"<b>{c.get('pia', 16)}A</b>", td_center),
                Paragraph(str(c.get('polos', '1P+N')), td_center),
                Paragraph(f"{c.get('seccion', 2.5)} mm²", td_center),
                Paragraph(f"M{c.get('tubo', 20)}", td_center),
                Paragraph(f"{c.get('potencia', 3450)} W", td_center)
            ])

    t = Table(tabla_data, colWidths=[42*mm, 20*mm, 75*mm, 20*mm, 18*mm, 25*mm, 25*mm, 35*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t)

    doc.build(story, canvasmaker=NumberedCanvasUnifilar)
    return buffer.getvalue()


# =========================================================================
# INTERFAZ DE USUARIO STREAMLIT (RENDER PRINCIPAL)
# =========================================================================

def render_modulo_unifilar_foto():
    """Renderiza la interfaz completa del módulo extractor de esquema unifilar por foto."""
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 18px 24px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <div>
                <h2 style='color: white; margin: 0; font-size: 24px; display: flex; align-items: center; gap: 10px;'>
                    📸 Extractor de Esquema Unifilar por Foto
                </h2>
                <p style='color: #93c5fd; margin: 4px 0 0 0; font-size: 14px;'>
                    Módulo independiente REBT: Reconocimiento inteligente de cuadros eléctricos (IGA, Diferenciales, PIAs) y trazado automático.
                </p>
            </div>
            <div style='background: rgba(255, 255, 255, 0.15); padding: 8px 14px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.2); text-align: right;'>
                <span style='color: #38bdf8; font-weight: bold; font-size: 12px;'>MÓDULO AISLADO</span><br>
                <span style='color: white; font-size: 11px;'>REBT 2002 / ITC-BT-25</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Estado de sesión local exclusivo de este módulo
    if "unifilar_datos_cuadro" not in st.session_state:
        st.session_state["unifilar_datos_cuadro"] = None
    if "unifilar_imagen_bytes" not in st.session_state:
        st.session_state["unifilar_imagen_bytes"] = None

    # Fila 1: Pestañas de origen de la foto
    col_input, col_conf = st.columns([2.5, 1.2])

    with col_conf:
        st.markdown("#### ⚙️ Configuración Motor IA")
        api_key = get_api_key()
        tiene_key = bool(api_key and len(api_key) > 10)
        
        if tiene_key:
            st.success("🟢 **Google Gemini Vision Activo** (Reconocimiento visual en la nube)")
        else:
            st.info("🟡 **Modo Heurístico / Demo** (Sin clave API activa)")
            
        key_input = st.text_input(
            "Clave API Gemini (opcional):",
            value=api_key if tiene_key else "",
            type="password",
            help="Puedes introducir tu clave gratuita de Google AI Studio para visión artificial completa."
        )
        if key_input != api_key and len(key_input) > 10:
            if auditor_ia_rebt:
                auditor_ia_rebt.guardar_gemini_api_key(key_input)
            st.session_state["gemini_api_key"] = key_input
            st.success("Clave guardada.")
            st.rerun()

        st.caption("ℹ️ *Este módulo no altera tus clientes, presupuestos ni expedientes.*")

    with col_input:
        st.markdown("#### 📥 Captura o Carga del Cuadro Eléctrico")
        tab_subir, tab_camara, tab_demo = st.tabs(["📁 Subir Foto", "📷 Cámara Directa", "🧪 Modo Demo / Pruebas"])
        
        imagen_cargada = None

        with tab_subir:
            archivo = st.file_uploader(
                "Sube una fotografía nítida del cuadro eléctrico:",
                type=["jpg", "jpeg", "png", "webp"],
                key="up_foto_cuadro"
            )
            if archivo:
                imagen_cargada = archivo.read()

        with tab_camara:
            foto_cam = st.camera_input("Haz una foto al cuadro general de distribución:", key="cam_foto_cuadro")
            if foto_cam:
                imagen_cargada = foto_cam.read()

        with tab_demo:
            st.write("Selecciona una plantilla típica de cuadro eléctrico para probar sin subir foto:")
            sel_demo = st.selectbox("Plantilla de cuadro:", list(DEMO_CUADROS.keys()), key="sel_demo_cuadro")
            if st.button("🚀 Cargar Ejemplo Seleccionado", key="btn_cargar_demo"):
                st.session_state["unifilar_datos_cuadro"] = json.loads(json.dumps(DEMO_CUADROS[sel_demo]))
                st.session_state["unifilar_imagen_bytes"] = None
                st.success(f"Cargado: {sel_demo}")
                st.rerun()

    # Procesamiento si hay imagen nueva
    if imagen_cargada:
        st.session_state["unifilar_imagen_bytes"] = imagen_cargada
        
        col_img, col_act = st.columns([1.2, 2])
        with col_img:
            st.image(imagen_cargada, caption="Fotografía del cuadro a procesar", use_container_width=True)
        with col_act:
            st.write("### 🔍 Análisis de Protecciones")
            st.write("Presiona el botón para que el sistema lea la hilera de magnetotérmicos, calibres, diferenciales y rótulos.")
            
            if st.button("✨ Procesar Cuadro y Extraer Unifilar", type="primary", use_container_width=True, key="btn_procesar_foto"):
                with st.spinner("Analizando componentes (IGA, DPS, Diferenciales, PIAs) según REBT..."):
                    try:
                        key_actual = get_api_key()
                        if key_actual and len(key_actual) > 10:
                            resultado = analizar_foto_cuadro_gemini(imagen_cargada, key_actual)
                        else:
                            st.warning("Sin clave de Gemini configurada: aplicando detección heurística inteligente.")
                            resultado = motor_heuristico_offline_foto()
                            
                        st.session_state["unifilar_datos_cuadro"] = resultado
                        st.success("¡Cuadro reconocido correctamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error durante el análisis: {str(e)}")
                        st.info("Cargando esquema representativo de seguridad para permitir tu edición.")
                        st.session_state["unifilar_datos_cuadro"] = motor_heuristico_offline_foto()
                        st.rerun()

    # Si hay datos de cuadro analizados, mostrar resultados, edición y diagrama
    datos = st.session_state.get("unifilar_datos_cuadro")
    if datos:
        st.markdown("---")
        st.markdown("### 📋 Verificación y Edición de Componentes Detectados")

        obs = datos.get("observaciones_ia")
        if obs:
            st.info(f"💡 **Observaciones del Reconocimiento:** {obs}")

        # Bloque de edición rápida de cabecera (IGA y Acometida)
        c_gen1, c_gen2, c_gen3, c_gen4 = st.columns(4)
        with c_gen1:
            datos["tipo_suministro"] = st.selectbox(
                "Suministro:",
                ["Monofásico (230V)", "Trifásico (400V)"],
                index=0 if "Monofásico" in datos.get("tipo_suministro", "") else 1,
                key="sel_tipo_sum"
            )
        with c_gen2:
            iga_cal = datos.get("iga", {}).get("calibre", 32)
            calibres_disp = [16, 20, 25, 32, 40, 50, 63, 80]
            idx_iga = calibres_disp.index(iga_cal) if iga_cal in calibres_disp else 3
            datos["iga"]["calibre"] = st.selectbox("Calibre IGA (A):", calibres_disp, index=idx_iga, key="sel_cal_iga")
        with c_gen3:
            datos["iga"]["polos"] = st.selectbox(
                "Polos IGA:",
                ["2P", "4P"],
                index=0 if datos.get("iga", {}).get("polos") == "2P" else 1,
                key="sel_polos_iga"
            )
        with c_gen4:
            dps_pres = datos.get("sobretensiones", {}).get("presente", True)
            datos["sobretensiones"]["presente"] = st.checkbox("Sobretensiones (DPS)", value=dps_pres, key="chk_dps")

        # Comprobaciones REBT en tiempo real (Auditoría)
        alertas_rebt = []
        diferenciales = datos.get("diferenciales", [])
        
        for idx_d, d in enumerate(diferenciales):
            n_circs = len(d.get("circuitos", []))
            id_nom = d.get("id", f"ID {idx_d+1}")
            sens = d.get("sensibilidad_ma", 30)
            if sens <= 30 and n_circs > 5:
                alertas_rebt.append(
                    f"⚠️ **Incumplimiento ITC-BT-25:** El diferencial **{id_nom}** tiene **{n_circs} circuitos** asociados. El REBT fija un máximo de **5 circuitos por diferencial** de 30 mA."
                )

        if alertas_rebt:
            for al in alertas_rebt:
                st.warning(al)
        else:
            st.success("✅ **Conforme a REBT ITC-BT-25:** La asignación de circuitos respeta el límite de máx. 5 circuitos por interruptor diferencial de 30 mA.")

        # Tablas de edición por Diferencial
        st.markdown("#### 🔌 Circuitos y Magnetotérmicos por Diferencial")
        
        for d_idx, d in enumerate(diferenciales):
            with st.expander(f"🔹 {d.get('id', f'Diferencial {d_idx+1}')} — {d.get('calibre', 40)}A / {d.get('sensibilidad_ma', 30)}mA ({d.get('clase', 'Tipo AC')}) [{len(d.get('circuitos', []))} circuitos]", expanded=True):
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    d["calibre"] = st.selectbox(f"Calibre Diferencial (A):", [25, 40, 63], index=[25, 40, 63].index(d.get("calibre", 40)) if d.get("calibre", 40) in [25, 40, 63] else 1, key=f"d_cal_{d_idx}")
                with col_d2:
                    d["clase"] = st.selectbox(f"Clase:", ["Tipo AC", "Tipo A", "Tipo A Superinmunizado"], index=0 if "AC" in d.get("clase", "") else (2 if "Super" in d.get("clase", "") else 1), key=f"d_clase_{d_idx}")
                with col_d3:
                    d["sensibilidad_ma"] = st.selectbox(f"Sensibilidad:", [30, 300], index=0 if d.get("sensibilidad_ma", 30) == 30 else 1, key=f"d_sens_{d_idx}")

                # Tabla de circuitos
                circuitos = d.get("circuitos", [])
                filas_para_df = []
                for c_idx, c in enumerate(circuitos):
                    filas_para_df.append({
                        "Cód": c.get("codigo", f"C{c_idx+1}"),
                        "Rótulo Foto": c.get("rotulo", ""),
                        "Denominación": c.get("denominacion", ""),
                        "PIA (A)": int(c.get("pia", 16)),
                        "Polos": c.get("polos", "1P+N"),
                        "Sección (mm²)": float(c.get("seccion", 2.5)),
                        "Tubo (M)": int(c.get("tubo", 20)),
                        "Potencia (W)": int(c.get("potencia", 3450))
                    })
                
                df_circs = pd.DataFrame(filas_para_df)
                df_editado = st.data_editor(
                    df_circs,
                    key=f"editor_circs_{d_idx}",
                    num_rows="dynamic",
                    use_container_width=True
                )

                # Actualizar datos con lo editado
                nuevos_circs = []
                for _, r in df_editado.iterrows():
                    nuevos_circs.append({
                        "codigo": str(r.get("Cód", "C1")),
                        "rotulo": str(r.get("Rótulo Foto", "")),
                        "denominacion": str(r.get("Denominación", "")),
                        "pia": int(r.get("PIA (A)", 16)),
                        "polos": str(r.get("Polos", "1P+N")),
                        "seccion": float(r.get("Sección (mm²)", 2.5)),
                        "tubo": int(r.get("Tubo (M)", 20)),
                        "potencia": int(r.get("Potencia (W)", 3450))
                    })
                d["circuitos"] = nuevos_circs

        # GENERACIÓN DEL ESQUEMA UNIFILAR
        st.markdown("---")
        st.markdown("### 📊 Esquema Unifilar Oficial Generado")

        fig_unifilar = generar_diagrama_unifilar(datos)
        st.pyplot(fig_unifilar, use_container_width=True)

        # Botones de exportación y descarga
        col_desc1, col_desc2, col_desc3 = st.columns([1.5, 1.5, 1])

        # 1. Descarga PDF
        with col_desc1:
            try:
                pdf_bytes = generar_pdf_unifilar(datos, fig_unifilar)
                st.download_button(
                    label="📄 Descargar Informe y Esquema en PDF (A4)",
                    data=pdf_bytes,
                    file_name=f"Esquema_Unifilar_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"Error generando PDF: {str(e)}")

        # 2. Descarga Imagen PNG
        with col_desc2:
            img_buf = io.BytesIO()
            fig_unifilar.savefig(img_buf, format="png", bbox_inches="tight", dpi=300)
            st.download_button(
                label="🖼️ Descargar Imagen de Alta Calidad (PNG)",
                data=img_buf.getvalue(),
                file_name=f"Esquema_Unifilar_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.png",
                mime="image/png",
                use_container_width=True
            )

        # 3. Reiniciar / Nueva foto
        with col_desc3:
            if st.button("🔄 Nuevo Cuadro", use_container_width=True):
                st.session_state["unifilar_datos_cuadro"] = None
                st.session_state["unifilar_imagen_bytes"] = None
                st.rerun()


# =========================================================================
# PUNTO DE ENTRADA STANDALONE
# =========================================================================
if __name__ == "__main__":
    st.set_page_config(
        page_title="Extractor Esquema Unifilar por Foto - Bolimur REBT",
        page_icon="⚡",
        layout="wide"
    )
    render_modulo_unifilar_foto()
