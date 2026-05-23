"""
Ejercicios prácticos de BeautifulSoup4
Para que los estudiantes practiquen
"""

from bs4 import BeautifulSoup

# ============================================
# EJERCICIO 1: Analizar una tienda online
# ============================================
print("EJERCICIO 1: Tienda Online")
print("=" * 50)

html_tienda = """
<html>
    <body>
        <div class="productos">
            <div class="producto">
                <h3>Laptop</h3>
                <p class="precio">$899.99</p>
                <p class="descripcion">Laptop de alta performance</p>
            </div>
            <div class="producto">
                <h3>Mouse</h3>
                <p class="precio">$29.99</p>
                <p class="descripcion">Mouse inalámbrico</p>
            </div>
            <div class="producto">
                <h3>Teclado</h3>
                <p class="precio">$79.99</p>
                <p class="descripcion">Teclado mecánico RGB</p>
            </div>
        </div>
    </body>
</html>
"""

soup = BeautifulSoup(html_tienda, 'html.parser')

# TODO: Completa estos ejercicios
# 1. Encuentra todos los productos
# 2. Extrae el nombre, precio y descripción de cada uno
# 3. Calcula el precio total de todos los productos
# 4. Encuentra el producto más caro

print("Respuesta esperada:")
print("Productos encontrados: 3")
print("- Laptop: $899.99")
print("- Mouse: $29.99")
print("- Teclado: $79.99")
print("Precio total: $1009.97")
print()

# ============================================
# EJERCICIO 2: Extraer información de tabla
# ============================================
print("EJERCICIO 2: Tabla de estudiantes")
print("=" * 50)

html_tabla = """
<html>
    <body>
        <table>
            <thead>
                <tr>
                    <th>Nombre</th>
                    <th>Carrera</th>
                    <th>Calificación</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Juan García</td>
                    <td>Ingeniería</td>
                    <td>8.5</td>
                </tr>
                <tr>
                    <td>María López</td>
                    <td>Diseño</td>
                    <td>9.2</td>
                </tr>
                <tr>
                    <td>Pedro Martínez</td>
                    <td>Ingeniería</td>
                    <td>7.8</td>
                </tr>
            </tbody>
        </table>
    </body>
</html>
"""

soup = BeautifulSoup(html_tabla, 'html.parser')

# TODO: Completa estos ejercicios
# 1. Extrae los encabezados de la tabla
# 2. Extrae los datos de cada fila
# 3. Encuentra al estudiante con calificación más alta
# 4. Cuenta cuántos estudiantes de Ingeniería hay

print("Respuesta esperada:")
print("Encabezados: Nombre, Carrera, Calificación")
print("Estudiantes: Juan García, María López, Pedro Martínez")
print("Mejor calificación: María López (9.2)")
print()

# ============================================
# EJERCICIO 3: Red social simulada
# ============================================
print("EJERCICIO 3: Posts en red social")
print("=" * 50)

html_red_social = """
<html>
    <body>
        <div class="feed">
            <article class="post">
                <div class="autor">
                    <h4>Ana Silva</h4>
                    <span class="fecha">2024-01-15</span>
                </div>
                <p class="contenido">Mi primer post en Python</p>
                <div class="stats">
                    <span class="likes">245 me gusta</span>
                    <span class="comentarios">12 comentarios</span>
                </div>
            </article>
            <article class="post">
                <div class="autor">
                    <h4>Luis Rodríguez</h4>
                    <span class="fecha">2024-01-16</span>
                </div>
                <p class="contenido">¡Aprendiendo BeautifulSoup!</p>
                <div class="stats">
                    <span class="likes">89 me gusta</span>
                    <span class="comentarios">5 comentarios</span>
                </div>
            </article>
        </div>
    </body>
</html>
"""

soup = BeautifulSoup(html_red_social, 'html.parser')

# TODO: Completa estos ejercicios
# 1. Extrae todos los posts
# 2. Para cada post, extrae: autor, fecha, contenido
# 3. Extrae los "me gusta" y comentarios
# 4. Encuentra el post con más me gusta

