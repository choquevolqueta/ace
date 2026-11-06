from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from src.cadena_tres_pasos import construir_cadena


def test_cadena_conecta_los_tres_pasos():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
        AIMessage(content="Python es un lenguaje interpretado."),
        AIMessage(
            content=(
                "Es interpretado\n"
                "Tiene sintaxis simple\n"
                "Es multipropósito"
            )
        ),
        AIMessage(
            content="¿Por qué se dice que Python es interpretado?"
        ),
    ]

    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"concepto": "Python"})

    assert modelo_falso.call_count == 3
    assert "interpretado" in resultado
