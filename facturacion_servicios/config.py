from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


__EXISTING_ENV_FILES = (".env.dev", ".env.prd")

class ConfigEntorno(BaseSettings):
    entorno: str  # used to select .env.<entorno>

    @property
    def env_file(self) -> str:
        env_file = f".env.{self.entorno}"
        if self.entorno not in __EXISTING_ENV_FILES:
            raise Exception("Invalid env file selected")
        return env_file


_config_entorno = ConfigEntorno()


class InvoiceSource(BaseSettings):
    """Rutas a los recursos necesarios para construir el comprobante."""
    invoice_source_dir: str = "./invoice_data"
    consumidor_filepath: str = f"{invoice_source_dir}/consumidor.json"
    contribuyente_filepath: str = f"{invoice_source_dir}/contribuyente.json"
    invoice_items_filepath: str = f"{invoice_source_dir}/invoice_items.json"
    base_invoice_data_filepath: str = f"{invoice_source_dir}/base_invoice_data.json"


class AfipAuth(BaseSettings):
    """Allows override of specific variables"""
    model_config = SettingsConfigDict(env_file=_config_entorno.env_file, env_file_encoding="utf-8")
    key_path: str
    cert_path: str
    afip_access_token: SecretStr
    cuit: str
    is_production: bool


class Settings(BaseSettings):
    is_mock: bool = True
    output_dir: str = "invoices"

    if not Path(output_dir).exists:
        Path(output_dir).mkdir(parents=True)


invoice_source = InvoiceSource()
afip_auth = AfipAuth()
settings = Settings()
