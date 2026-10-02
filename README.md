# ⚡ Bolimur - Panel de Cálculo Eléctrico y Presupuestos (REBT)

Herramienta profesional de ingeniería y cálculo eléctrico conforme al **Reglamento Electrotécnico para Baja Tensión (REBT - Real Decreto 842/2002)** de España y sus Instrucciones Técnicas Complementarias (ITC-BT).

---

## 🚀 Módulos Incluidos

1. **🧮 Cálculo Rápido (CDT & Icc):**
   - Dimensionamiento de circuitos por caída de tensión admisible y comprobación térmica ($I_z$).
   - Comprobación de corte de cortocircuito instantáneo ($I_{cc,final}$) y disparo magnético en 0.1s.
   - Soporte para **Cobre** y **Aluminio** en aislamiento PVC (70 ºC) y XLPE/EPR (90 ºC).
   - Dimensionamiento de tubos protectores según **ITC-BT-21**.

2. **🏢 Previsión de Cargas ($P_t$):**
   - Cálculo conforme a **ITC-BT-10** con factores de simultaneidad $K$ oficiales.
   - Desglose detallado de Viviendas ($P_1$), Locales ($P_2$), Servicios Generales ($P_3$) y Garajes/IRVE ($P_4$).
   - Sincronización automática de carga con la Línea General de Alimentación (LGA).

3. **⚡ Línea General de Alimentación (LGA):**
   - Dimensionamiento de la LGA según **ITC-BT-14**.
   - Admite contadores concentrados (límite 0.5% CDT) o centralizaciones parciales (límite 1.0% CDT).
   - Soporte para conductores de cobre ($\ge 10\text{ mm}^2$) y aluminio ($\ge 16\text{ mm}^2$).
   - Dimensionamiento de tubos protectores según **ITC-BT-14 Tabla 1** ($\varnothing \ge 110\text{ mm}$).

4. **🔌 Derivación Individual (DI):**
   - Cálculo de la derivación individual según **ITC-BT-15** con límite de CDT al 1.0%.
   - Selección automática del IGA de vivienda (Curva C).
   - Diámetro mínimo de tubo reglamentario: **$\varnothing\,32\text{ mm}$**.

5. **🚗 Línea Específica de Recarga IRVE:**
   - Dimensionamiento de circuitos terminales para puntos de recarga de vehículo eléctrico según **ITC-BT-52**.
   - Soporte para Esquemas 1, 2, 3a, 3b y 4.

6. **🏡 Presupuesto de Vivienda e Inspector REBT:**
   - Generación de presupuestos con cálculo de rozas, canalizaciones, cableado y mecanismos según ITC-BT-25.
   - Base de datos conectada con precios de materiales.
   - Exportación de ofertas y resumen de acopio a **Excel (.xlsx)**.

7. **📚 Tablas REBT:**
   - Consulta rápida interactiva de conductividades, intensidades admisibles (UNE-HD 60364-5-52) y tablas de tubos.

---

## 💻 Instalación y Puesta en Marcha

### Requisitos
- Python 3.10 o superior (recomendado Python 3.11).

### 1. Clonar / Descargar el repositorio
```bash
cd Bolimur
```

### 2. Crear y activar entorno virtual
```bash
python -m venv .venv
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Iniciar la aplicación
```bash
streamlit run inicio.py
```
La aplicación se abrirá automáticamente en tu navegador web en `http://localhost:8501`.

---

## 🧪 Ejecución de Tests Automatizados

Para ejecutar la batería de pruebas normativas con `pytest`:
```bash
pytest tests/ -v
```

---

## 📜 Normativa y Referencias
- **Real Decreto 842/2002**: Reglamento Electrotécnico para Baja Tensión (REBT).
- **UNE-HD 60364-5-52 / UNE 20460-5-523**: Instalaciones eléctricas en edificios - Elección e instalación de equipos eléctricos (Canalizaciones e intensidades admisibles).
- **Guías Técnicas de Aplicación (BT-GEN, ITC-BT-10, 14, 15, 19, 21, 22, 25, 52)** emitidas por el Ministerio de Industria.
