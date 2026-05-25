# Tutorial Completo — ScrapingMLOpsEc

Guía paso a paso para usar todas las herramientas de la plataforma: web scraping, OSINT y preprocesamiento de datos para Machine Learning.

---

## Tabla de Contenidos

1. [Instalación y configuración](#1-instalación-y-configuración)
2. [OSINT CLI — Dominios e IPs](#2-osint-cli--dominios-e-ips)
3. [Web Scraper Universal](#3-web-scraper-universal)
4. [Email Finder](#4-email-finder)
5. [IP Checker](#5-ip-checker)
6. [Preprocesamiento ML](#6-preprocesamiento-ml)
7. [Gestor de Proyectos](#7-gestor-de-proyectos)
8. [Flujos de trabajo combinados](#8-flujos-de-trabajo-combinados)

---

## 1. Instalación y configuración

### Requisitos

- Python 3.8 o superior
- pip3
- Conexión a internet

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/CertAcademico/ScarpingMLOpsEc.git
cd ScarpingMLOpsEc

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar el entorno virtual
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 4. Instalar todas las dependencias
pip install -r requirements.txt
```

### Verificar instalación

```bash
python3 -c "import bs4, requests, rich, dns.resolver, whois; print('Todo instalado correctamente')"
```

Deberías ver: `Todo instalado correctamente`

> **Nota:** Cada vez que abras una nueva terminal debes activar el entorno virtual con `source venv/bin/activate` antes de usar las herramientas.

---

## 2. OSINT CLI — Dominios e IPs

La herramienta principal de inteligencia. Detecta automáticamente si le pasas un dominio o una IP y genera un reporte completo con tablas visuales.

### Modo interactivo

La forma más sencilla de empezar:

```bash
python3 osint_tools/osint_cli.py
```

Verás un menú así:

```
╭──────────────────────────────────────────────────────────────────────────────╮
│                                                                              │
│   Herramienta OSINT unificada                                                │
│   Analiza dominios e IPs: WHOIS · DNS · Geolocalización · Seguridad HTTP    │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

Opciones:
  1. Analizar dominio  (ej: github.com)
  2. Analizar IP       (ej: 8.8.8.8)
  3. Salir
```

### Analizar un dominio

```bash
python3 osint_tools/osint_cli.py github.com
```

El reporte incluye cuatro secciones:

**WHOIS** — quién registró el dominio y cuándo:
```
╭────────────────────┬──────────────────────────────╮
│ Registrador        │ MarkMonitor, Inc.             │
│ Creado             │ 2007-10-09                    │
│ Expira             │ 2026-10-09                    │
│ Nameserver 1       │ dns1.p08.nsone.net            │
╰────────────────────┴──────────────────────────────╯
```

**Registros DNS** — infraestructura técnica del dominio:
```
╭─────────┬────────────────────────────────────────╮
│ Tipo    │ Valor                                  │
├─────────┼────────────────────────────────────────┤
│ A       │ 140.82.113.3                           │
│ MX      │ 0 github-com.mail.protection.outlook.. │
│ NS      │ dns1.p08.nsone.net.                    │
│ TXT     │ v=spf1 ip4:192.30.252.0/22 ...        │
╰─────────┴────────────────────────────────────────╯
```

**HTTP / Seguridad** — qué tan bien configurado está el sitio:
```
╭────────────────────┬──────────────────╮
│ Status HTTP        │ 200              │
│ Servidor           │ github.com       │
│ HSTS               │ Sí               │  ← protege contra downgrade HTTPS
│ CSP                │ Sí               │  ← protege contra XSS
│ X-Frame-Options    │ deny             │
╰────────────────────┴──────────────────╯
```

**IP Asociada** — dónde está físicamente alojado el dominio.

### Analizar una IP

```bash
python3 osint_tools/osint_cli.py 8.8.8.8
```

Muestra geolocalización, ISP, ASN y si la IP pertenece a un proxy, VPN o datacenter.

### Exportar el reporte a JSON

```bash
python3 osint_tools/osint_cli.py google.com --output reporte_google.json
```

El archivo JSON contiene todos los datos en formato estructurado, listo para procesar con pandas u otras herramientas.

### Casos de uso prácticos

```bash
# Verificar dónde está alojada una empresa
python3 osint_tools/osint_cli.py empresa.com

# Identificar el proveedor de email (registro MX)
python3 osint_tools/osint_cli.py empresa.com
# → busca en la sección DNS el registro MX

# Comprobar si un sitio tiene HTTPS y cabeceras de seguridad
python3 osint_tools/osint_cli.py misitioweb.com

# Investigar una IP sospechosa
python3 osint_tools/osint_cli.py 185.220.101.45 --output ip_sospechosa.json
```

---

## 3. Web Scraper Universal

Extrae datos de cualquier página web. Funciona con HTML y también detecta respuestas JSON.

### Modo interactivo

```bash
python3 scraper_universal.py
```

El menú ofrece tres opciones:
1. **Scraping Básico** — extrae todos los elementos principales de una URL
2. **Scraping Avanzado** — usa un selector CSS para apuntar a elementos específicos
3. **Ejemplos predefinidos** — sitios de práctica ya configurados

### Scraping básico desde la terminal

```bash
python3 scraper_universal.py https://quotes.toscrape.com
```

Extrae automáticamente:
- Título y meta descripción
- Primeros 5 enlaces con texto y URL
- Encabezados H1, H2, H3
- Imágenes (alt + src)
- Primeros 3 párrafos
- Estadísticas: total de tags, divs, tablas, enlaces, etc.

### Scraping avanzado con selector CSS

Útil cuando sabes exactamente qué elemento del HTML quieres.

```bash
# Extraer todas las tarjetas de libros
python3 scraper_universal.py https://books.toscrape.com \
    --selector article.product_pod

# Extraer todos los encabezados h2
python3 scraper_universal.py https://news.ycombinator.com \
    --selector .titleline

# Extraer todos los enlaces del menú de navegación
python3 scraper_universal.py https://ejemplo.com \
    --selector nav a
```

**Cómo encontrar el selector correcto:**
1. Abre el sitio en Chrome o Firefox
2. Clic derecho sobre el elemento que quieres → "Inspeccionar"
3. Copia la clase CSS o el ID del elemento
4. Úsalo como selector: `.mi-clase` o `#mi-id`

### Exportar resultados

```bash
# Guardar en JSON (estructura completa)
python3 scraper_universal.py https://quotes.toscrape.com \
    --output citas.json

# Guardar en CSV (ideal para análisis en pandas/Excel)
python3 scraper_universal.py https://books.toscrape.com \
    --selector article.product_pod \
    --output libros.csv
```

### Cargar los datos en pandas

```python
import pandas as pd
import json

# Desde CSV
df = pd.read_csv("libros.csv")
print(df.head())

# Desde JSON
with open("citas.json") as f:
    datos = json.load(f)
print(datos["titulo"])
print(datos["estadisticas"])
```

### Sitios de práctica recomendados

| Sitio | URL | Qué practicar |
|---|---|---|
| Quotes to Scrape | `https://quotes.toscrape.com` | Texto, autores, tags |
| Books to Scrape | `https://books.toscrape.com` | Precios, títulos, ratings |
| Hacker News | `https://news.ycombinator.com` | Noticias, puntuaciones |
| HTTPBin | `https://httpbin.org/html` | HTML limpio de prueba |

---

## 4. Email Finder

Busca emails expuestos públicamente en las páginas principales de un dominio (inicio, contacto, about, team).

### Uso como script

```python
from osint_tools.email_finder import EmailFinder

# Crear el buscador para el dominio
finder = EmailFinder("empresa.com", delay=1)

# Buscar emails en las páginas principales
emails = finder.find_company_emails()

# Ver resultados
print(f"Emails encontrados: {len(emails)}")
for email in emails:
    print(f"  {email}")

# Guardar en archivo
finder.save_to_file("emails_empresa.txt")
```

### Parámetros

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `domain` | Dominio a analizar (sin http) | Requerido |
| `delay` | Segundos de espera entre peticiones | `1` |

### Qué busca y dónde

Revisa estas URLs automáticamente:
- `https://dominio.com`
- `https://www.dominio.com`
- `https://dominio.com/contact`
- `https://dominio.com/about`
- `https://dominio.com/team`

Busca emails en:
- Atributos `href="mailto:..."` de los enlaces
- Texto visible de la página (con expresión regular)

> **Nota:** Solo encuentra emails expuestos públicamente en el HTML de la página. No accede a bases de datos privadas.

---

## 5. IP Checker

Versión directa para analizar una IP puntual sin pasar por el menú OSINT.

```python
from osint_tools.ip_checker import IPChecker

# Analizar una IP
checker = IPChecker("1.1.1.1")
checker.print_report()

# Obtener solo la geolocalización
geo = checker.get_geolocation()
print(geo["country"])
print(geo["city"])

# Obtener el ISP
isp = checker.get_isp()
print(isp["provider"])

# Obtener análisis completo como diccionario
analisis = checker.get_full_analysis()
print(analisis)
```

> Para análisis más completos (con hostname reverso y detección de VPN) usa la herramienta OSINT CLI: `python3 osint_tools/osint_cli.py 1.1.1.1`

---

## 6. Preprocesamiento ML

Pipeline reutilizable para limpiar y preparar datos antes de entrenar modelos.

### Cargar datos

```python
from ml_data_science.preprocessing import DataPreprocessor

# Desde archivo CSV
proc = DataPreprocessor("datos.csv")

# Desde archivo Excel
proc = DataPreprocessor("datos.xlsx")

# Desde un DataFrame de pandas
import pandas as pd
df = pd.read_csv("datos.csv")
proc = DataPreprocessor(df)
```

### Ver información del dataset

```python
proc.get_info()
```

Muestra: dimensiones, tipos de columnas, valores faltantes por columna y estadísticas descriptivas.

### Pipeline completo paso a paso

```python
# 1. Ver el estado inicial
proc.get_info()

# 2. Manejar valores faltantes
proc.handle_missing_values(strategy="mean")     # media
# proc.handle_missing_values(strategy="median") # mediana
# proc.handle_missing_values(strategy="most_frequent") # moda

# 3. Eliminar filas duplicadas
proc.remove_duplicates()

# 4. Eliminar outliers
proc.remove_outliers(method="iqr")     # rango intercuartil (recomendado)
# proc.remove_outliers(method="zscore") # desviación estándar

# 5. Codificar variables categóricas (texto → número)
proc.encode_categorical()                       # todas las columnas de texto
# proc.encode_categorical(["ciudad", "estado"]) # columnas específicas

# 6. Escalar variables numéricas
proc.scale_features(method="standard")   # media=0, std=1 (para ML)
# proc.scale_features(method="minmax")   # rango [0, 1] (para redes neuronales)

# 7. Ver resultado
df_limpio = proc.get_data()
print(df_limpio.head())

# 8. Guardar
proc.save("datos_limpios.csv")
proc.save("datos_limpios.xlsx")

# Si algo salió mal, vuelves al estado original
proc.reset()
```

### Eliminar columnas irrelevantes

```python
# Antes de escalar, eliminar columnas que no aportan al modelo
proc.drop_columns(["id", "nombre", "fecha_registro"])
```

### Ejemplo completo con dataset real

```python
import pandas as pd
from ml_data_science.preprocessing import DataPreprocessor

# Dataset de ejemplo
data = pd.DataFrame({
    "edad":    [25, 30, None, 35, 200, 28],   # tiene faltante y outlier
    "ingreso": [30000, 50000, 60000, 55000, None, 45000],
    "ciudad":  ["Bogotá", "Medellín", "Bogotá", "Cali", "Bogotá", "Bogotá"],
    "compro":  ["Sí", "No", "Sí", "Sí", "No", "Sí"]
})

proc = DataPreprocessor(data)
proc.get_info()                              # ver estado inicial
proc.handle_missing_values("median")         # rellenar faltantes
proc.remove_duplicates()                     # sin duplicados
proc.remove_outliers(method="iqr")           # quitar outlier de edad=200
proc.encode_categorical(["ciudad", "compro"])  # texto → número
proc.scale_features(method="standard")       # normalizar

X = proc.get_data().drop(columns=["compro"])  # features
y = data["compro"]                             # target original
print("Datos listos para entrenamiento:")
print(X.head())
```

---

## 7. Gestor de Proyectos

Organiza tus análisis en proyectos con estructura estandarizada.

### Crear un proyecto

```bash
python3 tools/project_manager.py --create "Análisis Empresa XYZ" \
    --type osint \
    --description "Investigación OSINT sobre dominio empresaxyz.com"
```

Tipos disponibles: `general`, `ml`, `osint`, `scraping`

Esto crea automáticamente:
```
projects/my_projects/Análisis Empresa XYZ/
├── data/
│   ├── raw/          ← datos originales sin modificar
│   ├── processed/    ← datos limpios
│   └── external/     ← fuentes externas
├── scripts/
│   └── main.py       ← plantilla lista para usar
├── notebooks/
├── models/
├── results/
├── docs/
├── README.md
└── config.json
```

### Listar proyectos

```bash
python3 tools/project_manager.py --list
```

### Abrir un proyecto (ver su contenido)

```bash
python3 tools/project_manager.py --open "Análisis Empresa XYZ"
```

### Ver estadísticas generales

```bash
python3 tools/project_manager.py --stats
```

### Exportar resultados

```bash
python3 tools/project_manager.py --export "Análisis Empresa XYZ" --format json
```

---

## 8. Flujos de trabajo combinados

### Flujo 1: Investigación OSINT completa de un dominio

```bash
# Paso 1: Reporte completo del dominio
python3 osint_tools/osint_cli.py empresa.com --output resultados/empresa_osint.json

# Paso 2: Buscar emails públicos
python3 -c "
from osint_tools.email_finder import EmailFinder
f = EmailFinder('empresa.com')
f.find_company_emails()
f.save_to_file('resultados/emails.txt')
"

# Paso 3: Scraping del sitio público
python3 scraper_universal.py https://empresa.com --output resultados/empresa_web.json
```

### Flujo 2: Scraping + análisis de datos con pandas

```bash
# Paso 1: Extraer datos del sitio
python3 scraper_universal.py https://books.toscrape.com \
    --selector article.product_pod \
    --output datos_libros.csv
```

```python
# Paso 2: Preprocesar y analizar
import pandas as pd
from ml_data_science.preprocessing import DataPreprocessor

df = pd.read_csv("datos_libros.csv")
proc = DataPreprocessor(df)
proc.get_info()
proc.handle_missing_values()
proc.remove_duplicates()
proc.save("datos_libros_limpios.csv")

print(df.describe())
```

### Flujo 3: Proyecto completo organizado

```bash
# 1. Crear proyecto
python3 tools/project_manager.py --create "Mi Análisis" --type scraping

# 2. Scraping → data/raw/
python3 scraper_universal.py https://quotes.toscrape.com \
    --output "projects/my_projects/Mi Análisis/data/raw/quotes.json"

# 3. Procesar → data/processed/
python3 -c "
from ml_data_science.preprocessing import DataPreprocessor
import pandas as pd, json

with open('projects/my_projects/Mi Análisis/data/raw/quotes.json') as f:
    datos = json.load(f)

df = pd.DataFrame(datos['parrafos'], columns=['texto'])
proc = DataPreprocessor(df)
proc.save('projects/my_projects/Mi Análisis/data/processed/quotes_clean.csv')
"

# 4. Ver el proyecto
python3 tools/project_manager.py --open "Mi Análisis"
```

---

## Referencia rápida de comandos

```bash
# OSINT
python3 osint_tools/osint_cli.py DOMINIO_O_IP
python3 osint_tools/osint_cli.py DOMINIO_O_IP --output archivo.json

# Scraper
python3 scraper_universal.py URL
python3 scraper_universal.py URL --output archivo.json
python3 scraper_universal.py URL --selector ".clase" --output archivo.csv

# Proyectos
python3 tools/project_manager.py --create "Nombre" --type [general|ml|osint|scraping]
python3 tools/project_manager.py --list
python3 tools/project_manager.py --open "Nombre"
python3 tools/project_manager.py --stats
```

---

## Solución de problemas frecuentes

**`ModuleNotFoundError`** — el entorno virtual no está activado:
```bash
source venv/bin/activate
```

**`ConnectionError` en scraping** — verifica tu conexión o prueba con otra URL.

**WHOIS devuelve error** — algunos TLDs (`.co`, `.io`) tienen WHOIS restringido. Los registros DNS siguen funcionando.

**El scraper muestra pocos datos** — el sitio probablemente usa JavaScript (React, Vue, Angular). BeautifulSoup solo lee el HTML inicial; para esos sitios se requiere Playwright o Selenium.

---

**Versión:** 2.0 — Mayo 2025
