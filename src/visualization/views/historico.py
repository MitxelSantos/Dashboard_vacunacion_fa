import streamlit as st


def mostrar_historico(df, fecha_actualizacion):
    # TODO: Aquí va tu lógica visual original de histórico
    st.header("Evolución Histórica de la Vacunación")
    st.info(f"Datos actualizados hasta: {fecha_actualizacion.date()}")
    # KPIs, gráficos, tablas, imágenes, etc. que ya tenías:
    # ...
    # Ejemplo mínimo:
    if df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return
    df["Mes"] = df["Fecha_Aplicacion"].dt.to_period("M")
    evolucion = df.groupby("Mes").size().reset_index(name="Vacunados")
    st.line_chart(evolucion.set_index("Mes"))
