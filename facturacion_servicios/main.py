import json
from datetime import datetime

from afip import Afip

from afip_enums import TipoDeDocumento, TipoFactura, Concepto, Mes, CondicionFrenteIVA, Consumidor, Contribuyente
from create_pdf import render_invoice, create_invoice_through_afip, create_data_for_render
from voucher import get_data_for_voucher, get_invoice_number, get_period

with open('./credentials.json', 'r') as f:
    DEV_CUIT = json.load(f).get('dev').get('CUIT')


def main(CUIT: int, month: Mes) -> None:
    afip = Afip({ "CUIT":  CUIT})

    gsalomone = Contribuyente(
        full_name='SALOMONE GIANFRANCO',
        id_type=TipoDeDocumento.cuit,
        id_nr=23316378609,
        tax_situation=CondicionFrenteIVA.responsable_monotributo,
        email='gianfranco.s@gmail.com',
        month_billed=month,
        invoice_type=TipoFactura.factura_c,
        concept=Concepto.servicios,
        units=80,
        unit_amount=20_000.00,
        sales_location=2,
        legal_address='Miguel Andén 0 Piso:DPTO Dpto:2 - ElBolson, Río Negro',
        id_before_tax=1440000,
        activity_since='01/12/2022',
    )

    baitcon = Consumidor(
        full_name='BAITCON S.A.',
        id_type=TipoDeDocumento.cuit,
        id_nr=30709425389,
        tax_situation=CondicionFrenteIVA.iva_responsable_inscripto,
        email='facturas_baitcon@datco.net',
        legal_address='Jujuy Av. 1956 - Capital Federal, Ciudad de Buenos Aires',
    )

    current_date = int(datetime.today().strftime("%Y%m%d"))
    since, until, overdue = get_period(gsalomone.month_billed.value)

    invoice_number = get_invoice_number(afip_client=afip,
                                        sales_location=gsalomone.sales_location,
                                        invoice_type=gsalomone.invoice_type)

    data = get_data_for_voucher(contribuyente=gsalomone,
                                consumidor=baitcon,
                                invoice_number=invoice_number,
                                date=current_date,
                                since=since,
                                until=until,
                                overdue=overdue)

    voucher = afip.ElectronicBilling.createVoucher(data)

    invoice_data = create_data_for_render(contribuyente=gsalomone,
                                          consumidor=baitcon,
                                          CAE=voucher.get('CAE'),
                                          vencimiento_cae=voucher.get('vencimiento_cae'),
                                          invoice_number=invoice_number,
                                          since=since,
                                          until=until,
                                          overdue=overdue)

    invoice = render_invoice(invoice_data)
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
    PRD_CUIT = get_prod_cuit()
    main(PRD_CUIT or DEV_CUIT, month=Mes.agosto)
