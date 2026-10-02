"""Transporte HTTP compartido; las rutas de negocio viven en cada service."""
import os
import httpx
from typing import TypeVar
from pydantic import ValidationError
from models.base import Contrato

Modelo = TypeVar('Modelo', bound=Contrato)


class ApiError(Exception):
    """Error legible de API; status_code identifica errores HTTP, si existen."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ApiClient:
    """Reutiliza conexiones HTTP y el token de la sesión de escritorio."""

    def __init__(self, base_url=None, transport=None):
        """base_url: servidor; transport: transporte opcional para pruebas sin red."""
        self.base_url = base_url or os.getenv('FIXIFY_API_URL', 'http://127.0.0.1:8000')
        self.token = None
        self._transport = transport
        self._client = None

    def set_token(self, token):
        """token: JWT vigente o None para cerrar la sesión local."""
        self.token = token

    async def request(self, method, path, *, authenticated=True, **kwargs):
        """method/path: operación HTTP (PUT, POST, GET, DELETE); kwargs: JSON, formulario o parámetros."""
        # Se crea y utiliza exclusivamente en el loop asyncio del trabajador.
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=5, transport=self._transport,
                follow_redirects=True,
            )
        headers = {'Authorization': f'Bearer {self.token}'} if authenticated and self.token else {}
        try:
            response = await self._client.request(method, path, headers=headers, **kwargs)
        except httpx.TimeoutException as exc:
            raise ApiError('El servidor tardó demasiado en responder.') from exc
        except httpx.RequestError as exc:
            raise ApiError('No se pudo conectar con el servidor.') from exc
        if response.is_error:
            raise ApiError(self._error_message(response), response.status_code)
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise ApiError('El servidor devolvió una respuesta inválida.') from exc

    @staticmethod
    def _error_message(response):
        """response: respuesta HTTP; convierte detail de FastAPI a texto breve."""
        try:
            detail = response.json().get('detail')
            if isinstance(detail, list):
                return '\n'.join(str(error.get('msg', 'Dato inválido')) for error in detail)
            if isinstance(detail, str):
                return detail
        except (ValueError, AttributeError, TypeError):
            pass
        return f'La solicitud falló (HTTP {response.status_code}).'

    async def aclose(self):
        """Libera conexiones al cerrar la aplicación."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class ModuleService:
    """Base para compartir transporte y validar listas sin duplicar HTTP."""

    def __init__(self, api):
        """api: ApiClient compartido por los módulos."""
        self.api = api

    @staticmethod
    def _parse(model: type[Modelo], data, *, entrada=False) -> Modelo:
        """model: contrato esperado; data: valores; entrada: distingue formulario de respuesta."""
        try:
            return model.model_validate(data)
        except ValidationError:
            # No incluimos valores inválidos: podrían contener contraseñas o tokens.
            origen = 'Los datos ingresados' if entrada else 'La respuesta del servidor'
            raise ApiError(f'{origen} no cumplen el contrato {model.__name__}.') from None

    async def _list(self, path, model: type[Modelo], **kwargs) -> list[Modelo]:
        """path: colección; model: contrato de cada registro; kwargs: filtros opcionales."""
        data = await self.api.request('GET', path, **kwargs)
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise ApiError('El servidor no devolvió una lista válida.')
        return [self._parse(model, item) for item in data]
