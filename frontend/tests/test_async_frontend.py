"""Pruebas de contratos y concurrencia sin servidor, Supabase ni ventanas."""
import asyncio
import json
from pathlib import Path
import sys
from threading import get_ident
import time
import unittest

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from app.async_runner import AsyncRunner
from services import Services
from services.api_client import ApiClient, ApiError
from ui.views.dashboard import DashboardView


class ServicesTests(unittest.IsolatedAsyncioTestCase):
    """Comprueba transporte compartido, entradas y manejo de errores."""

    async def asyncSetUp(self):
        """Crea una API simulada que registra solicitudes."""
        self.requests = []

        def handle(request):
            self.requests.append(request)
            if request.url.path == '/auth/login':
                return httpx.Response(200, json={'access_token': 'test-token', 'token_type': 'bearer', 'role': 'admin'})
            if request.method == 'POST':
                payload = json.loads(request.content)
                if request.url.path == '/clientes/':
                    return httpx.Response(201, json={'mensaje': 'ok', 'cliente': {'id': 1, **payload}})
                if request.url.path == '/equipos/':
                    return httpx.Response(201, json={'mensaje': 'ok', 'folio': 'EQ-001', 'detalles': {
                        'id_interno': 1, 'tipo': payload['tipo'], 'marca': payload['marca'],
                        'modelo': payload['modelo'], 'cliente_id': payload['client_id']}})
                if request.url.path == '/usuarios/':
                    return httpx.Response(201, json={'mensaje': 'ok', 'usuario': payload['username']})
            return httpx.Response(200, json=[] if request.method == 'GET' else {'mensaje': 'ok'})

        self.api = ApiClient(transport=httpx.MockTransport(handle))
        self.services = Services(self.api)

    async def asyncTearDown(self):
        """Libera el cliente HTTP después de cada escenario."""
        await self.api.aclose()

    async def test_login_form_and_session_cleanup(self):
        """Login conserva contraseña; token se agrega solo a operaciones protegidas."""
        self.api.set_token('previous')
        result = await self.services.auth.login('Admin', ' with spaces ')
        request = self.requests[-1]
        self.assertNotIn('authorization', request.headers)
        self.assertIn(b'password=+with+spaces+', request.content)
        self.assertEqual(self.api.token, 'previous')  # La UI aplica el resultado.
        self.api.set_token(result.access_token)
        await self.services.clients.listar()
        self.assertEqual(self.requests[-1].headers['authorization'], 'Bearer test-token')
        self.api.set_token(None)
        await self.services.clients.listar()
        self.assertNotIn('authorization', self.requests[-1].headers)

    async def test_module_routes_and_payloads(self):
        """Cada módulo mantiene sus rutas, opcionales y parámetros de dominio."""
        await self.services.clients.crear('Cliente', '3312345678', '', '')
        self.assertEqual(json.loads(self.requests[-1].content)['correo'], None)
        await self.services.clients.buscar('Ana & Luis')
        self.assertEqual(self.requests[-1].url.params['q'], 'Ana & Luis')
        await self.services.equipment.crear('Laptop', 'Marca', 'Modelo', 'No enciende', 7, '')
        body = json.loads(self.requests[-1].content)
        self.assertEqual(body['client_id'], 7)
        self.assertIsNone(body['numero_serie'])
        await self.services.equipment.listar()
        self.assertEqual(self.requests[-1].url.path, '/equipos/')
        await self.services.users.crear('empleado', 'secret-test', 'tecnico')
        self.assertEqual(json.loads(self.requests[-1].content)['role'], 'tecnico')
        await self.services.users.cambiar_rol(3, 'recepcion')
        self.assertEqual(self.requests[-1].method, 'PATCH')
        self.assertEqual(self.requests[-1].url.path, '/usuarios/3/rol')
        await self.services.users.activar(3, False)
        self.assertEqual(self.requests[-1].url.path, '/usuarios/3/inhabilitar')
        await self.services.users.activar(3)
        self.assertEqual(self.requests[-1].url.path, '/usuarios/3/habilitar')

    async def test_errors_and_invalid_responses(self):
        """HTTP, validación, timeout y JSON inválido llegan como errores legibles."""
        cases = [
            (httpx.Response(403, json={'detail': 'Acceso denegado'}), 'Acceso denegado', 403),
            (httpx.Response(422, json={'detail': [{'msg': 'Nombre obligatorio'}]}), 'Nombre obligatorio', 422),
            (httpx.Response(502, text='<html>internal</html>'), 'HTTP 502', 502),
            (httpx.Response(200, text='invalid'), 'respuesta inválida', None),
        ]
        for response, message, status in cases:
            api = ApiClient(transport=httpx.MockTransport(lambda request: response))
            try:
                with self.assertRaises(ApiError) as caught:
                    await api.request('GET', '/clientes/')
                self.assertIn(message, str(caught.exception))
                self.assertEqual(caught.exception.status_code, status)
            finally:
                await api.aclose()

        def timeout(request):
            raise httpx.ReadTimeout('simulated', request=request)

        api = ApiClient(transport=httpx.MockTransport(timeout))
        try:
            with self.assertRaisesRegex(ApiError, 'tardó demasiado'):
                await api.request('GET', '/')
        finally:
            await api.aclose()

    async def test_invalid_list_and_login(self):
        """Respuestas inesperadas no rompen tablas ni crean sesión."""
        api = ApiClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={'unexpected': True})))
        services = Services(api)
        try:
            with self.assertRaisesRegex(ApiError, 'lista válida'):
                await services.clients.listar()
            with self.assertRaisesRegex(ApiError, 'contrato Sesion'):
                await services.auth.login('test', 'test')
        finally:
            await api.aclose()

    async def test_dashboard_queries_are_concurrent(self):
        """Las métricas arrancan juntas y un error no pierde las otras respuestas."""
        started = set()
        all_started = asyncio.Event()

        async def query(name, fail=False):
            started.add(name)
            if len(started) == 3:
                all_started.set()
            await asyncio.wait_for(all_started.wait(), timeout=1)
            if fail:
                raise ApiError('no disponible')
            return [{'id': 1}]

        view = object.__new__(DashboardView)
        view.queries = [('eq', lambda: query('eq', True)), ('cl', lambda: query('cl')),
                        ('us', lambda: query('us'))]
        results = await view._fetch()
        self.assertIsInstance(results[0], ApiError)
        self.assertEqual(results[1:], [[{'id': 1}], [{'id': 1}]])


