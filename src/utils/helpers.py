def configure_page(page_title, page_icon, layout="wide"):
    """
    Configura el estilo y el tema de la página.
    
    Args:
        page_title (str): Título de la página
        page_icon (str): Icono de la página
        layout (str): Diseño de la página ('wide' o 'centered')
    """
    # Configuración básica
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state="expanded"
    )
    
    # Cargar CSS personalizado
    css_path = Path(__file__).parent.parent.parent / "assets" / "styles" / "main.css"
    
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        # CSS básico en línea si no se encuentra el archivo
        st.markdown("""
        <style>
            /* Colores institucionales */
            :root {
                --primary-color: #7D0F2B;
                --secondary-color: #CFB53B;
                --accent-color: #215E8F;
                --background-color: #F5F5F5;
            }
            
            /* Estilos para la barra lateral */
            .sidebar .sidebar-content {
                background-color: #F8F9FA;
            }
            
            /* Estilos para títulos */
            h1, h2, h3 {
                color: var(--primary-color);
            }
            
            /* Botones primarios */
            .stButton>button {
                background-color: var(--primary-color);
                color: white;
            }
        </style>
        """, unsafe_allow_html=True)

def create_download_links(data, filters, fuente_poblacion):
    """
    Crea enlaces para descargar los datos filtrados en diferentes formatos.
    
    Args:
        data (dict): Diccionario con los dataframes
        filters (dict): Filtros aplicados
        fuente_poblacion (str): Fuente de datos de población seleccionada
    """
    from src.data.preprocessor import apply_filters
    import base64
    
    # Aplicar filtros
    filtered_data = apply_filters(data, filters, fuente_poblacion)
    
    # Crear enlace para CSV
    csv = filtered_data["metricas"].to_csv(index=False)
    b64_csv = base64.b64encode(csv.encode()).decode()
    href_csv = f'<a href="data:file/csv;base64,{b64_csv}" download="metricas_vacunacion_{fuente_poblacion}.csv">Descargar datos como CSV</a>'
    
    # Crear enlace para Excel
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    filtered_data["metricas"].to_excel(writer, sheet_name=f'Metricas_{fuente_poblacion}', index=False)
    filtered_data["vacunacion"].to_excel(writer, sheet_name='Vacunacion', index=False)
    writer.save()
    excel_data = output.getvalue()
    b64_excel = base64.b64encode(excel_data).decode()
    href_excel = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="datos_vacunacion_{fuente_poblacion}.xlsx">Descargar datos como Excel</a>'
    
    st.markdown("### Descargar datos filtrados")
    st.markdown(href_csv, unsafe_allow_html=True)
    st.markdown(href_excel, unsafe_allow_html=True)
    
    # Añadir información sobre los filtros aplicados
    filtros_aplicados = []
    for key, value in filters.items():
        if value != "Todos":
            filtros_aplicados.append(f"{key}: {value}")
    
    if filtros_aplicados:
        st.info(f"Filtros aplicados: {', '.join(filtros_aplicados)}")
    else:
        st.info("No hay filtros aplicados. Se muestran todos los datos.")
    
    st.info(f"Fuente de datos de población: {fuente_poblacion}")