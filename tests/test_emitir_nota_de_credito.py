"""
Caso de uso: Emitir Nota de Crédito C
Referencia: use-cases/emitir_nota_de_credito.md
"""
import pytest
from datetime import datetime

from facturacion_servicios.afip_enums import TipoFactura
from facturacion_servicios.create_pdf import build_template_context
from facturacion_servicios.voucher import _convert_data_for_voucher, get_invoice_number, get_cae


class TestDatosNotaDeCredito:
    """El AfipInvoiceData construido representa una Nota de Crédito C válida."""

    def test_tipo_comprobante(self, invoice_data_nota_de_credito):
        assert invoice_data_nota_de_credito.base_invoice_data.invoice_type == TipoFactura.nota_de_credito_c

    def test_codigo_afip(self, invoice_data_nota_de_credito):
        assert invoice_data_nota_de_credito.base_invoice_data.invoice_type.value == 13

    def test_comprobante_asociado_presente(self, invoice_data_nota_de_credito):
        assert invoice_data_nota_de_credito.base_invoice_data.comprobante_asociado is not None

    def test_comprobante_asociado_tipo(self, invoice_data_nota_de_credito):
        ca = invoice_data_nota_de_credito.base_invoice_data.comprobante_asociado
        assert ca.tipo == 11  # Factura C original

    def test_comprobante_asociado_nro(self, invoice_data_nota_de_credito):
        ca = invoice_data_nota_de_credito.base_invoice_data.comprobante_asociado
        assert ca.nro == 52

    def test_total(self, invoice_data_nota_de_credito):
        assert invoice_data_nota_de_credito.total_value == 800000.0


class TestVoucherWSFE:
    """_convert_data_for_voucher incluye CbtesAsoc con la referencia a la factura original."""

    @pytest.fixture
    def voucher(self, invoice_data_nota_de_credito):
        since = datetime(2026, 4, 1)
        until = datetime(2026, 4, 30)
        overdue = datetime(2026, 5, 10)
        return _convert_data_for_voucher(
            contribuyente=invoice_data_nota_de_credito.tax_payer,
            base_invoice_data=invoice_data_nota_de_credito.base_invoice_data,
            consumidor=invoice_data_nota_de_credito.consumer,
            invoice_number=1,
            date=datetime(2026, 4, 30),
            since=since,
            until=until,
            overdue=overdue,
            importe_total=invoice_data_nota_de_credito.total_value,
        )

    def test_cbte_tipo(self, voucher):
        assert voucher["CbteTipo"] == 13

    def test_cbtes_asoc_presente(self, voucher):
        assert "CbtesAsoc" in voucher

    def test_cbtes_asoc_tipo_factura_original(self, voucher):
        assert voucher["CbtesAsoc"][0]["Tipo"] == 11

    def test_cbtes_asoc_pto_vta(self, voucher):
        assert voucher["CbtesAsoc"][0]["PtoVta"] == 1

    def test_cbtes_asoc_nro(self, voucher):
        assert voucher["CbtesAsoc"][0]["Nro"] == 52

    def test_imp_iva_cero(self, voucher):
        assert voucher["ImpIVA"] == 0

    def test_imp_neto_igual_total(self, voucher):
        assert voucher["ImpNeto"] == voucher["ImpTotal"]


class TestOrquestacionVoucher:
    """get_invoice_number y get_cae orquestan correctamente el PuertoAFIP para Nota de Crédito."""

    def test_numero_comprobante_es_ultimo_mas_uno(self, mock_afip, invoice_data_nota_de_credito):
        numero = get_invoice_number(mock_afip,
                                    sales_location=invoice_data_nota_de_credito.tax_payer.sales_location,
                                    invoice_type=invoice_data_nota_de_credito.base_invoice_data.invoice_type)
        assert numero == 52  # ultimo_comprobante=51 + 1

    def test_get_cae_retorna_cae_y_vencimiento(self, mock_afip, invoice_data_nota_de_credito):
        since, until, overdue = invoice_data_nota_de_credito.period
        cae, vencimiento = get_cae(mock_afip, invoice_data_nota_de_credito,
                                   invoice_number=1, date=datetime(2026, 4, 30),
                                   since=since, until=until, overdue=overdue)
        assert cae == mock_afip.cae
        assert vencimiento == mock_afip.vencimiento_cae

    def test_get_cae_incluye_cbtes_asoc_en_datos_enviados(self, mock_afip, invoice_data_nota_de_credito):
        since, until, overdue = invoice_data_nota_de_credito.period
        get_cae(mock_afip, invoice_data_nota_de_credito,
                invoice_number=1, date=datetime(2026, 4, 30),
                since=since, until=until, overdue=overdue)
        datos_enviados = mock_afip.llamadas_crear[0]
        assert "CbtesAsoc" in datos_enviados


class TestContextoTemplate:
    """build_template_context expone las variables correctas para el PDF."""

    @pytest.fixture
    def contexto(self, invoice_data_nota_de_credito):
        return build_template_context(
            contribuyente=invoice_data_nota_de_credito.tax_payer,
            base_invoice_data=invoice_data_nota_de_credito.base_invoice_data,
            consumidor=invoice_data_nota_de_credito.consumer,
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
        assert contexto["document_label"] == "Nota de Crédito"

    def test_invoice_type_letra(self, contexto):
        assert contexto["invoice_type_letra"] == "C"

    def test_invoice_type_code(self, contexto):
        assert contexto["invoice_type_code"] == 13