class FakeRoot:
    """Simula after y detecta cualquier acceso de Tk desde el trabajador."""

    def __init__(self):
        self.thread = get_ident()
        self.callbacks = {}
        self.sequence = 0

    def after(self, delay, callback):
        assert get_ident() == self.thread
        self.sequence += 1
        self.callbacks[self.sequence] = callback
        return self.sequence

    def after_cancel(self, identifier):
        assert get_ident() == self.thread
        self.callbacks.pop(identifier, None)

    def tick(self):
        callbacks, self.callbacks = self.callbacks, {}
        for callback in callbacks.values():
            callback()


class Owner:
    """Representa una vista activa o destruida sin abrir Tk."""
    exists = True

    def winfo_exists(self):
        return self.exists


class RunnerTests(unittest.TestCase):
    """Comprueba entrega en Tk, descarte de tareas y cierre sin bloquear."""

    def setUp(self):
        self.root = FakeRoot()
        self.runner = AsyncRunner(self.root)

    def wait_for(self, predicate):
        """predicate: condición esperada; bombea callbacks con un límite breve."""
        deadline = time.monotonic() + 2
        while not predicate() and time.monotonic() < deadline:
            self.root.tick()
            time.sleep(0.005)
        self.assertTrue(predicate())

    def tearDown(self):
        closed = []

        async def cleanup():
            closed.append('http')

        if not self.runner._closing:
            self.runner.close(cleanup(), lambda: closed.append('tk'))
            self.wait_for(lambda: 'tk' in closed)
        self.assertFalse(self.runner._thread.is_alive())
        self.assertTrue(self.runner.loop.is_closed())

    def test_callback_runs_on_main_thread(self):
        delivered = []
        main_thread = get_ident()

        async def work():
            await asyncio.sleep(0.03)
            return get_ident()

        future = self.runner.submit(work(), Owner(),
            lambda worker: delivered.append((worker, get_ident())), self.fail)
        self.assertFalse(future.done())  # submit no espera la solicitud.
        self.wait_for(lambda: bool(delivered))
        self.assertNotEqual(delivered[0][0], main_thread)
        self.assertEqual(delivered[0][1], main_thread)

    def test_cancel_owner_and_destroyed_view(self):
        delivered = []

        async def work():
            await asyncio.sleep(0.03)
            return 'late'

        owner = Owner()
        future = self.runner.submit(work(), owner, delivered.append, self.fail)
        self.runner.cancel_owner(owner)
        self.assertTrue(future.cancelled())
        dead = Owner()
        dead.exists = False
        future = self.runner.submit(work(), dead, delivered.append, self.fail)
        self.wait_for(lambda: future.done() and not self.runner._pending)
        self.assertEqual(delivered, [])

    def test_close_cancels_work_and_closes_http(self):
        finished = []

        async def pending():
            await asyncio.sleep(20)

        async def cleanup():
            await asyncio.sleep(0)
            finished.append('http')

        future = self.runner.submit(pending(), Owner(), self.fail, self.fail)
        self.runner.close(cleanup(), lambda: finished.append('tk'))
        self.wait_for(lambda: 'tk' in finished)
        self.assertTrue(future.cancelled())
        self.assertEqual(finished, ['http', 'tk'])


if __name__ == '__main__':
    unittest.main()
