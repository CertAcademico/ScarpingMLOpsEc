"""
OSINT CLI - Inteligencia sobre Dominios e IPs
Detecta automáticamente si el objetivo es un dominio o IP y genera un reporte completo.

Uso:
  python3 osint_tools/osint_cli.py google.com
  python3 osint_tools/osint_cli.py 8.8.8.8
  python3 osint_tools/osint_cli.py github.com --output reporte.json
"""

import sys
import json
import re
import socket
import argparse
from datetime import datetime
from typing import Optional

import requests
import dns.resolver
import whois
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.rule import Rule
from rich.text import Text


console = Console()

_IP_REGEX = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


# ─────────────────────────────────────────
# DETECCIÓN DE TIPO DE OBJETIVO
# ─────────────────────────────────────────

def es_ip(objetivo: str) -> bool:
    return bool(_IP_REGEX.match(objetivo))


def limpiar_dominio(dominio: str) -> str:
    return dominio.lower().replace("https://", "").replace("http://", "").split("/")[0].strip()


# ─────────────────────────────────────────
# RESOLUCIÓN DNS BÁSICA
# ─────────────────────────────────────────

def ip_desde_dominio(dominio: str) -> Optional[str]:
    try:
        return socket.gethostbyname(dominio)
    except Exception:
        return None


def hostname_desde_ip(ip: str) -> Optional[str]:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


# ─────────────────────────────────────────
# MÓDULO: GEOLOCALIZACIÓN E ISP
# ─────────────────────────────────────────

def obtener_info_ip(ip: str) -> dict:
    try:
        r = _SESSION.get(
            f"http://ip-api.com/json/{ip}",
            params={
                "fields": "status,country,countryCode,regionName,city,lat,lon,timezone,isp,org,as,proxy,hosting"
            },
            timeout=8,
        )
        data = r.json()
        if data.get("status") == "success":
            return {
                "pais": data.get("country", "N/A"),
                "codigo_pais": data.get("countryCode", ""),
                "region": data.get("regionName", "N/A"),
                "ciudad": data.get("city", "N/A"),
                "latitud": data.get("lat"),
                "longitud": data.get("lon"),
                "timezone": data.get("timezone", "N/A"),
                "isp": data.get("isp", "N/A"),
                "organizacion": data.get("org", "N/A"),
                "asn": data.get("as", "N/A"),
                "es_proxy": data.get("proxy", False),
                "es_hosting": data.get("hosting", False),
            }
    except Exception as e:
        return {"error": str(e)}
    return {"error": "Sin respuesta de la API"}


# ─────────────────────────────────────────
# MÓDULO: REGISTROS DNS
# ─────────────────────────────────────────

def obtener_registros_dns(dominio: str) -> dict:
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 6.0
    registros = {}

    for tipo in ("A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"):
        try:
            respuesta = resolver.resolve(dominio, tipo)
            if tipo == "MX":
                registros[tipo] = [f"{r.preference} {r.exchange}" for r in respuesta]
            elif tipo == "SOA":
                r = list(respuesta)[0]
                registros[tipo] = [f"mname={r.mname} rname={r.rname} serial={r.serial}"]
            else:
                registros[tipo] = [str(r) for r in respuesta]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            registros[tipo] = []
        except Exception as e:
            registros[tipo] = [f"Error: {e}"]

    return registros


# ─────────────────────────────────────────
# MÓDULO: WHOIS
# ─────────────────────────────────────────

def obtener_whois(dominio: str) -> dict:
    try:
        w = whois.whois(dominio)

        def fmt(val):
            if isinstance(val, list):
                val = val[0]
            if hasattr(val, "strftime"):
                return val.strftime("%Y-%m-%d")
            return str(val).strip() if val else "N/A"

        nameservers = w.name_servers or []
        if isinstance(nameservers, str):
            nameservers = [nameservers]

        return {
            "registrador": str(w.registrar or "N/A"),
            "creado": fmt(w.creation_date),
            "expira": fmt(w.expiration_date),
            "actualizado": fmt(w.updated_date),
            "estado": (
                w.status[0] if isinstance(w.status, list) else str(w.status or "N/A")
            )[:80],
            "nameservers": [str(ns).lower() for ns in list(nameservers)[:6]],
            "pais_registrante": str(w.country or "N/A"),
        }
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────
# MÓDULO: ANÁLISIS HTTP / SEGURIDAD
# ─────────────────────────────────────────