print("Respuesta esperada:")
print("Post 1: Ana Silva (2024-01-15)")
print("  - 245 me gusta, 12 comentarios")
print("Post 2: Luis Rodríguez (2024-01-16)")
print("  - 89 me gusta, 5 comentarios")
print()

# ============================================
# EJERCICIO 4: Catálogo de películas
# ============================================
print("EJERCICIO 4: Catálogo de películas")
print("=" * 50)

html_peliculas = """
<html>
    <body>
        <div class="catalogo">
            <div class="pelicula">
                <h2>Titanic</h2>
                <p class="genero">Drama, Romance</p>
                <p class="año">1997</p>
                <p class="director">James Cameron</p>
                <p class="rating">★★★★★ (8.3/10)</p>
            </div>
            <div class="pelicula">
                <h2>Matrix</h2>
                <p class="genero">Sci-Fi, Acción</p>
                <p class="año">1999</p>
                <p class="director">Wachowski</p>
                <p class="rating">★★★★☆ (8.7/10)</p>
            </div>
            <div class="pelicula">
                <h2>Inception</h2>
                <p class="genero">Sci-Fi, Thriller</p>
                <p class="año">2010</p>
                <p class="director">Christopher Nolan</p>
                <p class="rating">★★★★★ (8.8/10)</p>
            </div>
        </div>
    </body>
</html>
"""

soup = BeautifulSoup(html_peliculas, 'html.parser')

# TODO: Completa estos ejercicios
# 1. Extrae todas las películas
# 2. Para cada película, obtén: título, género, año, director
# 3. Extrae la calificación numérica (8.3, 8.7, etc.)
# 4. Encuentra la película más reciente
# 5. Encuentra la película mejor calificada

print("Respuesta esperada:")
print("Total películas: 3")
print("Película más reciente: Inception (2010)")
print("Mejor calificada: Inception (8.8/10)")
print()

# ============================================
# EJERCICIO 5: Carrito de compras
# ============================================
print("EJERCICIO 5: Carrito de compras")
print("=" * 50)

html_carrito = """
<html>
    <body>
        <div class="carrito">
            <h1>Tu carrito</h1>
            <table>
                <tr>
                    <td class="producto">Café Brasileño</td>
                    <td class="cantidad">2</td>
                    <td class="precio-unitario">$8.50</td>
                    <td class="subtotal">$17.00</td>
                </tr>
                <tr>
                    <td class="producto">Pan Integral</td>
                    <td class="cantidad">1</td>
                    <td class="precio-unitario">$4.20</td>
                    <td class="subtotal">$4.20</td>
                </tr>
                <tr>
                    <td class="producto">Mantequilla</td>
                    <td class="cantidad">3</td>
                    <td class="precio-unitario">$5.99</td>
                    <td class="subtotal">$17.97</td>
                </tr>
            </table>
            <div class="resumen">
                <p>Subtotal: $39.17</p>
                <p>Impuesto: $3.13</p>
                <p class="total">Total: $42.30</p>
            </div>
        </div>
    </body>
</html>
"""

soup = BeautifulSoup(html_carrito, 'html.parser')

# TODO: Completa estos ejercicios
# 1. Extrae cada producto del carrito
# 2. Para cada producto: nombre, cantidad, precio unitario
# 3. Calcula el total de tu carrito
# 4. ¿Cuál es el artículo más caro?
# 5. ¿Cuántos artículos hay en total?

print("Respuesta esperada:")
print("Artículos en carrito: 3")
print("Cantidad total: 6 unidades")
print("Total: $42.30")
print()

# ============================================
# SOLUCIONES
# ============================================
print("\n" + "=" * 50)
print("SOLUCIONES DISPONIBLES")
print("=" * 50)
print("""
Para ver las soluciones, descomenta el archivo 'soluciones.py'
o pregunta a tu instructor.

Recuerda:
- Intenta resolver primero sin ver la solución
- Prueba diferentes formas de hacerlo
- Experimenta con find(), find_all(), select()
- Usa print() para verificar tus resultados
""")
