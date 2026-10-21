# Validación realizada · 21 de octubre de 2026

- Suite completa antes del envío a GitHub: 33 pruebas ejecutadas, 33 correctas; ninguna omitida. Incluye subida de PDF privado, descarga autenticada y denegación a docente ajeno y desarrollador.
- `manage.py check`: sin incidencias; `makemigrations --check --dry-run`: sin migraciones pendientes; `pip check`: dependencias consistentes; `git diff --check`: sin errores de espacios.
- Instalación repetida con `scripts/install.sh`: correcta, sin cambios pendientes de migración. Carga demo repetida: detecta datos ya creados y no los sobrescribe.
- Chromium: siete secciones principales responden; diseño a 768 px sin desbordamiento; ningún error JavaScript. Flujo desde interfaz: crear sesión, asistencia, avance individual, cerrar sesión, vista previa de informe, descarga PDF y configuración borrador → validación de vista previa → publicación. Todo usando registros ficticios aislados en demo.
- Copia local demo: snapshot SQLite y restauración temporal con integridad, claves foráneas y lectura de aprendizaje correctas. Se ha vuelto a ejecutar tras los últimos cambios de esquema. No se ha validado recuperación externa completa de servicio/archivos.
- `check --deploy` en desarrollo emite seis avisos esperados (DEBUG, TLS, clave local y cookies). El perfil production con clave temporal no persistida activa esas protecciones; quedan dos avisos sobre HSTS para subdominios y preload. No se habilitan sin conocer el dominio y sus subdominios. Este chequeo de configuración no prueba un despliegue HTTPS real.

No se han utilizado datos reales. No se ha publicado ni desplegado en producción. Los límites funcionales y las tareas previas a datos reales están en SCOPE.md y OPERATIONS.md.
