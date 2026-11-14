"""ProductoController – búsqueda de productos activos para la lista del CU-03."""
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .repositories import ProductoRepository


class ProductoController:
    @staticmethod
    @require_GET
    def buscar(request):
        """GET /api/productos?buscar=texto – solo productos activos (RN-15)."""
        productos = ProductoRepository().buscar_activos(request.GET.get("buscar", ""))
        return JsonResponse({
            "productos": [
                {"codigo": p.codigo, "nombre": p.nombre, "unidad": p.unidad_medida}
                for p in productos
            ]
        })
