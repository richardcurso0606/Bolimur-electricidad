# -*- coding: utf-8 -*-
"""
Módulo Oficial de Constantes, Tablas y Fórmulas del REBT (Real Decreto 842/2002)
Normas UNE-HD 60364-5-52, UNE 20460-5-523, ITC-BT-10, ITC-BT-14, ITC-BT-15, ITC-BT-19, ITC-BT-21, ITC-BT-52.
"""

import math

# =========================================================================
# 1. CONDUCTIVIDAD (γ) Y RESISTIVIDAD (ρ) SEGÚN TEMPERATURA DE SERVICIO
# =========================================================================
# Valores oficiales a máxima temperatura de servicio en régimen permanente:
# - XLPE / EPR: 90 ºC
# - PVC: 70 ºC
CONDUCTIVIDADES = {
    ("cobre", "xlpe"): 44.0,      # m / (Ω · mm²)
    ("cobre", "pvc"): 48.5,       # m / (Ω · mm²)
    ("aluminio", "xlpe"): 28.0,   # m / (Ω · mm²)
    ("aluminio", "pvc"): 31.0     # m / (Ω · mm²)
}

def obtener_gamma(material: str, aislamiento: str) -> float:
    mat = "aluminio" if "alum" in material.lower() else "cobre"
    aisl = "xlpe" if ("xlpe" in aislamiento.lower() or "epr" in aislamiento.lower() or "90" in aislamiento) else "pvc"
    return CONDUCTIVIDADES.get((mat, aisl), 44.0)

def obtener_rho(material: str, aislamiento: str) -> float:
    gamma = obtener_gamma(material, aislamiento)
    return 1.0 / gamma if gamma > 0 else 0.0227

# =========================================================================
# 2. SECCIONES COMERCIALES NORMALIZADAS (mm²)
# =========================================================================
SECCIONES_COMERCIALES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
SECCIONES_ALUMINIO = [10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

def obtener_secciones_disponibles(material: str) -> list:
    if "alum" in material.lower():
        return list(SECCIONES_ALUMINIO)
    return list(SECCIONES_COMERCIALES)

def seleccionar_seccion_optima(s_necesaria: float, material: str = "cobre", s_minima: float = 1.5) -> float:
    secciones = obtener_secciones_disponibles(material)
    s_objetivo = max(s_necesaria, s_minima)
    for sec in secciones:
        if sec >= s_objetivo:
            return sec
    return secciones[-1]

# =========================================================================
# 3. CALIBRES NORMALIZADOS DE PROTECCIONES (A)
# =========================================================================
CALIBRES_PIAS = [6, 10, 16, 20, 25, 32, 40, 50, 63]
CALIBRES_INTERRUPTORES_GENERALES = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630]

def seleccionar_proteccion(ib: float, tipo: str = "pia") -> int:
    calibres = CALIBRES_PIAS if tipo == "pia" else CALIBRES_INTERRUPTORES_GENERALES
    for cal in calibres:
        if cal >= ib:
            return cal
    return calibres[-1]

