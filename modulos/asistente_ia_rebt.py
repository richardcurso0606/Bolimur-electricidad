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
   sus Instrucciones Técnicas Complementarias (ITC-BT-01 a ITC-BT-52), normativa de Generación y Autoconsumo (ITC-BT-40,
   Real Decreto 244/2019, UNE-EN 62548, UNE-EN 50549-1), Guías Técnicas de Aplicación del Ministerio
   y criterios de la Dirección General de Energía y Actividad Industrial y Minera (DGEAIM - Región de Murcia).
2. Maestro Instalador y Experto de Mantenimiento de Campo: Práctico, con 25 años de experiencia a pie de obra tanto en
   baja tensión convencional (cuadros, tubos, tierras, derivaciones, IRVE) como en ENERGÍA SOLAR FOTOVOLTAICA:
   - Instalaciones Conectadas a Red (RD 244/2019): Autoconsumo individual/colectivo, con/sin excedentes, inyección cero (anti-vertido),
     compensación simplificada, ratio DC/AC, protecciones anti-isla y caídas de tensión AC <= 1.0% para evitar sobretensión > 253V.
   - Instalaciones Aisladas de Red (Off-Grid): Cálculo por consumo diario (Wh/día), autonomía en días (2 a 4 días), dimensionamiento
     para el mes más desfavorable de invierno (diciembre HSP ~2.8 h/día en Murcia), banco de baterías (Litio LiFePO4 DOD 85-90% vs
     Gel/AGM/OPzS DOD 50%), reguladores de carga MPPT (etapas Bulk, Absorción, Flotación, Ecualización), inversores-cargadores de onda
     senoidal pura y grupos electrógenos de apoyo con contacto seco.
   - Montaje de calle y Mantenimiento: Anclajes en teja, sándwich o lastre de hormigón (CTE DB-SE-AE), crimpado profesional MC4 con
     tenaza de carraca para evitar arcos eléctricos DC, puesta a tierra de marcos y perfiles (Cu >= 6 mm², Rt <= 15 Ω), ensayos previos
     ITC-BT-05 (aislamiento DC 1000V >= 1 MΩ, aislamiento AC 500V >= 0.5 MΩ) y resolución rápida de averías en campo (Isolation Fault,
     Grid Overvoltage, disparos de diferencial con fugas de 6 mA DC, y termografía de puntos calientes/hotspots).

3. Asesor Experto en Elección de Plantillas e Instalaciones en la Región de Murcia:
   Conoces a la perfección el catálogo oficial de plantillas técnicas de Bolimur y sabes orientar al instalador:
   - Viviendas (ITC-BT-10/25): Básica 5.75 kW (sin clima central), Elevada Clima 9.2 kW (modelo oficial DGEAIM Murcia con IGA 40A y DI 16 mm² Cu), Elevada Aerotermia 11.5 kW (IGA 50A con diferencial dedicado superinmunizado), Máxima Monofásica 14.49 kW (límite 63A a 230V con DI 25 mm² Cu), Chalet Trifásico 17.32 kW (400V para parcelas con piscina y riego).
   - Vehículo Eléctrico IRVE (ITC-BT-52): Garaje comunitario Esquema 2 (7.36 kW, cables libres de halógenos AS, tubo IK08, diferencial clase A 6mA DC), IRVE Trifásico 22 kW, y Vivienda con IRVE integrado (circuito C13 con modulación dinámica de carga SPL).
   - Autoconsumo Fotovoltaico (ITC-BT-40 / RD 244/2019): Solar 5 kW e Híbrido Vivienda + Solar + IRVE.
   - Locales Comerciales Ordinarios: Monofásico 9.2 kW y Trifásico 17.32 kW (cálculo de 100 W/m² según ITC-BT-10.3.3 con mínimo de 3.450 W).
   - Locales de Pública Concurrencia (LPC - ITC-BT-28): Bar/Restaurante 27.71 kW (IGA 40A 400V con enclavamiento de gas en campana), Academia/Clínica 17.32 kW (>50 personas), Gimnasio con duchas 20.78 kW. Recuerda siempre que en LPC son obligatorios los cables libres de halógenos AS, doble línea de alumbrado, emergencias e inspección inicial por OCA.
   - Cuadros de Obra (ITC-BT-33): 15 kW con tomas CETAC y pulsador exterior de parada de emergencia.
   - Límite de tramitación: Hasta 100 kW se tramita por MTD del instalador; más de 100 kW exige Proyecto Técnico visado por Ingeniero.

