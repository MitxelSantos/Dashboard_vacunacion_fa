# Dashboard de Vacunación - Fiebre Amarilla del Tolima

Dashboard interactivo para el análisis integral de la vacunación contra la fiebre amarilla en el departamento del Tolima, incluyendo **vacunación individual regular** y **barridos territoriales de emergencia**.

## 🎯 Características Principales

- **Análisis Dual**: Vacunación individual + Barridos territoriales
- **Cálculo Automático de Edad**: Desde fecha de nacimiento
- **9 Rangos de Edad**: < 1, 1-5, 6-10, 11-20, 21-30, 31-40, 41-50, 51-59, 60+ años
- **Consolidación Automática**: Combina rangos 60-69 y 70+ en "60 años y más"
- **Cobertura Geográfica**: Municipios y veredas
- **Análisis Temporal**: Pre-emergencia vs Emergencia sanitaria
- **Población por EAPB**: Múltiples aseguradoras por municipio

## 📊 Rangos de Edad Configurados

| Código | Descripción | Criterio de Clasificación |
|--------|-------------|---------------------------|
| **<1** | < 1 año | 0 a 11 meses |
| **1-5** | 1-5 años | 1 a 5 años cumplidos |
| **6-10** | 6-10 años | 6 a 10 años cumplidos |
| **11-20** | 11-20 años | 11 a 20 años cumplidos |
| **21-30** | 21-30 años | 21 a 30 años cumplidos |
| **31-40** | 31-40 años | 31 a 40 años cumplidos |
| **41-50** | 41-50 años | 41 a 50 años cumplidos |
| **51-59** | 51-59 años | 51 a 59 años cumplidos |
| **60+** | 60 años y más | 60 años cumplidos en adelante |

> **Nota**: La edad se calcula automáticamente desde `FechaNacimiento` usando la fecha de vacunación como referencia.

## 📂 Estructura de Datos

### 1. Datos Históricos Individuales (`data/vacunacion_fa.csv`)
Registros de vacunación individual pre-emergencia:

```csv
IdPaciente,TipoIdentificacion,Documento,PrimerNombre,PrimerApellido,Sexo,FechaNacimiento,NombreMunicipioNacimiento,NombreDptoNacimiento,NombreMunicipioResidencia,NombreDptoResidencia,GrupoEtnico,Desplazado,Discapacitado,RegimenAfiliacion,NombreAseguradora,FA UNICA,Edad_Vacunacion,Grupo_Edad
1,CC,12345678,JUAN,PEREZ,M,1990-05-15,IBAGUE,TOLIMA,IBAGUE,TOLIMA,MESTIZO,NO,NO,CONTRIBUTIVO,NUEVA EPS,2024-01-10,33,31-40
```

**Columnas críticas:**
- `FechaNacimiento`: Fecha de nacimiento (para calcular edad)
- `FA UNICA`: Fecha de vacunación individual
- `NombreMunicipioResidencia`: Municipio de residencia

### 2. Barridos Territoriales (`data/Resumen.xlsx`)
Registros agregados por cantidades en rangos de edad:

```csv
FECHA,MUNICIPIO,VEREDAS,<1,1-5,6-10,11-20,21-30,31-40,41-50,51-59,60+
2024-01-15,IBAGUE,VEREDA_RURAL_1,5,12,18,25,35,28,22,15,20
2024-01-16,ESPINAL,VEREDA_RURAL_2,3,8,15,20,30,25,18,12,15
```

**Columnas clave:**
- `FECHA`: Fecha del barrido territorial
- `MUNICIPIO`: Municipio donde se realizó el barrido
- `VEREDAS`: Vereda específica visitada
- `<1`, `1-5`, `6-10`, `11-20`, `21-30`, `31-40`, `41-50`, `51-59`, `60+`: Cantidades vacunadas por rango

**Consolidación Automática:**
El sistema detecta y consolida automáticamente columnas adicionales en el rango "60+":
- `60-69 AÑOS` → Se suma a `60+`
- `70 AÑOS Y MAS` → Se suma a `60+`
- `70+` → Se suma a `60+`

