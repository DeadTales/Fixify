"""Ventana de navegación; delega cada módulo a su propia vista."""
from tkinter import TclError, messagebox
import ttkbootstrap as ttk
from ui.views.dashboard import DashboardView
from ui.views.discovery import available_views
from ui.branding import load_logo, set_window_icon

ROLE_LABELS = {'admin': 'Administrador', 'recepcion': 'Recepción', 'tecnico': 'Técnico'}


class SistemaGestion(ttk.Toplevel):
    """Compone navegación por rol con servicios y runner compartidos."""

    def __init__(self, master, usuario_actual, rol_actual, services, runner):
        """master: login; usuario_actual: cuenta; rol_actual: rol API; services/runner: dependencias."""
        super().__init__(master)
        self.services, self.runner, self.role = services, runner, rol_actual
        self.view = None
        set_window_icon(self)
        self.title('Fixify — Gestión de Equipos Tecnológicos')
        self.geometry('1100x700')
        self.minsize(900, 600)
        self.protocol('WM_DELETE_WINDOW', master.cerrar_aplicacion)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self, padding=15, bootstyle='secondary')
        sidebar.grid(row=0, column=0, sticky='nsew')

        self.logo = load_logo(self, (150, 150))
        ttk.Label(sidebar, image=self.logo, bootstyle='inverse-secondary').pack(pady=15)
        ttk.Label(sidebar, text=f'''Usuario: {usuario_actual}\nRol: {ROLE_LABELS.get(
            self.role,
            self.role,
        )}''',
                  bootstyle='inverse-secondary').pack(pady=(0, 20))

        # Cada vista declara etiqueta, roles y orden. El backend debe validar
        # permisos: ocultar un botón solo controla la presentación.
        views = available_views(self.role)

        for label, view_class in views:
            ttk.Button(sidebar, text=label, bootstyle='secondary',
                       command=lambda cls=view_class: self.show_view(cls)).pack(fill='x', pady=5)

        ttk.Button(sidebar, text='Cerrar sesión', bootstyle='danger',
                   command=self.cerrar_sesion).pack(side='bottom', fill='x', pady=10)

        self.content = ttk.Frame(self, padding=25)
        self.content.grid(row=0, column=1, sticky='nsew')
        self.place_window_center()
        self.show_view(DashboardView)

    def show_view(self, view_class):
        """view_class: módulo a mostrar; destruye la vista anterior y sus modales."""

        if self.view is not None:
            self.view.destroy()

        self.view = view_class(self.content, self.services, self.runner, self.role)
        self.view.pack(fill='both', expand=True)

    def bring_to_front(self):
        """Eleva la ventana tras login; topmost se libera para usar otras apps."""
        if not self.winfo_exists():
            return

        self.deiconify()
        self.lift()
        self.focus_force()

        try:
            self.attributes('-topmost', True)
            self.after(250, self._release_topmost)
        except TclError:
            pass  # Algunos gestores no admiten topmost; lift ya se ejecutó.

    def _release_topmost(self):
        """Restaura la prioridad normal si la ventana sigue abierta."""
        if self.winfo_exists():
            try:
                self.attributes('-topmost', False)
            except TclError:
                pass

    def cerrar_sesion(self):
        """Borra el JWT local y vuelve a login; no revoca tokens en backend."""

        if messagebox.askyesno(
            'Cerrar sesión',
            '¿Desea salir del sistema?',
            parent=self,
        ):
            self.services.api.set_token(None)
            self.destroy()
            self.master.deiconify()

    def destroy(self):
        """Cancela tareas de la vista antes de cerrar la ventana."""

        if self.view is not None:
            self.view.destroy()

            self.view = None

        super().destroy()
