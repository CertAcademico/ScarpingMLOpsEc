"""Interfaz local para explorar URLs y conservar evidencia web."""

import hashlib
import ipaddress
import json
import re
import socket
import ssl
import threading
import time
import uuid
from collections import deque
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
EVIDENCE_DIR = ROOT / "data" / "osint_evidence"
INDEX_FILE = EVIDENCE_DIR / "index.json"
MAX_BODY_BYTES = 4 * 1024 * 1024
USER_AGENT = "ScrapingMLOpsEc/1.0 (local OSINT research tool)"
_index_lock = threading.Lock()
# Cabeceras informativas que se conservan; permiten identificar CDN/antibots. Nunca se guardan cookies.
CAPTURED_HEADERS = ("Content-Type", "Date", "Server", "Content-Length", "Retry-After", "Via", "CF-Ray", "CF-Mitigated",
                    "CF-Cache-Status", "X-Cache", "X-Amz-Cf-Id", "X-Akamai-Transformed", "X-Iinfo", "X-CDN",
                    "X-Sucuri-ID", "WWW-Authenticate")


def public_http_url(value):
    value = value.strip()
    if not value:
        raise ValueError("Escribe una URL para comenzar.")
    if not urlparse(value).scheme:
        value = "https://" + value
    parts = urlparse(value)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("La URL debe usar http:// o https:// y tener un dominio válido.")
    if parts.username or parts.password:
        raise ValueError("No se admiten credenciales dentro de la URL.")
    try:
        addresses = {ipaddress.ip_address(parts.hostname.strip("[]"))}
    except ValueError:
        try:
            addresses = {ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM)}
        except socket.gaierror as exc:
            raise ValueError(f"No se pudo resolver el dominio: {parts.hostname}") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Por seguridad, solo se permiten destinos públicos de Internet.")
    path = parts.path or "/"
    return urlunparse((parts.scheme, parts.netloc, path, "", parts.query, ""))


def domain_of(url):
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def download(url, timeout):
    current = public_http_url(url)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.5"})
    for _ in range(6):
        current = public_http_url(current)
        response = session.get(current, timeout=timeout, allow_redirects=False, stream=True)
        if response.is_redirect or response.is_permanent_redirect:
            target = response.headers.get("Location")
            response.close()
            if not target:
                raise ValueError("El sitio devolvió una redirección sin destino.")
            current = urljoin(current, target)
            continue
        body = bytearray()
        for chunk in response.iter_content(65536):
            body.extend(chunk)
            if len(body) > MAX_BODY_BYTES:
                response.close()
                raise ValueError("La página supera el límite de 4 MB por captura.")
        content_type = response.headers.get("Content-Type", "")
        final_url, status = response.url, response.status_code
        captured_headers = {
            name: response.headers[name]
            for name in CAPTURED_HEADERS
            if name in response.headers
        }
        response.close()
        return public_http_url(final_url), bytes(body), content_type, status, captured_headers
    raise ValueError("Demasiadas redirecciones.")


def save_evidence(url, body, content_type, status, response_headers=None):
    digest = hashlib.sha256(body).hexdigest()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    capture_id = f"{stamp}_{digest[:12]}"
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    extension = ".json" if "json" in content_type.lower() else ".html"
    (EVIDENCE_DIR / f"{capture_id}{extension}").write_bytes(body)
    record = {
        "id": capture_id,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "status": status,
        "content_type": content_type,
        "response_headers": response_headers or {},
        "bytes": len(body),
        "sha256": digest,
        "file": f"{capture_id}{extension}",
    }
    with _index_lock:
        records = json.loads(INDEX_FILE.read_text("utf-8")) if INDEX_FILE.exists() else []
        records.append(record)
        INDEX_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


@lru_cache(maxsize=128)
def resolver_ips_publicas(host, port):
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)}
        if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
            return ()
        return tuple(sorted(addresses))
    except (socket.gaierror, OSError, ValueError):
        return ()


