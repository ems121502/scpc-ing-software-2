"""
AutorizacionService – lógica de negocio del CU-02 Seleccionar Tarea.
RN-08: el menú se arma con ROL_FUNCIONALIDAD.
RN-09: el permiso se verifica en el servidor en cada petición.
"""
from cuentas.repositories import RolRepository

# Rutas de la API que pertenecen a una funcionalidad del menú.
# Las pantallas se resuelven con la columna FUNCIONALIDAD.ruta de la base de datos.
PERMISOS_API = {
    "/api/solicitudes": "ORDENES_COMPRA",
}


class AutorizacionService:
    def __init__(self, roles=None):
        self.roles = roles or RolRepository()

    def obtener_menu(self, id_rol):
        return [
            {"codigo": f.codigo, "nombre": f.nombre, "ruta": f.ruta}
            for f in self.roles.funcionalidades_de_rol(id_rol)
        ]

    def tiene_permiso(self, id_rol, codigo_funcionalidad):
        return self.roles.rol_tiene_funcionalidad(id_rol, codigo_funcionalidad)

    def funcionalidad_requerida(self, ruta):
        """
        Devuelve el código de la funcionalidad que protege la ruta, o None si la
        ruta solo requiere sesión (por ejemplo /menu/ o /api/productos).
        """
        for prefijo, codigo in PERMISOS_API.items():
            if ruta.startswith(prefijo):
                return codigo
        for funcionalidad in self.roles.todas_las_funcionalidades():
            if funcionalidad.ruta and ruta.startswith(funcionalidad.ruta):
                return funcionalidad.codigo
        return None
