# Matriz de riesgos del agente de delivery

Estimaciones previas a los controles, no probabilidades medidas. BAJO 1-3; MEDIO 4-8; ALTO 9-14; CRITICO 15-25. Los cortes son la convención del programa.

AL LIMITE indica que variar un punto en P o I cambia la categoría. Cada responsable es un rol a asignar a una persona. Los controles pendientes no se presentan como implementados.

| ID | Riesgo | P | I | Puntaje | Categoría | AL LIMITE |
|---|---|---:|---:|---:|---|---|
| R1 | Un reembolso se ejecuta por un monto o pedido incorrecto, o sin aprobación | 3 | 5 | 15 | CRITICO | Si |
| R2 | Se filtran direcciones o teléfonos de clientes en logs, trazas o memoria | 3 | 5 | 15 | CRITICO | Si |
| R3 | El agente informa un estado de envío incorrecto o desactualizado | 3 | 4 | 12 | ALTO | Si |
| R4 | Un comentario del pedido o mensaje del cliente intenta cambiar las reglas del agente | 3 | 4 | 12 | ALTO | Si |
| R7 | Se activa un cambio de prompt sin revisión | 3 | 4 | 12 | ALTO | Si |
| R5 | Un cliente recibe datos de otro pedido por reutilizar el thread_id o la memoria | 2 | 5 | 10 | ALTO | Si |
| R6 | El costo de envío calculado es incorrecto y se informa como definitivo | 3 | 3 | 9 | ALTO | Si |

## R1 Un reembolso se ejecuta por un monto o pedido incorrecto, o sin aprobación

**Justificacion**: El reembolso es irreversible y mueve fondos; una validación débil o una aprobación mal informada produce pérdida directa.

**Mitigacion**: Validación de pedido existente, estado entregado, monto menor o igual al total y un reembolso por pedido; aprobación humana en src/agente_supervisado.py y src/agente_con_memoria.py (Bloques 21-23 y 32).

**Supervision**: Aprobación humana explícita antes de ejecutar; revisión obligatoria de trazas después de cada reembolso (docs/limites_autonomia_agente.md).

**Responsable**: Responsable de operaciones

**Evidencia**: esperar_aprobacion en src/agente_con_memoria.py:188; trazas_agente.jsonl.

**Estado**: Aprobación implementada; faltan pruebas de regresión y límites de monto en producción.


## R2 Se filtran direcciones o teléfonos de clientes en logs, trazas o memoria

**Justificacion**: El agente maneja datos de entrega; los logs y las trazas persistentes amplían su exposición.

**Mitigacion**: Registrar huellas y longitudes en vez de contenido (src/logs_rag.py, Bloque 31); revisar y minimizar trazas_agente.jsonl.

**Supervision**: Aprobación para acceder o exportar logs y trazas; revisión semanal.

**Responsable**: Custodio de datos

**Evidencia**: logs_rag.py registra hashes; las trazas contienen datos del pedido.

**Estado**: Parcial: falta política de acceso y limpieza de trazas históricas.


## R3 El agente informa un estado de envío incorrecto o desactualizado

**Justificacion**: El cliente decide en base al estado; un dato viejo genera reclamos y entregas fallidas.

**Mitigacion**: consultar_estado_envio_detallado es de solo lectura y debe incluir timestamp; si el dato es viejo o desconocido, no afirmar (Bloques 21-23).

**Supervision**: Si el estado no se puede confirmar, derivar a una persona antes de responder.

**Responsable**: Responsable de logística

**Evidencia**: Tool consultar_estado_envio_detallado en src/agente_con_memoria.py.

**Estado**: Prueba con datos simulados; falta integración con el carrier real.


## R4 Un comentario del pedido o mensaje del cliente intenta cambiar las reglas del agente

**Justificacion**: El texto del cliente entra al contexto y puede intentar revelar el prompt o forzar un reembolso.

**Mitigacion**: Filtro de patrones y delimitación de contexto; src/prevencion_prompt_inyection.py (Bloque 31).

**Supervision**: Una consulta bloqueada pasa a revisión humana antes de reintentarse.

**Responsable**: Responsable de seguridad

**Evidencia**: El script bloquea 2 patrones en la pregunta y descarta un documento con 3.

**Estado**: Prototipo probado; falta integrarlo al agente de delivery.


## R7 Se activa un cambio de prompt sin revisión

**Justificacion**: El prompt define abstención, límites de reembolso y defensa anti-inyección; un cambio sin revisar los elimina.

**Mitigacion**: Registro con huellas, diff, interrupt y aprobación de la huella exacta; la versión activa la leen el RAG y los agentes: src/registro_prompts.py, src/grafo_supervision.py, src/registro_rag.py, src/agente_supervisado.py y src/agente_con_memoria.py (Bloque 32).

**Supervision**: El responsable revisa el diff y aprueba la huella exacta antes de activar.

**Responsable**: Responsable funcional

**Evidencia**: docs/evidencias/supervision.json; .local/prompt_activo.json (595743c6ac49); PROMPT_AGENTE incluye las reglas v2.

**Estado**: v2 activa y leída por el agente; falta uso en producción.


## R5 Un cliente recibe datos de otro pedido por reutilizar el thread_id o la memoria

**Justificacion**: La memoria por InMemorySaver se indexa por thread_id; un id compartido mezcla conversaciones y pedidos.

**Mitigacion**: thread_id único por cliente y sesión, pruebas de aislamiento y no persistir memoria entre clientes (LangGraph, Bloque 23).

**Supervision**: Revisión de trazas cuando un cliente consulta un pedido que no es suyo.

**Responsable**: Responsable técnico

**Evidencia**: InMemorySaver y thread_id en src/agente_con_memoria.py.

**Estado**: Pendiente: falta prueba de aislamiento entre clientes.


## R6 El costo de envío calculado es incorrecto y se informa como definitivo

**Justificacion**: calcular_costo_envio es local; un error de fórmula o de tarifa produce un precio falso.

**Mitigacion**: Guardrail de rango y contraste con la tarifa vigente; no confirmar el monto sin validación (docs/limites_autonomia_agente.md).

**Supervision**: Si el monto queda fuera de rango, lo revisa una persona antes de comunicarlo.

**Responsable**: Responsable de logística

**Evidencia**: Tool calcular_costo_envio; límite de autonomía documentado.

**Estado**: Parcial: falta guardrail automático.

