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
