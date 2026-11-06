from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from src.enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
)


def test_enrutamiento_va_a_cadena_concepto():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "concepto"
    cadena_concepto_falsa = MagicMock()
    cadena_concepto_falsa.return_value = "respuesta de concepto"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_concepto=cadena_concepto_falsa,
    )
    resultado = cadena.invoke({"mensaje": "¿qué es una tupla?"})

    assert cadena_concepto_falsa.called
    assert resultado == "respuesta de concepto"


def test_enrutamiento_va_a_cadena_error():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "error"
    cadena_error_falsa = MagicMock()
    cadena_error_falsa.return_value = "respuesta de error"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_error=cadena_error_falsa,
    )
    resultado = cadena.invoke({"mensaje": "me sale KeyError"})

    assert cadena_error_falsa.called
    assert resultado == "respuesta de error"


def test_enrutamiento_va_a_cadena_ejemplo():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "ejemplo"
    cadena_ejemplo_falsa = MagicMock()
    cadena_ejemplo_falsa.return_value = "respuesta de ejemplo"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_ejemplo=cadena_ejemplo_falsa,
    )
    resultado = cadena.invoke({"mensaje": "dame un ejemplo de diccionario"})

    assert cadena_ejemplo_falsa.called
    assert resultado == "respuesta de ejemplo"


def test_enrutamiento_usa_default_ante_categoria_desconocida():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "categoria_inventada"
    cadena_general_falsa = MagicMock()
    cadena_general_falsa.return_value = "respuesta general"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_general=cadena_general_falsa,
    )
    resultado = cadena.invoke({"mensaje": "mensaje ambiguo"})

    assert cadena_general_falsa.called
    assert resultado == "respuesta general"


def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    modelo_falso.return_value = AIMessage(content=" Concepto. \n")

    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"mensaje": "algo sobre listas"}
    )

    assert resultado == "concepto"
