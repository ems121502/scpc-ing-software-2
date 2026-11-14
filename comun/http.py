"""Utilidades HTTP compartidas por los controladores."""
import json

from django.http import JsonResponse


def leer_json(request):
    """Devuelve el cuerpo JSON como dict, o None si no es un objeto JSON válido."""
    try:
        datos = json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return None
    return datos if isinstance(datos, dict) else None


def respuesta_error(mensaje, estado, **extra):
    """Respuesta JSON de error con el formato común {"error": "...", ...}."""
    cuerpo = {"error": mensaje}
    cuerpo.update(extra)
    return JsonResponse(cuerpo, status=estado)
