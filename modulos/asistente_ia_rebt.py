# -*- coding: utf-8 -*-
"""
Módulo de Asistente Inteligente REBT: Experto Instalador con Visión de Ingeniero Eléctrico
Permite al instalador resolver dudas técnicas, reglamentarias, de diseño, tramitación en Industria (DGEAIM Murcia)
y trucos de ejecución a pie de obra. Soporta motor online (Google Gemini) y motor offline de base de conocimiento experto.
"""

import streamlit as st
import json
import os
import requests
from modulos import auditor_ia_rebt

SYSTEM_PROMPT_INGENIERO_INSTALADOR = """
Eres el Consultor Senior de Ingeniería Eléctrica y Maestro Instalador Habilitado de Bolimur.
Combinas dos perfiles complementarios:
1. Vista de Ingeniero Eléctrico: Riguroso en el Reglamento Electrotécnico para Baja Tensión (REBT 2002 - RD 842/2002),
   sus Instrucciones Técnicas Complementarias (ITC-BT-01 a ITC-BT-52), Guías Técnicas de Aplicación del Ministerio
   y criterios de la Dirección General de Energía y Actividad Industrial y Minera (DGEAIM - Región de Murcia).
2. Maestro Instalador Electricista de Campo: Práctico, con 25 años de experiencia a pie de obra. Conoces la realidad del tubo corrugado,
   cajas de derivación, marcas habituales (Schneider, Hager, Legrand, Simon, Prysmian, Top Cable), uso de comprobadores
   multifunción (Kyoritsu, Fluke, Megger) y los defectos más frecuentes que tumban expedientes en Industria y OCAs.

Tus principios de respuesta:
- Cita siempre que sea aplicable la ITC-BT exacta (ej. ITC-BT-04, ITC-BT-15, ITC-BT-17, ITC-BT-18, ITC-BT-25, etc.).
- Si la consulta involucra una instalación que supera los límites de MTD (como bares, restaurantes, locales de pública concurrencia,
  garajes > 5 coches o potencias > 50/100 kW), advierte claramente que requiere PROYECTO TÉCNICO visado por Ingeniero Colegiado y OCA.
- Sé claro, directo y estructurado (utiliza viñetas, tablas markdown y fórmulas KaTeX cuando haya cálculos de caída de tensión o potencias).
- Aporta tanto la fórmula y el artículo legal como el consejo práctico de taller o montaje para que el instalador no tenga problemas con el cliente ni con el perito del seguro.
- Responde siempre en español profesional, técnico y motivador.
"""

