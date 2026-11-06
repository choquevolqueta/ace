from unittest.mock import MagicMock

from langchain_core.runnables import RunnableLambda

from src.enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_cadena_error_segura,
    procesar_mensaje_seguro,
)


def test_cadena_error_usa_fallback_ante_fallo_del_modelo():
    def fallar_a_proposito(entrada):
        raise ConnectionError("simulado")

    cadena_error_falsa = RunnableLambda(fallar_a_proposito)
    cadena_segura = construir_cadena_error_segura(cadena_error_falsa)

    resultado = cadena_segura.invoke({"mensaje": "esto no funciona"})

    assert "traceback" in resultado.lower()


def test_procesar_mensaje_seguro_no_propaga_excepciones():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("simulado")

    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
    )

    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")

    assert "no pudimos procesar" in resultado.lower()


def test_procesar_mensaje_seguro_devuelve_la_respuesta_normal():
    cadena_falsa = RunnableLambda(lambda entrada: "respuesta normal")

    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")

    assert resultado == "respuesta normal"
