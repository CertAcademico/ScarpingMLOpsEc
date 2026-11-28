"""Registros DNS, comparación entre observaciones, traza de ruta (traceroute) y WHOIS para el monitoreo forense.

Todas las consultas se hacen sin caché, desde la conexión del sistema (el proxy HTTP de la app no aplica a DNS ni a
traceroute). Los datos se devuelven como diccionarios simples para guardarlos en la línea de tiempo JSONL.
"""

import ipaddress
import os
import platform
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

import dns.exception
import dns.resolver
import dns.reversename

DNS_TIPOS = ("A", "AAAA", "CNAME", "NS", "MX", "TXT", "CAA")
# Tipos que se comparan para detectar un cambio de resolución. El SOA se compara aparte por su número de serie.
DNS_TIPOS_COMPARADOS = ("A", "AAAA", "CNAME", "NS", "MX", "TXT", "CAA")
TRAZA_MAX_SALTOS = 30
TRAZA_TIMEOUT = 120


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _resolver(lifetime=5.0):
    resolver = dns.resolver.Resolver()
    resolver.cache = None
    resolver.lifetime = lifetime
    resolver.timeout = min(2.5, lifetime)
    return resolver


def _consultar(resolver, nombre, tipo):
    """Devuelve (valores ordenados, TTL) o ([], None) si no existe el registro."""
    try:
        respuesta = resolver.resolve(nombre, tipo, raise_on_no_answer=False)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.resolver.NoAnswer, dns.exception.Timeout,
            dns.resolver.YXDOMAIN, dns.name.EmptyLabel, ValueError):
        return [], None
    if respuesta.rrset is None:
        return [], None
    def limpio(texto):
        # Quita el punto final de los nombres, pero conserva el MX nulo «0 .» (el dominio declara que no recibe correo).
        return texto[:-1] if tipo != "TXT" and texto.endswith(".") and not texto.endswith(" .") else texto

    valores = sorted({limpio(item.to_text()) for item in respuesta.rrset})
    return valores[:30], respuesta.rrset.ttl


def zona_de(host):
    """Zona DNS (dominio registrado) que contiene al host, p. ej. www.ejemplo.com → ejemplo.com."""
    try:
        return dns.resolver.zone_for_name(host, resolver=_resolver(4.0)).to_text().rstrip(".")
    except Exception:
        partes = host.rstrip(".").split(".")
        return ".".join(partes[-2:]) if len(partes) >= 2 else host


def nombre_inverso(ip, resolver=None):
    """Registro PTR (hostname) de una IP pública; None si no tiene."""
    try:
        if not ipaddress.ip_address(ip).is_global:
            return None
        valores, _ = _consultar(resolver or _resolver(3.0), dns.reversename.from_address(ip), "PTR")
        return valores[0] if valores else None
    except ValueError:
        return None


def asn_de(ip, resolver=None):
    """Sistema autónomo y titular de la red de una IP, mediante el servicio DNS público de Team Cymru."""
    try:
        direccion = ipaddress.ip_address(ip)
    except ValueError:
        return None
    if not direccion.is_global:
        return {"asn": None, "titular": "Red privada / local", "prefijo": None, "pais": None}
    resolver = resolver or _resolver(3.0)
    if direccion.version == 4:
        consulta = ".".join(reversed(ip.split("."))) + ".origin.asn.cymru.com"
    else:
        nibbles = direccion.exploded.replace(":", "")
        consulta = ".".join(reversed(nibbles)) + ".origin6.asn.cymru.com"
    valores, _ = _consultar(resolver, consulta, "TXT")
    if not valores:
        return None
    campos = [c.strip() for c in valores[0].strip('"').split("|")]
    asn = campos[0].split()[0] if campos and campos[0] else None
    info = {"asn": f"AS{asn}" if asn else None, "prefijo": campos[1] if len(campos) > 1 else None,
            "pais": campos[2] if len(campos) > 2 else None, "titular": None}
    if asn:
        nombre, _ = _consultar(resolver, f"AS{asn}.asn.cymru.com", "TXT")
        if nombre:
            partes = [c.strip() for c in nombre[0].strip('"').split("|")]
            info["titular"] = partes[-1] if partes else None
    return info


