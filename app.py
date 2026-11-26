"""Interfaz local para explorar URLs y conservar evidencia web."""

import hashlib
import ipaddress
import json
import re
import socket
import ssl
import threading
import time
from collections import deque
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
            for name in ("Content-Type", "Date", "Server", "Content-Length", "Retry-After")
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


def explore(payload):
    start = public_http_url(str(payload.get("url", "")))
    try:
        max_pages = max(1, min(30, int(payload.get("max_pages", 10))))
        max_depth = max(0, min(2, int(payload.get("max_depth", 1))))
        timeout = max(3, min(20, int(payload.get("timeout", 10))))
        delay = max(0, min(3, float(payload.get("delay", 0.3))))
    except (TypeError, ValueError) as exc:
        raise ValueError("Revisa los valores de parametrización.") from exc
    same_domain = bool(payload.get("same_domain", True))
    origin_domain = domain_of(start)
    queue = deque([(start, 0)])
    queued = {start}
    nodes, edges, captures, errors = [], [], [], []
    while queue and len(nodes) < max_pages:
        url, depth = queue.popleft()
        if nodes and delay:
            time.sleep(delay)
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
            node = {"id": final_url, "label": title[:36] or domain_of(final_url), "url": final_url, "domain": domain_of(final_url), "depth": depth, "status": status, "accessible": status < 400, "sha256": evidence["sha256"], "bytes": evidence["bytes"], "content_type": content_type, "response_headers": response_headers, "evidence_file": f"data/osint_evidence/{evidence['file']}", "links_found": len(links), "emails": emails[:20], "identity": identity}
            nodes.append(node)
            if status == 403:
                errors.append({"url": final_url, "status": status, "evidence_saved": True, "error": "El sitio rechazó la solicitud (HTTP 403). Se preservó la respuesta recibida; el contenido protegido no fue descargado."})
            elif status >= 400:
                errors.append({"url": final_url, "status": status, "evidence_saved": True, "error": f"El sitio respondió HTTP {status}. Se preservó la respuesta recibida."})
            for linked in links:
                if linked == final_url or linked == url:
                    continue
                edges.append({"source": final_url, "target": linked})
                if depth < max_depth and len(queued) < max_pages and linked not in queued:
                    if not same_domain or domain_of(linked) == origin_domain:
                        queued.add(linked)
                        queue.append((linked, depth + 1))
        except Exception as exc:
            errors.append({"url": url, "error": str(exc)[:240]})
    valid_ids = {node["id"] for node in nodes}
    shown_edges = [edge for edge in edges if edge["source"] in valid_ids]
    return {"nodes": nodes, "edges": shown_edges, "captures": captures, "errors": errors, "settings": {"max_pages": max_pages, "max_depth": max_depth, "same_domain": same_domain, "timeout": timeout, "delay": delay}}


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
        if self.path == "/api/evidence":
            records = json.loads(INDEX_FILE.read_text("utf-8")) if INDEX_FILE.exists() else []
            return self.respond(200, records[-100:][::-1])
        if self.path in ("/", "/index.html"):
            return self.respond(200, (WEB_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
        return self.respond(404, {"error": "No encontrado"})

    def do_POST(self):
        if self.path != "/api/explore":
            return self.respond(404, {"error": "No encontrado"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 20000:
                return self.respond(413, {"error": "Solicitud demasiado grande"})
            payload = json.loads(self.rfile.read(length))
            return self.respond(200, explore(payload))
        except (ValueError, json.JSONDecodeError) as exc:
            return self.respond(400, {"error": str(exc)})
        except Exception as exc:
            return self.respond(502, {"error": str(exc)[:240]})

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


if __name__ == "__main__":
    host, port = "127.0.0.1", 8000
    print(f"Interfaz OSINT disponible en http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
