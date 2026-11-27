"""Bloque 32: interrupt real, huella revisada y caminos de aprobación y rechazo."""

import argparse
from typing import TypedDict
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from configuracion import DOCS, guardar_json
from registro_prompts import (
    ARCHIVO_ACTIVO,
    NOMBRE_PROMPT,
    cargar_registro,
    diff_prompts,
    obtener_activa,
)


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    huella_activa: str
    aprobado: bool


def supervisar(estado):
    decision = interrupt(
        {
            "motivo": "Revisar diff y aprobar activación local del prompt",
            "huella_propuesta": estado["huella_nueva"],
            "huella_activa": estado["huella_activa"],
        }
    )
    if type(decision) is not bool:
        raise ValueError("La decisión debe ser un booleano, nunca un texto como 'no'")
    return {"aprobado": decision}


def aplicar(estado):
    return {"huella_activa": estado["huella_nueva"]} if estado["aprobado"] else {}


def crear_app():
    grafo = StateGraph(EstadoDespliegue)
    grafo.add_node("supervisar", supervisar)
    grafo.add_node("aplicar", aplicar)
    grafo.add_edge(START, "supervisar")
    grafo.add_edge("supervisar", "aplicar")
    grafo.add_edge("aplicar", END)
    return grafo.compile(checkpointer=InMemorySaver())


def iniciar(app, anterior, nueva):
    config = {"configurable": {"thread_id": "prompt-" + uuid4().hex}}
    resultado = app.invoke(
        {"huella_nueva": nueva, "huella_activa": anterior, "aprobado": False},
        config=config,
    )
    if "__interrupt__" not in resultado or resultado["huella_activa"] != anterior:
        raise RuntimeError("No se verificó la pausa anterior a la activación")
    return config, resultado


def resolver(app, config, aprobar, huella_revisada):
    if type(aprobar) is not bool:
        raise ValueError("La decisión debe ser True o False")
    snapshot = app.get_state(config)
    if not snapshot.next or not snapshot.interrupts:
        raise ValueError("No existe una aprobación pendiente en este hilo")
    if snapshot.values["huella_nueva"] != huella_revisada:
        raise ValueError("La huella pendiente no coincide con la revisada")
    return app.invoke(Command(resume=aprobar), config=config)


def persistir_activacion(final, anterior, ruta=None):
    archivo = ruta or ARCHIVO_ACTIVO
    if not final["aprobado"]:
        return
    if obtener_activa(archivo)["huella"] != anterior:
        raise ValueError(
            "La versión activa cambió durante la revisión. Iniciá otra solicitud"
        )
    if not any(
        v["huella"] == final["huella_activa"] for v in cargar_registro().versiones
    ):
        raise ValueError("La versión propuesta no está registrada")
    temporal = archivo.with_name(archivo.name + "." + uuid4().hex + ".tmp")
    guardar_json(temporal, {"huella": final["huella_activa"]})
    temporal.replace(archivo)


def verificar():
    registro = cargar_registro()
    anterior = registro.versiones[0]["huella"]
    nueva = registro.versiones[-1]["huella"]
    app = crear_app()
    evidencias = []
    for decision in (True, False):
        config, _ = iniciar(app, anterior, nueva)
        final = resolver(app, config, decision, nueva)
        assert final["huella_activa"] == (nueva if decision else anterior)
        evidencias.append(
            {
                "thread_id": config["configurable"]["thread_id"],
                "pausa_verificada": True,
                "decision": decision,
                "estado_final": final,
            }
        )
    guardar_json(DOCS / "evidencias" / "supervision.json", evidencias)
    print(
        "OK: pausa, aprobación y rechazo. "
        "Prueba automática; no cambia la versión activa."
    )
    return evidencias


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verificar", action="store_true")
    args = parser.parse_args()
    if args.verificar:
        verificar()
        return

    anterior = obtener_activa()
    nueva = cargar_registro().ultima(NOMBRE_PROMPT)
    if anterior["huella"] == nueva["huella"]:
        print("La última versión ya está activa. No hay cambio que aprobar.")
        return

    print(diff_prompts(anterior["texto"], nueva["texto"]))
    app = crear_app()
    config, _ = iniciar(app, anterior["huella"], nueva["huella"])
    print("PAUSADO:", app.get_state(config).interrupts[0].value)

    respuesta = input("Escribe aprobar o rechazar: ").strip().lower()
    while respuesta not in {"aprobar", "rechazar"}:
        respuesta = input("Escribe aprobar o rechazar: ").strip().lower()

    final = resolver(app, config, respuesta == "aprobar", nueva["huella"])
    persistir_activacion(final, anterior["huella"])
    guardar_json(
        ARCHIVO_ACTIVO.parent / "ultima_revision_prompt.json",
        {
            "thread_id": config["configurable"]["thread_id"],
            "decision": respuesta,
            "estado_final": final,
        },
    )
    print("Huella activa:", obtener_activa()["huella"])


if __name__ == "__main__":
    main()