def analizar_http(dominio: str) -> dict:
    try:
        r = _SESSION.get(
            f"https://{dominio}",
            timeout=10,
            allow_redirects=True,
        )
        h = {k.lower(): v for k, v in r.headers.items()}
        return {
            "url_final": r.url,
            "status": r.status_code,
            "servidor": r.headers.get("Server", "N/A"),
            "tecnologia": r.headers.get("X-Powered-By", "N/A"),
            "https": True,
            "hsts": "strict-transport-security" in h,
            "csp": "content-security-policy" in h,
            "x_frame": r.headers.get("X-Frame-Options", "No configurado"),
            "referrer_policy": r.headers.get("Referrer-Policy", "No configurado"),
        }
    except requests.exceptions.SSLError:
        return {"https": False, "error": "Certificado SSL inválido o no disponible"}
    except requests.exceptions.ConnectionError:
        return {"error": "No se pudo conectar"}
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────────
# ORQUESTACIÓN
# ─────────────────────────────────────────

def analizar_ip(ip: str) -> dict:
    console.print(f"  [dim]Resolviendo hostname...[/dim]")
    hostname = hostname_desde_ip(ip)

    console.print(f"  [dim]Consultando geolocalización e ISP...[/dim]")
    info = obtener_info_ip(ip)

    return {
        "tipo": "ip",
        "ip": ip,
        "hostname": hostname or "N/A",
        **info,
    }


def analizar_dominio(dominio: str) -> dict:
    dominio = limpiar_dominio(dominio)

    console.print(f"  [dim]Resolviendo IP del dominio...[/dim]")
    ip = ip_desde_dominio(dominio)

    console.print(f"  [dim]Consultando registros DNS...[/dim]")
    dns_records = obtener_registros_dns(dominio)

    console.print(f"  [dim]Consultando WHOIS...[/dim]")
    whois_data = obtener_whois(dominio)

    console.print(f"  [dim]Analizando headers HTTP...[/dim]")
    http_data = analizar_http(dominio)

    ip_data = {}
    if ip:
        console.print(f"  [dim]Geolocalización de la IP ({ip})...[/dim]")
        ip_data = obtener_info_ip(ip)

    return {
        "tipo": "dominio",
        "dominio": dominio,
        "ip_resuelta": ip or "No resolvió",
        "dns": dns_records,
        "whois": whois_data,
        "http": http_data,
        "info_ip": ip_data,
    }


# ─────────────────────────────────────────
# PRESENTACIÓN CON RICH
# ─────────────────────────────────────────

def _icono_bool(valor: bool, texto_si="Sí", texto_no="No") -> str:
    return f"[green]{texto_si}[/green]" if valor else f"[red]{texto_no}[/red]"


def mostrar_reporte_ip(datos: dict):
    console.print()
    console.print(Panel(
        f"[bold cyan]IP:[/bold cyan]        {datos['ip']}\n"
        f"[bold cyan]Hostname:[/bold cyan]  {datos.get('hostname', 'N/A')}",
        title="[bold white on blue]  ANÁLISIS DE IP  [/bold white on blue]",
        border_style="cyan",
        padding=(1, 3),
    ))

    if "error" not in datos:
        # Geolocalización
        tabla_geo = Table(
            title="[bold]Geolocalización[/bold]",
            box=box.ROUNDED,
            border_style="blue",
            show_header=True,
            header_style="bold white",
        )
        tabla_geo.add_column("Campo", style="bold yellow", min_width=18)
        tabla_geo.add_column("Valor", style="white")

        tabla_geo.add_row("País", f"{datos.get('pais', 'N/A')} ({datos.get('codigo_pais', '')})")
        tabla_geo.add_row("Región", datos.get("region", "N/A"))
        tabla_geo.add_row("Ciudad", datos.get("ciudad", "N/A"))
        tabla_geo.add_row("Coordenadas", f"{datos.get('latitud')}, {datos.get('longitud')}")
        tabla_geo.add_row("Timezone", datos.get("timezone", "N/A"))
        console.print(tabla_geo)
        console.print()

        # Red / ISP
        tabla_red = Table(
            title="[bold]Red / ISP[/bold]",
            box=box.ROUNDED,
            border_style="magenta",
            header_style="bold white",
        )
        tabla_red.add_column("Campo", style="bold yellow", min_width=18)
        tabla_red.add_column("Valor", style="white")

        tabla_red.add_row("ISP", datos.get("isp", "N/A"))
        tabla_red.add_row("Organización", datos.get("organizacion", "N/A"))
        tabla_red.add_row("ASN", datos.get("asn", "N/A"))
        tabla_red.add_row("Es Proxy/VPN", _icono_bool(datos.get("es_proxy", False), "⚠ Sí", "No"))
        tabla_red.add_row("Es Hosting/DC", _icono_bool(datos.get("es_hosting", False), "Sí", "No"))
        console.print(tabla_red)
    else:
        console.print(f"[red]Error al obtener datos: {datos['error']}[/red]")

    console.print()


