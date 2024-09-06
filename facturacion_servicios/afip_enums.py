from dataclasses import dataclass
from enum import Enum


class TipoFactura(Enum):
	factura_c = 11


class Concepto(Enum):
	productos = 1
	servicios = 2
	productos_y_servicios = 3


class TipoDeDocumento(Enum):
	cuit = 80
	cuil = 86
	dni = 96
	consumidor_final = 99


class Mes(Enum):
	enero = 1
	febrero = 2
	marzo = 3
	abril = 4
	mayo = 5
	junio = 6
	julio = 7
	agosto = 8
	septiembre = 9
	octubre = 10
	noviembre = 11
	diciembre = 12


class CondicionFrenteIVA(Enum):
	iva_responsable_inscripto = 'IVA Responsable Inscripto'
	responsable_monotributo = 'Responsable Monotributo'
	# Completar


@dataclass
class Consumidor:
    full_name: str
    id_type: TipoDeDocumento
    id_nr: int
    tax_situation: CondicionFrenteIVA
    email: str


@dataclass
class Contribuyente(Consumidor):
    month_billed: Mes
    concept: Concepto
    unit_amount: float
    units: float
    invoice_type: TipoFactura
    sales_location: int  # punto de venta
