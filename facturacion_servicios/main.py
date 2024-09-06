import json

from afip import Afip

from afip_enums import TipoDeDocumento, TipoFactura, Concepto, Mes, CondicionFrenteIVA, Consumidor, Contribuyente
from voucher import get_data_for_voucher, get_invoice_number, get_period

with open('./credentials.json', 'r') as f:
    DEV_CUIT = json.load(f).get('dev').get('CUIT')


def main(CUIT: int = DEV_CUIT) -> None:
    afip = Afip({ "CUIT":  CUIT})

    gsalomone = Contribuyente(
        full_name='Gianfranco Salomone',
        id_type=TipoDeDocumento.cuit,
        id_nr='23316378609',
        tax_situation=CondicionFrenteIVA.responsable_monotributo,
        email='gianfranco.s@gmail.com',
        month_billed=Mes.agosto,
        invoice_type=TipoFactura.factura_c,
        concept=Concepto.servicios,
        units=80,
        unit_amount=20_000.00,
        sales_location=2
    )

    baitcon = Consumidor(
        full_name='BAITCON S.A.',
        id_type=TipoDeDocumento.cuit,
        id_nr='23316378609',
        tax_situation=CondicionFrenteIVA.iva_responsable_inscripto,
        email='facturas_baitcon@datco.net',
    )

    since, until, overdue = get_period(gsalomone.month_billed.value)
    invoice_number = get_invoice_number(afip_client=afip, sales_location=gsalomone.sales_location, invoice_type=gsalomone.invoice_type)
    data = get_data_for_voucher(contribuyente=gsalomone,
                                consumidor=baitcon,
                                invoice_number=invoice_number,
                                since=since,
                                until=until,
                                overdue=overdue)

    res = afip.ElectronicBilling.createVoucher(data)

    print(res.items())


if __name__ == '__main__':
    main()
