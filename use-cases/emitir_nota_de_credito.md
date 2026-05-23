# Caso de Uso: Emitir Nota de Crédito C

## Descripción

Genera una Nota de Crédito C electrónica que revierte parcial o totalmente una Factura C previamente emitida. Requiere referenciar el comprobante original mediante `CbtesAsoc`.

---

## Actores

- **Monotributista (emisor):** quien emite la nota de crédito.
- **Cliente (receptor):** quien recibió la factura original.
- **ARCA / AFIP:** autoriza el comprobante y emite el CAE.

---

## Pre-condiciones

- Se conoce el número de la factura original que se quiere reversar (tipo 11, punto de venta, número).
- Los archivos en `invoice_data/` están actualizados:
  - `contribuyente.json` — datos del emisor (igual que en la factura original)
  - `consumidor.json` — datos del receptor (igual que en la factura original)
  - `invoice_items.json` — monto a acreditar (puede ser el total o parcial de la factura original)
  - `base_invoice_data.json` — tipo `"nota_de_credito_c"`, con `comprobante_asociado` completado
- El entorno está configurado (`.env.dev` o `.env.prd`), o `IS_MOCK=true` para prueba local.

---

## Flujo principal

1. **Cargar datos:** `AfipInvoiceBuilder` lee los 4 archivos JSON. Detecta `comprobante_asociado` en `base_invoice_data.json` y construye un `ComprobanteAsociado`.
2. **Obtener número de comprobante:** consulta a ARCA el último número de Nota de Crédito C emitido y suma 1 (`CbteTipo=13`).
3. **Solicitar CAE:** envía los datos a ARCA con `CbteTipo=13` y `CbtesAsoc` apuntando a la factura original. Recibe `CAE` y `CAEFchVto`.
4. **Generar QR:** construye la URL de validación AFIP con `tipoCmp=13` y la convierte en QR.
5. **Renderizar PDF:** el encabezado muestra **"Nota de Crédito"** con letra **"C"** y código **13**.
6. **Guardar PDF:** escribe el archivo en el directorio de salida correspondiente al entorno.

---

## Post-condiciones

- PDF generado con:
  - Encabezado: `Nota de Crédito | C | COD. 13`
  - CAE válido y fecha de vencimiento
  - Código QR apuntando a la URL de validación AFIP
  - Tres copias: ORIGINAL, DUPLICADO, TRIPLICADO
- Comprobante registrado en ARCA asociado a la factura original.

---

## Datos de ejemplo

```json
// base_invoice_data.json
{
  "month_billed": 4,
  "concept": "servicios",
  "invoice_type": "nota_de_credito_c",
  "comprobante_asociado": {
    "tipo": 11,
    "pto_vta": 1,
    "nro": 52
  }
}
```

```json
// invoice_items.json
[
  {
    "servicio": "Nota de Crédito por error en factura Nro 00001-00000052 — Abril 2026",
    "cantidad": 1,
    "precio_unit": 800000.00,
    "bonif": 0.0,
    "imp_bonif": 0.0
  }
]
```

---

## Diferencias con Emitir Factura

| Aspecto | Factura C | Nota de Crédito C |
|---|---|---|
| `invoice_type` | `"c"` | `"nota_de_credito_c"` |
| `CbteTipo` (AFIP) | 11 | 13 |
| `comprobante_asociado` | No aplica | Requerido |
| `CbtesAsoc` en WSFE | No incluido | Incluido con referencia a la factura original |
| Encabezado del PDF | "Factura" | "Nota de Crédito" |

---

## Errores comunes

| Error | Causa | Solución |
|---|---|---|
| ARCA rechaza el comprobante | `comprobante_asociado` apunta a una factura inexistente o de otro CUIT | Verificar número, punto de venta y tipo del comprobante original |
| PDF dice "Factura" en lugar de "Nota de Crédito" | `invoice_type` no fue actualizado | Verificar `base_invoice_data.json` |
| `comprobante_asociado` ausente | Se olvidó completar el campo | Agregar `comprobante_asociado` al JSON antes de ejecutar |
