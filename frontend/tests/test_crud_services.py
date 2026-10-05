"""Comprueba contratos HTTP de edición/eliminación sin servidor ni ventanas."""
import json
from pathlib import Path
import sys
import unittest
import httpx
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from services import Services
from services.api_client import ApiClient, ApiError


class CrudServicesTests(unittest.IsolatedAsyncioTestCase):
    async def test_edit_and_delete_contracts(self):
        requests = []
        def handle(request):
            requests.append(request)
            if request.method == 'DELETE':
                return httpx.Response(200, json={'mensaje': 'Eliminado'})
            return httpx.Response(200, json={'id': 4, **json.loads(request.content)})
        api = ApiClient(transport=httpx.MockTransport(handle))
        services = Services(api)
        try:
            client = await services.clients.editar(4, nombre='Ana López', telefono='3312345678', correo='')
            self.assertEqual(client.id, 4)
            self.assertIsNone(client.correo)
            equipment = await services.equipment.editar(4, tipo='Laptop', marca='Marca', modelo='Modelo',
                problema_reportado='No enciende', client_id=4, numero_serie='')
            self.assertIsNone(equipment.numero_serie)
            await services.clients.eliminar(4)
            await services.equipment.eliminar(4)
            self.assertEqual([(req.method, req.url.path) for req in requests],
                [('PUT', '/clientes/4'), ('PUT', '/equipos/4'), ('DELETE', '/clientes/4'), ('DELETE', '/equipos/4')])
        finally:
            await api.aclose()

    async def test_invalid_edit_and_history_conflict(self):
        requests = []
        def handle(request):
            requests.append(request)
            return httpx.Response(409, json={'detail': 'El registro tiene órdenes asociadas.'})
        api = ApiClient(transport=httpx.MockTransport(handle))
        services = Services(api)
        try:
            with self.assertRaises(ApiError):
                await services.clients.editar(4, nombre='  ', telefono='inválido')
            self.assertEqual(requests, [])
            with self.assertRaisesRegex(ApiError, 'órdenes asociadas'):
                await services.equipment.eliminar(4)
        finally:
            await api.aclose()


    async def test_user_edit_contract(self):
        requests = []
        def handle(request):
            requests.append(request)
            return httpx.Response(200, json={'id': 4, 'is_active': False, **json.loads(request.content)})
        api = ApiClient(transport=httpx.MockTransport(handle))
        try:
            user = await Services(api).users.editar(4, 'nombre_editado', 'recepcion')
            self.assertEqual(user.id, 4)
            self.assertFalse(user.is_active)
            self.assertEqual(requests[0].method, 'PUT')
            self.assertEqual(requests[0].url.path, '/usuarios/4')
            self.assertEqual(json.loads(requests[0].content), {'username': 'nombre_editado', 'role': 'recepcion'})
        finally:
            await api.aclose()
