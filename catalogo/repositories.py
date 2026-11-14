"""ProductoRepository: acceso al catálogo de productos (Fase 2)."""
from django.db.models import Q

from .models import Producto

LIMITE_BUSQUEDA = 20  # RNF-06: resultados limitados para no cargar todo el catálogo


class ProductoRepository:
    def buscar_activos(self, texto, limite=LIMITE_BUSQUEDA):
        consulta = Producto.objects.filter(activo=True)
        texto = (texto or "").strip()
        if texto:
            consulta = consulta.filter(Q(codigo__icontains=texto) | Q(nombre__icontains=texto))
        return list(consulta.order_by("codigo")[:limite])

    def obtener_activos_por_codigos(self, codigos):
        """Devuelve {codigo: Producto} solo con los productos existentes y activos (RN-15)."""
        productos = Producto.objects.filter(codigo__in=list(codigos), activo=True)
        return {p.codigo: p for p in productos}