def registros_dns(host):
    """Fotografía DNS del host y de su zona: registros, TTL, SOA, PTR de las IP y resolvedores usados."""
    resolver = _resolver()
    host = host.rstrip(".").lower()
    zona = zona_de(host)
    registros, ttl = {}, {}
    for tipo in DNS_TIPOS:
        nombre = zona if tipo in ("NS", "MX", "CAA") and host != zona else host
        valores, vida = _consultar(resolver, nombre, tipo)
        if tipo in ("NS", "MX", "CAA") and not valores and nombre != host:
            valores, vida = _consultar(resolver, host, tipo)
        registros[tipo] = valores
        if vida is not None:
            ttl[tipo] = vida
    soa_valores, _ = _consultar(resolver, zona, "SOA")
    soa = None
    if soa_valores:
        partes = soa_valores[0].split()
        if len(partes) >= 7:
            soa = {"servidor_primario": partes[0].rstrip("."), "responsable": partes[1].rstrip("."), "serial": partes[2],
                   "refresh": partes[3], "retry": partes[4], "expire": partes[5], "minimum": partes[6]}
    ips = registros.get("A", []) + registros.get("AAAA", [])
    with ThreadPoolExecutor(max_workers=6) as pool:
        ptr = dict(zip(ips[:8], pool.map(lambda ip: nombre_inverso(ip), ips[:8])))
    return {"consultado_at": _ahora(), "host": host, "zona": zona, "registros": registros, "ttl": ttl, "soa": soa,
            "ptr": {ip: nombre for ip, nombre in ptr.items() if nombre},
            "resolvedores": [str(servidor) for servidor in resolver.nameservers][:4]}


def comparar_dns(anterior, actual):
    """Diferencias de resolución entre dos fotografías DNS: valores añadidos y retirados por tipo, y cambio de serial SOA."""
    if not anterior or not actual:
        return []
    cambios = []
    for tipo in DNS_TIPOS_COMPARADOS:
        antes = set((anterior.get("registros") or {}).get(tipo) or [])
        ahora = set((actual.get("registros") or {}).get(tipo) or [])
        if antes != ahora:
            cambios.append({"tipo": tipo, "antes": sorted(antes), "despues": sorted(ahora),
                            "anadidos": sorted(ahora - antes), "retirados": sorted(antes - ahora)})
    serial_antes = (anterior.get("soa") or {}).get("serial")
    serial_ahora = (actual.get("soa") or {}).get("serial")
    if serial_antes and serial_ahora and serial_antes != serial_ahora:
        cambios.append({"tipo": "SOA", "antes": [serial_antes], "despues": [serial_ahora], "anadidos": [serial_ahora],
                        "retirados": [serial_antes], "nota": "Cambió el número de serie de la zona: el titular editó sus registros DNS."})
    return cambios


def _comando_traza(destino):
    sistema = platform.system()
    if sistema == "Windows":
        if shutil.which("tracert"):
            return ["tracert", "-d", "-h", str(TRAZA_MAX_SALTOS), "-w", "1500", destino], "tracert"
        return None, None
    if shutil.which("traceroute") or os.path.exists("/usr/sbin/traceroute"):
        binario = shutil.which("traceroute") or "/usr/sbin/traceroute"
        return [binario, "-n", "-q", "2", "-w", "2", "-m", str(TRAZA_MAX_SALTOS), destino], "traceroute"
    if shutil.which("tracepath"):
        return ["tracepath", "-n", "-m", str(TRAZA_MAX_SALTOS), destino], "tracepath"
    return None, None


SALTO = re.compile(r"^\s*(\d+)\s+(.*)$")
IP_EN_LINEA = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3}|[0-9a-fA-F]*:[0-9a-fA-F:]+)")
RTT = re.compile(r"(<?\d+(?:\.\d+)?)\s*ms")


def _parsear_traza(salida):
    saltos = {}
    for linea in salida.splitlines():
        coincide = SALTO.match(linea)
        if not coincide:
            continue
        numero, resto = int(coincide.group(1)), coincide.group(2)
        if numero > TRAZA_MAX_SALTOS or "traceroute to" in resto:
            continue
        ips = [ip for ip in IP_EN_LINEA.findall(resto) if _es_ip(ip)]
        tiempos = [float(valor.lstrip("<")) for valor in RTT.findall(resto)]
        salto = saltos.setdefault(numero, {"salto": numero, "ip": None, "ips_alternativas": [], "rtt_ms": []})
        for ip in ips:
            if salto["ip"] is None:
                salto["ip"] = ip
            elif ip != salto["ip"] and ip not in salto["ips_alternativas"]:
                salto["ips_alternativas"].append(ip)
        salto["rtt_ms"].extend(tiempos)
    return [saltos[n] for n in sorted(saltos)]


def _es_ip(valor):
    try:
        ipaddress.ip_address(valor)
        return True
    except ValueError:
        return False


