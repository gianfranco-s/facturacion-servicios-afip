from datetime import datetime

from afip import Afip
from jinja2 import Template

from afip_enums import Consumidor, Contribuyente


def render_invoice(invoice_data: dict, template_filename: str = 'invoice_template.html') -> str:
    with open(f'./{template_filename}', 'r') as f:
        invoice_template = Template(f.read())
    rendered_html = invoice_template.render(invoice_data)
    return rendered_html


def create_invoice_through_afip(afip_client: Afip, rendered_html: str, file_name: str) -> str:
    options = {
    "width": 8,  # Ancho de pagina en pulgadas. Usar 3.1 para ticket
    "marginLeft": 0.4,  # Margen izquierdo en pulgadas. Usar 0.1 para ticket 
    "marginRight": 0.4,  # Margen derecho en pulgadas. Usar 0.1 para ticket 
    "marginTop": 0.4,  # Margen superior en pulgadas. Usar 0.1 para ticket 
    "marginBottom": 0.4  # Margen inferior en pulgadas. Usar 0.1 para ticket 
    }

    res = afip_client.ElectronicBilling.createPDF({
        "html": rendered_html,
        "file_name": file_name,
        "options": options
    })

    return res["file"]


def create_data_for_render(contribuyente: Contribuyente,
                           consumidor: Consumidor,
                           CAE: str,
                           vencimiento_cae: str,
                           invoice_number: str,
                           since: str,
                           until: str,
                           overdue: str
                           ) -> dict:
    return dict(
        razon_social=contribuyente.full_name,
        invoice_type=contribuyente.invoice_type.value,
        domicilio_comercial=contribuyente.legal_address,
        condicion_frente_al_iva=contribuyente.tax_situation.value,
        sales_location=contribuyente.sales_location,
        invoice_number=invoice_number,
        contribuyente_cuit=contribuyente.id_nr,
        id_before_tax=contribuyente.id_before_tax,
        activity_since=contribuyente.activity_since,
        valid_since=since,
        valid_until=until,
        overdue=overdue,
        consumidor_cuit=consumidor.id_nr,
        consumidor_name=consumidor.full_name,
        consumidor_frente_iva=consumidor.tax_situation.value,
        consumidor_domicilio=consumidor.legal_address,
        CAE=CAE,
        vencimiento_cae=vencimiento_cae,
    )


if __name__ == '__main__':
    afip = Afip({ "CUIT": 20409378472 })


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
        valid_since='ab',
        valid_until='cd',
        overdue='ef',
        consumidor_cuit='30709425389',
        consumidor_name='consumidor S.A.',
        consumidor_frente_iva='IVA Responsable Inscripto',
        consumidor_domicilio='Jujuy Av. 1956 - Capital Federal, Ciudad de Buenos Aires',
        CAE='123456abcd',
        vencimiento_cae='22/06/1985',
    )

    invoice = render_invoice(invoice_data)
    current_timestamp = datetime.today().strftime("%Y%m%d")
    name = f"factura_contribuyente_consumidor_{current_timestamp}"
    link = create_invoice_through_afip(afip_client=afip, rendered_html=invoice, file_name=name)
    print(link)
