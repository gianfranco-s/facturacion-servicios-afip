# Changelog

## [v0.1.0] - 2026-03-31

Initial release. Generates Factura C for monotributistas via AFIP WSFE + AFIPSDK.

### Features
- Load taxpayer, consumer, and invoice data from JSON files
- Generate invoice PDF locally using a Jinja2 HTML template
- Mock mode for local development (no AFIP connection required)
- Connect to AFIP WSFE to obtain CAE (Código de Autorización Electrónico)
- QR code embedded in PDF linking to AFIP's invoice validation service
- Support for homologación (dev) and production environments
- Config via environment variables (`AFIP_CERT`, `AFIP_KEY`, `AFIP_CUIT`, `AFIP_ACCESS_TOKEN`)
- Logging throughout invoice generation flow
- Correct monotributista amounts: `ImpNeto = ImpTotal`, `ImpIVA = ImpTrib = 0`
- Comma as decimal separator in final PDF
