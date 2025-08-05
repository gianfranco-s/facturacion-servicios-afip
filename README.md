# Factura Monotributista

Basado en [AFIP SDK](https://afipsdk.com/)

python3 -m facturacion_servicios.main

Work in progress:
- [ ] load personal info from json
- [ ] load consumer info from json
- [ ] perform unit tests (check if tax data is correctly sent to AFIP)
- [x] generate pdf locally
- [x] generate mock pdf
- [x] use ',' as decimal separator in final invoice
- [ ] add logging
- [ ] calculate "Importe Otros tributos" and "Importe total = Subtotal + Importe Otros tributos"
- [ ] get prod credentials


# Guía de inicio
[Fuente ARCA](https://www.afip.gob.ar/ws/)

## Entorno de homologación
Es el entorno de desarrollo. Para activar el acceso programático, ingresar a ARCA, y buscar "WSASS". Ello redirecciona a https://wsass-homo.afip.gob.ar/wsass/portal/main.aspx

Para habilitar el entorno de homologación se necesita
* generar un certificado
* habilitar el servicio

En esta guía se presenta la manera de crear y habilitar el certificado por primera vez.

1. Localmente, generar private key y un pedido de firma (CSR)
```
# Private key
openssl genrsa -out gsalomone-dev-privkey 2048
# Certificate Signing Request (CSR)
openssl req -new -key gsalomone-dev-privkey -subj "/C=AR/O=gianfranco-salomone/CN=desarrollo/serialNumber=CUIT 23316378609" -out gsalomone-dev-req
```

2. Ir a ["Crear DN y certificado"](https://wsass-homo.afip.gob.ar/wsass/portal/Autoservicio/crearcomputador.aspx), y llenar los campos.
```
1. gsalomoneDnHomologacion
2. 23316378609
3. # pegar texto del CSR
-----BEGIN CERTIFICATE REQUEST-----
abcn
sldj
-----END CERTIFICATE REQUEST-----

4. Click en "Crear"
# Resultado

-----BEGIN CERTIFICATE REQUEST-----
xyz
lkjljk
-----END CERTIFICATE REQUEST-----
```

3. Guardar el contenido del resultado en un archivo .pem. Por ejemplo gsalomoneDnHomologacion.pem

4. Asociar el certificado al Web Service de negocio al que se va a acceder [aquí](https://wsass-homo.afip.gob.ar/wsass/portal/Autoservicio/crearautorizacion.aspx), elegir  `wsfe`, y al momento de ser autorizado, se leerá algo así:
```
OK. Autorización fue creada (CUITCOMPUTADOR=23316378609, ALIASCOMPUTADOR=gsalomoneDnHomologacion, CUITREPRESENTADO=23316378609, SERVICIO=ws://wsfe, CUITAUTORIZANTE=23316378609).
```
