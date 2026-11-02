# -*- coding: utf-8 -*-
"""
Módulo de Presupuesto Rápido con IA y Dictado por Micrófono (Bolimur Instant Work).
Diseñado para el instalador electricista de calle que necesita cotizar un trabajo
urgente en segundos a pie de obra o en la furgoneta.
Permite dictar por voz, ver la transcripción en pantalla, modificarla,
visualizar la memoria técnica completa determinada por la IA y generar
el presupuesto detallado con escandallo de materiales, mano de obra y régimen de IVA.
"""

import streamlit as st
import pandas as pd
import datetime
import base64
import json
import re
import requests
from modulos import auditor_ia_rebt
from modulos import asistente_ia_rebt


def transcribir_audio_gemini(raw_bytes: bytes, mime_type: str = "audio/wav", api_key: str = "") -> dict:
    """Envía el audio a Gemini 2.0 Flash para transcribir la voz del instalador a texto en español."""
    if not api_key:
        return {"exito": False, "error": "Falta la clave API de Google Gemini."}

    b64_data = base64.b64encode(raw_bytes).decode("utf-8")
    clean_mime = mime_type or "audio/wav"
    if ";" in clean_mime:
        clean_mime = clean_mime.split(";")[0].strip()

    prompt = (
        "Eres un transcriptor técnico de campo para instaladores electricistas en España (normativa REBT).\n"
        "Escucha atentamente este audio grabado por el instalador y transcribe con máxima exactitud "
        "lo que dice sobre el trabajo eléctrico a realizar (cables, metros, tubos, automáticos, cuadros, "
        "relojes, enchufes, etc.).\n"
        "Devuelve ÚNICAMENTE el texto en español transcrito en lenguaje natural limpio, sin saludos, "
        "sin comillas ni explicaciones adicionales."
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": clean_mime,
                            "data": b64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 800
        }
    }

    modelos = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.5-flash", "gemini-3.8-flash"]
    ultimo_error = "Error desconocido de conexión."
    for modelo in modelos:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        try:
            resp = requests.post(endpoint, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands:
                    partes = cands[0].get("content", {}).get("parts", [])
                    if partes:
                        texto = partes[0].get("text", "").strip()
                        if texto:
                            return {"exito": True, "texto": texto}
            else:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", resp.text[:250])
                except Exception:
                    err_msg = resp.text[:250]
                ultimo_error = f"HTTP {resp.status_code} ({modelo}): {err_msg}"
        except Exception as e:
            ultimo_error = str(e)
            continue

    return {"exito": False, "error": ultimo_error}


def analizar_trabajo_ia_gemini(descripcion: str, api_key: str, precio_hora: float = 25.0) -> dict:
    """Utiliza Gemini para desglosar el trabajo en memoria técnica REBT exhaustiva, partidas y materiales."""
    if not api_key:
        return {"exito": False}

    prompt = f"""Actúa como un Maestro Instalador Electricista Autorizado e Ingeniero Eléctrico en España con 25 años de experiencia y dominio exhaustivo del REBT (RD 842/2002) y normativa de Industria (DGEAIM Murcia).
Analiza detalladamente el siguiente trabajo eléctrico explicado por el instalador:
"{descripcion}"

Redacta un dictamen técnico riguroso, completo y profesional.
Devuelve EXCLUSIVAMENTE un objeto JSON válido con la siguiente estructura exacta (sin texto previo ni posterior, sin formato markdown adicional):
{{
  "concepto": "Título técnico oficial conciso de la obra",
  "norma": "Instrucciones técnicas REBT y normas UNE de aplicación directa (ej: ITC-BT-25, ITC-BT-31, UNE-HD 60364)",
  "descripcion_detallada": "Memoria descriptiva y exhaustiva del trabajo (3 párrafos técnicos completos describiendo el alcance, canalizaciones, trazado, protecciones y envolventes apta para el presupuesto o factura formal)",
  "justificacion_tecnica": "Justificación técnica de ingeniería: por qué se han seleccionado esas secciones de cable, caídas de tensión calculadas, tipo de diferencial (Clase A/AC/Superinmunizado), curvas de disparo y grados de protección IP/IK requeridos",
  "pasos_ejecucion": [
    "Paso 1: Consignación de la instalación y comprobación de ausencia de tensión",
    "Paso 2: Instalación de canalizaciones y fijaciones",
    "Paso 3: Tendido de conductores y conexionado",
    "Paso 4: Montaje y rotulado de aparamenta en cuadro",
    "Paso 5: Ensayos reglamentarios finales y puesta en servicio"
  ],
  "pruebas_rebt": [
    "Medida de continuidad de conductores de protección y equipotenciales (R < 1 Ohm)",
    "Medida de resistencia de aislamiento entre conductores activos y tierra (> 0.5 MOhm a 500V DC)",
    "Comprobación de tiempo y corriente de disparo del interruptor diferencial (t < 200 ms)",
    "Verificación de polaridad y correspondencia de neutro y fase"
  ],
  "horas": 3.5,
  "materiales": [
    {{"mat": "Nombre comercial y especificación técnica del material", "cant": 1.0, "unid": "ud"|"m"|"pack", "p_u": 32.50}}
  ]
}}"""

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2500
        }
    }

    modelos = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.5-flash", "gemini-3.8-flash"]
    for modelo in modelos:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        try:
            resp = requests.post(endpoint, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands:
                    texto = cands[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    if "```json" in texto:
                        texto = texto.split("```json")[1].split("```")[0].strip()
                    elif "```" in texto:
                        texto = texto.split("```")[1].split("```")[0].strip()
                    obj = json.loads(texto)
                    if "concepto" in obj and "materiales" in obj and "descripcion_detallada" in obj:
                        return {"exito": True, "resultado": obj}
        except Exception:
            continue

    return {"exito": False}


def motor_reglas_rebt_rapido(prompt_consulta: str) -> dict:
    """Motor reglamentario REBT exhaustivo cuando se opera sin conexión IA o clave API."""
    p_low = prompt_consulta.lower().strip()

    if "depuradora" in p_low or "piscina" in p_low:
        concepto = "Línea Dedicada Protegida y Automatismo Horario para Depuradora de Piscina (ITC-BT-31)"
        norma = "ITC-BT-31 (Piscinas y Fuentes), ITC-BT-30 (Locales Húmedos/Mojados), ITC-BT-24 (Protección contra Contactos)"
        descripcion = (
            "Instalación de línea eléctrica independiente desde el Cuadro General de Mando y Protección (CGMP) "
            "hasta la caseta técnica o arqueta de depuración de piscina. Incluye tendido de línea monofásica con conductor "
            "unipolar de cobre Cu RZ1-K 0.6/1kV de sección 3G2.5 mm² libre de halógenos y no propagador del incendio (Cca-s1b,d1,a1), "
            "instalado bajo tubo corrugado reforzado flexible M25 libre de halógenos de 750N de resistencia a la compresión.\n\n"
            "Montaje de cuadro modular de mando estanco con envolvente de policarbonato IP65 e impacto IK08. En su interior se "
            "instala un interruptor magnetotérmico 1P+N de 16A curva C (6kA) para protección contra sobrecargas y cortocircuitos, "
            "junto con un reloj programador horario modular carril DIN con esfera analógica/digital y reserva de marcha de 100 horas, "
            "más selector manual-automático-paro. Conexionado del motor de bomba de impulsión con prensaestopas estancos y puente "
            "de equipotencialidad con la red de tierra general de la instalación."
        )
        justificacion = (
            "La ITC-BT-31 clasifica los volúmenes de piscinas y exige envolventes mínimas IPX5 para equipos exteriores expuestos a proyecciones. "
            "Se prescribe cable de aislamiento 0.6/1kV RZ1-K debido a la presencia constante de humedad y agentes desinfectantes (cloro/sal). "
            "La protección magnetotérmica calibrada a 16A curva C absorbe la punta de arranque inductiva del motor ($I_a \\approx 5\\text{ a }7 \\times I_n$) "
            "sin disparos intempestivos, manteniendo la caída de tensión calculada por debajo del 1.5%."
        )
        pasos = [
            "Consignación eléctrica y verificación de ausencia de tensión en CGMP.",
            "Replanteo del trazado exterior y fijación de canalización con grapas de acero inoxidable.",
            "Tendido de conductores RZ1-K 3G2.5 mm² y conexionado de conductor de protección PE.",
            "Fijación mecánica de cuadro estanco IP65, montaje de PIA 16A y reloj horario en carril DIN.",
            "Conexionado borne a borne del motor de la bomba y ajuste de caballetes horarios.",
            "Ensayos finales reglamentarios (continuidad, aislamiento y disparo diferencial) y rotulación."
        ]
        pruebas = [
            "Medida de continuidad del conductor de protección equipotencial PE (R < 1 Ohm)",
            "Medida de resistencia de aislamiento con generador de 500V DC (> 0.5 MOhm)",
            "Comprobación de sensibilidad y tiempo de corte diferencial (t < 200 ms a 30 mA)",
            "Verificación de estanqueidad de prensaestopas y sellado de cuadro IP65"
        ]
        horas = 3.5
        materiales = [
            {"mat": "Reloj Programador Horario Modular Carril DIN con Reserva", "cant": 1.0, "unid": "ud", "p_u": 34.50},
            {"mat": "PIA Magnetotérmico 1P+N 16A Curva C 6kA", "cant": 1.0, "unid": "ud", "p_u": 8.40},
            {"mat": "Cable Cu RZ1-K 0.6/1kV 3x2.5 mm² Libre Halógenos Cca", "cant": 20.0, "unid": "m", "p_u": 1.15},
            {"mat": "Tubo Corrugado Libre de Halógenos M25 750N", "cant": 20.0, "unid": "m", "p_u": 0.85},
            {"mat": "Cuadro Modular Estanco IP65 4-6 Módulos con Tapa Fumé", "cant": 1.0, "unid": "ud", "p_u": 16.80},
            {"mat": "Prensaestopas M25 IP68 y Bridas de Nylon UV", "cant": 1.0, "unid": "pack", "p_u": 6.50}
        ]

    elif "aire" in p_low or "clima" in p_low or "split" in p_low:
        concepto = "Circuito Independiente de Climatización C9 bajo ITC-BT-25 con Diferencial Superinmunizado"
        norma = "ITC-BT-25 (Instalaciones Interiores de Viviendas), ITC-BT-19 (Prescripciones Generales)"
        descripcion = (
            "Instalación de circuito independiente de climatización C9 según prescripciones de la ITC-BT-25 para alimentación "
            "de equipo de aire acondicionado / bomba de calor. Comprende la derivación directa desde el Cuadro General con conductor "
            "unipolar H07Z1-K (AS) 3G2.5 mm² bajo canaleta decorativa de superficie blanca con tapa de clipado rápido de 20x40 mm "
            "o tubo corrugado empotrado según configuración de paramentos.\n\n"
            "Incorporación en cuadro de interruptor magnetotérmico 1P+N de 16A curva C (6kA) exclusivo para el circuito C9, junto a "
            "un interruptor diferencial de cabecera bipolar de 40A / 30mA Clase A Superinmunizado para protección contra contactos "
            "indirectos y corrientes de fuga generadas por la electrónica de potencia del compresor inverter. En el extremo receptor se instala "
            "caja de mecanismo de superficie con base Schuko de 16A 2P+T con tapa o interruptor de corte en carga bipolar de proximidad."
        )
        justificacion = (
            "La ITC-BT-25 exige que los equipos de aire acondicionado dispongan de circuito C9 propio e independiente. Dado que los equipos "
            "modernos incorporan rectificadores y variadores de frecuencia (tecnología inverter), generan componentes de corriente continua "
            "y armónicos de alta frecuencia que saturan los núcleos magnéticos de diferenciales estándar Tipo AC provocando disparos intempestivos "
            "o ceguera ante defectos. El diferencial Tipo A Superinmunizado garantiza seguridad absoluta."
        )
        pasos = [
            "Desconexión y consignación del Cuadro General CGMP.",
            "Instalación y nivelación de canaleta decorativa blanca de 20x40 mm con accesorios de esquina.",
            "Tendido de conductores H07Z1-K 3G2.5 mm² (marrón, azul, amarillo-verde).",
            "Montaje de PIA 16A y diferencial Tipo A Superinmunizado en el CGMP.",
            "Fijación de caja de mecanismo o base Schuko reforzada junto a la unidad interior/exterior.",
            "Medida de caída de tensión (< 3%), resistencia de aislamiento y prueba de disparo de diferencial."
        ]
        pruebas = [
            "Verificación del calibre de la protección magnetotérmica adecuada a la sección de 2.5 mm² (16A)",
            "Ensayo de disparo diferencial Clase A (prueba de rampa y test a 30 mA, t < 200 ms)",
            "Medida de aislamiento entre conductores y tierra (> 0.5 MOhm a 500V DC)",
            "Comprobación de continuidad del conductor de tierra PE"
        ]
        horas = 3.0
        materiales = [
            {"mat": "PIA Magnetotérmico 1P+N 16A Curva C 6kA", "cant": 1.0, "unid": "ud", "p_u": 8.40},
            {"mat": "Diferencial 2x40A / 30mA Clase A Superinmunizado", "cant": 1.0, "unid": "ud", "p_u": 42.00},
            {"mat": "Cable Cu H07Z1-K 3x2.5 mm² (Fase, Neutro, Tierra)", "cant": 15.0, "unid": "m", "p_u": 0.95},
            {"mat": "Canaleta Decorativa Blanca con Tapa 20x40mm", "cant": 12.0, "unid": "m", "p_u": 2.20},
            {"mat": "Base Schuko Superficie 16A 2P+T Mecanismo", "cant": 1.0, "unid": "ud", "p_u": 6.80},
            {"mat": "Accesorios de Canaleta (Ángulos y Empalmes)", "cant": 1.0, "unid": "pack", "p_u": 5.50}
        ]

    elif "recarga" in p_low or "coche" in p_low or "vehículo" in p_low or "irve" in p_low:
        concepto = "Infraestructura para Recarga de Vehículo Eléctrico IRVE (ITC-BT-52 Esquema 2)"
        norma = "ITC-BT-52 (Infraestructura para Recarga de Vehículos Eléctricos), ITC-BT-23 (Sobretensiones)"
        descripcion = (
            "Instalación de línea eléctrica dedicada exclusiva para punto de recarga de vehículo eléctrico (IRVE) conforme a la "
            "ITC-BT-52, modo de recarga 3. Tendido de línea monofásica de 32A con conductores unipolares de cobre RZ1-K 0.6/1kV "
            "3G6 mm² (o 3G10 mm² según distancia para limitar la caída de tensión estricta al 1%) bajo tubo rígido blindado o curvable "
            "libre de halógenos de M32 con grado de resistencia al impacto IK08 y aplastamiento de 1250N.\n\n"
            "Cuadro secundario estanco de protección IRVE con envolvente IP65 dotado de: Interruptor General Automático IGA 2P 32A "
            "curva C, Interruptor Diferencial Clase A Superinmunizado 2P 40A / 30mA con filtro contra fugas de componente continua "
            "(> 6mA DC), y protector combinado de sobretensiones transitorias y permanentes con reconexión automática según ITC-BT-23."
        )
        justificacion = (
            "La ITC-BT-52 establece que la caída de tensión en la línea de recarga no debe superar el 1% para potencia nominal del punto "
            "de recarga (7.4 kW en monofásico a 32A). Se exige obligatoriamente protección diferencial Clase A o Tipo B con detección de "
            "fuga DC > 6mA para salvaguardar las baterías y el cargador embarcado del vehículo, así como protección contra sobretensiones permanentes."
        )
        pasos = [
            "Comprobación de la derivación o acometida y potencia contratada disponible.",
            "Trazado y anclaje de tubo rígido libre de halógenos M32 mediante abrazaderas metálicas cada 50 cm.",
            "Tendido de conductores Cu RZ1-K 3x6 mm² y comprobación de sección por caída de tensión al 1%.",
            "Montaje de cuadro de protecciones IRVE con diferencial Tipo A, IGA y protector de sobretensiones.",
            "Conexionado al cargador Wallbox o toma Mennekes y prueba funcional de protocolo de comunicación PWM.",
            "Ensayos reglamentarios ITC-BT-52 y redacción de certificado para tramitación de subvención Plan MOVES."
        ]
        pruebas = [
            "Medida de caída de tensión en carga a 32A (verificación de deltaV <= 1%)",
            "Disparo diferencial con inyección de corrientes pulsantes y rampa de 30 mA",
            "Comprobación de resistencia de la toma de tierra (Ra < 15 Ohm recomendada)",
            "Verificación de aislamiento de conductores a 500V DC (> 0.5 MOhm)"
        ]
        horas = 5.0
        materiales = [
            {"mat": "Interruptor General Automático IGA 2P 32A Curva C 10kA", "cant": 1.0, "unid": "ud", "p_u": 14.50},
            {"mat": "Diferencial Superinmunizado Clase A 2P 40A / 30mA (6mA DC)", "cant": 1.0, "unid": "ud", "p_u": 48.00},
            {"mat": "Protector Sobretensiones Transitorias y Permanentes POP+DPS", "cant": 1.0, "unid": "ud", "p_u": 52.00},
            {"mat": "Cable Cu RZ1-K 0.6/1kV 3x6 mm² Libre Halógenos Cca", "cant": 25.0, "unid": "m", "p_u": 2.25},
            {"mat": "Tubo Rígido Enchufable Libre de Halógenos M32 1250N", "cant": 20.0, "unid": "m", "p_u": 1.55},
            {"mat": "Cuadro Modular Estanco IP65 8 Módulos Garaje", "cant": 1.0, "unid": "ud", "p_u": 28.50}
        ]

    elif "derivación" in p_low or "di" in p_low or "contador" in p_low:
        concepto = "Sustitución y Adecuación de Derivación Individual Monofásica (ITC-BT-15)"
        norma = "ITC-BT-15 (Instalaciones de Enlace: Derivaciones Individuales), UNE 20460"
        descripcion = (
            "Renovación completa de la Derivación Individual monofásica desde la centralización de contadores del edificio hasta "
            "el Cuadro General de Mando y Protección (CGMP) de la vivienda, dando cumplimiento estricto a la ITC-BT-15.\n\n"
            "Tendido de conductores unipolares de cobre de alta seguridad Cu RZ1-K 0.6/1kV de sección 2x10 mm² (fase y neutro) más "
            "conductor de protección de 1x10 mm² con aislamiento amarillo-verde, clase de reacción al fuego Cca-s1b,d1,a1. Se incluye "
            "hilo rojo de mando de 1.5 mm² para telegestión de la distribuidora. Alojado en canalización independiente bajo tubo corrugado "
            "o rígido libre de halógenos de diámetro mínimo normalizado M40 (750N de resistencia), sin empalmes intermedios y con caja de "
            "seccionamiento y fusibles de protección reglamentaria en la centralización."
        )
        justificacion = (
            "La ITC-BT-15 estipula que la caída de tensión máxima admisible para contadores totalmente concentrados es del 1.5%. Con sección de "
            "10 mm² se garantiza alimentar hasta 9.200W (40A) en previsión de electrificación elevada manteniendo la caída de tensión inferior al 1.2% "
            "y una temperatura de servicio controlada en cables termoestables (90ºC de régimen continuo)."
        )
        pasos = [
            "Coordinación de corte de suministro con la compañía distribuidora o técnico autorizado.",
            "Desmontaje de la derivación antigua fuera de normativa.",
            "Guíado y tendido de los nuevos conductores RZ1-K de 10 mm² e hilo de mando por la canaladura vertical.",
            "Conexionado en el embarrado del contador con bornas seccionables y apriete dinamométrico.",
            "Entrada en la vivienda y conexión a los bornes superiores del nuevo IGA de cabecera.",
            "Comprobación de rigidez dieléctrica, continuidad y precintado oficial."
        ]
        pruebas = [
            "Medida de continuidad y resistencia de paso de la derivación",
            "Ensayo de aislamiento entre conductores fase-neutro y contra tierra (> 0.5 MOhm a 500V DC)",
            "Comprobación de calibre de fusibles en módulo de contadores (GL/GG según potencia)",
            "Verificación de sección de tubo normalizada (mínimo M40 según ITC-BT-15)"
        ]
        horas = 4.5
        materiales = [
            {"mat": "Cable Cu RZ1-K 0.6/1kV 2x10 mm² + TT 1x10 mm² Cca", "cant": 22.0, "unid": "m", "p_u": 4.35},
            {"mat": "Hilo de Mando Rojo 1.5 mm² para Telegestión", "cant": 22.0, "unid": "m", "p_u": 0.28},
            {"mat": "Tubo Corrugado Libre de Halógenos M40 750N", "cant": 22.0, "unid": "m", "p_u": 1.35},
            {"mat": "Bornas de Conexión Seccionables de Entrada en CGMP", "cant": 2.0, "unid": "ud", "p_u": 4.50},
            {"mat": "Base Fusible Unipolar y Cartucho Fusible Calibrado", "cant": 1.0, "unid": "ud", "p_u": 9.80}
        ]

    elif "cuadro" in p_low or "automático" in p_low or "térmico" in p_low or "diferencial" in p_low or "sobretension" in p_low:
        concepto = "Sustitución, Ampliación y Normalización de Cuadro General de Mando y Protección (CGMP)"
        norma = "ITC-BT-17 (Dispositivos Generales de Mando y Protección), ITC-BT-23 (Sobretensiones), ITC-BT-24"
        descripcion = (
            "Desmontaje de cuadro eléctrico obsoleto o fuera de norma y suministro e instalación de nuevo Cuadro General de Mando "
            "y Protección (CGMP) empotrado o de superficie con envolvente aislante autoextinguible clase II de 18 a 24 módulos DIN.\n\n"
            "Estructuración de aparamenta de primeras marcas (Schneider / Hager / Legrand): Interruptor General Automático (IGA) bipolar "
            "de 25A o 32A curva C con poder de corte de 6kA; Protector combinado contra Sobretensiones Permanentes y Transitorias (POP+DPS) "
            "según normativa autonómica; dos o más Interruptores Diferenciales bipolares de 40A / 30mA (garantizando un máximo reglamentario "
            "de 5 circuitos por diferencial según ITC-BT-25); peines de conexión bipolares aislados con cubrenormas y rotulación normalizada "
            "indeleble de cada uno de los circuitos terminales."
        )
        justificacion = (
            "La ITC-BT-17 y las resoluciones de la Dirección General de Industria (Murcia) obligan a la instalación de protectores de "
            "sobretensiones en cualquier reforma o alta de suministro. Asimismo, la ITC-BT-25 prohíbe conectar más de 5 circuitos a un mismo "
            "diferencial para evitar acumulaciones de corrientes de fuga y garantizar la selectividad del suministro."
        )
        pasos = [
            "Identificación, timbrado y etiquetado provisional de todos los circuitos existentes.",
            "Corte general de suministro y desmontaje de envolvente y aparamenta antigua.",
            "Adecuación del hueco o fijación de nueva envolvente de 18-24 módulos en paramento.",
            "Montaje en carril DIN de IGA, protector de sobretensiones POP+DPS y diferenciales.",
            "Distribución mediante peines bipolares aislados y reordenación de cableado con punteras huecas.",
            "Pruebas de disparo diferencial en rampa, medida de aislamiento general y rotulación definitiva."
        ]
        pruebas = [
            "Medida de disparo individual de cada interruptor diferencial (tiempo < 200 ms y corriente < 30 mA)",
            "Comprobación del led de estado del cartucho de sobretensiones transitorias (verde = OK)",
            "Verificación de apriete dinamométrico en todos los bornes de conexión (par recomendado por fabricante)",
            "Resistencia de aislamiento general con aparamenta bajada (> 0.5 MOhm a 500V DC)"
        ]
        horas = 4.0
        materiales = [
            {"mat": "Envolvente Empotrada CGMP 18-24 Módulos con Puerta Blanca", "cant": 1.0, "unid": "ud", "p_u": 28.50},
            {"mat": "Interruptor General Automático IGA 2P 32A Curva C 6kA", "cant": 1.0, "unid": "ud", "p_u": 12.50},
            {"mat": "Protector Sobretensiones Permanentes y Transitorias POP+DPS", "cant": 1.0, "unid": "ud", "p_u": 49.00},
            {"mat": "Interruptores Diferenciales 2x40A / 30mA Tipo A (x2)", "cant": 2.0, "unid": "ud", "p_u": 24.50},
            {"mat": "Peines de Conexión Bipolares y Punteras Aisladas", "cant": 1.0, "unid": "pack", "p_u": 16.00}
        ]

    else:
        concepto = f"Trabajo Eléctrico Especializado a Medida: {prompt_consulta[:45]}" if prompt_consulta else "Trabajo Eléctrico Especializado a Medida (REBT)"
        norma = "REBT (RD 842/2002), ITC-BT-19, ITC-BT-24 (Protección contra Contactos Directos e Indirectos)"
        descripcion = (
            f"Ejecución técnica de los trabajos eléctricos correspondientes a: \"{prompt_consulta or 'Reforma y adecuación eléctrica puntual'}\".\n\n"
            "Comprende el suministro e instalación de canalizaciones normalizadas, conductores de cobre unipolar termoestable o termoplástico "
            "de alta seguridad libres de halógenos y no propagadores de la llama, aparamenta modular de corte y protección calibrada para la potencia "
            "solicitada, conexionado en cajas estancas o mecanismos homologados y puesta a tierra reglamentaria de todos los elementos metálicos accesibles."
        )
        justificacion = (
            "Todos los componentes y materiales seleccionados cumplen con el Reglamento Electrotécnico para Baja Tensión (RD 842/2002) y sus "
            "Instrucciones Técnicas Complementarias, garantizando la coordinación estricta entre sección de cable y calibre de protección "
            "para evitar calentamientos y garantizar el corte automático ante cualquier defecto de aislamiento."
        )
        pasos = [
            "Inspección previa del circuito y verificación de seguridad eléctrica.",
            "Tendido de canalización y conductores normalizados.",
            "Conexionado de aparamenta y borneros de derivación.",
            "Ensayos reglamentarios de continuidad y aislamiento."
        ]
        pruebas = [
            "Medida de resistencia de aislamiento (> 0.5 MOhm a 500V DC)",
            "Comprobación de continuidad de tierra y equipotencialidad (R < 1 Ohm)",
            "Verificación de disparo de protecciones ante defectos simulados"
        ]
        horas = 2.5
        materiales = [
            {"mat": "Conductores de Cobre Normalizados y Canalización", "cant": 1.0, "unid": "partida", "p_u": 35.00},
            {"mat": "Aparamenta de Maniobra y Protección Calibrada", "cant": 1.0, "unid": "partida", "p_u": 25.00},
            {"mat": "Menudencia, Borneros de Conexión y Fijaciones", "cant": 1.0, "unid": "pack", "p_u": 12.00}
        ]

    return {
        "concepto": concepto,
        "norma": norma,
        "descripcion_detallada": descripcion,
        "justificacion_tecnica": justificacion,
        "pasos_ejecucion": pasos,
        "pruebas_rebt": pruebas,
        "horas": horas,
        "materiales": materiales
    }


def renderizar():
    st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">⚡ Presupuesto Rápido con IA y Dictado por Voz</h3></div>', unsafe_allow_html=True)
    st.caption("Diseñado para calle y furgoneta: habla por el micrófono o escribe el trabajo. La IA transcribirá tus palabras, las mostrará en pantalla, generará la memoria técnica detallada y estructurará el escandallo en segundos.")

    # Inicializar variables en session_state de forma segura
    if "pr_texto_input" not in st.session_state:
        st.session_state["pr_texto_input"] = ""
    if "pr_last_audio_bytes" not in st.session_state:
        st.session_state["pr_last_audio_bytes"] = None

    # Estado de la API de Gemini
    api_key = auditor_ia_rebt.obtener_gemini_api_key()
    tiene_gemini = bool(api_key and len(api_key) > 10)

    # Panel de Configuración de Clave API si no está configurada
    if not tiene_gemini:
        with st.expander("🔑 Activar Transcripción de Voz IA Directa con Google Gemini (Gratuito)", expanded=True):
            st.info("Para que la IA transcriba directamente tu voz a texto en la pantalla, introduce tu clave gratuita de Google Gemini (se obtiene gratis en 1 minuto en [Google AI Studio](https://aistudio.google.com/)).")
            nueva_key = st.text_input("Pega tu Clave API de Gemini aquí:", type="password", placeholder="AIzaSy...", key="pr_input_gemini_key")
            if st.button("💾 Guardar Clave API para Siempre", key="btn_save_gemini_pr", type="primary"):
                if nueva_key.strip():
                    auditor_ia_rebt.guardar_gemini_api_key(nueva_key.strip())
                    st.success("✅ Clave API guardada con éxito en secrets.toml de forma permanente.")
                    st.rerun()

    # 1. Configuración de Mano de Obra y Cliente Rápido
    col_cfg1, col_cfg2, col_cfg3 = st.columns([2.5, 1.5, 1.5])
    with col_cfg1:
        nom_cliente = st.text_input("👤 Cliente / Referencia:", value="Cliente Particular / Urgencia", key="pr_cliente_nom")
    with col_cfg2:
        precio_hora_mo = st.number_input("⏱️ Precio Mano de Obra (€/h):", min_value=15.0, max_value=80.0, value=25.0, step=1.0, key="pr_precio_hora")
    with col_cfg3:
        iva_pct = st.selectbox("🏛️ Régimen de IVA:", [21.0, 10.0, 0.0], format_func=lambda x: f"{x:.0f}% (General)" if x == 21.0 else (f"{x:.0f}% (Reducido)" if x == 10.0 else "0% (Inversión Sujeto Pasivo / Subcontrata)"), key="pr_iva_sel")

    st.markdown("---")

    # 2. Entrada Multimodal: Micrófono de Voz y Texto
    st.markdown("#### 🎙️ Paso 1: Dicta o escribe el trabajo a realizar")
    st.info(
        "💡 **Dictado directo por voz más rápido y fiable:**\n\n"
        "• **En PC (Windows):** Haz clic en la caja de texto izquierda de abajo y pulsa **`Tecla Windows + H`**. Windows activará el micrófono y escribirá en tiempo real lo que digas.\n"
        "• **En Móvil o Tablet:** Toca la caja de texto y pulsa el **icono de micrófono del teclado** de tu teléfono.\n"
        "• **Con el grabador web (`Graba tu voz`):** Si usas el botón web inferior, accede mediante `http://localhost:8501` para que el navegador autorice la subida del audio sin restricciones de seguridad de red."
    )

    col_input1, col_input2 = st.columns([3, 2])

    with col_input2:
        with st.container(border=True):
            st.markdown("🎤 **1. Dictado por Micrófono:**")
            st.caption("Pulsa el botón de grabar, explica el trabajo y pulsa detener:")
            audio_in = st.audio_input("Graba tu voz", key="pr_mic_audio")

            # Procesamiento de audio capturado
            if audio_in is not None:
                raw_bytes = audio_in.getvalue()
                if st.session_state["pr_last_audio_bytes"] != raw_bytes:
                    st.session_state["pr_last_audio_bytes"] = raw_bytes
                    if tiene_gemini:
                        with st.spinner("🎧 Escuchando y transcribiendo tu voz a texto..."):
                            res_trans = transcribir_audio_gemini(raw_bytes, audio_in.type or "audio/wav", api_key)
                            if res_trans.get("exito"):
                                texto_transcrito = res_trans.get("texto", "")
                                st.session_state["pr_texto_input"] = texto_transcrito
                                st.session_state["pr_texto_area"] = texto_transcrito
                                st.toast("✅ ¡Dictado transcrito con éxito!", icon="🎙️")
                                st.rerun()
                            else:
                                st.error(f"Error al transcribir: {res_trans.get('error')}")

            if not tiene_gemini:
                st.markdown("---")
                with st.container(border=True):
                    st.markdown("🔑 **Pega tu clave gratuita de Google Gemini aquí:**")
                    st.caption("Obtén tu clave gratis en 1 minuto en [Google AI Studio](https://aistudio.google.com/)")
                    c_k1, c_k2 = st.columns([2.5, 1.2])
                    with c_k1:
                        inline_key = st.text_input("Clave Gemini:", type="password", placeholder="AIzaSy...", key="pr_inline_key_box", label_visibility="collapsed")
                    with c_k2:
                        if st.button("💾 Guardar", key="btn_save_inline_box", type="primary", use_container_width=True):
                            if inline_key.strip():
                                auditor_ia_rebt.guardar_gemini_api_key(inline_key.strip())
                                st.success("✅ ¡Guardada para siempre!")
                                st.rerun()

            st.markdown(
                """
                <div style='background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; padding: 8px 10px; font-size: 12px; margin-top: 8px;'>
                    💡 <b>Atajos de dictado rápido sin configuración:</b><br/>
                    • En PC: Pulsa <b>Tecla Windows + H</b> para dictar directamente en el texto.<br/>
                    • En Móvil/Tablet: Toca el icono de micrófono en tu teclado virtual.
                </div>
                """,
                unsafe_allow_html=True
            )

    with col_input1:
        txt_descripcion = st.text_area(
            "✍️ **2. Texto transcrito del trabajo (revísalo o modifícalo aquí):**",
            value=st.session_state.get("pr_texto_input", ""),
            placeholder="Aquí aparecerá lo que digas por el micrófono. También puedes escribirlo directamente:\nEj: Instalar línea para depuradora de piscina con reloj horario en cuadro estanco exterior y 15 metros de cable 3x2.5mm² con tubo corrugado M25.",
            height=135,
            key="pr_texto_area"
        )
        st.session_state["pr_texto_input"] = txt_descripcion

        col_txt_actions = st.columns([1, 1])
        with col_txt_actions[0]:
            if st.button("🧹 Borrar texto para nuevo dictado", key="btn_limpiar_pr_texto", use_container_width=True):
                st.session_state["pr_texto_input"] = ""
                st.session_state["pr_texto_area"] = ""
                st.session_state["pr_last_audio_bytes"] = None
                st.rerun()

    # Atajos de 1 Clic para avisos habituales
    st.markdown("**⚡ O pulsa una plantilla rápida si es un aviso habitual:**")
    col_at1, col_at2, col_at3, col_at4, col_at5, col_at6 = st.columns(6)
    if col_at1.button("🏊 Piscina", key="btn_at_dep", use_container_width=True):
        txt = "Instalación de línea protegida para depuradora de piscina con reloj programador horario modular carril DIN y magnetotérmico de 16A."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_texto_area"] = txt
        st.rerun()
    if col_at2.button("❄️ Clima", key="btn_at_clima", use_container_width=True):
        txt = "Línea independiente de climatización C9 de 16A bajo canaleta blanca con cable 3x2.5mm² y protección en cuadro con diferencial superinmunizado."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_texto_area"] = txt
        st.rerun()
    if col_at3.button("🚗 Recarga VE", key="btn_at_irve", use_container_width=True):
        txt = "Línea dedicada IRVE para recarga de coche eléctrico con cable 3x6mm², tubo M32, diferencial clase A e IGA 32A."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_texto_area"] = txt
        st.rerun()
    if col_at4.button("🔌 Derivación DI", key="btn_at_di", use_container_width=True):
        txt = "Derivación individual monofásica desde contadores hasta vivienda con cable libre de halógenos 2x10mm²+TT y tubo M40."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_texto_area"] = txt
        st.rerun()
    if col_at5.button("🍳 Horno/Vitro", key="btn_at_vitro", use_container_width=True):
        txt = "Circuito independiente C3 de 25A para horno y vitrocerámica con cable de 6mm² y base de enchufe de fuerza de 25A."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_texto_area"] = txt
        st.rerun()
    if col_at6.button("⚡ Cuadro CGMP", key="btn_at_cgmp", use_container_width=True):
        txt = "Sustitución de cuadro general de mando y protección con nuevo IGA 32A, protector de sobretensiones permanente y transitoria y 2 diferenciales de 40A."
        st.session_state["pr_texto_input"] = txt
        st.session_state["pr_texto_area"] = txt
        st.rerun()

    st.markdown("")
    btn_calcular = st.button("🚀 Calcular Presupuesto Inmediato con IA", type="primary", use_container_width=True, key="btn_pr_calcular")

    # 3. Procesamiento y Generación de Partidas
    if btn_calcular or ("pr_resultado_escandallo" in st.session_state and not btn_calcular):
        prompt_consulta = st.session_state.get("pr_texto_input", "").strip()

        if btn_calcular:
            if not prompt_consulta:
                st.warning("⚠️ Escribe o dicta el trabajo antes de pulsar en calcular.")
                return

            with st.spinner("⚙️ Estructurando memoria técnica oficial y escandallo REBT..."):
                resultado_final = None
                if tiene_gemini:
                    res_ia = analizar_trabajo_ia_gemini(prompt_consulta, api_key, precio_hora_mo)
                    if res_ia.get("exito"):
                        resultado_final = res_ia.get("resultado")

                if not resultado_final:
                    resultado_final = motor_reglas_rebt_rapido(prompt_consulta)

                resultado_final["consulta_orig"] = prompt_consulta
                st.session_state["pr_resultado_escandallo"] = resultado_final

                # Limpiar cualquier clave residual de la tabla anterior
                for k in list(st.session_state.keys()):
                    if k.startswith("prm_") or k == "pr_target_round":
                        del st.session_state[k]

        # 4. Visualización del Presupuesto Dinámico, Memoria Técnica y Escandallo
        res = st.session_state.get("pr_resultado_escandallo", {})
        if res:
            st.markdown("---")
            st.markdown(f"## 📋 Dictamen Oficial: **{res.get('concepto', 'Trabajo Eléctrico')}**")
            st.markdown(f"**Normativa REBT Aplicable:** `{res.get('norma', 'REBT RD 842/2002')}`")

            # SECCIÓN DESTACADA: MEMORIA TÉCNICA ESCRITA DETERMINADA POR LA IA
            st.markdown("#### 📄 Memoria y Determinación Técnica Escrita de la IA")
            tab_mem1, tab_mem2, tab_mem3 = st.tabs([
                "📝 Memoria y Alcance de Obra (Editable para Cliente)",
                "⚖️ Justificación Técnica e Ingeniería REBT",
                "🛠️ Protocolo de Montaje y Ensayos Oficiales (ITC-BT-05)"
            ])

            with tab_mem1:
                st.caption("Esta es la descripción exhaustiva formal generada por la IA. Puedes modificarla o adaptarla antes de imprimir o transferir al presupuesto:")
                memoria_val = st.text_area(
                    "Texto descriptivo formal para factura o presupuesto:",
                    value=res.get("descripcion_detallada", ""),
                    height=160,
                    key="pr_memoria_editable"
                )
                res["descripcion_detallada"] = memoria_val

            with tab_mem2:
                st.info(f"**Criterio Técnico y Reglamentario:**\n\n{res.get('justificacion_tecnica', 'Conforme a los criterios generales del REBT RD 842/2002.')}")

            with tab_mem3:
                c_pas1, c_pas2 = st.columns(2)
                with c_pas1:
                    st.markdown("**🔧 Pasos de Ejecución en Obra:**")
                    pasos_list = res.get("pasos_ejecucion", [])
                    for idx_p, p_item in enumerate(pasos_list, 1):
                        st.markdown(f"{idx_p}. {p_item}")
                with c_pas2:
                    st.markdown("**✅ Ensayos Reglamentarios Obligatorios (ITC-BT-05):**")
                    pruebas_list = res.get("pruebas_rebt", [])
                    for p_test in pruebas_list:
                        st.markdown(f"- 🧪 {p_test}")

            st.markdown("---")
            st.markdown("#### 📦 Escandallo Económico Desglosado")

            col_esc1, col_esc2 = st.columns([3, 2])

            with col_esc1:
                st.markdown("##### Materiales Desglosados (Modificables en tiempo real):")
                mats = res.get("materiales", [])
                total_mat_calc = 0.0

                filas_mats_edit = []
                for idx_m, m_item in enumerate(mats):
                    c_m1, c_m2, c_m3, c_m4 = st.columns([3, 1, 1.2, 1.2])
                    with c_m1:
                        key_n = f"prm_n_{idx_m}"
                        val_n = st.session_state.get(key_n, m_item.get("mat", ""))
                        n_mat = st.text_input(f"Mat {idx_m}", value=val_n, key=key_n, label_visibility="collapsed")
                    with c_m2:
                        key_c = f"prm_c_{idx_m}"
                        val_c = float(st.session_state.get(key_c, m_item.get("cant", 1.0)))
                        n_cnt = st.number_input(f"Cant {idx_m}", value=val_c, min_value=0.1, step=1.0, key=key_c, label_visibility="collapsed")
                    with c_m3:
                        key_p = f"prm_p_{idx_m}"
                        val_p = float(st.session_state.get(key_p, m_item.get("p_u", 10.0)))
                        n_pu = st.number_input(f"P.U {idx_m}", value=val_p, step=1.0, format="%.2f", key=key_p, label_visibility="collapsed")
                    with c_m4:
                        sub_m = round(n_cnt * n_pu, 2)
                        st.markdown(f"<div style='margin-top:6px; font-weight:bold;'>{sub_m:,.2f} €</div>", unsafe_allow_html=True)
                        total_mat_calc += sub_m
                    filas_mats_edit.append({"mat": n_mat, "cant": n_cnt, "unid": m_item.get("unid", "ud"), "p_u": n_pu, "subtotal": sub_m})

            with col_esc2:
                with st.container(border=True):
                    st.markdown("##### ⏱️ Mano de Obra y Totales:")
                    horas_default = float(res.get("horas", 2.5))
                    horas_mo_val = st.number_input("Horas de Mano de Obra (h):", value=horas_default, min_value=0.5, step=0.5, key="pr_horas_mo_in")
                    coste_mo_calc = round(horas_mo_val * precio_hora_mo, 2)

                    st.markdown(f"- **Mano de Obra:** `{horas_mo_val:.1f} h` × `{precio_hora_mo:.2f} €/h` = **`{coste_mo_calc:,.2f} €`**")
                    st.markdown(f"- **Total Materiales:** **`{total_mat_calc:,.2f} €`**")

                    subtotal_siva = round(total_mat_calc + coste_mo_calc, 2)
                    cuota_iva = round(subtotal_siva * (iva_pct / 100.0), 2)
                    total_civa = round(subtotal_siva + cuota_iva, 2)

                    st.markdown("---")
                    st.markdown(f"#### **Base Imponible (S/IVA):** `{subtotal_siva:,.2f} €`")
                    if iva_pct == 0.0:
                        st.markdown(f"#### **Total a Facturar (0% IVA):** `<span style='color:#059669; font-size:24px;'>{subtotal_siva:,.2f} €</span>`", unsafe_allow_html=True)
                        st.caption("ℹ️ Inversión de Sujeto Pasivo (Art. 84.Uno.2º.f LIVA) o Subcontrata.")
                    else:
                        st.markdown(f"#### **Total Cliente (C/IVA {iva_pct:.0f}%):** `<span style='color:#0284c7; font-size:24px;'>{total_civa:,.2f} €</span>`", unsafe_allow_html=True)

            # 5. Opciones de Negociación y Ajuste a Precio Cerrado
            st.markdown("---")
            col_neg1, col_neg2, col_neg3 = st.columns([1.5, 1.5, 2])
            with col_neg1:
                precio_base_redondeo = total_civa if iva_pct > 0 else subtotal_siva
                if "pr_target_round" not in st.session_state:
                    st.session_state["pr_target_round"] = float(round(precio_base_redondeo, 0))
                target_quick = st.number_input("🎯 Ajustar a Precio Redondo Cerrado (€):", step=10.0, format="%.2f", key="pr_target_round")
            with col_neg2:
                dif_quick = target_quick - precio_base_redondeo
                signo = "+" if dif_quick > 0 else ""
                st.caption(f"Ajuste comercial aplicado: `{signo}{dif_quick:,.2f} €`")
                st.markdown(f"**Precio Final Acordado:** `{target_quick:,.2f} €`")
            with col_neg3:
                if st.button("📥 Incorporar a Presupuesto Vivienda", type="primary", use_container_width=True, key="btn_transfer_to_vivienda"):
                    if "partidas_manuales" not in st.session_state:
                        st.session_state.partidas_manuales = []
                    sub_final_siva = round(target_quick / (1 + (iva_pct / 100.0)), 2)
                    st.session_state.partidas_manuales.append({
                        "id": f"PM-{len(st.session_state.partidas_manuales) + 1:02d}",
                        "concepto": res.get("concepto", "Trabajo Eléctrico"),
                        "descripcion": res.get("descripcion_detallada", f"Instalación según {res.get('norma', 'REBT')}: {res.get('consulta_orig', '')}"),
                        "cantidad": 1.0,
                        "unidad": "partida",
                        "precio_unitario": sub_final_siva,
                        "subtotal": sub_final_siva
                    })
                    st.session_state.presupuesto_calculado = True
                    st.success(f"✅ Trabajo '{res.get('concepto')}' transferido con su memoria completa al Presupuesto de Vivienda.")
