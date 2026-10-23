import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()

API_KEY= os.getenv("DEEPSEEK_API_KEY")
MODELO= "deepseek-flash"
URL_BASE= "https://api.deepseek.com/chat/completions"

def armar_peticion(pregunta, modelo):
    
    url= URL_BASE
    body= {
        "model": modelo,
        "messages": [
            {"role": "user", "content": pregunta}
        ],
        "stream": False
    }
    return url, body

def enviar_peticion(url, body):
    headers= {"Authorization": f"Bearer {API_KEY}"}
    try:
        respuesta= requests.post(url, json=body, headers=headers, timeout= 60)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Error de conexión. No se pudo establecer la conexión con el servidor.")    
    except requests.exceptions.Timeout:
        raise RuntimeError("Tiempo de espera agotado. La solicitud tardó demasiado en completarse.")

    if respuesta.status_code != 200:
        raise RuntimeError(f"Error en la solicitud: {respuesta.status_code}{respuesta.text}")    
        
    try:    
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("Error al decodificar la respuesta JSON.")
    
def extraer_textos(datos):
    try:
        return datos["choices"][0]["message"]["content"]
    
    except (KeyError, IndexError):
        raise RuntimeError("No se pudo extraer el texto de la respuesta.")

def obtener_dato_de_prueba(pregunta, modelo):
    url, body= armar_peticion(pregunta, modelo)
    
    inicio= time.perf_counter()

    datos= enviar_peticion(url, body)
    
    fin= time.perf_counter()
    latencia= fin - inicio

    print(f"latencia: {latencia:.2f} segundos")
    costo= calcular_costo(datos, 0.0000003, 0.00000120)
    print(f"Costo de la operación: ${costo:.6f} USD")
    return extraer_textos(datos)

def calcular_costo(datos, precio_entrada, precio_salida):
    uso= datos["usage"]
    tokens_entrada= uso["prompt_tokens"]
    tokens_salida= uso["completion_tokens"]
    costo= (tokens_entrada * precio_entrada) + (tokens_salida * precio_salida)
    return costo

def main():
    try:
        print(obtener_dato_de_prueba("¿donde esta ubicada la plaza murillo?", MODELO))

    except (ValueError, RuntimeError) as error:
        print(f"No se pudo completar la operación: {error}")

if __name__ == "__main__":
    main()
