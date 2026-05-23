# 🌐 BeautifulSoup4 - Tutorial Completo de Web Scraping

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![BeautifulSoup4](https://img.shields.io/badge/BeautifulSoup4-4.9%2B-green)](https://www.crummy.com/software/BeautifulSoup/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Educational](https://img.shields.io/badge/Type-Educational-orange)](README.md)

**Un repositorio educativo completo para aprender Web Scraping con BeautifulSoup4**

[Inicio Rápido](#-inicio-rápido) • [Ejemplos](#-ejemplos) • [Tutoriales](#-tutoriales) • [Documentación](#-documentación)

</div>

---

## 📚 ¿Qué es BeautifulSoup4?

**BeautifulSoup4** es una poderosa librería de Python para analizar documentos HTML y XML. Permite extraer información de páginas web de forma fácil y elegante.

### ✨ Características

- 🎯 Búsqueda flexible de elementos HTML
- 🔍 Extracción de datos estructurados
- 📝 Parseo de documentos HTML/XML
- 🚀 Compatible con múltiples parsers (html.parser, lxml, html5lib)
- 💡 API intuitiva y fácil de usar
- 🌐 Ideal para Web Scraping ético

### 🎓 Casos de Uso

```
✅ Web scraping de datos públicos
✅ Análisis de documentos HTML
✅ Extracción de metadatos
✅ Automatización web
✅ Proyectos educativos
✅ Análisis de información online
```

---

## 🚀 Inicio Rápido

### 1️⃣ Requisitos

- **Python 3.7+** 
- **pip o pip3**

Verifica tu Python:

```bash
python3 --version
pip3 --version
```

### 2️⃣ Clonar el Repositorio

```bash
git clone https://github.com/TU_USUARIO/BeautifulSoup4.git
cd BeautifulSoup4
```

### 3️⃣ Instalar Dependencias

**Opción A - Instalación Global:**
```bash
pip3 install -r requirements.txt
```

**Opción B - Ambiente Virtual (Recomendado):**
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4️⃣ ¡Estás Listo!

```bash
python ejemplos_basicos.py
```

---

## 📁 Estructura del Proyecto

```
BeautifulSoup4/
├── README.md                    # Este archivo
├── README_PRO.md               # Versión profesional
├── TUTORIAL_INSTALACION.md     # Guía paso a paso
├── CHEAT_SHEET.md              # Referencia rápida
├── requirements.txt            # Dependencias
│
├── ejemplos_basicos.py         # 8 ejemplos básicos ejecutables
├── ejercicios_practicos.py     # 5 ejercicios para practicar
├── scraping_real.py            # Scraping de 6 sitios reales
└── scraper_universal.py        # Scraper interactivo universal
```

---

## 📖 Tutoriales Incluidos

### 🟢 Nivel Principiante

1. **[TUTORIAL_INSTALACION.md](TUTORIAL_INSTALACION.md)**
   - Instalación paso a paso
   - Solución de problemas
   - Instalación en diferentes OS

2. **[ejemplos_basicos.py](ejemplos_basicos.py)**
   - Parsear HTML simple
   - Encontrar elementos
   - Extraer texto y atributos
   
   Ejecuta:
   ```bash
   python ejemplos_basicos.py
   ```

### 🟡 Nivel Intermedio

3. **[ejercicios_practicos.py](ejercicios_practicos.py)**
   - 5 ejercicios prácticos
   - Casos reales: tienda, tabla, red social, películas, carrito
   
   Ejecuta:
   ```bash
   python ejercicios_practicos.py
   ```

4. **[CHEAT_SHEET.md](CHEAT_SHEET.md)**
   - Referencia rápida de todos los comandos
   - Ejemplos de código
   - Selectores CSS

### 🔴 Nivel Avanzado

5. **[scraping_real.py](scraping_real.py)**
   - Web scraping real de 6 sitios
   - Manejo de errores
   - Integración con requests
   
   Ejecuta:
   ```bash
   python scraping_real.py
   ```

6. **[scraper_universal.py](scraper_universal.py)**
   - Scraper interactivo universal
   - Funciona con cualquier URL
   - Extrae múltiples tipos de datos
   
   Ejecuta:
   ```bash
   python scraper_universal.py
   ```

---

## 💻 Ejemplos Rápidos

### Ejemplo 1: Parsear HTML Básico

```python
from bs4 import BeautifulSoup

html = """
<html>
  <head>
    <title>Mi Página</title>
  </head>
  <body>
    <h1>¡Hola!</h1>
    <p>Este es un párrafo.</p>
  </body>
</html>
"""

soup = BeautifulSoup(html, 'html.parser')

print(soup.title.string)      # Mi Página
print(soup.h1.string)          # ¡Hola!
print(soup.p.get_text())       # Este es un párrafo.
```

### Ejemplo 2: Buscar Elementos

```python
from bs4 import BeautifulSoup

html = """
<div>
  <p class="importante">Párrafo 1</p>
  <p class="importante">Párrafo 2</p>
  <p>Párrafo 3</p>
</div>
"""

soup = BeautifulSoup(html, 'html.parser')

# Encontrar el primer elemento
print(soup.find('p', class_='importante').string)
# → Párrafo 1

# Encontrar todos los elementos
todos = soup.find_all('p', class_='importante')
for p in todos:
    print(p.string)
# → Párrafo 1
# → Párrafo 2
```

### Ejemplo 3: Usar Selectores CSS

```python
soup = BeautifulSoup(html, 'html.parser')

# Por clase
soup.select('.importante')

# Por ID
soup.select('#contenedor')

# Combinadores
soup.select('div > p')
soup.select('div p')
```

### Ejemplo 4: Extraer Datos de una Página Real

```python
import requests
from bs4 import BeautifulSoup

url = "https://quotes.toscrape.com/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extraer citas
citas = soup.find_all('div', class_='quote')
for cita in citas[:3]:
    texto = cita.find('span', class_='text').string
    autor = cita.find('small', class_='author').string
    print(f"{texto}\n— {autor}\n")
```

---

## 🔧 Instalación de Herramientas Adicionales

### Para Web Scraping Real

```bash
# Descargar páginas web
pip install requests

# Parsers más rápidos
pip install lxml

# Parsers más tolerantes
pip install html5lib
```

### Para Análisis de Datos

```bash
# Trabajar con CSV/Excel
pip install pandas

# Base de datos
pip install sqlite3

# Guardar como JSON
pip install json
```

---

## ⚠️ Consideraciones Éticas

Cuando hagas web scraping, recuerda:

1. ✅ **Respeta el robots.txt** - Verifica si el sitio permite scraping
2. ✅ **Lee los términos de servicio** - Algunos sitios lo prohíben explícitamente
3. ✅ **Limita tus solicitudes** - No hagas spam, usa delays (`time.sleep()`)
4. ✅ **Sé transparente** - Identifica tu bot en el User-Agent
5. ✅ **Respeta la privacidad** - No recopiles datos personales sin consentimiento

### Ejemplo de User-Agent Responsable

```python
headers = {
    'User-Agent': 'Mi Bot Educativo/1.0 (Propósito educativo)'
}
response = requests.get(url, headers=headers)
```

---

## 🐛 Solucionar Problemas

### Error: "ModuleNotFoundError: No module named 'bs4'"

```bash
pip install beautifulsoup4
```

### Error: "AttributeError: 'NoneType' object has no attribute..."

El elemento no existe. Siempre valida:

```python
elemento = soup.find('div', id='mi-div')
if elemento:
    print(elemento.string)
else:
    print("Elemento no encontrado")
```

### El HTML se ve "roto"

Intenta cambiar el parser:

```python
# En lugar de 'html.parser', intenta:
soup = BeautifulSoup(html, 'lxml')        # Más tolerante
soup = BeautifulSoup(html, 'html5lib')    # Muy tolerante
```

---

## 📚 Recursos Externos

| Recurso | Descripción |
|---------|------------|
| [Documentación Oficial](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) | Guía completa de BeautifulSoup4 |
| [PyPI Package](https://pypi.org/project/beautifulsoup4/) | Página oficial en PyPI |
| [Real Python](https://realpython.com/beautiful-soup-web-scraping-python/) | Tutorial completo |
| [W3Schools](https://www.w3schools.com/python/python_web_scraping.asp) | Introducción web scraping |
| [Stack Overflow](https://stackoverflow.com/questions/tagged/beautifulsoup) | Preguntas y respuestas |

---

## 🎯 Roadmap de Aprendizaje

### Semana 1: Fundamentos ✅
- [ ] Instalar BeautifulSoup4
- [ ] Leer tutorial de instalación
- [ ] Ejecutar ejemplos básicos
- [ ] Entender `find()` y `find_all()`
- [ ] Completar CHEAT_SHEET.md

### Semana 2: Práctica 📝
- [ ] Resolver ejercicios prácticos
- [ ] Experimentar con HTML personalizado
- [ ] Aprender CSS selectors
- [ ] Extraer atributos y texto
- [ ] Navegar estructura HTML

### Semana 3: Proyectos 🚀
- [ ] Crear mini proyecto de scraping
- [ ] Integrar con `requests`
- [ ] Guardar datos en CSV/JSON
- [ ] Manejo de errores robusto
- [ ] Deploy a GitHub

---

## 💡 Tips y Trucos

### 🎨 Debuggear HTML

```python
# Ver HTML formateado
print(soup.prettify())

# Ver solo una parte
print(soup.find('div').prettify())
```

### ⚡ Mejorar Rendimiento

```python
# Usar lxml en lugar de html.parser
soup = BeautifulSoup(html, 'lxml')  # 10x más rápido

# Parsear solo lo que necesitas
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'html.parser', features='lxml')
```

### 🔄 Loop seguro

```python
# Siempre validar antes de acceder
elemento = soup.find('p', class_='inexistente')
if elemento:
    print(elemento.string)
else:
    print("No encontrado")

# O usar get() en atributos
print(elemento.get('id', 'No tiene ID'))  # Retorna default si no existe
```

---

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Úsalo libremente en tus proyectos educativos.

```
MIT License © 2024
Permitido: Uso, modificación, distribución
Condición: Incluir licencia y copyright
```

---

## 🤝 Contribuciones

¿Quieres mejorar este repositorio?

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/mejora`)
3. Commit cambios (`git commit -m 'Agrega mejora'`)
4. Push a la rama (`git push origin feature/mejora`)
5. Abre un Pull Request

---

## 📞 Soporte

¿Tienes preguntas?

1. 📖 Consulta el [CHEAT_SHEET.md](CHEAT_SHEET.md)
2. 📚 Lee la [documentación oficial](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
3. 🔍 Busca en [Stack Overflow](https://stackoverflow.com/questions/tagged/beautifulsoup)
4. 💬 Abre un Issue en este repositorio

---

## 🎉 ¡Comienza Ahora!

Eres solo 3 comandos de distancia de tu primer web scraper:

```bash
git clone https://github.com/TU_USUARIO/BeautifulSoup4.git
cd BeautifulSoup4
python ejemplos_basicos.py
```

**¡Feliz aprendizaje! 🚀**

---

<div align="center">

**Made with ❤️ for education**

⭐ Si te fue útil, considera dejar una estrella ⭐

</div>
