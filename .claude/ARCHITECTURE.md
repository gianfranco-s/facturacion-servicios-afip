# Arquitectura del Proyecto

> **Para agentes:** leer este archivo antes de explorar el código. Actualizarlo cuando se agreguen módulos, clases, funciones relevantes o se cambien responsabilidades.

Herramienta para emitir comprobantes electrónicos (facturas para monotributistas) ante AFIP/ARCA, generando un PDF firmado con CAE.

---

## Estructura de directorios

```
facturacion-servicios-afip/
├── facturacion_servicios/        # Paquete principal
│   ├── main.py                   # Punto de entrada; orquesta el flujo completo
│   ├── afip_enums.py             # Enums y dataclasses del dominio
│   ├── afip_invoice_builder.py   # Carga de JSONs y ensamblado del comprobante
│   ├── voucher.py                # Comunicación con ARCA: número, CAE, conversión de datos
│   ├── afip_qr.py                # Generación de URL de validación y código QR
│   ├── afip_session.py           # Autenticación con AFIP via certificado + token
│   ├── config.py                 # Configuración via pydantic-settings
│   ├── create_pdf.py             # Renderizado HTML (Jinja2) → PDF (WeasyPrint)
│   └── invoice_template.html     # Plantilla Jinja2 del comprobante
├── invoice_data/                 # Datos de entrada (JSON) — se editan antes de cada emisión
│   ├── base_invoice_data.json    # Tipo de comprobante, concepto, mes facturado
│   ├── contribuyente.json        # Datos del emisor (monotributista)
│   ├── consumidor.json           # Datos del receptor (cliente)
│   └── invoice_items.json        # Ítems / servicios del comprobante
├── invoices/                     # PDFs generados en producción
├── invoices-dev/                 # PDFs generados en mock/homologación
├── certs/                        # Certificados y claves privadas AFIP
├── docker/                       # Dockerfile
├── .env / .env.dev / .env.prd    # Variables de entorno por ambiente
└── pyproject.toml
```

---

## Flujo de ejecución

```
main()  [main.py]
  │
  ├─ get_afip_session()               [afip_session.py]   Crea cliente AFIP (cert + token)
  │
  └─ generate_invoice()               [main.py]
       │
       ├─ AfipInvoiceBuilder.build()  [afip_invoice_builder.py]  Lee 4 JSONs → AfipInvoiceData
       │
       ├─ get_invoice_number()        [voucher.py]   Consulta ARCA: último nro + 1
       ├─ get_cae()                   [voucher.py]   Envía voucher a ARCA → (CAE, CAEFchVto)
       │    └─ _convert_data_for_voucher()           Mapea AfipInvoiceData → dict WSFE
       │
       ├─ invoice_validation_url()    [afip_qr.py]   Construye URL con payload Base64
       ├─ generate_qr()               [afip_qr.py]   Devuelve data URI PNG del QR
       │
       ├─ build_template_context()    [create_pdf.py]  Prepara dict para Jinja2
       ├─ render_invoice()            [create_pdf.py]  Renderiza HTML con invoice_template.html
       └─ render_pdf()                [create_pdf.py]  HTML → PDF con WeasyPrint
```

En modo **mock** (`IS_MOCK=true`), `get_afip_session()` no se llama y `_get_valid_afip_data` es reemplazado por `_get_valid_mock_data` (valores fijos hardcodeados en `main.py`).

---

## Modelos del dominio — `afip_enums.py`

### Enums

```python
class TipoFactura(Enum):
    c = 11                          # Factura C (monotributista)
    # nota_de_credito_c = 13       # ← agregar aquí para Nota de Crédito C

class Concepto(Enum):
    productos = 1
    servicios = 2
    productos_y_servicios = 3

class TipoDeDocumento(Enum):
    cuit = 80
    cuil = 86
    dni = 96
    consumidor_final = 99

class CondicionFrenteIVA(Enum):
    iva_responsable_inscripto = 1
    iva_sujeto_exento = 4
    consumidor_final = 5
    responsable_monotributo = 6
    # ... (ver archivo para lista completa)

class Mes(Enum):
    enero = 1  # ... diciembre = 12
```

### Dataclasses

