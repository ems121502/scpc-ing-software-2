"""
Modelos de cuentas y acceso – Fase 2, sección 6 (diccionario de datos).
Tablas: ROL, FUNCIONALIDAD, ROL_FUNCIONALIDAD, USUARIO, BITACORA_ACCESO.
"""
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40, unique=True)
    descripcion = models.CharField(max_length=150, null=True, blank=True)
    funcionalidades = models.ManyToManyField(
        "Funcionalidad", through="RolFuncionalidad", related_name="roles"
    )

    class Meta:
        db_table = "rol"
        ordering = ["id_rol"]

    def __str__(self):
        return self.nombre


class Funcionalidad(models.Model):
    """Opción del menú principal (RN-08). `ruta` es la pantalla que protege."""

    id_funcionalidad = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=60)
    ruta = models.CharField(max_length=100)

    class Meta:
        db_table = "funcionalidad"
        ordering = ["id_funcionalidad"]

    def __str__(self):
        return self.nombre


class RolFuncionalidad(models.Model):
    """
    Asignación de funcionalidades a roles.
    Ajuste justificado respecto a la Fase 2: la PK compuesta (id_rol,
    id_funcionalidad) se implementa como PK simple autoincremental + UNIQUE
    sobre el par, porque el ORM de Django maneja relaciones muchos-a-muchos con
    PK de una sola columna. La regla de integridad (no repetir el par) se
    conserva con la restricción UNIQUE.
    """

    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column="id_rol")
    funcionalidad = models.ForeignKey(
        Funcionalidad, on_delete=models.CASCADE, db_column="id_funcionalidad"
    )

    class Meta:
        db_table = "rol_funcionalidad"
        constraints = [
            models.UniqueConstraint(
                fields=["rol", "funcionalidad"], name="uq_rol_funcionalidad"
            )
        ]


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=30, unique=True)
    contrasena_hash = models.CharField(max_length=255)  # RN-02: hash bcrypt
    nombre_completo = models.CharField(max_length=100)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, db_column="id_rol")
    activo = models.BooleanField(default=True)
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "usuario"
        constraints = [
            models.CheckConstraint(
                condition=Q(intentos_fallidos__gte=0),
                name="ck_usuario_intentos_no_negativos",
            )
        ]

    def __str__(self):
        return f"{self.nombre_usuario} ({self.rol})"

    def esta_bloqueado(self, ahora=None):
        ahora = ahora or timezone.now()
        return self.bloqueado_hasta is not None and self.bloqueado_hasta > ahora


class BitacoraAcceso(models.Model):
    """RN-07 / DD-09: registro de todos los intentos de inicio de sesión."""

    EXITOSO = "EXITOSO"
    FALLIDO = "FALLIDO"
    BLOQUEADO = "BLOQUEADO"
    RESULTADOS = [(EXITOSO, "Exitoso"), (FALLIDO, "Fallido"), (BLOQUEADO, "Bloqueado")]

    id_bitacora = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, db_column="id_usuario"
    )
    usuario_ingresado = models.CharField(max_length=30)
    fecha_hora = models.DateTimeField(default=timezone.now)
    resultado = models.CharField(max_length=10, choices=RESULTADOS)

    class Meta:
        db_table = "bitacora_acceso"
        ordering = ["-fecha_hora"]
        constraints = [
            models.CheckConstraint(
                condition=Q(resultado__in=["EXITOSO", "FALLIDO", "BLOQUEADO"]),
                name="ck_bitacora_resultado",
            )
        ]
