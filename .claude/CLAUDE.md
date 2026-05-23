## Contexto actual
<!-- Actualizar al inicio de cada sesión de trabajo -->
- Trabajando en: Nota de Crédito
- Estado: planificación completa, implementación pendiente
- No tocar: `invoice_template.html` hasta tener el caso de uso funcionando

## Próximos pasos

## Agent instructions
- To begin with, read ARCHITECTURE.md
- If changes made by user or agent can affect ARCHITECTURE.md changes, update said file.
- Every plan you make should be preceded by an abstract of no more than 10 lines, explaining the plan.

### Funcionalidades
- Mejorar preguntas de las SKILLS
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

### Implementadas
- Mejorar transición entre entornos de producción y homologación
- Generar Nota de Crédito
