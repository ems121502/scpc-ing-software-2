"""
SolicitudController – controlador del CU-03 Registro de Compra.
Traduce las respuestas de SolicitudService a HTTP según la Fase 2, sección 7.2.
"""
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from comun.http import leer_json, respuesta_error

from .excepciones import (
    DatosInvalidosError,
    ErrorAlGuardarError,
    EstadoNoPermitidoError,
    NoEncontradoError,
    NoEsSolicitanteError,
    PermisoDenegadoError,
)
from .services import SolicitudService

FORMATO_FECHA = "%d/%m/%Y"


def _solicitud_a_dict(solicitud):
    return {
        "id": solicitud.id_solicitud,
        "numero": solicitud.numero,
        "fecha": solicitud.fecha_solicitud.strftime(FORMATO_FECHA),
        "estado": solicitud.estado,
        "estado_texto": solicitud.get_estado_display(),
        "lineas": [
            {
                "id": d.id_detalle,
                "codigo": d.producto.codigo,
                "producto": d.producto.nombre,
                "unidad": d.producto.unidad_medida,
                "cantidad": d.cantidad,
                "prioridad": d.prioridad,
                "prioridad_texto": d.get_prioridad_display(),
                "observacion": d.observacion or "",
            }
            for d in solicitud.detalles.all()
        ],
    }


class SolicitudController:
    @staticmethod
    @require_GET
    @ensure_csrf_cookie
    def pantalla(request):
        return render(request, "solicitudes/solicitud.html", {"usuario": request.usuario})

    @staticmethod
    @require_GET
    def nueva(request):
        """GET /api/solicitudes/nueva – cabecera automática (RN-13)."""
        try:
            datos = SolicitudService().preparar_nueva(request.usuario)
        except PermisoDenegadoError:
            return respuesta_error("Acceso restringido", 403)
        return JsonResponse({
            "numero_provisional": datos["numero_provisional"],
            "fecha": datos["fecha"].strftime(FORMATO_FECHA),
            "solicitante": datos["solicitante"],
        })

    @staticmethod
    @require_http_methods(["GET", "POST"])
    def coleccion(request):
        """GET /api/solicitudes (listar) y POST /api/solicitudes (registrar)."""
        servicio = SolicitudService()
        try:
            if request.method == "GET":
                solicitudes = servicio.listar(request.usuario)
                return JsonResponse({"solicitudes": [_solicitud_a_dict(s) for s in solicitudes]})

            datos = leer_json(request)
            if datos is None:
                return respuesta_error("Solicitud inválida", 400)
            solicitud = servicio.registrar(request.usuario, datos.get("lineas"))
            return JsonResponse(
                {"id": solicitud.id_solicitud, "numero": solicitud.numero,
                 "estado": solicitud.estado},
                status=201,
            )
        except PermisoDenegadoError:
            return respuesta_error("Acceso restringido", 403)
        except DatosInvalidosError as e:
            return respuesta_error("Hay datos inválidos en la solicitud", 400, errores=e.errores)
        except ErrorAlGuardarError:
            return respuesta_error(
                "No se pudo guardar la solicitud. No se guardó ningún dato; intente nuevamente.",
                500,
            )

    @staticmethod
    @require_http_methods(["DELETE"])
    def eliminar_detalle(request, id_solicitud, id_detalle):
        """DELETE /api/solicitudes/{id}/detalles/{idDetalle} – RN-19."""
        try:
            SolicitudService().eliminar_detalle(request.usuario, id_solicitud, id_detalle)
        except PermisoDenegadoError:
            return respuesta_error("Acceso restringido", 403)
        except NoEncontradoError:
            return respuesta_error("La solicitud o la línea no existe", 404)
        except NoEsSolicitanteError:
            return respuesta_error("Solo el solicitante puede modificar esta solicitud", 403)
        except EstadoNoPermitidoError:
            return respuesta_error(
                "Solo se pueden eliminar líneas de solicitudes en estado Pendiente", 409
            )
        return HttpResponse(status=204)
