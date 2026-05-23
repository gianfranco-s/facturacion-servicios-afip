import logging

from datetime import datetime
from time import sleep
from pathlib import Path

from afip import Afip

from facturacion_servicios.config import settings, afip_auth, invoice_source
from facturacion_servicios.logging_conf import setup_logging
from facturacion_servicios.afip_qr import invoice_validation_url, generate_qr
from facturacion_servicios.afip_session import get_afip_session
from facturacion_servicios.create_pdf import render_invoice, render_pdf, build_template_context
from facturacion_servicios.voucher import get_cae, get_invoice_number
from facturacion_servicios.afip_invoice_builder import AfipInvoiceBuilder, AfipInvoiceData

setup_logging()
logger = logging.getLogger(__name__)


def _get_valid_afip_data(afip_client: Afip, invoice_data: AfipInvoiceData) -> tuple:
    logger.warning("Comunicándose con ARCA (a través de servers de afipsdk)")
    tax_payer = invoice_data.tax_payer
    since, until, overdue = invoice_data.period
    current_date = datetime.today()

    invoice_number = get_invoice_number(
        afip_client=afip_client,
        sales_location=tax_payer.sales_location,
        invoice_type=invoice_data.base_invoice_data.invoice_type,
    )
    logger.info(f"Número de comprobante: {invoice_number}")

    CAE, vencimiento_cae = get_cae(
        afip_client=afip_client,
        invoice_data=invoice_data,
        invoice_number=invoice_number,
        date=current_date,
        since=since,
        until=until,
        overdue=overdue,
    )
    logger.info(f"CAE recibido: {CAE} (vto. {vencimiento_cae})")

    validation_url = invoice_validation_url(
        cuit=tax_payer.id_nr,
        cae=int(CAE),
        fecha_emision=current_date,
        tipo_factura_code=invoice_data.base_invoice_data.invoice_type.value,
        punto_venta=tax_payer.sales_location,
        numero_comprobante=invoice_number,
        importe_total=invoice_data.total_value,
        tipo_doc_receptor_code=invoice_data.consumer.id_type.value,
        numero_doc_receptor=invoice_data.consumer.id_nr,
    )
    return invoice_number, CAE, vencimiento_cae, validation_url, since, until, overdue


def _get_valid_mock_data(invoice_data: AfipInvoiceData, *args, **kwargs) -> tuple:
    since, until, overdue = invoice_data.period
    invoice_number, CAE, vencimiento_cae, validation_url = 52, 75314447442077, '22/06/1985', invoice_validation_url(is_mock=True)
    return invoice_number, CAE, vencimiento_cae, validation_url, since, until, overdue


def _build_output_filepath(output_dir: str,
                           consumer_name_raw: str,
                           tax_payer_name_raw: str,
                           id_nr: str,
                           invoice_nr: str,
                           sufijo: str = "",
                           ) -> str:
    consumer_name = consumer_name_raw.lower().replace(" ", "_").replace(".", "_")
    tax_payer_name = tax_payer_name_raw.lower().replace(" ", "_").replace(".", "_")
    return Path(output_dir) / f"{tax_payer_name}_{id_nr}_{invoice_nr}_{consumer_name}{sufijo}"


def _get_watermark_text(is_mock: bool, is_production: bool) -> str | None:
    if is_mock:
        return "PRUEBA LOCAL"
    if not is_production:
        return "HOMOLOGACIÓN"
    return None


def generate_invoice(afip_client: Afip | None,
                     invoice_source_files: dict[str, str],
                     output_dir: Path,
                     watermark_text: str | None = None) -> None:
    builder = AfipInvoiceBuilder(**invoice_source_files)

    invoice_data: AfipInvoiceData = builder.build()
    logger.info("1. Datos de factura")
    logger.info("\n%s", invoice_data)
    sleep(5)


    logger.info("2. Obteniendo datos de AFIP (nro factura, CAE, vencimiento, URL de validación)")
    get_valid_data_fn = _get_valid_afip_data if afip_client is not None else _get_valid_mock_data
    invoice_number, CAE, vencimiento_cae, validation_url, since, until, overdue = get_valid_data_fn(afip_client=afip_client, invoice_data=invoice_data)

    logger.info("3. Generando QR para validación de factura")
    qr_code = generate_qr(validation_url)

    logger.info("4. Generando HTML")
    template_context = build_template_context(
        contribuyente=invoice_data.tax_payer,
        base_invoice_data=invoice_data.base_invoice_data,
        consumidor=invoice_data.consumer,
        CAE=CAE,
        vencimiento_cae=vencimiento_cae,
        invoice_number=invoice_number,
        since=since.strftime(r"%d/%m/%Y"),
        until=until.strftime(r"%d/%m/%Y"),
        overdue=overdue.strftime(r"%d/%m/%Y"),
        qr_code=qr_code,
        validation_url=validation_url,
    )
    invoice_html = render_invoice(template_context, invoice_data.invoice_services, invoice_data.total_value, watermark_text)

    logger.info("5. Generando PDF")
    file_name = _build_output_filepath(output_dir=output_dir,
                                       consumer_name_raw=invoice_data.consumer.full_name,
                                       tax_payer_name_raw=invoice_data.tax_payer.full_name,
                                       id_nr=invoice_data.tax_payer.id_nr,
                                       invoice_nr=invoice_number,
                                       sufijo=invoice_data.base_invoice_data.invoice_type.sufijo_archivo)

    pdf_path = render_pdf(rendered_html=invoice_html, file_name=file_name)
    logger.info(f"  PDF generado: {pdf_path}")


def main() -> None:
    afip_client = None if settings.is_mock else get_afip_session(**afip_auth.model_dump())
    output_dir = settings.output_dir if afip_auth.is_production else f"{settings.output_dir}-dev"
    generate_invoice(afip_client=afip_client,
                     invoice_source_files=invoice_source.model_dump(exclude={"invoice_source_dir"}),
                     output_dir=output_dir,
                     watermark_text=_get_watermark_text(settings.is_mock, afip_auth.is_production))


if __name__ == "__main__":
    main()
