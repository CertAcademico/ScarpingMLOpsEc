"""Informe pericial del monitoreo: análisis de la línea de tiempo y documento HTML autocontenido.

El HTML no lleva JavaScript ni recursos externos: los gráficos son SVG generados aquí, para que el documento se pueda
abrir, imprimir o convertir a PDF sin conexión, y su SHA-256 identifique exactamente lo que se entregó.
"""

import html
from collections import Counter
from datetime import datetime, timezone

HERRAMIENTA = "F0R3nsic Web · ScrapingMLOpsEc"
VERSION_INFORME = "1.0"


def esc(valor):
    return html.escape("" if valor is None else str(valor), quote=True)


def _dt(iso):
    try:
        valor = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def fecha(iso, segundos=True):
    valor = _dt(iso)
    if not valor:
        return "—"
    return valor.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC" if segundos else "%Y-%m-%d %H:%M UTC")


def duracion(segundos):
    segundos = int(max(0, segundos))
    dias, resto = divmod(segundos, 86400)
    horas, resto = divmod(resto, 3600)
    minutos = resto // 60
    partes = [f"{dias} d" if dias else "", f"{horas} h" if horas else "", f"{minutos} min" if minutos and not dias else ""]
    return " ".join(p for p in partes if p) or f"{segundos} s"


def clase_estado(status):
    if status is None:
        return "none"
    if 200 <= status < 300:
        return "ok"
    if status in (401, 403, 429) or 300 <= status < 400:
        return "warn"
    return "bad"


ETIQUETA_ESTADO = {"ok": "Accesible (2xx)", "warn": "Rechazada / redirección", "bad": "Error", "none": "Sin respuesta"}
ETIQUETA_CAMBIO = {"estado": "Estado HTTP", "contenido": "Contenido", "ip": "IP del servidor", "tls": "Certificado TLS",
                   "salida": "IP de salida", "dns": "Resolución DNS"}


def _dns_texto(cambios):
    partes = []
    for cambio in cambios or []:
        detalle = []
        if cambio.get("anadidos"):
            detalle.append("+ " + ", ".join(cambio["anadidos"][:4]))
        if cambio.get("retirados"):
            detalle.append("− " + ", ".join(cambio["retirados"][:4]))
        partes.append(f"{cambio['tipo']}: {' / '.join(detalle) or 'modificado'}")
    return "; ".join(partes)


