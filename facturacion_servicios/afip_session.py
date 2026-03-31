from afip import Afip
from pydantic import SecretStr

def get_afip_session(cert_path: str,
                     key_path: str,
                     cuit: str,
                     afip_access_token: SecretStr,
                     is_production: bool) -> Afip:
    cert = open(cert_path).read()
    key = open(key_path).read()

    return Afip({
        "CUIT": cuit,
        "cert": cert,
        "key": key,
        "access_token": afip_access_token.get_secret_value(),
        "production": is_production
    })
