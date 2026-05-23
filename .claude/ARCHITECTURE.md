# Arquitectura del Proyecto

> **Para agentes:** leer este archivo antes de explorar el código. Actualizarlo cuando cambien responsabilidades, flujos o decisiones de diseño — no para reflejar firmas de funciones o campos que ya están en el código.

Herramienta para emitir comprobantes electrónicos (facturas para monotributistas) ante AFIP/ARCA, generando un PDF firmado con CAE.

---

## Patrón arquitectónico: Puertos y Adaptadores (parcial)

El proyecto aplica el patrón de forma incremental. La separación actual es:

| Capa | Responsabilidad |
|---|---|
| **Dominio** | Modelos, enums, builder (`afip_enums.py`, `afip_invoice_builder.py`) |
| **Orquestación** | Casos de uso, coordinación del flujo (`main.py`, `voucher.py`) |
| **Puerto de salida** | Contrato con ARCA/AFIP (`afip_port.py`) — sólo un `Protocol` |
| **Adaptador** | Implementación concreta del puerto (`afip_adapter.py`) |
| **Infraestructura** | PDF, QR, configuración (`create_pdf.py`, `afip_qr.py`, `config.py`) |

La orquestación y el dominio **importan sólo `afip_port.py`**, nunca la librería `afip` (SDK externo). El tipo `Afip` no sale de `afip_adapter.py`.

### Puerto de salida: `PuertoAFIP`

| Método | Descripción |
|---|---|
| `obtener_ultimo_comprobante(punto_venta, tipo)` | Último número de comprobante autorizado |
| `crear_comprobante(datos)` | Enviar comprobante a ARCA; retorna dict con CAE |

### Adaptadores conocidos

| Clase | Módulo | Descripción |
|---|---|---|
| `AdaptadorAfipSDK` | `afip_adapter.py` | Producción: wraps `afip.Afip` con retry de red |
| *(mock implícito)* | `main.py` | Cuando `is_mock=True`, se usa `None` y `_get_valid_mock_data` |
| `MockPuertoAFIP` | `tests/conftest.py` | Doble de test en memoria |

> **Deuda técnica:** el mock implícito (`None` + función libre) debería convertirse en una clase `AdaptadorAfipMock` formal. `_convert_data_for_voucher` aún vive en `voucher.py` pero es AFIP-específico; debería moverse al adaptador cuando se extraigan los casos de uso formales.

---

## Estructura de directorios

```
facturacion-servicios-afip/
├── facturacion_servicios/        # Paquete principal
│   ├── main.py                   # Punto de entrada; orquesta el flujo completo
│   ├── afip_enums.py             # Enums y dataclasses del dominio
│   ├── afip_invoice_builder.py   # Carga de JSONs y ensamblado del comprobante
│   ├── afip_port.py              # Puerto de salida → PuertoAFIP (Protocol)
│   ├── afip_adapter.py           # Adaptador real → AdaptadorAfipSDK + reintentar_en_red
│   ├── voucher.py                # Orquestación de comprobantes; usa PuertoAFIP
│   ├── afip_qr.py                # Generación de URL de validación y código QR
│   ├── config.py                 # Configuración via pydantic-settings
│   ├── create_pdf.py             # Renderizado HTML (Jinja2) → PDF (WeasyPrint)
│   └── invoice_template.html     # Plantilla Jinja2 del comprobante
├── invoice_data/                 # Datos de entrada (JSON) — se editan antes de cada emisión
├── invoices/                     # PDFs generados en producción
├── invoices-dev/                 # PDFs generados en mock/homologación
├── certs/                        # Certificados y claves privadas AFIP
└── .env.dev / .env.prd           # Credenciales por ambiente
```

---

## Flujo de ejecución

```
main()  [main.py]
  │
  ├─ AdaptadorAfipSDK.desde_credenciales()  [afip_adapter.py]
  │    └─ construye el cliente Afip internamente (cert + token)
  │
  └─ generate_invoice()               [main.py]
       │
       ├─ AfipInvoiceBuilder.build()  [afip_invoice_builder.py]  Lee 4 JSONs → AfipInvoiceData
       │
       ├─ get_invoice_number()        [voucher.py]   → afip_client.obtener_ultimo_comprobante()
       ├─ get_cae()                   [voucher.py]   → afip_client.crear_comprobante()
       │    └─ _convert_data_for_voucher()           Mapea AfipInvoiceData → dict WSFE
       │
       ├─ invoice_validation_url()    [afip_qr.py]   Construye URL con payload Base64
       ├─ generate_qr()               [afip_qr.py]   Devuelve data URI PNG del QR
       │
       ├─ build_template_context()    [create_pdf.py]  Prepara dict para Jinja2
       ├─ render_invoice()            [create_pdf.py]  Renderiza HTML con invoice_template.html
       └─ render_pdf()                [create_pdf.py]  HTML → PDF con WeasyPrint
```

