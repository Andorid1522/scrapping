import time
import csv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def setup_driver(headless=True):
    """
    Configura y devuelve una instancia de WebDriver para Chrome utilizando webdriver-manager.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")  # Ejecutar en modo headless (sin interfaz gráfica)
    options.add_argument("--disable-gpu")  # Deshabilitar la aceleración por GPU
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument("--disable-dev-shm-usage")  # Soluciona problemas en algunos entornos
    options.add_argument("--window-size=1920,1080")  # Definir el tamaño de la ventana
    options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Evita mensajes de automatización
    options.add_experimental_option('useAutomationExtension', False)  # Evita extensiones de automatización

    # Inicializar el WebDriver con webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Evitar la detección de Selenium
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

def get_coordinates_nominatim(ciudad, localidad, barrio):
    """
    Obtiene las coordenadas geográficas (latitud y longitud) usando Nominatim de OpenStreetMap.
    """
    direccion = f"{barrio}, {localidad}, {ciudad}, Colombia"
    geocode_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': direccion,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; TuNombre/1.0; tuemail@example.com)'  # Reemplaza con tu información
    }
    try:
        response = requests.get(geocode_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if len(data) > 0:
            latitud = data[0]['lat']
            longitud = data[0]['lon']
            return latitud, longitud
        else:
            print(f"No se encontraron coordenadas para la dirección: {direccion}")
            return 'N/A', 'N/A'
    except Exception as e:
        print(f"Error al obtener coordenadas para {direccion}: {e}")
        return 'N/A', 'N/A'

def scrape_properties(headless=True, num_pages=5):
    """
    Realiza el scraping de las propiedades en las primeras 'num_pages' páginas y guarda los datos en un CSV.
    """
    driver = setup_driver(headless=headless)
    base_url = "https://www.ciencuadras.com/arriendo/bogota/local?q=bogota&page={}"

    properties = []
    failed_addresses = []

    for page in range(1, num_pages + 1):
        url = base_url.format(page)
        print(f"Scraping página {page}: {url}")
        driver.get(url)

        try:
            # Esperar a que se carguen los elementos
            WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ciencuadras-card"))
            )
        except Exception as e:
            print(f"Error al esperar elementos en la página {page}: {e}")
            print("Contenido de la página:")
            print(driver.page_source)  # Imprime el HTML para verificar
            continue  # Pasar a la siguiente página
        
        time.sleep(2)  # Esperar un poco más para asegurar que se cargue todo
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extraer tarjetas de propiedades
        cards = soup.find_all('ciencuadras-card')
        
        if not cards:
            print(f"No se encontraron propiedades en la página {page}. Verifica los selectores o la estructura de la página.")
            print("Contenido de la página:")
            print(driver.page_source)  # Imprimir el HTML completo para verificar
            continue  # Pasar a la siguiente página

        for card in cards:
            # Nombre y ubicación
            location_label = card.find('span', class_='card__location-label')
            if location_label:
                ubicacion = location_label.text.strip()
                partes = [parte.strip() for parte in ubicacion.split(',')]
                if len(partes) >= 4:
                    # Asumiendo que la última parte es "Colombia" y la penúltima es la ciudad
                    ciudad = partes[-2]
                    localidad = partes[-3]
                    barrio = ', '.join(partes[:-3])
                elif len(partes) == 3:
                    ciudad = partes[-1]
                    localidad = partes[-2]
                    barrio = partes[0]
                elif len(partes) == 2:
                    ciudad = partes[-1]
                    localidad = partes[-2]
                    barrio = 'N/A'
                else:
                    ciudad = localidad = barrio = 'N/A'
            else:
                ciudad = localidad = barrio = 'N/A'

            # Nombre (asume que 'p' tag con class 'card__location' tiene más info)
            nombre_tag = card.find('p', class_='card__location')
            nombre = nombre_tag.text.strip() if nombre_tag else 'N/A'

            # Precio
            precio_tag = card.find('span', class_='card__price-big')
            precio = precio_tag.text.strip() if precio_tag else 'N/A'

            # Imagen
            img_tag = card.find('img')
            imagen = img_tag['src'] if img_tag and 'src' in img_tag.attrs else 'N/A'

            # Tipo de Propiedad
            if 'oficina' in nombre.lower():
                tipo_propiedad = 'Oficina'
            elif 'local' in nombre.lower():
                tipo_propiedad = 'Local'
            else:
                tipo_propiedad = 'Otro'
                
                # Extraer el tamaño en m2
            specs_results = card.find('ciencuadras-specs-results')
            if specs_results:
                specs_div = specs_results.find('div', class_='specs')
                if specs_div:
                    tamano_tag = specs_div.find('p')  
                    if tamano_tag:
                        span_tamano = tamano_tag.find('span')
                        tamano = span_tamano.text.strip() if span_tamano else 'N/A'
                    else:
                        tamano = 'N/A'
                else:
                    tamano = 'N/A'
            else:
                tamano = 'N/A'

            # Baños
            baños = 'N/A'
            specs = card.find('ciencuadras-specs-results')
            if specs:
                span_tags = specs.find_all('span')
                for span in span_tags:
                    texto = span.text.strip()
                    if texto.startswith('Baños'):
                        # Extraer el número después de 'Baños'
                        baños = texto.replace('Baños', '').strip()
                        break

            # Obtener coordenadas
            if barrio != 'N/A' and localidad != 'N/A' and ciudad != 'N/A':
                latitud, longitud = get_coordinates_nominatim(ciudad, localidad, barrio)
                if latitud == 'N/A' or longitud == 'N/A':
                    failed_addresses.append(f"{barrio}, {localidad}, {ciudad}, Colombia")
                time.sleep(1)  # Esperar 1 segundo entre solicitudes para evitar sobrecargar la API
            else:
                latitud = longitud = 'N/A'

            # Colectar información en un diccionario
            properties.append({
                'Nombre': nombre,                
                'Precio': precio,
                'Tamaño': tamano,
                'Imagen': imagen,
                'Ciudad': ciudad,
                'Localidad': localidad,
                'Barrio': barrio,
                'Baños': baños,
                'Tipo': tipo_propiedad,
                'Latitud': latitud,
                'Longitud': longitud
            })

    driver.quit()

    if not properties:
        print("No se encontraron propiedades en las páginas especificadas.")
        return

    # Guardar en CSV
    csv_file = 'propiedades_arriendo.csv'
    fieldnames = ['Nombre', 'Precio', 'Tamaño', 'Imagen', 'Ciudad', 'Localidad', 'Barrio', 'Baños', 'Tipo', 'Latitud', 'Longitud']

    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for prop in properties:
                writer.writerow(prop)
        print(f"Datos guardados en '{csv_file}'. Total propiedades: {len(properties)}")
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")

    # Guardar direcciones fallidas
    if failed_addresses:
        with open('direcciones_fallidas.txt', 'w', encoding='utf-8') as f:
            for address in failed_addresses:
                f.write(address + '\n')
        print(f"Direcciones fallidas guardadas en 'direcciones_fallidas.txt'")

    # Imprimir algunas propiedades
    for prop in properties[:5]:  # Imprimir las primeras 5 para verificar
        print(prop)

if __name__ == "__main__":
    # Ejecutar con headless=False para ver el navegador durante la depuración
    scrape_properties(headless=False, num_pages=5)

