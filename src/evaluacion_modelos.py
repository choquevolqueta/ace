import time
import consumir_deepseek

def evaluar_modelo(nombre_modelo, pregunta, precio_entrada, precio_salida, repeticiones= 4):
    print("=" * 70)
    print(f"Evaluando modelo: {nombre_modelo}")
    print("=" * 70)

    latencias= []  
    costos= []

    for i in range(1, repeticiones + 1):
        print(f"\nrepeticion {i} de {repeticiones} {nombre_modelo}---")

        url, body= consumir_deepseek.armar_peticion(pregunta, nombre_modelo)

        inicio= time.perf_counter()
        datos= consumir_deepseek.enviar_peticion(url, body)
        fin= time.perf_counter()

        latencia= fin - inicio
        latencias.append(latencia)

        costo= consumir_deepseek.calcular_costo(datos, precio_entrada, precio_salida)
        costos.append(costo)

        respuesta= consumir_deepseek.extraer_textos(datos)

        print(f"latencia: {latencia:.2f} segundos")
        print(f"Costo de la operación: ${costo:.6f} USD")
        print(f"Respuesta: {respuesta}")

    latencia_promedio= sum(latencias) / len(latencias)
    costo_total= sum(costos)

    print("\n" + "-" * 70)
    print(f"resumen {nombre_modelo}:")
    print(f"Latencia promedio: {latencia_promedio:.2f} segundos")
    print(f"Costo total de las operaciones: ${costo_total:.6f} USD")
    print("-" * 70 + "\n")

pregunta_prueba= "¿donde esta ubicada la plaza murillo?"

modelos= [
    {"nombre": "deepseek-flash", "precio_entrada": 0.00000030, "precio_salida": 0.00000120},
    {"nombre": "deepseek-v4-pro", "precio_entrada": 0.000000132, "precio_salida": 0.00000396},
]

for config in modelos:
    evaluar_modelo(
    nombre_modelo= config["nombre"], 
    pregunta= pregunta_prueba,
    precio_entrada= config["precio_entrada"], 
    precio_salida= config["precio_salida"],
    repeticiones= 4
    )
