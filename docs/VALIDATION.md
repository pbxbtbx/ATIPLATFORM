# Validación de importaciones y paleta · 0.4.0

- Suite completa: 54 pruebas, todas correctas. Incluye las pruebas anteriores y nueve nuevas de importación/paleta.
- Lotes de alumnado: subida sin crear registros, revisión, matrícula de dos personas, capacidad insuficiente y duplicados, revalidación al confirmar y confirmación repetida sin duplicar.
- Sesiones: extracción DOCX, copia del contenido, estado planificado sin asistencia, campos obligatorios, conflictos entre filas y rechazo completo del lote.
- Seguridad: borradores ajenos inaccesibles, caducidad, grupos ajenos, desarrollo sin acceso educativo, CSV malformados y DOCX inválidos/DTD rechazados.
- Prueba en Chromium con la ficha Word aportada: duración 90 minutos, retos R1–R8 conservados, revisión y creación de sesión en un grupo demo con fecha y horario ficticios elegidos para la prueba. No se han creado sesiones en PythonAnywhere.
- Navegador: alta y matrícula de dos alumnos ficticios; paleta básica guardada y previsualizada; interfaz de importación en español e inglés; ancho de tablet 768 px sin desbordamiento; sin errores JavaScript.
- Migración `0005` aplicada sobre la base demo existente después de copia verificada. Configuración básica y datos previos conservados.
- Comprobación Django, ausencia de migraciones pendientes por generar y compilación de traducciones incluidas en la validación final.

## Validaciones anteriores

# Validación realizada · 22 de octubre de 2026

- Suite completa de la versión 0.3.0: 45 pruebas ejecutadas, 45 correctas; ninguna omitida. Incluye subida de PDF privado, descarga autenticada y denegación a docente ajeno y desarrollador.
- `manage.py check`: sin incidencias; `makemigrations --check --dry-run`: sin migraciones pendientes; `pip check`: dependencias consistentes; `git diff --check`: sin errores de espacios.
- Instalación repetida con `scripts/install.sh`: correcta, sin cambios pendientes de migración. Carga demo repetida: detecta datos ya creados y no los sobrescribe.
- Chromium: siete secciones principales responden; diseño a 768 px sin desbordamiento; ningún error JavaScript. Flujo desde interfaz: crear sesión, asistencia, avance individual, cerrar sesión, vista previa de informe, descarga PDF y configuración borrador → validación de vista previa → publicación. Todo usando registros ficticios aislados en demo.
- Copia local demo: snapshot SQLite y restauración temporal con integridad, claves foráneas y lectura de aprendizaje correctas. Se ha vuelto a ejecutar tras los últimos cambios de esquema. No se ha validado recuperación externa completa de servicio/archivos.
- `check --deploy` en desarrollo emite seis avisos esperados (DEBUG, TLS, clave local y cookies). El perfil production con clave temporal no persistida activa esas protecciones; quedan dos avisos sobre HSTS para subdominios y preload. No se habilitan sin conocer el dominio y sus subdominios. Este chequeo de configuración no prueba un despliegue HTTPS real.

No se han utilizado datos reales. No se ha publicado ni desplegado en producción. Los límites funcionales y las tareas previas a datos reales están en SCOPE.md y OPERATIONS.md.

## Notificaciones e idiomas · 0.3.0

Pruebas de alcance por autor (también para administración), completar/reabrir mediante POST y CSRF, preferencias de idioma aisladas por cuenta, idioma de acceso anónimo, rechazo de idiomas no admitidos y redirecciones externas, etiquetas inglesas e historial sin reescritura.

Chromium: 11 pantallas en inglés; crear, completar y reabrir recordatorio; campana con aviso de cambios; limpiar el aviso al revertir el campo; bloquear cambio de idioma con cambios pendientes; conservar contenido al fallar la validación; volver a español. Sin errores JavaScript y sin desbordamiento de Notificaciones a 768 px. La paleta operativa es distinta de la escala de aprendizaje.

Migración 0004 aplicada sobre una copia SQLite anterior: recuentos de todas las tablas de aplicación y estilos por usuario conservados; idioma inicial español; integridad y claves foráneas correctas. Se ha vuelto a ejecutar el comando de backup con restauración temporal. El catálogo inglés contiene 656 mensajes compilados, incluidos contextos para distinguir Inicio/Home de Inicio/Start. Estas comprobaciones se hicieron en desarrollo; no afirman que PythonAnywhere se haya actualizado automáticamente.
