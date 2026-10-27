"""Catálogo, alertas y consumo de materiales por orden."""
import asyncio
from tkinter import messagebox

import ttkbootstrap as ttk

from ui.components import AsyncFrame, Field, FormDialog, create_table


MATERIAL_FIELDS = (
    Field('clave', 'Clave (opcional)', required=False),
    Field('descripcion', 'Descripción'),
    Field('unidad', 'Unidad (opcional)', required=False),
    Field('existencia_actual', 'Existencia actual'),
    Field('stock_minimo', 'Stock mínimo'),
)


class InventoryView(AsyncFrame):
    """Presenta existencias y concentra mutaciones en diálogos pequeños."""

    menu_label = 'Inventario'
    allowed_roles = ('admin', 'recepcion', 'tecnico')
    menu_order = 40

    def __init__(self, master, services, runner, role):
        super().__init__(master, services, runner, role)
        self.records = []
        self.alert_records = []
        self._dialog = None
        self._loading = False

        ttk.Label(self, text='Inventario y refacciones', font=('Arial', 18, 'bold')).pack(
            anchor='w', pady=(0, 12)
        )
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', pady=(0, 10))
        self.refresh = ttk.Button(toolbar, text='Actualizar', command=self.load)
        self.refresh.pack(side='left')
        if role == 'admin':
            ttk.Button(toolbar, text='+ Material', bootstyle='success', command=self.open_create).pack(
                side='right'
            )
            ttk.Button(toolbar, text='Editar', bootstyle='warning', command=self.open_edit).pack(
                side='right', padx=8
            )
        if role in ('admin', 'tecnico'):
            ttk.Button(
                toolbar, text='Registrar consumo', bootstyle='primary',
                command=self.open_consumption,
            ).pack(side='right', padx=8)

        filters = ttk.Frame(self)
        filters.pack(fill='x', pady=(0, 10))
        ttk.Label(filters, text='Buscar').pack(side='left')
        self.search = ttk.StringVar()
        ttk.Entry(filters, textvariable=self.search).pack(side='left', fill='x', expand=True, padx=10)
        self.only_low = ttk.BooleanVar(value=False)
        ttk.Checkbutton(filters, text='Solo stock bajo', variable=self.only_low,
                        command=self._render).pack(side='right')
        self.search.trace_add('write', lambda *_: self._render())

        self.status = ttk.Label(self, text='Cargando…', wraplength=750)
        self.status.pack(fill='x', pady=(0, 8))
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)
        materials_tab = ttk.Frame(notebook)
        alerts_tab = ttk.Frame(notebook)
        notebook.add(materials_tab, text='Existencias')
        notebook.add(alerts_tab, text='Historial de alertas')
        self.table = create_table(
            materials_tab,
            ('ID', 'Clave', 'Descripción', 'Unidad', 'Existencia', 'Mínimo', 'Estado'),
        )
        self.table.tag_configure('low', background='#ffe7e7', foreground='#8a1c1c')
        self.alerts = create_table(
            alerts_tab,
            ('Fecha', 'Material', 'Descripción', 'Existencia', 'Mínimo'),
        )
        self.load()

    async def _fetch(self):
        return await asyncio.gather(
            self.services.inventory.listar(),
            self.services.inventory.alertas(),
            return_exceptions=True,
        )

    def load(self):
        if self._loading:
            return
        self._loading = True
        self.refresh.configure(state='disabled')
        self.status.configure(text='Actualizando inventario…')
        self.request(self._fetch, on_success=self._loaded, on_error=self._failed_load)

    def _loaded(self, results):
        self._loading = False
        self.refresh.configure(state='normal')
        errors = []
        if isinstance(results[0], Exception):
            errors.append(f'Existencias: {results[0]}')
        else:
            self.records = results[0]
        if isinstance(results[1], Exception):
            errors.append(f'Alertas: {results[1]}')
        else:
            self.alert_records = results[1]
        self._render()
        self._render_alerts()
        if errors:
            self.status.configure(text='\n'.join(errors))

    def _failed_load(self, error):
        self._loading = False
        self.refresh.configure(state='normal')
        self.status.configure(text=str(error))

    def _render(self):
        term = self.search.get().strip().casefold()
        for item in self.table.get_children():
            self.table.delete(item)
        visible = 0
        for index, record in enumerate(self.records):
            values = (
                record.id_material, record.clave or '-', record.descripcion, record.unidad or '-',
                record.existencia_actual, record.stock_minimo,
                'Stock bajo' if record.bajo_stock else 'Disponible',
            )
            if self.only_low.get() and not record.bajo_stock:
                continue
            if term and not any(term in str(value).casefold() for value in values):
                continue
            self.table.insert('', 'end', iid=str(index), values=values,
                              tags=('low',) if record.bajo_stock else ('even' if visible % 2 == 0 else 'odd',))
            visible += 1
        low = sum(record.bajo_stock for record in self.records)
        self.status.configure(text=f'{visible} de {len(self.records)} materiales · {low} con stock bajo')

    def _render_alerts(self):
        for item in self.alerts.get_children():
            self.alerts.delete(item)
        for index, alert in enumerate(self.alert_records):
            self.alerts.insert('', 'end', values=(
                (alert.fecha_alerta.astimezone().strftime('%d/%m/%Y %H:%M')
                 if alert.fecha_alerta else '-'),
                alert.id_material, alert.material_descripcion or '-',
                alert.existencia_actual, alert.stock_minimo,
            ), tags=('even' if index % 2 == 0 else 'odd',))

    def selected(self):
        selection = self.table.selection()
        if not selection:
            self.status.configure(text='Seleccione un material de la tabla.')
            return None
        return self.records[int(selection[0])]

    def _open(self, title, fields, save, callback, initial=None):
        if self._dialog is not None and self._dialog.winfo_exists():
            self._dialog.lift()
            return
        self._dialog = FormDialog(self, title, fields, self.runner, save, callback, initial=initial)

    def open_create(self):
        self._open('Registrar material', MATERIAL_FIELDS,
                   lambda values: self.services.inventory.crear(**values), self._saved)

    def open_edit(self):
        record = self.selected()
        if record is None:
            return
        initial = record.model_dump()
        self._open(
            'Editar material', MATERIAL_FIELDS,
            lambda values: self.services.inventory.editar(record.id_material, **values),
            self._saved, initial,
        )

    def open_consumption(self):
        record = self.selected()
        initial = {'id_material': record.id_material} if record else None
        self._open(
            'Consumo por orden',
            (Field('id_orden', 'ID de orden'), Field('id_material', 'ID de material'),
             Field('cantidad_utilizada', 'Cantidad utilizada')),
            lambda values: self.services.inventory.consumir(**values),
            self._consumed,
            initial,
        )

    def _saved(self, _result):
        messagebox.showinfo('Inventario', 'Material guardado correctamente.', parent=self)
        self.load()

    def _consumed(self, result):
        extra = f'\n{result.alerta_stock_bajo}' if result.alerta_stock_bajo else ''
        messagebox.showinfo('Consumo registrado', f'La existencia fue actualizada.{extra}', parent=self)
        self.load()
