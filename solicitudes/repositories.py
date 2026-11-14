"""SolicitudRepository: acceso a SOLICITUD_COMPRA y DETALLE_SOLICITUD (Fase 2)."""
import secrets

from django.db.models import Max

from .models import DetalleSolicitud, SolicitudCompra


def formatear_numero(id_solicitud):
    """RN-13: número con formato S-0000000."""
    return f"S-{id_solicitud:07d}"


class SolicitudRepository:
    def siguiente_numero_provisional(self):
        """DD-08: número que se muestra al abrir la pantalla (puede cambiar al guardar)."""
        ultimo = SolicitudCompra.objects.aggregate(maximo=Max("id_solicitud"))["maximo"] or 0
        return formatear_numero(ultimo + 1)

    def crear_cabecera(self, usuario, fecha):
        """
        Crea la cabecera en estado PENDIENTE (RN-19) y le asigna el número
        definitivo a partir de su id (RN-13, DD-08). Debe llamarse dentro de
        una transacción (la abre SolicitudService).
        """
        temporal = "T" + secrets.token_hex(4)  # único y de 9 caracteres
        solicitud = SolicitudCompra.objects.create(
            numero=temporal, fecha_solicitud=fecha, usuario=usuario,
            estado=SolicitudCompra.PENDIENTE,
        )
        solicitud.numero = formatear_numero(solicitud.id_solicitud)
        solicitud.save(update_fields=["numero"])
        return solicitud

    def crear_detalles(self, solicitud, lineas):
        DetalleSolicitud.objects.bulk_create([
            DetalleSolicitud(
                solicitud=solicitud,
                producto=linea["producto"],
                cantidad=linea["cantidad"],
                prioridad=linea["prioridad"],
                observacion=linea["observacion"] or None,
            )
            for linea in lineas
        ])

    def listar_por_usuario(self, id_usuario):
        return (
            SolicitudCompra.objects.filter(usuario_id=id_usuario)
            .prefetch_related("detalles__producto")
            .order_by("-id_solicitud")
        )

    def obtener_para_actualizar(self, id_solicitud):
        """Bloquea la fila mientras dura la transacción (evita cambios simultáneos)."""
        return (
            SolicitudCompra.objects.select_for_update()
            .filter(id_solicitud=id_solicitud)
            .first()
        )

    def obtener_detalle(self, id_solicitud, id_detalle):
        return DetalleSolicitud.objects.filter(
            id_detalle=id_detalle, solicitud_id=id_solicitud
        ).first()

    def eliminar_detalle(self, detalle):
        detalle.delete()

    def contar_detalles(self, id_solicitud):
        return DetalleSolicitud.objects.filter(solicitud_id=id_solicitud).count()

    def actualizar_estado(self, solicitud, estado):
        solicitud.estado = estado
        solicitud.save(update_fields=["estado"])
