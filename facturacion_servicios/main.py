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


def main(month: Mes, afip: Afip = afip_session) -> None:

    gsalomone = Contribuyente(
        full_name='SALOMONE GIANFRANCO',
        id_type=TipoDeDocumento.cuit,
        id_nr=23316378609,
        tax_situation=CondicionFrenteIVA.responsable_monotributo,
        email='gianfranco.s@gmail.com',
        sales_location=2,
        legal_address='Miguel Andén 0 Piso:DPTO Dpto:2 - ElBolson, Río Negro',
        id_before_tax=1440000,
        activity_since='01/12/2022',
    )

    base_invoice_data = DatosBaseFactura(
        month_billed=month,
        concept=Concepto.servicios,
        invoice_type=TipoFactura.factura_c,
    )

    invoice_services = [
        ServicioPrestado(
            servicio='Hora de desarrollo',
            cantidad=80,
            precio_unit=19366.40,
            bonif=0.0,
            imp_bonif=0.0,
        ),
        ServicioPrestado(
            servicio='Hora de consultoría',
            cantidad=12,
            precio_unit=10,
            bonif=0.0,
            imp_bonif=0.0,
        ),
    ]

    total_value = sum([serv.subtotal for serv in invoice_services])

    baitcon = Consumidor(
        full_name='BAITCON S.A.',
        id_type=TipoDeDocumento.cuit,
        id_nr=30709425389,
        tax_situation=CondicionFrenteIVA.iva_responsable_inscripto,
        email='facturas_baitcon@datco.net',
        legal_address='Jujuy Av. 1956 - Capital Federal, Ciudad de Buenos Aires',
    )

    current_date = int(datetime.today().strftime("%Y%m%d"))
    since, until, overdue = get_period(base_invoice_data.month_billed.value)

    invoice_number = get_invoice_number(afip_client=afip,
                                        sales_location=gsalomone.sales_location,
                                        invoice_type=base_invoice_data.invoice_type)

    data = get_data_for_voucher(contribuyente=gsalomone,
                                base_invoice_data=base_invoice_data,
                                consumidor=baitcon,
                                invoice_number=invoice_number,
                                date=current_date,
                                since=since.strftime(r"%Y%m%d"),
                                until=until.strftime(r"%Y%m%d"),
                                overdue=overdue.strftime(r"%Y%m%d"),
                                importe_total=total_value)

    voucher = afip.ElectronicBilling.createVoucher(data)

    invoice_data = create_data_for_render(contribuyente=gsalomone,
                                          base_invoice_data=base_invoice_data,
                                          consumidor=baitcon,
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
    invoice_services = [
        ServicioPrestado(
            servicio='Hora de desarrollo',
            cantidad=4,
            precio_unit=1234,
            bonif=0.0,
            imp_bonif=0.0,
        ),
        ServicioPrestado(
            servicio='Hora de consultoría',
            cantidad=12,
            precio_unit=10,
            bonif=0.0,
            imp_bonif=0.0,
        ),
    ]

    since, until, overdue = get_period(month.value)

    invoice_data = dict(
        razon_social='SALOMONE GIANFRANCO',
        invoice_type='C',
        domicilio_comercial='Miguel Andén 0 Piso:DPTO Dpto:2 - ElBolson, Río Negro',
        condicion_frente_al_iva='Responsable Monotributo',
        sales_location='00002',
        invoice_number='00000026',
        contribuyente_cuit='23316378609',
        id_before_tax='1440000',
        activity_since='01/12/2022',
        valid_since=since,
        valid_until=until,
        overdue=overdue,
        consumidor_cuit='30709425389',
        consumidor_name='consumidor S.A.',
        consumidor_frente_iva='IVA Responsable Inscripto',
        consumidor_domicilio='Jujuy Av. 1956 - Capital Federal, Ciudad de Buenos Aires',
        CAE='123456abcd',
        vencimiento_cae='22/06/1985',
        current_date=datetime.now().strftime(r"%d/%m/%Y"),
    )

    total_value = sum([serv.subtotal for serv in invoice_services])

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
