# Integrar módulos en el frontend de Fixify

Esta guía explica la implementación actual y una plantilla de órdenes. El ejemplo propone un contrato HTTP para enseñar el procedimiento; las rutas `/ordenes/` todavía no existen. No basta con copiar la vista para disponer del módulo: primero hay que implementar y acordar sus contratos en el backend. Los nombres de la API pueden ser alias de las columnas SQL.

## 1. Recorrido de una operación

```text
Botón o apertura de vista (hilo principal Tk)
  -> capturar valores de widgets
  -> runner.submit(coroutine, owner, éxito, error)
  -> coroutine del service (hilo que aloja asyncio)
  -> contrato de entrada -> ApiClient -> httpx -> backend
  -> contrato de respuesta -> Future terminado -> Queue
  -> root.after -> callback en Tk -> actualizar widgets
```

`async def` produce una coroutine al llamarse. `await` espera una operación dentro del bucle asyncio sin bloquearlo; no inicia ese bucle. Tk ya tiene `mainloop()`, por lo que `AsyncRunner` mantiene un bucle asyncio en un hilo adicional compartido. La cola comunica los resultados y `after()` permite que Tk los atienda. Revisar esta cola cada 30 ms no consulta Supabase ni refresca los datos de la API.

Se reutilizan un `Services`, un `ApiClient` y un `AsyncRunner` creados en login. No crear estos objetos por botón, vista o solicitud. El token se establece tras el login y se comparte entre servicios. El cliente HTTP se crea de forma diferida en el bucle asyncio y se cierra al terminar la aplicación.

## 2. Acordar primero el contrato del backend

Para este ejemplo se propone:

| Operación | Solicitud | Respuesta propuesta |
|---|---|---|
| GET `/ordenes/` | JWT en Authorization | Lista de `{id, equipo_id, estado}` |
| POST `/ordenes/` | JSON `{equipo_id}` y JWT | `{mensaje, orden: {id, equipo_id, estado}}` |

El servidor debe validar que exista el equipo, asignar el estado inicial y comprobar los permisos. Esta estructura es ilustrativa: el módulo real puede necesitar técnico asignado, fechas, prioridad y transiciones de estado. Revisar SQL, requisitos y diagrama antes de definir esos campos. Si cambia la respuesta propuesta, adaptar los modelos y el service; no modificar ApiClient para cada entidad.

## 3. Crear contratos: `src/models/orders.py`

```python
from pydantic import Field
from models.base import Contrato, Mensaje


class OrdenCrear(Contrato):
    """equipo_id: identificador API del equipo que recibirá mantenimiento."""
    equipo_id: int = Field(gt=0)


class Orden(Contrato):
    """Respuesta pública del servidor; estado lo decide el backend."""
    id: int = Field(gt=0)
    equipo_id: int = Field(gt=0)
    estado: str


class OrdenRegistrada(Mensaje):
    """Confirmación del POST; orden contiene el registro creado."""
    orden: Orden
```

Entrada, registro y confirmación representan mensajes diferentes: el alta no necesita `id` ni debe permitir elegir cualquier estado. Los modelos heredan la configuración de `Contrato`. Usar imports directos desde `models.orders`; no es obligatorio reexportarlos en `models/__init__.py`.

## 4. Crear servicio: `src/services/orders_service.py`

```python
from services.api_client import ModuleService
from models.orders import OrdenCrear, Orden, OrdenRegistrada


class OrdersService(ModuleService):
    """Operaciones de órdenes; comparte HTTP y no conoce la interfaz."""

    async def listar(self) -> list[Orden]:
        return await self._list('/ordenes/', Orden)

    async def crear(self, equipo_id) -> OrdenRegistrada:
        entrada = self._parse(OrdenCrear, {'equipo_id': equipo_id}, entrada=True)
        data = await self.api.request(
            'POST', '/ordenes/', json=entrada.model_dump(mode='json'))
        return self._parse(OrdenRegistrada, data)
```

`_parse(..., entrada=True)` valida el formulario; sin esa opción valida la respuesta. `_list` exige una lista JSON de objetos y valida cada registro. `mode='json'` también permite serializar tipos como fechas cuando se añadan al contrato. Para filtros usar `params={...}`; para JSON usar `json=...`. `data=...` se reserva para cuerpos de formulario como el login actual.

El servicio deja propagarse `ApiError`: el runner lo entrega al callback de error. No devolver una lista vacía al fallar una consulta, porque ocultaría el error como si no hubiera registros.

En `services/__init__.py`, importar `OrdersService` y añadir dentro de `Services.__init__`:

```python
self.orders = OrdersService(self.api)
```

## 5. Crear vista: `src/ui/views/orders.py`

```python
from models.orders import Orden
from services.api_client import ApiError
from ui.components import CollectionView, Field


class OrdersView(CollectionView):
    """Configura listado y alta reutilizando los componentes comunes."""
    title = 'Órdenes de servicio'
    columns = ('ID', 'ID Equipo', 'Estado')
    fields = (Field('equipo_id', 'ID del equipo'),)

    async def fetch(self):
        return await self.services.orders.listar()

    async def save(self, values):
        try:
            equipo_id = int(values['equipo_id'])
        except ValueError:
            raise ApiError('El ID del equipo debe ser un entero.') from None
        return await self.services.orders.crear(equipo_id=equipo_id)

    def row(self, record: Orden):
        return (record.id, record.equipo_id, record.estado)
```

