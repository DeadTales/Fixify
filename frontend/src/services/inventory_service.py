"""Operaciones tipadas para materiales, consumos y alertas."""
from models.inventory import AlertaStock, ConsumoMaterial, Material
from services.api_client import ApiError, ModuleService


def entero_positivo(value, label, *, permite_cero=False):
    """Convierte entradas de Tk sin permitir decimales, booleanos ni signos."""

    text = str(value).strip()
    if not text.isdigit():
        raise ApiError(f'{label} debe ser un número entero.')
    result = int(text)
    if result < (0 if permite_cero else 1):
        suffix = 'mayor o igual a cero' if permite_cero else 'mayor que cero'
        raise ApiError(f'{label} debe ser {suffix}.')
    return result


class InventoryService(ModuleService):
    """Mantiene las rutas y conversiones de inventario fuera de la vista."""

    async def listar(self) -> list[Material]:
        return await self._list('/inventario/', Material)

    async def bajo_stock(self) -> list[Material]:
        return await self._list('/inventario/bajo-stock', Material)

    async def alertas(self) -> list[AlertaStock]:
        return await self._list('/inventario/alertas', AlertaStock)

    async def crear(self, clave, descripcion, unidad, existencia_actual, stock_minimo) -> Material:
        payload = {
            'clave': clave.strip() or None,
            'descripcion': descripcion.strip(),
            'unidad': unidad.strip() or None,
            'existencia_actual': entero_positivo(existencia_actual, 'Existencia', permite_cero=True),
            'stock_minimo': entero_positivo(stock_minimo, 'Stock mínimo', permite_cero=True),
        }
        data = await self.api.request('POST', '/inventario/', json=payload)
        return self._parse(Material, data)

    async def editar(self, material_id, **values) -> Material:
        payload = {
            'clave': values['clave'].strip() or None,
            'descripcion': values['descripcion'].strip(),
            'unidad': values['unidad'].strip() or None,
            'existencia_actual': entero_positivo(values['existencia_actual'], 'Existencia', permite_cero=True),
            'stock_minimo': entero_positivo(values['stock_minimo'], 'Stock mínimo', permite_cero=True),
        }
        data = await self.api.request('PATCH', f'/inventario/{material_id}', json=payload)
        return self._parse(Material, data)

    async def consumir(self, id_orden, id_material, cantidad_utilizada) -> ConsumoMaterial:
        payload = {
            'id_orden': entero_positivo(id_orden, 'Orden'),
            'id_material': entero_positivo(id_material, 'Material'),
            'cantidad_utilizada': entero_positivo(cantidad_utilizada, 'Cantidad'),
        }
        data = await self.api.request('POST', '/inventario/consumos', json=payload)
        return self._parse(ConsumoMaterial, data)

    async def consumos_orden(self, order_id) -> list[ConsumoMaterial]:
        order_id = entero_positivo(order_id, 'Orden')
        return await self._list(f'/inventario/consumos/orden/{order_id}', ConsumoMaterial)
