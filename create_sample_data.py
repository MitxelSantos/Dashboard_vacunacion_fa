"""
create_sample_data.py
Generador de datos de muestra para probar el dashboard
Útil cuando no se tienen los archivos de datos reales
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import random


def create_sample_vaccination_data(n_records=5000):
    """
    Crea datos de vacunación de muestra
    """
    np.random.seed(42)  # Para reproducibilidad

    # Municipios del Tolima
    municipios_tolima = [
        "IBAGUÉ",
        "ESPINAL",
        "HONDA",
        "MELGAR",
        "GIRARDOT",
        "CHAPARRAL",
        "LÍBANO",
        "PURIFICACIÓN",
        "MARIQUITA",
        "ARMERO",
        "CAJAMARCA",
        "FRESNO",
        "ROVIRA",
        "FLANDES",
        "GUAMO",
        "SALDAÑA",
        "NATAGAIMA",
        "ORTEGA",
        "DOLORES",
        "ALPUJARRA",
        "ALVARADO",
        "AMBALEMA",
        "ANZOÁTEGUI",
        "ATACO",
        "COELLO",
        "COYAIMA",
        "CUNDAY",
        "FALAN",
        "HERVEO",
        "ICONONZO",
        "LÉRIDA",
        "MURILLO",
        "PALOCABILDO",
        "PIEDRAS",
        "PLANADAS",
        "PRADO",
        "RIOBLANCO",
        "RONCESVALLES",
        "SAN ANTONIO",
        "SAN LUIS",
        "SANTA ISABEL",
        "SUÁREZ",
        "VALLE DE SAN JUAN",
        "VENADILLO",
        "VILLAHERMOSA",
        "VILLARRICA",
        "CASABIANCA",
    ]

    # EAPBs comunes
    eapbs = [
        "NUEVA EPS",
        "SALUD TOTAL",
        "SANITAS",
        "SURA",
        "FAMISANAR",
        "COOMEVA",
        "MEDIMÁS",
        "CAPITAL SALUD",
        "EMSSANAR",
        "COMFENALCO",
        "AIC",
        "MUTUAL SER",
        "ECOOPSOS",
        "COMFAMILIAR HUILA",
    ]

    # Grupos étnicos
    grupos_etnicos = [
        "Mestizo",
        "Indígena",
        "Afrodescendiente",
        "Blanco",
        "Gitano",
        "Sin dato",
    ]

    # Generar datos
    data = []

    # Fecha de inicio y fin para generar fechas aleatorias
    fecha_inicio = datetime(2023, 1, 1)
    fecha_fin = datetime(2024, 12, 31)

    for i in range(n_records):
        # Fecha de nacimiento (edades entre 1 y 85 años)
        edad_anos = np.random.randint(1, 86)
        fecha_nacimiento = datetime.now() - timedelta(
            days=edad_anos * 365 + np.random.randint(0, 365)
        )

        # Fecha de vacunación
        fecha_vacunacion = fecha_inicio + timedelta(
            days=np.random.randint(0, (fecha_fin - fecha_inicio).days)
        )

        # Sexo con distribución realista
        sexo = np.random.choice(["Masculino", "Femenino"], p=[0.48, 0.52])

        # Municipio con distribución ponderada (Ibagué más probable)
        if np.random.random() < 0.3:
            municipio = "IBAGUÉ"
        else:
            municipio = np.random.choice(municipios_tolima[1:])

        # EAPB con distribución ponderada
        eapb = np.random.choice(
            eapbs,
            p=[
                0.25,
                0.15,
                0.12,
                0.1,
                0.08,
                0.06,
                0.05,
                0.04,
                0.04,
                0.03,
                0.02,
                0.02,
                0.02,
                0.02,
            ],
        )

        # Régimen basado en EAPB
        if eapb in ["NUEVA EPS", "MEDIMÁS", "EMSSANAR"]:
            regimen = "Subsidiado"
        elif eapb in ["SALUD TOTAL", "SANITAS", "SURA"]:
            regimen = "Contributivo"
        else:
            regimen = np.random.choice(["Contributivo", "Subsidiado"], p=[0.6, 0.4])

        # Grupo étnico
        grupo_etnico = np.random.choice(
            grupos_etnicos, p=[0.75, 0.08, 0.10, 0.05, 0.01, 0.01]
        )

        # Determinar grupo de edad
        if edad_anos < 1:
            grupo_edad = "Menor de 1 año"
        elif edad_anos <= 4:
            grupo_edad = "1 a 4 años"
        elif edad_anos <= 9:
            grupo_edad = "5 a 9 años"
        elif edad_anos <= 19:
            grupo_edad = "10 a 19 años"
        elif edad_anos <= 29:
            grupo_edad = "20 a 29 años"
        elif edad_anos <= 39:
            grupo_edad = "30 a 39 años"
        elif edad_anos <= 49:
            grupo_edad = "40 a 49 años"
        elif edad_anos <= 59:
            grupo_edad = "50 a 59 años"
        elif edad_anos <= 69:
            grupo_edad = "60 a 69 años"
        else:
            grupo_edad = "70 años o más"

        record = {
            "IdPaciente": f"PAC{i+1:06d}",
            "TipoIdentificacion": np.random.choice(
                ["CC", "TI", "RC"], p=[0.8, 0.15, 0.05]
            ),
            "Documento": f"{np.random.randint(10000000, 99999999)}",
            "PrimerNombre": f"Nombre{i+1}",
            "PrimerApellido": f"Apellido{i+1}",
            "Sexo": sexo,
            "FechaNacimiento": fecha_nacimiento,
            "NombreMunicipioNacimiento": municipio,
            "NombreDptoNacimiento": "TOLIMA",
            "NombreMunicipioResidencia": municipio,
            "NombreDptoResidencia": "TOLIMA",
            "GrupoEtnico": grupo_etnico,
            "Desplazado": np.random.choice(["No", "Sí"], p=[0.92, 0.08]),
            "Discapacitado": np.random.choice(["No", "Sí"], p=[0.95, 0.05]),
            "RegimenAfiliacion": regimen,
            "NombreAseguradora": eapb,
            "FA UNICA": fecha_vacunacion,
            "Edad_Vacunacion": edad_anos,
            "Grupo_Edad": grupo_edad,
        }

        data.append(record)

    return pd.DataFrame(data)


def create_sample_population_data():
    """
    Crea datos de población por EAPB de muestra
    """
    municipios_tolima = [
        "IBAGUÉ",
        "ESPINAL",
        "HONDA",
        "MELGAR",
        "GIRARDOT",
        "CHAPARRAL",
        "LÍBANO",
        "PURIFICACIÓN",
        "MARIQUITA",
        "ARMERO",
        "CAJAMARCA",
        "FRESNO",
        "ROVIRA",
        "FLANDES",
        "GUAMO",
        "SALDAÑA",
        "NATAGAIMA",
        "ORTEGA",
        "DOLORES",
        "ALPUJARRA",
    ]

    eapbs = [
        "NUEVA EPS",
        "SALUD TOTAL",
        "SANITAS",
        "SURA",
        "FAMISANAR",
        "COOMEVA",
        "MEDIMÁS",
        "CAPITAL SALUD",
        "EMSSANAR",
        "COMFENALCO",
    ]

    data = []

    for municipio in municipios_tolima:
        # Población base del municipio (Ibagué más grande)
        if municipio == "IBAGUÉ":
            poblacion_base = np.random.randint(80000, 120000)
        elif municipio in ["ESPINAL", "HONDA", "MELGAR"]:
            poblacion_base = np.random.randint(15000, 25000)
        else:
            poblacion_base = np.random.randint(3000, 15000)

        for eapb in eapbs:
            # Distribución por EAPB
            if eapb == "NUEVA EPS":
                porcentaje = np.random.uniform(0.20, 0.35)
            elif eapb in ["SALUD TOTAL", "SANITAS"]:
                porcentaje = np.random.uniform(0.08, 0.15)
            else:
                porcentaje = np.random.uniform(0.02, 0.08)

            total = int(poblacion_base * porcentaje)

            # Distribución por régimen
            if eapb in ["NUEVA EPS", "MEDIMÁS"]:
                subsidiado = int(total * 0.8)
                contributivo = int(total * 0.18)
                especial = int(total * 0.015)
                excepcion = total - subsidiado - contributivo - especial
            else:
                contributivo = int(total * 0.7)
                subsidiado = int(total * 0.25)
                especial = int(total * 0.03)
                excepcion = total - subsidiado - contributivo - especial

            record = {
                "Municipio": f"{np.random.randint(1, 48):03d} - {municipio}",
                "EAPB": eapb,
                "Subsidiado": subsidiado,
                "Contributivo": contributivo,
                "Especial": especial,
                "Excepcion": excepcion,
                "Total": total,
                "Mes": 4,
                "Año": 2025,
            }

            data.append(record)

    return pd.DataFrame(data)


def create_sample_brigades_data():
    """
    Crea datos de brigadas de emergencia de muestra
    """
    municipios = ["IBAGUÉ", "ESPINAL", "HONDA", "MELGAR", "CHAPARRAL", "LÍBANO"]
    veredas = [
        "Centro",
        "La Esperanza",
        "El Progreso",
        "San José",
        "Las Flores",
        "Villa Nueva",
        "El Carmen",
        "Santa Rosa",
        "La Libertad",
        "Buenos Aires",
    ]

    data = []

    # Generar 50 brigadas
    for i in range(50):
        fecha = datetime(2024, 9, 1) + timedelta(days=np.random.randint(0, 120))
        municipio = np.random.choice(municipios)
        vereda = np.random.choice(veredas)

        # Datos realistas de brigada
        tpe = np.random.randint(20, 150)  # Total población encontrada
        tpvp = int(tpe * np.random.uniform(0.1, 0.4))  # Ya vacunados
        tpnvp = int(tpe * np.random.uniform(0.05, 0.2))  # No vacunados
        tpvb = max(0, tpe - tpvp - tpnvp)  # Vacunados por brigada

        efectivas = np.random.randint(15, min(50, tpvb + 10))
        no_efectivas = np.random.randint(2, 15)
        fallidas = np.random.randint(0, 8)
        casa_renuente = np.random.randint(0, 10)

        record = {
            "FECHA": fecha,
            "MUNICIPIO": municipio,
            "VEREDAS": vereda,
            "Efectivas (E)": efectivas,
            "No Efectivas (NE)": no_efectivas,
            "Fallidas (F)": fallidas,
            "Casa renuente": casa_renuente,
            "TPE": tpe,
            "TPVP": tpvp,
            "TPNVP": tpnvp,
            "TPVB": tpvb,
            "< 1 AÑO": np.random.poisson(2),
            "1-5 AÑOS": np.random.poisson(8),
            "6-10 AÑOS": np.random.poisson(12),
            "11-20 AÑOS": np.random.poisson(15),
            "21-30 AÑOS": np.random.poisson(20),
            "31-40 AÑOS": np.random.poisson(18),
            "41-50 AÑOS": np.random.poisson(16),
            "51-59 AÑOS": np.random.poisson(12),
            "60 Y MAS": np.random.poisson(10),
        }

        data.append(record)

    return pd.DataFrame(data)


def create_all_sample_files():
    """
    Crea todos los archivos de muestra necesarios
    """
    # Crear directorio data si no existe
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    print("🔄 Creando archivos de datos de muestra...")

    try:
        # 1. Datos de vacunación histórica
        print("📊 Creando datos de vacunación histórica...")
        df_vacunacion = create_sample_vaccination_data(5000)
        df_vacunacion.to_csv(data_dir / "vacunacion_fa.csv", index=False)
        print(
            f"✅ Creado: {data_dir / 'vacunacion_fa.csv'} ({len(df_vacunacion)} registros)"
        )

        # 2. Datos de población por EAPB
        print("📊 Creando datos de población por EAPB...")
        df_poblacion = create_sample_population_data()
        df_poblacion.to_excel(data_dir / "Poblacion_aseguramiento.xlsx", index=False)
        print(
            f"✅ Creado: {data_dir / 'Poblacion_aseguramiento.xlsx'} ({len(df_poblacion)} registros)"
        )

        # 3. Datos de brigadas de emergencia
        print("📊 Creando datos de brigadas de emergencia...")
        df_brigadas = create_sample_brigades_data()

        # Crear archivo Excel con hoja específica
        with pd.ExcelWriter(data_dir / "Resumen.xlsx") as writer:
            df_brigadas.to_excel(writer, sheet_name="Vacunacion", index=False)

        print(f"✅ Creado: {data_dir / 'Resumen.xlsx'} ({len(df_brigadas)} registros)")

        print("\n🎉 ¡Todos los archivos de muestra han sido creados exitosamente!")
        print(f"📁 Archivos creados en el directorio: {data_dir.absolute()}")

        # Mostrar resumen
        print("\n📋 Resumen de archivos creados:")
        for file_path in [
            data_dir / "vacunacion_fa.csv",
            data_dir / "Poblacion_aseguramiento.xlsx",
            data_dir / "Resumen.xlsx",
        ]:
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"  ✅ {file_path.name} ({size_mb:.2f} MB)")

        return True

    except Exception as e:
        print(f"❌ Error creando archivos de muestra: {str(e)}")
        return False


if __name__ == "__main__":
    success = create_all_sample_files()

    if success:
        print("\n🚀 ¡Ahora puedes ejecutar el dashboard con:")
        print("   streamlit run app.py")
    else:
        print("\n❌ Hubo errores creando los archivos de muestra")
