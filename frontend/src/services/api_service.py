import requests

class APIService:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.token = None

    def set_token(self, token):
        self.token = token

    def _headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _parse_error(self, res):
        """Formatea adecuadamente respuestas de error de FastAPI (strings o listas Pydantic)."""
        try:
            data = res.json()
            detail = data.get("detail", res.text)
            if isinstance(detail, list):
                # Errores de validación Pydantic
                msgs = [f"• {err.get('msg', 'Error en el campo ' + str(err.get('loc')))}" for err in detail]
                return "\n".join(msgs)
            return str(detail)
        except Exception:
            return res.text or "Error desconocido en el servidor"

    def login(self, username, password):
        url = f"{self.base_url}/auth/login"
        payload = {"username": username, "password": password}
        try:
            res = requests.post(url, data=payload, timeout=5)
            if res.status_code == 200:
                data = res.json()
                self.token = data.get("access_token")
                return True, data
            return False, self._parse_error(res)
        except Exception as e:
            return False, f"No se pudo conectar con el servidor: {str(e)}"

    def obtener_usuarios(self):
        url = f"{self.base_url}/usuarios/"
        try:
            res = requests.get(url, headers=self._headers(), timeout=5)
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def crear_usuario(self, username, password, role):
        url = f"{self.base_url}/usuarios/"
        payload = {"username": username, "password": password, "role": role}
        try:
            res = requests.post(url, json=payload, headers=self._headers(), timeout=5)
            if res.status_code in (200, 201):
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def obtener_clientes(self):
        url = f"{self.base_url}/clientes/"
        try:
            res = requests.get(url, headers=self._headers(), timeout=5)
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def crear_cliente(self, nombre, telefono, correo=None, direccion=None):
        url = f"{self.base_url}/clientes/"
        payload = {
            "nombre": nombre,
            "telefono": telefono,
            "correo": correo if correo else None,
            "direccion": direccion if direccion else None
        }
        try:
            res = requests.post(url, json=payload, headers=self._headers(), timeout=5)
            if res.status_code in (200, 201):
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def obtener_equipos(self):
        url = f"{self.base_url}/equipos/"
        try:
            res = requests.get(url, headers=self._headers(), timeout=5)
            if res.status_code == 200:
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

    def crear_equipo(self, tipo, marca, modelo, problema_reportado, client_id, numero_serie=None):
        url = f"{self.base_url}/equipos/"
        payload = {
            "tipo": tipo,
            "marca": marca,
            "modelo": modelo,
            "numero_serie": numero_serie if numero_serie else None,
            "problema_reportado": problema_reportado,
            "client_id": int(client_id)
        }
        try:
            res = requests.post(url, json=payload, headers=self._headers(), timeout=5)
            if res.status_code in (200, 201):
                return True, res.json()
            return False, self._parse_error(res)
        except Exception as e:
            return False, str(e)

api_client = APIService()