import json
import base64
import io
from datetime import datetime
import segno


def invoice_validation_url(
    cuit: int | None = None,
    cae: int | None = None,
    fecha_emision: datetime | None = None,
    tipo_factura_code: int | None = None,
    punto_venta: int | None = None,
    numero_comprobante: int | None = None,
    importe_total: float | None = None,
    tipo_doc_receptor_code: int | None = None,
    numero_doc_receptor: int | None = None,
    is_mock: bool = False,
) -> str:
    """
    Returns a Base64-PNG data URI for the AFIP QR validation link,
    built from the form fields.

    Mock values generate a valid URL
    """

    if is_mock:
        print("WARNING: replacing values with mock")
        cuit = 23368708194
        cae = 75314447442077
        fecha_emision = datetime(2025, 7, 31)
        tipo_factura_code = 11
        punto_venta = 1
        numero_comprobante = 52
        importe_total = 538473.88
        tipo_doc_receptor_code = 80
        numero_doc_receptor = 30626786657

    payload = {
        "ver":         1,
        "fecha":       fecha_emision.strftime(r"%Y-%m-%d"),
        "cuit":        cuit,
        "ptoVta":      punto_venta,
        "tipoCmp":     tipo_factura_code,
        "nroCmp":      numero_comprobante,
        "importe":     round(importe_total, 2),
        "moneda":      "PES",
        "ctz":         1.000,
        "tipoDocRec":  tipo_doc_receptor_code,
        "nroDocRec":   numero_doc_receptor,
        "tipoCodAut":  "E",         # "E" for normal CAE
        "codAut":      cae
    }

    for k, v in payload.items():
        if v is None:
            raise ValueError(f"Invalid value of None for field {k} in payload")

    compact = json.dumps(payload, separators=(",", ":"))
    b64_json = base64.b64encode(compact.encode("utf-8")).decode("ascii")

    return f"https://www.afip.gob.ar/fe/qr/?p={b64_json}"


def generate_qr(qr_url: str) -> str:
    qr = segno.make(qr_url, micro=False)
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=5)
    img_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{img_b64}"


if __name__ == "__main__":
    validation_url = invoice_validation_url(
        cuit=23368708194,
        cae=75314447442077,
        fecha_emision=datetime(2025, 7, 31),
        tipo_factura_code=11,
        punto_venta=1,
        numero_comprobante=52,
        importe_total=538473.88,
        tipo_doc_receptor_code=80,
        numero_doc_receptor=30626786657
    )
    print(validation_url)
    qr_data_uri = generate_qr(validation_url)
    print(qr_data_uri)
