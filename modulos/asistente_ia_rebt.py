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
Eres el Consultor Senior de Ingeniería (Eléctrica y Telecomunicaciones) y Maestro Instalador Habilitado de Bolimur.
Combinas con máxima excelencia los siguientes perfiles:

1. Vista de Ingeniero Eléctrico e Ingeniero de Telecomunicación (Colegiado COIT / COITT):
   - Riguroso en el Reglamento Electrotécnico para Baja Tensión (REBT 2002 - RD 842/2002) y sus 52 ITCs (ITC-BT-01 a ITC-BT-52).
   - Experto en Infraestructuras Comunes de Telecomunicaciones (ICT-2 - Real Decreto 346/2011 y Orden ITC/1644/2011).
   - Normativa de Generación y Autoconsumo (ITC-BT-40, Real Decreto 244/2019, UNE-EN 62548, UNE-EN 50549-1).
   - Normas europeas de cableado estructurado y compatibilidad electromagnética (UNE-EN 50173, UNE-EN 50174-2 sobre separación mínima de 20 cm entre cables de energía y datos, IEC 60794 para fibra monomodo G.657A2, y DVB-T2 / DVB-S2 para RTV).
   - Criterios de tramitación técnica y administrativa ante la Dirección General de Energía y Actividad Industrial y Minera (DGEAIM Murcia) y ante la Secretaría de Estado de Telecomunicaciones e Infraestructuras Digitales (SETSI).

2. Maestro Instalador y Especialista de Telecomunicaciones a Pie de Obra (25 años en calle):
   A) TELECOMUNICACIONES EN VIVIENDAS, LOCALES Y COMUNIDADES (ICT-2):
      - RTV (TDT y Satélite FI): Captación en mástil con antenas UHF preparadas para el 2º Dividendo Digital con filtro de corte LTE 700 MHz (canales 21 al 48, corte a 694 MHz para evitar saturación 5G). Parábolas offset orientadas a Astra 19.2ºE o Hispasat 30ºW con LNB universal (conmutación 13/18V y tono 22 kHz). Centrales amplificadoras programables digitales (Televes Avant X, Ikusi ONE) con CAG. Niveles reglamentarios obligatorios en toma de usuario:
        * TDT (DVB-T / DVB-T2 COFDM): 45 dBµV a 70 dBµV (MER >= 21 dB, BER < 1e-4).
        * Satélite FI (DVB-S / DVB-S2): 47 dBµV a 77 dBµV (C/N > 11 dB).
        * Radio FM: 40 a 70 dBµV. Radio DAB: 35 a 70 dBµV.
        * Distribución con cable coaxial clase A+ (Televes T-100plus), atenuación <= 18 dB/100m en UHF y <= 30 dB/100m en FI.
      - Fibra Óptica FTTH: Fibra monomodo ITU-T G.657.A2 (baja sensibilidad a curvatura, R_min = 7.5 mm), conectores SC/APC verde (pérdidas de retorno > 60 dB). Fusionadora de fibra óptica por arco voltaico (<0.05 dB por empalme). PAU óptico en RTR de vivienda con 2 fibras monomodo. Atenuación máxima permitida de la red interior de usuario: <= 2.0 dB a 1310, 1490 y 1550 nm (medida con emisor láser y medidor de potencia óptica o reflectómetro OTDR).
      - Redes de Datos y Cableado Estructurado (Cat6, Cat6A, Cat7):
        * Viviendas: Mínimo Cat6 UTP (250 MHz, 1 Gbps hasta 100m).
        * Locales y Oficinas: Cat6A F/UTP o U/FTP (500 MHz, 10 Gbps a 100m, blindaje contra diafonía exógena).
        * Conectorización en rosetas RJ45 y patch panels bajo el estándar uniforme TIA/EIA-568-B.
        * Alimentación PoE (802.3af 15.4W, 802.3at 30W PoE+, 802.3bt 60W/90W PoE++) para puntos de acceso Wi-Fi 6/7, cámaras IP y pantallas.
        * Racks de 19 pulgadas murales (6U-12U) o de suelo (24U-42U), organizadores de cables, latiguillos y puesta a tierra obligatoria del chasis con cable verde/amarillo de 16 mm² Cu conectado a la borna principal de tierra del edificio.
        * Separación crítica con cables de 230V/400V: Según norma UNE-EN 50174-2, mantener al menos 20 cm de distancia entre cables de fuerza y datos sin apantallar, o 5 cm si hay tabique metálico continuo conectado a tierra. ¡JAMÁS compartir tubo o corrugado entre cables eléctricos de 230V y cables de telecomunicación UTP/coaxial (prohibición terminante REBT e ICT-2)!
      - Registros y Recintos ICT:
        * En edificio: RITS (superior en cubierta), RITI (inferior), RITU (único para <= 10 PAUs o 3 plantas).
        * En vivienda / local: Registro de Terminación de Red (RTR) en la entrada, dimensiones mínimas 500x600x80 mm (o 2 de 500x300x80 contiguos), equipado obligatoriamente con 2 tomas schuko 16A/230V con tierra para alimentar router/ONT y borna de equipotencialidad (Cu >= 6 mm²). Dotación mínima por estancias: salón (2 tomas dobles RJ45 + 2 RTV + FO), dormitorio ppal (1 doble RJ45 + 1 RTV), otros dormitorios y cocina (1 RJ45 + 1 RTV).
      - Videoporteros y Control de Acceso:
        * Sistemas digitales 2 hilos no polarizados (Fermax DUOX PLUS, Tegui 2 Hilos): Ideales para renovaciones y reformas sin cambiar canalizaciones preexistentes, transmisión digital de audio/vídeo hasta 300 metros.
        * Sistemas IP / SIP (Fermax MEET, Dahua, Hikvision): Cableado Cat6 PoE con conexión a red local y desvío de llamada a móviles vía app.
        * Abrepuertas: 12V AC o DC con protección varistor o diodo para amortiguar picos inductivos que averíen la placa electrónica.
      - Tramitación Legal SETSI vs Proyecto ICT:
        * Edificios comunitarios (> 1 vivienda o locales): Exigen Proyecto de Telecomunicaciones visado por Ingeniero de Telecomunicación + Dirección de Obra + Certificado Fin de Obra + Protocolo de Pruebas visado.
        * Viviendas unifamiliares / locales independientes sin comunidad: Se tramitan con Boletín de Telecomunicaciones emitido por Instalador Autorizado registrado en la SETSI (Tipos A, C o F).

   B) BAJA TENSIÓN, SOLAR FOTOVOLTAICA E IRVE (REBT):
      - Criterios de caída de tensión (1.5% DI, 3% alumbrado, 5% fuerza).
      - Límite de 5 circuitos por diferencial de 30 mA (ITC-BT-25).
      - Sobretensiones permanentes y transitorias obligatorias en Murcia (ITC-BT-23).
      - Autoconsumo solar conectado a red (RD 244/2019) y aisladas off-grid con baterías (LiFePO4 DOD 90% vs Gel 50%, HSP Diciembre Murcia 2.8 h/día).
      - Resolución de averías: 'Isolation Fault' (localización por tensión DC a tierra) y 'Grid Overvoltage' (evitar caídas > 1% en AC).
      - Recarga de Vehículo Eléctrico IRVE (ITC-BT-52, Esquema 2, cables AS Cca, diferencial Clase A con 6mA DC según IEC 62955).
      - Locales de Pública Concurrencia (ITC-BT-28: cables libres de halógenos, doble línea de luz, emergencias, OCA obligatoria).

