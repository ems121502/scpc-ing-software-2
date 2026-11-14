"""
AuthMiddleware (Fase 2): filtra TODAS las peticiones.
1. Exige una sesión válida (CU-02 incluye CU-01).
2. Verifica en el servidor que el rol tenga permiso sobre la ruta (RN-09, DD-03).
3. Si no tiene permiso responde "Acceso restringido" y regresa al menú (RN-10).
"""
from django.contrib import messages
from django.shortcuts import redirect

from comun.http import respuesta_error
from menu.services import AutorizacionService

from .repositories import UsuarioRepository

RUTAS_PUBLICAS = ("/login/", "/api/auth/login", "/static/", "/favicon.ico")


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ruta = request.path
        request.usuario = None

        if ruta == "/" or ruta.startswith(RUTAS_PUBLICAS):
            return self.get_response(request)

        es_api = ruta.startswith("/api/")

        # 1. Sesión válida
        id_usuario = request.session.get("id_usuario")
        usuario = UsuarioRepository().obtener_por_id(id_usuario) if id_usuario else None
        if usuario is None or not usuario.activo:
            request.session.flush()
            if es_api:
                return respuesta_error("Sesión no válida o expirada", 401)
            return redirect("/login/?expirada=1")
        request.usuario = usuario

        # 2. Permiso del rol sobre la ruta solicitada
        autorizacion = AutorizacionService()
        codigo = autorizacion.funcionalidad_requerida(ruta)
        if codigo and not autorizacion.tiene_permiso(usuario.rol_id, codigo):
            if es_api:
                return respuesta_error("Acceso restringido", 403)
            messages.error(request, "Acceso restringido")
            return redirect("/menu/")

        return self.get_response(request)
