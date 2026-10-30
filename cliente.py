import time
import random
from typing import Callable, Any

from src.consumir_deepseek import armar_peticion, extraer_textos, enviar_peticion

MODELO = "deepseek-flash"

def con_reintento(
    funcion: Callable[[], Any], 
    intentos: int = 3, 
    espera_base: float = 2, 
    espera_maxima: float = 30,) -> Any:
    
    for intento in range(1, intentos + 1):
        try:
            return funcion()
        except TimeoutError:
            if intento == intentos:
                raise
            espera = min(espera_base * (2 ** (intento - 1)), espera_maxima)
            espera_con_jitter = espera + random.uniform(0, espera * 0.1)
            print(f"Intento {intento} de {intentos} falló. Reintentando en {espera_con_jitter:.1f}s...")
            time.sleep(espera_con_jitter)


PRECIO_ENTRADA = 0.00000030  
PRECIO_SALIDA = 0.00000120
costo_total_sesion = 0.0

def registrar_costo(respuesta: dict) -> float:
    global costo_total_sesion
    uso = respuesta.get("usage", {})
    entrada = uso.get("prompt_tokens", 0)
    salida = uso.get("completion_tokens", 0)
    costo_estimado = entrada * PRECIO_ENTRADA + salida * PRECIO_SALIDA
    costo_total_sesion += costo_estimado
    print(f"Operación: {entrada} in / {salida} out, costo estimado: ${costo_estimado:.6f} (acumulado: ${costo_total_sesion:.6f})")
    return costo_estimado
 
 
def consultar_modelo(pregunta: str, system_instruction: str = "") -> str:
    url, cuerpo = armar_peticion(MODELO, pregunta, system_instruction)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(url, cuerpo))
    except TimeoutError:
        raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")
    registrar_costo(respuesta)
    return extraer_textos(respuesta)
 
 
if __name__ == "__main__":
    resultado = consultar_modelo("¿Cuál es la capital de Chile?", " ")
    print(resultado)
    
    for i in range(10):
        try:
            respuesta = consultar_modelo(f"Pregunta de prueba número {i}")
            print(f"Respuesta {i}: {respuesta[:40]}...")
        except RuntimeError as error:
            print(f"Respuesta {i} falló definitivamente: {error}")
