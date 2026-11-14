"""
Carga los datos de demostración del SCPC:
roles, funcionalidades del menú (matriz de la Fase 2), usuarios de prueba,
tipos de producto, catálogo de productos y dos solicitudes de ejemplo.

Uso:  python manage.py cargar_datos_demo
Se puede ejecutar varias veces: actualiza los datos y desbloquea a los usuarios.
"""
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalogo.models import Producto, TipoProducto
from cuentas.models import Funcionalidad, Rol, RolFuncionalidad, Usuario
from solicitudes.models import DetalleSolicitud, SolicitudCompra
from solicitudes.repositories import formatear_numero

CONTRASENA_DEMO = "Clinica2026*"

SALUD = "Personal de Salud"
SERVICIOS = "Servicios Hospitalarios"
INVENTARISTA = "Inventarista"
PLANIFICADOR = "Planificador"

ROLES = {
    SALUD: "Registra solicitudes de compra de productos médicos.",
    SERVICIOS: "Consulta inventario y reportes de uso mensual.",
    INVENTARISTA: "Registra entradas de productos al inventario.",
    PLANIFICADOR: "Gestiona las requisiciones de compra.",
}

# (código, texto del menú, ruta, roles con acceso) – matriz de funcionalidades por rol, Fase 2
FUNCIONALIDADES = [
    ("ORDENES_COMPRA", "Órdenes de compra", "/solicitudes/", [SALUD]),
    ("GESTIONAR_REQUISICIONES", "Gestionar requisiciones", "/requisiciones/", [PLANIFICADOR]),
    ("PRODUCTOS", "Productos", "/productos/", [INVENTARISTA]),
    ("INVENTARIO", "Inventario", "/inventario/", [SALUD, SERVICIOS, INVENTARISTA, PLANIFICADOR]),
    ("REPORTES", "Reportes de uso mensual", "/reportes/", [SERVICIOS]),
    ("CONFIGURACION", "Configuración", "/configuracion/", [SALUD, SERVICIOS, INVENTARISTA, PLANIFICADOR]),
    ("FINALIZAR_SESION", "Finalizar sesión", "/logout/", [SALUD, SERVICIOS, INVENTARISTA, PLANIFICADOR]),
]

# (usuario, nombre completo, rol, activo)
USUARIOS = [
    ("salud1", "Ana Rodríguez", SALUD, True),
    ("salud2", "Carlos Méndez", SALUD, True),
    ("servicios1", "Luis Herrera", SERVICIOS, True),
    ("inventario1", "Rosa Castillo", INVENTARISTA, True),
    ("planificador1", "Jorge Batista", PLANIFICADOR, True),
    ("inactivo1", "Pedro Sánchez", SALUD, False),  # para probar RN-03
]

TIPOS = ["Medicamento", "Material", "Equipo"]

# (código, nombre, tipo, unidad, stock actual, stock mínimo, activo)
PRODUCTOS = [
    ("P-0001", "Paracetamol 500 mg", "Medicamento", "caja", 40, 10, True),
    ("P-0002", "Amoxicilina 500 mg", "Medicamento", "caja", 25, 10, True),
    ("P-0003", "Ibuprofeno 400 mg", "Medicamento", "caja", 30, 10, True),
    ("P-0004", "Omeprazol 20 mg", "Medicamento", "caja", 18, 8, True),
    ("P-0005", "Solución salina 0.9% 500 ml", "Medicamento", "frasco", 60, 20, True),
    ("P-0006", "Guantes de nitrilo talla M", "Material", "caja", 15, 10, True),
    ("P-0007", "Jeringas desechables 5 ml", "Material", "caja", 22, 10, True),
    ("P-0008", "Gasas estériles 10x10 cm", "Material", "paquete", 50, 15, True),
    ("P-0009", "Mascarillas quirúrgicas", "Material", "caja", 12, 10, True),
    ("P-0010", "Alcohol isopropílico 70%", "Material", "frasco", 35, 10, True),
    ("P-0011", "Catéter intravenoso 20G", "Material", "caja", 8, 5, True),
    ("P-0012", "Termómetro digital", "Equipo", "unidad", 6, 3, True),
    ("P-0013", "Tensiómetro digital de brazo", "Equipo", "unidad", 4, 2, True),
    ("P-0014", "Oxímetro de pulso", "Equipo", "unidad", 5, 2, True),
    ("P-0015", "Ranitidina 150 mg (descontinuado)", "Medicamento", "caja", 0, 0, False),  # RN-15
]


