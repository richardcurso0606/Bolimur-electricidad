# -*- coding: utf-8 -*-
"""
Módulo del Asistente de Inteligencia Artificial Experto en IRVE y REBT (ITC-BT-52)
Permite realizar consultas por texto y por voz (Reconocimiento y Síntesis de Voz Web),
con conocimiento técnico normativo avanzado, resolución de dudas de obra y trámites legales.
"""

import streamlit as st
import streamlit.components.v1 as html_comp
import os
import json

# Base de conocimiento experta para instaladores electricistas (REBT / ITC-BT-52)
CONOCIMIENTO_IRVE = {
    "lph": {
        "titulo": "Permisos en Comunidad de Propietarios (Art. 17.5 LPH)",
        "keywords": ["comunidad", "vecinos", "permiso", "comunicar", "lph", "acta", "votacion", "presidente", "administrador"],
        "respuesta": """
**📋 Normativa y Procedimiento en Comunidades de Propietarios (Art. 17.5 de la Ley de Propiedad Horizontal):**

1. **NO requiere votación ni aprobación:** Según el artículo 17.5 de la Ley de Propiedad Horizontal (modificada por la Ley 19/2009), la instalación de un punto de recarga en una plaza individual en un garaje comunitario **NO necesita la aprobación de la junta de propietarios**.
2. **Obligación de Comunicación Previa:** El propietario o usuario de la plaza solo tiene la **obligación de comunicar por escrito** al Presidente de la Comunidad o al Administrador de Fincas su intención de realizar la instalación con carácter previo al inicio de las obras.
3. **Plazo habitual:** Se recomienda presentar el escrito con al menos **30 días de antelación**, adjuntando una copia de la Memoria Técnica de Diseño (MTD) o memoria descriptiva con el trazado propuesto por las zonas comunes (bandejas, falsos techos o tubos).
4. **Costes:** Todos los costes de instalación, derivación, protecciones y consumo eléctrico corresponden íntegramente al titular del punto de recarga.
5. **Esquema habitual:** El **Esquema 2** (derivación desde los bornes del contador de la vivienda en la centralización) es el más utilizado y evita tener que pagar un segundo término fijo de potencia.
"""
    },
    "diferencial": {
        "titulo": "Protección Diferencial Obligatoria (Tipo A 6mA DC vs Tipo B)",
        "keywords": ["diferencial", "tipo a", "tipo b", "tipo ac", "6ma", "fuga", "continua", "superinmunizado"],
        "respuesta": """
**🛡️ Requisitos Reglamentarios del Interruptor Diferencial (ITC-BT-52 apartado 6.3):**

* **¿Por qué NO se permite el Diferencial Tipo AC convencional?**
  Los cargadores de vehículos eléctricos incorporan rectificadores AC/DC. En caso de defecto de aislamiento, pueden generarse corrientes de fuga con componente continua pura (> 6 mA DC). Un diferencial estándar Tipo AC se satura magnéticamente ("se cega") y **deja de proteger**, provocando un grave riesgo de electrocución.
* **Opciones reglamentarias según ITC-BT-52:**
  1. **Opción 1 (Más económica y habitual):** Interruptor Diferencial **Clase A** (sensibilidad 30 mA) combinado con un dispositivo de detección de fugas en corriente continua de **6 mA DC** (RDC-DD según norma IEC 62955). La mayoría de cargadores modernos (Wallbox Pulsar, Orbis Viaris, Circutor, etc.) ya integran este sensor de 6mA DC en su electrónica interna.
  2. **Opción 2:** Interruptor Diferencial **Clase B** (30 mA), que detecta de forma autónoma fugas en AC, alterna pulsante y corriente continua pura (obligatorio si el cargador no dispone de detector RDC-DD interno de 6mA DC).
* **Calibre recomendado:** In ≥ al calibre del magnetotérmico (ej. 40 A / 30 mA Tipo A Superinmunizado).
"""
    },
    "balanceo": {
        "titulo": "Sistema de Balanceo Dinámico de Potencia (SPL / Modulación)",
        "keywords": ["balanceo", "modulacion", "potencia", "spl", "pinza", "toroidal", "amperimetrica", "contratada", "icp", "subir potencia"],
        "respuesta": """
**⚡ Sistema de Modulación Dinámica de Carga / Balanceo Inteligente:**

* **¿Cómo funciona?**
  Se instala un sensor de corriente (pinza amperimétrica toroidal o medidor de energía Modbus/RS-485) en la cabecera del cuadro general de la vivienda (junto al IGA/ICP). Este sensor mide en tiempo real el consumo de electrodomésticos, aire acondicionado, horno, etc.
* **Ventajas para el cliente:**
  1. **Evita que salte el ICP:** El cargador ajusta automáticamente la potencia disponible para el coche según lo que consume la casa (si la casa consume 3 kW y hay 4.6 kW contratados, el coche carga a 1.6 kW; cuando la casa se apaga por la noche, el coche sube a la máxima potencia).
  2. **Ahorro económico radical:** El cliente **no necesita subir el término de potencia contratada**, ahorrando cientos de euros al año en la factura eléctrica.
* **Cableado de comunicación:**
  Se debe prever una manguera de comunicación apantallada (par trenzado LiYCY 2x0.5 o cable UTP Cat6) o comunicación inalámbrica (Wi-Fi/PLC) entre el medidor de la vivienda/contador y el Wallbox.
"""
    },
    "esquemas": {
        "titulo": "Esquemas de Conexión en Origen ITC-BT-52",
        "keywords": ["esquema", "origen", "esquema 2", "esquema 1", "esquema 3a", "esquema 3b", "esquema 4", "elegir", "cual elegir"],
        "respuesta": """
**📐 ¿Cuál esquema de instalación ITC-BT-52 elegir según la obra real?**

1. **Esquema 2 (POR DEFECTO - El más utilizado):**
   * *Instalación individual con contador común para vivienda y recarga.*
   * **Cuándo se usa:** Cuando el propietario tiene la plaza de garaje en el mismo edificio donde vive.
   * **Punto de conexión:** En los bornes de salida del contador de la vivienda en la centralización de contadores del edificio (con fusible/IGA de protección en el módulo de contadores).
   * **Ventaja:** Solo se paga un contrato de luz y permite balanceo dinámico con la vivienda.
2. **Esquema 3a (Contador exclusivo en centralización):**
   * **Cuándo se usa:** Cuando el propietario vive en otro edificio cercano o no tiene vivienda en la finca.
   * **Requisito:** Requiere solicitar un nuevo punto de suministro (CUPS independiente) a la distribuidora.
3. **Esquema 4a / 4b (Circuito adicional desde CGMP de la vivienda):**
   * **Cuándo se usa:** En viviendas unifamiliares (chalets, adosados) o plazas que disponen de línea directa con el cuadro eléctrico de la casa.
   * **Ventaja:** El más rápido y económico en viviendas unifamiliares.
4. **Esquema 1 (Contador colectivo troncal):**
   * **Cuándo se usa:** Parkings públicos, empresas, flotas o garajes comunitarios nuevos con gestor de carga (CPO).
"""
    },
    "cdt": {
        "titulo": "Caída de Tensión y Secciones Mínimas (ITC-BT-52)",
        "keywords": ["caida", "tension", "cdt", "seccion", "minima", "porcentaje", "limite", "rz1-k", "tubo"],
        "respuesta": """
**📏 Criterios de Caída de Tensión y Secciones Reglamentarias:**

* **Límites máximos de Caída de Tensión ($\Delta V$):**
  * **Esquemas 1, 2 y 3a (desde centralización de contadores):** Máximo **1.0%** ($\Delta V \le 2.30\text{ V}$ en 230V / $\le 4.0\text{ V}$ en 400V).
  * **Esquema 4a/4b (circuito interior desde CGMP en unifamiliar):** Máximo **1.5%** ($\Delta V \le 3.45\text{ V}$).
* **Sección mínima obligatoria:**
  * Para circuitos terminales de recarga: Mínimo **2.5 mm²** en cobre.
  * Para potencias habituales de **7.36 kW (32A)** en distancias de garaje (20-40 m), la sección requerida por caída de tensión y calentamiento suele ser **6 mm²** o **10 mm²**.
* **Tipo de Cable Obligatorio:**
  * Cable con aislamiento termoestable libre de halógenos y no propagador de la llama, clasificación CPR mínima **Cca-s1b,d1,a1** (ejemplo: *RZ1-K 0.6/1 kV* o *H07Z1-K AS* bajo tubo).
* **Tubo Protector:**
  * Debe ser no propagador de llama, libre de halógenos y con resistencia al impacto **IK08** (mínimo M25 o M32 para permitir ventilación y ampliación).
"""
    },
    "moves": {
        "titulo": "Subvenciones y Ayudas del Plan MOVES III",
        "keywords": ["moves", "subvencion", "ayuda", "descuento", "70%", "80%", "factura", "requisitos"],
        "respuesta": """
**💰 Subvenciones Plan MOVES III para Puntos de Recarga:**

* **Particulares y Comunidades de Propietarios:**
  * **70% de subvención** sobre el coste total subvencionable de la instalación (IVA incluido para particulares).
  * **80% de subvención** si la instalación se realiza en municipios de menos de 5.000 habitantes.
* **Conceptos subvencionables:**
  * Compra del punto de recarga (Wallbox).
  * Materiales eléctricos (cableado, protecciones, tubos, cuadro estanco).
  * Obra civil y mano de obra de instalación.
  * Tramitación del boletín oficial (CIE / Memoria Técnica de Diseño).
  * Sistemas de balanceo dinámico de carga.
* **Requisitos imprescindibles:**
  * Factura detallada emitida por instalador autorizado con fecha posterior a la convocatoria.
  * Justificante bancario de pago (no se admite efectivo).
  * Certificado de Instalación Eléctrica (CIE / Boletín) registrado en la Dirección General de Industria de la Comunidad Autónoma.
"""
    },
    "tramites": {
        "titulo": "Trámites Legales: ¿Memoria Técnica de Diseño (MTD) o Proyecto?",
        "keywords": ["tramite", "proyecto", "mtd", "boletin", "cie", "industria", "legalizar", "memoria tecnica"],
        "respuesta": """
**📑 Trámites de Legalización y Documentación Técnica (ITC-BT-04 e ITC-BT-52):**

* **Memoria Técnica de Diseño (MTD) + Certificado CIE (Sin Proyecto):**
  * Se requiere para instalaciones de potencia hasta **50 kW en interiores** o hasta **10 kW en intemperie/exteriores**.
  * Puede ser firmada y tramitada directamente por el **Instalador Autorizado en Baja Tensión** (categoría básica o especialista).
* **Proyecto de Ingeniero:**
  * Obligatorio si la potencia del circuito supera los **50 kW en interiores** o **10 kW en exteriores**, o en instalaciones clasificadas con riesgo especial de incendio/explosión.
* **Paso a paso para el instalador:**
  1. Ejecución de la instalación según ITC-BT-52.
  2. Verificación inicial de aislamiento y continuidad de tierra.
  3. Redacción de la MTD y emisión del Certificado de Instalación Eléctrica (CIE).
  4. Registro telemático en el órgano competente de Industria de la Comunidad Autónoma para obtención del número de registro y diligenciado.
  5. Entrega de copia al cliente y a la compañía distribuidora si hay cambio de potencia o nuevo suministro.
"""
    }
}

