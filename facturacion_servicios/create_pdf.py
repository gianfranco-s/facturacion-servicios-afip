from datetime import datetime
from pathlib import Path
from typing import List

from jinja2 import Template
from weasyprint import HTML, CSS

from facturacion_servicios import BASEDIR
from facturacion_servicios.afip_enums import Consumidor, Contribuyente, ServicioPrestado


def render_invoice(invoice_data: dict,
                   invoice_services: List[ServicioPrestado],
                   total_value: float,
                   template_dir: str = "facturacion_servicios",
                   template_filename: str = 'invoice_template.html',
                   export_file: bool = False) -> str:
    with open(BASEDIR / template_dir / template_filename, 'r') as f:
        invoice_template = Template(f.read())
    
    data = {
        **invoice_data,
        'invoice_services': invoice_services,
        'total_value': total_value
    }
    rendered_html = invoice_template.render(data)

    if export_file:
        with open(BASEDIR / "rendered_invoice.html", "w") as exported_file:
            exported_file.write(rendered_html)

    return rendered_html


def render_pdf(
    rendered_html: str,
    file_name: str,
    output_dir: str = ".",
    page_size: str = "A4",
    margin_top_cm: float = 1.0,
    margin_right_cm: float = 0.5,
    margin_bottom_cm: float = 1.0,
    margin_left_cm: float = 0.5
) -> str:
    """
    Render HTML → PDF using WeasyPrint, saving to `{output_dir}/{file_name}.pdf`.

    - page_size: any valid CSS size (named or dimension), defaults to "A4" portrait.
    - margins in centimeters (cm).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{file_name}.pdf"

    # Build our single @page rule:
    css = f"""
    @page {{
      size: {page_size};
      margin: {margin_top_cm}cm {margin_right_cm}cm
              {margin_bottom_cm}cm {margin_left_cm}cm;
    }}
    """
    page_css = CSS(string=css)

    # Render!
    HTML(string=rendered_html).write_pdf(
        target=str(pdf_path),
        stylesheets=[page_css]
    )
    return str(pdf_path)


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
        condicion_frente_al_iva=contribuyente.tax_situation.name,
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
        current_date=datetime.now().strftime(r"%d/%m/%Y"),
    )


if __name__ == '__main__':
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
        current_date=datetime.now().strftime(r"%d/%m/%Y"),
    )

    total_value = sum([serv.subtotal for serv in invoice_services])

    invoice = render_invoice(invoice_data, invoice_services, total_value)

    current_timestamp = datetime.today().strftime("%Y%m%d")
    name = f"factura_contribuyente_consumidor_{current_timestamp}"
    render_pdf(rendered_html=invoice, file_name=name)
