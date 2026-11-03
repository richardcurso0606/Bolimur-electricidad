"""
Módulo de Generación de Planos Eléctricos en formato AutoCAD (.DXF) y Render Técnico.
Cumple con la normativa REBT (ITC-BT-17, ITC-BT-18, ITC-BT-25) y UNE-EN 60617.
Genera archivos DXF nativos (compatibles con AutoCAD, DraftSight, LibreCAD, NanoCAD, ZWCAD)
y genera la vista previa idéntica al espacio de trabajo (Model Space Dark) de AutoCAD.
"""

import io
import os
import datetime
from typing import Dict, Any, Optional

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    EZDXF_AVAILABLE = True
except ImportError:
    EZDXF_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.lines import Line2D
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def obtener_datos_ejemplo_unifilar() -> Dict[str, Any]:
    """Retorna una estructura completa de datos técnicos para un cuadro REBT normalizado."""
    return {
        "instalacion": {
            "cliente": "PROYECTO VIVIENDA / LOCAL TÉCNICO",
            "ubicacion": "Av. Juan Carlos I, s/n, Murcia",
            "empresa": "BOLIMUR INSTALACIONES S.L.",
            "cif": "B-73000000",
            "instalador": "Instalador Autorizado Categoría Especialista",
            "plano": "ELE-01",
            "escala": "1:50 / Model 1:1",
            "normativa": "REBT (RD 842/2002) - UNE-EN 60617"
        },
        "tipo_suministro": "Monofásico 1N~ 230V - 50 Hz",
        "potencia_prevista_w": 9200,
        "iga": {
            "calibre": 40,
            "polos": "2P",
            "poder_corte_ka": 6.0,
            "curva": "C"
        },
        "sobretensiones": {
            "tipo": "POP + DPS Tipo 2",
            "permanente": True,
            "transitoria": True,
            "imax_ka": 20
        },
        "diferenciales": [
            {
                "id": "ID-1",
                "denominacion": "Diferencial General (Uso Básico)",
                "calibre": 40,
                "polos": "2P",
                "sensibilidad_ma": 30,
                "clase": "A Inmunizado",
                "circuitos": [
                    {"codigo": "C1", "denominacion": "Iluminación General", "pia": 10, "polos": "1P+N", "seccion": 1.5, "tubo": 16, "potencia_w": 2300},
                    {"codigo": "C2", "denominacion": "Tomas Uso General", "pia": 16, "polos": "1P+N", "seccion": 2.5, "tubo": 20, "potencia_w": 3680},
                    {"codigo": "C3", "denominacion": "Cocina y Horno", "pia": 25, "polos": "1P+N", "seccion": 6.0, "tubo": 25, "potencia_w": 5750},
                    {"codigo": "C4", "denominacion": "Lavadora, Lavavajillas, Termo", "pia": 20, "polos": "1P+N", "seccion": 4.0, "tubo": 20, "potencia_w": 4600},
                    {"codigo": "C5", "denominacion": "Tomas Baño y Aux. Cocina", "pia": 16, "polos": "1P+N", "seccion": 2.5, "tubo": 20, "potencia_w": 3680}
                ]
            },
            {
                "id": "ID-2",
                "denominacion": "Diferencial Climatización y VE",
                "calibre": 40,
                "polos": "2P",
                "sensibilidad_ma": 30,
                "clase": "A Superinmunizado",
                "circuitos": [
                    {"codigo": "C9", "denominacion": "Aire Acondicionado / Clima", "pia": 25, "polos": "1P+N", "seccion": 6.0, "tubo": 25, "potencia_w": 5750},
                    {"codigo": "C13", "denominacion": "Recarga Vehículo Eléctrico (ITC-BT-52)", "pia": 32, "polos": "1P+N", "seccion": 10.0, "tubo": 32, "potencia_w": 7360}
                ]
            }
        ],
        "puesta_a_tierra": {
            "seccion_enlace_mm2": 16,
            "resistencia_rt_ohm": 11.8,
            "picas": "2x 2 metros acero cobreado"
        }
    }


def configurar_capas_autocad(doc):
    """Crea y estandariza las capas de AutoCAD con colores ACI normativos."""
    capas = [
        # (Nombre, Color ACI, Tipo línea, Grosor mm)
        ("0_MARCO_PAPEL", 7, "CONTINUOUS", 0.50),           # Blanco / Negro
        ("ELE_LINEAS_DISTRIBUCION", 4, "CONTINUOUS", 0.35), # Cyan (Distribución / Fases)
        ("ELE_SIMBOLOS_APARAMENTA", 2, "CONTINUOUS", 0.35), # Amarillo (Aparamenta UNE-EN 60617)
        ("ELE_TIERRA_PE", 3, "CONTINUOUS", 0.30),           # Verde (Puesta a tierra)
        ("ELE_TEXTOS_PARAMETROS", 7, "CONTINUOUS", 0.20),   # Blanco (Textos calibres / secciones)
        ("ELE_TEXTOS_TITULOS", 2, "CONTINUOUS", 0.30),      # Amarillo (Cabeceras y títulos)
        ("ELE_CAJETIN_ROTULO", 7, "CONTINUOUS", 0.35),      # Blanco / Contornos cajetín
        ("ELE_COTAS_REFERENCIAS", 1, "CONTINUOUS", 0.18),   # Rojo (Cotas y referencias)
    ]
    for nombre, color, ltype, grosor in capas:
        if nombre not in doc.layers:
            layer = doc.layers.add(nombre, color=color, linetype=ltype)
            layer.lineweight = int(grosor * 100)