# =========================================================================
# 4. TABLAS DE INTENSIDADES ADMISIBLES (Iz) - UNE-HD 60364-5-52 / ITC-BT-19
# =========================================================================
# Temperatura ambiente de referencia: 40 ºC al aire, 25 ºC enterrado.
TABLAS_IZ = {
    # COBRE - Tubo empotrado o en superficie (B1 / B2)
    ("cobre", "pvc", "tubo"): {
        1.5: 14.5, 2.5: 20.0, 4: 26.0, 6: 34.0, 10: 46.0, 16: 61.0,
        25: 80.0, 35: 99.0, 50: 119.0, 70: 151.0, 95: 182.0, 120: 210.0,
        150: 240.0, 185: 275.0, 240: 320.0
    },
    ("cobre", "xlpe", "tubo"): {
        1.5: 17.5, 2.5: 24.0, 4: 32.0, 6: 41.0, 10: 57.0, 16: 76.0,
        25: 101.0, 35: 125.0, 50: 151.0, 70: 192.0, 95: 232.0, 120: 269.0,
        150: 300.0, 185: 341.0, 240: 400.0
    },
    # COBRE - Enterrado bajo tubo (Método D)
    ("cobre", "pvc", "enterrado"): {
        1.5: 22.0, 2.5: 29.0, 4: 38.0, 6: 48.0, 10: 65.0, 16: 85.0,
        25: 110.0, 35: 135.0, 50: 160.0, 70: 170.0, 95: 202.0, 120: 230.0,
        150: 270.0, 185: 310.0, 240: 360.0
    },
    ("cobre", "xlpe", "enterrado"): {
        1.5: 26.0, 2.5: 34.0, 4: 44.0, 6: 56.0, 10: 75.0, 16: 98.0,
        25: 128.0, 35: 157.0, 50: 185.0, 70: 230.0, 95: 275.0, 120: 315.0,
        150: 355.0, 185: 400.0, 240: 460.0
    },
    # ALUMINIO - Tubo empotrado o superficie (B1 / B2)
    ("aluminio", "pvc", "tubo"): {
        10: 36.0, 16: 48.0, 25: 62.0, 35: 77.0, 50: 93.0, 70: 118.0,
        95: 142.0, 120: 164.0, 150: 189.0, 185: 215.0, 240: 252.0
    },
    ("aluminio", "xlpe", "tubo"): {
        10: 44.0, 16: 58.0, 25: 77.0, 35: 96.0, 50: 117.0, 70: 149.0,
        95: 180.0, 120: 208.0, 150: 236.0, 185: 268.0, 240: 315.0
    },
    # ALUMINIO - Enterrado bajo tubo (Método D)
    ("aluminio", "pvc", "enterrado"): {
        10: 50.0, 16: 66.0, 25: 85.0, 35: 105.0, 50: 124.0, 70: 132.0,
        95: 157.0, 120: 179.0, 150: 210.0, 185: 240.0, 240: 280.0
    },
    ("aluminio", "xlpe", "enterrado"): {
        10: 58.0, 16: 76.0, 25: 99.0, 35: 121.0, 50: 143.0, 70: 178.0,
        95: 213.0, 120: 244.0, 150: 275.0, 185: 310.0, 240: 356.0
    }
}

def obtener_tabla_iz(material: str, aislamiento: str, metodo: str) -> dict:
    mat = "aluminio" if "alum" in material.lower() else "cobre"
    aisl = "xlpe" if ("xlpe" in aislamiento.lower() or "epr" in aislamiento.lower() or "90" in aislamiento) else "pvc"
    met = "enterrado" if ("d (" in metodo.lower() or "subterrá" in metodo.lower() or "enterrado" in metodo.lower()) else "tubo"
    return TABLAS_IZ.get((mat, aisl, met), TABLAS_IZ[("cobre", "xlpe", "tubo")])

def obtener_iz(material: str, aislamiento: str, metodo: str, seccion: float) -> float:
    tabla = obtener_tabla_iz(material, aislamiento, metodo)
    return tabla.get(seccion, 0.0)

# =========================================================================
# 5. FÓRMULAS DE CÁLCULO ELÉCTRICO REGLAMENTARIAS
# =========================================================================

def calcular_intensidad_diseno(potencia: float, tension: float, cos_phi: float = 1.0, es_trifasico: bool = False) -> float:
    """
    Monofásica: Ib = P / (V * cos phi)
    Trifásica:   Ib = P / (sqrt(3) * V * cos phi)
    """
    if tension <= 0 or cos_phi <= 0:
        return 0.0
    if es_trifasico:
        return potencia / (math.sqrt(3) * tension * cos_phi)
    return potencia / (tension * cos_phi)

def calcular_caida_tension_v(potencia: float, longitud: float, gamma: float, seccion: float, tension: float, es_trifasico: bool = False) -> float:
    """
    Monofásica: ΔV = (2 * P * L) / (γ * S * V)
    Trifásica:   ΔV = (1 * P * L) / (γ * S * V)   <-- ¡Factor 1.0, NO sqrt(3)!
    """
    denom = gamma * seccion * tension
    if denom <= 0:
        return 0.0
    k_circuito = 1.0 if es_trifasico else 2.0
    return (k_circuito * potencia * longitud) / denom

def calcular_caida_tension_pct(dv_volts: float, tension: float) -> float:
    if tension <= 0:
        return 0.0
    return (dv_volts / tension) * 100.0