En modo **mock** (`IS_MOCK=true`), `AdaptadorAfipSDK` no se instancia y los datos AFIP son valores fijos en `_get_valid_mock_data` (`main.py`).

---

## Configuración (`config.py`)

| Clase | Variables | Fuente |
|---|---|---|
| `ConfigEntorno` | `ENTORNO` (**requerido**, sin default) | shell env var únicamente |
| `AfipAuth` | `KEY_PATH`, `CERT_PATH`, `CUIT`, `AFIPSDK_ACCESS_TOKEN`, `IS_PRODUCTION` | `.env.<entorno>` |
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
| `afip-py 1.1.2` | Cliente WSFE de AFIP (`ElectronicBilling`) — confinado a `afip_adapter.py` |
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

- **Puertos y adaptadores:** el tipo `Afip` (SDK externo) está confinado a `afip_adapter.py`. `AdaptadorAfipSDK.desde_credenciales()` construye el cliente internamente; nada fuera del adaptador conoce ese tipo. Cambiar de SDK implica sólo escribir un nuevo adaptador que satisfaga `PuertoAFIP`.
- **Carga de enums desde JSON:** `_load_base_invoice_data` convierte strings a enums usando `Enum[key]` (por nombre) o `Enum(value)` (por valor). Al agregar un nuevo `TipoFactura`, el JSON usa el nombre del miembro (ej. `"nota_de_credito_c"`). `comprobante_asociado` se carga como `ComprobanteAsociado(**dict)` si está presente.
- **`TipoFactura.letra` / `.etiqueta` / `.sufijo_archivo`:** propiedades del enum que desacoplan la representación visual del valor AFIP. La plantilla usa `invoice_type_letra` (siempre `"C"`), `document_label` (`"Factura"` o `"Nota de Crédito"`) y `comprobante_asociado_label` (ej. `"Fac. C: 00001-00000004"`, `None` para Factura). El nombre del archivo PDF usa `sufijo_archivo` (`""` para Factura, `"_nc"` para Nota de Crédito). Al agregar un tipo nuevo, extender las tres propiedades.
- **`CbtesAsoc` para Nota de Crédito:** `_convert_data_for_voucher` agrega la lista solo si `base_invoice_data.comprobante_asociado` está definido. La librería `afip-py` envuelve la lista en `{"CbteAsoc": [...]}` automáticamente.
- **`ImpNeto == ImpTotal`:** para monotributistas no hay IVA discriminado; `_convert_data_for_voucher` envía `ImpIVA=0` e `ImpNeto=ImpTotal`. Aplica tanto a Factura C como a Nota de Crédito C. No cambiar sin verificar contra WSFE.
- **Overdue clamp (AFIP error 10036):** `_get_period()` en `afip_invoice_builder.py` calcula `overdue_date` como el último día del mes + 10 días, pero lo clampea a `max(..., hoy)`. Necesario porque AFIP rechaza comprobantes con `FchVtoPago` anterior a la fecha de emisión (error 10036). Aplica cuando se emite un comprobante de un mes ya vencido (ej. nota de crédito de abril emitida en mayo).
- **Reintentos ante errores de red (`afip_adapter.py`):** el decorador `reintentar_en_red` envuelve los métodos `obtener_ultimo_comprobante` y `crear_comprobante` del adaptador (3 intentos, 2 s de espera). Captura `socket.gaierror`, `ConnectionError`, `OSError`, `TimeoutError` — errores de DNS/red transientes típicos de afipsdk. No captura errores de negocio de AFIP (son excepciones de otro tipo).

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

### Cambiar la implementación de AFIP

1. Crear una clase nueva que implemente `PuertoAFIP` (los dos métodos del protocolo)
2. Instanciarla en `main.py` en lugar de `AdaptadorAfipSDK.desde_credenciales(...)`
3. No tocar `voucher.py`, `main.py` (salvo el punto de inyección), ni el dominio

### Agregar un nuevo tipo de comprobante

1. **`afip_enums.py`** → agregar miembro a `TipoFactura` con el código AFIP; extender propiedades `letra`, `etiqueta` y `sufijo_archivo`
2. Si requiere comprobante asociado, ya está soportado vía `comprobante_asociado` en `DatosBaseFactura`
3. **`voucher.py`** → `CbteTipo` se toma de `invoice_type.value` automáticamente; sin cambios salvo lógica de importes nueva
4. **`afip_qr.py`** → sin cambios
