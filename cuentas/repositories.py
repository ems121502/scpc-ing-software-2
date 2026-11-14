"""
Capa de persistencia de cuentas: UsuarioRepository, BitacoraRepository y
RolRepository (Fase 2, diagrama de clases de diseño).
Solo estas clases consultan las tablas de usuarios, roles y bitácora.
"""
from .models import BitacoraAcceso, Funcionalidad, RolFuncionalidad, Usuario


class UsuarioRepository:
    def buscar_por_nombre_usuario(self, nombre_usuario):
        return (
            Usuario.objects.select_related("rol")
            .filter(nombre_usuario=nombre_usuario)
            .first()
        )

    def obtener_por_id(self, id_usuario):
        return Usuario.objects.select_related("rol").filter(id_usuario=id_usuario).first()

    def actualizar_control_acceso(self, usuario):
        """Guarda solo los campos del control de intentos y bloqueo (RN-04)."""
        usuario.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])


class BitacoraRepository:
    def registrar(self, usuario, usuario_ingresado, resultado):
        return BitacoraAcceso.objects.create(
            usuario=usuario,
            usuario_ingresado=(usuario_ingresado or "")[:30],
            resultado=resultado,
        )


class RolRepository:
    def funcionalidades_de_rol(self, id_rol):
        return Funcionalidad.objects.filter(
            rolfuncionalidad__rol=id_rol
        ).order_by("id_funcionalidad")

    def rol_tiene_funcionalidad(self, id_rol, codigo_funcionalidad):
        return RolFuncionalidad.objects.filter(
            rol_id=id_rol, funcionalidad__codigo=codigo_funcionalidad
        ).exists()

    def todas_las_funcionalidades(self):
        return Funcionalidad.objects.all()
