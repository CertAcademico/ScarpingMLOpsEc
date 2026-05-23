# Tutorial: Instalación de BeautifulSoup4 en macOS

## ¿Qué es BeautifulSoup4?

BeautifulSoup4 es una librería de Python que permite analizar y extraer datos de archivos HTML y XML. Es muy útil para:
- Web scraping (extraer información de sitios web)
- Parsear documentos HTML
- Buscar y filtrar elementos específicos
- Trabajar con datos estructurados en la web

---

## Requisitos Previos

Antes de instalar BeautifulSoup4, necesitas tener:

1. **Python 3 instalado**
2. **pip3** (gestor de paquetes de Python)

### Verificar si tienes Python y pip instalados

Abre una terminal y ejecuta:

```bash
python3 --version
pip3 --version
```

Si ambos comandos muestran versiones, ¡estás listo! Si no, necesitas instalar Python desde [python.org](https://www.python.org).

---

## Método 1: Instalación Global (Más Simple)

Esta es la forma más rápida si solo necesitas usar BeautifulSoup4 en un proyecto.

### Paso 1: Abrir la Terminal

En macOS, puedes:
- Presionar `Cmd + Espacio` y escribir "Terminal"
- O buscar Terminal en Aplicaciones → Utilidades

### Paso 2: Ejecutar el comando de instalación

```bash
pip3 install beautifulsoup4
```

**¿Qué sucede?**
- pip descargará BeautifulSoup4 desde PyPI (repositorio oficial)
- Instalará la librería en tu computadora
- Estará disponible en cualquier proyecto Python

### Paso 3: Verificar la instalación

```bash
python3 -c "import bs4; print(bs4.__version__)"
```

Si ves un número de versión (ej: 4.12.0), ¡la instalación fue exitosa!

---

## Método 2: Instalación con Ambiente Virtual (Recomendado para Proyectos)

Un ambiente virtual es una carpeta que contiene una copia aislada de Python. Esto evita conflictos entre proyectos.

### Paso 1: Navegar a la carpeta del proyecto

```bash
cd /path/a/tu/proyecto
```

Por ejemplo, si tu proyecto está en el Escritorio:
```bash
cd ~/Desktop/mi_proyecto
```

### Paso 2: Crear el ambiente virtual

```bash
python3 -m venv venv
```

Este comando crea una carpeta llamada `venv` con un ambiente aislado.

### Paso 3: Activar el ambiente virtual

```bash
source venv/bin/activate
```

Después de ejecutar esto, verás `(venv)` al inicio de tu línea de comandos.

### Paso 4: Instalar BeautifulSoup4

```bash
pip install beautifulsoup4
```

**Nota:** Cuando está activado el ambiente virtual, usamos `pip` en lugar de `pip3`.

### Paso 5: Verificar la instalación

```bash
python -c "import bs4; print(bs4.__version__)"
```

---

## Método 3: Instalación con Homebrew (Si tienes Homebrew)

Si tienes Homebrew instalado en tu Mac:

```bash
brew install beautifulsoup4
```

**Nota:** Homebrew puede no tener la versión más reciente.

---

## Mi Primer Programa con BeautifulSoup4

Después de instalar, crea un archivo llamado `prueba.py`:

```python
from bs4 import BeautifulSoup

# Ejemplo simple
html = """
<html>
  <head>
    <title>Mi Página</title>
  </head>
  <body>
    <h1>¡Hola Mundo!</h1>
    <p>Este es un párrafo.</p>
  </body>
</html>
"""

# Crear un objeto BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Extraer el título
print("Título:", soup.find('title').string)

# Extraer el encabezado
print("Encabezado:", soup.find('h1').string)

# Extraer el párrafo
print("Párrafo:", soup.find('p').string)
```

### Ejecutar el programa

```bash
python3 prueba.py
```

**Resultado esperado:**
```
Título: Mi Página
Encabezado: ¡Hola Mundo!
Párrafo: Este es un párrafo.
```

---

## Solucionar Problemas Comunes

### Problema 1: "ModuleNotFoundError: No module named 'bs4'"

**Causa:** BeautifulSoup4 no está instalado.

**Solución:**
```bash
pip3 install beautifulsoup4
```

### Problema 2: "Permission denied" al instalar

**Causa:** No tienes permisos de escritura.

**Solución:** Usa un ambiente virtual (Método 2) o instala con `--user`:
```bash
pip3 install --user beautifulsoup4
```

### Problema 3: Instalé con pip, pero python3 no lo encuentra

**Causa:** Confusión entre versiones de Python.

**Solución:** Asegúrate de que estés usando el mismo intérprete:
```bash
# Instalar con la versión correcta
python3 -m pip install beautifulsoup4

# Verificar con la misma versión
python3 -c "import bs4; print(bs4.__version__)"
```

---

## Instalar Parser Adicionales (Opcional)

BeautifulSoup4 puede usar diferentes parsers. El `html.parser` viene integrado, pero también puedes instalar:

### lxml (más rápido)
```bash
pip3 install lxml
```

### html5lib (más tolerante con HTML mal formado)
```bash
pip3 install html5lib
```

---

## Desactivar el Ambiente Virtual (Cuando Termines)

Si creaste un ambiente virtual y quieres salir:

```bash
deactivate
```

---

## Recursos Útiles

- **Documentación oficial:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- **Página de PyPI:** https://pypi.org/project/beautifulsoup4/
- **Tutorial interactivo:** https://www.w3schools.com/python/python_web_scraping.asp

---

## Resumen

| Método | Comando | Cuándo usar |
|--------|---------|------------|
| **Global** | `pip3 install beautifulsoup4` | Proyectos simples |
| **Virtual Env** | `python3 -m venv venv` + `pip install beautifulsoup4` | Proyectos profesionales |
| **Homebrew** | `brew install beautifulsoup4` | Si tienes Homebrew |

---

## ¡Estás listo para comenzar!

Con BeautifulSoup4 instalado, ahora puedes:
- Hacer web scraping
- Analizar documentos HTML
- Extraer datos de sitios web
- Automatizar tareas relacionadas con datos web

¡Felicidades y a programar! 🚀
