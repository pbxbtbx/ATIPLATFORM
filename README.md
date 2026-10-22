# Atigra Makers

Plataforma interna de gestión educativa con interfaz en español e inglés. Django 5.2 LTS, SQLite con transacciones y migraciones, plantillas renderizadas en servidor y archivos privados. Esta arquitectura evita dependencias externas para los flujos diarios y mantiene centralizada la autorización. La base de datos y los archivos se conservan en `var/`, nunca en el navegador. Los archivos se separan por `var/private/<APP_ENV>/` y las bases por entorno (`db.sqlite3` en desarrollo; `demo.sqlite3`, `staging.sqlite3`, `production.sqlite3`, etc.).

## Guías de uso

- [Cómo entrar paso a paso](docs/ACCESO.md).
- [Prueba guiada con dos alumnos ficticios](docs/PRUEBA_DOS_ALUMNOS.md).
- [Notificaciones e idiomas](docs/NOTIFICACIONES_IDIOMAS.md).
- [Personalización y colores del aprendizaje](docs/PERSONALIZACION.md).
- [Actualizar PythonAnywhere](docs/ACTUALIZAR_PYTHONANYWHERE.md).
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

## Instrucciones de uso diario

1. **Entra con tu cuenta interna** y comprueba el entorno visible. Para aprender a usar la aplicación, trabaja en DEMO con registros ficticios.
2. **Abre Inicio o Calendario**, elige la sesión y consulta objetivos, materiales y planificación.
3. **Pasa asistencia y registra el aprendizaje individual**. La actividad realizada y el aprendizaje demostrado tienen estados separados. La escala de colores solo representa aprendizaje; los avisos operativos usan un acento neutro turquesa.
4. **Guarda el borrador o cierra la clase**. Si cambias un campo, la campana y el aviso de esa misma página indican que queda trabajo sin guardar. No hay autoguardado ni sincronización de borradores entre pestañas.
5. **Abre Notificaciones** para crear recordatorios personales, consultar pendientes/completados, marcarlos como terminados o reabrirlos. No incluyas información sensible en sus títulos.
6. **Prepara informes** con selección de apartados y revisa la vista previa antes de descargar. No se envía nada automáticamente.
7. **Elige tu estilo en Personalización**. El tema RPG usa libros de circuitos y una herramienta de creación con destellos, dibujados localmente; son decorativos. Los otros temas mantienen los mismos flujos y datos.
8. **Cambia el idioma en el selector superior** y pulsa ↵ para aplicarlo. Español e inglés se guardan por cuenta; la pantalla de acceso también permite elegir idioma. Guarda los formularios antes de cambiar. La interfaz se traduce localmente; los nombres, notas, recursos y evidencias del alumnado no se envían a servicios de traducción ni se reescriben.

## División modular del proyecto

Las rutas se mantienen estables en `config/urls.py`. `core/views/` sustituye el antiguo archivo único de vistas; su `__init__.py` conserva los nombres públicos para las rutas. Cada área se puede revisar sin editar el resto de vistas.

