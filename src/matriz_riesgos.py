"""Bloque 32: riesgos del asistente de la carnicería y estado de los controles."""

from configuracion import DOCS, guardar_json

RIESGOS = [
    {
        "id": "R1",
        "riesgo": "El asistente responde con un precio que ya cambió",
        "probabilidad": 4,
        "impacto": 4,
        "justificacion": "La lista de precios cambia semanal o mensualmente; un índice viejo produce una respuesta comercial equivocada.",
        "mitigacion": "Reindexado semanal de la lista y fecha de fuente en cada chunk; src/rag_indexer.py (Bloques 24 y 25).",
        "supervision": "El dueño revisa y aprueba la lista nueva antes de publicarla; si la fuente supera la semana, el asistente no responde precios.",
        "responsable": "Dueño del negocio",
        "evidencia": "Pendiente: el corpus de la carnicería todavía no está indexado.",
        "estado": "Pipeline RAG probado con otro corpus; falta cargar la lista real.",
    },
    {
        "id": "R2",
        "riesgo": "El asistente inventa un precio o una promoción que no está en las fuentes",
        "probabilidad": 3,
        "impacto": 5,
        "justificacion": "El modelo puede completar un dato faltante y comprometer al negocio.",
        "mitigacion": "Prompt con abstención y citas; sin contexto suficiente no responde; validación de citas (Bloques 26 y 31).",
        "supervision": "Si falta contexto, la consulta se deriva al dueño antes de responder.",
        "responsable": "Dueño del negocio",
        "evidencia": "Prompt v2 y flujo RAG con citas; falta prueba con preguntas reales.",
        "estado": "Diseñado; prueba real pendiente.",
    },
    {
        "id": "R3",
        "riesgo": "Una instrucción dentro de un mensaje o documento hace que el asistente ignore sus reglas",
        "probabilidad": 3,
        "impacto": 4,
        "justificacion": "El texto del cliente o del corpus puede intentar cambiar el comportamiento del asistente.",
        "mitigacion": "Filtro de patrones y delimitación de contexto; src/prevencion_prompt_inyection.py (Bloque 31).",
        "supervision": "Una consulta bloqueada pasa a revisión humana antes de reintentarse.",
        "responsable": "Responsable de seguridad",
        "evidencia": "El script bloquea 2 patrones en la pregunta y descarta un documento con 3.",
        "estado": "Prototipo probado; falta integrarlo al flujo de WhatsApp.",
    },
    {
        "id": "R4",
        "riesgo": "El tono repetitivo hace que WhatsApp banee el número del negocio",
        "probabilidad": 3,
        "impacto": 3,
        "justificacion": "Sin la API de Meta, los patrones repetitivos se parecen a un bot y arriesgan el canal.",
        "mitigacion": "Variación de respuestas, few-shot y límite de frecuencia; RF-03 del proyecto.",
        "supervision": "Revisión semanal de conversaciones marcadas por el dueño.",
        "responsable": "Dueño del negocio",
        "evidencia": "Requisito RF-03; todavía no hay conversaciones.",
        "estado": "Pendiente.",
    },
    {
        "id": "R5",
        "riesgo": "Los logs guardan teléfonos o direcciones de clientes",
        "probabilidad": 2,
        "impacto": 5,
        "justificacion": "Los clientes pegan datos personales; un log persistente amplía su exposición.",
        "mitigacion": "Registrar huellas y longitudes, no contenido crudo; src/logs_rag.py (Bloque 31).",
        "supervision": "Aprobación para acceder o exportar los logs.",
        "responsable": "Custodio de datos",
        "evidencia": "logs_rag.py registra hashes y longitudes.",
        "estado": "Parcial: falta política de acceso.",
    },
    {
        "id": "R6",
        "riesgo": "El modelo de embeddings cambia o queda deprecado y el índice queda inconsistente",
        "probabilidad": 2,
        "impacto": 3,
        "justificacion": "Un cambio de modelo obliga a reindexar; mezclar dimensiones rompe la búsqueda.",
        "mitigacion": "Manifiesto del modelo y revisión periódica; reindexar con el mismo modelo (Bloque 28).",
        "supervision": "No requiere por consulta; revisión trimestral del responsable técnico.",
        "responsable": "Responsable técnico",
        "evidencia": "Pendiente: no hay manifiesto del índice.",
        "estado": "Pendiente.",
    },
]


def puntaje_riesgo(probabilidad, impacto):
    if any(type(n) is not int or not 1 <= n <= 5 for n in (probabilidad, impacto)):
        raise ValueError("P e I deben ser enteros entre 1 y 5")
    return probabilidad * impacto


def categoria_riesgo(puntaje):
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad, impacto):
    actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto),
        (probabilidad - 1, impacto),
        (probabilidad, impacto + 1),
        (probabilidad, impacto - 1),
    ]
    return any(
        categoria_riesgo(p * i) != actual
        for p, i in vecinos
        if 1 <= p <= 5 and 1 <= i <= 5
    )


def completar_matriz():
    filas = []
    for riesgo in RIESGOS:
        fila = dict(riesgo)
        fila["puntaje"] = puntaje_riesgo(fila["probabilidad"], fila["impacto"])
        fila["categoria"] = categoria_riesgo(fila["puntaje"])
        fila["al_limite"] = esta_en_el_limite(
            fila["probabilidad"], fila["impacto"]
        )
        filas.append(fila)
    return sorted(filas, key=lambda r: -r["puntaje"])


def main():
    filas = completar_matriz()
    guardar_json(DOCS / "matriz_riesgos.json", filas)

    lineas = [
        "# Matriz de riesgos del asistente de carnicería",
        "",
        "Estimaciones previas a los controles, no probabilidades medidas. "
        "BAJO 1-3; MEDIO 4-8; ALTO 9-14; CRITICO 15-25. "
        "Los cortes son la convención del programa.",
        "",
        "AL LIMITE indica que variar un punto en P o I cambia la categoría. "
        "Cada responsable es un rol a asignar a una persona. "
        "Los controles pendientes no se presentan como implementados.",
        "",
        "| ID | Riesgo | P | I | Puntaje | Categoría | AL LIMITE |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for r in filas:
        lineas.append(
            f"| {r['id']} | {r['riesgo']} | {r['probabilidad']} | "
            f"{r['impacto']} | {r['puntaje']} | {r['categoria']} | "
            f"{'Si' if r['al_limite'] else 'No'} |"
        )
    for r in filas:
        lineas.extend(["", f"## {r['id']} {r['riesgo']}", ""])
        for campo in (
            "justificacion",
            "mitigacion",
            "supervision",
            "responsable",
            "evidencia",
            "estado",
        ):
            lineas.append(f"**{campo.capitalize()}**: {r[campo]}\n")

    (DOCS / "matriz_riesgos.md").write_text(
        "\n".join(lineas) + "\n", encoding="utf-8"
    )
    for r in filas:
        print(
            r["id"],
            r["categoria"],
            r["puntaje"],
            "AL LIMITE" if r["al_limite"] else "",
        )


if __name__ == "__main__":
    main()
