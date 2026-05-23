import socket
import time
import logging
from functools import wraps

from afip import Afip
from pydantic import SecretStr

logger = logging.getLogger(__name__)

_ERRORES_DE_RED = (socket.gaierror, ConnectionError, OSError, TimeoutError)


def reintentar_en_red(intentos: int = 3, espera: float = 2.0):
    """Decorador que reintenta una función ante errores de red transientes.

    Captura errores de DNS, conexión y timeout — típicos de llamadas a afipsdk
    cuando la resolución DNS falla de forma intermitente.

    Args:
        intentos: Cantidad máxima de intentos (default: 3).
        espera: Segundos de espera entre reintentos (default: 2).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ultimo_error = None
            for intento in range(1, intentos + 1):
                try:
                    return func(*args, **kwargs)
                except _ERRORES_DE_RED as e:
                    ultimo_error = e
                    if intento < intentos:
                        logger.warning(
                            "'%s' falló por error de red (intento %d/%d): %s. "
                            "Reintentando en %.0fs...",
                            func.__name__, intento, intentos, e, espera,
                        )
                        time.sleep(espera)
                    else:
                        logger.error(
                            "'%s' falló tras %d intentos: %s",
                            func.__name__, intentos, e,
                        )
            raise ultimo_error
        return wrapper
    return decorator


class AdaptadorAfipSDK:
    """Adaptador sobre el SDK externo de afipsdk.

    Implementa PuertoAFIP encapsulando las llamadas al cliente Afip.
    Toda la lógica de infraestructura (reintentos, formato de red) vive aquí;
    el dominio nunca importa este módulo directamente.
    """

    def __init__(self, cliente: Afip) -> None:
        self._cliente = cliente

    @classmethod
    def desde_credenciales(cls,
                           cert_path: str,
                           key_path: str,
                           cuit: str,
                           afipsdk_access_token: SecretStr,
                           is_production: bool) -> "AdaptadorAfipSDK":
        """Crea el adaptador a partir de las credenciales de ARCA.

        Construye el cliente del SDK internamente; el tipo Afip no necesita
        salir nunca de este módulo.
        """
        cert = open(cert_path).read()
        key = open(key_path).read()
        cliente = Afip({
            "CUIT": cuit,
            "cert": cert,
            "key": key,
            "access_token": afipsdk_access_token.get_secret_value(),
            "production": is_production,
        })
        return cls(cliente)

    @reintentar_en_red(intentos=3, espera=2)
    def obtener_ultimo_comprobante(self, punto_venta: int, tipo_comprobante: int) -> int:
        """Consulta a ARCA el último comprobante emitido para el punto de venta y tipo dados."""
        return self._cliente.ElectronicBilling.getLastVoucher(punto_venta, tipo_comprobante)

    @reintentar_en_red(intentos=3, espera=2)
    def crear_comprobante(self, datos: dict) -> dict:
        """Envía los datos del comprobante a ARCA y retorna la respuesta con CAE y vencimiento."""
        return self._cliente.ElectronicBilling.createVoucher(datos)
