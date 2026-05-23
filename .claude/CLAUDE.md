## Próximos pasos

## Agent instructions
- To begin with, read ARCHITECTURE.md
- If changes made by user or agent can affect ARCHITECTURE.md changes, update said file.

### Funcionalidades
- Generar Nota de Crédito (además de Factura)
- Historial y sugerencias de datos
  - Importar datos de comprobantes anteriores y almacenarlos localmente (ej. SQLite o JSON persistente)
  - Al generar un nuevo comprobante, sugerir valores usados previamente: número de comprobante, cliente, importe, período, etc.
  - Detectar y alertar cuando ciertos campos parecen desactualizados respecto al historial (ej. número de comprobante sin incrementar, período igual al anterior, importe idéntico al último)
  - El objetivo es evitar errores por valores hardcodeados olvidados entre emisiones
- Unificar los datos de entrada en un único JSON
- Crear casos de uso explícitos: `emitir_factura`, `emitir_nota_de_credito`
- Automatizar tests para los casos de uso (`emitir_factura`, `emitir_nota_de_credito`)
- Ampliar cobertura con tests unitarios: construcción del comprobante, generación de URL del QR, conversión de datos del voucher, etc.
- Traducir conceptos al español siempre que sea posible (clases, variables, métodos, comentarios, etc.)
