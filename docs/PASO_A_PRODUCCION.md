# Paso de demo a producción conservando datos

Cambiar solo `APP_ENV` cambia las rutas por defecto. Para conservar un servicio
existente, fija explícitamente las tres rutas: base educativa, adjuntos privados y
práctica ficticia. El nombre `demo.sqlite3` del archivo no determina el entorno ni
crea datos ficticios; puede conservarse para evitar movimientos durante el cambio.
Este paso endurece la configuración y separa la configuración publicada por entorno;
no certifica seguridad ni sustituye las revisiones de `SECURITY.md`.

## Antes de cambiar

1. Copia y comprobación de restauración con el entorno actual. Conserva una copia
   privada del WSGI actual para volver atrás; nunca la subas al repositorio.
2. Revisa configuraciones publicadas de demo: no se aplican automáticamente en
   producción. Si hay alguna, revisa y publica su configuración declarativa en
   producción por el proceso de borrador/vista previa/publicación. No cambies el
   entorno de los registros antiguos ni borres el historial.
3. Actualiza el repositorio: debe admitir `PRIVATE_MEDIA_ROOT` y
   `PRACTICE_DATABASE_PATH`. Verifica el manifiesto sin regenerarlo en el servidor.
4. Verifica que DATABASE_PATH del WSGI apunta al archivo existente. No cambies ni
   copies bases educativas con el servicio escribiendo. Mantén HTTPS y la clave
   privada existente, sin mostrar su contenido.

## WSGI de la instalación actual en PythonAnywhere

Antes de cargar Django, mantén estas rutas (el usuario que está configurando esta
instalación es `pablete97`; adapta la ruta en otras instalaciones):

```python
os.environ['APP_ENV'] = 'production'
os.environ['DATABASE_PATH'] = project + '/var/demo.sqlite3'
os.environ['PRIVATE_MEDIA_ROOT'] = project + '/var/private/demo'
os.environ['PRACTICE_DATABASE_PATH'] = project + '/var/practice/demo.sqlite3'
os.environ['DEBUG'] = '0'
os.environ['HTTPS_ONLY'] = '1'
```

Mantén `ALLOWED_HOSTS` y la lectura del archivo de clave existente. No reemplaces
la clave por un ejemplo. Guarda y recarga solo después de revisar las rutas.
No se necesita migración ni copiar expedientes para cambiar estas variables.
Si algo falla, vuelve al WSGI anterior y recarga; este cambio de entorno por sí
solo no borra ni transforma registros.

## Consola con exactamente la misma configuración

Las variables del WSGI **no se heredan en Bash**. En cada consola nueva, antes de
administrar el servicio, configura lo mismo sin imprimir la clave:

```bash
cd ~/ATIPLATFORM
export APP_ENV=production
export DEBUG=0
export HTTPS_ONLY=1
export ALLOWED_HOSTS=pablete97.pythonanywhere.com
export DATABASE_PATH=/home/pablete97/ATIPLATFORM/var/demo.sqlite3
export PRIVATE_MEDIA_ROOT=/home/pablete97/ATIPLATFORM/var/private/demo
export PRACTICE_DATABASE_PATH=/home/pablete97/ATIPLATFORM/var/practice/demo.sqlite3
export DJANGO_SECRET_KEY="$(cat /home/pablete97/.atigra-demo-secret)"
```

No uses `echo`, `env`, `printenv`, `set` ni `diffsettings` para compartir resultados:
pueden mostrar secretos. No pegues el contenido del archivo de clave en incidencias.
Tras exportar estas variables, los comandos ya no llevan el prefijo `APP_ENV=demo`:

```bash
.venv/bin/python manage.py check --deploy
.venv/bin/python manage.py security_manifest --check
.venv/bin/python manage.py security_scan
.venv/bin/python manage.py backup
```

El informe de seguridad de demo no se reutiliza: hay que generar el de producción.
Las futuras copias quedan en `var/backups/production`, tomando la BD y los adjuntos
existentes de las rutas explícitas. La práctica mantiene su base independiente y
no forma parte de la copia educativa. No ejecutes el comando `demo` contra datos reales.

## Verificar después

- El panel indica producción y la configuración segura prevista.
- Se conserva el número de alumnos y el grupo que ya existía, sin modificarlos.
- Se puede consultar una sesión y descargar una evidencia privada autorizada.
- La práctica ficticia mantiene sus avances separados.
- Los análisis de producción aparecen vigentes, la copia se comprueba y los permisos
  siguen denegando accesos ajenos. Registrar como pendientes las comprobaciones que
  no puedan hacerse (por ejemplo, si aún no hay una evidencia adjunta).

No cambies después DATABASE_PATH por `production.sqlite3` sin un procedimiento
independiente de copia coherente, parada de escritores, validación y recuperación.