def calcular_seccion_por_cdt(potencia: float, longitud: float, gamma: float, cdt_lim_pct: float, tension: float, es_trifasico: bool = False) -> float:
    """
    Monofásica: S = (2 * P * L) / (γ * ΔV_max * V)
    Trifásica:   S = (1 * P * L) / (γ * ΔV_max * V)
    """
    dv_max_v = tension * (cdt_lim_pct / 100.0)
    denom = gamma * dv_max_v * tension
    if denom <= 0:
        return 1.5
    k_circuito = 1.0 if es_trifasico else 2.0
    return (k_circuito * potencia * longitud) / denom

def calcular_icc_final(tension: float, icc_origen_ka: float, longitud: float, seccion: float, gamma: float, es_trifasico: bool = False) -> tuple[float, float, float]:
    """
    Calcula la corriente de cortocircuito francamente derivada al final de la línea.
    Retorna: (icc_final_a, z_origen, r_cable_total)
    """
    if icc_origen_ka <= 0 or seccion <= 0 or gamma <= 0:
        return 0.0, 0.0, 0.0
    
    # Impedancia origen aproximada (fase-neutro o fase-fase)
    z_origen = tension / (icc_origen_ka * 1000.0)
    rho = 1.0 / gamma
    r_unitaria = (rho * longitud) / seccion
    r_total = r_unitaria if es_trifasico else (2.0 * r_unitaria)
    z_total = z_origen + r_total
    
    icc_final = (tension / z_total) if z_total > 0 else 0.0
    return icc_final, z_origen, r_total

# =========================================================================
# 6. DIMENSIONAMIENTO REGLAMENTARIO DE TUBOS PROTECTORES
# =========================================================================

def dimensionar_tubo_di(seccion: float) -> tuple[str, str]:
    """
    ITC-BT-15 apartado 3:
    Diámetro nominal exterior mínimo para cualquier Derivación Individual: 32 mm.
    Permite ampliación del 100%.
    """
    if seccion <= 6:
        return "Ø 32 mm", "Mínimo reglamentario absoluto por ITC-BT-15 (reserva de ampliación del 100%)."
    elif seccion <= 16:
        return "Ø 40 mm", "Exigido por ITC-BT-15 para secciones de 10 y 16 mm² en suministros elevados."
    elif seccion <= 35:
        return "Ø 50 mm", "Necesario para conductores de 25 y 35 mm² garantizando el factor de llenado."
    else:
        return "Ø 63 mm o Canaladura / Bandeja", "Gran calibre para conductores pesados en derivaciones singulares."

def dimensionar_tubo_lga(seccion: float) -> tuple[str, str]:
    """
    ITC-BT-14 Tabla 1:
    Diámetros exteriores nominales mínimos de tubos en LGA (3F + N + PE).
    Mínimo absoluto: 110 mm.
    """
    if seccion <= 25:
        return "Ø 110 mm", "Mínimo reglamentario por ITC-BT-14 Tabla 1 para LGA (reserva de ampliación del 100%)."
    elif seccion <= 35:
        return "Ø 125 mm", "Reglamentario para 35 mm² según ITC-BT-14 Tabla 1."
    elif seccion <= 70:
        return "Ø 140 mm", "Reglamentario para 50 y 70 mm² según ITC-BT-14 Tabla 1."
    elif seccion <= 120:
        return "Ø 160 mm", "Reglamentario para 95 y 120 mm² según ITC-BT-14 Tabla 1."
    elif seccion <= 150:
        return "Ø 180 mm", "Reglamentario para 150 mm² según ITC-BT-14 Tabla 1."
    elif seccion <= 185:
        return "Ø 200 mm", "Reglamentario para 185 mm² según ITC-BT-14 Tabla 1."
    elif seccion <= 240:
        return "Ø 225 mm", "Reglamentario para 240 mm² según ITC-BT-14 Tabla 1."
    else:
        return "Bandeja técnica / Canaladura de obra", "Obligatorio canal o bandeja registrable por rigidez extrema del cable."

