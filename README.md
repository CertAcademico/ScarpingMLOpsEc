# BeautifulSoup4 - Guía Completa para Estudiantes

Bienvenido al repositorio educativo de **BeautifulSoup4**. Aquí encontrarás todo lo que necesitas para aprender a usar esta poderosa librería de Python para web scraping y análisis de HTML.

## 📁 Estructura del Repositorio

```
BeautifulSoup4/
├── README.md                    ← Este archivo
├── TUTORIAL_INSTALACION.md      ← Guía paso a paso para instalar
├── CHEAT_SHEET.md              ← Referencia rápida de comandos
├── ejemplos_basicos.py         ← Ejemplos básicos ejecutables
├── ejercicios_practicos.py     ← Ejercicios para practicar
├── soluciones.py               ← Soluciones a los ejercicios
└── requirements.txt            ← Dependencias del proyecto
```

## 🚀 Inicio Rápido

### 1. Instalación (3 minutos)

```bash
# Opción A: Instalación global
pip3 install beautifulsoup4

# Opción B: Con ambiente virtual (Recomendado)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Primer Ejemplo

```python
from bs4 import BeautifulSoup

html = "<html><body><h1>¡Hola!</h1></body></html>"
soup = BeautifulSoup(html, 'html.parser')

print(soup.h1.string)  # ¡Hola!
```

### 3. Ejecutar Ejemplos

```bash
# Ver ejemplos básicos
python3 ejemplos_basicos.py

# Ver ejercicios (intenta resolverlos)
python3 ejercicios_practicos.py
```

## 📚 Contenido Educativo

### Para Principiantes
1. **Leer primero:** [TUTORIAL_INSTALACION.md](TUTORIAL_INSTALACION.md)
2. **Ejecutar:** `python3 ejemplos_basicos.py`
3. **Practicar:** `python3 ejercicios_practicos.py`

### Referencia Rápida
- **Cheat Sheet:** [CHEAT_SHEET.md](CHEAT_SHEET.md) - Todos los comandos en un lugar

### Niveles de Dificultad

#### 🟢 Básico
- Parsear HTML simple
- Encontrar elementos con `find()`
- Extraer texto y atributos

#### 🟡 Intermedio
- Búsquedas avanzadas con `find_all()`
- Usar CSS selectors
- Navegar la estructura HTML

#### 🔴 Avanzado
- Web scraping de sitios reales
- Combinación con `requests`
- Manejo de errores y excepciones

## 🎯 Objetivos de Aprendizaje

Al completar este curso aprenderás:

✅ Qué es BeautifulSoup4 y para qué sirve  
✅ Cómo parsear documentos HTML  
✅ Buscar y filtrar elementos específicos  
✅ Extraer datos de páginas web  
✅ Navegar la estructura HTML/XML  
✅ Realizar web scraping ético  
✅ Integrar con `requests` para APIs web  

## 💻 Requisitos

- **Python 3.7+** (verifica con `python3 --version`)
- **pip3** (verifica con `pip3 --version`)
- Cualquier editor de texto o IDE (VS Code, PyCharm, etc.)

## 📖 Documentación Oficial

- [BeautifulSoup4 Docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [PyPI Package](https://pypi.org/project/beautifulsoup4/)

## 🔧 Instalación de Herramientas Adicionales

### Para Web Scraping Real

```bash
# Instalar requests para descargar páginas web
pip install requests

# Instalar parsers alternativos (más rápidos)
pip install lxml
pip install html5lib
```

### Para Desarrollo

```bash
# Instalar todas las herramientas recomendadas
pip install -r requirements.txt
```

## 📝 Ejemplos de Uso

### Ejemplo 1: Extraer títulos

```python
from bs4 import BeautifulSoup

html = """
<html>
    <h1>Título Principal</h1>
    <h2>Subtítulo</h2>
</html>
"""

soup = BeautifulSoup(html, 'html.parser')

# Encontrar todos los títulos
titulos = soup.find_all(['h1', 'h2'])
for titulo in titulos:
    print(titulo.string)
```

### Ejemplo 2: Extraer enlaces

```python
enlaces = soup.find_all('a')

for enlace in enlaces:
    url = enlace.get('href')
    texto = enlace.string
    print(f"{texto}: {url}")
```

### Ejemplo 3: Web Scraping Simple

```python
import requests
from bs4 import BeautifulSoup

# Descargar página
response = requests.get('https://ejemplo.com')
soup = BeautifulSoup(response.content, 'html.parser')

# Extraer datos
noticias = soup.find_all('article')
for noticia in noticias:
    print(noticia.find('h2').string)
```

## 🎓 Estructura Recomendada de Aprendizaje

### Semana 1: Fundamentos
- [ ] Instalar BeautifulSoup4
- [ ] Leer tutorial de instalación
- [ ] Ejecutar ejemplos básicos
- [ ] Entender `find()` y `find_all()`

### Semana 2: Práctica
- [ ] Resolver ejercicios básicos
- [ ] Experimentar con diferentes HTML
- [ ] Aprender CSS selectors
- [ ] Practicar extracción de atributos

### Semana 3: Proyectos
- [ ] Crear mini proyecto de scraping
- [ ] Integrar con `requests`
- [ ] Guardar datos en CSV/JSON
- [ ] Manejo de errores

## ⚠️ Consideraciones Éticas

Cuando hagas web scraping, recuerda:

1. **Respeta el robots.txt** - Verifica si el sitio permite scraping
2. **Lee los términos de servicio** - Algunos sitios lo prohíben
3. **No hagas spam** - Limita tus solicitudes
4. **Sé transparente** - Identifica tu bot en User-Agent
5. **Respeta la privacidad** - No recopiles datos personales sin consentimiento

Ejemplo de User-Agent:
```python
headers = {
    'User-Agent': 'Mi Bot Educativo/1.0 (Propósito educativo)'
}
response = requests.get(url, headers=headers)
```

## 🐛 Solucionar Problemas

### Error: "ModuleNotFoundError: No module named 'bs4'"

```bash
pip install beautifulsoup4
```

### Error: "AttributeError: 'NoneType' object has no attribute..."

Significa que el elemento no existe. Siempre valida:

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
soup = BeautifulSoup(html, 'lxml')  # Más tolerante
soup = BeautifulSoup(html, 'html5lib')  # Muy tolerante
```

## 🤝 Cómo Contribuir

Si encuentras errores o quieres mejorar este material:

1. Abre un issue con tu sugerencia
2. Proporciona ejemplos de código
3. Sé respetuoso y constructivo

## 📞 Soporte

Si tienes preguntas:
1. Consulta el [CHEAT_SHEET.md](CHEAT_SHEET.md)
2. Lee la [documentación oficial](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
3. Busca en Stack Overflow
4. Pregunta en foros de Python

## 📄 Licencia

Este material educativo es de libre uso para fines educativos.

---

## 🎉 ¡Estás Listo para Comenzar!

Ahora que tienes todo configurado, dirígete al archivo [TUTORIAL_INSTALACION.md](TUTORIAL_INSTALACION.md) y comienza tu viaje con BeautifulSoup4.

**Recuerda:** La práctica es la clave. Cuanto más practiques, mejor serás.

¡Feliz aprendizaje! 🚀

---

**Última actualización:** Mayo 2024  
**Versión:** 1.0  
**Compatible con:** BeautifulSoup4 4.9+
