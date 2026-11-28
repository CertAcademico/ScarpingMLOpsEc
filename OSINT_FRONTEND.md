# F0R3nsic Web · interfaz local de OSINT web

La interfaz permite ingresar una URL, descubrir páginas enlazadas, visualizar sus relaciones, generar un perfil de identidad online con señales públicas y guardar cada respuesta web como evidencia con hash SHA-256.

## Iniciar

Desde la raíz del proyecto, con las dependencias de `requirements.txt` instaladas. En macOS/Linux, inicia el entorno virtual del proyecto para usar esas dependencias:

```bash
venv/bin/python app.py
```

En Windows usa `venv\\Scripts\\python.exe app.py`. Si aún no existe el entorno o faltan dependencias, créalo con `python3 -m venv venv` e instala con `venv/bin/pip install -r requirements.txt`.

Abre `http://127.0.0.1:8000` en el navegador. El servidor escucha solo en la interfaz local de la máquina.

## Parámetros

- **Páginas máximas:** de 1 a 30.
- **Profundidad:** hasta dos niveles de enlaces desde la URL inicial.
- **Tiempo límite:** de 3 a 20 segundos por página.
- **Pausa:** de 0 a 3 segundos entre solicitudes.
- **Mantenerse en el dominio inicial:** limita las páginas que se visitan; los enlaces externos encontrados se muestran como relaciones.

La exploración se ve en vivo: cada página aparece en el mapa en cuanto se captura, junto a la página que la enlazó, y una barra sobre el mapa muestra la URL que se consulta, las páginas capturadas, las que esperan en cola y los errores. El botón «Detener exploración» corta el rastreo y conserva lo capturado hasta ese momento. La cámara sigue el crecimiento del grafo hasta que la persona mueve o acerca el mapa; «Centrar» vuelve a activar el seguimiento. Internamente, `POST /api/explore/stream` envía un evento JSON por línea (`start`, `fetching`, `page`, `error`, `done`); `POST /api/explore` sigue disponible y devuelve el análisis completo al terminar.

Cada respuesta se escribe en `data/osint_evidence/` y se registra en `index.json`, junto con la URL final, el origen de la consulta (IP de salida y ubicación), fecha UTC, tipo de contenido, estado HTTP, tamaño y SHA-256 del cuerpo recibido. También se conservan algunas cabeceras informativas, sin guardar cookies. El mapa se organiza por fuerzas: la URL inicial queda al centro y cada nivel de profundidad forma un anillo. El color indica el estado HTTP (verde 2xx, ámbar 403/redirección, rojo error), el tamaño los enlaces encontrados y las flechas el sentido de cada enlace. Los enlaces no capturados se agrupan por dominio con un contador; un clic los despliega. Al pasar el cursor se resaltan las conexiones del nodo, y al seleccionarlo se anima el camino desde la URL inicial. Los nodos se pueden arrastrar (quedan fijados; doble clic los libera), y con «Centrar» se encuadra todo el grafo. Con la preferencia del sistema de reducir movimiento, las animaciones se desactivan. La interfaz muestra y permite copiar la ruta de cada captura. El análisis se puede exportar en JSON.

Si el servidor devuelve HTTP 403, la aplicación conserva y calcula el hash de esa respuesta de denegación. Esto documenta el acceso rechazado; no recupera el contenido protegido ni intenta eludir el control del sitio.

El perfil online muestra el dominio y las IP públicas resueltas, detalles disponibles del certificado TLS, nombre y organización declarados en metadatos, y URL canónica. Estos son indicios técnicos/declarativos y no prueban por sí solos la identidad legal del operador.

El descargador acepta solo destinos HTTP/HTTPS públicos, vuelve a validar los destinos de redirección, limita cada respuesta a 4 MB y sigue como máximo cinco redirecciones. Los datos extraídos reflejan el HTML recibido; las páginas que generan su contenido solo con JavaScript pueden requerir un navegador automatizado en una iteración posterior.

## Diagnóstico de respuestas y monitoreo

