import streamlit as st
import psycopg2
import pandas as pd
import locale
import re

# Configuración de la localización para formateo de moneda
locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')

# Conexión a la base de datos PostgreSQL
def get_data_from_db():
    # Conexión a la base de datos PostgreSQL
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

# Función para validar si un enlace es una URL válida
def es_url_valido(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # esquema
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # dominio...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # dirección IP
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # dirección IPv6
        r'(?::\d+)?'  # puerto
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

# Cargar datos
data = get_data_from_db()

# Ajustar las imágenes en una fila: izquierda, centro, derecha
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.image("Logo_CCB_big.jpg", use_column_width=True)  # Imagen izquierda

with col2:
    st.image("localhost-logo.png", use_column_width=True)  # Imagen centro

with col3:
    st.image("p4sretina-resaltado-2-fotor-bg-remover-20241016223938.png", use_column_width=True)  # Imagen derecha

# Título de la aplicación debajo de las imágenes
st.title("Búsqueda de Locales Comerciales en Arriendo en Bogotá")

# Filtro de búsqueda por barrio
barrios_unicos = data['barrio'].unique()
barrio_seleccionado = st.selectbox("Selecciona un barrio:", ["Todos"] + list(barrios_unicos))

# Función para mostrar los locales comerciales
def mostrar_locales(data, barrio):
    # Filtrar locales por barrio si se selecciona uno específico
    if barrio != "Todos":
        data = data[data['barrio'] == barrio]

    # Filtrar los locales prioritarios
    prioritarios = data[data['prioridad'] == 1]
    no_prioritarios = data[data['prioridad'] != 1]

    # Mostrar locales prioritarios primero
    for idx, row in prioritarios.iterrows():
        st.markdown(
            f"""
            <div style="border: 4px solid gold; padding: 15px; margin-bottom: 20px; border-radius: 10px;">
                <h3>{row['barrio']}, {row['ciudad']}</h3>
                <img src="{row['fotolocal']}" style="width: 100%; height: auto;">
                <p><strong>Valor Arriendo:</strong> {locale.currency(row['valorarriendo'], grouping=True)}</p>
                <p><strong>Tamaño:</strong> {row['areacuadrada']} m²</p>
                {'<p><strong>Garajes:</strong> ' + str(row['garajes']) + '</p>' if row['garajes'] > 0 else ''}
                <p><strong>Baños:</strong> {row['banios']}</p>  <!-- Campo de baños añadido -->
                {f'<p><a href="{row["link"].strip()}" target="_blank" style="text-decoration: none;">Ver detalles</a></p>' if es_url_valido(row["link"].strip()) else "<p>Enlace no disponible</p>"}
                <p><a href="https://wa.me/+57{row['telefonocontacto'].strip()}" target="_blank" style="text-decoration: none;">Contactar vía WhatsApp</a></p>
                {f'<p><a href="https://www.google.com/maps/place/{row["coordenadas"].strip()}" target="_blank" style="text-decoration: none;">Ver en el mapa</a></p>' if row['coordenadas'] and ',' in row['coordenadas'] else ''}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Mostrar locales no prioritarios
    for idx, row in no_prioritarios.iterrows():
        st.markdown(
            f"""
            <div style="border: 4px solid gray; padding: 15px; margin-bottom: 20px; border-radius: 10px;">
                <h3>{row['barrio']}, {row['ciudad']}</h3>
                <img src="{row['fotolocal']}" style="width: 100%; height: auto;">
                <p><strong>Valor Arriendo:</strong> {locale.currency(row['valorarriendo'], grouping=True)}</p>
                <p><strong>Tamaño:</strong> {row['areacuadrada']} m²</p>
                {'<p><strong>Garajes:</strong> ' + str(row['garajes']) + '</p>' if row['garajes'] > 0 else ''}
                <p><strong>Baños:</strong> {row['banios']}</p>  <!-- Campo de baños añadido -->
                {f'<p><a href="{row["link"].strip()}" target="_blank" style="text-decoration: none;">Ver detalles</a></p>' if es_url_valido(row["link"].strip()) else "<p>Enlace no disponible</p>"}
                <p><a href="https://wa.me/+57{row['telefonocontacto'].strip()}" target="_blank" style="text-decoration: none;">Contactar vía WhatsApp</a></p>
                {f'<p><a href="https://www.google.com/maps/place/{row["coordenadas"].strip()}" target="_blank" style="text-decoration: none;">Ver en el mapa</a></p>' if row['coordenadas'] and ',' in row['coordenadas'] else ''}
            </div>
            """,
            unsafe_allow_html=True
        )

# Título principal
st.title("Locales Comerciales en Arriendo en Bogotá")

# Mostrar locales comerciales
mostrar_locales(data, barrio_seleccionado)
