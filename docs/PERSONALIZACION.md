# Personalización y estética RPG

## Elegir un estilo

Abre **Personalización** en el menú lateral. Está disponible para cualquier usuario interno autenticado, incluido el personal de desarrollo, sin conceder acceso adicional a grupos o alumnado.

1. Selecciona una tarjeta de estilo: **Fantasía RPG**, **Atigra claro** o **Noche tranquila**.
2. La misma pantalla cambia para mostrar una vista previa. Todavía no se ha guardado la elección.
3. Pulsa **Guardar mi estilo** para conservarla en tu cuenta, también en futuros accesos y otros dispositivos.
4. **Volver al estilo guardado** cancela la vista previa. Salir con cambios pendientes muestra el aviso habitual.

El estilo inicial es Fantasía RPG. La preferencia es personal; no cambia la interfaz elegida por otros docentes. Los formularios, navegación principal, permisos, asistencia, actividades, informes y datos mantienen sus funciones. Los informes familiares siguen siendo documentos legibles e imprimibles. No hay puntos, clasificaciones, recompensas automáticas, acceso del alumnado ni mecánicas competitivas.

## Colores por objetivo de aprendizaje

| Color | Decoración | Estado al que se aplica |
| --- | --- | --- |
| Gris | Por aprender | Sin iniciar (`new`). |
| Verde | En proceso | En proceso (`progress`). |
| Azul | Con apoyo | Completado con apoyo (`supported`). |
| Lila | Consolidado | Estado personalizado Consolidado (`consolidated`), cuando esté configurado. |
| Naranja | Legendario | Completado con autonomía (`autonomous`). |

**Legendario se refiere al objetivo del registro**, no a toda la formación ni a una etiqueta permanente sobre el alumno. El docente sigue registrando evidencias y distinguiendo actividad y aprendizaje; el tema no modifica estados automáticamente.

**Pendiente de retomar** conserva una presentación neutra gris: no equivale a un nivel superior. Los estados personalizados que no tengan asignación conocida también son neutros. Los nombres educativos y los colores aparecen juntos; no se depende únicamente de distinguir colores.

La escala visual incluye los cinco colores, pero **no añade ni cambia los estados educativos existentes**. Para disponer del escalón Consolidado como opción del formulario, una persona con permiso de desarrollo puede añadir `{"key":"consolidated","label":"Consolidado"}` a `progress_states` en el JSON de configuración, conservando el resto de estados, y seguir el flujo borrador → vista previa → publicación. Esa decisión es independiente del cambio decorativo y no se aplica automáticamente con esta entrega. Los registros anteriores conservan sus etiquetas históricas.

## Detalles técnicos

- `Profile.theme`: preferencia persistente por usuario; validada por formulario en servidor, con CSRF y auditoría de cambio sin datos educativos.
- Migración `0003_profile_theme`: añade solo esa columna, con `rpg` como valor inicial. No transforma matrículas, avances o evidencias.
- `core/presentation.py`: relación central entre estados y rarezas. Los filtros de plantilla y el JavaScript utilizan esa misma relación.
- `static/core/rpg.css`: decoración de fantasía original con paneles oscuros, marcos dorados y títulos con tipografía local. No contiene logotipos, personajes, imágenes ni recursos de World of Warcraft ni modifica los recursos oficiales de Atigra.
- `static/core/night.css`: tema oscuro sobrio; `app.css`: base y tema claro.
- Las vistas previas no usan almacenamiento del navegador como base de datos. La preferencia se guarda en servidor solo al confirmar.

## Validación

37 pruebas correctas, incluidas autenticación, CSRF, persistencia de preferencias y aislamiento entre cuentas. Comprobación sobre una copia SQLite anterior a la migración: recuentos de alumnos, aprendizaje, asistencia, matrículas y perfiles conservados. Chromium: los tres estilos guardan y persisten, la vista previa no guarda por sí sola, su cancelación funciona, la leyenda muestra cinco colores y no hay desbordamiento en el historial a 768 px ni errores JavaScript. Contraste de texto de la leyenda: mínimo 5,40:1 en claro y 7,79:1 en ambos temas oscuros. Esto no sustituye una auditoría completa de accesibilidad.
