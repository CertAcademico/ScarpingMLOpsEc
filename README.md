# ScrapingMLOpsEc — Web Scraping · OSINT · Data Science

Plataforma educativa y funcional para **Data Scientists** que cubre web scraping, inteligencia de fuentes abiertas (OSINT) y preprocesamiento de datos para Machine Learning.

---

## Estructura del Proyecto

```
ScrapingMLOpsEc/
├── scraper_universal.py          ← Scraper web (cualquier URL, exporta CSV/JSON)
├── scraping_real.py              ← Ejemplos de scraping en sitios reales
├── ejemplos_basicos.py           ← Introducción a BeautifulSoup4
├── ejercicios_practicos.py       ← Ejercicios guiados
│
├── osint_tools/
│   ├── osint_cli.py              ← OSINT unificado: dominio + IP (NUEVO)
│   ├── email_finder.py           ← Búsqueda de emails por dominio
│   └── ip_checker.py             ← Geolocalización e ISP de una IP
│
├── ml_data_science/
│   └── preprocessing.py          ← Pipeline de preprocesamiento para ML
│
├── tools/
│   └── project_manager.py        ← Gestor de proyectos de análisis
│
├── requirements.txt              ← Todas las dependencias
└── CHEAT_SHEET.md                ← Referencia rápida de BeautifulSoup4
```

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/CertAcademico/ScarpingMLOpsEc.git
cd ScrapingMLOpsEc

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

## Herramientas

### Web Scraper Universal

Extrae información estructurada de cualquier URL. Detecta automáticamente HTML y JSON, y puede exportar los resultados.

```bash
# Scraping básico (muestra en pantalla)
python3 scraper_universal.py https://quotes.toscrape.com

# Exportar a JSON
python3 scraper_universal.py https://quotes.toscrape.com --output resultado.json

# Scraping con selector CSS y exportar a CSV
python3 scraper_universal.py https://books.toscrape.com \
    --selector article.product_pod \
    --output libros.csv

# Modo interactivo (menú)
python3 scraper_universal.py
```

**Qué extrae:**
- Título, meta descripción
- Encabezados H1/H2/H3
- Primeros 10 enlaces con texto y URL
- Imágenes con alt y src
- Párrafos y listas
- Estadísticas de la página (total de tags, divs, tablas, etc.)

---

### OSINT CLI — Análisis de Dominios e IPs

Herramienta unificada que detecta automáticamente si el objetivo es un dominio o IP y genera un reporte visual completo con tablas coloreadas.

```bash
# Analizar dominio
python3 osint_tools/osint_cli.py github.com

# Analizar IP
python3 osint_tools/osint_cli.py 8.8.8.8

# Analizar y exportar a JSON
python3 osint_tools/osint_cli.py google.com --output reporte.json

# Modo interactivo (menú)
python3 osint_tools/osint_cli.py
```

**Para dominios muestra:**

| Sección | Datos |
|---|---|
| WHOIS | Registrador, fechas de creación/expiración, nameservers, estado |
| DNS | Registros A, AAAA, MX, NS, TXT, CNAME, SOA |
| HTTP / Seguridad | Status, servidor, HSTS, CSP, X-Frame-Options, Referrer-Policy |
| IP asociada | País, ciudad, ISP, ASN, detección de proxy/VPN |

**Para IPs muestra:**

| Sección | Datos |
|---|---|
| Geolocalización | País, región, ciudad, coordenadas, timezone |
| Red | ISP, organización, ASN |
| Seguridad | Es proxy/VPN, es hosting/datacenter |
| Reverso | Hostname (PTR) |

---

### Email Finder

Busca emails expuestos públicamente en las páginas principales de un dominio.

```python
from osint_tools.email_finder import EmailFinder

finder = EmailFinder("empresa.com")
emails = finder.find_company_emails()
finder.save_to_file("emails.txt")
```

---

### IP Checker

Geolocalización e ISP de una IP puntual.

```python
from osint_tools.ip_checker import IPChecker

checker = IPChecker("1.1.1.1")
checker.print_report()
```

---

### Preprocesamiento ML

Pipeline de limpieza y transformación de datos para Machine Learning.

```python
from ml_data_science.preprocessing import DataPreprocessor

proc = DataPreprocessor("datos.csv")
proc.get_info()
proc.handle_missing_values(strategy="mean")
proc.remove_duplicates()
proc.remove_outliers(method="iqr")
proc.encode_categorical()
proc.scale_features(method="standard")
proc.save("datos_limpios.csv")
```

**Métodos disponibles:**

| Método | Descripción |
|---|---|
| `handle_missing_values(strategy)` | Imputa faltantes: `mean`, `median`, `most_frequent` |
| `remove_duplicates()` | Elimina filas duplicadas |
| `remove_outliers(method)` | IQR o Z-score |
| `encode_categorical(columns)` | Label Encoding de variables categóricas |
| `scale_features(method)` | `standard` (StandardScaler) o `minmax` |
| `reset()` | Vuelve a los datos originales |

---

### Gestor de Proyectos

Crea y gestiona proyectos de análisis de datos con estructura estandarizada.

```bash
# Crear proyecto
python3 tools/project_manager.py --create "Mi Análisis" --type ml

# Listar proyectos
python3 tools/project_manager.py --list

# Abrir proyecto (ver estructura y archivos)
python3 tools/project_manager.py --open "Mi Análisis"

# Estadísticas
python3 tools/project_manager.py --stats

# Eliminar
python3 tools/project_manager.py --delete "Mi Análisis"
```

**Estructura generada por proyecto:**
```
Mi Análisis/
├── data/raw/          ← Datos crudos (sin tocar)
├── data/processed/    ← Datos limpios
├── data/external/     ← Fuentes externas
├── scripts/           ← Scripts Python
├── notebooks/         ← Jupyter Notebooks
├── models/            ← Modelos entrenados
├── results/           ← Resultados y reportes
├── docs/
├── README.md
└── config.json
```

---

## Dependencias

```
beautifulsoup4   Web scraping / parsing HTML
requests         Peticiones HTTP
lxml             Parser HTML rápido
dnspython        Consultas DNS (OSINT)
python-whois     Consultas WHOIS (OSINT)
rich             Presentación visual en terminal
pandas           Análisis de datos
numpy            Computación numérica
scikit-learn     Machine Learning
scipy            Estadísticas
openpyxl         Lectura/escritura Excel
```

---

## Consideraciones éticas

- Respeta el archivo `robots.txt` del sitio objetivo.
- No automatices peticiones masivas sin control de velocidad.
- Usa estas herramientas únicamente en sistemas y dominios para los que tienes autorización.
- Las herramientas OSINT consultan únicamente información pública disponible en internet.

---

**Versión:** 2.0 — Mayo 2025