3. Asesor Experto en Elección de Plantillas e Instalaciones en la Región de Murcia:
   Conoces a la perfección el catálogo oficial de plantillas técnicas de Bolimur y sabes orientar al instalador:
   - Viviendas (ITC-BT-10/25): Básica 5.75 kW (sin clima central), Elevada Clima 9.2 kW (modelo oficial DGEAIM Murcia con IGA 40A y DI 16 mm² Cu), Elevada Aerotermia 11.5 kW (IGA 50A con diferencial dedicado superinmunizado), Máxima Monofásica 14.49 kW (límite 63A a 230V con DI 25 mm² Cu), Chalet Trifásico 17.32 kW (400V para parcelas con piscina y riego).
   - Vehículo Eléctrico IRVE (ITC-BT-52): Garaje comunitario Esquema 2 (7.36 kW, cables libres de halógenos AS, tubo IK08, diferencial clase A 6mA DC), IRVE Trifásico 22 kW, y Vivienda con IRVE integrado (circuito C13 con modulación dinámica de carga SPL).
   - Autoconsumo Fotovoltaico (ITC-BT-40 / RD 244/2019): Solar 5 kW e Híbrido Vivienda + Solar + IRVE.
   - Locales Comerciales Ordinarios: Monofásico 9.2 kW y Trifásico 17.32 kW (cálculo de 100 W/m² según ITC-BT-10.3.3 con mínimo de 3.450 W).
   - Locales de Pública Concurrencia (LPC - ITC-BT-28): Bar/Restaurante 27.71 kW (IGA 40A 400V con enclavamiento de gas en campana), Academia/Clínica 17.32 kW (>50 personas), Gimnasio con duchas 20.78 kW.
   - Cuadros de Obra (ITC-BT-33): 15 kW con tomas CETAC y pulsador exterior de parada de emergencia.
   - Límites de tramitación: Hasta 100 kW se tramita por MTD del instalador; más de 100 kW exige Proyecto Técnico visado por Ingeniero.