class Command(BaseCommand):
    help = "Carga roles, menú, usuarios, catálogo y solicitudes de demostración del SCPC."

    @transaction.atomic
    def handle(self, *args, **opciones):
        roles = {
            nombre: Rol.objects.update_or_create(nombre=nombre, defaults={"descripcion": desc})[0]
            for nombre, desc in ROLES.items()
        }

        for codigo, nombre, ruta, roles_con_acceso in FUNCIONALIDADES:
            funcionalidad, _ = Funcionalidad.objects.update_or_create(
                codigo=codigo, defaults={"nombre": nombre, "ruta": ruta}
            )
            RolFuncionalidad.objects.filter(funcionalidad=funcionalidad).exclude(
                rol__nombre__in=roles_con_acceso
            ).delete()
            for nombre_rol in roles_con_acceso:
                RolFuncionalidad.objects.get_or_create(rol=roles[nombre_rol], funcionalidad=funcionalidad)

        hash_demo = make_password(CONTRASENA_DEMO)  # RN-02: se guarda solo el hash
        usuarios = {}
        for nombre_usuario, nombre_completo, rol, activo in USUARIOS:
            usuarios[nombre_usuario], _ = Usuario.objects.update_or_create(
                nombre_usuario=nombre_usuario,
                defaults={
                    "contrasena_hash": hash_demo,
                    "nombre_completo": nombre_completo,
                    "rol": roles[rol],
                    "activo": activo,
                    "intentos_fallidos": 0,
                    "bloqueado_hasta": None,
                },
            )

        tipos = {nombre: TipoProducto.objects.get_or_create(nombre=nombre)[0] for nombre in TIPOS}
        productos = {}
        for codigo, nombre, tipo, unidad, stock, minimo, activo in PRODUCTOS:
            productos[codigo], _ = Producto.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre, "tipo": tipos[tipo], "unidad_medida": unidad,
                    "stock_actual": stock, "stock_minimo": minimo, "activo": activo,
                },
            )

        # Solicitudes de ejemplo (solo la primera vez)
        if not SolicitudCompra.objects.exists():
            # salud1: solicitud ya En gestión → sus líneas NO se pueden eliminar (RN-19, 409)
            self._crear_solicitud(usuarios["salud1"], SolicitudCompra.EN_GESTION, [
                (productos["P-0006"], 10, DetalleSolicitud.MEDIA, ""),
                (productos["P-0009"], 5, DetalleSolicitud.ALTA, "Stock por debajo del mínimo"),
            ])
            # salud2: solicitud Pendiente de otro usuario (salud1 no puede modificarla, 403)
            self._crear_solicitud(usuarios["salud2"], SolicitudCompra.PENDIENTE, [
                (productos["P-0001"], 4, DetalleSolicitud.BAJA, ""),
            ])

        self.stdout.write(self.style.SUCCESS(
            "Datos de demostración cargados. Contraseña de todos los usuarios: " + CONTRASENA_DEMO
        ))
        for nombre_usuario, nombre_completo, rol, activo in USUARIOS:
            estado = "" if activo else "  (INACTIVO)"
            self.stdout.write(f"  {nombre_usuario:<14} {rol}{estado}")

    @staticmethod
    def _crear_solicitud(usuario, estado, lineas):
        solicitud = SolicitudCompra.objects.create(
            numero="TEMPORAL", fecha_solicitud=timezone.localdate(), usuario=usuario, estado=estado
        )
        solicitud.numero = formatear_numero(solicitud.id_solicitud)
        solicitud.save(update_fields=["numero"])
        for producto, cantidad, prioridad, observacion in lineas:
            DetalleSolicitud.objects.create(
                solicitud=solicitud, producto=producto, cantidad=cantidad,
                prioridad=prioridad, observacion=observacion or None,
            )
