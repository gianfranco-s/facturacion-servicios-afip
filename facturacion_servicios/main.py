import logging

from datetime import datetime

from afip import Afip

from facturacion_servicios.config import JSON_DIR, ENV_NAME
from facturacion_servicios.logging_conf import setup_logging

from facturacion_servicios.afip_qr import invoice_validation_url, generate_qr
from facturacion_servicios.afip_session import afip_session
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
    return 52, 75314447442077, '22/06/1985', invoice_validation_url(is_mock=True), since, until, overdue


def main(afip_client: Afip | None) -> None:
    builder = AfipInvoiceBuilder(
        consumidor_filepath=JSON_DIR / "consumidor.json",
        contribuyente_filepath=JSON_DIR / "contribuyente.json",
        invoice_items_filepath=JSON_DIR / "invoice_items.json",
        base_invoice_data_filepath=JSON_DIR / "base_invoice_data.json",
    )

    invoice_data: AfipInvoiceData = builder.build()
    logger.info("\n%s", invoice_data)

    get_valid_data_fn = _get_valid_afip_data if afip_client is not None else _get_valid_mock_data
    invoice_number, CAE, vencimiento_cae, validation_url, since, until, overdue = get_valid_data_fn(afip_client=afip_client, invoice_data=invoice_data)

    qr_code = generate_qr(validation_url)

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
        validation_url=validation_url
    )

    invoice_html = render_invoice(template_context, invoice_data.invoice_services, invoice_data.total_value)

    consumer_name = invoice_data.consumer.full_name.lower().replace(" ", "_").replace(".", "_")
    tax_payer_name = invoice_data.tax_payer.full_name.lower().replace(" ", "_").replace(".", "_")
    file_name = f"{tax_payer_name}_{invoice_data.tax_payer.id_nr}_{invoice_number}_{consumer_name}"
    pdf_path = render_pdf(rendered_html=invoice_html, file_name=file_name)
    logger.info(f"PDF generado: {pdf_path}")


if __name__ == '__main__':
    import os
    
    IS_MOCK = os.getenv("IS_MOCK", "True").lower() in ("1", "true")
    afip_client = afip_session if not IS_MOCK else None

    logger.info("==================================")
    logger.info(f"======= Environment: {ENV_NAME} =======")
    logger.info("==================================")
    main(afip_client=afip_client)