def dibujar_cajetin_autocad(msp, x0, y0, w, h, info_instalacion: dict):
    """Dibuja el Cajetín oficial normalizado UNE 1035 / ISO 7200 en AutoCAD."""
    layer_frame = "ELE_CAJETIN_ROTULO"
    layer_txt = "ELE_TEXTOS_PARAMETROS"
    layer_title = "ELE_TEXTOS_TITULOS"

    # Marco exterior del cajetín
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h), (x0, y0)],
        dxfattribs={"layer": layer_frame}
    )

    # Divisiones horizontales
    y_div1 = y0 + h * 0.45
    y_div2 = y0 + h * 0.75
    msp.add_line((x0, y_div1), (x0 + w, y_div1), dxfattribs={"layer": layer_frame})
    msp.add_line((x0, y_div2), (x0 + w, y_div2), dxfattribs={"layer": layer_frame})

    # Divisiones verticales
    x_div1 = x0 + w * 0.55
    msp.add_line((x_div1, y0), (x_div1, y_div2), dxfattribs={"layer": layer_frame})

    # Textos del cajetín
    empresa = info_instalacion.get("empresa", "BOLIMUR INSTALACIONES S.L.")
    cliente = info_instalacion.get("cliente", "PROYECTO TÉCNICO")
    plano_nom = info_instalacion.get("plano", "ELE-01")
    escala = info_instalacion.get("escala", "1:50")
    fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")

    msp.add_text(empresa, dxfattribs={"layer": layer_title, "height": 3.8}).set_placement((x0 + 4, y0 + h - 8))
    msp.add_text("INGENIERÍA Y MONTAJES ELÉCTRICOS BT", dxfattribs={"layer": layer_txt, "height": 2.2}).set_placement((x0 + 4, y0 + h - 13))

    msp.add_text(f"PROYECTO: {cliente}", dxfattribs={"layer": layer_txt, "height": 2.5}).set_placement((x0 + 4, y_div1 + 5))
    msp.add_text("ESQUEMA UNIFILAR GENERAL (REBT / ITC-BT-17 / ITC-BT-25)", dxfattribs={"layer": layer_title, "height": 2.5}).set_placement((x0 + 4, y_div1 + 1))

    msp.add_text(f"FECHA: {fecha_hoy}", dxfattribs={"layer": layer_txt, "height": 2.2}).set_placement((x0 + 4, y0 + 4))
    msp.add_text(f"ESCALA: {escala}", dxfattribs={"layer": layer_txt, "height": 2.2}).set_placement((x0 + 45, y0 + 4))

    msp.add_text(f"PLANO Nº: {plano_nom}", dxfattribs={"layer": layer_title, "height": 3.2}).set_placement((x_div1 + 5, y_div1 + 5))
    msp.add_text("NORMA: UNE-EN 60617 / UNE 20460", dxfattribs={"layer": layer_txt, "height": 2.0}).set_placement((x_div1 + 5, y0 + 4))