Tus principios de respuesta:
- Cita siempre la norma técnica y legal exacta (ej. RD 346/2011 ICT-2, ITC-BT correspondiente, UNE-EN 50174-2, etc.).
- Aporta tanto la fórmula y el artículo legal como el consejo práctico de taller o montaje para que el instalador resuelva la obra sin incidencias.
- Sé claro, directo y estructurado (utiliza viñetas, tablas markdown y fórmulas KaTeX cuando haya cálculos técnicos o económicos).
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
    },
    {
        "keywords": ["ict", "ict-2", "telecomunicaciones", "rd 346/2011", "orden itc/1644/2011", "reglamento telecomunicaciones", "setsi"],
        "pregunta": "¿Qué es la ICT-2 (RD 346/2011) y qué redes y recintos comprende en edificios y viviendas?",
        "respuesta": """### 📡 Infraestructuras Comunes de Telecomunicaciones (ICT-2) - RD 346/2011 y Orden ITC/1644/2011

La **ICT-2** regula las instalaciones de telecomunicación para garantizar el acceso ultrarrápido a los servicios de telecomunicación en edificios y viviendas. Comprende 3 redes principales y recintos normalizados:

1. **Redes Técnicas Obligatorias:**
   - **RTV (Radiodifusión Sonora y Televisión):** TDT terrestre (canales 21 al 48, con filtro LTE 700 5G a 694 MHz) y Satélite FI (950-2150 MHz).
   - **TBA (Telecomunicaciones de Banda Ancha):** Red de fibra óptica (FTTH) con 2 fibras monomodo por vivienda y red de par trenzado (Cat6).
   - **Servicios de Hogar Digital y Telefonía:** Tomas RJ45 y videoportero digital.

2. **Recintos de Telecomunicación en el Edificio:**
   - **RITS (Recinto Superior):** En azotea para cabeceras RTV y enlaces de radio.
   - **RITI (Recinto Inferior):** En planta baja o sótano para acometidas de operadores (fibra óptica, pares, coaxial).
   - **RITU (Recinto Único):** Permitido en edificios pequeños de hasta 10 viviendas o 3 plantas.

3. **En la Vivienda / Local:**
   - **RTR (Registro de Terminación de Red):** Registro central empotrado en la entrada de la vivienda ($500 \\times 600 \\times 80\\text{ mm}$), con 2 tomas de corriente Schuko con tierra y borna equipotencial de puesta a tierra."""
    },
    {
        "keywords": ["proyecto telecomunicacion", "proyecto ict", "boletin telecomunicaciones", "boletin ict", "setsi", "coit", "coitt", "tipo a", "tipo f", "cuando proyecto telecomunicaciones"],
        "pregunta": "¿Cuándo se necesita Proyecto de Ingeniero de Telecomunicación vs Boletín Oficial de Telecomunicaciones?",
        "respuesta": """### ⚖️ Proyecto de Ingeniero de Telecomunicación vs Boletín de Instalador (SETSI)

El régimen legal de telecomunicaciones (RD 346/2011 y Ley General de Telecomunicaciones) distingue claramente:

1. **Cuándo es OBLIGATORIO Proyecto Técnico de Telecomunicaciones:**
   - **Edificios en régimen de propiedad horizontal:** Con más de **1 vivienda o local comercial**. Requiere:
     * **Proyecto Técnico** visado por Ingeniero de Telecomunicación o Ingeniero Técnico (COIT / COITT).
     * **Acta de Replanteo** inicial.
     * **Dirección de Obra** y **Certificado de Fin de Obra** visado.
     * **Protocolo de Pruebas** con medidas reales de señal (TDT, SAT, atenuación fibra óptica y datos).

2. **Cuándo basta con Boletín de Instalador de Telecomunicaciones:**
   - **Viviendas unifamiliares aisladas** o locales independientes que no formen parte de una comunidad en propiedad horizontal.
   - **Reformas o adecuaciones puntuales** dentro de una vivienda o local donde no se altere la infraestructura común del edificio.
   - Debe ser emitido por un Instalador Autorizado registrado en la **SETSI (Secretaría de Estado de Telecomunicaciones e Infraestructuras Digitales)**:
     * **Tipo A:** Infraestructuras en edificios (coaxial, pares, fibra).
     * **Tipo C:** Instalaciones audiovisuales (antenas RTV, megafonía, CCTV).
     * **Tipo F:** Redes de nueva generación (fibra óptica y redes ultrarrápidas completas ICT-2)."""
    },
    {
        "keywords": ["tdt", "satelite", "rtv", "nivel de senal", "dbuv", "mer", "ber", "lte 700", "5g", "antena tv", "segundo dividendo digital", "amplificador televes"],
        "pregunta": "¿Cuáles son los niveles de señal reglamentarios en toma para TDT y Satélite según la ICT-2 y cómo filtrar el 5G?",
        "respuesta": """### 📺 Niveles de Señal Reglamentarios RTV en Toma de Usuario - RD 346/2011 (Anexo I)

El instalador debe verificar con un medidor de campo homologado (Televes MosaiQ, Promax HD Ranger o similar) los siguientes valores en **cada toma de usuario**:

1. **Televisión Digital Terrestre (TDT - DVB-T / DVB-T2 COFDM):**
   - **Nivel de Potencia:** Entre **$45\\text{ dB}\\mu\\text{V}$ y $70\\text{ dB}\\mu\\text{V}$** (óptimo de trabajo en toma: $52 - 62\\text{ dB}\\mu\\text{V}$).
   - **MER (Tasa de Error de Modulación):** Mínimo legal $\\ge 21\\text{ dB}$ (en la práctica profesional buscar siempre **$\\ge 26\\text{ dB}$** para margen de guarda).
   - **BER (Bit Error Rate):** $\\text{CBER} < 1 \\times 10^{-4}$ y $\\text{VBER} < 1 \\times 10^{-7}$ (señal cuasi-libre de errores).

2. **Satélite FI (DVB-S / DVB-S2 QPSK/8PSK - 950 a 2.150 MHz):**
   - **Nivel de Potencia:** Entre **$47\\text{ dB}\\mu\\text{V}$ y $77\\text{ dB}\\mu\\text{V}$**.
   - **C/N (Relación Portadora/Ruido):** $\\ge 11\\text{ dB}$.

3. **Radio:**
   - **FM (87.5 - 108 MHz):** $40\\text{ dB}\\mu\\text{V}$ a $70\\text{ dB}\\mu\\text{V}$.
   - **DAB (Radio Digital):** $35\\text{ dB}\\mu\\text{V}$ a $70\\text{ dB}\\mu\\text{V}$.

4. **Filtro LTE 700 MHz (5G / Segundo Dividendo Digital):**
   - Las bandas de telefonía móvil 5G ocupan desde 694 MHz hacia arriba (antiguos canales UHF 49 al 69).
   - **Solución en obra:** Utilizar antena UHF con filtro SAW incorporado cortando en el **canal 48 (694 MHz)** o intercalar un filtro de rechazo LTE700 en mástil. Si la señal 5G entra al amplificador, satura los transistores y pixela los canales de TDT aunque la antena marque señal alta."""
    },
    {
        "keywords": ["fibra optica", "ftth", "g657a2", "sc/apc", "fusionadora", "atenuacion fibra", "pau fibra", "2 db", "monomodo", "red interior fibra"],
        "pregunta": "¿Qué exigencias técnicas tiene la instalación de fibra óptica FTTH (ICT-2) y cómo medir la atenuación?",
        "respuesta": """### 💡 Fibra Óptica FTTH en Viviendas y Locales - RD 346/2011

1. **Tipo de Fibra Obligatoria:**
   - Fibra **Monomodo ITU-T G.657.A2** (fibra insensible a curvaturas con radio mínimo admisible de **$7,5\\text{ mm}$**). Es la única que permite giros cerrados en cajas de mecanismos y tubos corrugados de 20-25 mm sin romperse ni sufrir pérdidas por macrocurvatura.

2. **Conectores y Pulido:**
   - Conectores **SC/APC** (cuerpo verde, pulido angular a 8º). El corte en ángulo evita que la luz reflejada retorne al láser del transmisor, garantizando pérdidas de retorno (Return Loss) $> 60\\text{ dB}$.

3. **Empalmes y Fusiones:**
   - Realizados con **fusionadora por arco voltaico**.
   - Pérdida máxima por fusión: **$< 0,05\\text{ dB}$** por empalme.

4. **Punto de Acceso al Usuario (PAU) y Dotación:**
   - La ICT-2 exige tender **2 fibras monomodo** desde el RITI hasta el PAU óptico del RTR de cada vivienda. Una queda en servicio para la operadora y la otra en reserva fría.

5. **Límite de Atenuación de la Red Interior de Usuario:**
   - La atenuación óptica total de la instalación interior (desde el PAU hasta la toma de usuario más lejana) no debe superar **$2,0\\text{ dB}$** medidos a las longitudes de onda de $1.310\\text{ nm}$, $1.490\\text{ nm}$ y $1.550\\text{ nm}$ con fuente de luz calibrada y medidor de potencia (Power Meter)."""
    },
    {
        "keywords": ["cable red", "cat6", "cat6a", "utp", "ftp", "rj45", "t568b", "rack", "poe", "red local", "cableado estructurado", "tomas datos"],
        "pregunta": "¿Cómo instalar y certificar cableado estructurado Cat6 / Cat6A y racks en viviendas, locales y oficinas?",
        "respuesta": """### 🌐 Cableado Estructurado y Redes de Datos - UNE-EN 50173 e ICT-2

1. **Categoría según el Ámbito:**
   - **Viviendas (ICT-2):** Mínimo **Categoría 6 UTP** (frecuencia hasta $250\\text{ MHz}$, velocidad 1 Gbps hasta $100\\text{ m}$).
   - **Locales Comerciales, Oficinas y Despachos:** **Categoría 6A F/UTP o U/FTP** (frecuencia hasta $500\\text{ MHz}$, velocidad garantizada **$10\\text{ Gbps}$ hasta $100\\text{ m}$** con apantallamiento contra diafonía exógena o Alien Crosstalk).

2. **Patrón de Conectorización RJ45:**
   - Usar siempre el estándar **TIA/EIA-568-B** de forma idéntica en ambos extremos (roseta y patch panel):
     1. Blanco/Naranja | 2. Naranja
     3. Blanco/Verde | 4. Azul
     5. Blanco/Azul | 6. Verde
     7. Blanco/Marrón | 8. Marrón
   - *Truco de montaje:* Destrenzar el par un máximo de **$13\\text{ mm}$** antes de la crimpadora para no degradar el parámetro NEXT (diafonía cercana).

3. **Alimentación PoE (Power over Ethernet):**
   - **PoE (802.3af):** Hasta $15,4\\text{ W}$ (teléfonos IP, sensores).
   - **PoE+ (802.3at):** Hasta $30\\text{ W}$ (puntos de acceso Wi-Fi 6, videoporteros IP).
   - **PoE++ (802.3bt):** Hasta $60\\text{ W}$ (Tipo 3) o $90\\text{ W}$ (Tipo 4) para cámaras PTZ con calefactor o pantallas táctiles.

4. **Armarios Rack de 19 Pulgadas:**
   - Murales de $6\\text{U}$ a $12\\text{U}$ para viviendas unifamiliares y pequeños comercios; suelo de $24\\text{U}$ a $42\\text{U}$ para oficinas.
   - **Puesta a tierra obligatoria:** Conectar el bastidor metálico del rack a la borna principal de tierra con conductor de cobre verde/amarillo de **$\\ge 16\\text{ mm}^2$**."""
    },
    {
        "keywords": ["separacion cables", "cables datos y 230v", "interferencias", "une-en 50174-2", "tubo compartido", "distancia baja tension telecomunicaciones"],
        "pregunta": "¿Qué separación debe mantenerse entre conductores de electricidad de 230V y cables de telecomunicaciones?",
        "respuesta": """### ⚡ Distancias de Separación entre Electricidad (230V/400V) y Telecomunicaciones - UNE-EN 50174-2 y REBT

La convivencia de cables de energía y cables de datos/coaxial está regulada estrictamente para evitar ruidos electromagnéticos e inducciones peligrosas:

1. **Prohibición Taxativa de Tubo Compartido:**
   - **¡JAMÁS deben pasar cables de 230V/400V y cables de telecomunicaciones (UTP, fibra, coaxial) por el mismo tubo corrugado o canalización sin tabique!** (Infracción grave según REBT ITC-BT-19/21 y RD 346/2011).

2. **Distancias Mínimas de Separación Física (UNE-EN 50174-2):**
   - **Cables sin apantallar (UTP Cat6):** Separación mínima de **$200\\text{ mm}$ (20 cm)** en recorridos paralelos de más de 10 metros.
   - **Con tabique separador metálico puesto a tierra:** La distancia puede reducirse a **$50\\text{ mm}$ (5 cm)**.
   - **Cables apantallados (FTP / STP Cat6A):** Separación mínima de **$50\\text{ mm}$** sin tabique.

3. **Cruces de Canalizaciones:**
   - Si una canalización eléctrica debe cruzarse con una de telecomunicaciones, el cruce debe realizarse preferentemente en **ángulo de $90^\\circ$** para minimizar el acoplamiento magnético."""
    },
    {
        "keywords": ["rtr", "registro terminacion red", "dimensiones rtr", "tomas vivienda", "pau", "cuantas tomas telecomunicaciones", "cuadro telecomunicaciones"],
        "pregunta": "¿Qué dimensiones y tomas debe tener el Registro de Terminación de Red (RTR) y cuántas tomas tocan por habitación?",
        "respuesta": """### 🏢 Registro de Terminación de Red (RTR) y Dotación Mínima de Tomas - ICT-2 RD 346/2011

1. **Dimensiones Reglamentarias del RTR en Vivienda:**
   - Registro único: Mínimo **$500 \\times 600 \\times 80\\text{ mm}$** (ancho x alto x profundidad).
   - O dos registros contiguos de **$500 \\times 300 \\times 80\\text{ mm}$** comunicados por 2 tubos de $32\\text{ mm}$.
   - Ubicación: En el interior de la vivienda, preferiblemente junto al cuadro eléctrico CGMP (a menos de $50\\text{ cm}$).

2. **Equipamiento Interior Obligatorio del RTR:**
   - **2 tomas de corriente tipo Schuko $16\\text{ A} / 230\\text{ V}$ con toma de tierra**, conectadas al circuito eléctrico de uso general (C2) para alimentar router, ONT y switch.
   - **Borna de equipotencialidad de puesta a tierra** conectada a la tierra de la vivienda con cable de cobre $\\ge 6\\text{ mm}^2$.
   - Espacio reservado para los PAUs: PAU coaxial RTV, PAU fibra óptica FTTH y multiplexor pasivo RJ45.

3. **Tomas Mínimas Reglamentarias por Estancia (RD 346/2011 Anexo III):**
   - **Salón / Estancia Principal:** Mínimo **2 tomas dobles RJ45 Cat6** + **2 tomas RTV** + toma de fibra óptica o previsión.
   - **Dormitorio Principal:** Mínimo **1 toma doble RJ45 Cat6** + **1 toma RTV**.
   - **Resto de Dormitorios:** Mínimo **1 toma RJ45 Cat6** + **1 toma RTV**.
   - **Cocina:** Mínimo **1 toma RJ45 Cat6** + **1 toma RTV**.
   - **Junto al RTR:** 1 toma RJ45 de datos adicional para configuración del instalador."""
    },
    {
        "keywords": ["videoportero", "portero automatico", "2 hilos", "fermax duox", "tegui", "videoportero ip", "abrepuertas", "instalacion videoportero"],
        "pregunta": "¿Cómo elegir e instalar un videoportero de 2 hilos (Fermax DUOX / Tegui) frente a uno IP / SIP?",
        "respuesta": """### 🚪 Videoporteros y Control de Acceso: 2 Hilos Digital vs Sistema IP / SIP

1. **Sistema Digital 2 Hilos No Polarizados (ej. Fermax DUOX PLUS, Tegui 2 Hilos):**
   - **Cuándo elegirlo:** En **reformas y sustitución de porteros antiguos (4+N)** o unifamiliares donde ya existen tubos con 2 cables.
   - **Ventajas:** Funciona sobre cualquier par de hilos ($0,5\\text{ mm}^2$ a $1\\text{ mm}^2$ o cable UTP), digitaliza audio, vídeo HD y datos sin polaridad (no importa cuál es polo 1 o polo 2). Alcance de hasta $300\\text{ metros}$.
   - **Montaje:** Se alimenta con fuente central a carril DIN (18V - 24V DC). En cada vivienda se coloca el monitor y se programa con el switch DIP o menú de display con el número de vivienda asignado.

2. **Sistema IP / SIP (ej. Fermax MEET, Dahua, Hikvision, Akuvox):**
   - **Cuándo elegirlo:** En **obra nueva, chalets modernos, oficinas y naves comerciales**.
   - **Ventajas:** Conexión directa a la red local Ethernet con cable **Cat6 PoE (802.3af)**. Permite desvío instantáneo de llamada al smartphone del cliente sin costes mensuales, integración con cámaras CCTV y apertura remota desde cualquier lugar del mundo.

3. **Consejo Profesional para el Abrepuertas:**
   - La cerradura eléctrica de 12V genera **picos inductivos de alta tensión** al desenergizarse la bobina.
   - Para no bloquear la placa exterior, coloca siempre un **varistor o diodo volante (flyback)** en paralelo con los bornes del abrepuertas."""
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

def transcribir_audio_gemini(raw_bytes: bytes, mime_type: str = "audio/wav", api_key: str = "") -> dict:
    """Transcribe audio de voz a texto técnico usando los modelos de Google Gemini optimizados para audio."""
    if not api_key:
        return {"exito": False, "error": "Falta la clave API de Google Gemini."}

    b64_data = base64.b64encode(raw_bytes).decode("utf-8")
    clean_mime = mime_type or "audio/wav"
    if ";" in clean_mime:
        clean_mime = clean_mime.split(";")[0].strip()

    prompt = (
        "Eres un transcriptor técnico de campo experto para instaladores de baja tensión (REBT 2002) "
        "y telecomunicaciones (ICT-2 RD 346/2011) en España.\n"
        "Escucha atentamente este audio grabado por el instalador o técnico y transcribe con máxima exactitud "
        "su consulta, duda o instrucción técnica (cables, potencias, caídas de tensión, diferenciales, cuadros, "
        "telecomunicaciones, antenas TDT, satélite, fibra óptica FTTH, videoporteros, etc.).\n"
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

    modelos = ["gemini-3.5-transcribe", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]
    ultimo_error = "Error desconocido de conexión."
    for modelo in modelos:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        try:
            resp = requests.post(endpoint, json=payload, timeout=12)
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

def render_reproductor_voz_tts(texto: str, msg_idx: int):
    """Genera un botón interactivo que lee la respuesta técnica en voz alta en español usando la API de síntesis de voz del navegador."""
    import streamlit.components.v1 as components
    # Limpiar markdown, fórmulas KaTeX y caracteres especiales para síntesis de voz natural
    texto_limpio = re.sub(r'[*_#`$>\-•]', ' ', texto)
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
    texto_limpio = texto_limpio[:1200].replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    html_tts = f"""
    <div style="margin-top: 6px; display: inline-flex; gap: 8px; align-items: center;">
        <button id="btn_tts_play_{msg_idx}" onclick="hablar_{msg_idx}()" style="
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        ">
            🔊 Escuchar Respuesta por Voz
        </button>
        <button id="btn_tts_stop_{msg_idx}" onclick="parar_{msg_idx}()" style="
            background: #f1f5f9;
            color: #475569;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 12px;
            cursor: pointer;
        ">
            ⏹️ Silenciar
        </button>
    </div>
    <script>
    function hablar_{msg_idx}() {{
        if (!('speechSynthesis' in window)) {{
            alert('Tu navegador no soporta síntesis de voz directa.');
            return;
        }}
        window.speechSynthesis.cancel();
        var u = new SpeechSynthesisUtterance("{texto_limpio}");
        u.lang = 'es-ES';
        u.rate = 1.03;
        u.pitch = 1.0;
        window.speechSynthesis.speak(u);
    }}
    function parar_{msg_idx}() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
        }}
    }}
    </script>
    """
    components.html(html_tts, height=38)

def consultar_gemini_rebt(consulta: str, historial: list, api_key: str, imagen_b64: str = None) -> str:
    """Consulta a los modelos Google Gemini con el system prompt de Ingeniero Eléctrico/Telecomunicaciones e Instalador REBT/ICT-2."""
    contents = []
    for h in historial[-6:]:  # Contexto de mensajes previos
        role = "user" if h["role"] == "user" else "model"
        parts = [{"text": h["content"]}]
        contents.append({"role": role, "parts": parts})

    prompt_texto = consulta.strip()
    if not prompt_texto:
        if imagen_b64:
            prompt_texto = "Analiza detalladamente esta imagen técnica según el REBT (RD 842/2002) o ICT-2 (RD 346/2011) y criterios de ingeniería."
        else:
            prompt_texto = "Hola, ¿en qué me puedes ayudar hoy con el REBT y las instalaciones de telecomunicaciones?"

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

    modelos = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]
    for modelo in modelos:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        try:
            resp = requests.post(endpoint, json=payload, timeout=25)
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

def responder_consulta_rebt(consulta: str, historial: list = None, imagen_b64: str = None) -> str:
    """Enruta la consulta a Gemini con soporte multimodal (texto e imágenes) o al motor offline."""
    key = auditor_ia_rebt.obtener_gemini_api_key()
    if key and len(key) > 10:
        return consultar_gemini_rebt(consulta, historial or [], key, imagen_b64=imagen_b64)
    return responder_consulta_offline_con_imagen(consulta, imagen_b64)

def render_interfaz_asistente_rebt():
    """Renderiza la interfaz principal del Consultor IA REBT & Telecomunicaciones ICT-2."""
    st.markdown('<div class="section-header-blue"><h3 style="margin:0; color:#0369a1;">🤖 Consultor IA: Experto REBT & Telecomunicaciones ICT-2 (Ingeniero & Instalador)</h3></div>', unsafe_allow_html=True)
    st.caption("Asesor técnico integral 24/7 con doble titulación y visión práctica a pie de obra. Resuelve dudas reglamentarias de Electricidad (REBT 2002), Telecomunicaciones (ICT-2 RD 346/2011), Antenas RTV, Fibra Óptica FTTH, Cableado Estructurado Cat6/Cat6A, Racks, Videoporteros, Solar y tramitaciones en Murcia (DGEAIM) y SETSI.")

    # Barra superior de configuración rápida de IA
    api_key_actual = auditor_ia_rebt.obtener_gemini_api_key()
    tiene_key = bool(api_key_actual and len(api_key_actual) > 10)

    with st.expander("⚙️ Estado del Motor de Inteligencia Artificial", expanded=False):
        col_st1, col_st2 = st.columns([3, 1.2])
        with col_st1:
            if tiene_key:
                st.success("🟢 **Modo Online Activo (Google Gemini 3.5 Flash / Transcribe)**: Máxima capacidad de comprensión por voz, análisis visual y cálculo normativo en tiempo real.")
            else:
                st.info("ℹ️ **Modo Offline Activo (Base Experta REBT & ICT-2 Bolimur)**: Consultas automáticas guiadas por las 52 ITCs del REBT y RD 346/2011.")
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

    with st.expander("🎙️ Instrucciones por Voz, Cámara en Vivo y Documentos Técnicos", expanded=bool(st.session_state.get("ia_chat_imagen_activa"))):
        tab_mic, tab_cam, tab_up = st.tabs(["🎙️ Hablar por Micrófono (Voz Directa)", "📸 Tomar Foto con la Cámara", "📁 Subir Archivo (JPG, PNG, PDF)"])

        with tab_mic:
            st.caption("Graba tu duda o instrucción técnica por el micrófono. La IA transcribirá tus palabras y las procesará al instante con criterio de Ingeniero e Instalador:")
            audio_pic = st.audio_input("Hablar por micrófono al Consultor IA", key="voice_mic_ia_chat")
            if audio_pic is not None:
                st.audio(audio_pic)
                raw_audio = audio_pic.getvalue()
                audio_hash = hash(raw_audio)

                # Si es un audio nuevo, transcribir automáticamente
                if st.session_state.get("ia_chat_last_trans_hash") != audio_hash:
                    if tiene_key:
                        with st.spinner("🎙️ Escuchando y transcribiendo tu voz a texto con IA..."):
                            res_tr = transcribir_audio_gemini(raw_audio, audio_pic.type or "audio/wav", api_key_actual)
                            if res_tr.get("exito"):
                                st.session_state["ia_chat_last_trans_hash"] = audio_hash
                                st.session_state["ia_chat_texto_voz"] = res_tr.get("texto", "")
                                st.toast("🗣️ Voz transcrita con éxito", icon="🎙️")
                            else:
                                st.error(f"Error al transcribir voz: {res_tr.get('error')}")
                    else:
                        st.info("ℹ️ Para transcripción por voz directa con IA, activa tu clave Gemini en el panel superior. También puedes dictar en Windows con la combinación `Tecla Windows + H`.")

                texto_voz_actual = st.session_state.get("ia_chat_texto_voz", "")
                if texto_voz_actual:
                    st.success(f"🗣️ **Texto Transcrito Reconocido:**\n\n*«{texto_voz_actual}»*")
                    col_va1, col_va2 = st.columns([1.8, 3])
                    with col_va1:
                        if st.button("🚀 Enviar esta Consulta a la IA", type="primary", key="btn_send_voice_direct", use_container_width=True):
                            img_actual = st.session_state.get("ia_chat_imagen_activa")
                            st.session_state["ia_chat_imagen_activa"] = None
                            st.session_state["ia_chat_texto_voz"] = None

                            st.session_state.mensajes_chat_rebt.append({
                                "role": "user",
                                "content": f"🎙️ **Consulta de Voz:** «{texto_voz_actual}»",
                                "audio": raw_audio,
                                "image": img_actual
                            })
                            with st.spinner("Consultando normativas REBT e ICT-2 con visión de Ingeniero e Instalador..."):
                                resp = responder_consulta_rebt(
                                    consulta=texto_voz_actual,
                                    historial=st.session_state.mensajes_chat_rebt[:-1],
                                    imagen_b64=img_actual
                                )
                                st.session_state.mensajes_chat_rebt.append({"role": "assistant", "content": resp})
                            st.rerun()
                    with col_va2:
                        st.caption("💡 *Tip:* Puedes combinar una foto tomada con la cámara y tu nota de voz preguntando sobre ella.")

        with tab_cam:
            st.caption("Apunta con la cámara de tu móvil o portátil al cuadro eléctrico, pica de tierra, rotulación, antena o rack:")
            cam_pic = st.camera_input("Capturar foto desde el dispositivo", key="cam_input_ia_chat")
            if cam_pic is not None:
                b64_cam = procesar_archivo_camara_o_adjunto(cam_pic)
                if b64_cam:
                    st.session_state["ia_chat_imagen_activa"] = b64_cam

        with tab_up:
            st.caption("Sube un esquema unifilar, plano ICT o fotografía desde tu galería o disco (PNG, JPG, PDF):")
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
                    txt_q = "Analiza detalladamente esta imagen técnica según el REBT o ICT-2 y criterios de ingeniería. Identifica componentes, comprueba cumplimiento normativo y señala cualquier defecto o mejora."
                    st.session_state.mensajes_chat_rebt.append({
                        "role": "user",
                        "content": txt_q,
                        "image": img_actual
                    })
                    st.session_state["ia_chat_imagen_activa"] = None
                    with st.spinner("Analizando imagen con visión técnica e ingeniería REBT / ICT-2..."):
                        resp = responder_consulta_rebt(txt_q, st.session_state.mensajes_chat_rebt[:-1], imagen_b64=img_actual)
                        st.session_state.mensajes_chat_rebt.append({"role": "assistant", "content": resp})
                    st.rerun()

    # Preguntas Rápidas Frecuentes (REBT, Solar y Telecomunicaciones ICT-2)
    st.markdown("##### ⚡ Consultas Rápidas de Taller, Obra, Telecomunicaciones e ICT-2:")
    pills = [
        "📡 ¿Cuáles son los niveles de señal reglamentarios en toma para TDT y Satélite según la ICT-2?",
        "⚖️ ¿Cuándo se necesita Proyecto de Ingeniero de Telecomunicación vs Boletín?",
        "🌐 ¿Cómo instalar y certificar cableado estructurado Cat6 / Cat6A y racks?",
        "💡 ¿Qué exigencias técnicas tiene la instalación de fibra óptica FTTH (ICT-2)?",
        "🏢 ¿Qué dimensiones y tomas debe tener el Registro de Terminación de Red (RTR)?",
        "🚪 ¿Cómo elegir e instalar un videoportero de 2 hilos frente a uno IP / SIP?",
        "⚡ ¿Qué separación debe mantenerse entre conductores de electricidad de 230V y datos?",
        "⚖️ ¿Cuándo se necesita Proyecto de Ingeniero en lugar de MTD (REBT)?",
        "☀️ ¿Cuál es la diferencia entre una instalación solar conectada a red y una aislada?",
        "🛡️ ¿Cuántos circuitos magnetotérmicos (PIAs) se pueden conectar por cada diferencial?"
    ]

    pills_labels = [
        "📡 Niveles RTV TDT/SAT",
        "⚖️ Proyecto ICT vs Boletín",
        "🌐 Cableado Cat6 / Cat6A",
        "💡 Fibra Óptica FTTH < 2dB",
        "🏢 Registro RTR Vivienda",
        "🚪 Videoportero 2 Hilos / IP",
        "⚡ Separación 230V y Datos",
        "⚖️ MTD vs Proyecto REBT",
        "☀️ Solar Red vs Aislada",
        "🛡️ 5 Circuitos por Diferencial"
    ]

    cols_p1 = st.columns(5)
    cols_p2 = st.columns(5)
    todas_cols = cols_p1 + cols_p2

    pregunta_seleccionada = None
    for idx, p_text in enumerate(pills):
        with todas_cols[idx]:
            lbl = pills_labels[idx]
            if st.button(lbl, key=f"btn_pill_{idx}", help=p_text, use_container_width=True):
                pregunta_seleccionada = p_text

    # Inicializar historial de chat
    if "mensajes_chat_rebt" not in st.session_state:
        st.session_state.mensajes_chat_rebt = [
            {
                "role": "assistant",
                "content": (
                    "¡Hola! Soy tu **Consultor Senior de Ingeniería y Maestro Instalador Habilitado** (REBT e ICT-2) de Bolimur.\n\n"
                    "Estoy preparado para resolver cualquier duda sobre:\n"
                    "- ⚡ **Baja Tensión y Fotovoltaica (REBT):** Cálculos de caídas de tensión, secciones, coordinación de protecciones, esquemas unifilares, tramitación de MTD ante Industria (DGEAIM Murcia) y límites de Proyecto.\n"
                    "- 📡 **Telecomunicaciones (ICT-2 RD 346/2011):** Niveles de señal RTV (TDT LTE 700 / Satélite FI), cableado estructurado Cat6/Cat6A, armarios rack, redes FTTH de fibra óptica insensible a curvatura (G.657A2), registros RTR y videoporteros digitales de 2 hilos e IP.\n\n"
                    "🎙️ **Novedad:** Ahora puedes **hablar directamente por micrófono** y la IA transcribirá tu voz al instante, además de contar con **reproducción de voz en audio (🔊)** de todas las respuestas técnicas.\n\n"
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
        with st.spinner("Consultando normativa técnica REBT / ICT-2 y criterios de ingeniería..."):
            resp = responder_consulta_rebt(pregunta_seleccionada, st.session_state.mensajes_chat_rebt[:-1], imagen_b64=img_p)
            st.session_state.mensajes_chat_rebt.append({"role": "assistant", "content": resp})
        st.rerun()

    # Mostrar mensajes del chat
    st.markdown("---")
    chat_container = st.container()
    with chat_container:
        for idx, m in enumerate(st.session_state.mensajes_chat_rebt):
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
                    # Reproductor de voz Web Speech API
                    render_reproductor_voz_tts(m["content"], idx)

    # Entrada del usuario en la parte inferior
    prompt = st.chat_input("Escribe o consulta sobre electricidad (REBT), telecomunicaciones (ICT-2) o la foto adjunta...")
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
            with st.spinner("Analizando consulta según REBT, ICT-2 e ingeniería técnica..."):
                respuesta = responder_consulta_rebt(prompt, st.session_state.mensajes_chat_rebt[:-1], imagen_b64=img_enviar)
                st.markdown(respuesta)
                st.session_state.mensajes_chat_rebt.append({"role": "assistant", "content": respuesta})
                render_reproductor_voz_tts(respuesta, len(st.session_state.mensajes_chat_rebt) - 1)

    # Botones de control inferiores
    col_b1, col_b2 = st.columns([1, 4])
    with col_b1:
        if st.button("🗑️ Limpiar Conversación", key="btn_clear_chat", use_container_width=True):
            st.session_state.mensajes_chat_rebt = [
                {
                    "role": "assistant",
                    "content": "Conversación reiniciada. ¿En qué te puedo asesorar ahora sobre el REBT, ICT-2 o tus proyectos?"
                }
            ]
            st.session_state["ia_chat_imagen_activa"] = None
            st.session_state["ia_chat_texto_voz"] = None
            st.session_state["ia_chat_last_trans_hash"] = None
            st.rerun()