### 3. Población por EAPB (`data/Poblacion_aseguramiento.xlsx`)
Población por municipio y aseguradora:

```csv
Municipio,EAPB,Total
IBAGUE,NUEVA EPS,45000
IBAGUE,SANITAS,23000
IBAGUE,SURA,18000
ESPINAL,NUEVA EPS,15000
```

**Características:**
- Múltiples líneas por municipio (una por cada EAPB)
- Campo `Total`: Población afiliada a cada EAPB

## 🏗️ Instalación y Configuración

### 1. Clonar repositorio
```bash
git clone https://github.com/tu-repo/dashboard-vacunacion-fa.git
cd dashboard-vacunacion-fa
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
# Dependencia adicional para logo
pip install Pillow
```

### 4. Configurar assets y estructura
```bash
python setup_assets.py
```

### 5. Configurar datos
Coloca tus archivos en la carpeta `data/`:
- `vacunacion_fa.csv` - **Debe incluir columna `FechaNacimiento`**
- `Resumen.xlsx` - Barridos territoriales (hoja "Barridos" o "Vacunacion")
- `Poblacion_aseguramiento.xlsx` - Población por EAPB
- Logo oficial en `assets/images/logo_gobernacion.png`

### 6. Validar datos
```bash
python validate_data.py
```

### 7. Ejecutar dashboard
```bash
streamlit run app.py
```

## 🧮 Cálculo Automático de Edad

### Algoritmo de Cálculo
```python
def calculate_age(fecha_nacimiento, fecha_vacunacion):
    edad = fecha_vacunacion.year - fecha_nacimiento.year
    
    # Ajustar si no ha llegado el cumpleaños
    if (fecha_vacunacion.month, fecha_vacunacion.day) < 
       (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    
    return max(0, edad)  # No permitir edades negativas
```

### Clasificación en Rangos
```python
def classify_age_group(edad):
    if edad < 1: return "<1"
    elif 1 <= edad <= 5: return "1-5"
    elif 6 <= edad <= 10: return "6-10"
    elif 11 <= edad <= 20: return "11-20"
    elif 21 <= edad <= 30: return "21-30"
    elif 31 <= edad <= 40: return "31-40"
    elif 41 <= edad <= 50: return "41-50"
    elif 51 <= edad <= 59: return "51-59"
    else: return "60+"
```

## 📋 Funcionalidades del Dashboard

### 🏠 **Resumen General**
- Métricas principales: Individual vs Barridos
- Distribución combinada por rangos de edad
- Tabla detallada con porcentajes por rango
- Cobertura total y por modalidad

### 📅 **Análisis Temporal**
- **Pre-emergencia**: Evolución diaria de vacunación individual
- **Emergencia**: Frecuencia de barridos territoriales
- Identificación automática de fecha de corte
- Estadísticas de duración y promedio diario

### 🗺️ **Distribución Geográfica**
- Top municipios por vacunación individual
- Top municipios por barridos territoriales
- **Análisis de veredas**: Cobertura rural específica con métricas detalladas
- Comparación directa entre modalidades

### 🏥 **Análisis de Población**
- Distribución por EAPB
- Múltiples aseguradoras por municipio
- Cálculo de coberturas por EAPB
- Métricas de avance hacia metas (80% población objetivo)

## 🔧 Detección Automática de Columnas

El sistema detecta automáticamente columnas con estos patrones:

