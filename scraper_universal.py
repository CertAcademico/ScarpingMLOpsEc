"""
Web Scraper Universal - Scraping de Cualquier Página Web
Tutorial flexible para extraer datos de cualquier sitio
"""

import csv
import json
import time
import argparse
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


TIMEOUT_SEGUNDOS = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


def normalizar_url(url):
    """Completa y valida URLs escritas como dominio.com o www.dominio.com."""
    url = url.strip()
    if not url:
        raise ValueError("La URL está vacía")

    if not urlparse(url).scheme:
        url = "https://" + url

    partes = urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ValueError("URL inválida. Usa algo como https://ejemplo.com")

    return url


def crear_sesion():
    """Crea una sesión con reintentos para errores temporales."""
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.7,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# Sesión global reutilizada en todas las llamadas
_SESSION = None

def obtener_sesion():
    global _SESSION
    if _SESSION is None:
        _SESSION = crear_sesion()
    return _SESSION


def descargar_pagina(url):
    """Descarga una URL y devuelve response + BeautifulSoup si el contenido es HTML."""
    url = normalizar_url(url)
    session = obtener_sesion()
    response = session.get(url, timeout=TIMEOUT_SEGUNDOS, allow_redirects=True)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if "json" in content_type:
        return response.url, response, None, "json"
    if "html" not in content_type and "xml" not in content_type and response.text.strip().startswith(("{", "[")):
        return response.url, response, None, "json"

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "lxml")
    return response.url, response, soup, "html"


def texto_limpio(elemento, limite=80):
    texto = elemento.get_text(" ", strip=True) if elemento else ""
    return texto[:limite] if texto else "Sin texto visible"


def resolver_url(base_url, posible_url):
    if not posible_url:
        return "N/A"
    return urljoin(base_url, posible_url)


def imprimir_ayuda_sitios_modernos():
    print()
    print("Nota:")
    print("  Si la página muestra pocos datos, puede depender de JavaScript.")
    print("  BeautifulSoup solo lee el HTML inicial; para sitios React/Vue/Angular")
    print("  normalmente se necesita Playwright o Selenium.")


# ============================================
# EXPORTACIÓN DE DATOS
# ============================================

def exportar_resultados(datos, ruta_salida):
    """
    Exporta un dict de resultados a CSV o JSON según la extensión de ruta_salida.
    datos debe ser una lista de dicts (para CSV) o cualquier objeto serializable (para JSON).
    """
    if ruta_salida.endswith(".json"):
        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        print(f"Resultados guardados en: {ruta_salida}")

    elif ruta_salida.endswith(".csv"):
        if not datos:
            print("Sin datos para exportar.")
            return
        filas = datos if isinstance(datos, list) else [datos]
        campos = list(filas[0].keys())
        with open(ruta_salida, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(filas)
        print(f"Resultados guardados en: {ruta_salida} ({len(filas)} filas)")

    else:
        print(f"Formato no soportado: usa .json o .csv")


def recopilar_datos_pagina(url_final, soup):
    """Extrae los datos principales de una página y los devuelve como dict."""
    titulo = soup.find("title")
    meta_desc = soup.find("meta", attrs={"name": "description"})

    enlaces = [
        {
            "texto": texto_limpio(a, 80),
            "url": resolver_url(url_final, a.get("href")),
        }
        for a in soup.find_all("a", href=True, limit=10)
    ]

    encabezados = {
        "h1": [texto_limpio(h, 100) for h in soup.find_all("h1", limit=5)],
        "h2": [texto_limpio(h, 100) for h in soup.find_all("h2", limit=5)],
        "h3": [texto_limpio(h, 100) for h in soup.find_all("h3", limit=5)],
    }

    imagenes = [
        {
            "alt": img.get("alt", "Sin descripción")[:60],
            "src": resolver_url(url_final, img.get("src") or img.get("data-src")),
        }
        for img in soup.find_all("img", limit=10)
    ]

    parrafos = [texto_limpio(p, 200) for p in soup.find_all("p", limit=5)]

    stats = {
        "total_etiquetas": len(soup.find_all()),
        "total_enlaces": len(soup.find_all("a")),
        "total_imagenes": len(soup.find_all("img")),
        "total_parrafos": len(soup.find_all("p")),
        "total_encabezados": len(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])),
        "total_divs": len(soup.find_all("div")),
    }

    return {
        "url": url_final,
        "titulo": texto_limpio(titulo, 200) if titulo else "N/A",
        "descripcion": meta_desc.get("content", "N/A") if meta_desc else "N/A",
        "enlaces": enlaces,
        "encabezados": encabezados,
        "imagenes": imagenes,
        "parrafos": parrafos,
        "estadisticas": stats,
    }


