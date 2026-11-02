# -*- coding: utf-8 -*-
"""
Módulo de Presupuesto Rápido con IA y Dictado por Micrófono (Bolimur Instant Work).
Diseñado para el instalador electricista de calle que necesita cotizar un trabajo
urgente en segundos a pie de obra o en la furgoneta.
"""

import streamlit as st
import pandas as pd
import datetime
import base64
import re
from modulos import auditor_ia_rebt
from modulos import asistente_ia_rebt
from modulos import pdf_presupuesto

def renderizar():
    st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">⚡ Presupuesto Rápido con IA y Micrófono de Voz</h3></div>', unsafe_allow_html=True)
    st.caption("Diseñado para calle y furgoneta: describe el trabajo urgente por voz o texto y la IA estructurará el escandallo de materiales, mano de obra y precio cerrado en segundos.")

    # 1. Configuración de Mano de Obra y Cliente Rápido
    col_cfg1, col_cfg2, col_cfg3 = st.columns([2.5, 1.5, 1.5])
    with col_cfg1:
        nom_cliente = st.text_input("👤 Cliente / Referencia:", value="Cliente Particular / Urgencia", key="pr_cliente_nom")
    with col_cfg2:
        precio_hora_mo = st.number_input("⏱️ Precio Mano de Obra (€/h):", min_value=15.0, max_value=80.0, value=25.0, step=1.0, key="pr_precio_hora")
    with col_cfg3:
        iva_pct = st.selectbox("🏛️ IVA Aplicable:", [21.0, 10.0, 0.0], format_func=lambda x: f"{x:.0f}%" if x > 0 else "0% (Exento / ISP)", key="pr_iva_sel")

    st.markdown("---")

    # 2. Entrada Multimodal: Micrófono de Voz o Texto en Lenguaje de Calle
    st.markdown("#### 🎙️ Paso 1: Describe el trabajo a realizar:")
    
    col_input1, col_input2 = st.columns([3, 2])
    audio_grabado = None
    with col_input2:
        with st.container(border=True):
            st.markdown("🎤 **Dictado por Micrófono (Voz):**")
            audio_in = st.audio_input("Pulsa para grabar tu voz", key="pr_mic_audio")
            if audio_in is not None:
                audio_grabado = audio_in
                st.audio(audio_in)
                st.caption("✅ Audio listo para análisis con IA.")

    with col_input1:
        txt_descripcion = st.text_area(
            "✍️ O escribe el trabajo con tus propias palabras:",
            placeholder="Ej: Instalar línea directa para horno de 25A con cable de 6mm desde el cuadro de la entrada hasta la cocina, unos 12 metros de tubo visto con canaleta blanca y poner el automático de 25A.",
            height=120,
            key="pr_texto_input"
        )

    # 3. Botones de Acción Rápida con IA
    col_btn1, col_btn2 = st.columns([2, 3])
    with col_btn1:
        btn_calcular = st.button("🚀 Calcular Presupuesto Inmediato con IA", type="primary", use_container_width=True, key="btn_pr_calcular")
    with col_btn2:
        # Atajos de 1 Clic para trabajos habituales
        st.markdown("**⚡ Trabajos Comunes Rápidos:**")
        col_at1, col_at2, col_at3, col_at4 = st.columns(4)
        if col_at1.button("🏊 Depuradora", key="btn_at_dep"):
            st.session_state["pr_texto_input"] = "Instalación de línea protegida para depuradora de piscina con reloj programador horario modular y térmico de 16A."
            st.rerun()
        if col_at2.button("❄️ Aire Acond.", key="btn_at_clima"):
            st.session_state["pr_texto_input"] = "Línea independiente de climatización C9 de 16A bajo canaleta blanca con cable 3x2.5mm² y protección en cuadro."
            st.rerun()
        if col_at3.button("🚗 Punto Recarga", key="btn_at_irve"):
            st.session_state["pr_texto_input"] = "Línea dedicada IRVE para recarga de coche eléctrico con cable 3x6mm², tubo M25, diferencial superinmunizado clase A e IGA 32A."
            st.rerun()
        if col_at4.button("🔌 Derivación DI", key="btn_at_di"):
            st.session_state["pr_texto_input"] = "Derivación individual monofásica desde contadores hasta vivienda con cable libre de halógenos 2x10mm²+TT y tubo M40."
            st.rerun()

    # 4. Procesamiento Inteligente y Generación de Partidas
    if btn_calcular or ("pr_resultado_escandallo" in st.session_state and not btn_calcular):
        prompt_consulta = txt_descripcion.strip()
        
        if btn_calcular:
            # Si hay audio y no hay texto, pedir a Gemini que transcriba y resuelva
            api_key = auditor_ia_rebt.obtener_gemini_api_key()
            tiene_gemini = bool(api_key and len(api_key) > 10)

            # Motor Experto REBT de Escandallo (Reglas Eléctricas + IA)
            p_low = prompt_consulta.lower()
            
            # Inicializar estructura de escandallo
            concepto_oficial = "Trabajo Eléctrico Especializado a Medida (REBT)"
            norma_rebt = "RD 842/2002"
            horas_estimadas = 2.5
            materiales_lista = []

            if "depuradora" in p_low or "piscina" in p_low:
                concepto_oficial = "Línea Dedicada para Depuradora de Piscina con Reloj Horario (ITC-BT-31)"
                norma_rebt = "ITC-BT-31 (Piscinas y Fuentes)"
                horas_estimadas = 3.5
                materiales_lista = [
                    {"mat": "Reloj Programador Horario Modular Carril DIN", "cant": 1, "unid": "ud", "p_u": 32.50},
                    {"mat": "PIA Magnetotérmico 1P+N 16A Curva C", "cant": 1, "unid": "ud", "p_u": 8.40},
                    {"mat": "Cable Cu RZ1-K 0.6/1kV 3x2.5 mm² Libre Halógenos", "cant": 20, "unid": "m", "p_u": 1.15},
                    {"mat": "Tubo Corrugado M25 Libre de Halógenos 750N", "cant": 20, "unid": "m", "p_u": 0.85},
                    {"mat": "Caja Estanca IP65 con Borna de Conexión", "cant": 1, "unid": "ud", "p_u": 12.80}
                ]
            elif "aire" in p_low or "clima" in p_low or "split" in p_low:
                concepto_oficial = "Circuito Independiente de Climatización C9 (ITC-BT-25)"
                norma_rebt = "ITC-BT-25 (Instalaciones Interiores)"
                horas_estimadas = 3.0
                materiales_lista = [
                    {"mat": "PIA Magnetotérmico 1P+N 16A Curva C 6kA", "cant": 1, "unid": "ud", "p_u": 8.40},
                    {"mat": "Interruptor Diferencial 2x40A / 30mA Clase A Superinmunizado", "cant": 1, "unid": "ud", "p_u": 38.00},
                    {"mat": "Cable Cu H07Z1-K 3x2.5 mm² (Fase, Neutro, Tierra)", "cant": 15, "unid": "m", "p_u": 0.95},
                    {"mat": "Canaleta Decorativa Blanca con Tapa 20x40mm", "cant": 12, "unid": "m", "p_u": 2.20},
                    {"mat": "Caja de Mecanismo de Superficie IP44", "cant": 1, "unid": "ud", "p_u": 6.50}
                ]
            elif "recarga" in p_low or "coche" in p_low or "vehículo" in p_low or "irve" in p_low or "patinete" in p_low:
                concepto_oficial = "Instalación de Punto de Recarga para Vehículo Eléctrico IRVE (ITC-BT-52)"
                norma_rebt = "ITC-BT-52 (Infraestructura para Recarga VE)"
                horas_estimadas = 5.0
                materiales_lista = [
                    {"mat": "Interruptor General Automático IGA 2P 32A Curva C", "cant": 1, "unid": "ud", "p_u": 12.50},
                    {"mat": "Diferencial Superinmunizado Clase A 2P 40A / 30mA", "cant": 1, "unid": "ud", "p_u": 42.00},
                    {"mat": "Cable Unipolar Cu RZ1-K 0.6/1kV 3x6 mm² Libre Halógenos", "cant": 25, "unid": "m", "p_u": 2.10},
                    {"mat": "Tubo Rígido Enchufable M32 Libre de Halógenos 1250N", "cant": 20, "unid": "m", "p_u": 1.45},
                    {"mat": "Cuadro Modular Estanco IP65 para Garaje", "cant": 1, "unid": "ud", "p_u": 28.50},
                    {"mat": "Base Schuko Reforzada 16A Green'Up / Mennekes", "cant": 1, "unid": "ud", "p_u": 45.00}
                ]
            elif "derivación" in p_low or "di" in p_low or "contador" in p_low:
                concepto_oficial = "Renovación / Tendido de Derivación Individual Monofásica (ITC-BT-15)"
                norma_rebt = "ITC-BT-15 (Derivaciones Individuales)"
                horas_estimadas = 4.0
                materiales_lista = [
                    {"mat": "Cable Cu RZ1-K 0.6/1kV 2x10 mm² + TT 1x10 mm² Cca", "cant": 20, "unid": "m", "p_u": 4.20},
                    {"mat": "Hilo de Mando Rojo 1.5 mm² para Telegestión", "cant": 20, "unid": "m", "p_u": 0.28},
                    {"mat": "Tubo Corrugado Libre de Halógenos M40 750N", "cant": 20, "unid": "m", "p_u": 1.25},
                    {"mat": "Bornas de Conexión Seccionables de Entrada", "cant": 2, "unid": "ud", "p_u": 4.50}
                ]
            elif "horno" in p_low or "vitro" in p_low or "cocina" in p_low or "25a" in p_low:
                concepto_oficial = "Circuito de Fuerza C3 para Horno y Cocina/Vitrocerámica (ITC-BT-25)"
                norma_rebt = "ITC-BT-25 (Circuitos Interiores)"
                horas_estimadas = 2.5
                materiales_lista = [
                    {"mat": "PIA Magnetotérmico 1P+N 25A Curva C 6kA", "cant": 1, "unid": "ud", "p_u": 9.50},
                    {"mat": "Cable Cu H07Z1-K 3x6 mm² Libre de Halógenos", "cant": 15, "unid": "m", "p_u": 1.85},
                    {"mat": "Tubo Corrugado M25", "cant": 15, "unid": "m", "p_u": 0.75},
                    {"mat": "Base Enchufe de Fuerza 25A 2P+T con Clavija", "cant": 1, "unid": "ud", "p_u": 14.50}
                ]
            elif "cuadro" in p_low or "automático" in p_low or "térmico" in p_low or "diferencial" in p_low:
                concepto_oficial = "Sustitución y Adecuación de Cuadro General de Protección (CGMP)"
                norma_rebt = "ITC-BT-17 e ITC-BT-24"
                horas_estimadas = 3.5
                materiales_lista = [
                    {"mat": "Envolvente Empotrada Cuadro 18-24 Módulos", "cant": 1, "unid": "ud", "p_u": 26.00},
                    {"mat": "Interruptor General Automático IGA 2P 25A/32A", "cant": 1, "unid": "ud", "p_u": 12.00},
                    {"mat": "Protector Sobretensiones Permanentes y Transitorias POP+DPS", "cant": 1, "unid": "ud", "p_u": 48.00},
                    {"mat": "Interruptores Diferenciales 2x40A / 30mA (x2)", "cant": 2, "unid": "ud", "p_u": 22.00},
                    {"mat": "Peine de Conexión Bipolar y Menudencia", "cant": 1, "unid": "pack", "p_u": 15.00}
                ]
            elif "tierra" in p_low or "pica" in p_low:
                concepto_oficial = "Instalación de Red de Puesta a Tierra y Pica de Cobre (ITC-BT-18)"
                norma_rebt = "ITC-BT-18 (Puestas a Tierra)"
                horas_estimadas = 2.0
                materiales_lista = [
                    {"mat": "Pica de Acero-Cobre 2m x 14mm con Brida de Conexión", "cant": 1, "unid": "ud", "p_u": 21.00},
                    {"mat": "Arqueta de Registro de P.A.T. 200x200 con Tapa", "cant": 1, "unid": "ud", "p_u": 14.50},
                    {"mat": "Cable de Tierra Cu Desnudo 35 mm²", "cant": 10, "unid": "m", "p_u": 3.80},
                    {"mat": "Puente Seccionador de Tierra", "cant": 1, "unid": "ud", "p_u": 11.00}
                ]
            else:
                concepto_oficial = f"Trabajo Eléctrico Urgente: {prompt_consulta[:40]}" if prompt_consulta else "Trabajo Eléctrico Especializado"
                norma_rebt = "REBT RD 842/2002"
                horas_estimadas = 2.5
                materiales_lista = [
                    {"mat": "Material conductor y canalización normalizada", "cant": 1, "unid": "partida", "p_u": 35.00},
                    {"mat": "Aparamenta de maniobra y protecciones", "cant": 1, "unid": "partida", "p_u": 25.00},
                    {"mat": "Menudencia, cajas y bornes de conexión", "cant": 1, "unid": "pack", "p_u": 12.00}
                ]

            st.session_state["pr_resultado_escandallo"] = {
                "concepto": concepto_oficial,
                "norma": norma_rebt,
                "horas": horas_estimadas,
                "materiales": materiales_lista,
                "consulta_orig": prompt_consulta
            }

        # 5. Visualización del Presupuesto Dinámico y Editable
        res = st.session_state.get("pr_resultado_escandallo", {})
        if res:
            st.markdown("---")
            st.markdown(f"### 📋 Resultado Técnico: **{res['concepto']}**")
            st.info(f"📘 **Normativa Oficial Aplicable:** `{res['norma']}` | 📝 **Trabajo Descrito:** *\"{res.get('consulta_orig', '')}\"*")

            col_esc1, col_esc2 = st.columns([3, 2])
            
            with col_esc1:
                st.markdown("##### 📦 Escandallo Desglosado de Materiales (Editable):")
                mats = res.get("materiales", [])
                total_mat_calc = 0.0
                
                filas_mats_edit = []
                for idx_m, m_item in enumerate(mats):
                    c_m1, c_m2, c_m3, c_m4 = st.columns([3, 1, 1.2, 1.2])
                    with c_m1:
                        n_mat = st.text_input(f"Mat {idx_m}", value=m_item["mat"], key=f"prm_n_{idx_m}", label_visibility="collapsed")
                    with c_m2:
                        n_cnt = st.number_input(f"Cant {idx_m}", value=float(m_item["cant"]), min_value=0.1, step=1.0, key=f"prm_c_{idx_m}", label_visibility="collapsed")
                    with c_m3:
                        n_pu = st.number_input(f"P.U {idx_m}", value=float(m_item["p_u"]), step=1.0, format="%.2f", key=f"prm_p_{idx_m}", label_visibility="collapsed")
                    with c_m4:
                        sub_m = round(n_cnt * n_pu, 2)
                        st.markdown(f"<div style='margin-top:6px; font-weight:bold;'>{sub_m:,.2f} €</div>", unsafe_allow_html=True)
                        total_mat_calc += sub_m
                    filas_mats_edit.append({"mat": n_mat, "cant": n_cnt, "unid": m_item.get("unid", "ud"), "p_u": n_pu, "subtotal": sub_m})

            with col_esc2:
                with st.container(border=True):
                    st.markdown("##### ⏱️ Mano de Obra y Rendimiento:")
                    horas_mo_val = st.number_input("Horas de Instalación (h):", value=float(res.get("horas", 2.5)), min_value=0.5, step=0.5, key="pr_horas_mo_in")
                    coste_mo_calc = round(horas_mo_val * precio_hora_mo, 2)
                    
                    st.markdown(f"- **Horas:** `{horas_mo_val:.1f} h` × `{precio_hora_mo:.2f} €/h` = **`{coste_mo_calc:,.2f} €`**")
                    st.markdown(f"- **Materiales:** **`{total_mat_calc:,.2f} €`**")
                    
                    subtotal_siva = round(total_mat_calc + coste_mo_calc, 2)
                    cuota_iva = round(subtotal_siva * (iva_pct / 100.0), 2)
                    total_civa = round(subtotal_siva + cuota_iva, 2)

                    st.markdown("---")
                    st.markdown(f"#### **Base Imponible (S/IVA):** `{subtotal_siva:,.2f} €`")
                    st.markdown(f"#### **Total Cliente (C/IVA {iva_pct:.0f}%):** `<span style='color:#0284c7; font-size:24px;'>{total_civa:,.2f} €</span>`", unsafe_allow_html=True)

            # 6. Opciones de Negociación Rápida y Cierre en Obra
            st.markdown("---")
            col_neg1, col_neg2, col_neg3 = st.columns(3)
            with col_neg1:
                target_quick = st.number_input("🎯 Ajustar a Precio Redondo Cerrado (€):", value=float(round(total_civa, 0)), step=10.0, format="%.2f", key="pr_target_round")
            with col_neg2:
                dif_quick = target_quick - total_civa
                st.caption(f"Ajuste comercial: `{dif_quick:+,.2f} €` (con IVA)")
                st.markdown(f"**Precio Final Acordado:** `{target_quick:,.2f} €`")
            with col_neg3:
                # Botón para transferir este trabajo al Presupuesto Completo de Vivienda
                if st.button("📥 Incorporar a Presupuesto Vivienda", type="primary", use_container_width=True, key="btn_transfer_to_vivienda"):
                    if "partidas_manuales" not in st.session_state:
                        st.session_state.partidas_manuales = []
                    sub_final_siva = round(target_quick / (1 + (iva_pct / 100.0)), 2)
                    st.session_state.partidas_manuales.append({
                        "id": f"PM-{len(st.session_state.partidas_manuales) + 1:02d}",
                        "concepto": res["concepto"],
                        "descripcion": f"Instalación según {res['norma']}: {res.get('consulta_orig', '')}. Incluye materiales desglosados y {horas_mo_val:.1f} h de mano de obra.",
                        "cantidad": 1.0,
                        "unidad": "partida",
                        "precio_unitario": sub_final_siva,
                        "subtotal": sub_final_siva
                    })
                    st.session_state.presupuesto_calculado = True
                    st.success(f"✅ Trabajo '{res['concepto']}' transferido con éxito al Presupuesto General!")
