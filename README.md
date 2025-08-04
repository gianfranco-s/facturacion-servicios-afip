# Factura Monotributista

Basado en [AFIP SDK](https://afipsdk.com/)

python3 -m facturacion_servicios.main

Work in progress:
* load personal info from json
* load consumer info from json
* perform unit tests (check if tax data is correctly sent to AFIP)
* use ',' as decimal separator in final invoice
* add logs
* calculate "Importe Otros tributos"
* calculate "Importe total" as the sum of Subtotal + Importe Otros tributos
* get prod credentials


# Guía de inicio
https://www.afip.gob.ar/ws/
Generar entorno de homologación (es el entorno de desarrollo)

Ingresar a ARCA, y buscar "WSASS". Ello redirecciona a https://wsass-homo.afip.gob.ar/wsass/portal/main.aspx

Se necesita crear un certificado con su correspondiente Distinguished Name (DN).

Formulario por primera vez
1. Generar private key y un CSR
```
# Private key
openssl genrsa -out gsalomone-dev-privkey 2048
SR
openssl req -new -key gsalomone-dev-privkey -subj "/C=AR/O=gianfranco-salomone/CN=desarrollo/serialNumber=CUIT 23316378609" -out gsalomone-dev-req
```

3. Ir a ["Crear DN y certificado"](https://wsass-homo.afip.gob.ar/wsass/portal/Autoservicio/crearcomputador.aspx), y llenar los campos.
```
1. gsalomoneDnHomologacion
2. 23316378609
3. -----BEGIN CERTIFICATE REQUEST-----
abcn
sldj
-----END CERTIFICATE REQUEST-----

#Resultado

-----BEGIN CERTIFICATE REQUEST-----
xyz
lkjljk
-----END CERTIFICATE REQUEST-----
```

4. Guardar el contenido del resultado en un archivo .pem. Por ejemplo gsalomoneDnHomologacion.pem
5. Asociar el certificado al Web Service de negocio al que se va a acceder [aquí](https://wsass-homo.afip.gob.ar/wsass/portal/Autoservicio/crearautorizacion.aspx) (es el mismo sitio que antes)

6. Se debe elegir `wsfe`, y al momento de ser autorizado, se leerá algo así:
```
OK. Autorización fue creada (CUITCOMPUTADOR=23316378609, ALIASCOMPUTADOR=gsalomoneDnHomologacion, CUITREPRESENTADO=23316378609, SERVICIO=ws://wsfe, CUITAUTORIZANTE=23316378609).
```