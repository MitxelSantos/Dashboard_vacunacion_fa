import pandas as pd


def load_aseguramiento(path):
    df = pd.read_csv(path)
    df[["Codigo_Municipio", "Nombre_Municipio"]] = df["Municipio"].str.split(
        "-", n=1, expand=True
    )
    df["Codigo_Municipio"] = df["Codigo_Municipio"].str.strip()
    df["Nombre_Municipio"] = df["Nombre_Municipio"].str.strip().str.upper()
    df["EAPB"] = df["EAPB"].str.upper().str.strip()
    cols_totales = [
        "Subsidiado",
        "Contributivo",
        "Especial",
        "Excepcion",
        "Total",
        "Mes",
        "Año",
    ]
    for col in cols_totales:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
