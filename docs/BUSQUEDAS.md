# Buscar alumnado y organizar grupos

## Alumnado

En **Alumnado**, escribe parte del nombre, apellidos o nombre preferido. Pulsa
**Buscar y filtrar** o Intro desde el cuadro. Se ignoran mayúsculas, tildes y orden
de las palabras: «lopez angela» encuentra «Ángela López». No se busca en contactos,
responsables, información restringida ni notas educativas.

Puedes combinar el texto con **Grupo con matrícula abierta** y **Estado del alumno**.
El filtro de grupo incluye matrículas sin fecha de fin, no matrículas finalizadas;
no sustituye la consulta de alumnado vigente en una fecha concreta de sesión.
Cada persona aparece una vez aunque tenga varias matrículas. El contador indica
los resultados de la búsqueda, no un recuento global de alumnado ajeno.

## Grupos

El texto busca en nombre, ubicación y horario informativo. Se puede combinar con
**Tipo de clase**, **Curso académico**, **Ubicación** y **Estado del grupo**.
**Ordenar por** permite nombre, ubicación, tipo o fecha de inicio. El orden de nombres
usa el orden de la base de datos; no interpreta los días de la semana ni el texto del
horario como recurrencias.

Todos los filtros se combinan. Si no hay coincidencias, prueba filtros más amplios
o pulsa **Limpiar filtros**. No se elimina ni modifica ningún registro por buscar,
ordenar o limpiar. Los campos mantienen sus valores después de buscar. Los filtros
no se guardan como preferencias personales ni se trasladan a otras pantallas.

## Acceso y privacidad

Resultados y opciones de grupos, cursos y ubicaciones parten siempre del ámbito
permitido al usuario. No se puede ampliar ese ámbito manipulando un identificador;
una opción inválida muestra error sin resultados. Desarrollo por sí solo no da
acceso educativo. Las respuestas son privadas y sin caché.

Los formularios usan POST con CSRF para no poner nombres de alumnos en el enlace
de búsqueda. Se conserva compatibilidad con los enlaces GET antiguos, pero conviene
usar el formulario y no compartir URLs con nombres. No registrar cuerpos de búsqueda
en proxies o herramientas de diagnóstico. No se consultan servicios externos ni
se añade almacenamiento de datos en el navegador.

La coincidencia Unicode se realiza en memoria sobre los campos permitidos del
conjunto ya autorizado, adecuada para el tamaño del piloto. Para un crecimiento
sustancial, añadir índices/búsqueda normalizada en base de datos y paginación sin
relajar permisos. Este cambio no requiere migración ni dependencias nuevas.

## Módulos

- `core/list_filters.py`: formularios, opciones por ámbito y coincidencia de texto.
- `core/views/students.py:student_list` y `core/views/groups.py:group_list`: combinación de criterios.
- `templates/core/list_filters.html`: controles etiquetados y contador de resultados.
- `static/core/operations.css`: distribución adaptable a tablet y móvil.
- `core/test_list_filters.py`: búsqueda, permisos, filtros combinados, entrada inválida y privacidad.

## Sugerencias y filtros plegables (0.8.3)

Desde **dos caracteres** se solicitan hasta **8 sugerencias** privadas. En alumnado
son nombres completos (también se puede encontrar por nombre preferido); en grupos,
nombres de grupo que coincidan con el texto buscado en nombre, ubicación u horario.
Se aplican los mismos filtros y permisos que en la lista. No se descargan todos los
nombres para incluirlos en JavaScript ni se guardan consultas en el navegador.

Pulsa una sugerencia para rellenar la barra y después **Buscar y filtrar** o Intro.
Con teclado: flechas arriba/abajo recorren las sugerencias, Intro selecciona la
resaltada y Escape cierra sin borrar el texto. Tab continúa la navegación normal.
Los nombres iguales siguen siendo posibles: revisa las fichas, no presupongas que
un nombre identifica de forma única a una persona.

El botón **×** borra únicamente lo escrito y devuelve el foco al buscador. Conserva
los demás filtros; para aplicar la búsqueda vacía pulsa Buscar y filtrar. **Limpiar
filtros** reinicia toda la búsqueda. El panel de filtros empieza plegado; se puede
abrir con su título. Se muestra abierto con contador si hay filtros adicionales
activos, o si hay errores que corregir. La ordenación también está dentro del
panel de Grupos. Cambiar el texto por sí solo no modifica los resultados de la
lista hasta que se envía la búsqueda.

Las solicitudes de sugerencias son POST con CSRF, autenticación, mínimo de dos
caracteres, máximo de 150, respuesta sin caché y límite de 8 resultados. Hay una
espera de 200 ms al escribir; las peticiones obsoletas se cancelan y sus respuestas
no sustituyen a las actuales. Un error de conexión muestra una ayuda y permite
seguir usando el botón de búsqueda. Sin JavaScript funcionan la búsqueda y el
panel nativo de filtros, con el borrado nativo que ofrezca el navegador.

Módulos añadidos: `core/views/suggestions.py` y `static/core/list_search.js`.
La consulta por ámbito/filtros se comparte en `core/list_filters.py`, para evitar
diferencias de permisos entre sugerencias y listados. No hay migración ni
paquetes nuevos.
