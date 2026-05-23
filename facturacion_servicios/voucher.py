import socket
import time
import logging
from datetime import datetime
from functools import wraps

from afip import Afip

from facturacion_servicios.afip_enums import TipoFactura, Concepto, Consumidor, Contribuyente, DatosBaseFactura
from facturacion_servicios.afip_invoice_builder import AfipInvoiceData

logger = logging.getLogger(__name__)

_ERRORES_DE_RED = (socket.gaierror, ConnectionError, OSError, TimeoutError)


def reintentar_en_red(intentos: int = 3, espera: float = 2.0):
    """Decorador que reintenta una función ante errores de red transientes.

    Captura errores de DNS, conexión y timeout — típicos de llamadas a afipsdk
    cuando la resolución DNS falla de forma intermitente.

    Args:
        intentos: Cantidad máxima de intentos (default: 3).
        espera: Segundos de espera entre reintentos (default: 2).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ultimo_error = None
            for intento in range(1, intentos + 1):
                try:
                    return func(*args, **kwargs)
                except _ERRORES_DE_RED as e:
                    ultimo_error = e
                    if intento < intentos:
                        logger.warning(
                            "'%s' falló por error de red (intento %d/%d): %s. "
                            "Reintentando en %.0fs...",
                            func.__name__, intento, intentos, e, espera,
                        )
                        time.sleep(espera)
                    else:
                        logger.error(
                            "'%s' falló tras %d intentos: %s",
                            func.__name__, intentos, e,
                        )
            raise ultimo_error
        return wrapper
    return decorator


@reintentar_en_red(intentos=3, espera=2)
def get_cae(afip_client: Afip,
            invoice_data: AfipInvoiceData,
            invoice_number: int,
            date: datetime,
            since: datetime,
            until: datetime,
            overdue: datetime,
            ) -> tuple[str]:
    """CAE stands for Código de Autorización Electrónico it has a code and an expiry date."""
    voucher_data = _convert_data_for_voucher(contribuyente=invoice_data.tax_payer,
                                base_invoice_data=invoice_data.base_invoice_data,
                                consumidor=invoice_data.consumer,
                                invoice_number=invoice_number,
                                date=date,
                                since=since,
                                until=until,
                                overdue=overdue,
                                importe_total=invoice_data.total_value)

    voucher = afip_client.ElectronicBilling.createVoucher(voucher_data)

    return voucher.get('CAE'), voucher.get('CAEFchVto')


@reintentar_en_red(intentos=3, espera=2)
def get_invoice_number(afip_client: Afip, sales_location: int, invoice_type: TipoFactura) -> str:
    """Connects to ARCA to find out the last emitted voucher."""
    last_voucher = afip_client.ElectronicBilling.getLastVoucher(sales_location, invoice_type.value)
    return last_voucher + 1


def _convert_data_for_voucher(contribuyente: Contribuyente,
                         base_invoice_data: DatosBaseFactura,
                         consumidor: Consumidor,
                         invoice_number: int,
                         date: datetime,
                         since: datetime,
                         until: datetime,
                         overdue: datetime,
                         importe_total: float) -> dict:
    """Convert invoice data into the values required by ARCA."""
    if base_invoice_data.concept == Concepto.productos:
        fecha_servicio_desde = None
        fecha_servicio_hasta = None
        fecha_vencimiento_pago = None

    else:
        # Formato valido: aaaammdd
        fecha_servicio_desde = int(since.strftime(r"%Y%m%d"))
        fecha_servicio_hasta = int(until.strftime(r"%Y%m%d"))
        fecha_vencimiento_pago = int(overdue.strftime(r"%Y%m%d"))

    result = {
        "CantReg": 1, # Cantidad de facturas a registrar
        "PtoVta": contribuyente.sales_location,
        "CbteTipo": base_invoice_data.invoice_type.value,
        "Concepto": base_invoice_data.concept.value,
        "DocTipo": consumidor.id_type.value,
        "DocNro": consumidor.id_nr,
        "CbteDesde": invoice_number,
        "CbteHasta": invoice_number,
        "CbteFch": int(date.strftime("%Y%m%d")),
        "FchServDesde": fecha_servicio_desde,
        "FchServHasta": fecha_servicio_hasta,
        "FchVtoPago": fecha_vencimiento_pago,
        # Para Factura C y Nota de Crédito C (monotributista): ImpNeto = ImpTotal, el resto en cero.
        # ImpTotal debe ser igual a la suma de todos los campos Imp*.
        "ImpTotal": importe_total,
        "ImpTotConc": 0,  # Importe neto no gravado
        "ImpNeto": importe_total,
        "ImpOpEx": 0,
        "ImpIVA": 0,
        "ImpTrib": 0,  # Otros tributos (percepciones, etc.) — no aplica a monotributista
        "MonId": "PES",  # Tipo de moneda usada en la factura ("PES" = pesos argentinos)
        "MonCotiz": 1,  # Cotización de la moneda usada (1 para pesos argentinos)
        "CondicionIVAReceptorId": consumidor.tax_situation.value,
    }

    if base_invoice_data.comprobante_asociado:
        ca = base_invoice_data.comprobante_asociado
        result["CbtesAsoc"] = [{"Tipo": ca.tipo, "PtoVta": ca.pto_vta, "Nro": ca.nro}]

    return result
