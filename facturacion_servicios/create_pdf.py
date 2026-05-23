from datetime import datetime
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

from facturacion_servicios.afip_enums import ComprobanteAsociado, Consumidor, Contribuyente, ServicioPrestado, DatosBaseFactura


def render_invoice(invoice_data: dict,
                   invoice_services: List[ServicioPrestado],
                   total_value: float,
                   watermark_text: str | None = None,
                   template_dir: str = "facturacion_servicios",
                   template_filename: str = 'invoice_template.html',) -> str:

    loader = FileSystemLoader(template_dir)
    jinja_env = Environment(loader=loader, autoescape=True)
    jinja_env.filters["money"] = _money
    jinja_env.filters["num_format"] = _num_format

    invoice_template = jinja_env.get_template(template_filename)

    data = {
        **invoice_data,
        'invoice_services': invoice_services,
        'total_value': total_value,
        'watermark_text': watermark_text,
    }
    rendered_html = invoice_template.render(data)

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
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{file_name}.pdf"

    css = f"""
    @page {{
      size: {page_size};
      margin: {margin_top_cm}cm {margin_right_cm}cm
              {margin_bottom_cm}cm {margin_left_cm}cm;
    }}
    """
    page_css = CSS(string=css)

    HTML(string=rendered_html).write_pdf(
        target=str(pdf_path),
        stylesheets=[page_css]
    )
    return str(pdf_path)


def build_template_context(contribuyente: Contribuyente,
                           base_invoice_data: DatosBaseFactura,
                           consumidor: Consumidor,
                           CAE: str,
                           vencimiento_cae: str,
                           invoice_number: str,
                           since: str,
                           until: str,
                           overdue: str,
                           qr_code: str,
                           validation_url: str,) -> dict:
    return dict(
        razon_social=contribuyente.full_name,
        domicilio_comercial=contribuyente.legal_address,
        condicion_frente_al_iva=contribuyente.tax_situation.name,
        sales_location=contribuyente.sales_location,
        contribuyente_cuit=contribuyente.id_nr,
        id_before_tax=contribuyente.id_before_tax,
        activity_since=contribuyente.activity_since,
        invoice_type_letra=base_invoice_data.invoice_type.letra,
        invoice_type_code=base_invoice_data.invoice_type.value,
        document_label=base_invoice_data.invoice_type.etiqueta,
        invoice_number=invoice_number,
        valid_since=since,
        valid_until=until,
        overdue=overdue,
        consumidor_cuit=consumidor.id_nr,
        consumidor_name=consumidor.full_name,
        consumidor_frente_iva=consumidor.tax_situation.name,
        consumidor_domicilio=consumidor.legal_address,
        CAE=CAE,
        vencimiento_cae=vencimiento_cae,
        current_date=datetime.now().strftime(r"%d/%m/%Y"),
        qr_code=qr_code,
        validation_url=validation_url,
        comprobante_asociado_label=_format_comprobante_asociado_label(base_invoice_data.comprobante_asociado),
    )


def _format_comprobante_asociado_label(ca: ComprobanteAsociado | None) -> str | None:
    """
    Formatea la referencia al comprobante original para mostrar en el PDF.
    Ej: ComprobanteAsociado(tipo=11, pto_vta=1, nro=4) → "Fac. C: 00001-00000004"
    """
    if ca is None:
        return None
    _tipo_labels = {
        11: "Fac. C",
        13: "N.Cred. C",
    }
    label = _tipo_labels.get(ca.tipo, f"Tipo {ca.tipo}")
    return f"{label}: {ca.pto_vta:05d}-{ca.nro:08d}"


def _num_format(value: float | int) -> str:
    """Format 1150000.0 → '1.150.000,00' (sin símbolo de moneda)."""
    s = f"{value:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _money(value: float | int) -> str:
    """
    Format a float like 1234567.89 → "$ 1.234.567,89"
    Format a float like 12345 → "$ 1.234,00"
    """
    s = f"{value:,.2f}"  # "1,234,567.89"
    return "$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")