def mostrar_reporte_dominio(datos: dict):
    http = datos.get("http", {})
    whois_data = datos.get("whois", {})
    dns_data = datos.get("dns", {})
    ip_info = datos.get("info_ip", {})

    console.print()
    console.print(Panel(
        f"[bold cyan]Dominio:[/bold cyan]   {datos['dominio']}\n"
        f"[bold cyan]IP:[/bold cyan]        {datos.get('ip_resuelta', 'N/A')}\n"
        f"[bold cyan]HTTPS:[/bold cyan]     {_icono_bool(http.get('https', False), 'Activo', 'No disponible')}",
        title="[bold white on blue]  ANÁLISIS DE DOMINIO  [/bold white on blue]",
        border_style="cyan",
        padding=(1, 3),
    ))

    # ── WHOIS ──
    console.print(Rule("[bold magenta]WHOIS[/bold magenta]"))
    if "error" not in whois_data:
        tabla_whois = Table(box=box.ROUNDED, border_style="magenta", header_style="bold white", show_header=False)
        tabla_whois.add_column("Campo", style="bold yellow", min_width=18)
        tabla_whois.add_column("Valor", style="white")

        tabla_whois.add_row("Registrador", whois_data.get("registrador", "N/A"))
        tabla_whois.add_row("Creado", whois_data.get("creado", "N/A"))
        tabla_whois.add_row("Expira", whois_data.get("expira", "N/A"))
        tabla_whois.add_row("Actualizado", whois_data.get("actualizado", "N/A"))
        tabla_whois.add_row("Estado", whois_data.get("estado", "N/A"))
        tabla_whois.add_row("País registrante", whois_data.get("pais_registrante", "N/A"))
        for i, ns in enumerate(whois_data.get("nameservers", []), 1):
            tabla_whois.add_row(f"Nameserver {i}", ns)
        console.print(tabla_whois)
    else:
        console.print(f"[yellow]WHOIS no disponible: {whois_data.get('error')}[/yellow]")

    # ── DNS ──
    console.print(Rule("[bold green]Registros DNS[/bold green]"))
    tabla_dns = Table(box=box.ROUNDED, border_style="green", header_style="bold white")
    tabla_dns.add_column("Tipo", style="bold yellow", min_width=7)
    tabla_dns.add_column("Valor", style="white")

    for tipo, valores in dns_data.items():
        if valores:
            for i, v in enumerate(valores):
                tabla_dns.add_row(tipo if i == 0 else "", str(v)[:110])
        else:
            tabla_dns.add_row(tipo, "[dim]Sin registro[/dim]")
    console.print(tabla_dns)

    # ── HTTP / SEGURIDAD ──
    console.print(Rule("[bold red]HTTP / Cabeceras de Seguridad[/bold red]"))
    if "error" not in http:
        tabla_http = Table(box=box.ROUNDED, border_style="red", header_style="bold white", show_header=False)
        tabla_http.add_column("Campo", style="bold yellow", min_width=18)
        tabla_http.add_column("Valor", style="white")

        tabla_http.add_row("Status HTTP", str(http.get("status", "N/A")))
        tabla_http.add_row("Servidor", http.get("servidor", "N/A"))
        tabla_http.add_row("Tecnología", http.get("tecnologia", "N/A"))
        tabla_http.add_row("URL final", str(http.get("url_final", "N/A"))[:90])
        tabla_http.add_row("HSTS", _icono_bool(http.get("hsts", False)))
        tabla_http.add_row("CSP", _icono_bool(http.get("csp", False)))
        tabla_http.add_row("X-Frame-Options", http.get("x_frame", "No configurado"))
        tabla_http.add_row("Referrer-Policy", http.get("referrer_policy", "No configurado"))
        console.print(tabla_http)
    else:
        console.print(f"[yellow]HTTP: {http.get('error', 'No disponible')}[/yellow]")

    # ── IP ASOCIADA ──
    if ip_info and "error" not in ip_info:
        console.print(Rule(f"[bold blue]IP Asociada — {datos.get('ip_resuelta')}[/bold blue]"))
        tabla_ip = Table(box=box.ROUNDED, border_style="blue", header_style="bold white", show_header=False)
        tabla_ip.add_column("Campo", style="bold yellow", min_width=18)
        tabla_ip.add_column("Valor", style="white")

        tabla_ip.add_row("País", f"{ip_info.get('pais', 'N/A')} ({ip_info.get('codigo_pais', '')})")
        tabla_ip.add_row("Ciudad", ip_info.get("ciudad", "N/A"))
        tabla_ip.add_row("ISP", ip_info.get("isp", "N/A"))
        tabla_ip.add_row("Organización", ip_info.get("organizacion", "N/A"))
        tabla_ip.add_row("ASN", ip_info.get("asn", "N/A"))
        tabla_ip.add_row("Es Proxy/VPN", _icono_bool(ip_info.get("es_proxy", False), "⚠ Sí", "No"))
        tabla_ip.add_row("Es Hosting/DC", _icono_bool(ip_info.get("es_hosting", False), "Sí", "No"))
        console.print(tabla_ip)

    console.print()


