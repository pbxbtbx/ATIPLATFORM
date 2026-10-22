# Retos, adaptaciones y prueba de una clase · 0.5.0

## Retos estructurados

La sesión muestra primero **Materiales y preparación** y **Objetivos**, después **Atención a la diversidad**, el **Mapa de retos** y el desarrollo de la clase. Cada tarjeta tiene identificador, consigna, pista docente desplegable y qué observar.

Las fichas Word nuevas extraen la estructura automáticamente cuando reconocen el formato. Las sesiones importadas anteriormente se muestran con tarjetas a partir de su copia de texto, sin reimportar ni borrar la planificación. El texto original sigue disponible en un desplegable.

**Organizar retos** permite revisar consignas, pistas y criterios, y añadir bloques vacíos. Se admiten hasta 30 retos. Una vez registrado seguimiento, la estructura se fija para conservar la interpretación histórica; prepara otra sesión para una versión diferente. La edición comprueba la versión y no pisa cambios concurrentes.

En cada alumno, abre su fila y marca sus **Retos alcanzados en esta sesión**. Registra una evidencia u observación cuando resulte útil. El contador y color se previsualizan al marcar casillas; solo quedan guardados al pulsar **Guardar borrador** o **Guardar y cerrar sesión**.

Para ocho retos y paleta RPG:

| Retos alcanzados | Color |
| --- | --- |
| 0–1 | Gris |
| 2–3 | Verde |
| 4–5 | Azul |
| 6–7 | Lila |
| 8 | Naranja · Legendario |

Para otra cantidad se calculan umbrales del 25 %, 50 % y 75 %, redondeando hacia arriba; todos los retos dan naranja. El resultado es individual y propio de esa sesión, sin clasificaciones públicas. La paleta Básicos conserva su presentación simplificada en gris, azul y verde, sin el subtítulo Legendario.

Completar retos es progreso de actividad. No cambia automáticamente el estado de **Aprendizaje demostrado**, las rúbricas ni el curso. Las revisiones conservan casillas, consignas, autor, fecha y observación anteriores. Se pueden consultar en **Alumnado → Aprendizaje → Historial de retos alcanzados**. No se copian observaciones privadas entre alumnos.

## Atención a la diversidad y adaptación individual

**Atención a la diversidad** en la planificación contiene orientaciones generales para esa clase, sin diagnósticos ni información personal. El apartado **Adaptaciones aplicadas** al registrar la ejecución conserva su finalidad: documentar lo que se utilizó realmente.

Para registrar apoyos individuales:

1. Accede a la ficha del alumno y a **Información restringida**.
2. Pulsa **Registrar o revisar adaptación**.
3. Indica si requiere adaptación y el tipo: metodológica, de acceso, curricular o combinada.
4. Marca **NEAE comunicada por una fuente identificada** únicamente si esa información ha sido comunicada. La aplicación no la infiere del rendimiento, asistencia o impresión del docente.
5. Diferencia hecho comunicado, observación docente e interpretación por contrastar. Una NEAE comunicada solo puede registrarse como hecho comunicado.
6. Completa fuente, relevancia/finalidad, apoyos acordados y fecha de revisión. No es necesario introducir detalles clínicos ni una etiqueta diagnóstica.
7. Guarda. Se genera una revisión nueva, sin sobrescribir la anterior.

El permiso existente de **información restringida** es obligatorio, además del acceso al alumno y al grupo. No basta Administración, Docente, Coordinación ni Desarrollo. En modo clase, solo quien tenga ese permiso verá la adaptación activa y los apoyos. El resto no recibe la marca ni sus datos en el HTML. Las lecturas y modificaciones quedan auditadas por identificador, sin copiar el contenido a la auditoría. Las páginas de sesión y ficha no se almacenan en caché.

Para finalizar una adaptación, abre el mismo formulario y desmarca **Requiere adaptación educativa**. La nueva revisión será la vigente y la anterior quedará en el historial restringido. Los informes familiares y exportaciones educativas no añaden estas marcas ni planes automáticamente. La exportación administrativa solo los incluye al seleccionar expresamente la información restringida y comprobar el permiso.

## Crear y probar una clase con una lista privada de alumnado

La plataforma de PythonAnywhere debe actualizarse primero; sigue [la guía de actualización](ACTUALIZAR_PYTHONANYWHERE.md). No hay acceso remoto automático a esa cuenta desde el repositorio. Ningún nombre real se añade al código, documentación, fixtures ni semillas demo.