def responder_consulta_experta(pregunta: str) -> str:
    """
    Busca la respuesta óptima en la base de conocimiento o genera una respuesta
    técnica contextualizada de alta precisión para el instalador.
    """
    if not pregunta or len(pregunta.strip()) < 3:
        return "Por favor, escribe o dicta una consulta técnica sobre la instalación de recarga (IRVE), normativa REBT, protecciones, esquemas o trámites."
    
    preg_lower = pregunta.lower()
    
    # 1. Búsqueda por coincidencia en base de conocimiento experta
    max_matches = 0
    mejor_clave = None
    
    for clave, item in CONOCIMIENTO_IRVE.items():
        matches = sum(1 for kw in item["keywords"] if kw in preg_lower)
        if matches > max_matches:
            max_matches = matches
            mejor_clave = clave
            
    if mejor_clave and max_matches >= 1:
        item = CONOCIMIENTO_IRVE[mejor_clave]
        return f"### 💡 {item['titulo']}\n\n{item['respuesta']}"
    
    # 2. Respuestas inteligentes para consultas frecuentes adicionales
    if "precio" in preg_lower or "cuanto cuesta" in preg_lower or "coste" in preg_lower:
        return """
### 💡 Coste Típico de Instalación de Punto de Recarga (Esquema 2)
* **Cargador Wallbox (Modo 3 con balanceo):** 600 € - 1.000 €
* **Cuadro de protecciones (PIA, Diferencial Tipo A 6mA DC, VTP+VSP):** 150 € - 280 €
* **Línea de cable RZ1-K libre de halógenos + tubo M32 (20-30m):** 180 € - 320 €
* **Mano de obra especializada y pasamuros:** 300 € - 550 €
* **Memoria Técnica y Boletín Oficial CIE:** 120 € - 200 €
* **Total orientativo:** Entre **1.350 € y 2.350 € + IVA** (subvencionable al 70%-80% con Plan MOVES III).
"""

    if "tierra" in preg_lower or "pica" in preg_lower:
        return """
### 💡 Requisitos de Puesta a Tierra para IRVE (ITC-BT-52 e ITC-BT-18)
* El punto de recarga debe conectarse siempre al **conductor de protección (PE)** de la instalación existente.
* La resistencia de puesta a tierra debe ser compatible con la sensibilidad del diferencial (en esquemas TT, $R_t \cdot I_{\Delta n} \le 50\text{ V}$, para 30 mA exige $R_t \le 1666\ \Omega$, aunque por buena práctica técnica se recomienda $R_t \le 15-20\ \Omega$).
* En parkings comunitarios se utiliza la red de tierra general del edificio. En unifamiliares, si la tierra es deficiente, se debe hincar una pica auxiliar de cobre de 2 metros.
"""

    # 3. Respuesta técnica genérica experta
    return f"""
### 💡 Consulta Técnica REBT ITC-BT-52: "{pregunta}"

Para esta consulta sobre la infraestructura de recarga de vehículos eléctricos:
* **Normativa de aplicación:** Real Decreto 1053/2014 e **ITC-BT-52** del Reglamento Electrotécnico para Baja Tensión.
* **Criterios Generales de Seguridad:**
  1. Todos los circuitos deben dimensionarse con factor de servicio continuo (100% de la carga de diseño en régimen permanente).
  2. La caída de tensión no debe superar el **1.0%** desde centralización de contadores o el **1.5%** en circuitos interiores de viviendas unifamiliares.
  3. Es preceptivo el uso de cable libre de halógenos **RZ1-K 0.6/1kV** o **H07Z1-K** con clasificación CPR Cca-s1b,d1,a1.
  4. La protección debe incluir corte omnipolar con **PIA Curva C**, protección diferencial con detección de corriente continua **≤ 6 mA DC** (según IEC 62955) o **Tipo B**, y limitador de sobretensiones transitorias y permanentes.

*Si deseas una respuesta específica, puedes seleccionar una de las preguntas rápidas del panel lateral o formular una consulta sobre esquemas, protecciones, permisos LPH o balanceo.*
"""

