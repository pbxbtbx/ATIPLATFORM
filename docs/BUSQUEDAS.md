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
