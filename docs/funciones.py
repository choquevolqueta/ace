#El nombre de la estudiante
#La calificación del curso
#El titulo de la segunda tarea
#Si la primera tarea está completada
estudiante = {
    "nombre": "Ana",
    "edad": 24,
    "curso": {
        "nombre": "Python",
        "calificacion": 92
    },
    "tareas": [
        {
            "titulo": "Variables",
            "completada": True
        },
        {
            "titulo": "Consumo de APIs",
            "completada": False
        }
    ]
}
def main():

    print(estudiante["nombre"])
    print(estudiante["curso"]["calificacion"])
    print(estudiante["tareas"][1]["titulo"])
    print(estudiante["tareas"][0]["completada"])

if __name__ == "__main__":
    main()