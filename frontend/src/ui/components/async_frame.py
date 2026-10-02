"""Base de vista que cancela sus peticiones cuando se destruye."""
import ttkbootstrap as ttk


class AsyncFrame(ttk.Frame):
    """Base de vista que cancela sus peticiones cuando se destruye."""

    def __init__(self, master, services, runner, role):
        """master: contenedor; services: módulos API; runner: puente asyncio; role: rol de dominio."""
        super().__init__(master)

        self.services, self.runner, self.role = services, runner, role

    def destroy(self):
        """Descarta tareas y callbacks antes de destruir los controles."""
        self.runner.cancel_owner(self)
        super().destroy()

    def request(self, operation, *args, on_success, on_error=None, **kwargs):
        """operation: método async; args/kwargs: sus datos; callbacks normales en Tk.

        Vincula la tarea a esta vista y usa _failed si no se indica on_error.
        Capturar los valores de widgets antes de llamar; no crear hilos ni loops.
        Devuelve el Future solo para quien necesite cancelar una lectura anterior.
        """
        return self.runner.submit(operation(*args, **kwargs), self,
                                  on_success, on_error or self._failed)

    def _failed(self, error):
        """error: excepción del service; muestra el mensaje en el estado de la vista."""
        self.status.configure(text=str(error))
