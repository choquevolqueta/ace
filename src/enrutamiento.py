import logging

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_deepseek import ChatDeepSeek

from src.cadena_tres_pasos import construir_cadena


load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="app.log",
    filemode="a",
    encoding="utf-8",
    force=True,
)
logger = logging.getLogger(__name__)


plantilla_clasificacion = PromptTemplate.from_template(
    "Clasifica la siguiente duda sobre Python en una sola "
    "palabra: concepto, error o ejemplo. Responde solo con "
    "esa palabra.\n\n{mensaje}"
)

plantilla_error = PromptTemplate.from_template(
    "Explica qué significa este error de Python y cómo "
    "diagnosticarlo:\n\n{mensaje}"
)

plantilla_ejemplo = PromptTemplate.from_template(
    "Da un ejemplo de código en Python para esta duda y "
    "explícalo en pocas líneas:\n\n{mensaje}"
)

plantilla_general = PromptTemplate.from_template(
    "Responde esta duda sobre Python de forma clara y "
    "breve:\n\n{mensaje}"
)


def construir_paso_clasificacion(modelo):
    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower().rstrip("."))
    )


def construir_cadena_concepto(modelo):
    return (
        (lambda entrada: {"concepto": entrada["mensaje"]})
        | construir_cadena(modelo)
    )


respuesta_error_generica = RunnableLambda(
    lambda entrada: (
        "No pude analizar el error en este momento. "
        "Revisa la última línea del traceback: ahí aparece el tipo "
        "de error y el archivo donde ocurrió."
    )
)


def construir_cadena_error_segura(cadena_error):
    return cadena_error.with_fallbacks([respuesta_error_generica])


def procesar_mensaje_seguro(cadena, mensaje):
    try:
        return cadena.invoke({"mensaje": mensaje})
    except Exception as error:
        logger.error("Error procesando mensaje: %s", error)
        return (
            "No pudimos procesar tu mensaje en este momento. "
            "Intenta de nuevo más tarde."
        )


def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_concepto=None,
    cadena_error=None,
    cadena_ejemplo=None,
    cadena_general=None,
):
    cadena_concepto = cadena_concepto or RunnablePassthrough()
    cadena_error = cadena_error or RunnablePassthrough()
    cadena_ejemplo = cadena_ejemplo or RunnablePassthrough()
    cadena_general = cadena_general or RunnablePassthrough()

    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "concepto", cadena_concepto),
        (lambda x: x["categoria"] == "error", cadena_error),
        (lambda x: x["categoria"] == "ejemplo", cadena_ejemplo),
        cadena_general,
    )

    return (
        RunnablePassthrough.assign(categoria=paso_clasificacion)
        | bifurcacion
    )


if __name__ == "__main__":
    modelo = ChatDeepSeek(
        model="deepseek-flash",
        temperature=0,
        timeout=30,
        max_retries=2,
    )

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=construir_paso_clasificacion(modelo),
        cadena_concepto=construir_cadena_concepto(modelo),
        cadena_error=construir_cadena_error_segura(
            plantilla_error | modelo | StrOutputParser()
        ),
        cadena_ejemplo=plantilla_ejemplo | modelo | StrOutputParser(),
        cadena_general=plantilla_general | modelo | StrOutputParser(),
    )

    mensajes = [
        "¿Qué es una lista en Python?",
        "Me sale IndexError al recorrer una lista.",
        "Muéstrame cómo recorrer una lista con un for.",
    ]

    for mensaje in mensajes:
        print(mensaje)
        print(procesar_mensaje_seguro(cadena, mensaje))
        print()