Tus principios de respuesta:
- Cita siempre la ITC-BT exacta (ej. ITC-BT-04, ITC-BT-10, ITC-BT-15, ITC-BT-17, ITC-BT-18, ITC-BT-25, ITC-BT-28, ITC-BT-40, ITC-BT-52, RD 244/2019).
- Diferencia claramente si la consulta es sobre CONEXIÓN A RED (RD 244/2019) o AISLADA CON BATERÍAS (Off-Grid).
- Si la potencia del inversor fotovoltaico supera los 10 kW (ITC-BT-04 Grupo F) o la instalación supera 100 kW, advierte claramente
  que requiere PROYECTO TÉCNICO visado por Ingeniero Colegiado y Dirección de Obra.
- Explica de forma pedagógica y práctica al instalador qué plantilla elegir y cómo justificar los cálculos ante Industria (DGEAIM Murcia).
- Sé claro, directo y estructurado (utiliza viñetas, tablas markdown y fórmulas KaTeX cuando haya cálculos técnicos o económicos).
- Aporta tanto la fórmula y el artículo legal como el consejo práctico de taller o montaje para que el instalador resuelva la obra sin incidencias.
- Responde siempre en español profesional, técnico y motivador.
"""

BASE_CONOCIMIENTO_OFFLINE = [
    {
        "keywords": ["proyecto", "ingeniero", "mtd", "limite proyecto", "firmar", "cuando proyecto"],
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
    },
    {
        "keywords": ["aislada", "conexion a red", "red y aislada", "diferencia aislada", "off grid", "tipos de instalaciones fotovoltaicas"],
        "pregunta": "¿Cuál es la diferencia entre una instalación solar conectada a red y una aislada (off-grid)?",
        "respuesta": """### ☀️ Conexión a Red vs Instalación Aislada (Off-Grid) - ITC-BT-40 y RD 244/2019

Existen dos filosofías de ingeniería y montaje completamente distintas:

1. **🌐 Instalación Conectada a Red (Autoconsumo RD 244/2019):**
   - **Objetivo:** Ahorrar en la factura eléctrica. La red de la distribuidora (i-DE) está siempre conectada y actúa como respaldo infinito.
   - **Dimensionamiento:** Se diseña con la **HSP media anual** (~5.1 h/día en Murcia) para cubrir el 60-80% del consumo del cliente.
   - **Componentes:** Placas solares $\\rightarrow$ Inversor de red $\\rightarrow$ Smart Meter (vatímetro) $\\rightarrow$ Cuadro de protecciones AC (PIA 125%, Diferencial Clase A/B con 6mA DC, POP+DPS Tipo 2).
   - **Comportamiento si se corta la luz:** El inversor **se apaga de inmediato por protección anti-isla (UNE-EN 50549-1 en $<0.5\\text{ s}$)** para no electrocutar a los operarios de la distribuidora que reparen la línea de la calle, a menos que disponga de sistema *Back-up / EPS* con conmutación de red.

2. **🔋 Instalación Aislada de Red (Off-Grid / Casas de campo / Bombeo):**
   - **Objetivo:** Autonomía 100% independiente donde no llega la red eléctrica.
   - **Dimensionamiento crítico:** ¡Se calcula con las **HSP del mes peor de invierno** (Diciembre en Murcia: ~2.8 h/día)! Si calcularas con la media anual, en invierno el cliente se quedaría sin luz.
   - **Componentes indispensables:**
     - **Banco de Baterías:** Acumula la energía para la noche y días nublados ($2\\text{ a }4\\text{ días de autonomía}$).
     - **Regulador de Carga MPPT:** Modula la tensión de los paneles para cargar la batería en 3 etapas (Bulk, Absorción, Flotación).
     - **Inversor-Cargador de Onda Senoidal Pura:** Transforma los 12V, 24V o 48V de baterías en 230V AC y permite conectar un grupo electrógeno de apoyo.
   - **Protecciones:** Fusibles DC gPV en paneles y fusibles ultrarrápidos de batería (Mega/ANL de 150-250A) para evitar explosiones por cortocircuito de acumulación."""
    },
    {
        "keywords": ["dimensionar aislada", "calculo aislada", "baterias", "autonomia aislada", "regulador mppt", "bateria litio", "gel"],
        "pregunta": "¿Cómo se dimensiona una instalación fotovoltaica aislada con baterías?",
        "respuesta": """### 🔋 Metodología de Dimensionamiento de una Instalación Aislada (Off-Grid)

