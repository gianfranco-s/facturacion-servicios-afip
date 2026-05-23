"""
Caso de uso: Emitir Nota de Crédito C
Referencia: use-cases/emitir_nota_de_credito.md
"""
import pytest
from datetime import datetime

from facturacion_servicios.afip_enums import TipoFactura
from facturacion_servicios.create_pdf import build_template_context
from facturacion_servicios.voucher import _convert_data_for_voucher


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
