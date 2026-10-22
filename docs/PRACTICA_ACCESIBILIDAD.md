# Práctica ficticia, bloques de progreso y accesibilidad · 0.7.0

## Probar dos alumnos sin afectar a la clase real

1. Actualiza la plataforma siguiendo [Actualizar PythonAnywhere](ACTUALIZAR_PYTHONANYWHERE.md). Esta versión necesita la migración `0008` antes de recargar.
2. Inicia sesión y pulsa **Práctica ficticia** en el menú lateral. No abras la sesión del grupo real para hacer el ensayo.
3. Comprueba el aviso **BASE DE PRÁCTICA SEPARADA** y las identidades **Aprendiz ficticio A** y **Aprendiz ficticio B**. Son identidades inventadas sin matrícula ni contacto de responsables.
4. En **Bloque de la práctica**, elige **Programación de videojuegos** y pulsa **Abrir bloque**. Hay ocho retos ficticios por aprendiz.
5. Despliega Aprendiz ficticio A y marca R1 y R2.
6. Despliega Aprendiz ficticio B y marca los ocho retos.
7. Pulsa una vez **Guardar retos ficticios**. Guarda los dos aprendices juntos; no es necesario guardar uno y perder el borrador del otro.
8. Comprueba **2/8** y **8/8** y sus tarjetas de progreso personal. Con paleta RPG y contraste normal se ven verde y naranja legendario, respectivamente. En Básicos se utiliza su escala simplificada; en Alto contraste los números y las etiquetas acompañan una presentación monocroma.
9. Puedes elegir Robótica, Diseño e impresión 3D u otro ámbito, marcar retos y guardar. Cada ámbito conserva sus propias casillas; cambiar el selector no guarda un borrador pendiente.
10. Para volver a empezar, despliega **Reiniciar únicamente mi práctica**, lee el alcance, escribe **REINICIAR** y pulsa **Reiniciar mi práctica**. Solo reinicia tus dos aprendices ficticios y sus revisiones, no los de otra cuenta ni los registros educativos reales.

La práctica no aparece en grupos, matrículas, asistencia o informes del alumnado real. No permite seleccionar personas reales, importar su ficha ni escribir notas personales. Cada cuenta tiene un ensayo independiente. Dos pestañas que guardan simultáneamente utilizan una versión de control; si aparece un conflicto, utiliza **Recargar práctica guardada** antes de volver a editar.

## Progreso personal: tres bloques y dos mini extras

En **Alumnado → ficha → Aprendizaje**, la sección **Mi recorrido maker** contiene:

| Bloque | Tipo |
| --- | --- |
| Diseño e impresión 3D | Principal |
| Robótica | Principal |
| Programación de videojuegos | Principal |
| IA ética | Extra |
| Creación de apps móviles | Extra |

Cada tarjeta tiene icono propio, nombre, explicación y contador de retos registrados. Las tarjetas principales ocupan la primera fila; los extras se presentan en un bloque secundario. Los iconos son gráficos de interfaz, no un logotipo ni una representación de Atibot.

Los contadores muestran **retos alcanzados de las sesiones con seguimiento registrado**. No representan el porcentaje de todo el currículo ni una clasificación del alumno. Una tarjeta sin registros muestra esa situación expresamente. Las observaciones vigentes se cuentan sin duplicar revisiones; el historial cronológico conserva todas las versiones.

**Ver historial del bloque** filtra los registros de ese ámbito. **Todo el historial** vuelve a mostrarlos todos y **Sin bloque asignado** permite consultar los anteriores sin clasificación.

### Asignar el bloque a una clase o recurso

1. Abre la clase y pulsa **Editar planificación**.
2. En **Bloque de contenidos**, selecciona su ámbito; para la ficha de videojuegos, selecciona **Programación de videojuegos**.
3. Guarda antes de registrar nuevos avances.
4. También puedes asignar el bloque al recurso de biblioteca o seleccionarlo al importar sesiones Word/CSV. Una sesión puede copiar el bloque explícito del recurso seleccionado.

Los nuevos registros de aprendizaje y de retos conservan una copia del bloque al que pertenecen. Cambiar posteriormente la clasificación de una sesión o recurso no reescribe sus registros anteriores. Las clases e historiales ya creados sin clasificación permanecen sin bloque; no se adivina su ámbito a partir del nombre ni se cambia una evaluación automáticamente. Una sesión tiene un bloque principal; para seguimiento de varios ámbitos separados, prepara sesiones/actividades con esa separación explícita.

Los filtros y tarjetas comprueban el ámbito de grupos autorizado en el servidor. No añaden acceso a notas familiares, salud o adaptaciones restringidas. Los informes existentes mantienen sus selecciones de contenido y no incluyen prácticas ficticias.

## Accesibilidad de la interfaz

Abre **Accesibilidad** en el menú. Sus preferencias se guardan por cuenta y no cambian las de otros docentes ni los avances del alumnado.

| Ajuste | Efecto |
| --- | --- |
| Tamaño del texto | Normal, Grande o Muy grande en textos y controles. |
| Contraste | Tema elegido o Alto contraste con fondos claros, texto oscuro, contornos marcados y botones contrastados. |
| Espaciado | Aumenta separación de líneas, campos y bloques. |
| Controles grandes | Amplía botones, enlaces de navegación, casillas y controles. |
| Movimiento reducido | Elimina transiciones y animaciones; también se respeta la preferencia de reducción de movimiento del dispositivo. |
| Decoración simplificada | Reduce adornos de fantasía, brillos y fondos decorativos; conserva iconos útiles y etiquetas. |
| Audiodescripción | Habilita ayuda hablada bajo demanda. |
| Velocidad | Pausada, normal o ágil. |

