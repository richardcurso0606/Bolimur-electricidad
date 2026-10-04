# -*- coding: utf-8 -*-
import pytest
from modulos import pdf_memoria_tecnica

def test_generar_pdf_mtd_industria_murcia_bytes():
    datos_mtd = {
        "titular": {
            "nombre": "Juan Pérez Martínez",
            "nif": "48123456X",
            "domicilio": "Calle Mayor 12, 3ºB",
            "localidad": "Murcia",
            "cp": "30001",
            "provincia": "Murcia",
            "telefono": "600123456",
            "email": "juan@example.com"
        },
        "emplazamiento": {
            "direccion": "Calle Mayor 12, 3ºB",
            "localidad": "Murcia",
            "cp": "30001",
            "uso": "Vivienda Residencial"
        },
        "instalador": {
            "empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
            "cif": "B-73000000",
            "proyectista": "Richard Orlando Choque Tejerina",
            "nif_instalador": "X-1234567-Y",
            "carnet": "REBT-30/15892",
            "registro_rii": "RII-30/08492",
            "domicilio": "Rincón de Seca, Murcia",
            "telefono": "600000000"
        },
        "suministro": {
            "tension": "Monofásico 230 V",
            "potencia_solicitada_w": 5750,
            "potencia_max_w": 9200,
            "grado_electrificacion": "Básica",
            "di_longitud_m": 16.0,
            "di_seccion_fase": 10.0,
            "di_tubo": "Tubo M32",
            "di_cable_tipo": "H07Z1-K (AS)"
        },
        "protecciones": {
            "iga_amperaje": 25,
            "iga_icn_ka": 6.0,
            "sobretensiones": "POP + DPS Tipo 2 (ITC-BT-23)",
            "diferenciales": "2x Diferencial 2P 40A / 30mA Clase A"
        },
        "circuitos": [
            {"id": "C1", "denominacion": "Iluminación", "pia": 10, "dif": "Dif. 1", "cable_sec": "2x1.5+TT1.5", "tubo_diam": "M16", "long_m": 15, "cdt_pct": 0.85, "pot_w": 2300},
            {"id": "C2", "denominacion": "Tomas de corriente", "pia": 16, "dif": "Dif. 1", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 18, "cdt_pct": 1.10, "pot_w": 3450},
            {"id": "C3", "denominacion": "Cocina / Horno", "pia": 25, "dif": "Dif. 1", "cable_sec": "2x6+TT6", "tubo_diam": "M25", "long_m": 12, "cdt_pct": 0.90, "pot_w": 5400},
            {"id": "C4.1", "denominacion": "Lavadora", "pia": 16, "dif": "Dif. 2", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 14, "cdt_pct": 1.00, "pot_w": 3450},
            {"id": "C4.2", "denominacion": "Lavavajillas", "pia": 16, "dif": "Dif. 2", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 14, "cdt_pct": 1.00, "pot_w": 3450},
            {"id": "C4.3", "denominacion": "Termo eléctrico", "pia": 16, "dif": "Dif. 2", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 12, "cdt_pct": 0.85, "pot_w": 2300},
            {"id": "C5", "denominacion": "Baños y aux cocina", "pia": 16, "dif": "Dif. 2", "cable_sec": "2x2.5+TT2.5", "tubo_diam": "M20", "long_m": 16, "cdt_pct": 1.15, "pot_w": 3450}
        ],
        "fecha": "03/10/2026",
        "expediente": "EXP-30/2026/00482"
    }

    pdf_bytes = pdf_memoria_tecnica.generar_pdf_mtd_industria_murcia(datos_mtd)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF")

def test_generar_pdf_cie_oficial_bytes():
    datos_cie = {
        "titular": {"nombre": "Juan Pérez", "nif": "48123456X", "telefono": "600123456", "email": "juan@test.com"},
        "emplazamiento": {"direccion": "C/ Mayor 12", "cp": "30001", "municipio": "Murcia", "cups": "ES0021000000000000XX", "uso": "Vivienda"},
        "instalador": {"empresa": "BOLIMUR", "cif": "B-73000000", "nombre": "Richard Orlando Choque", "licencia": "REBT-30/15892", "registro_rii": "RII-30/08492", "telefono": "600000000"},
        "suministro": {"potencia_instalada_w": 5750, "potencia_max_admisible_w": 9200, "tension": "Monofásico (230 V)", "di_cable": "2x10 mm² Cu", "di_tubo": "Tubo M32", "di_cdt_pct": 0.72, "grado_electrif": "Básica"},
        "protecciones": {"iga_amperaje": 25, "iga_curva": "Curva C", "iga_icn_ka": 6.0, "diferenciales": "2P 40A / 30mA Clase A", "sobretensiones": "VTP+DPS Tipo 2"},
        "ensayos": {
            "pe_ohm": 0.18,
            "aisl_mohm": 85.0,
            "rt_ohm": 8.5,
            "dif_ma": 21.0,
            "dif_ms": 28.0
        },
        "expediente": "EXP-CIE-2026-01",
        "fecha": "03/10/2026"
    }
    pdf_bytes = pdf_memoria_tecnica.generar_pdf_cie_oficial(datos_cie)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")

def test_generar_pdf_manual_usuario_bytes():
    datos_man = {
        "titular": {"nombre": "Juan Pérez"},
        "emplazamiento": {"direccion": "C/ Mayor 12", "municipio": "Murcia"},
        "instalador": {"empresa": "BOLIMUR", "telefono": "600000000", "licencia": "REBT-30/15892"},
        "fecha": "03/10/2026"
    }
    pdf_bytes = pdf_memoria_tecnica.generar_pdf_manual_usuario(datos_man)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 3000
    assert pdf_bytes.startswith(b"%PDF")

