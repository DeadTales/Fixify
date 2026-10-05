"""Prueba equipos con nombres físicos del diagrama, sin Supabase ni main.py."""
import os
from pathlib import Path
import sys
import unittest
from datetime import datetime, timedelta, timezone

# Configuración aislada: las pruebas no necesitan DataBase.env ni conexión remota.
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['SECRET_KEY'] = 'fixify-equipment-tests-only-secret-key-32-chars'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'frontend/src'))

import jwt
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.config.settings import settings
from src.database.conexion import get_db
from src.modules.equipment.model import Equipment
from src.modules.equipment.router import router
from src.database.conexion import Base
from src.modules.users.model import User
from src.modules.roles.model import Role
from src.database.domain_models import ServiceOrder
from src.shared.security import get_password_hash
from services import Services
from services.api_client import ApiClient


class EquipmentTests(unittest.TestCase):
    """Comprueba alta/listado, serialización, columnas y permisos de equipos."""

    def setUp(self):
        """Crea tablas independientes del ORM con los nombres del diagrama."""
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        self.sessions = sessionmaker(bind=self.engine)
        with self.engine.begin() as connection:
            connection.execute(text('PRAGMA foreign_keys=ON'))
            connection.execute(text('''CREATE TABLE clientes (
                id_cliente INTEGER PRIMARY KEY, nombre VARCHAR(150),
                telefono VARCHAR(20), correo VARCHAR(100))'''))
            connection.execute(text('''CREATE TABLE equipos (
                id_equipo INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL REFERENCES clientes(id_cliente),
                tipo VARCHAR(50), marca VARCHAR(50), modelo VARCHAR(50),
                numero_serie VARCHAR(100), falla_reportada TEXT)'''))
            connection.execute(text("INSERT INTO clientes VALUES (7, 'Cliente prueba', '3312345678', NULL)"))

        ServiceOrder.__table__.create(self.engine)
        Base.metadata.tables['roles'].create(self.engine)
        Base.metadata.tables['usuarios'].create(self.engine)
        with self.sessions() as db:
            for code, label in [('admin', 'Administrador'), ('recepcion', 'Recepcionista'), ('tecnico', 'Técnico')]:
                role = Role(nombre_rol=label)
                db.add(User(username=code, hashed_password=get_password_hash('Prueba123'), rol=role))
            db.commit()

        def override_db():
            """Entrega una sesión de prueba y la cierra al terminar la petición."""
            with self.sessions() as session:
                yield session

        self.app = FastAPI()
        self.app.include_router(router)
        self.app.dependency_overrides[get_db] = override_db
        self.client = TestClient(self.app)
        self.headers = self.auth_headers('recepcion')
        self.payload = {'tipo': 'Laptop', 'marca': 'Marca', 'modelo': 'Modelo',
                        'numero_serie': 'PRUEBA-001', 'problema_reportado': 'No enciende', 'client_id': 7}

    def tearDown(self):
        """Libera servidor y base temporal."""
        self.client.close()
        self.engine.dispose()

    @staticmethod
    def auth_headers(role):
        """role: rol simulado; firma un JWT exclusivamente de pruebas."""
        token = jwt.encode({'sub': role, 'role': role,
                            'exp': datetime.now(timezone.utc) + timedelta(minutes=5)},
                           settings.SECRET_KEY, algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}

    def test_create_and_list_against_diagram_columns(self):
        """Alta y recarga conservan contrato API sin exigir renombrar la BD."""
        response = self.client.post('/equipos/', json=self.payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()['folio'], 'EQ-001')
        response = self.client.get('/equipos/', headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), [{'id': 1, **self.payload}])
        with self.engine.connect() as connection:
            row = connection.execute(text('SELECT id_equipo, id_cliente, falla_reportada FROM equipos')).one()
            self.assertEqual(tuple(row), (1, 7, 'No enciende'))
        fk = next(iter(Equipment.__table__.c.id_cliente.foreign_keys))
        self.assertEqual(fk.column.name, 'id_cliente')

    def test_missing_client_and_invalid_payload(self):
        """Rechaza cliente inexistente y datos inválidos sin insertar equipos."""
        response = self.client.post('/equipos/', json={**self.payload, 'client_id': 999}, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        response = self.client.post('/equipos/', json={**self.payload, 'tipo': ''}, headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get('/equipos/', headers=self.headers).json(), [])

    def test_optional_serial_and_order(self):
        """Serie ausente retorna null; listado tiene orden estable por ID."""
        for serial in (None, 'SEGUNDO'):
            response = self.client.post('/equipos/', json={**self.payload, 'numero_serie': serial}, headers=self.headers)
            self.assertEqual(response.status_code, 201)
        items = self.client.get('/equipos/', headers=self.headers).json()
        self.assertEqual([item['id'] for item in items], [1, 2])
        self.assertIsNone(items[0]['numero_serie'])

    def test_permissions(self):
        """Conserva acceso admin/recepción y rechaza técnico o falta de JWT."""
        for method in ('get', 'post'):
            kwargs = {'json': {**self.payload, 'numero_serie': 'PERMISOS'}} if method == 'post' else {}
            request = getattr(self.client, method)
            self.assertEqual(request('/equipos/', **kwargs).status_code, 401)
            self.assertEqual(request('/equipos/', headers=self.auth_headers('tecnico'), **kwargs).status_code, 403)
            self.assertIn(request('/equipos/', headers=self.auth_headers('admin'), **kwargs).status_code, (200, 201))

    def test_edit_delete_and_history(self):
        created = self.client.post('/equipos/', json=self.payload, headers=self.headers).json()
        identifier = created['detalles']['id_interno']
        path = f'/equipos/{identifier}'
        changed = {**self.payload, 'modelo': 'Modelo actualizado', 'numero_serie': None}
        result = self.client.put(path, json=changed, headers=self.headers)
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['modelo'], 'Modelo actualizado')
        self.assertEqual(self.client.put(path, json=changed,
                         headers=self.auth_headers('tecnico')).status_code, 403)
        with self.sessions() as db:
            db.add(ServiceOrder(folio='TEST-001', id_equipo=identifier, id_cliente=7, estado='Recibido'))
            db.commit()
        self.assertEqual(self.client.delete(path, headers=self.headers).status_code, 409)
        with self.sessions() as db:
            db.query(ServiceOrder).delete()
            db.commit()
        self.assertEqual(self.client.delete(path, headers=self.headers).status_code, 200)
        self.assertEqual(self.client.delete(path, headers=self.headers).status_code, 404)

    def test_edit_rejects_duplicate_and_unknown_owner(self):
        first = self.client.post('/equipos/', json=self.payload, headers=self.headers).json()['detalles']['id_interno']
        self.client.post('/equipos/', json={**self.payload, 'numero_serie': 'OTRO'}, headers=self.headers)
        self.assertEqual(self.client.put(f'/equipos/{first}', json={**self.payload, 'numero_serie': 'OTRO'},
                                        headers=self.headers).status_code, 409)
        self.assertEqual(self.client.put(f'/equipos/{first}', json={**self.payload, 'client_id': 999},
                                        headers=self.headers).status_code, 404)

    def test_duplicate_serial(self):
        self.assertEqual(self.client.post('/equipos/', json=self.payload, headers=self.headers).status_code, 201)
        self.assertEqual(self.client.post('/equipos/', json=self.payload, headers=self.headers).status_code, 409)
        self.assertEqual(len(self.client.get('/equipos/', headers=self.headers).json()), 1)

    def test_current_account_state_and_role(self):
        headers = self.auth_headers('admin')
        with self.sessions() as db:
            user = db.query(User).filter(User.username == 'admin').one()
            user.rol = db.query(Role).filter(Role.nombre_rol == 'Técnico').one()
            db.commit()
        self.assertEqual(self.client.get('/equipos/', headers=headers).status_code, 403)
        with self.sessions() as db:
            db.query(User).filter(User.username == 'admin').one().is_active = False
            db.commit()
        self.assertEqual(self.client.get('/equipos/', headers=headers).status_code, 401)

    def test_frontend_service_consumes_real_router(self):
        """httpx del frontend usa el router real en memoria mediante ASGITransport."""
        import asyncio

        async def flow():
            api = ApiClient(transport=httpx.ASGITransport(app=self.app))
            api.set_token(self.headers['Authorization'].removeprefix('Bearer '))
            services = Services(api)
            try:
                created = await services.equipment.crear(**self.payload)
                items = await services.equipment.listar()
                self.assertEqual(created.folio, 'EQ-001')
                self.assertEqual([item.model_dump() for item in items], [{'id': 1, **self.payload}])
            finally:
                await api.aclose()

        asyncio.run(flow())


if __name__ == '__main__':
    unittest.main()