Cada página capturada incluye un diagnóstico de la respuesta: identifica protecciones antibots (Cloudflare, Akamai, Imperva, Sucuri, CloudFront) por sus cabeceras y por los desafíos de verificación del cuerpo, y distingue límite de solicitudes (429 o `Retry-After`), autenticación requerida, acceso denegado, recurso inexistente y errores del servidor. Para ello se conservan cabeceras informativas como `Server`, `Via`, `CF-Ray` o `CF-Mitigated`; nunca cookies.

Cuando un sitio está en línea pero rechaza la consulta, la pestaña **Monitoreo** permite seguirlo en el tiempo. Se crea desde el detalle de cualquier nodo («Monitorizar esta URL») o escribiendo la URL en la pestaña. Cada intervalo (de 5 minutos a 24 horas) la app hace **una sola consulta**, sin seguir enlaces, y registra:

- estado HTTP, causa probable y tiempo de respuesta;
- SHA-256 del cuerpo recibido, en cada consulta;
- huella de contenido: hash del contenido sin scripts, estilos ni tokens volátiles. Las páginas de desafío antibots cambian su SHA-256 en cada consulta aunque muestren lo mismo; la huella evita registrar esos falsos cambios. La captura se guarda en `data/osint_evidence/` solo cuando la huella cambia (si no, se referencia la anterior);
- IP resueltas y certificado TLS, consultados sin caché en cada chequeo;
- cambios respecto a la consulta anterior: estado, contenido, IP o certificado.

- origen de la consulta: IP pública de salida de este equipo (con VPN, la del servidor VPN), ciudad, país y red (ASN), según ipinfo.io o, si falla, ipwho.is. Un cambio de salida se marca en la línea de tiempo como `salida`, para ver si el sitio responde distinto según desde dónde se consulta. La herramienta no cambia de IP por sí misma;
- snapshot visual (PNG), por defecto cada 3 horas y también bajo demanda con «Snapshot ahora». Se genera con Playwright a partir del HTML ya capturado, con JavaScript desactivado y sin conexión: no se ejecuta código del sitio ni se descarga nada más, y la imagen corresponde exactamente a la captura con hash. En cada snapshot el HTML se guarda de nuevo aunque la huella no haya cambiado.

Si el sitio envía `Retry-After`, la siguiente consulta respeta ese tiempo. La línea de tiempo muestra el estado como franja (las consultas sin respuesta aparecen rayadas) y, debajo, el tiempo de respuesta, con las marcas de cambio sobre ambas. La tabla lista cada consulta con la ruta de su evidencia, y el historial se exporta en JSON o CSV.

### Capturas manuales del analista

Cuando el sitio bloquea las consultas automatizadas (por ejemplo, un desafío de Cloudflare), el analista puede ver la página en su navegador, guardarla (Archivo › Guardar como… o una captura de pantalla) e incorporarla con «Importar captura manual». Se admiten HTML, MHTML, PNG, JPG y PDF de hasta 25 MB. El tipo se confirma con la firma del archivo, no solo con su extensión. Al recibirlo, la app calcula su SHA-256, lo guarda en `data/osint_evidence/` y lo añade a la línea de tiempo con la fecha en que se vio (no puede ser futura), la nota del analista, el nombre original y la salida de este equipo en el momento de importarlo, que puede diferir de la usada por el navegador. Los HTML importados se convierten además en un snapshot visual con el mismo método sin JavaScript.

El informe pericial incluye una sección de **relacionamiento de evidencia digital**: un diagrama de cadena de custodia (el informe sella la línea de tiempo, que registra el SHA-256 de cada evidencia), la tabla de derivaciones (cada snapshot enlazado a su HTML de origen por SHA-256) y los comandos para reverificar la integridad de extremo a extremo.

Las capturas manuales aparecen como rombos sobre la línea de tiempo y como filas propias en la tabla. No modifican el estado ni los tiempos de respuesta del monitor, que solo reflejan las consultas automáticas.

Los snapshots requieren Playwright y Chromium: `venv/bin/pip install -r requirements.txt` y `venv/bin/python -m playwright install chromium`. Sin ellos, el monitoreo sigue funcionando y la pestaña indica cómo instalarlos. La app solo sirve los snapshots PNG (`/evidence/<archivo>.png`); el HTML capturado nunca se abre en el navegador, porque ejecutaría código del sitio dentro de la app.

