# PyMySQL se usa como conector de MySQL porque se instala con pip en
# Windows, Linux y macOS sin compilar nada (alternativa a mysqlclient).
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # Solo es necesario cuando se usa MySQL.
    pass
