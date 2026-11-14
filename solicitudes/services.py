"""
SolicitudService – lógica de negocio del CU-03 Registro de Compra.
Reglas aplicadas: RN-12, RN-13, RN-14 a RN-17 (vía ValidadorSolicitud),
RN-18 (transacción) y RN-19 (estados y eliminación de líneas).
"""
import logging

from django.db import DatabaseError, transaction
from django.utils import timezone

from menu.services import AutorizacionService

from .excepciones import (
    DatosInvalidosError,
    ErrorAlGuardarError,
    EstadoNoPermitidoError,
    NoEncontradoError,
    NoEsSolicitanteError,
    PermisoDenegadoError,
)
from .models import SolicitudCompra
from .repositories import SolicitudRepository
from .validators import ValidadorSolicitud

logger = logging.getLogger(__name__)

FUNCIONALIDAD_REGISTRAR = "ORDENES_COMPRA"


class SolicitudService:
    def __init__(self, repositorio=None, validador=None, autorizacion=None):
        self.repositorio = repositorio or SolicitudRepository()
        self.validador = validador or ValidadorSolicitud()
        self.autorizacion = autorizacion or AutorizacionService()

    def _verificar_rol(self, usuario):
        """RN-12: además del middleware, el servicio vuelve a verificar el rol."""
        if not self.autorizacion.tiene_permiso(usuario.rol_id, FUNCIONALIDAD_REGISTRAR):
            raise PermisoDenegadoError()

    def preparar_nueva(self, usuario):
        """RN-13: número provisional, fecha y solicitante automáticos."""
        self._verificar_rol(usuario)
        return {
            "numero_provisional": self.repositorio.siguiente_numero_provisional(),
            "fecha": timezone.localdate(),
            "solicitante": usuario.nombre_completo,
        }

    def registrar(self, usuario, lineas):
        self._verificar_rol(usuario)

        lineas_limpias, errores = self.validador.validar(lineas)
        if errores:
            raise DatosInvalidosError(errores)

        # RN-18: cabecera y líneas en una sola transacción (todo o nada)
        try:
            with transaction.atomic():
                solicitud = self.repositorio.crear_cabecera(usuario, timezone.localdate())
                self.repositorio.crear_detalles(solicitud, lineas_limpias)
        except DatabaseError as error:  # incluye IntegrityError
            logger.exception("Error al guardar la solicitud: %s", error)
            raise ErrorAlGuardarError() from error
        return solicitud

    def listar(self, usuario):
        self._verificar_rol(usuario)
        return self.repositorio.listar_por_usuario(usuario.id_usuario)

    def eliminar_detalle(self, usuario, id_solicitud, id_detalle):
        """
        RN-19: solo líneas de solicitudes propias en estado Pendiente.
        Si se elimina la última línea, la solicitud pasa a Cancelada.
        Devuelve el estado final de la solicitud.
        """
        self._verificar_rol(usuario)
        with transaction.atomic():
            solicitud = self.repositorio.obtener_para_actualizar(id_solicitud)
            if solicitud is None:
                raise NoEncontradoError()
            if solicitud.usuario_id != usuario.id_usuario:
                raise NoEsSolicitanteError()
            if solicitud.estado != SolicitudCompra.PENDIENTE:
                raise EstadoNoPermitidoError()

            detalle = self.repositorio.obtener_detalle(id_solicitud, id_detalle)
            if detalle is None:
                raise NoEncontradoError()

            self.repositorio.eliminar_detalle(detalle)
            if self.repositorio.contar_detalles(id_solicitud) == 0:
                self.repositorio.actualizar_estado(solicitud, SolicitudCompra.CANCELADA)
        return solicitud.estado