BASE_CONOCIMIENTO_OFFLINE = [
    {
        "keywords": ["proyecto", "ingeniero", "mtd", "limite", "firmar", "bar", "restaurante", "publica concurrencia"],
        "pregunta": "¿Cuándo se necesita Proyecto de Ingeniero en lugar de MTD?",
        "respuesta": """### ⚖️ Proyecto de Ingeniero vs Memoria Técnica de Diseño (MTD) - ITC-BT-04

El REBT (Tabla 3.1 de la ITC-BT-04) fija límites infranqueables:

1. **Instalaciones que exigen OBLIGATORIAMENTE Proyecto de Ingeniero:**
   - **Locales de Pública Concurrencia (LPC - ITC-BT-28):** Bares, restaurantes, discotecas, cines, clínicas, academias, centros comerciales $\rightarrow$ **Cualquier potencia (desde 0 kW)**. *¡Nunca se pueden tramitar mediante MTD!*
   - **Locales con riesgo de incendio o explosión (ITC-BT-29):** Gasolineras, talleres de automóviles, carpinterías $\rightarrow$ **Cualquier potencia**.
   - **Garajes y aparcamientos:** Con ventilación forzada mecánica o para más de **5 vehículos**.
   - **Edificios de viviendas:** Potencia total prevista $> 100\\text{ kW}$.
   - **Viviendas unifamiliares:** Potencia instalada $> 50\\text{ kW}$.
   - **Industrias / Naves fabriles:** Potencia instalada $> 20\\text{ kW}$.
   - **Alumbrado público exterior:** Potencia instalada $> 5\\text{ kW}$.
   - **Puntos de Recarga VE (ITC-BT-52):** En interior $> 50\\text{ kW}$ o exterior $> 10\\text{ kW}$.

2. **Lo que SÍ puede diseñar y firmar el Instalador Autorizado con MTD:**
   - Viviendas unifamiliares habituales (básica $5.750\\text{ W}$ o elevada $9.200\\text{ W}$).
   - Edificios de viviendas con potencia total $\\le 100\\text{ kW}$.
   - Pequeños comercios (no pública concurrencia) $\\le 50\\text{ kW}$ o $\\le 100\\text{ kW}$.
   - Cuadros temporales de obra (ITC-BT-33) $\\le 50\\text{ kW}$.
   - Puntos de recarga de vehículos eléctricos en viviendas o garajes comunitarios $\\le 50\\text{ kW}$.

> 💡 **Consejo de Ingeniero:** Si intentas tramitar una MTD para un bar o taller, la plataforma telemática de Industria (DGEAIM Murcia) te rechazará el trámite de inmediato y te exigirá visado colegial y dirección técnica de obra."""
    },
    {
        "keywords": ["derivacion individual", "di", "caida de tension", "seccion", "tubo", "itc-bt-15"],
        "pregunta": "¿Cómo se dimensiona y qué requisitos tiene una Derivación Individual (DI)?",
        "respuesta": """### 🔌 Derivación Individual (DI) - Normativa ITC-BT-15

La DI enlaza la centralización de contadores con el cuadro general (CGMP) de cada usuario.

1. **Límites de Caída de Tensión Máxima admisible ($\\Delta V$):**
   - **Contadores totalmente concentrados:** Máximo **$1,5\\%$** (ej. $3,45\\text{ V}$ a $230\\text{ V}$).
   - **Contadores concentrados por plantas:** Máximo **$1,0\\%$**.
   - **Suministro individual para un solo usuario (sin LGA previa):** Máximo **$1,5\\%$**.

2. **Secciones Mínimas Reglamentarias:**
   - **Cobre (Cu):** Mínimo **$6\\text{ mm}^2$** (independientemente de que por cálculo saliera menos).
   - **Aluminio (Al):** Mínimo **$16\\text{ mm}^2$**.
   - Conductor de neutro: Misma sección que las fases. Conductor de protección (tierra PE): Misma sección hasta $16\\text{ mm}^2$.

3. **Cálculo de la Sección por Caída de Tensión (Monofásica a 230V):**
   $$S = \\frac{2 \\cdot L \\cdot P}{\\gamma \\cdot \\Delta V \\cdot V_n} = \\frac{2 \\cdot L \\cdot P}{44 \\cdot (0,015 \\cdot 230) \\cdot 230}$$
   *(Donde $\\gamma = 44\\text{ m}/(\\Omega\\cdot\\text{mm}^2)$ para cobre a 90ºC en servicio permanente).*

4. **Tubo Protector y Conductores:**
   - Tubo protector mínimo: **Diámetro exterior $32\\text{ mm}$ (M32)**.
   - Cables obligatorios: No propagadores del incendio y con emisión de humos y opacidad reducida (cables libres de halógenos tipo **H07Z1-K** o **RZ1-K 0.6/1kV** clase $C_{ca}\\text{-s1b,d1,a1}$)."""
    },
    {
        "keywords": ["diferencial", "diferenciales", "5 circuitos", "cuantos circuitos", "itc-bt-25", "30ma"],
        "pregunta": "¿Cuántos circuitos magnetotérmicos (PIAs) se pueden conectar por cada diferencial?",
        "respuesta": """### 🛡️ Regla de los Diferenciales - ITC-BT-25 (Punto 2.1)

1. **El límite reglamentario estricto:**
   - El REBT establece taxativamente: **Máximo 5 circuitos por cada interruptor diferencial de $30\\text{ mA}$**.
   - Si tu instalación tiene 6 circuitos, **es obligatorio colocar al menos 2 interruptores diferenciales**.

2. **Intensidad Asignada del Diferencial ($I_n$):**
   - El diferencial debe estar protegido contra sobrecargas por el IGA situado aguas arriba:
     - Si tu IGA es de **$25\\text{ A}$** $\\rightarrow$ El diferencial debe ser de **$25\\text{ A}$ o $40\\text{ A}$**.
     - Si tu IGA es de **$32\\text{ A}$ o $40\\text{ A}$** $\\rightarrow$ El diferencial debe ser obligatoriamente de **$40\\text{ A}$ o mayor**.
     *(En la práctica se instala siempre de $40\\text{ A} / 30\\text{ mA}$ por economía de escala).*

3. **Tipo / Clase de Diferencial:**
   - **Clase AC:** Permitido históricamente para cargas puramente resistivas, pero desaconsejado hoy en día.
   - **Clase A / Superinmunizado (Recomendado):** Obligatorio en puntos de recarga IRVE y altamente recomendado para circuitos de informática, lavadoras inverter, frigoríficos y aire acondicionado, evitando disparos intempestivos provocados por armónicos."""
    },
    {
        "keywords": ["tierra", "resistencia", "pica", "ohmios", "itc-bt-18", "valor de tierra"],
        "pregunta": "¿Cuál es el valor máximo reglamentario de la resistencia de toma de tierra?",
        "respuesta": """### 🌍 Resistencia de Puesta a Tierra - ITC-BT-18 e ITC-BT-24

El REBT no fija un valor numérico único fijo (como 15 o 30 $\\Omega$), sino que vincula la resistencia de tierra al valor de disparo del diferencial para garantizar que **la tensión de contacto jamás supere la tensión de seguridad ($U_L$)**:

$$R_A \\le \\frac{U_L}{I_{\\Delta n}}$$

1. **Valores según la Tensión Límite de Seguridad:**
   - **Locales secos ($U_L = 50\\text{ V}$):** Con diferencial de $30\\text{ mA}$ ($0,03\\text{ A}$):
     $$R_A \\le \\frac{50\\text{ V}}{0,03\\text{ A}} = 1.666\\ \\Omega$$
   - **Locales húmedos / Obras / Exterior ($U_L = 24\\text{ V}$):**
     $$R_A \\le \\frac{24\\text{ V}}{0,03\\text{ A}} = 800\\ \\Omega$$

2. **El estándar de buena práctica profesional y normas de compañía:**
   - **Edificios con pararrayos (ITC-BT-23 / CTE DB-SUA 8):** Máximo **$15\\ \\Omega$** (o preferiblemente $< 10\\ \\Omega$).
   - **Buena práctica en viviendas habituales:** El valor medido en obra debe quedar preferiblemente **por debajo de $15 - 20\\ \\Omega$** para absorber corrientes de sobretensiones transitorias y garantizar la seguridad ante fallos de los diferenciales.

3. **Electrodo y Conductor de Tierra:**
   - Pica mínima: Acero cobreado de **$2\\text{ metros}$** de longitud y $14\\text{ mm}$ de diámetro.
   - Conductor de tierra de enlace: Cobre desnudo de **$35\\text{ mm}^2$** o cobre aislado de **$16\\text{ mm}^2$**."""
    },
    {
        "keywords": ["sobretensiones", "vtp", "transitorias", "permanentes", "murcia", "itc-bt-23"],
        "pregunta": "¿Qué exige Industria sobre las protecciones contra sobretensiones en Murcia?",
        "respuesta": """### ⚡ Protecciones contra Sobretensiones - ITC-BT-23 y Normativa de Murcia

En la Región de Murcia (DGEAIM) y según las especificaciones técnicas de la distribuidora i-DE (Iberdrola), es **obligatorio instalar protección combinada contra sobretensiones** en todas las nuevas altas y reformas integrales:

1. **Sobretensiones Permanentes (POP / VTP):**
   - Provocadas por rotura o descompensación del neutro en la red de distribución (la tensión sube de 230V a 400V).
   - Exigencia: **Bobina de disparo asociada al Interruptor General Automático (IGA)**. Si la tensión supera los 265 V durante más de unos milisegundos, dispara el IGA desconectando toda la vivienda para que no se quemen los electrodomésticos.

2. **Sobretensiones Transitorias (DPS / VSP):**
   - Provocadas por rayos o maniobras bruscas en la red de media/alta tensión (picos de miles de voltios en microsegundos).
   - Exigencia: Descargador de sobretensiones **Tipo 2** derivado a tierra antes del diferencial.

3. **Consejo práctico de taller:**
   - Se instalan los bloques monobloc compactos **IGA + Bobina Permanente + Descargador Transitorio** (marcas como Toscano Combi-Pro, Schneider Acti9 iQuick, Circutor o Hager). Ocupan 3 o 4 módulos y resuelven el 100% de los requisitos de Industria en Murcia."""
    },
    {
        "keywords": ["cuadro de obra", "obra", "provisional", "itc-bt-33"],
        "pregunta": "¿Qué requisitos reglamentarios debe tener un Cuadro de Obra (ITC-BT-33)?",
        "respuesta": """### 🏗️ Instalaciones Provisionales y Cuadros de Obra - ITC-BT-33

1. **Límite de tramitación MTD:** Hasta **$50\\text{ kW}$** se tramita mediante Memoria Técnica de Diseño (MTD 30). Si la potencia de obra supera los $50\\text{ kW}$, requiere Proyecto de Ingeniero.
2. **Envolvente del Cuadro:**
   - Mínimo grado de protección **IP45** (o IP54 en exteriores desprotegidos) y resistencia al impacto **IK08**.
   - Debe disponer de puerta con cerradura para evitar manipulación por personal no autorizado.
3. **Protecciones Obligatorias:**
   - **Interruptor de parada de emergencia exterior tipo seta** visible y accesible.
   - **Interruptores Diferenciales de $30\\text{ mA}$ Clase A** para todas las tomas de corriente $\\le 32\\text{ A}$.
   - Magnetotérmicos con poder de corte mínimo de **$6\\text{ kA}$**.
4. **Puesta a Tierra y Comprobaciones:**
   - Tensión límite de contacto estricta: **$U_L = 24\\text{ V}$** (local mojado/obra).
   - Pica de tierra con arqueta propia independiente identificada.
   - Obligatorio realizar ensayos periódicos mensuales del pulsador de prueba (test T) de los diferenciales."""
    },
    {
        "keywords": ["recarga", "coche electrico", "irve", "itc-bt-52", "wallbox"],
        "pregunta": "¿Qué exige la ITC-BT-52 para la instalación de puntos de recarga de vehículos eléctricos?",
        "respuesta": """### 🚗 Infraestructura para Recarga de Vehículos Eléctricos - ITC-BT-52

1. **Esquemas de Conexión más habituales:**
   - **Esquema 2:** Contador individual en centralización compartida con la vivienda (canalización propia desde el cuadro de contadores a la plaza de garaje).
   - **Esquema 4:** Derivación directa desde el propio cuadro general (CGMP) de la vivienda unifamiliar.
2. **Protecciones del Circuito Dedicado (Línea Wallbox):**
   - **Interruptor Magnetotérmico:** Curva C, calibre acorde al cargador (ej. **$32\\text{ A}$** para punto de $7,4\\text{ kW}$ o **$16\\text{ A}$** para $3,7\\text{ kW}$).
   - **Diferencial específico:** Debe ser **Clase A de $30\\text{ mA}$** con dispositivo de detección de fugas en corriente continua de $6\\text{ mA}$ (según norma **IEC 62955**), o directamente un diferencial **Clase B**.
   - **Protector contra sobretensiones permanentes y transitorias:** Obligatorio en el circuito de recarga.
3. **Cableado y Tubos:**
   - Sección mínima habitual: **$6\\text{ mm}^2$** en cobre libre de halógenos ($C_{ca}\\text{-s1b,d1,a1}$) bajo tubo M32.
   - Caída de tensión máxima permitida en la línea IRVE: **$5\\%$** desde el origen."""
    }
]

