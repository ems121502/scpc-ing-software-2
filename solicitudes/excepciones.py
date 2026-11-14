"""Excepciones del CU-03. SolicitudController las traduce a códigos HTTP (Fase 2, 7.2)."""


class DatosInvalidosError(Exception):
    """RF-09: errores de validación por fila y campo → HTTP 400."""

    def __init__(self, errores):
        super().__init__("Datos inválidos")
        self.errores = errores


class PermisoDenegadoError(Exception):
    """RN-12: el rol no puede registrar solicitudes → HTTP 403."""


class NoEsSolicitanteError(Exception):
    """RN-19: la solicitud pertenece a otro usuario → HTTP 403."""


class EstadoNoPermitidoError(Exception):
    """RN-19: la solicitud no está Pendiente → HTTP 409."""


class NoEncontradoError(Exception):
    """La solicitud o la línea no existe → HTTP 404."""


class ErrorAlGuardarError(Exception):
    """RN-18: falló la base de datos; la transacción se revirtió → HTTP 500."""