Los monitores y sus líneas de tiempo se guardan en `data/monitors/` y continúan al reiniciar la app; las consultas solo se ejecutan mientras `app.py` esté en marcha. Eliminar un monitor borra su línea de tiempo, pero conserva las capturas.

## Vigilancia DNS

El interruptor **DNS** de cada monitor activa la vigilancia de la resolución del dominio. Al encenderlo se toma una línea base. Desde ese momento, cada consulta del monitor obtiene sin caché los registros A, AAAA, CNAME, NS, MX, TXT, CAA y SOA (con TTL, PTR de las IP y resolvedores usados) y los compara con la observación anterior. Un cambio se marca como `dns` en la línea de tiempo (línea violeta), con los valores añadidos y retirados por tipo de registro. Un cambio del número de serie SOA indica que el titular editó la zona. Encender y apagar el interruptor queda registrado como evento, para que el informe muestre qué tramos estuvieron vigilados. Las consultas DNS usan los resolvedores del sistema, no el proxy HTTP.

## Traza de red

«Traza de red» ejecuta `traceroute` (`tracert` en Windows) hacia la IP del servidor. Para cada salto obtiene el hostname (PTR) y el sistema autónomo y titular de la red (servicio DNS público de Team Cymru). Añade además el WHOIS del dominio (registrador, fechas, servidores DNS declarados, estado y titular si es público) y una fotografía DNS. El resultado se guarda en la línea de tiempo con la salida original del comando, y se indica si la ruta cambió respecto a la traza anterior. Los saltos que no responden se conservan como `*`: muchos routers y CDN ignoran estas sondas.

## Informe pericial

«Informe pericial» genera un documento HTML autocontenido, sin JavaScript ni recursos remotos, listo para imprimir o guardar en PDF desde el navegador. Contiene: ficha (n.º de informe, caso, perito, periodo), resumen ejecutivo con cifras y dictamen descriptivo, metodología, línea de tiempo gráfica (estado HTTP, tiempo de respuesta, tramos de vigilancia DNS, cambios, lagunas, trazas y capturas manuales), distribución de respuestas, cronología de hechos, cambios y registros DNS, traza de ruta, WHOIS, servidor y certificado TLS, origen de las consultas, inventario de evidencias con SHA-256 y snapshots, limitaciones e integridad.

Se guarda en `data/reports/informe_<monitor>_<fecha>.html`, junto con un `.sha256` verificable con `shasum -a 256 -c`, y se registra en `data/reports/index.json`. El informe incluye el SHA-256 de la línea de tiempo en el momento de emitirlo, y la emisión queda como evento en la propia línea de tiempo. Las **lagunas** son los intervalos entre consultas mayores que el doble del intervalo configurado: en ellos no hay observaciones.

### Análisis asistido por IA (opcional, con tokens limitados)

Al emitir el informe se puede marcar «Incluir análisis técnico asistido por IA». La app envía a la API de Anthropic **solo un resumen estructurado** (métricas, hechos, DNS, traza y WHOIS), nunca las capturas ni el HTML del sitio. El texto se incluye en una sección propia, marcada como ayuda de redacción y no como evidencia, con el modelo, los tokens usados y el SHA-256 de la entrada. Requiere `ANTHROPIC_API_KEY` definida al iniciar `app.py`. Límites configurables por variable de entorno:

- `F0R3NSIC_IA_TOKENS_DIA`: tokens por día UTC (entrada + salida). Por defecto, 50 000.
- `F0R3NSIC_IA_MAX_SALIDA`: tokens de respuesta por informe. Por defecto, 2 500.
- `F0R3NSIC_IA_MAX_ENTRADA`: tamaño máximo del resumen enviado. Por defecto, 12 000.
- `F0R3NSIC_IA_MODELO`: por defecto, `claude-opus-5-5`, con esfuerzo bajo y respaldo automático de modelo si la solicitud se rechaza.

Antes de cada llamada se cuentan los tokens de entrada y se rechaza la solicitud si no cabe en lo que queda del día. Si el mismo resumen ya se analizó, se reutiliza la respuesta guardada en `data/ia_cache/` sin consumir tokens. El consumo diario se guarda en `data/ia_uso.json`.
