# API de Fixify: guía de endpoints

Contrato revisado contra los routers, esquemas y repositorios actuales del backend. Alcance: RF01–RF04 y edición/eliminación de clientes y equipos. Los ejemplos son ilustrativos: sustituir IDs por los de sus registros. Este documento no ejecuta peticiones.

## Cómo leer una petición

La dirección local es `http://127.0.0.1:8000`. Las rutas registradas **no llevan `/api/v1`**: por ejemplo, `GET /clientes/` significa consultar `http://127.0.0.1:8000/clientes/`.

- **Método:** GET consulta, POST registra o inicia sesión, PUT reemplaza los datos editables y PATCH cambia una parte específica. DELETE elimina cuando las relaciones lo permiten.
- **Ruta:** `{record_id}` y `{user_id}` son valores a sustituir por un entero, sin llaves: `/equipos/3`.
- **Query:** parámetros después de `?`, como `/clientes/buscar?q=Ana`. No son un cuerpo JSON.
- **Body:** datos enviados en el cuerpo de la petición. Las altas/ediciones usan `Content-Type: application/json`; el login usa formulario.
- **Respuesta:** combina código HTTP y cuerpo. Un 200/201 indica éxito; 4xx indica rechazo. El texto de ejemplo puede variar con el registro.

Conservar la barra final en los listados y altas (`/clientes/`, `/equipos/`, `/usuarios/`). Los endpoints por ID no la incluyen. Así se usa directamente la ruta registrada sin depender de redirecciones.

## Sesión y permisos

Para todas las rutas de usuarios, clientes y equipos enviar:

```http
Authorization: Bearer <access_token obtenido en el login>
```

`admin` gestiona usuarios, clientes y equipos. `recepcion` gestiona clientes y equipos. `tecnico` no tiene acceso a estos routers; sus módulos operativos se desarrollan en entregas posteriores.

El JWT vence en ocho horas. En cada petición protegida se consulta la cuenta actual: desactivarla impide usar tokens anteriores y cambiar su rol modifica los permisos aunque el token conserve el rol antiguo. No hay endpoint de logout: el frontend elimina su token local; eso no revoca un JWT válido en el servidor.

## Mapa de rutas

| Método y ruta | Para qué sirve | Permiso | Éxito |
| --- | --- | --- | --- |
| GET `/` | Información general de la API | Público | 200 |
| GET `/health` | Comprobar conexión a la BD | Público | 200 |
| POST `/auth/login` | Autenticar y obtener JWT | Público | 200 |
| GET `/usuarios/` | Consultar cuentas | admin | 200 |
| POST `/usuarios/` | Crear cuenta | admin | 200 |
| PUT `/usuarios/{user_id}` | Editar nombre y rol | admin | 200 |
| PATCH `/usuarios/{user_id}/rol` | Cambiar rol | admin | 200 |
| PATCH `/usuarios/{user_id}/habilitar` | Activar cuenta | admin | 200 |
| PATCH `/usuarios/{user_id}/inhabilitar` | Desactivar cuenta | admin | 200 |
| GET `/clientes/` | Consultar clientes | admin / recepcion | 200 |
| GET `/clientes/buscar?q=...` | Buscar por nombre o teléfono | admin / recepcion | 200 |
| POST `/clientes/` | Registrar cliente | admin / recepcion | 201 |
| PUT `/clientes/{record_id}` | Editar cliente | admin / recepcion | 200 |
| DELETE `/clientes/{record_id}` | Eliminar cliente sin relaciones | admin / recepcion | 200 |
| GET `/equipos/` | Consultar equipos | admin / recepcion | 200 |
| POST `/equipos/` | Registrar equipo de un cliente | admin / recepcion | 201 |
| PUT `/equipos/{record_id}` | Editar equipo | admin / recepcion | 200 |
| DELETE `/equipos/{record_id}` | Eliminar equipo sin órdenes | admin / recepcion | 200 |

## Errores comunes

Todos los endpoints protegidos pueden responder 401 por sesión ausente/inválida/expirada o cuenta desactivada, y 403 por rol sin permiso. Un 401 por token inválido o cuenta desactivada incluye `WWW-Authenticate: Bearer`. En login, una cuenta inactiva devuelve 403.

