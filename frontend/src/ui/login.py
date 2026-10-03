"""Login de escritorio con solicitudes asíncronas y sesión en memoria."""
import ttkbootstrap as ttk
import logging
from app.async_runner import AsyncRunner
from services import Services
from ui.branding import load_logo, set_window_icon


class VentanaLogin(ttk.Window):
    """Ventana principal; administra recursos y el ciclo de vida de la aplicación."""

    def __init__(self, services=None):
        """services: contenedor opcional para inyectar una API de pruebas."""
        super().__init__(title='Fixify — Iniciar sesión', themename='litera', size=(450, 460))
        self.geometry('450x540')
        set_window_icon(self)

        self.services = services if services is not None else Services()
        self.runner = AsyncRunner(self)
        self._closing = False
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.cerrar_aplicacion)
        self.crear_widgets()
        self.place_window_center()

    def crear_widgets(self):
        """Construye campos con etiquetas estables y feedback de conexión."""

        body = ttk.Frame(self, padding=35)
        body.pack(fill='both', expand=True)

        # Tk requiere una referencia a la imagen mientras el widget esté visible.
        self.logo = load_logo(self, (140, 140))
        ttk.Label(body, image=self.logo).pack(pady=(0, 20))
        ttk.Label(body, text='Usuario').pack(anchor='w')

        self.entry_usuario = ttk.Entry(body)
        self.entry_usuario.pack(fill='x', pady=(5, 15))
        ttk.Label(body, text='Contraseña').pack(anchor='w')

        self.entry_password = ttk.Entry(body, show='*')
        self.entry_password.pack(fill='x', pady=5)

        self.status = ttk.Label(body, text='', wraplength=370)
        self.status.pack(fill='x', pady=10)

        self.button = ttk.Button(
            body,
            text='Iniciar sesión',
            command=self.verificar_login,
        )
        self.button.pack(fill='x', pady=10)
        ttk.Button(body, text='¿Olvidaste tu contraseña?', bootstyle='link',
                   command=self.mostrar_recuperacion).pack()
        self.bind('<Return>', lambda event: self.verificar_login())

    def verificar_login(self):
        """Valida presencia; preserva contraseña y evita solicitudes repetidas."""

        if self._closing or str(self.button['state']) == 'disabled':
            return

        username = self.entry_usuario.get().strip()
        password = self.entry_password.get()

        if not username or not password:
            self.status.configure(text='Complete usuario y contraseña.')
            return

        self.button.configure(state='disabled')
        self.status.configure(text='Conectando…')
        self.runner.submit(self.services.auth.login(username, password), self,
                           lambda data: self._logged_in(username, data), self._failed)

    def _logged_in(self, username, data):
        """username: cuenta ingresada; data: respuesta validada con token y rol."""
        # El 200 valida credenciales, pero abrir la UI todavía puede fallar.
        # Mantener visible login hasta completar imports y construir la ventana.
        previous_children = set(self.winfo_children())
        self.services.api.set_token(data.access_token)

        try:
            from ui.sistema_gestion import SistemaGestion

            window = SistemaGestion(
                self, username, data.role, self.services, self.runner
            )
        except Exception:
            logging.exception('No se pudo abrir la ventana de gestión tras el login')
            self.services.api.set_token(None)

            # Una construcción interrumpida puede dejar un Toplevel parcial.
            for child in self.winfo_children():
                if child not in previous_children:
                    child.destroy()

            self.deiconify()
            self._failed(RuntimeError(
                'El login fue aceptado, pero no se pudo abrir la ventana. '
                'Revisa el error en la terminal del frontend.'
            ))
            return

        self.entry_password.delete(0, 'end')
        self.status.configure(text='')
        self.button.configure(state='normal')
        self.withdraw()
        # Dar foco después de ocultar login y de que Tk procese la nueva ventana.
        window.after_idle(window.bring_to_front)

    def _failed(self, error):
        """error: fallo de login; deja corregir credenciales o reintentar."""
        self.status.configure(text=str(error))
        self.button.configure(state='normal')

    def mostrar_recuperacion(self):
        """Informa el procedimiento actual; no existe recuperación automática."""
        from tkinter import messagebox
        messagebox.showinfo(
            'Recuperar cuenta',
            'Contacte al administrador para restablecer su cuenta.',
            parent=self,
        )

    def cerrar_aplicacion(self):
        """Cancela tareas y cierra HTTP antes de destruir la ventana principal."""

        if self._closing:
            return

        self._closing = True
        self.services.api.set_token(None)
        self.button.configure(state='disabled')
        self.status.configure(text='Cerrando…')
        self.runner.close(self.services.api.aclose(), self.destroy)
