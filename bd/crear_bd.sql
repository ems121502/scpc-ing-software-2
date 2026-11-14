-- SCPC – Script de creación de la base de datos y del usuario de la aplicación
-- OPCIONAL (solo si se usa MySQL con DB_ENGINE=mysql). Ejecutar una vez como root:
--   mysql -u root -p < bd/crear_bd.sql
-- Las tablas NO se crean aquí: las crea Django con "python manage.py migrate"
-- a partir de los modelos (cuentas, catalogo, solicitudes).

CREATE DATABASE IF NOT EXISTS scpc
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'scpc_app'@'localhost' IDENTIFIED BY 'scpc_2026';
GRANT ALL PRIVILEGES ON scpc.* TO 'scpc_app'@'localhost';

-- Base de datos que Django crea temporalmente al ejecutar pruebas (manage.py test)
GRANT ALL PRIVILEGES ON test_scpc.* TO 'scpc_app'@'localhost';

FLUSH PRIVILEGES;
