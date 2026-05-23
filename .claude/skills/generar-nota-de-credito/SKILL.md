---
description: Genera una Nota de Crédito C referenciando una factura original. Actualiza los archivos JSON de invoice_data/ y ejecuta la generación.
argument-hint: "[mes] [nro-factura-original] [importe] [descripción]"
disable-model-invocation: true
allowed-tools: Read Edit Bash
---

Genera una Nota de Crédito C siguiendo el caso de uso en `use-cases/emitir_nota_de_credito.md`.

## Pasos

1. **Leer el estado actual** de los archivos JSON:
   - `invoice_data/base_invoice_data.json` → mostrar tipo y comprobante asociado actuales
   - `invoice_data/invoice_items.json` → mostrar descripción e importe actuales

2. **Solicitar al usuario los datos** si no se proveyeron en `$ARGUMENTS`:
   - Mes a facturar (número 1–12)
   - Número de la factura original (`nro`)
   - Punto de venta de la factura original (`pto_vta`, default: 1)
   - Tipo de la factura original (`tipo`, default: 11 para Factura C)
   - Importe a acreditar
   - Descripción del motivo de la nota de crédito

3. **Actualizar `invoice_data/base_invoice_data.json`**:
   - `invoice_type`: `"nota_de_credito_c"`
   - `month_billed`: el mes indicado
   - `comprobante_asociado`: `{ "tipo": <tipo>, "pto_vta": <pto_vta>, "nro": <nro> }`

4. **Actualizar `invoice_data/invoice_items.json`** con la descripción y el importe provistos.

5. **Mostrar un resumen** de los cambios y pedir confirmación antes de ejecutar.

6. **Ejecutar**:
   ```sh
   ENTORNO=dev IS_MOCK=true python3 -m facturacion_servicios.main
   ```
   Usar `IS_MOCK=false` si el usuario indicó homologación o producción.

7. **Reportar** el path del PDF generado, o el error si falla.
