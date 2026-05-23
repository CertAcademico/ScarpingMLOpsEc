"""
Ejemplos básicos de BeautifulSoup4
Tutorial para estudiantes
"""

from bs4 import BeautifulSoup

# ============================================
# EJEMPLO 1: Parsear HTML básico
# ============================================
print("=" * 50)
print("EJEMPLO 1: Parsear HTML básico")
print("=" * 50)

html_simple = """
<html>
    <head>
        <title>Mi Blog</title>
    </head>
    <body>
        <h1>¡Bienvenido!</h1>
        <p>Este es mi primer párrafo.</p>
    </body>
</html>
"""

soup = BeautifulSoup(html_simple, 'html.parser')
print("Título:", soup.title.string)
print("Encabezado:", soup.h1.string)
print()

# ============================================
# EJEMPLO 2: Buscar elementos
# ============================================
print("=" * 50)
print("EJEMPLO 2: Buscar elementos con find()")
print("=" * 50)

html_blog = """
<html>
    <body>
        <article>
            <h2>Artículo 1</h2>
            <p>Contenido del artículo 1</p>
            <span class="fecha">2024-01-15</span>
        </article>
        <article>
            <h2>Artículo 2</h2>
            <p>Contenido del artículo 2</p>
            <span class="fecha">2024-01-20</span>
        </article>
    </body>
</html>
"""

soup = BeautifulSoup(html_blog, 'html.parser')

# Encontrar el primer artículo
primer_articulo = soup.find('article')
print("Primer artículo:", primer_articulo.h2.string)

# Encontrar elemento por clase
fecha = soup.find('span', class_='fecha')
print("Fecha encontrada:", fecha.string)
print()

# ============================================
# EJEMPLO 3: Buscar todos los elementos
# ============================================
print("=" * 50)
print("EJEMPLO 3: Buscar múltiples elementos con find_all()")
print("=" * 50)

# Encontrar todos los artículos
articulos = soup.find_all('article')
print(f"Se encontraron {len(articulos)} artículos\n")

for i, articulo in enumerate(articulos, 1):
    titulo = articulo.h2.string
    contenido = articulo.p.string
    fecha = articulo.span.string
    print(f"Artículo {i}:")
    print(f"  Título: {titulo}")
    print(f"  Contenido: {contenido}")
    print(f"  Fecha: {fecha}\n")

# ============================================
# EJEMPLO 4: Acceder a atributos
# ============================================
print("=" * 50)
print("EJEMPLO 4: Acceder a atributos de elementos")
print("=" * 50)

html_enlaces = """
<html>
    <body>
        <a href="https://google.com" target="_blank">Google</a>
        <a href="https://github.com" id="link-github">GitHub</a>
        <img src="imagen.jpg" alt="Mi imagen">
    </body>
</html>
"""

soup = BeautifulSoup(html_enlaces, 'html.parser')

# Obtener atributos
enlaces = soup.find_all('a')
for enlace in enlaces:
    print(f"Texto: {enlace.string}")
    print(f"  href: {enlace.get('href')}")
    print(f"  id: {enlace.get('id')}")
    print()

# Obtener atributo de imagen
imagen = soup.find('img')
print(f"Imagen src: {imagen.get('src')}")
print(f"Imagen alt: {imagen.get('alt')}")
print()

# ============================================
# EJEMPLO 5: Navegar la estructura
# ============================================
print("=" * 50)
print("EJEMPLO 5: Navegar entre elementos")
print("=" * 50)

html_estructura = """
<html>
    <body>
        <div class="contenedor">
            <h2>Título</h2>
            <p>Párrafo 1</p>
            <p>Párrafo 2</p>
        </div>
    </body>
</html>
"""

soup = BeautifulSoup(html_estructura, 'html.parser')

div = soup.find('div')
print("Primer elemento (h2):", div.contents[0].string)
print("Segundo elemento (p):", div.contents[1].string)
print()

# Elemento padre
p = soup.find('p')
print("Padre del párrafo:", p.parent.name)
print()

# Siguiente hermano
h2 = soup.find('h2')
siguiente = h2.next_sibling.next_sibling  # next_sibling salta espacios en blanco
print("Siguiente hermano de h2:", siguiente.name)
print()

# ============================================
# EJEMPLO 6: Filtrar y extraer texto
# ============================================
print("=" * 50)
print("EJEMPLO 6: Extraer solo texto")
print("=" * 50)

html_textos = """
<html>
    <body>
        <div>
            <h1>Encabezado</h1>
            <p>Párrafo con <strong>texto importante</strong></p>
        </div>
    </body>
</html>
"""

soup = BeautifulSoup(html_textos, 'html.parser')

# Extraer todo el texto
div = soup.find('div')
print("Todo el texto:", div.get_text())
print()

# Extraer texto sin espacios extra
print("Texto limpio:", div.get_text(strip=True))
print()

# Extraer con separador
print("Texto con separador:")
print(div.get_text(separator=" | "))
print()

# ============================================
# EJEMPLO 7: CSS Selectors
# ============================================
print("=" * 50)
print("EJEMPLO 7: Usar selectores CSS")
print("=" * 50)

html_css = """
<html>
    <body>
        <div class="contenedor">
            <p class="importante">Párrafo importante 1</p>
            <p>Párrafo normal</p>
            <p class="importante">Párrafo importante 2</p>
        </div>
    </body>
</html>
"""

soup = BeautifulSoup(html_css, 'html.parser')

# Seleccionar por clase
importantes = soup.select('.importante')
print(f"Encontrados {len(importantes)} párrafos importantes:")
for p in importantes:
    print(f"  - {p.string}")
print()

# Seleccionar dentro de contenedor
parrafos = soup.select('div.contenedor > p')
print(f"Párrafos dentro del contenedor: {len(parrafos)}")
print()

# ============================================
# EJEMPLO 8: Funciones útiles
# ============================================
print("=" * 50)
print("EJEMPLO 8: Funciones útiles de BeautifulSoup")
print("=" * 50)

html_util = """
<html>
    <body>
        <div id="seccion1" class="importante destacado">
            <p>Contenido</p>
        </div>
    </body>
</html>
"""

soup = BeautifulSoup(html_util, 'html.parser')
div = soup.find('div')

# has_attr: Verificar si tiene atributo
print("¿Tiene atributo 'id'?", div.has_attr('id'))
print("¿Tiene atributo 'data'?", div.has_attr('data'))
print()

# string vs strings
print("String único:", div.p.string)
print("Todos los strings:", list(div.p.strings))
print()

# name: Nombre de la etiqueta
print("Nombre de etiqueta:", div.name)
print()

print("=" * 50)
print("¡Fin de los ejemplos básicos!")
print("=" * 50)
