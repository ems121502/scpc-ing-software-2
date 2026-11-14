"""MenuController – controlador del CU-02 Seleccionar Tarea."""
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

from .services import AutorizacionService


class MenuController:
    @staticmethod
    @require_GET
    @ensure_csrf_cookie
    def pantalla_menu(request):
        return render(request, "menu/menu.html", {"usuario": request.usuario})

    @staticmethod
    @require_GET
    def api_menu(request):
        """GET /api/menu – RN-08: solo las opciones asignadas al rol."""
        usuario = request.usuario  # lo coloca AuthMiddleware
        return JsonResponse({
            "usuario": {
                "nombre_usuario": usuario.nombre_usuario,
                "nombre_completo": usuario.nombre_completo,
                "rol": usuario.rol.nombre,
            },
            "opciones": AutorizacionService().obtener_menu(usuario.rol_id),
        })

    @staticmethod
    @require_GET
    @ensure_csrf_cookie
    def modulo_no_implementado(request, titulo):
        """Opciones del menú cuyo módulo está fuera del alcance de la Fase 3."""
        return render(request, "menu/modulo_no_implementado.html",
                      {"usuario": request.usuario, "titulo": titulo})
