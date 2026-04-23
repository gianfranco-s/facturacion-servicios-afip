
import json
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

from facturacion_servicios.afip_enums import (Mes,
                        Concepto,
                        CondicionFrenteIVA,
                        Consumidor,
                        Contribuyente,
                        DatosBaseFactura,
                        ServicioPrestado,
                        TipoDeDocumento,
                        TipoFactura,)

@dataclass
class AfipInvoiceData:
    tax_payer: Contribuyente
    base_invoice_data: DatosBaseFactura
    invoice_services: list[ServicioPrestado]
    consumer: Consumidor

    @property
    def total_value(self) -> float:
        return sum([serv.subtotal for serv in self.invoice_services])

    @property
    def period(self) -> tuple[datetime, datetime, datetime]:
        since, until, overdue = _get_period(self.base_invoice_data.month_billed.value)
        if self.base_invoice_data.overdue_date is not None:
            overdue = datetime.strptime(self.base_invoice_data.overdue_date, "%Y-%m-%d")
        return since, until, overdue

    def __str__(self) -> str:
        def _serialize(obj):
            if isinstance(obj, Enum):
                return obj.name
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        sections = {
            "base_invoice_data": asdict(self.base_invoice_data),
            "tax_payer": asdict(self.tax_payer),
            "consumer": asdict(self.consumer),
            "invoice_services": [asdict(s) for s in self.invoice_services],
        }
        return json.dumps(sections, indent=2, default=_serialize)


def _get_period(month: int) -> tuple[datetime]:
    """Calculates month_first_day, month_last_day, and overdue_date, 10 days after month_last_day"""
    current_year = datetime.now().year
    month_first_day = datetime(current_year, month, 1)
    
    if month == 12:
        month_last_day = datetime(current_year + 1, 1, 1) - timedelta(days=1)
    else:
        month_last_day = datetime(current_year, month + 1, 1) - timedelta(days=1)
    
    # Calculate the overdue date (10 days after the last day of the month)
    overdue_date = month_last_day + timedelta(days=10)
    
    return (month_first_day, month_last_day, overdue_date)


class AfipInvoiceBuilder:
    def __init__(self,
                 consumidor_filepath: Path,
                 contribuyente_filepath: Path,
                 invoice_items_filepath: Path,
                 base_invoice_data_filepath: Path,
                 ) -> None:

        self.tax_payer=self._load_tax_payer(contribuyente_filepath)
        self.consumer=self._load_consumer(consumidor_filepath)
        self.base_invoice_data=self._load_base_invoice_data(base_invoice_data_filepath)
        self.invoice_services=self._load_invoice_items(invoice_items_filepath)

    def build(self) -> AfipInvoiceData:
        return AfipInvoiceData(
            tax_payer=self.tax_payer,
            consumer=self.consumer,
            base_invoice_data=self.base_invoice_data,
            invoice_services=self.invoice_services,
        )

    def _load_tax_payer(self, filepath: Path) -> Contribuyente:
        tax_payer_dict = self.__load_legal_person(filepath)
        return Contribuyente(**tax_payer_dict)

    def _load_consumer(self, filepath: Path) -> Consumidor:
        tax_payer_dict = self.__load_legal_person(filepath)
        return Consumidor(**tax_payer_dict)

    @staticmethod
    def _load_invoice_items(filepath: Path) -> list[ServicioPrestado]:
        """This function is geared towards services"""
        with open(filepath, "r") as f:
            invoice_items_list = json.load(f)

        return [ServicioPrestado(**item) for item in invoice_items_list]

    @staticmethod
    def _load_base_invoice_data(filepath: Path) -> DatosBaseFactura:
        """This function is highly coupled with the implementation of Mes, Concepto and TipoFactura"""
        with open(filepath, "r") as f:
            invoice_items_list = json.load(f)
        invoice_items_list["month_billed"] = Mes(invoice_items_list["month_billed"])
        invoice_items_list["concept"] = Concepto[invoice_items_list["concept"]]
        invoice_items_list["invoice_type"] = TipoFactura[invoice_items_list["invoice_type"]]
        return DatosBaseFactura(**invoice_items_list)

    @staticmethod
    def __load_legal_person(filepath: Path) -> dict:
        """This function is highly coupled with the implementation of TipoDeDocumento and CondicionFrenteIVA
        TODO: reduce coupling using pydantic"""
        with open(filepath, "r") as f:
            tax_payer_dict = json.load(f)
        tax_payer_dict["id_type"] = TipoDeDocumento[tax_payer_dict["id_type"]]
        tax_payer_dict["tax_situation"] = CondicionFrenteIVA[tax_payer_dict["tax_situation"]]
        return tax_payer_dict
