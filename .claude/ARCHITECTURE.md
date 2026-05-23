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
| 13 | `nota_de_credito_c` | ✅ implementado |

> Códigos completos: manual del desarrollador WSFEV1 (AFIP).

---

## Decisiones de diseño no obvias

- **Carga de enums desde JSON:** `_load_base_invoice_data` convierte strings a enums usando `Enum[key]` (por nombre) o `Enum(value)` (por valor). Al agregar un nuevo `TipoFactura`, el JSON usa el nombre del miembro (ej. `"nota_de_credito_c"`). `comprobante_asociado` se carga como `ComprobanteAsociado(**dict)` si está presente.
- **`TipoFactura.letra` / `.etiqueta` / `.sufijo_archivo`:** propiedades del enum que desacoplan la representación visual del valor AFIP. La plantilla usa `invoice_type_letra` (siempre `"C"`), `document_label` (`"Factura"` o `"Nota de Crédito"`) y `comprobante_asociado_label` (ej. `"Fac. C: 00001-00000004"`, `None` para Factura). El nombre del archivo PDF usa `sufijo_archivo` (`""` para Factura, `"_nc"` para Nota de Crédito). Al agregar un tipo nuevo, extender las tres propiedades.
- **`CbtesAsoc` para Nota de Crédito:** `_convert_data_for_voucher` agrega la lista solo si `base_invoice_data.comprobante_asociado` está definido. La librería `afip-py` envuelve la lista en `{"CbteAsoc": [...]}` automáticamente.
- **`ImpNeto == ImpTotal`:** para monotributistas no hay IVA discriminado; `_convert_data_for_voucher` envía `ImpIVA=0` e `ImpNeto=ImpTotal`. Aplica tanto a Factura C como a Nota de Crédito C. No cambiar sin verificar contra WSFE.
- **Overdue clamp (AFIP error 10036):** `_get_period()` en `afip_invoice_builder.py` calcula `overdue_date` como el último día del mes + 10 días, pero lo clampea a `max(..., hoy)`. Necesario porque AFIP rechaza comprobantes con `FchVtoPago` anterior a la fecha de emisión (error 10036). Aplica cuando se emite un comprobante de un mes ya vencido (ej. nota de crédito de abril emitida en mayo).
- **Reintentos ante errores de red (`voucher.py`):** El decorador `reintentar_en_red` envuelve `get_cae` y `get_invoice_number` (3 intentos, 2 s de espera). Captura `socket.gaierror`, `ConnectionError`, `OSError`, `TimeoutError` — errores de DNS/red transientes típicos de afipsdk. No captura errores de negocio de AFIP (son excepciones de otro tipo).

---

## Datos de entrada (`invoice_data/`)

Los 4 archivos JSON se editan manualmente antes de cada emisión. **Principal fuente de errores** (valores desactualizados entre emisiones).

- `base_invoice_data.json` — `month_billed` (int 1–12), `concept` (nombre de `Concepto`), `invoice_type` (nombre de `TipoFactura`), `overdue_date` (`"YYYY-MM-DD"` o `null`)
- `contribuyente.json` / `consumidor.json` — `id_type` (nombre de `TipoDeDocumento`), `tax_situation` (nombre de `CondicionFrenteIVA`)
- `invoice_items.json` — lista de servicios prestados

---

## Guía de extensión para agentes

### Emitir una Nota de Crédito C

Editar `invoice_data/base_invoice_data.json`:
```json
{
  "month_billed": 4,
  "concept": "servicios",
  "invoice_type": "nota_de_credito_c",
  "comprobante_asociado": { "tipo": 11, "pto_vta": 1, "nro": 52 }
}
```
El resto del flujo (ítems, contribuyente, consumidor) es idéntico al de una Factura C.

### Agregar un nuevo tipo de comprobante

1. **`afip_enums.py`** → agregar miembro a `TipoFactura` con el código AFIP; extender propiedades `letra`, `etiqueta` y `sufijo_archivo`
2. Si requiere comprobante asociado, ya está soportado vía `comprobante_asociado` en `DatosBaseFactura`
3. **`voucher.py`** → `CbteTipo` se toma de `invoice_type.value` automáticamente; sin cambios salvo lógica de importes nueva
4. **`afip_qr.py`** → sin cambios