def analizar(monitor, timeline):
    """Calcula los hechos del informe a partir de la línea de tiempo. No modifica nada."""
    auto = [r for r in timeline if not r.get("tipo")]
    manual = [r for r in timeline if r.get("tipo") == "manual"]
    eventos = [r for r in timeline if r.get("tipo") == "evento"]
    trazas = [r for r in timeline if r.get("tipo") == "traza"]
    instantes = [_dt(r.get("at")) for r in timeline if _dt(r.get("at"))]
    inicio = min(instantes) if instantes else _dt(monitor.get("created_at"))
    fin = max(instantes) if instantes else inicio
    intervalo = monitor.get("interval", 900)

    clases = Counter(clase_estado(r.get("status")) for r in auto)
    codigos = Counter("sin respuesta" if r.get("status") is None else str(r["status"]) for r in auto)
    tiempos = sorted(r["ms"] for r in auto if r.get("ms") is not None and r.get("status") is not None)
    cambios = Counter(c for r in auto for c in r.get("cambios") or [])

    # Lagunas: dos consultas automáticas consecutivas más separadas que el doble del intervalo (y al menos 10 min más).
    lagunas = []
    umbral = max(2 * intervalo, intervalo + 600)
    for anterior, siguiente in zip(auto, auto[1:]):
        a, b = _dt(anterior["at"]), _dt(siguiente["at"])
        if a and b and (b - a).total_seconds() > umbral:
            lagunas.append({"desde": anterior["at"], "hasta": siguiente["at"], "segundos": (b - a).total_seconds()})

    # Cobertura de la vigilancia DNS a partir de los eventos de encendido y apagado.
    cobertura, abierta = [], None
    for evento in eventos:
        if evento.get("evento") == "dns_on" and abierta is None:
            abierta = evento["at"]
        elif evento.get("evento") == "dns_off" and abierta is not None:
            cobertura.append({"desde": abierta, "hasta": evento["at"]})
            abierta = None
    if abierta is not None:
        cobertura.append({"desde": abierta, "hasta": fin.isoformat() if fin else abierta, "abierta": True})
    segundos_periodo = (fin - inicio).total_seconds() if inicio and fin else 0
    segundos_dns = sum(max(0, (_dt(c["hasta"]) - _dt(c["desde"])).total_seconds()) for c in cobertura)

    cambios_dns = [{"at": r["at"], "cambios": r["dns_cambios"]} for r in auto if r.get("dns_cambios")]
    ultimo_dns = next((r["dns"] for r in reversed(timeline) if r.get("dns")), None)

    # Cronología de hechos relevantes, con el valor anterior de cada cambio.
    hechos, previo = [], None
    if auto:
        hechos.append({"at": auto[0]["at"], "clase": "inicio", "titulo": "Primera consulta automática",
                       "detalle": f"HTTP {auto[0].get('status') or 'sin respuesta'} · {(auto[0].get('diagnostico') or {}).get('causa', '')}"})
    # El monitor compara cada campo con su último valor conocido (una consulta sin respuesta no borra la huella ni las IP),
    # así que la cronología muestra ese mismo valor de referencia.
    conocido = {}
    for registro in auto:
        for cambio in registro.get("cambios") or []:
            if cambio == "estado":
                detalle = f"{previo.get('status') or 'sin respuesta'} → {registro.get('status') or 'sin respuesta'} · {(registro.get('diagnostico') or {}).get('causa', '')}" if previo else ""
            elif cambio == "contenido":
                detalle = f"Huella {str(conocido.get('huella'))[:12]}… → {str(registro.get('huella'))[:12]}… · evidencia {registro.get('evidence_file') or '—'}"
            elif cambio == "ip":
                detalle = f"{', '.join(conocido.get('ips') or [])} → {', '.join(registro.get('ips') or [])}"
            elif cambio == "tls":
                detalle = f"Vencimiento {(conocido.get('tls') or {}).get('valido_hasta')} → {(registro.get('tls') or {}).get('valido_hasta')} · emisor {(registro.get('tls') or {}).get('emisor')}"
            elif cambio == "salida":
                detalle = f"{(conocido.get('origen') or {}).get('ip')} → {(registro.get('origen') or {}).get('ip')} ({(registro.get('origen') or {}).get('pais') or '—'})"
            elif cambio == "dns":
                detalle = _dns_texto(registro.get("dns_cambios"))
            else:
                detalle = ""
            hechos.append({"at": registro["at"], "clase": cambio, "titulo": f"Cambio · {ETIQUETA_CAMBIO.get(cambio, cambio)}", "detalle": detalle})
        previo = registro
        for campo in ("huella", "ips", "tls"):
            if registro.get(campo):
                conocido[campo] = registro[campo]
        if (registro.get("origen") or {}).get("ip"):
            conocido["origen"] = registro["origen"]
    for evento in eventos:
        nombre = {"dns_on": "Vigilancia DNS activada", "dns_off": "Vigilancia DNS desactivada",
                  "informe": "Informe pericial emitido"}.get(evento.get("evento"), evento.get("evento"))
        detalle = evento.get("detalle") or ""
        if evento.get("dns"):
            registros = evento["dns"].get("registros") or {}
            detalle = f"Línea base: A {', '.join(registros.get('A') or ['—'])} · NS {', '.join(registros.get('NS') or ['—'])}"
        hechos.append({"at": evento["at"], "clase": "evento", "titulo": nombre, "detalle": detalle})
    for registro in manual:
        hechos.append({"at": registro.get("observado_at") or registro["at"], "clase": "manual", "titulo": "Captura manual del analista",
                       "detalle": f"{registro.get('nombre_original')} · SHA-256 {registro.get('sha256', '')[:16]}… · {registro.get('nota') or 'sin nota'}"})
    ruta_previa = None
    for traza in trazas:
        ruta = [s.get("ip") for s in (traza.get("traza") or {}).get("saltos", []) if s.get("ip")]
        detalle = f"{len((traza.get('traza') or {}).get('saltos', []))} saltos · {'destino alcanzado' if (traza.get('traza') or {}).get('alcanzado') else 'destino no confirmado'}"
        if ruta_previa is not None and ruta != ruta_previa:
            detalle += " · la ruta difiere de la traza anterior"
        hechos.append({"at": traza["at"], "clase": "traza", "titulo": "Traza de red (traceroute + WHOIS)", "detalle": detalle})
        ruta_previa = ruta
    for laguna in lagunas:
        hechos.append({"at": laguna["desde"], "clase": "laguna", "titulo": "Laguna de monitoreo",
                       "detalle": f"Sin consultas durante {duracion(laguna['segundos'])}, hasta {fecha(laguna['hasta'])}"})
    if len(auto) > 1:
        hechos.append({"at": auto[-1]["at"], "clase": "fin", "titulo": "Última consulta automática",
                       "detalle": f"HTTP {auto[-1].get('status') or 'sin respuesta'} · {(auto[-1].get('diagnostico') or {}).get('causa', '')}"})
    hechos.sort(key=lambda h: _dt(h["at"]) or inicio)

    ips_servidor = {}
    for registro in auto:
        for ip in registro.get("ips") or []:
            item = ips_servidor.setdefault(ip, {"ip": ip, "primera": registro["at"], "ultima": registro["at"], "veces": 0})
            item["ultima"], item["veces"] = registro["at"], item["veces"] + 1
    origenes = {}
    for registro in auto + manual + trazas:
        origen = registro.get("origen") or {}
        if not origen.get("ip"):
            continue
        item = origenes.setdefault(origen["ip"], {"ip": origen["ip"], "ubicacion": ", ".join(v for v in (origen.get("ciudad"), origen.get("region"), origen.get("pais")) if v),
                                                  "red": origen.get("red"), "primera": registro["at"], "ultima": registro["at"], "veces": 0})
        item["ultima"], item["veces"] = registro["at"], item["veces"] + 1

    evidencias, vistos = [], set()
    for registro in timeline:
        if registro.get("evidence_file") and registro.get("sha256") and not registro.get("evidencia_reutilizada") and registro["evidence_file"] not in vistos:
            vistos.add(registro["evidence_file"])
            evidencias.append({"at": registro["at"], "archivo": registro["evidence_file"], "sha256": registro["sha256"], "bytes": registro.get("bytes"),
                               "tipo": "Captura manual" if registro.get("tipo") == "manual" else f"Respuesta HTTP {registro.get('status') or '—'}"})
        snapshot = registro.get("snapshot") or {}
        if snapshot.get("file") and snapshot["file"] not in vistos:
            vistos.add(snapshot["file"])
            evidencias.append({"at": registro["at"], "archivo": f"data/osint_evidence/{snapshot['file']}", "sha256": snapshot.get("sha256"),
                               "bytes": snapshot.get("bytes"), "tipo": "Snapshot visual (PNG)", "snapshot": snapshot["file"]})

    ultima_traza = next((r for r in reversed(trazas)), None)
    ultimo_auto = auto[-1] if auto else None
    p95 = tiempos[min(len(tiempos) - 1, int(len(tiempos) * 0.95))] if tiempos else None
    return {
        "monitor": monitor, "auto": auto, "manual": manual, "eventos": eventos, "trazas": trazas,
        "inicio": inicio.isoformat() if inicio else None, "fin": fin.isoformat() if fin else None, "segundos_periodo": segundos_periodo,
        "total": len(auto), "clases": clases, "codigos": codigos, "cambios": cambios, "lagunas": lagunas,
        "segundos_laguna": sum(l["segundos"] for l in lagunas),
        "ms": {"min": tiempos[0] if tiempos else None, "max": tiempos[-1] if tiempos else None,
               "media": round(sum(tiempos) / len(tiempos)) if tiempos else None, "p95": p95},
        "cobertura_dns": cobertura, "segundos_dns": segundos_dns, "cambios_dns": cambios_dns, "ultimo_dns": ultimo_dns,
        "dns_activo": bool(monitor.get("dns_watch")), "hechos": hechos, "ips_servidor": list(ips_servidor.values()),
        "origenes": list(origenes.values()), "evidencias": evidencias, "ultima_traza": ultima_traza, "ultimo": ultimo_auto,
    }