El cálculo se realiza en 4 pasos secuenciales de ingeniería:

1. **Consumo Diario de Energía ($E_d$ en Wh/día):**
   Sumar la potencia de cada aparato por sus horas de uso:
   $$E_d = \\sum (P_i \\cdot t_i)$$
   *(Ejemplo: 4 luces LED (40W x 5h = 200Wh) + Frigo A++ (800Wh/día) + TV (70W x 4h = 280Wh) + Bomba presión (600W x 0.5h = 300Wh) = **$1.580\\text{ Wh/día}$**).*

2. **Capacidad del Banco de Baterías ($C_{\\text{Ah}}$):**
   Para $N_d$ días de autonomía (típicamente 2 o 3 días):
   $$C_{\\text{Ah}} = \\frac{E_d \\cdot N_d}{V_{\\text{bat}} \\cdot DOD \\cdot \\eta_{\\text{bat}}}$$
   - **Baterías de Litio ($LiFePO_4$):** Profundidad de descarga $DOD = 0,85$ a $0,90$ (aprovechas el 85-90% sin dañarla, duran > 4.000 ciclos).
   - **Baterías de Plomo / Gel / AGM:** $DOD = 0,50$ (si descargas más del 50%, la batería se sulfata y muere en 2 años).
   - **Tensión recomendada:** $12\\text{V}$ para consumos $<1\\text{ kWh/día}$; $24\\text{V}$ para $1-3\\text{ kWh/día}$; **$48\\text{V}$** para $>3\\text{ kWh/día}$.

3. **Potencia Pico del Campo Solar ($P_{\\text{pico}}$):**
   Calculada con el mes más desfavorable (Diciembre en Murcia: $\\text{HSP} = 2,80\\text{ h/día}$):
   $$P_{\\text{pico}} = \\frac{E_d}{\\text{HSP}_{\\text{invierno}} \\cdot \\eta_{\\text{global}}} = \\frac{1580}{2,80 \\cdot 0,75} \\approx 752\\text{ Wp} \\rightarrow 2\\text{ paneles de }450-500\\text{W}$$

4. **Regulador MPPT e Inversor-Cargador:**
   - **Regulador MPPT:** Corriente $I_{\\text{reg}} = \\frac{P_{\\text{pico}}}{V_{\\text{bat}}} \\cdot 1,20$.
   - **Inversor senoidal puro:** Potencia nominal igual a la suma de cargas simultáneas $\\times 1,25$, con capacidad de sobrecarga de arranque del $200\\%$ para motores de bombas y compresores de nevera."""
    },
    {
        "keywords": ["isolation fault", "fallo aislamiento", "fuga tierra inversor", "derivacion tierra placa"],
        "pregunta": "¿Cómo resolver el error 'Isolation Fault' (Fallo de aislamiento DC) en un inversor solar?",
        "respuesta": """### 🔴 Diagnóstico Rápido en Obra: 'Isolation Fault' / Fallo de Aislamiento DC

Es la avería número 1 en días de lluvia o con rocío matinal. El inversor comprueba con su relé interno que la resistencia de aislamiento entre polos activos (+ / -) y tierra sea $\\ge 1,0\\text{ M}\\Omega$ (UNE-EN 62109). Si detecta humedad o un cable pellizcado, se bloquea por seguridad.

**Truco de Maestro Instalador para localizarlo en 5 minutos sin desmontar paneles:**
1. Desconecta el seccionador DC y quita los conectores MC4 (+ y -) del inversor.
2. Pon el polímetro en **tensión continua (DC)**.
3. Mide la tensión entre el **polo positivo (+) y la toma de tierra (PE)**: anota $V_{(+)-PE}$.
4. Mide la tensión entre el **polo negativo (-) y la toma de tierra (PE)**: anota $V_{(-)-PE}$.
5. Comprueba que la suma $V_{(+)-PE} + |V_{(-)-PE}| = V_{oc,\\text{string}}$.
6. **Localización exacta:**
   $$\\text{Posición del panel derivado} = \\frac{V_{(+)-PE}}{V_{oc,\\text{módulo}}}$$
   *(Ejemplo: String de 8 paneles de $50\\text{V}$ cada uno ($V_{oc}=400\\text{V}$). Si mides $V_{(+)-PE} = 150\\text{ V}$, el fallo está exactamente en el conector o cable del **tercer módulo** contable desde el polo positivo: $150 / 50 = 3$).*
