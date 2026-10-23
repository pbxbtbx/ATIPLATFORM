# Importar una hoja ODS de alumnado, responsables y grupos · 0.6.0

Puedes cargar el archivo `.ods` directamente. No necesitas convertirlo a CSV ni preparar un archivo por clase. Puedes importar un grupo, una pestaña o varios grupos de distintas pestañas en un mismo lote.

## Paso a paso

1. Entra con Administración en **Alumnado → Importar / añadir varios**.
2. Selecciona **Alumnado, responsables y grupos · ODS**.
3. Elige el archivo de tu ordenador, deja vacía la lista de nombres y pulsa **Preparar importación**. Solo se crea un borrador privado; todavía no se da de alta alumnado.
4. Marca las **pestañas que quieres importar**. No se selecciona ninguna automáticamente. Una jornada abierta o un campus no implican una matrícula de curso: déjalos sin seleccionar si no quieres importarlos.
5. Indica la **fecha real de incorporación y matrícula**, que se aplicará a las matrículas nuevas del lote. Debe estar dentro de la vigencia de sus grupos. Si necesitas fechas diferentes, prepara lotes separados.
6. En cada pestaña, asigna los nombres de grupo de la hoja a los **grupos ya creados** en la plataforma. Deja **No importar este grupo** para excluirlo. Si varias etiquetas de origen describen el mismo grupo, puedes elegir el mismo destino para ellas. No se interpretan automáticamente horarios ni textos como «plazas libres».
7. Si falta un grupo, créalo en otra pestaña del navegador con su curso académico, tipo, capacidad, docentes y fechas. Reabre el borrador para que aparezca entre las opciones; los borradores caducan a las 24 horas. No se inventan esos datos al leer la hoja.
8. Despliega **Revisar alumnos y responsables de esta pestaña**. Revisa nombres, nacimientos, contactos y filas incluidas. Desmarca las filas o responsables que no quieras importar. Solo se validan e importan las filas marcadas de pestañas seleccionadas y grupos asignados.
9. Para un alumno existente, selecciónalo expresamente en su fila. Deben coincidir nombre y nacimiento revisados; su ficha no se modifica. Si tiene un nombre diferente, revisa la ficha y el archivo antes de continuar. No se fusionan personas por nombre automáticamente.
10. Si un mismo alumno aparece en varias filas con el mismo nombre y nacimiento y has verificado que es la misma persona, marca **Unir filas…**. Así puede tener una ficha y varias matrículas. Para homónimos diferentes, utiliza la gestión individual y verifica su identidad.
11. Si has comprobado los responsables compartidos, marca **Reutilizar responsables con nombre y contactos idénticos…**. Se exige al menos teléfono o correo. No se usa solo un teléfono para decidir que dos personas son la misma.
12. Si un nombre de responsable coincide pero sus contactos difieren, se detiene la validación y se abre el apartado con el error. Corrige el dato si era un error; si son realmente dos personas distintas, marca **Es una persona diferente aunque coincida su nombre; lo he comprobado** en ese contacto. No marques esa opción para evitar revisar un posible duplicado.
13. Un contacto sin nombre queda sin seleccionar y se señala. Puedes completar su nombre y seleccionarlo o dejarlo fuera sin excluir al alumno. El resultado mostrará cuántos contactos no se incluyen. No se crean responsables con nombres inventados.
14. Marca **He verificado la tutela legal para los vínculos nuevos** únicamente si puedes confirmar esa condición para todos los nuevos vínculos seleccionados. Si no, se crean como responsables sin tutela verificada. Puedes revisar sus condiciones individualmente después. No se presuponen contacto prioritario, emergencia, estructura familiar ni autorización de recogida.
15. Pulsa **Validar y ver resultado**. Comprueba personas nuevas/existentes, grupos, contactos, fecha, tutela y exclusiones. Corrige y vuelve a validar si es necesario.
16. Pulsa **Confirmar e importar alumnado y responsables**. El lote completo se revalida y se guarda en una transacción. Si hay un error, no se guardan altas parciales. Repetir la confirmación de ese borrador no duplica las altas.
17. Abre las fichas creadas, comprueba matrículas y responsables en **Tutores**, y vuelve a tu sesión para comprobar el listado de alumnado vigente ese día.

Para empezar solo por el grupo del jueves, selecciona únicamente su pestaña y asigna únicamente su etiqueta de grupo al grupo del jueves que ya creaste. El resto puede permanecer sin asignar. No es necesario copiar o publicar la lista de alumnos.

## Columnas admitidas

| Destino | Columnas de origen reconocidas |
| --- | --- |
| Nombre del alumno | `Nombre Alumno` + `Apellido Alumno` |
| Fecha de nacimiento opcional | `Date Nacimiento` o `DateNacimiento` |
| Grupo que debe revisarse/asignarse | `Form Grupo` |
| Primer responsable | `Nombre Resp1`, `Apellido Resp1`, `Email Resp1`, `Tel Resp 1` o `Tel Resp1` |
| Segundo responsable | `Nombre Resp2`, `Apellido Resp2`, `Email Resp2`, `Tel Resp 2` o `Tel Resp2` |

Se normalizan mayúsculas/minúsculas y espacios de cabeceras. Se ignoran concatenados, títulos intermedios, filas vacías y filas sin ambos campos de nombre/apellido del alumno. Si hay alumnado con datos incompletos, completa la hoja antes de importarlo; el importador no puede identificarlo a partir de un título de sección. No es un importador universal de cualquier estructura de hoja.

