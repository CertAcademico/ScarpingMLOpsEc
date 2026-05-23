"""
Web Scraper Universal - Scraping de Cualquier Página Web
Tutorial flexible para extraer datos de cualquier sitio
"""

import requests
from bs4 import BeautifulSoup
import time

def scraping_basico(url):
    """
    Función básica para hacer scraping de cualquier URL
    """
    print("=" * 60)
    print(f"Scraping de: {url}")
    print("=" * 60)
    print()
    
    try:
        # Validar URL
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Headers para no parecer un bot
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print("📥 Descargando página...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("✓ Página descargada exitosamente\n")
        
        # Parsear HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. INFORMACIÓN BÁSICA
        print("📋 INFORMACIÓN BÁSICA DE LA PÁGINA")
        print("-" * 60)
        
        titulo = soup.find('title')
        print(f"Título: {titulo.string if titulo else 'N/A'}")
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            print(f"Descripción: {meta_desc.get('content', 'N/A')}")
        
        print()
        
        # 2. ENLACES (Links)
        print("🔗 ENLACES ENCONTRADOS")
        print("-" * 60)
        
        enlaces = soup.find_all('a', href=True, limit=10)
        print(f"Primeros {len(enlaces)} enlaces:\n")
        
        for i, enlace in enumerate(enlaces[:5], 1):
            texto = enlace.get_text(strip=True)[:40]
            href = enlace.get('href', 'N/A')
            print(f"{i}. {texto}")
            print(f"   URL: {href}\n")
        
        # 3. ENCABEZADOS
        print("📝 ENCABEZADOS (H1, H2, H3)")
        print("-" * 60)
        
        h1s = soup.find_all('h1', limit=5)
        h2s = soup.find_all('h2', limit=5)
        h3s = soup.find_all('h3', limit=5)
        
        if h1s:
            print("H1 encontrados:")
            for h1 in h1s:
                print(f"  - {h1.get_text(strip=True)[:60]}")
        
        if h2s:
            print("\nH2 encontrados:")
            for h2 in h2s[:3]:
                print(f"  - {h2.get_text(strip=True)[:60]}")
        
        if h3s:
            print("\nH3 encontrados:")
            for h3 in h3s[:3]:
                print(f"  - {h3.get_text(strip=True)[:60]}")
        
        print()
        
        # 4. IMÁGENES
        print("🖼️ IMÁGENES")
        print("-" * 60)
        
        imagenes = soup.find_all('img', limit=5)
        print(f"Total de imágenes encontradas: {len(soup.find_all('img'))}")
        print(f"Mostrando las primeras {len(imagenes)}:\n")
        
        for i, img in enumerate(imagenes, 1):
            alt = img.get('alt', 'Sin descripción')
            src = img.get('src', 'N/A')
            print(f"{i}. {alt[:40]}")
            print(f"   URL: {src[:60]}...\n")
        
        # 5. PÁRRAFOS
        print("📄 PÁRRAFOS (primeros 3)")
        print("-" * 60)
        
        parrafos = soup.find_all('p', limit=3)
        for i, p in enumerate(parrafos, 1):
            texto = p.get_text(strip=True)[:100]
            print(f"{i}. {texto}...\n")
        
        # 6. LISTAS
        print("📋 LISTAS (UL/OL)")
        print("-" * 60)
        
        listas = soup.find_all(['ul', 'ol'], limit=2)
        
        for lista in listas[:1]:
            items = lista.find_all('li', limit=5)
            print(f"Lista con {len(lista.find_all('li'))} items:\n")
            for item in items:
                print(f"  • {item.get_text(strip=True)[:60]}")
            print()
        
        # 7. TABLAS
        print("📊 TABLAS")
        print("-" * 60)
        
        tablas = soup.find_all('table')
        if tablas:
            print(f"Total de tablas: {len(tablas)}\n")
            
            tabla = tablas[0]
            headers = tabla.find_all('th')
            if headers:
                print("Encabezados:")
                for header in headers[:5]:
                    print(f"  | {header.get_text(strip=True)[:20]}", end="")
                print(" |")
            
            filas = tabla.find_all('tr', limit=3)
            for fila in filas[1:3]:
                celdas = fila.find_all('td')
                for celda in celdas[:5]:
                    print(f"  | {celda.get_text(strip=True)[:20]}", end="")
                print(" |")
        else:
            print("No se encontraron tablas")
        
        print()
        
        # 8. ESTADÍSTICAS
        print("📊 ESTADÍSTICAS DE LA PÁGINA")
        print("-" * 60)
        
        todas_las_etiquetas = soup.find_all()
        print(f"Total de etiquetas: {len(todas_las_etiquetas)}")
        print(f"Total de enlaces: {len(soup.find_all('a'))}")
        print(f"Total de imágenes: {len(soup.find_all('img'))}")
        print(f"Total de párrafos: {len(soup.find_all('p'))}")
        print(f"Total de encabezados: {len(soup.find_all(['h1','h2','h3','h4','h5','h6']))}")
        print(f"Total de divs: {len(soup.find_all('div'))}")
        print(f"Total de listas: {len(soup.find_all(['ul', 'ol']))}")
        print()
        
    except requests.exceptions.MissingSchema:
        print("❌ Error: URL inválida. Asegúrate de incluir https:// o http://")
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar. Verifica tu conexión a internet")
    except requests.exceptions.Timeout:
        print("❌ Error: La conexión tardó demasiado (timeout)")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e.response.status_code}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    print("=" * 60)
    print()