7. Vas directamente a ese panel y encontrarás el cable aprisionado bajo la grapa de aluminio de la estructura o un conector MC4 mal sellado lleno de agua."""
    },
    {
        "keywords": ["grid overvoltage", "253v", "tension de red", "inversor se apaga", "sobretension inversor"],
        "pregunta": "¿Por qué el inversor se apaga al mediodía con error 'Grid Overvoltage' (Tensión > 253V)?",
        "respuesta": """### ⚡ Avería: Inversor se apaga con sol radiante por 'Grid Overvoltage' ($V > 253\\text{ V}$)

1. **La Causa Técnica:**
   - La norma europea **UNE-EN 50549** obliga al inversor a desconectarse si la tensión en sus bornes supera los **$253\\text{ V}$** ($230\\text{ V} + 10\\%$).
   - Para poder inyectar energía a la vivienda o a la red, el inversor **debe elevar su propia tensión** por encima de la tensión de la red para vencer la resistencia del cable:
     $$V_{\\text{inversor}} = V_{\\text{red}} + \\Delta V_{\\text{cable}}$$
   - Si la línea de evacuación AC es muy larga o de sección insuficiente (ej. $2,5\\text{ mm}^2$ o $4\\text{ mm}^2$), la caída de tensión $\\Delta V$ será de $5\\text{ V}$ o $6\\text{ V}$. Si la red de la calle ya viene a $248\\text{ V}$, el inversor sube a $254\\text{ V}$ y **se bloquea automáticamente**.

2. **La Solución de Campo:**
   - **Aumentar la sección del cable AC:** La caída de tensión en la línea AC debe ser **$\\le 1,0\\%$ (máximo 2,3 V)**. Cambiar la línea de 4 mm² a 6 mm² o 10 mm² reduce la resistencia y la tensión en bornes del inversor baja inmediatamente de 253V.
   - **Comprobar apriete de bornes:** Un borne flojo en el PIA o diferencial añade resistencia de contacto que eleva la tensión localmente.
   - **Si la red en reposo ya supera los 250V:** Abrir reclamación a la distribuidora eléctrica (i-DE) para que regulen las tomas del centro de transformación (bajar el *tap* del transformador)."""
    },
    {
        "keywords": ["local comercial", "potencia local", "100 w/m2", "calcular local", "tienda", "oficina"],
        "pregunta": "¿Cómo se calcula la potencia y qué plantilla elegir para un local comercial o nave?",
        "respuesta": """### 🏢 Dimensionamiento de Potencia para Locales Comerciales - ITC-BT-10.3.3 e ITC-BT-28

Para cualquier local comercial, oficina o nave terciaria en la Región de Murcia, el REBT exige seguir esta metodología de cálculo:

1. **La Base Legal Mínima por Superficie (ITC-BT-10.3.3):**
   - Mínimo **$100\\text{ W/m}^2$** de superficie útil.
   - Suelo mínimo absoluto legal: **$3.450\\text{ W}$** (incluso si el local tiene solo $15\\text{ m}^2$).
   - *Ejemplo:* Local de $80\\text{ m}^2 \\rightarrow 80 \\times 100 = 8.000\\text{ W}$.

2. **Añadir Cargas Específicas (Climatización y Maquinaria):**
   - **Climatización / Bomba de calor:** Se suma con factor de simultaneidad $0,8$ a $1,0$ según el uso.
   - **Maquinaria / Hornos / Frío industrial:** Se suma la potencia nominal de los receptores.
   - $$P_{\\text{prevista}} = P_{\\text{base}} + 0,8 \\cdot P_{\\text{clima}} + 0,75 \\cdot P_{\\text{maquinaria}}$$

3. **¿Monofásica (230 V) o Trifásica (400 V)?:**
   - **Monofásica hasta $9.200\\text{ W}$ (IGA 40A) o máx $14.490\\text{ W}$ (IGA 63A):** Adecuada para pequeñas tiendas de ropa, oficinas, zapaterías o despachos profesionales sin maquinaria trifásica.
   - **Trifásica a 400 V (17.320 W en adelante):** Obligatoria si hay equipos de aire centralizado trifásicos, cámaras frigoríficas, hornos trifásicos o cuando la potencia prevista supera los $14.490\\text{ W}$.

