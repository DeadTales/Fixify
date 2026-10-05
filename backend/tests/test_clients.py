"""RF03: datos obligatorios, permisos y confirmación consumible por el frontend."""
import unittest
import test_equipment
from src.modules.clients.router import router as clients_router


class ClientTests(unittest.TestCase):
    tearDown = test_equipment.EquipmentTests.tearDown
    auth_headers = staticmethod(test_equipment.EquipmentTests.auth_headers)
    # Reutiliza la base física y las cuentas reales del escenario integrado.
    def setUp(self):
        test_equipment.EquipmentTests.setUp(self)
        self.app.include_router(clients_router)

    def test_client_registration_search_and_validation(self):
        data = {'nombre': '  Ana López  ', 'telefono': '3398765432'}
        response = self.client.post('/clientes/', json=data, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        saved = response.json()['cliente']
        self.assertGreater(saved['id'], 0)
        self.assertEqual(saved['nombre'], 'Ana López')
        self.assertEqual(self.client.get('/clientes/buscar', params={'q': 'Ana'},
                                        headers=self.headers).json(), [saved])
        self.assertEqual(self.client.post('/clientes/', json=data, headers=self.headers).status_code, 400)
        for invalid in ({'nombre': '   '}, {'telefono': 'abcdefgh'}, {'correo': 'inválido'}):
            self.assertEqual(self.client.post('/clientes/', json={**data, **invalid},
                                             headers=self.headers).status_code, 422)
        self.assertEqual(self.client.post('/clientes/', json=data,
                         headers=self.auth_headers('tecnico')).status_code, 403)


    def test_edit_delete_and_related_equipment(self):
        data = {'nombre': 'Cliente editable', 'telefono': '3398765432', 'correo': None}
        identifier = self.client.post('/clientes/', json=data, headers=self.headers).json()['cliente']['id']
        path = f'/clientes/{identifier}'
        result = self.client.put(path, json={**data, 'nombre': 'Cliente corregido'}, headers=self.headers)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['nombre'], 'Cliente corregido')
        self.assertEqual(self.client.put(path, json={**data, 'telefono': '3312345678'}, headers=self.headers).status_code, 409)
        self.assertEqual(self.client.delete(path, headers=self.auth_headers('tecnico')).status_code, 403)
        self.assertEqual(self.client.delete('/clientes/7', headers=self.headers).status_code, 200)
        self.assertEqual(self.client.delete(path, headers=self.headers).status_code, 200)
        self.assertEqual(self.client.put(path, json=data, headers=self.headers).status_code, 404)

    def test_client_with_equipment_is_preserved(self):
        self.client.post('/equipos/', json=self.payload, headers=self.headers)
        self.assertEqual(self.client.delete('/clientes/7', headers=self.headers).status_code, 409)
        self.assertEqual(len(self.client.get('/clientes/', headers=self.headers).json()), 1)
