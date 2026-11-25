from datetime import date
from rag_indexer import cargar_vectorstore


def precision_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float:
    """
    ids_recuperados los que me trajo el retriever
    De los 'k' chunks que me trajo el retriever, ¿qué fracción realmente sirve?
    Devuelve 0.0 si el retriever no devolvió ningún id
    """
    if not ids_recuperados:
        return 0.0
    
    #Recorro uno por uno cada ID que devolvió el retriever, si acaso existe en ids_relevantes lo agrego a la lista de acertados
    acertados = [i for i in ids_recuperados if i in ids_relevantes] 

    return len(acertados) / len(ids_recuperados)

def recall_at_k(ids_recuperados: list[str], ids_relevantes: set[str]) -> float | None:
    """
    Exhaustividad
    De todos los chunks relevantes que existen en mi corpus, ¿qué fracción logré rescatar?
    Devuelve None si la pregunta no tiene respuesta en corpus (ids_relevantes es vacío)
    """
    if not ids_relevantes:
        return None
    
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_relevantes)

def f1_score(precision: float, recall: float | None) -> float:
    """
    Media armónica entre precisión y exhaustividad: equilibrio entre ambos para comparar
    configuraciones distintas de k o chunk_size.
    """
    if recall is None or (precision + recall) == 0:
        return 0.0
    
    return 2 * precision * recall / (precision + recall)

def evaluar_recuperacion(retriever, casos: list[dict], k: int = 3):
    """
    Correr cada caso del conjunto de evaluaciones contra el retriever real de Chroma
    y va a calcular precisión, recall y F1
    """
    resultados = []

    for caso in casos:
        #1.- Consultamos al retriever, cuáles son los chunks que me regresa la invocación. SI GASTA TOKENS
        chunks = retriever.invoke(caso["pregunta"])

        #2.- Extraer los IDs
        ids_recuperados = [c.id for c in chunks]

        #3.- Calculamos las métricas
        p = precision_at_k(ids_recuperados, caso["ids_relevantes"])
        r = recall_at_k(ids_recuperados, caso["ids_relevantes"])
        f1 = f1_score(p, r)

        #4.- Agregar esas métricas a los resultados
        resultados.append({
            "pregunta": caso["pregunta"],
            "ids_recuperados": ids_recuperados,
            "precision": p,
            "recall": r,
            "f1": f1
        })
    
    return resultados

def guardar_reporte(ruta_archivo: str, resultados: list[dict], k: int, chunk_size: int = 200, chunk_overlap: int = 30):
    """Guarda el registro en un .txt para compararlo cuando cambies k o chunk_size."""
    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        archivo.write(f"Fecha: {date.today()}\n")
        archivo.write(f"Configuracion: k={k}, chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n\n")

        for r in resultados:
            recall_txt = "n/a" if r["recall"] is None else f"{r['recall']:.2f}"
            archivo.write(f"P={r['precision']:.2f} | R={recall_txt} | F1={r['f1']:.2f} | {r['pregunta']}\n")
    print(f"\nReporte guardado en '{ruta_archivo}'")

if __name__ == "__main__":
    CARPETA_DB = "vectorstore_ejemplo"
    K = 4
    vs = cargar_vectorstore(CARPETA_DB)

    pregunta = "Cuáles son los errores de credenciales inválidas?"
    ids_relevantes = {
        "2977f39e-7bbd-47f9-a97b-e8661a8f69c6", # Indica que 401/403 no reintentan y fallan de inmediato
        "434dd9e8-5713-43d2-97d1-b1c6a9c2e551", # Indica que arroja AuthenticationError
        "499be197-1f9e-4c4e-b0c2-ef46037316d5", # Solución: revisar API_KEY y vigencia de 24h
    }

    retriever = vs.as_retriever(search_kwargs={"k": K})
    chunks = retriever.invoke(pregunta) #Consulta
    print(chunks)
    ids_recuperados = [c.id for c in chunks]

    precision = precision_at_k(ids_recuperados, ids_relevantes)
    print("Precision: ", precision)

    exhaustividad = recall_at_k(ids_recuperados, ids_relevantes)
    print("Exhaustividad: ", exhaustividad)

    f1 = f1_score(precision, exhaustividad)
    print("F1 Score: ", f1)

    casos_evaluacion = [
        # Caso 1: Cubre la Sección 1 del manual (Política de Reintentos ante TimeoutError)
        {
            "pregunta": "¿Cuántos intentos hace el cliente ante un TimeoutError y cuánto espera entre cada uno?",
            "ids_relevantes": {
                "94277f25-c78b-4dfe-8962-83c168104bdb", # Explica TimeoutError y códigos 502, 503, 504
                "008319c9-060c-4458-bada-6c4a86e829b2", # Indica el máximo de 3 intentos y espera exponencial
                "c39d2eb6-0008-49cc-9f22-6ea3700f47bf", # Detalla los segundos (2s, 4s, 8s)
            }
        },
        # Caso 2: Cubre la Sección 2 del manual (Errores de Autenticación y cómo resolverlos)
        {
            "pregunta": "¿Qué ocurre cuando hay un error 401 o 403 de credenciales inválidas y cómo se soluciona?",
            "ids_relevantes": {
                "2977f39e-7bbd-47f9-a97b-e8661a8f69c6", # Indica que 401/403 no reintentan y fallan de inmediato
                "434dd9e8-5713-43d2-97d1-b1c6a9c2e551", # Indica que arroja AuthenticationError
                "499be197-1f9e-4c4e-b0c2-ef46037316d5", # Solución: revisar API_KEY y vigencia de 24h
            }
        },
        # Caso 3: Cubre la Sección 3 del manual (Límites de Tasa / Rate Limiting 429)
        {
            "pregunta": "¿Cuál es el límite de peticiones por minuto y qué pasa si se excede?",
            "ids_relevantes": {
                "dd40aaae-8ab0-4f6c-959a-f70fad8dc352", # Máximo 60 peticiones por minuto por clave
                "8eb158fe-932a-4ceb-bccf-4c27bb5a550b", # El servidor responde con HTTP 429 Too Many Requests
                "84eed674-57e1-4355-87ac-c2245fec62ef", # La cabecera Retry-After indica los segundos de pausa
            }
        },
        # Caso 4: Cubre la Sección 4 del manual (Control de Costos y Créditos de Sesión)
        {
            "pregunta": "¿Cuántas unidades de crédito consumen las consultas de lectura y las de escritura?",
            "ids_relevantes": {
                "34d03333-e61f-49e8-aff4-4d1f40052fa0", # Solo lectura: 1 unidad por cada 100 registros
                "ca9789ce-cbdf-40c0-8a14-1fc9630c16e9", # Escritura y actualización: 5 unidades por transacción
            }
        },
    ]

    resultados = evaluar_recuperacion(retriever, casos_evaluacion, 4)
    print(resultados)

    guardar_reporte("resultados_evaluacion_rag.txt", resultados, 4)

    """
    Precisión: Fórmula: Verdaderos Positivos / (Verdaderos Positivos + Falsos Positivos) 

    Exhaustividad (recall ) :
    Fórmula: Verdaderos Positivos / (Verdaderos Positivos + Falsos Negativos)
    """
