---
description: Genera una Factura C. Actualiza los archivos JSON de invoice_data/ y ejecuta la generación.
argument-hint: "[mes] [descripción] [precio]"
disable-model-invocation: true
allowed-tools: Read Edit Bash
---

Genera una Factura C siguiendo el caso de uso en `use-cases/emitir_factura.md`.

## Pasos

1. **Leer el estado actual** de los archivos JSON:
   - `invoice_data/base_invoice_data.json` → mostrar mes facturado actual
   - `invoice_data/invoice_items.json` → mostrar descripción y precio actuales

2. **Solicitar al usuario los datos del período** si no se proveyeron en `$ARGUMENTS`:
   - Mes a facturar (número 1–12)
   - Descripción del servicio
   - Precio unitario

   Alertar si algún valor parece igual al de la última emisión (mismo mes, mismo importe).

3. **Actualizar `invoice_data/base_invoice_data.json`**:
   - `invoice_type`: `"c"`
   - `month_billed`: el mes indicado
   - Eliminar `comprobante_asociado` si existiera

4. **Actualizar `invoice_data/invoice_items.json`** con la descripción y precio provistos.

5. **Mostrar un resumen** de los cambios y pedir confirmación antes de ejecutar.

6. **Ejecutar**:
   ```sh
   ENTORNO=dev IS_MOCK=true python3 -m facturacion_servicios.main
   ```
   Usar `IS_MOCK=false` si el usuario indicó homologación o producción.

7. **Reportar** el path del PDF generado, o el error si falla.
