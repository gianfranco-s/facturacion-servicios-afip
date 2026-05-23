from typing import Protocol


class PuertoAFIP(Protocol):
    """Puerto de salida: define la interfaz para comunicarse con ARCA/AFIP.

    Cualquier implementación concreta (SDK real, mock, stub de test) debe
    satisfacer esta interfaz estructural. El dominio y los casos de uso sólo
    dependen de este contrato, nunca de una librería externa.
    """

    def obtener_ultimo_comprobante(self, punto_venta: int, tipo_comprobante: int) -> int:
        """Retorna el número del último comprobante autorizado para el punto de venta y tipo dados."""
        ...

    def crear_comprobante(self, datos: dict) -> dict:
        """Envía un comprobante a ARCA para su autorización.

        Returns:
            dict con al menos las claves 'CAE' y 'CAEFchVto'.
        """
        ...
