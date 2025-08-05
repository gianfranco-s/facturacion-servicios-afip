# Factura Monotributista

Generar factura:
```sh
IS_MOCK=false python3 -m facturacion_servicios.main
```

[Documentación ARCA](https://www.afip.gob.ar/ws/documentacion/arquitectura-general.asp)
[Documentación ARCA WSASS](https://www.afip.gob.ar/ws/WSASS/html/index.html)
[Web Service de factura electrónica](https://www.afip.gob.ar/ws/documentacion/ws-factura-electronica.asp)
[Manual para el desarrollador wsfev1](https://www.afip.gob.ar/fe/ayuda/documentos/wsfev1-RG-4291.pdf)
Basado en [AFIP SDK](https://afipsdk.com/)

Work in progress:
- [x] load personal info from JSON
- [x] load base invoice info from JSON
- [x] load consumer info from JSON
- [ ] perform unit tests (check if tax data is correctly sent to AFIP)
- [x] generate pdf locally
- [x] generate mock pdf
- [x] use ',' as decimal separator in final invoice
- [ ] add logging
- [ ] calculate "Importe Otros tributos" and "Importe total = Subtotal + Importe Otros tributos"
- [x] add QR code to validate invoice
- [ ] improve QR rendering
- [ ] get prod credentials


<details>
  <summary>Notas sobre los archivos JSON</summary>
    consumidor.json / contribuyente.json
    ```json
    {
        ...
        "id_type": "cuit",  # ver TipoDeDocumento
        ...
        "tax_situation": "responsable_monotributo",  # ver CondicionFrenteIVA
        ...
    }
    ```

    base_invoice_data.json
    ```json
    {
        "month_billed": 8,  # enteros, 1 a 12
        "concept": "servicios",  # ver Concepto
        "invoice_type": "c"  # ver TipoFactura
    }

    ```

</details>


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
