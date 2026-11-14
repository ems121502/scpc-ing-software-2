"""
Catálogo de productos – Fase 2, sección 6. Tablas: TIPO_PRODUCTO, PRODUCTO.
Lo usa el CU-03 y lo reutilizarán los módulos de inventario y reportes.
"""
from django.db import models
from django.db.models import Q


class TipoProducto(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = "tipo_producto"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=10, unique=True)  # formato P-0000
    nombre = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoProducto, on_delete=models.PROTECT, db_column="id_tipo")
    unidad_medida = models.CharField(max_length=20)
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "producto"
        ordering = ["codigo"]
        # RNF-06: índice para la búsqueda por nombre (el código ya es UNIQUE)
        indexes = [models.Index(fields=["nombre"], name="ix_producto_nombre")]
        constraints = [
            models.CheckConstraint(
                condition=Q(stock_actual__gte=0), name="ck_producto_stock_actual"
            ),
            models.CheckConstraint(
                condition=Q(stock_minimo__gte=0), name="ck_producto_stock_minimo"
            ),
        ]

    def __str__(self):
        return f"{self.codigo} – {self.nombre}"