Los errores de negocio usan un objeto con `detail`:

```json
{
  "detail": "El cliente tiene equipos asociados. No puede eliminarse."
}
```

Los errores de validación usan `detail` como lista. Ejemplo de un cuerpo incompleto:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "body",
        "nombre"
      ],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

`loc` señala el origen (`body`, `query` o `path`) y el campo rechazado; `msg` explica el motivo. Es una estructura ilustrativa: mensajes y detalles dependen de la validación. Un ID no interpretable como entero, como `/equipos/abc`, produce 422. Un ID entero que no existe produce 404 en edición/eliminación.

Los conflictos documentados por endpoint son los manejados por el código. Un fallo de infraestructura no se convierte necesariamente en esos errores; `/health` sí transforma un fallo de consulta en 503.


## Información general y autenticación

### GET `/`

**Para qué sirve:** Consultar que la API responde y conocer su entorno. No consulta la base de datos.

**Permiso:** público.

**Qué recibe:** Sin body ni parámetros.

**Qué devuelve:**

HTTP 200.

```json
{
  "status": "success",
  "environment": "development",
  "message": "Bienvenido al backend de Fixify"
}
```

**Errores específicos:** No hay errores de negocio definidos para esta ruta.


### GET `/health`

**Para qué sirve:** Verificar que la API puede ejecutar SELECT 1 en la base de datos.

**Permiso:** público.

**Qué recibe:** Sin body ni parámetros.

**Qué devuelve:**

HTTP 200.

```json
{
  "api_status": "running",
  "db_status": "connected",
  "environment": "development",
  "version": "1.0.0"
}
```

**Errores específicos:** 503 si la consulta a la BD falla; devuelve `{"detail":"Error conectando a la base de datos: ..."}`.

El entorno y versión dependen de settings. Una respuesta correcta no demuestra que todas las tablas o migraciones existan.


### POST `/auth/login`

**Para qué sirve:** Validar credenciales de personal y obtener una sesión.

**Permiso:** público.

**Qué recibe:** **Formulario, no JSON.** Usar `Content-Type: application/x-www-form-urlencoded`. Campos `username` y `password` obligatorios. username acepta el nombre de cuenta o su correo registrado.

```text
username=tecnico_demo&password=Ejemplo123
```

**Qué devuelve:**

HTTP 200.

```json
{
  "access_token": "<JWT firmado>",
  "token_type": "bearer",
  "role": "tecnico",
  "message": "Ingreso exitoso"
}
```

**Errores específicos:** 401: usuario inexistente o contraseña incorrecta. 403: cuenta deshabilitada o rol no autorizado. 422: faltan campos del formulario.

Guardar `access_token` para la cabecera Authorization. La contraseña conserva sus espacios; el cliente no debe recortarla. `message` está en inglés como nombre de campo en esta respuesta; otras confirmaciones usan `mensaje`.


## Usuarios

Estos endpoints exigen administrador. No devuelven contraseña ni hash. No existe DELETE de usuarios: la desactivación conserva relaciones históricas. Se puede editar nombre y rol mediante PUT. No existe una ruta para restablecer contraseña.

### Contrato para crear una cuenta

| Campo | Tipo | Obligatorio | Regla |
| --- | --- | --- | --- |
| username | string | Sí | 4–50 caracteres |
| password | string | Sí | Mínimo 6 caracteres y máximo 72 bytes UTF-8 por bcrypt |
| role | string | No | admin, tecnico o recepcion; si se omite usa tecnico |

El catálogo de roles debe contener el rol solicitado. Los 72 bytes no equivalen siempre a 72 caracteres cuando hay acentos u otros caracteres multibyte.


### GET `/usuarios/`

**Para qué sirve:** Consultar cuentas ordenadas por ID.

**Permiso:** admin.

**Qué recibe:** Sin body ni filtros.

**Qué devuelve:**

HTTP 200: lista de usuarios; `[]` si no hay registros.

```json
[
  {
    "id": 2,
    "username": "tecnico_demo",
    "role": "tecnico",
    "is_active": true
  }
]
```

**Errores específicos:** Solo los errores comunes de sesión/permisos.

Cada usuario contiene `id` entero, `username` string, `role` string y `is_active` booleano.


### POST `/usuarios/`

