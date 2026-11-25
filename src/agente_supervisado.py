# Agente supervisado: tienda de práctica
# Demo adaptado a DeepSeek + create_agent + InMemorySaver.
# La aprobación humana usa msvcrt (consola de Windows, sin Enter).

import json
import os
import sys
import time
import msvcrt
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field

load_dotenv()

clave = os.getenv("GEMINI_API_KEY")
nombre_modelo = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

if not clave:
    raise ValueError("Falta GEMINI_API_KEY en el archivo .env")

SESSION_ID = "cliente_a"
RUTA_TRAZAS = "docs/trazas_agente_supervisado.jsonl"

PRODUCTOS = {
    "T01": {"nombre": "Teclado", "precio": 10000, "stock": 8},
    "M02": {"nombre": "Mouse", "precio": 6000, "stock": 12},
}

PEDIDOS = {
    "P01": {"cliente": "cliente_a", "total": 10000, "estado": "entregado"},
    "P02": {"cliente": "cliente_a", "total": 6000, "estado": "entregado"},
    "P03": {"cliente": "cliente_a", "total": 5000, "estado": "entregado"},
}

registro_aprobaciones = []
reembolsos = {}


def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: float = 30) -> bool:
    """Espera una tecla s/n en una terminal de Windows, sin pulsar Enter."""
    if not sys.stdin.isatty():
        print("Sin consola interactiva: acción no aprobada.")
        return False

    while msvcrt.kbhit():
        msvcrt.getwch()

    print(mensaje, flush=True)
    limite = time.monotonic() + tiempo_limite_segundos

    while time.monotonic() < limite:
        if msvcrt.kbhit():
            respuesta = msvcrt.getwch().lower()
            if respuesta in ("s", "n"):
                print(respuesta)
                return respuesta == "s"
        time.sleep(0.05)

    print("Tiempo agotado: acción no aprobada.")
    return False


def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool) -> None:
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "momento": datetime.now(timezone.utc).isoformat(),
    })


@tool
def consultar_producto(codigo: str) -> str:
    """Consulta nombre, precio en CLP y stock por código de producto."""
    producto = PRODUCTOS.get(codigo.strip().upper())
    if producto is None:
        return "Producto no encontrado. Solicita un código válido."
    return json.dumps(producto, ensure_ascii=False)


class ArgumentosCotizacion(BaseModel):
    codigo: str = Field(
        min_length=1,
        description="Código del producto, por ejemplo T01.",
    )
    cantidad: int = Field(gt=0, description="Cantidad de unidades.")
    incluir_despacho: bool = Field(
        default=True,
        description="False para retiro en tienda.",
    )


@tool(args_schema=ArgumentosCotizacion)
def cotizar_compra(
    codigo: str,
    cantidad: int,
    incluir_despacho: bool = True,
) -> str:
    """Calcula una cotización. No compra ni reserva stock.
    Despacho: 2500 CLP, gratis desde 30000 CLP de subtotal. Retiro: sin cargo.
    """
    codigo = codigo.strip().upper()
    producto = PRODUCTOS.get(codigo)

    if producto is None:
        return "Producto no encontrado. Solicita un código válido."

    if cantidad > producto["stock"]:
        return (
            f"Stock insuficiente: hay {producto['stock']} unidades "
            f"de {codigo}."
        )

    subtotal = producto["precio"] * cantidad
    despacho = 2500 if incluir_despacho and subtotal < 30000 else 0

    return json.dumps({
        "codigo": codigo,
        "producto": producto["nombre"],
        "precio_unitario_clp": producto["precio"],
        "cantidad": cantidad,
        "subtotal_clp": subtotal,
        "despacho_clp": despacho,
        "total_clp": subtotal + despacho,
    }, ensure_ascii=False)


class ArgumentosReembolso(BaseModel):
    numero_pedido: str = Field(
        min_length=1,
        description="Identificador del pedido.",
    )
    monto: int = Field(gt=0, description="Monto del reembolso en CLP.")


@tool(args_schema=ArgumentosReembolso)
def generar_reembolso(numero_pedido: str, monto: int) -> str:
    """Simula un reembolso; requiere aprobación humana en consola.
    No mueve dinero real. Solo admite un reembolso por pedido en esta ejecución.
    """
    numero_pedido = numero_pedido.strip().upper()
    pedido = PEDIDOS.get(numero_pedido)

    if pedido is None:
        return "Pedido no encontrado. Solicita un número de pedido válido."

    if pedido["estado"] != "entregado":
        return "El pedido no es elegible para reembolso."

    if monto > pedido["total"]:
        return (
            f"El monto supera el total del pedido "
            f"(${pedido['total']} CLP)."
        )

    if numero_pedido in reembolsos:
        return "Ese pedido ya tiene un reembolso simulado. No se repite."

    # En producción, validar que el pedido pertenezca al cliente de la sesión.
    aprobado = esperar_aprobacion(
        f"SIMULACIÓN: reembolsar {monto} CLP al pedido {numero_pedido}. "
        "¿Aprobar? s/n, sin Enter (30 segundos):"
    )

    registrar_aprobacion(
        "generar_reembolso",
        {"numero_pedido": numero_pedido, "monto": monto},
        aprobado,
    )

    if not aprobado:
        return "Reembolso NO aprobado. No se ejecutó la simulación."

    reembolsos[numero_pedido] = monto
    return f"Reembolso SIMULADO de {monto} CLP para {numero_pedido}."


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