@lru_cache(maxsize=128)
def certificado_tls(host, port, addresses):
    try:
        context = ssl.create_default_context()
        tls_socket = None
        for address in addresses:
            try:
                raw_socket = socket.create_connection((address, port), timeout=3)
                tls_socket = context.wrap_socket(raw_socket, server_hostname=host)
                break
            except (OSError, ssl.SSLError):
                continue
        if tls_socket is None:
            return None
        with tls_socket:
            cert = tls_socket.getpeercert()

        def common_name(items):
            return next((value for group in items for key, value in group if key == "commonName"), None)

        return {
            "sujeto": common_name(cert.get("subject", ())),
            "emisor": common_name(cert.get("issuer", ())),
            "valido_hasta": cert.get("notAfter"),
            "nombres_alternativos": [value for kind, value in cert.get("subjectAltName", ()) if kind == "DNS"][:20],
        }
    except (OSError, ssl.SSLError, ValueError):
        return None


def identidad_sitio(url, soup=None):
    parts = urlparse(url)
    host = (parts.hostname or "").lower()
    identity = {
        "url_final": url,
        "dominio": host,
        "https": parts.scheme == "https",
        "certificado_tls": None,
        "ips_resueltas": [],
        "nombre_declarado": None,
        "organizacion_declarada": None,
        "url_canonica": None,
        "canonica_mismo_host": None,
        "descripcion_declarada": None,
    }
    port = parts.port or (443 if parts.scheme == "https" else 80)
    addresses = resolver_ips_publicas(host, port)
    identity["ips_resueltas"] = list(addresses[:12])
    if parts.scheme == "https" and addresses:
        identity["certificado_tls"] = certificado_tls(host, port, addresses)

    if soup is None:
        return identity

    def meta_value(selector, attribute="content"):
        tag = soup.select_one(selector)
        return tag.get(attribute, "").strip()[:300] if tag else ""

    canonical = soup.find("link", rel=lambda value: value and "canonical" in value)
    if canonical and canonical.get("href"):
        identity["url_canonica"] = urljoin(url, canonical["href"].strip())
        canonical_host = (urlparse(identity["url_canonica"]).hostname or "").lower().removeprefix("www.")
        identity["canonica_mismo_host"] = canonical_host == host.removeprefix("www.")
    identity["nombre_declarado"] = (
        meta_value('meta[property="og:site_name"]')
        or meta_value('meta[name="application-name"]')
        or None
    )
    identity["descripcion_declarada"] = meta_value('meta[name="description"]') or None

    scripts = soup.select('script[type="application/ld+json"]')[:20]
    for script in scripts:
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            item = stack.pop()
            if not isinstance(item, dict):
                continue
            graph = item.get("@graph")
            if isinstance(graph, list):
                stack.extend(graph[:50])
            types = item.get("@type", [])
            types = [types] if isinstance(types, str) else types
            types_lower = {str(value).lower() for value in types}
            name = item.get("name")
            if name and not identity["nombre_declarado"]:
                identity["nombre_declarado"] = str(name)[:180]
            if name and any(value.endswith(("organization", "collegeoruniversity", "school")) for value in types_lower):
                identity["organizacion_declarada"] = str(name)[:180]
            if name and any(value.endswith("website") for value in types_lower) and not identity["nombre_declarado"]:
                identity["nombre_declarado"] = str(name)[:180]
            for key in ("mainEntity", "publisher", "provider"):
                nested = item.get(key)
                if isinstance(nested, dict):
                    stack.append(nested)
    return identity