4. **Trámite Legal ante Industria (DGEAIM Murcia):**
   - **Hasta $100\\text{ kW}$:** Se diseña y legaliza directamente mediante **Memoria Técnica de Diseño (MTD)** por el instalador autorizado.
   - **Más de $100\\text{ kW}$:** Exige **Proyecto de Ingeniero Colegiado** y Dirección Facultativa (ITC-BT-04 Tabla 3.1).
   - *¡Atención!* Si el local es de Pública Concurrencia (aforo $>50$ personas, bar, restaurante, clínica), exige además **inspección inicial por OCA**."""
    },
    {
        "keywords": ["publica concurrencia", "pública concurrencia", "lpc", "itc-bt-28", "oca", "cables as", "doble linea"],
        "pregunta": "¿Qué requisitos debe cumplir un Local de Pública Concurrencia (LPC) según la ITC-BT-28?",
        "respuesta": """### 🏛️ Requisitos Estrictos para Locales de Pública Concurrencia (LPC) - ITC-BT-28

Se consideran Locales de Pública Concurrencia:
- **Por actividad:** Bares, restaurantes, cafeterías, discotecas, cines, teatros, centros de culto, hospitales, clínicas, centros sanitarios y centros docentes/academias.
- **Por aforo:** Cualquier establecimiento comercial o de pública reunión cuya ocupación calculada supere las **50 personas** ($1\\text{ pers.}/0,8\\text{ m}^2$ en zona de público o $1\\text{ pers.}/2\\text{ m}^2$ en comercial).

**Prescripciones técnicas obligatorias que revisará el inspector:**
1. **Cables de Alta Seguridad (AS) obligatorios en TODA la instalación:**
   - Conductores no propagadores del incendio y de reducida emisión de humos y opacidad (cables libres de halógenos tipo **H07Z1-K** o **RZ1-K 0.6/1kV** clase $C_{ca}\\text{-s1b,d1,a1}$). Queda totalmente prohibido el PVC.
2. **Doble Línea de Alumbrado General:**
   - En todas las dependencias destinadas al público, el alumbrado debe repartirse en al menos **dos circuitos independientes** alternados (Línea A y Línea B). Si dispara un PIA, nunca debe quedarse la sala en penumbra total.
3. **Alumbrado de Emergencia y Señalización:**
   - Obligatorio en cuadros eléctricos (mínimo **$5\\text{ lux}$**), salidas y puertas de evacuación, y a lo largo de los recorridos y pasillos (mínimo **$1\\text{ lux}$**). Autonomía mínima de **1 hora**.
4. **Corte Omnipolar:**
   - Todos los dispositivos de mando y protección (IGA, diferenciales, magnetotérmicos) deben cortar simultáneamente fase y neutro.
5. **Enclavamiento de Gas en Campanas (Hostelería):**
   - En cocinas de bares/restaurantes con gas, la campana extractora debe tener enclavamiento eléctrico que corte la electroválvula de gas si el extractor está apagado o falla el tiro.
6. **Inspección Inicial OBLIGATORIA por OCA:**
   - Antes de dar de alta el boletín y antes de que la distribuidora enganche el contador, un Organismo de Control Autorizado (OCA) debe inspeccionar y emitir acta de inspección favorable. Además, tienen inspección periódica obligatoria cada 5 años."""
    },
    {
        "keywords": ["potencias", "vivienda", "electrificacion", "aerotermia", "grados electrificacion", "14490", "11500", "9200", "chalet trifasica", "itc-bt-25"],
        "pregunta": "¿Qué potencias normalizadas de electrificación existen para viviendas y cuál elegir?",
        "respuesta": """### 🏡 Potencias de Electrificación en Viviendas - ITC-BT-10 e ITC-BT-25

En la Región de Murcia y bajo el REBT se manejan estas opciones clave según el grado de equipamiento:

1. **Electrificación Básica ($5.750\\text{ W}$ - Monofásica 230 V - IGA 25 A):**
   - Para viviendas de hasta $160\\text{ m}^2$ sin aire centralizado ni calefacción eléctrica.
   - Dotación de 5 circuitos básicos: C1 (Alumbrado), C2 (Tomas uso general), C3 (Cocina/Horno), C4 (Lavadora/Termo/Lavavajillas), C5 (Baños/Auxiliares).
   - Derivación individual mínima: $10\\text{ mm}^2\\text{ Cu}$ en tubo M32.

