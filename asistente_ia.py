"""Análisis pericial asistido por Claude, con consumo de tokens limitado.

Es opcional: el informe se genera completo sin IA. Cuando se pide, se envía a la API de Anthropic solo un resumen
estructurado del monitoreo (no las capturas ni el HTML del sitio). Límites:

- F0R3NSIC_IA_TOKENS_DIA: tokens (entrada + salida) permitidos por día UTC. Por defecto 50 000.
- F0R3NSIC_IA_MAX_SALIDA: tokens máximos de respuesta por informe. Por defecto 2 500.
- F0R3NSIC_IA_MAX_ENTRADA: tokens máximos del resumen enviado. Por defecto 12 000.
- F0R3NSIC_IA_MODELO: modelo a usar. Por defecto claude-opus-5-5.

Si el mismo resumen ya se analizó, se reutiliza la respuesta guardada y no se consumen tokens.
"""

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
USO_FILE = ROOT / "data" / "ia_uso.json"
CACHE_DIR = ROOT / "data" / "ia_cache"
MODELO = os.environ.get("F0R3NSIC_IA_MODELO", "claude-opus-5-5")
_lock = threading.Lock()


def _entero(nombre, defecto):
    try:
        return max(0, int(os.environ.get(nombre, defecto)))
    except ValueError:
        return defecto


LIMITE_DIARIO = _entero("F0R3NSIC_IA_TOKENS_DIA", 50000)
MAX_SALIDA = _entero("F0R3NSIC_IA_MAX_SALIDA", 2500)
MAX_ENTRADA = _entero("F0R3NSIC_IA_MAX_ENTRADA", 12000)

SISTEMA = """Eres el asistente técnico de un perito informático. Recibes, en JSON, el resumen de un monitoreo
automatizado de una URL: consultas HTTP periódicas, cambios detectados (estado, contenido, IP, certificado TLS, DNS,
IP de salida del equipo), lagunas de monitoreo, trazas de ruta, WHOIS y capturas manuales del analista.

Redacta en español, con tono técnico, neutral y verificable, para un informe pericial:
- Basa cada afirmación únicamente en los datos recibidos y cita la fecha UTC o el valor concreto que la sostiene.
- No atribuyas autoría ni identidad a personas u organizaciones más allá de lo que digan los registros (WHOIS, ASN).
- Distingue hechos observados de interpretaciones técnicas; marca las interpretaciones como tales.
- Señala lo que los datos no permiten concluir (lagunas, saltos sin respuesta, registros WHOIS ocultos, CDN).
- No inventes datos ausentes ni recomiendes eludir protecciones del sitio.

Formato: texto plano con estos encabezados en líneas propias, que empiezan por «## »:
## Hallazgos
## Interpretación técnica
## Limitaciones
Usa viñetas que empiecen por «- ». Máximo 450 palabras."""


def _hoy():
    return datetime.now(timezone.utc).date().isoformat()


