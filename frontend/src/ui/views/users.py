"""Vista de administración de cuentas y roles."""
from tkinter import messagebox
import ttkbootstrap as ttk
from ui.components import CollectionView, Field, FormDialog
from models.users import Usuario

ROLES = {'Administrador': 'admin', 'Técnico': 'tecnico', 'Recepción': 'recepcion'}


class UsersView(CollectionView):
    """Permite altas y cambios de acceso sobre el usuario seleccionado."""
    menu_label = 'Usuarios'
    allowed_roles = ('admin',)
    menu_order = 30
    service_name = 'users'
    title = 'Administración de Usuarios'
    columns = ('ID', 'Usuario', 'Rol', 'Estado')
    fields = (
        Field('username', 'Usuario (mín. 4 caracteres)'),
        Field('password', 'Contraseña (mín. 6 caracteres)', secret=True),
        Field('role', 'Rol', choices=tuple(ROLES)),
    )

    def __init__(self, master, services, runner, role):
        """Recibe dependencias comunes y agrega acciones administrativas."""
        super().__init__(master, services, runner, role)

        self.edit_button = ttk.Button(self.action_bar, text='Editar usuario', bootstyle='warning',
                                      command=self.edit_selected)
        self.edit_button.pack(side='left', padx=(10, 0))
        self.access_button = ttk.Button(self.action_bar, text='Desactivar usuario', bootstyle='danger',
                                        command=self.toggle_active)
        self.access_button.pack(side='left', padx=(10, 0))
        self.action_buttons = [self.edit_button, self.access_button]
        self.table.bind('<<TreeviewSelect>>', self._selection_changed)

    def _selection_changed(self, event=None):
        selected = self.table.selection()
        user = self.records[int(selected[0])] if selected else None
        active = user is None or user.is_active
        self.access_button.configure(text='Desactivar usuario' if active else 'Activar usuario',
                                     bootstyle='danger' if active else 'success')

    def edit_selected(self):
        if self._mutating:
            return
        user = self._selected()
        if user is None:
            return
        if self._dialog is not None and self._dialog.winfo_exists():
            self._dialog.lift()
            return
        role_label = next(label for label, code in ROLES.items() if code == user.role)
        async def save(values):
            return await self.services.users.editar(user.id, values['username'], ROLES[values['role']])
        self._dialog = FormDialog(self, f'Editar usuario: {user.username}',
            (Field('username', 'Usuario (mín. 4 caracteres)'), Field('role', 'Rol', choices=tuple(ROLES))),
            self.runner, save, self._edited, initial={'username': user.username, 'role': role_label})

    async def fetch(self):
        """Consulta personal autorizado para administración."""
        return await self.services.users.listar()

    async def save(self, values):
        """values: credenciales y etiqueta de rol; convierte esta al valor API."""
        return await self.services.users.crear(**{**values, 'role': ROLES[values['role']]})

    def row(self, record: Usuario):
        """record: usuario API; muestra estado legible sin datos de contraseña."""
        return (record.id, record.username, record.role, 'Activo' if record.is_active else 'Inactivo')

    def _selected(self):
        """Retorna el registro seleccionado o informa que falta selección."""

        selected = self.table.selection()

        if not selected:
            self.status.configure(text='Seleccione un usuario en la tabla.')
            return None

        return self.records[int(selected[0])]

    def toggle_active(self):
        """Alterna acceso sin eliminar el historial del usuario."""

        if self._mutating:
            return
        if self._dialog is not None and self._dialog.winfo_exists():
            self.status.configure(text='Cierre el formulario antes de cambiar el acceso.')
            return
        user = self._selected()

        if user and messagebox.askyesno(
            'Desactivar usuario' if user.is_active else 'Activar usuario',
            f"¿{'Desactivar' if user.is_active else 'Activar'} la cuenta {user.username}?",
            parent=self,
        ):
            self._update(self.services.users.activar, user.id, not user.is_active)

    def _update(self, operation, *args):
        """operation: método async; args: datos; bloquea acciones repetidas."""

        self._mutating = True
        if self._load_future is not None:
            self._load_future.cancel()

        for button in [self.refresh, self.create, *self.action_buttons]:
            button.configure(state='disabled')

        self.status.configure(text='Actualizando cuenta…')
        self.request(
            operation,
            *args,
            on_success=self._updated,
            on_error=self._update_failed,
        )

    def _updated(self, result):
        """result: respuesta API; restaura acciones y recarga cuentas."""

        self._mutating = False
        for button in [self.create, *self.action_buttons]:
            button.configure(state='normal')

        self.load()

    def _update_failed(self, error):
        """error: fallo; permite reintentar sin ocultar la causa."""

        self._mutating = False
        for button in [self.create, *self.action_buttons]:
            button.configure(state='normal')

        self._failed(error)