def dimensionar_tubo_interior(seccion: float) -> tuple[str, str]:
    """
    ITC-BT-21: Circuitos interiores / cálculo rápido general.
    """
    if seccion <= 2.5:
        return "Ø 20 mm", "Adecuado para circuitos interiores de alumbrado y tomas C1/C2."
    elif seccion <= 6:
        return "Ø 25 mm", "Requerido para circuitos de fuerza de 4 y 6 mm² (cocina/horno C3, lavadora C4)."
    elif seccion <= 16:
        return "Ø 32 mm o Ø 40 mm", "Para circuitos de climatización, bombas de calor o subcuadros."
    elif seccion <= 35:
        return "Ø 50 mm", "Para acometidas secundarias y factores de llenado de 30-40%."
    else:
        return "Ø 63 mm o superior", "Para alimentaciones principales de gran potencia."

def dimensionar_tubo_irve(seccion: float, es_trifasico: bool = False) -> tuple[str, str]:
    """
    ITC-BT-52 apartado 5 y Guía Técnica de Aplicación:
    Tubos para canalizaciones de recarga IRVE (con protección IK08 y libre de halógenos).
    Se recomienda prever espacio para el cable de comunicaciones del balanceo dinámico de carga.
    """
    if seccion <= 4.0:
        return "Ø 25 mm o Ø 32 mm", "Reglamentario para 2.5 y 4 mm² (Ø 32 mm recomendado si incluye manguera de datos/balanceo)."
    elif seccion <= 6.0:
        return "Ø 32 mm", "Estándar reglamentario para 6 mm² (7.36 kW / 32A monofásico) con protección mecánica IK08."
    elif seccion <= 16.0:
        return "Ø 40 mm", "Exigido para 10 y 16 mm² (11 kW / 22 kW trifásicos) garantizando disipación térmica y tirada."
    elif seccion <= 35.0:
        return "Ø 50 mm", "Para conductores de 25 y 35 mm² en derivaciones colectivas o largas distancias."
    else:
        return "Ø 63 mm o Bandeja metálica/PVC libre de halógenos", "Para grandes acometidas o canalizaciones troncales multitubo."

# =========================================================================
# 7. CONDUCTORES DE PROTECCIÓN (PE) Y TIERRAS - ITC-BT-19 TABLA 2
# =========================================================================

def dimensionar_conductor_pe(seccion_fase: float) -> float:
    """
    ITC-BT-19 Tabla 2: Sección mínima de conductores de protección (PE):
    - Sfase <= 16 mm²   -->  Spe = Sfase
    - 16 < Sfase <= 35  -->  Spe = 16 mm²
    - Sfase > 35 mm²    -->  Spe = Sfase / 2
    """
    if seccion_fase <= 16:
        return float(seccion_fase)
    elif seccion_fase <= 35:
        return 16.0
    else:
        # Seleccionar sección normalizada inmediatamente superior a Sfase / 2
        s_half = seccion_fase / 2.0
        for s in SECCIONES_COMERCIALES:
            if s >= s_half:
                return float(s)
        return float(s_half)

# =========================================================================
# 8. COORDINACIÓN DE PROTECCIÓN TÉRMICA - ITC-BT-19 / UNE-HD 60364-4-43
# =========================================================================

def verificar_coordinacion_proteccion(ib: float, in_prot: float, iz: float) -> dict:
    """
    Verifica las dos condiciones reglamentarias de protección contra sobrecargas:
    1) Ib <= In <= Iz  (La intensidad nominal del magneto está entre la de diseño y la admisible del cable)
    2) I2 <= 1.45 * Iz (Para PIAs UNE-EN 60898, I2 = 1.45 * In, por lo que equivale a In <= Iz)
    """
    cumple_ib_in = (in_prot >= ib - 0.05)  # Margen numérico mínimo
    cumple_in_iz = (in_prot <= iz + 0.05)
    cumple_sobrecarga = cumple_ib_in and cumple_in_iz
    
    mensajes = []
    if not cumple_ib_in:
        mensajes.append(f"⚠️ El calibre del PIA ({in_prot} A) es inferior a la intensidad de diseño ({ib:.2f} A). Se disparará por sobrecarga.")
    if not cumple_in_iz:
        mensajes.append(f"❌ ¡PELIGRO TÉRMICO! El calibre del PIA ({in_prot} A) supera la intensidad admisible del cable ({iz:.2f} A). El cable puede quemarse antes de que dispare el automático.")
    if cumple_sobrecarga:
        mensajes.append(f"✅ Coordinación térmica perfecta: Ib ({ib:.2f} A) ≤ In ({in_prot} A) ≤ Iz ({iz:.2f} A).")
        
    return {
        "cumple": cumple_sobrecarga,
        "cumple_ib_in": cumple_ib_in,
        "cumple_in_iz": cumple_in_iz,
        "mensajes": mensajes,
        "ib": ib,
        "in_prot": in_prot,
        "iz": iz
    }