def trazar_ruta(host, destino_ip=None):
    """Ejecuta traceroute (tracert en Windows) hacia el host y enriquece cada salto con PTR y ASN.

    Los saltos sin respuesta (*) se conservan: muchos routers y CDN no responden a estas sondas, y eso no implica caída.
    """
    destino = destino_ip or host
    comando, herramienta = _comando_traza(destino)
    resultado = {"iniciado_at": _ahora(), "host": host, "destino": destino, "herramienta": herramienta, "comando": None,
                 "saltos": [], "alcanzado": False, "error": None}
    if not comando:
        resultado["error"] = "No se encontró traceroute/tracert en este equipo."
        return resultado
    resultado["comando"] = " ".join(comando)
    errores = ""
    try:
        proceso = subprocess.run(comando, capture_output=True, text=True, timeout=TRAZA_TIMEOUT)
        salida, errores = proceso.stdout, proceso.stderr or ""
        if proceso.returncode != 0 and not salida.strip():
            resultado["error"] = (errores or "traceroute terminó con error").strip()[:240]
    except subprocess.TimeoutExpired as exc:
        salida = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        resultado["error"] = f"La traza superó {TRAZA_TIMEOUT} s; se conservan los saltos obtenidos."
    except OSError as exc:
        resultado["error"] = f"No se pudo ejecutar {herramienta}: {exc}"[:240]
        return resultado
    resultado["salida_bruta"] = (errores + salida)[-8000:]
    # traceroute de macOS escribe la cabecera («traceroute to host (IP)») en stderr; tracert la escribe en stdout.
    cabecera = re.search(r"(?:traceroute to|Tracing route to)\s+\S+\s+[\[(]([0-9a-fA-F.:]+)[\])]", errores + salida)
    if cabecera and _es_ip(cabecera.group(1)):
        destino = resultado["destino"] = cabecera.group(1)
    saltos = _parsear_traza(salida)
    ips = sorted({s["ip"] for s in saltos if s["ip"]})
    with ThreadPoolExecutor(max_workers=8) as pool:
        ptr = dict(zip(ips, pool.map(nombre_inverso, ips)))
        asn = dict(zip(ips, pool.map(asn_de, ips)))
    for salto in saltos:
        tiempos = salto.pop("rtt_ms")
        salto["rtt_ms"] = round(min(tiempos), 2) if tiempos else None
        salto["hostname"] = ptr.get(salto["ip"]) if salto["ip"] else None
        salto["red"] = asn.get(salto["ip"]) if salto["ip"] else None
    resultado["saltos"] = saltos
    resultado["alcanzado"] = bool(saltos) and saltos[-1]["ip"] == destino
    resultado["terminado_at"] = _ahora()
    return resultado


def ruta_resumen(traza):
    """Secuencia de IP que respondieron; sirve para comparar si la ruta cambió."""
    return [s["ip"] for s in (traza or {}).get("saltos", []) if s.get("ip")]


def _texto(valor):
    if isinstance(valor, (list, tuple)):
        vistos = []
        for item in valor:
            texto = _texto(item)
            if texto and texto not in vistos:
                vistos.append(texto)
        return vistos
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return str(valor) if valor not in (None, "") else None


def whois_dominio(dominio):
    """Datos de registro del dominio (registrador, fechas, servidores DNS declarados, estado y titular si es público)."""
    try:
        import whois
    except ImportError:
        return {"dominio": dominio, "error": "python-whois no está instalado."}
    try:
        datos = whois.whois(dominio)
    except Exception as exc:
        return {"dominio": dominio, "consultado_at": _ahora(), "error": f"WHOIS no disponible: {str(exc)[:160]}"}
    campos = {
        "registrador": "registrar", "whois_servidor": "whois_server", "creado": "creation_date", "actualizado": "updated_date",
        "expira": "expiration_date", "servidores_dns": "name_servers", "estado": "status", "titular": "name",
        "organizacion": "org", "pais": "country", "estado_region": "state", "dnssec": "dnssec", "emails": "emails",
    }
    resultado = {"dominio": dominio, "consultado_at": _ahora()}
    for destino, origen in campos.items():
        valor = _texto(datos.get(origen))
        if destino == "servidores_dns" and isinstance(valor, list):
            valor = sorted({v.lower().rstrip(".") for v in valor})
        if destino == "estado" and isinstance(valor, list):
            valor = [v.split()[0] for v in valor][:8]
        if destino in ("creado", "actualizado", "expira") and isinstance(valor, list):
            valor = valor[0]
        resultado[destino] = valor
    return resultado