def scraping_avanzado(url, selector_css=None):
    """
    Scraping avanzado con selectores CSS personalizados
    """
    print("=" * 60)
    print(f"SCRAPING AVANZADO: {url}")
    print("=" * 60)
    print()
    
    try:
        if not url.startswith('http'):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        if selector_css:
            print(f"Buscando elementos con selector: {selector_css}\n")
            elementos = soup.select(selector_css, limit=10)
            
            print(f"✓ Se encontraron {len(elementos)} elementos\n")
            
            for i, elemento in enumerate(elementos, 1):
                print(f"Elemento {i}:")
                print(f"  Etiqueta: {elemento.name}")
                print(f"  Clase: {elemento.get('class', 'N/A')}")
                print(f"  ID: {elemento.get('id', 'N/A')}")
                print(f"  Texto: {elemento.get_text(strip=True)[:60]}")
                print()
        else:
            print("Por favor proporciona un selector CSS")
            print("\nEjemplos de selectores:")
            print("  '.nombre-clase'     - Por clase")
            print("  '#id-elemento'      - Por ID")
            print("  'div.contenedor'    - Por etiqueta y clase")
            print("  'a[href]'           - Por atributo")
            print("  'li:first-child'    - Con pseudo-selector")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("=" * 60)
    print()


# ============================================
# MENÚ INTERACTIVO
# ============================================

def mostrar_menu():
    """Mostrar menú de opciones"""
    print("\n" + "=" * 60)
    print("🌐 WEB SCRAPER UNIVERSAL - MENÚ")
    print("=" * 60)
    print("1. Scraping Básico de cualquier página")
    print("2. Scraping Avanzado (con selectores CSS)")
    print("3. Ejemplos predefinidos")
    print("4. Salir")
    print("=" * 60)
    return input("Elige una opción (1-4): ").strip()


def ejemplos_predefinidos():
    """Mostrar ejemplos de sitios disponibles"""
    ejemplos = {
        '1': ('https://quotes.toscrape.com', 'Citas'),
        '2': ('https://books.toscrape.com', 'Libros'),
        '3': ('https://github.com/trending', 'GitHub Trending'),
        '4': ('https://news.ycombinator.com', 'Hacker News'),
        '5': ('https://httpbin.org/html', 'HTML de prueba'),
    }
    
    print("\n" + "=" * 60)
    print("📚 EJEMPLOS PREDEFINIDOS")
    print("=" * 60)
    for key, (url, nombre) in ejemplos.items():
        print(f"{key}. {nombre} - {url}")
    print("=" * 60)
    
    opcion = input("Elige un ejemplo (1-5): ").strip()
    
    if opcion in ejemplos:
        url, nombre = ejemplos[opcion]
        print(f"\nCargando {nombre}...")
        time.sleep(1)
        scraping_basico(url)
    else:
        print("❌ Opción inválida")


# ============================================
# PROGRAMA PRINCIPAL
# ============================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "    🌐 WEB SCRAPER UNIVERSAL CON BEAUTIFULSOUP4".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    while True:
        opcion = mostrar_menu()
        
        if opcion == '1':
            url = input("\nIngresa la URL (ejemplo: google.com o https://google.com): ").strip()
            if url:
                scraping_basico(url)
            else:
                print("❌ URL vacía")
        
        elif opcion == '2':
            url = input("\nIngresa la URL: ").strip()
            selector = input("Ingresa el selector CSS (ejemplo: .producto o #contenido): ").strip()
            if url and selector:
                scraping_avanzado(url, selector)
            else:
                print("❌ URL o selector vacío")
        
        elif opcion == '3':
            ejemplos_predefinidos()
        
        elif opcion == '4':
            print("\n👋 ¡Hasta pronto!")
            break
        
        else:
            print("❌ Opción inválida. Intenta de nuevo.")
        
        input("\nPresiona ENTER para continuar...")
