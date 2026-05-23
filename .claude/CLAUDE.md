## Contexto actual
<!-- Actualizar al inicio de cada sesión de trabajo -->
- Trabajando en: Unificar datos de ingreso en un único JSON y persistencia de salida
- Estado: Planificando

## Próximos pasos

## Agent instructions
- To begin with, read `.claude/ARCHITECTURE.md`
- If changes made by user or agent can affect `.claude/ARCHITECTURE.md`, update said file.
- Every plan you make should be preceded by an abstract of no more than 10 lines, explaining the plan.

## Design decisions
- Currently based in AFIPSDK(afip-py) package. Will eventually change it to avoid costs.
- Ponder if a new feature requires using AFIPSDK(afip-py). If implementation is simple, avoid AFIPSDK.

### Funcionalidades
- Mejorar preguntas de las SKILLS
- Historial y sugerencias de datos
  - Importar datos de comprobantes anteriores y almacenarlos localmente (ej. SQLite o JSON persistente)
  - Al generar un nuevo comprobante, sugerir valores usados previamente: número de comprobante, cliente, importe, período, etc.
  - Detectar y alertar cuando ciertos campos parecen desactualizados respecto al historial (ej. número de comprobante sin incrementar, período igual al anterior, importe idéntico al último)
  - El objetivo es evitar errores por valores hardcodeados olvidados entre emisiones
