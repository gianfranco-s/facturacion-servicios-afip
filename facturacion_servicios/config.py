from os import getenv
from pathlib import Path

BASEDIR = Path(__file__).parents[1]
CERTS_DIR = BASEDIR / "certs"
JSON_DIR = BASEDIR / "invoice_data"

ENV_NAME = getenv("AFIP_ENV", "dev")
OUTPUT_DIR = BASEDIR / f"invoices{'' if ENV_NAME == 'prd' else '-dev'}"
IS_MOCK = getenv("IS_MOCK", "True").lower() in ("1", "true")

if not OUTPUT_DIR.exists():
    OUTPUT_DIR.mkdir(parents=True)

VALID_ENV_NAMES = ("dev", "prd")
if ENV_NAME not in VALID_ENV_NAMES:
    raise Exception(f"Invalid {ENV_NAME=}. Must be wither of {VALID_ENV_NAMES}.")

IS_PRODUCTION = ENV_NAME == "prd"

cert_file = {
    "dev": "gsalomoneDnHomologacion.cert",
    "prd": "facturador-py_56aaab496237fb5f.crt",
}

key_file = {
    "dev": "gsalomone-dev-privkey",
    "prd": "gsalomone-prd-privkey",
}

CERT_PATH = CERTS_DIR / cert_file.get(ENV_NAME)
KEY_PATH = CERTS_DIR / key_file.get(ENV_NAME)
CUIT = 23316378609

ACCESS_TOKEN = getenv("AFIP_ACCESS_TOKEN")
