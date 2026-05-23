import pytest
from datetime import datetime

from facturacion_servicios.afip_enums import (
    Mes,
    Concepto,
    CondicionFrenteIVA,
    ComprobanteAsociado,
    Consumidor,
    Contribuyente,
    DatosBaseFactura,
    ServicioPrestado,
    TipoDeDocumento,
    TipoFactura,
)
from facturacion_servicios.afip_invoice_builder import AfipInvoiceData


# ---------------------------------------------------------------------------
# Mock del puerto AFIP — permite testear voucher.py sin llamar al SDK real
# ---------------------------------------------------------------------------

class MockPuertoAFIP:
    """Doble de test que implementa PuertoAFIP en memoria.

    Registra las llamadas recibidas para que los tests puedan inspeccionarlas.
    """

    def __init__(self, ultimo_comprobante: int = 51,
                 cae: str = "75314447442077",
                 vencimiento_cae: str = "2026-05-10") -> None:
        self.ultimo_comprobante = ultimo_comprobante
        self.cae = cae
        self.vencimiento_cae = vencimiento_cae
        # registros de llamadas
        self.llamadas_obtener: list[tuple] = []
        self.llamadas_crear: list[dict] = []

    def obtener_ultimo_comprobante(self, punto_venta: int, tipo_comprobante: int) -> int:
        self.llamadas_obtener.append((punto_venta, tipo_comprobante))
        return self.ultimo_comprobante

    def crear_comprobante(self, datos: dict) -> dict:
        self.llamadas_crear.append(datos)
        return {"CAE": self.cae, "CAEFchVto": self.vencimiento_cae}


@pytest.fixture
def mock_afip():
    return MockPuertoAFIP()


# ---------------------------------------------------------------------------
# Fixtures de dominio
# ---------------------------------------------------------------------------

@pytest.fixture
def contribuyente():
    return Contribuyente(
        full_name="SALOMONE GIANFRANCO",
        id_type=TipoDeDocumento.cuit,
        id_nr=23316378609,
        tax_situation=CondicionFrenteIVA.responsable_monotributo,
        email="gianfranco.s@gmail.com",
        legal_address="Miguel Andén 0 Piso:DPTO Dpto:2 - ElBolson, Río Negro",
        sales_location=1,
        id_before_tax=1440000,
        activity_since="01/12/2022",
    )


@pytest.fixture
def consumidor():
    return Consumidor(
        full_name="FIDEICOMISO COMPLEJO SOLARES",
        id_type=TipoDeDocumento.cuit,
        id_nr=30715560824,
        tax_situation=CondicionFrenteIVA.iva_responsable_inscripto,
        email="",
        legal_address="Miro 248 Piso:2 - Capital Federal, Ciudad de Buenos Aires",
    )


@pytest.fixture
def servicios():
    return [
        ServicioPrestado(
            servicio="Servicio de desarrollo — Abril 2026",
            cantidad=1,
            precio_unit=800000.0,
            bonif=0.0,
            imp_bonif=0.0,
        )
    ]


@pytest.fixture
def datos_base_factura():
    return DatosBaseFactura(
        month_billed=Mes.abril,
        concept=Concepto.servicios,
        invoice_type=TipoFactura.c,
    )


@pytest.fixture
def comprobante_asociado():
    return ComprobanteAsociado(tipo=11, pto_vta=1, nro=52)


@pytest.fixture
def datos_base_nota_de_credito(comprobante_asociado):
    return DatosBaseFactura(
        month_billed=Mes.abril,
        concept=Concepto.servicios,
        invoice_type=TipoFactura.nota_de_credito_c,
        comprobante_asociado=comprobante_asociado,
    )


@pytest.fixture
def invoice_data_factura(contribuyente, consumidor, servicios, datos_base_factura):
    return AfipInvoiceData(
        tax_payer=contribuyente,
        consumer=consumidor,
        invoice_services=servicios,
        base_invoice_data=datos_base_factura,
    )


@pytest.fixture
def invoice_data_nota_de_credito(contribuyente, consumidor, servicios, datos_base_nota_de_credito):
    return AfipInvoiceData(
        tax_payer=contribuyente,
        consumer=consumidor,
        invoice_services=servicios,
        base_invoice_data=datos_base_nota_de_credito,
    )
