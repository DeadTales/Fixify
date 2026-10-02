"""Formulario y tabla del módulo de clientes."""
from ui.components import CollectionView, Field
from models.clients import Cliente


class ClientsView(CollectionView):
    """Configura clientes reutilizando la vista común de colección."""
    title = 'Directorio de Clientes'
    columns = ('ID', 'Nombre', 'Teléfono', 'Correo', 'Dirección')
    fields = (Field('nombre', 'Nombre completo'), Field('telefono', 'Teléfono'),
              Field('correo', 'Correo (opcional)', required=False),
              Field('direccion', 'Dirección (opcional)', required=False))

    async def fetch(self):
        """Consulta clientes desde su service."""
        return await self.services.clients.listar()

    async def save(self, values):
        """values: nombre, teléfono y datos opcionales capturados."""
        return await self.services.clients.crear(**values)

    def row(self, record: Cliente):
        """record: cliente API; convierte campos opcionales vacíos a guion."""
        return (record.id, record.nombre, record.telefono, record.correo or '-', record.direccion or '-')
