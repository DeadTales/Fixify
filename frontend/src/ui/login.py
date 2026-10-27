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
        super().__init__(title='Fixify — Iniciar sesión', themename='litera', size=(480, 640))
        self.style.configure('TButton', padding=(14, 9))
        self.style.configure('Login.TEntry', padding=(10, 8), font=('Segoe UI', 10))
        self.style.configure('Treeview', rowheight=34, font=('DejaVu Sans', 10))
        self.style.configure('Treeview.Heading', font=('DejaVu Sans', 10, 'bold'), padding=10)
        set_window_icon(self)

        self.services = services if services is not None else Services()
        self.runner = AsyncRunner(self)
        self._closing = False
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.cerrar_aplicacion)
        self.crear_widgets()
        self._fit_to_content()
        self.place_window_center()

    def crear_widgets(self):
        """Construye campos con etiquetas estables y feedback de conexión."""

        accent = ttk.Frame(self, height=6, bootstyle='primary')
        accent.pack(fill='x')
        accent.pack_propagate(False)

        body = ttk.Frame(self, padding=(42, 18, 42, 16))
        body.pack(fill='both', expand=True)

        # Tk requiere una referencia a la imagen mientras el widget esté visible.
        self.logo = load_logo(self, (108, 108))
        ttk.Label(body, image=self.logo).pack(pady=(0, 8))
        ttk.Label(
            body,
            text='Bienvenido a Fixify',
            font=('Segoe UI', 22, 'bold'),
        ).pack(pady=(0, 4))
        ttk.Label(
            body,
            text='Administra servicios, reparaciones e inventario.',
            bootstyle='secondary',
            font=('Segoe UI', 10),
            justify='center',
            wraplength=360,
        ).pack(pady=(0, 16))

        form = ttk.Frame(body)
        form.pack(fill='x')

        ttk.Label(form, text='Usuario', font=('Segoe UI', 10, 'bold')).pack(anchor='w')

        self.entry_usuario = ttk.Entry(form, style='Login.TEntry')
        self.entry_usuario.pack(fill='x', pady=(4, 12))
        ttk.Label(form, text='Contraseña', font=('Segoe UI', 10, 'bold')).pack(anchor='w')

        self.entry_password = ttk.Entry(form, show='*', style='Login.TEntry')
        self.entry_password.pack(fill='x', pady=(4, 5))

        options = ttk.Frame(form)
        options.pack(fill='x')
        self.show_password = ttk.BooleanVar(value=False)
        ttk.Checkbutton(
            options,
            text='Mostrar contraseña',
            variable=self.show_password,
            command=lambda: self.entry_password.configure(
                show='' if self.show_password.get() else '*'
            ),
        ).pack(side='left')
        ttk.Button(
            options,
            text='¿Olvidaste tu contraseña?',
            bootstyle='link',
            command=self.mostrar_recuperacion,
        ).pack(side='right')
        self.entry_usuario.focus_set()

        self.status = ttk.Label(
            form,
            text='',
            bootstyle='secondary',
            justify='left',
            wraplength=380,
        )
        self.status.pack(fill='x', pady=(8, 5))

        self.button = ttk.Button(
            form,
            text='Iniciar sesión',
            bootstyle='primary',
            command=self.verificar_login,
        )
        self.button.pack(fill='x', pady=(0, 11))

        divider = ttk.Frame(form)
        divider.pack(fill='x', pady=(0, 10))
        ttk.Separator(divider).pack(side='left', fill='x', expand=True, padx=(0, 10))
        ttk.Label(
            divider,
            text='ACCESO PARA CLIENTES',
            bootstyle='secondary',
            font=('Segoe UI', 8, 'bold'),
        ).pack(side='left')
        ttk.Separator(divider).pack(side='left', fill='x', expand=True, padx=(10, 0))

        ttk.Button(
            form,
            text='Consultar mi reparación',
            bootstyle='primary-outline',
            command=self.mostrar_consulta,
        ).pack(fill='x')

        ttk.Label(
            body,
            text='Sistema de gestión de mantenimiento',
            bootstyle='secondary',
            font=('Segoe UI', 8),
        ).pack(side='bottom', pady=(12, 0))
        self.bind('<Return>', lambda event: self.verificar_login())

    def _fit_to_content(self):
        """Ajusta la ventana al contenido sin rebasar el área visible."""

        self.update_idletasks()
        screen_margin = 80
        width = min(max(480, self.winfo_reqwidth()), self.winfo_screenwidth() - screen_margin)
        height = min(max(620, self.winfo_reqheight()), self.winfo_screenheight() - screen_margin)
        self.geometry(f'{width}x{height}')

    def verificar_login(self):
        """Valida presencia; preserva contraseña y evita solicitudes repetidas."""

        if self._closing or str(self.button['state']) == 'disabled':
            return

        username = self.entry_usuario.get().strip()
        password = self.entry_password.get()

        if not username or not password:
            self.status.configure(
                text='Complete usuario y contraseña.',
                bootstyle='warning',
            )
            return

        self.button.configure(state='disabled')
        self.status.configure(text='Verificando credenciales…', bootstyle='secondary')
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
        self.status.configure(text='', bootstyle='secondary')
        self.button.configure(state='normal')
        self.withdraw()
        # Dar foco después de ocultar login y de que Tk procese la nueva ventana.
        window.after_idle(window.bring_to_front)

    def _failed(self, error):
        """error: fallo de login; deja corregir credenciales o reintentar."""
        self.status.configure(text=str(error), bootstyle='danger')
        self.button.configure(state='normal')

    def mostrar_recuperacion(self):
        """Informa el procedimiento actual; no existe recuperación automática."""
        from tkinter import messagebox
        messagebox.showinfo(
            'Recuperar cuenta',
            'Contacte al administrador para restablecer su cuenta.',
            parent=self,
        )

    def mostrar_consulta(self):
        """Abre la consulta pública usando el mismo transporte asíncrono."""
        from ui.consultation import ConsultationDialog

        ConsultationDialog(self, self.services.consultation, self.runner)

    def cerrar_aplicacion(self):
        """Cancela tareas y cierra HTTP antes de destruir la ventana principal."""

        if self._closing:
            return

        self._closing = True
        self.services.api.set_token(None)
        self.button.configure(state='disabled')
        self.status.configure(text='Cerrando…', bootstyle='secondary')
        self.runner.close(self.services.api.aclose(), self.destroy)
