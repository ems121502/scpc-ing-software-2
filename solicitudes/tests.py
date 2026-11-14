"""
Pruebas automáticas del CU-03 Registro de Compra (verificación técnica de la Fase 3).
Ejecutar:  python manage.py test
"""
import json
from unittest import mock

from django.core.management import call_command
from django.db import DatabaseError
from django.test import TestCase

from solicitudes.models import DetalleSolicitud, SolicitudCompra

CLAVE = "Clinica2026*"


class RegistroCompraTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_datos_demo", verbosity=0)

    def setUp(self):
        self.client.post("/api/auth/login", data=json.dumps(
            {"usuario": "salud1", "contrasena": CLAVE}), content_type="application/json")

    def guardar(self, lineas):
        return self.client.post("/api/solicitudes", data=json.dumps({"lineas": lineas}),
                                content_type="application/json")

    def test_cabecera_automatica(self):  # RN-13
        datos = self.client.get("/api/solicitudes/nueva").json()
        self.assertRegex(datos["numero_provisional"], r"^S-\d{7}$")
        self.assertEqual(datos["solicitante"], "Ana Rodríguez")

    def test_registro_correcto_queda_pendiente(self):  # flujo básico, RN-19
        r = self.guardar([
            {"codigo": "P-0002", "cantidad": 3, "prioridad": "MEDIA", "observacion": ""},
            {"codigo": "p-0003", "cantidad": "2", "prioridad": "ALTA", "observacion": "Urgencias"},
        ])
        self.assertEqual(r.status_code, 201)
        solicitud = SolicitudCompra.objects.get(numero=r.json()["numero"])
        self.assertEqual(solicitud.estado, "PENDIENTE")
        self.assertEqual(solicitud.detalles.count(), 2)

    def test_sin_lineas(self):  # RN-14
        r = self.guardar([])
        self.assertEqual(r.status_code, 400)

    def test_campo_vacio(self):  # flujo de excepción "Campo en blanco"
        r = self.guardar([{"codigo": "P-0002", "cantidad": "", "prioridad": "", "observacion": ""}])
        self.assertEqual(r.status_code, 400)
        errores = r.json()["errores"]
        self.assertIn("Algunos de los campos no han sido llenados", errores["general"])
        self.assertIn("cantidad", errores["lineas"]["0"])
        self.assertIn("prioridad", errores["lineas"]["0"])

    def test_producto_inactivo(self):  # RN-15
        r = self.guardar([{"codigo": "P-0015", "cantidad": 1, "prioridad": "BAJA", "observacion": ""}])
        self.assertEqual(r.json()["errores"]["lineas"]["0"]["codigo"], "El producto no existe o está inactivo")

    def test_producto_repetido(self):  # RN-16
        r = self.guardar([
            {"codigo": "P-0002", "cantidad": 1, "prioridad": "BAJA", "observacion": ""},
            {"codigo": "P-0002", "cantidad": 2, "prioridad": "BAJA", "observacion": ""},
        ])
        self.assertEqual(r.json()["errores"]["lineas"]["1"]["codigo"], "El producto ya fue agregado")

    def test_prioridad_alta_sin_observacion(self):  # RN-17
        r = self.guardar([{"codigo": "P-0002", "cantidad": 1, "prioridad": "ALTA", "observacion": ""}])
        self.assertEqual(r.json()["errores"]["lineas"]["0"]["observacion"], "Justifique la prioridad Alta")

    def test_cantidad_fuera_de_rango(self):
        for cantidad in (0, 10000, "2.5", -1):
            r = self.guardar([{"codigo": "P-0002", "cantidad": cantidad, "prioridad": "BAJA", "observacion": ""}])
            self.assertEqual(r.status_code, 400, cantidad)

    def test_error_bd_no_guarda_nada(self):  # RN-18: todo o nada
        antes = SolicitudCompra.objects.count()
        with mock.patch("solicitudes.repositories.SolicitudRepository.crear_detalles",
                        side_effect=DatabaseError("falla simulada")):
            r = self.guardar([{"codigo": "P-0002", "cantidad": 1, "prioridad": "BAJA", "observacion": ""}])
        self.assertEqual(r.status_code, 500)
        self.assertEqual(SolicitudCompra.objects.count(), antes)

    def test_eliminar_ultima_linea_cancela(self):  # RN-19
        numero = self.guardar([{"codigo": "P-0004", "cantidad": 1, "prioridad": "BAJA", "observacion": ""}]).json()["numero"]
        solicitud = SolicitudCompra.objects.get(numero=numero)
        detalle = solicitud.detalles.first()
        r = self.client.delete(f"/api/solicitudes/{solicitud.id_solicitud}/detalles/{detalle.id_detalle}")
        self.assertEqual(r.status_code, 204)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "CANCELADA")

    def test_no_eliminar_si_no_esta_pendiente(self):  # RN-19 → 409
        solicitud = SolicitudCompra.objects.get(usuario__nombre_usuario="salud1", estado="EN_GESTION")
        detalle = solicitud.detalles.first()
        r = self.client.delete(f"/api/solicitudes/{solicitud.id_solicitud}/detalles/{detalle.id_detalle}")
        self.assertEqual(r.status_code, 409)

    def test_no_eliminar_solicitud_ajena(self):  # RN-19 → 403
        solicitud = SolicitudCompra.objects.get(usuario__nombre_usuario="salud2")
        detalle = solicitud.detalles.first()
        r = self.client.delete(f"/api/solicitudes/{solicitud.id_solicitud}/detalles/{detalle.id_detalle}")
        self.assertEqual(r.status_code, 403)
        self.assertTrue(DetalleSolicitud.objects.filter(id_detalle=detalle.id_detalle).exists())

    def test_otro_rol_no_puede_registrar(self):  # RN-12
        self.client.post("/api/auth/logout")
        self.client.post("/api/auth/login", data=json.dumps(
            {"usuario": "inventario1", "contrasena": CLAVE}), content_type="application/json")
        r = self.guardar([{"codigo": "P-0002", "cantidad": 1, "prioridad": "BAJA", "observacion": ""}])
        self.assertEqual(r.status_code, 403)
