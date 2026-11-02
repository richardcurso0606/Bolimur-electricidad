# -*- coding: utf-8 -*-
"""
Módulo de Presupuesto Rápido con IA y Dictado por Micrófono (Bolimur Instant Work).
Diseñado para el instalador electricista de calle que necesita cotizar un trabajo
urgente en segundos a pie de obra o en la furgoneta.
Permite dictar por voz, ver la transcripción en pantalla, modificarla y generar
el presupuesto detallado con/sin IVA.
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

    modelos = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
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
        except Exception:
            continue

    return {"exito": False, "error": "No se pudo transcribir el audio mediante la API de Gemini."}


def analizar_trabajo_ia_gemini(descripcion: str, api_key: str, precio_hora: float = 25.0) -> dict:
    """Utiliza Gemini para desglosar el trabajo en partidas técnicas REBT, materiales y mano de obra."""
    if not api_key:
        return {"exito": False}

    prompt = f"""Actúa como un Maestro Instalador Electricista Autorizado e Ingeniero Eléctrico en España experto en REBT (RD 842/2002).
Analiza el siguiente trabajo eléctrico descrito por un instalador:
"{descripcion}"

Genera el escandallo técnico oficial en formato JSON estricto con esta estructura:
{{
  "concepto": "Título técnico formal del trabajo (ej: Línea protegida para depuradora con reloj horario ITC-BT-31)",
  "norma": "Instrucción técnica REBT aplicable (ej: ITC-BT-31)",
  "horas": 3.0,
  "materiales": [
    {{"mat": "Nombre comercial y técnico del material", "cant": 1.0, "unid": "ud"|"m"|"pack", "p_u": 32.50}}
  ]
}}
Devuelve EXCLUSIVAMENTE el objeto JSON sin texto antes ni después."""

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1500
        }
    }

    modelos = ["gemini-2.0-flash", "gemini-1.5-flash"]
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
                    if "concepto" in obj and "materiales" in obj:
                        return {"exito": True, "resultado": obj}
        except Exception:
            continue

    return {"exito": False}


def motor_reglas_rebt_rapido(prompt_consulta: str) -> dict:
    """Motor experto reglamentario REBT cuando no hay conexión IA o clave API."""
    p_low = prompt_consulta.lower().strip()

    if "depuradora" in p_low or "piscina" in p_low:
        concepto = "Línea Dedicada para Depuradora de Piscina con Reloj Horario (ITC-BT-31)"
        norma = "ITC-BT-31 (Piscinas y Fuentes)"
        horas = 3.5
        materiales = [
            {"mat": "Reloj Programador Horario Modular Carril DIN", "cant": 1.0, "unid": "ud", "p_u": 32.50},
            {"mat": "PIA Magnetotérmico 1P+N 16A Curva C", "cant": 1.0, "unid": "ud", "p_u": 8.40},
            {"mat": "Cable Cu RZ1-K 0.6/1kV 3x2.5 mm² Libre Halógenos", "cant": 20.0, "unid": "m", "p_u": 1.15},
            {"mat": "Tubo Corrugado M25 Libre de Halógenos 750N", "cant": 20.0, "unid": "m", "p_u": 0.85},
            {"mat": "Caja Estanca IP65 con Borna de Conexión", "cant": 1.0, "unid": "ud", "p_u": 12.80}
        ]
    elif "aire" in p_low or "clima" in p_low or "split" in p_low:
        concepto = "Circuito Independiente de Climatización C9 (ITC-BT-25)"
        norma = "ITC-BT-25 (Instalaciones Interiores)"
        horas = 3.0
        materiales = [
            {"mat": "PIA Magnetotérmico 1P+N 16A Curva C 6kA", "cant": 1.0, "unid": "ud", "p_u": 8.40},
            {"mat": "Interruptor Diferencial 2x40A / 30mA Clase A Superinmunizado", "cant": 1.0, "unid": "ud", "p_u": 38.00},
            {"mat": "Cable Cu H07Z1-K 3x2.5 mm² (Fase, Neutro, Tierra)", "cant": 15.0, "unid": "m", "p_u": 0.95},
            {"mat": "Canaleta Decorativa Blanca con Tapa 20x40mm", "cant": 12.0, "unid": "m", "p_u": 2.20},
            {"mat": "Caja de Mecanismo de Superficie IP44", "cant": 1.0, "unid": "ud", "p_u": 6.50}
        ]
    elif "recarga" in p_low or "coche" in p_low or "vehículo" in p_low or "irve" in p_low or "patinete" in p_low:
        concepto = "Instalación de Punto de Recarga para Vehículo Eléctrico IRVE (ITC-BT-52)"
        norma = "ITC-BT-52 (Infraestructura para Recarga VE)"
        horas = 5.0
        materiales = [
            {"mat": "Interruptor General Automático IGA 2P 32A Curva C", "cant": 1.0, "unid": "ud", "p_u": 12.50},
            {"mat": "Diferencial Superinmunizado Clase A 2P 40A / 30mA", "cant": 1.0, "unid": "ud", "p_u": 42.00},
            {"mat": "Cable Unipolar Cu RZ1-K 0.6/1kV 3x6 mm² Libre Halógenos", "cant": 25.0, "unid": "m", "p_u": 2.10},
            {"mat": "Tubo Rígido Enchufable M32 Libre de Halógenos 1250N", "cant": 20.0, "unid": "m", "p_u": 1.45},
            {"mat": "Cuadro Modular Estanco IP65 para Garaje", "cant": 1.0, "unid": "ud", "p_u": 28.50},
            {"mat": "Base Schuko Reforzada 16A Green'Up / Mennekes", "cant": 1.0, "unid": "ud", "p_u": 45.00}
        ]
    elif "derivación" in p_low or "di" in p_low or "contador" in p_low:
        concepto = "Renovación / Tendido de Derivación Individual Monofásica (ITC-BT-15)"
        norma = "ITC-BT-15 (Derivaciones Individuales)"
        horas = 4.0
        materiales = [
            {"mat": "Cable Cu RZ1-K 0.6/1kV 2x10 mm² + TT 1x10 mm² Cca", "cant": 20.0, "unid": "m", "p_u": 4.20},
            {"mat": "Hilo de Mando Rojo 1.5 mm² para Telegestión", "cant": 20.0, "unid": "m", "p_u": 0.28},
            {"mat": "Tubo Corrugado Libre de Halógenos M40 750N", "cant": 20.0, "unid": "m", "p_u": 1.25},
            {"mat": "Bornas de Conexión Seccionables de Entrada", "cant": 2.0, "unid": "ud", "p_u": 4.50}
        ]
    elif "horno" in p_low or "vitro" in p_low or "cocina" in p_low or "25a" in p_low:
        concepto = "Circuito de Fuerza C3 para Horno y Cocina/Vitrocerámica (ITC-BT-25)"
        norma = "ITC-BT-25 (Circuitos Interiores)"
        horas = 2.5
        materiales = [
            {"mat": "PIA Magnetotérmico 1P+N 25A Curva C 6kA", "cant": 1.0, "unid": "ud", "p_u": 9.50},
            {"mat": "Cable Cu H07Z1-K 3x6 mm² Libre de Halógenos", "cant": 15.0, "unid": "m", "p_u": 1.85},
            {"mat": "Tubo Corrugado M25", "cant": 15.0, "unid": "m", "p_u": 0.75},
            {"mat": "Base Enchufe de Fuerza 25A 2P+T con Clavija", "cant": 1.0, "unid": "ud", "p_u": 14.50}
        ]
    elif "cuadro" in p_low or "automático" in p_low or "térmico" in p_low or "diferencial" in p_low:
        concepto = "Sustitución y Adecuación de Cuadro General de Protección (CGMP)"
        norma = "ITC-BT-17 e ITC-BT-24"
        horas = 3.5
        materiales = [
            {"mat": "Envolvente Empotrada Cuadro 18-24 Módulos", "cant": 1.0, "unid": "ud", "p_u": 26.00},
            {"mat": "Interruptor General Automático IGA 2P 25A/32A", "cant": 1.0, "unid": "ud", "p_u": 12.00},
            {"mat": "Protector Sobretensiones Permanentes y Transitorias POP+DPS", "cant": 1.0, "unid": "ud", "p_u": 48.00},
            {"mat": "Interruptores Diferenciales 2x40A / 30mA (x2)", "cant": 2.0, "unid": "ud", "p_u": 22.00},
            {"mat": "Peine de Conexión Bipolar y Menudencia", "cant": 1.0, "unid": "pack", "p_u": 15.00}
        ]
    elif "tierra" in p_low or "pica" in p_low:
        concepto = "Instalación de Red de Puesta a Tierra y Pica de Cobre (ITC-BT-18)"
        norma = "ITC-BT-18 (Puestas a Tierra)"
        horas = 2.0
        materiales = [
            {"mat": "Pica de Acero-Cobre 2m x 14mm con Brida de Conexión", "cant": 1.0, "unid": "ud", "p_u": 21.00},
            {"mat": "Arqueta de Registro de P.A.T. 200x200 con Tapa", "cant": 1.0, "unid": "ud", "p_u": 14.50},
            {"mat": "Cable de Tierra Cu Desnudo 35 mm²", "cant": 10.0, "unid": "m", "p_u": 3.80},
            {"mat": "Puente Seccionador de Tierra", "cant": 1.0, "unid": "ud", "p_u": 11.00}
        ]
    else:
        concepto = f"Trabajo Eléctrico Especializado: {prompt_consulta[:45]}" if prompt_consulta else "Trabajo Eléctrico Especializado"
        norma = "REBT RD 842/2002"
        horas = 2.5
        materiales = [
            {"mat": "Material conductor y canalización normalizada", "cant": 1.0, "unid": "partida", "p_u": 35.00},
            {"mat": "Aparamenta de maniobra y protecciones", "cant": 1.0, "unid": "partida", "p_u": 25.00},
            {"mat": "Menudencia, cajas y bornes de conexión", "cant": 1.0, "unid": "pack", "p_u": 12.00}
        ]

    return {
        "concepto": concepto,
        "norma": norma,
        "horas": horas,
        "materiales": materiales
    }


def renderizar():
    st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">⚡ Presupuesto Rápido con IA y Dictado por Voz</h3></div>', unsafe_allow_html=True)
    st.caption("Diseñado para calle y furgoneta: habla por el micrófono o escribe el trabajo. La IA transcribirá tus palabras, las mostrará en pantalla para que puedas modificarlas y calculará el desglose en segundos.")

    # Inicializar variables en session_state de forma segura
    if "pr_texto_input" not in st.session_state:
        st.session_state["pr_texto_input"] = ""
    if "pr_last_audio_bytes" not in st.session_state:
        st.session_state["pr_last_audio_bytes"] = None

    # Estado de la API de Gemini
    api_key = auditor_ia_rebt.obtener_gemini_api_key()
    tiene_gemini = bool(api_key and len(api_key) > 10)

    # Panel plegable de Configuración de Clave API si no está configurada
    if not tiene_gemini:
        with st.expander("🔑 Activar Transcripción de Voz IA Directa con Google Gemini (Gratuito)", expanded=False):
            st.info("Para que la IA transcriba directamente tu voz a texto en la pantalla, introduce tu clave gratuita de Google Gemini (se obtiene gratis en 1 minuto en [Google AI Studio](https://aistudio.google.com/)).")
            nueva_key = st.text_input("Clave API de Gemini:", type="password", key="pr_input_gemini_key")
            if st.button("💾 Guardar Clave API", key="btn_save_gemini_pr"):
                if nueva_key.strip():
                    auditor_ia_rebt.guardar_gemini_api_key(nueva_key.strip())
                    st.success("✅ Clave API guardada con éxito.")
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

    col_input1, col_input2 = st.columns([3, 2])

    with col_input2:
        with st.container(border=True):
            st.markdown("🎤 **1. Dictado por Micrófono:**")
            st.caption("Pulsa el botón de grabar, explica el trabajo y pulsa detener:")
            audio_in = st.audio_input("Graba tu voz", key="pr_mic_audio")

            # Procesamiento de audio capturado
            if audio_in is not None:
                raw_bytes = audio_in.getvalue()
                # Verificar si es una nueva grabación comparando los bytes
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
                    else:
                        st.warning("⚠️ **Clave Gemini no detectada:** Para transcribir audio grabado automáticamente, añade tu clave gratuita de Google Gemini en el panel superior, o utiliza el dictado de Windows (`Win + H`).")

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
        # Sincronizar cambios manuales de texto en session_state
        st.session_state["pr_texto_input"] = txt_descripcion

        col_txt_actions = st.columns([1, 1])
        with col_txt_actions[0]:
            if st.button("🧹 Borrar texto para nuevo dictado", key="btn_limpiar_pr_texto", use_container_width=True):
                st.session_state["pr_texto_input"] = ""
                st.session_state["pr_texto_area"] = ""
                st.session_state["pr_last_audio_bytes"] = None
                st.rerun()

    # Atajos de 1 Clic para trabajos habituales
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

            with st.spinner("⚙️ Estructurando escandallo de materiales y mano de obra REBT..."):
                resultado_final = None
                # Si hay Gemini disponible, intentar análisis con IA generativa
                if tiene_gemini:
                    res_ia = analizar_trabajo_ia_gemini(prompt_consulta, api_key, precio_hora_mo)
                    if res_ia.get("exito"):
                        resultado_final = res_ia.get("resultado")

                # Fallback al motor experto reglamentario si no hay IA o falla
                if not resultado_final:
                    resultado_final = motor_reglas_rebt_rapido(prompt_consulta)

                resultado_final["consulta_orig"] = prompt_consulta
                st.session_state["pr_resultado_escandallo"] = resultado_final

                # Limpiar cualquier clave residual de la tabla anterior
                for k in list(st.session_state.keys()):
                    if k.startswith("prm_") or k == "pr_target_round":
                        del st.session_state[k]

        # 4. Visualización del Presupuesto Dinámico y Editable
        res = st.session_state.get("pr_resultado_escandallo", {})
        if res:
            st.markdown("---")
            st.markdown(f"### 📋 Presupuesto Técnico: **{res.get('concepto', 'Trabajo Eléctrico')}**")
            st.info(f"📘 **Normativa REBT Aplicable:** `{res.get('norma', 'REBT RD 842/2002')}` | 📝 **Trabajo:** *\"{res.get('consulta_orig', '')}\"*")

            col_esc1, col_esc2 = st.columns([3, 2])

            with col_esc1:
                st.markdown("##### 📦 Materiales Desglosados (Modificables en tiempo real):")
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
                        "descripcion": f"Instalación según {res.get('norma', 'REBT')}: {res.get('consulta_orig', '')}. Incluye materiales desglosados y {horas_mo_val:.1f} h de mano de obra.",
                        "cantidad": 1.0,
                        "unidad": "partida",
                        "precio_unitario": sub_final_siva,
                        "subtotal": sub_final_siva
                    })
                    st.session_state.presupuesto_calculado = True
                    st.success(f"✅ Trabajo '{res.get('concepto')}' transferido con éxito al Presupuesto de Vivienda.")
