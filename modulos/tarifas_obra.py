"""
Módulo de Tarifas de Obra, Kits Inteligentes y Rentabilidad de Calle.
Conecta los cálculos rigurosos del REBT (ITC-BT-15, ITC-BT-25) con la realidad económica
del instalador electricista de calle y el análisis informático de rentabilidad.
"""
import math
from modulos import rebt_tablas as rebt

# Precios de coste de mercado orientativos para escandallo real (S/IVA)
PRECIOS_COSTE_MATERIAL_DI = {
    "cable_rz1k_10mm": 1.45,   # €/m por hilo conductor Cu 10 mm² RZ1-K 0.6/1kV libre halógenos
    "cable_rz1k_16mm": 2.38,   # €/m por hilo conductor Cu 16 mm² RZ1-K 0.6/1kV libre halógenos
    "cable_rz1k_25mm": 3.75,   # €/m por hilo conductor Cu 25 mm² RZ1-K 0.6/1kV libre halógenos
    "cable_rz1k_6mm":  0.92,   # €/m por hilo conductor Cu 6 mm² RZ1-K
    "cable_mando_15mm": 0.26,  # €/m hilo de mando rojo 1.5 mm² telegestión / discriminación horaria
    "tubo_lh_32mm": 0.88,      # €/m tubo corrugado libre de halógenos 750N M32
    "tubo_lh_40mm": 1.25,      # €/m tubo corrugado libre de halógenos 750N M40
    "tubo_lh_50mm": 1.85,      # €/m tubo corrugado libre de halógenos 750N M50
    "menudencia_bornes_fusibles": 16.50, # Lote pequeño material (bornes, punteras, tornillos, abrazaderas)
    "mortero_yeso_roza_saco": 4.50       # Saco pasta/yeso rápido para tapado de rozas
}

def calcular_seccion_di_tecnica(
    potencia_w: float = 5750.0,
    longitud_m: float = 18.0,
    es_trifasico: bool = False,
    cdt_max_pct: float = 1.0,
    cos_phi: float = 1.0,
    aislamiento: str = "XLPE / EPR (90°C) - RZ1-K"
) -> dict:
    """
    Cálculo técnico normativo según ITC-BT-15 de la Derivación Individual.
    """
    tension = 400.0 if es_trifasico else 230.0
    gamma = rebt.obtener_gamma("cobre", aislamiento)
    ib = rebt.calcular_intensidad_diseno(potencia_w, tension, cos_phi, es_trifasico)
    
    # Caída de tensión
    s_cdt = rebt.calcular_seccion_por_cdt(potencia_w, longitud_m, gamma, cdt_max_pct, tension, es_trifasico)
    
    # REBT ITC-BT-15: Sección mínima en DI = 6 mm² (10 mm² recomendado en monofásico para previsión)
    s_min_normativa = 6.0
    s_teorica = max(s_cdt, s_min_normativa)
    s_optima = rebt.seleccionar_seccion_optima(s_teorica, material="cobre", s_minima=6.0)
    
    # IGA recomendado
    in_iga = rebt.seleccionar_proteccion(ib, tipo="pia")
    
    # Verificación Iz admisible (instalación típica B1 o B2)
    tabla_iz = rebt.obtener_tabla_iz("cobre", aislamiento, "B1 (Bajo tubo empotrado)")
    iz_adm = tabla_iz.get(s_optima, 61.0)
    if in_iga > iz_adm:
        # Aumentar sección para coordinar IGA <= Iz
        for s_cand in [10.0, 16.0, 25.0, 35.0, 50.0]:
            if s_cand >= s_optima and tabla_iz.get(s_cand, 0.0) >= in_iga:
                s_optima = s_cand
                break
                
    # Caída de tensión real obtenida
    dv_v = rebt.calcular_caida_tension_v(potencia_w, longitud_m, gamma, s_optima, tension, es_trifasico)
    cdt_real_pct = rebt.calcular_caida_tension_pct(dv_v, tension)
    
    # Tubo reglamentario ITC-BT-15
    tubo_diam_str, tubo_razon = rebt.dimensionar_tubo_di(s_optima)
    
    # Conductor PE de protección reglamentario (ITC-BT-19)
    pe_seccion = rebt.dimensionar_conductor_pe(s_optima)
    
    return {
        "potencia_w": potencia_w,
        "longitud_m": longitud_m,
        "es_trifasico": es_trifasico,
        "tension": tension,
        "ib": round(ib, 2),
        "in_iga": in_iga,
        "s_cdt": round(s_cdt, 2),
        "seccion_fase": s_optima,
        "seccion_pe": pe_seccion,
        "cdt_real_pct": round(cdt_real_pct, 2),
        "cdt_max_pct": cdt_max_pct,
        "tubo_diam": tubo_diam_str,
        "tubo_razon": tubo_razon,
        "cumple_normativa": cdt_real_pct <= cdt_max_pct
    }

