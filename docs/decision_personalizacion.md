# Decisión de personalización

## 1. El problema

La carnicería de mis padres no alcanza a responder por WhatsApp las consultas de precios, horarios y preguntas frecuentes. Necesito un asistente que responda con información correcta, sin inventar, y con un tono natural.

## 2. Resultado del método de decisión

| Clave | Valor | Evidencia |
|---|---|---|
| `informacion_cambia_seguido` | True | Los precios cambian semanal o mensualmente; la ficha pide conexión a la base de precios en tiempo real. |
| `problema_de_formato_o_tono` | False | No hay 20 respuestas todavía para medir fallos. El tono es un requisito, pero no una evidencia. |
| `dataset_grande_y_de_calidad` | False | No hay dataset etiquetado; la información es una lista de precios y un FAQ. |
| `presupuesto_limitado_o_iterar_rapido` | True | Negocio familiar, sin presupuesto para varios entrenamientos; un cambio de precio debe verse el mismo día. |
| `necesita_multiples_variantes` | False | Un negocio, un idioma, un canal. |

**Puntaje: RAG 5 · PEFT 1 · Fine-tuning completo 0.** No hay empate.

## 3. Técnica elegida y por qué

Elijo **RAG**. Lo que le falta al asistente no es capacidad del modelo, sino información actualizada: los precios y horarios cambian, y RAG se actualiza reindexando los documentos. Fine-tuning congelaría los precios del día del entrenamiento, y PEFT no resuelve la frescura ni la falta de dataset. El tono humano se maneja con el prompt y ejemplos de conversación, no con los pesos. Aun si el tono fallara en 3 de 20 respuestas, RAG seguiría ganando (5 contra 3).

## 4. Qué necesitaría para ejecutarla

- **3 documentos**: lista de precios, horarios/ubicación y FAQ. Hoy tengo **0 de 3** digitalizados.
- **Reindexado semanal**, porque la lista de precios cambia; ese proceso todavía no existe.
- **20–30 conversaciones de prueba** para validar exactitud y tono. Hoy tengo 0.
- **0 ejemplos etiquetados** para entrenar, porque no voy a personalizar el modelo.
