import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import locale

# Configuración de la página (nombre de pestaña, ícono y layout)
st.set_page_config(
    page_title="Donde las ideas cobran vida",
    page_icon="localhost-logo.png",  # Ruta de la imagen que quieres usar como ícono
    layout="wide"  # Cambia a "centered" si prefieres un layout centrado
)

# Configuración para formato de moneda
locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')

# Conexión a la base de datos PostgreSQL
def get_data_from_db():
    conn = psycopg2.connect(
        host="localhost",
        database="arrendamiento_comercial",
        user="postgres",
        password="123456"
    )
    query = "SELECT * FROM locales_comerciales"
    data = pd.read_sql(query, conn)
    conn.close()
    return data

# Cargar datos
data = get_data_from_db()

# Título de la aplicación
st.title("Análisis de Locales Comerciales en Arriendo en Bogotá")

# CSS para alinear imágenes en la parte inferior y la imagen central centrada
st.markdown("""
    <style>
        .image-container {
            display: flex;
            justify-content: center;
            align-items: flex-end;
            height: 200px;  /* Ajusta esta altura para que las imágenes se alineen al borde inferior */
            margin-bottom: 10px;
        }
        .center-image-container {
            display: flex;
            justify-content: center;
            align-items: center; /* Asegura que la imagen central esté centrada vertical y horizontalmente */
            height: 200px;  /* Ajusta esta altura para que la imagen se centre */
        }
        img {
            max-width: 100%;
            max-height: 150px; /* Ajusta el tamaño máximo de las imágenes */
            object-fit: contain; /* Esto asegura que la imagen se ajuste sin distorsionarse */
        }
    </style>
""", unsafe_allow_html=True)

# Ajustar el layout de las imágenes: izquierda, centro resaltada, derecha
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown('<div class="image-container">', unsafe_allow_html=True)
    st.image("Logo_CCB_big.jpg", use_column_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="center-image-container">', unsafe_allow_html=True)
    st.image("localhost-logo.png", use_column_width=False, caption="Equipo Impacto")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="image-container">', unsafe_allow_html=True)
    st.image("p4sretina-resaltado-2-fotor-bg-remover-20241016223938.png", use_column_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

# Mostrar la tabla completa
st.subheader("Datos completos de locales comerciales")
st.dataframe(data)

# Función para descargar los datos en formato CSV
def descargar_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Botón para descargar el archivo CSV
csv = descargar_csv(data)
st.download_button(
    label="Descargar datos en CSV",
    data=csv,
    file_name="locales_comerciales.csv",
    mime="text/csv"
)

# Análisis 1: Precio promedio por barrio
st.subheader("Análisis del valor promedio de arriendo por barrio")
precios_barrio = data.groupby('barrio')['valorarriendo'].mean().reset_index()

# Ordenar los precios promedio de mayor a menor
precios_barrio = precios_barrio.sort_values(by='valorarriendo', ascending=False)

# Visualización de los precios promedio por barrio
fig_precios_barrio = px.bar(
    precios_barrio,
    x='barrio',
    y='valorarriendo',
    title="Valor promedio de arriendo por barrio (COP)",
    labels={'valorarriendo': 'Valor Arriendo (COP)'},
    text_auto=True
)
fig_precios_barrio.update_layout(
    yaxis_tickprefix='$',
    yaxis_tickformat=','
)
st.plotly_chart(fig_precios_barrio)

# Análisis 2: Distribución del tamaño de locales (área en m²)
st.subheader("Distribución del tamaño de locales (área en m²)")

# Filtrar valores nulos y erróneos
data_filtrada = data[data['areacuadrada'].notnull() & (data['areacuadrada'] >= 0)]

# Crear el histograma
fig_tamano = px.histogram(
    data_filtrada,
    x='areacuadrada',
    nbins=15,  # Ajustar el número de bins
    title="Distribución del tamaño de locales (área en m²)",
    labels={'areacuadrada': 'Área (m²)'},
    histnorm='percent'  # Normaliza el histograma para mostrar porcentajes
)

# Ajustar el rango de valores del eje x
fig_tamano.update_layout(
    xaxis_title='Área (m²)',
    yaxis_title='Porcentaje (%)',
    xaxis=dict(range=[data_filtrada['areacuadrada'].min(), data_filtrada['areacuadrada'].max()]),  # Ajustar rango del eje x
    yaxis=dict(tickformat='%')
)

st.plotly_chart(fig_tamano)


# Análisis 3: Tendencia de locales prioritarios
st.subheader("Tendencia de locales prioritarios")
prioritarios = data[data['prioridad'] == 1]
fig_prioritarios = px.scatter(
    prioritarios,
    x='barrio',
    y='valorarriendo',
    size='areacuadrada',
    color='ciudad',
    title="Locales prioritarios y sus valores de arriendo",
    labels={'valorarriendo': 'Valor Arriendo (COP)', 'areacuadrada': 'Tamaño (m²)'}
)
fig_prioritarios.update_layout(
    yaxis_tickprefix='$',
    yaxis_tickformat=','
)
st.plotly_chart(fig_prioritarios)

# Conclusiones o tendencias destacadas
st.markdown("""
**Tendencias destacadas:**
- Los barrios con los arriendos más altos están en zonas centrales.
- La mayoría de los locales tienen un área promedio entre 30 y 100 m².
- Los locales prioritarios suelen estar en barrios específicos y tienen un valor superior al promedio.
""")

# Función para mostrar insights adicionales
def mostrar_insights():
    num_locales = data.shape[0]
    valor_promedio = locale.currency(data['valorarriendo'].mean(), grouping=True)
    area_promedio = data['areacuadrada'].mean()
    locales_prioritarios = prioritarios.shape[0]

    st.markdown(f"**Total de locales comerciales:** {num_locales}")
    st.markdown(f"**Valor de arriendo promedio:** {valor_promedio}")
    st.markdown(f"**Tamaño promedio de los locales:** {area_promedio:.2f} m²")
    st.markdown(f"**Locales prioritarios:** {locales_prioritarios}")

# Mostrar insights adicionales
mostrar_insights()