def scraping_basico(url, salida=None):
    """
    Función básica para hacer scraping de cualquier URL.
    Si se indica salida (.json o .csv), exporta los resultados.
    """
    print("=" * 60)
    print(f"Scraping de: {url}")
    print("=" * 60)
    print()

    try:
        print("Descargando página...")
        url_final, response, soup, tipo = descargar_pagina(url)
        print(f"Página descargada exitosamente ({response.status_code})")
        if url_final != normalizar_url(url):
            print(f"URL final: {url_final}")
        print()

        if tipo == "json":
            datos = response.json()
            print("La URL devuelve JSON, no HTML.")
            if isinstance(datos, list):
                print(f"Elementos en la lista: {len(datos)}")
                print(f"Primer elemento: {datos[0] if datos else 'N/A'}")
            elif isinstance(datos, dict):
                print(f"Claves principales: {', '.join(list(datos.keys())[:10])}")
            if salida:
                exportar_resultados(datos, salida)
            print("=" * 60)
            print()
            return

        datos = recopilar_datos_pagina(url_final, soup)

        # Mostrar resultados en pantalla
        print("INFORMACIÓN BÁSICA DE LA PÁGINA")
        print("-" * 60)
        print(f"Título: {datos['titulo']}")
        if datos["descripcion"] != "N/A":
            print(f"Descripción: {datos['descripcion']}")
        print()

        print("ENLACES ENCONTRADOS")
        print("-" * 60)
        for i, enlace in enumerate(datos["enlaces"][:5], 1):
            print(f"{i}. {enlace['texto']}")
            print(f"   URL: {enlace['url']}\n")

        print("ENCABEZADOS (H1, H2, H3)")
        print("-" * 60)
        for nivel, items in datos["encabezados"].items():
            if items:
                print(f"{nivel.upper()} encontrados:")
                for texto in items[:3]:
                    print(f"  - {texto}")
                print()

        print("IMÁGENES")
        print("-" * 60)
        print(f"Total de imágenes: {datos['estadisticas']['total_imagenes']}")
        for i, img in enumerate(datos["imagenes"][:3], 1):
            print(f"{i}. {img['alt']}")
            print(f"   URL: {img['src'][:70]}\n")

        print("PÁRRAFOS (primeros 3)")
        print("-" * 60)
        for i, p in enumerate(datos["parrafos"][:3], 1):
            print(f"{i}. {p}...\n")

        print("ESTADÍSTICAS DE LA PÁGINA")
        print("-" * 60)
        for clave, valor in datos["estadisticas"].items():
            print(f"{clave.replace('_', ' ').capitalize()}: {valor}")

        imprimir_ayuda_sitios_modernos()

        if salida:
            exportar_resultados(datos, salida)

    except ValueError as e:
        print(f"Error: {e}")
    except requests.exceptions.ConnectionError:
        print("Error: No se pudo conectar. Verifica tu conexión a internet")
    except requests.exceptions.Timeout:
        print("Error: La conexión tardó demasiado (timeout)")
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e.response.status_code}")
        if e.response.status_code in (401, 403):
            print("  El sitio bloqueó la solicitud. Prueba otro sitio o usa una API oficial.")
        elif e.response.status_code == 404:
            print("  La página no existe o la URL está mal escrita.")
    except requests.exceptions.SSLError:
        print("Error SSL: el certificado del sitio no pudo validarse")
    except Exception as e:
        print(f"Error inesperado: {e}")

    print("=" * 60)
    print()


