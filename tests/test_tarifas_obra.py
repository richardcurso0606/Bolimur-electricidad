"""
Tests para el módulo modulos.tarifas_obra:
Cálculos de calle, REBT ITC-BT-15 y rentabilidad de Derivaciones Individuales.
"""
import pytest
from modulos import tarifas_obra as to

def test_calculo_seccion_di_tecnica_basica():
    res = to.calcular_seccion_di_tecnica(potencia_w=5750.0, longitud_m=18.0, es_trifasico=False)
    assert res["seccion_fase"] in [10.0, 16.0]
    assert res["seccion_pe"] >= 10.0
    assert "40" in res["tubo_diam"] or "32" in res["tubo_diam"]
    assert res["cumple_normativa"] is True

def test_calculo_seccion_di_tecnica_elevada():
    res = to.calcular_seccion_di_tecnica(potencia_w=9200.0, longitud_m=18.0, es_trifasico=False)
    assert res["seccion_fase"] in [10.0, 16.0]
    assert res["in_iga"] == 40
    assert res["cumple_normativa"] is True

def test_escandallo_coste_di():
    coste = to.calcular_escandallo_coste_di(
        longitud_m=18.0,
        seccion_fase=10.0,
        metodo_montaje="superficie",
        es_obra=False,
        precio_hora=25.0
    )
    assert coste["coste_materiales"] > 0
    assert coste["horas_mo"] > 0
    assert coste["coste_directo_total"] == round(coste["coste_materiales"] + coste["coste_mo"], 2)

def test_cotizar_tarifa_calle_di():
    cot = to.cotizar_tarifa_calle_di(
        longitud_m=18.0,
        potencia_w=5750.0,
        metodo_montaje="superficie",
        es_obra=False,
        precio_base_20m=225.0
    )
    assert cot["pvp_venta_neto"] >= 200.0
    assert "semaforo" in cot
    assert "diagnostico" in cot
    assert cot["beneficio_neto"] == round(cot["pvp_venta_neto"] - cot["coste"]["coste_directo_total"], 2)

def test_generar_partida_presupuesto_di():
    cot = to.cotizar_tarifa_calle_di(longitud_m=18.0, potencia_w=5750.0)
    partida = to.generar_partida_presupuesto_di(cot)
    assert "Derivación Individual" in partida["concepto"]
    assert "RZ1-K" in partida["descripcion"]
    assert partida["subtotal"] == cot["pvp_venta_neto"]
