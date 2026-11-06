import logging

from langchain_core.runnables import RunnableLambda

from src.enrutamiento_callback import (
    clasificar,
    con_fallback,
    enrutar,
    procesar,
)


def test_procesar_devuelve_la_respuesta_normal():
    cadena = RunnableLambda(lambda entrada: "respuesta normal")

    assert procesar(cadena, "hola") == "respuesta normal"


def test_fallback_global_registra_una_sola_vez(caplog):
    def fallar(entrada):
        raise ConnectionError("simulado")

    cadena = con_fallback(RunnableLambda(fallar))

    with caplog.at_level(logging.WARNING, logger="src.enrutamiento_callback"):
        resultado = procesar(cadena, "prueba")

    assert "gracias por tu mensaje" in resultado.lower()

    errores = [
        registro
        for registro in caplog.records
        if registro.name == "src.enrutamiento_callback"
        and "Error antes del fallback" in registro.getMessage()
    ]
    assert len(errores) == 1


def test_clasificar_normaliza_la_categoria():
    paso = clasificar(RunnableLambda(lambda entrada: "  ERROR. "))

    assert paso.invoke({"mensaje": "esto falla"}) == "error"


def test_enrutar_elige_la_ruta():
    cadena = enrutar(
        RunnableLambda(lambda entrada: "error"),
        concepto=RunnableLambda(lambda entrada: "ruta concepto"),
        error=RunnableLambda(lambda entrada: "ruta error"),
        ejemplo=RunnableLambda(lambda entrada: "ruta ejemplo"),
        general=RunnableLambda(lambda entrada: "ruta general"),
    )

    assert cadena.invoke({"mensaje": "esto falla"}) == "ruta error"
