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
	iva_responsable_inscripto = 1
	iva_sujeto_exento = 4
	consumidor_final = 5
	responsable_monotributo = 6
	sujeto_no_categorizado = 7
	proveedor_del_exterior = 8
	cliente_del_exterior = 9
	iva_liberado = 10
	monotributista_social = 13
	iva_no_alcanzado = 15
	monotributo_trabajador_independiente_promovido = 16


@dataclass
class Consumidor:
	full_name: str
	id_type: TipoDeDocumento
	id_nr: int
	tax_situation: CondicionFrenteIVA
	email: str
	legal_address: str


@dataclass
class Contribuyente(Consumidor):
	sales_location: int  # punto de venta
	id_before_tax: int
	activity_since: str


@dataclass
class DatosBaseFactura:
	month_billed: Mes
	concept: Concepto
	invoice_type: TipoFactura


@dataclass
class ServicioPrestado:
	servicio: str
	cantidad: float
	precio_unit: float
	bonif: float
	imp_bonif: float
	codigo: int | str = ''
	unidad: str = 'unidades'
	subtotal: float = 0.0

	def __post_init__(self) -> None:
		self.subtotal = self.cantidad * self.precio_unit