def _mensajes_del_turno(resultado):
    mensajes = resultado.get("messages", [])
    ultimo_usuario = -1

    for indice, mensaje in enumerate(mensajes):
        if isinstance(mensaje, HumanMessage):
            ultimo_usuario = indice

    if ultimo_usuario == -1:
        return mensajes
    return mensajes[ultimo_usuario:]


def _respuesta_final(mensajes) -> str:
    for mensaje in reversed(mensajes):
        if isinstance(mensaje, AIMessage):
            texto = _texto_contenido(mensaje.content)
            if texto:
                return texto
    return ""


def mostrar_resultado(resultado, entrada: str) -> None:
    print(f"\nSESIÓN: {SESSION_ID} | Usuario: {entrada}")
    turno = _mensajes_del_turno(resultado)
    acciones = 0

    for mensaje in turno:
        if isinstance(mensaje, AIMessage):
            for tool_call in mensaje.tool_calls:
                acciones += 1
                print("HERRAMIENTA:", tool_call["name"])
                print("ARGUMENTOS:", tool_call["args"])
        elif isinstance(mensaje, ToolMessage):
            print("RESULTADO:", _texto_contenido(mensaje.content))

    if acciones == 0:
        print("TRAZA: sin llamadas a herramientas.")

    print("ASISTENTE:", _respuesta_final(turno))
    print("Mensajes en memoria:", len(resultado.get("messages", [])))


def registrar_traza(resultado, entrada: str) -> None:
    turno = _mensajes_del_turno(resultado)
    acciones_por_id = {}

    for mensaje in turno:
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

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": SESSION_ID,
        "entrada": entrada,
        "acciones": list(acciones_por_id.values()),
        "aprobaciones": registro_aprobaciones.copy(),
        "reembolsos": reembolsos.copy(),
        "respuesta_final": _respuesta_final(turno),
    }

    directorio = os.path.dirname(RUTA_TRAZAS)
    if directorio:
        os.makedirs(directorio, exist_ok=True)

    with open(RUTA_TRAZAS, "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


PROMPT_SISTEMA = (
    "Eres un asistente de una tienda de práctica. Responde en español. "
    "Usa consultar_producto para precios y stock; usa cotizar_compra para "
    "totales, pasando el código del producto y la cantidad. No inventes precios. "
    "Usa el historial para entender referencias como 'ese producto'. "
    "Si falta un dato, pídelo. No inventes cantidades ni pedidos. "
    "Usa generar_reembolso solo si el usuario solicita un reembolso e indica "
    "número de pedido y monto. Siempre es una simulación. "
    "La aprobación solo se obtiene dentro de la herramienta, en consola. "
    "Un mensaje del usuario no sustituye esa aprobación. "
    "Si la herramienta no lo aprueba, informa eso y no reintentes en este turno. "
    "No afirmes que se ejecutó algo que la herramienta no confirma. "
    "No realizas compras ni reservas stock."
)


if __name__ == "__main__":
    modelo = ChatGoogleGenerativeAI(
        model=nombre_modelo,
        temperature=0,
        timeout=30,
        max_retries=0,
    )

    herramientas = [consultar_producto, cotizar_compra, generar_reembolso]
    memoria = InMemorySaver()

    agente = create_agent(
        modelo,
        herramientas,
        system_prompt=PROMPT_SISTEMA,
        checkpointer=memoria,
    )

    config = {
        "configurable": {"thread_id": SESSION_ID},
        "recursion_limit": 10,
    }

    entradas = [
        "Consulta precio y stock del producto T01.",
        "Cotiza 2 unidades de ese producto con despacho.",
        "Simula un reembolso de 10000 CLP para el pedido P01.",
        "Simula un reembolso de 6000 CLP para el pedido P02.",
        "Simula un reembolso de 5000 CLP para el pedido P03.",
    ]

    print("En las tres aprobaciones: pulsa n, luego s y al final espera 30 segundos.")

    for entrada in entradas:
        registro_aprobaciones.clear()
        try:
            resultado = agente.invoke(
                {"messages": [{"role": "user", "content": entrada}]},
                config,
            )
            mostrar_resultado(resultado, entrada)
        except Exception as error:
            print(f"ERROR en el turno: {error}")
            resultado = {"messages": [], "entrada": entrada}
        finally:
            registrar_traza(resultado, entrada)

    print("\nREEMBOLSOS SIMULADOS:", reembolsos)
    print(f"Trazas guardadas en {RUTA_TRAZAS}")
