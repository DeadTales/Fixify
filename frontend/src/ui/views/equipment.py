"""Vista de equipos con selección asíncrona de clientes existentes."""
from ui.components import CollectionView, Field, FormDialog
from models.equipment import Equipo
from models.clients import Cliente


class EquipmentView(CollectionView):
    """Reutiliza la tabla y prepara el selector de propietario antes del alta."""
    menu_label = 'Equipos'
    allowed_roles = ('admin', 'recepcion')
    menu_order = 10
    editable = True
    service_name = 'equipment'
    title = 'Gestión de Equipos'
    columns = ('Folio', 'Tipo', 'Marca', 'Modelo', 'Nº Serie', 'Problema', 'ID Cliente')

    async def fetch(self):
        """Consulta los equipos disponibles mediante su service."""
        return await self.services.equipment.listar()

    def row(self, record: Equipo):
        """record: equipo API; formatea su identificador visual."""
        return (f"EQ-{record.id:03d}", record.tipo, record.marca, record.modelo,
                record.numero_serie or '-', record.problema_reportado, record.client_id)

    def edit_selected(self):
        if self._mutating:
            return
        record = self.selected_record()
        if record is not None:
            self._prepare_form(record)

    def open_form(self):
        self._prepare_form(None)

    def _prepare_form(self, record):
        """Carga propietarios sin detener Tk; evita consultas duplicadas."""

        if getattr(self, '_preparing', False):
            return
        if self._dialog is not None and self._dialog.winfo_exists():
            self._dialog.lift()
            return

        self._preparing = True
        self.create.configure(state='disabled')
        self.status.configure(text='Cargando clientes…')
        self.request(self.services.clients.listar, on_success=lambda clients: self._clients_ready(clients, record),
                     on_error=self._clients_failed)

    def _clients_failed(self, error):
        """error: fallo de consulta; restaura el botón de alta."""
        self._preparing = False
        self.create.configure(state='normal')
        self.status.configure(text=str(error))

    def _clients_ready(self, clients: list[Cliente], record=None):
        """clients: lista API; crea etiquetas legibles asociadas a IDs."""
        self._preparing = False
        self.create.configure(state='normal')

        if not clients:
            self.status.configure(text='Registre al menos un cliente antes de ingresar un equipo.')
            return

        owners = {f"[{c.id}] {c.nombre} ({c.telefono})": c.id for c in clients}
        fields = (Field('client_id', 'Cliente', choices=tuple(owners)),
                  Field('tipo', 'Tipo de equipo'), Field('marca', 'Marca'),
                  Field(
                      'modelo',
                      'Modelo',
                  ), Field('numero_serie', 'Serie (opcional)', required=False),
                  Field('problema_reportado', 'Problema reportado'))

        async def save(values):
            """values: formulario; traduce la etiqueta elegida a ID de cliente."""
            payload = {**values, 'client_id': owners[values['client_id']]}
            if record is not None:
                return await self.services.equipment.editar(record.id, **payload)
            return await self.services.equipment.crear(**payload)

        initial = None
        if record is not None:
            initial = record.model_dump()
            initial['client_id'] = next(label for label, identifier in owners.items() if identifier == record.client_id)
        self._dialog = FormDialog(
            self,
            'Editar Equipo' if record is not None else 'Registrar Equipo',
            fields,
            self.runner,
            save,
            self._edited if record is not None else self._created,
            initial=initial,
        )
        self.status.configure(text='Seleccione el cliente propietario en el formulario.')