def dictamen(a):
    """Conclusiones descriptivas, redactadas solo a partir de los datos calculados."""
    m, total = a["monitor"], a["total"]
    if not total:
        return ["El monitor aún no registra consultas automáticas; no hay base para conclusiones."]
    pct = lambda n: f"{n / total * 100:.1f} %"
    respondidas = total - a["clases"].get("none", 0)
    frases = [
        f"Entre el {fecha(a['inicio'])} y el {fecha(a['fin'])} ({duracion(a['segundos_periodo'])}) se realizaron {total} consultas "
        f"automáticas a {m['url']}, con un intervalo configurado de {duracion(m.get('interval', 0))}.",
        f"El servidor respondió en {respondidas} consultas ({pct(respondidas)}). Entregó el contenido (2xx) en {a['clases'].get('ok', 0)} "
        f"({pct(a['clases'].get('ok', 0))}), rechazó o redirigió la consulta en {a['clases'].get('warn', 0)} ({pct(a['clases'].get('warn', 0))}) "
        f"y devolvió error en {a['clases'].get('bad', 0)} ({pct(a['clases'].get('bad', 0))}).",
    ]
    if a["ms"]["media"] is not None:
        frases.append(f"El tiempo de respuesta medio fue de {a['ms']['media']} ms (mínimo {a['ms']['min']} ms, p95 {a['ms']['p95']} ms, máximo {a['ms']['max']} ms).")
    listado = ", ".join(f"{ETIQUETA_CAMBIO.get(k, k).lower()}: {v}" for k, v in a["cambios"].most_common())
    frases.append(f"Se registraron cambios entre consultas consecutivas ({listado})." if listado else "No se registraron cambios entre consultas consecutivas.")
    if a["cobertura_dns"]:
        porcentaje = a["segundos_dns"] / a["segundos_periodo"] * 100 if a["segundos_periodo"] else 100
        base = f"La vigilancia DNS estuvo activa durante {duracion(a['segundos_dns'])} ({porcentaje:.0f} % del periodo observado). "
        if a["cambios_dns"]:
            base += f"En ese tiempo se detectaron {len(a['cambios_dns'])} cambios de resolución; el último, el {fecha(a['cambios_dns'][-1]['at'])}: {_dns_texto(a['cambios_dns'][-1]['cambios'])}."
        else:
            base += "No se detectaron cambios en los registros DNS vigilados."
        frases.append(base)
    else:
        frases.append("La vigilancia DNS no se activó en este monitor; los cambios de resolución fuera de las IP observadas en cada consulta no están documentados.")
    if a["lagunas"]:
        frases.append(f"Se identificaron {len(a['lagunas'])} lagunas de monitoreo que suman {duracion(a['segundos_laguna'])}; en esos intervalos no existen observaciones.")
    traza = (a["ultima_traza"] or {}).get("traza")
    if traza:
        destino = next((s for s in reversed(traza.get("saltos", [])) if s.get("ip")), None)
        red = (destino or {}).get("red") or {}
        frases.append(f"La última traza de red ({fecha(a['ultima_traza']['at'])}) {'alcanzó' if traza.get('alcanzado') else 'no confirmó'} el destino "
                      f"{traza.get('destino')} en {len(traza.get('saltos', []))} saltos" + (f"; el último salto que respondió pertenece a {red.get('asn')} {red.get('titular') or ''}".rstrip() + "." if red.get("asn") else "."))
    if a["manual"]:
        frases.append(f"El analista incorporó {len(a['manual'])} capturas manuales, identificadas por su SHA-256 en el inventario de evidencias.")
    return frases


# ── Gráficos SVG ──────────────────────────────────────────────────────────────────────────────────────────────────

COLOR = {"ok": "var(--ok)", "warn": "var(--warn)", "bad": "var(--bad)", "none": "url(#rayado)"}


