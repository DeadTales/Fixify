# Front-end Fixify

Interfaz de escritorio con ttkbootstrap. Desde la raíz del proyecto:

```powershell
python -m pip install -r frontend/requirements.txt
python frontend/src/app/main.py
```

Requiere Python con Tkinter. `asyncio` pertenece a la biblioteca estándar: no se instala como dependencia. La API usa `http://127.0.0.1:8000`; puede cambiarse con la variable `FIXIFY_API_URL`.

- `services/api_client.py`: HTTP, token y errores comunes.
- `services/*_service.py`: rutas y datos de cada módulo.
- `app/async_runner.py`: solicitudes en asyncio; callbacks de widgets en Tk.
- `ui/components/`: componentes reutilizables separados en `field.py`, `async_frame.py`, `table.py`, `form_dialog.py` y `collection_view.py`. `__init__.py` conserva los imports comunes.
- `ui/views/`: dashboard, clientes, equipos y usuarios.
- `ui/sistema_gestion.py`: navegación según rol.
- `models/`: contratos Pydantic de sesión, clientes, equipos y usuarios.

Los servicios validan entradas antes de enviarlas y convierten respuestas JSON a modelos. Las vistas usan atributos: `equipo.numero_serie`, `cliente.nombre` o `sesion.role`. Para enviar un modelo como JSON se usa `model_dump()`; no se reutilizan modelos ORM del backend. Los campos opcionales aceptan `None`; los tipos de respuesta se comprueban sin conversiones silenciosas. El backend conserva la validación final de formatos e integridad.

`models/database.py` es un prototipo anterior en memoria; no es parte del contrato ni del login activo.

Para agregar un módulo, crear su service, heredar de `CollectionView` si usa listado/alta y registrarlo en la navegación. Los métodos async solo trabajan con datos; los callbacks leen y actualizan widgets. Cerrar una vista cancela tareas y descarta resultados pendientes. Cancelar una solicitud no garantiza revertir una escritura ya recibida por el servidor: comprobar el listado antes de repetir un alta.

Pruebas sin GUI ni servidor:

```powershell
python -m unittest discover -s frontend/tests -v
```

El backend incluye GET `/equipos/` y mapea sus columnas al diagrama de BD. Los cambios de rol/actividad requieren autorización vigente en backend; ocultar botones y limpiar JWT local no revoca un token ya emitido.

La [documentación v2](../docs/Documentacion_frontend_v2.ipynb) explica el transporte httpx, los servicios y la integración con asyncio paso a paso.


Para integrar nuevos módulos, consultar [la guía paso a paso](../docs/GUIA_INTEGRACION_MODULOS_FRONTEND.ipynb) y el tutorial del notebook v2.
