# Validación de práctica y accesibilidad · 0.7.0

- Suite completa: 88 pruebas correctas, incluidas doce nuevas de preferencias, práctica, ámbitos e integridad.
- Práctica: SQLite separado con esquema versionado; dos aprendices por propietario; 2/8 y 8/8 guardados, control de edición concurrente, IDs de personas reales sin capacidad de dirigir el guardado, ámbito permitido, CSRF, autenticación y reinicio confirmado.
- Antes/después de la práctica en pruebas y navegador: alumnado, matrículas, sesiones, aprendizaje y retos de la base educativa conservados sin cambios. La auditoría registra metadatos de acciones.
- Ámbitos: tres principales y dos extras, resúmenes sin duplicar revisiones, historial anterior sin clasificación conservado, códigos copiados al registrar aprendizaje y retos; docente ajeno sin acceso a registros fuera de su ámbito.
- Preferencias por cuenta: persistencia tras nuevo acceso, rechazo de valores inválidos y clases HTML acotadas. Las ayudas de voz no incorporan datos de la ficha individual a sus mensajes.
- Chromium: ajustes de texto, contraste, espaciado, controles grandes, reducción de movimiento y decoración simplificada; práctica guardada; cinco tarjetas por aprendiz; IDs de elementos únicos; Saltar al contenido lleva el foco a main; español/inglés; 768 y 384 px sin desbordamiento; sin errores JavaScript.
- Voz comprobada con API simulada: selección de voz local aunque exista una remota antes, idioma es/en, velocidad configurada, sin reproducción automática, pausa/continuación/parada y bloqueo de voces exclusivamente remotas. La reproducción audible con voces reales de Windows y el uso con lectores de pantalla reales quedan pendientes de la prueba en el dispositivo del usuario; no se afirma certificación de accesibilidad.
- Migración 0008 aplicada en demo local tras copia verificada. No se añaden dependencias externas; el esquema ficticio se inicializa desde SQL estático del repositorio en su propio archivo.

## Validaciones anteriores

# Validación de importación ODS · 0.6.0

- Suite completa: 76 pruebas correctas, incluidas 13 específicas de ODS.
- Archivo real inspeccionado en memoria: pestañas/columnas reconocidas y grupo solicitado localizado. No se ha importado alumnado real ni contactos reales a la base demo local ni a PythonAnywhere. El archivo no se incluye en el repositorio, fixtures o capturas.
- Se detectaron datos de contacto que necesitan revisión, sin inventar nombres ni fusionar responsables con datos distintos.
- Pruebas ficticias: varias pestañas y grupos, responsables compartidos, alumnos repetidos entre grupos, selección expresa de existentes, capacidad revalidada, campos excluidos, corrección de contactos, tutela explícita, homónimos de responsables y contacto sin nombre excluible sin perder el alumno.
- Seguridad: propietario del borrador, Administración en servidor, CSRF, caducidad, ODS/XML inválidos, límites, bloques vacíos de Calc y texto/formato acotado. No se copian pagos, observaciones ni casillas de privacidad a la carga temporal; no se crean autorizaciones desde ellas.
- Confirmaciones repetidas sin duplicar; plan cambiado desde la revisión rechazado; fichas, matrículas y condiciones existentes conservadas.
- Chromium con ODS ficticio: subir, seleccionar una pestaña y dos grupos, validar, confirmar dos alumnos y un responsable compartido; resultado recargable sin duplicación, idiomas español/inglés, tablet 768 px sin desbordamiento y sin errores JavaScript. Comprobación de relaciones también en base de datos.
- Sin nuevas migraciones ni dependencias; conserva las tablas existentes y aumenta a 6000 el límite finito de campos de formulario para revisar lotes ODS.

## Validaciones anteriores

# Validación de retos y adaptaciones · 0.5.0

- Suite completa: 63 pruebas correctas, incluidas nueve de retos, adaptaciones y eliminación.
- Ocho retos: límites 0–1 gris, 2–3 verde, 4–5 azul, 6–7 lila y 8 naranja. Dos alumnos avanzan a ritmos distintos sin generar evaluación automática de aprendizaje.
- Revisiones de retos: historial preservado, selección inválida revierte el lote, edición concurrente rechazada y casillas vacías conservadas como borrador tras un error.
- Importaciones anteriores: estructura recuperada desde su copia, sin reimportar. Al guardar seguimiento queda fijada la estructura de esa sesión. El editor no cambia consignas con seguimiento existente.
- Adaptaciones: permiso adicional y ámbito de alumno exigidos en servidor; sin marca ni contenido para docente sin permiso o desarrollo; NEAE no inferida; revisiones y finalización conservan la historia; excluidas de informes y exportación administrativa sin selección expresa de información restringida.
- Eliminación: Administración, confirmación literal y versión vigente; borra una sola sesión vacía y conserva alumnado, otras sesiones y auditoría. Asistencia o seguimiento bloquean el borrado.
- Migraciones 0006/0007 aplicadas sobre demo tras copia verificada. Comparación con esa copia: alumnado, matrículas, aprendizaje, asistencia, vínculos de responsables y autorizaciones conservados sin cambios.

- Prueba en Chromium con la ficha Word anterior: ocho tarjetas sin reimportación, materiales al principio, diversidad separada, colores 2/8 y 8/8 con guardado, plan curricular ficticio restringido y eliminación de sesión vacía. Tablet 768 px sin desbordamiento, español/inglés y sin errores JavaScript.

## Validaciones anteriores

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

## 0.8.0 — ciberseguridad

- `APP_ENV=testing .venv/bin/python manage.py test --noinput`: **96 pruebas correctas**, incluidas 8 del nuevo módulo. La suite de configuración fija explícitamente su entorno de desarrollo para probar el aislamiento aunque CI use testing.
- Acceso anónimo redirigido; superusuario sin permiso de desarrollo rechazado; desarrollador no recibe acceso educativo. GET no ejecuta subprocesos, POST rechazado y CSRF probado.
- Cambios, altas, ausencias y enlaces simbólicos en código detectados; manifiesto ausente no comprobado; comprobación CLI sin escribir.
- Informes corruptos, caducados, de otro entorno o huella rechazados; ausencia y fallos de herramientas nunca se convierten en éxito. Informe agregado con permiso 0600; secretos no renderizados.
- Bandit 1.8.6: **0 hallazgos** tras reforzar XML con defusedxml y revisar excepciones puntuales documentadas.
- pip-audit 2.9.0 contra dependencias de ejecución fijadas: **0 vulnerabilidades conocidas** en la consulta realizada. Esto no acredita ausencia de fallos, seguridad de OS/proxy ni todas las clases de vulnerabilidad.
- `manage.py check`, `makemigrations --check --dry-run` y `git diff --check` correctos; no hay migración de datos nueva.
- Pendiente ejecutar el workflow alojado de GitHub y validar el despliegue PythonAnywhere y su configuración HTTPS/DEBUG/clave. No se ha realizado una auditoría independiente, prueba de intrusión ni revisión legal.