def calcular_escandallo_coste_di(
    longitud_m: float,
    seccion_fase: float,
    es_trifasico: bool = False,
    metodo_montaje: str = "superficie", # "existente", "superficie", "roza"
    es_obra: bool = False,
    precio_hora: float = 25.0
) -> dict:
    """
    Calcula el coste real de materiales de almacén y horas de mano de obra
    que asume el instalador para ejecutar la Derivación Individual.
    """
    # Merma habitual en cables y tubos de DI: 8%
    factor_merma = 1.08
    m_cable_calculo = longitud_m * factor_merma
    
    # Número de conductores de fase/neutro
    # Monofásico: 2 hilos (Fase + Neutro) + 1 hilo Tierra (PE) + 1 hilo Mando rojo 1.5mm²
    # Trifásico: 4 hilos (3 Fases + Neutro) + 1 hilo Tierra (PE) + 1 hilo Mando rojo 1.5mm²
    num_fases_neutro = 4 if es_trifasico else 2
    
    if seccion_fase <= 6.0:
        p_cable_fase = PRECIOS_COSTE_MATERIAL_DI["cable_rz1k_6mm"]
        p_cable_pe = PRECIOS_COSTE_MATERIAL_DI["cable_rz1k_6mm"]
        p_tubo_m = PRECIOS_COSTE_MATERIAL_DI["tubo_lh_32mm"]
    elif seccion_fase <= 10.0:
        p_cable_fase = PRECIOS_COSTE_MATERIAL_DI["cable_rz1k_10mm"]
        p_cable_pe = PRECIOS_COSTE_MATERIAL_DI["cable_rz1k_10mm"]
        p_tubo_m = PRECIOS_COSTE_MATERIAL_DI["tubo_lh_40mm"]
    elif seccion_fase <= 16.0:
        p_cable_fase = PRECIOS_COSTE_MATERIAL_DI["cable_rz1k_16mm"]
        p_cable_pe = PRECIOS_COSTE_MATERIAL_DI["cable_rz1k_16mm"]
        p_tubo_m = PRECIOS_COSTE_MATERIAL_DI["tubo_lh_40mm"]
    else:
        p_cable_fase = PRECIOS_COSTE_MATERIAL_DI["cable_rz1k_25mm"]
        p_cable_pe = PRECIOS_COSTE_MATERIAL_DI["cable_rz1k_25mm"]
        p_tubo_m = PRECIOS_COSTE_MATERIAL_DI["tubo_lh_50mm"]
        
    p_mando_m = PRECIOS_COSTE_MATERIAL_DI["cable_mando_15mm"]
    
    coste_cables = (
        (num_fases_neutro * p_cable_fase * m_cable_calculo) +
        (1 * p_cable_pe * m_cable_calculo) +
        (1 * p_mando_m * m_cable_calculo)
    )
    
    # Tubo y fijaciones
    if metodo_montaje == "existente":
        coste_tubo = 0.0 # Se aprovecha el tubo existente
        coste_fijaciones = 8.00 # Guía pasacables, lubricante tira-cables y bornes
        coste_albañileria = 0.0
    elif metodo_montaje == "superficie":
        coste_tubo = p_tubo_m * (longitud_m * 1.05)
        coste_fijaciones = PRECIOS_COSTE_MATERIAL_DI["menudencia_bornes_fusibles"] + (longitud_m * 0.40) # Abrazaderas M40
        coste_albañileria = 0.0
    else: # "roza"
        coste_tubo = p_tubo_m * (longitud_m * 1.05)
        coste_fijaciones = PRECIOS_COSTE_MATERIAL_DI["menudencia_bornes_fusibles"]
        sacos_yeso = max(1, math.ceil(longitud_m / 6.0))
        coste_albañileria = sacos_yeso * PRECIOS_COSTE_MATERIAL_DI["mortero_yeso_roza_saco"]
        
    coste_materiales_total = round(coste_cables + coste_tubo + coste_fijaciones + coste_albañileria, 2)
    
    # Tiempos de mano de obra según realidad de la calle
    if metodo_montaje == "existente":
        h_base = 2.5
        h_por_metro = 0.04
    elif metodo_montaje == "superficie":
        h_base = 3.2
        h_por_metro = 0.06
    else: # "roza"
        h_base = 5.0
        h_por_metro = 0.18 # Picado, colocación y tapado con yeso
        
    # Coeficiente si el cable es de 16 mm² o superior (mayor rigidez y esfuerzo de tiro)
    coef_peso_cable = 1.20 if seccion_fase >= 16.0 else 1.0
    if es_trifasico:
        coef_peso_cable *= 1.15
        
    horas_mo = (h_base + (longitud_m * h_por_metro)) * coef_peso_cable
    if es_obra:
        horas_mo += 1.0 # Coordinación en obra con otros gremios
        
    horas_mo = round(horas_mo, 2)
    coste_mo_total = round(horas_mo * precio_hora, 2)
    coste_directo_total = round(coste_materiales_total + coste_mo_total, 2)
    
    return {
        "coste_materiales": coste_materiales_total,
        "coste_cables": round(coste_cables, 2),
        "coste_tubo": round(coste_tubo, 2),
        "coste_fijaciones": round(coste_fijaciones + coste_albañileria, 2),
        "horas_mo": horas_mo,
        "precio_hora": precio_hora,
        "coste_mo": coste_mo_total,
        "coste_directo_total": coste_directo_total
    }

