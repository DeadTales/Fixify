"""Vista del flujo completo de recepción, reparación y entrega de órdenes."""
import asyncio
from datetime import date
from tkinter import messagebox

import ttkbootstrap as ttk

from models.orders import ESTADOS_ORDEN, Orden
from ui.components import AsyncFrame, Field, FormDialog, create_table


SIGUIENTE_ESTADO = {
    'Recibido': 'En revisión',
    'En revisión': 'Reparando',
    'Reparando': 'Listo',
    'Listo': 'Entregado',
}


def equipment_choices_for_client(devices, client_id):
    """Devuelve las etiquetas de equipos cuyo propietario es el cliente elegido."""
    return tuple(
        label for label, equipment in devices.items()
        if equipment.client_id == client_id
    )


class OrdersView(AsyncFrame):
    """Coordina órdenes mediante servicios; ningún callback realiza HTTP directo."""
    menu_label = 'Órdenes'
    allowed_roles = ('admin', 'recepcion', 'tecnico')
    menu_order = 15
    columns = (
        'Folio', 'Estado', 'ID Cliente', 'ID Equipo', 'ID Técnico',
        'Recepción', 'Entrega',
    )

    def __init__(self, master, services, runner, role):
        super().__init__(master, services, runner, role)
        self.records: list[Orden] = []
        self._dialog = None
        self._loading = False

        ttk.Label(self, text='Órdenes de Servicio',
                  font=('Arial', 18, 'bold')).pack(anchor='w', pady=(0, 12))
        self._build_filters()
        self._build_actions()
        self.status = ttk.Label(self, text='', wraplength=850)
        self.status.pack(fill='x', pady=(0, 8))
        self.table = create_table(self, self.columns)
        self.table.bind('<Double-1>', lambda _event: self.show_detail())
        self.load()

    def _build_filters(self):
        filters = ttk.Labelframe(self, text='Búsqueda y filtros', padding=8)
        filters.pack(fill='x', pady=(0, 10))
        self.folio_filter = ttk.StringVar()
        self.client_filter = ttk.StringVar()
        self.equipment_filter = ttk.StringVar()
        self.state_filter = ttk.StringVar(value='Todos')
        self.date_from = ttk.StringVar()
        self.date_to = ttk.StringVar()
        definitions = (
            ('Folio', self.folio_filter, 15),
            ('Cliente', self.client_filter, 20),
            ('Equipo', self.equipment_filter, 20),
        )
        for column, (label, variable, width) in enumerate(definitions):
            ttk.Label(filters, text=label).grid(row=0, column=column, sticky='w')
            ttk.Entry(filters, textvariable=variable, width=width).grid(
                row=1, column=column, padx=(0, 8), sticky='ew'
            )
        ttk.Label(filters, text='Estado').grid(row=0, column=3, sticky='w')
        ttk.Combobox(
            filters, textvariable=self.state_filter,
            values=('Todos', *ESTADOS_ORDEN), state='readonly', width=15,
        ).grid(row=1, column=3, padx=(0, 8))
        ttk.Label(filters, text='Desde').grid(row=2, column=0, sticky='w', pady=(8, 0))
        ttk.Entry(filters, textvariable=self.date_from, width=15).grid(
            row=3, column=0, padx=(0, 8), sticky='w'
        )
        ttk.Label(filters, text='Hasta').grid(row=2, column=1, sticky='w', pady=(8, 0))
        ttk.Entry(filters, textvariable=self.date_to, width=15).grid(
            row=3, column=1, padx=(0, 8), sticky='w'
        )
        ttk.Label(filters, text='Fechas: AAAA-MM-DD', bootstyle='secondary').grid(
            row=3, column=2, sticky='w'
        )
        ttk.Button(filters, text='Aplicar filtros', command=self.load).grid(
            row=3, column=3, sticky='e', padx=(0, 8)
        )
        ttk.Button(filters, text='Limpiar', bootstyle='secondary-outline',
                   command=self._clear_filters).grid(row=3, column=4, sticky='e')
        filters.columnconfigure(1, weight=1)
        filters.columnconfigure(2, weight=1)

    def _build_actions(self):
        bar = ttk.Frame(self)
        bar.pack(fill='x', pady=(0, 10))
        self.refresh = ttk.Button(bar, text='Actualizar', command=self.load)
        self.refresh.pack(side='left')
        if self.role in ('admin', 'recepcion'):
            ttk.Button(bar, text='+ Nueva orden', bootstyle='success',
                       command=self.open_create).pack(side='left', padx=(8, 0))
            ttk.Button(bar, text='Asignar técnico', bootstyle='info',
                       command=self.open_assign).pack(side='left', padx=(8, 0))
        if self.role in ('admin', 'tecnico'):
            for label, command, style in (
                ('Diagnóstico', self.open_diagnostic, 'secondary'),
                ('Actividad', self.open_activity, 'secondary'),
                ('Registrar solución', self.open_resolution, 'warning'),
                ('Avanzar estado', self.advance_state, 'primary'),
            ):
                ttk.Button(bar, text=label, command=command,
                           bootstyle=style).pack(side='left', padx=(8, 0))
        if self.role in ('admin', 'recepcion'):
            ttk.Button(bar, text='Entregar', command=self.deliver,
                       bootstyle='success-outline').pack(side='left', padx=(8, 0))
        ttk.Button(bar, text='Ver detalle', command=self.show_detail,
                   bootstyle='secondary-outline').pack(side='right')

    def load(self):
        if self._loading:
            return
        try:
            for value in (self.date_from.get(), self.date_to.get()):
                if value:
                    date.fromisoformat(value)
        except ValueError:
            self.status.configure(text='Use fechas con formato AAAA-MM-DD.')
            return
        filters = {
            'folio': self.folio_filter.get().strip(),
            'cliente': self.client_filter.get().strip(),
            'equipo': self.equipment_filter.get().strip(),
            'estado': None if self.state_filter.get() == 'Todos' else self.state_filter.get(),
            'fecha_desde': self.date_from.get().strip(),
            'fecha_hasta': self.date_to.get().strip(),
        }
        self._loading = True
        self.refresh.configure(state='disabled')
        self.status.configure(text='Cargando órdenes…')
        self.request(self.services.orders.listar, on_success=self._loaded,
                     on_error=self._load_failed, **filters)

    def _loaded(self, records):
        self._loading = False
        self.refresh.configure(state='normal')
        self.records = records
        self._render()

    def _load_failed(self, error):
        self._loading = False
        self.refresh.configure(state='normal')
        self.status.configure(text=str(error))

    def _render(self):
        if not hasattr(self, 'table'):
            return
        for item in self.table.get_children():
            self.table.delete(item)
        for index, order in enumerate(self.records):
            self.table.insert('', 'end', iid=str(index), values=(
                order.folio or f'ORD-{order.id_orden:03d}', order.estado,
                order.id_cliente, order.id_equipo, order.id_tecnico or 'Sin asignar',
                self._format_date(order.fecha_recepcion), self._format_date(order.fecha_entrega),
            ), tags=('even' if index % 2 == 0 else 'odd',))
        self.status.configure(text=f'{len(self.records)} órdenes encontradas')

    @staticmethod
    def _format_date(value):
        return value[:16].replace('T', ' ') if value else '-'

    def _clear_filters(self):
        self.folio_filter.set('')
        self.client_filter.set('')
        self.equipment_filter.set('')
        self.state_filter.set('Todos')
        self.date_from.set('')
        self.date_to.set('')
        self.load()

    def selected(self):
        selected = self.table.selection()
        if not selected:
            self.status.configure(text='Seleccione una orden en la tabla.')
            return None
        return self.records[int(selected[0])]

    def _open_form(self, title, fields, save, initial=None):
        if self._dialog is not None and self._dialog.winfo_exists():
            self._dialog.lift()
            return
        self._dialog = FormDialog(
            self, title, fields, self.runner, save, self._saved, initial=initial,
        )

    def _saved(self, _result):
        messagebox.showinfo('Orden actualizada', 'La operación se guardó correctamente.', parent=self)
        self.load()

    def open_create(self):
        self.status.configure(text='Preparando clientes, equipos y técnicos…')
        self.request(self._creation_options, on_success=self._create_ready)

    async def _creation_options(self):
        clients, equipment = await asyncio.gather(
            self.services.clients.listar(), self.services.equipment.listar(),
        )
        try:
            technicians = await self.services.orders.listar_tecnicos()
        except Exception:
            technicians = []
        return clients, equipment, technicians

    def _create_ready(self, data):
        clients, equipment, technicians = data
        if not clients or not equipment:
            self.status.configure(text='Registre un cliente y su equipo antes de abrir una orden.')
            return
        owners = {f'[{c.id}] {c.nombre}': c.id for c in clients}
        devices = {
            f'[{e.id}] {e.tipo} {e.marca} {e.modelo} · cliente {e.client_id}': e
            for e in equipment
        }
        people = {'Sin asignar': None, **{
            f'[{u.id}] {u.username}': u.id for u in technicians if u.is_active
        }}
        first_client_label, first_client_id = next(
            (label, client_id)
            for label, client_id in owners.items()
            if equipment_choices_for_client(devices, client_id)
        )
        fields = (
            Field('cliente', 'Cliente', choices=tuple(owners)),
            Field(
                'equipo', 'Equipo',
                choices=equipment_choices_for_client(devices, first_client_id),
            ),
            Field('tecnico', 'Técnico', choices=tuple(people)),
        )
        async def save(values):
            client_id = owners[values['cliente']]
            device = devices[values['equipo']]
            if device.client_id != client_id:
                raise ValueError('El equipo seleccionado no pertenece al cliente indicado.')
            return await self.services.orders.crear(
                client_id, device.id, people[values['tecnico']],
            )
        self._open_form(
            'Nueva orden de servicio', fields, save,
            initial={'cliente': first_client_label},
        )
        dialog = self._dialog

        def filter_equipment(_event=None):
            client_id = owners.get(dialog.inputs['cliente'].get())
            choices = equipment_choices_for_client(devices, client_id)
            has_equipment = dialog.set_choices('equipo', choices)
            dialog.button.configure(state='normal' if has_equipment else 'disabled')
            dialog.status.configure(
                text='' if has_equipment else 'El cliente seleccionado no tiene equipos registrados.'
            )

        dialog.inputs['cliente'].bind('<<ComboboxSelected>>', filter_equipment, add='+')
        filter_equipment()

    def open_assign(self):
        order = self.selected()
        if order is None:
            return
        self.request(self.services.orders.listar_tecnicos,
                     on_success=lambda users: self._assign_ready(order, users))

    def _assign_ready(self, order, users):
        choices = {f'[{u.id}] {u.username}': u.id for u in users if u.is_active}
        if not choices:
            self.status.configure(text='No hay técnicos activos disponibles.')
            return
        async def save(values):
            return await self.services.orders.asignar(order.id_orden, choices[values['tecnico']])
        self._open_form(f'Asignar {order.folio}',
                        (Field('tecnico', 'Técnico', choices=tuple(choices)),), save)

    def open_diagnostic(self):
        order = self.selected()
        if order:
            self.status.configure(text='Consultando diagnóstico actual…')
            self.request(
                self.services.orders.obtener_diagnostico,
                order.id_orden,
                on_success=lambda current: self._diagnostic_ready(order, current),
                on_error=lambda error: self._diagnostic_failed(order, error),
            )

    def _diagnostic_failed(self, order, error):
        if getattr(error, 'status_code', None) == 404:
            self._diagnostic_ready(order, None)
        else:
            self._failed(error)

    def _diagnostic_ready(self, order, current):
        async def save(values):
            return await self.services.orders.diagnosticar(order.id_orden, values['descripcion'])
        self._open_form(
            f'Diagnóstico de {order.folio}',
            (Field('descripcion', 'Descripción del diagnóstico'),),
            save,
            {'descripcion': current.descripcion} if current else None,
        )

    def open_activity(self):
        order = self.selected()
        if order:
            async def save(values):
                return await self.services.orders.registrar_actividad(order.id_orden, **values)
            self._open_form(f'Actividad en {order.folio}', (
                Field('trabajo_realizado', 'Trabajo realizado'),
                Field('solucion', 'Resultado parcial (opcional)', required=False),
            ), save)

    def open_resolution(self):
        order = self.selected()
        if order:
            async def save(values):
                return await self.services.orders.resolver(
                    order.id_orden, values['causa'], values['acciones'], 'Listo',
                )
            self._open_form(f'Solución final de {order.folio}', (
                Field('causa', 'Causa identificada'),
                Field('acciones', 'Acciones y solución final'),
            ), save)

    def advance_state(self):
        order = self.selected()
        if order is None:
            return
        target = SIGUIENTE_ESTADO.get(order.estado)
        if target is None:
            self.status.configure(text='La orden ya está entregada.')
            return
        if order.id_tecnico is None:
            self.status.configure(text='Asigne un técnico antes de avanzar el estado.')
            return
        if messagebox.askyesno('Avanzar estado',
                               f'¿Cambiar {order.folio} de {order.estado} a {target}?', parent=self):
            self.request(self.services.orders.cambiar_estado, order.id_orden, target,
                         on_success=self._saved)

    def deliver(self):
        order = self.selected()
        if order is None:
            return
        if order.estado != 'Listo':
            self.status.configure(text='Solo puede entregarse una orden en estado Listo.')
            return
        if messagebox.askyesno('Registrar entrega',
                               f'¿Confirmar la entrega de {order.folio}?', parent=self):
            self.request(self.services.orders.entregar, order.id_orden, on_success=self._saved)

    def show_detail(self):
        order = self.selected()
        if order:
            self.status.configure(text='Cargando expediente de la orden…')
            self.request(self._detail_bundle, order.id_orden, on_success=self._show_detail)

    async def _detail_bundle(self, order_id):
        detail = await self.services.orders.detalle(order_id)
        diagnosis, activities = await asyncio.gather(
            self.services.orders.obtener_diagnostico(order_id),
            self.services.orders.listar_actividades(order_id),
            return_exceptions=True,
        )
        return detail, diagnosis, activities

    def _show_detail(self, bundle):
        detail, diagnosis, activities = bundle
        order = detail.orden
        history = '\n'.join(
            f'• {item.estado_anterior or "Inicio"} → {item.estado_nuevo} '
            f'({self._format_date(item.fecha_cambio)})'
            for item in detail.historial
        ) or 'Sin cambios registrados.'
        assignments = '\n'.join(
            f'• {item.id_tecnico_anterior or "Sin asignar"} → '
            f'{item.id_tecnico_nuevo} · usuario {item.id_usuario} '
            f'({self._format_date(item.fecha_cambio)})'
            for item in detail.asignaciones
        ) or 'Sin asignaciones registradas.'
        if isinstance(diagnosis, Exception):
            diagnosis_text = (
                'Sin diagnóstico registrado.'
                if getattr(diagnosis, 'status_code', None) == 404
                else f'No disponible: {diagnosis}'
            )
        else:
            diagnosis_text = diagnosis.descripcion
        if isinstance(activities, Exception):
            activities_text = f'No disponibles: {activities}'
        else:
            activities_text = '\n'.join(
                f'• {item.trabajo_realizado}' +
                (f' — {item.solucion}' if item.solucion else '')
                for item in activities
            ) or 'Sin actividades registradas.'
        messagebox.showinfo('Detalle de orden',
            f'Folio: {order.folio}\nEstado: {order.estado}\n'
            f'Cliente: {order.id_cliente}\nEquipo: {order.id_equipo}\n'
            f'Técnico: {order.id_tecnico or "Sin asignar"}\n'
            f'Diagnóstico: {diagnosis_text}\n'
            f'Causa: {order.causa or "-"}\nSolución: {order.acciones or "-"}\n\n'
            f'Actividades:\n{activities_text}\n\n'
            f'Historial de estados:\n{history}\n\n'
            f'Historial de asignaciones:\n{assignments}', parent=self)