1. En **Grupos → Crear grupo**, introduce el nombre facilitado por la academia, tipo **Inicial**, curso académico vigente, docente asignado, horario recurrente informativo, fechas de vigencia y capacidad suficiente para los nueve alumnos. Usa los datos reales que conozcas; no se inventan docente, ubicación o fechas del curso.
2. Antes de dar altas, comprueba si esas personas ya existen. Para alumnos existentes, utiliza su matrícula o traslado, conservando su historia. La importación bloquea nombres duplicados y no fusiona personas automáticamente.
3. Para quienes todavía no existan, ve a **Alumnado → Importar / añadir varios**, pega la lista privada (un nombre por línea), selecciona grupo y fecha de incorporación, valida y confirma. No pegues datos reales en GitHub ni ejecutes la semilla demo para crearlos.
4. Comprueba que la fecha de incorporación sea anterior o igual a la clase: así aparecerán en su lista de asistencia.
5. Importa la ficha Word y selecciona el grupo real y su docente. Para la prueba solicitada: **22/10/2026, 16:30, 90 minutos**, zona **Europe/Madrid**; el final debe ser **18:00**. Valida y confirma una única sesión, sin crear una serie de recurrencias por accidente.
6. Abre la sesión y comprueba los nueve alumnos y las ocho tarjetas. No marques asistencia ni logros que no hayan ocurrido. El registro queda planificado hasta que el docente decida cerrarlo.
7. Para ensayar colores, utiliza registros ficticios en un entorno separado. En una clase real, marca únicamente retos observados. No se asigna NEAE a ninguna persona por pertenecer al grupo o por la información aportada en una lista de matrícula.

Los servidores y los datos de demostración están separados mediante `APP_ENV`. Antes de pasar de la prueba a uso estable con datos reales, aplica la configuración y revisiones pendientes de [operación y privacidad](OPERATIONS.md). El repositorio no da por completadas esas revisiones ni cambia el despliegue de demo a producción automáticamente.

## Eliminar la sesión de prueba anterior

Solo Administración dispone del botón **Eliminar sesión de prueba** dentro de una sesión.

1. Abre exactamente la sesión de prueba que quieras retirar y pulsa ese botón.
2. Comprueba título, grupo, día y horario en la confirmación.
3. Lee el alcance. Se elimina una sesión y su planificación, no el grupo, matrículas, biblioteca, demás sesiones ni auditoría.
4. Escribe **ELIMINAR** y pulsa **Eliminar esta sesión**.
5. Vuelve al calendario y comprueba que desapareció esa sesión y se conserva la clase que querías mantener.

Solo se puede borrar una sesión planificada sin asistencia, registros de aprendizaje, seguimiento de retos, evidencias, ejecución o vínculos de recuperación. Si ya contiene historial o es una recuperación, se bloquea el borrado: utiliza **Editar planificación → Estado: Cancelada**, conservando sus datos. Se comprueba de nuevo al confirmar, por si otro docente registró algo mientras la confirmación estaba abierta. Una confirmación caducada por cambios de versión también se rechaza.

## Mapa técnico y recuperación

- `core/challenges.py`: extracción de estructura, umbrales, validación y revisiones individuales.
- `Session.challenge_specs` y `Session.diversity`: estructura y apoyos generales previstos.
- `ChallengeProgress`: revisiones inmutables con copia de consignas y relación a la revisión previa.
- `SupportPlan`: revisiones restringidas de adaptaciones, sin diagnóstico automático.
- `core/views/planning.py`: tarjetas, editor, registro de clase y eliminación protegida.
- `core/views/students.py`: permisos, planes individuales e historial.
- `static/core/challenges.css` y `challenges.js`: presentación y previsualización del contador, sin persistencia en el navegador.
- `core/test_challenges.py`: ritmos distintos, colores, versiones, permisos, exclusión de informes y eliminación.

Las migraciones `0006` y `0007` añaden campos/tablas; no reescriben las matrículas ni registros educativos anteriores. La copia de seguridad debe realizarse **antes** de migrar. Si una actualización falla, conserva la copia, evita nuevas escrituras y sigue el procedimiento de restauración de OPERATIONS.md. No borres la base ni reviertas las migraciones eliminando tablas con seguimiento real.