Las fechas ODS tipadas se leen como fechas, sin convertir números arbitrarios en fechas. También se reconocen textos `AAAA-MM-DD`, `DD/MM/AAAA` y `DD-MM-AAAA`. En la revisión se utilizan fechas `AAAA-MM-DD`; una fecha no reconocida se mantiene visible y debe corregirse o borrarse expresamente si no se va a recoger.

Los correos y nombres se pueden corregir antes de confirmar. Los teléfonos se conservan como texto, sin inventar prefijos o dígitos. Si la hoja ya perdió dígitos por su formato numérico, hay que contrastarlos con el origen.

## Qué se conserva y qué se excluye

- Se conservan fichas, matrículas activas, autorizaciones y condiciones de responsables existentes. No se convierten matrículas previas en traslados ni se cierran automáticamente otros grupos.
- Si ya existe una matrícula activa en el destino, no se duplica. Una matrícula terminada conserva sus fechas; una matrícula nueva debe ser revisada y cumplir vigencia/capacidad.
- Los vínculos existentes conservan también sus condiciones de tutela y recogida; el selector de tutela del lote solo afecta a vínculos nuevos.
- No se importan pagos, cuotas, datos bancarios, observaciones libres, conocimientos previos, notas familiares o de salud, asistencias históricas, casillas de privacidad ni autorizaciones. Una casilla marcada no documenta por sí sola finalidad, fecha ni versión de una autorización.
- El archivo original, sus fórmulas, macros, metadatos y columnas excluidas no se guardan en el borrador. Solo se conservan temporalmente los campos admitidos y los nombres de pestaña/grupo necesarios para revisarlos.

## Seguridad y límites

Solo Administración puede subir y confirmar ODS. El borrador es privado del autor, usa identificadores aleatorios, CSRF, caducidad de 24 horas y respuestas sin caché. Se revalidan datos, capacidad y vigencia al confirmar. Si cambió el resultado desde la revisión, es necesario volver a validar. La auditoría guarda acciones e identificadores, sin nombres, teléfonos, correos ni contenido de celdas.

Máximo: 2 MB de archivo, 20 MB descomprimidos, 30 pestañas, 300 filas de alumnado reconocibles y dos responsables por fila. Se limita la lectura a 64 columnas y a 2000 caracteres por celda; no se expanden millones de filas o columnas vacías de Calc. XML con entidades/DTD y contenedores inválidos se rechazan. Las fórmulas no se ejecutan: solo se leen valores guardados. No se visitan enlaces ni se envía la hoja a IA o servicios externos.

El formulario admite hasta 6000 campos para poder revisar un lote con varios responsables. Conserva límites finitos de tamaño y validación del servidor. Los datos temporales se eliminan tras confirmar; los borradores caducados se limpian con `manage.py purge_imports`, según [la guía de importaciones](IMPORTACIONES.md).

El archivo del usuario no forma parte del repositorio ni de las demostraciones. Las pruebas persistentes usan únicamente personas ficticias. Sigue las configuraciones de [operación y privacidad](OPERATIONS.md) antes del uso estable con datos reales.

## Módulos y pruebas

- `core/ods_importing.py`: lectura ODS, selección de columnas, límites y normalización.
- `ODSImportForm` en `core/import_forms.py`: pestañas, grupos, filas, correcciones y decisiones explícitas.
- `core/ods_service.py`: altas, matrículas, responsables compartidos, integridad e identificación de cambios del plan.
- `core/views/ods.py` y `templates/core/ods_preview.html`: revisión, confirmación y control de acceso.
- `static/core/ods.css` y `ods.js`: estilo operativo y filtrado visual según pestañas/grupos; la validación siempre se realiza en el servidor.
- `core/test_ods.py`: pruebas con archivos generados de datos ficticios, sin incluir el archivo original.

Esta versión utiliza `ImportDraft`, `Student`, `Guardian`, `GuardianLink` y `Enrollment` existentes. No necesita nuevas migraciones ni dependencias de ofimática. Conserva una copia previa a actualizar; si falla una importación, corrige el borrador y vuelve a validar. Si hubo un error humano después de confirmar, revisa los registros concretos; no borres historiales ni restaures toda la base sobre cambios posteriores sin seguir el procedimiento de recuperación.

## Corregir una matrícula añadida por error

No borres la ficha del alumno ni simules un traslado para corregir una importación.
Administración puede abrir la ficha → Resumen → Historial de matrículas →
**Corregir matrícula errónea**, junto al grupo equivocado. Revisa alumno y grupo y
escribe **RETIRAR** en la confirmación. Se elimina exclusivamente esa matrícula,
no se asigna un destino ni se modifica la ficha, responsables u otros registros.
La auditoría conserva actor, fecha, acción e identificadores del alumno y grupo,
sin copiar nombres ni contactos.

Esta corrección se limita a matrículas activas **creadas hace menos de 24 horas**
(el plazo se refiere al alta en el sistema, no a la fecha de matrícula educativa).
El servidor bloquea la operación si existe cualquier asistencia, aprendizaje, reto
o evidencia de ese alumno en ese grupo, también de fechas anteriores. Matrículas
finalizadas o antiguas requieren revisión administrativa; una baja real no debe
borrarse como si fuera un error. Se revalida todo en transacción y se rechaza una
versión obsoleta. Solo POST con CSRF y confirmación expresa modifica datos.

Para el caso del piloto: tras retirar el alta equivocada de Martes Intermedio,
se conserva la persona en Alumnado. Cuando se cree Miércoles Intermedio, selecciona
su ficha existente al matricularla o importarla; no crees otra persona.

Módulos: `core/enrollment_correction.py`, vista `enrollment_remove` en
`core/views/students.py`, `templates/core/enrollment_remove.html` y
`core/test_enrollment_correction.py`. No requiere migración nueva.