def generar_dxf_unifilar(datos_cuadro: Optional[Dict[str, Any]] = None):
    """
    Genera un Drawing DXF nativo de AutoCAD Release 2010 con capas, bloques UNE-EN 60617,
    embarrado de fases, diferenciales, PIAs y cajetín oficial.
    """
    if not EZDXF_AVAILABLE:
        raise ImportError("ezdxf no está instalado en el entorno.")

    if not datos_cuadro:
        datos_cuadro = obtener_datos_ejemplo_unifilar()

    # Formato R2010 (AC1024) - compatible universalmente
    doc = ezdxf.new("R2010")
    configurar_capas_autocad(doc)
    msp = doc.modelspace()

    # Dimensiones estándar A3 (420 x 297 mm)
    ancho_lamina = 420.0
    alto_lamina = 297.0
    margen = 10.0

    x_min = margen
    y_min = margen
    x_max = ancho_lamina - margen
    y_max = alto_lamina - margen

    # Marco exterior de la lámina
    msp.add_lwpolyline(
        [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max), (x_min, y_min)],
        dxfattribs={"layer": "0_MARCO_PAPEL"}
    )
    # Marco interior (5 mm adicional)
    msp.add_lwpolyline(
        [(x_min + 5, y_min + 5), (x_max - 5, y_min + 5), (x_max - 5, y_max - 5), (x_min + 5, y_max - 5), (x_min + 5, y_min + 5)],
        dxfattribs={"layer": "0_MARCO_PAPEL"}
    )

    # Cajetín en esquina inferior derecha
    w_caj = 175.0
    h_caj = 40.0
    dibujar_cajetin_autocad(msp, x_max - 5 - w_caj, y_min + 5, w_caj, h_caj, datos_cuadro.get("instalacion", {}))

    # Título superior del plano
    msp.add_text("ESQUEMA UNIFILAR DEL CUADRO GENERAL DE MANDO Y PROTECCIÓN (CGMP)", dxfattribs={"layer": "ELE_TEXTOS_TITULOS", "height": 4.5}).set_placement((x_min + 15, y_max - 15))
    tipo_sum = datos_cuadro.get("tipo_suministro", "Monofásico 1N~ 230V - 50 Hz")
    msp.add_text(f"SUMINISTRO: {tipo_sum} | POTENCIA MÁXIMA DE DISEÑO: {datos_cuadro.get('potencia_prevista_w', 9200)} W", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 2.8}).set_placement((x_min + 15, y_max - 22))

    # Distribución de circuitos
    diferenciales = datos_cuadro.get("diferenciales", [])
    total_circs = sum(len(d.get("circuitos", [])) for d in diferenciales)
    total_circs = max(total_circs, 1)

    # Coordenadas de cabecera
    xc = (x_min + x_max) / 2.0 - 40.0
    y_cab = y_max - 35.0

    # 1. Acometida / Red
    msp.add_text("RED DE DISTRIBUCIÓN PÚBLICA 230V 50Hz", dxfattribs={"layer": "ELE_TEXTOS_TITULOS", "height": 2.5}).set_placement((xc - 25, y_cab + 5))
    msp.add_line((xc, y_cab), (xc, y_cab - 12), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})

    # 2. Símbolo IGA (UNE-EN 60617)
    iga = datos_cuadro.get("iga", {})
    iga_cal = iga.get("calibre", 40)
    y_iga = y_cab - 12
    # Interruptor
    msp.add_line((xc, y_iga), (xc - 5, y_iga - 10), dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
    msp.add_circle((xc, y_iga), 0.8, dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
    msp.add_circle((xc, y_iga - 12), 0.8, dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
    # Térmico (bimetal)
    msp.add_line((xc - 3, y_iga - 5), (xc - 8, y_iga - 8), dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
    msp.add_line((xc - 8, y_iga - 8), (xc - 6, y_iga - 10), dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
    # Magnético (bobina)
    msp.add_lwpolyline([(xc - 11, y_iga - 9), (xc - 8, y_iga - 9), (xc - 8, y_iga - 12), (xc - 11, y_iga - 12), (xc - 11, y_iga - 9)], dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})

    msp.add_text("IGA", dxfattribs={"layer": "ELE_TEXTOS_TITULOS", "height": 3.0}).set_placement((xc + 4, y_iga - 4))
    msp.add_text(f"2P {iga_cal}A Curva C", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 2.5}).set_placement((xc + 4, y_iga - 9))
    msp.add_text("Pdc: 6 kA (UNE-EN 60898)", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 1.8}).set_placement((xc + 4, y_iga - 13))

    # Sobretensiones POP + DPS
    y_dps = y_iga - 12
    msp.add_line((xc, y_dps), (xc, y_dps - 10), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})
    msp.add_line((xc, y_dps - 5), (xc - 18, y_dps - 5), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})
    msp.add_lwpolyline([(xc - 28, y_dps - 10), (xc - 18, y_dps - 10), (xc - 18, y_dps), (xc - 28, y_dps), (xc - 28, y_dps - 10)], dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
    msp.add_text("DPS", dxfattribs={"layer": "ELE_TEXTOS_TITULOS", "height": 2.0}).set_placement((xc - 26, y_dps - 4))
    msp.add_text("POP+DPS Tipo 2", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 1.8}).set_placement((xc - 38, y_dps - 14))

    # Barra distribuidora a diferenciales
    y_bus_difs = y_dps - 10
    msp.add_line((xc, y_bus_difs), (xc, y_bus_difs - 6), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})
    y_split = y_bus_difs - 6

    # Calcular posiciones horizontales para los grupos
    ancho_disponible = x_max - x_min - 30.0
    paso_circ = ancho_disponible / max(total_circs, 1)

    c_acum = 0
    x_difs = []
    for d_idx, d in enumerate(diferenciales):
        circs = d.get("circuitos", [])
        n_c = max(len(circs), 1)
        x_inicio = x_min + 15 + c_acum * paso_circ
        x_fin = x_min + 15 + (c_acum + n_c) * paso_circ - 6
        x_centro = (x_inicio + x_fin) / 2.0
        x_difs.append({"idx": d_idx, "centro": x_centro, "x1": x_inicio, "x2": x_fin, "circs": circs, "dif": d})
        c_acum += n_c

    # Barra horizontal principal
    if len(x_difs) > 1:
        x_prim = x_difs[0]["centro"]
        x_ult = x_difs[-1]["centro"]
        msp.add_line((x_prim, y_split), (x_ult, y_split), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})

    # Dibujar diferenciales y sus circuitos
    y_bus_circs = y_split - 38.0

    for item in x_difs:
        xd = item["centro"]
        d = item["dif"]
        circs = item["circs"]

        # Bajante al diferencial
        msp.add_line((xd, y_split), (xd, y_split - 8), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})
        msp.add_circle((xd, y_split), 0.7, dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})

        # Símbolo Interruptor Diferencial UNE-EN 60617
        yd = y_split - 8
        msp.add_line((xd, yd), (xd - 4, yd - 8), dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
        msp.add_circle((xd, yd), 0.7, dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
        msp.add_circle((xd, yd - 10), 0.7, dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})

        # Toroide diferencial
        msp.add_circle((xd - 10, yd - 5), 3.2, dxfattribs={"layer": "ELE_TIERRA_PE"})
        msp.add_line((xd - 10, yd - 2), (xd - 10, yd - 8), dxfattribs={"layer": "ELE_TIERRA_PE"})
        msp.add_line((xd - 13, yd - 5), (xd - 7, yd - 5), dxfattribs={"layer": "ELE_TIERRA_PE"})
        msp.add_line((xd - 7, yd - 5), (xd - 2, yd - 5), dxfattribs={"layer": "ELE_TIERRA_PE"})

        # Textos diferencial
        msp.add_text(f"{d.get('id', 'ID')}", dxfattribs={"layer": "ELE_TEXTOS_TITULOS", "height": 2.8}).set_placement((xd + 4, yd - 3))
        msp.add_text(f"2P {d.get('calibre', 40)}A / {d.get('sensibilidad_ma', 30)}mA", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 2.2}).set_placement((xd + 4, yd - 7))
        msp.add_text(f"Clase: {d.get('clase', 'A')}", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 2.0}).set_placement((xd + 4, yd - 10.5))

        # Línea de bajada al peine del grupo
        msp.add_line((xd, yd - 10), (xd, y_bus_circs), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})

        # Peine repartidor de este grupo
        x1 = item["x1"]
        x2 = item["x2"]
        msp.add_line((x1, y_bus_circs), (x2, y_bus_circs), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})
        msp.add_circle((xd, y_bus_circs), 0.8, dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})

        # Circuitos individuales (PIAs)
        n_c = len(circs)
        if n_c > 0:
            step_c = (x2 - x1) / (n_c + 1)
            for j, c in enumerate(circs):
                xc_pia = x1 + (j + 1) * step_c

                # Bajante al PIA
                msp.add_line((xc_pia, y_bus_circs), (xc_pia, y_bus_circs - 8), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})
                msp.add_circle((xc_pia, y_bus_circs), 0.6, dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})

                yp = y_bus_circs - 8
                # Símbolo Magnetotérmico PIA
                msp.add_line((xc_pia, yp), (xc_pia - 4, yp - 7), dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
                msp.add_circle((xc_pia, yp), 0.6, dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
                msp.add_circle((xc_pia, yp - 9), 0.6, dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})

                # Disparador térmico y magnético del PIA
                msp.add_line((xc_pia - 2, yp - 4), (xc_pia - 5, yp - 6), dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})
                msp.add_lwpolyline([(xc_pia - 8, yp - 6), (xc_pia - 6, yp - 6), (xc_pia - 6, yp - 8), (xc_pia - 8, yp - 8), (xc_pia - 8, yp - 6)], dxfattribs={"layer": "ELE_SIMBOLOS_APARAMENTA"})

                # Salida de línea
                msp.add_line((xc_pia, yp - 9), (xc_pia, yp - 28), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})

                # Marcas de conductores oblicuas (Fase + Neutro + Tierra)
                y_tr = yp - 16
                msp.add_line((xc_pia - 2, y_tr - 2), (xc_pia + 2, y_tr + 2), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})
                msp.add_line((xc_pia - 2, y_tr), (xc_pia + 2, y_tr + 4), dxfattribs={"layer": "ELE_LINEAS_DISTRIBUCION"})
                msp.add_line((xc_pia - 2, y_tr + 2), (xc_pia + 2, y_tr + 6), dxfattribs={"layer": "ELE_TIERRA_PE"})
                msp.add_circle((xc_pia + 3, y_tr + 7), 0.4, dxfattribs={"layer": "ELE_TIERRA_PE"})

                # Textos del circuito
                cod = c.get("codigo", f"C{j+1}")
                pia_val = c.get("pia", 16)
                sec_val = c.get("seccion", 2.5)
                tubo_val = c.get("tubo", 20)
                denom = c.get("denominacion", "")

                msp.add_text(f"{cod}", dxfattribs={"layer": "ELE_TEXTOS_TITULOS", "height": 2.5}).set_placement((xc_pia - 4, yp - 32))
                msp.add_text(f"{pia_val}A (C)", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 1.9}).set_placement((xc_pia + 3, yp - 5))
                msp.add_text(f"2x{sec_val}+TT", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 1.7}).set_placement((xc_pia + 3, yp - 14))
                msp.add_text(f"M{tubo_val}", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 1.6}).set_placement((xc_pia + 3, yp - 18))

                # Denominación vertical / multilínea
                palabras = denom.split()
                if len(palabras) > 3:
                    p1 = " ".join(palabras[:2])
                    p2 = " ".join(palabras[2:])
                else:
                    p1 = denom
                    p2 = ""
                msp.add_text(p1[:18], dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 1.8}).set_placement((xc_pia - 9, yp - 37))
                if p2:
                    msp.add_text(p2[:18], dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 1.8}).set_placement((xc_pia - 9, yp - 41))

    # 4. Barra General de Tierra PE (ITC-BT-18)
    y_pe = y_min + 18.0
    msp.add_line((x_min + 15, y_pe), (x_max - w_caj - 15, y_pe), dxfattribs={"layer": "ELE_TIERRA_PE"})
    # Símbolo de tierra
    x_pe_sym = x_min + 25
    msp.add_line((x_pe_sym, y_pe), (x_pe_sym, y_pe - 5), dxfattribs={"layer": "ELE_TIERRA_PE"})
    msp.add_line((x_pe_sym - 4, y_pe - 5), (x_pe_sym + 4, y_pe - 5), dxfattribs={"layer": "ELE_TIERRA_PE"})
    msp.add_line((x_pe_sym - 2.5, y_pe - 7), (x_pe_sym + 2.5, y_pe - 7), dxfattribs={"layer": "ELE_TIERRA_PE"})
    msp.add_line((x_pe_sym - 1, y_pe - 9), (x_pe_sym + 1, y_pe - 9), dxfattribs={"layer": "ELE_TIERRA_PE"})

    pt = datos_cuadro.get("puesta_a_tierra", {})
    sec_enlace = pt.get("seccion_enlace_mm2", 16)
    rt = pt.get("resistencia_rt_ohm", 11.8)
    msp.add_text("BORNE PRINCIPAL DE PUESTA A TIERRA (PE - ITC-BT-18)", dxfattribs={"layer": "ELE_TEXTOS_TITULOS", "height": 2.2}).set_placement((x_pe_sym + 8, y_pe - 4))
    msp.add_text(f"Conductor Enlace Cu 1x{sec_enlace} mm² | Rt = {rt} Ω (Exigencia REBT: Rt ≤ 15 Ω)", dxfattribs={"layer": "ELE_TEXTOS_PARAMETROS", "height": 1.9}).set_placement((x_pe_sym + 8, y_pe - 8))

    return doc


