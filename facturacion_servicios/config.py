from os import getenv
from pathlib import Path

BASEDIR = Path(__file__).parents[1]
JSON_DIR = BASEDIR / "invoice_data"

ENV_NAME = getenv("AFIP_ENV", "dev")

VALID_ENV_NAMES = ("dev", "prd")
if ENV_NAME not in VALID_ENV_NAMES:
    raise Exception(f"Invalid {ENV_NAME=}. Must be wither of {VALID_ENV_NAMES}.")

cert_file = {
    "dev": "gsalomoneDnHomologacion.cert",
    "prd": "facturador-py_56aaab496237fb5f.crt",
}

key_file = {
    "dev": "gsalomone-dev-privkey",
    "prd": "gsalomone-prd-privkey",
}

CERT_PATH = BASEDIR / cert_file.get(ENV_NAME)
KEY_PATH = BASEDIR / key_file.get(ENV_NAME)
CUIT = 23316378609
ACCESS_TOKEN = getenv("AFIP_ACCESS_TOKEN")
