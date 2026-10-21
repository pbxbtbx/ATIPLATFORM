# Prueba guiada de una clase con dos alumnos ficticios

## Preparación y resultados que buscamos

Sigue primero [la guía de acceso](ACCESO.md). Esta prueba es manual y utiliza solo **DEMO**. No introduzcas nombres, contactos, situaciones familiares ni datos de salud reales.

Usaremos:

- Grupo: **Exploradores · DEMO**.
- Alumno A: **Persona ficticia 01**.
- Alumno B: **Persona ficticia 02**.
- Responsable: **Responsable ficticio compartido**, ya vinculado a ambos en la demo.

La demo contiene más alumnos y avances previos. No los borres para hacer esta prueba. En la clase trabajaremos solo con los dos indicados; el tercer alumno del grupo se deja sin modificar. Buscaremos nuestros registros por el título de sesión nuevo, sin asumir que el historial empieza vacío.

Objetivo: comprobar que ambos pueden trabajar la misma actividad con ritmos distintos, que todo queda guardado y que el informe familiar excluye las notas internas.

## Paso 1. Verifica el acceso

1. Entra como `demo.admin`.
2. Comprueba el indicador **DEMO**.
3. Abre **Grupos → Exploradores · DEMO**.
4. Comprueba que están inscritos los dos alumnos indicados y que el grupo tiene asignado `demo.docente`.

**Resultado esperado:** puedes abrir el grupo y las fichas de ambos alumnos.

- [ ] Acceso confirmado.

## Paso 2. Comprueba el responsable compartido

1. Abre **Alumnado → Persona ficticia 01 → Tutores**.
2. Localiza **Responsable ficticio compartido**.
3. Repite con **Persona ficticia 02**.
4. Comprueba que se trata del mismo responsable y que sus funciones se muestran por separado: tutor legal, contacto prioritario, emergencia y recogida no son equivalentes.

**Resultado esperado:** un responsable puede estar asociado a ambos alumnos sin crear dos contactos independientes.

- [ ] Responsable compartido confirmado.

## Paso 3. Prepara una sesión nueva

1. Abre **Calendario → Nueva sesión**, o **Inicio → Planificar sesión**.
2. Selecciona **Exploradores · DEMO** y el docente `demo.docente`.
3. Título: **Prueba guiada de dos alumnos · DEMO**. Si repites la prueba, añade un número al final.
4. Elige una fecha de prueba dentro de las fechas de vigencia del grupo y una hora libre. Inicio y fin deben ser distintos y no coincidir con otro grupo del docente ni con un festivo. Las horas se interpretan en **Europe/Madrid**.
5. Número de sesión: el siguiente que corresponda en tu prueba; el número no completa aprendizajes automáticamente.
6. Objetivos: **Comprender una condición y explicar el resultado de una prueba**.
7. Materiales: **Ordenador y simulador de prueba; datos ficticios**.
8. Actividades previstas: **Crear una condición, probar dos entradas y explicar la salida**.
9. Repeticiones: **1**.
10. Pulsa **Guardar cambios**.

Puedes dejar el recurso de biblioteca vacío para probar una actividad propia. No cambies una sesión histórica ya realizada para reutilizarla.

**Resultado esperado:** se abre el modo clase con estado **Planificada**, los objetivos y la lista del grupo. Si hay un conflicto, el formulario debe explicarlo; selecciona otro intervalo antes de guardar.

- [ ] Nueva sesión creada.

## Paso 4. Registra asistencia y avances diferentes

En **Actividad común para los registros seleccionados**, escribe:

**Crear y probar una condición con dos entradas**.

Despliega la tarjeta de cada uno de los dos alumnos, marca **Presente** y selecciona **Añadir avance o revisión individual**. Introduce estos ejemplos ficticios:

| Campo | Persona ficticia 01 | Persona ficticia 02 |
| --- | --- | --- |
| Reto individual | Deja vacío para usar la actividad común. | Deja vacío para usar la actividad común. |
| Objetivo | Comprender una condición simple. | Explicar y ampliar una condición simple. |
| Actividad | Completado con apoyo. | Completado con autonomía. |
| Aprendizaje demostrado | En proceso. | Completado con autonomía. |
| Evidencia observable | Prueba dos entradas siguiendo una guía y explica una salida con ayuda. | Prueba dos entradas, anticipa la salida y explica por qué cambia. |
| Logros / fortalezas | Identifica la entrada que activa la condición. | Justifica la condición con ejemplos propios. |
| Dificultades encontradas | Necesita recordar el orden de comprobación. | El primer ejemplo no cubría una entrada alternativa. |
| Apoyos y adaptaciones | Guía visual y preguntas breves. | Pregunta de ampliación, sin guía paso a paso. |
| Comentario del alumno | Quiero volver a probar con otro valor. | Quiero añadir una segunda condición. |
| Próximo paso | Repetir la prueba y explicar ambas salidas con menos ayuda. | Añadir una segunda condición y comprobar un caso límite. |

