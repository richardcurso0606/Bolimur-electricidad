# -*- coding: utf-8 -*-
"""
Suite de Pruebas Automatizadas para Cálculos Eléctricos y Normativa REBT
Verifica el cumplimiento de fórmulas, constantes, límites y sincronización.
"""

import math
import pytest
from modulos import rebt_tablas as rebt
from modulos import prevision_cargas
from modulos import presupuesto_vivienda


class TestConductividadesYResistividades:
    """Verifica los valores oficiales de conductividad y resistividad."""
    
    def test_conductividad_cobre_xlpe(self):
        gamma = rebt.obtener_gamma("cobre", "XLPE / EPR (90ºC)")
        assert gamma == 44.0
        rho = rebt.obtener_rho("cobre", "XLPE / EPR (90ºC)")
        assert pytest.approx(rho, rel=1e-3) == 1.0 / 44.0

    def test_conductividad_cobre_pvc(self):
        gamma = rebt.obtener_gamma("cobre", "PVC (70ºC)")
        assert gamma == 48.5
        rho = rebt.obtener_rho("cobre", "PVC (70ºC)")
        assert pytest.approx(rho, rel=1e-3) == 1.0 / 48.5

    def test_conductividad_aluminio_xlpe(self):
        gamma = rebt.obtener_gamma("aluminio", "XLPE / EPR (90ºC)")
        assert gamma == 28.0
        rho = rebt.obtener_rho("aluminio", "XLPE / EPR (90ºC)")
        assert pytest.approx(rho, rel=1e-3) == 1.0 / 28.0

    def test_conductividad_aluminio_pvc(self):
        gamma = rebt.obtener_gamma("aluminio", "PVC (70ºC)")
        assert gamma == 31.0
        rho = rebt.obtener_rho("aluminio", "PVC (70ºC)")
        assert pytest.approx(rho, rel=1e-3) == 1.0 / 31.0


class TestCaidaTensionYCorriente:
    """Verifica que las fórmulas de caída de tensión y corriente sean matemáticamente exactas."""

    def test_intensidad_monofasica(self):
        # P = 5750 W, V = 230 V, cos phi = 1.0 -> Ib = 25.0 A
        ib = rebt.calcular_intensidad_diseno(5750.0, 230.0, cos_phi=1.0, es_trifasico=False)
        assert pytest.approx(ib, rel=1e-3) == 25.0

    def test_intensidad_trifasica(self):
        # P = 15000 W, V = 400 V, cos phi = 0.9 -> Ib = 15000 / (sqrt(3) * 400 * 0.9) = 24.056 A
        ib = rebt.calcular_intensidad_diseno(15000.0, 400.0, cos_phi=0.9, es_trifasico=True)
        esperado = 15000.0 / (math.sqrt(3) * 400.0 * 0.9)
        assert pytest.approx(ib, rel=1e-3) == esperado

    def test_caida_tension_monofasica(self):
        # ΔV = (2 * P * L) / (γ * S * V)
        # P = 5750 W, L = 20 m, γ = 44, S = 6 mm², V = 230 V
        # ΔV = (2 * 5750 * 20) / (44 * 6 * 230) = 230000 / 60720 ≈ 3.78788 V
        dv_v = rebt.calcular_caida_tension_v(5750.0, 20.0, 44.0, 6.0, 230.0, es_trifasico=False)
        assert pytest.approx(dv_v, rel=1e-3) == 3.78788
        
        dv_pct = rebt.calcular_caida_tension_pct(dv_v, 230.0)
        assert pytest.approx(dv_pct, rel=1e-3) == (3.78788 / 230.0) * 100.0

    def test_caida_tension_trifasica_sin_sqrt3(self):
        """
        Prueba fundamental: Comprobar que en trifásica NO se multiplica por sqrt(3).
        ΔV = (1 * P * L) / (γ * S * V)
        """
        # P = 22000 W, L = 30 m, γ = 44, S = 10 mm², V = 400 V
        # ΔV = (22000 * 30) / (44 * 10 * 400) = 660000 / 176000 = 3.75 V
        dv_v = rebt.calcular_caida_tension_v(22000.0, 30.0, 44.0, 10.0, 400.0, es_trifasico=True)
        assert pytest.approx(dv_v, rel=1e-3) == 3.75
        
        dv_pct = rebt.calcular_caida_tension_pct(dv_v, 400.0)
        assert pytest.approx(dv_pct, rel=1e-3) == (3.75 / 400.0) * 100.0  # 0.9375%