**Para qué sirve:** Crear una cuenta activa con contraseña almacenada mediante hash.

**Permiso:** admin.

**Qué recibe:** Body JSON con el contrato de cuenta. Ejemplo:

```json
{
  "username": "tecnico_demo",
  "password": "Ejemplo123",
  "role": "tecnico"
}
```


**Qué devuelve:**

HTTP **200**, como está implementado actualmente; esta ruta no declara 201.

```json
{
  "mensaje": "Usuario creado con éxito",
  "usuario": "tecnico_demo"
}
```

**Errores específicos:** 409: nombre/correo identificado como cuenta existente, o rol ausente del catálogo. 422: incumplimiento del esquema o límite bcrypt.


### PATCH `/usuarios/{user_id}/rol`

**Para qué sirve:** Asignar un rol válido a una cuenta existente.

**Permiso:** admin.

**Qué recibe:** user_id entero en la ruta. Body JSON con role obligatorio:

```json
{
  "role": "recepcion"
}
```


**Qué devuelve:**

HTTP 200.

```json
{
  "mensaje": "El rol de tecnico_demo ha sido actualizado a recepcion."
}
```

**Errores específicos:** 404: usuario no encontrado. 409: rol no existe en catálogo. 422: role inválido o ID mal formado.

El cambio se aplica a sus siguientes peticiones, incluidos tokens anteriores.


### PATCH `/usuarios/{user_id}/habilitar`

**Para qué sirve:** Permitir nuevamente el acceso de una cuenta.

**Permiso:** admin.

**Qué recibe:** user_id entero en la ruta. Sin body; no enviar JSON vacío por obligación.

**Qué devuelve:**

HTTP 200.

```json
{
  "mensaje": "La cuenta de tecnico_demo ha sido habilitada para acceder al sistema."
}
```

**Errores específicos:** 404: usuario no encontrado; 422: ID mal formado.

Conserva el rol y el historial.


### PATCH `/usuarios/{user_id}/inhabilitar`

**Para qué sirve:** Bloquear el acceso sin borrar la cuenta.

**Permiso:** admin.

**Qué recibe:** user_id entero en la ruta. Sin body.

**Qué devuelve:**

HTTP 200.

```json
{
  "mensaje": "La cuenta de tecnico_demo ha sido inhabilitada. Su acceso fue bloqueado pero la información se conservó."
}
```

**Errores específicos:** 404: usuario no encontrado; 422: ID mal formado.

Impide nuevos logins y uso de JWT anteriores mientras la cuenta esté inactiva.


## Clientes

### Contrato JSON de alta y edición

| Campo | Tipo | Obligatorio | Regla |
| --- | --- | --- | --- |
| nombre | string | Sí | 2–100 caracteres después de recortar espacios externos |
| telefono | string | Sí | Longitud 8–20; entre 8 y 15 dígitos; admite dígitos, +, paréntesis, guion, punto y espacios |
| correo | string o null | No | Email válido si se proporciona; omitir o usar null si no existe |

Teléfono se envía como string, no número, para conservar signos y ceros. El repositorio compara duplicados por el string almacenado; no normaliza formatos distintos al mismo número. El frontend convierte correo vacío a null, pero para consumir directamente la API enviar null u omitirlo, no `""`.

El registro devuelto añade `id` entero. El body editable no incluye id.


### GET `/clientes/`

**Para qué sirve:** Obtener el directorio de clientes.

**Permiso:** admin o recepcion.

**Qué recibe:** Sin body. No hay filtros ni paginación en esta ruta.

**Qué devuelve:**

HTTP 200: lista de registros, o `[]`.

```json
[
  {
    "id": 7,
    "nombre": "Ana López",
    "telefono": "3312345678",
    "correo": null
  }
]
```

**Errores específicos:** Solo errores comunes de sesión/permisos.

No se garantiza orden explícito en el repositorio actual.


### GET `/clientes/buscar`

**Para qué sirve:** Localizar coincidencias parciales en nombre o teléfono.

**Permiso:** admin o recepcion.

**Qué recibe:** Query `q` string obligatoria: `/clientes/buscar?q=Ana`. Sin body.

**Qué devuelve:**

HTTP 200: lista de coincidencias, o `[]` si no encuentra.

