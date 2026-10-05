"""Comprueba columnas SQL y autenticación con usuarios/roles, sin conexión remota."""
import os
from pathlib import Path
import re
import sys
import unittest

os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['SECRET_KEY'] = 'schema-tests-secret-only-32-characters'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.database.conexion import Base, get_db
from src.database import domain_models
from src.modules.clients.model import Client
from src.modules.equipment.model import Equipment
from src.modules.users.model import User
from src.modules.roles.model import Role
from src.modules.users.repository import user_repository
from src.modules.users.schema import UserCreate
from src.modules.auth.router import router
from src.shared.security import verify_password


class SchemaTests(unittest.TestCase):
    def test_actual_account_state_column(self):
        """Regresión del 500: PostgreSQL confirmó usuarios.is_active, no is_activate."""
        self.assertEqual(User.is_active.property.columns[0].name, 'is_active')
        self.assertNotIn('is_activate', User.__table__.columns)

    def test_all_sql_columns_and_foreign_keys(self):
        """El SQL local, no el ORM, define las columnas físicas esperadas."""
        sql = (Path(__file__).resolve().parents[2] / 'database/scripts/BASE DE DATOS FIXIFY.sql').read_text(encoding='utf-8')
        definitions = re.findall(r'CREATE TABLE (\w+)\s*\((.*?)\);', sql, re.S)
        self.assertEqual(set(Base.metadata.tables), {name for name, _ in definitions})
        for name, body in definitions:
            expected = set(re.findall(r'^\s*(\w+)\s+(?:SERIAL|VARCHAR|INT|TEXT|TIMESTAMP|BOOLEAN)\b', body, re.M))
            table = Base.metadata.tables[name]
            self.assertEqual(set(table.columns.keys()), expected, name)
            for column_name, definition in re.findall(r'^\s*(\w+)\s+((?:SERIAL|VARCHAR|INT|TEXT|TIMESTAMP|BOOLEAN)[^,\n]*)', body, re.M):
                column = table.columns[column_name]
                self.assertEqual(column.nullable, not ('NOT NULL' in definition or 'PRIMARY KEY' in definition), f'{name}.{column_name}')
                length = re.search(r'VARCHAR\((\d+)\)', definition)
                if length:
                    self.assertEqual(column.type.length, int(length.group(1)))
            expected_fk = set(re.findall(r'FOREIGN KEY \((\w+)\) REFERENCES (\w+)\((\w+)\)', body))
            actual_fk = {(fk.parent.name, fk.column.table.name, fk.column.name) for fk in table.foreign_keys}
            self.assertEqual(actual_fk, expected_fk, name)

    def test_create_and_authenticate_sql_user(self):
        """Cuenta con nombre, correo, hash e id_rol autentica con el contrato actual."""
        engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add(Role(nombre_rol='Recepcionista (prueba)'))
            db.commit()
            user = user_repository.create(db, UserCreate(username='prueba_test', password='Prueba-segura-123', role='recepcion'))
            self.assertEqual(user.role, 'recepcion')
            self.assertTrue(user.is_active)
            identifier = user.id
            self.assertTrue(verify_password('Prueba-segura-123', user.hashed_password))
            self.assertFalse(verify_password('incorrecta', user.hashed_password))

        def override():
            with Session(engine) as db:
                yield db

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_db] = override
        with TestClient(app) as client:
            response = client.post('/auth/login', data={'username': 'prueba_test', 'password': 'Prueba-segura-123'})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['role'], 'recepcion')
            self.assertEqual(client.post('/auth/login', data={'username': 'prueba_test', 'password': 'incorrecta'}).status_code, 401)
            with Session(engine) as db:
                user_repository.inhabilitar_usuario(db, identifier)
            self.assertEqual(client.post('/auth/login', data={'username': 'prueba_test', 'password': 'Prueba-segura-123'}).status_code, 403)
            with Session(engine) as db:
                user = db.get(User, identifier)
                self.assertFalse(user.is_active)
                self.assertEqual(user.role, 'recepcion')
                user_repository.habilitar_usuario(db, identifier)
                self.assertIsNone(user_repository.habilitar_usuario(db, 99999))
                self.assertIsNone(user_repository.inhabilitar_usuario(db, 99999))
            self.assertEqual(client.post('/auth/login', data={'username': 'prueba_test', 'password': 'Prueba-segura-123'}).status_code, 200)
        engine.dispose()
