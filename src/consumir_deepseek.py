import os
import requests
from dotenv import load_dotenv
import time
import json
import re

load_dotenv()

API_KEY= os.getenv("DEEPSEEK_API_KEY")
MODELO= "deepseek-flash"
URL_BASE= "https://api.deepseek.com/chat/completions"

def armar_peticion(modelo, pregunta, system_instruction, response_JSON= None):
    if not pregunta:
        raise ValueError("La pregunta no puede estar vacía.")

    if response_JSON is not None:
        system_instruction += "\nResponde unicamente con JSON valido que cumpla este esquema: " + json.dumps(response_JSON, ensure_ascii=False)

    url= URL_BASE
    body= {
        "model": modelo,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": pregunta}
        ],
        "stream": False
    }
    if response_JSON is not None:
        body["response_format"] = {"type": "json_object"}
        body["max_tokens"] = 1000
        body["thinking"] = {"type": "disabled"}
    return url, body

def enviar_peticion(url, body):
    headers= {"Authorization": f"Bearer {API_KEY}"}
    try:
        respuesta= requests.post(url, json=body, headers=headers, timeout= 60)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Error de conexión. No se pudo establecer la conexión con el servidor.")    
    except requests.exceptions.Timeout:
        raise RuntimeError("Tiempo de espera agotado. La solicitud tardó demasiado en completarse.")

    if respuesta.status_code in(401, 403):
        raise RuntimeError(f"Error de autenticación: {respuesta.status_code} - Verifica tu API Key.")

    if respuesta.status_code >= 500:
        raise RuntimeError("Error del servidor. Intenta nuevamente más tarde.")
    
    if respuesta.status_code == 429:
        raise TimeoutError("Limite excedido: demasiadas peticiones concurrentes. Intenta de nuevo en unos segundos.")

    
    if respuesta.status_code != 200:
        raise RuntimeError(f"Error en la solicitud: {respuesta.status_code} - {respuesta.text}")    
        
    try:    
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("Error al decodificar la respuesta JSON.")
    
def extraer_textos(datos):
    try:
        return datos["choices"][0]["message"]["content"]
    
    except (KeyError, IndexError):
        raise RuntimeError("No se pudo extraer el texto de la respuesta.")

def parsear_respuesta_json(texto, claves_requeridas= None):
    texto_limpio= texto.strip()
    texto_limpio= re. sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio= re. sub(r"\s*```$", "", texto_limpio)
    try:
        datos= json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es JSON valido")
    if claves_requeridas:
        faltantes= [clave for clave in claves_requeridas if clave not in datos]
        if faltantes:
            raise ValueError(f"Faltan claves requeridas en la respuesta JSON: {faltantes}")
    return datos

def obtener_dato_de_prueba(modelo, pregunta, system_instruction, response_JSON= None):
    url, body= armar_peticion(modelo, pregunta, system_instruction, response_JSON)

    inicio= time.perf_counter()

    datos= enviar_peticion(url, body)

    fin= time.perf_counter()
    latencia= fin - inicio

    print(f"latencia: {latencia:.2f} segundos")
    costo= calcular_costo(datos, 0.0000003, 0.00000120)
    print(f"Costo de la operación: ${costo:.6f} USD")

    texto= extraer_textos(datos)
    if response_JSON is None:
        return texto

    return parsear_respuesta_json(texto, response_JSON.get("required"))

def calcular_costo(datos, precio_entrada, precio_salida):
    uso= datos["usage"]
    tokens_entrada= uso["prompt_tokens"]
    tokens_salida= uso["completion_tokens"]
    costo= (tokens_entrada * precio_entrada) + (tokens_salida * precio_salida)
    return costo

#def main():
#   try:
#        print(obtener_dato_de_prueba("deepseek-flash", "¿donde esta ubicada la plaza murillo?", "Eres un asistente amigable y respondes en maximo 5 palabras"))
#
#    except (ValueError, RuntimeError) as error:
#        print(f"No se pudo completar la operación: {error}")
def main():
    try:
        response_JSON= {
            "type": "object",
            "properties": {
                "ciudad": {"type": "string"},
                "pais": {"type": "string"},
                "resumen": {"type": "string"}
            },
            "required": ["ciudad", "pais", "resumen"]
        }

        resultado= obtener_dato_de_prueba(
            MODELO,
            "¿donde esta ubicada la plaza murillo?",
            "Eres un asistente preciso.",
            response_JSON
        )

        print(json.dumps(resultado, ensure_ascii=False, indent=2))

    except (ValueError, RuntimeError, TimeoutError) as error:
        print(f"No se pudo completar la operación: {error}")

if __name__ == "__main__":
    main()