```json
[
  {
    "id": 7,
    "nombre": "Ana López",
    "telefono": "3312345678",
    "correo": null
  }
]
```

**Errores específicos:** 422 si falta q.

La búsqueda usa ILIKE; no exige un tamaño mínimo de q. Un resultado vacío no es 404. Codificar caracteres especiales de la URL, por ejemplo con --data-urlencode de curl.


### POST `/clientes/`

**Para qué sirve:** Registrar un cliente y obtener su ID para asociar equipos.

**Permiso:** admin o recepcion.

**Qué recibe:** Body JSON según el contrato de cliente:

```json
{
  "nombre": "Ana López",
  "telefono": "3312345678",
  "correo": null
}
```


**Qué devuelve:**

HTTP 201.

```json
{
  "mensaje": "¡Cliente registrado correctamente en el sistema!",
  "cliente": {
    "id": 7,
    "nombre": "Ana López",
    "telefono": "3312345678",
    "correo": null
  }
}
```

**Errores específicos:** 400: teléfono ya registrado. 422: nombre/teléfono/correo inválido.

La confirmación contiene el registro completo en `cliente`.


### PUT `/clientes/{record_id}`

**Para qué sirve:** Corregir los datos de un cliente conservando su ID y relaciones.

**Permiso:** admin o recepcion.

**Qué recibe:** record_id entero en ruta. Body con nombre y teléfono obligatorios, correo opcional:

```json
{
  "nombre": "Ana López García",
  "telefono": "3312345678",
  "correo": null
}
```


**Qué devuelve:**

HTTP 200: registro actualizado directamente, sin envoltorio mensaje/cliente.

```json
{
  "id": 7,
  "nombre": "Ana López García",
  "telefono": "3312345678",
  "correo": null
}
```

**Errores específicos:** 404: registro no existe. 409: teléfono pertenece a otro cliente o conflicto de integridad al guardar. 422: body inválido.

Es reemplazo completo de campos editables, no PATCH. Si se omite correo, se guarda null; para conservarlo enviarlo nuevamente.


### DELETE `/clientes/{record_id}`

**Para qué sirve:** Eliminar un cliente que no tenga equipos ni órdenes asociados.

**Permiso:** admin o recepcion.

**Qué recibe:** record_id entero en ruta; sin body.

**Qué devuelve:**

HTTP 200 con JSON; no devuelve 204.

```json
{
  "mensaje": "Registro eliminado correctamente."
}
```

**Errores específicos:** 404: no existe. 409: tiene equipos, órdenes o conflicto de integridad.

No elimina equipos u órdenes en cascada. La confirmación describe una eliminación física del registro libre.


## Equipos

### Contrato JSON de alta y edición

| Campo | Tipo | Obligatorio | Regla |
| --- | --- | --- | --- |
| tipo | string | Sí | 2–50 caracteres |
| marca | string | Sí | 2–50 caracteres |
| modelo | string | Sí | 2–50 caracteres |
| numero_serie | string o null | No | Máximo 100 caracteres; se comprueba duplicado si no está vacío |
| problema_reportado | string | Sí | Mínimo 5 caracteres |
| client_id | integer | Sí | Mayor que 0 y cliente existente |

Se recortan espacios externos de strings. Para equipos sin serie enviar null u omitirla. El frontend convierte serie vacía a null; la API directa admite un string vacío según su esquema actual. La unicidad se comprueba en el repositorio antes de guardar; este control por sí solo no garantiza unicidad entre altas simultáneas.

`client_id` es el nombre público del propietario en los cuerpos y listados. La confirmación de alta usa `cliente_id` dentro de detalles. No son dos propietarios distintos. EQ identifica el equipo, no una orden de servicio.


### GET `/equipos/`

**Para qué sirve:** Consultar los equipos registrados y su propietario.

**Permiso:** admin o recepcion.

**Qué recibe:** Sin body ni filtros/paginación.

**Qué devuelve:**

HTTP 200: lista ordenada por ID, o `[]`.

```json
[
  {
    "id": 3,
    "tipo": "Laptop",
    "marca": "Lenovo",
    "modelo": "ThinkPad T14",
    "numero_serie": "SN-003",
    "problema_reportado": "No enciende",
    "client_id": 7
  }
]
```