class TestIntensidadesAdmisiblesIz:
    """Verifica coherencia técnica en tablas Iz según UNE-HD 60364-5-52."""

    def test_cobre_admite_mas_que_aluminio(self):
        iz_cu = rebt.obtener_iz("cobre", "XLPE", "tubo", 25.0)
        iz_al = rebt.obtener_iz("aluminio", "XLPE", "tubo", 25.0)
        assert iz_cu > iz_al
        assert iz_cu == 101.0
        assert iz_al == 77.0

    def test_xlpe_admite_mas_que_pvc(self):
        iz_xlpe = rebt.obtener_iz("cobre", "XLPE", "tubo", 16.0)
        iz_pvc = rebt.obtener_iz("cobre", "PVC", "tubo", 16.0)
        assert iz_xlpe > iz_pvc
        assert iz_xlpe == 76.0
        assert iz_pvc == 61.0

    def test_enterrado_admite_mas_que_aire_a_misma_seccion(self):
        iz_tubo = rebt.obtener_iz("cobre", "XLPE", "tubo", 10.0)
        iz_enterrado = rebt.obtener_iz("cobre", "XLPE", "enterrado", 10.0)
        assert iz_enterrado > iz_tubo


class TestSeccionesMinimasYTubosReglamentarios:
    """Verifica los mínimos obligatorios fijados por el REBT."""

    def test_seccion_minima_di_es_6mm2(self):
        s_opt = rebt.seleccionar_seccion_optima(1.5, material="cobre", s_minima=6.0)
        assert s_opt >= 6.0

    def test_seccion_minima_lga_cobre_es_10mm2(self):
        s_opt = rebt.seleccionar_seccion_optima(4.0, material="cobre", s_minima=10.0)
        assert s_opt >= 10.0

    def test_seccion_minima_lga_aluminio_es_16mm2(self):
        s_opt = rebt.seleccionar_seccion_optima(10.0, material="aluminio", s_minima=16.0)
        assert s_opt >= 16.0

    def test_tubo_minimo_di_es_32mm(self):
        diam, razon = rebt.dimensionar_tubo_di(6.0)
        assert "32" in diam

    def test_tubo_minimo_lga_es_110mm(self):
        diam, razon = rebt.dimensionar_tubo_lga(16.0)
        assert "110" in diam
        diam_50, _ = rebt.dimensionar_tubo_lga(50.0)
        assert "140" in diam_50


class TestPrevisionCargasITCBT10:
    """Verifica coeficientes de simultaneidad y criterios ITC-BT-10 e ITC-BT-52."""

    def test_coeficiente_k_tabla_oficial(self):
        assert prevision_cargas.get_coef_simultaneidad(1) == 1.0
        assert prevision_cargas.get_coef_simultaneidad(2) == 2.0
        assert prevision_cargas.get_coef_simultaneidad(3) == 3.0
        assert prevision_cargas.get_coef_simultaneidad(4) == 3.8
        assert prevision_cargas.get_coef_simultaneidad(10) == 8.5
        assert prevision_cargas.get_coef_simultaneidad(20) == 15.4

    def test_coeficiente_k_mas_de_20_viviendas(self):
        # K = 15.4 + (n - 20) * 0.5
        k_25 = prevision_cargas.get_coef_simultaneidad(25)
        esperado_25 = 15.4 + (25 - 20) * 0.5  # 15.4 + 2.5 = 17.9
        assert pytest.approx(k_25, rel=1e-3) == esperado_25

        k_30 = prevision_cargas.get_coef_simultaneidad(30)
        esperado_30 = 15.4 + (30 - 20) * 0.5  # 15.4 + 5.0 = 20.4
        assert pytest.approx(k_30, rel=1e-3) == esperado_30