def _leer_uso():
    try:
        return json.loads(USO_FILE.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _registrar_uso(entrada, salida):
    with _lock:
        uso = _leer_uso()
        dia = uso.setdefault(_hoy(), {"entrada": 0, "salida": 0, "llamadas": 0})
        dia["entrada"] += entrada
        dia["salida"] += salida
        dia["llamadas"] += 1
        # Se conservan los últimos 60 días.
        uso = dict(sorted(uso.items())[-60:])
        USO_FILE.parent.mkdir(parents=True, exist_ok=True)
        USO_FILE.write_text(json.dumps(uso, indent=2), encoding="utf-8")


def estado():
    """Disponibilidad y consumo del día, para mostrarlo en la interfaz antes de pedir el análisis."""
    dia = _leer_uso().get(_hoy(), {})
    usados = dia.get("entrada", 0) + dia.get("salida", 0)
    try:
        import anthropic  # noqa: F401
        sdk = True
    except ImportError:
        sdk = False
    credenciales = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
    motivo = None
    if not sdk:
        motivo = "Falta el paquete anthropic: venv/bin/pip install -r requirements.txt"
    elif not credenciales:
        motivo = "Define ANTHROPIC_API_KEY antes de iniciar app.py para activar el análisis asistido."
    elif LIMITE_DIARIO - usados < MAX_SALIDA + 500:
        motivo = "Se alcanzó el límite diario de tokens."
    return {"disponible": motivo is None, "motivo": motivo, "modelo": MODELO, "limite_diario": LIMITE_DIARIO,
            "usados_hoy": usados, "restantes_hoy": max(0, LIMITE_DIARIO - usados), "max_salida": MAX_SALIDA,
            "max_entrada": MAX_ENTRADA, "llamadas_hoy": dia.get("llamadas", 0)}


def analizar(resumen):
    """Devuelve {"texto", "modelo", "tokens_entrada", "tokens_salida", "entrada_sha256", "reutilizado"} o {"error"}."""
    contenido = json.dumps(resumen, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    huella = hashlib.sha256(f"{MODELO}\n{SISTEMA}\n{contenido}".encode("utf-8")).hexdigest()
    cache = CACHE_DIR / f"{huella}.json"
    if cache.exists():
        try:
            guardado = json.loads(cache.read_text("utf-8"))
            return guardado | {"reutilizado": True, "tokens_consumidos_ahora": 0}
        except ValueError:
            pass
    info = estado()
    if not info["disponible"]:
        return {"error": info["motivo"]}
    import anthropic

    client = anthropic.Anthropic(max_retries=2, timeout=180.0)
    mensajes = [{"role": "user", "content": "Datos del monitoreo (JSON):\n" + contenido}]
    try:
        entrada = client.messages.count_tokens(model=MODELO, system=SISTEMA, messages=mensajes).input_tokens
    except anthropic.APIStatusError as exc:
        if exc.status_code in (401, 403):
            return {"error": "La API rechazó las credenciales de Anthropic."}
        entrada = len(SISTEMA + contenido) // 3
    except anthropic.APIConnectionError:
        return {"error": "No se pudo conectar con la API de Anthropic."}
    if entrada > MAX_ENTRADA:
        return {"error": f"El resumen ocupa {entrada} tokens y supera el máximo de entrada ({MAX_ENTRADA})."}
    if entrada + MAX_SALIDA > info["restantes_hoy"]:
        return {"error": f"Quedan {info['restantes_hoy']} tokens hoy y el análisis puede requerir hasta {entrada + MAX_SALIDA}."}
    try:
        respuesta = client.beta.messages.create(
            model=MODELO,
            max_tokens=MAX_SALIDA,
            system=SISTEMA,
            messages=mensajes,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.AuthenticationError:
        return {"error": "La API rechazó las credenciales de Anthropic."}
    except anthropic.RateLimitError:
        return {"error": "La API de Anthropic limitó la solicitud; inténtalo más tarde."}
    except anthropic.APIStatusError as exc:
        return {"error": f"La API de Anthropic devolvió HTTP {exc.status_code}."}
    except anthropic.APIConnectionError:
        return {"error": "No se pudo conectar con la API de Anthropic."}
    uso = respuesta.usage
    consumidos_entrada = (uso.input_tokens or 0) + (getattr(uso, "cache_creation_input_tokens", 0) or 0) + (getattr(uso, "cache_read_input_tokens", 0) or 0)
    _registrar_uso(consumidos_entrada, uso.output_tokens or 0)
    if respuesta.stop_reason == "refusal":
        return {"error": "El modelo declinó analizar este resumen; el informe se emite sin análisis asistido."}
    texto = "\n".join(bloque.text for bloque in respuesta.content if bloque.type == "text").strip()
    if not texto:
        return {"error": "El modelo no devolvió texto."}
    resultado = {"texto": texto, "modelo": respuesta.model, "tokens_entrada": consumidos_entrada, "tokens_salida": uso.output_tokens,
                 "truncado": respuesta.stop_reason == "max_tokens", "entrada_sha256": huella, "generado_at": datetime.now(timezone.utc).isoformat()}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultado | {"reutilizado": False, "tokens_consumidos_ahora": consumidos_entrada + (uso.output_tokens or 0)}
