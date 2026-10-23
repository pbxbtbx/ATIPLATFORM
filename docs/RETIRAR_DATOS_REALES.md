# Retirar datos reales del piloto — 0.9.0

No certifica cumplimiento ni borrado de todas las copias. No crear nuevas copias de
los datos que se pretende retirar. El original de inscripciones del responsable,
fuera de esta plataforma, no se modifica. Esta operación no sustituye una decisión
del responsable del tratamiento ni el procedimiento de conservación/supresión legal.

## 1. Interrumpir el acceso antes de actualizar

En PythonAnywhere → Web → **Disable web app**. Detener también tareas programadas,
comandos y otros escritores. No borrar código ni credenciales. Mantener el servicio
desactivado mientras se actualiza y migra la aplicación. El modo mantenimiento
ordinario no basta para bloquear todos los usuarios ni las pantallas de acceso.

Tras descargar esta versión, cargar en Bash las mismas variables privadas que usa
WSGI (véase PASO_A_PRODUCCION.md). Ejecutar `manage.py migrate --noinput` para crear
`0009_dataerasure`, que solo añade una tabla de justificantes. No añadir una copia
nueva al procedimiento de retirada. No ejecutar `demo` ni reimportar el ODS.

Antes de reactivar el sitio para operar la interfaz, configurar **antes de cargar
Django**, en WSGI:

```python
os.environ['ERASURE_ONLY'] = '1'
```

Este modo admite únicamente login/logout y la zona `/privacy/erasure/`. Exige una
cuenta de Administración **con permiso específico de información restringida**;
Desarrollo por sí solo no basta. Los usuarios sin ese permiso reciben 403 y el resto
de rutas de la aplicación quedan bloqueadas/redirigidas. El control de estáticos
externo al WSGI no debe publicar archivos privados. No retirar este modo hasta
concluir el procedimiento y decidir si se vuelve a abrir un entorno ficticio.

## 2. Selección múltiple desde la interfaz

En funcionamiento normal: **Alumnado → Retirar datos personales**. En modo de
retirada, al entrar se redirige directamente a esa pantalla.

1. Marcar las fichas a retirar o pulsar **Seleccionar todos**. No hay inferencia
   automática de «real»/«ficticio»: el operador debe revisar las personas. Máximo
   300 por operación, incluyendo personas sin matrícula o de grupos archivados.
2. Pulsar **Revisar selección y alcance**. No borra nada.
3. Revisar nombres, cantidad y alcance. Se eliminan fichas, matrículas, asistencia,
   aprendizaje y revisiones, retos y revisiones, apoyos/NEAE y revisiones, notas
   restringidas, autorizaciones, evidencias y sus archivos propios.
4. Se eliminan los responsables que ya no estén vinculados a otros alumnos. Los
   responsables compartidos con alumnado no seleccionado se conservan, así como
   sus otros vínculos y datos. Si se selecciona a todo el alumnado, también se
   eliminan los responsables vinculados exclusivamente a esas fichas.
5. **Se eliminan TODOS los borradores de importación**, de cualquier usuario,
   porque pueden contener copias de contactos sin identificadores enlazables. Esto
   afecta a importaciones ajenas en preparación y se declara en la confirmación.
6. Aceptar el alcance, escribir `ELIMINAR N ALUMNOS` con el número mostrado y
   reintroducir la contraseña actual. No enviarla al chat. No hay copia automática.

El plan está firmado, vinculado a usuario/entorno y caduca a los 15 minutos.
Cambios concurrentes en fichas, datos vinculados, responsables o borradores obligan
a revisar de nuevo. Un error, contraseña incorrecta, falta de confirmación o
referencias protegidas ajenas impide confirmar la transacción. Las revisiones se
desvinculan únicamente dentro del alcance seleccionado para no romper historial
no seleccionado. No se alteran grupos, sesiones, biblioteca ni otros alumnos.

## 3. Doble comprobación y justificante

- **Comprobación 1, en la transacción:** ausencia de las fichas seleccionadas y sus
  relaciones, responsables exclusivos y todos los borradores. Si falla, la operación
  de base de datos no se confirma. También se eliminan referencias de auditoría a
  esos registros, conservando un evento mínimo de retirada.
- **Comprobación 2, tras la transacción:** se borran los archivos propios y se
  comprueba que no existen en almacenamiento. Las rutas deben estar dentro del
  almacenamiento privado local previsto; no se siguen enlaces simbólicos ni rutas
  arbitrarias. Un archivo todavía referenciado por otro alumno no se borra a ciegas.

