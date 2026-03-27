import json

from datetime import datetime
from pathlib import Path

from afip import Afip

from facturacion_servicios.config import JSON_DIR, ENV_NAME
from facturacion_servicios.afip_enums import (Mes,
                        Concepto,
                        CondicionFrenteIVA,
                        Consumidor,
                        Contribuyente,
                        DatosBaseFactura,
                        ServicioPrestado,
                        TipoDeDocumento,
                        TipoFactura,)
from facturacion_servicios.afip_qr import invoice_validation_url, generate_qr
from facturacion_servicios.afip_session import afip_session
from facturacion_servicios.create_pdf import render_invoice, render_pdf, create_data_for_render
from facturacion_servicios.voucher import get_cae, get_invoice_number, get_period


def __load_legal_person(filepath: Path) -> dict:
    """This function is highly coupled with the implementation of TipoDeDocumento and CondicionFrenteIVA
    TODO: reduce coupling using pydantic"""
    with open(filepath, "r") as f:
        tax_payer_dict = json.load(f)
    tax_payer_dict["id_type"] = TipoDeDocumento[tax_payer_dict["id_type"]]
    tax_payer_dict["tax_situation"] = CondicionFrenteIVA[tax_payer_dict["tax_situation"]]
    return tax_payer_dict


def _load_tax_payer(filepath: Path = JSON_DIR / "contribuyente.json") -> Contribuyente:
    tax_payer_dict = __load_legal_person(filepath)
    return Contribuyente(**tax_payer_dict)


def _load_consumer(filepath: Path = JSON_DIR / "consumidor.json") -> Consumidor:
    tax_payer_dict = __load_legal_person(filepath)    
    return Consumidor(**tax_payer_dict)


def _load_invoice_items(filepath: Path = JSON_DIR / "invoice_items.json") -> list[ServicioPrestado]:
    """This function is geared towards services"""
    with open(filepath, "r") as f:
        invoice_items_list = json.load(f)
    
    return [ServicioPrestado(**item) for item in invoice_items_list]


def _load_base_invoice_data(filepath: Path = JSON_DIR / "base_invoice_data.json") -> DatosBaseFactura:
    """This function is highly coupled with the implementation of Mes, Concepto and TipoFactura"""
    with open(filepath, "r") as f:
        invoice_items_list = json.load(f)
    invoice_items_list["month_billed"] = Mes(invoice_items_list["month_billed"])
    invoice_items_list["concept"] = Concepto[invoice_items_list["concept"]]
    invoice_items_list["invoice_type"] = TipoFactura[invoice_items_list["invoice_type"]]
    return DatosBaseFactura(**invoice_items_list)


def main(afip_client: Afip | None, env_name: str) -> None:

    tax_payer = _load_tax_payer()

    base_invoice_data = _load_base_invoice_data()

    invoice_services = _load_invoice_items()
    total_value = sum([serv.subtotal for serv in invoice_services])

    consumer = _load_consumer()

    current_date = datetime.today()
    since, until, overdue = get_period(base_invoice_data.month_billed.value)

    if afip_client is not None:
        print(f"WARNING: this communicates with ARCA {env_name=}")
        invoice_number = get_invoice_number(afip_client=afip_client,
                                            sales_location=tax_payer.sales_location,
                                            invoice_type=base_invoice_data.invoice_type)
        
        CAE, vencimiento_cae = get_cae(afip_client=afip_client,
                                    tax_payer=tax_payer,
                                    base_invoice_data=base_invoice_data,
                                    consumer=consumer,
                                    invoice_number=invoice_number,
                                    date=current_date,
                                    since=since,
                                    until=until,
                                    overdue=overdue,
                                    total_value=total_value)

        validation_url = invoice_validation_url(
            cuit=tax_payer.id_nr,
            cae=int(CAE),
            fecha_emision=current_date,
            tipo_factura_code=base_invoice_data.invoice_type.value,
            punto_venta=tax_payer.sales_location,
            numero_comprobante=invoice_number,
            importe_total=total_value,
            tipo_doc_receptor_code=consumer.id_type.value,
            numero_doc_receptor=consumer.id_nr
        )

    else:
        invoice_number = 52
        CAE=75314447442077
        vencimiento_cae='22/06/1985'
        validation_url = invoice_validation_url(is_mock=True)

    qr_code = generate_qr(validation_url)

    invoice_data = create_data_for_render(contribuyente=tax_payer,
                                          base_invoice_data=base_invoice_data,
                                          consumidor=consumer,
                                          CAE=CAE,
                                          vencimiento_cae=vencimiento_cae,
                                          invoice_number=invoice_number,
                                          since=since.strftime(r"%d/%m/%Y"),
                                          until=until.strftime(r"%d/%m/%Y"),
                                          overdue=overdue.strftime(r"%d/%m/%Y"),
                                          qr_code=qr_code,
                                          validation_url=validation_url)
    
    invoice_html = render_invoice(invoice_data, invoice_services, total_value)

    consumer_name = consumer.full_name.lower().replace(" ", "_").replace(".", "_")
    tax_payer_name = tax_payer.full_name.lower().replace(" ", "_").replace(".", "_")
    file_name = f"{tax_payer_name}_{tax_payer.id_nr}_{invoice_number}_{consumer_name}"
    render_pdf(rendered_html=invoice_html, file_name=file_name)


if __name__ == '__main__':
    import os
    IS_MOCK = os.getenv("IS_MOCK", "True").lower() in ("1", "true")
    afip_client = afip_session if not IS_MOCK else None

    main(afip_client=afip_client, env_name=ENV_NAME)
