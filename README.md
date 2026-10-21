# Atigra Makers

Plataforma interna de gestión educativa en español. Django 5.2 LTS, SQLite con transacciones y migraciones, plantillas renderizadas en servidor y archivos privados. Esta arquitectura evita dependencias externas para los flujos diarios y mantiene centralizada la autorización. La base de datos y los archivos se conservan en `var/`, nunca en el navegador. Los archivos se separan por `var/private/<APP_ENV>/` y las bases por entorno (`db.sqlite3` en desarrollo; `demo.sqlite3`, `staging.sqlite3`, `production.sqlite3`, etc.).

## Guías de uso

- [Cómo entrar paso a paso](docs/ACCESO.md).
- [Prueba guiada con dos alumnos ficticios](docs/PRUEBA_DOS_ALUMNOS.md).
- [Índice de documentación](docs/README.md).

## Instalación y primera cuenta

Requiere Python 3.12 o posterior. Desde `/workspace/ATIPLATFORM`:

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py init_admin --username administracion --development --sensitive
.venv/bin/python manage.py runserver 0.0.0.0:8000
```

El comando solicita la contraseña sin mostrarla. `--development` y `--sensitive` conceden explícitamente permisos adicionales; omítelos cuando no correspondan. No hay contraseñas universales, registro público ni acceso de familias/alumnos. Configura el nombre de dominio en `ALLOWED_HOSTS` antes de acceder desde un dominio distinto. El servidor de desarrollo no es un despliegue de producción.

## Demostración aislada

Todos los nombres, lugares, actividades y horarios de esta demostración son ficticios. El comando rechaza el uso en otro entorno y nunca sobrescribe datos existentes. Usa una base de datos independiente `var/demo.sqlite3`; no crees datos demo en producción.

```sh
export APP_ENV=demo
.venv/bin/python manage.py migrate
read -s -p 'Contraseña de demostración (mínimo 12 caracteres): ' DEMO_PASSWORD
export DEMO_PASSWORD
.venv/bin/python manage.py demo
unset DEMO_PASSWORD
.venv/bin/python manage.py runserver 0.0.0.0:8001
```

Usuarios `demo.admin`, `demo.docente`, `demo.desarrollo`, con la contraseña elegida. El tercero no puede acceder a alumnado, aunque tenga acceso a Desarrollador. Para volver al entorno sin datos ficticios: `unset APP_ENV`.

## Flujo de trabajo

1. Administración crea curso académico, usuarios y grupos; asigna docentes/coordinación a cada grupo.
2. Crea alumnado y responsables compartidos, y vincula matrículas con fechas desde la ficha individual.
3. Prepara recursos de biblioteca y sesiones (hasta 52 repeticiones semanales). Se rechazan conflictos de grupo/docente y festivos; la serie se crea completa o no se crea.
4. Abre una clase desde Inicio o Calendario, pasa asistencia, selecciona alumnos para añadir avances y personaliza evidencias, apoyos y próximos pasos. Guarda borrador o cierra la sesión. Los borradores se guardan explícitamente en servidor; hay aviso de cambios pendientes y desconexión.
5. Los estados de actividad y aprendizaje son independientes. Las revisiones añaden registros y conservan anteriores. La fecha no cambia el aprendizaje automáticamente.
6. Informes filtra alumno, grupo, ámbito y periodo; selecciona apartados y revisa la vista previa antes de exportar PDF o CSV. No se envían informes automáticamente.
7. Desarrollador permite borrador → vista previa validada → publicación de configuración. Restaurar crea un nuevo borrador, sin tocar datos educativos.

La configuración admite colores, fuentes permitidas, recurso oficial local para logotipo, textos de navegación, orden de menús, activación de Biblioteca/Informes, indicador `rubrics`, plantillas de sesión e informe, rúbricas y campos personalizados de ficha (`text` o `choice`, obligatorios/opcionales). No ejecuta código. Los campos retirados conservan valores previos. Las etiquetas admiten navegación, título de inicio, botón de guardado y etiquetas/ayudas de campos con claves `<modelo>.<campo>.label` y `<modelo>.<campo>.help`.

## Comprobaciones

```sh
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py test
.venv/bin/python manage.py backup
```

Las pruebas usan una base de datos temporal y registros ficticios. Cubren permisos en servidor/interfaz, protección CSRF, ritmos distintos, revisión del aprendizaje, recuperación de sesiones, cambios de recurrencia, conflictos, festivos, traslados, hermanos, informes, copia histórica, concurrencia, archivos y configuración.

Consulta [operación y privacidad](docs/OPERATIONS.md), [extensión y migraciones](docs/EXTENDING.md) y [alcance de esta versión](docs/SCOPE.md). Las instrucciones de esta documentación se ejecutan en la copia existente del repositorio; no hace falta crear un worktree.