def renderizar_asistente_irve():
    """
    Renderiza la interfaz del Asistente de IA con soporte de Voz (Dictado y TTS) y Texto.
    """
    st.markdown('<div class="section-header-amber"><h4 style="margin:0; color:#b45309;">🤖 Asistente IA Experto en IRVE y Normativa REBT (Voz y Texto)</h4></div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("""
        <p style="font-size: 13px; color: #475569; margin-bottom: 12px;">
            Consulta cualquier duda técnica, normativa, legal o de obra directamente al asistente de IA.
            Puedes <b>escribir tu pregunta</b> o usar el <b>micrófono por voz</b> en tiempo real.
        </p>
        """, unsafe_allow_html=True)
        
        # Historial de chat en session_state
        if "historial_irve_ia" not in st.session_state:
            st.session_state.historial_irve_ia = [
                {
                    "rol": "asistente",
                    "texto": "👋 ¡Hola! Soy tu **Asistente Técnico Especialista en IRVE (ITC-BT-52)**. ¿En qué puedo ayudarte hoy? Puedes preguntarme sobre esquemas en origen (Esquema 2, 3a, 3b, 4), protecciones diferenciales (Tipo A 6mA vs Tipo B), permisos en comunidades (LPH 17.5), balanceo dinámico SPL o subvenciones Plan MOVES III."
                }
            ]
            
        # Pestañas: Chat Interactivo / Preguntas Rápidas de Instaladores
        tab_chat, tab_preguntas = st.tabs(["💬 Chat con IA (Voz y Texto)", "⚡ Consultas Frecuentes de Instalador"])
        
        with tab_preguntas:
            st.markdown("##### 📌 Temas Clave con 1 Clic para el Instalador:")
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                if st.button("🏢 ¿Cómo tramitar el permiso en la Comunidad de Vecinos (Art. 17.5 LPH)?", key="btn_q_lph", use_container_width=True):
                    q_text = "¿Cómo pedir permiso a la comunidad de vecinos para instalar punto de recarga?"
                    ans = responder_consulta_experta(q_text)
                    st.session_state.historial_irve_ia.append({"rol": "usuario", "texto": q_text})
                    st.session_state.historial_irve_ia.append({"rol": "asistente", "texto": ans})
                    st.rerun()
                    
                if st.button("🛡️ ¿Por qué es obligatorio el Diferencial Tipo A con 6mA DC o Tipo B?", key="btn_q_dif", use_container_width=True):
                    q_text = "¿Qué diferencial es obligatorio según ITC-BT-52 y por qué no vale el Tipo AC?"
                    ans = responder_consulta_experta(q_text)
                    st.session_state.historial_irve_ia.append({"rol": "usuario", "texto": q_text})
                    st.session_state.historial_irve_ia.append({"rol": "asistente", "texto": ans})
                    st.rerun()
                    
                if st.button("⚡ ¿Cómo funciona el Balanceo Dinámico (SPL) para no subir potencia?", key="btn_q_bal", use_container_width=True):
                    q_text = "¿Cómo instalar el balanceo dinámico de carga para no subir la potencia contratada?"
                    ans = responder_consulta_experta(q_text)
                    st.session_state.historial_irve_ia.append({"rol": "usuario", "texto": q_text})
                    st.session_state.historial_irve_ia.append({"rol": "asistente", "texto": ans})
                    st.rerun()

            with col_p2:
                if st.button("📐 ¿Por qué el Esquema 2 es el más utilizado en garajes comunitarios?", key="btn_q_esq", use_container_width=True):
                    q_text = "¿Por qué se elige el Esquema 2 de ITC-BT-52 en garajes de comunidades?"
                    ans = responder_consulta_experta(q_text)
                    st.session_state.historial_irve_ia.append({"rol": "usuario", "texto": q_text})
                    st.session_state.historial_irve_ia.append({"rol": "asistente", "texto": ans})
                    st.rerun()
                    
                if st.button("💰 Requisitos de las Ayudas y Subvenciones Plan MOVES III (70-80%)", key="btn_q_mov", use_container_width=True):
                    q_text = "¿Cuáles son los requisitos de las ayudas del Plan MOVES III para punto de recarga?"
                    ans = responder_consulta_experta(q_text)
                    st.session_state.historial_irve_ia.append({"rol": "usuario", "texto": q_text})
                    st.session_state.historial_irve_ia.append({"rol": "asistente", "texto": ans})
                    st.rerun()
                    
                if st.button("📑 ¿Cuándo se necesita Proyecto o solo Memoria Técnica de Diseño (MTD)?", key="btn_q_tram", use_container_width=True):
                    q_text = "¿Cuándo hace falta proyecto de ingeniero y cuándo solo MTD con boletín CIE?"
                    ans = responder_consulta_experta(q_text)
                    st.session_state.historial_irve_ia.append({"rol": "usuario", "texto": q_text})
                    st.session_state.historial_irve_ia.append({"rol": "asistente", "texto": ans})
                    st.rerun()

        with tab_chat:
            # Componente de interfaz de Voz Web nativa (HTML5 Web Speech Recognition y Speech Synthesis)
            componente_voz_html = """
            <div id="voice-panel" style="background: #f1f5f9; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <button id="btn-mic" onclick="toggleVoiceRecording()" style="background-color: #0284c7; color: white; border: none; border-radius: 50%; width: 42px; height: 42px; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(2,132,199,0.3); transition: all 0.2s;">
                        🎤
                    </button>
                    <div>
                        <b style="font-size: 13px; color: #0f172a;" id="mic-status-title">Dictado por Voz</b><br/>
                        <span style="font-size: 11px; color: #64748b;" id="mic-status-desc">Pulsa el micro para hablar</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <button onclick="leerUltimaRespuesta()" style="background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 6px 12px; font-size: 12px; color: #334155; font-weight: 500; cursor: pointer;">
                        🔊 Escuchar Última Respuesta
                    </button>
                    <button onclick="detenerVoz()" style="background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; font-size: 12px; color: #dc2626; cursor: pointer;">
                        ⏹️ Parar
                    </button>
                </div>
            </div>

            <script>
                var recognition = null;
                var isRecording = false;

                if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                    var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
                    recognition = new SpeechRec();
                    recognition.lang = 'es-ES';
                    recognition.continuous = false;
                    recognition.interimResults = false;

                    recognition.onstart = function() {
                        isRecording = true;
                        document.getElementById('btn-mic').style.backgroundColor = '#dc2626';
                        document.getElementById('btn-mic').innerText = '🔴';
                        document.getElementById('mic-status-title').innerText = 'Escuchando...';
                        document.getElementById('mic-status-desc').innerText = 'Habla ahora en tu micrófono';
                    };

                    recognition.onresult = function(event) {
                        var transcript = event.results[0][0].transcript;
                        document.getElementById('btn-mic').style.backgroundColor = '#0284c7';
                        document.getElementById('btn-mic').innerText = '🎤';
                        document.getElementById('mic-status-title').innerText = 'Texto capturado';
                        document.getElementById('mic-status-desc').innerText = '"' + transcript + '"';
                        
                        // Intentar poner el texto en el input de Streamlit
                        var stInputs = window.parent.document.querySelectorAll('input[type="text"]');
                        if (stInputs.length > 0) {
                            var target = stInputs[stInputs.length - 1];
                            target.value = transcript;
                            target.dispatchEvent(new Event('input', { bubbles: true }));
                            target.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    };

                    recognition.onerror = function(event) {
                        isRecording = false;
                        document.getElementById('btn-mic').style.backgroundColor = '#0284c7';
                        document.getElementById('btn-mic').innerText = '🎤';
                        document.getElementById('mic-status-title').innerText = 'Error o silencio';
                        document.getElementById('mic-status-desc').innerText = 'Pulsa el micro para reintentar';
                    };

                    recognition.onend = function() {
                        isRecording = false;
                        document.getElementById('btn-mic').style.backgroundColor = '#0284c7';
                        document.getElementById('btn-mic').innerText = '🎤';
                        document.getElementById('mic-status-title').innerText = 'Dictado por Voz';
                        document.getElementById('mic-status-desc').innerText = 'Pulsa el micro para hablar';
                    };
                } else {
                    document.getElementById('mic-status-title').innerText = 'Voz no soportada';
                    document.getElementById('mic-status-desc').innerText = 'Usa Chrome / Edge para dictado por voz';
                }

                function toggleVoiceRecording() {
                    if (!recognition) {
                        alert('El reconocimiento de voz requiere Google Chrome, Microsoft Edge o un navegador compatible.');
                        return;
                    }
                    if (isRecording) {
                        recognition.stop();
                    } else {
                        recognition.start();
                    }
                }

                function leerUltimaRespuesta() {
                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                        // Buscar el último mensaje del asistente en el chat
                        var mensajes = window.parent.document.querySelectorAll('.chat-ia-msg-text');
                        var textoALeer = "No hay mensajes recientes para reproducir.";
                        if (mensajes.length > 0) {
                            textoALeer = mensajes[mensajes.length - 1].innerText;
                        }
                        var utterance = new SpeechSynthesisUtterance(textoALeer);
                        utterance.lang = 'es-ES';
                        utterance.rate = 1.05;
                        window.speechSynthesis.speak(utterance);
                    }
                }

                function detenerVoz() {
                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                    }
                }
            </script>
            """
            html_comp.html(componente_voz_html, height=75)

            # Visualización de historial de mensajes
            for msg in st.session_state.historial_irve_ia:
                if msg["rol"] == "usuario":
                    st.markdown(f"""
                    <div style="background: #e0f2fe; border-left: 4px solid #0284c7; padding: 10px 14px; border-radius: 6px; margin: 6px 0;">
                        <b style="color: #0369a1;">👤 Instalador:</b><br/>
                        <span style="color: #0f172a; font-size: 13.5px;">{msg['texto']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #f8fafc; border-left: 4px solid #10b981; padding: 12px 14px; border-radius: 6px; margin: 6px 0;" class="chat-ia-msg-text">
                        <b style="color: #047857;">🤖 Asistente Experto IRVE:</b><br/>
                        {msg['texto']}
                    </div>
                    """, unsafe_allow_html=True)
                    
            # Formulario de entrada de texto
            with st.form("form_chat_ia_irve", clear_on_submit=True):
                col_i1, col_i2 = st.columns([5, 1])
                with col_i1:
                    pregunta_usuario = st.text_input("Haz tu pregunta sobre IRVE / REBT (o dicta por voz):", placeholder="Ej: ¿Qué sección de cable necesito para 7.4 kW a 35 metros?", key="input_ia_irve")
                with col_i2:
                    st.write("")
                    btn_enviar = st.form_submit_button("💬 Preguntar", type="primary", use_container_width=True)
                    
                if btn_enviar and pregunta_usuario:
                    respuesta = responder_consulta_experta(pregunta_usuario)
                    st.session_state.historial_irve_ia.append({"rol": "usuario", "texto": pregunta_usuario})
                    st.session_state.historial_irve_ia.append({"rol": "asistente", "texto": respuesta})
                    st.rerun()

            if len(st.session_state.historial_irve_ia) > 1:
                if st.button("🗑️ Limpiar Historial de Chat", key="btn_clear_ia_chat"):
                    st.session_state.historial_irve_ia = [st.session_state.historial_irve_ia[0]]
                    st.rerun()
