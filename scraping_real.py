"""
Web Scraping Práctico: Ejemplos con Páginas Reales
Tutorial para extraer datos de sitios web verdaderos
"""

import requests
from bs4 import BeautifulSoup

print("=" * 60)
print("WEB SCRAPING CON BEAUTIFULSOUP4 - EJEMPLOS REALES")
print("=" * 60)
print()

# ============================================
# EJEMPLO 1: Scraping Educativo (Quotes)
# ============================================
print("EJEMPLO 1: Extraer Citas de gobiernobogota.gov.co/")
print("-" * 60)

try:
    # Descargar la página
    url = "https:www.gobiernobogota.gov.co/"
    response = requests.get(url, timeout=5)
    response.raise_for_status()  # Verificar si la descarga fue exitosa
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extraer todas las citas
    citas = soup.find_all('div', class_='quote')
    
    print(f"✓ Se encontraron {len(citas)} citas\n")
    
    # Mostrar las primeras 3
    for i, cita_div in enumerate(citas[:3], 1):
        # Extraer el texto de la cita
        texto_cita = cita_div.find('span', class_='text').string
        
        # Extraer el autor
        autor_tag = cita_div.find('small', class_='author')
        autor = autor_tag.string if autor_tag else "Desconocido"
        
        # Extraer tags (etiquetas)
        tags = [tag.string for tag in cita_div.find_all('a', class_='tag')]
        
        print(f"Cita {i}:")
        print(f"  Texto: {texto_cita}")
        print(f"  Autor: {autor}")
        print(f"  Tags: {', '.join(tags)}")
        print()
    
except requests.exceptions.RequestException as e:
    print(f"❌ Error al descargar la página: {e}")
except Exception as e:
    print(f"❌ Error al procesar: {e}")

print()

# ============================================
# EJEMPLO 2: Scraping de Tecnología (DevTo)
# ============================================
print("EJEMPLO 2: Extraer Artículos de Dev.to")
print("-" * 60)

try:
    url = "https://dev.to/api/articles?per_page=5"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    
    # Este sitio devuelve JSON, no HTML
    articulos = response.json()
    
    print(f"✓ Se encontraron {len(articulos)} artículos recientes\n")
    
    for i, articulo in enumerate(articulos[:3], 1):
        print(f"Artículo {i}:")
        print(f"  Título: {articulo.get('title', 'N/A')}")
        print(f"  Autor: {articulo.get('user', {}).get('name', 'N/A')}")
        print(f"  Reacciones: {articulo.get('positive_reactions_count', 0)} 👍")
        print(f"  Comentarios: {articulo.get('comments_count', 0)} 💬")
        print(f"  URL: {articulo.get('url', 'N/A')}")
        print()
    
except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Error al procesar JSON: {e}")

print()

# ============================================
# EJEMPLO 3: Scraping de Noticias (BBC)
# ============================================
print("EJEMPLO 3: Extraer Titulares de BBC News")
print("-" * 60)

try:
    url = "https://www.bbc.com/news"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=5)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Buscar titulares (la estructura puede cambiar)
    titulares = soup.find_all('h2', limit=5)
    
    if titulares:
        print(f"✓ Se encontraron {len(titulares)} titulares\n")
        
        for i, titular in enumerate(titulares, 1):
            texto = titular.get_text(strip=True)
            if texto:  # Solo mostrar si hay texto
                print(f"{i}. {texto}")
    else:
        print("⚠ No se encontraron titulares (estructura de página puede haber cambiado)")
    
except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Error al procesar: {e}")

print()

# ============================================
# EJEMPLO 4: Scraping de Productos (Books)
# ============================================
print("EJEMPLO 4: Extraer Libros de Books.toscrape.com")
print("-" * 60)

try:
    url = "https://books.toscrape.com/"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Encontrar todos los libros
    libros = soup.find_all('article', class_='product_pod')
    
    print(f"✓ Se encontraron {len(libros)} libros en la página\n")
    
    # Mostrar los primeros 5
    for i, libro in enumerate(libros[:5], 1):
        # Título
        titulo_tag = libro.find('h3').find('a')
        titulo = titulo_tag.get('title', 'N/A')
        
        # Precio
        precio_tag = libro.find('p', class_='price_color')
        precio = precio_tag.get_text(strip=True) if precio_tag else 'N/A'
        
        # Rating
        rating_tag = libro.find('p', class_='star-rating')
        rating = rating_tag.get('class')[1] if rating_tag else 'N/A'
        
        # Disponibilidad
        disponibilidad_tag = libro.find('p', class_='instock availability')
        disponibilidad = disponibilidad_tag.get_text(strip=True) if disponibilidad_tag else 'N/A'
        
        print(f"Libro {i}:")
        print(f"  Título: {titulo}")
        print(f"  Precio: {precio}")
        print(f"  Rating: {rating}")
        print(f"  Estado: {disponibilidad}")
        print()
    
except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Error al procesar: {e}")

print()

# ============================================
# EJEMPLO 5: Scraping de GitHub
# ============================================
print("EJEMPLO 5: Proyectos Trending en GitHub")
print("-" * 60)

try:
    url = "https://github.com/trending"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=5)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Encontrar repositorios
    repos = soup.find_all('article', class_='Box-row')
    
    print(f"✓ Se encontraron {len(repos)} repositorios trending\n")
    
    # Mostrar los primeros 3
    for i, repo in enumerate(repos[:3], 1):
        # Nombre del repo
        nombre_tag = repo.find('h2').find('a')
        nombre = nombre_tag.get_text(strip=True) if nombre_tag else 'N/A'
        
        # Descripción
        descripcion_tag = repo.find('p', class_='col-9')
        descripcion = descripcion_tag.get_text(strip=True) if descripcion_tag else 'N/A'
        
        # Lenguaje
        lenguaje_tag = repo.find('span', itemprop='programmingLanguage')
        lenguaje = lenguaje_tag.get_text(strip=True) if lenguaje_tag else 'N/A'
        
        print(f"Proyecto {i}:")
        print(f"  Nombre: {nombre}")
        print(f"  Lenguaje: {lenguaje}")
        if descripcion and descripcion != 'N/A':
            print(f"  Descripción: {descripcion[:60]}...")
        print()
    
except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Error al procesar: {e}")

print()

# ============================================
# EJEMPLO 6: Obtener meta información
# ============================================
print("EJEMPLO 6: Información de Página (Meta Tags)")
print("-" * 60)

try:
    url = "https://quotes.toscrape.com/"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Título
    titulo = soup.find('title')
    print(f"Título: {titulo.string if titulo else 'N/A'}")
    
    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        print(f"Descripción: {meta_desc.get('content', 'N/A')}")
    
    # Todos los meta tags
    metas = soup.find_all('meta')
    print(f"Total de meta tags: {len(metas)}")
    
    print()
    
except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
except Exception as e:
    print(f"❌ Error al procesar: {e}")

print("=" * 60)
print("FIN DE LOS EJEMPLOS")
print("=" * 60)
print("""
NOTAS IMPORTANTES:
1. Algunos sitios pueden bloquear requests (necesitan headers)
2. Siempre revisa el robots.txt del sitio
3. No hagas demasiadas solicitudes rápido (considéra usar time.sleep())
4. Lee los términos de servicio del sitio
5. Algunos sitios usan JavaScript (BeautifulSoup no las ve)

Para ver HTML de una página:
    print(soup.prettify())

Para guardar los datos:
    - CSV: pip install pandas
    - JSON: Usar json.dumps()
    - Base de datos: pip install sqlite3
""")
