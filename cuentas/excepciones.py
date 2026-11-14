"""Excepciones del CU-01. AuthController las traduce a códigos HTTP (Fase 2, 7.2)."""


class CamposVaciosError(Exception):
    """RN-01: usuario o contraseña vacíos → HTTP 400."""

    def __init__(self, campos):
        super().__init__("Campos obligatorios vacíos")
        self.campos = campos


class CredencialesInvalidasError(Exception):
    """RN-03 / RN-05: usuario inexistente, inactivo o contraseña incorrecta → HTTP 401."""


class CuentaBloqueadaError(Exception):
    """RN-04: cuenta bloqueada temporalmente → HTTP 423."""

    def __init__(self, minutos_restantes):
        super().__init__("Cuenta bloqueada")
        self.minutos_restantes = minutos_restantes
