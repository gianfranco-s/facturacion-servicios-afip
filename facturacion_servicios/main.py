import json

from datetime import datetime

from afip import Afip

from facturacion_servicios.afip_enums import (Mes,
                        Concepto,
                        CondicionFrenteIVA,
                        Consumidor,
                        Contribuyente,
                        DatosBaseFactura,
                        ServicioPrestado,
                        TipoDeDocumento,
                        TipoFactura,)
from facturacion_servicios.afip_session import afip_session
from facturacion_servicios.create_pdf import render_invoice, render_pdf, create_data_for_render
from facturacion_servicios.voucher import get_data_for_voucher, get_invoice_number, get_period


def _load_tax_payer(filepath: str = "facturacion_servicios/contribuyente.json") -> Contribuyente:
    """This function is highly coupled with the implementation of TipoDeDocumento and CondicionFrenteIVA
    TODO: reduce coupling using pydantic"""
    with open(filepath, "r") as f:
        tax_payer_dict = json.load(f)
    tax_payer_dict["id_type"] = TipoDeDocumento[tax_payer_dict["id_type"]]
    tax_payer_dict["tax_situation"] = CondicionFrenteIVA(tax_payer_dict["tax_situation"])
    return Contribuyente(**tax_payer_dict)


def _load_consumer(filepath: str = "facturacion_servicios/consumidor.json") -> Consumidor:
    """This function is highly coupled with the implementation of TipoDeDocumento and CondicionFrenteIVA
    TODO: reduce coupling using pydantic"""
    with open(filepath, "r") as f:
        consumer_dict = json.load(f)
    consumer_dict["id_type"] = TipoDeDocumento[consumer_dict["id_type"]]
    consumer_dict["tax_situation"] = CondicionFrenteIVA[consumer_dict["tax_situation"]]
    
    return Consumidor(**consumer_dict)


def _load_invoice_items(filepath: str = "facturacion_servicios/invoice_items.json") -> list[ServicioPrestado]:
    """This function is geared towards services"""
    with open(filepath, "r") as f:
        invoice_items_list = json.load(f)
    
    return [ServicioPrestado(**item) for item in invoice_items_list]
    

def main(month: Mes, afip: Afip = afip_session) -> None:

    tax_payer = _load_tax_payer()

    base_invoice_data = DatosBaseFactura(
        month_billed=month,
        concept=Concepto.servicios,
        invoice_type=TipoFactura.c,
    )

    invoice_services = _load_invoice_items()
    total_value = sum([serv.subtotal for serv in invoice_services])

    consumer = _load_consumer()

    current_date = int(datetime.today().strftime("%Y%m%d"))
    since, until, overdue = get_period(base_invoice_data.month_billed.value)

    invoice_number = get_invoice_number(afip_client=afip,
                                        sales_location=tax_payer.sales_location,
                                        invoice_type=base_invoice_data.invoice_type)

    data = get_data_for_voucher(contribuyente=tax_payer,
                                base_invoice_data=base_invoice_data,
                                consumidor=consumer,
                                invoice_number=invoice_number,
                                date=current_date,
                                since=since.strftime(r"%Y%m%d"),
                                until=until.strftime(r"%Y%m%d"),
                                overdue=overdue.strftime(r"%Y%m%d"),
                                importe_total=total_value)

    voucher = afip.ElectronicBilling.createVoucher(data)

    invoice_data = create_data_for_render(contribuyente=tax_payer,
                                          base_invoice_data=base_invoice_data,
                                          consumidor=consumer,
                                          CAE=voucher.get('CAE'),
                                          vencimiento_cae=voucher.get('CAEFchVto'),
                                          invoice_number=invoice_number,
                                          since=since.strftime(r"%d/%m/%Y"),
                                          until=until.strftime(r"%d/%m/%Y"),
                                          overdue=overdue.strftime(r"%d/%m/%Y"))
    
    invoice_html = render_invoice(invoice_data, invoice_services, total_value)
    current_timestamp = datetime.today().strftime("%Y%m%d")
    name = f"factura_gsalomone_baitcon_{current_timestamp}"
    render_pdf(rendered_html=invoice_html, file_name=name)
    print(name)


def mock_main(month: Mes):
    """No connection to ARCA API"""
    tax_payer = _load_tax_payer()
    consumer = _load_consumer()
    invoice_services = _load_invoice_items()
    total_value = sum([serv.subtotal for serv in invoice_services])

    since, until, overdue = get_period(month.value)

    invoice_data = dict(
        invoice_type=TipoFactura.c.name.upper(),
        invoice_type_code=TipoFactura.c.value,
        razon_social=tax_payer.full_name,
        domicilio_comercial=tax_payer.legal_address,
        condicion_frente_al_iva=tax_payer.tax_situation.name,
        sales_location=tax_payer.sales_location,
        invoice_number='00000026',
        contribuyente_cuit=tax_payer.id_nr,
        id_before_tax=tax_payer.id_before_tax,
        activity_since=tax_payer.activity_since,
        valid_since=since.strftime(r"%d/%m/%Y"),
        valid_until=until.strftime(r"%d/%m/%Y"),
        overdue=overdue.strftime(r"%d/%m/%Y"),
        consumidor_cuit=consumer.id_nr,
        consumidor_name=consumer.full_name,
        consumidor_frente_iva=consumer.tax_situation.name,
        consumidor_domicilio=consumer.legal_address,
        CAE='123456abcd',
        vencimiento_cae='22/06/1985',
        current_date=datetime.now().strftime(r"%d/%m/%Y"),
    )

    invoice = render_invoice(invoice_data, invoice_services, total_value)

    current_timestamp = datetime.today().strftime("%Y%m%d")
    name = f"factura_contribuyente_consumidor_{current_timestamp}"
    render_pdf(rendered_html=invoice, file_name=name)


if __name__ == '__main__':
    import os
    IS_MOCK = os.getenv("IS_MOCK", "True").lower() in ("1", "true")
    if IS_MOCK:
        mock_main(month=Mes.agosto)

    else:
        print("WARNING: this communicates with ARCA")
        main(month=Mes.agosto)