BD y filesystem **no son una sola transacción**. Ante errores de archivos, la
retirada de registros ya confirmada no se revierte: el justificante muestra pendiente
y conserva las claves privadas necesarias para reintentar con contraseña. No muestra
esas rutas ni contenido en la interfaz. Una vez eliminados se vacía esa lista.

El justificante conserva autor, fecha, recuentos y resultados, sin nombres,
contactos ni lista de IDs de alumnos. Solo lo ve su autor autorizado; se puede volver
a abrir desde **Comprobaciones anteriores**. El resultado corresponde a esa operación
y fecha, no es un escaneo perpetuo de posibles reimportaciones posteriores.

## 4. Qué sigue pendiente incluso con dos comprobaciones superadas

El informe muestra recuentos orientativos de archivos de copias locales y otras
bases SQLite directamente bajo `var`; un valor negativo indica comprobación no
posible. No se abren para leer datos ni su ausencia demuestra ausencia de copias.

Revisar por separado:

- `var/backups` de todos los entornos, bases antiguas, descargas y exportaciones.
- Notas generales de sesiones, tareas, textos libres, recursos o configuraciones:
  pueden contener menciones a personas sin vínculos estructurados identificables.
- Archivos compartidos y responsables conservados por vínculos con otras personas.
- Logs del alojamiento y copias/snapshots del proveedor: gestionar acceso, retención
  y eliminación según contrato y posibilidades técnicas. No se puede verificar ni
  ordenar su borrado desde este botón.
- Copias y datos enviados a otros servicios, incluido el ODS y contenido compartido
  en este chat: borrar la plataforma no borra la conversación ni sus adjuntos.
  Gestionarlos mediante las opciones y políticas de la cuenta correspondiente.

SQLite puede conservar bytes en páginas libres, WAL, diarios y copias. Los SELECT
que devuelven cero no demuestran borrado físico. El borrado de archivos tampoco
acredita sobrescritura física en el almacenamiento del proveedor. No presentar este
justificante como certificado legal ni como «todo borrado».

## 5. Reinicio completo opcional de todos los datos operativos locales

**Solo si se ha decidido retirar TODO el contenido operativo del piloto**, no si
se desea conservar planificación, usuarios o datos de alumnos no seleccionados.
Este es un paso de consola autorizado y separado del botón de selección múltiple.

Con web y todos los escritores detenidos, se puede inventariar sin leer contenidos:

```bash
.venv/bin/python scripts/remove_pilot_data.py
```

No necesita Django ni abre una base. La retirada explícita de TODO `var` se realiza
solo tras revisar su alcance:

```bash
.venv/bin/python scripts/remove_pilot_data.py --site-disabled --confirm RETIRAR_DATOS_DEL_PILOTO
```

Elimina **todas** las bases, cuentas, sesiones, adjuntos, copias, borradores, prácticas,
informes y justificantes de ese repositorio. Mantiene código, `.venv` y los archivos
externos, incluida la clave privada habitual. Después no se podrá iniciar sesión
hasta crear una base vacía y una nueva cuenta; no reactivar automáticamente la web.
No restaura datos, no crea una copia y rechaza rutas configuradas fuera de `var` o
enlaces simbólicos. La declaración `--site-disabled` es del operador: no verifica
por red el estado del proveedor. Si hay un fallo de filesystem puede haber una
retirada parcial; mantener el servicio detenido y revisar.

Esta limpieza no elimina archivos fuera de `var`, logs externos, copias descargadas
ni snapshots del proveedor y tampoco prueba borrado físico. Consultar esas ubicaciones
antes de dar por concluida la retirada. No restaurar una copia antigua sin volver
a aplicar las decisiones de supresión.

## Módulos y pruebas

- `core/data_erasure.py`: alcance, huella HMAC, transacción, archivos y verificaciones.
- `core/views/data_erasure.py`: selección, reautenticación y justificantes privados.
- `DataErasure`, migración `0009_dataerasure`: recibo mínimo y archivos pendientes.
- `core/middleware.py:ErasureOnlyMiddleware`: acceso limitado a la retirada.
- `templates/core/erasure*.html`, `static/core/data_erasure.js`: selección múltiple y confirmaciones.
- `scripts/remove_pilot_data.py`: inventario y retirada total local opcional, fuera de HTTP.
- `core/test_data_erasure.py`, `core/test_pilot_removal.py`: solo datos y archivos ficticios.