Pulsa **Guardar accesibilidad** para aplicar los ajustes. Puedes volver al mismo apartado y elegir los valores normales en cualquier momento. Alto contraste puede sustituir colores decorativos de progreso por una presentación monocroma: los números y etiquetas siguen indicando el estado. No hay información transmitida únicamente mediante color.

El foco visible señala el control activo. **Tabulador** y **Mayús + Tabulador** recorren los controles; **Enter** activa enlaces/botones y **Espacio** marca casillas. El primer enlace **Saltar al contenido** lleva el foco a la región principal. Los títulos, etiquetas, grupos de campos, contadores y barras de progreso aportan estructura para lectores de pantalla. No se afirma una certificación de accesibilidad: queda pendiente probar con usuarios y tecnologías de apoyo reales.

## Audiodescripción y voces locales

1. En Accesibilidad, marca **Activar ayudas de audiodescripción**, selecciona la velocidad y guarda.
2. Pulsa **Probar voz local** o **Escuchar ayuda de esta pantalla**.
3. Utiliza **Pausar**, **Continuar** y **Detener**. **Escape** también detiene la lectura.
4. En los bloques de progreso, **Escuchar ayuda** explica cómo interpretarlos.

Es lectura de **ayudas de navegación de la interfaz**, no un generador de descripciones de fotografías o vídeos ni un lector automático de fichas. Solo se leen textos estáticos revisados de la aplicación. No se recorren ni se envían nombres, contactos, entradas de formulario, evidencias, notas familiares o de salud a la síntesis de voz. No hay lectura automática al abrir una página.

La aplicación acepta solo voces que el navegador declare locales y que correspondan al idioma de la interfaz, español o inglés. Si no hay voz local, lo indica y deshabilita la reproducción; no cambia a un servicio remoto. Si el navegador no admite síntesis, informa de ello. Las ayudas complementan un lector de pantalla, no lo sustituyen.

En Windows puedes revisar **Configuración → Hora e idioma → Voz** y las voces instaladas para el idioma elegido; el nombre exacto del apartado puede variar por versión. Instala una voz local si la necesitas, vuelve a abrir el navegador y prueba de nuevo. La presencia de voces disponibles en el sistema no garantiza que todos los navegadores las expongan como locales. La lectura real debe comprobarse en el dispositivo del usuario. No se solicita instalar extensiones ni introducir claves de servicios.

## Separación de datos, migraciones y recuperación

- Base educativa: continúa en la ruta configurada por `DATABASE_PATH`/`APP_ENV`.
- Base de práctica: `var/practice/<APP_ENV>.sqlite3`, creada automáticamente al abrir la práctica, con permisos privados. Usa una tabla separada, claves de aprendiz ficticias y el identificador interno del propietario; no contiene nombres reales de alumnado ni vínculos a sus fichas.
- Esquema de práctica: `core/practice_migrations/0001_initial.sql`, versionado con `PRAGMA user_version=1`. No necesitas ejecutar SQL manualmente. Se rechaza que su ruta o archivo coincida con la base principal o que contenga tablas ajenas a la práctica.
- Se conservan hasta cien revisiones de práctica por cuenta hasta reiniciarla. La auditoría principal registra únicamente acciones de práctica y cuenta, sin contenido educativo.
- La migración Django `0008` añade preferencias de accesibilidad y códigos de ámbito a recursos, sesiones y registros. Sus valores iniciales vacíos conservan los historiales existentes; no migra ni completa aprendizajes.
- Haz una copia educativa antes de actualizar. El comando `backup` existente no incluye la base ficticia de práctica: sus cambios no alteran la copia educativa ni deben restaurarse encima de ella. Si quieres conservar una práctica, gestiona una copia independiente de ese archivo sin escritores activos. Si falla la práctica, no borres ni sustituyas la base educativa para resolverla.

Antes de un uso estable con datos reales siguen vigentes las revisiones de [operación y privacidad](OPERATIONS.md). Esta actualización no cambia el entorno del despliegue automáticamente.

## Mapa modular

| Archivo | Responsabilidad |
| --- | --- |
| `core/curriculum.py` | Los cinco ámbitos y resúmenes del progreso autorizado, sin duplicar revisiones. |
| `core/accessibility.py` | Preferencias acotadas y textos estáticos de las ayudas de voz. |
| `core/views/accessibility.py` | Guardado por cuenta con autenticación y CSRF. |
| `core/practice.py` | Almacén ficticio separado, control de versión y reinicio por propietario. |
| `core/views/practice.py` | Formularios y visualización de los dos aprendices, sin acceso a fichas reales. |
| `templates/core/content_*.html` | Iconos, tarjetas y filtros de los bloques. |
| `static/core/accessibility.css` | Ajustes visuales, foco, tamaños y diseño adaptable. |
| `static/core/accessibility.js` | Voz local bajo demanda y controles de reproducción. |
| `core/test_accessibility_curriculum.py` | Aislamiento, permisos, revisiones, resúmenes y preferencias. |

Para añadir un ámbito o cambiar su código estable hay que modificar código y preparar la migración correspondiente; no se ejecutan scripts arbitrarios desde la interfaz. Los cambios de preferencias no necesitan migraciones de datos educativos.
