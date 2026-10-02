"""Alinea la columna de equipos y crea una cuenta sintética sin borrar datos."""
import json
from pathlib import Path
import secrets
import sys
from dotenv import load_dotenv
from sqlalchemy import text

BACKEND = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND / 'DataBase.env')
sys.path.insert(0, str(BACKEND))
from src.database.conexion import SessionLocal, engine
from src.modules.users.model import User
from src.modules.roles.model import Role
from src.shared.security import get_password_hash, verify_password


def main():
    """Migra y crea en una transacción; conserva usuarios existentes sin resetear claves."""
    path = BACKEND / 'usuario_prueba.local.json'
    username = 'fixify_prueba'
    password = secrets.token_urlsafe(18)
    created = False
    with SessionLocal.begin() as db:
        # Evita ejecuciones concurrentes de este bootstrap en PostgreSQL.
        db.execute(text("SELECT pg_advisory_xact_lock(26060201)"))
        columns = set(db.execute(text("SELECT column_name FROM information_schema.columns "
                                      "WHERE table_schema='public' AND table_name='equipos'")).scalars())
        if 'problema_reportado' in columns and 'falla_reportada' in columns:
            raise RuntimeError('Hay dos columnas de falla; se requiere reconciliarlas antes de continuar.')
        if 'problema_reportado' in columns:
            migration = BACKEND.parent / 'database/migrations/001_equipment_reported_fault.sql'
            db.execute(text(migration.read_text(encoding='utf-8')))
        elif 'falla_reportada' not in columns:
            raise RuntimeError('La tabla equipos no contiene la columna de falla esperada.')
        role = next((row for row in db.query(Role).order_by(Role.id).all() if row.code == 'recepcion'), None)
        if role is None:
            role = Role(nombre_rol='Recepcionista')
            db.add(role)
            db.flush()
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            if db.query(User).filter(User.correo == 'fixify.prueba@example.com').first():
                raise RuntimeError('El correo sintético ya pertenece a otra cuenta.')
            user = User(username=username, correo='fixify.prueba@example.com',
                        hashed_password=get_password_hash(password), rol=role)
            db.add(user)
            db.flush()
            created = True
        else:
            if not path.exists():
                raise RuntimeError('La cuenta ya existe; no se sobrescribe su contraseña.')
            saved = json.loads(path.read_text(encoding='utf-8'))
            password = saved['password']
        if not verify_password(password, user.hashed_password):
            raise RuntimeError('No coincide la credencial de prueba; no se modifica la cuenta.')
        identifier = user.id
        role_code = user.role
    if created:
        path.write_text(json.dumps({'username': username, 'password': password, 'role': role_code,
                                   'id': identifier}, indent=2) + '\n', encoding='utf-8')
    # Usa el flujo real de autenticación, no solo la comparación aislada del hash.
    from fastapi.security import OAuth2PasswordRequestForm
    from src.modules.auth.router import login
    from src.modules.equipment.repository import equipment_repository
    from src.modules.equipment.schema import EquipmentResponse
    from src.modules.clients.repository import client_repository
    from src.modules.clients.schema import ClientResponse
    with SessionLocal() as db:
        session = login(OAuth2PasswordRequestForm(username=username, password=password), db)
        assert session['role'] == role_code and session['access_token']
        for item in equipment_repository.get_all(db):
            EquipmentResponse.model_validate(item)
        for item in client_repository.get_all(db):
            ClientResponse.model_validate(item)
    print('Login y serialización de clientes/equipos verificados contra Supabase.')
    print(f'Usuario verificado: {username}; ID: {identifier}; rol: {role_code}.')
    print('Credenciales disponibles en backend/usuario_prueba.local.json (archivo local excluido de Git).')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # No imprimimos excepciones de conexión: podrían incluir credenciales/SQL.
        print('No se completó la operación:', type(error).__name__)
        sys.exit(1)
    finally:
        engine.dispose()
