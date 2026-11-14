# SCPC – Sistema de Control de Productos Centralizado (Clínica XYZ)

Proyecto semestral de Ingeniería de Software II – UTP, II semestre 2026.
**Fase 3: Implementación** de los tres casos de uso seleccionados:

| CU | Nombre | Actor |
|----|--------|-------|
| CU-01 | Inicio de Sesión | Todos los usuarios |
| CU-02 | Seleccionar Tarea | Todos los usuarios |
| CU-03 | Registro de Compra | Personal de Salud |

Tecnologías: Python 3.10+ · Django 5.2 · SQLite (MySQL 8 opcional) · HTML5/CSS3/JavaScript · bcrypt.

---

## 1. Guía de ejecución

### 1.1 Requisitos previos
- Python 3.10 o superior (`python --version`). Compatible con Python 3.14.
- Git
- No hace falta instalar un servidor de base de datos: SQLite viene incluido con Python.

### 1.2 Instalar
```bash
git clone <URL-del-repositorio>
cd scpc
python -m venv .venv
# Windows:      .venv\Scripts\activate
# Linux/macOS:  source .venv/bin/activate
pip install -r requirements.txt
```
En Windows, si PowerShell indica que la ejecución de scripts está deshabilitada:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 1.3 Crear la base de datos, las tablas y los datos de demostración
```bash
python manage.py makemigrations cuentas catalogo solicitudes
python manage.py migrate
python manage.py cargar_datos_demo
```
La base de datos queda en el archivo `scpc.sqlite3`, dentro de la carpeta del proyecto.
Se puede abrir con *DB Browser for SQLite* para ver las tablas.

### 1.4 Ejecutar
```bash
python manage.py runserver
```
Abrir **http://127.0.0.1:8000/**

