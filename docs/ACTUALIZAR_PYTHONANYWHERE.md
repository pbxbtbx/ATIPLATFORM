# Actualizar PythonAnywhere: práctica y accesibilidad (0.7.0)

Esta entrega añade práctica con dos aprendices ficticios en una base separada, cinco bloques de progreso, preferencias de accesibilidad por cuenta y ayudas de voz local bajo demanda. Conserva las importaciones, retos y datos existentes.

## 1. Copia de seguridad previa

En **Consoles**, abre tu consola **Bash** y ejecuta:

```sh
cd ~/ATIPLATFORM
APP_ENV=demo .venv/bin/python manage.py backup
```

Debe indicar que la copia y restauración de comprobación son correctas. Si falla, resuelve el error antes de continuar. La copia es local a la cuenta; no sustituye una copia externa para producción.

## 2. Descargar la actualización

```sh
git pull --ff-only
```

Si Git indica cambios locales o no puede avanzar, detente y revisa el mensaje. No uses reset, clean ni fuerces la actualización. El archivo WSGI y la clave privada se configuraron fuera del checkout y no se sustituyen con estos comandos.

## 3. Actualizar la estructura de la base de datos

```sh
APP_ENV=demo .venv/bin/python manage.py migrate --noinput
```

Debe aparecer `0008_challengeprogress_content_area_learning_content_area_and_more` seguida de `OK`. Añade preferencias de accesibilidad y clasificación de ámbito sin modificar aprendizajes anteriores. Si faltan otras migraciones, se aplicarán también. La práctica crea su archivo SQLite separado al abrirla; no tienes que ejecutar SQL manualmente. Las preferencias de estilo y los datos educativos se conservan. No recargues la web antes de completar la migración. Si aparece un error, detente y conserva la copia anterior.

## 4. Actualizar los archivos de diseño

```sh
APP_ENV=demo .venv/bin/python manage.py collectstatic --noinput
```

Actualiza `staticfiles/`. No borra la base de datos ni los archivos privados. No es necesario repetir `demo`, crear usuarios, reinstalar dependencias ni cambiar contraseñas.

## 5. Recargar la web

1. Entra en la pestaña **Web** de PythonAnywhere.
2. Pulsa el botón verde **Reload**.
3. Abre la plataforma con HTTPS y pulsa **Ctrl+F5**.
4. Comprueba que el pie muestra **v0.7.0**, que Calendario muestra **Importar sesiones / Word** y que Personalización permite **Básicos** o **RPG**.
5. Comprueba los nuevos accesos **Accesibilidad** y **Práctica ficticia**.
6. Sigue [la prueba de dos aprendices ficticios](PRACTICA_ACCESIBILIDAD.md), sin abrir la clase real para ensayar logros.

## 6. Comprobar y continuar la prueba

- Abre Notificaciones y prueba un recordatorio ficticio; complétalo y reábrelo.
- Edita un formulario sin guardarlo y comprueba el aviso de la campana. Revierte o guarda antes de salir.
- Selecciona English y pulsa ↵; vuelve a Español cuando quieras. Los contenidos que escribiste no cambian.
- Abre Personalización y comprueba que tu estilo anterior se conserva.
- Abre Alumnado → Persona ficticia 01 → Aprendizaje y comprueba la separación de clases y los colores.
- Verifica que se conservan los avances y la asistencia de los dos alumnos de la prueba. Cambiar el estilo no completa objetivos ni modifica notas.
- La actualización no cierra la clase ni crea avances. Podemos continuar donde se dejó: registrar lo realizado, cerrar la sesión y revisar los informes familiares.

Más información: [Notificaciones e idiomas](NOTIFICACIONES_IDIOMAS.md), [Personalización](PERSONALIZACION.md) y [mapa modular del README](../README.md).

## Recuperación ante una actualización fallida

Conserva la ruta de la copia indicada en el paso 1 y anota el mensaje de error sin contraseñas. No sustituyas la base mientras el servicio esté escribiendo. Sigue el procedimiento de [operación y recuperación](OPERATIONS.md): detener escritores, verificar la copia, restaurar sobre una ruta nueva y utilizar código compatible antes de devolver el tráfico. Si solo quieres cambiar la apariencia, usa Personalización y guarda Atigra claro; no necesitas revertir la base de datos.

## Actualización 0.8.0: panel de ciberseguridad

Realiza la copia previa habitual. Después de `git pull --ff-only`, instala
`.venv/bin/python -m pip install -r requirements.txt` (nuevo analizador XML seguro).
Esta actualización no añade migraciones; puedes ejecutar el migrate habitual.
Recoge estáticos y recarga Web. Entra en Desarrollador → Abrir panel de ciberseguridad.

Para disponer de análisis locales recientes, instala `requirements-security.txt`
y ejecuta `APP_ENV=demo .venv/bin/python manage.py security_scan` desde consola.
La web no inicia análisis. Si la red del plan gratuito los impide, queda pendiente
y el comando termina con error explícito. No regeneres el manifiesto descargado.
Lee [SECURITY.md](SECURITY.md) para revisar DEBUG, HTTPS y la transición segura de
demo a producción **antes de seguir registrando datos reales**. No cambies de
entorno sin fijar las rutas de la BD y los adjuntos existentes.
