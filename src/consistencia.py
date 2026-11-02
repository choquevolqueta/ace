import json
import time
from pathlib import Path
from prompts.banco import BANCO_DE_PROMPT
from consumir_deepseek import armar_peticion, enviar_peticion, extraer_textos, parsear_respuesta_json

registro= {}

try:
    for prompt in BANCO_DE_PROMPT:
        exitos= 0
        intentos= 3

        for intento in range(intentos):
            url, body= armar_peticion(
                "deepseek-flash",
                prompt["ejemplo_usuario"],
                prompt["system_instruction"],
                prompt["response_schema"]
            )
            respuesta= enviar_peticion(url, body)
            texto= extraer_textos(respuesta)

            try:
                parsear_respuesta_json(texto, prompt["claves_esperadas"])
                exitos += 1
            except ValueError as error:
                print(f" intento{intento + 1} fallo: {error}")

            time.sleep(1)

        print(f"Prompt: {prompt['nombre']}, exitos: {exitos}/{intentos}")
        registro[prompt["nombre"]]= {"exitos": exitos, "intentos": intentos}

    ruta= Path(__file__).parent / "prompts" / "registro_resultados.json"

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, ensure_ascii=False, indent=2)

except (ValueError, RuntimeError) as error:
    print(f"No se pudo completar la operación: {error}" )
