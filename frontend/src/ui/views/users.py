"""Vista de administración de cuentas y roles."""
from tkinter import messagebox
import ttkbootstrap as ttk
from ui.components import CollectionView, Field
from models.users import Usuario

ROLES = {'Administrador': 'admin', 'Técnico': 'tecnico', 'Recepción': 'recepcion'}


class UsersView(CollectionView):
    """Permite altas y cambios de acceso sobre el usuario seleccionado."""
    title = 'Administración de Usuarios'
    columns = ('ID', 'Usuario', 'Rol', 'Estado')
    fields = (Field('username', 'Usuario (mín. 4 caracteres)'),
              Field('password', 'Contraseña (mín. 6 caracteres)', secret=True),
              Field('role', 'Rol', choices=tuple(ROLES)))

    def __init__(self, master, services, runner, role):
        """Recibe dependencias comunes y agrega acciones administrativas."""
        super().__init__(master, services, runner, role)
        actions = ttk.Frame(self)
        actions.pack(fill='x', pady=10)
        self.role_input = ttk.Combobox(actions, values=tuple(ROLES), state='readonly', width=18)
        self.role_input.set('Técnico')
        self.role_input.pack(side='left', padx=(0, 10))
        self.action_buttons = []
        for label, callback in (('Cambiar rol', self.change_role),
                                ('Activar / Desactivar', self.toggle_active)):
            button = ttk.Button(actions, text=label, command=callback)
            button.pack(side='left', padx=5)
            self.action_buttons.append(button)

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

    def change_role(self):
        """Solicita cambio al rol seleccionado para la cuenta elegida."""
        user = self._selected()
        if user and messagebox.askyesno('Cambiar rol', '¿Cambiar el rol de esta cuenta?', parent=self):
            self._update(self.services.users.cambiar_rol(user.id, ROLES[self.role_input.get()]))

    def toggle_active(self):
        """Alterna acceso sin eliminar el historial del usuario."""
        user = self._selected()
        if user and messagebox.askyesno('Cambiar acceso', '¿Cambiar el acceso de esta cuenta?', parent=self):
            self._update(self.services.users.activar(user.id, not user.is_active))

    def _update(self, coroutine):
        """coroutine: actualización administrativa; bloquea acciones repetidas."""
        if self._load_future is not None:
            self._load_future.cancel()
        for button in [self.refresh, self.create, *self.action_buttons]:
            button.configure(state='disabled')
        self.status.configure(text='Actualizando cuenta…')
        self.runner.submit(coroutine, self, self._updated, self._update_failed)

    def _updated(self, result):
        """result: respuesta API; restaura acciones y recarga cuentas."""
        for button in [self.create, *self.action_buttons]:
            button.configure(state='normal')
        self.load()

    def _update_failed(self, error):
        """error: fallo; permite reintentar sin ocultar la causa."""
        for button in [self.create, *self.action_buttons]:
            button.configure(state='normal')
        self._failed(error)
