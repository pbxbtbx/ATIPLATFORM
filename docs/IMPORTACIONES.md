# Importar alumnado y sesiones

**Desde 0.6.0:** también puedes [importar directamente hojas ODS con responsables y grupos](IMPORTAR_ODS.md). Los límites y exclusiones de CSV descritos aquí no se aplican a las funciones específicas de ODS.

Las importaciones son locales al servidor y requieren iniciar sesión. No usan IA, no envían el documento a terceros y no ejecutan macros, comandos, instrucciones del documento ni sus enlaces. Un archivo se interpreta como contenido educativo, nunca como una orden para la aplicación.

## Probar la ficha Word recibida

1. Entra en **Calendario → Importar sesiones / Word**.
2. En «Qué quieres añadir», elige **Ficha de sesión · Word DOCX**.
3. Selecciona tu archivo `Ficha_03_Atigra_Inicial_Videojuegos_I(1).docx`. Deja vacía la lista de nombres.
4. Pulsa **Preparar importación**. Todavía no se crea ninguna sesión.
5. Comprueba el título «Desarrollo de videojuegos I · MakeCode Arcade · Atrapa la estrella», número 3, duración de 90 minutos, conceptos, preparación y actividades. El texto incluye los retos R1–R8, pistas y criterios de observación, diversidad y plan B.
6. Selecciona un grupo existente y su docente. Introduce la fecha y hora reales. El texto «Atigra Inicial · 7–14 años» del Word describe el destinatario: no identifica un grupo del sistema ni crea alumnado. No se deducen horarios.
7. Revisa y, si hace falta, edita los campos extraídos. «Actividades previstas y apoyos» conserva también las orientaciones docentes: no se registran como adaptaciones ya aplicadas.
8. Pulsa **Validar y ver resultado**. Comprueba grupo y docente seleccionados, fecha, hora, duración y contenido. Si modificas algo, vuelve a validar para actualizar el resultado previsto.
9. Pulsa **Confirmar y crear registros**. Se crea una sesión **planificada** y aparece un enlace para abrirla. No se marca como realizada, no se pasa asistencia ni se asignan avances automáticamente.
10. Abre la sesión y usa el modo clase habitual. El contenido importado queda guardado como copia; cambiar después el Word no altera la sesión.

La lectura reconoce los encabezados de esta ficha. Otros DOCX conservan el texto para revisión y necesitan completar o corregir los campos; no es un extractor universal. No admite `.doc`, documentos protegidos, documentos escaneados sin texto ni `.docm`. Las imágenes y la maquetación no se importan. Los enlaces se conservan como texto visible cuando está presente, sin descargar su destino ni reconstruir enlaces ocultos. El original binario y sus metadatos no se guardan. Se conserva una copia del texto de origen en la instantánea privada de la sesión.

## Añadir dos o más alumnos de una vez

Solo Administración puede dar de alta alumnado.

1. Ve a **Alumnado → Importar / añadir varios**.
2. Elige **Alumnado · CSV o lista**.
3. Sin seleccionar un archivo, escribe un nombre completo por línea. Para la prueba, usa nombres inequívocamente ficticios en el entorno demo.
4. Pulsa **Preparar importación**.
5. Revisa los nombres y selecciona grupo y fecha de incorporación.
6. Pulsa **Validar y ver resultado** y después **Confirmar y crear registros**.
7. Comprueba las dos fichas y sus matrículas. El historial de los alumnos que ya existían permanece intacto.

Los nombres repetidos dentro del lote o coincidentes con un alumno existente bloquean el lote. No se fusionan personas por nombre ni se sobreescriben datos. Para homónimos reales, utiliza la ficha individual y comprueba la identidad; para matricular alumnado existente, utiliza Matrícula y traslado.

## Importar CSV

Descarga la plantilla desde la pantalla de importación y conserva sus cabeceras técnicas en español, también si la interfaz está en inglés. Guarda el archivo como **CSV UTF-8**, con coma o punto y coma. Los valores que contengan el separador deben ir entre comillas CSV.

- Alumnado: `nombre` obligatorio; `nombre_preferido` y `nacimiento` opcionales. Nacimiento: `AAAA-MM-DD`. La fecha de incorporación y el grupo se seleccionan para el lote.
- Sesiones: `titulo`, `inicio`, `duracion_minutos` obligatorios; `numero`, `objetivos`, `materiales`, `actividades` opcionales. Inicio: `AAAA-MM-DDTHH:MM` en Europe/Madrid; las horas ambiguas o inexistentes por cambio horario se rechazan. También se admite una fecha ISO con desplazamiento explícito. El grupo y docente se eligen para el lote. Las sesiones se crean independientes, sin recurrencia.

Máximo 200 registros y 2 MB por archivo. El grupo debe estar activo, tener plazas suficientes y estar vigente. Se comprueban docentes asignados, festivos, horarios existentes y solapamientos entre filas. Cada lote se guarda en una sola transacción: un error revierte todo. Se revalida al confirmar por si alguien cambió los datos tras la vista previa. Repetir la confirmación del mismo borrador no duplica registros; las importaciones nuevas vuelven a comprobar duplicados y conflictos.

## Permisos y conservación

Docentes y coordinación solo importan sesiones en sus grupos autorizados. Desarrollo no concede acceso. Los borradores son privados de su autor, tienen identificador aleatorio y caducan a las 24 horas. Los formularios usan CSRF; las respuestas no se almacenan en caché. La auditoría registra identificadores y acciones, sin copiar nombres ni contenido del archivo.

Tras confirmar se eliminan los datos temporales del borrador y se conserva el resultado para evitar repeticiones. Para borrar físicamente borradores caducados aunque su autor no vuelva, programa diariamente en PythonAnywhere **Tasks** (ajusta las rutas si tu instalación difiere):

```sh
cd /home/pablete97/ATIPLATFORM && APP_ENV=demo .venv/bin/python manage.py purge_imports
```

La caducidad impide reutilizar el borrador aunque no se haya ejecutado la limpieza. Los registros educativos creados y la auditoría no se borran con ese comando. Incluye las copias de seguridad en tu política de conservación.

## Módulos

- `core/importing.py`: lectura CSV/DOCX, límites y extracción de texto.
- `core/import_forms.py`: carga y opciones revisables con grupos autorizados.
- `core/views/imports.py`: borrador, validación, transacción y confirmación.
- `ImportDraft` en `core/models.py`: propietario, contenido temporal y resultado.
- `templates/core/import_*.html`: pasos de la interfaz.
- `core/test_importing.py`: permisos, extracción, conflictos, capacidad e idempotencia.

En los flujos CSV/Word no se importan responsables, información restringida, calificaciones, asistencia, cuentas, grupos completos ni archivos de evidencias. Para responsables y varias matrículas por hoja utiliza [la importación ODS](IMPORTAR_ODS.md).