| Módulo / carpeta | Responsabilidad | Dónde mirar primero para corregirlo |
| --- | --- | --- |
| `core/views/dashboard.py` | Inicio y accesos a tareas | `templates/core/home.html` |
| `core/views/groups.py` | Grupos y sus fichas | `ClassGroup`, `GroupForm`, `templates/core/page.html` |
| `core/views/students.py` | Alumnado, responsables, matrículas, información restringida y exportación | `Student`, `Enrollment`, `GuardianLink`, `RestrictedNote`, `core/access.py` |
| `core/views/planning.py` | Calendario, recurrencias, asistencia y modo clase | `core/services.py`, `templates/core/calendar.html`, `templates/core/session.html` |
| `core/views/library.py` | Recursos y secuencias con copia histórica | `Resource`, `Sequence`, `snapshot()` |
| `core/views/evidence.py` | Subidas privadas y descargas autorizadas | `Evidence`, validación de archivos y permisos |
| `core/views/reports.py` | Informes familiares e internos, PDF y CSV | `templates/core/reports.html`, `templates/core/group_report.html` |
| `core/views/notifications.py` | Recordatorios privados, filtros y completar/reabrir | `Task`, `templates/core/notifications.html`, `notification_tray.html` |
| `core/views/appearance.py` | Preferencia de estilo por cuenta | `Profile.theme`, `appearance.html`, `app.css`, `rpg.css`, `night.css` |
| `core/views/language.py` | Cambio seguro de idioma por cuenta o cookie de acceso | `Profile.language`, `UserLanguageMiddleware`, `locale/en/` |
| `core/views/administration.py` | Cursos, festivos, usuarios y permisos | `core/forms.py`, `core/access.py` |
| `core/views/development.py` | Configuración versionada, diagnóstico, vistas previas y restauración | `core/configuration.py`, `developer.html`, `preview.html` |
| `core/views/common.py` | Helpers compartidos de renderizado y edición | Solo cambiarlo cuando el comportamiento deba ser común a varias áreas |
| `core/models.py` + `core/migrations/` | Entidades, relaciones y evolución de la base de datos | No renombrar tablas para reorganizar pantallas; preparar migraciones versionadas |
| `core/access.py` | Permisos y alcance por usuario/grupo | Toda nueva vista debe aplicar autorización en servidor |
| `core/services.py` | Validación de sesiones, copias históricas, traslados y control de versión | Reutilizarlo al añadir mutaciones |
| `core/presentation.py` + `core/templatetags/` | Escala visual del aprendizaje y etiquetas de presentación | No cambiar datos ni permisos para cambiar colores |
| `static/core/drafts.js` | Cambios sin guardar, guardado fallido, aviso de conexión y bloqueo de cambio de idioma con cambios pendientes | Estado solo en memoria de esa página; sin localStorage |
| `static/core/notifications.js` | Comportamiento accesible de la bandeja de la campana | Cierre exterior y Escape; sin lecturas de datos privados |
| `static/core/operations.css` | Notificaciones, avisos, elementos maker y paleta operativa | Mantenerla separada de la escala de aprendizaje |
| `templates/core/maker_symbols.html` | Libro de circuitos y herramienta con destellos | SVG originales decorativos, sin logotipos o personajes de terceros |
| `locale/en/LC_MESSAGES/` | Traducciones de interfaz | Editar `django.po` y recompilar `django.mo` |
| `core/tests.py` | Pruebas operativas, de privacidad y regresión | `PlatformTests`, `AppearanceTests`, `NotificationTests`, `LanguageTests` |

Los modelos y formularios compartidos permanecen en sus archivos actuales para conservar las relaciones y el historial de migraciones. La separación por áreas no crea bases de datos independientes ni cambia identificadores.

## Cómo centrarse en una corrección

1. Localiza el módulo en la tabla. Por ejemplo, para una campana incorrecta revisa `core/context.py`, `notification_tray.html` y `drafts.js`; para un error al guardar la clase, `planning.py` y `services.py`.
2. Determina si es presentación, validación, permisos o persistencia. Cambiar una plantilla no debe modificar entidades educativas.
3. Añade o ejecuta una prueba del caso y otra que compruebe el acceso de un usuario sin permiso cuando corresponda.
4. Ejecuta las comprobaciones, revisa el cambio y despliega primero en pruebas con copia previa si hay migración.

```sh
.venv/bin/python manage.py test core.tests.NotificationTests
.venv/bin/python manage.py test core.tests.LanguageTests
.venv/bin/python manage.py test
.venv/bin/python manage.py makemigrations --check --dry-run
```

## Mantener las traducciones

La aplicación usa los catálogos locales de Django, sin servicios de traducción. Los textos nuevos se marcan con `gettext`, `gettext_lazy` o `{% translate %}`. Para palabras ambiguas se usa contexto: «Inicio» del menú es Home, pero el inicio de una sesión es Start. Los códigos de estado y confirmaciones (`PUBLICAR`, `RESTAURAR`, `EXPORTAR`) permanecen estables; las instrucciones explican qué escribir en ambos idiomas.

Añade o actualiza una entrada `msgid`/`msgstr` en el `.po` para cada texto nuevo de interfaz. Para editar y compilar catálogos en desarrollo:

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/compile_translations.py
```

Versiona tanto `django.po` como `django.mo`. El archivo compilado se entrega en el repositorio: **no necesitas instalar gettext ni polib en PythonAnywhere para ejecutar la aplicación**. Las dependencias de producción siguen en `requirements.txt`.
