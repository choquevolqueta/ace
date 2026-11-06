import logging

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
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


def clasificar(modelo):
    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower().rstrip("."))
    )


def ruta_concepto(modelo):
    return (
        (lambda entrada: {"concepto": entrada["mensaje"]})
        | construir_cadena(modelo)
    )


def ruta_error(modelo):
    return plantilla_error | modelo | StrOutputParser()


def ruta_ejemplo(modelo):
    return plantilla_ejemplo | modelo | StrOutputParser()


def ruta_general(modelo):
    return plantilla_general | modelo | StrOutputParser()


def enrutar(paso, concepto, error, ejemplo, general):
    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "concepto", concepto),
        (lambda x: x["categoria"] == "error", error),
        (lambda x: x["categoria"] == "ejemplo", ejemplo),
        general,
    )

    return (
        RunnablePassthrough.assign(categoria=paso)
        | bifurcacion
    )


respuesta_generica = RunnableLambda(
    lambda entrada: (
        "Gracias por tu mensaje. "
        "Un miembro de nuestro equipo te va a responder pronto."
    )
)


def con_fallback(cadena):
    return cadena.with_fallbacks([respuesta_generica])


class CapturaError(BaseCallbackHandler):
    def on_chain_error(self, error, *, parent_run_id=None, **kwargs):
        if parent_run_id is not None:
            return
        logger.warning(
            "Error antes del fallback: [%s] -> %s",
            type(error).__name__,
            error,
        )


captura = CapturaError()


def procesar(cadena, mensaje):
    try:
        return cadena.invoke(
            {"mensaje": mensaje},
            config={"callbacks": [captura]},
        )
    except Exception as error:
        logger.error("Error procesando mensaje: %s", error)
        return (
            "No pudimos procesar tu mensaje en este momento. "
            "Intenta de nuevo más tarde."
        )


if __name__ == "__main__":
    modelo = ChatDeepSeek(
        model="deepseek-flash",
        temperature=0,
        timeout=30,
        max_retries=2,
    )

    cadena = con_fallback(
        enrutar(
            clasificar(modelo),
            concepto=ruta_concepto(modelo),
            error=ruta_error(modelo),
            ejemplo=ruta_ejemplo(modelo),
            general=ruta_general(modelo),
        )
    )

    print(procesar(cadena, "Llevo varios días sin poder entrar a mi cuenta."))
