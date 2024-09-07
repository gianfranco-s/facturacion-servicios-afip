from typing import Tuple
from datetime import datetime, timedelta
from afip import Afip

from afip_enums import TipoFactura, Concepto, Consumidor, Contribuyente


def get_period(month: int) -> Tuple[str]:
    """Calculates month_first_day, month_last_day, and overdue_date, 10 days after month_last_day"""
    current_year = datetime.now().year
    month_first_day = datetime(current_year, month, 1)
    
    if month == 12:
        month_last_day = datetime(current_year + 1, 1, 1) - timedelta(days=1)
    else:
        month_last_day = datetime(current_year, month + 1, 1) - timedelta(days=1)
    
    # Calculate the overdue date (10 days after the last day of the month)
    overdue_date = month_last_day + timedelta(days=10)
    
    return (month_first_day.strftime(r"%Y%m%d"), 
            month_last_day.strftime(r"%Y%m%d"), 
            overdue_date.strftime(r"%Y%m%d"))


def get_invoice_number(afip_client: Afip, sales_location: int, invoice_type: TipoFactura) -> str:
    last_voucher = afip_client.ElectronicBilling.getLastVoucher(sales_location, invoice_type.value)
    return last_voucher + 1


def get_data_for_voucher(contribuyente: Contribuyente,
                         consumidor: Consumidor,
                         invoice_number: int,
                         date: int,
                         since: str,
                         until: str,
                         overdue: str,
                         importe_total: float) -> dict:

    if contribuyente.concept == Concepto.productos:
        fecha_servicio_desde = None
        fecha_servicio_hasta = None
        fecha_vencimiento_pago = None

    else:
        fecha_servicio_desde = int(since)
        fecha_servicio_hasta = int(until)
        fecha_vencimiento_pago = int(overdue)

    return {
        "CantReg": 1, # Cantidad de facturas a registrar
        "PtoVta": contribuyente.sales_location,
        "CbteTipo": contribuyente.invoice_type.value, 
        "Concepto": contribuyente.concept.value,
        "DocTipo": consumidor.id_type.value,
        "DocNro": consumidor.id_nr,
        "CbteDesde": invoice_number,
        "CbteHasta": invoice_number,
        "CbteFch": date,
        "FchServDesde": fecha_servicio_desde,
        "FchServHasta": fecha_servicio_hasta,
        "FchVtoPago": fecha_vencimiento_pago,
        "ImpTotal": importe_total,
        "ImpTotConc": 0,  # Importe neto no gravado
        "ImpNeto": importe_total,
        "ImpOpEx": 0,
        "ImpIVA": 0,
        "ImpTrib": 0,  # Importe total de tributos
        "MonId": "PES",  # Tipo de moneda usada en la factura ("PES" = pesos argentinos) 
        "MonCotiz": 1  # Cotización de la moneda usada (1 para pesos argentinos)  
    }
