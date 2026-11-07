from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_deepseek import ChatDeepSeek

load_dotenv()


@tool
def buscar_en_documentacion(consulta: str) -> str:
    """Busca información en la documentación interna del producto."""
    documentacion = {
        "reintentos": (
            "El cliente reintenta hasta 3 veces ante un TimeoutError."
        ),
        "costos": (
            "El costo se calcula a partir de totalTokenCount."
        ),
    }

    for clave, texto in documentacion.items():
        if clave in consulta.lower():
            return texto

    return "No encontré información sobre esa consulta."


@tool
def calcular(expresion: str) -> str:
    """Evalúa una expresión aritmética simple, como '350 + 250'."""
    try:
        return str(eval(expresion))
    except Exception as error:
        return f"Error al evaluar: {error}"


if __name__ == "__main__":
    modelo = ChatDeepSeek(
        model="deepseek-flash",
        temperature=0,
        timeout=30,
        max_retries=2,
    )

    agente = create_agent(
        modelo,
        [buscar_en_documentacion, calcular],
        system_prompt=(
            "Usa las herramientas cuando la pregunta lo requiera. "
            "Si ninguna sirve, responde con lo que sepas."
        ),
    )

    try:
        resultado = agente.invoke({
            "messages": [
                {"role": "user", "content": "¿Cuánto es 340 + 215?"}
            ]
        })
        print(resultado["messages"][-1].content)
    except Exception as error:
        print(f"No se pudo ejecutar el agente: {error}")
