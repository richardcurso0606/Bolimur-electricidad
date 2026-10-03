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