def svg_linea_tiempo(a):
    auto = a["auto"]
    if not auto:
        return '<p class="vacio">Sin consultas automáticas que representar.</p>'
    W, L, R = 1000, 118, 16
    filas = {"dns": 34, "estado": 64, "resp": 112}
    alto_resp, eje = 120, 112 + 120 + 22
    H = eje + 10
    marcas = [_dt(r["at"]).timestamp() for r in a["manual"] + a["trazas"] + a["eventos"] if _dt(r.get("at"))]
    tiempos = [_dt(r["at"]).timestamp() for r in auto]
    paso = (tiempos[-1] - tiempos[0]) / (len(tiempos) - 1) if len(tiempos) > 1 else a["monitor"].get("interval", 900)
    t0 = min([tiempos[0]] + marcas)
    t1 = max([tiempos[-1] + max(paso * 0.6, 60)] + [v + 60 for v in marcas])
    x = lambda v: L + (v - t0) / (t1 - t0) * (W - L - R)
    ms = [r["ms"] for r in auto if r.get("ms") is not None and r.get("status") is not None]
    maximo = max([100] + ms)
    escala = next((s for s in (50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000, 20000) if maximo / s <= 4), 50000)
    tope = -(-int(maximo * 1.05) // escala) * escala
    y = lambda v: filas["resp"] + alto_resp - v / tope * alto_resp
    umbral = max(2 * a["monitor"].get("interval", 900), a["monitor"].get("interval", 900) + 600)

    partes = [f'<svg class="grafico" viewBox="0 0 {W} {H}" role="img" aria-label="Línea de tiempo del monitoreo">',
              '<defs><pattern id="rayado" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
              '<rect width="6" height="6" fill="var(--panel)"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--muted)" stroke-width="2"/></pattern></defs>',
              f'<text class="fila" x="0" y="{filas["dns"] + 11}">Vigilancia DNS</text>',
              f'<text class="fila" x="0" y="{filas["estado"] + 15}">Estado HTTP</text>',
              f'<text class="fila" x="0" y="{filas["resp"] + 10}">Respuesta</text><text class="sub" x="0" y="{filas["resp"] + 23}">milisegundos</text>']
    # Franja de cobertura DNS
    partes.append(f'<rect x="{L}" y="{filas["dns"]}" width="{W - L - R}" height="14" rx="3" fill="var(--panel)"/>')
    for tramo in a["cobertura_dns"]:
        x0, x1 = x(_dt(tramo["desde"]).timestamp()), x(_dt(tramo["hasta"]).timestamp())
        partes.append(f'<rect x="{x0:.1f}" y="{filas["dns"]}" width="{max(2, x1 - x0):.1f}" height="14" rx="3" fill="var(--dns)" opacity=".85"><title>Vigilancia DNS activa: {esc(fecha(tramo["desde"]))} – {esc(fecha(tramo["hasta"]))}</title></rect>')
    # Franja de estado; los tramos sin consulta (lagunas) se dejan en blanco con borde punteado.
    for i, registro in enumerate(auto):
        inicio = tiempos[i]
        final = tiempos[i + 1] if i + 1 < len(auto) else t1
        laguna = final - inicio > umbral
        if laguna:
            final = inicio + a["monitor"].get("interval", 900)
        x0, ancho = x(inicio), max(1.5, x(final) - x(inicio))
        clase = clase_estado(registro.get("status"))
        partes.append(f'<rect x="{x0:.1f}" y="{filas["estado"]}" width="{ancho:.1f}" height="22" fill="{COLOR[clase]}"><title>{esc(fecha(registro["at"]))} · HTTP {esc(registro.get("status") or "sin respuesta")}</title></rect>')
        if laguna:
            g0, g1 = x(final), x(tiempos[i + 1])
            partes.append(f'<rect x="{g0:.1f}" y="{filas["estado"]}" width="{max(1, g1 - g0):.1f}" height="22" fill="none" stroke="var(--muted)" stroke-dasharray="3 3"><title>Laguna de monitoreo</title></rect>')
            if g1 - g0 > 60:
                partes.append(f'<text class="sub" x="{(g0 + g1) / 2:.1f}" y="{filas["estado"] + 15}" text-anchor="middle">sin datos</text>')
    # Rejilla y curva de tiempo de respuesta
    valor = 0
    while valor <= tope:
        partes.append(f'<line class="rejilla" x1="{L}" x2="{W - R}" y1="{y(valor):.1f}" y2="{y(valor):.1f}"/><text class="tick" x="{L - 6}" y="{y(valor) + 3:.1f}" text-anchor="end">{valor / 1000:g} s</text>'
                      if valor >= 1000 else f'<line class="rejilla" x1="{L}" x2="{W - R}" y1="{y(valor):.1f}" y2="{y(valor):.1f}"/><text class="tick" x="{L - 6}" y="{y(valor) + 3:.1f}" text-anchor="end">{valor}</text>')
        valor += escala
    trazo, pluma = "", False
    for i, registro in enumerate(auto):
        if registro.get("ms") is None or registro.get("status") is None or (i and tiempos[i] - tiempos[i - 1] > umbral):
            pluma = False
            if registro.get("ms") is None or registro.get("status") is None:
                continue
        trazo += f'{"L" if pluma else "M"}{x(tiempos[i]):.1f},{y(registro["ms"]):.1f}'
        pluma = True
    if trazo:
        partes.append(f'<path class="curva" d="{trazo}"/>')
    # Marcas: cambios, cambios DNS, trazas, capturas manuales
    ultima_etiqueta = -1e9
    for i, registro in enumerate(auto):
        cambios = registro.get("cambios") or []
        if not cambios:
            continue
        cx = x(tiempos[i])
        dns = "dns" in cambios
        partes.append(f'<line class="{"marca-dns" if dns else "marca"}" x1="{cx:.1f}" x2="{cx:.1f}" y1="{filas["dns"] - 6}" y2="{filas["resp"] + alto_resp}"><title>{esc(fecha(registro["at"]))} · {esc(", ".join(cambios))}</title></line>')
        if cx - ultima_etiqueta > 70:
            derecha = cx > W - R - 80
            partes.append(f'<text class="{"etq-dns" if dns else "etq"}" x="{cx + (-3 if derecha else 3):.1f}" y="{filas["dns"] - 10}" text-anchor="{"end" if derecha else "start"}">{esc(" · ".join(cambios))}</text>')
            ultima_etiqueta = cx
    for registro in a["trazas"]:
        cx = x(_dt(registro["at"]).timestamp())
        partes.append(f'<path class="traza" d="M{cx:.1f},{filas["estado"] + 26} l5,9 h-10 z"><title>Traza de red · {esc(fecha(registro["at"]))}</title></path>')
    for registro in a["manual"]:
        cx = x(_dt(registro.get("observado_at") or registro["at"]).timestamp())
        cy = filas["estado"] - 6
        partes.append(f'<rect class="manual" x="{cx - 4:.1f}" y="{cy - 4:.1f}" width="8" height="8" transform="rotate(45 {cx:.1f} {cy:.1f})"><title>Captura manual · {esc(fecha(registro.get("observado_at") or registro["at"]))}</title></rect>')
    # Eje temporal
    marcas_eje = 6
    for k in range(marcas_eje + 1):
        v = t0 + (t1 - t0) * k / marcas_eje
        formato = "%H:%M:%S" if t1 - t0 < 3600 else "%d/%m %H:%M" if t1 - t0 < 4 * 86400 else "%d/%m/%Y"
        etiqueta = datetime.fromtimestamp(v, timezone.utc).strftime(formato)
        partes.append(f'<text class="tick" x="{x(v):.1f}" y="{eje}" text-anchor="{"start" if k == 0 else "end" if k == marcas_eje else "middle"}">{etiqueta}</text>')
    partes.append("</svg>")
    leyenda = ('<div class="leyenda"><span><i style="background:var(--ok)"></i>Accesible 2xx</span><span><i style="background:var(--warn)"></i>Rechazada 401/403/429 o redirección</span>'
               '<span><i style="background:var(--bad)"></i>Error</span><span><i class="rayas"></i>Sin respuesta</span><span><i class="hueco"></i>Laguna de monitoreo</span>'
               '<span><i style="background:var(--dns)"></i>Vigilancia DNS activa</span><span><i class="linea-dns"></i>Cambio DNS</span><span><i class="linea"></i>Otro cambio</span>'
               '<span><i class="tri"></i>Traza de red</span><span><i class="rombo"></i>Captura manual</span><span><i class="curva-l"></i>Tiempo de respuesta</span></div>')
    return "".join(partes) + leyenda


def barras_estado(a):
    total = a["total"] or 1
    filas = []
    for codigo, cantidad in a["codigos"].most_common(8):
        clase = clase_estado(None if codigo == "sin respuesta" else int(codigo))
        filas.append(f'<div class="barra"><span class="barra-etq">{esc("HTTP " + codigo if codigo != "sin respuesta" else "Sin respuesta")}</span>'
                     f'<span class="barra-pista"><span class="barra-valor b-{clase}" style="width:{cantidad / total * 100:.1f}%"></span></span>'
                     f'<span class="barra-num">{cantidad} · {cantidad / total * 100:.1f} %</span></div>')
    return "".join(filas) or '<p class="vacio">Sin datos.</p>'


def ruta_html(traza_registro):
    if not traza_registro:
        return '<p class="vacio">Aún no se ha ejecutado una traza de red para este monitor. Usa «Traza de red» en la pestaña Monitoreo.</p>'
    traza = traza_registro.get("traza") or {}
    if traza.get("error") and not traza.get("saltos"):
        return f'<p class="vacio">{esc(traza["error"])}</p>'
    paleta = ["#2f6fd6", "#1f9d74", "#c2571a", "#7b5cd6", "#b03a6b", "#2b8a99", "#8a6d1f"]
    colores = {}
    filas = []
    for salto in traza.get("saltos", []):
        red = salto.get("red") or {}
        clave = red.get("asn") or ("privada" if red.get("titular") == "Red privada / local" else None)
        color = colores.setdefault(clave, paleta[len(colores) % len(paleta)]) if clave else "var(--muted)"
        filas.append(f'<li class="salto{" mudo" if not salto.get("ip") else ""}"><span class="punto" style="background:{color}"></span>'
                     f'<span class="s-num">{salto["salto"]}</span><span class="s-ip">{esc(salto.get("ip") or "* sin respuesta")}'
                     f'{"<small> también " + esc(", ".join(salto["ips_alternativas"])) + "</small>" if salto.get("ips_alternativas") else ""}</span>'
                     f'<span class="s-host">{esc(salto.get("hostname") or "—")}</span>'
                     f'<span class="s-red">{esc(red.get("asn") or "")} {esc(red.get("titular") or ("sin datos de ASN" if salto.get("ip") else ""))}{" · " + esc(red["pais"]) if red.get("pais") else ""}</span>'
                     f'<span class="s-ms">{str(salto["rtt_ms"]) + " ms" if salto.get("rtt_ms") is not None else "—"}</span></li>')
    cabecera = (f'<p class="meta">Ejecutada el {esc(fecha(traza_registro["at"]))} desde {esc((traza_registro.get("origen") or {}).get("ip") or "origen desconocido")} · '
                f'destino {esc(traza.get("destino"))} · {"destino alcanzado" if traza.get("alcanzado") else "destino no confirmado (los últimos saltos no respondieron)"} · '
                f'comando <code>{esc(traza.get("comando"))}</code></p>')
    return cabecera + '<ol class="ruta"><li class="salto cab"><span></span><span>#</span><span>IP</span><span>Hostname (PTR)</span><span>Red (ASN)</span><span>RTT</span></li>' + "".join(filas) + "</ol>"


def _tabla(filas, cabeceras, clase=""):
    cuerpo = "".join("<tr>" + "".join(f"<td>{celda}</td>" for celda in fila) + "</tr>" for fila in filas)
    return f'<table class="{clase}"><thead><tr>{"".join(f"<th>{esc(c)}</th>" for c in cabeceras)}</tr></thead><tbody>{cuerpo}</tbody></table>'


def _ia_html(ia):
    if not ia:
        return ""
    if ia.get("error"):
        return f'<section><h2>10. Análisis asistido</h2><p class="vacio">No se incluyó: {esc(ia["error"])}</p></section>'
    bloques, lista = [], []

    def cerrar_lista():
        if lista:
            bloques.append("<ul>" + "".join(lista) + "</ul>")
            lista.clear()

    for linea in ia["texto"].splitlines():
        linea = linea.strip()
        if not linea:
            cerrar_lista()
        elif linea.startswith("#"):
            cerrar_lista()
            bloques.append(f"<h3>{esc(linea.lstrip('#').strip())}</h3>")
        elif linea.startswith(("- ", "* ", "• ")):
            lista.append(f"<li>{esc(linea[2:].strip())}</li>")
        else:
            cerrar_lista()
            bloques.append(f"<p>{esc(linea)}</p>")
    cerrar_lista()
    return (f'<section class="ia"><h2>10. Análisis técnico asistido por IA</h2>'
            f'<p class="aviso">Texto generado por {esc(ia.get("modelo"))} a partir del resumen estructurado de este informe (SHA-256 de la entrada '
            f'<code>{esc(ia.get("entrada_sha256", "")[:24])}…</code>, {esc(ia.get("tokens_entrada"))} tokens de entrada y {esc(ia.get("tokens_salida"))} de salida'
            f'{", reutilizado de un análisis previo idéntico" if ia.get("reutilizado") else ""}). No constituye evidencia: es una ayuda de redacción que el perito '
            f'debe verificar contra las secciones anteriores.{" La respuesta se cortó por el límite de tokens." if ia.get("truncado") else ""}</p>'
            + "".join(bloques) + "</section>")


def resumen_para_ia(a):
    """Resumen compacto para el análisis asistido: sin HTML ni capturas, solo hechos y métricas."""
    traza = (a["ultima_traza"] or {}).get("traza") or {}
    whois = (a["ultima_traza"] or {}).get("whois") or {}
    return {
        "url": a["monitor"]["url"], "periodo_utc": [a["inicio"], a["fin"]], "intervalo_s": a["monitor"].get("interval"),
        "consultas": a["total"], "resultados": dict(a["clases"]), "codigos_http": dict(a["codigos"]), "tiempo_respuesta_ms": a["ms"],
        "cambios": dict(a["cambios"]), "lagunas": [{"desde": l["desde"], "hasta": l["hasta"]} for l in a["lagunas"][:30]],
        "vigilancia_dns": {"tramos": a["cobertura_dns"][:20], "cambios": a["cambios_dns"][-40:],
                           "registros_actuales": (a["ultimo_dns"] or {}).get("registros"), "soa": (a["ultimo_dns"] or {}).get("soa")},
        "ultimo_diagnostico": (a["ultimo"] or {}).get("diagnostico"), "certificado_tls": (a["ultimo"] or {}).get("tls"),
        "ips_servidor": a["ips_servidor"][:20], "origenes_consulta": a["origenes"][:10],
        "traza": {"destino": traza.get("destino"), "alcanzado": traza.get("alcanzado"),
                  "saltos": [{"n": s["salto"], "ip": s.get("ip"), "host": s.get("hostname"), "asn": (s.get("red") or {}).get("asn"),
                              "titular": (s.get("red") or {}).get("titular")} for s in traza.get("saltos", [])]},
        "whois": {k: v for k, v in whois.items() if k not in ("emails",)},
        "capturas_manuales": [{"observado": r.get("observado_at") or r["at"], "nota": r.get("nota")} for r in a["manual"][-20:]],
        "hechos": [{"at": h["at"], "tipo": h["clase"], "titulo": h["titulo"], "detalle": h["detalle"]} for h in a["hechos"][-150:]],
    }


ESTILOS = """
:root{--bg:#f6f7f9;--paper:#fff;--text:#16202a;--muted:#5f6c78;--line:#d9dee4;--panel:#eef1f4;--accent:#11755d;
--ok:#1f9d74;--warn:#d1951b;--bad:#d0453f;--dns:#7b5cd6;--trace:#2f6fd6;--manual:#16202a}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0b1016;--paper:#111821;--text:#e8eef3;--muted:#93a1ae;--line:#26323f;
--panel:#18222d;--accent:#7be0c3;--manual:#e8eef3}}
:root[data-theme="dark"]{--bg:#0b1016;--paper:#111821;--text:#e8eef3;--muted:#93a1ae;--line:#26323f;--panel:#18222d;--accent:#7be0c3;--manual:#e8eef3}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:1060px;margin:0 auto;padding:32px 16px 60px}.hoja{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:36px 40px}
header.portada{border-bottom:3px solid var(--accent);padding-bottom:20px;margin-bottom:8px}.sello{font:600 11px ui-monospace,monospace;letter-spacing:.14em;color:var(--accent);text-transform:uppercase}
h1{font-size:26px;margin:6px 0 4px;line-height:1.2}h2{font-size:17px;margin:34px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}h3{font-size:14px;margin:18px 0 6px}
.objeto{font:13px ui-monospace,monospace;overflow-wrap:anywhere;color:var(--text)}.meta{color:var(--muted);font-size:12px}
.ficha{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:6px 22px;margin-top:16px;font-size:12px}.ficha div{display:flex;flex-direction:column}.ficha b{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:600}
.cifras{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin:14px 0}.cifra{border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:var(--panel)}
.cifra b{display:block;font-size:22px;line-height:1.2}.cifra span{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em}
.dictamen{border-left:4px solid var(--accent);background:var(--panel);padding:12px 16px;border-radius:0 8px 8px 0}.dictamen p{margin:6px 0}
.grafico{width:100%;height:auto;display:block}.grafico .fila{font-size:11px;font-weight:650;fill:var(--text)}.grafico .sub,.grafico .tick{font-size:10px;fill:var(--muted)}
.grafico .rejilla{stroke:var(--line)}.grafico .curva{fill:none;stroke:var(--trace);stroke-width:2;stroke-linejoin:round}
.grafico .marca{stroke:var(--muted);stroke-dasharray:2 3}.grafico .marca-dns{stroke:var(--dns);stroke-width:2}.grafico .etq{font-size:10px;fill:var(--muted)}.grafico .etq-dns{font-size:10px;fill:var(--dns);font-weight:700}
.grafico .traza{fill:var(--trace)}.grafico .manual{fill:var(--manual)}
.leyenda{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:11px;color:var(--muted);margin-top:8px}.leyenda i{display:inline-block;width:12px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.leyenda .rayas{background:repeating-linear-gradient(45deg,var(--muted) 0 2px,var(--panel) 2px 4px)}.leyenda .hueco{border:1px dashed var(--muted)}
.leyenda .linea-dns{width:2px;background:var(--dns)}.leyenda .linea{width:1px;background:var(--muted)}.leyenda .curva-l{height:2px;background:var(--trace);vertical-align:3px}
.leyenda .tri{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:9px solid var(--trace);border-radius:0}.leyenda .rombo{width:8px;height:8px;background:var(--manual);transform:rotate(45deg)}
.barra{display:grid;grid-template-columns:130px 1fr 110px;gap:10px;align-items:center;font-size:12px;margin:5px 0}.barra-pista{background:var(--panel);border-radius:4px;height:14px;overflow:hidden}
.barra-valor{display:block;height:100%;border-radius:4px}.b-ok{background:var(--ok)}.b-warn{background:var(--warn)}.b-bad{background:var(--bad)}.b-none{background:var(--muted)}.barra-num{color:var(--muted);text-align:right}
table{width:100%;border-collapse:collapse;font-size:12px;margin:8px 0}th{text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);border-bottom:2px solid var(--line);padding:6px 8px}
td{border-bottom:1px solid var(--line);padding:6px 8px;vertical-align:top;overflow-wrap:anywhere}td code,.mono{font:11px ui-monospace,monospace}
.hechos td:first-child{white-space:nowrap;font:11px ui-monospace,monospace}.etiqueta{display:inline-block;font-size:10px;font-weight:700;padding:1px 7px;border-radius:10px;background:var(--panel);white-space:nowrap}
.c-dns{background:var(--dns);color:#fff}.c-estado{background:var(--warn);color:#1b1300}.c-contenido{background:var(--trace);color:#fff}.c-laguna{background:transparent;border:1px dashed var(--muted)}.c-traza{background:var(--trace);color:#fff}
.c-manual{background:var(--manual);color:var(--paper)}.c-ip,.c-tls{background:#c2571a;color:#fff}
.ruta{list-style:none;padding:0;margin:10px 0}.salto{display:grid;grid-template-columns:16px 28px minmax(120px,1fr) minmax(140px,1.3fr) minmax(170px,1.6fr) 70px;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid var(--line);font-size:12px;position:relative}
.salto.cab{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);border-bottom-width:2px}.punto{width:12px;height:12px;border-radius:50%}
.salto:not(.cab):not(:last-child) .punto:after{content:"";position:absolute;left:5px;top:26px;width:2px;height:calc(100% - 14px);background:var(--line)}
.salto.mudo{color:var(--muted)}.s-ip{font:12px ui-monospace,monospace}.s-ip small{display:block;color:var(--muted)}.s-ms{text-align:right;font:11px ui-monospace,monospace}.s-host{overflow-wrap:anywhere}
.dos{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px}.dos>*{min-width:0}.vacio{color:var(--muted);font-style:italic}.aviso{font-size:12px;color:var(--muted);background:var(--panel);padding:10px 12px;border-radius:6px}
.capturas{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}.capturas figure{margin:0;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.capturas img{display:block;width:100%;height:140px;object-fit:cover;object-position:top;background:#fff}.capturas figcaption{font-size:10px;padding:6px 8px;color:var(--muted)}
.firma{margin-top:40px;display:grid;grid-template-columns:1fr 1fr;gap:40px}.firma div{border-top:1px solid var(--text);padding-top:6px;font-size:12px;color:var(--muted)}
footer{margin-top:30px;font-size:11px;color:var(--muted);border-top:1px solid var(--line);padding-top:12px}
code{word-break:break-all}.hoja{overflow-wrap:anywhere}
@media(max-width:720px){table{display:block;overflow-x:auto}td{min-width:90px}.hechos td:first-child{white-space:normal}.hoja{padding:22px 16px}.dos,.firma{grid-template-columns:1fr}.salto{grid-template-columns:14px 24px 1fr;}.salto .s-host,.salto .s-red{grid-column:3}.salto .s-ms{grid-column:3;text-align:left}.salto.cab{display:none}.barra{grid-template-columns:90px 1fr}.barra-num{grid-column:2;text-align:left}}
@media print{:root{--bg:#fff;--paper:#fff;--text:#000;--muted:#555;--line:#ccc;--panel:#f2f2f2;--manual:#000}body{background:#fff}main{padding:0;max-width:none}.hoja{border:0;padding:0}
h2{break-after:avoid}section{break-inside:auto}table,tr,.salto,figure,.cifras{break-inside:avoid}a{color:inherit;text-decoration:none}}
"""


def generar(monitor, timeline, *, informe_id, emitido_at, timeline_sha256, timeline_registros, analista=None, caso=None, ia=None, a=None):
    """Devuelve el HTML completo del informe."""
    a = a or analizar(monitor, timeline)
    ultimo = a["ultimo"] or {}
    traza_registro = a["ultima_traza"]
    whois = (traza_registro or {}).get("whois") or {}
    dns_actual = a["ultimo_dns"] or ((traza_registro or {}).get("dns"))
    respondidas = a["total"] - a["clases"].get("none", 0)
    cifras = [
        ("Consultas", a["total"]), ("Respondidas", f"{respondidas / a['total'] * 100:.0f} %" if a["total"] else "—"),
        ("Accesibles 2xx", a["clases"].get("ok", 0)), ("Rechazadas", a["clases"].get("warn", 0)),
        ("Tiempo medio", f"{a['ms']['media']} ms" if a["ms"]["media"] is not None else "—"),
        ("Cambios de contenido", a["cambios"].get("contenido", 0)), ("Cambios DNS", len(a["cambios_dns"])),
        ("Cambios de IP", a["cambios"].get("ip", 0)), ("Lagunas", len(a["lagunas"])), ("Evidencias", len(a["evidencias"])),
    ]

    # 4. Cronología
    hechos = a["hechos"]
    filas_hechos = [[esc(fecha(h["at"])), f'<span class="etiqueta c-{esc(h["clase"])}">{esc(h["clase"])}</span>', f'<b>{esc(h["titulo"])}</b><br>{esc(h["detalle"])}'] for h in hechos[-400:]]
    nota_hechos = f'<p class="meta">Se muestran los últimos 400 de {len(hechos)} hechos; el CSV del monitor contiene el registro completo.</p>' if len(hechos) > 400 else ""

    # 5. DNS
    if a["cobertura_dns"]:
        tramos = _tabla([[esc(fecha(t["desde"])), esc(fecha(t["hasta"])) + (" (sigue activa)" if t.get("abierta") else ""), esc(duracion((_dt(t["hasta"]) - _dt(t["desde"])).total_seconds()))] for t in a["cobertura_dns"]],
                        ["Activada", "Desactivada", "Duración"])
    else:
        tramos = '<p class="vacio">La vigilancia DNS no se activó para este monitor.</p>'
    if a["cambios_dns"]:
        filas = []
        for cambio in a["cambios_dns"]:
            for detalle in cambio["cambios"]:
                filas.append([esc(fecha(cambio["at"])), f'<b>{esc(detalle["tipo"])}</b>', "<br>".join(esc(v) for v in detalle.get("antes") or ["—"]),
                              "<br>".join(esc(v) for v in detalle.get("despues") or ["—"]), esc(detalle.get("nota") or "")])
        cambios_dns = _tabla(filas, ["Detectado", "Registro", "Antes", "Después", "Observación"])
    else:
        cambios_dns = '<p class="vacio">No se detectaron cambios de resolución DNS en los tramos vigilados.</p>'
    if dns_actual:
        registros = dns_actual.get("registros") or {}
        filas = [[f"<b>{esc(tipo)}</b>", "<br>".join(f"<code>{esc(v)}</code>" for v in valores) or "—", esc((dns_actual.get("ttl") or {}).get(tipo, "—"))]
                 for tipo, valores in registros.items()]
        soa = dns_actual.get("soa") or {}
        if soa:
            filas.append(["<b>SOA</b>", f"<code>{esc(soa.get('servidor_primario'))}</code> · responsable {esc(soa.get('responsable'))} · serial <code>{esc(soa.get('serial'))}</code>", "—"])
        if dns_actual.get("ptr"):
            filas.append(["<b>PTR</b>", "<br>".join(f"<code>{esc(ip)}</code> → {esc(nombre)}" for ip, nombre in dns_actual["ptr"].items()), "—"])
        dns_tabla = (f'<p class="meta">Consulta del {esc(fecha(dns_actual.get("consultado_at")))} · host {esc(dns_actual.get("host"))} · zona {esc(dns_actual.get("zona"))} · '
                     f'resolvedores del equipo: {esc(", ".join(dns_actual.get("resolvedores") or []) or "—")}</p>' + _tabla(filas, ["Tipo", "Valor", "TTL (s)"]))
    else:
        dns_tabla = '<p class="vacio">Sin fotografía DNS. Activa la vigilancia DNS o ejecuta una traza de red.</p>'

    # 6. Infraestructura
    if whois and not whois.get("error"):
        claves = [("Dominio", "dominio"), ("Registrador", "registrador"), ("Servidor WHOIS", "whois_servidor"), ("Creado", "creado"), ("Actualizado", "actualizado"),
                  ("Expira", "expira"), ("Servidores DNS declarados", "servidores_dns"), ("Estado", "estado"), ("Titular", "titular"), ("Organización", "organizacion"),
                  ("País", "pais"), ("DNSSEC", "dnssec")]
        filas = []
        for etiqueta, clave in claves:
            valor = whois.get(clave)
            if isinstance(valor, list):
                valor = ", ".join(valor)
            filas.append([esc(etiqueta), esc(valor) if valor else '<span class="vacio">no publicado</span>'])
        whois_tabla = f'<p class="meta">Consulta del {esc(fecha(whois.get("consultado_at")))}</p>' + _tabla(filas, ["Campo", "Valor"])
    else:
        whois_tabla = f'<p class="vacio">{esc(whois.get("error") or "Sin datos WHOIS: ejecuta una traza de red para obtenerlos.")}</p>'
    tls = ultimo.get("tls") or {}
    servidor = _tabla([
        ["IP resueltas (última consulta)", esc(", ".join(ultimo.get("ips") or []) or "—")],
        ["Certificado TLS · sujeto", esc(tls.get("sujeto") or "—")], ["Certificado TLS · emisor", esc(tls.get("emisor") or "—")],
        ["Certificado TLS · válido hasta", esc(tls.get("valido_hasta") or "—")],
        ["Proveedor / protección detectada", esc((ultimo.get("diagnostico") or {}).get("proveedor") or "Ninguno identificado")],
        ["Cabecera Server", esc((ultimo.get("headers") or {}).get("Server") or "—")],
    ], ["Dato", "Valor"])
    ips_tabla = _tabla([[f"<code>{esc(i['ip'])}</code>", esc(fecha(i["primera"])), esc(fecha(i["ultima"])), esc(i["veces"])] for i in a["ips_servidor"][:40]],
                       ["IP del servidor", "Primera vez", "Última vez", "Consultas"]) if a["ips_servidor"] else '<p class="vacio">Sin IP registradas.</p>'
    origenes = _tabla([[f"<code>{esc(o['ip'])}</code>", esc(o["ubicacion"] or "—"), esc(o["red"] or "—"), esc(fecha(o["primera"])), esc(fecha(o["ultima"])), esc(o["veces"])] for o in a["origenes"][:30]],
                      ["IP de salida", "Ubicación aproximada", "Red", "Primera vez", "Última vez", "Registros"]) if a["origenes"] else '<p class="vacio">Sin datos de origen.</p>'

    # 8. Evidencias
    filas_ev = [[esc(fecha(e["at"])), esc(e["tipo"]), f"<code>{esc(e['archivo'])}</code>", f"<code>{esc(e['sha256'])}</code>", esc(f"{e['bytes']:,}".replace(",", ".") if e.get("bytes") else "—")] for e in a["evidencias"][-300:]]
    evidencias = _tabla(filas_ev, ["Fecha", "Tipo", "Archivo", "SHA-256", "Bytes"]) if filas_ev else '<p class="vacio">Sin evidencias registradas.</p>'
    snaps = [e for e in a["evidencias"] if e.get("snapshot")][-6:]
    capturas = ('<div class="capturas">' + "".join(f'<figure><img src="../osint_evidence/{esc(e["snapshot"])}" alt="Snapshot del {esc(fecha(e["at"]))}" loading="lazy">'
                                                  f'<figcaption>{esc(fecha(e["at"]))}<br>SHA-256 {esc((e["sha256"] or "")[:16])}…</figcaption></figure>' for e in snaps) + "</div>") if snaps else ""

    lagunas = _tabla([[esc(fecha(l["desde"])), esc(fecha(l["hasta"])), esc(duracion(l["segundos"]))] for l in a["lagunas"][:60]], ["Desde", "Hasta", "Duración"]) if a["lagunas"] else '<p class="meta">No se detectaron lagunas: todas las consultas consecutivas están dentro del doble del intervalo configurado.</p>'

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Informe pericial {esc(informe_id)}</title><style>{ESTILOS}</style></head>
<body><main><article class="hoja">
<header class="portada"><div class="sello">Informe pericial · monitoreo de sitio web</div>
<h1>Observación continua de {esc(monitor["url"])}</h1>
<div class="ficha">
<div><b>N.º de informe</b><span class="mono">{esc(informe_id)}</span></div>
<div><b>Caso / referencia</b><span>{esc(caso or "—")}</span></div>
<div><b>Perito / analista</b><span>{esc(analista or "—")}</span></div>
<div><b>Emitido</b><span>{esc(fecha(emitido_at))}</span></div>
<div><b>Periodo observado</b><span>{esc(fecha(a["inicio"], False))} – {esc(fecha(a["fin"], False))}</span></div>
<div><b>Herramienta</b><span>{esc(HERRAMIENTA)} · informe v{VERSION_INFORME}</span></div>
<div><b>Monitor</b><span class="mono">{esc(monitor["id"])} · {"activo" if monitor.get("active") else "en pausa"}</span></div>
<div><b>Zona horaria</b><span>Todas las horas en UTC</span></div>
</div></header>

<section><h2>1. Resumen ejecutivo</h2><div class="cifras">{"".join(f'<div class="cifra"><b>{esc(v)}</b><span>{esc(k)}</span></div>' for k, v in cifras)}</div>
<div class="dictamen">{"".join(f"<p>{esc(f)}</p>" for f in dictamen(a))}</div></section>

<section><h2>2. Objeto, alcance y metodología</h2>
<p><b>Objeto.</b> Documentar la disponibilidad, el contenido entregado y la infraestructura de red de <span class="objeto">{esc(monitor["url"])}</span> mediante consultas periódicas automatizadas, con preservación de cada respuesta.</p>
<ul>
<li>Una consulta HTTP GET por intervalo ({esc(duracion(monitor.get("interval", 0)))}), sin seguir enlaces, con el agente <code>ScrapingMLOpsEc/1.0</code>, hasta 5 redirecciones y 4 MB por respuesta. Se respeta <code>Retry-After</code>.</li>
<li>Cada respuesta se identifica con SHA-256 del cuerpo y una huella de contenido (sin scripts, estilos ni tokens volátiles) para distinguir cambios reales de variaciones automáticas. Las respuestas nuevas se guardan en <code>data/osint_evidence/</code>.</li>
<li>En cada consulta se resuelven las IP del servidor y se lee el certificado TLS sin caché, y se registra la IP pública de salida del equipo (ipinfo.io o ipwho.is).</li>
<li>Vigilancia DNS (interruptor por monitor): cuando está activa, cada consulta obtiene sin caché los registros A, AAAA, CNAME, NS, MX, TXT, CAA y SOA, y los compara con la observación anterior. El encendido y apagado queda en la línea de tiempo.</li>
<li>Traza de red a petición del analista: <code>traceroute</code> (o <code>tracert</code>) hacia la IP del servidor, con PTR y sistema autónomo de cada salto (DNS de Team Cymru), más WHOIS del dominio.</li>
<li>La herramienta no elude protecciones: si el sitio deniega el acceso, se conserva la respuesta de denegación como evidencia.</li>
</ul></section>

<section><h2>3. Línea de tiempo</h2>{svg_linea_tiempo(a)}
<div class="dos" style="margin-top:22px"><div><h3>Distribución de respuestas</h3>{barras_estado(a)}</div><div><h3>Lagunas de monitoreo</h3>{lagunas}</div></div></section>

<section><h2>4. Cronología de hechos relevantes</h2>{nota_hechos}{_tabla(filas_hechos, ["Fecha (UTC)", "Tipo", "Hecho"], "hechos") if filas_hechos else '<p class="vacio">Sin hechos registrados.</p>'}</section>

<section><h2>5. Vigilancia de DNS y resolución de dominio</h2><h3>Tramos vigilados</h3>{tramos}<h3>Cambios de resolución detectados</h3>{cambios_dns}<h3>Registros DNS vigentes</h3>{dns_tabla}</section>

<section><h2>6. Infraestructura de red y registro del dominio</h2><h3>Traza de ruta</h3>{ruta_html(traza_registro)}
<div class="dos"><div><h3>Registro del dominio (WHOIS)</h3>{whois_tabla}</div><div><h3>Servidor</h3>{servidor}<h3>IP del servidor observadas</h3>{ips_tabla}</div></div></section>

<section><h2>7. Origen de las consultas</h2><p class="meta">IP pública desde la que salieron las consultas de este equipo (con VPN, la del servidor VPN). La ubicación es la que el servicio de geolocalización asocia a la IP.</p>{origenes}</section>

<section><h2>8. Inventario de evidencias</h2><p class="meta">Archivos conservados durante el monitoreo. La integridad de cada uno se verifica recalculando su SHA-256 (p. ej. <code>shasum -a 256 &lt;archivo&gt;</code>).</p>{evidencias}{capturas}</section>

<section><h2>9. Limitaciones</h2><ul>
<li>Las consultas solo se ejecutan mientras <code>app.py</code> está en marcha; fuera de esos periodos no hay observaciones (ver lagunas).</li>
<li>Las respuestas reflejan lo que el servidor entregó a esta herramienta desde la IP de salida indicada; otros clientes, ubicaciones o navegadores con JavaScript pueden recibir contenido distinto.</li>
<li>Los registros DNS se obtienen con los resolvedores del sistema; un CDN o un DNS geográfico puede devolver otras IP en otras redes. Los cambios entre dos observaciones se detectan en la siguiente consulta, no en el instante exacto en que ocurrieron.</li>
<li>Muchos routers y CDN no responden a traceroute: los saltos «sin respuesta» no indican caída. Traceroute y DNS no usan el proxy HTTP configurado en la app.</li>
<li>Los datos WHOIS y ASN provienen de registros públicos de terceros y pueden estar ocultos por servicios de privacidad; no identifican por sí solos al operador del sitio.</li>
<li>Los snapshots visuales se renderizan desde el HTML capturado, sin JavaScript ni recursos externos; pueden diferir de la vista en un navegador.</li>
</ul></section>
{_ia_html(ia)}
<section><h2>{"11" if ia else "10"}. Integridad del informe</h2>
<p>Al emitir este informe, la línea de tiempo del monitor (<code>data/monitors/{esc(monitor["id"])}.jsonl</code>) contenía <b>{esc(timeline_registros)}</b> registros y su SHA-256 era:</p>
<p><code>{esc(timeline_sha256)}</code></p>
<p class="meta">El SHA-256 de este documento HTML se guarda junto a él en un archivo <code>.sha256</code> con el mismo nombre y se registra en <code>data/reports/index.json</code>. Cualquier modificación del documento cambia ese valor.</p>
<div class="firma"><div>Firma del perito / analista</div><div>Lugar y fecha</div></div></section>
<footer>Generado por {esc(HERRAMIENTA)} el {esc(fecha(emitido_at))}. Documento autocontenido, sin JavaScript ni recursos remotos.</footer>
</article></main></body></html>"""