```python
@dataclass
class Consumidor:
    full_name: str
    id_type: TipoDeDocumento
    id_nr: int
    tax_situation: CondicionFrenteIVA
    email: str
    legal_address: str

@dataclass
class Contribuyente(Consumidor):   # extiende Consumidor
    sales_location: int             # punto de venta
    id_before_tax: int
    activity_since: str

@dataclass
class DatosBaseFactura:
    month_billed: Mes
    concept: Concepto
    invoice_type: TipoFactura
    overdue_date: str | None        # "YYYY-MM-DD"; None = cálculo automático

@dataclass
class ServicioPrestado:
    servicio: str
    cantidad: float
    precio_unit: float
    bonif: float
    imp_bonif: float
    codigo: int | str = ''
    unidad: str = 'unidades'
    subtotal: float = 0.0           # calculado en __post_init__: cantidad × precio_unit
```

---

## `afip_invoice_builder.py`

```python
@dataclass
class AfipInvoiceData:
    tax_payer: Contribuyente
    base_invoice_data: DatosBaseFactura
    invoice_services: list[ServicioPrestado]
    consumer: Consumidor

    @property
    def total_value(self) -> float: ...   # suma de subtotales
    @property
    def period(self) -> tuple[datetime, datetime, datetime]: ...  # (since, until, overdue)


class AfipInvoiceBuilder:
    # Constructor: recibe 4 rutas de archivo
    def __init__(self, consumidor_filepath, contribuyente_filepath,
                 invoice_items_filepath, base_invoice_data_filepath): ...
    def build(self) -> AfipInvoiceData: ...
```

**Acoplamiento importante:** `_load_base_invoice_data` convierte strings a enums (`Mes`, `Concepto`, `TipoFactura`) usando `Enum[key]` / `Enum(value)`. Al agregar un nuevo `TipoFactura`, el JSON puede usar el nombre del miembro (`"nota_de_credito_c"`).

---

## `voucher.py`

```python
def get_invoice_number(afip_client, sales_location: int, invoice_type: TipoFactura) -> int:
    # Llama a afip_client.ElectronicBilling.getLastVoucher(sales_location, invoice_type.value)
    # Devuelve último + 1

def get_cae(afip_client, invoice_data: AfipInvoiceData, invoice_number, date, since, until, overdue) -> tuple[str, str]:
    # Devuelve (CAE, CAEFchVto)

def _convert_data_for_voucher(...) -> dict:
    # Genera el dict que espera ElectronicBilling.createVoucher()
    # Campos clave: CbteTipo (= invoice_type.value), PtoVta, DocTipo, DocNro,
    #               ImpTotal, ImpNeto (= ImpTotal para monotributista), ImpIVA=0
    # Si concept == productos: FchServDesde/Hasta/VtoPago = None
```

---

## `afip_qr.py`

```python
def invoice_validation_url(cuit, cae, fecha_emision, tipo_factura_code, punto_venta,
                            numero_comprobante, importe_total,
                            tipo_doc_receptor_code, numero_doc_receptor,
                            is_mock=False) -> str:
    # Devuelve URL: https://www.afip.gob.ar/fe/qr/?p=<base64_json>
    # El payload incluye tipoCmp = tipo_factura_code (int)

def generate_qr(qr_url: str) -> str:
    # Devuelve data URI: "data:image/png;base64,..."
```

---

## `create_pdf.py`

```python
def build_template_context(contribuyente, base_invoice_data, consumidor,
                            CAE, vencimiento_cae, invoice_number,
                            since, until, overdue, qr_code, validation_url) -> dict:
    # Campos relevantes para la plantilla:
    # invoice_type = base_invoice_data.invoice_type.name.upper()  → "C"
    # invoice_type_code = base_invoice_data.invoice_type.value    → 11

def render_invoice(invoice_data: dict, invoice_services, total_value,
                   watermark_text=None, ...) -> str:
    # Renderiza invoice_template.html con Jinja2
    # Filtro custom: {{ valor | money }} → "$ 1.234,56"

def render_pdf(rendered_html, file_name, ...) -> str:
    # Escribe PDF en disco, devuelve path
```

---

## `config.py`

```python
class Settings(BaseSettings):
    is_mock: bool = True
    output_dir: str = "invoices"

class AfipAuth(BaseSettings):        # lee desde .env
    key_path: str
    cert_path: str
    afip_access_token: SecretStr
    cuit: str
    is_production: bool

class InvoiceSource(BaseSettings):   # rutas con defaults
    invoice_source_dir: str = "./invoice_data"
    consumidor_filepath: str
    contribuyente_filepath: str
    invoice_items_filepath: str
    base_invoice_data_filepath: str
```

