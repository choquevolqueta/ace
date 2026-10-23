# Decision de arquitectura: eleccion de modelo

Estado: aceptada. Fecha: 23 de octubre de 2026.

## Modelo elegido

`deepseek-flash`, a traves de `https://api.deepseek.com/chat/completions` con autenticacion `Bearer`.

## Diagrama de arquitectura

```
pregunta → evaluacion_modelos.py → consumir_deepseek.py → POST /chat/completions
        → API DeepSeek → choices + usage → respuesta y costo
```

El diagrama general del sistema esta en `docs/diagrama de arquitectura.drawio.png`.

## Comparacion de candidatos

Probe los dos modelos con la misma pregunta y el mismo cuerpo de peticion, cuatro veces cada uno. La salida completa esta en `docs/evaluacion comparativa de apis.txt`.

| | deepseek-flash | deepseek-v4-pro |
|---|---|---|
| Latencia promedio | 3.47 s | 9.37 s |
| Rango de latencia | 3.03 - 4.04 s | 6.96 - 12.82 s |
| Costo de las 4 llamadas | $0.000703 | $0.003392 |
| Costo promedio por llamada | $0.000176 | $0.000848 |
| Precio entrada / salida (1M tokens, peak) | $0.30 / $1.20 | $1.32 / $3.96 |
| Calidad de la respuesta | correcta | correcta |

Flash respondio en 3.47 s promedio y pro en 9.37 s. Las cuatro llamadas a flash costaron $0.000703; las de pro, $0.003392. Pro sale 2.7 veces mas lento y 4.8 veces mas caro.

## Justificacion

Las dos respuestas fueron correctas. En una pregunta factual no encontre diferencia de calidad, asi que no hay motivo para pagar casi cinco veces mas.

El costo crece mas rapido que la latencia. Pro duplica el tiempo de respuesta pero multiplica el gasto por 4.8.

Flash tambien se comporta de forma mas estable. Su latencia quedo entre 3.03 y 4.04 s, mientras que pro salto de 6.96 a 12.82 s y su costo por repeticion vario hasta 2.7 veces. Para fijar timeouts y presupuesto, la previsibilidad pesa mas que un pico de calidad que aqui no aparecio.

## Alternativa descartada y por que

Descarte `deepseek-v4-pro`. Cuesta 4.8 veces mas, tarda 2.7 veces mas y respondio igual de bien que flash.

Cambiaria de modelo si el proyecto pasa a tareas de razonamiento largo, analisis de documentos extensos o generacion que dependa de mas profundidad. Tambien si la latencia deja de importar y el presupuesto se vuelve la unica restriccion. En ese caso repetiria esta misma prueba.

## Notas sobre la medicion

Cuatro repeticiones por modelo y una sola pregunta. La primera llamada de cada modelo carga el arranque, y en pro se nota: 10.18 s y $0.001612 frente a 6.96 s y $0.000587 de la segunda.

Use tarifas peak. De noche cuestan la mitad y la comparacion no cambia.

DeepSeek guarda en cache la entrada cuando repites el mismo prompt, pero `calcular_costo` la cobra completa. Los dos modelos quedan sobreestimados por igual.
