# Operación, seguridad y revisión antes de datos reales

## Entornos y credenciales

Usa procesos, base de datos, archivos, claves y dominios separados para desarrollo, pruebas y producción. `APP_ENV` identifica el entorno visible y limita las versiones de configuración. La separación real requiere asignar rutas y volúmenes distintos; cambiar solo el indicador no garantiza aislamiento. Pruebas usa una base de datos temporal. Demo exige `APP_ENV=demo` y nombre de base de datos con `demo`.

No copies datos reales a desarrollo ni a las demostraciones. No se integra ninguna IA, publicidad, analítica o rastreador. Las URLs de evidencias se abren únicamente por acción del usuario; revisar la política de terceros antes de introducirlas.

En producción: `APP_ENV=production`, `DEBUG=0`, `DJANGO_SECRET_KEY` única y aleatoria desde un gestor de secretos, `ALLOWED_HOSTS` exactos. Django exige clave y activa cookies seguras, redirección HTTPS y HSTS. Termina TLS en un proxy correctamente configurado. No actives cabeceras de proxy confiables sin limitar el origen. Ejecuta un servidor WSGI (por ejemplo Gunicorn instalado y fijado por infraestructura), configura estáticos con `collectstatic`, almacenamiento persistente cifrado, límites de petición y recursos y supervisión. No publiques `var/`, archivos privados o backups con el servidor de estáticos. En SQLite evita varios servidores escritores; para escalar hay que migrar y probar PostgreSQL.

Antes de exponer el servicio: limitar intentos de login en el proxy, definir expiración de sesiones y recuperación de cuenta, decidir MFA/SSO, comprobar cabeceras, revisar dependencias, monitorización y alertas. La versión actual usa sesiones Django y contraseñas con hash; no incluye MFA ni recuperación por correo. Revocar cuentas desde Configuración; las siguientes peticiones comprueban estado y permisos. No imprimir variables o secretos.

## Copias y recuperación

`manage.py backup` usa la API de backup SQLite (copia coherente), copia los archivos privados del entorno (`var/private/<APP_ENV>/`) a `var/backups/<APP_ENV>/`, calcula SHA-256 y restaura la base de datos en una copia temporal. Comprueba integridad, claves foráneas y lectura de registros de aprendizaje. Registra fecha y resultado sin contenido educativo. El panel muestra la última ejecución comprobada, no afirma una periodicidad que no existe. La prueba actual no equivale a un simulacro completo de recuperación de servicio y archivos.

Antes de datos reales, programa copias automáticas con el orquestador, limita acceso, cifra el almacenamiento y envía las copias a otra ubicación privada autorizada. Define RPO/RTO y retención con el responsable. La copia local junto al servicio no cubre pérdida del volumen.

Recuperación: parar escritores y poner el servicio en mantenimiento mediante infraestructura; guardar una copia del estado actual; comprobar SHA-256 del backup; restaurar `database.sqlite3` en una ruta nueva y `private/` en un directorio privado nuevo; ejecutar `PRAGMA integrity_check` y `foreign_key_check`; ajustar `DATABASE_PATH` y ubicación de archivos si fuera necesario; iniciar una instancia de prueba sin conexiones externas; comprobar login, permisos, matrículas, sesiones y descarga de archivos; registrar fecha, alcance, responsable y resultado; cambiar tráfico y conservar recuperación inversa. No restaurar directamente sobre un servicio escribiendo. El mantenimiento del panel no bloquea comandos externos: detenerlos también.

## Privacidad y derechos

Esta implementación no acredita por sí sola cumplimiento legal. Antes de datos de menores: definir responsable/encargados, base jurídica, finalidades, información y autorizaciones, política de conservación, acceso de personal, gestión de incidentes y revisión legal. Diferenciar autorizaciones para imágenes, recogida y otros tratamientos. El permiso de desarrollo no concede acceso educativo; la información restringida exige permiso adicional y pertenencia a un ámbito autorizado. Un administrador tampoco recibe ese permiso automáticamente.

No guardar detalles clínicos/familiares sin propósito. Las notas restringidas distinguen hechos, observaciones e interpretaciones. Se auditan lectura y creación sin contenido; los registros técnicos no deben contener cargas de formularios ni consultas con nombres, cookies o contraseñas. En producción, DEBUG debe permanecer desactivado y los logs del proxy deben omitir parámetros de consulta y cuerpos. El visor solo registra códigos genéricos y referencias; nunca el mensaje ni la traza de la excepción. Monitorización externa y alertas pendientes de integrar.

La conservación en configuración expresa una política pendiente de revisión, no ejecuta borrados automáticos. Para solicitudes de acceso/rectificación/supresión: administración verifica identidad, alcance y base de conservación; exporta únicamente registros autorizados, deja constancia en auditoría por identificador, rectifica datos operativos desde fichas y añade correcciones de aprendizaje sin sobrescribir evidencias; la información restringida requiere revisión de personal con permiso específico. Supresión requiere evaluación y procedimiento técnico revisado, copia previa autorizada y tratamiento de archivos/backups dentro de su política. La exportación administrativa JSON contiene datos personales y educativos con confirmación expresa; la información restringida requiere selección y permiso adicional. Los archivos se descargan aparte. No existe botón de borrado masivo. No presentar CSV familiar como un expediente completo.

## Código, lanzamientos y cambios destructivos

Trabajar en una rama del repositorio, revisar cambios y migraciones, ejecutar pruebas, desplegar en pruebas con datos ficticios, tomar una copia verificable previa, aplicar migraciones, desplegar código y comprobar salud y flujos principales. Publicar notas y versión en el modelo Release con una migración de datos o comando autorizado. Ante fallo, decidir rollback de código compatible o recuperación de backup; no revertir esquemas a ciegas. La pestaña Desarrollador muestra estado y configuración, no credenciales ni terminal.

Las acciones actuales no borran registros: archivar conserva datos; traslado cierra una matrícula; restaurar configuración crea borrador. Publicar y restaurar exigen confirmación textual y muestran el alcance. Para futuras acciones destructivas, mostrar el conjunto afectado y una confirmación específica, controlar permiso/CSRF y auditar antes de ejecutarlas.
