# Guía paso a paso para entrar

## 1. Distingue dónde se ejecuta la aplicación

El repositorio contiene el programa y la documentación. GitHub no ejecuta la plataforma ni es una pantalla de acceso a ella. Publicar una configuración de entorno de Codex tampoco equivale a desplegar una web pública.

El servidor preparado durante el desarrollo se ejecuta dentro del entorno cloud. Su puerto 8000 se ha comprobado desde esa máquina. Escribir `localhost` en tu ordenador apunta a tu ordenador, no a esa máquina cloud. Este entorno de onboarding no proporciona una vista previa web pública que podamos dar por disponible.

Elige una vía:

- **Tienes el proyecto en tu ordenador:** sigue el apartado 2 y accede con tu navegador al servidor que ejecutes allí.
- **Solo tienes GitHub/Codex en el navegador:** no hay todavía una dirección pública de la aplicación. Primero necesitas obtener una copia del proyecto para ejecutarla localmente, usar un túnel privado autorizado que tu herramienta admita o preparar un despliegue de pruebas con HTTPS. No introduzcas datos reales para esta prueba.
- **Ya tienes un despliegue autorizado:** usa su dirección HTTPS y las cuentas creadas en ese despliegue. Los usuarios demo del entorno cloud no existen automáticamente en otra base de datos.

La copia que uses debe incluir `manage.py`, `requirements.txt`, `config/`, `core/` y `templates/`. Los cambios locales de Codex no aparecen en GitHub hasta que se hayan incorporado a Git y enviado al remoto. Si solo ves LICENSE y README, todavía no tienes el código de la aplicación.

## 2. Prepara una demostración local

Necesitas Python 3.12 o posterior y la copia completa del proyecto. Los comandos siguientes son para Bash en Linux, macOS o WSL. En Windows sin WSL, las rutas de ejecutables y la configuración de variables cambian.

Abre una terminal y entra en la carpeta del proyecto. En la máquina cloud la ruta es:

```sh
cd /workspace/ATIPLATFORM
```

En tu ordenador utiliza la ruta donde esté tu copia. Después:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export APP_ENV=demo
.venv/bin/python manage.py migrate --noinput
```

Mantén `APP_ENV=demo` en esta terminal durante toda la prueba. La base de datos será `var/demo.sqlite3`; los archivos privados estarán en `var/private/demo/`. No exportes `DATABASE_PATH` apuntando a datos reales.

### Si aún no existen los usuarios y registros ficticios

```sh
read -r -s -p 'Elige contraseña demo (mínimo 12 caracteres): ' DEMO_PASSWORD
printf '\n'
export DEMO_PASSWORD
.venv/bin/python manage.py demo
unset DEMO_PASSWORD
```

La contraseña no se muestra mientras escribes. No la envíes al chat ni la añadas a archivos del repositorio. Este comando crea los usuarios demo y los datos ficticios una sola vez. Si indica que ya existen, no los sobrescribe ni modifica sus contraseñas.

### Si la demostración ya existe y necesitas elegir otra contraseña

```sh
APP_ENV=demo .venv/bin/python manage.py changepassword demo.admin
```

Escribe la nueva contraseña dos veces. Es normal que no aparezcan letras ni asteriscos. Este comando modifica únicamente la cuenta indicada dentro de la base demo. Para la prueba posterior de permisos, puedes elegir también una contraseña para `demo.docente` y `demo.desarrollo` usando el mismo comando con cada nombre.

## 3. Arranca el servidor

En la misma terminal:

```sh
APP_ENV=demo .venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
```

Deja esta terminal abierta. Para detener únicamente este servidor, pulsa Ctrl+C en esa terminal. Si el puerto ya está ocupado por tu servidor de pruebas, úsalo; no arranques otro ni detengas un proceso que no reconozcas. Como alternativa, cambia el puerto a 8001 y usa ese mismo puerto en el navegador.

En el navegador **del ordenador donde has arrancado el servidor**, introduce la dirección `http://127.0.0.1:8000/login/`. Esta es una dirección local de desarrollo, no una dirección pública de la instancia cloud.

## 4. Inicia sesión

1. Usuario: `demo.admin`.
2. Contraseña: la que acabas de elegir para esa cuenta.
3. Pulsa **Entrar a la plataforma**.
4. Comprueba que aparece Inicio y que el indicador superior dice **DEMO**.
5. Abre **Alumnado**. Deben aparecer `Persona ficticia 01` y `Persona ficticia 02`.

Si el indicador no dice DEMO, no continúes con las pruebas: comprueba el proceso y la base de datos que estás utilizando.

Las cuentas tienen funciones distintas:

| Cuenta | Uso en la prueba |
| --- | --- |
| `demo.admin` | Preparar y revisar la prueba como administración. Tiene permisos adicionales explícitos en la demo. |
| `demo.docente` | Registrar clases de sus grupos. No tiene acceso a información restringida ni a Desarrollador. |
| `demo.desarrollo` | Configuración de desarrollo. No tiene acceso educativo al alumnado. |

No hay acceso de alumnos ni familias en esta versión.

## 5. Resuelve problemas de acceso

| Síntoma | Comprobación |
| --- | --- |
| No se abre la página | Confirma que el servidor sigue ejecutándose y que navegador y servidor están en la misma máquina, o que usas un acceso remoto autorizado. |
| Aparece un error de usuario/contraseña | Restablece la contraseña en `APP_ENV=demo`; no asumas que recrear la demo la cambia. |
| Usuario inexistente | Comprueba que cargaste la demo en esa misma copia/base de datos. |
| `DisallowedHost` | Para un dominio autorizado distinto, configura su nombre exacto en `ALLOWED_HOSTS`. No habilites `*` como solución general. |
| No aparecen los alumnos ficticios | Comprueba `APP_ENV=demo` y que `DATABASE_PATH` no apunta a otra base. |
| Solo ves código en GitHub | Falta ejecutar o desplegar la aplicación; el repositorio no es el servicio web. |
| No hay terminal en la herramienta que utilizas | Necesitamos elegir una vía de ejecución local o un despliegue de pruebas; una contraseña no soluciona la ausencia de servidor accesible. |

Cuando hayas entrado y veas DEMO, continúa con la [prueba de dos alumnos](PRUEBA_DOS_ALUMNOS.md).
