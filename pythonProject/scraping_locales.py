# scraping_locales.py
import requests
from bs4 import BeautifulSoup
import psycopg2


# Función para hacer scraping de un portal
def obtener_datos_locales():
    url = "https://www.metrocuadrado.com/apartamentos/arriendo/bogota/"
    response = requests.get(url)
    print(response)
    soup = BeautifulSoup(response.text, 'html.parser')
    print(soup)
    locales = []
    for local in soup.find_all('div', class_='local-item'):
        ubicacion = local.find('div', class_='ubicacion').text.strip()
        precio = local.find('div', class_='precio').text.strip().replace("$", "").replace(",", "")
        tamanio = local.find('div', class_='tamanio').text.strip().replace("m²", "")
        descripcion = local.find('div', class_='descripcion').text.strip()

        locales.append((ubicacion, int(precio), int(tamanio), descripcion))

    return locales


# Guardar los datos en PostgreSQL
def guardar_en_base_de_datos(locales):
    conexion = psycopg2.connect(
        host="localhost",
        database="arrendamiento_comercial",
        user="postgres",
        password="123456"
    )
    cursor = conexion.cursor()

    query = "INSERT INTO locales_comerciales (ubicacion, precio, tamanio, descripcion) VALUES (%s, %s, %s, %s)"
    cursor.executemany(query, locales)

    conexion.commit()
    cursor.close()
    conexion.close()


if __name__ == "__main__":
    locales = obtener_datos_locales()
    guardar_en_base_de_datos(locales)