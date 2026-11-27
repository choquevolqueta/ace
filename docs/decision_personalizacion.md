# Decisión de personalización

## 1. El problema

El agente de delivery responde sobre estado de pedidos, productos, costos de envío y reembolsos. Necesita datos frescos, no inventar estados ni montos, y derivar los reembolsos a aprobación humana.

## 2. Resultado del método de decisión

| Clave | Valor | Evidencia |
|---|---|---|
| `informacion_cambia_seguido` | True | El estado de los pedidos, los precios y las tarifas cambian a diario; el agente consulta herramientas en vivo. |
| `problema_de_formato_o_tono` | False | No hay 20 respuestas medidas ni un defecto persistente de formato. Queda como riesgo a medir. |
| `dataset_grande_y_de_calidad` | False | No hay 200 ejemplos etiquetados de delivery. El tuning fue una side mission de clasificación de errores. |
| `presupuesto_limitado_o_iterar_rapido` | True | Proyecto académico; un job de tuning tarda horas y uno se perdió por una suspensión. |
| `necesita_multiples_variantes` | False | Un solo agente, un idioma, un canal. |

**Puntaje: RAG 5 · PEFT 1 · Fine-tuning completo 0.** No hay empate.

## 3. Técnica elegida y por qué

Elijo **RAG con herramientas y prompt versionado**. Lo que le falta al agente no es capacidad del modelo, sino información actualizada: el estado y el costo de un envío cambian y se consultan en vivo. Fine-tuning congelaría esos datos, y PEFT no agrega herramientas ni frescura. Tampoco hay dataset de delivery para entrenar.

Aunque `problema_de_formato_o_tono` resultara True, el puntaje quedaría **RAG 5 · PEFT 3 · Fine-tuning completo 1**: RAG seguiría ganando. No se entrena el modelo en esta iteración.

## 4. Qué necesitaría para ejecutarla

- **0 ejemplos etiquetados** para entrenar, porque no se personaliza el modelo.
- **20 conversaciones de prueba** para medir formato, tono y exactitud; hoy hay 0.
- **Integración real con el sistema de pedidos**: hoy `consultar_estado_envio_detallado` y `calcular_costo_envio` trabajan con datos simulados.
- **Conectar la versión activa del prompt** al agente: hoy el prompt está fijo en el código, aunque el registro y la supervisión ya existen.
- **1 reembolso de prueba** con aprobación humana registrada en la traza, para validar el control más crítico.