def generar_dxf_unifilar_bytes(datos_cuadro: Optional[Dict[str, Any]] = None) -> bytes:
    """Retorna el contenido del archivo DXF como bytes listos para descarga."""
    doc = generar_dxf_unifilar(datos_cuadro)
    buffer = io.StringIO()
    doc.write(buffer)
    return buffer.getvalue().encode("utf-8")


def generar_autocad_preview_image(datos_cuadro: Optional[Dict[str, Any]] = None, output_path: Optional[str] = None) -> bytes:
    """
    Genera una imagen con la estética auténtica de AutoCAD (Espacio Modelo Dark Mode):
    - Fondo antracita / gris oscuro de dibujo (#1e1e1e / #22262e)
    - Rejilla técnica tenue (Drafting Grid)
    - Icono de Coordenadas SCP / UCS (X rojo, Y verde, origen WCS)
    - Capas normativas con colores ACI: Cyan (#00e5ff), Amarillo (#ffd600), Verde (#00e676), Blanco (#ffffff)
    - Barra inferior de pestañas [Modelo] [Presentación 1]
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib no está instalado para renderizar la imagen.")

    if not datos_cuadro:
        datos_cuadro = obtener_datos_ejemplo_unifilar()

    fig, ax = plt.subplots(figsize=(16, 11.3), dpi=150)
    
    # Fondo idéntico al espacio modelo de AutoCAD Dark Theme
    bg_color = "#1e222a"
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    # Rejilla suave de dibujo (AutoCAD Grid F7)
    ax.grid(True, which="both", color="#2a303c", linestyle="-", linewidth=0.6, alpha=0.8)
    ax.minorticks_on()
    ax.grid(True, which="minor", color="#242933", linestyle=":", linewidth=0.4, alpha=0.5)

    # Dimensiones
    ancho_lamina = 420.0
    alto_lamina = 297.0
    margen = 10.0

    x_min, y_min = margen, margen
    x_max, y_max = ancho_lamina - margen, alto_lamina - margen

    # Colores ACI AutoCAD para pantalla
    c_cyan = "#00e5ff"       # ELE_LINEAS_DISTRIBUCION (ACI 4)
    c_yellow = "#ffea00"     # ELE_SIMBOLOS_APARAMENTA (ACI 2)
    c_green = "#00e676"      # ELE_TIERRA_PE (ACI 3)
    c_white = "#ffffff"      # TEXTOS / MARCO (ACI 7)
    c_dim = "#90a4ae"        # Secundario
    c_red = "#ff3d00"        # Cotas / Alerta (ACI 1)

    # Marco exterior e interior
    ax.add_patch(patches.Rectangle((x_min, y_min), x_max - x_min, y_max - y_min, fill=False, edgecolor=c_white, linewidth=1.4))
    ax.add_patch(patches.Rectangle((x_min + 5, y_min + 5), (x_max - x_min) - 10, (y_max - y_min) - 10, fill=False, edgecolor=c_white, linewidth=0.8))

    # Cajetín oficial en esquina inferior derecha
    w_caj = 175.0
    h_caj = 40.0
    x_caj = x_max - 5 - w_caj
    y_caj = y_min + 5
    ax.add_patch(patches.Rectangle((x_caj, y_caj), w_caj, h_caj, fill=True, facecolor="#181b22", edgecolor=c_white, linewidth=1.0))
    ax.plot([x_caj, x_caj + w_caj], [y_caj + h_caj * 0.45, y_caj + h_caj * 0.45], color=c_white, linewidth=0.7)
    ax.plot([x_caj, x_caj + w_caj], [y_caj + h_caj * 0.75, y_caj + h_caj * 0.75], color=c_white, linewidth=0.7)
    ax.plot([x_caj + w_caj * 0.55, x_caj + w_caj * 0.55], [y_caj, y_caj + h_caj * 0.75], color=c_white, linewidth=0.7)

    # Textos de Cajetín
    info = datos_cuadro.get("instalacion", {})
    ax.text(x_caj + 4, y_caj + h_caj - 8, info.get("empresa", "BOLIMUR INSTALACIONES S.L."), color=c_yellow, fontsize=11, fontweight="bold", family="sans-serif")
    ax.text(x_caj + 4, y_caj + h_caj - 14, "INGENIERÍA Y MONTAJES ELÉCTRICOS BT - REBT / UNE-EN 60617", color=c_dim, fontsize=7.5, family="monospace")
    ax.text(x_caj + 4, y_caj + h_caj * 0.45 + 5, f"PROYECTO: {info.get('cliente', 'VIVIENDA UNIFAMILIAR')}", color=c_white, fontsize=8, family="sans-serif")
    ax.text(x_caj + 4, y_caj + h_caj * 0.45 + 1.2, "ESQUEMA UNIFILAR GENERAL (ITC-BT-17 / ITC-BT-25)", color=c_yellow, fontsize=8, fontweight="bold")
    ax.text(x_caj + 4, y_caj + 3.5, f"FECHA: {datetime.date.today().strftime('%d/%m/%Y')}   |   ESCALA: 1:50", color=c_dim, fontsize=7.5, family="monospace")
    ax.text(x_caj + w_caj * 0.55 + 6, y_caj + h_caj * 0.45 + 4, f"PLANO: {info.get('plano', 'ELE-01')}", color=c_cyan, fontsize=10, fontweight="bold")
    ax.text(x_caj + w_caj * 0.55 + 6, y_caj + 3.5, "FORMATO: DWG / DXF R2010", color=c_dim, fontsize=7, family="monospace")

    # Título del plano superior
    ax.text(x_min + 15, y_max - 15, "ESQUEMA UNIFILAR DEL CUADRO GENERAL DE MANDO Y PROTECCIÓN (CGMP)", color=c_yellow, fontsize=12, fontweight="bold")
    ax.text(x_min + 15, y_max - 23, f"SUMINISTRO: {datos_cuadro.get('tipo_suministro', 'Monofásico 1N~ 230V - 50 Hz')}  |  POTENCIA DISEÑO: {datos_cuadro.get('potencia_prevista_w', 9200)} W", color=c_white, fontsize=8.5, family="monospace")

    # Cabecera / IGA / DPS
    xc = (x_min + x_max) / 2.0 - 45.0
    y_cab = y_max - 35.0

    ax.text(xc, y_cab + 6, "RED DE DISTRIBUCIÓN PÚBLICA 230V 50Hz", color=c_cyan, fontsize=8, fontweight="bold", ha="center")
    ax.plot([xc, xc], [y_cab, y_cab - 12], color=c_cyan, linewidth=1.8)

    # IGA
    iga = datos_cuadro.get("iga", {})
    y_iga = y_cab - 12
    ax.plot([xc, xc - 6], [y_iga, y_iga - 10], color=c_yellow, linewidth=2.0)
    ax.plot(xc, y_iga, marker="o", markersize=4, color=c_yellow)
    ax.plot(xc, y_iga - 12, marker="o", markersize=4, color=c_yellow)
    # Bimetal térmico
    ax.plot([xc - 3, xc - 8, xc - 6], [y_iga - 5, y_iga - 8, y_iga - 10], color=c_yellow, linewidth=1.2)
    # Bobina magnética
    ax.add_patch(patches.Rectangle((xc - 11, y_iga - 12), 3, 3, fill=True, facecolor=c_yellow, edgecolor=c_yellow))

    ax.text(xc + 5, y_iga - 4, "IGA", color=c_yellow, fontsize=9.5, fontweight="bold")
    ax.text(xc + 5, y_iga - 9, f"2P {iga.get('calibre', 40)}A Curva C", color=c_white, fontsize=8, fontweight="bold")
    ax.text(xc + 5, y_iga - 13, "Pdc: 6 kA (UNE-EN 60898)", color=c_dim, fontsize=6.8)

    # DPS (Sobretensiones)
    y_dps = y_iga - 12
    ax.plot([xc, xc], [y_dps, y_dps - 10], color=c_cyan, linewidth=1.8)
    ax.plot([xc, xc - 20], [y_dps - 5, y_dps - 5], color=c_cyan, linewidth=1.4)
    ax.add_patch(patches.Rectangle((xc - 30, y_dps - 11), 10, 11, fill=True, facecolor="#14171d", edgecolor=c_yellow, linewidth=1.2))
    ax.text(xc - 25, y_dps - 5, "DPS", color=c_yellow, fontsize=7.5, fontweight="bold", ha="center")
    ax.text(xc - 25, y_dps - 15, "POP + DPS Tipo 2\n(Sobretensiones)", color=c_white, fontsize=6.5, ha="center")

    # Reparto a Diferenciales
    y_bus_difs = y_dps - 10
    ax.plot([xc, xc], [y_bus_difs, y_bus_difs - 6], color=c_cyan, linewidth=1.8)
    y_split = y_bus_difs - 6

    diferenciales = datos_cuadro.get("diferenciales", [])
    total_circs = sum(len(d.get("circuitos", [])) for d in diferenciales)
    ancho_disp = x_max - x_min - 35.0
    paso = ancho_disp / max(total_circs, 1)

    x_difs = []
    c_acum = 0
    for d_idx, d in enumerate(diferenciales):
        circs = d.get("circuitos", [])
        n_c = max(len(circs), 1)
        x1 = x_min + 15 + c_acum * paso
        x2 = x_min + 15 + (c_acum + n_c) * paso - 6
        xc_d = (x1 + x2) / 2.0
        x_difs.append({"centro": xc_d, "x1": x1, "x2": x2, "dif": d, "circs": circs})
        c_acum += n_c

    if len(x_difs) > 1:
        ax.plot([x_difs[0]["centro"], x_difs[-1]["centro"]], [y_split, y_split], color=c_cyan, linewidth=2.0)

    y_bus_circs = y_split - 40.0

    for item in x_difs:
        xd = item["centro"]
        d = item["dif"]
        circs = item["circs"]

        # Bajante
        ax.plot([xd, xd], [y_split, y_split - 8], color=c_cyan, linewidth=1.6)
        ax.plot(xd, y_split, marker="o", markersize=3.5, color=c_cyan)

        # Diferencial símbolo UNE-EN 60617
        yd = y_split - 8
        ax.plot([xd, xd - 5], [yd, yd - 8], color=c_yellow, linewidth=1.8)
        ax.plot(xd, yd, marker="o", markersize=3.5, color=c_yellow)
        ax.plot(xd, yd - 10, marker="o", markersize=3.5, color=c_yellow)

        # Toroide
        ax.add_patch(patches.Circle((xd - 10, yd - 5), 3.2, fill=False, edgecolor=c_green, linewidth=1.4))
        ax.plot([xd - 10, xd - 10], [yd - 2, yd - 8], color=c_green, linewidth=1.0)
        ax.plot([xd - 13, xd - 2], [yd - 5, yd - 5], color=c_green, linewidth=1.0)

        # Textos diferencial
        ax.text(xd + 4, yd - 3, d.get("id", "ID"), color=c_yellow, fontsize=8.5, fontweight="bold")
        ax.text(xd + 4, yd - 7, f"2P {d.get('calibre', 40)}A / {d.get('sensibilidad_ma', 30)}mA", color=c_white, fontsize=7.5, fontweight="bold")
        ax.text(xd + 4, yd - 11, f"Clase: {d.get('clase', 'A')}", color=c_green, fontsize=7.0)

        # Bajante a barra de circuitos
        ax.plot([xd, xd], [yd - 10, y_bus_circs], color=c_cyan, linewidth=1.8)

        # Peine
        x1, x2 = item["x1"], item["x2"]
        ax.plot([x1, x2], [y_bus_circs, y_bus_circs], color=c_cyan, linewidth=2.4)
        ax.plot(xd, y_bus_circs, marker="o", markersize=4, color=c_cyan)

        # Circuitos (PIAs)
        n_c = len(circs)
        if n_c > 0:
            step_c = (x2 - x1) / (n_c + 1)
            for j, c in enumerate(circs):
                xc_p = x1 + (j + 1) * step_c

                # Bajante
                ax.plot([xc_p, xc_p], [y_bus_circs, y_bus_circs - 8], color=c_cyan, linewidth=1.2)
                ax.plot(xc_p, y_bus_circs, marker="o", markersize=3, color=c_cyan)

                yp = y_bus_circs - 8
                # Símbolo PIA
                ax.plot([xc_p, xc_p - 4], [yp, yp - 7], color=c_yellow, linewidth=1.6)
                ax.plot(xc_p, yp, marker="o", markersize=3, color=c_yellow)
                ax.plot(xc_p, yp - 9, marker="o", markersize=3, color=c_yellow)

                # Disparador PIA
                ax.plot([xc_p - 2, xc_p - 5], [yp - 4, yp - 6], color=c_yellow, linewidth=1.0)
                ax.add_patch(patches.Rectangle((xc_p - 7.5, yp - 8), 2.2, 2.2, fill=True, facecolor=c_yellow, edgecolor=c_yellow))

                # Salida
                ax.plot([xc_p, xc_p], [yp - 9, yp - 28], color=c_cyan, linewidth=1.4)

                # Conductores oblicuos
                y_tr = yp - 16
                ax.plot([xc_p - 2, xc_p + 2], [y_tr - 2, y_tr + 2], color=c_dim, linewidth=1.2)
                ax.plot([xc_p - 2, xc_p + 2], [y_tr, y_tr + 4], color=c_dim, linewidth=1.2)
                ax.plot([xc_p - 2, xc_p + 2], [y_tr + 2, y_tr + 6], color=c_green, linewidth=1.2)
                ax.plot(xc_p + 3, y_tr + 7, marker="o", markersize=2, color=c_green)

                # Textos
                cod = c.get("codigo", f"C{j+1}")
                pia_val = c.get("pia", 16)
                sec_val = c.get("seccion", 2.5)
                tubo_val = c.get("tubo", 20)
                denom = c.get("denominacion", "")

                ax.text(xc_p, yp - 32, cod, color=c_yellow, fontsize=8.5, fontweight="bold", ha="center")
                ax.text(xc_p + 2.5, yp - 5, f"{pia_val}A (C)", color=c_white, fontsize=6.8, fontweight="bold")
                ax.text(xc_p + 2.5, yp - 13, f"2x{sec_val}+TT", color=c_cyan, fontsize=6.5)
                ax.text(xc_p + 2.5, yp - 17, f"M{tubo_val}", color=c_dim, fontsize=6.2)

                # Denominación dividida
                palabras = denom.split()
                if len(palabras) > 2:
                    p1 = " ".join(palabras[:2])
                    p2 = " ".join(palabras[2:])
                else:
                    p1 = denom
                    p2 = ""
                ax.text(xc_p, yp - 37, p1[:16], color=c_white, fontsize=6.5, ha="center")
                if p2:
                    ax.text(xc_p, yp - 41, p2[:16], color=c_dim, fontsize=6.0, ha="center")

    # Barra Puesta a Tierra PE
    y_pe = y_min + 18.0
    ax.plot([x_min + 15, x_max - w_caj - 15], [y_pe, y_pe], color=c_green, linewidth=2.0)
    x_pe_s = x_min + 25
    ax.plot([x_pe_s, x_pe_s], [y_pe, y_pe - 5], color=c_green, linewidth=1.5)
    ax.plot([x_pe_s - 4, x_pe_s + 4], [y_pe - 5, y_pe - 5], color=c_green, linewidth=1.5)
    ax.plot([x_pe_s - 2.5, x_pe_s + 2.5], [y_pe - 7, y_pe - 7], color=c_green, linewidth=1.2)
    ax.plot([x_pe_s - 1, x_pe_s + 1], [y_pe - 9, y_pe - 9], color=c_green, linewidth=1.0)

    pt = datos_cuadro.get("puesta_a_tierra", {})
    ax.text(x_pe_s + 8, y_pe - 3, "BORNE PRINCIPAL DE PUESTA A TIERRA (PE - ITC-BT-18)", color=c_green, fontsize=7.8, fontweight="bold")
    ax.text(x_pe_s + 8, y_pe - 7.5, f"Línea de Enlace Cu 1x{pt.get('seccion_enlace_mm2', 16)} mm²  |  Rt = {pt.get('resistencia_rt_ohm', 11.8)} Ω (Límite REBT ≤ 15 Ω)", color=c_white, fontsize=7.0, family="monospace")

    # Icono UCS de AutoCAD en esquina inferior izquierda (WCS X red, Y green)
    ucs_x = x_min + 12
    ucs_y = y_min + 30
    ax.annotate("", xy=(ucs_x + 9, ucs_y), xytext=(ucs_x, ucs_y), arrowprops=dict(arrowstyle="->", color="#f44336", lw=1.6))
    ax.annotate("", xy=(ucs_x, ucs_y + 9), xytext=(ucs_x, ucs_y), arrowprops=dict(arrowstyle="->", color="#4caf50", lw=1.6))
    ax.add_patch(patches.Rectangle((ucs_x - 1, ucs_y - 1), 2, 2, fill=True, facecolor=c_white, edgecolor=c_white))
    ax.text(ucs_x + 10.5, ucs_y - 1.5, "X", color="#f44336", fontsize=7.5, fontweight="bold")
    ax.text(ucs_x - 1.5, ucs_y + 10.5, "Y", color="#4caf50", fontsize=7.5, fontweight="bold")
    ax.text(ucs_x - 3, ucs_y - 4, "WCS", color=c_dim, fontsize=5.8, family="monospace")

    # Límites de coordenadas
    ax.set_xlim(0, ancho_lamina)
    ax.set_ylim(0, alto_lamina)
    ax.set_aspect("equal")

    # Estilo de interfaz AutoCAD (Quitar bordes habituales de matplotlib)
    ax.tick_params(axis="both", which="both", colors="#546e7a", labelsize=6.5)
    for spine in ax.spines.values():
        spine.set_color("#37474f")
        spine.set_linewidth(1.0)

    # Sub-barra inferior estilo AutoCAD: [ Modelo ] [ Presentación 1 ] [ Presentación 2 ]
    plt.subplots_adjust(left=0.03, right=0.98, top=0.96, bottom=0.05)
    fig.text(0.04, 0.015, "◄ ►  | Modelo |  Presentación1  |  Presentación2  |  +  |", color="#b0bec5", fontsize=8.5, family="monospace", bbox=dict(boxstyle="square,pad=0.3", facecolor="#263238", edgecolor="#37474f"))
    fig.text(0.72, 0.015, "AUTOCAD REBT ED. 2026  |  SNAP GRID ORTHO POLAR OSNAP", color="#78909c", fontsize=7.5, family="monospace")

    # Guardar a buffer o disco
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png", dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    img_bytes = img_buf.getvalue()

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_bytes)

    return img_bytes
