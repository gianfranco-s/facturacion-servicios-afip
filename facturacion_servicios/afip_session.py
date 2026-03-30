from afip import Afip

from facturacion_servicios.config import CERT_PATH, KEY_PATH, CUIT, ACCESS_TOKEN


def get_afip_session(is_production: bool) -> Afip:
    cert = open(CERT_PATH).read()
    key = open(KEY_PATH).read()

    return Afip({
        "CUIT": CUIT,
        "cert": cert,
        "key": key,
        "access_token": ACCESS_TOKEN,
        "production": is_production
    })