2. **Electrificación Elevada con Clima ($9.200\\text{ W}$ - Monofásica 230 V - IGA 40 A):**
   - **El estándar de referencia en Murcia** para pisos y adosados con aire acondicionado por conductos (C9) y secadora (C10).
   - Obligatorio si la vivienda supera $160\\text{ m}^2$ o tiene previsión de clima/calefacción.
   - Derivación individual oficial Murcia: **$16\\text{ mm}^2\\text{ Cu}$ en tubo M40**. Al tener más de 5 circuitos, exige al menos 2 diferenciales de 30 mA.

3. **Electrificación Elevada con Aerotermia ($11.500\\text{ W}$ - Monofásica 230 V - IGA 50 A):**
   - Para viviendas modernas con bomba de calor aerotérmica para ACS y suelo radiante/refrescante.
   - Exige circuito dedicado para la bomba de calor protegido con **diferencial Tipo A Superinmunizado** para evitar disparos por los variadores de frecuencia.

4. **Máxima Electrificación Monofásica ($14.490\\text{ W}$ - Monofásica 230 V - IGA 63 A):**
   - Es el **tope legal monofásico** admitido por las distribuidoras en España ($63\\text{ A} \\times 230\\text{ V}$).
   - Para unifamiliares con gran demanda (inducción potente, climatización zonificada, domótica) que no quieren contratar suministro trifásico.
   - Derivación individual reforzada a **$25\\text{ mm}^2\\text{ Cu}$ en tubo M50**.

5. **Chalet Unifamiliar Trifásica ($17.320\\text{ W}$ - Trifásica 400 V - IGA 25 A Tri):**
   - Para chalets en huerta o parcelas con piscina, bomba de pozo, riego por goteo y aire acondicionado trifásico.
   - Equilibra el consumo entre las 3 fases y reduce la sección necesaria de los cables en parcelas grandes."""
    },
    {
        "keywords": ["irve garaje comunitario", "esquema 2", "wallbox comunidad", "cargador garaje", "itc-bt-52"],
        "pregunta": "¿Cómo se legaliza un punto de recarga IRVE en garaje comunitario de Murcia según ITC-BT-52?",
        "respuesta": """### 🚗 Instalación de Puntos de Recarga en Garajes Comunitarios - ITC-BT-52

Para instalar un punto de recarga en una plaza de aparcamiento comunitaria en un edificio de viviendas en Murcia:

1. **Esquema de Instalación Habitual (Esquema 2 de ITC-BT-52):**
   - Es el más utilizado: Se instala un nuevo contador principal en la **centralización común de contadores** del edificio.
   - Desde ese contador sale una derivación individual exclusiva que discurre por zonas comunes del aparcamiento hasta el punto de recarga (Wallbox).
   - Alternativamente, si el garaje está en el mismo edificio que la vivienda y la derivación lo permite, se puede alimentar desde el propio cuadro de la vivienda (Esquema 1 o derivación interior con circuito C13).

2. **Requisitos Técnicos Indispensables a pie de obra:**
   - **Cables Libres de Halógenos (AS):** Obligatoriamente cables de no propagación de llama y reducida emisión de humos clase $C_{ca}\\text{-s1b,d1,a1}$ (ej. RZ1-K 0.6/1kV) al cruzar zonas comunes de aparcamiento.
   - **Tubo Protector:** Resistencia al impacto **IK08** (mínimo M32).
   - **Protección Diferencial (IEC 62955):** Diferencial 2P 40A / 30mA **Clase A** que disponga de detección de fuga en corriente continua de $6\\text{ mA}$ DC (para proteger la red frente a los convertidores del coche), o bien diferencial Clase B.
   - **Protección contra Sobretensiones:** Protector combinado de sobretensiones transitorias y permanentes con bobina de disparo asociada al IGA.

3. **Modulación de Potencia (Sensor SPL):**
   - Se recomienda encarecidamente instalar una pinza amperimétrica (CT) que module dinámicamente la corriente de carga del vehículo, evitando que supere la potencia contratada.