### Patrones para Rangos de Edad:
```python
PATRONES_DETECCION = {
    "<1": ["<1", "< 1", "MENOR 1", "LACTANTE", "0-11M", "0-1"],
    "1-5": ["1-5", "1 A 5", "1A5", "PREESCOLAR"],
    "6-10": ["6-10", "6 A 10", "6A10", "ESCOLAR"],
    "11-20": ["11-20", "11 A 20", "11A20", "ADOLESCENTE"],
    "21-30": ["21-30", "21 A 30", "21A30"],
    "31-40": ["31-40", "31 A 40", "31A40"],
    "41-50": ["41-50", "41 A 50", "41A50"],
    "51-59": ["51-59", "51 A 59", "51A59"],
    "60+": ["60+", "60 +", "60 Y MAS", "MAYOR 60", ">60"]
}

# Patrones para consolidación automática en 60+
CONSOLIDACION_60_MAS = [
    "60-69", "60 A 69", "70+", "70 Y MAS", "MAYOR 70"
]
```

## 📊 Validaciones Integradas

El sistema incluye validaciones automáticas:

### ✅ **Validaciones de Estructura**
- Detecta columnas de edad automáticamente
- Verifica presencia de `FechaNacimiento`
- Identifica columnas para consolidación
- Valida formato de fechas

### ✅ **Validaciones de Cálculo**
- Pruebas unitarias de cálculo de edad
- Verificación de clasificación por rangos
- Detección de edades ilógicas (negativas, >120 años)
- Estadísticas de edades calculadas

### ✅ **Validaciones de Datos**
- Consistencia temporal entre períodos
- Completitud de registros por barrido
- Integridad de datos de población
- Calidad de datos geográficos

## 🚀 Despliegue en Producción

### Streamlit Cloud
1. Sube el repositorio a GitHub
2. Configura Streamlit Cloud
3. Establece variables de entorno si es necesario
4. Despliega automáticamente

### Docker (Opcional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## 🔍 Troubleshooting

### Logo no se muestra
```bash
# Verificar si existe el archivo
ls -la assets/images/logo_gobernacion.png

# Si no existe, ejecutar configuración
python setup_assets.py
```

### Edades no se calculan correctamente
```bash
# Verificar que existe la columna FechaNacimiento
python -c "import pandas as pd; df = pd.read_csv('data/vacunacion_fa.csv'); print('FechaNacimiento' in df.columns)"

# Ejecutar validación específica
python validate_data.py
```

### Columnas de edad no detectadas
```bash
# Ver columnas del archivo de barridos
python -c "import pandas as pd; df = pd.read_excel('data/Resumen.xlsx'); print(list(df.columns))"

# El sistema detecta automáticamente variaciones como:
# "<1", "< 1", "MENOR 1", "1-5", "1 A 5", etc.
```

### Error de fechas o datos inconsistentes
```bash
# Ejecutar validación completa
python validate_data.py

# Verificar ejemplos de datos
cat data/ejemplo_*.csv
```

## 📈 Métricas Clave Calculadas

- **Cobertura General**: Vacunados / Población Total × 100
- **Avance de Meta**: Vacunados / Meta × 100 (Meta = 80% población)
- **Distribución Etaria**: % por cada rango de edad calculado desde FechaNacimiento
- **Eficiencia Territorial**: Veredas cubiertas / Barridos realizados
- **Tasa de Completitud**: Registros con datos completos / Total registros

## 🤝 Contribución

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/mejora`)
3. Commit cambios (`git commit -m 'Agregar mejora'`)
4. Push a la rama (`git push origin feature/mejora`)
5. Crear Pull Request

## 📞 Soporte

- **Secretaría de Salud del Tolima**
- **Sistema de Vigilancia Epidemiológica**
- Dashboard versión 2.1 - Cálculo Automático de Edad

## 📚 Archivos de Referencia

- `docs/rangos_edad_referencia.md` - Documentación completa de rangos
- `data/ejemplo_*.csv` - Ejemplos de estructura de datos
- `validate_data.py` - Script de validación completa

---

> **Importante**: Este dashboard calcula automáticamente la edad desde `FechaNacimiento` y clasifica en 9 rangos específicos. Los rangos 60-69 y 70+ se consolidan automáticamente en "60 años y más" para los barridos territoriales.

**Fecha de actualización**: Rangos de edad correctos implementados
**Versión**: 2.1 - Cálculo automático de edad desde fecha de nacimiento