`Field.name` coincide con el argumento `equipo_id`. Los Entry entregan texto y `Contrato` usa validación estricta: convertir explícitamente el ID en `save()`; el service valida después que sea positivo. En una implementación final puede sustituirse por un selector de equipos: `EquipmentView` muestra cómo consultar registros y relacionar etiquetas con IDs.

`CollectionView` carga automáticamente al construirse, gestiona la tabla, Actualizar y Nuevo, y abre `FormDialog`. El modal verifica campos obligatorios y evita envíos repetidos; el service valida el contrato. Tras guardar, `_created` muestra confirmación y recarga. La respuesta debe ser compatible con `Mensaje`; el folio se muestra específicamente para `EquipoRegistrado`, no para todas las entidades.

No duplicar `submit()` en `fetch()` o `save()`: la base ya programa esas coroutines. `row()` es síncrono y devuelve tantos valores como columnas, en el mismo orden. Para una pantalla con acciones o estructura distintas, heredar de `AsyncFrame` y componer controles en lugar de forzar `CollectionView`.

## 6. Registrar navegación y permisos

En `ui/sistema_gestion.py`, importar `OrdersView`. Agregar `('Órdenes', OrdersView)` a `views` dentro del grupo de roles acordado. Por ejemplo, si el contrato autoriza administrador y recepción, colocarlo en ese bloque existente.

`show_view` ya pasa contenedor, services, runner y role; no se cambia `main.py` ni el login. La navegación solo controla la presentación. Las rutas del backend deben aplicar autorización; para un técnico puede ser necesaria una vista de órdenes asignadas y un filtro aplicado por el servidor.

Si se necesita una métrica, incorporar la consulta a `DashboardView.queries` únicamente para los roles autorizados. Su `_fetch` ejecuta consultas independientes con `gather(return_exceptions=True)` y `_loaded` distingue errores de listas vacías.

## 7. Usar AsyncRunner en una vista personalizada

```python
# Dentro de un método normal de un widget, ejecutado en Tk:
try:
    equipo_id = int(self.entry_equipo.get())  # Leer widgets en Tk y convertir el ID.
except ValueError:
    self.status.configure(text='El ID del equipo debe ser un entero.')
    return
self.button.configure(state='disabled')
self.runner.submit(
    self.services.orders.crear(equipo_id),
    self,                  # Propietario que recibirá los callbacks.
    self._saved,           # Método normal: recibe OrdenRegistrada.
    self._failed,          # Método normal: recibe la excepción.
)
```

Definir `_saved(self, result)` y `_failed(self, error)` como métodos normales; ambos deben restablecer el estado visual del botón cuando corresponda. Se ejecutan en Tk y pueden modificar widgets. La coroutine no debe acceder a controles, abrir messagebox ni ejecutar trabajo CPU prolongado. `asyncio.run()` y `future.result()` dentro de botones bloquearían la interfaz; tampoco llamar manualmente a `root.update()` para simular concurrencia.

`submit` retorna un Future cancelable, o `None` si comienza el cierre. No confundirlo con el modelo de respuesta: este llega a `_saved`. Usar `owner` para vincular la tarea a la vista o al modal correcto. Una vista basada en `AsyncFrame` cancela sus tareas al destruirse; si sobrescribe `destroy()`, debe llamar a `super().destroy()`.

Cancelar una petición evita entregar resultados a widgets cerrados, pero no revierte una escritura que el servidor ya recibió. Evitar reintentos automáticos de POST sin acordar idempotencia. Cambiar de módulo cancela sus tareas; solo el cierre global utiliza `runner.close(api.aclose(), on_closed)` para cerrar HTTP y detener el hilo antes de destruir Tk.

## 8. Validación de una integración

1. Comprobar que rutas, métodos, JSON, permisos y respuestas coinciden con el backend real.
2. Probar el service con `httpx.MockTransport`: alta, listado, payload enviado, tipos recibidos y errores HTTP/de contrato. El laboratorio del notebook ofrece ejemplos sin red.
3. Probar filas y permisos de la vista; verificar lectura inicial, doble clic, carga fallida, guardado y navegación mientras una petición está pendiente.
4. Ejecutar las pruebas existentes desde la raíz: `python -m unittest discover -s frontend/tests -v`.
5. Ejecutar manualmente `python frontend/src/app/main.py` con backend disponible para verificar formularios, selector, navegación y cierre. Las pruebas sin Tk no certifican la apariencia visual.
6. Actualizar contratos, comentarios y el notebook cuando cambie la API. No incluir JWT, credenciales ni archivos locales de prueba en la documentación.

Una pantalla conectada debe distinguir datos vacíos de fallos, mantener la interfaz utilizable y cancelar callbacks al cerrar. Actualizar es una nueva lectura; si se requiere refresco automático, diseñar explícitamente polling o eventos en tiempo real y su cancelación al abandonar la vista.
