import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY= os.getenv("GEMINI_API_KEY")
MODELO= "gemini-3.6-flash"
URL_BASE= "https://generativelanguage.googleapis.com/v1beta/models/"

def armar_peticion(pregunta):
    
    url= f"{URL_BASE}{MODELO}:generateContent?key={API_KEY}"
    body= {
        "contents": [
        {
            "parts": [{"text": pregunta}]}]
    }
    return url, body

def enviar_peticion(url, body):
    try:
        respuesta= requests.post(url, json=body, timeout= 30)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Error de conexión. No se pudo establecer la conexión con el servidor.")    
    except requests.exceptions.Timeout:
        raise RuntimeError("Tiempo de espera agotado. La solicitud tardó demasiado en completarse.")

    if respuesta.status_code != 200:
        raise RuntimeError(f"Error en la solicitud: {respuesta.status_code}")    
        
    try:    
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("Error al decodificar la respuesta JSON.")
    
def extraer_textos(datos):
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    
    except (KeyError, IndexError):
        raise RuntimeError("No se pudo extraer el texto de la respuesta.")

def obtener_dato_de_prueba(pregunta):
    url, body= armar_peticion(pregunta)
    datos= enviar_peticion(url, body)
    costo= calcular_costo(datos, 0.00000075, 0.00000375)
    print(f"Costo de la operación: ${costo:.6f} USD")
    return extraer_textos(datos)

def calcular_costo(datos, precio_entrada, precio_salida):
    uso= datos["usageMetadata"]
    tokens_entrada= uso["promptTokenCount"]
    tokens_salida= uso["candidatesTokenCount"]
    tokens_razonamiento= uso["thoughtsTokenCount"]
    costo= (tokens_entrada * precio_entrada) + ((tokens_salida + tokens_razonamiento) * precio_salida)
    return costo

try:
    print(obtener_dato_de_prueba("¿hazme un resumen de bukarin y su concepto de materialismo historico?"))


except (ValueError, RuntimeError) as error:
    print(f"No se pudo completar la operación: {error}")