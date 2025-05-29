import streamlit as st


def mostrar_cobertura(df_aseg, df_vac, fecha_actualizacion):
    # TODO: Aquí va tu lógica visual original de cobertura
    st.header("Cobertura de Vacunación por Municipio y Aseguramiento")
    st.info(f"Vacunación actualizada hasta: {fecha_actualizacion.date()}")
    # KPIs, gráficos, tablas, imágenes, etc. que ya tenías:
    # ...
    # Ejemplo mínimo:
    if df_aseg.empty or df_vac.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return
    cobertura = df_vac.groupby("Municipio").size().reset_index(name="Vacunados")
    cobertura = cobertura.merge(
        df_aseg[["Codigo_Municipio", "Nombre_Municipio", "Total"]],
        left_on="Municipio",
        right_on="Nombre_Municipio",
        how="left",
    )
    cobertura["Cobertura_%"] = (
        cobertura["Vacunados"] / cobertura["Total"] * 100
    ).round(2)
    st.dataframe(
        cobertura[["Municipio", "Vacunados", "Total", "Cobertura_%"]].sort_values(
            "Cobertura_%", ascending=False
        )
    )
