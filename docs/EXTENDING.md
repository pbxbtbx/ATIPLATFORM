# Extender la plataforma

## Organización

`config/`: despliegue, rutas y seguridad. `core/models.py`: entidades e integridad. `core/access.py`: autorización y ámbitos. `core/services.py`: snapshots, cambios con control de versión y traslados transaccionales. `core/forms.py`: validación y formularios. `core/views.py`: flujos HTTP. `core/configuration.py`: esquema declarativo permitido. `templates/core/` y `static/core/`: interfaz y recursos locales, sin CDN. `core/tests.py`: casos operativos y de aislamiento. La siguiente partición al crecer debería separar apps de matrícula, planificación, aprendizaje y configuración sin cambiar identificadores.

## Añadir pantallas y permisos

Añadir una vista con login_required y consulta limitada mediante groups()/students()/session_q(), no obtener un objeto global y confiar en ocultarlo en HTML. Para notas restringidas, require_sensitive() además del ámbito y audit() para lectura/escritura. Usar POST con CSRF para mutaciones. Añadir ruta, plantilla accesible y pruebas que intenten acceder como docente ajeno y desarrollador sin datos educativos. No usar `is_staff` como permiso de desarrollo: solo development_access lo concede. Los coordinadores acceden únicamente a grupos explícitamente asignados; no hay ámbitos de dominio independientes aún.

## Campos y formularios

Campos personalizados de alumnado: Desarrollador → custom_fields. Definición: `{ "key":"herramienta", "label":"Herramienta preferida", "type":"choice", "required":false, "options":["Robótica","3D"] }`. Texto admite hasta 500 caracteres. Nunca usar campos personalizados para saltarse el apartado restringido. Se conservan valores de campos retirados; cambiar identificadores o tipos requiere evaluación de datos. La versión actual no ofrece un constructor visual de formularios completos ni validaciones ejecutables.

Campos estructurales nuevos: añadir nullable/blank o valor por defecto seguro, generar migración versionada, revisar `sqlmigrate`, copia previa, ejecutar sobre una copia privada de pruebas y verificar registros previos. Si se requiere transformación, `RunPython` con apps.get_model, transformación explícita y reversible o procedimiento de recuperación; no importar modelos actuales en migraciones antiguas. No eliminar columnas en la misma entrega que deja de leerlas. Probar actualización y recuperación antes de producción.

## Historial, concurrencia e integraciones

Nunca modificar snapshots de sesiones para sincronizarlos con biblioteca. Las secuencias guardan una selección histórica en el orden seleccionado por la consulta; el editor actual no ofrece reordenación manual. Los registros de aprendizaje son append-only y supersedes apunta a la versión previa. Ediciones de sesiones y fichas usan versión esperada y una actualización condicional dentro de una transacción. No eludir esa comparación en nuevas vistas.

En recurrencias, conservar Europe/Madrid y pruebas alrededor de cambio de hora. Las repeticiones actuales son semanales, entre 1 y 52; `schedule` del grupo es informativo y no genera automáticamente sesiones. Cambiar «siguientes» mueve fechas/docente/estado, conservando las actividades originales; las clases realizadas no se modifican en lote.

Para integraciones nuevas: configurar destino explícito, credenciales del gestor de secretos, permisos de mínimo alcance, tiempo límite, reintentos idempotentes y auditoría sin datos personales. No enviar datos de menores a IA ni servicios externos por defecto. Probar con dobles controlados y solo después con sandbox del proveedor. No añadir comandos ni carga de código a Desarrollador.

## Configuración

Claves y validaciones en configuration.py. Los módulos operativos son library y reports; los controles también se aplican en servidor. El indicador `rubrics` activa/desactiva las observaciones de rúbrica en modo clase. Otros indicadores se guardan para futuras funciones y no ejecutan acciones. Tipografías limitadas, colores hexadecimales, logotipo oficial solo en `/static/`. Subir el logotipo requiere revisión del recurso y despliegue del archivo estático. Las etiquetas permiten cambiar navegación, `home_title`, `save_button` y los campos de los formularios con `<modelo>.<campo>.label` y `<modelo>.<campo>.help` (por ejemplo `session.goals.help`). Las plantillas son texto, nunca código. La restauración vuelve a pasar por validación/vista previa/publicación y no ejecuta migraciones ni cambia registros educativos.
