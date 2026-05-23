"""
Caso de uso: Emitir Factura C
Referencia: use-cases/emitir_factura.md
"""
import pytest
from datetime import datetime

from facturacion_servicios.afip_enums import TipoFactura
from facturacion_servicios.create_pdf import build_template_context
from facturacion_servicios.voucher import _convert_data_for_voucher, get_invoice_number, get_cae


class TestDatosFactura:
    """El AfipInvoiceData construido representa una Factura C válida."""

    def test_tipo_comprobante(self, invoice_data_factura):
        assert invoice_data_factura.base_invoice_data.invoice_type == TipoFactura.c

    def test_codigo_afip(self, invoice_data_factura):
        assert invoice_data_factura.base_invoice_data.invoice_type.value == 11

    def test_sin_comprobante_asociado(self, invoice_data_factura):
        assert invoice_data_factura.base_invoice_data.comprobante_asociado is None

    def test_total(self, invoice_data_factura):
        assert invoice_data_factura.total_value == 800000.0


class TestVoucherWSFE:
    """_convert_data_for_voucher produce el dict correcto para ARCA."""

    @pytest.fixture
    def voucher(self, invoice_data_factura):
        since = datetime(2026, 4, 1)
        until = datetime(2026, 4, 30)
        overdue = datetime(2026, 5, 10)
        return _convert_data_for_voucher(
            contribuyente=invoice_data_factura.tax_payer,
            base_invoice_data=invoice_data_factura.base_invoice_data,
            consumidor=invoice_data_factura.consumer,
            invoice_number=1,
            date=datetime(2026, 4, 30),
            since=since,
            until=until,
            overdue=overdue,
            importe_total=invoice_data_factura.total_value,
        )

    def test_cbte_tipo(self, voucher):
        assert voucher["CbteTipo"] == 11

    def test_importe_total(self, voucher):
        assert voucher["ImpTotal"] == 800000.0

    def test_imp_iva_cero(self, voucher):
        # Monotributista: no hay IVA discriminado
        assert voucher["ImpIVA"] == 0

    def test_imp_neto_igual_total(self, voucher):
        assert voucher["ImpNeto"] == voucher["ImpTotal"]

    def test_sin_cbtes_asoc(self, voucher):
        assert "CbtesAsoc" not in voucher


class TestOrquestacionVoucher:
    """get_invoice_number y get_cae orquestan correctamente el PuertoAFIP."""

    def test_numero_comprobante_es_ultimo_mas_uno(self, mock_afip, invoice_data_factura):
        numero = get_invoice_number(mock_afip,
                                    sales_location=invoice_data_factura.tax_payer.sales_location,
                                    invoice_type=invoice_data_factura.base_invoice_data.invoice_type)
        assert numero == 52  # ultimo_comprobante=51 + 1

    def test_get_invoice_number_consulta_punto_venta_correcto(self, mock_afip, invoice_data_factura):
        get_invoice_number(mock_afip,
                           sales_location=invoice_data_factura.tax_payer.sales_location,
                           invoice_type=invoice_data_factura.base_invoice_data.invoice_type)
        punto_venta, _ = mock_afip.llamadas_obtener[0]
        assert punto_venta == invoice_data_factura.tax_payer.sales_location

    def test_get_cae_retorna_cae_y_vencimiento(self, mock_afip, invoice_data_factura):
        since, until, overdue = invoice_data_factura.period
        cae, vencimiento = get_cae(mock_afip, invoice_data_factura,
                                   invoice_number=1, date=datetime(2026, 4, 30),
                                   since=since, until=until, overdue=overdue)
        assert cae == mock_afip.cae
        assert vencimiento == mock_afip.vencimiento_cae

    def test_get_cae_invoca_crear_comprobante_una_vez(self, mock_afip, invoice_data_factura):
        since, until, overdue = invoice_data_factura.period
        get_cae(mock_afip, invoice_data_factura,
                invoice_number=1, date=datetime(2026, 4, 30),
                since=since, until=until, overdue=overdue)
        assert len(mock_afip.llamadas_crear) == 1


class TestContextoTemplate:
    """build_template_context expone las variables correctas para el PDF."""

    @pytest.fixture
    def contexto(self, invoice_data_factura):
        return build_template_context(
            contribuyente=invoice_data_factura.tax_payer,
            base_invoice_data=invoice_data_factura.base_invoice_data,
            consumidor=invoice_data_factura.consumer,
            CAE="75314447442077",
            vencimiento_cae="2026-05-10",
            invoice_number=1,
            since="01/04/2026",
            until="30/04/2026",
            overdue="10/05/2026",
            qr_code="data:image/png;base64,abc",
            validation_url="https://www.afip.gob.ar/fe/qr/?p=abc",
        )

    def test_document_label(self, contexto):
        assert contexto["document_label"] == "Factura"

    def test_invoice_type_letra(self, contexto):
        assert contexto["invoice_type_letra"] == "C"

    def test_invoice_type_code(self, contexto):
        assert contexto["invoice_type_code"] == 11
