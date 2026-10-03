# -*- coding: utf-8 -*-
import pytest
import pandas as pd
from modulos import pdf_presupuesto

def test_generar_pdf_presupuesto_bytes():
    proyecto_info = {
        "empresa": "BOLIMUR Instalaciones",
        "proyectista": "Ingeniero Test",
        "licencia": "REBT-12345",
        "localidad": "Madrid",
        "telefono": "600112233",
        "expediente": "PRES-TEST-01",
        "fecha": "02/10/2026"
    }
    df_comercial = pd.DataFrame([
        {"Estancia / Partida": "Cocina", "Detalle de Mecanismos / Equipamiento": "3 Schukos + C4 Lavadora", "Importe (€)": "450.00 €"},
        {"Estancia / Partida": "Salón", "Detalle de Mecanismos / Equipamiento": "4 Schukos + 2 Interruptores", "Importe (€)": "320.00 €"}
    ])
    presupuesto_data = {
        "df_comercial": df_comercial,
        "subtotal_neto": 770.0,
        "iva_pct": 21.0,
        "cuota_iva": 161.7,
        "total_cliente": 931.7,
        "total_puntos": 9,
        "precio_medio_punto": 103.52,
        "serie_mecanismos": "Simon 27",
        "marca_protecciones": "Schneider",
        "potencia_kw": "5.75 kW"
    }

    pdf_bytes = pdf_presupuesto.generar_pdf_presupuesto(proyecto_info, presupuesto_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")

def test_generar_pdf_orden_compra_bytes():
    proyecto_info = {
        "empresa": "BOLIMUR Instalaciones",
        "proyectista": "Richard Choque",
        "licencia": "REBT-30/15892",
        "localidad": "Murcia",
        "telefono": "600000000",
        "expediente": "OC-TEST-01",
        "fecha": "03/10/2026"
    }
    orden_compra_data = {
        "categorias": {
            "🔲 1. Mecanismos y Marcos": [
                {"articulo": "Interruptor simple", "desc_exacta": "Interruptor Simon 27 Play Blanco", "proveedor": "Obramat", "cantidad": 6, "unidad": "ud", "precio_unitario": 2.50, "subtotal": 15.0}
            ],
            "⚡ 2. Cables y Conductores": [
                {"articulo": "Cable 1.5 mm² Azul", "desc_exacta": "Cable H07Z1-K 1.5mm² Azul (Rollo 100m)", "proveedor": "Obramat", "cantidad": 100, "unidad": "m", "precio_unitario": 0.24, "subtotal": 24.0}
            ]
        },
        "total_neto": 39.0,
        "iva_pct": 21.0,
        "cuota_iva": 8.19,
        "total_con_iva": 47.19,
        "potencia_kw": "5.750 W",
        "serie_mecanismos": "Simon 27 Play",
        "marca_protecciones": "Schneider"
    }

    pdf_bytes = pdf_presupuesto.generar_pdf_orden_compra(proyecto_info, orden_compra_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 3000
    assert pdf_bytes.startswith(b"%PDF")

def test_generar_pdf_unifilar_industria_bytes():
    proyecto_info = {
        "empresa": "BOLIMUR Instalaciones",
        "proyectista": "Richard Choque",
        "licencia": "REBT-30/15892",
        "localidad": "Rincón de Seca, Murcia",
        "telefono": "600000000",
        "expediente": "MTD-TEST-01",
        "fecha": "03/10/2026"
    }
    unifilar_data = {
        "potencia_w": 5750,
        "iga_amperaje": 25,
        "grado_electr": "Básica",
        "tipo_cable": "H07Z1-K Libre de Halógenos",
        "tipo_tubo": "Tubo Corrugado PVC",
        "marca_protecciones": "Schneider",
        "n_difs": 1,
        "circuitos": [
            {"id": "C1", "denominacion": "Iluminación", "pia": 10, "dif": "ID 1", "cable_sec": "2x1.5+TT1.5", "tubo_diam": "M20", "long_m": 15.0, "cdt_pct": 0.85, "pot_w": 2300},
            {"id": "C2", "denominacion": "Tomas de uso general", "pia": 16, "dif": "ID 1", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 18.0, "cdt_pct": 1.15, "pot_w": 3450},
            {"id": "C3", "denominacion": "Cocina y horno", "pia": 25, "dif": "ID 1", "cable_sec": "2x6+TT6", "tubo_diam": "M25", "long_m": 12.0, "cdt_pct": 0.82, "pot_w": 5400},
            {"id": "C4-A", "denominacion": "Lavado", "pia": 16, "dif": "ID 1", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 14.0, "cdt_pct": 0.98, "pot_w": 3450},
            {"id": "C4-B", "denominacion": "Termo ACS", "pia": 16, "dif": "ID 1", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 14.0, "cdt_pct": 0.95, "pot_w": 3450},
            {"id": "C5", "denominacion": "Tomas baños/cocina", "pia": 16, "dif": "ID 1", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 14.0, "cdt_pct": 0.92, "pot_w": 3450}
        ]
    }

    pdf_bytes = pdf_presupuesto.generar_pdf_unifilar_industria(proyecto_info, unifilar_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")

def test_generar_pdf_presupuesto_completo_capitulos_y_manuales():
    proyecto_info = {
        "empresa": "BOLIMUR Instalaciones Eléctricas",
        "proyectista": "Richard Choque",
        "licencia": "REBT-30/15892",
        "localidad": "Murcia",
        "telefono": "600000000",
        "expediente": "PRES-2026-0901",
        "fecha": "03/10/2026"
    }
    capitulos = [
        {"cap": "CAP. 01", "titulo": "Cuadro General CGMP", "desc": "Cuadro 24 elementos con IGA y protecciones", "importe": 380.0},
        {"cap": "CAP. 02", "titulo": "Canalizaciones y Rozas", "desc": "Tubo corrugado y cajas", "importe": 420.0},
        {"cap": "CAP. 03", "titulo": "Cableado Libre de Halógenos", "desc": "Conductores H07Z1-K", "importe": 350.0},
        {"cap": "CAP. 04", "titulo": "Mecanismos por Estancias", "desc": "Serie Efapel MEC 21", "importe": 510.0},
        {"cap": "CAP. 05", "titulo": "Ensayos Reglamentarios y Boletín CIE", "desc": "Ensayos ITC-BT-05 y CIE Murcia", "importe": 150.0},
        {"cap": "CAP. 06", "titulo": "Trabajos Adicionales", "desc": "Línea IRVE para vehículo eléctrico", "importe": 450.0}
    ]
    df_comercial = pd.DataFrame([
        {"Estancia": "Cocina", "Detalle Comercial": "Instalación REBT", "Importe Venta (€)": 450.0},
        {"Estancia": "Salón", "Detalle Comercial": "Instalación REBT", "Importe Venta (€)": 380.0}
    ])
    partidas_manuales = [
        {"concepto": "Línea IRVE Vehículo Eléctrico", "descripcion": "Línea 3x6mm² con diferencial clase A", "cantidad": 1, "unidad": "partida", "precio_unitario": 450.0, "subtotal": 450.0}
    ]
    materiales_pvp = [
        {"categoria": "Mecanismos", "articulo": "Interruptor 10AX", "desc_exacta": "Efapel MEC 21 Blanco", "cantidad": 8, "unidad": "ud", "pvp_unitario": 4.50, "subtotal_pvp": 36.0}
    ]
    presupuesto_data = {
        "capitulos": capitulos,
        "df_comercial": df_comercial,
        "partidas_manuales": partidas_manuales,
        "materiales_pvp": materiales_pvp,
        "incluir_catalogo_pvp": True,
        "subtotal_neto": 2260.0,
        "iva_pct": 21.0,
        "cuota_iva": 474.6,
        "total_cliente": 2734.6,
        "total_puntos": 32,
        "precio_medio_punto": 85.45,
        "serie_mecanismos": "Efapel MEC 21",
        "marca_protecciones": "Schneider",
        "potencia_kw": "5.75 kW (25A)",
        "grado_electr": "Básica",
        "plazo_dias": 4.5,
        "num_operarios": 2
    }

    pdf_bytes = pdf_presupuesto.generar_pdf_presupuesto(proyecto_info, presupuesto_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 8000
    assert pdf_bytes.startswith(b"%PDF")



