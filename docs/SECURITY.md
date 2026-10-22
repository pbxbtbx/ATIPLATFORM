# Integridad, ciberseguridad y diagnóstico

Disponible en **Desarrollador → Abrir panel de ciberseguridad**. Requiere el permiso
explícito `development_access` en el servidor, incluso para administración y
superusuarios. Ese permiso no otorga acceso a expedientes ni información restringida.
Consultar el panel registra usuario y fecha en auditoría. La respuesta es privada,
sin caché, y no admite POST, comandos, cargas, consultas SQL ni scripts.

## Qué comprueba

- Configuración real del proceso: DEBUG, clave propia sin mostrarla, hosts, HTTPS,
  cookies, HSTS, CSRF, cabeceras y entorno. Comprueba también que los paquetes
  instalados coincidan con las versiones exactas de `requirements.txt`.
- SHA-256 de código, plantillas, recursos, traducciones, scripts, dependencias y CI,
  contra `security-manifest.json` versionado. Detecta archivos nuevos, modificados
  y ausentes en esos directorios; rechaza enlaces simbólicos y archivos excesivos.
  No lee `var`, bases educativas, adjuntos, `.env`, copias ni credenciales.
- Bandit: patrones inseguros en Python de aplicación y scripts, excluidas pruebas
  y migraciones. Las excepciones `nosec` son puntuales, comentadas y revisables:
  placeholder local rechazado en producción, ejecución fija solo por consola,
  escape de salida PDF sin analizar XML, y fallo de telemetría sin ocultar excepción.
- pip-audit: avisos públicos de vulnerabilidades para **todas las dependencias de
  ejecución declaradas**, incluidas transitivas fijadas. No analiza el SO, proxy,
  navegador, herramientas del analizador, dependencias JavaScript ni imágenes del host.
- Fecha de una copia cuya restauración SQLite fue comprobada. Advertencia tras 7 días;
  no verifica en cada visita que los archivos sigan existiendo ni recupera producción.
- Hasta 20 referencias de incidencias sin trazas, mensajes, URLs, cuerpos, nombres o
  secretos. Es diagnóstico seguro, no un depurador interactivo.

Los resultados de analizadores son locales, privados y agregados. El panel solo acepta
esquema y estados conocidos, números acotados, el mismo entorno, código sin diferencias,
la huella del manifiesto actual y una fecha de las últimas **24 horas**. Ausencia,
JSON corrupto, permisos insuficientes, fallo de red, herramienta ausente y caducidad
se muestran como pendientes/no comprobados, nunca como seguridad superada. Renovar
el análisis no está disponible desde la web.

## Ejecutar análisis

En un checkout revisado con Python 3.12 y entorno virtual. No instalar herramientas
por peticiones HTTP. No introducir datos reales para ejecutar estas comprobaciones.

```bash
.venv/bin/python -m pip install -r requirements-security.txt
.venv/bin/python manage.py security_scan
```

En PythonAnywhere utiliza el mismo `APP_ENV` que usa el WSGI, actualmente `demo`:

```bash
APP_ENV=demo .venv/bin/python manage.py security_scan
```

`pip-audit` consulta PyPI enviando nombres y versiones de paquetes; no envía expedientes,
archivos de alumnos ni el código. Puede fallar en alojamientos gratuitos que restringen
salidas de red: en ese caso queda **no comprobado**. Bandit analiza código localmente.
Cada herramienta tiene límite de 180 segundos. Código de salida distinto de cero en
el comando combinado significa que hace falta revisión, no que haya aprobado.

El informe resumido se escribe atómicamente con permiso 0600 en
`var/security/<entorno>.json`, fuera de estáticos. La caché contiene solo metadatos
públicos de dependencias. No copiar informes entre entornos, no subirlos desde la web.
El informe del despliegue se genera en ese despliegue; un análisis de CI no certifica
la configuración del servidor ni se importa automáticamente.

Para investigar hallazgos en un entorno controlado, ejecuta directamente:

```bash
.venv/bin/python -m bandit -r core config scripts -x core/migrations,core/test -f json
.venv/bin/python -m pip_audit -r requirements.txt --no-deps --disable-pip --cache-dir var/security/audit-cache -f json
```

Estos comandos muestran detalles técnicos del código, por lo que sus resultados deben
permanecer en manos de mantenedores. No pegues trazas con datos reales en incidencias.
Revisa cada hallazgo; no añadas exclusiones globales ni actualices dependencias sin
pruebas. Actualizar versiones también exige volver a generar y revisar el manifiesto.

## Proceso de repositorio y publicación

