# Dashboard de Vacunación - Fiebre Amarilla del Tolima

Dashboard interactivo para análisis de vacunación contra fiebre amarilla en el departamento del Tolima.

**Desarrollado por:** Ing. José Miguel Santos  
**Secretaría de Salud del Tolima**

## Características

- **Análisis territorial** por municipios
- **Distribución por rangos de edad** (9 rangos consolidados)
- **Comparación de modalidades**: Individual vs Barridos territoriales
- **Análisis temporal** de evolución de vacunación
- **Cálculo automático de edad** desde fecha de nacimiento

## Datos Requeridos

### Obligatorios:
1. **`data/vacunacion_fa.csv`** - Vacunación individual
   - Columnas críticas: `FechaNacimiento`, `FA UNICA`, `NombreMunicipioResidencia`

2. **`data/Resumen.xlsx`** - Barridos territoriales  
   - Columnas por rangos de edad: `<1`, `1-5`, `6-10`, `11-20`, `21-30`, `31-40`, `41-50`, `51-59`, `60+`
   - Secciones: TPVB (vacunados en barrido), TPNVP (renuentes)

### Opcionales:
3. **`data/Poblacion_aseguramiento.xlsx`** - Población por municipios
   - Para análisis de cobertura territorial completo

## Instalación

```bash
# 1. Clonar repositorio
git clone [tu-repo]
cd dashboard

# 2. Instalar dependencias  
pip install -r requirements.txt

# 3. Colocar archivos de datos en carpeta data/

# 4. Ejecutar dashboard
streamlit run app.py
```

## Estructura

```
/dashboard
├── app.py                 # Aplicación principal
├── vistas/
│   ├── overview.py       # Resumen general
│   ├── temporal.py       # Análisis temporal
│   ├── geographic.py     # Análisis geográfico  
│   └── population.py     # Análisis poblacional
├── requirements.txt      # Dependencias
└── README.md            # Documentación
```

## Funcionamiento

### Lógica de Datos:

1. **Vacunación Individual**: Cada fila = 1 persona vacunada
   - Edad calculada desde `FechaNacimiento` a fecha actual
   - Agrupación por municipio de residencia

2. **Barridos Territoriales**: Cada fila = 1 barrido en vereda
   - Sección TPVB: Vacunados durante el barrido  
   - Sección TPNVP: Renuentes (rechazan vacunación)
   - Cantidades por rangos de edad preestablecidos

3. **Población**: Suma de todas las EAPB por municipio
   - Base para cálculo de cobertura territorial

### Métricas Calculadas:

- **Cobertura Real** = (Vacunados municipio / Población asegurada municipio) × 100
- **Meta 80%** = Población asegurada × 0.8  
- **Tasa de Aceptación** = Vacunados / (Vacunados + Renuentes) × 100

## Rangos de Edad

| Código | Descripción | Criterio |
|--------|-------------|----------|
| <1     | < 1 año     | 0-11 meses |
| 1-5    | 1-5 años    | 1-5 años |
| 6-10   | 6-10 años   | 6-10 años |
| 11-20  | 11-20 años  | 11-20 años |
| 21-30  | 21-30 años  | 21-30 años |  
| 31-40  | 31-40 años  | 31-40 años |
| 41-50  | 41-50 años  | 41-50 años |
| 51-59  | 51-59 años  | 51-59 años |
| 60+    | 60+ años    | 60+ años |

## Vistas del Dashboard

1. **📊 Resumen**: Métricas principales y distribución por edad
2. **📅 Temporal**: Evolución de vacunación individual vs barridos  
3. **🗺️ Geográfico**: Distribución por municipios
4. **🏘️ Poblacional**: Análisis de cobertura territorial

## Notas Técnicas

- Datos de población opcionales (dashboard funciona sin ellos)
- Consolidación automática de rangos 60-69 y 70+ en "60+"
- Detección automática de columnas de barridos por secciones

---

**Secretaría de Salud del Tolima © 2025**