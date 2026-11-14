"""
Configuración del SCPC – Sistema de Control de Productos Centralizado.

Los valores sensibles se leen de variables de entorno para no subirlos a Git.
Los valores por defecto coinciden con el script bd/crear_bd.sql.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "SCPC_SECRET_KEY", "solo-desarrollo-cambiar-esta-clave-en-produccion"
)
DEBUG = os.environ.get("SCPC_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("SCPC_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Módulos del SCPC
    "cuentas",       # CU-01 Inicio de Sesión (usuarios, roles, bitácora, middleware)
    "menu",          # CU-02 Seleccionar Tarea
    "catalogo",      # Catálogo de productos (usado por CU-03)
    "solicitudes",   # CU-03 Registro de Compra
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # AuthMiddleware (Fase 2): sesión válida + permiso del rol en cada petición
    "cuentas.middleware.AuthMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Base de datos (ajuste A-07): SQLite por defecto para la implementación de la
# Fase 3; viene incluido con Python y no requiere instalar un servidor.
# Con DB_ENGINE=mysql se usa MySQL 8, la base prevista en la Fase 2 para producción.
# El código no cambia: el ORM de Django genera el SQL para cualquiera de las dos.
# ---------------------------------------------------------------------------
if os.environ.get("DB_ENGINE", "sqlite").lower() == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "scpc.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "scpc"),
            "USER": os.environ.get("DB_USER", "scpc_app"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "scpc_2026"),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# RN-02: contraseñas con hash bcrypt (nunca en texto plano).
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# RN-06: la sesión expira tras 30 minutos de inactividad.
SESSION_COOKIE_AGE = 30 * 60
SESSION_SAVE_EVERY_REQUEST = True       # cada petición reinicia el contador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
# En producción (HTTPS) poner SCPC_HTTPS=1 para cookies solo por HTTPS.
SESSION_COOKIE_SECURE = os.environ.get("SCPC_HTTPS", "0") == "1"
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# RN-04: bloqueo temporal tras intentos fallidos.
SCPC_INTENTOS_MAXIMOS = 5
SCPC_MINUTOS_BLOQUEO = 15

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Panama"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
