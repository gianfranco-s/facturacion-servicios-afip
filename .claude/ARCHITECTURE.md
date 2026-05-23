# Arquitectura del Proyecto

> **Para agentes:** leer este archivo antes de explorar el código. Actualizarlo cuando cambien responsabilidades, flujos o decisiones de diseño — no para reflejar firmas de funciones o campos que ya están en el código.

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
├── invoices/                     # PDFs generados en producción
├── invoices-dev/                 # PDFs generados en mock/homologación
├── certs/                        # Certificados y claves privadas AFIP
├── docker/                       # Dockerfile
└── .env.dev / .env.prd           # Credenciales por ambiente
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

En modo **mock** (`IS_MOCK=true`), `get_afip_session()` no se llama y los datos AFIP son valores fijos hardcodeados en `main.py`.

---

## Configuración (`config.py`)

| Clase | Variables | Fuente |
|---|---|---|
| `ConfigEntorno` | `ENTORNO` (**requerido**, sin default) | shell env var únicamente |
| `AfipAuth` | `KEY_PATH`, `CERT_PATH`, `CUIT`, `AFIP_ACCESS_TOKEN`, `IS_PRODUCTION` | `.env.<entorno>` |
| `Settings` | `IS_MOCK` (default `true`), `output_dir` | env vars |
| `InvoiceSource` | Rutas a los 4 archivos JSON de entrada | valores por defecto |

**Selección del archivo `.env`:** `ConfigEntorno` se instancia primero (sin leer ningún archivo `.env`) y su propiedad `env_file` determina qué archivo carga `AfipAuth`. Omitir `ENTORNO` produce un crash inmediato en el import. `IS_PRODUCTION` vive dentro del archivo `.env.<entorno>`, no se pasa como variable de shell.

---

## Modos de operación

| Modo | `ENTORNO` | `IS_MOCK` | Conexión AFIP | Directorio salida | Marca de agua |
|---|---|---|---|---|---|
| Mock local | `dev` | `true` | Ninguna (datos ficticios) | `invoices-dev/` | "PRUEBA LOCAL" |
| Homologación | `dev` | `false` | AFIP sandbox | `invoices-dev/` | "HOMOLOGACIÓN" |
| Producción | `prd` | `false` | AFIP producción | `invoices/` | Ninguna |

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

## Decisiones de diseño no obvias

- **Carga de enums desde JSON:** `_load_base_invoice_data` convierte strings a enums usando `Enum[key]` (por nombre) o `Enum(value)` (por valor). Al agregar un nuevo `TipoFactura`, el JSON usa el nombre del miembro (ej. `"nota_de_credito_c"`).
- **`invoice_type` en la plantilla:** `build_template_context` expone tanto `.name.upper()` (letra visible, ej. `"C"`) como `.value` (código numérico AFIP, ej. `11`). Si se agrega un tipo nuevo, verificar que la plantilla muestre la letra correcta.
- **`ImpNeto == ImpTotal`:** para monotributistas no hay IVA discriminado; `_convert_data_for_voucher` envía `ImpIVA=0` e `ImpNeto=ImpTotal`. No cambiar sin verificar contra WSFE.

---

## Datos de entrada (`invoice_data/`)

Los 4 archivos JSON se editan manualmente antes de cada emisión. **Principal fuente de errores** (valores desactualizados entre emisiones).

- `base_invoice_data.json` — `month_billed` (int 1–12), `concept` (nombre de `Concepto`), `invoice_type` (nombre de `TipoFactura`), `overdue_date` (`"YYYY-MM-DD"` o `null`)
- `contribuyente.json` / `consumidor.json` — `id_type` (nombre de `TipoDeDocumento`), `tax_situation` (nombre de `CondicionFrenteIVA`)
- `invoice_items.json` — lista de servicios prestados

---

## Guía de extensión para agentes

### Agregar un nuevo tipo de comprobante (ej. Nota de Crédito C)

1. **`afip_enums.py`** → agregar miembro a `TipoFactura`: `nota_de_credito_c = 13`
2. **`invoice_data/base_invoice_data.json`** → cambiar `"invoice_type": "nota_de_credito_c"`
3. **`invoice_template.html`** → verificar que la letra del recuadro central sea correcta ("C" para Nota de Crédito C)
4. **`voucher.py`** → `_convert_data_for_voucher` no requiere cambios; `CbteTipo` se toma de `invoice_type.value` automáticamente
5. **`afip_qr.py`** → sin cambios; `tipoCmp` ya usa el código directamente
6. Si la Nota de Crédito debe referenciar la factura original: agregar `cbte_asociado` en `DatosBaseFactura` y mapearlo en `_convert_data_for_voucher` (clave WSFE: `CbtesAsoc`)
