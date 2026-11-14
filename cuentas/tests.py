"""
Pruebas automáticas de CU-01 y CU-02 (verificación técnica de la Fase 3).
Ejecutar:  python manage.py test
"""
import json

from django.core.management import call_command
from django.test import TestCase

from cuentas.models import BitacoraAcceso, Usuario

CLAVE = "Clinica2026*"


def login(cliente, usuario, contrasena):
    return cliente.post("/api/auth/login", data=json.dumps(
        {"usuario": usuario, "contrasena": contrasena}), content_type="application/json")


class InicioSesionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_datos_demo", verbosity=0)

    def test_login_correcto_crea_sesion_y_registra_bitacora(self):
        r = login(self.client, "salud1", CLAVE)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["rol"], "Personal de Salud")
        self.assertIn("id_usuario", self.client.session)
        self.assertTrue(BitacoraAcceso.objects.filter(
            usuario_ingresado="salud1", resultado="EXITOSO").exists())

    def test_campos_vacios_responde_400(self):  # RN-01
        self.assertEqual(login(self.client, "", "").status_code, 400)

    def test_contrasena_incorrecta_mensaje_generico(self):  # RN-05
        r = login(self.client, "salud1", "mala")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"], "Usuario o contraseña incorrectos")

    def test_usuario_inexistente_mismo_mensaje(self):  # RN-05
        r = login(self.client, "noexiste", "x")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"], "Usuario o contraseña incorrectos")

    def test_usuario_inactivo_no_ingresa(self):  # RN-03
        self.assertEqual(login(self.client, "inactivo1", CLAVE).status_code, 401)

    def test_contrasena_guardada_como_hash(self):  # RN-02
        hash_guardado = Usuario.objects.get(nombre_usuario="salud1").contrasena_hash
        self.assertNotEqual(hash_guardado, CLAVE)
        self.assertTrue(hash_guardado.startswith("bcrypt"))

    def test_bloqueo_tras_5_intentos(self):  # RN-04
        for _ in range(4):
            self.assertEqual(login(self.client, "salud2", "mala").status_code, 401)
        self.assertEqual(login(self.client, "salud2", "mala").status_code, 423)
        # Bloqueada: ni siquiera con la contraseña correcta
        self.assertEqual(login(self.client, "salud2", CLAVE).status_code, 423)

    def test_ingreso_correcto_reinicia_contador(self):  # RN-04
        login(self.client, "salud1", "mala")
        login(self.client, "salud1", CLAVE)
        self.assertEqual(Usuario.objects.get(nombre_usuario="salud1").intentos_fallidos, 0)


class SeleccionarTareaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("cargar_datos_demo", verbosity=0)

    def codigos_menu(self):
        return [o["codigo"] for o in self.client.get("/api/menu").json()["opciones"]]

    def test_sin_sesion_api_responde_401(self):
        self.assertEqual(self.client.get("/api/menu").status_code, 401)

    def test_sin_sesion_pantalla_redirige_a_login(self):
        r = self.client.get("/menu/")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("/login/"))

    def test_menu_personal_salud(self):  # RN-08
        login(self.client, "salud1", CLAVE)
        codigos = self.codigos_menu()
        self.assertIn("ORDENES_COMPRA", codigos)
        self.assertNotIn("GESTIONAR_REQUISICIONES", codigos)

    def test_menu_planificador_no_tiene_ordenes(self):  # RN-08
        login(self.client, "planificador1", CLAVE)
        codigos = self.codigos_menu()
        self.assertIn("GESTIONAR_REQUISICIONES", codigos)
        self.assertNotIn("ORDENES_COMPRA", codigos)

    def test_ruta_no_permitida_escrita_a_mano(self):  # RN-09 / RN-10
        login(self.client, "planificador1", CLAVE)
        r = self.client.get("/solicitudes/")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "/menu/")
        self.assertEqual(self.client.get("/api/solicitudes").status_code, 403)

    def test_logout_invalida_sesion(self):  # RN-11
        login(self.client, "salud1", CLAVE)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.assertEqual(self.client.get("/api/menu").status_code, 401)
