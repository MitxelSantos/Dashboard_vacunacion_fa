"""
setup_assets.py - Script para configurar assets necesarios del dashboard
Versión actualizada con rangos de edad correctos
"""

import os
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont
import io


def create_directories():
    """Crea las carpetas necesarias"""
    directories = ["assets/images", "data", "data/processed", "logs"]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio creado/verificado: {directory}")


def create_placeholder_logo():
    """Crea un logo placeholder si no existe el oficial"""
    logo_path = "assets/images/logo_gobernacion.png"

    if not os.path.exists(logo_path):
        # Crear logo placeholder
        width, height = 400, 200
        image = Image.new("RGB", (width, height), color="#7D0F2B")
        draw = ImageDraw.Draw(image)

        # Texto del logo
        try:
            # Intentar usar una fuente del sistema
            font_large = ImageFont.truetype("arial.ttf", 28)
            font_medium = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except:
            # Fallback a fuente por defecto
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Líneas del logo
        lines = [
            {"text": "GOBERNACIÓN", "font": font_large, "y": 30},
            {"text": "DEL TOLIMA", "font": font_large, "y": 65},
            {"text": "Secretaría de Salud", "font": font_medium, "y": 110},
            {"text": "Dashboard Fiebre Amarilla", "font": font_small, "y": 140},
            {"text": "Sistema de Vigilancia", "font": font_small, "y": 160},
        ]

        # Dibujar cada línea centrada
        for line in lines:
            bbox = draw.textbbox((0, 0), line["text"], font=line["font"])
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, line["y"]), line["text"], fill="white", font=line["font"])

        image.save(logo_path)
        print(f"✅ Logo placeholder creado: {logo_path}")
    else:
        print(f"✅ Logo ya existe: {logo_path}")


def verify_data_files():
    """Verifica la existencia de archivos de datos críticos"""
    critical_files = [
        "data/vacunacion_fa.csv",
        "data/Resumen.xlsx",
        "data/Poblacion_aseguramiento.xlsx",
    ]

    print("\n🔍 Verificando archivos de datos:")
    for file_path in critical_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path} - {size:,} bytes")
        else:
            print(f"❌ {file_path} - NO ENCONTRADO")


def create_sample_data_structure():
    """Crea estructura de datos de ejemplo para referencia con rangos correctos"""

    # Crear archivo de ejemplo para barridos con rangos correctos
    sample_barridos = """FECHA,MUNICIPIO,VEREDAS,<1,1-5,6-10,11-20,21-30,31-40,41-50,51-59,60+
2024-01-15,IBAGUE,VEREDA_EJEMPLO_1,5,12,18,25,35,28,22,15,20
2024-01-16,ESPINAL,VEREDA_EJEMPLO_2,3,8,15,20,30,25,18,12,15
2024-01-17,MELGAR,VEREDA_EJEMPLO_3,4,10,12,22,28,20,16,10,18
2024-01-18,CHAPARRAL,VEREDA_EJEMPLO_4,2,6,10,18,25,22,14,8,12
2024-01-19,HONDA,VEREDA_EJEMPLO_5,3,9,14,20,32,26,20,11,16"""

    with open("data/ejemplo_barridos.csv", "w", encoding="utf-8") as f:
        f.write(sample_barridos)
    print("✅ Archivo de ejemplo creado: data/ejemplo_barridos.csv")

    # Crear archivo de ejemplo para datos históricos individuales
    sample_historicos = """IdPaciente,TipoIdentificacion,Documento,PrimerNombre,PrimerApellido,Sexo,FechaNacimiento,NombreMunicipioNacimiento,NombreDptoNacimiento,NombreMunicipioResidencia,NombreDptoResidencia,GrupoEtnico,Desplazado,Discapacitado,RegimenAfiliacion,NombreAseguradora,FA UNICA,Edad_Vacunacion,Grupo_Edad
1,CC,12345678,JUAN,PEREZ,M,1990-05-15,IBAGUE,TOLIMA,IBAGUE,TOLIMA,MESTIZO,NO,NO,CONTRIBUTIVO,NUEVA EPS,2024-01-10,33,31-40
2,TI,87654321,MARIA,GONZALEZ,F,2019-03-20,ESPINAL,TOLIMA,ESPINAL,TOLIMA,MESTIZO,NO,NO,SUBSIDIADO,MEDIMAS,2024-01-12,4,1-5
3,CC,11223344,CARLOS,RODRIGUEZ,M,1975-08-10,MELGAR,TOLIMA,MELGAR,TOLIMA,MESTIZO,NO,NO,CONTRIBUTIVO,SANITAS,2024-01-15,48,41-50
4,RC,55667788,ANA,MARTINEZ,F,2023-12-01,IBAGUE,TOLIMA,IBAGUE,TOLIMA,MESTIZO,NO,NO,SUBSIDIADO,NUEVA EPS,2024-01-20,0,<1"""

    with open("data/ejemplo_historicos.csv", "w", encoding="utf-8") as f:
        f.write(sample_historicos)
    print("✅ Archivo de ejemplo creado: data/ejemplo_historicos.csv")

    # Crear archivo de ejemplo para población
    sample_poblacion = """Municipio,EAPB,Total
IBAGUE,NUEVA EPS,45000
IBAGUE,SANITAS,23000
IBAGUE,SURA,18000
IBAGUE,MEDIMAS,15000
ESPINAL,NUEVA EPS,15000
ESPINAL,SANITAS,8000
ESPINAL,MEDIMAS,5000
MELGAR,NUEVA EPS,12000
MELGAR,SANITAS,6000
CHAPARRAL,NUEVA EPS,18000
CHAPARRAL,MEDIMAS,8000
HONDA,NUEVA EPS,10000
HONDA,SANITAS,4000"""

    with open("data/ejemplo_poblacion.csv", "w", encoding="utf-8") as f:
        f.write(sample_poblacion)
    print("✅ Archivo de ejemplo creado: data/ejemplo_poblacion.csv")


