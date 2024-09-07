import json

from typing import List
from datetime import datetime

from afip import Afip

from afip_enums import (Mes,
                        Concepto,
                        CondicionFrenteIVA,
                        Consumidor,
                        Contribuyente,
                        ServicioPrestado,
                        TipoDeDocumento,
                        TipoFactura,)
from create_pdf import render_invoice, create_invoice_through_afip, create_data_for_render
from voucher import get_data_for_voucher, get_invoice_number, get_period

BILLING_INFO_PATH = './billing_info.json'


def format_date(orig_date: str) -> str:
    """orig_date in format YYYYMMDD"""
    parsed_date = datetime.strptime(orig_date, '%Y%m%d')
    return parsed_date.strftime('%d/%m/%Y')


def load_billing_data(billing_info_file: str = BILLING_INFO_PATH) -> dict:
    with open(billing_info_file, 'r') as f:
        billing_data = json.load(f)
    return billing_data


def load_taxpayer(tax_payer: dict) -> Contribuyente:
    id_type = tax_payer.get('id_type')
    tax_situation = tax_payer.get('tax_situation').lower().replace(' ', '_')
    invoice_type = tax_payer.get('invoice_type').lower().replace(' ', '_')
    concept = tax_payer.get('concept')
    month_billed = tax_payer.get('month_billed')

    activity_since = tax_payer.get('activity_since')

    return Contribuyente(
        full_name=tax_payer.get('full_name'),
        id_type=TipoDeDocumento[id_type],
        id_nr=int(tax_payer.get('id_nr')),
        tax_situation=CondicionFrenteIVA[tax_situation],
        email=tax_payer.get('email'),
        month_billed=Mes[month_billed],
        invoice_type=TipoFactura[invoice_type],
        concept=Concepto[concept],
        sales_location=tax_payer.get('sales_location'),
        legal_address=tax_payer.get('legal_address'),
        id_before_tax=tax_payer.get('id_before_tax'),
        activity_since=format_date(activity_since),
    )


def load_services(services: List[dict]) -> List[ServicioPrestado]:
    invoice_services = []
    for serv in services:
        invoice_services.append(ServicioPrestado(
            servicio=serv.get('servicio'),
            cantidad=serv.get('cantidad'),
            precio_unit=serv.get('precio_unit'),
            bonif=serv.get('bonif'),
            imp_bonif=serv.get('imp_bonif'),
        ))
    return invoice_services


def load_customer(customer: dict) -> Consumidor:
    id_type = customer.get('id_type')
    tax_situation = customer.get('tax_situation').lower().replace(' ', '_')

    return Consumidor(
        full_name=customer.get('full_name'),
        id_type=TipoDeDocumento[id_type],
        id_nr=int(customer.get('id_nr')),
        tax_situation=CondicionFrenteIVA[tax_situation],
        email=customer.get('email'),
        legal_address=customer.get('legal_address'),
    )

def main(DEV_CUIT: int, month: Mes, customer_order: int) -> None:
    afip = Afip({ "CUIT":  DEV_CUIT})
    billing_data = load_billing_data()
    taxpayer = load_taxpayer(billing_data.get('tax-payer'))

    invoice_services = load_services(billing_data.get('services'))
    total_value = sum([serv.subtotal for serv in invoice_services])

    customer = load_customer(billing_data.get('consumers')[customer_order])


    current_date = int(datetime.today().strftime("%Y%m%d"))
    since, until, overdue = get_period(taxpayer.month_billed.value)

    invoice_number = get_invoice_number(afip_client=afip,
                                        sales_location=taxpayer.sales_location,
                                        invoice_type=taxpayer.invoice_type)

    data = get_data_for_voucher(contribuyente=taxpayer,
                                consumidor=customer,
                                invoice_number=invoice_number,
                                date=current_date,
                                since=since,
                                until=until,
                                overdue=overdue,
                                importe_total=total_value)

    voucher = afip.ElectronicBilling.createVoucher(data)


    invoice_data = create_data_for_render(contribuyente=taxpayer,
                                          consumidor=customer,
                                          CAE=voucher.get('CAE'),
                                          vencimiento_cae=voucher.get('CAEFchVto'),
                                          invoice_number=invoice_number,
                                          since=format_date(since),
                                          until=format_date(until),
                                          overdue=format_date(overdue))
    
    invoice = render_invoice(invoice_data, invoice_services, total_value)
    current_timestamp = datetime.today().strftime("%Y%m%d")
    name = f"factura_gsalomone_baitcon_{current_timestamp}"
    link = create_invoice_through_afip(afip_client=afip, rendered_html=invoice, file_name=name)
    print(link)


def get_prod_cuit() -> int | None:
    """get prod cuit"""
    # If none is provided, return None
    return None


def get_month_from_cli() -> int | None:
    """if none is provided, return current month"""
    # Use Enum Mes
    """
    class Mes(Enum):
        enero = 1
        febrero = 2
        marzo = 3
        abril = 4
    """
    return None

if __name__ == '__main__':
    with open('./credentials.json', 'r') as f:
        DEV_CUIT = json.load(f).get('dev').get('CUIT')

    PRD_CUIT = get_prod_cuit()
    main(PRD_CUIT or DEV_CUIT, month=Mes.agosto, customer_order=0)
