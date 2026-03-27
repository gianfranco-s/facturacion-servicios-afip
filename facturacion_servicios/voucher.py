from datetime import datetime, timedelta
from afip import Afip

from facturacion_servicios.afip_enums import TipoFactura, Concepto, Consumidor, Contribuyente, DatosBaseFactura


def get_cae(afip_client: Afip,
            tax_payer: Contribuyente,
            base_invoice_data: DatosBaseFactura,
            consumer: Consumidor,
            invoice_number: int,
            date: datetime,
            since: datetime,
            until: datetime,
            overdue: datetime,
            total_value: float,
            ) -> tuple[str]:
    """CAE stands for Código de Autorización Electrónico it has a code and an expiry date."""
    voucher_data = _convert_data_for_voucher(contribuyente=tax_payer,
                                base_invoice_data=base_invoice_data,
                                consumidor=consumer,
                                invoice_number=invoice_number,
                                date=date,
                                since=since,
                                until=until,
                                overdue=overdue,
                                importe_total=total_value)
    
    voucher = afip_client.ElectronicBilling.createVoucher(voucher_data)

    return voucher.get('CAE'), voucher.get('CAEFchVto')


def get_period(month: int) -> tuple[datetime]:
    """Calculates month_first_day, month_last_day, and overdue_date, 10 days after month_last_day"""
    current_year = datetime.now().year
    month_first_day = datetime(current_year, month, 1)
    
    if month == 12:
        month_last_day = datetime(current_year + 1, 1, 1) - timedelta(days=1)
    else:
        month_last_day = datetime(current_year, month + 1, 1) - timedelta(days=1)
    
    # Calculate the overdue date (10 days after the last day of the month)
    overdue_date = month_last_day + timedelta(days=10)
    
    return (month_first_day, month_last_day, overdue_date)


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

    return {
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
        # Para Factura C (monotributista): ImpNeto = ImpTotal, el resto en cero.
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