def cotizar_tarifa_calle_di(
    longitud_m: float = 18.0,
    potencia_w: float = 5750.0,
    es_trifasico: bool = False,
    metodo_montaje: str = "superficie", # "existente", "superficie", "roza"
    es_obra: bool = False,
    incluir_boletin: bool = False,
    precio_base_20m: float = 225.0, # Tarifa base instalador hasta 20 m (rango 200 - 250 €)
    precio_metro_extra: float = 9.0, # Por cada metro que supere los 20 m
    suple_16mm: float = 75.0,        # Suplemento si la sección técnica REBT exige 16 mm²
    suple_25mm: float = 145.0,       # Suplemento si la sección técnica REBT exige 25 mm²
    suple_roza_m: float = 8.50,      # Suplemento por metro de roza y tapado
    porc_suple_obra: float = 20.0,   # Recargo si es obra nueva / reforma integral frente a particular
    precio_boletin_di: float = 150.0,# Suplemento tramitación boletín/CIE si se incluye en este kit
    precio_hora_coste: float = 25.0
) -> dict:
    """
    Calcula el precio de venta según tarifa de calle de instalador (tutor de prácticas)
    y realiza una auditoría de rentabilidad contra el coste real del escandallo.
    """
    # 1. Dimensionamiento técnico reglamentario
    tec = calcular_seccion_di_tecnica(potencia_w, longitud_m, es_trifasico)
    seccion = tec["seccion_fase"]
    
    # 2. Escandallo de coste real directo (lo que le cuesta al instalador)
    coste = calcular_escandallo_coste_di(
        longitud_m=longitud_m,
        seccion_fase=seccion,
        es_trifasico=es_trifasico,
        metodo_montaje=metodo_montaje,
        es_obra=es_obra,
        precio_hora=precio_hora_coste
    )
    
    # 3. Construcción del precio de venta al cliente según tarifa de calle
    p_base = float(precio_base_20m)
    
    # Metros adicionales más allá de 20m
    m_extra = max(0.0, longitud_m - 20.0)
    importe_m_extra = round(m_extra * precio_metro_extra, 2)
    
    # Suplemento de sección técnica REBT
    if seccion == 16.0:
        importe_suple_sec = float(suple_16mm)
        motivo_sec = "Suplemento técnico cable 16 mm² (ITC-BT-15)"
    elif seccion >= 25.0:
        importe_suple_sec = float(suple_25mm)
        motivo_sec = f"Suplemento técnico cable {int(seccion)} mm² (ITC-BT-15)"
    else:
        importe_suple_sec = 0.0
        motivo_sec = "Sección estándar 10 mm² incluida en tarifa base"
        
    # Suplemento por rozas
    if metodo_montaje == "roza":
        importe_suple_roza = round(longitud_m * suple_roza_m, 2)
    else:
        importe_suple_roza = 0.0
        
    # Subtotal preliminar antes del recargo de obra
    sub_antes_obra = p_base + importe_m_extra + importe_suple_sec + importe_suple_roza
    
    # Suplemento de obra vs particular
    importe_suple_obra = round(sub_antes_obra * (porc_suple_obra / 100.0), 2) if es_obra else 0.0
    
    # Boletín / CIE opcional
    importe_boletin = float(precio_boletin_di) if incluir_boletin else 0.0
    
    # PVP Total de Venta S/IVA de la Derivación Individual
    pvp_venta_neto = round(sub_antes_obra + importe_suple_obra + importe_boletin, 2)
    
    # 4. Auditoría de rentabilidad
    coste_total = coste["coste_directo_total"] + (35.0 if incluir_boletin else 0.0) # Tasas mínimas si incluye boletín
    beneficio_neto = round(pvp_venta_neto - coste_total, 2)
    margen_sobre_venta_pct = round((beneficio_neto / pvp_venta_neto * 100.0), 1) if pvp_venta_neto > 0 else 0.0
    margen_sobre_coste_pct = round((beneficio_neto / coste_total * 100.0), 1) if coste_total > 0 else 0.0
    
    # Semáforo de Rentabilidad
    if margen_sobre_venta_pct >= 28.0:
        semaforo = "🟢 RENTABLE"
        color_hex = "#16a34a"
        diagnostico = f"Margen saludable del {margen_sobre_venta_pct}%. Trabajo seguro con ganancia empresarial neta de +{beneficio_neto:.2f} €."
    elif margen_sobre_venta_pct >= 12.0:
        semaforo = "🟡 MARGEN AJUSTADO"
        color_hex = "#ca8a04"
        diagnostico = f"Margen justo del {margen_sobre_venta_pct}% (+{beneficio_neto:.2f} € de beneficio). Válido si va junto con reforma, cuadro o boletín."
    else:
        semaforo = "🔴 PELIGRO DE PÉRDIDAS"
        color_hex = "#dc2626"
        diagnostico = f"Margen deficiente ({margen_sobre_venta_pct}%). A este precio ({pvp_venta_neto:.2f} €) trabajas a coste o en pérdidas. Se recomienda aplicar suplemento de al menos +{max(40.0, coste_total * 1.30 - pvp_venta_neto):.0f} €."
        
    precio_min_recomendado = round(coste_total * 1.35, 2) # Margen objetivo mínimo del 26% s/venta (35% s/coste)
    
    return {
        "tecnica": tec,
        "coste": coste,
        "pvp_venta_neto": pvp_venta_neto,
        "desglose_tarifa": {
            "base_20m": p_base,
            "metros_extra": m_extra,
            "importe_metros_extra": importe_m_extra,
            "seccion_mm2": seccion,
            "suple_seccion": importe_suple_sec,
            "motivo_seccion": motivo_sec,
            "suple_rozas": importe_suple_roza,
            "suple_obra": importe_suple_obra,
            "importe_boletin": importe_boletin
        },
        "beneficio_neto": beneficio_neto,
        "margen_sobre_venta_pct": margen_sobre_venta_pct,
        "margen_sobre_coste_pct": margen_sobre_coste_pct,
        "semaforo": semaforo,
        "color_hex": color_hex,
        "diagnostico": diagnostico,
        "precio_min_recomendado": precio_min_recomendado
    }