**Errores específicos:** Solo errores comunes de sesión/permisos.


### POST `/equipos/`

**Para qué sirve:** Registrar un equipo asociado a un cliente existente.

**Permiso:** admin o recepcion.

**Qué recibe:** Body JSON según el contrato de equipo:

```json
{
  "tipo": "Laptop",
  "marca": "Lenovo",
  "modelo": "ThinkPad T14",
  "numero_serie": "SN-003",
  "problema_reportado": "No enciende",
  "client_id": 7
}
```


**Qué devuelve:**

HTTP 201.

```json
{
  "mensaje": "¡Equipo registrado correctamente!",
  "folio": "EQ-003",
  "detalles": {
    "id_interno": 3,
    "tipo": "Laptop",
    "marca": "Lenovo",
    "modelo": "ThinkPad T14",
    "cliente_id": 7
  }
}
```

**Errores específicos:** 404: cliente inexistente. 409: número de serie ya registrado. 422: body inválido.

La respuesta es un resumen; para recuperar todos los campos consultar GET /equipos/.


### PUT `/equipos/{record_id}`

**Para qué sirve:** Corregir los datos de un equipo manteniendo su identificador.

**Permiso:** admin o recepcion.

**Qué recibe:** record_id entero en ruta; body completo según contrato:

```json
{
  "tipo": "Laptop",
  "marca": "Lenovo",
  "modelo": "ThinkPad T14",
  "numero_serie": "SN-003",
  "problema_reportado": "No enciende después de una caída",
  "client_id": 7
}
```


**Qué devuelve:**

HTTP 200: registro actualizado directamente.

```json
{
  "id": 3,
  "tipo": "Laptop",
  "marca": "Lenovo",
  "modelo": "ThinkPad T14",
  "numero_serie": "SN-003",
  "problema_reportado": "No enciende después de una caída",
  "client_id": 7
}
```

**Errores específicos:** 404: equipo o cliente no existe. 409: serie de otro equipo, cambio de propietario de un equipo con órdenes o conflicto de integridad. 422: body inválido.

Enviar client_id incluso si el propietario no cambia. Si se omite numero_serie se guarda null. Con órdenes se puede editar características, pero no cambiar propietario.


### DELETE `/equipos/{record_id}`

**Para qué sirve:** Eliminar un equipo que todavía no tenga órdenes.

**Permiso:** admin o recepcion.

**Qué recibe:** record_id entero en ruta; sin body.

**Qué devuelve:**

HTTP 200.

```json
{
  "mensaje": "Registro eliminado correctamente."
}
```

**Errores específicos:** 404: equipo no existe. 409: órdenes vinculadas o conflicto de integridad.

Conserva el cliente. No borra órdenes ni historial en cascada.


## Ejemplos de uso con curl

Estos ejemplos están escritos para Bash. En PowerShell usar `curl.exe` y adaptar comillas/variables, o utilizar Swagger UI. **Los POST, PUT, PATCH y DELETE modifican la base configurada por el backend**: ejecutarlos con datos de práctica y IDs propios.

Login (formulario):

```bash
curl -i -X POST 'http://127.0.0.1:8000/auth/login' --data-urlencode 'username=tecnico_demo' --data-urlencode 'password=Ejemplo123'
```

Usar una cuenta admin o recepción para los siguientes ejemplos; un token de técnico recibirá 403. Copiar access_token del login:

```bash
TOKEN='<access_token>'
curl -i 'http://127.0.0.1:8000/clientes/' -H "Authorization: Bearer $TOKEN"
curl -i -G 'http://127.0.0.1:8000/clientes/buscar' -H "Authorization: Bearer $TOKEN" --data-urlencode 'q=Ana López'
curl -i -X POST 'http://127.0.0.1:8000/clientes/' -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' --data '{"nombre":"Ana López","telefono":"3312345678","correo":null}'
curl -i -X PUT 'http://127.0.0.1:8000/clientes/7' -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' --data '{"nombre":"Ana López García","telefono":"3312345678","correo":null}'
curl -i -X DELETE 'http://127.0.0.1:8000/equipos/3' -H "Authorization: Bearer $TOKEN"
```

