"""Pruebas del contrato y su integración con services y filas de UI, sin ventanas."""
from pathlib import Path
import sys
import unittest
import httpx
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from models.auth import Login, Sesion
from models.clients import Cliente
from models.equipment import Equipo
from models.users import Usuario
from services import Services
from services.api_client import ApiClient, ApiError
from ui.views.clients import ClientsView
from ui.views.equipment import EquipmentView
from ui.views.users import UsersView


class ModelsTests(unittest.TestCase):
    """Asegura tipos públicos y evita conservar campos sensibles adicionales."""

    def test_strict_types_and_required_fields(self):
        """IDs string/bool, roles desconocidos y campos ausentes rompen el contrato."""
        valid = {'id': 1, 'username': 'admin', 'role': 'admin', 'is_active': True}
        for changes in ({'id': '1'}, {'id': True}, {'is_active': 'false'}, {'role': 'superadmin'}):
            with self.assertRaises(ValidationError):
                Usuario.model_validate({**valid, **changes})
        with self.assertRaises(ValidationError):
            Cliente.model_validate({'id': 1, 'nombre': 'Ana'})

    def test_extras_optional_fields_and_secret_repr(self):
        """Opcionales funcionan; hashes extra y credenciales no aparecen en repr."""
        user = Usuario.model_validate({'id': 1, 'username': 'admin', 'role': 'admin',
                                       'is_active': True, 'hashed_password': 'hash-sensible'})
        self.assertNotIn('hashed_password', user.model_dump())
        client = Cliente(id=7, nombre='Ana', telefono='3312345678')
        self.assertIsNone(client.correo)
        self.assertNotIn('clave-sensible', repr(Login(username='admin', password='clave-sensible')))
        self.assertNotIn('token-sensible', repr(Sesion(access_token='token-sensible', token_type='bearer', role='admin')))

    def test_views_render_models(self):
        """Filas consumen atributos tipados y muestran opcionales como guion."""
        client = Cliente(id=7, nombre='Ana', telefono='3312345678')
        equipment = Equipo(id=3, tipo='Laptop', marca='Marca', modelo='Modelo',
                           problema_reportado='No enciende', client_id=7)
        user = Usuario(id=2, username='tecnico', role='tecnico', is_active=False)
        self.assertEqual(ClientsView.row(None, client), (7, 'Ana', '3312345678', '-'))
        self.assertEqual(EquipmentView.row(None, equipment),
                         ('EQ-003', 'Laptop', 'Marca', 'Modelo', '-', 'No enciende', 7))
        self.assertEqual(UsersView.row(None, user), (2, 'tecnico', 'tecnico', 'Inactivo'))


class ContractServicesTests(unittest.IsolatedAsyncioTestCase):
    """Valida la frontera HTTP antes de entregar datos a Tk."""

    async def test_invalid_record_rejected_before_view(self):
        """Un JSON válido con campos inválidos se informa como ApiError."""
        for payload in ([{'id': 1}], [{'id': True, 'nombre': 'Ana', 'telefono': '3312345678'}]):
            api = ApiClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload)))
            try:
                with self.assertRaisesRegex(ApiError, 'contrato Cliente'):
                    await Services(api).clients.listar()
            finally:
                await api.aclose()

    async def test_valid_list_returns_models(self):
        """Un listado correcto retorna Cliente, no dict; vacío sigue siendo válido."""
        payload = [{'id': 7, 'nombre': 'Ana', 'telefono': '3312345678'}]
        api = ApiClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload)))
        try:
            items = await Services(api).clients.listar()
            self.assertIsInstance(items[0], Cliente)
            self.assertEqual(items[0].id, 7)
        finally:
            await api.aclose()

    async def test_invalid_input_is_not_sent_and_no_secret_leaks(self):
        """No realiza HTTP para entradas inválidas ni incluye credenciales en errores."""
        requests = []

        def handle(request):
            requests.append(request)
            return httpx.Response(200, json={})

        api = ApiClient(transport=httpx.MockTransport(handle))
        try:
            with self.assertRaises(ApiError) as caught:
                await Services(api).users.crear('x', 'clave-sensible', 'admin')
            self.assertNotIn('clave-sensible', str(caught.exception))
            self.assertIsNone(caught.exception.__cause__)
            self.assertTrue(caught.exception.__suppress_context__)
            self.assertEqual(requests, [])
        finally:
            await api.aclose()

    async def test_malformed_creation_confirmation_rejected(self):
        """Una confirmación incompleta no se presenta como alta válida."""
        api = ApiClient(transport=httpx.MockTransport(lambda r: httpx.Response(201, json={'mensaje': 'ok'})))
        try:
            with self.assertRaisesRegex(ApiError, 'contrato EquipoRegistrado'):
                await Services(api).equipment.crear('Laptop', 'Marca', 'Modelo', 'No enciende', 7)
        finally:
            await api.aclose()
