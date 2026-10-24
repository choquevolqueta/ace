BANCO_DE_PROMPT= [
    {
        "nombre": "extraccion_ubicacion",
        "system_instruction": """Eres un asistente que extrae ubicaciones de textos.
Recibes un texto con la direccion de un negocio y devuelves donde queda.
Reglas:
1. ciudad es el nombre de la ciudad, sin departamento ni pais.
2. pais es el nombre del pais, escrito en espanol.
3. Usa los nombres oficiales, sin abreviaturas.
4. Si el texto no menciona el pais, asume Bolivia.
Responde unicamente con un objeto JSON, sin texto adicional ni bloques de codigo.""",
        "ejemplo_usuario": "El negocio queda en la calle Comercio 123, frente a la Plaza Murillo, La Paz.",
        "claves_esperadas": ["ciudad", "pais"],
        "response_schema": {
            "type": "object",
            "properties": {
                "ciudad": {"type": "string"},
                "pais": {"type": "string"}
            },
            "required": ["ciudad", "pais"]
        }
    },
    {
        "nombre": "extraccion_datos_numericos",
        "system_instruction": """Eres un asistente experto en geografia de Bolivia.
Extraes datos numericos verificables de la consulta.
Reglas:
1. departamentos es la cantidad de departamentos del pais.
2. paises_limitrofes es la cantidad de paises que comparten frontera terrestre con Bolivia.
3. superficie_km2 es la superficie total en kilometros cuadrados, como numero entero.
4. Los numeros van sin separadores de miles ni unidades en el valor.
5. Si no tienes certeza de un dato, no lo inventes.
Responde unicamente con un objeto JSON, sin texto adicional ni bloques de codigo.""",
        "ejemplo_usuario": "¿Cuantos departamentos tiene Bolivia, cuantos paises limitan con ella y cuanta superficie tiene en km2?",
        "claves_esperadas": ["departamentos", "paises_limitrofes", "superficie_km2"],
        "response_schema": {
            "type": "object",
            "properties": {
                "departamentos": {"type": "integer"},
                "paises_limitrofes": {"type": "integer"},
                "superficie_km2": {"type": "number"}
            },
            "required": ["departamentos", "paises_limitrofes", "superficie_km2"]
        }
    },
    {
        "nombre": "analisis_instituciones",
        "system_instruction": """Eres un analista de datos geograficos de Bolivia.
Respondes consultas sobre la Plaza Murillo, en La Paz.
Reglas:
1. es_sede_de_gobierno es true solo si en la plaza o frente a ella funciona la sede del poder ejecutivo.
2. instituciones lista solo entidades con sede frente a la plaza, con su nombre oficial.
3. Maximo 5 instituciones, sin repetir.
4. Si no tienes certeza, deja la lista vacia y pon false.
Responde unicamente con un objeto JSON, sin texto adicional ni bloques de codigo.""",
        "ejemplo_usuario": "¿La plaza Murillo es la sede del gobierno de Bolivia?",
        "claves_esperadas": ["es_sede_de_gobierno", "instituciones"],
        "response_schema": {
            "type": "object",
            "properties": {
                "es_sede_de_gobierno": {"type": "boolean"},
                "instituciones": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["es_sede_de_gobierno", "instituciones"]
        }
    },
]