### 1.5 (Opcional) Usar MySQL 8
```bash
mysql -u root -p < bd/crear_bd.sql
# PowerShell: $env:DB_ENGINE="mysql"     bash: export DB_ENGINE=mysql
python manage.py migrate
python manage.py cargar_datos_demo
```
Datos de conexión por defecto: base `scpc`, usuario `scpc_app` / `scpc_2026`
(variables `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).

### 1.6 Ejecutar las pruebas automáticas
```bash
python manage.py test
```

---

## 2. Datos de demostración

Contraseña de todos los usuarios: **`Clinica2026*`**

| Usuario | Nombre | Rol | Para demostrar |
|---------|--------|-----|----------------|
| `salud1` | Ana Rodríguez | Personal de Salud | CU-03 completo; tiene una solicitud *En gestión* (sus líneas no se pueden eliminar) |
| `salud2` | Carlos Méndez | Personal de Salud | Tiene una solicitud *Pendiente* que `salud1` no puede modificar |
| `servicios1` | Luis Herrera | Servicios Hospitalarios | Menú distinto (Reportes) |
| `inventario1` | Rosa Castillo | Inventarista | Menú distinto (Productos) |
| `planificador1` | Jorge Batista | Planificador | Menú sin “Órdenes de compra”; acceso restringido a `/solicitudes/` |
| `inactivo1` | Pedro Sánchez | Personal de Salud | Usuario inactivo: no puede ingresar (RN-03) |

Catálogo: 15 productos (`P-0001` a `P-0015`). **`P-0015` está inactivo** (sirve para probar RN-15).

Si un usuario queda bloqueado durante la demostración, `python manage.py cargar_datos_demo`
lo desbloquea.

---

## 3. Guion de demostración (evidencia funcional)

**CU-01 Inicio de Sesión**
1. Pulsar *Siguiente* con los campos vacíos → mensajes en rojo (RN-01).
2. `salud1` con una contraseña incorrecta → “Usuario o contraseña incorrectos”; el usuario escrito se conserva (RN-05).
3. `inactivo1` → el mismo mensaje genérico (RN-03).
4. Cinco intentos fallidos con `salud2` → cuenta bloqueada 15 minutos (RN-04).
5. `salud1` con la contraseña correcta → menú principal (flujo básico).

**CU-02 Seleccionar Tarea**
1. Comparar el menú de `salud1` con el de `planificador1` (RN-08).
2. Como `planificador1`, escribir a mano `http://127.0.0.1:8000/solicitudes/` → “Acceso restringido” y regreso al menú (RN-09, RN-10).
3. *Finalizar sesión* y luego intentar abrir `/menu/` → vuelve a la pantalla de inicio de sesión (RN-11).

**CU-03 Registro de Compra** (con `salud1`)
1. Abrir *Órdenes de compra*: número provisional, fecha y solicitante automáticos (RN-13).
2. Pulsar *Guardar* con la fila vacía → “Algunos de los campos no han sido llenados” (flujo de excepción).
3. Agregar `P-0015` → “El producto no existe o está inactivo” (RN-15).
4. Agregar el mismo producto dos veces → “El producto ya fue agregado” (RN-16).
5. Prioridad Alta sin observación → “Justifique la prioridad Alta” (RN-17).
6. Registrar dos líneas válidas → confirmación con el número definitivo y estado Pendiente (flujo básico, RN-19).
7. *Cancelar* con datos escritos → se descartan solo los datos no guardados (RN-20).
8. En *Mis solicitudes*, eliminar una línea de la solicitud Pendiente. Eliminar la última línea → la solicitud pasa a Cancelada (RN-19).
9. La solicitud *En gestión* no muestra el botón Eliminar. Por API responde 409 (RN-19).

---

## 4. Estructura del código (Controlador – Servicio – Repositorio)

```
scpc/
├── config/            settings.py (MySQL, sesión 30 min, bcrypt), urls.py (rutas y API)
├── comun/http.py      utilidades JSON compartidas
├── cuentas/           CU-01: models, repositories, services (AuthService),
│                      views (AuthController), middleware (AuthMiddleware), tests
├── menu/              CU-02: services (AutorizacionService), views (MenuController)
├── catalogo/          PRODUCTO / TIPO_PRODUCTO: models, repositories (ProductoRepository),
│                      views (ProductoController), management/commands/cargar_datos_demo.py
├── solicitudes/       CU-03: models, repositories (SolicitudRepository), validators
│                      (ValidadorSolicitud), services (SolicitudService), views (SolicitudController), tests
├── templates/         pantallas: cuentas/login.html, menu/menu.html, solicitudes/solicitud.html
├── static/js/         api.js, login.js, menu.js, solicitud.js (validación en el cliente)
├── static/css/        scpc.css
└── bd/crear_bd.sql    creación de la base de datos y del usuario de MySQL
```

| Capa (Fase 2) | Dónde está |
|---------------|-----------|
| Presentación | `templates/`, `static/` |
| Lógica: middleware | `cuentas/middleware.py` → `AuthMiddleware` |
| Lógica: controladores | `*/views.py` → `AuthController`, `MenuController`, `ProductoController`, `SolicitudController` |
| Lógica: servicios | `*/services.py` → `AuthService`, `AutorizacionService`, `SolicitudService`; `solicitudes/validators.py` → `ValidadorSolicitud` |
| Persistencia | `*/repositories.py` → `UsuarioRepository`, `BitacoraRepository`, `RolRepository`, `ProductoRepository`, `SolicitudRepository`; `*/models.py` |

Los controladores nunca consultan la base de datos directamente: llaman a los
servicios, y los servicios usan los repositorios.

---

## 5. Trazabilidad RF → CU → diseño → código

| RF | CU | Elemento de diseño (Fase 2) | Código (archivo · clase/función) |
|----|----|-----------------------------|----------------------------------|
| RF-10 | CU-01 | Vista Inicio de Sesión | `templates/cuentas/login.html`, `static/js/login.js` |
| RF-10 | CU-01 | AuthController | `cuentas/views.py · AuthController.login`, `.pantalla_login` |
| RF-10 | CU-01 | AuthService (RN-01 a RN-05, RN-07) | `cuentas/services.py · AuthService.autenticar` |
| RF-10 | CU-01 | UsuarioRepository, BitacoraRepository | `cuentas/repositories.py` |
| RF-10 | CU-01 | USUARIO, BITACORA_ACCESO | `cuentas/models.py · Usuario, BitacoraAcceso` |
| RF-10 | CU-01 | RN-06 sesión de 30 min | `config/settings.py · SESSION_COOKIE_AGE, SESSION_SAVE_EVERY_REQUEST` |
| RF-05 | CU-02 | Vista Menú Principal | `templates/base.html`, `templates/menu/menu.html`, `static/js/menu.js` |
| RF-05 | CU-02 | AuthMiddleware (RN-09, RN-10) | `cuentas/middleware.py · AuthMiddleware.__call__` |
| RF-05 | CU-02 | MenuController | `menu/views.py · MenuController.api_menu`, `.pantalla_menu` |
| RF-05 | CU-02 | AutorizacionService (RN-08) | `menu/services.py · AutorizacionService.obtener_menu`, `.tiene_permiso`, `.funcionalidad_requerida` |
| RF-05 | CU-02 | RolRepository | `cuentas/repositories.py · RolRepository` |
| RF-05 | CU-02 | ROL, FUNCIONALIDAD, ROL_FUNCIONALIDAD | `cuentas/models.py · Rol, Funcionalidad, RolFuncionalidad` |
| RF-05 | CU-02 | RN-11 Finalizar sesión | `cuentas/views.py · AuthController.logout`, `static/js/menu.js · cerrarSesion` |
| RF-06 | CU-03 | Vista Solicitud de Compra | `templates/solicitudes/solicitud.html`, `static/js/solicitud.js` |
| RF-06 | CU-03 | SolicitudController | `solicitudes/views.py · SolicitudController` (`nueva`, `coleccion`, `eliminar_detalle`) |
| RF-06 | CU-03 | SolicitudService (RN-12, RN-13, RN-18, RN-19) | `solicitudes/services.py · SolicitudService.registrar`, `.eliminar_detalle`, `.preparar_nueva` |
| RF-06 | CU-03 | SolicitudRepository | `solicitudes/repositories.py · SolicitudRepository` |
| RF-06 | CU-03 | SOLICITUD_COMPRA, DETALLE_SOLICITUD | `solicitudes/models.py · SolicitudCompra, DetalleSolicitud` |
| RF-09 | CU-03 | Validador de formularios (cliente) | `static/js/solicitud.js · validarCliente` |
| RF-09 | CU-03 | ValidadorSolicitud (RN-14 a RN-17) | `solicitudes/validators.py · ValidadorSolicitud.validar` |
| RF-09 | CU-03 | ProductoRepository | `catalogo/repositories.py · ProductoRepository`, `catalogo/views.py · ProductoController.buscar` |
| RF-09 | CU-03 | PRODUCTO, TIPO_PRODUCTO | `catalogo/models.py · Producto, TipoProducto` |
| RF-01 a RF-04, RF-07, RF-08 | — | Arquitectura general (módulos futuros) | **No implementados en esta fase.** Las opciones del menú existen y están protegidas por rol (`menu/views.py · MenuController.modulo_no_implementado`). |

### Reglas de negocio → código

| Regla | Código |
|-------|--------|
| RN-01 campos obligatorios | `static/js/login.js` (submit) + `AuthService.autenticar` |
| RN-02 hash bcrypt | `config/settings.py · PASSWORD_HASHERS`, `check_password` en `AuthService` |
| RN-03 usuario activo | `AuthService.autenticar` |
| RN-04 bloqueo 5 intentos / 15 min | `AuthService.autenticar`, `config/settings.py · SCPC_INTENTOS_MAXIMOS, SCPC_MINUTOS_BLOQUEO` |
| RN-05 mensaje genérico | `cuentas/views.py · MENSAJE_GENERICO` |
| RN-06 expiración 30 min | `config/settings.py` |
| RN-07 bitácora | `BitacoraRepository.registrar` (llamado en cada intento) |
| RN-08 menú por rol | `AutorizacionService.obtener_menu` |
| RN-09 verificación en servidor | `AuthMiddleware` |
| RN-10 “Acceso restringido” | `AuthMiddleware`, `static/js/api.js` |
| RN-11 finalizar sesión | `AuthController.logout` |
| RN-12 solo Personal de Salud | `AuthMiddleware` + `SolicitudService._verificar_rol` |
| RN-13 cabecera automática | `SolicitudService.preparar_nueva`, `SolicitudRepository.crear_cabecera` |
| RN-14 a RN-17 validaciones | `ValidadorSolicitud.validar` y `solicitud.js · validarCliente` |
| RN-16 sin duplicados (BD) | `DetalleSolicitud.Meta · uq_detalle_solicitud_producto` |
| RN-18 transacción | `SolicitudService.registrar` (`transaction.atomic`) |
| RN-19 estados / eliminar líneas | `SolicitudService.eliminar_detalle` |
| RN-20 cancelar | `solicitud.js · cancelar` |

---

## 6. Ajustes respecto al diseño de la Fase 2 (justificados)

| # | Diseño Fase 2 | Implementación | Justificación |
|---|---------------|----------------|---------------|
| A-01 | ROL_FUNCIONALIDAD con PK compuesta | PK autoincremental `id` + UNIQUE (`id_rol`, `id_funcionalidad`) | El ORM de Django maneja relaciones muchos-a-muchos con PK de una columna. La regla de no repetir el par se conserva con UNIQUE. |
| A-02 | Nombres de tabla en mayúsculas | Nombres en minúsculas (`usuario`, `solicitud_compra`, …) | MySQL en Windows convierte los nombres a minúsculas y en Linux distingue mayúsculas. En minúsculas funciona igual en las computadoras de todo el equipo. |
| A-03 | “Recuérdame” | Recuerda solo el nombre de usuario en el navegador | Mantener la sesión abierta contradice RN-06 (expira a los 30 min). Nunca se guarda la contraseña. |
| A-04 | Ruta de pantalla de solicitud | `/solicitudes/` muestra el formulario y “Mis solicitudes” | Permite eliminar líneas guardadas (RN-19) desde la misma pantalla. |
| A-05 | HTTPS | HTTP en el entorno local; `SCPC_HTTPS=1` activa cookies seguras | `runserver` no ofrece HTTPS. En producción se usaría detrás de un servidor con certificado. |
| A-06 | Usuario vacío en el login (RN-07) | Si el usuario o la contraseña están vacíos, el intento no se registra en la bitácora | Se rechaza antes de llegar a la autenticación; no hay intento real que auditar. |
| A-07 | Base de datos MySQL 8 | SQLite (incluido con Python); MySQL 8 sigue disponible con `DB_ENGINE=mysql` | Decisión del equipo para simplificar la instalación y la ejecución en todas las computadoras. SQLite aplica las mismas PK, FK, UNIQUE, CHECK y transacciones del modelo de datos, y el código no cambia porque el ORM abstrae el motor. Compromiso: SQLite no está pensado para muchos usuarios simultáneos; en producción se usaría MySQL 8. |

---

## 7. Uso de inteligencia artificial

Se utilizó un asistente de IA (Claude, de Anthropic) como apoyo. El equipo revisó, programó,
ejecutó y probó el código, y es responsable de explicar cada archivo, clase y función.
