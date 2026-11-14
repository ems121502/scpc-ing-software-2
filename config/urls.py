"""
Rutas del SCPC.

- Rutas con barra final (/login/, /menu/, /solicitudes/): pantallas HTML.
- Rutas /api/...: API REST en JSON definida en la Fase 2, sección 7.2.
"""
from django.urls import path

from catalogo.views import ProductoController
from cuentas.views import AuthController
from menu.views import MenuController
from solicitudes.views import SolicitudController

urlpatterns = [
    path("", AuthController.inicio, name="inicio"),

    # CU-01 Inicio de Sesión
    path("login/", AuthController.pantalla_login, name="login"),
    path("api/auth/login", AuthController.login, name="api_login"),
    path("api/auth/logout", AuthController.logout, name="api_logout"),

    # CU-02 Seleccionar Tarea
    path("menu/", MenuController.pantalla_menu, name="menu"),
    path("api/menu", MenuController.api_menu, name="api_menu"),

    # Opciones del menú fuera del alcance de la Fase 3 (protegidas por rol)
    path("requisiciones/", MenuController.modulo_no_implementado,
         {"titulo": "Gestionar requisiciones"}),
    path("productos/", MenuController.modulo_no_implementado,
         {"titulo": "Productos (registro de entradas)"}),
    path("inventario/", MenuController.modulo_no_implementado,
         {"titulo": "Inventario (consulta)"}),
    path("reportes/", MenuController.modulo_no_implementado,
         {"titulo": "Reportes de uso mensual"}),
    path("configuracion/", MenuController.modulo_no_implementado,
         {"titulo": "Configuración (cambio de contraseña)"}),

    # Catálogo (búsqueda de productos para CU-03)
    path("api/productos", ProductoController.buscar, name="api_productos"),

    # CU-03 Registro de Compra
    path("solicitudes/", SolicitudController.pantalla, name="solicitudes"),
    path("api/solicitudes/nueva", SolicitudController.nueva, name="api_solicitud_nueva"),
    path("api/solicitudes", SolicitudController.coleccion, name="api_solicitudes"),
    path(
        "api/solicitudes/<int:id_solicitud>/detalles/<int:id_detalle>",
        SolicitudController.eliminar_detalle,
        name="api_eliminar_detalle",
    ),
]
