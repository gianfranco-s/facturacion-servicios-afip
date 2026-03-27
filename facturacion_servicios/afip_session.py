from afip import Afip

from facturacion_servicios.config import CERT_PATH, KEY_PATH, CUIT, ACCESS_TOKEN

cert = open(CERT_PATH).read()
key = open(KEY_PATH).read()

afip_session = Afip({
    "CUIT": CUIT,
    "cert": cert,
    "key": key,
    "access_token": ACCESS_TOKEN,
})
