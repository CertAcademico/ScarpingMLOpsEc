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

Cada respuesta se escribe en `data/osint_evidence/` y se registra en `index.json`, junto con la URL final, fecha UTC, tipo de contenido, estado HTTP, tamaño y SHA-256 del cuerpo recibido. También se conservan algunas cabeceras informativas, sin guardar cookies. El mapa se organiza por fuerzas: la URL inicial queda al centro y cada nivel de profundidad forma un anillo. El color indica el estado HTTP (verde 2xx, ámbar 403/redirección, rojo error), el tamaño los enlaces encontrados y las flechas el sentido de cada enlace. Los enlaces no capturados se agrupan por dominio con un contador; un clic los despliega. Al pasar el cursor se resaltan las conexiones del nodo, y al seleccionarlo se anima el camino desde la URL inicial. Los nodos se pueden arrastrar (quedan fijados; doble clic los libera), y con «Centrar» se encuadra todo el grafo. Con la preferencia del sistema de reducir movimiento, las animaciones se desactivan. La interfaz muestra y permite copiar la ruta de cada captura. El análisis se puede exportar en JSON.

Si el servidor devuelve HTTP 403, la aplicación conserva y calcula el hash de esa respuesta de denegación. Esto documenta el acceso rechazado; no recupera el contenido protegido ni intenta eludir el control del sitio.

El perfil online muestra el dominio y las IP públicas resueltas, detalles disponibles del certificado TLS, nombre y organización declarados en metadatos, y URL canónica. Estos son indicios técnicos/declarativos y no prueban por sí solos la identidad legal del operador.

El descargador acepta solo destinos HTTP/HTTPS públicos, vuelve a validar los destinos de redirección, limita cada respuesta a 4 MB y sigue como máximo cinco redirecciones. Los datos extraídos reflejan el HTML recibido; las páginas que generan su contenido solo con JavaScript pueden requerir un navegador automatizado en una iteración posterior.