| Parte | Función |
| --- | --- |
| curl | Cliente HTTP desde la terminal |
| -i | Muestra las cabeceras y el código HTTP junto al cuerpo |
| -X POST/PUT/DELETE | Selecciona explícitamente el método; sin -X ni datos usa GET |
| -H | Añade una cabecera, como Authorization o Content-Type |
| --data | Envía el cuerpo; con application/json ese texto es el JSON de entrada |
| --data-urlencode | Codifica valores especiales; en login envía formulario |
| -G | Coloca los datos codificados en la query de un GET en vez de un body |
| $TOKEN | Sustituye la variable Bash por el JWT copiado; no enviar literalmente el marcador |

## Documentación interactiva y alcance

Con el backend ejecutándose y `ENVIRONMENT=development`, abrir `http://127.0.0.1:8000/docs` (Swagger UI) o `/redoc`. Swagger permite inspeccionar los esquemas y probar las operaciones con una cuenta autorizada. Su ejecución de POST/PUT/PATCH/DELETE también modifica datos. Algunas respuestas construidas sin response_model no muestran en OpenAPI un esquema detallado; los ejemplos de esta guía describen sus cuerpos reales.

`/openapi.json` expone el esquema generado; el código actual solo condiciona /docs y /redoc al entorno. Las rutas automáticas de documentación no son endpoints de negocio del mapa anterior.

No hay endpoints públicos de órdenes, diagnóstico, inventario ni consulta de folio registrados en main.py actualmente. La existencia de modelos SQL o carpetas api/v1 no implica que haya rutas para consumirlos.

La [guía de pruebas](../Test/Guia_Pruebas_Fixify.ipynb) explica cómo verificar los contratos con bases temporales y transportes controlados. Los ejemplos de esta guía no constituyen evidencia de una ejecución contra PostgreSQL real.


## Si Uvicorn no encuentra FastAPI aunque está instalado

Si pip encuentra FastAPI dentro del entorno, pero el traceback de uvicorn muestra `/usr/lib/python.../site-packages/uvicorn`, se están usando dos intérpretes distintos. Desde la carpeta backend, ejecutar:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

`python -m uvicorn` carga Uvicorn con el Python activo; `main:app` selecciona el objeto app de main.py; `--reload` reinicia el servidor ante cambios de código en desarrollo; `--host 127.0.0.1` escucha en la máquina local; `--port 8000` selecciona el puerto.

Para el entorno fixify de esta máquina, puede seleccionarse el intérprete explícitamente, sin depender de PATH:

```bash
/home/deadtales/.venvs/fixify/bin/python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Esta ruta es específica de esta máquina. Para otros entornos utilizar su propio ejecutable. Si faltan dependencias, desde backend instalar con `python -m pip install -r requirements.txt` usando ese mismo intérprete. No hace falta reinstalar FastAPI si ya está en él.

Diagnóstico sin iniciar el servidor:

```bash
python -c "import sys, fastapi, uvicorn; print(sys.executable); print(fastapi.__file__); print(uvicorn.__file__)"
```

Las bibliotecas deben provenir del entorno seleccionado. `hash -r` limpia rutas de ejecutables memorizadas por Bash, pero el comando con `python -m` ya evita depender de la resolución del ejecutable uvicorn. Ejecutar desde backend mantiene la resolución correcta de main.py y DataBase.env.


## PUT `/usuarios/{user_id}` — editar usuario

**Para qué sirve:** cambiar nombre y rol de una cuenta conservando ID, contraseña, estado e historial. Solo admin, con Authorization: Bearer.

**Recibe:** user_id entero en ruta y JSON con los dos campos obligatorios. username: 4–50 caracteres tras recortar espacios externos; role: admin, tecnico o recepcion.

```json
{"username": "tecnico_editado", "role": "recepcion"}
```

**Devuelve:** HTTP 200 y registro público, sin contraseña/hash:

```json
{"id": 2, "username": "tecnico_editado", "role": "recepcion", "is_active": true}
```

**Errores:** 401 sesión inválida; 403 sin rol admin; 404 cuenta inexistente; 409 nombre ocupado, rol ausente del catálogo o conflicto de integridad; 422 datos inválidos. No modifica is_active: utilizar PATCH habilitar/inhabilitar. Al cambiar el nombre, la cuenta debe iniciar sesión de nuevo, porque el JWT anterior identifica el nombre previo.
