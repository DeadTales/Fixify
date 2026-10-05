"""Formulario y tabla del módulo de clientes."""
from ui.components import CollectionView, Field
from models.clients import Cliente


class ClientsView(CollectionView):
    """Configura clientes reutilizando la vista común de colección."""
    # Plantilla de módulo: campos -> save -> service -> contrato de respuesta.
    # row solo adapta presentación; no realiza consultas ni valida la API.
    title = 'Directorio de Clientes'
    menu_label = 'Clientes'
    allowed_roles = ('admin', 'recepcion')
    menu_order = 20
    service_name = 'clients'
    columns = ('ID', 'Nombre', 'Teléfono', 'Correo')
   
    fields = (
        Field('nombre', 'Nombre completo'),
        Field('telefono', 'Teléfono'),
        Field('correo', 'Correo (opcional)', required=False),
    )

    async def fetch(self):
        """Consulta clientes desde su service."""
        return await self.services.clients.listar()

    async def save(self, values):
        """values: nombre, teléfono y datos opcionales capturados."""
        return await self.services.clients.crear(**values)

    def row(self, record: Cliente):
        """record: cliente API; convierte campos opcionales vacíos a guion."""
        return (record.id, record.nombre, record.telefono, record.correo or '-')
