"""
AuthController – controlador del CU-01 Inicio de Sesión.
Recibe la petición, delega en AuthService y traduce el resultado a HTTP
según la Fase 2, sección 7.2 (200 / 400 / 401 / 423).
"""
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import rotate_token
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from comun.http import leer_json, respuesta_error

from .excepciones import CamposVaciosError, CredencialesInvalidasError, CuentaBloqueadaError
from .services import AuthService

MENSAJE_GENERICO = "Usuario o contraseña incorrectos"  # RN-05


class AuthController:
    @staticmethod
    @require_GET
    def inicio(request):
        return redirect("/menu/" if request.session.get("id_usuario") else "/login/")

    @staticmethod
    @require_GET
    @ensure_csrf_cookie
    def pantalla_login(request):
        if request.session.get("id_usuario"):
            return redirect("/menu/")
        return render(request, "cuentas/login.html")

    @staticmethod
    @require_POST
    def login(request):
        """POST /api/auth/login  {usuario, contrasena}"""
        datos = leer_json(request)
        if datos is None:
            return respuesta_error("Solicitud inválida", 400)

        try:
            usuario = AuthService().autenticar(datos.get("usuario"), datos.get("contrasena"))
        except CamposVaciosError as e:
            return respuesta_error("Ingrese usuario y contraseña", 400, campos=e.campos)
        except CredencialesInvalidasError:
            return respuesta_error(MENSAJE_GENERICO, 401)
        except CuentaBloqueadaError as e:
            return respuesta_error(
                "Cuenta bloqueada temporalmente por intentos fallidos. "
                f"Intente de nuevo en {e.minutos_restantes} minuto(s) o contacte al administrador.",
                423,
            )

        # Nueva sesión (evita fijación de sesión) con los datos del rol
        request.session.cycle_key()
        rotate_token(request)
        request.session["id_usuario"] = usuario.id_usuario
        request.session["id_rol"] = usuario.rol_id

        return JsonResponse({
            "usuario": usuario.nombre_usuario,
            "nombre_completo": usuario.nombre_completo,
            "rol": usuario.rol.nombre,
            "redirigir": "/menu/",
        })

    @staticmethod
    @require_POST
    def logout(request):
        """POST /api/auth/logout – RN-11: invalida la sesión en el servidor."""
        request.session.flush()
        return HttpResponse(status=204)