import re

def buscar_respuesta_offline(consulta: str) -> str:
    """Busca la mejor coincidencia técnica en la base de conocimiento offline REBT."""
    c_lower = consulta.lower()
    mejor_match = None
    max_puntos = 0
    
    for item in BASE_CONOCIMIENTO_OFFLINE:
        puntos = 0
        for kw in item["keywords"]:
            # Buscar coincidencia de palabra completa o frase exacta
            if " " in kw:
                if kw in c_lower:
                    puntos += 3  # Frase completa tiene mayor peso
            else:
                if re.search(r'\b' + re.escape(kw) + r'\b', c_lower):
                    puntos += 2  # Palabra aislada exacta
        
        if puntos > max_puntos:
            max_puntos = puntos
            mejor_match = item
            
    if mejor_match and max_puntos >= 2:
        return mejor_match["respuesta"]
        
    return (
        "### 📚 Dictamen Técnico REBT - Base Experta Bolimur\n\n"
        f"Has consultado: *\"{consulta}\"*\n\n"
        "Para responder con máxima exactitud según el **Reglamento Electrotécnico para Baja Tensión (REBT 2002)** "
        "y los criterios de la **DGEAIM (Murcia)**:\n\n"
        "1. **Marco Normativo General:** Toda instalación debe diseñarse calculando la caída de tensión máxima admisible "
        "(1,5% en DI, 3% en alumbrado, 5% en fuerza) y verificando la intensidad admisible térmica ($I_z$) según el método de instalación "
        "en tubo bajo la norma UNE-HD 60364-5-52.\n"
        "2. **Límites de Proyecto (ITC-BT-04):** Si la instalación corresponde a pública concurrencia (bar, clínica, local > 50 pers.), "
        "garaje > 5 plazas o potencia > 50 kW, requiere obligatoriamente **Proyecto visado por Ingeniero** e inspección de OCA.\n"
        "3. **Protecciones de Seguridad:** Es imprescindible garantizar el corte omnipolar con IGA, protección contra sobretensiones "
        "permanentes y transitorias (ITC-BT-23) y respetar el límite de **máximo 5 circuitos por diferencial de 30 mA** (ITC-BT-25).\n\n"
        "> 💡 *Tip Pro:* Si dispones de clave gratuita de Google Gemini (puedes activarla en el desplegable superior), "
        "el asistente analizará tu caso particular con razonamiento profundo en tiempo real."
    )

