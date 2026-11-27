# Matriz de riesgos del asistente de carnicería

Estimaciones previas a los controles, no probabilidades medidas. BAJO 1-3; MEDIO 4-8; ALTO 9-14; CRITICO 15-25. Los cortes son la convención del programa.

AL LIMITE indica que variar un punto en P o I cambia la categoría. Cada responsable es un rol a asignar a una persona. Los controles pendientes no se presentan como implementados.

| ID | Riesgo | P | I | Puntaje | Categoría | AL LIMITE |
|---|---|---:|---:|---:|---|---|
| R1 | El asistente responde con un precio que ya cambió | 4 | 4 | 16 | CRITICO | Si |
| R2 | El asistente inventa un precio o una promoción que no está en las fuentes | 3 | 5 | 15 | CRITICO | Si |
| R3 | Una instrucción dentro de un mensaje o documento hace que el asistente ignore sus reglas | 3 | 4 | 12 | ALTO | Si |
| R5 | Los logs guardan teléfonos o direcciones de clientes | 2 | 5 | 10 | ALTO | Si |
| R4 | El tono repetitivo hace que WhatsApp banee el número del negocio | 3 | 3 | 9 | ALTO | Si |
| R6 | El modelo de embeddings cambia o queda deprecado y el índice queda inconsistente | 2 | 3 | 6 | MEDIO | Si |

## R1 El asistente responde con un precio que ya cambió

**Justificacion**: La lista de precios cambia semanal o mensualmente; un índice viejo produce una respuesta comercial equivocada.

**Mitigacion**: Reindexado semanal de la lista y fecha de fuente en cada chunk; src/rag_indexer.py (Bloques 24 y 25).

**Supervision**: El dueño revisa y aprueba la lista nueva antes de publicarla; si la fuente supera la semana, el asistente no responde precios.

**Responsable**: Dueño del negocio

**Evidencia**: Pendiente: el corpus de la carnicería todavía no está indexado.

**Estado**: Pipeline RAG probado con otro corpus; falta cargar la lista real.


## R2 El asistente inventa un precio o una promoción que no está en las fuentes

**Justificacion**: El modelo puede completar un dato faltante y comprometer al negocio.

**Mitigacion**: Prompt con abstención y citas; sin contexto suficiente no responde; validación de citas (Bloques 26 y 31).

**Supervision**: Si falta contexto, la consulta se deriva al dueño antes de responder.

**Responsable**: Dueño del negocio

**Evidencia**: Prompt v2 y flujo RAG con citas; falta prueba con preguntas reales.

**Estado**: Diseñado; prueba real pendiente.


## R3 Una instrucción dentro de un mensaje o documento hace que el asistente ignore sus reglas

**Justificacion**: El texto del cliente o del corpus puede intentar cambiar el comportamiento del asistente.

**Mitigacion**: Filtro de patrones y delimitación de contexto; src/prevencion_prompt_inyection.py (Bloque 31).

**Supervision**: Una consulta bloqueada pasa a revisión humana antes de reintentarse.

**Responsable**: Responsable de seguridad

**Evidencia**: El script bloquea 2 patrones en la pregunta y descarta un documento con 3.

**Estado**: Prototipo probado; falta integrarlo al flujo de WhatsApp.


## R5 Los logs guardan teléfonos o direcciones de clientes

**Justificacion**: Los clientes pegan datos personales; un log persistente amplía su exposición.

**Mitigacion**: Registrar huellas y longitudes, no contenido crudo; src/logs_rag.py (Bloque 31).

**Supervision**: Aprobación para acceder o exportar los logs.

**Responsable**: Custodio de datos

**Evidencia**: logs_rag.py registra hashes y longitudes.

**Estado**: Parcial: falta política de acceso.


## R4 El tono repetitivo hace que WhatsApp banee el número del negocio

**Justificacion**: Sin la API de Meta, los patrones repetitivos se parecen a un bot y arriesgan el canal.

**Mitigacion**: Variación de respuestas, few-shot y límite de frecuencia; RF-03 del proyecto.

**Supervision**: Revisión semanal de conversaciones marcadas por el dueño.

**Responsable**: Dueño del negocio

**Evidencia**: Requisito RF-03; todavía no hay conversaciones.

**Estado**: Pendiente.


## R6 El modelo de embeddings cambia o queda deprecado y el índice queda inconsistente

**Justificacion**: Un cambio de modelo obliga a reindexar; mezclar dimensiones rompe la búsqueda.

**Mitigacion**: Manifiesto del modelo y revisión periódica; reindexar con el mismo modelo (Bloque 28).

**Supervision**: No requiere por consulta; revisión trimestral del responsable técnico.

**Responsable**: Responsable técnico

**Evidencia**: Pendiente: no hay manifiesto del índice.

**Estado**: Pendiente.

