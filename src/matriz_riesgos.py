"""Bloque 32: riesgos del agente de delivery y estado de los controles."""

from configuracion import DOCS, guardar_json

RIESGOS = [
    {
        "id": "R1",
        "riesgo": "Un reembolso se ejecuta por un monto o pedido incorrecto, o sin aprobación",
        "probabilidad": 3,
        "impacto": 5,
        "justificacion": "El reembolso es irreversible y mueve fondos; una validación débil o una aprobación mal informada produce pérdida directa.",
        "mitigacion": "Validación de pedido existente, estado entregado, monto menor o igual al total y un reembolso por pedido; aprobación humana en src/agente_supervisado.py y src/agente_con_memoria.py (Bloques 21-23 y 32).",
        "supervision": "Aprobación humana explícita antes de ejecutar; revisión obligatoria de trazas después de cada reembolso (docs/limites_autonomia_agente.md).",
        "responsable": "Responsable de operaciones",
        "evidencia": "esperar_aprobacion en src/agente_con_memoria.py:188; trazas_agente.jsonl.",
        "estado": "Aprobación implementada; faltan pruebas de regresión y límites de monto en producción.",
    },
    {
        "id": "R2",
        "riesgo": "Se filtran direcciones o teléfonos de clientes en logs, trazas o memoria",
        "probabilidad": 3,
        "impacto": 5,
        "justificacion": "El agente maneja datos de entrega; los logs y las trazas persistentes amplían su exposición.",
        "mitigacion": "Registrar huellas y longitudes en vez de contenido (src/logs_rag.py, Bloque 31); revisar y minimizar trazas_agente.jsonl.",
        "supervision": "Aprobación para acceder o exportar logs y trazas; revisión semanal.",
        "responsable": "Custodio de datos",
        "evidencia": "logs_rag.py registra hashes; las trazas contienen datos del pedido.",
        "estado": "Parcial: falta política de acceso y limpieza de trazas históricas.",
    },
    {
        "id": "R3",
        "riesgo": "El agente informa un estado de envío incorrecto o desactualizado",
        "probabilidad": 3,
        "impacto": 4,
        "justificacion": "El cliente decide en base al estado; un dato viejo genera reclamos y entregas fallidas.",
        "mitigacion": "consultar_estado_envio_detallado es de solo lectura y debe incluir timestamp; si el dato es viejo o desconocido, no afirmar (Bloques 21-23).",
        "supervision": "Si el estado no se puede confirmar, derivar a una persona antes de responder.",
        "responsable": "Responsable de logística",
        "evidencia": "Tool consultar_estado_envio_detallado en src/agente_con_memoria.py.",
        "estado": "Prueba con datos simulados; falta integración con el carrier real.",
    },
    {
        "id": "R4",
        "riesgo": "Un comentario del pedido o mensaje del cliente intenta cambiar las reglas del agente",
        "probabilidad": 3,
        "impacto": 4,
        "justificacion": "El texto del cliente entra al contexto y puede intentar revelar el prompt o forzar un reembolso.",
        "mitigacion": "Filtro de patrones y delimitación de contexto; src/prevencion_prompt_inyection.py (Bloque 31).",
        "supervision": "Una consulta bloqueada pasa a revisión humana antes de reintentarse.",
        "responsable": "Responsable de seguridad",
        "evidencia": "El script bloquea 2 patrones en la pregunta y descarta un documento con 3.",
        "estado": "Prototipo probado; falta integrarlo al agente de delivery.",
    },
    {
        "id": "R5",
        "riesgo": "Un cliente recibe datos de otro pedido por reutilizar el thread_id o la memoria",
        "probabilidad": 2,
        "impacto": 5,
        "justificacion": "La memoria por InMemorySaver se indexa por thread_id; un id compartido mezcla conversaciones y pedidos.",
        "mitigacion": "thread_id único por cliente y sesión, pruebas de aislamiento y no persistir memoria entre clientes (LangGraph, Bloque 23).",
        "supervision": "Revisión de trazas cuando un cliente consulta un pedido que no es suyo.",
        "responsable": "Responsable técnico",
        "evidencia": "InMemorySaver y thread_id en src/agente_con_memoria.py.",
        "estado": "Pendiente: falta prueba de aislamiento entre clientes.",
    },
    {
        "id": "R6",
        "riesgo": "El costo de envío calculado es incorrecto y se informa como definitivo",
        "probabilidad": 3,
        "impacto": 3,
        "justificacion": "calcular_costo_envio es local; un error de fórmula o de tarifa produce un precio falso.",
        "mitigacion": "Guardrail de rango y contraste con la tarifa vigente; no confirmar el monto sin validación (docs/limites_autonomia_agente.md).",
        "supervision": "Si el monto queda fuera de rango, lo revisa una persona antes de comunicarlo.",
        "responsable": "Responsable de logística",
        "evidencia": "Tool calcular_costo_envio; límite de autonomía documentado.",
        "estado": "Parcial: falta guardrail automático.",
    },
    {
        "id": "R7",
        "riesgo": "Se activa un cambio de prompt sin revisión",
        "probabilidad": 3,
        "impacto": 4,
        "justificacion": "El prompt define abstención, límites de reembolso y defensa anti-inyección; un cambio sin revisar los elimina.",
        "mitigacion": "Registro con huellas, diff, interrupt y aprobación de la huella exacta; la versión activa la leen el RAG y los agentes: src/registro_prompts.py, src/grafo_supervision.py, src/registro_rag.py, src/agente_supervisado.py y src/agente_con_memoria.py (Bloque 32).",
        "supervision": "El responsable revisa el diff y aprueba la huella exacta antes de activar.",
        "responsable": "Responsable funcional",
        "evidencia": "docs/evidencias/supervision.json; .local/prompt_activo.json (595743c6ac49); PROMPT_AGENTE incluye las reglas v2.",
        "estado": "v2 activa y leída por el agente; falta uso en producción.",
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
        "# Matriz de riesgos del agente de delivery",
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
