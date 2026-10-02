"""Comprueba descubrimiento de módulos y delegación a tareas sin abrir Tk."""
import asyncio
from pathlib import Path
from types import SimpleNamespace, ModuleType
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from services import Services
from services.api_client import ModuleService
from services.discovery import service_classes
from ui.components import AsyncFrame, CollectionView
from ui.views.discovery import available_views


class IntegrationTests(unittest.TestCase):
    def test_existing_services_and_menus(self):
        """Conserva las claves existentes, una API y los accesos por rol."""
        api = object()
        services = Services(api)
        for name in ('auth', 'clients', 'equipment', 'users'):
            self.assertIs(getattr(services, name).api, api)
        self.assertEqual([label for label, _ in available_views('admin')],
                         ['Dashboard', 'Equipos', 'Clientes', 'Usuarios'])
        self.assertEqual([label for label, _ in available_views('recepcion')],
                         ['Dashboard', 'Equipos', 'Clientes'])
        self.assertEqual([label for label, _ in available_views('tecnico')], ['Dashboard'])

    def test_new_service_and_view_need_no_manual_registration(self):
        """Un archivo de servicio y una vista con metadatos bastan para descubrirlos."""
        service_module = ModuleType('services.orders_service')
        service_module.OrdersService = type('OrdersService', (ModuleService,),
                                           {'__module__': service_module.__name__})
        with patch('services.discovery.iter_modules', return_value=[SimpleNamespace(name='orders_service')]), \
             patch('services.discovery.import_module', return_value=service_module):
            services = Services(object())
            self.assertIsInstance(services.orders, service_module.OrdersService)
        view_module = ModuleType('ui.views.orders')
        view_module.OrdersView = type('OrdersView', (CollectionView,), {
            '__module__': view_module.__name__, 'menu_label': 'Órdenes',
            'allowed_roles': ('admin',), 'service_name': 'orders'})
        with patch('ui.views.discovery.iter_modules', return_value=[SimpleNamespace(name='orders')]), \
             patch('ui.views.discovery.import_module', return_value=view_module):
            self.assertEqual(available_views('admin'), [('Órdenes', view_module.OrdersView)])
            self.assertEqual(available_views('tecnico'), [])

    def test_request_sets_owner_and_default_error_callback(self):
        """La vista pasa una operación; la base configura propietario y callbacks."""
        async def operation(value):
            return value * 2
        received = []
        def submit(coroutine, owner, success, error):
            received.append((owner, success, error))
            success(asyncio.run(coroutine))
            return 'future'
        results = []
        error_callback = lambda error: None
        view = SimpleNamespace(runner=SimpleNamespace(submit=submit), _failed=error_callback)
        self.assertEqual(AsyncFrame.request(view, operation, 3, on_success=results.append), 'future')
        self.assertEqual(results, [6])
        self.assertIs(received[0][0], view)
        self.assertIs(received[0][2], error_callback)

    def test_duplicate_service_key_is_rejected(self):
        module = ModuleType('services.orders_service')
        for name in ('First', 'Second'):
            setattr(module, name, type(name, (ModuleService,), {
                '__module__': module.__name__, 'service_name': 'orders'}))
        with patch('services.discovery.iter_modules', return_value=[SimpleNamespace(name='orders_service')]), \
             patch('services.discovery.import_module', return_value=module):
            with self.assertRaisesRegex(ValueError, 'duplicado'):
                service_classes()


class DefaultCollectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_and_save_delegate_to_declared_service(self):
        """Listado y alta comunes no requieren coroutines nuevas en cada vista."""
        class Service:
            async def listar(self):
                return ['orden']
            async def crear(self, equipo_id):
                return equipo_id
        view = SimpleNamespace(service=Service())
        self.assertEqual(await CollectionView.fetch(view), ['orden'])
        self.assertEqual(await CollectionView.save(view, {'equipo_id': 7}), 7)