1. Rama y cambios revisados. Pruebas con datos sintéticos. Actualiza documentación y
   traducciones. Nunca pruebes restauraciones sobre el servicio educativo.
2. Ejecuta pruebas, revisión estática y de dependencias. Al terminar los cambios:
   `.venv/bin/python manage.py security_manifest`. **Revisa su diff** junto con el código;
   no regeneres el manifiesto en producción para esconder diferencias inesperadas.
3. Versiona código y manifiesto en el mismo commit. GitHub Actions comprueba el
   manifiesto, las pruebas y los analizadores en pushes, PR, diariamente y manualmente.
   Configura protección de `main`, revisión obligatoria y estos checks requeridos en
   GitHub; el fichero workflow por sí solo no impide un merge. No hay despliegue automático.
4. Copia previa y restauración de comprobación, actualización de paquetes, migraciones
   si las hay, estáticos y recarga. Ejecuta `security_scan` en el entorno desplegado.
5. Comprueba permisos, inicio de sesión, estado del panel y un flujo ficticio. Ante
   cambios inesperados conserva evidencias mínimas, compara con un checkout confiable
   y prepara rollback; no sobrescribas el manifiesto local sin investigar.

El manifiesto **no está firmado**: un atacante que controle código y manifiesto puede
alterar ambos. Los resultados locales tampoco son una atestación independiente de un
host comprometido. Para mayor garantía quedan pendientes firma/procedencia de artefactos,
verificación externa, revisión humana y protección de GitHub. No cubre `.env`, permisos
del SO, ficheros fuera del alcance ni integridad continua de la base educativa.

## Configuración pública y menores

No cambies `APP_ENV=demo` a `production` sin un plan: las rutas predeterminadas de BD y
archivos dependen del entorno y podrías abrir una base vacía. Antes de ese paso fija
rutas privadas correctas, copia, verifica restauración y revisa las credenciales.
Para endurecer el despliegue actual sin mover datos, configura en WSGI **antes de
cargar Django** `DEBUG=0`, `HTTPS_ONLY=1`, un `DJANGO_SECRET_KEY` aleatorio y privado de
al menos 50 caracteres y `ALLOWED_HOSTS` con el dominio exacto. Nunca publiques ni pegues
la clave; cambiar una clave existente invalida sesiones. `HTTPS_ONLY` activa cookies
seguras, redirección HTTPS y HSTS: probar exclusivamente en un dominio con TLS correcto.
No confíes en `X-Forwarded-Proto` sin comprobar el proxy del proveedor. No activar en
localhost HTTP. `demo` y `staging` ahora desactivan DEBUG por defecto, pero una variable
`DEBUG=1` explícita lo vuelve a activar y debe corregirse.

Pendientes antes de considerar un despliegue adecuado para datos reales: auditoría
independiente de autorización y almacenamiento, MFA en hosting/GitHub y cuentas
privilegiadas, protección contra fuerza bruta (no implementada en este cambio), gestión
y rotación de secretos, cabeceras/CSP y TLS comprobados desde fuera, actualización del
SO por proveedor, copias cifradas fuera del host y simulacro completo, revisión de
conservación/permisos y acuerdos del alojamiento. No se afirma cumplimiento normativo
ni certificación de seguridad por disponer de este panel.

## Incidentes y debug

Ante sospecha de acceso indebido, limita el acceso y activa mantenimiento si procede,
revoca sesiones y rota credenciales desde canales de administración confiables.
Mantenimiento por sí solo no bloquea login ni revoca sesiones existentes. Conserva
referencia, hora y versión mínima, restringe evidencias y evita copiar contenido de
menores. Investiga en una copia sintética aislada; no habilites DEBUG ni un depurador
remoto en el dominio público. Reproduce con pruebas, corrige en rama y despliega por
el proceso anterior. Valora con los responsables del tratamiento las obligaciones de
comunicación y los plazos aplicables a una brecha.

## Módulos

- `core/security_review.py`: comprobaciones de solo lectura y validación de evidencia.
- `core/views/security.py`: autorización y auditoría del panel.
- `templates/core/security*.html`: representación accesible, estados con texto/iconos.
- `core/management/commands/security_manifest.py`: referencia versionada del lanzamiento.
- `core/management/commands/security_scan.py`: analizadores fijos por consola.
- `.github/workflows/security.yml`: comprobaciones sin credenciales de producción.
- `core/test_security_review.py`: permisos, manipulación de archivos, evidencia caducada,
  secretos ausentes, ausencia de ejecución desde HTTP y errores de herramientas.
