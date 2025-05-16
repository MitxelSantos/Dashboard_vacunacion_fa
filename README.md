# Dashboard de Vacunación - Fiebre Amarilla del Tolima

Dashboard interactivo para el análisis de la vacunación contra la fiebre amarilla en el departamento del Tolima.

## Estructura de archivos necesarios

Para que el dashboard funcione correctamente, asegúrate de tener los siguientes archivos:

1. `data/POBLACION.xlsx`: Archivo Excel con la población de cada municipio del Tolima según DANE y SISBEN
   - Debe contener una hoja llamada "Poblacion"
   - Columnas requeridas: DPMP (municipio), SISBEN, DANE, CODMUN/DIVIPOLA/COD DANE

2. `data/vacunacion_fa.csv`: Archivo CSV con los datos de vacunación de fiebre amarilla
   - Columnas requeridas: IdPaciente, TipoIdentificacion, Documento, PrimerNombre, PrimerApellido, Sexo, 
     FechaNacimiento, NombreMunicipioNacimiento, NombreDptoNacimiento, NombreMunicipioResidencia, 
     NombreDptoResidencia, GrupoEtnico, Desplazado, Discapacitado, RegimenAfiliacion, NombreAseguradora, 
     FA UNICA, Edad_Vacunacion, Grupo_Edad

3. `assets/images/logo_gobernacion.png`: Logo de la Gobernación del Tolima

## Instalación y ejecución

1. Clona este repositorio:

git clone https://github.com/jose-santos/dashboard-vacunacion-fa.git
cd dashboard-vacunacion-fa

2. Crea un entorno virtual e instala las dependencias:

python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

3. Coloca los archivos de datos en la carpeta `data/`

4. Ejecuta la aplicación:

streamlit run app.py

## Despliegue en producción

Para desplegar la aplicación en Streamlit Cloud:

1. Sube este repositorio a GitHub
2. Inicia sesión en [Streamlit Cloud](https://streamlit.io/cloud)
3. Haz clic en "New app" y selecciona tu repositorio
4. Configura las opciones de despliegue:
- Main file path: app.py
- Python version: 3.9
5. Haz clic en "Deploy"

## Notas importantes

- Asegúrate de que las carpetas `data/` y `assets/images/` existan y contengan los archivos necesarios
- No se incluyen datos de ejemplo por razones de privacidad y confidencialidad