def test_generar_pdf_mtd_cuadro_obra_itc_bt_33():
    datos_obra = {
        "tipo_instalacion": "🏗️ Instalación Provisional y Temporal de Obras (ITC-BT-33 / Cuadro de Obra)",
        "tipo_tramitacion": "🏗️ Instalación Temporal de Obra (Suministro Provisional)",
        "titular": {"nombre": "Constructora e Inversiones SL", "nif": "B-30999888"},
        "emplazamiento": {"direccion": "Parcela 45, Sector Residencial", "municipio": "Murcia", "cups": "ES0021000000000000XX", "uso": "Obra de Edificación"},
        "instalador": {"empresa": "BOLIMUR", "cif": "B-73000000", "nombre": "Richard Orlando Choque", "licencia": "REBT-30/15892", "registro_rii": "RII-30/08492"},
        "suministro": {
            "potencia_instalada_w": 15000,
            "potencia_max_admisible_w": 15000,
            "tension": "Trifásico (400 V) - 50 Hz",
            "di_cable": "4x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV",
            "di_tubo": "Tubo M40 intemperie IK09",
            "di_long_m": 15.0,
            "di_cdt_pct": 0.52,
            "grado_electrif": "Provisional de Obra (ITC-BT-33)"
        },
        "protecciones": {
            "iga_amperaje": 40,
            "iga_curva": "Curva D",
            "iga_icn_ka": 10.0,
            "diferenciales": "4P 40A / 30mA Clase A con Seta Parada Emergencia",
            "sobretensiones": "Permanentes + Transitorias Tipo 2 con bobina",
            "puesta_a_tierra": "Pica tierra obra Rt ≤ 15 Ω"
        },
        "ensayos": {
            "pe_ohm": 0.12,
            "aisl_mohm": 100.0,
            "rt_ohm": 9.4,
            "dif_ma": 22.0,
            "dif_ms": 25.0
        },
        "circuitos": [
            {"nombre": "C1 - Toma CETAC Trifásica 32A (Grúa)", "potencia": 10000, "pia": 32, "seccion": "4x6.0+TT6.0", "tubo": "M32", "longitud": 15, "cdt": 0.65, "norma": "ITC-BT-33"},
            {"nombre": "C2 - Toma CETAC Trifásica 16A (Hormigonera)", "potencia": 5000, "pia": 16, "seccion": "4x2.5+TT2.5", "tubo": "M25", "longitud": 15, "cdt": 0.85, "norma": "ITC-BT-33"},
            {"nombre": "C3 - Tomas CETAC/Schuko Monofásicas 16A", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 12, "cdt": 0.78, "norma": "ITC-BT-33"}
        ],
        "expediente": "EXP-OBRA-2026-01",
        "fecha": "04/10/2026"
    }
    pdf_bytes = pdf_memoria_tecnica.generar_pdf_mtd_industria_murcia(datos_obra)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 10000
    assert pdf_bytes.startswith(b"%PDF")

def test_generar_pdf_mtd_con_anexos_graficos_y_unifilar_personalizado():
    import io, base64
    from PIL import Image as PILImage
    
    # Crear imagen PNG simulada para planos
    im_dummy = PILImage.new('RGB', (400, 300), color='white')
    bio_dummy = io.BytesIO()
    im_dummy.save(bio_dummy, format='PNG')
    dummy_b64 = "data:image/png;base64," + base64.b64encode(bio_dummy.getvalue()).decode('utf-8')
    
    datos_anexos = {
        "tipo_instalacion": "🏡 Vivienda Unifamiliar / Piso Residencial (ITC-BT-25)",
        "tipo_tramitacion": "🆕 Nueva Instalación",
        "titular": {"nombre": "Beatriz Iriarte Quiroz", "nif": "34330049L"},
        "emplazamiento": {"direccion": "Calle Cruceta 11", "municipio": "Murcia", "cups": "ES0021000000000000XX", "uso": "Vivienda"},
        "instalador": {"empresa": "BOLIMUR", "nombre": "Richard Orlando Choque", "licencia": "REBT-30/15892"},
        "suministro": {"potencia_instalada_w": 9200, "tension": "Monofásico (230 V)"},
        "protecciones": {"iga_amperaje": 40},
        "circuitos": [],
        "expediente": "EXP-MUR-2026-001",
        "anexos": {
            "plano_situacion": dummy_b64,
            "plano_emplazamiento": dummy_b64,
            "plano_distribucion": dummy_b64,
            "unifilar_modo": "custom",
            "plano_unifilar_custom": dummy_b64
        }
    }
    pdf_bytes = pdf_memoria_tecnica.generar_pdf_mtd_industria_murcia(datos_anexos)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 12000
    assert pdf_bytes.startswith(b"%PDF")

def test_generar_pdf_mtd_con_tipo_en_blanco():
    datos_blanco = {
        "tipo_instalacion": "⚪ -- Seleccionar Tipo de Instalación (En Blanco) --",
        "tipo_tramitacion": "🆕 Nueva Instalación",
        "titular": {"nombre": "Cliente En Blanco", "nif": "12345678A"},
        "emplazamiento": {"direccion": "Calle de Prueba", "municipio": "Murcia", "uso": "Vivienda Unifamiliar"},
        "instalador": {"empresa": "BOLIMUR", "nombre": "Richard Orlando Choque", "licencia": "REBT-30/15892"},
        "suministro": {"potencia_instalada_w": 5750, "tension": "Monofásico (230 V)"},
        "protecciones": {"iga_amperaje": 25},
        "circuitos": [],
        "expediente": "EXP-BLANCO-2026"
    }
    pdf_bytes = pdf_memoria_tecnica.generar_pdf_mtd_industria_murcia(datos_blanco)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")



