"""Puente asyncio/Tkinter: red en un hilo; todos los widgets en el hilo Tk."""
import asyncio
from concurrent.futures import CancelledError
from queue import Empty, Queue
from threading import Event, Thread
import logging


class AsyncRunner:
    """Puente compartido: recibe coroutines y entrega sus resultados al hilo Tk.

    Crear una sola instancia desde login y pasarla a las vistas. Las coroutines
    hacen I/O; los callbacks modifican widgets. No usar asyncio.run en botones.
    """

    def __init__(self, root):
        """root: ventana principal que programa la revisión de resultados."""

        self.root = root
        self.loop = asyncio.new_event_loop()
        self._ready = Event()
        # El trabajador produce resultados; Tk consume la cola sin bloquear.
        self._queue = Queue()
        # Future -> (propietario, callback de éxito, callback de error).
        # Solo el hilo Tk modifica este registro.
        self._pending = {}
        self._closing = False
        self._thread = Thread(target=self._run, name='fixify-asyncio', daemon=True)
        self._thread.start()
        self._ready.wait()

        self._poll_id = root.after(30, self._poll)

    def _run(self):
        """Mantiene un único loop para todas las conexiones HTTP."""
        asyncio.set_event_loop(self.loop)
        self._ready.set()

        try:
            self.loop.run_forever()
        finally:
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    def submit(self, coroutine, owner, on_success, on_error):
        """Programar desde Tk y devolver un Future cancelable (None al cerrar).

        coroutine: llamada async ya creada, por ejemplo service.listar().
        owner: widget cuya destrucción debe cancelar la entrega del resultado.
        on_success(result) y on_error(exception): funciones normales en Tk.
        No leer widgets dentro de coroutine: capturar sus valores antes de submit.
        """

        if self._closing:
            coroutine.close()
            return None

        future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
        self._pending[future] = (owner, on_success, on_error)
        # Este callback solo toca una cola Python; nunca llama a Tkinter.
        future.add_done_callback(self._queue.put)
        return future

    def cancel_owner(self, owner):
        """owner: vista/modal cerrado; elimina sus callbacks y cancela peticiones."""

        # Cancelar una petición no garantiza deshacer una escritura ya recibida
        # por el servidor. No reintentar POST automáticamente tras cancelación.
        for future, context in list(self._pending.items()):
            if context[0] is owner:
                self._pending.pop(future, None)
                future.cancel()

    def _poll(self):
        """Procesa resultados en el hilo principal; ignora ventanas destruidas."""

        try:
            while True:
                future = self._queue.get_nowait()
                context = self._pending.pop(future, None)

                if context is None:
                    continue

                owner, success, error = context

                if not owner.winfo_exists():
                    continue

                try:
                    result = future.result()
                except CancelledError:
                    continue
                except Exception as exc:
                    error(exc)
                else:
                    success(result)
        except Empty:
            pass
        finally:
            if not self._closing:
                self._poll_id = self.root.after(30, self._poll)

    def close(self, cleanup, on_closed):
        """cleanup: coroutine que cierra HTTP; on_closed: cierre de ventana en Tk."""

        # Solo el cierre global llama a este método. Cambiar de vista utiliza
        # cancel_owner; cerrar el cliente aquí lo inutilizaría para otros módulos.
        if self._closing:
            cleanup.close()
            return

        self._closing = True
        self.root.after_cancel(self._poll_id)

        for future in self._pending:
            future.cancel()

        self._pending.clear()

        async def shutdown():
            """Espera cancelaciones y libera HTTP antes de detener el loop."""

            current = asyncio.current_task()
            tasks = [task for task in asyncio.all_tasks() if task is not current]

            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)
            await cleanup

        future = asyncio.run_coroutine_threadsafe(shutdown(), self.loop)

        def finish():
            """Revisa el cierre sin bloquear el bucle de eventos de Tk."""

            if not future.done():
                self.root.after(30, finish)
                return

            try:
                future.result()
            except Exception:
                logging.exception('No se pudo cerrar el cliente HTTP')

            self.loop.call_soon_threadsafe(self.loop.stop)
            self._wait_thread(on_closed)

        self.root.after(30, finish)

    def _wait_thread(self, on_closed):
        """on_closed: se llama cuando el trabajador ya terminó."""

        if self._thread.is_alive():
            self.root.after(30, lambda: self._wait_thread(on_closed))
        else:
            on_closed()