En la **Nota privada individual** de Persona ficticia 01 escribe únicamente:

**NOTA INTERNA DE PRUEBA — NO EXPORTAR**.

Deja vacía la nota privada de Persona ficticia 02. No selecciones **Añadir avance** para el tercer alumno.

Pulsa **Guardar borrador** una vez.

**Resultado esperado:** aparece confirmación de guardado; cada alumno mantiene su estado individual y la sesión sigue planificada. Las notas privadas no se copian entre alumnos.

- [ ] Asistencia y dos avances guardados.

## Paso 5. Comprueba que se conservan al recargar

1. Recarga la página después de guardar.
2. Comprueba la asistencia de ambos y el texto de **Último avance**.
3. Abre las fichas individuales en **Aprendizaje** y busca el título de la nueva sesión.
4. Comprueba que Persona ficticia 01 muestra aprendizaje **En proceso** y Persona ficticia 02 **Completado con autonomía**.
5. Verifica que la nota interna solo aparece en el registro del primero.

**Resultado esperado:** los datos proceden de la base de datos y siguen presentes tras recargar. Los campos vacíos para añadir un avance nuevo no significan que se haya perdido el avance anterior: este se muestra en Último avance y en el historial.

- [ ] Persistencia y ritmos distintos comprobados.

## Paso 6. Cierra la clase y prepara la siguiente

Vuelve a la sesión de prueba. En esta visita **no vuelvas a marcar Añadir avance**, salvo que quieras crear una revisión adicional.

1. Actividades realizadas: **Ambos probaron una condición. Se personalizaron la ayuda y la ampliación**.
2. Pendiente de retomar: **Persona ficticia 01: explicar las dos salidas con menos ayuda**.
3. Adaptaciones aplicadas: **Guía visual y preguntas breves para quien las necesitó**.
4. Próximos pasos: **Repaso guiado para un alumno y segunda condición para el otro**.
5. Pulsa **Guardar y cerrar sesión**.
6. Si quieres preparar el siguiente encuentro, crea otra sesión con esos objetivos desde Calendario.

**Resultado esperado:** la sesión cambia a **Realizada**. Cerrar la sesión no cambia automáticamente los estados individuales de aprendizaje. No se crea otra sesión automáticamente al rellenar Próximos pasos.

- [ ] Clase cerrada sin igualar los aprendizajes.

## Paso 7. Prepara un informe familiar de cada alumno

1. Abre **Informes** y selecciona **Persona ficticia 01**.
2. Filtra el periodo para incluir la sesión de prueba. Si existen otros avances en el mismo periodo, identifica el bloque de esta sesión.
3. Selecciona **Actividades y proyectos**, **Evidencias observadas**, **Avances y fortalezas**, **Apoyos utilizados** y **Objetivos pendientes y próximos pasos**.
4. Incluye asistencia solo si quieres probar ese apartado.
5. Pulsa **Generar vista previa**.
6. Comprueba que el informe contiene las observaciones seleccionadas de ese alumno, pero no la frase **NOTA INTERNA DE PRUEBA — NO EXPORTAR**, información restringida ni el avance del otro alumno.
7. Descarga el PDF y compruébalo también.
8. Repite el proceso para **Persona ficticia 02**.

**Resultado esperado:** dos informes independientes y revisables. No se envían automáticamente a nadie.

- [ ] Informe de Persona ficticia 01 comprobado.
- [ ] Informe de Persona ficticia 02 comprobado.

## Paso 8. Comprueba los permisos

Esta parte requiere haber elegido contraseñas propias para las cuentas de prueba con `changepassword`; no cambies sus permisos para que la prueba pase.

1. Cierra sesión con el control de salida e inicia sesión como `demo.docente`.
2. Comprueba que puedes abrir el grupo y registrar sus sesiones.
3. Comprueba que **Desarrollador** y **Información restringida** no aparecen como accesos disponibles. El servidor debe rechazar también sus direcciones si intentas abrirlas directamente; ocultar enlaces por sí solo no basta.
4. Cierra sesión e inicia como `demo.desarrollo`.
5. Comprueba que puedes abrir **Desarrollador**, pero que **Alumnado** no muestra las fichas de estos alumnos ni permite abrirlas por su dirección.
6. Vuelve a `demo.admin` para continuar gestionando la demo.

**Resultado esperado:** desarrollo y acceso educativo no se conceden mutuamente. Las denegaciones en esta prueba son el resultado esperado, no un fallo que debamos resolver dando más permisos.

- [ ] Aislamiento de permisos comprobado.

## Cómo continuar juntos

Avanza un paso cada vez y comunica qué resultado ves. Si falla un paso, indica el número, la acción y el mensaje mostrado, sin compartir contraseñas, cookies ni datos reales. No marques el paso como completado hasta comprobar su resultado.

Una segunda prueba puede cubrir traslado de grupo conservando historial, cancelación y recuperación, recurrencias y restauración de configuración. No es necesario modificar esas funciones para completar esta primera clase con dos alumnos.
