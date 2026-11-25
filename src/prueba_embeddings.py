# Prueba de embeddings + Chroma.
# Adaptación mínima: embeddings locales con FastEmbed.
# DeepSeek no provee embeddings, así que se usa un modelo local.
# El resto de la estructura es la misma que la de la profesora.

from dotenv import load_dotenv
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_chroma import Chroma  # Importación de Chroma

load_dotenv()

embedding = FastEmbedEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

try:
    vector = embedding.embed_query("Hola, cómo estás?")
    vector2 = embedding.embed_query("Qué tal, cómo va todo?")
except Exception as error:
    mensaje = str(error)
    if "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje:
        print("Límite de peticiones alcanzado.")
    else:
        print("No se pudo generar el embedding:", mensaje)

# print("Dimensión: ", len(vector))
print("Primeros valores: ", vector)
print("*****")
# print("Dimensión: ", len(vector2))
# print("Primeros valores: ", vector2[:5])

# Inicializando el vector store
vector_store = Chroma(
    collection_name="ejemplo_rag",  # Si no coloco collection_name, LangChain usa una por defecto
    embedding_function=embedding,
    persist_directory="./chroma_db"
)

# Agrega un fragmento de texto (chunk) al vector_store
# vector_store.add_texts(["RAG significa Retrieval-Augmented Generation"])

# TODO: Agregar un documento completo

datos = vector_store.get()  # Obtengo mi colección completa
print("IDs almacenados: ", datos["ids"])
print("Textos guardados: ", datos["documents"])

# Consulta / búsqueda
consulta = "¿Qué ocurre si mi red falla?"
documentos_recuperados = vector_store.similarity_search(consulta, k=2)

for doc in documentos_recuperados:
    print("Contenido encontrado: ", doc.page_content)
