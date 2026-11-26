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

Cada respuesta se escribe en `data/osint_evidence/` y se registra en `index.json`, junto con la URL final, fecha UTC, tipo de contenido, estado HTTP, tamaño y SHA-256 del cuerpo recibido. También se conservan algunas cabeceras informativas, sin guardar cookies. El mapa se organiza por fuerzas: la URL inicial queda al centro y cada nivel de profundidad forma un anillo. El color indica el estado HTTP (verde 2xx, ámbar 403/redirección, rojo error), el tamaño los enlaces encontrados y las flechas el sentido de cada enlace. Los enlaces no capturados se agrupan por dominio con un contador; un clic los despliega. Al pasar el cursor se resaltan las conexiones del nodo, y al seleccionarlo se anima el camino desde la URL inicial. Los nodos se pueden arrastrar (quedan fijados; doble clic los libera), y con «Centrar» se encuadra todo el grafo. Con la preferencia del sistema de reducir movimiento, las animaciones se desactivan. La interfaz muestra y permite copiar la ruta de cada captura. El análisis se puede exportar en JSON.

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

Si el sitio envía `Retry-After`, la siguiente consulta respeta ese tiempo. La línea de tiempo muestra el estado como franja (las consultas sin respuesta aparecen rayadas) y, debajo, el tiempo de respuesta, con las marcas de cambio sobre ambas. La tabla lista cada consulta con la ruta de su evidencia, y el historial se exporta en JSON o CSV.

Los monitores y sus líneas de tiempo se guardan en `data/monitors/` y continúan al reiniciar la app; las consultas solo se ejecutan mientras `app.py` esté en marcha. Eliminar un monitor borra su línea de tiempo, pero conserva las capturas.
