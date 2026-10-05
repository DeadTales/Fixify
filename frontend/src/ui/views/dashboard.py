"""Dashboard con consultas concurrentes y métricas limitadas por rol."""
import asyncio
import ttkbootstrap as ttk
from ui.components import AsyncFrame, create_table


class DashboardView(AsyncFrame):
    """Muestra conteos sin confundir fallos de red con cero registros."""
    menu_label = 'Dashboard'
    allowed_roles = ('admin', 'recepcion', 'tecnico')
    menu_order = 0

    def __init__(self, master, services, runner, role):
        """Recibe dependencias comunes y solicita solo colecciones autorizadas."""
        super().__init__(master, services, runner, role)
        ttk.Label(
            self,
            text='Dashboard General',
            font=('Arial', 18, 'bold'),
        ).pack(anchor='w', pady=(0, 20))

        self.status = ttk.Label(self, text='Cargando…', wraplength=750)
        self.status.pack(fill='x', pady=10)

        cards = ttk.Frame(self)
        cards.pack(fill='x', pady=10)

        self.metrics = {}
        self.queries = []

        if role in ('admin', 'recepcion'):
            self.queries = [
                ('Equipos', services.equipment.listar),
                ('Clientes', services.clients.listar),
            ]

        if role == 'admin':
            self.queries.append(('Usuarios', services.users.listar))

        for index, (label, _) in enumerate(self.queries):
            card = ttk.Labelframe(cards, text=label, padding=15)
            card.grid(row=0, column=index, sticky='nsew', padx=5)
            cards.columnconfigure(index, weight=1)

            metric = ttk.Label(card, text='…', font=('Arial', 22, 'bold'))
            metric.pack()

            self.metrics[label] = metric

        if not self.queries:
            self.status.configure(text='Sesión de técnico activa. El módulo de órdenes asignadas está pendiente.')
            return

        self.table = create_table(
            self,
            ('Folio', 'Tipo', 'Marca', 'Modelo', 'Problema', 'ID Cliente'),
            height=8,
        )
        self.request(self._fetch, on_success=self._loaded)

    async def _fetch(self):
        """Consulta métricas en paralelo; conserva errores independientes."""
        return await asyncio.gather(
            *(fetch() for _, fetch in self.queries),
            return_exceptions=True,
        )

    def _loaded(self, results):
        """results: una lista o error por métrica; muestra fallos sin ocultarlos."""

        errors = []

        for (label, _), result in zip(self.queries, results):
            if isinstance(result, Exception):
                self.metrics[label].configure(text='No disponible')
                errors.append(f'{label}: {result}')
                continue

            self.metrics[label].configure(text=str(len(result)))

            if label == 'Equipos':
                for equipment in sorted(result, key=lambda eq: eq.id, reverse=True)[:8]:
                    self.table.insert(
                        '',
                        'end',
                        values=(
                            f"EQ-{equipment.id:03d}",
                            equipment.tipo,
                            equipment.marca,
                            equipment.modelo,
                            equipment.problema_reportado,
                            equipment.client_id,
                        ),
                    )

        self.status.configure(text='\n'.join(errors) or 'Datos actualizados. Equipos ordenados por ID descendente.')

    def _failed(self, error):
        """error: fallo general del dashboard; mantiene la ventana utilizable."""
        self.status.configure(text=str(error))
