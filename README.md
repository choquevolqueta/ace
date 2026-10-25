# Mi mini aplicacion version 1.0

Hola, me llamo Alexander Cortez y este es el manual de primer uso de mi mini aplicacion. Inicialmente empece con la API de Gemini, pero debido a que tengo planeado usar la API de Deepseek por el tema de costos y disponibilidad hice este cambio de timon...
Debo decir honestamente que cuesta ya que Deepseek funciona de manera distinta a Gemini, y posee algunas limitaciones que salve con codigo, de todos modos, me alegra el resultado actual hasta ahora

## Cómo empezar

El paso mas importante es descargar el repositorio desde el github ya sea como zip o usando el comando
-git clone https://github.com/choquevolqueta/ace.git

### Requisitos:
Python 3.11 o superior(probado en 3.11.)
Una API key de Deepseek

### Instalacion:
 Ejecutar en una terminal bash

 python -m venv venv
 venv\ Scripts\activate
 pip install -r requirements.txt

 ### Configuracion:
Copia `.env.example` a un archivo nuevo llamado `.env`, y completa ahí tus credenciales reales (llaves de API, tokens). El archivo `.env` nunca se sube al repositorio: ya está excluido en `.gitignore`.

## Estructura de carpetas

- `src/` : todo el código fuente de tu proyecto va aquí.
- `docs/` : documentación técnica del proyecto (diagramas, decisiones de arquitectura, notas).
- `tests/` : pruebas de tu código (las vas a usar más adelante en el programa, cuando el proyecto lo requiera).
- `requirements.txt` : dependencias de Python de tu proyecto, para que cualquier otra persona pueda reconstruir tu entorno con un solo comando.
- `.env.example` : plantilla de las variables de entorno que tu proyecto necesita, sin valores reales. Tu archivo `.env` real (con tus credenciales) nunca se commitea.
- `.gitignore` : le dice a Git qué archivos y carpetas ignorar (entre ellos, tu entorno virtual y tu archivo `.env`).

## Reglas que se mantienen durante todo el programa

- Ningún secreto (contraseña, llave de API, token) va escrito directamente en el código ni en ningún archivo que se suba al repositorio.
- Cada proyecto nuevo tiene su propio entorno virtual: no se comparten dependencias entre proyectos distintos.
- Todo el trabajo que se entrega en este programa vive en un repositorio de GitHub, sin excepción.

## Registro del ensayo de instalacion limpia

- Fecha: 2026-10-25

Se inicio todo el procedimiento mostrado en la plataforma para la prueba de uso limpio desde cero. Siguiendo los pasos al pie de la letra y agregando la API key de Deepseek se puede dar fe que el programa test_consistencia.py el ultimo en ser desarrollado funciona sin problemas y de manera correcta.