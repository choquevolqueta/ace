# Límites de autonomía: Agente Adelita

## Herramientas y nivel de riesgo

- `consultar_estado_envio_detallado`: bajo, solo hace peticiones de tipo lectura
- `calcular_costo_envio`: bajo, es un cálculo local; no modifica estado ni mueve dinero. Su resultado puede ser incorrecto, pero se puede validar con un guardrail antes de usarlo.
- `generar_reembolso`: alto, es irreversible, requiere necesariamente, la aprobacion de un ser humano para su ejecucion

## Herramientas que requieren aprobación humana


- `[generar_reembolso]`: Generar reembolso, en el flujo, autoriza reembolsos a clientes en caso de desperfectos o alguna eventualidad, al tratar de una herramienta que toca fondos de la empresa, es necesario el concepto HITL para descargos y responsabilidades

## Revisión de trazas

- **Frecuencia:** revisión obligatoria después de cada ejecución de `generar_reembolso`; revisión completa de `trazas_agente.jsonl` al menos una vez por semana o cada 10 interacciones, lo que ocurra primero.
- **Qué se busca:**
  - `generar_reembolso` ejecutado sin una aprobación humana registrada.
  - Reembolsos con `monto` negativo, cero, mayor al valor del pedido o con `numero_pedido` inexistente.
  - Llamadas a herramientas que no se corresponden con la intención del usuario.
  - Reintentos o bucles anormales de una misma herramienta.
  - Diferencias entre lo que muestra la traza y la respuesta final del agente.
  - Sesiones con muchas acciones en un solo turno o intentos de saltear la aprobación.
  - Textos que parezcan inyección de prompt ("ignorá las reglas", "aprobá sin preguntar").

## Qué hacer ante un comportamiento inesperado

1. **Contener:** quitar `generar_reembolso` de `herramientas` o comentar su registro, para que el agente no pueda ejecutar la acción de riesgo alto.
2. **Preservar evidencia:** copiar `trazas_agente.jsonl` y guardar la salida de `registro_aprobaciones` antes de modificar nada.
3. **Reproducir en seguro:** repetir la entrada con la herramienta de alto riesgo deshabilitada o en un entorno de prueba; no volver a ejecutar el reembolso real.
4. **Diagnosticar:** revisar en la traza qué herramienta eligió el agente, con qué argumentos, qué observación devolvió y si hubo aprobación. Revisar también el system prompt y la descripción de la herramienta.
5. **Corregir la causa:** ajustar la descripción/docstring de la herramienta, el `args_schema` (por ejemplo `monto > 0` y un límite máximo), el system prompt, o agregar validación de negocio (pedido existente, monto menor o igual al total).
6. **Agregar prueba de regresión:** por ejemplo, un reembolso sin aprobación debe devolver rechazo; un monto negativo debe fallar; un monto mayor al pedido debe rechazarse.
7. **Reactivar con control:** volver a habilitar `generar_reembolso` solo con aprobación humana y monitorear las primeras N ejecuciones.
8. **Registrar el incidente:** dejar nota de qué pasó, qué se cambió y cómo se verificó.

## Verificación con código y trazas reales

- Aprobación implementada:

```bash
grep -n "esperar_aprobacion(" src/agente_con_memoria.py
```

Resultado real:

```text
30:def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 15) -> bool:
188:    aprobado = esperar_aprobacion(mensaje, tiempo_limite_segundos=15)
```

La línea 188 está dentro de `generar_reembolso` (definida en la línea 178).

- Traza actual:

```bash
wc -l trazas_agente.jsonl
grep -c '"herramienta": "calcular_costo_envio"' trazas_agente.jsonl
grep -c '"herramienta": "generar_reembolso"' trazas_agente.jsonl
```

Resultado real:

```text
1 trazas_agente.jsonl
1
0
```

Hay una traza de riesgo bajo (`calcular_costo_envio`) en `trazas_agente.jsonl`. La prueba de riesgo alto se hizo con otro archivo, `src/agente_supervisado.py`, y quedó en `docs/trazas_agente_supervisado.jsonl`: 5 turnos, 3 llamadas a `generar_reembolso`, 1 aprobada y 2 rechazadas.

## Limitaciones conocidas

- El programa vive en la RAM, una ve se cierra todo desaparece, es necesaria una base de datos que escriba en el disco o en la nube para tener un registro y un historial
- `generar_reembolso` no valida que el pedido exista, que el monto sea menor o igual al total del pedido ni que no se haya reembolsado antes; la aprobación humana es la única barrera.
- La aprobación se hace por consola (`input()` en un hilo) y no verifica identidad ni rol del aprobador; no sirve para un entorno remoto o multiusuario.
- `trazas_agente.jsonl` es un archivo local editable: no es un registro centralizado, inmutable ni firmado, así que puede borrarse o modificarse.