---

## Configuración (`config.py`)

| Clase | Variables | Fuente |
|---|---|---|
| `Settings` | `IS_MOCK` (default `true`), `output_dir` | env vars |
| `AfipAuth` | `KEY_PATH`, `CERT_PATH`, `CUIT`, `AFIP_ACCESS_TOKEN`, `IS_PRODUCTION` | `.env` |
| `InvoiceSource` | Rutas a los 4 archivos JSON de entrada | valores por defecto |

---

## Modos de operación

| Modo | `IS_MOCK` | `IS_PRODUCTION` | Conexión AFIP | Directorio salida | Marca de agua |
|---|---|---|---|---|---|
| Mock local | `true` | — | Ninguna (datos ficticios) | `invoices-dev/` | "PRUEBA LOCAL" |
| Homologación | `false` | `false` | AFIP sandbox | `invoices-dev/` | "HOMOLOGACIÓN" |
| Producción | `false` | `true` | AFIP producción | `invoices/` | Ninguna |

---

## Dependencias principales

| Librería | Uso |
|---|---|
| `afip-py 1.1.2` | Cliente WSFE de AFIP (`ElectronicBilling`) |
| `pydantic-settings` | Gestión de configuración y variables de entorno |
| `jinja2` | Renderizado de la plantilla HTML del comprobante |
| `weasyprint` | Conversión HTML → PDF |
| `segno` | Generación del código QR |

---

## Tipos de comprobante AFIP relevantes

| Código | Nombre en `TipoFactura` | Estado |
|---|---|---|
| 11 | `c` | ✅ implementado |
| 13 | `nota_de_credito_c` | 🔲 pendiente |

> Códigos completos: manual del desarrollador WSFEV1 (AFIP).

---

## Datos de entrada (`invoice_data/`)

Los 4 archivos JSON se editan manualmente antes de cada emisión. **Principal fuente de errores** (valores desactualizados entre emisiones).

### `base_invoice_data.json`
```json
{
  "month_billed": 4,
  "concept": "servicios",
  "invoice_type": "c",
  "overdue_date": null
}
```
- `month_billed`: entero 1–12 (cargado como `Mes(value)`)
- `concept`: nombre del miembro de `Concepto` (cargado como `Concepto[key]`)
- `invoice_type`: nombre del miembro de `TipoFactura` (cargado como `TipoFactura[key]`)
- `overdue_date`: `"YYYY-MM-DD"` o `null`

### `contribuyente.json` / `consumidor.json`
```json
{
  "full_name": "...",
  "id_type": "cuit",
  "id_nr": 23316378609,
  "tax_situation": "responsable_monotributo",
  "email": "...",
  "legal_address": "..."
}
```
Contribuyente agrega: `sales_location` (int), `id_before_tax` (int), `activity_since` (str `"DD/MM/YYYY"`).

### `invoice_items.json`
```json
[{ "servicio": "...", "cantidad": 1, "precio_unit": 100000.0, "bonif": 0.0, "imp_bonif": 0.0 }]
```

---

## Guía de extensión para agentes

### Agregar un nuevo tipo de comprobante (ej. Nota de Crédito C)

1. **`afip_enums.py`** → agregar miembro a `TipoFactura`: `nota_de_credito_c = 13`
2. **`invoice_data/base_invoice_data.json`** → cambiar `"invoice_type": "nota_de_credito_c"`
3. **`invoice_template.html`** → el campo `{{ invoice_type }}` ya muestra el nombre; verificar que la letra del recuadro central sea correcta ("C" para Nota de Crédito C)
4. **`voucher.py`** → `_convert_data_for_voucher` no requiere cambios; `CbteTipo` se toma de `invoice_type.value` automáticamente
5. **`afip_qr.py`** → `tipoCmp` en el payload ya usa `tipo_factura_code` directamente; sin cambios
6. Si la Nota de Crédito requiere referenciar la factura original: agregar campo `cbte_asociado` en `DatosBaseFactura` y en `_convert_data_for_voucher` (clave WSFE: `CbtesAsoc`)
