import pandas as pd


def normalize_municipality_names(df, col="Municipio"):
    df[col] = df[col].str.upper().str.strip()
    return df


def clean_dates(df, date_cols):
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def clean_age(df, birth_col, ref_date=None, new_col="Edad"):
    if ref_date is None:
        ref_date = pd.Timestamp.today()
    df[new_col] = (
        (ref_date - pd.to_datetime(df[birth_col], errors="coerce")).dt.days // 365
    ).astype("Int64")
    return df


def apply_filters(df, filters):
    for col, val in filters.items():
        df = df[df[col] == val]
    return df