# =========================================================================
# 9. FACTORES DE CORRECCIÓN (TEMPERATURA Y AGRUPAMIENTO) - UNE-HD 60364-5-52
# =========================================================================

def obtener_factor_temperatura(temp_amb: float, aislamiento: str = "xlpe", enterrado: bool = False) -> float:
    """
    Factores de corrección por temperatura ambiente (Base: 40ºC al aire, 25ºC en terreno).
    """
    es_xlpe = ("xlpe" in aislamiento.lower() or "epr" in aislamiento.lower() or "90" in aislamiento)
    
    if not enterrado:
        # Al aire (Base 40 ºC)
        if temp_amb <= 25: return 1.14 if es_xlpe else 1.22
        elif temp_amb <= 30: return 1.10 if es_xlpe else 1.15
        elif temp_amb <= 35: return 1.05 if es_xlpe else 1.08
        elif temp_amb <= 40: return 1.00
        elif temp_amb <= 45: return 0.96 if es_xlpe else 0.91
        elif temp_amb <= 50: return 0.90 if es_xlpe else 0.82
        elif temp_amb <= 55: return 0.84 if es_xlpe else 0.71
        elif temp_amb <= 60: return 0.76 if es_xlpe else 0.58
        else: return 0.65
    else:
        # Enterrado (Base 25 ºC)
        if temp_amb <= 15: return 1.08 if es_xlpe else 1.11
        elif temp_amb <= 20: return 1.04 if es_xlpe else 1.06
        elif temp_amb <= 25: return 1.00
        elif temp_amb <= 30: return 0.96 if es_xlpe else 0.93
        elif temp_amb <= 35: return 0.92 if es_xlpe else 0.87
        elif temp_amb <= 40: return 0.87 if es_xlpe else 0.79
        else: return 0.80

def obtener_factor_agrupamiento(num_circuitos: int, instalacion: str = "tubo") -> float:
    """
    Factores de corrección por agrupamiento de varios circuitos en el mismo tubo o canalización.
    """
    if num_circuitos <= 1: return 1.00
    elif num_circuitos == 2: return 0.80
    elif num_circuitos == 3: return 0.70
    elif num_circuitos == 4: return 0.65
    elif num_circuitos == 5: return 0.60
    elif num_circuitos == 6: return 0.57
    elif num_circuitos <= 8: return 0.52
    else: return 0.50

# =========================================================================
# 10. VERIFICACIÓN CONTRA CORTOCIRCUITO (ENERGÍA ESPECÍFICA I²·t)
# =========================================================================

def verificar_cortocircuito_cable(icc_ka: float, tiempo_s: float, seccion: float, material: str = "cobre", aislamiento: str = "xlpe") -> tuple[bool, float]:
    """
    Verifica que la sección del cable soporte la energía térmica del cortocircuito:
    S >= sqrt(Icc² * t) / k
    Constantes k (A·s^(1/2)/mm²):
    - Cobre / XLPE: 143
    - Cobre / PVC:  115
    - Aluminio / XLPE: 94
    - Aluminio / PVC:  76
    """
    mat = "aluminio" if "alum" in material.lower() else "cobre"
    aisl = "xlpe" if ("xlpe" in aislamiento.lower() or "epr" in aislamiento.lower() or "90" in aislamiento) else "pvc"
    
    if mat == "cobre":
        k = 143.0 if aisl == "xlpe" else 115.0
    else:
        k = 94.0 if aisl == "xlpe" else 76.0
        
    icc_a = icc_ka * 1000.0
    s_min_cc = (math.sqrt((icc_a ** 2) * max(tiempo_s, 0.01))) / k
    cumple = (seccion >= s_min_cc)
    return cumple, s_min_cc