import re
import io
import base64

def procesar_archivo_camara_o_adjunto(uploaded_file) -> str:
    """
    Procesa un archivo tomado desde la cámara o subido (JPG, PNG, PDF de 1 página)
    y lo convierte en una data URI base64 optimizada para visión artificial.
    """
    if uploaded_file is None:
        return ""
    try:
        raw_bytes = uploaded_file.getvalue()
        # Si es un PDF, renderizar primera página a PNG con PyMuPDF
        if raw_bytes.startswith(b"%PDF"):
            try:
                import fitz
                pdf_doc = fitz.open(stream=raw_bytes, filetype="pdf")
                if len(pdf_doc) > 0:
                    page = pdf_doc[0]
                    pix = page.get_pixmap(dpi=150)
                    raw_bytes = pix.tobytes("png")
                pdf_doc.close()
            except Exception as e_pdf:
                st.error(f"Error procesando archivo PDF: {e_pdf}")
                return ""

        from PIL import Image as PILImage
        bio_in = io.BytesIO(raw_bytes)
        with PILImage.open(bio_in) as im:
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            # Redimensionar a máx 1600px manteniendo relación de aspecto
            im.thumbnail((1600, 1600), PILImage.Resampling.LANCZOS)
            bio_out = io.BytesIO()
            im.save(bio_out, format="JPEG", quality=85, optimize=True)
            b64_str = base64.b64encode(bio_out.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        st.error(f"Error procesando imagen para la IA: {e}")
        return ""

def consultar_gemini_rebt(consulta: str, historial: list, api_key: str, imagen_b64: str = None, audio_b64: str = None, audio_mime: str = "audio/wav") -> str:
    """Consulta al modelo Google Gemini con el system prompt de Ingeniero Eléctrico e Instalador REBT, con soporte multimodal (texto, imágenes y audio de voz)."""
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # Construir contenido
    contents = []
    for h in historial[-6:]: # Contexto de mensajes previos
        role = "user" if h["role"] == "user" else "model"
        parts = [{"text": h["content"]}]
        contents.append({"role": role, "parts": parts})
    
    # Mensaje actual del usuario con imagen y/o audio opcionales
    prompt_texto = consulta.strip()
    if not prompt_texto:
        if audio_b64:
            prompt_texto = "Escucha atentamente este mensaje de voz del instalador eléctrico, atiende su consulta o instrucción y respóndele con rigor según el REBT y criterios de ingeniería eléctrica."
        elif imagen_b64:
            prompt_texto = "Analiza detalladamente esta imagen técnica según el REBT y criterios de ingeniería eléctrica."
        else:
            prompt_texto = "Hola, ¿en qué me puedes ayudar hoy con el REBT?"

    user_parts = [{"text": prompt_texto}]
    
    # Adjuntar imagen si existe
    if imagen_b64:
        mime_type, clean_b64 = auditor_ia_rebt._limpiar_b64_imagen(imagen_b64)
        if clean_b64:
            user_parts.append({
                "inlineData": {
                    "mimeType": mime_type,
                    "data": clean_b64
                }
            })

    # Adjuntar audio de voz si existe
    if audio_b64:
        user_parts.append({
            "inlineData": {
                "mimeType": audio_mime or "audio/wav",
                "data": audio_b64
            }
        })
            
    contents.append({"role": "user", "parts": user_parts})
    
    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT_INGENIERO_INSTALADOR}]
        },
        "generationConfig": {
            "temperature": 0.25,
            "topP": 0.85,
            "maxOutputTokens": 2000
        }
    }
    
    try:
        resp = requests.post(endpoint, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            cands = data.get("candidates", [])
            if cands:
                texto = cands[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if texto.strip():
                    return texto.strip()
    except Exception:
        pass
        
    # Fallback a gemini-1.5-flash
    endpoint_fb = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    try:
        resp = requests.post(endpoint_fb, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            cands = data.get("candidates", [])
            if cands:
                texto = cands[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if texto.strip():
                    return texto.strip()
    except Exception:
        pass
        
    return responder_consulta_offline_con_imagen(consulta, imagen_b64)

def responder_consulta_offline_con_imagen(consulta: str, imagen_b64: str = None) -> str:
    """Responde en modo offline combinando la base de conocimiento y el motor de reglas REBT si hay imagen."""
    if imagen_b64:
        res_auditoria = auditor_ia_rebt._auditar_con_motor_reglas_rebt(
            tipo_evidencia=consulta or "Evidencia de Obra / Cuadro Eléctrico",
            descripcion_usuario=consulta or "Consulta sobre imagen"
        )
        dictamen_md = (
            f"### 🔍 Diagnóstico Técnico Offline sobre la Imagen (REBT)\n\n"
            f"**Dictamen Preliminar:** `{res_auditoria.get('calificacion', 'Inspección REBT')}`\n\n"
            f"{res_auditoria.get('resumen', '')}\n\n"
            "**Elementos Verificados reglamentariamente:**\n"
        )
        for e in res_auditoria.get("elementos_identificados", []):
            dictamen_md += f"- {e}\n"
            
        dictamen_md += "\n**Comprobaciones de Seguridad:**\n"
        for c in res_auditoria.get("comprobaciones", []):
            dictamen_md += f"- ✅ **{c.get('criterio')}** (`{c.get('norma_rebt')}`): {c.get('detalle')}\n"
            
        dictamen_md += "\n**Recomendaciones del Instalador e Ingeniero:**\n"
        for r in res_auditoria.get("recomendaciones", []):
            dictamen_md += f"• {r}\n"
            
        dictamen_md += "\n> 💡 *Nota:* Para análisis visual profundo con reconocimiento de lectura de pantallas o cableado real, introduce tu clave gratuita de Google Gemini en el panel superior."
        return dictamen_md
        
    return buscar_respuesta_offline(consulta)

def responder_consulta_rebt(consulta: str, historial: list = None, imagen_b64: str = None, audio_b64: str = None, audio_mime: str = "audio/wav") -> str:
    """Enruta la consulta a Gemini con soporte multimodal (texto, fotos y voz) o al motor offline."""
    key = auditor_ia_rebt.obtener_gemini_api_key()
    if key and len(key) > 10:
        return consultar_gemini_rebt(consulta, historial or [], key, imagen_b64=imagen_b64, audio_b64=audio_b64, audio_mime=audio_mime)
    if audio_b64:
        return (
            "### 🎙️ Mensaje de Voz Recibido\n\n"
            "Has grabado una consulta de voz para la IA. Para escuchar y comprender audio directamente en tiempo real, "
            "activa tu clave gratuita de Google Gemini en el panel superior `⚙️ Estado del Motor`.\n\n"
            "💡 **Truco directo sin clave:** Puedes dictar con tu propia voz utilizando el atajo del teclado de Windows "
            "presionando **`Tecla Windows + H`** en cualquier momento, o tocando el micrófono de tu teclado en el móvil."
        )
    return responder_consulta_offline_con_imagen(consulta, imagen_b64)

def render_interfaz_asistente_rebt():
    """Renderiza la interfaz principal del Consultor IA REBT."""
    st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🤖 Consultor IA: Experto REBT & Ingeniero Eléctrico de Bolimur</h3></div>', unsafe_allow_html=True)
    st.caption("Tu asesor técnico 24/7 para resolver cualquier duda reglamentaria del REBT, cálculos de caídas de tensión, coordinación de protecciones, límites de MTD vs Proyecto y requisitos de Industria en Murcia.")

    # Barra superior de configuración rápida de IA
    api_key_actual = auditor_ia_rebt.obtener_gemini_api_key()
    tiene_key = bool(api_key_actual and len(api_key_actual) > 10)

    with st.expander("⚙️ Estado del Motor de Inteligencia Artificial", expanded=False):
        col_st1, col_st2 = st.columns([3, 1.2])
        with col_st1:
            if tiene_key:
                st.success("🟢 **Modo Online Activo (Google Gemini 2.0 / 1.5 Flash)**: Capacidad total de razonamiento técnico y normativo.")
            else:
                st.info("ℹ️ **Modo Offline Activo (Base Experta REBT Bolimur)**: Consultas automáticas guiadas por las 52 ITCs del REBT.")
            key_in = st.text_input("Clave API de Gemini (Gratuita en Google AI Studio):", value=api_key_actual if tiene_key else "", type="password", key="txt_ia_chat_key")
        with col_st2:
            st.write("")
            st.write("")
            if st.button("💾 Guardar Clave", key="btn_save_ia_chat_key", use_container_width=True):
                auditor_ia_rebt.guardar_gemini_api_key(key_in)
                st.success("Clave guardada.")
                st.rerun()

    # Bloque de captura con Micrófono (Voz), Cámara o Subida de Archivos
    if "ia_chat_imagen_activa" not in st.session_state:
        st.session_state["ia_chat_imagen_activa"] = None

    with st.expander("🎙️ Instrucciones de Voz, Cámara en Vivo y Documentos", expanded=bool(st.session_state.get("ia_chat_imagen_activa"))):
        tab_mic, tab_cam, tab_up = st.tabs(["🎙️ Hablar por Micrófono (Voz)", "📸 Tomar Foto con la Cámara", "📁 Subir Archivo (JPG, PNG, PDF)"])
        
        with tab_mic:
            st.caption("Graba tu voz para hacer una consulta o darle una instrucción directa a la IA:")
            audio_pic = st.audio_input("Hablar por micrófono a la IA", key="voice_mic_ia_chat")
            if audio_pic is not None:
                st.audio(audio_pic)
                col_va1, col_va2 = st.columns([1.8, 3])
                with col_va1:
                    if st.button("🚀 Enviar Instrucción de Voz a la IA", type="primary", key="btn_send_voice_direct"):
                        raw_audio = audio_pic.getvalue()
                        b64_audio = base64.b64encode(raw_audio).decode("utf-8")
                        mime_aud = audio_pic.type or "audio/wav"
                        img_actual = st.session_state.get("ia_chat_imagen_activa")
                        st.session_state["ia_chat_imagen_activa"] = None

                        st.session_state.mensajes_chat_rebt.append({
                            "role": "user",
                            "content": "🎙️ [Instrucción de voz enviada por micrófono]",
                            "audio": raw_audio,
                            "image": img_actual
                        })
                        with st.spinner("Escuchando y analizando instrucción de voz según el REBT y criterios de ingeniería..."):
                            resp = responder_consulta_rebt(
                                consulta="",
                                historial=st.session_state.mensajes_chat_rebt[:-1],
                                imagen_b64=img_actual,
                                audio_b64=b64_audio,
                                audio_mime=mime_aud
                            )
                            st.session_state.mensajes_chat_rebt.append({"role": "assistant", "content": resp})
                        st.rerun()
                with col_va2:
                    st.caption("💡 *Tip:* Puedes combinar una foto tomada con la cámara y una nota de voz preguntando sobre ella.")

        with tab_cam:
            st.caption("Apunta con la cámara de tu móvil o portátil al cuadro eléctrico, pica de tierra, rotulación o display:")
            cam_pic = st.camera_input("Capturar foto desde el dispositivo", key="cam_input_ia_chat")
            if cam_pic is not None:
                b64_cam = procesar_archivo_camara_o_adjunto(cam_pic)
                if b64_cam:
                    st.session_state["ia_chat_imagen_activa"] = b64_cam

        with tab_up:
            st.caption("Sube un esquema unifilar, plano o fotografía desde tu galería o disco (PNG, JPG, PDF):")
            up_file = st.file_uploader("Seleccionar archivo técnico:", type=["png", "jpg", "jpeg", "webp", "pdf"], key="file_up_ia_chat")
            if up_file is not None:
                b64_up = procesar_archivo_camara_o_adjunto(up_file)
                if b64_up:
                    st.session_state["ia_chat_imagen_activa"] = b64_up

        if st.session_state.get("ia_chat_imagen_activa"):
            col_prev1, col_prev2 = st.columns([1.2, 3])
            with col_prev1:
                st.image(st.session_state["ia_chat_imagen_activa"], caption="Evidencia lista para consultar", width=220)
                if st.button("🗑️ Descartar Imagen", key="btn_del_chat_img"):
                    st.session_state["ia_chat_imagen_activa"] = None
                    st.rerun()
            with col_prev2:
                st.info("✅ **Imagen adjunta cargada**. Escribe tu consulta abajo, habla por el micrófono o pulsa el botón directo para una auditoría general:")
                if st.button("🔍 Auditar esta Imagen con IA", type="primary", key="btn_analizar_img_directo"):
                    img_actual = st.session_state["ia_chat_imagen_activa"]
                    txt_q = "Analiza detalladamente esta imagen técnica según el REBT y criterios de ingeniería eléctrica. Identifica componentes, comprueba cumplimiento normativo y señala cualquier defecto o mejora."
                    st.session_state.mensajes_chat_rebt.append({
                        "role": "user",
                        "content": txt_q,
                        "image": img_actual
                    })
                    st.session_state["ia_chat_imagen_activa"] = None
                    with st.spinner("Analizando imagen con visión técnica e ingeniería REBT..."):
                        resp = responder_consulta_rebt(txt_q, st.session_state.mensajes_chat_rebt[:-1], imagen_b64=img_actual)
                        st.session_state.mensajes_chat_rebt.append({"role": "assistant", "content": resp})
                    st.rerun()

    # Preguntas Rápidas Frecuentes
    st.markdown("##### ⚡ Consultas Rápidas de Taller y Obra:")
    pills = [
        "⚖️ ¿Cuándo necesito Proyecto de Ingeniero en vez de MTD?",
        "🔌 ¿Cómo se calcula la sección de una Derivación Individual?",
        "🛡️ ¿Cuántos circuitos puedo poner bajo un diferencial de 30mA?",
        "🏗️ ¿Qué exige la norma para un Cuadro de Obra (ITC-BT-33)?",
        "🌍 ¿Qué valor de tierra me exige el REBT y cómo medirlo?",
        "⚡ ¿Qué sobretensiones son obligatorias en Murcia?",
        "🚗 ¿Qué protecciones exige la ITC-BT-52 para recarga VE?"
    ]

    cols_pills = st.columns(len(pills))
    pregunta_seleccionada = None
    for idx, p_text in enumerate(pills):
        with cols_pills[idx]:
            # Botón compacto
            lbl = p_text.split("¿")[0].strip() + " " + p_text.split("¿")[1].split("?")[0][:18] + "..."
            if st.button(lbl, key=f"btn_pill_{idx}", help=p_text, use_container_width=True):
                pregunta_seleccionada = p_text

    # Inicializar historial de chat
    if "mensajes_chat_rebt" not in st.session_state:
        st.session_state.mensajes_chat_rebt = [
            {
                "role": "assistant",
                "content": (
                    "¡Hola! Soy tu **Consultor de Ingeniería y Maestro Instalador REBT** de Bolimur. "
                    "Estoy preparado para resolver cualquier duda sobre cálculos eléctricos, dimensionamiento de conductores, "
                    "aparamenta, esquemas unifilares, tramitación de MTD ante Industria (DGEAIM Murcia) o límites legales de la ITC-BT-04.\n\n"
                    "📷 **Novedad:** Ahora puedes **tomar fotos con tu cámara o adjuntar planos y PDFs** en el panel superior para que los revise y te dé mi dictamen.\n\n"
                    "¿Qué instalación estás ejecutando o qué consulta técnica tienes hoy?"
                )
            }
        ]

    # Procesar si se seleccionó una píldora rápida
    if pregunta_seleccionada:
        img_p = st.session_state.get("ia_chat_imagen_activa")
        st.session_state["ia_chat_imagen_activa"] = None
        user_p = {"role": "user", "content": pregunta_seleccionada}
        if img_p:
            user_p["image"] = img_p
        st.session_state.mensajes_chat_rebt.append(user_p)
        with st.spinner("Consultando normativa técnica REBT y criterios de ingeniería..."):
            resp = responder_consulta_rebt(pregunta_seleccionada, st.session_state.mensajes_chat_rebt[:-1], imagen_b64=img_p)
            st.session_state.mensajes_chat_rebt.append({"role": "assistant", "content": resp})
        st.rerun()

    # Mostrar mensajes del chat
    st.markdown("---")
    chat_container = st.container()
    with chat_container:
        for m in st.session_state.mensajes_chat_rebt:
            if m["role"] == "user":
                with st.chat_message("user", avatar="👷"):
                    if m.get("audio"):
                        st.audio(m["audio"])
                    if m.get("image"):
                        st.image(m["image"], caption="📷 Evidencia técnica adjunta", width=320)
                    st.markdown(m["content"])
            else:
                with st.chat_message("assistant", avatar="⚡"):
                    st.markdown(m["content"])

    # Entrada del usuario en la parte inferior
    prompt = st.chat_input("Escribe tu consulta o pregunta sobre la imagen adjunta (ej: ¿Este cuadro cumple con la ITC-BT-17?)...")
    if prompt:
        img_enviar = st.session_state.get("ia_chat_imagen_activa")
        st.session_state["ia_chat_imagen_activa"] = None
        
        user_entry = {"role": "user", "content": prompt}
        if img_enviar:
            user_entry["image"] = img_enviar
        st.session_state.mensajes_chat_rebt.append(user_entry)
        
        with st.chat_message("user", avatar="👷"):
            if img_enviar:
                st.image(img_enviar, caption="📷 Evidencia técnica adjunta", width=320)
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="⚡"):
            with st.spinner("Analizando imagen y consulta según REBT e ingeniería eléctrica..."):
                respuesta = responder_consulta_rebt(prompt, st.session_state.mensajes_chat_rebt[:-1], imagen_b64=img_enviar)
                st.markdown(respuesta)
                st.session_state.mensajes_chat_rebt.append({"role": "assistant", "content": respuesta})

    # Botones de control inferiores
    col_b1, col_b2 = st.columns([1, 4])
    with col_b1:
        if st.button("🗑️ Limpiar Conversación", key="btn_clear_chat", use_container_width=True):
            st.session_state.mensajes_chat_rebt = [
                {
                    "role": "assistant",
                    "content": "Conversación reiniciada. ¿En qué te puedo asesorar ahora sobre el REBT o tus proyectos?"
                }
            ]
            st.session_state["ia_chat_imagen_activa"] = None
            st.rerun()
