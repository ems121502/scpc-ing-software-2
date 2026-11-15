"""
ValidadorSolicitud (Fase 2): validaciones definitivas del CU-03 en el servidor.
Son las mismas que hace la pantalla (DD-05), con los mensajes de la tabla
"Validaciones de los campos" de la Fase 2.
"""
from catalogo.repositories import ProductoRepository

from .models import DetalleSolicitud
# Mensajes de Retroalimentacion de datos faltantes
MSG_CAMPOS_VACIOS = "Algunos de los campos no han sido llenados"
MSG_SIN_LINEAS = "La solicitud debe tener al menos una línea de producto"
MSG_PRODUCTO_VACIO = "Seleccione un producto"
MSG_PRODUCTO_INVALIDO = "El producto no existe o está inactivo"
MSG_PRODUCTO_REPETIDO = "El producto ya fue agregado"
MSG_CANTIDAD = "Ingrese una cantidad válida"
MSG_PRIORIDAD = "Seleccione una prioridad"
MSG_OBSERVACION_ALTA = "Justifique la prioridad Alta"
MSG_OBSERVACION_LARGA = "La observación admite máximo 250 caracteres"

# Limites de valores funcionales en las entradas numericas 
CANTIDAD_MIN, CANTIDAD_MAX = 1, 9999
PRIORIDADES_VALIDAS = {DetalleSolicitud.ALTA, DetalleSolicitud.MEDIA, DetalleSolicitud.BAJA}


class ValidadorSolicitud:
    def __init__(self, productos=None):
        self.productos = productos or ProductoRepository()

    def validar(self, lineas):
        """
        Recibe la lista de líneas enviada por la pantalla.
        Devuelve (lineas_limpias, errores). `errores` es None si todo es válido, o
        {"general": [...], "lineas": {"0": {"campo": "mensaje"}}} si hay errores.
        """
        general, por_linea = [], {}

        # RN-14: al menos una línea
        if not isinstance(lineas, list) or len(lineas) == 0:
            return [], {"general": [MSG_SIN_LINEAS], "lineas": {}}

        codigos = [self._texto(l.get("codigo")).upper() for l in lineas if isinstance(l, dict)]
        catalogo = self.productos.obtener_activos_por_codigos(c for c in codigos if c)

        limpias, vistos, hay_vacios = [], set(), False
        for indice, linea in enumerate(lineas):
            errores = {}
            if not isinstance(linea, dict):
                linea = {}

            # Código de producto: obligatorio, existente y activo (RN-15), no repetido (RN-16)
            codigo = self._texto(linea.get("codigo")).upper()
            producto = None
            if not codigo:
                errores["codigo"] = MSG_PRODUCTO_VACIO
                hay_vacios = True
            elif codigo not in catalogo:
                errores["codigo"] = MSG_PRODUCTO_INVALIDO
            elif codigo in vistos:
                errores["codigo"] = MSG_PRODUCTO_REPETIDO
            else:
                producto = catalogo[codigo]
                vistos.add(codigo)

            # Cantidad: entero entre 1 y 9999
            cantidad = self._entero(linea.get("cantidad"))
            if linea.get("cantidad") in (None, ""):
                errores["cantidad"] = MSG_CANTIDAD
                hay_vacios = True
            elif cantidad is None or not CANTIDAD_MIN <= cantidad <= CANTIDAD_MAX:
                errores["cantidad"] = MSG_CANTIDAD

            # Prioridad: Alta, Media o Baja
            prioridad = self._texto(linea.get("prioridad")).upper()
            if not prioridad:
                errores["prioridad"] = MSG_PRIORIDAD
                hay_vacios = True
            elif prioridad not in PRIORIDADES_VALIDAS:
                errores["prioridad"] = MSG_PRIORIDAD

            # Observación: máx. 250; obligatoria si la prioridad es Alta (RN-17)
            observacion = self._texto(linea.get("observacion"))
            if len(observacion) > 250:
                errores["observacion"] = MSG_OBSERVACION_LARGA
            elif prioridad == DetalleSolicitud.ALTA and not observacion:
                errores["observacion"] = MSG_OBSERVACION_ALTA

            if errores:
                por_linea[str(indice)] = errores
            else:
                limpias.append({
                    "producto": producto,
                    "cantidad": cantidad,
                    "prioridad": prioridad,
                    "observacion": observacion,
                })
        # Control de campos vacios
        if hay_vacios:
            general.append(MSG_CAMPOS_VACIOS)
        if general or por_linea:
            return [], {"general": general, "lineas": por_linea}
        return limpias, None

    @staticmethod
    def _texto(valor):
        return valor.strip() if isinstance(valor, str) else ""

    @staticmethod
    def _entero(valor):
        """Acepta 5 o "5"; rechaza decimales, booleanos y texto."""
        if isinstance(valor, bool):
            return None
        if isinstance(valor, int):
            return valor
        if isinstance(valor, str) and valor.strip().isdigit():
            return int(valor.strip())
        return None
