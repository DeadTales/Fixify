# Alineación del backend con SQL y diagrama

Revisión: 02-Oct-2026. El SQL local y `Diagramas.pdf` definen las diez tablas del dominio. Se mapearon columnas, longitudes, nullabilidad, defaults y llaves foráneas. `domain_models.py` reúne las entidades de mantenimiento aún sin endpoints; usuarios, roles, clientes y equipos conservan módulos propios.

| Contrato API | Tabla / columna física |
|---|---|
| User.id / username / hashed_password | usuarios.id_usuario / nombre / contrasena_hash |
| User.role | roles.nombre_rol mediante usuarios.id_rol |
| Client.id | clientes.id_cliente |
| Equipment.id / client_id / problema_reportado | equipos.id_equipo / id_cliente / falla_reportada |

El login acepta nombre de cuenta o correo. El catálogo convierte Administrador, Técnico y Recepcionista (incluidas etiquetas de prueba) a admin/tecnico/recepcion. Las contraseñas se almacenan como hashes bcrypt; se usa bcrypt directamente para evitar incompatibilidades con passlib. El listado de usuarios limita la salida con UserResponse.

El esquema SQL no contiene `is_active`: la propiedad API devuelve True como compatibilidad y los endpoints de activar/desactivar devuelven 409 explicando que falta el estado persistido. No se simula un bloqueo guardado. Para recuperar esa función hace falta acordar una extensión del SQL/diagrama.

El SQL tampoco contiene dirección del cliente. El ORM no la consulta ni la guarda; la API devuelve None y rechaza un alta con dirección no vacía. Supabase conserva la columna adicional existente y sus datos. Los formularios actuales deben omitir ese dato hasta acordar su inclusión en el esquema.

## Cambios y verificación en Supabase

Se inspeccionó el catálogo con DataBase.env sin exponer credenciales. Existían tablas `users` y `usuarios`: el backend ahora usa `usuarios`; `users` se conserva y sus cuentas no se copian automáticamente. Equipos tenía `problema_reportado`: se renombró a `falla_reportada` mediante la migración 001, conservando valores. No se ejecutó el SQL destructivo de recreación ni se eliminó ninguna tabla. El arranque dejó de ejecutar create_all.

Se creó `fixify_prueba`, ID 2, rol recepción, en usuarios con FK al catálogo roles. La contraseña aleatoria está en `backend/usuario_prueba.local.json`, excluido de Git; no se incorpora a este documento. Se verificaron el hash, el flujo real de login y la serialización de clientes/equipos contra Supabase. Esto no es una prueba visual completa ni valida las funciones futuras de órdenes/inventario.

El script `backend/scripts/crear_usuario_prueba.py` carga DataBase.env, aplica el ajuste solo si hace falta y crea la cuenta en una transacción. Una segunda ejecución reutiliza la cuenta y verifica su contraseña local, sin resetearla. Nunca imprime tokens, hashes ni cadenas de conexión.

Pruebas locales: `python -m unittest discover -s backend/tests -v`. Comparan columnas/FK/nullabilidad/longitudes con el SQL y prueban alta de usuario, bcrypt y autenticación. El SQL conserva sus datos de ejemplo históricos: `hash_falso_12345` no es una contraseña válida; se debe usar la cuenta creada por el script.
