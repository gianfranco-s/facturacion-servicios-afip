# Plan: Unificar datos de entrada y persistir historial

## Abstract

Los 4 JSONs de entrada son difíciles de revisar de un vistazo y no tienen marca temporal.
El plan tiene dos etapas: **unificar** toda la entrada en un solo `invoice.json`
(resuelve legibilidad y el problema de editar múltiples archivos), y **persistir** cada
comprobante completado —entrada *y* salida (CAE, número, timestamp, ruta PDF)— en un
`history.json`. El historial habilita las "Funcionalidades" ya en CLAUDE.md:
sugerencias de valores previos y detección de campos desactualizados.
No se agregan librerías externas; sólo se crea `invoice_history.py` y se ajustan
`AfipInvoiceBuilder`, `config.py` y `main.py`.

---

## Problema → solución

| Problema | Solución |
|---|---|
| 4 archivos separados, no legibles de un vistazo | Unificar en un `invoice.json` con secciones nombradas |
| Sin timestamp de creación | `history.json` registra `generated_at` por comprobante |
| Re-hardcodear en cada emisión | Copiar la última entrada del historial como base; editar sólo lo que cambió |
| Salida (CAE, número) no almacenada con la entrada | El registro de historial guarda entrada + salida AFIP |

---

## Etapa 1 — JSON de entrada unificado

Reemplazar los 4 archivos con un único `invoice_data/invoice.json`:

```json
{
  "meta": {
    "note": "Factura Abril 2025 - Barrancas"
  },
  "base_invoice": {
    "month_billed": 4,
    "concept": "servicios",
    "invoice_type": "c",
    "overdue_date": null
  },
  "contribuyente": {
    "full_name": "SALOMONE GIANFRANCO",
    "id_type": "cuit",
    "id_nr": 23316378609,
    "tax_situation": "responsable_monotributo",
    "sales_location": 1,
    "email": "gianfranco.s@gmail.com",
    "legal_address": "Miguel Andén 0 Piso:DPTO Dpto:2 - ElBolson, Río Negro",
    "id_before_tax": 1440000,
    "activity_since": "01/12/2022"
  },
  "consumidor": {
    "full_name": "BARRANCAS PASO DEL REY S.A.",
    "id_type": "cuit",
    "id_nr": 30716020513,
    "tax_situation": "iva_responsable_inscripto",
    "email": "",
    "legal_address": "1 De Mayo 1280 - Moreno, Buenos Aires"
  },
  "invoice_items": [
    {
      "servicio": "Servicio de desarrollo...",
      "cantidad": 1,
      "precio_unit": 2219500.0,
      "bonif": 0.0,
      "imp_bonif": 0.0
    }
  ]
}
```

> `comprobante_asociado` se agrega dentro de `base_invoice` sólo para Notas de Crédito:
> `"comprobante_asociado": { "tipo": 11, "pto_vta": 1, "nro": 52 }`

### Cambios de código — Etapa 1

| Archivo | Cambio |
|---|---|
| `invoice_data/invoice.json` | **Nuevo** — reemplaza los 4 JSONs |
| `afip_invoice_builder.py` | Agregar classmethod `from_unified_json(path)` que lee las secciones y llama a los loaders existentes |
| `config.py` | `InvoiceSource` colapsa a un solo campo `invoice_filepath` |
| `main.py` | Pasar la ruta única al builder en lugar del dict de 4 rutas |

Los 4 archivos originales se eliminan una vez migrado `invoice.json`.

---

## Etapa 2 — Historial de comprobantes

### Nuevo módulo: `facturacion_servicios/invoice_history.py`

Guarda los comprobantes en `invoice_data/history.json` (array JSON, más nuevo al final).

**Estructura de un registro:**

```json
{
  "generated_at": "2025-04-30T15:23:10",
  "is_mock": false,
  "input": {
    "meta": { "note": "Factura Abril 2025 - Barrancas" },
    "base_invoice": { ... },
    "contribuyente": { ... },
    "consumidor": { ... },
    "invoice_items": [ ... ]
  },
  "output": {
    "invoice_number": 52,
    "cae": "75314447442077",
    "cae_expiry": "2025-05-10",
    "pdf_path": "invoices/salomone_23316378609_52_barrancas.pdf"
  }
}
```

**API del módulo:**

```python
def append_to_history(
    input_snapshot: dict,       # el JSON tal como fue leído, sin deserializar enums
    invoice_number: int,
    cae: str,
    cae_expiry: str,
    pdf_path: str,
    is_mock: bool,
    history_path: Path,
) -> None: ...

def load_history(history_path: Path) -> list[dict]: ...
```

### Archivos de historial por entorno

Espejando el patrón de directorios de salida (`invoices/` vs `invoices-dev/`):

| Modo | Archivo de historial |
|---|---|
| Producción | `invoice_data/history.json` |
| Dev / mock | `invoice_data/history-dev.json` |

### Cambios de código — Etapa 2

| Archivo | Cambio |
|---|---|
| `facturacion_servicios/invoice_history.py` | **Nuevo** |
| `main.py` | Después de `render_pdf`, llamar a `append_to_history` con el snapshot de entrada y los datos de salida |
| `config.py` | Agregar `history_filepath` a `InvoiceSource` (o `Settings`) apuntando al archivo correcto según entorno |

---

## Flujo de trabajo resultante

En lugar de editar 4 archivos hardcodeados:

1. Abrir `invoice_data/invoice.json`
2. Actualizar los campos que cambiaron: `month_billed`, `invoice_items[0].precio_unit`, `note`
3. Ejecutar — el historial se actualiza automáticamente

El historial es también la fuente de datos para las funcionalidades planificadas:
- **Sugerencias:** leer el último registro para precompletar el próximo `invoice.json`
- **Detección de valores obsoletos:** comparar el `invoice.json` actual con el último registro antes de emitir

---

## Archivos tocados (resumen)

| Archivo | Acción |
|---|---|
| `invoice_data/invoice.json` | Nuevo |
| `invoice_data/history.json` | Creado en primer ejecución real |
| `invoice_data/history-dev.json` | Creado en primer ejecución mock/dev |
| `invoice_data/base_invoice_data.json` | Eliminar |
| `invoice_data/contribuyente.json` | Eliminar |
| `invoice_data/consumidor.json` | Eliminar |
| `invoice_data/invoice_items.json` | Eliminar |
| `facturacion_servicios/invoice_history.py` | Nuevo |
| `facturacion_servicios/afip_invoice_builder.py` | Agregar `from_unified_json()` |
| `facturacion_servicios/config.py` | Simplificar `InvoiceSource` |
| `facturacion_servicios/main.py` | Nuevo builder + llamada al historial |
| `.claude/ARCHITECTURE.md` | Actualizar sección de datos de entrada y flujo |

---

## Decisiones tomadas

- **4 archivos viejos:** eliminar (no mantener compatibilidad hacia atrás).
- **Runs mock en historial:** archivo separado `history-dev.json` (espeja el patrón `invoices-dev/`).
- **Snapshot de entrada:** guardar el JSON crudo (strings, no enums deserializados) para que el registro sea legible sin importar el código.
- **Sin nuevas dependencias:** stdlib `json` + `datetime`. SQLite queda como migración futura si el historial crece.
