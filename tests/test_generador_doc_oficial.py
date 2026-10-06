# -*- coding: utf-8 -*-
import pytest
from modulos import generador_doc_oficial

def test_generar_docx_oficial_dgeaim_murcia():
    datos_mtd = {
        "titular": {
            "nombre": "BEATRIZ IRIARTE QUIROZ",
            "nif": "34330049L",
            "telefono": "632587747",
            "email": "beita2005@gmail.com"
        },
        "emplazamiento": {
            "direccion": "CALLE CRUCETA 11",
            "cp": "30165",
            "municipio": "MURCIA (Rincón de Seca)",
            "cups": "ES0021000000000000XX",
            "uso": "Vivienda Residencial"
        },
        "instalador": {
            "empresa": "BOLIMUR INSTALACIONES Y REFORMAS",
            "cif": "B-73123456",
            "nombre": "Richard Orlando Choque Tejerina",
            "licencia": "REBT-30/15892",
            "registro_rii": "RII-30/08492",
            "telefono": "632676824"
        },
        "suministro": {
            "potencia_instalada_w": 9200.0,
            "potencia_max_admisible_w": 9200.0,
            "tension": "Monofásico (230 V) - 50 Hz",
            "di_cable": "2x16 mm² Cu + TT 1x16 mm² RZ1-K 0.6/1kV (AS)",
            "di_tubo": "Tubo M40 libre de halógenos",
            "di_long_m": 18.0,
            "di_cdt_pct": 0.85,
            "grado_electrif": "Elevada"
        },
        "protecciones": {
            "iga_amperaje": 40,
            "iga_curva": "Curva C",
            "iga_icn_ka": 6.0,
            "diferenciales": "2 x 40A / 30mA",
            "sobretensiones": "VTP + DPS Tipo 2"
        },
        "ensayos": {
            "rt_ohm": 11.8
        },
        "circuitos": [
            {"nombre": "C1 - Alumbrado", "potencia": 2300, "pia": 10, "seccion": "2x1.5+TT1.5", "tubo": "M20", "longitud": 18, "cdt": 1.15, "norma": "ITC-BT-25"},
            {"nombre": "C2 - Tomas", "potencia": 3450, "pia": 16, "seccion": "2x2.5+TT2.5", "tubo": "M20", "longitud": 20, "cdt": 1.42, "norma": "ITC-BT-25"},
            {"nombre": "C3 - Cocina/Horno", "potencia": 5400, "pia": 25, "seccion": "2x6+TT6", "tubo": "M25", "longitud": 12, "cdt": 0.88, "norma": "ITC-BT-25"},
            {"nombre": "C9 - Climatización", "potencia": 5750, "pia": 25, "seccion": "2x6+TT6", "tubo": "M25", "longitud": 15, "cdt": 1.10, "norma": "ITC-BT-25"}
        ],
        "anexos": {}
    }

    docx_bytes = generador_doc_oficial.generar_docx_oficial_dgeaim_murcia(datos_mtd)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 50000
    # ZIP / DOCX magic bytes: PK
    assert docx_bytes.startswith(b"PK")


def test_generar_docx_oficial_con_nulos():
    """Verifica que campos nulos en datos_mtd no produzcan errores AttributeError: 'NoneType' object has no attribute 'strip'"""
    datos_con_nulos = {
        "titular": {"nombre": None, "nif": None, "telefono": None, "email": None},
        "emplazamiento": {"direccion": None, "cp": None, "municipio": None, "cups": None, "uso": None},
        "instalador": {"empresa": None, "cif": None, "nombre": None, "licencia": None, "registro_rii": None, "telefono": None},
        "suministro": {"potencia_instalada_w": None, "tension": None, "di_cable": None, "di_tubo": None, "di_long_m": None, "di_cdt_pct": None, "grado_electrif": None},
        "protecciones": {"iga_amperaje": None},
        "ensayos": {"rt_ohm": None},
        "circuitos": [{"nombre": None, "potencia": None, "seccion": None, "tubo": None, "longitud": None, "cdt": None}],
        "anexos": {}
    }
    docx_bytes = generador_doc_oficial.generar_docx_oficial_dgeaim_murcia(datos_con_nulos)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 50000
    assert docx_bytes.startswith(b"PK")


def test_convertir_docx_a_pdf():
    """Verifica la función de conversión Word COM a PDF oficial."""
    datos_basicos = {}
    docx_bytes = generador_doc_oficial.generar_docx_oficial_dgeaim_murcia(datos_basicos)
    pdf_bytes = generador_doc_oficial.convertir_docx_a_pdf(docx_bytes)
    if pdf_bytes is not None:
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")