def scraping_avanzado(url, selector_css=None, salida=None):
    """
    Scraping avanzado con selectores CSS personalizados.
    Si se indica salida (.json o .csv), exporta los resultados.
    """
    print("=" * 60)
    print(f"SCRAPING AVANZADO: {url}")
    print("=" * 60)
    print()

    try:
        url_final, _, soup, tipo = descargar_pagina(url)

        if tipo == "json":
            print("La URL devuelve JSON. Usa scraping básico para ver sus claves.")
            print("=" * 60)
            print()
            return

        if selector_css:
            print(f"Buscando elementos con selector: {selector_css}\n")
            elementos_bs = soup.select(selector_css, limit=10)
            print(f"Se encontraron {len(elementos_bs)} elementos\n")

            resultados = []
            for i, elemento in enumerate(elementos_bs, 1):
                dato = {
                    "numero": i,
                    "etiqueta": elemento.name,
                    "clase": " ".join(elemento.get("class", [])) or "N/A",
                    "id": elemento.get("id", "N/A"),
                    "texto": texto_limpio(elemento, 100),
                }
                if elemento.name == "a":
                    dato["href"] = resolver_url(url_final, elemento.get("href"))
                if elemento.name == "img":
                    dato["src"] = resolver_url(url_final, elemento.get("src") or elemento.get("data-src"))

                resultados.append(dato)

                print(f"Elemento {i}:")
                print(f"  Etiqueta : {dato['etiqueta']}")
                print(f"  Clase    : {dato['clase']}")
                print(f"  ID       : {dato['id']}")
                print(f"  Texto    : {dato['texto']}")
                if "href" in dato:
                    print(f"  URL      : {dato['href']}")
                if "src" in dato:
                    print(f"  Imagen   : {dato['src']}")
                print()

            if salida:
                exportar_resultados(resultados, salida)

        else:
            print("Por favor proporciona un selector CSS")
            print("\nEjemplos de selectores:")
            print("  '.nombre-clase'     - Por clase")
            print("  '#id-elemento'      - Por ID")
            print("  'div.contenedor'    - Por etiqueta y clase")
            print("  'a[href]'           - Por atributo")
            print("  'li:first-child'    - Con pseudo-selector")

    except ValueError as e:
        print(f"Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
    except Exception as e:
        print(f"Error: {e}")

    print("=" * 60)
    print()


# ============================================
# MENÚ INTERACTIVO
# ============================================

def mostrar_menu():
    print("\n" + "=" * 60)
    print("WEB SCRAPER UNIVERSAL - MENÚ")
    print("=" * 60)
    print("1. Scraping Básico de cualquier página")
    print("2. Scraping Avanzado (con selectores CSS)")
    print("3. Ejemplos predefinidos")
    print("4. Salir")
    print("=" * 60)
    return input("Elige una opción (1-4): ").strip()


def pausar():
    try:
        input("\nPresiona ENTER para continuar...")
    except EOFError:
        pass


def ejemplos_predefinidos():
    ejemplos = {
        "1": ("https://quotes.toscrape.com", "Citas"),
        "2": ("https://books.toscrape.com", "Libros"),
        "3": ("https://github.com/trending", "GitHub Trending"),
        "4": ("https://news.ycombinator.com", "Hacker News"),
        "5": ("https://httpbin.org/html", "HTML de prueba"),
    }

    print("\n" + "=" * 60)
    print("EJEMPLOS PREDEFINIDOS")
    print("=" * 60)
    for key, (url, nombre) in ejemplos.items():
        print(f"{key}. {nombre} - {url}")
    print("=" * 60)

    opcion = input("Elige un ejemplo (1-5): ").strip()

    if opcion in ejemplos:
        url, nombre = ejemplos[opcion]
        salida = input("Guardar resultados en archivo? (ej: resultado.json, resultado.csv, o ENTER para omitir): ").strip() or None
        print(f"\nCargando {nombre}...")
        time.sleep(1)
        scraping_basico(url, salida=salida)
    else:
        print("Opción inválida")


def ejecutar_menu():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "    WEB SCRAPER UNIVERSAL CON BEAUTIFULSOUP4".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    while True:
        opcion = mostrar_menu()

        if opcion == "1":
            url = input("\nIngresa la URL (ejemplo: google.com o https://google.com): ").strip()
            salida = input("Guardar en archivo? (ej: resultado.json, resultado.csv, o ENTER para omitir): ").strip() or None
            if url:
                scraping_basico(url, salida=salida)
            else:
                print("URL vacía")

        elif opcion == "2":
            url = input("\nIngresa la URL: ").strip()
            selector = input("Ingresa el selector CSS (ejemplo: .producto o #contenido): ").strip()
            salida = input("Guardar en archivo? (ej: resultado.json, resultado.csv, o ENTER para omitir): ").strip() or None
            if url and selector:
                scraping_avanzado(url, selector, salida=salida)
            else:
                print("URL o selector vacío")

        elif opcion == "3":
            ejemplos_predefinidos()

        elif opcion == "4":
            print("\nHasta pronto!")
            break

        else:
            print("Opción inválida. Intenta de nuevo.")

        pausar()


def main():
    parser = argparse.ArgumentParser(
        description="Scraper universal con BeautifulSoup4",
        epilog=(
            "Ejemplos: "
            "python3 scraper_universal.py https://quotes.toscrape.com | "
            "python3 scraper_universal.py https://quotes.toscrape.com --output resultado.json | "
            "python3 scraper_universal.py https://books.toscrape.com --selector article.product_pod --output libros.csv"
        ),
    )
    parser.add_argument("url", nargs="?", help="URL para analizar, por ejemplo https://example.com")
    parser.add_argument("-s", "--selector", help="Selector CSS para scraping avanzado")
    parser.add_argument("-o", "--output", help="Archivo de salida: resultado.json o resultado.csv")
    args = parser.parse_args()

    if args.url and args.selector:
        scraping_avanzado(args.url, args.selector, salida=args.output)
    elif args.url:
        scraping_basico(args.url, salida=args.output)
    else:
        try:
            ejecutar_menu()
        except EOFError:
            print("No se recibió entrada por teclado.")
            print("Uso rápido: python3 scraper_universal.py https://quotes.toscrape.com")
            return 1

    return 0


# ============================================
# PROGRAMA PRINCIPAL
# ============================================

if __name__ == "__main__":
    sys.exit(main())
