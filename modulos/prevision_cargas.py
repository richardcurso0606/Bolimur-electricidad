import streamlit as st

# =========================================================================
# CONSTANTES Y FUNCIONES EXCLUSIVAS DE PREVISIÓN
# =========================================================================
def get_coef_simultaneidad(num):
    tabla = {1: 1.0, 2: 2.0, 3: 3.0, 4: 3.8, 5: 4.6, 6: 5.4, 7: 6.2, 8: 7.0, 9: 7.8, 10: 8.5, 
             11: 9.1, 12: 9.8, 13: 10.5, 14: 11.2, 15: 11.9, 16: 12.6, 17: 13.3, 18: 14.0, 19: 14.7, 20: 15.4}
    if num <= 0: return 0.0
    if num <= 20: return tabla.get(num, 15.4)
    return float(round(15.4 + (num - 20) * 0.7, 2))

# =========================================================================
# FUNCIÓN MAESTRA DEL MÓDULO
# =========================================================================
def renderizar():

    # Blindaje total de variables de sesión
    if 'grupos_viviendas' not in st.session_state:
        st.session_state.grupos_viviendas = [{"nombre": "Plantas 1ª a 4ª (Básica)", "qty": 8, "pot": 5750, "nocturna": False}]
    if 'locales' not in st.session_state:
        st.session_state.locales = [{"nombre": "Locales Comerciales", "qty": 2, "superficie": 100.0}]
    if 'servicios_generales' not in st.session_state:
        st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 1, "potencia": 4000.0, "factor": 1.30, "cos_phi": 1.0}]
    if 'garajes' not in st.session_state:
        st.session_state.garajes = {
            "sup": 240.0, 
            "plazas_irve": 18, 
            "esquema_irve": "Esquema 3a (Conexión al contador de la vivienda)",
            "spl": False
        }

    if "esquema_irve" not in st.session_state.garajes:
        st.session_state.garajes["esquema_irve"] = "Esquema 3a (Conexión al contador de la vivienda)"
        st.session_state.garajes["spl"] = False

    st.title("🏢 Previsión de Cargas (ITC-BT-10)")
    
    col_t1, col_b1 = st.columns([4, 1])
    with col_t1: 
        st.write("Desarrollo analítico y reglamentario para el cálculo de la Potencia Total Prevista ($P_t$) del edificio.")
    with col_b1:
        if st.button("🔄 Resetear Todo"): 
            st.session_state.grupos_viviendas = [{"nombre": "Plantas 1ª a 4ª (Básica)", "qty": 8, "pot": 5750, "nocturna": False}]
            st.session_state.locales = [{"nombre": "Locales Comerciales", "qty": 2, "superficie": 100.0}]
            st.session_state.servicios_generales = [{"nombre": "Ascensor principal", "qty": 1, "potencia": 4000.0, "factor": 1.30, "cos_phi": 1.0}]
            st.session_state.garajes = {
                "sup": 240.0, 
                "plazas_irve": 18, 
                "esquema_irve": "Esquema 3a (Conexión al contador de la vivienda)",
                "spl": False
            }
            st.rerun()

    # --- 1. VIVIENDAS ---
    st.header("1. Viviendas ($P_1$)")
    if st.button("➕ Añadir Grupo de Viviendas"): 
        st.session_state.grupos_viviendas.append({"nombre": f"Grupo {len(st.session_state.grupos_viviendas)+1}", "qty": 2, "pot": 5750, "nocturna": False})

    with st.expander("📖 Criterios REBT: Electrificación Básica o Elevada y Tabla ITC-BT-10"):
        st.markdown("""
        * **Básica (5.750 W):** Necesidades primarias (viviendas habituales estándar).
        * **Elevada (9.200 W o más):** Superficies > 160 m², calefacción eléctrica o domótica/automatización.
        """)
        tabla_k_markdown = """
| Nº VIVIENDAS (n) | COEFICIENTE K | Nº VIVIENDAS (n) | COEFICIENTE K |
| :--- | :--- | :--- | :--- |
| n = 1 | 1,0 | n = 11 | 9,1 |
| n = 2 | 2,0 | n = 12 | 9,8 |
| n = 3 | 2,8 | n = 13 | 10,5 |
| n = 4 | 3,6 | n = 14 | 11,2 |
| n = 5 | 4,4 | n = 15 | 11,9 |
| n = 6 | 5,2 | n = 16 | 12,6 |
| n = 7 | 6,0 | n = 17 | 13,3 |
| n = 8 | 6,8 | n = 18 | 14,0 |
| n = 9 | 7,6 | n = 19 | 14,7 |
| n = 10 | 8,4 | n = 20 | 15,4 |
        """
        st.markdown(tabla_k_markdown)
        st.markdown("*Nota reglamentaria:* Para más de 20 viviendas se aplica la fórmula 15,4 + 0,7 · (n - 20).")

    st.markdown("---")

    pot_total_viviendas = 0
    viviendas_diurnas_qty = sum(v["qty"] for v in st.session_state.grupos_viviendas if not v["nocturna"])
    k_diurno = get_coef_simultaneidad(max(viviendas_diurnas_qty, 1))

    opciones_potencia = {
        "5.750 W (Básica - Estándar)": 5750,
        "7.360 W (Elevada - Moderada)": 7360,
        "9.200 W (Elevada - Domótica / Clima)": 9200,
        "11.500 W (Elevada - Gran Superficie)": 11500,
        "✏️ Personalizada (Introducir W)": -1
    }
    lista_etiquetas = list(opciones_potencia.keys())
    lista_valores = list(opciones_potencia.values())

    for idx, viv in enumerate(st.session_state.grupos_viviendas):
        with st.container(border=True):
            st.markdown(f"#### Grupo #{idx+1}: {viv['nombre']}")

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            with c1: 
                viv["nombre"] = st.text_input(f"Descripción #{idx+1}", viv["nombre"], key=f"v_n_{idx}")
            with c2: 
                viv["qty"] = st.number_input(f"Nº Viv.", min_value=0, value=int(viv["qty"]), key=f"v_q_{idx}")
            
            pot_actual = viv["pot"]
            curr_idx = lista_valores.index(pot_actual) if pot_actual in lista_valores else 4
                
            with c3: 
                sel_etiqueta = st.selectbox(f"Pot. Unitaria", lista_etiquetas, index=curr_idx, key=f"v_p_{idx}")
                if sel_etiqueta.startswith("✏️"):
                    viv["pot"] = st.number_input(f"Valor personalizado (W)", min_value=0, value=int(pot_actual if pot_actual > 0 else 7000), step=100, key=f"v_custom_{idx}")
                else:
                    viv["pot"] = opciones_potencia[sel_etiqueta]
                
            with c4: 
                viv["nocturna"] = st.checkbox(f"Tarifa Nocturna", value=viv["nocturna"], key=f"v_no_{idx}")
            with c5:
                st.write(""); st.write("")
                if st.button("🗑️", key=f"del_v_{idx}"):
                    if len(st.session_state.grupos_viviendas) > 1: 
                        st.session_state.grupos_viviendas.pop(idx)
                        st.rerun()

            if viv["nocturna"]:
                pot_parcial = int(round(viv["qty"] * viv["pot"]))
            else:
                if viviendas_diurnas_qty > 0:
                    pot_parcial = int(round(viv["qty"] * viv["pot"] * (k_diurno / viviendas_diurnas_qty)))
                else:
                    pot_parcial = 0

            pot_total_viviendas += pot_parcial

            with st.expander(f"🔍 Ver Justificación Analítica: {viv['nombre']} (Parcial: {pot_parcial:,} W)"):
                if viv["nocturna"]:
                    st.info(
                        f"**Desarrollo de Cálculo (Tarifa Nocturna):**\n\n"
                        f"- Nº de viviendas: **{viv['qty']}**\n"
                        f"- Potencia unitaria: **{viv['pot']:,} W**\n"
                        f"- Criterio: Al estar bajo régimen nocturno, computa al 100% de su potencia sin coeficiente de simultaneidad diurno.\n\n"
                        f"**Fórmula:** P_parcial = Nº Viv. * Pot. Unitaria\n"
                        f"**Resultado parcial:** **{pot_parcial:,} W**"
                    )
                else:
                    st.info(
                        f"**Desarrollo de Cálculo (ITC-BT-10):**\n\n"
                        f"- Total de viviendas diurnas en el edificio (n): **{viviendas_diurnas_qty}**\n"
                        f"- Coeficiente de simultaneidad de tabla (K): **{k_diurno}**\n"
                        f"- Viviendas en este grupo: **{viv['qty']}**\n"
                        f"- Potencia unitaria: **{viv['pot']:,} W**\n\n"
                        f"**Fórmula reglamentaria aplicada:**\n"
                        f"P_parcial = (Nº Viv. grupo * Pot. Unitaria) * (K / n_diurnas)\n\n"
                        f"**Sustitución numérica:**\n"
                        f"({viv['qty']} * {viv['pot']:,}) * ({k_diurno} / {viviendas_diurnas_qty}) = **{pot_parcial:,} W**"
                    )

    # --- DESGLOSE Y JUSTIFICACIÓN DEL SUBTOTAL DE VIVIENDAS ---
    st.markdown("---")
    st.markdown(f"### 📌 Subtotal Viviendas ($P_1$): **{pot_total_viviendas:,} W**")
    
    with st.expander("📖 Ver Justificación, Operación Matemática y Leyenda de Variables ($P_1$)"):
        detalle_grupos = []
        suma_bruta_diurna = 0
        for g in st.session_state.grupos_viviendas:
            if not g["nocturna"]:
                parcial_grupo = g["qty"] * g["pot"]
                suma_bruta_diurna += parcial_grupo
                detalle_grupos.append(f"({g['qty']} viv. * {g['pot']:,} W)")

        formula_str = " + ".join(detalle_grupos) if detalle_grupos else "0"

        st.info(
            f"**1. Criterio Normativo (ITC-BT-10):**\n"
            f"La potencia total prevista para el conjunto de viviendas se calcula aplicando el coeficiente de simultaneidad $K$ correspondiente al número total de viviendas diurnas del edificio ($n = {viviendas_diurnas_qty}$), obteniendo un coeficiente $K = {k_diurno}$[cite: 3].\n\n"
            f"**2. Leyenda y Definición de Variables:**\n"
            f"- **P1**: Potencia total prevista para el conjunto de viviendas (W)[cite: 3].\n"
            f"- **n_i**: Número de viviendas de cada grupo con la misma potencia unitaria[cite: 3].\n"
            f"- **P_u,i**: Potencia unitaria asignada a cada vivienda del grupo (W)[cite: 3].\n"
            f"- **K**: Coeficiente de simultaneidad obtenido de la tabla ITC-BT-10 según el total de viviendas diurnas ($n = {viviendas_diurnas_qty} \\rightarrow K = {k_diurno}$)[cite: 3].\n"
            f"- **n_diurnas**: Número total de viviendas diurnas del edificio ({viviendas_diurnas_qty})[cite: 3].\n"
            f"- **P_nocturnas**: Potencia de viviendas con tarifa nocturna (computan al 100% sin simultaneidad diurna)[cite: 3].\n\n"
            f"**3. Operación Matemática Detallada:**\n"
            f"P1 = [ Σ (n_i * P_u,i) ] * (K / n_diurnas) + Σ P_nocturnas[cite: 3]\n\n"
            f"**Sustitución Numérica:**\n"
            f"P1 = [ {formula_str} ] * ({k_diurno} / {viviendas_diurnas_qty})[cite: 3]\n"
            f"P1 = [ {suma_bruta_diurna:,} W ] * {(k_diurno / viviendas_diurnas_qty if viviendas_diurnas_qty > 0 else 0):.4f}[cite: 3]\n"
            f"**Resultado Final P1 = {pot_total_viviendas:,} W**[cite: 3]"
        )
    
    # --- 2. LOCALES COMERCIALES ---
    st.markdown("---")
    st.header("2. Locales Comerciales ($P_2$)")
    if st.button("➕ Añadir Local"): 
        st.session_state.locales.append({"nombre": f"Local {len(st.session_state.locales)+1}", "qty": 1, "superficie": 100.0})
    
    pot_total_locales = 0.0
    for idx, loc in enumerate(st.session_state.locales):
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            with c1: loc["nombre"] = st.text_input(f"Local", loc["nombre"], key=f"l_n_{idx}")
            with c2: loc["superficie"] = st.number_input(f"Sup. m²", value=float(loc.get("superficie", 100.0)), key=f"l_s_{idx}")
            with c3: loc["qty"] = st.number_input(f"Cantidad", value=int(loc.get("qty", 1)), key=f"l_q_{idx}")
            with c4:
                st.write(""); st.write("")
                if st.button("🗑️", key=f"del_l_{idx}"): 
                    st.session_state.locales.pop(idx); st.rerun()

            pot_u = max(loc["superficie"] * 100.0, 3450.0 if loc["superficie"] > 0 else 0.0)
            pot_parcial = pot_u * loc["qty"]
            pot_total_locales += pot_parcial
            
            with st.expander(f"🔍 Ver Justificación Analítica: {loc['nombre']} (Parcial: {pot_parcial:,.0f} W)"):
                st.info(f"""
                **Justificación Analítica:**[cite: 3]
                El REBT exige un mínimo de 100 W/m² con un suelo de 3.450 W por local comercial[cite: 3].
                P_local = max(Superficie * 100, 3450) * Cantidad[cite: 3]
                **Cálculo:** max({loc['superficie']} * 100, 3450) * {loc['qty']} = **{pot_parcial:,.0f} W**[cite: 3]
                """)

    st.markdown(f"### 📌 Subtotal Locales Comerciales ($P_2$): **{pot_total_locales:,.0f} W**")

    # --- 3. SERVICIOS GENERALES ---
    st.markdown("---")
    st.header("3. Servicios Generales ($P_3$)")
    if st.button("➕ Añadir Servicio"): 
        st.session_state.servicios_generales.append({"nombre": "Nuevo Servicio", "potencia": 0.0, "factor": 1.30, "cos_phi": 1.0, "qty": 1})
    
    pot_total_servicios = 0.0
    
    # Opciones completas con sus factores K explícitos y visibles
    opciones_factores_k = {
        "Ascensor / Motores principales (K = 1.30)": 1.30,
        "Bombas de agua / Presión (K = 1.25)": 1.25,
        "Alumbrado Fluorescente / Descarga (K = 1.80)": 1.80,
        "Iluminación incandescente / Estándar (K = 1.00)": 1.00,
        "✏️ Personalizado (K a medida)": -1
    }

    for idx, serv in enumerate(st.session_state.servicios_generales):
        with st.container(border=True):
            st.markdown(f"**Servicio #{idx+1}: {serv['nombre']}**")
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1: serv["nombre"] = st.text_input(f"Descripción del Servicio", serv["nombre"], key=f"s_n_{idx}")
            with c2: serv["potencia"] = st.number_input(f"Potencia unitaria (W)", value=float(serv.get("potencia", 0.0)), key=f"s_p_{idx}")
            with c3: serv["qty"] = st.number_input(f"Cantidad (Uds.)", value=int(serv.get("qty", 1)), key=f"s_q_{idx}")

            c4, c5, c6 = st.columns([3, 2, 1])
            factor_actual = serv.get("factor", 1.30)
            lista_k_keys = list(opciones_factores_k.keys())
            lista_k_vals = list(opciones_factores_k.values())
            
            if factor_actual in lista_k_vals:
                def_opt_idx = lista_k_vals.index(factor_actual)
            else:
                def_opt_idx = 4 # Opción personalizada

            with c4:
                sel_opt = st.selectbox(f"Multiplicador (K)", lista_k_keys, index=def_opt_idx, key=f"serv_tipo_opt_{idx}")
                if sel_opt.startswith("✏️"):
                    factor = st.number_input(f"Valor personalizado K", min_value=1.0, max_value=5.0, value=float(factor_actual if factor_actual > 0 else 1.30), step=0.05, key=f"s_custom_k_{idx}")
                else:
                    factor = opciones_factores_k[sel_opt]
                serv["factor"] = factor
                
            with c5:
                serv["cos_phi"] = st.number_input(f"Coseno phi (cos φ)", min_value=0.5, max_value=1.0, value=float(serv.get("cos_phi", 1.0)), step=0.05, key=f"s_cos_{idx}")
                
            with c6:
                st.write("")
                if st.button("🗑️", key=f"del_s_{idx}"): 
                    st.session_state.servicios_generales.pop(idx); st.rerun()
            
            cos_val = serv.get("cos_phi", 1.0)
            if factor == 1.80 and cos_val < 1.0:
                p_parcial = serv["potencia"] * serv["qty"] * factor * cos_val
            else:
                p_parcial = serv["potencia"] * serv["qty"] * factor

            pot_total_servicios += p_parcial
            
            with st.expander(f"🔍 Ver Justificación Analítica (Parcial: {p_parcial:,.2f} W)"):
                st.info(
                    f"**Expresión reglamentaria:** P_servicio = P_unitaria * Uds. * K * (cos φ)[cite: 3]\n\n"
                    f"**Sustitución numérica:** {serv['potencia']} W * {serv['qty']} ud(s) * {factor}" + (f" * {cos_val}" if factor == 1.80 and cos_val < 1.0 else "") + f"\n\n"
                    f"**Subtotal del servicio:** **{p_parcial:,.2f} W**[cite: 3]"
                )

    st.markdown(f"### 📌 Subtotal Servicios Generales ($P_3$): **{pot_total_servicios:,.2f} W**")

    # --- 4. GARAJES E IRVE (REDISEÑADO CON RIGOR ITC-BT-52) ---
    st.markdown("---")
    st.header("4. Garajes e Infraestructura de Recarga (IRVE - ITC-BT-52)")
    
    with st.expander("📖 Ayuda Técnica: Esquemas Oficiales de Conexión IRVE (ITC-BT-52)"):
        st.markdown("""
        El Reglamento Electrotécnico (**ITC-BT-52**) define legalmente la forma de conectar el cargador del vehículo eléctrico a la red[cite: 3]. Conocer el esquema es vital para dimensionar correctamente la Línea General de Alimentación del edificio[cite: 3].

        <div style="overflow-x: auto; margin-top: 10px; margin-bottom: 10px;">
        <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background-color: #1e293b; color: #ffffff; text-align: left; font-size: 13px;">
                    <th style="padding: 10px 14px;">ESQUEMA OFICIAL</th>
                    <th style="padding: 10px 14px;">DESCRIPCIÓN TOPOLÓGICA</th>
                    <th style="padding: 10px 14px;">USO HABITUAL</th>
                </tr>
            </thead>
            <tbody style="font-size: 13px; color: #334155;">
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #0284c7;">Esquema 1</td>
                    <td style="padding: 10px 14px;">Instalación colectiva con un contador principal general y contadores secundarios por plaza.</td>
                    <td style="padding: 10px 14px;">Parkings públicos, centros comerciales, flotas de empresa.</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #0284c7;">Esquema 2</td>
                    <td style="padding: 10px 14px;">Instalación individual con un contador principal nuevo exclusivo para el coche en el cuarto de centralización.</td>
                    <td style="padding: 10px 14px;">Usuarios que contratan un suministro eléctrico totalmente nuevo solo para el garaje.</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #166534;">Esquema 3a</td>
                    <td style="padding: 10px 14px;">Conexión directa empalmando en los bornes de salida del contador principal de la vivienda.</td>
                    <td style="padding: 10px 14px; font-weight: bold;">El más común en garajes comunitarios (bloques de pisos). Aprovecha el contrato de la casa.</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0; background-color: #f8fafc;">
                    <td style="padding: 10px 14px; font-weight: bold; color: #166534;">Esquema 3b</td>
                    <td style="padding: 10px 14px;">Conexión que nace de un magnetotérmico dedicado dentro del Cuadro General (CGMP) de la vivienda.</td>
                    <td style="padding: 10px 14px;">Viviendas unifamiliares, chalets o adosados con garaje propio.</td>
                </tr>
                <tr>
                    <td style="padding: 10px 14px; font-weight: bold; color: #0284c7;">Esquema 4</td>
                    <td style="padding: 10px 14px;">Circuito que cuelga directamente de un cuadro general existente en un local comercial.</td>
                    <td style="padding: 10px 14px;">Negocios, talleres u oficinas con plazas privadas.</td>
                </tr>
            </tbody>
        </table>
        </div>
        
        * **Protecciones exigidas:** Diferencial Tipo A (mínimo) o Tipo B, más protección contra sobretensiones transitorias y permanentes dedicada[cite: 3].
        * **SPL (Sistema de Protección de la Línea):** Control dinámico inteligente. Si la vivienda consume mucho, baja la potencia del coche para no exceder la potencia contratada[cite: 3]. Permite reducir el factor de simultaneidad al 5%[cite: 3].
        """, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("#### ⚙️ Parámetros del Garaje y Puntos de Recarga")
        
        g1, g2 = st.columns(2)
        with g1: 
            st.session_state.garajes["sup"] = st.number_input("Superficie del Garaje (m²)", value=float(st.session_state.garajes["sup"]), min_value=0.0)
            st.session_state.garajes["plazas_irve"] = st.number_input("Nº Plazas Totales en el Garaje", value=int(st.session_state.garajes["plazas_irve"]), min_value=0)
        with g2: 
            tipo_vent = st.selectbox("Tipo de Ventilación (afecta a la carga base)", ["Forzada (20 W/m²)", "Natural (10 W/m²)"])
            st.session_state.garajes["spl"] = st.checkbox("✅ Instalar Control Dinámico (SPL) en los cargadores", value=st.session_state.garajes["spl"])

        st.markdown("#### 🔌 Selección de Esquema Topológico (ITC-BT-52)")
        opciones_esquema = [
            "Esquema 1 (Instalación colectiva con contadores secundarios)",
            "Esquema 2 (Instalación individual con contador nuevo exclusivo)",
            "Esquema 3a (Conexión al contador de la vivienda - Bloques de pisos)",
            "Esquema 3b (Conexión al cuadro general CGMP - Unifamiliares)",
            "Esquema 4 (Conexión al cuadro de local comercial o nave)"
        ]
        
        idx_esq = 2
        for i, opt in enumerate(opciones_esquema):
            if st.session_state.garajes["esquema_irve"].split(" ")[0] in opt:
                idx_esq = i; break
                
        st.session_state.garajes["esquema_irve"] = st.selectbox("Esquema Reglamentario de Conexión", opciones_esquema, index=idx_esq)

        # CÁLCULOS INTERNOS IRVE
        sup_g = st.session_state.garajes["sup"]
        ratio_vent = 20.0 if "Forzada" in tipo_vent else 10.0
        p_gar = max(sup_g * ratio_vent, 3450.0 if sup_g > 0 else 0.0)
        
        # Factor inteligente según normativa y SPL
        factor_irve_val = 0.05 if st.session_state.garajes["spl"] else 0.10
        plazas_calculo = st.session_state.garajes["plazas_irve"] * factor_irve_val
        p_irve = plazas_calculo * 3680.0
        
        pot_total_garaje = p_gar + p_irve

        if sup_g > 0 or st.session_state.garajes["plazas_irve"] > 0:
            with st.expander(f"🔍 Ver Justificación Analítica Garajes e IRVE (Total: {pot_total_garaje:,.2f} W)"):
                st.info(
                    f"**1. Demanda Base del Garaje (Ventilación {tipo_vent}):**[cite: 3]\n"
                    f"P_base = max(Superficie * {ratio_vent} W/m², Mínimo REBT 3.450 W)[cite: 3]\n"
                    f"P_base = {sup_g} m² * {ratio_vent} = **{p_gar:,.0f} W**[cite: 3]\n\n"
                    f"**2. Previsión Vehículo Eléctrico (Cargadores a 3.680 W):**[cite: 3]\n"
                    f"Al configurar la instalación bajo el **{st.session_state.garajes['esquema_irve'].split(' ')[0]}** y "[cite: 3]
                    f"{'**contar con SPL (Control Dinámico)**, el factor de simultaneidad se reduce al **5%**.' if st.session_state.garajes['spl'] else '**NO contar con SPL**, se aplica el factor de simultaneidad por defecto del **10%**.'}[cite: 3]\n\n"
                    f"P_IRVE = Total Plazas * Factor Simultaneidad * Potencia Cargador[cite: 3]\n"
                    f"P_IRVE = {st.session_state.garajes['plazas_irve']} plazas * {int(factor_irve_val*100)}% = {plazas_calculo:.1f} plazas simultáneas * 3.680 W = **{p_irve:,.2f} W**[cite: 3]\n\n"
                    f"**3. Potencia Total Prevista de Garaje ($P_4$):** {p_gar:,.0f} W + {p_irve:,.2f} W = **{pot_total_garaje:,.2f} W**[cite: 3]"
                )

    st.markdown(f"### 📌 Subtotal Garajes y Recarga ($P_4$): **{pot_total_garaje:,.2f} W**")  
    
    # --- RESULTADO GLOBAL ---
    st.markdown("---")
    pt_total = pot_total_viviendas + pot_total_locales + pot_total_servicios + pot_total_garaje

    st.success(f"""
    ### ✅ POTENCIA TOTAL PREVISTA DEL EDIFICIO ($P_t$): {pt_total:,.2f} W
    
    **Desglose acumulado para la memoria técnica:**[cite: 3]
    * 🏠 Total Viviendas ($P_1$): **{pot_total_viviendas:,} W**[cite: 3]
    * 🏪 Total Locales Comerciales ($P_2$): **{pot_total_locales:,.0f} W**[cite: 3]
    * 💡 Total Servicios Generales ($P_3$): **{pot_total_servicios:,.2f} W**[cite: 3]
    * 🚗 Total Garajes e IRVE ($P_4$): **{pot_total_garaje:,.2f} W**[cite: 3]
    
    *Valor listo y optimizado para el cálculo inmediato de la Línea General de Alimentación (LGA).*[cite: 3]
    """)