def create_age_ranges_reference():
    """Crea archivo de referencia con los rangos de edad correctos"""

    # Crear directorio docs si no existe
    Path("docs").mkdir(exist_ok=True)

    age_ranges_info = """# RANGOS DE EDAD - DASHBOARD FIEBRE AMARILLA TOLIMA

## Rangos de Edad Configurados

| Código | Descripción | Rango de Edad |
|--------|-------------|---------------|
| <1     | < 1 año     | 0 a 11 meses  |
| 1-5    | 1-5 años    | 1 a 5 años    |
| 6-10   | 6-10 años   | 6 a 10 años   |
| 11-20  | 11-20 años  | 11 a 20 años  |
| 21-30  | 21-30 años  | 21 a 30 años  |
| 31-40  | 31-40 años  | 31 a 40 años  |
| 41-50  | 41-50 años  | 41 a 50 años  |
| 51-59  | 51-59 años  | 51 a 59 años  |
| 60+    | 60 años y más | 60 años en adelante |

## Consolidación Automática

El sistema consolida automáticamente las siguientes columnas en el rango "60+":
- 60-69 AÑOS
- 70 AÑOS Y MAS
- 70+
- MAYOR 70

## Cálculo de Edad

La edad se calcula automáticamente desde la columna "FechaNacimiento" 
usando la fecha de vacunación ("FA UNICA") como referencia.

Fórmula: Edad = Año_Vacunación - Año_Nacimiento
(Ajustada si no ha llegado el cumpleaños en el año de vacunación)

## Patrones de Detección de Columnas

El sistema detecta automáticamente columnas con estos patrones:

### Rango < 1 año:
- "<1", "< 1", "MENOR 1", "LACTANTE", "0-11M"

### Rango 1-5 años:
- "1-5", "1 A 5", "1A5", "PREESCOLAR"

### Rango 6-10 años:
- "6-10", "6 A 10", "6A10", "ESCOLAR"

### Rango 11-20 años:
- "11-20", "11 A 20", "11A20", "ADOLESCENTE"

### Rango 21-30 años:
- "21-30", "21 A 30", "21A30"

### Rango 31-40 años:
- "31-40", "31 A 40", "31A40"

### Rango 41-50 años:
- "41-50", "41 A 50", "41A50"

### Rango 51-59 años:
- "51-59", "51 A 59", "51A59"

### Rango 60+ años:
- "60+", "60 +", "60 Y MAS", "60 Y MÁS", "MAYOR 60"

---

Última actualización: """ + str(
        os.path.getctime(__file__) if os.path.exists(__file__) else "N/A"
    )

    # Crear directorio docs si no existe
    Path("docs").mkdir(exist_ok=True)

    with open("docs/rangos_edad_referencia.md", "w", encoding="utf-8") as f:
        f.write(age_ranges_info)

    print("✅ Referencia de rangos creada: docs/rangos_edad_referencia.md")


def verify_requirements():
    """Verifica que las dependencias estén instaladas"""
    print("\n🔍 Verificando dependencias:")

    required_packages = ["streamlit", "pandas", "numpy", "plotly", "openpyxl", "Pillow"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.lower().replace("-", "_"))
            print(f"✅ {package} - Instalado")
        except ImportError:
            print(f"❌ {package} - NO INSTALADO")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️ Paquetes faltantes: {', '.join(missing_packages)}")
        print("Ejecuta: pip install " + " ".join(missing_packages))
        return False
    else:
        print("\n✅ Todas las dependencias están instaladas")
        return True


def main():
    """Función principal de configuración"""
    print("🚀 Configurando assets del dashboard...\n")
    print("📊 Versión con rangos de edad actualizados:")
    print("   < 1, 1-5, 6-10, 11-20, 21-30, 31-40, 41-50, 51-59, 60+")
    print()

    # Crear directorios
    create_directories()

    # Verificar dependencias
    deps_ok = verify_requirements()

    # Crear logo
    create_placeholder_logo()

    # Verificar archivos de datos
    verify_data_files()

    # Crear ejemplos
    create_sample_data_structure()

    # Crear documentación de referencia
    create_age_ranges_reference()

    print("\n✅ Configuración completada!")
    print("\n📋 Próximos pasos:")
    print("1. Reemplaza assets/images/logo_gobernacion.png con el logo oficial")
    print("2. Coloca tus archivos de datos reales en la carpeta data/")
    print("   - data/vacunacion_fa.csv (con columna FechaNacimiento)")
    print("   - data/Resumen.xlsx (con rangos <1, 1-5, 6-10, etc.)")
    print("   - data/Poblacion_aseguramiento.xlsx")

    if not deps_ok:
        print("3. Instala las dependencias faltantes")
        print("4. Ejecuta: python validate_data.py")
        print("5. Ejecuta: streamlit run app.py")
    else:
        print("3. Ejecuta: python validate_data.py")
        print("4. Ejecuta: streamlit run app.py")

    print("\n📚 Documentación:")
    print("- Rangos de edad: docs/rangos_edad_referencia.md")
    print("- Ejemplos de datos: data/ejemplo_*.csv")


if __name__ == "__main__":
    main()