def diagnosticar_respuesta(status, headers=None, body=b""):
    """Clasifica la causa probable de una respuesta a partir de su estado, cabeceras y cuerpo."""
    h = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    text = (body or b"")[:20000].decode("utf-8", errors="ignore").lower()
    server = h.get("server", "").lower() + " " + h.get("via", "").lower()
    proveedor = None
    if "cf-ray" in h or "cloudflare" in server:
        proveedor = "Cloudflare"
    elif "x-akamai-transformed" in h or "akamai" in server:
        proveedor = "Akamai"
    elif "x-iinfo" in h or "incapsula" in text:
        proveedor = "Imperva"
    elif "x-sucuri-id" in h or "sucuri" in server:
        proveedor = "Sucuri"
    elif "x-amz-cf-id" in h or "cloudfront" in server:
        proveedor = "Amazon CloudFront"
    desafio = "cf-mitigated" in h or any(s in text for s in ("just a moment", "cf-chl", "attention required", "checking your browser", "captcha"))

    def resultado(codigo, causa, detalle, recomendacion):
        return {"codigo": codigo, "causa": causa, "proveedor": proveedor, "desafio": desafio, "detalle": detalle, "recomendacion": recomendacion}

    if status is None:
        return resultado("sin_respuesta", "Sin respuesta", "No se obtuvo respuesta HTTP (tiempo agotado, DNS o conexión rechazada).",
                         "Revisa si el fallo persiste en varias consultas; si es puntual, puede ser una caída temporal.")
    if status == 429 or (status in (403, 503) and "retry-after" in h):
        return resultado("limite", "Límite de solicitudes", f"El servidor pide esperar antes de volver a consultar (Retry-After: {h.get('retry-after', 'no indicado')}).",
                         "Aumenta el intervalo del monitoreo; la herramienta respeta el tiempo indicado por el sitio.")
    if status == 401 or "www-authenticate" in h:
        return resultado("autenticacion", "Requiere autenticación", "El recurso solo está disponible con credenciales.",
                         "Accede solo si estás autorizado; documenta la respuesta como evidencia de que el recurso existe.")
    if status == 403 and proveedor:
        detalle = f"La respuesta proviene de {proveedor}" + (" y contiene un desafío antibots (verificación de navegador o captcha)." if desafio else ", que filtra el tráfico antes de llegar al sitio.")
        return resultado("antibots", f"Protección antibots ({proveedor})", detalle,
                         "El sitio está en línea pero rechaza consultas automatizadas. Mantén el monitoreo para documentarlo y solicita acceso al propietario o una vía oficial (API, RSS).")
    if status == 403:
        return resultado("denegado", "Acceso denegado por el servidor", "El servidor respondió, pero no autoriza esta consulta (zona privada, bloqueo por país, IP o agente).",
                         "Mantén el monitoreo para registrar si el bloqueo cambia; solicita acceso si la investigación lo requiere.")
    if 200 <= status < 300:
        return resultado("accesible", "Accesible", "El contenido se entregó sin restricciones.", "")
    if status == 404 or status == 410:
        return resultado("no_encontrado", "No encontrado", "El servidor responde, pero el recurso no existe en esa ruta.", "Verifica la URL o monitoriza para detectar si vuelve a publicarse.")
    if status >= 500:
        return resultado("error_servidor", "Error del servidor", f"El servidor respondió con un error interno (HTTP {status}).", "Puede ser temporal; el monitoreo mostrará si persiste.")
    return resultado("otro", f"Respuesta HTTP {status}", "Respuesta no clasificada.", "")


