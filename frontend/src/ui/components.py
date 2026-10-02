"""Controles reutilizables para tablas, formularios y solicitudes asíncronas."""
from dataclasses import dataclass
from tkinter import messagebox
import ttkbootstrap as ttk
from models.base import Mensaje
from models.equipment import EquipoRegistrado


@dataclass(frozen=True)
class Field:
    """name: clave API; label: texto; required: obligatorio; secret: contraseña; choices: opciones."""
    name: str
    label: str
    required: bool = True
    secret: bool = False
    choices: tuple = ()


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


def create_table(parent, columns, height=12):
    """parent: contenedor; columns: encabezados; height: filas visibles; retorna Treeview."""
    frame = ttk.Frame(parent)
    frame.pack(fill='both', expand=True)
    table = ttk.Treeview(frame, columns=columns, show='headings', height=height)
    for column in columns:
        table.heading(column, text=column)
        table.column(column, anchor='center', width=130)
    scroll = ttk.Scrollbar(frame, orient='vertical', command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    table.pack(side='left', fill='both', expand=True)
    scroll.pack(side='right', fill='y')
    return table


class FormDialog(ttk.Toplevel):
    """Formulario genérico con validación de campos requeridos y guardado async."""

    def __init__(self, master, title, fields, runner, save, on_saved):
        """master: vista; title: título; fields: campos; runner: tareas; save/on_saved: guardar/confirmar."""
        super().__init__(master)
        self.runner, self.save, self.on_saved = runner, save, on_saved
        self.fields, self.inputs = fields, {}
        self.title(title)
        self.resizable(False, False)
        body = ttk.Frame(self, padding=20)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=title, font=('Arial', 14, 'bold')).pack(pady=(0, 15))
        for field in fields:
            ttk.Label(body, text=field.label).pack(anchor='w', pady=(5, 0))
            if field.choices:
                widget = ttk.Combobox(body, values=field.choices, state='readonly', width=38)
                widget.current(0)
            else:
                widget = ttk.Entry(body, width=40, show='*' if field.secret else '')
            widget.pack(fill='x', pady=5)
            self.inputs[field.name] = widget
        self.status = ttk.Label(body, text='', wraplength=350)
        self.status.pack(fill='x', pady=5)
        self.button = ttk.Button(body, text='Guardar', bootstyle='success', command=self._submit)
        self.button.pack(pady=(10, 0))
        self.transient(master.winfo_toplevel())
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.update_idletasks()
        self.place_window_center()

    def _submit(self):
        """Lee controles en Tk; conserva espacios de contraseñas y evita doble envío."""
        values = {f.name: self.inputs[f.name].get() if f.secret
                  else self.inputs[f.name].get().strip() for f in self.fields}
        missing = [f.label for f in self.fields if f.required and not values[f.name]]
        if missing:
            self.status.configure(text='Complete: ' + ', '.join(missing))
            return
        self.button.configure(state='disabled')
        self.status.configure(text='Guardando…')
        self.runner.submit(self.save(values), self, self._saved, self._failed)

    def _saved(self, result):
        """result: respuesta API; notifica al módulo y cierra el formulario."""
        self.on_saved(result)
        self.destroy()

    def _failed(self, error):
        """error: fallo de solicitud; permite corregir y reintentar."""
        self.status.configure(text=str(error))
        self.button.configure(state='normal')

    def destroy(self):
        """Cancela el guardado pendiente y evita callbacks sobre un modal cerrado."""
        self.runner.cancel_owner(self)
        super().destroy()


class CollectionView(AsyncFrame):
    """Comparte listado, recarga, alta y estados visuales entre módulos."""
    title = ''
    columns = ()
    fields = ()

    def __init__(self, master, services, runner, role):
        """Recibe dependencias comunes; cada subclase define columnas y operaciones."""
        super().__init__(master, services, runner, role)
        self.records = []
        self._load_future = None
        self._dialog = None
        ttk.Label(self, text=self.title, font=('Arial', 18, 'bold')).pack(anchor='w', pady=(0, 15))
        bar = ttk.Frame(self)
        bar.pack(fill='x', pady=(0, 10))
        self.refresh = ttk.Button(bar, text='Actualizar', command=self.load)
        self.refresh.pack(side='left')
        self.create = ttk.Button(bar, text='+ Nuevo', bootstyle='success', command=self.open_form)
        self.create.pack(side='right')
        self.status = ttk.Label(self, text='', wraplength=750)
        self.status.pack(fill='x', pady=(0, 10))
        self.table = create_table(self, self.columns)
        self.load()

    async def fetch(self):
        """Retorna registros; la subclase elige su service."""
        raise NotImplementedError

    async def save(self, values):
        """values: campos del formulario; la subclase llama al service de alta."""
        raise NotImplementedError

    def row(self, record):
        """record: entidad API; la subclase la convierte a valores de tabla."""
        raise NotImplementedError

    def load(self):
        """Consulta sin bloquear; asyncio no detecta cambios remotos automáticamente."""
        if self._load_future is not None:
            self._load_future.cancel()
        self.refresh.configure(state='disabled')
        self.status.configure(text='Cargando…')
        self._load_future = self.runner.submit(self.fetch(), self, self._loaded, self._failed)

    def _loaded(self, records):
        """records: lista validada; reemplaza filas y actualiza estado."""
        self.records = records
        for item in self.table.get_children():
            self.table.delete(item)
        for index, record in enumerate(records):
            self.table.insert('', 'end', iid=str(index), values=self.row(record))
        self.status.configure(text=f'{len(records)} registros')
        self.refresh.configure(state='normal')

    def _failed(self, error):
        """error: fallo visible; conserva datos anteriores y habilita reintento."""
        self.status.configure(text=str(error))
        self.refresh.configure(state='normal')

    def open_form(self):
        """Abre el formulario común con los campos del módulo."""
        if self._dialog is not None and self._dialog.winfo_exists():
            self._dialog.lift()
            return
        self._dialog = FormDialog(self, self.title, self.fields, self.runner, self.save, self._created)

    def _created(self, result: Mensaje):
        """result: confirmación de alta; informa y vuelve a consultar registros."""
        folio = result.folio if isinstance(result, EquipoRegistrado) else None
        messagebox.showinfo('Registro guardado', f'Guardado correctamente. Folio: {folio}'
                            if folio else 'Guardado correctamente.', parent=self)
        # load cancela solo la lectura previa; no interrumpe otras escrituras.
        self.load()
