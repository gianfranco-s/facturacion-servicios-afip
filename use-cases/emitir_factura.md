# Caso de Uso: Emitir Factura C

## Descripción

Genera una Factura C electrónica para un monotributista, la autoriza ante ARCA (AFIP) y produce un PDF firmado con CAE.

---

## Actores

- **Monotributista (emisor):** quien factura el servicio.
- **Cliente (receptor):** empresa o persona que recibe la factura.
- **ARCA / AFIP:** autoriza el comprobante y emite el CAE.

---

## Pre-condiciones

- Los archivos en `invoice_data/` están actualizados:
  - `contribuyente.json` — datos del emisor
  - `consumidor.json` — datos del receptor
  - `invoice_items.json` — servicios a facturar (con precios del período)
  - `base_invoice_data.json` — mes facturado, tipo de comprobante `"c"`, concepto
- El entorno está configurado (`.env.dev` o `.env.prd`) con credenciales válidas, o `IS_MOCK=true` para prueba local.

---

## Flujo principal

1. **Cargar datos:** `AfipInvoiceBuilder` lee los 4 archivos JSON y construye un `AfipInvoiceData`.
2. **Obtener número de comprobante:** consulta a ARCA el último número emitido y suma 1.
3. **Solicitar CAE:** envía el `AfipInvoiceData` a ARCA vía WSFE (`FECAESolicitar`) con `CbteTipo=11`. Recibe `CAE` y `CAEFchVto`.
4. **Generar QR:** construye la URL de validación AFIP y la convierte en código QR (data URI PNG).
5. **Renderizar PDF:** arma el contexto Jinja2 y genera el PDF con WeasyPrint. El encabezado muestra **"Factura"** con letra **"C"** y código **11**.
6. **Guardar PDF:** escribe el archivo en `invoices/` (producción) o `invoices-dev/` (otros modos).

---

## Post-condiciones

- PDF generado con:
  - Encabezado: `Factura | C | COD. 11`
  - CAE válido y fecha de vencimiento
  - Código QR que apunta a la URL de validación AFIP
  - Tres copias: ORIGINAL, DUPLICADO, TRIPLICADO
- Comprobante registrado en ARCA bajo el CUIT del monotributista.

---

## Datos de ejemplo

```json
// base_invoice_data.json
{
  "month_billed": 4,
  "concept": "servicios",
  "invoice_type": "c"
}
```

```json
// invoice_items.json
[
  {
    "servicio": "Desarrollo de software — Abril 2026",
    "cantidad": 1,
    "precio_unit": 800000.00,
    "bonif": 0.0,
    "imp_bonif": 0.0
  }
]
```

---

## Errores comunes

| Error | Causa | Solución |
|---|---|---|
| `(11002) El punto de venta no se encuentra habilitado` | Punto de venta no registrado en AFIP para facturación electrónica | Habilitarlo en ARCA → Administración de Puntos de Venta |
| PDF con mes incorrecto | `month_billed` no fue actualizado en `base_invoice_data.json` | Actualizar el campo antes de ejecutar |
| PDF con importe del mes anterior | `precio_unit` en `invoice_items.json` no fue actualizado | Actualizar el campo antes de ejecutar |
