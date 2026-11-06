from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek


plantilla_explicacion = PromptTemplate.from_template(
    "Explica el concepto de {concepto} en un párrafo breve, "
    "para alguien que recién empieza en Python."
)

plantilla_ideas = PromptTemplate.from_template(
    "Lee esta explicación y devuelve solo sus 3 ideas clave, "
    "una por línea, sin desarrollarlas:\n\n{explicacion}"
)

plantilla_pregunta = PromptTemplate.from_template(
    "A partir de estas ideas, redacta una sola pregunta de repaso, "
    "sin responderla, que se pueda contestar en dos o tres "
    "oraciones:\n\n{ideas}"
)


def construir_cadena(modelo):
    return (
        plantilla_explicacion
        | modelo
        | StrOutputParser()
        | (lambda explicacion: {"explicacion": explicacion})
        | plantilla_ideas
        | modelo
        | StrOutputParser()
        | (lambda ideas: {"ideas": ideas})
        | plantilla_pregunta
        | modelo
        | StrOutputParser()
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatDeepSeek(
        model="deepseek-flash",
        temperature=0,
        timeout=30,
        max_retries=2,
    )
    cadena = construir_cadena(modelo)
    print(cadena.invoke({"concepto": "una lista en Python"}))
