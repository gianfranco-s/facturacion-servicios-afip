# Plan: Implementación de Nota de Crédito C

## Contexto

Actualmente el sistema solo emite **Factura C** (CbteTipo 11). Se necesita soportar también **Nota de Crédito C** (CbteTipo 13), que permite reversar parcial o totalmente una factura emitida. AFIP requiere que la Nota de Crédito incluya una referencia al comprobante original (`CbtesAsoc`). La librería `afip-py` ya soporta este campo (línea 79 de `electronic_billing.py`).

---

## Archivos a modificar

| Archivo | Cambio |
|---|---|
| `facturacion_servicios/afip_enums.py` | Nuevo miembro en `TipoFactura`, nuevas propiedades, nuevo dataclass |
| `facturacion_servicios/afip_invoice_builder.py` | Cargar `comprobante_asociado` desde JSON |
| `facturacion_servicios/voucher.py` | Agregar `CbtesAsoc` al dict WSFE cuando corresponda |
| `facturacion_servicios/create_pdf.py` | Pasar `letra` y `etiqueta` del tipo de comprobante al template |
| `facturacion_servicios/invoice_template.html` | Usar variables en lugar de "Factura" hardcodeado |
| `.claude/ARCHITECTURE.md` | Actualizar con nuevas clases, campos y métodos |

---

## Paso 1 — `afip_enums.py`

### 1a. Extender `TipoFactura` con el nuevo tipo y propiedades

```python
class TipoFactura(Enum):
    c = 11
    nota_de_credito_c = 13

    @property
    def letra(self) -> str:
        """Letra que aparece en el recuadro central del comprobante."""
        return "C"  # todos los tipos del monotributista son C

    @property
    def etiqueta(self) -> str:
        """Nombre completo del tipo de comprobante para el encabezado del PDF."""
        _etiquetas = {
            TipoFactura.c: "Factura",
            TipoFactura.nota_de_credito_c: "Nota de Crédito",
        }
        return _etiquetas[self]
```

### 1b. Agregar `ComprobanteAsociado`

```python
@dataclass
class ComprobanteAsociado:
    """Referencia al comprobante original que origina la Nota de Crédito."""
    tipo: int     # CbteTipo del comprobante original (ej. 11 para Factura C)
    pto_vta: int  # punto de venta del comprobante original
    nro: int      # número del comprobante original
```

### 1c. Actualizar `DatosBaseFactura`

```python
@dataclass
class DatosBaseFactura:
    month_billed: Mes
    concept: Concepto
    invoice_type: TipoFactura
    overdue_date: str | None = None
    comprobante_asociado: ComprobanteAsociado | None = None  # requerido para Nota de Crédito
```

---

## Paso 2 — `afip_invoice_builder.py`

Actualizar `_load_base_invoice_data` para construir `ComprobanteAsociado` si el JSON lo incluye:

```python
@staticmethod
def _load_base_invoice_data(filepath: Path) -> DatosBaseFactura:
    with open(filepath, "r") as f:
        data = json.load(f)
    data["month_billed"] = Mes(data["month_billed"])
    data["concept"] = Concepto[data["concept"]]
    data["invoice_type"] = TipoFactura[data["invoice_type"]]
    if data.get("comprobante_asociado"):
        data["comprobante_asociado"] = ComprobanteAsociado(**data["comprobante_asociado"])
    return DatosBaseFactura(**data)
```

---

## Paso 3 — `voucher.py`

Agregar `CbtesAsoc` al final de `_convert_data_for_voucher`, antes del `return`:

```python
if base_invoice_data.comprobante_asociado:
    ca = base_invoice_data.comprobante_asociado
    result["CbtesAsoc"] = [{"Tipo": ca.tipo, "PtoVta": ca.pto_vta, "Nro": ca.nro}]
```

La librería `afip-py` ya envuelve la lista en `{"CbteAsoc": [...]}` automáticamente (línea 79 de `electronic_billing.py`).

---

## Paso 4 — `create_pdf.py`

En `build_template_context`, reemplazar:
```python
invoice_type=base_invoice_data.invoice_type.name.upper(),
invoice_type_code=base_invoice_data.invoice_type.value,
```
por:
```python
invoice_type_letra=base_invoice_data.invoice_type.letra,      # "C"
invoice_type_code=base_invoice_data.invoice_type.value,        # 11 o 13
document_label=base_invoice_data.invoice_type.etiqueta,        # "Factura" o "Nota de Crédito"
```

---

## Paso 5 — `invoice_template.html`

Dos cambios puntuales:

```html
<!-- línea 186: antes -->
<div class="bill-type">{{ invoice_type }}</div>
<!-- después -->
<div class="bill-type">{{ invoice_type_letra }}</div>

<!-- línea 190: antes -->
<div class="text-lg">Factura</div>
<!-- después -->
<div class="text-lg">{{ document_label }}</div>
```

---

## Paso 6 — `invoice_data/base_invoice_data.json`

Sin cambios en el archivo actual (sigue siendo Factura C por defecto). El formato para emitir una Nota de Crédito sería:

```json
{
  "month_billed": 4,
  "concept": "servicios",
  "invoice_type": "nota_de_credito_c",
  "comprobante_asociado": { "tipo": 11, "pto_vta": 1, "nro": 52 }
}
```

---

## Paso 7 — `.claude/ARCHITECTURE.md`

Actualizar:
- `TipoFactura`: marcar `nota_de_credito_c = 13` como implementado; documentar propiedades `letra` y `etiqueta`
- Agregar `ComprobanteAsociado` en la sección de dataclasses
- `DatosBaseFactura`: agregar campo `comprobante_asociado`
- `voucher.py`: mencionar la condición `CbtesAsoc`
- `create_pdf.py`: actualizar las claves que se pasan al template (`invoice_type_letra`, `document_label`)
- Tabla de tipos de comprobante: marcar `nota_de_credito_c = 13` como ✅ implementado

---

## Verificación

1. **Mock local** — cambiar `invoice_data/base_invoice_data.json` a `"invoice_type": "nota_de_credito_c"` con `comprobante_asociado`, ejecutar `IS_MOCK=true python3 -m facturacion_servicios.main`, verificar que el PDF muestre "Nota de Crédito" con letra "C" y código 13.
2. **Factura C sigue funcionando** — restaurar `"invoice_type": "c"` (sin `comprobante_asociado`) y verificar que el PDF muestre "Factura C" como antes.
3. **Homologación** — repetir con `IS_MOCK=false IS_PRODUCTION=false` para verificar que ARCA acepta el nuevo `CbteTipo` con `CbtesAsoc`.
