# Definición de la API por Módulos

Cada conjunto de rutas pertenece al controlador de su respectivo módulo y se centralizan en el enrutador principal (`src/api/v1/index.py`).

## 1. Módulo: Auth y Usuarios (`auth/` y `users/`)

Controla el acceso y los roles administrativos y técnicos.

* `POST /api/auth/login` - Autenticar personal y generar token de sesión.
* `GET /api/usuarios` - Listar usuarios del sistema (listado simple).
* `POST /api/usuarios` - Crear un nuevo usuario.
* `PUT /api/usuarios/{id}/estado` - Activar o desactivar usuarios.

## 2. Módulo: Clientes (`clients/`)

Gestiona los expedientes digitales de los clientes.

* `GET /api/clientes` - Listado simple de clientes.
* `QUERY /api/clientes/buscar` - Búsqueda avanzada de clientes (enviando JSON con múltiples filtros, ej. por fechas de registro, estado activo, ciudad).
* `POST /api/clientes` - Registrar un nuevo cliente.
* `GET /api/clientes/{id}` - Obtener detalles de un cliente específico.
* `PUT /api/clientes/{id}` - Actualizar datos del cliente.

## 3. Módulo: Equipos (`equipment/`)

Administra los dispositivos registrados por los clientes.

* `GET /api/equipos` - Listado simple de equipos registrados.
* `QUERY /api/equipos/buscar` - Filtrar el inventario de equipos (enviando JSON con criterios como `tipo`, `marca`, o `garantiaActiva`).
* `POST /api/equipos` - Registrar un nuevo equipo y asociarlo a un cliente.
* `GET /api/equipos/{id}` - Obtener detalles del equipo.
* `GET /api/equipos/{id}/historial` - Consultar servicios previos asociados al equipo.

## 4. Módulo: Órdenes de Servicio (`service-orders/`)

El núcleo operativo del sistema. Controla el flujo desde la recepción hasta la entrega.

* `GET /api/ordenes/{folio}` - Consultar estado de la orden por folio (ideal para uso del cliente y el Chatbot).
* `QUERY /api/ordenes/buscar` - Realizar búsquedas avanzadas (enviando JSON con combinación de múltiples `estados`, `rangoFechas`, `tecnicoId`, etc.).
* `POST /api/ordenes` - Crear nueva orden de servicio generando un folio único.
* `PUT /api/ordenes/{id}/tecnico` - Asignar o reasignar un técnico responsable.
* `PUT /api/ordenes/{id}/estado` - Actualizar el estado de la reparación (Recibido, En revisión, Reparando, Listo, Entregado).
* `POST /api/ordenes/{id}/diagnostico` - Registrar o actualizar el diagnóstico técnico inicial.
* `POST /api/ordenes/{id}/actividades` - Registrar actividades realizadas y la solución final.
* `POST /api/ordenes/{id}/entregar` - Registrar la entrega formal del equipo y cerrar el servicio.
* `GET /api/ordenes/{id}/historial` - Listar todos los cambios de una orden.
* `QUERY /api/ordenes/historial/filtrar` - Búsqueda avanzada en la bitácora de cambios (enviando JSON con `usuarioId`, `accion`, etc.).

## 5. Módulo: Inventario (`inventory/`)

Controla las piezas y refacciones disponibles para las reparaciones.

* `GET /api/inventario` - Listado simple de materiales.
* `QUERY /api/inventario/buscar` - Búsqueda avanzada de refacciones (enviando JSON para filtrar por categorías, o parámetros como `soloStockBajo: true`).
* `POST /api/inventario` - Registrar nuevos materiales y definir su stock mínimo.
* `PUT /api/inventario/{id}` - Actualizar detalles del material o ajustar existencias manualmente.
* `POST /api/inventario/consumo` - Registrar la salida/consumo de un material vinculándolo a una orden de servicio.

## 6. Módulo: Tablero / Reportes (`reports/`)

Endpoints destinados a la vista administrativa general y métricas.

* `QUERY /api/reportes/tablero` - Obtener métricas y conteos operativos (enviando JSON para filtrar dimensiones: ej. carga de trabajo por técnico, excluir ciertos estados, rango de fechas).
* `QUERY /api/reportes/inactividad` - Identificar equipos en estado Listo que exceden el tiempo de espera (enviando JSON con umbrales de días inactivos).