def generar_partida_presupuesto_di(tarifa_info: dict) -> dict:
    """
    Genera el diccionario de partida manual para ser insertado en `st.session_state.partidas_manuales`.
    """
    tec = tarifa_info["tecnica"]
    desg = tarifa_info["desglose_tarifa"]
    pvp = tarifa_info["pvp_venta_neto"]
    
    es_tri = tec["es_trifasico"]
    cable_desc = f"{'4x' if es_tri else '2x'}{int(tec['seccion_fase'])} mm² Cu + TT 1x{int(tec['seccion_pe'])} mm² RZ1-K 0.6/1kV CPR libre de halógenos"
    mando_desc = " + Hilo de mando rojo 1x1.5 mm²"
    tubo_desc = f"tubo {tec['tubo_diam']} libre de halógenos 750N (ITC-BT-15)"
    
    detalles_extra = []
    if desg["metros_extra"] > 0:
        detalles_extra.append(f"{desg['metros_extra']:.1f}m extra")
    if desg["suple_seccion"] > 0:
        detalles_extra.append(f"supl. sección {int(tec['seccion_fase'])}mm²")
    if desg["suple_rozas"] > 0:
        detalles_extra.append("ejecución con rozas y tapado")
    if desg["suple_obra"] > 0:
        detalles_extra.append("recargo coordinación obra")
    if desg["importe_boletin"] > 0:
        detalles_extra.append("ensayos e informe CIE")
        
    sufijo_extra = f" ({', '.join(detalles_extra)})" if detalles_extra else ""
    
    concepto = f"Derivación Individual DI {tec['longitud_m']:.0f}m - {int(tec['seccion_fase'])} mm² Cu (ITC-BT-15)"
    descripcion = (
        f"Suministro e instalación de Derivación Individual de {tec['longitud_m']:.1f} m desde centralización de contadores "
        f"hasta CGMP. Conductores {cable_desc}{mando_desc} bajo {tubo_desc}. "
        f"Caída de tensión calculada: {tec['cdt_real_pct']:.2f}% (límite {tec['cdt_max_pct']}%). "
        f"Protegido con IGA {tec['in_iga']}A. Incluye grapado/guiado, conexiones y timbrado normativo{sufijo_extra}."
    )
    
    return {
        "concepto": concepto,
        "descripcion": descripcion,
        "cantidad": 1.0,
        "unidad": "partida",
        "precio_unitario": pvp,
        "subtotal": pvp
    }
