# Herramientas Personalizadas
# Intro a Memoria

import json
import queue
import threading
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field

# Configuraciones e Inicializaciones
load_dotenv()
modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

# Memoria en RAM: guarda el estado de cada conversación por thread_id.
# En la API clásica, la profesora usa historiales + obtener_historial
# + RunnableWithMessageHistory. En LangChain 1.x usamos InMemorySaver.
memoria = InMemorySaver()

#=== Auditoría / Human in the Loop ===
registro_aprobaciones = []


def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 15) -> bool:
    cola_respuesta = queue.Queue()

    def pedir_entrada():
        try:
            texto = input(mensaje)
            # El commit original tenía texto.strip.lower(); acá lo corregimos.
            cola_respuesta.put(texto.strip().lower())
        except (EOFError, KeyboardInterrupt):
            cola_respuesta.put("")

    hilo = threading.Thread(target=pedir_entrada, daemon=True)
    hilo.start()

    try:
        respuesta = cola_respuesta.get(timeout=tiempo_limite_segundos)
        return respuesta == "s"
    except queue.Empty:
        print("Tiempo de espera agotado. Solicitud denegada por timeout")
        return False


def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool) -> None:
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "fecha_hora": datetime.now().isoformat(),
    })


#=== Persistencia y Análisis de Trazabilidad ===
def _texto_contenido(contenido) -> str:
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        partes = []
        for bloque in contenido:
            if isinstance(bloque, dict):
                partes.append(bloque.get("text", ""))
            else:
                partes.append(str(bloque))
        return " ".join(parte for parte in partes if parte).strip()
    return str(contenido or "")


