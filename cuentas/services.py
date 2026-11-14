"""
AuthService – lógica de negocio del CU-01 Inicio de Sesión.
Reglas aplicadas: RN-01 a RN-05 y RN-07 (RN-06 se configura en settings).
"""
import math
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from .excepciones import CamposVaciosError, CredencialesInvalidasError, CuentaBloqueadaError
from .models import BitacoraAcceso
from .repositories import BitacoraRepository, UsuarioRepository


class AuthService:
    def __init__(self, usuarios=None, bitacora=None):
        self.usuarios = usuarios or UsuarioRepository()
        self.bitacora = bitacora or BitacoraRepository()

    def autenticar(self, nombre_usuario, contrasena):
        """Devuelve el Usuario autenticado o lanza una excepción del CU-01."""
        nombre_usuario = (nombre_usuario or "").strip()
        contrasena = contrasena or ""

        # RN-01: campos obligatorios (validados también en la pantalla)
        vacios = [campo for campo, valor in
                  (("usuario", nombre_usuario), ("contrasena", contrasena)) if not valor]
        if vacios:
            raise CamposVaciosError(vacios)

        usuario = self.usuarios.buscar_por_nombre_usuario(nombre_usuario)
        ahora = timezone.now()

        # RN-03 / RN-05: usuario inexistente o inactivo → mensaje genérico
        if usuario is None or not usuario.activo:
            make_password(contrasena)  # mismo tiempo de respuesta que una verificación real
            self.bitacora.registrar(usuario, nombre_usuario, BitacoraAcceso.FALLIDO)
            raise CredencialesInvalidasError()

        # RN-04: cuenta bloqueada
        if usuario.esta_bloqueado(ahora):
            self.bitacora.registrar(usuario, nombre_usuario, BitacoraAcceso.BLOQUEADO)
            raise CuentaBloqueadaError(self._minutos_restantes(usuario, ahora))

        # El bloqueo ya venció: se reinicia el contador
        if usuario.bloqueado_hasta is not None:
            usuario.bloqueado_hasta = None
            usuario.intentos_fallidos = 0

        # RN-02: verificación contra el hash bcrypt
        if not check_password(contrasena, usuario.contrasena_hash):
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= settings.SCPC_INTENTOS_MAXIMOS:
                usuario.bloqueado_hasta = ahora + timedelta(minutes=settings.SCPC_MINUTOS_BLOQUEO)
                self.usuarios.actualizar_control_acceso(usuario)
                self.bitacora.registrar(usuario, nombre_usuario, BitacoraAcceso.BLOQUEADO)
                raise CuentaBloqueadaError(settings.SCPC_MINUTOS_BLOQUEO)
            self.usuarios.actualizar_control_acceso(usuario)
            self.bitacora.registrar(usuario, nombre_usuario, BitacoraAcceso.FALLIDO)
            raise CredencialesInvalidasError()

        # Ingreso correcto: RN-04 reinicia el contador; RN-07 registra el acceso
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        self.usuarios.actualizar_control_acceso(usuario)
        self.bitacora.registrar(usuario, nombre_usuario, BitacoraAcceso.EXITOSO)
        return usuario

    @staticmethod
    def _minutos_restantes(usuario, ahora):
        segundos = (usuario.bloqueado_hasta - ahora).total_seconds()
        return max(1, math.ceil(segundos / 60))
