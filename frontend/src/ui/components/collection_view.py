"""Comparte listado, recarga, alta y estados visuales entre módulos."""
from tkinter import messagebox
import ttkbootstrap as ttk
from models.base import Mensaje
from models.equipment import EquipoRegistrado
from .async_frame import AsyncFrame
from .form_dialog import FormDialog
from .table import create_table


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