def registrar_traza(session_id: str, entrada: str, resultado: dict) -> None:
    acciones_por_id = {}

    for mensaje in resultado.get("messages", []):
        if isinstance(mensaje, AIMessage):
            for tool_call in mensaje.tool_calls:
                tool_call_id = tool_call.get("id") or (
                    f"{tool_call['name']}-{len(acciones_por_id)}"
                )
                acciones_por_id[tool_call_id] = {
                    "herramienta": tool_call["name"],
                    "argumentos": tool_call["args"],
                    "observacion": "",
                }
        elif isinstance(mensaje, ToolMessage):
            accion = acciones_por_id.get(mensaje.tool_call_id)
            if accion is not None:
                accion["observacion"] = _texto_contenido(mensaje.content)

    respuesta_final = ""
    for mensaje in reversed(resultado.get("messages", [])):
        if isinstance(mensaje, AIMessage):
            texto = _texto_contenido(mensaje.content)
            if texto:
                respuesta_final = texto
                break

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": list(acciones_por_id.values()),
        "respuesta_final": respuesta_final,
    }

    with open("trazas_agente.jsonl", "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


class ArgumentosConsultaEnvio(BaseModel):
    """
    Esquema para documentar y validar argumentos campo por campo ante el LLM.
    """

    numero_seguimiento: str = Field(
        description="Número de seguimiento del envío, por ejemplo 'AR129012'."
    )
    incluir_historial: bool = Field(
        default=False,
        description="Si es True, incluye en historial completo de los estados, no solo el actual.",
    )


# Base de Datos
ESTADOS = {
    "AR12345": {
        "actual": "En tránsito, entrega estimada de 2 días",
        "historial": [
            "Recibido en depósito",
            "En tránsito",
        ],
    },
    "AR12346": {
        "actual": "Entregado",
        "historial": [
            "Recibido en depósito",
            "En tránsito",
        ],
    },
}


# Herramientas
@tool(args_schema=ArgumentosConsultaEnvio)
def consultar_estado_envio_detallado(
    numero_seguimiento: str,
    incluir_historial: bool = False,
):
    """
    Consulta el estado de un envío, con la opción de incluir el historial completo.
    """
    envio = ESTADOS.get(numero_seguimiento)

    if envio is None:
        return f"No se encontró un envío con el número {numero_seguimiento}."

    if not incluir_historial:
        return envio["actual"]

    historial = ", ".join(envio["historial"])
    return f"{envio['actual']} (historial: {historial})"


@tool
def calcular_costo_envio(peso_kg: float, distancia_km: float) -> str:
    """Calcula el costo estimado de un envío según su peso y la distancia a recorrer.
    Usar cuando el usuario pregunta cuánto va a costar enviar algo."""
    costo = 500 + (peso_kg * 120) + (distancia_km * 3)
    return f"El costo estimado es de ${costo:.2f}"


@tool
def generar_reembolso(numero_pedido: str, monto: float) -> str:
    """
    Generar un reembolso económico para un pedido. Acción irreversible:
    requiere aprobación humana antes de ejecutarse.
    """
    mensaje = (
        f"[SUPERVISIÓN HUMANA REQUERIDA] El usuario solicita reembolsar "
        f"${monto} para el pedido {numero_pedido}. ¿Desea aprobar? (s/n): "
    )

    aprobado = esperar_aprobacion(mensaje, tiempo_limite_segundos=15)

    registrar_aprobacion(
        herramienta="generar_reembolso",
        argumentos={"numero_pedido": numero_pedido, "monto": monto},
        aprobado=aprobado,
    )

    if not aprobado:
        return "Reembolso no aprobado por el supervisor o cancelado por timeout"

    return (
        f"Reembolso de {monto} fue generado con éxito "
        f"para el pedido {numero_pedido}"
    )


# Listado de herramientas
herramientas = [
    consultar_estado_envio_detallado,
    calcular_costo_envio,
    generar_reembolso,
]

# Construcción del agente
agente = create_agent(
    modelo,
    herramientas,
    system_prompt=(
        "Eres un asistente de logística que responde preguntas "
        "usando las herramientas disponibles."
    ),
    checkpointer=memoria,
)


if __name__ == "__main__":
    # Demo de memoria (comentada; se puede descomentar para probarla).
    # config1 = {"configurable": {"thread_id": "cliente_456"}}
    #
    # resultado1 = agente.invoke(
    #     {
    #         "messages": [
    #             {
    #                 "role": "user",
    #                 "content": "¿Cuál es el estado del envío AR12345, con su historial?",
    #             }
    #         ]
    #     },
    #     config1,
    # )
    # print("Turno 1:", resultado1["messages"][-1].content)
    #
    # resultado2 = agente.invoke(
    #     {
    #         "messages": [
    #             {
    #                 "role": "user",
    #                 "content": "¿Y ese mismo envío ya fue entregado?",
    #             }
    #         ]
    #     },
    #     config1,
    # )
    # print("Turno 2:", resultado2["messages"][-1].content)
    #
    # config2 = {"configurable": {"thread_id": "cliente_567"}}
    #
    # resultado3 = agente.invoke(
    #     {
    #         "messages": [
    #             {
    #                 "role": "user",
    #                 "content": "¿Cuánto cuesta enviar un paquete de 3kg a 300km?",
    #             }
    #         ]
    #     },
    #     config2,
    # )
    # print("Turno 3:", resultado3["messages"][-1].content)
    #
    # resultado4 = agente.invoke(
    #     {
    #         "messages": [
    #             {
    #                 "role": "user",
    #                 "content": "¿Y cuánto costaría con el doble de peso?",
    #             }
    #         ]
    #     },
    #     config2,
    # )
    # print("Turno 4:", resultado4["messages"][-1].content)

    # Demo de HITL (comentada; se puede descomentar para probarla).
    # config_reembolso = {"configurable": {"thread_id": "cliente_123"}}
    # resultado_reembolso = agente.invoke(
    #     {
    #         "messages": [
    #             {
    #                 "role": "user",
    #                 "content": (
    #                     "Mi pedido PED123 llegó roto. "
    #                     "Exijo un reembolso de mis 25000 pesos."
    #                 ),
    #             }
    #         ]
    #     },
    #     config_reembolso,
    # )
    # print("Resultado:", resultado_reembolso["messages"][-1].content)
    #
    # print("Registros de reembolsos:")
    # for registro in registro_aprobaciones:
    #     print(registro)

    # Demo de trazabilidad: consulta de costo + registro en JSONL.
    config_costo = {"configurable": {"thread_id": "cliente_246"}}
    entrada = "¿Cuánto me cuesta enviar un paquete de 2.5kg a 50km?"
    resultado_costo = agente.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": entrada,
                }
            ]
        },
        config_costo,
    )

    print(resultado_costo["messages"][-1].content)

    registrar_traza(
        session_id=config_costo["configurable"]["thread_id"],
        entrada=entrada,
        resultado=resultado_costo,
    )
