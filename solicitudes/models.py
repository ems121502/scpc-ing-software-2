"""
Solicitudes de compra – Fase 2, sección 6.
Tablas: SOLICITUD_COMPRA (cabecera) y DETALLE_SOLICITUD (líneas).
"""
from django.db import models
from django.db.models import Q


class SolicitudCompra(models.Model):
    PENDIENTE = "PENDIENTE"
    EN_GESTION = "EN_GESTION"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"
    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (EN_GESTION, "En gestión"),
        (COMPLETADA, "Completada"),
        (CANCELADA, "Cancelada"),
    ]

    id_solicitud = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=10, unique=True)  # formato S-0000000 (RN-13)
    fecha_solicitud = models.DateField()
    usuario = models.ForeignKey(
        "cuentas.Usuario", on_delete=models.PROTECT, db_column="id_usuario",
        related_name="solicitudes",
    )
    estado = models.CharField(max_length=12, choices=ESTADOS, default=PENDIENTE)

    class Meta:
        db_table = "solicitud_compra"
        ordering = ["-id_solicitud"]
        constraints = [
            models.CheckConstraint(
                condition=Q(estado__in=["PENDIENTE", "EN_GESTION", "COMPLETADA", "CANCELADA"]),
                name="ck_solicitud_estado",
            )
        ]

    def __str__(self):
        return self.numero


class DetalleSolicitud(models.Model):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    PRIORIDADES = [(ALTA, "Alta"), (MEDIA, "Media"), (BAJA, "Baja")]

    id_detalle = models.AutoField(primary_key=True)
    solicitud = models.ForeignKey(
        SolicitudCompra, on_delete=models.CASCADE, db_column="id_solicitud",
        related_name="detalles",
    )
    producto = models.ForeignKey(
        "catalogo.Producto", on_delete=models.PROTECT, db_column="id_producto"
    )
    cantidad = models.IntegerField()
    prioridad = models.CharField(max_length=5, choices=PRIORIDADES)
    # Obligatoria si la prioridad es ALTA: se valida en ValidadorSolicitud (RN-17)
    observacion = models.CharField(max_length=250, null=True, blank=True)

    class Meta:
        db_table = "detalle_solicitud"
        ordering = ["id_detalle"]
        constraints = [
            # RN-16 / DD-07: no repetir un producto en la misma solicitud
            models.UniqueConstraint(
                fields=["solicitud", "producto"], name="uq_detalle_solicitud_producto"
            ),
            models.CheckConstraint(
                condition=Q(cantidad__gte=1) & Q(cantidad__lte=9999),
                name="ck_detalle_cantidad",
            ),
            models.CheckConstraint(
                condition=Q(prioridad__in=["ALTA", "MEDIA", "BAJA"]),
                name="ck_detalle_prioridad",
            ),
        ]
