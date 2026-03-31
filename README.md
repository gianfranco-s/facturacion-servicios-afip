# Factura Monotributista

Generar factura:
```sh
IS_MOCK=true python3 -m facturacion_servicios.main
```

[Documentación ARCA](https://www.afip.gob.ar/ws/documentacion/arquitectura-general.asp)
[Documentación ARCA WSASS](https://www.afip.gob.ar/ws/WSASS/html/index.html)
[Web Service de factura electrónica](https://www.afip.gob.ar/ws/documentacion/ws-factura-electronica.asp)
[Manual para el desarrollador wsfev1](https://www.afip.gob.ar/fe/ayuda/documentos/wsfev1-RG-4291.pdf)
Basado en [AFIP SDK](https://afipsdk.com/)
[Guía externa para obtener certificados digitales](https://docs.afipsdk.com/recursos/tutoriales-pagina-de-arca/obtener-certificado-de-produccion)

Work in progress:
- [x] load personal info from JSON
- [x] load base invoice info from JSON
- [x] load consumer info from JSON
- [ ] perform unit tests (check if tax data is correctly sent to AFIP)
- [x] generate pdf locally
- [x] generate mock pdf
- [x] use ',' as decimal separator in final invoice
- [x] add logging
- [x] calculate "Importe Otros tributos" and "Importe total = Subtotal + Importe Otros tributos" (N/A para monotributista: ImpTrib=0, ImpIVA=0, ImpTotal=ImpNeto)
- [x] add QR code to validate invoice
- [x] improve QR rendering
- [x] get prod credentials (ver sección "Entorno de producción")


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

## Entorno de producción

Requiere Clave Fiscal nivel 3. El proceso es idéntico al de homologación, pero usando el **Administración de Certificados Digitales** dentro del portal de ARCA en lugar del portal WSASS.

1. Generar private key y CSR (mismos comandos, cambiar nombres de archivo)
```
# Private key
openssl genrsa -out gsalomone-prd-privkey 2048
# Certificate Signing Request (CSR)
openssl req -new -key gsalomone-prd-privkey -subj "/C=AR/O=gianfranco-salomone/CN=produccion/serialNumber=CUIT 23316378609" -out gsalomone-prod-req
```

2. Ingresar a [portal.afip.gob.ar](https://portalcf.cloud.afip.gob.ar) con Clave Fiscal → buscar **"Administrador de Certificados Digitales"**

3. Crear un nuevo "Computador Fiscal":
   - Alias: `gsalomoneProd` (o el nombre que elijas)
   - CUIT: `23316378609`
   - Pegar el texto del CSR (`gsalomone-prod-req`)
   - Guardar el certificado resultante como `gsalomoneProd.cert`

4. Autorizar el servicio `wsfe` para ese certificado (en el mismo administrador, sección "Autorizar servicio").

5. Vincular el certificado al servicio WSFE desde el **Administrador de Relaciones de Clave Fiscal**:
   - Ir a [arca.gob.ar](https://arca.gob.ar) → login con CUIT y Clave Fiscal
   - Buscar **"Administrador de Relaciones de Clave Fiscal"**
   - Click en **"Nueva Relación"**
   - Completar:
     - **Representado:** tu CUIT
     - **Representante:** tu CUIT
     - **Servicio:** AFIP → Servicios Interactivos → **WSFE - Facturación Electrónica**
   - Confirmar

7. Actualizar las variables de entorno o `__init__.py` para apuntar a los nuevos archivos:
```sh
export AFIP_CERT=gsalomoneProd.cert
export AFIP_KEY=gsalomone-prd-privkey
export AFIP_CUIT=23316378609
```

8. Agregar `"production": True` al inicializar el cliente en `afip_session.py`:
```python
afip_session = Afip({"CUIT": CUIT, "cert": cert, "key": key, "production": True})
```

9. Verificar emisión de comprobantes "hasta el día de ayer" en: arca.gob.ar -> Mis Comprobantes


> **Referencia oficial:** [Certificados Digitales - AFIP](https://www.afip.gob.ar/ws/programadores/certificados-digitales.asp)

---

> Si al correr la app en producción aparece el error `(11002) El punto de venta no se encuentra habilitado a usar en el presente WS`, el punto de venta no está registrado en AFIP para facturación electrónica. Pasos para habilitarlo:
>
> 1. Ir a [arca.gob.ar](https://arca.gob.ar) → login con CUIT y Clave Fiscal
> 2. Buscar **"Administración de Puntos de Venta"** -> "ABM Puntos de Venta"
> 3. Verificar el número de punto de venta que figura en `contribuyente.json` (`sales_location`)