4. **Trámite Legal y Comunidad de Vecinos:**
   - **No requiere autorización de la comunidad:** Según el artículo 17.5 de la Ley de Propiedad Horizontal (LPH), solo es necesario remitir una **comunicación previa por escrito al presidente o administrador** de la comunidad.
   - Se legaliza mediante Memoria Técnica de Diseño (MTD) por el instalador habilitado ante la DGEAIM de Murcia (hasta 50 kW en interior sin proyecto)."""
    },
    {
        "keywords": ["bar restaurante potencia", "dimensionar bar", "potencia hosteleria", "legalizar bar murcia", "cuadro bar"],
        "pregunta": "¿Cómo dimensionar la potencia y qué exige la normativa para legalizar un bar o restaurante en Murcia?",
        "respuesta": """### 🍽️ Dimensionamiento y Legalización de Bares y Restaurantes en Murcia

La hostelería es una de las instalaciones más habituales del instalador eléctrico en la Región de Murcia y exige máxima rigurosidad reglamentaria:

1. **Potencia Estándar y Suministro:**
   - El estándar habitual para un bar/cafetería mediano en Murcia es **$27.710\\text{ W}$ a $400\\text{ V}$ Trifásico (IGA 40 A)**.
   - Se calcula sumando la potencia base del local ($100\\text{ W/m}^2$, mínimo legal $3.450\\text{ W}$), la climatización del salón (8 a 12 kW), la cocina industrial (planchas, freidoras, lavavajillas de cúpula) y los botelleros y cámaras frigoríficas.

2. **Requisitos Críticos del REBT (ITC-BT-28 Pública Concurrencia):**
   - **Cables AS en todo el local:** Obligatoriamente libres de halógenos $C_{ca}\\text{-s1b,d1,a1}$ (H07Z1-K o RZ1-K).
   - **Doble circuito de iluminación en salón:** Los focos y tiras LED del salón comedor deben repartirse al 50% entre dos PIAs independientes (Línea A y Línea B).
   - **Alumbrado de emergencia:** Bloques autónomos en puertas, vías de evacuación y **mínimo 5 lux frente al cuadro eléctrico CGMP**.
   - **Enclavamiento de campana con electroválvula de gas:** La electroválvula de corte de gas debe estar enclavada eléctricamente con el extractor de humos. Si la campana no funciona o se pulsa la seta de corte de cocina, el gas debe quedar cortado al instante.
   - **Línea prioritaria de refrigeración:** Conectar las cámaras frigoríficas y botelleros a un diferencial independiente superinmunizado clase A para evitar pérdidas de género por disparos intempestivos.

3. **Trámite Legal y Puesta en Servicio en Murcia:**
   - **MTD vs Proyecto:** Hasta **$100\\text{ kW}$** se tramita mediante **Memoria Técnica de Diseño (MTD)** emitida por el Instalador Autorizado.
   - **Inspección Inicial por OCA OBLIGATORIA:** Es un requisito legal indispensable previo a que Iberdrola / i-DE enganche el contador definitivo. El instalador debe coordinar la inspección con el organismo de control."""
    }
]

import re
import unicodedata

def _normalizar_texto(texto: str) -> str:
    """Elimina tildes y caracteres diacríticos para búsqueda semántica insensible a acentos."""
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').lower()

def buscar_respuesta_offline(consulta: str) -> str:
    """Busca la mejor coincidencia técnica en la base de conocimiento offline REBT."""
    c_norm = _normalizar_texto(consulta)
    mejor_match = None
    max_puntos = 0
    
    for item in BASE_CONOCIMIENTO_OFFLINE:
        puntos = 0
        for kw in item["keywords"]:
            kw_norm = _normalizar_texto(kw)
            # Buscar coincidencia de palabra completa o frase exacta
            if " " in kw_norm:
                if kw_norm in c_norm:
                    puntos += 3  # Frase completa tiene mayor peso
            else:
                if re.search(r'\b' + re.escape(kw_norm) + r'\b', c_norm):
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
    st.markdown("##### ⚡ Consultas Rápidas de Taller, Obra y Solar Fotovoltaica:")
    pills = [
        "⚖️ ¿Cuándo necesito Proyecto de Ingeniero en vez de MTD?",
        "☀️ ¿Cuál es la diferencia entre una instalación solar a red y aislada?",
        "🔋 ¿Cómo se dimensiona una instalación fotovoltaica aislada con baterías?",
        "🔴 ¿Cómo resolver el error 'Isolation Fault' (Fallo de aislamiento DC)?",
        "⚡ ¿Por qué el inversor se apaga por 'Grid Overvoltage' (Tensión > 253V)?",
        "🛡️ ¿Cuántos circuitos puedo poner bajo un diferencial de 30mA?",
        "🔌 ¿Cómo se calcula la sección de una Derivación Individual?",
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
