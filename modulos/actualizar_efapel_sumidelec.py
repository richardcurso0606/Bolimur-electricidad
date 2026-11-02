# -*- coding: utf-8 -*-
"""
Script auxiliar para agregar el catálogo completo de Efapel (Sumidelec)
a base_datos_precio_oficial.xlsx sin modificar ninguno de los 395 artículos anteriores.
"""

import pandas as pd
import shutil
import os

ruta_excel = "base_datos_precio_oficial.xlsx"
ruta_backup = "base_datos_precio_oficial_backup.xlsx"

if not os.path.exists(ruta_backup):
    shutil.copyfile(ruta_excel, ruta_backup)
    print(f"Copia de seguridad creada en {ruta_backup}")

df = pd.read_excel(ruta_excel)
columnas_originales = list(df.columns)
total_previo = len(df)
print(f"Registros originales cargados: {total_previo}")

nuevos_articulos = [
    # --- MECANISMOS UNIVERSALES MEC 21 (SUMIDELEC) ---
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Mecanismos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21011-SUM",
        "Descripción Exacta del Artículo": "Interruptor Unipolar 10AX 250V Efapel MEC 21 (Ref. 21011)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.16,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.16 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Mecanismo base para empotrar universal (válido Logus 90, Apolo 5000, Sirius 70)"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Mecanismos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21021-SUM",
        "Descripción Exacta del Artículo": "Interruptor Bipolar 16AX 250V Efapel MEC 21 (Ref. 21021)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 2.45,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(2.45 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Corte bipolar 2P para termo eléctrico, caldera o climatización"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Mecanismos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21071-SUM",
        "Descripción Exacta del Artículo": "Conmutador 10AX 250V Efapel MEC 21 (Ref. 21071)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.25,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.25 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Conmutador para 2 puntos de luz con embornamiento rápido"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Mecanismos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21051-SUM",
        "Descripción Exacta del Artículo": "Cruzamiento 10AX 250V Efapel MEC 21 (Ref. 21051)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 2.05,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(2.05 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Cruzamiento intermedio para 3 o más puntos de luz"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Mecanismos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21151-SUM",
        "Descripción Exacta del Artículo": "Pulsador 10A 250V Efapel MEC 21 (Ref. 21151)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.30,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.30 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Pulsador para telerruptor, timbre o automatismo"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Mecanismos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21061-SUM",
        "Descripción Exacta del Artículo": "Doble Interruptor 10AX Efapel MEC 21 (Ref. 21061)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 2.10,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(2.10 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Control de dos circuitos independientes en una sola caja"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Mecanismos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21081-SUM",
        "Descripción Exacta del Artículo": "Doble Conmutador 10AX Efapel MEC 21 (Ref. 21081)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 2.25,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(2.25 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Doble conmutada en una sola caja de empotrar"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Mecanismos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21281-SUM",
        "Descripción Exacta del Artículo": "Pulsador de Persianas con Enclavamiento Efapel MEC 21 (Ref. 21281)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 3.65,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(3.65 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Mando motor persianas con bloqueo mecánico simultáneo"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Bases de Enchufe",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21111-SUM",
        "Descripción Exacta del Artículo": "Base de Enchufe Schuko 16A 250V 2P+T con Obturador Efapel MEC 21 (Ref. 21111)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.48,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.48 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Enchufe Schuko con protección infantil y embornamiento por tornillo/rápido"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Bases de Enchufe",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21113-SUM",
        "Descripción Exacta del Artículo": "Base de Enchufe Schuko 16A con Tapa Abatible Efapel MEC 21 (Ref. 21113)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 3.20,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(3.20 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Enchufe con tapa para cocinas, baños o zonas húmedas"
    },
    {
        "Nivel de Gama / Aplicación": "3. Media Residencial",
        "Familia / Categoria": "Bases de Enchufe",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21384-SUM",
        "Descripción Exacta del Artículo": "Toma Doble Cargador USB Tipo A+C 3.0A Efapel MEC 21 (Ref. 21384)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 16.50,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(16.50 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Carga rápida smartphones y tablets empotrable en caja de 67mm"
    },
    {
        "Nivel de Gama / Aplicación": "Telecomunicaciones / ICT",
        "Familia / Categoria": "Tomas / Datos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21381-SUM",
        "Descripción Exacta del Artículo": "Toma de Datos RJ45 Cat.6 UTP Efapel MEC 21 (Ref. 21381)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 3.25,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(3.25 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Conector Keystone RJ45 Cat.6 para redes gigabit ICT-2"
    },
    {
        "Nivel de Gama / Aplicación": "Telecomunicaciones / ICT",
        "Familia / Categoria": "Tomas / Datos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21541-SUM",
        "Descripción Exacta del Artículo": "Toma TV-R / SAT Final Desacoplada Efapel MEC 21 (Ref. 21541)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 2.95,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(2.95 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Toma de televisión terrestre y satélite paso de corriente final"
    },
    {
        "Nivel de Gama / Aplicación": "Telecomunicaciones / ICT",
        "Familia / Categoria": "Tomas / Datos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21542-SUM",
        "Descripción Exacta del Artículo": "Toma TV-R / SAT Paso / Intermedia Efapel MEC 21 (Ref. 21542)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 3.10,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(3.10 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Toma de televisión en cascada o paso intermedio"
    },
    {
        "Nivel de Gama / Aplicación": "3. Media Residencial",
        "Familia / Categoria": "Mecanismos",
        "Marca": "Efapel",
        "Serie / Gama": "MEC 21",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-21210-SUM",
        "Descripción Exacta del Artículo": "Regulador Giratorio LED Universal 4-100W Efapel MEC 21 (Ref. 21210)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 24.80,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(24.80 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Dimmer rotativo para iluminación LED regulable"
    },

    # --- SERIE LOGUS 90 BASE (BLANCO BRILLO) - SUMIDELEC ---
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90601-TBR-SUM",
        "Descripción Exacta del Artículo": "Tecla Simple Interruptor / Conmutador Efapel Logus 90 Blanco (Ref. 90601 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.58,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.58 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Tecla individual cuadrada serie Logus 90 Blanco"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90602-TBR-SUM",
        "Descripción Exacta del Artículo": "Tecla Doble para Doble Interruptor Efapel Logus 90 Blanco (Ref. 90602 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.85,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.85 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Tecla partida doble para MEC 21 21061/21081"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90611-TBR-SUM",
        "Descripción Exacta del Artículo": "Tapa Base de Enchufe Schuko con Obturador Logus 90 Blanco (Ref. 90611 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.65,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.65 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Frontal enchufe Schuko Logus 90"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90618-TBR-SUM",
        "Descripción Exacta del Artículo": "Tecla Persianas con Flechas Subir/Bajar Logus 90 Blanco (Ref. 90618 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.95,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.95 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Frontal para persianas motorizadas"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90642-TBR-SUM",
        "Descripción Exacta del Artículo": "Frontal Toma RJ45 1 Conector Logus 90 Blanco (Ref. 90642 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.75,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.75 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Tapa para conector de red RJ45"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90651-TBR-SUM",
        "Descripción Exacta del Artículo": "Frontal Toma TV-R / SAT Logus 90 Blanco (Ref. 90651 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.70,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.70 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Tapa embellecedora toma antena"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90675-TBR-SUM",
        "Descripción Exacta del Artículo": "Tapa Ciega Cuadrada Logus 90 Blanco (Ref. 90675 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.80,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.80 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Tapa de reserva para cajas de mecanismos"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90676-TBR-SUM",
        "Descripción Exacta del Artículo": "Tapa Salida de Cables Logus 90 Blanco (Ref. 90676 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.45,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.45 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Salida de cables para termo, placa o split"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90910-TBR-SUM",
        "Descripción Exacta del Artículo": "Marco 1 Elemento Efapel Logus 90 Blanco (Ref. 90910 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.42,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.42 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco individual serie Logus 90 Base Blanco"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90920-TBR-SUM",
        "Descripción Exacta del Artículo": "Marco 2 Elementos Efapel Logus 90 Blanco (Ref. 90920 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.95,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.95 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco doble reversible horizontal/vertical"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90930-TBR-SUM",
        "Descripción Exacta del Artículo": "Marco 3 Elementos Efapel Logus 90 Blanco (Ref. 90930 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.45,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.45 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco triple reversible horizontal/vertical"
    },
    {
        "Nivel de Gama / Aplicación": "2. Económica Estándar",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Base",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90940-TBR-SUM",
        "Descripción Exacta del Artículo": "Marco 4 Elementos Efapel Logus 90 Blanco (Ref. 90940 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 2.15,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(2.15 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco cuádruple para cabeceros o puestos de trabajo"
    },

    # --- SERIE LOGUS 90 ANIMATO / ACABADOS COLOR (ALUMINIO / ANTRACITA) ---
    {
        "Nivel de Gama / Aplicación": "3. Media Residencial",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Animato",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90601-TAL-SUM",
        "Descripción Exacta del Artículo": "Tecla Simple Conmutador Efapel Logus 90 Aluminio (Ref. 90601 TAL)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.45,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.45 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Acabado metalizado aluminio mate"
    },
    {
        "Nivel de Gama / Aplicación": "3. Media Residencial",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Animato",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90601-TIS-SUM",
        "Descripción Exacta del Artículo": "Tecla Simple Conmutador Efapel Logus 90 Antracita (Ref. 90601 TIS)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.45,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.45 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Acabado gris antracita moderno"
    },
    {
        "Nivel de Gama / Aplicación": "3. Media Residencial",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Animato",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90611-TAL-SUM",
        "Descripción Exacta del Artículo": "Tapa Enchufe Schuko Efapel Logus 90 Aluminio (Ref. 90611 TAL)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.65,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.65 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Tapa enchufe aluminio mate"
    },
    {
        "Nivel de Gama / Aplicación": "3. Media Residencial",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Animato",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90611-TIS-SUM",
        "Descripción Exacta del Artículo": "Tapa Enchufe Schuko Efapel Logus 90 Antracita (Ref. 90611 TIS)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.65,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.65 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Tapa enchufe antracita"
    },
    {
        "Nivel de Gama / Aplicación": "3. Media Residencial",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Animato",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90910-TAL-SUM",
        "Descripción Exacta del Artículo": "Marco 1 Elemento Efapel Logus 90 Animato Aluminio (Ref. 90910 TAL)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.35,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.35 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco individual acabado aluminio"
    },
    {
        "Nivel de Gama / Aplicación": "3. Media Residencial",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Animato",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90910-TIS-SUM",
        "Descripción Exacta del Artículo": "Marco 1 Elemento Efapel Logus 90 Animato Antracita (Ref. 90910 TIS)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.35,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.35 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco individual acabado antracita"
    },
    {
        "Nivel de Gama / Aplicación": "3. Media Residencial",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Animato",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90920-TIS-SUM",
        "Descripción Exacta del Artículo": "Marco 2 Elementos Efapel Logus 90 Animato Antracita (Ref. 90920 TIS)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 2.45,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(2.45 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco doble horizontal/vertical antracita"
    },
    {
        "Nivel de Gama / Aplicación": "4. Alta Decorativa",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Crystal",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90910-EBR-SUM",
        "Descripción Exacta del Artículo": "Marco 1 Elemento Cristal Blanco Efapel Logus 90 Crystal (Ref. 90910 EBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 8.50,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(8.50 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco de cristal templado auténtico blanco alta decoración"
    },
    {
        "Nivel de Gama / Aplicación": "4. Alta Decorativa",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Crystal",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90910-EPR-SUM",
        "Descripción Exacta del Artículo": "Marco 1 Elemento Cristal Negro Efapel Logus 90 Crystal (Ref. 90910 EPR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 8.50,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(8.50 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco de cristal templado auténtico negro para salones y suites"
    },

    # --- SERIE APOLO 5000 (SUMIDELEC) ---
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Apolo 5000",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-50601-TBR-SUM",
        "Descripción Exacta del Artículo": "Tecla Simple Interruptor / Conmutador Apolo 5000 Blanco (Ref. 50601 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.42,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.42 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Tecla clásica económica Apolo 5000"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Teclas / Tapas",
        "Marca": "Efapel",
        "Serie / Gama": "Apolo 5000",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-50602-TBR-SUM",
        "Descripción Exacta del Artículo": "Tecla Doble Interruptor Apolo 5000 Blanco (Ref. 50602 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.65,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.65 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Tecla doble serie Apolo 5000"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Apolo 5000",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-50910-TBR-SUM",
        "Descripción Exacta del Artículo": "Marco 1 Elemento Efapel Apolo 5000 Blanco (Ref. 50910 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.32,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.32 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco individual extra económico Apolo 5000"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Apolo 5000",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-50920-TBR-SUM",
        "Descripción Exacta del Artículo": "Marco 2 Elementos Efapel Apolo 5000 Blanco (Ref. 50920 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 0.72,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.72 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco doble serie Apolo 5000"
    },
    {
        "Nivel de Gama / Aplicación": "1. Ultra Económica",
        "Familia / Categoria": "Marcos / Placas",
        "Marca": "Efapel",
        "Serie / Gama": "Apolo 5000",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-50930-TBR-SUM",
        "Descripción Exacta del Artículo": "Marco 3 Elementos Efapel Apolo 5000 Blanco (Ref. 50930 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.10,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.10 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Marco triple serie Apolo 5000"
    },

    # --- SERIE ESTANCA 48 (IP65 SUPERFICIE) - SUMIDELEC ---
    {
        "Nivel de Gama / Aplicación": "Industrial / Estanco IP65",
        "Familia / Categoria": "Mecanismos Estancos",
        "Marca": "Efapel",
        "Serie / Gama": "Estanca 48 (IP65)",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-48011-CCZ-SUM",
        "Descripción Exacta del Artículo": "Interruptor Estanco Superficie IP65 Efapel Serie 48 Gris (Ref. 48011 CCZ)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 3.40,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(3.40 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Mecanismo estanco de superficie para garajes, terrazas y naves"
    },
    {
        "Nivel de Gama / Aplicación": "Industrial / Estanco IP65",
        "Familia / Categoria": "Mecanismos Estancos",
        "Marca": "Efapel",
        "Serie / Gama": "Estanca 48 (IP65)",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-48071-CCZ-SUM",
        "Descripción Exacta del Artículo": "Conmutador Estanco Superficie IP65 Efapel Serie 48 Gris (Ref. 48071 CCZ)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 3.65,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(3.65 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Conmutador estanco superficie IP65"
    },
    {
        "Nivel de Gama / Aplicación": "Industrial / Estanco IP65",
        "Familia / Categoria": "Mecanismos Estancos",
        "Marca": "Efapel",
        "Serie / Gama": "Estanca 48 (IP65)",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-48151-CCZ-SUM",
        "Descripción Exacta del Artículo": "Pulsador Estanco Superficie IP65 Efapel Serie 48 Gris (Ref. 48151 CCZ)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 3.60,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(3.60 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Pulsador estanco para puertas automáticas o timbres exteriores"
    },
    {
        "Nivel de Gama / Aplicación": "Industrial / Estanco IP65",
        "Familia / Categoria": "Bases de Enchufe",
        "Marca": "Efapel",
        "Serie / Gama": "Estanca 48 (IP65)",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-48132-CCZ-SUM",
        "Descripción Exacta del Artículo": "Base Enchufe Schuko Estanca IP65 Efapel Serie 48 Gris (Ref. 48132 CCZ)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 3.85,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(3.85 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Base schuko 16A con tapa estanca para exteriores y cuartos de caldera"
    },
    {
        "Nivel de Gama / Aplicación": "Industrial / Estanco IP65",
        "Familia / Categoria": "Bases de Enchufe",
        "Marca": "Efapel",
        "Serie / Gama": "Estanca 48 (IP65)",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-48134-CCZ-SUM",
        "Descripción Exacta del Artículo": "Base Enchufe Doble Schuko Estanca IP65 Efapel Serie 48 Gris (Ref. 48134 CCZ)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 7.20,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(7.20 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Enchufe doble monoblock estanco en superficie"
    },

    # --- CANALES Y CAJAS MODULARES EFAPEL (SUMIDELEC) ---
    {
        "Nivel de Gama / Aplicación": "Material Instalación",
        "Familia / Categoria": "Canalización / Canales",
        "Marca": "Efapel",
        "Serie / Gama": "Canales Moldura",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-CAN-12X7-SUM",
        "Descripción Exacta del Artículo": "Canaleta de Distribución Efapel 12x7mm Blanco (Tira 2m)",
        "Unidad": "m",
        "Precio S/IVA (€)": 0.75,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.75 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Canal miniatura para hilo de timbre, datos o iluminación"
    },
    {
        "Nivel de Gama / Aplicación": "Material Instalación",
        "Familia / Categoria": "Canalización / Canales",
        "Marca": "Efapel",
        "Serie / Gama": "Canales Moldura",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-CAN-16X10-SUM",
        "Descripción Exacta del Artículo": "Canaleta Adhesiva Efapel 16x10mm Blanco con Tapa Envolvente (Tira 2m)",
        "Unidad": "m",
        "Precio S/IVA (€)": 0.92,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(0.92 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Canaleta con adhesivo de alta adherencia"
    },
    {
        "Nivel de Gama / Aplicación": "Material Instalación",
        "Familia / Categoria": "Canalización / Canales",
        "Marca": "Efapel",
        "Serie / Gama": "Canales Moldura",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-CAN-32X16-SUM",
        "Descripción Exacta del Artículo": "Canaleta de Distribución Efapel 32x16mm Blanco con Tabique Divisor (Tira 2m)",
        "Unidad": "m",
        "Precio S/IVA (€)": 1.65,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.65 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Separación física obligatoria REBT de fuerza y telecomunicaciones"
    },
    {
        "Nivel de Gama / Aplicación": "Material Instalación",
        "Familia / Categoria": "Cajas Superficie",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Superficie",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90981-TBR-SUM",
        "Descripción Exacta del Artículo": "Caja de Superficie 1 Elemento Efapel Logus 90 Blanco (Ref. 90981 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 1.45,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(1.45 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Para montar cualquier mecanismo MEC 21 visto en superficie sin rozas"
    },
    {
        "Nivel de Gama / Aplicación": "Material Instalación",
        "Familia / Categoria": "Cajas Superficie",
        "Marca": "Efapel",
        "Serie / Gama": "Logus 90 Superficie",
        "Proveedor / Tienda": "Sumidelec",
        "Código SKU / Ref": "EFA-90982-TBR-SUM",
        "Descripción Exacta del Artículo": "Caja de Superficie 2 Elementos Efapel Logus 90 Blanco (Ref. 90982 TBR)",
        "Unidad": "Ud",
        "Precio S/IVA (€)": 2.30,
        "IVA (%)": 0.21,
        "Precio C/IVA (€)": round(2.30 * 1.21, 2),
        "Observaciones / Aplicación Técnica": "Caja doble de superficie para tomas o interruptores vistos"
    }
]

# Asignar IDs consecutivos continuando desde ART-0396
start_id = total_previo + 1
for i, item in enumerate(nuevos_articulos):
    item["ID"] = f"ART-{start_id + i:04d}"

df_nuevos = pd.DataFrame(nuevos_articulos)
# Garantizar el mismo orden de columnas
df_nuevos = df_nuevos[columnas_originales]

# Unir ambos dataframes
df_final = pd.concat([df, df_nuevos], ignore_index=True)

# Guardar
df_final.to_excel(ruta_excel, index=False)
print("--- PROCESO COMPLETADO ---")
print(f"Artículos originales (intactos): {total_previo}")
print(f"Nuevos artículos Efapel Sumidelec añadidos: {len(df_nuevos)}")
print(f"Total actual en base de datos: {len(df_final)}")
print(f"Primer nuevo ID: {df_nuevos.iloc[0]['ID']} ({df_nuevos.iloc[0]['Descripción Exacta del Artículo']})")
print(f"Último nuevo ID: {df_nuevos.iloc[-1]['ID']} ({df_nuevos.iloc[-1]['Descripción Exacta del Artículo']})")
