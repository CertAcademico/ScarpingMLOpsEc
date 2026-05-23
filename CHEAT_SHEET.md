# BeautifulSoup4 - Cheat Sheet (Referencia Rápida)

## 1. Importar y Crear un Soup

```python
from bs4 import BeautifulSoup

# Desde un string
html = "<html>...</html>"
soup = BeautifulSoup(html, 'html.parser')

# Desde un archivo
with open('archivo.html') as f:
    soup = BeautifulSoup(f, 'html.parser')

# Desde una URL (necesitas requests)
import requests
response = requests.get('https://ejemplo.com')
soup = BeautifulSoup(response.content, 'html.parser')
```

---

## 2. Acceso Directo a Elementos

```python
# Acceso como atributo
soup.title          # <title>...</title>
soup.body           # <body>...</body>
soup.div            # Primer <div>

# Acceder al contenido de texto
soup.title.string   # Texto dentro de <title>
```

---

## 3. Métodos de Búsqueda

### `find()` - Encuentra el PRIMER elemento

```python
# Por nombre de etiqueta
soup.find('div')

# Por atributo
soup.find('a', href='ejemplo.com')
soup.find('div', id='contenedor')

# Por clase
soup.find('p', class_='importante')

# Con atributos complejos
soup.find('div', attrs={'data-id': '123'})
```

### `find_all()` - Encuentra TODOS los elementos

```python
# Retorna una lista
todos_los_div = soup.find_all('div')

# Con límite
primeros_3 = soup.find_all('p', limit=3)

# Búsqueda recursiva
soup.find_all('a', recursive=True)
```

### `select()` - CSS Selectors

```python
# Por clase
soup.select('.clase')
soup.select('div.importante')

# Por ID
soup.select('#id')
soup.select('div#contenedor')

# Por atributo
soup.select('[href]')
soup.select('a[href="ejemplo.com"]')

# Combinadores
soup.select('div > p')           # Hijo directo
soup.select('div p')             # Descendiente
soup.select('h1, h2, h3')        # Múltiples
soup.select('p:first-child')     # Pseudo-selectores
```

---

## 4. Extraer Información

### Obtener Texto

```python
elemento = soup.find('p')

# Texto simple
elemento.string             # Si solo tiene un string
elemento.get_text()         # Todo el texto
elemento.get_text(strip=True)  # Sin espacios extra

# Todos los strings
list(elemento.strings)
list(elemento.stripped_strings)  # Sin espacios
```

### Obtener Atributos

```python
enlace = soup.find('a')

# Métodos diferentes (hacen lo mismo)
enlace['href']              # Como diccionario
enlace.get('href')          # Más seguro (no error si no existe)
enlace.attrs                # Todos los atributos como dict

# Verificar si existe un atributo
enlace.has_attr('href')

# Obtener con valor por defecto
enlace.get('data-custom', 'valor_por_defecto')
```

---

## 5. Navegar la Estructura

```python
elemento = soup.find('p')

# Elementos relacionados
elemento.parent             # Elemento padre
elemento.parents            # Todos los padres
elemento.contents           # Lista de hijos
elemento.children           # Iterador de hijos
elemento.next_sibling       # Hermano siguiente
elemento.previous_sibling   # Hermano anterior
elemento.next_element       # Siguiente elemento en el árbol
elemento.previous_element   # Elemento anterior en el árbol
```

---

## 6. Información sobre Elementos

```python
elemento = soup.find('p')

# Nombre de la etiqueta
elemento.name               # 'p'

# Todos los atributos
elemento.attrs              # {'class': ['importante'], 'id': 'p1'}

# Verificaciones
elemento.is_empty_element   # ¿Es una etiqueta vacía?
```

---

## 7. Modificar HTML (Avanzado)

```python
elemento = soup.find('p')

# Cambiar contenido
elemento.string = 'Nuevo texto'

# Agregar elemento
elemento.append('Más texto')

# Cambiar atributo
elemento['class'] = 'nueva-clase'

# Crear nuevo elemento
from bs4 import NavigableString, Tag
nuevo_p = soup.new_tag('p')
nuevo_p.string = 'Párrafo nuevo'
elemento.append(nuevo_p)
```

---

## 8. Parsers Disponibles

```python
# Parser por defecto (integrado)
soup = BeautifulSoup(html, 'html.parser')

# Con lxml (más rápido, necesita: pip install lxml)
soup = BeautifulSoup(html, 'lxml')

# Con html5lib (más tolerante, necesita: pip install html5lib)
soup = BeautifulSoup(html, 'html5lib')

# Con xml (para XML)
soup = BeautifulSoup(xml, 'xml')
```

---

## 9. Filtros de Búsqueda

### String - Coincidencia exacta

```python
soup.find_all('a', string='Haz clic aquí')
```

### Expresión Regular - Patrón

```python
import re
soup.find_all('p', string=re.compile(r'^Hola'))
```

### Función - Lógica personalizada

```python
def tiene_href(tag):
    return tag.name == 'a' and tag.has_attr('href')

soup.find_all(tiene_href)
```

### Lista - Cualquiera de varias opciones

```python
soup.find_all(['h1', 'h2', 'h3'])  # Cualquiera de estas etiquetas
```

---

## 10. Validar HTML

```python
# Prettify - Formato legible
print(soup.prettify())

# Convertir a string
html_str = str(soup)
html_str = soup.decode()

# Verificar si es válido
if soup.find('p'):
    print('Párrafo encontrado')
```

---

## 11. Errores Comunes y Soluciones

| Problema | Solución |
|----------|----------|
| `AttributeError: 'NoneType'` | El elemento no existe. Usa `.find()` con validación |
| `KeyError` al acceder atributo | Usa `.get('atributo')` en lugar de `['atributo']` |
| `ModuleNotFoundError` | Asegúrate de instalar: `pip install beautifulsoup4` |
| HTML no se parsea bien | Intenta con parser `'lxml'` o `'html5lib'` |
| Espacios en blanco extras | Usa `.get_text(strip=True)` o `.stripped_strings` |

---

## 12. Ejemplo Completo

```python
from bs4 import BeautifulSoup
import requests

# 1. Obtener HTML
response = requests.get('https://ejemplo.com')
soup = BeautifulSoup(response.content, 'html.parser')

# 2. Buscar elementos
articulos = soup.find_all('article')

# 3. Extraer datos
for articulo in articulos:
    titulo = articulo.find('h2').get_text(strip=True)
    enlace = articulo.find('a')['href']
    fecha = articulo.find('span', class_='fecha').get_text()
    
    print(f"{titulo}")
    print(f"Enlace: {enlace}")
    print(f"Fecha: {fecha}\n")

# 4. Guardar en archivo
with open('resultado.html', 'w') as f:
    f.write(soup.prettify())
```

---

## 13. Recursos

- [Documentación oficial](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [PyPI](https://pypi.org/project/beautifulsoup4/)
- [Web Scraping con BeautifulSoup](https://realpython.com/beautiful-soup-web-scraping-python/)

---

## Comandos de Instalación Rápidos

```bash
# Instalación básica
pip install beautifulsoup4

# Con parsers adicionales
pip install beautifulsoup4 lxml html5lib

# Para web scraping
pip install beautifulsoup4 requests

# Para todo
pip install beautifulsoup4 lxml html5lib requests
```

---

**Última actualización:** 2024 | **Versión:** BeautifulSoup4 4.12+