def inspect_body(url, body, content_type):
    if "json" in content_type.lower():
        try:
            data = json.loads(body.decode("utf-8", errors="replace"))
            title = "Documento JSON"
            links = []
            emails = []
            serialized = json.dumps(data, ensure_ascii=False)
            links.extend(re.findall(r"https?://[^\s\"'<>]+", serialized))
            emails.extend(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", serialized))
        except (ValueError, UnicodeDecodeError):
            title, links, emails = "Respuesta JSON no válida", [], []
        soup = None
    else:
        soup = BeautifulSoup(body, "html.parser")
        title = soup.title.get_text(" ", strip=True)[:180] if soup.title else "Sin título"
        links = [urljoin(url, tag.get("href", "")) for tag in soup.select("a[href]")]
        emails = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", soup.get_text(" ", strip=True))
    cleaned = []
    for candidate in links:
        try:
            parts = urlparse(candidate)
            if parts.scheme in ("http", "https") and parts.hostname:
                cleaned.append(urlunparse((parts.scheme, parts.netloc, parts.path or "/", "", parts.query, "")))
        except ValueError:
            continue
    return title, list(dict.fromkeys(cleaned)), list(dict.fromkeys(emails)), identidad_sitio(url, soup)


def explore_settings(payload):
    """Valida la solicitud antes de empezar, para responder 400 sin abrir el flujo."""
    start = public_http_url(str(payload.get("url", "")))
    try:
        max_pages = max(1, min(30, int(payload.get("max_pages", 10))))
        max_depth = max(0, min(2, int(payload.get("max_depth", 1))))
        timeout = max(3, min(20, int(payload.get("timeout", 10))))
        delay = max(0, min(3, float(payload.get("delay", 0.3))))
    except (TypeError, ValueError) as exc:
        raise ValueError("Revisa los valores de parametrización.") from exc
    same_domain = bool(payload.get("same_domain", True))
    return {"url": start, "max_pages": max_pages, "max_depth": max_depth, "same_domain": same_domain, "timeout": timeout, "delay": delay}


def explore_events(settings):
    """Rastrea el sitio y produce un evento por paso: start, fetching, page, error y done."""
    start, max_pages, max_depth = settings["url"], settings["max_pages"], settings["max_depth"]
    timeout, delay, same_domain = settings["timeout"], settings["delay"], settings["same_domain"]
    public_settings = {k: v for k, v in settings.items() if k != "url"}
    origin_domain = domain_of(start)
    queue = deque([(start, 0)])
    queued = {start}
    nodes, edges, captures, errors = [], [], [], []

    def progress():
        return {"visited": len(nodes), "queued": len(queue), "errors": len(errors), "max_pages": max_pages}

    yield {"type": "start", "url": start, "settings": public_settings, **progress()}
    while queue and len(nodes) < max_pages:
        url, depth = queue.popleft()
        if nodes and delay:
            time.sleep(delay)
        yield {"type": "fetching", "url": url, "depth": depth, **progress()}
        try:
            final_url, body, content_type, status, response_headers = download(url, timeout)
            if status == 403:
                title, links, emails = "Acceso denegado · HTTP 403", [], []
                identity = identidad_sitio(final_url)
            elif status >= 400:
                title, links, emails = f"Respuesta HTTP {status}", [], []
                identity = identidad_sitio(final_url)
            else:
                title, links, emails, identity = inspect_body(final_url, body, content_type)
            evidence = save_evidence(final_url, body, content_type, status, response_headers)
            captures.append(evidence)
            node = {"id": final_url, "label": title[:36] or domain_of(final_url), "url": final_url, "domain": domain_of(final_url), "depth": depth, "status": status, "accessible": status < 400, "sha256": evidence["sha256"], "bytes": evidence["bytes"], "content_type": content_type, "response_headers": response_headers, "evidence_file": f"data/osint_evidence/{evidence['file']}", "links_found": len(links), "emails": emails[:20], "identity": identity, "diagnostico": diagnosticar_respuesta(status, response_headers, body)}
            nodes.append(node)
            page_error = None
            if status == 403:
                page_error = {"url": final_url, "status": status, "evidence_saved": True, "error": "El sitio rechazó la solicitud (HTTP 403). Se preservó la respuesta recibida; el contenido protegido no fue descargado."}
            elif status >= 400:
                page_error = {"url": final_url, "status": status, "evidence_saved": True, "error": f"El sitio respondió HTTP {status}. Se preservó la respuesta recibida."}
            if page_error:
                errors.append(page_error)
            new_edges = []
            for linked in links:
                if linked == final_url or linked == url:
                    continue
                new_edges.append({"source": final_url, "target": linked})
                if depth < max_depth and len(queued) < max_pages and linked not in queued:
                    if not same_domain or domain_of(linked) == origin_domain:
                        queued.add(linked)
                        queue.append((linked, depth + 1))
            edges.extend(new_edges)
            yield {"type": "page", "node": node, "edges": new_edges, "capture": evidence, "error": page_error, **progress()}
        except Exception as exc:
            error = {"url": url, "error": str(exc)[:240]}
            errors.append(error)
            yield {"type": "error", "error": error, **progress()}
    result = {"nodes": nodes, "edges": edges, "captures": captures, "errors": errors, "settings": public_settings}
    yield {"type": "done", "result": result, **progress()}


def explore(payload):
    """Versión sin flujo: devuelve el análisis completo al terminar."""
    result = None
    for event in explore_events(explore_settings(payload)):
        if event["type"] == "done":
            result = event["result"]
    return result


MONITOR_DIR = ROOT / "data" / "monitors"
MONITORS_FILE = MONITOR_DIR / "monitors.json"
MONITOR_INTERVALS = (300, 900, 1800, 3600, 21600, 86400)
MONITOR_TIMEOUT = 15
MAX_MONITORS = 20
_monitor_lock = threading.Lock()
_monitor_wake = threading.Event()
_checking = set()


def _now():
    return datetime.now(timezone.utc)


def load_monitors():
    return json.loads(MONITORS_FILE.read_text("utf-8")) if MONITORS_FILE.exists() else []


def save_monitors(monitors):
    MONITOR_DIR.mkdir(parents=True, exist_ok=True)
    tmp = MONITORS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(monitors, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(MONITORS_FILE)


def timeline_file(monitor_id):
    return MONITOR_DIR / f"{monitor_id}.jsonl"


def read_timeline(monitor_id, limit=5000):
    path = timeline_file(monitor_id)
    if not path.exists():
        return []
    lines = path.read_text("utf-8").splitlines()[-limit:]
    return [json.loads(line) for line in lines if line.strip()]


def retry_after_seconds(headers):
    value = (headers or {}).get("Retry-After")
    if not value:
        return None
    try:
        return max(0, int(value))
    except ValueError:
        try:
            return max(0, (parsedate_to_datetime(value) - _now()).total_seconds())
        except (TypeError, ValueError):
            return None


def huella_contenido(body, content_type=""):
    """Hash del contenido sin scripts, estilos, comentarios ni tokens volátiles (ids de sesión, marcas de tiempo).

    Sirve para detectar cambios reales: páginas como los desafíos antibots cambian su SHA-256 en cada consulta
    aunque su contenido visible sea el mismo.
    """
    text = body.decode("utf-8", errors="replace")
    if "html" in content_type.lower() or text.lstrip()[:1] == "<":
        text = re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", " ", text)
    text = re.sub(r"(?=[A-Za-z_.\-]*\d)[A-Za-z0-9_.\-]{16,}", "§", text)
    text = re.sub(r"\d{6,}", "#", text)
    return hashlib.sha256(re.sub(r"\s+", " ", text).strip().encode("utf-8")).hexdigest()


def ejecutar_chequeo(monitor):
    """Una sola consulta a la URL: estado, tiempo, hash y, sin caché, DNS y certificado TLS."""
    url, prev = monitor["url"], monitor.get("last") or {}
    record = {"at": _now().isoformat(), "url": url, "status": None, "ms": None, "error": None}
    started = time.monotonic()
    try:
        final_url, body, content_type, status, headers = download(url, MONITOR_TIMEOUT)
        record["ms"] = round((time.monotonic() - started) * 1000)
        digest = hashlib.sha256(body).hexdigest()
        huella = huella_contenido(body, content_type)
        if huella == prev.get("huella") and prev.get("evidence_file"):
            evidence_file, reused = prev["evidence_file"], True
        else:
            evidence = save_evidence(final_url, body, content_type, status, headers)
            evidence_file, reused = f"data/osint_evidence/{evidence['file']}", False
        record.update({"status": status, "final_url": final_url, "content_type": content_type, "headers": headers,
                       "sha256": digest, "huella": huella, "bytes": len(body), "evidence_file": evidence_file, "evidencia_reutilizada": reused,
                       "diagnostico": diagnosticar_respuesta(status, headers, body)})
    except Exception as exc:
        record.update({"ms": round((time.monotonic() - started) * 1000), "error": str(exc)[:240], "diagnostico": diagnosticar_respuesta(None)})
    parts = urlparse(url)
    port = parts.port or (443 if parts.scheme == "https" else 80)
    ips = resolver_ips_publicas.__wrapped__(parts.hostname or "", port)
    tls = certificado_tls.__wrapped__(parts.hostname or "", port, ips) if parts.scheme == "https" and ips else None
    record["ips"] = list(ips[:12])
    record["tls"] = {k: tls.get(k) for k in ("sujeto", "emisor", "valido_hasta")} if tls else None
    record["cambios"] = [name for name, changed in (
        ("estado", bool(prev) and prev.get("status") != record["status"]),
        ("contenido", bool(prev.get("huella")) and bool(record.get("huella")) and prev["huella"] != record["huella"]),
        ("ip", bool(prev.get("ips")) and bool(record["ips"]) and set(prev["ips"]) != set(record["ips"])),
        ("tls", bool(prev.get("tls")) and bool(record["tls"]) and prev["tls"].get("valido_hasta") != record["tls"].get("valido_hasta")),
    ) if changed]
    return record


def run_monitor_check(monitor_id):
    """Ejecuta y registra un chequeo; devuelve el registro o None si el monitor no existe o ya se está consultando."""
    with _monitor_lock:
        monitor = next((m for m in load_monitors() if m["id"] == monitor_id), None)
        if not monitor or monitor_id in _checking:
            return None
        _checking.add(monitor_id)
    try:
        record = ejecutar_chequeo(monitor)
        with _monitor_lock:
            monitors = load_monitors()
            current = next((m for m in monitors if m["id"] == monitor_id), None)
            if not current:
                return None
            MONITOR_DIR.mkdir(parents=True, exist_ok=True)
            with timeline_file(monitor_id).open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            wait = current["interval"]
            retry = retry_after_seconds(record.get("headers"))
            if retry and retry > wait:
                wait = min(retry, 86400)
            current["checks"] = current.get("checks", 0) + 1
            current["last"] = {k: record.get(k) for k in ("at", "status", "ms", "sha256", "huella", "evidence_file", "ips", "tls", "diagnostico", "error", "cambios")}
            current["next_check_ts"] = time.time() + wait
            current["next_check_at"] = datetime.fromtimestamp(current["next_check_ts"], timezone.utc).isoformat()
            if record["cambios"]:
                current["last_change_at"] = record["at"]
            save_monitors(monitors)
        return record
    finally:
        with _monitor_lock:
            _checking.discard(monitor_id)


def monitor_loop():
    """Programador en segundo plano: consulta cada monitor activo cuando le toca."""
    while True:
        with _monitor_lock:
            monitors = load_monitors()
        now = time.time()
        for monitor in monitors:
            if monitor.get("active") and monitor.get("next_check_ts", 0) <= now:
                try:
                    run_monitor_check(monitor["id"])
                except Exception as exc:
                    print(f"Error en el monitoreo de {monitor['url']}: {exc}")
        with _monitor_lock:
            pending = [m["next_check_ts"] for m in load_monitors() if m.get("active")]
        timeout = min(30, max(1, min(pending) - time.time())) if pending else 30
        _monitor_wake.wait(timeout)
        _monitor_wake.clear()


def create_monitor(payload):
    url = public_http_url(str(payload.get("url", "")))
    try:
        interval = int(payload.get("interval", 900))
    except (TypeError, ValueError) as exc:
        raise ValueError("Intervalo no válido.") from exc
    if interval not in MONITOR_INTERVALS:
        raise ValueError("Elige un intervalo de la lista.")
    with _monitor_lock:
        monitors = load_monitors()
        existing = next((m for m in monitors if m["url"] == url), None)
        if existing:
            return existing
        if len(monitors) >= MAX_MONITORS:
            raise ValueError(f"Máximo {MAX_MONITORS} monitores activos.")
        monitor = {"id": uuid.uuid4().hex[:12], "url": url, "interval": interval, "active": True, "created_at": _now().isoformat(),
                   "checks": 0, "last": None, "next_check_ts": time.time(), "next_check_at": _now().isoformat()}
        monitors.append(monitor)
        save_monitors(monitors)
    _monitor_wake.set()
    return monitor


def update_monitor(monitor_id, changes):
    with _monitor_lock:
        monitors = load_monitors()
        monitor = next((m for m in monitors if m["id"] == monitor_id), None)
        if not monitor:
            return None
        if "interval" in changes:
            try:
                valid = int(changes["interval"]) in MONITOR_INTERVALS
            except (TypeError, ValueError):
                valid = False
            if not valid:
                raise ValueError("Elige un intervalo de la lista.")
            monitor["interval"] = int(changes["interval"])
            if monitor.get("last"):
                monitor["next_check_ts"] = datetime.fromisoformat(monitor["last"]["at"]).timestamp() + monitor["interval"]
                monitor["next_check_at"] = datetime.fromtimestamp(monitor["next_check_ts"], timezone.utc).isoformat()
        if "active" in changes:
            monitor["active"] = bool(changes["active"])
            if monitor["active"]:
                monitor["next_check_ts"] = time.time()
        save_monitors(monitors)
    _monitor_wake.set()
    return monitor


def delete_monitor(monitor_id):
    """Elimina el monitor y su línea de tiempo; las capturas en data/osint_evidence/ se conservan."""
    with _monitor_lock:
        monitors = load_monitors()
        remaining = [m for m in monitors if m["id"] != monitor_id]
        if len(remaining) == len(monitors):
            return False
        save_monitors(remaining)
        timeline_file(monitor_id).unlink(missing_ok=True)
    return True


MONITOR_PATH = re.compile(r"^/api/monitors/([a-f0-9]{12})(?:/(timeline|check|pause|resume|interval))?$")


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data, content_type="application/json; charset=utf-8"):
        body = data if isinstance(data, bytes) else (json.dumps(data, ensure_ascii=False).encode("utf-8") if content_type.startswith("application/json") else data.encode("utf-8"))
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/monitors":
            with _monitor_lock:
                return self.respond(200, {"monitors": load_monitors(), "intervals": MONITOR_INTERVALS})
        match = MONITOR_PATH.match(self.path)
        if match and match.group(2) == "timeline":
            with _monitor_lock:
                monitor = next((m for m in load_monitors() if m["id"] == match.group(1)), None)
            if not monitor:
                return self.respond(404, {"error": "Monitor no encontrado"})
            return self.respond(200, {"monitor": monitor, "timeline": read_timeline(monitor["id"])})
        if self.path == "/api/evidence":
            records = json.loads(INDEX_FILE.read_text("utf-8")) if INDEX_FILE.exists() else []
            return self.respond(200, records[-100:][::-1])
        if self.path in ("/", "/index.html"):
            return self.respond(200, (WEB_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
        return self.respond(404, {"error": "No encontrado"})

    def read_payload(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 20000:
            raise OverflowError
        return json.loads(self.rfile.read(length))

    def do_DELETE(self):
        match = MONITOR_PATH.match(self.path)
        if not match or match.group(2):
            return self.respond(404, {"error": "No encontrado"})
        return self.respond(200, {"ok": True}) if delete_monitor(match.group(1)) else self.respond(404, {"error": "Monitor no encontrado"})

    def monitor_post(self):
        try:
            if self.path == "/api/monitors":
                return self.respond(201, create_monitor(self.read_payload()))
            match = MONITOR_PATH.match(self.path)
            if not match or match.group(2) not in ("check", "pause", "resume", "interval"):
                return self.respond(404, {"error": "No encontrado"})
            monitor_id, action = match.groups()
            if action == "check":
                record = run_monitor_check(monitor_id)
                return self.respond(200, record) if record else self.respond(409, {"error": "El monitor no existe o ya se está consultando."})
            changes = {"interval": self.read_payload().get("interval")} if action == "interval" else {"active": action == "resume"}
            monitor = update_monitor(monitor_id, changes)
            return self.respond(200, monitor) if monitor else self.respond(404, {"error": "Monitor no encontrado"})
        except OverflowError:
            return self.respond(413, {"error": "Solicitud demasiado grande"})
        except (ValueError, json.JSONDecodeError) as exc:
            return self.respond(400, {"error": str(exc)})

    def do_POST(self):
        if self.path.startswith("/api/monitors"):
            return self.monitor_post()
        if self.path not in ("/api/explore", "/api/explore/stream"):
            return self.respond(404, {"error": "No encontrado"})
        try:
            settings = explore_settings(self.read_payload())
        except OverflowError:
            return self.respond(413, {"error": "Solicitud demasiado grande"})
        except (ValueError, json.JSONDecodeError) as exc:
            return self.respond(400, {"error": str(exc)})
        if self.path == "/api/explore/stream":
            return self.stream(settings)
        try:
            events = explore_events(settings)
            return self.respond(200, next(e["result"] for e in events if e["type"] == "done"))
        except Exception as exc:
            return self.respond(502, {"error": str(exc)[:240]})

    def stream(self, settings):
        """Envía un evento JSON por línea; si el navegador cierra la conexión, el rastreo se detiene."""
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        events = explore_events(settings)
        try:
            for event in events:
                self.wfile.write((json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            print("Exploración detenida por el navegador.")
        except Exception as exc:
            try:
                self.wfile.write((json.dumps({"type": "fatal", "error": str(exc)[:240]}, ensure_ascii=False) + "\n").encode("utf-8"))
            except OSError:
                pass
        finally:
            events.close()
            self.close_connection = True

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


if __name__ == "__main__":
    host, port = "127.0.0.1", 8000
    print(f"Interfaz OSINT disponible en http://{host}:{port}")
    threading.Thread(target=monitor_loop, name="monitor", daemon=True).start()
    ThreadingHTTPServer((host, port), Handler).serve_forever()