def mostrar_reporte(datos: dict):
    if datos.get("tipo") == "ip":
        mostrar_reporte_ip(datos)
    else:
        mostrar_reporte_dominio(datos)


# ─────────────────────────────────────────
# EXPORTACIÓN
# ─────────────────────────────────────────

def exportar_json(datos: dict, ruta: str):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2, default=str)
    console.print(f"\n[green]Reporte guardado en:[/green] [bold]{ruta}[/bold]")


# ─────────────────────────────────────────
# MENÚ INTERACTIVO
# ─────────────────────────────────────────

def menu_interactivo():
    console.print(Panel(
        "[bold cyan]Herramienta OSINT unificada[/bold cyan]\n"
        "Analiza dominios e IPs: WHOIS · DNS · Geolocalización · Seguridad HTTP",
        title="[bold white on blue]  OSINT CLI  [/bold white on blue]",
        border_style="cyan",
        padding=(1, 3),
    ))

    while True:
        console.print("\n[bold]Opciones:[/bold]")
        console.print("  [cyan]1.[/cyan] Analizar dominio  (ej: github.com)")
        console.print("  [cyan]2.[/cyan] Analizar IP       (ej: 8.8.8.8)")
        console.print("  [cyan]3.[/cyan] Salir\n")

        opcion = console.input("[bold]Elige (1-3): [/bold]").strip()

        if opcion == "1":
            dominio = console.input("[bold cyan]Dominio a analizar: [/bold cyan]").strip()
            if not dominio:
                console.print("[red]Dominio vacío.[/red]")
                continue
            salida = console.input("[dim]Guardar en JSON? (ej: reporte.json) o ENTER para omitir: [/dim]").strip() or None
            console.print(f"\n[bold]Analizando[/bold] [cyan]{dominio}[/cyan]...\n")
            datos = analizar_dominio(dominio)
            mostrar_reporte(datos)
            if salida:
                exportar_json(datos, salida)

        elif opcion == "2":
            ip = console.input("[bold cyan]IP a analizar: [/bold cyan]").strip()
            if not ip:
                console.print("[red]IP vacía.[/red]")
                continue
            if not es_ip(ip):
                console.print("[red]Formato de IP inválido. Ejemplo: 8.8.8.8[/red]")
                continue
            salida = console.input("[dim]Guardar en JSON? (ej: reporte.json) o ENTER para omitir: [/dim]").strip() or None
            console.print(f"\n[bold]Analizando[/bold] [cyan]{ip}[/cyan]...\n")
            datos = analizar_ip(ip)
            mostrar_reporte(datos)
            if salida:
                exportar_json(datos, salida)

        elif opcion == "3":
            console.print("\n[bold]Hasta pronto.[/bold]")
            break

        else:
            console.print("[red]Opción inválida.[/red]")


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OSINT CLI — Análisis de dominios e IPs",
        epilog=(
            "Ejemplos:\n"
            "  python3 osint_tools/osint_cli.py google.com\n"
            "  python3 osint_tools/osint_cli.py 8.8.8.8\n"
            "  python3 osint_tools/osint_cli.py github.com --output reporte.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("objetivo", nargs="?", help="Dominio o IP a analizar")
    parser.add_argument("-o", "--output", help="Guardar resultado en archivo .json")
    args = parser.parse_args()

    if not args.objetivo:
        try:
            menu_interactivo()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold]Saliendo.[/bold]")
        return 0

    objetivo = args.objetivo.strip()
    console.print(f"\n[bold]Analizando:[/bold] [cyan]{objetivo}[/cyan]\n")

    if es_ip(objetivo):
        datos = analizar_ip(objetivo)
    else:
        datos = analizar_dominio(objetivo)

    mostrar_reporte(datos)

    if args.output:
        exportar_json(datos, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