def test_generar_docx_con_planos_y_casillas():
    """Verifica que los planos se inserten sin errores y que las casillas no se solapen."""
    import io, base64, docx
    from PIL import Image

    im = Image.new('RGB', (1200, 900), color='lightblue')
    bio = io.BytesIO()
    im.save(bio, format='JPEG')
    b64_dummy = "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode('utf-8')

    datos = {
        "tipo_tramitacion": "Nueva Instalación",
        "emplazamiento": {"uso": "Vivienda Residencial"},
        "suministro": {"tension": "Monofásico 230 V", "potencia_instalada_w": 5750.0},
        "anexos": {
            "plano_situacion": b64_dummy,
            "plano_emplazamiento": b64_dummy,
            "plano_distribucion": b64_dummy,
        }
    }

    docx_bytes = generador_doc_oficial.generar_docx_oficial_dgeaim_murcia(datos)
    assert isinstance(docx_bytes, bytes)
    assert docx_bytes.startswith(b"PK")

    doc = docx.Document(io.BytesIO(docx_bytes))
    t0 = doc.tables[0]

    # Verificar que fila 19 tiene separadas las celdas
    c0_txt = t0.rows[19].cells[0].text
    c4_txt = t0.rows[19].cells[4].text
    assert "[X] Nueva" in c0_txt
    assert "Ampliación" in c4_txt
    assert "Modificación" in c4_txt
    # Verificar que no hay duplicación de Ampliación en c0
    assert "Ampliación" not in c0_txt


def test_generar_docx_anexo_iii_iv_v():
    """Verifica que Anexo III (unifilar dinámico), Anexo IV (cálculos trifásicos) y Anexo V (fotos) se generen correctamente en el Word."""
    import io, base64, docx
    from PIL import Image

    # Crear imagen dummy para fotos de Anexo V
    im = Image.new('RGB', (800, 600), color='forestgreen')
    bio = io.BytesIO()
    im.save(bio, format='JPEG')
    b64_foto = "data:image/jpeg;base64," + base64.b64encode(bio.getvalue()).decode('utf-8')

    datos = {
        "titular": {"nombre": "TEST TRIFASICO", "nif": "12345678Z"},
        "suministro": {
            "tension": "Trifásico (400 V) - 50 Hz",
            "potencia_instalada_w": 15000.0,
            "potencia_max_admisible_w": 15000.0,
            "di_cable": "4x10 mm² Cu + TT 1x10 mm² RZ1-K (AS)",
            "di_tubo": "Tubo M40",
            "di_long_m": 25.0,
            "di_cdt_pct": 0.95
        },
        "circuitos": [
            {"nombre": "C1 - Alumbrado", "potencia": 2000, "pia": 10, "seccion": "1.5", "tubo": "M20", "longitud": 15, "cdt": 1.2},
            {"nombre": "C2 - Fuerza Trifásica", "potencia": 6000, "pia": 16, "seccion": "4x2.5", "tubo": "M25", "longitud": 20, "cdt": 1.5}
        ],
        "anexos": {
            "fotos": [
                {"titulo": "Cuadro General Instalado", "data": b64_foto},
                {"titulo": "Canalización de suelo", "data": b64_foto}
            ]
        }
    }

    docx_bytes = generador_doc_oficial.generar_docx_oficial_dgeaim_murcia(datos)
    assert isinstance(docx_bytes, bytes)
    assert docx_bytes.startswith(b"PK")

    doc = docx.Document(io.BytesIO(docx_bytes))

    # Verificar Tabla 12 (Anexo IV Tramos)
    t12 = doc.tables[12]
    # Fila 12 debe tener DI A-B
    txt_di = t12.rows[12].cells[0].text
    assert "A-B" in txt_di
    # Fila 12 intensidad DI debe calcularse con sqrt(3)*400: 15000 / (1.73205 * 400) = 21.65 A
    i_di = t12.rows[12].cells[8].text.strip()
    assert float(i_di) == pytest.approx(21.65, abs=0.1)

    # Verificar Anexo V (párrafos de fotos)
    doc_text = "\n".join([p.text for p in doc.paragraphs])
    assert "ANEXO V: REPORTAJE FOTOGRÁFICO" in doc_text
    assert "Cuadro General Instalado" in doc_text
    assert "Canalización de suelo" in doc_text


def test_descripcion_instalacion_personalizada():
    """Verifica que la Breve Descripción de la Instalación personalizada aparezca en la Tabla 2 fila 33 del Word oficial."""
    import io, docx
    desc_test = "REFORMA ELECTRICA INTEGRAL EN LOCAL DESTINADO A PANADERIA-CAFETERIA CON HORNO TRIFASICO."
    datos = {
        "titular": {"nombre": "TEST LOCAL"},
        "descripcion_instalacion": desc_test,
        "suministro": {"potencia_instalada_w": 18000.0, "tension": "Trifásico 400 V"}
    }
    docx_bytes = generador_doc_oficial.generar_docx_oficial_dgeaim_murcia(datos)
    assert isinstance(docx_bytes, bytes)
    doc = docx.Document(io.BytesIO(docx_bytes))
    t2 = doc.tables[2]
    # Fila 33 contiene la breve descripción
    assert desc_test in t2.rows[33].cells[0].text




