# Límites de la métrica de evaluación

## Qué mide

Compara las palabras de la respuesta con las de la referencia. Las dos pasan
por limpieza (minúsculas, sin puntuación, sin espacios repetidos) y se separan
en tokens; después se cuentan las coincidencias. Devuelve precisión, cobertura
y F1. En los 20 casos el F1 promedio fue 0.501.

## Modos de falla conocidos

- Las variantes de una palabra no se reconocen. Caso 9, "¿Para qué sirve def
  en Python?": la referencia dice "def define una función" y la respuesta
  "Sirve para definir funciones reutilizables con nombre y parámetros en
  Python". F1 0.000. `define` y `definir` son tokens distintos, igual que
  `función` y `funciones`.

- Los sinónimos se castigan. Caso 11, try except: la referencia habla de
  "manejar excepciones" y la respuesta de "manejar errores"; solo coincide
  `manejar`. F1 0.125. En el caso 18 pasa algo parecido: `apariciones` no
  coincide con `frecuencias`. F1 0.222.

- El guion de un compuesto se borra al limpiar. Caso 6, diccionario: la
  respuesta dice "pares clave-valor" y la referencia "claves con valores".
  Al quitar el guion queda `clavevalor`, un token que no coincide con
  ninguno de los dos. F1 0.100, con una respuesta que es correcta.

- Una respuesta correcta pero menos detallada baja el puntaje. Caso 5, print:
  la referencia habla de "una representación de los objetos en la salida de
  texto" y la respuesta de "mostrar datos o resultados en la pantalla".
  F1 0.273. El contenido es correcto, cambia el vocabulario y el nivel de
  detalle.

- Un F1 alto puede ser solo copia literal. Caso 2, año de publicación de
  Python: la respuesta es idéntica a la referencia. F1 1.000. Los casos 4 y
  10 también quedan altos porque reutilizan casi todas las palabras de la
  referencia, no porque la métrica haya comprobado el contenido.

## Muestra revisada

Revisé 10 de los 20 casos: los cinco F1 más bajos (9, 6, 11, 18, 5) y los
cinco más altos (15, 3, 4, 10, 2). Fecha: 4/11/2026.

Usé la rúbrica de corrección factual, completitud y contradicción, con una
nota por caso en `docs/revision_manual.json`.

Los 10 resultaron factualmente correctos (uno parcialmente completo) y
ninguno se contradice. Los cinco F1 más bajos, que la métrica pondría al
final de la lista, también son correctos. En esta muestra el número ordenó
por parecido de vocabulario, no por calidad.

## Recomendación de uso

- Usar el F1 para comparar prompts o versiones del modelo sobre el mismo
  conjunto de referencias, no para aprobar respuestas sueltas. Con estos
  datos, filtrar por F1 bajo habría borrado cinco respuestas correctas.

- Todo lo que quede bajo 0.3 va a revisión humana, no a la basura. Los casos
  9, 6, 11 y 18 están ahí y están bien.

- Las fechas, números y nombres se revisan a mano aunque el F1 sea alto. La
  métrica cuenta palabras: una respuesta puede repetir la referencia y tener
  el dato mal.

- Para definiciones y explicaciones, el número solo no alcanza. El modelo
  parafrasea casi siempre y esta métrica castiga la paráfrasis; haría falta
  revisión humana o comparar significado (embeddings).
