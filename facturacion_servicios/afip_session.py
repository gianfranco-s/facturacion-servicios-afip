from afip import Afip

from facturacion_servicios import BASEDIR, CERT_FILE, KEY_FILE, CUIT

cert = open(CERT_FILE).read()
key = open(KEY_FILE).read()

afip_session = Afip({
    "CUIT": CUIT,
    "cert": cert,
    "key": key
})
