# Notificaciones, idioma y decoración maker

## Avisos y recordatorios

La campana superior muestra el número de recordatorios pendientes de tu cuenta. Si editas un formulario y dejas cambios sin guardar, añade un aviso de cambios pendientes en esa misma página. La bandeja permite volver al formulario; no muestra valores, notas privadas ni contenido de los campos editados.

**Notificaciones** reúne los recordatorios personales. Puedes crearlos con título y fecha, filtrar pendientes/completados/todos, completarlos o reabrirlos. La fecha vencida se indica con texto; no usa niveles ni colores de aprendizaje. Incluso una cuenta de administración solo ve sus propios recordatorios desde este apartado. No se envían correos ni notificaciones push y no hay avisos programados fuera de la aplicación.

Los cambios sin guardar permanecen únicamente en la página de edición. El aviso no constituye una copia de seguridad ni un borrador almacenado: guarda explícitamente. Si la validación de la clase falla, se conservan los valores recibidos y se sigue mostrando el aviso. Al devolver un campo a su valor original, desaparece el aviso si no quedan otros cambios. El navegador avisa antes de salir; cambiar de idioma con cambios pendientes queda bloqueado hasta que guardes o reviertas esos cambios.

## Idiomas

Selecciona Español o English en la cabecera y pulsa ↵. La preferencia se guarda por cuenta y se reutiliza al entrar desde otro dispositivo. Antes del acceso se utiliza una cookie de idioma. No se admiten otros códigos ni redirecciones a dominios ajenos.

Se traducen etiquetas, instrucciones, menús, estados estándar y mensajes de interfaz. Los nombres, títulos de proyectos, notas, evidencias, recursos y textos personalizados no se traducen automáticamente. Tampoco se reescriben etiquetas históricas en la base de datos. Las fechas mantienen Europe/Madrid; su presentación sigue el idioma seleccionado cuando procede.

El catálogo inglés está en `locale/en/LC_MESSAGES/django.po` y se entrega compilado como `django.mo`. No hay llamadas a servicios externos. Consulta las instrucciones del README para mantenerlo.

## Colores y elementos maker

La escala gris → verde → azul → lila → naranja se utiliza solo para el aprendizaje, no para ordenar recordatorios, asistencia o sesiones. Estos elementos operativos usan una paleta neutra con acento turquesa; los errores se distinguen por texto e indicación magenta. Los temas conservan los mismos significados.

El tema RPG incorpora un libro con circuitos y una herramienta de creación con destellos, mediante SVG originales locales. Son decoración: no cambian las funciones, no evalúan alumnos y no añaden puntos o competiciones. Las leyendas de aprendizaje se muestran en los apartados de aprendizaje y como ejemplo en Personalización.

## Actualización y límites

La versión 0.3.0 añade la migración `0004_profile_language`, que incorpora una preferencia al perfil y conserva datos previos. La reorganización de `core/views.py` en `core/views/` mantiene las rutas. Sigue [Actualizar PythonAnywhere](ACTUALIZAR_PYTHONANYWHERE.md): copia previa, descargar, migrar, recopilar estáticos y recargar. No recrees la demo ni cambies contraseñas.