class TestPresupuestoExcel:
    """Verifica carga con caché y exportación de presupuestos a Excel."""

    def test_carga_excel_precios(self):
        df, nombre = presupuesto_vivienda.cargar_precios_excel()
        assert df is not None
        assert len(df) > 0
        assert "Precio S/IVA (€)" in df.columns or "Precio" in str(df.columns)

    def test_exportacion_excel_bytes(self):
        df_ejemplo = presupuesto_vivienda.pd.DataFrame([
            {"Estancia": "Salón", "Superficie": "25 m²", "Importe Venta (€)": 1250.00}
        ])
        excel_bytes = presupuesto_vivienda.exportar_excel_presupuesto(
            df_ejemplo, 1250.0, 10, 125.0, 1375.0, {"empresa": "Bolimur"}
        )
        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 100
        # Validar cabecera de archivo ZIP / XLSX (PK..)
        assert excel_bytes[:2] == b'PK'


class TestREBTFuncionesAvanzadas:
    """Pruebas para coordinación térmica, tierras, cortocircuito y factores."""

    def test_dimensionar_conductor_pe(self):
        # Sfase <= 16 -> Spe = Sfase
        assert rebt.dimensionar_conductor_pe(1.5) == 1.5
        assert rebt.dimensionar_conductor_pe(2.5) == 2.5
        assert rebt.dimensionar_conductor_pe(6.0) == 6.0
        assert rebt.dimensionar_conductor_pe(10.0) == 10.0
        assert rebt.dimensionar_conductor_pe(16.0) == 16.0
        # 16 < Sfase <= 35 -> Spe = 16
        assert rebt.dimensionar_conductor_pe(25.0) == 16.0
        assert rebt.dimensionar_conductor_pe(35.0) == 16.0
        # Sfase > 35 -> Spe = Sfase / 2 normalizada
        assert rebt.dimensionar_conductor_pe(50.0) == 25.0
        assert rebt.dimensionar_conductor_pe(70.0) == 35.0
        assert rebt.dimensionar_conductor_pe(95.0) == 50.0

    def test_verificar_coordinacion_proteccion(self):
        # Caso correcto: Ib (28A) <= In (32A) <= Iz (41A)
        res_ok = rebt.verificar_coordinacion_proteccion(28.0, 32.0, 41.0)
        assert res_ok["cumple"] is True

        # Caso incorrecto por In < Ib: Ib (35A) > In (32A)
        res_falla_ib = rebt.verificar_coordinacion_proteccion(35.0, 32.0, 41.0)
        assert res_falla_ib["cumple"] is False
        assert res_falla_ib["cumple_ib_in"] is False

        # Caso peligro térmico: In (50A) > Iz (41A)
        res_falla_iz = rebt.verificar_coordinacion_proteccion(28.0, 50.0, 41.0)
        assert res_falla_iz["cumple"] is False
        assert res_falla_iz["cumple_in_iz"] is False

    def test_verificar_cortocircuito_cable(self):
        # 6 kA, 0.05s, 10mm² Cu XLPE (k=143)
        cumple, s_min = rebt.verificar_cortocircuito_cable(6.0, 0.05, 10.0, "cobre", "xlpe")
        assert s_min < 10.0
        assert cumple is True

    def test_factores_correccion(self):
        f_temp_40 = rebt.obtener_factor_temperatura(40.0, "xlpe")
        assert f_temp_40 == 1.00
        f_temp_50 = rebt.obtener_factor_temperatura(50.0, "xlpe")
        assert f_temp_50 == 0.90

        f_agrup_1 = rebt.obtener_factor_agrupamiento(1)
        assert f_agrup_1 == 1.00
        f_agrup_2 = rebt.obtener_factor_agrupamiento(2)
        assert f_agrup_2 == 0.80


class TestTablasNormativas:
    """Verifica el módulo de tablas normativas, buscador e índice."""

    def test_categorias_e_indice(self):
        from modulos import tablas_normativas
        assert len(tablas_normativas.CATEGORIAS_TABLAS) >= 7
        # Verificar que todos los IDs tienen título asignado
        for cat, lista_ids in tablas_normativas.CATEGORIAS_TABLAS.items():
            assert len(lista_ids) > 0
            for tid in lista_ids:
                tit = tablas_normativas._obtener_titulo_tabla(tid)
                assert isinstance(tit, str)
                assert len(tit) > 5

    def test_buscador_tablas(self):
        from modulos import tablas_normativas
        res_iz = tablas_normativas._buscar_tablas("temperatura")
        assert len(res_iz) > 0
        assert "tab_factores_temperatura" in res_iz

        res_irve = tablas_normativas._buscar_tablas("irve")
        assert len(res_irve) > 0
        assert "tab_esquemas_irve_bt52" in res_irve


