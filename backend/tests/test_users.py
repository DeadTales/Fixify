"""Edición administrativa de cuentas, permisos y conservación de credenciales."""
import unittest
import test_equipment
from src.modules.users.router import router
from src.modules.users.model import User


class UserTests(unittest.TestCase):
    tearDown = test_equipment.EquipmentTests.tearDown
    auth_headers = staticmethod(test_equipment.EquipmentTests.auth_headers)

    def setUp(self):
        test_equipment.EquipmentTests.setUp(self)
        self.app.include_router(router)
        with self.sessions() as db:
            user = db.query(User).filter(User.username == 'tecnico').one()
            self.identifier = user.id
            self.original_hash = user.hashed_password
        self.admin_headers = self.auth_headers('admin')

    def test_edit_preserves_credentials_and_state(self):
        response = self.client.put(f'/usuarios/{self.identifier}', headers=self.admin_headers,
                                  json={'username': 'tecnico_editado', 'role': 'recepcion'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {'id': self.identifier, 'username': 'tecnico_editado',
                                         'role': 'recepcion', 'is_active': True})
        with self.sessions() as db:
            self.assertEqual(db.get(User, self.identifier).hashed_password, self.original_hash)
        self.assertEqual(self.client.patch(f'/usuarios/{self.identifier}/inhabilitar',
                                          headers=self.admin_headers).status_code, 200)
        self.assertEqual(self.client.put(f'/usuarios/{self.identifier}', headers=self.admin_headers,
            json={'username': 'tecnico_editado', 'role': 'tecnico'}).json()['is_active'], False)
        self.assertEqual(self.client.patch(f'/usuarios/{self.identifier}/habilitar',
                                          headers=self.admin_headers).status_code, 200)

    def test_edit_permissions_invalid_input_and_conflicts(self):
        path = f'/usuarios/{self.identifier}'
        values = {'username': 'tecnico_editado', 'role': 'recepcion'}
        self.assertEqual(self.client.put(path, json=values).status_code, 401)
        for role in ('recepcion', 'tecnico'):
            self.assertEqual(self.client.put(path, json=values, headers=self.auth_headers(role)).status_code, 403)
        for changes in ({'username': 'x'}, {'role': 'invalido'}):
            self.assertEqual(self.client.put(path, json={**values, **changes}, headers=self.admin_headers).status_code, 422)
        self.assertEqual(self.client.put(path, json={**values, 'username': 'admin'},
                                        headers=self.admin_headers).status_code, 409)
        self.assertEqual(self.client.put('/usuarios/999', json=values, headers=self.admin_headers).status_code, 404)
        with self.sessions() as db:
            self.assertEqual(db.get(User, self.identifier).username, 'tecnico')
