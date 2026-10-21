# Actualizar el diseño en PythonAnywhere

Esta actualización añade colores de estado y separa las clases del historial de Aprendizaje en tarjetas con fecha, sesión y bordes. Distingue observaciones, acompañamiento, próximos pasos y notas internas. Los estados conservan su texto: el color es una ayuda adicional. No modifica el esquema de base de datos ni los registros de la prueba.

## 1. Descargar la actualización

En PythonAnywhere, abre Consoles y tu consola Bash. Ejecuta:

```sh
cd ~/ATIPLATFORM
git pull --ff-only
```

Si Git indica que hay cambios locales o no puede avanzar, detente y revisa el mensaje. No uses reset, clean ni fuerces la actualización. El archivo WSGI y la clave privada se configuraron fuera del checkout y no se sustituyen con estos comandos.

## 2. Actualizar los archivos de diseño

```sh
APP_ENV=demo .venv/bin/python manage.py collectstatic --noinput
```

Este comando actualiza `staticfiles/`. No borra la base de datos ni los archivos privados. No es necesario repetir `demo`, crear usuarios o cambiar contraseñas. Esta entrega solo cambia plantillas, CSS y JavaScript: no tiene migraciones nuevas.

## 3. Recargar la web

1. Entra en la pestaña Web.
2. Selecciona tu aplicación y pulsa el botón verde Reload.
3. En el navegador, abre la plataforma con HTTPS.
4. Pulsa Ctrl+F5 para recargar el diseño.

## 4. Comprobar el resultado

1. Abre Alumnado → Persona ficticia 01 → Aprendizaje.
2. Cada registro debe aparecer en una tarjeta con borde, fecha de clase y título de sesión.
3. Comprueba las etiquetas de texto y color: sin iniciar gris, en proceso ámbar, completado con apoyo azul, completado con autonomía verde y pendiente de retomar violeta. Los estados personalizados sin color específico utilizan un estilo neutro.
4. Comprueba que se conservan los avances registrados durante la prueba y que las notas internas siguen siendo individuales.
5. Abre la sesión: los bloques de alumno y los selectores de progreso deben mostrar también sus estados diferenciados.

La actualización no cierra la clase ni crea nuevos avances. Podemos continuar la prueba donde se dejó: guardar lo realizado, cerrar la sesión y revisar los informes familiares.

## Validación de esta entrega

- `manage.py check`: sin incidencias.
- Tres pruebas existentes de renderizado de pantallas, permisos y exclusión de datos sensibles en informes: correctas.
- Chromium: dos registros históricos visibles en tarjetas separadas; colores distintos de estado; selector actualiza el color al cambiar de estado; diseño a 768 px sin desbordamiento en el historial; sin errores JavaScript.
- No se ha actualizado automáticamente la instancia de PythonAnywhere: requiere los pasos anteriores en tu cuenta.
