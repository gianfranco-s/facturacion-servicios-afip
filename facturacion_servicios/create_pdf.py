
from afip import Afip
from jinja2 import Template

afip = Afip({ "CUIT": 20409378472 })

with open('./bill.html', 'r') as f:
    template = Template(f.read())


# Descargamos el HTML de ejemplo (ver mas arriba)
# y lo guardamos como bill.html
html = open("./bill.html").read()

# Nombre para el archivo (sin .pdf)
name = "PDF de prueba"

# Opciones para el archivo
options = {
  "width": 8, # Ancho de pagina en pulgadas. Usar 3.1 para ticket
  "marginLeft": 0.4, # Margen izquierdo en pulgadas. Usar 0.1 para ticket 
  "marginRight": 0.4, # Margen derecho en pulgadas. Usar 0.1 para ticket 
  "marginTop": 0.4, # Margen superior en pulgadas. Usar 0.1 para ticket 
  "marginBottom": 0.4 # Margen inferior en pulgadas. Usar 0.1 para ticket 
}

# Creamos el PDF
res = afip.ElectronicBilling.createPDF({
  "html": html,
  "file_name": name,
  "options": options
})

# Mostramos la url del archivo creado
print(res["file"])
