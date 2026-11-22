# Guía para preparar tu defensa de título en la UTEM

Esta plantilla te ayuda a armar la presentación de tu defensa con el diseño institucional de la UTEM. Tú pones tu tesis y Claude Code escribe un primer borrador de las láminas, el guion y el plan de ensayos. Después tú lo revisas, lo completas y lo ensayas.

La guía junta lo que recomiendan los talleres para tesistas de la Universidad de Chile, lo que dicen los reglamentos de la UTEM y lo que aprendió quien hizo esta plantilla en su propia defensa. Las fuentes están en `docs/references.md`.

## 1. Antes de empezar

1. **Pregunta a tu escuela cuánto tiempo tienes para exponer.** Cambia según la carrera. Por ejemplo, la escuela de Electrónica de la Facultad de Ingeniería pidió menos de 20 minutos, y el reglamento de Ingeniería Civil en Ciencia de Datos permite hasta 30 minutos. Anota tu límite en `duracion_minutos`, en `content/01-defensa.yml`.
2. **Deja un margen de 5 minutos.** Si tu límite es 20 minutos, arma una presentación de unos 15. En la sala se habla distinto que en el ensayo, y es mejor que te sobre tiempo a que te corten.
3. **Lee el reglamento de tu carrera.** Ahí se dice quiénes forman la comisión y cuánto pesa la defensa en tu nota. En Ciencia de Datos, por ejemplo, evalúan el jefe de carrera, el profesor guía y dos especialistas, con una rúbrica definida antes, y después de la exposición vienen las preguntas.

## 2. Qué tiene que lograr tu defensa

La comisión ya leyó tu tesis. La defensa no es para contar todo de nuevo. Es para mostrar dos cosas:

1. Que tu trabajo fue riguroso: tomaste decisiones con razones y las puedes explicar.
2. Que tu trabajo es un aporte: deja algo que antes no existía.

Todo lo que no ayude a mostrar eso puede ir a una lámina de respaldo o quedar fuera.

## 3. La estructura en tres momentos

| Momento | Qué incluye | Modelos de lámina |
|---|---|---|
| Inicio | Saludo y quién eres, por qué importa el tema, la pregunta central y la estructura de la presentación | `portada`, `agenda`, `separador`, `problema` |
| Cuerpo | Antecedentes muy breves, objetivos copiados textual de la tesis, cómo lo hiciste y por qué, y los resultados más importantes | `objetivos`, `imagen`, `dos-imagenes`, `tabla`, `cifras`, `grafico`, `validacion` |
| Cierre | Qué significan los resultados, tu aporte, las limitaciones, lo que sigue y una frase final para recordar | `conclusiones`, `cierre` |

Las cinco secciones de las pestañas (Problema, Objetivos, Metodología, Resultados y Conclusiones) siguen este orden. Puedes cambiar sus nombres en `secciones`.

## 4. Cómo escribir cada lámina

1. **Un título que diga la idea, no solo el tema.** En vez de "Resultados", escribe "El sistema respondió en menos de 2 segundos en 9 de 10 pruebas".
2. **Una idea por bloque.** Palabras clave en vez de párrafos. Si una lámina necesita mucho texto, divídela o mueve el detalle al respaldo.
3. **Lenguaje simple.** Escribe para alguien de la comisión que no es de tu especialidad. La primera vez que aparezca un término técnico, explícalo en una frase. Por ejemplo: "la latencia, que es el tiempo que tarda el sistema en responder".
4. **Objetivos y pregunta, textuales.** Cópialos tal como están en la tesis. No los resumas.
5. **Metodología que justifica.** No basta con la lista de pasos. Di por qué elegiste ese camino y no otro, y que otra persona podría repetirlo.
6. **Un recurso visual grande por lámina.** Un gráfico, un diagrama o una tabla corta. Rotula siempre qué muestra y escribe la fuente al pie, por ejemplo "Fuente: Tabla 5.1 de la tesis".
7. **Nunca inventes cifras.** Si falta un dato, déjalo entre corchetes, por ejemplo `[porcentaje de aciertos]`, hasta tenerlo.
8. **Evita** el exceso de texto, los colores oscuros o muy llamativos, las animaciones que giran, el exceso de logos y los gráficos que no se leen desde lejos.

## 5. Las láminas de respaldo

Prepara entre 3 y 8 láminas ocultas al final, con el detalle técnico que no cabe en la exposición. Solo las muestras si la comisión pregunta por ese tema.

Las preguntas más comunes son dos: **por qué elegiste esa solución y no otra**, y **cuáles son las limitaciones** de tu trabajo. Ten una lámina de respaldo lista para cada una. Los modelos `respaldo-alcance`, `respaldo-tarjetas`, `respaldo-pasos` y `respaldo-antes-despues` sirven para eso.

## 6. El guion

Cada lámina tiene un guion, que es lo que dirás, y los segundos que te tomará. El comando suma los segundos de las láminas visibles y te avisa si te pasas del límite.

1. Escribe frases cortas, como hablas, no como escribes la tesis.
2. No te aprendas el guion de memoria. Ten claro el recorrido de las ideas y dilo con tus palabras cada vez. Eso se llama improvisación controlada.
3. Los separadores duran unos 5 segundos. Una lámina con un resultado importante puede durar más de un minuto.

## 7. Los ensayos

Quien hizo esta plantilla lo dice después de su defensa: **ensaya más veces y siempre con reloj.** Usa `content/02-ensayos.md` para anotar cada ensayo.

1. Ensaya en modo presentación, con el cronómetro de PowerPoint.
2. Ensaya con otras personas, mejor si no son de tu especialidad. Si entienden, la comisión también.
3. Ensaya el error: qué haces si se cae el proyector o te quedas en blanco.
4. Cuida tu voz. Si hablas bajo, sube el volumen. Si hablas rápido, haz pausas en los cambios de sección.
5. Si te pasas del tiempo, recorta el detalle técnico y muévelo al respaldo. No recortes las conclusiones.

## 8. Cómo usar esta plantilla, paso a paso

1. En GitHub, presiona **Use this template** para crear tu propio repositorio. Déjalo privado si tu tesis todavía no es pública.
2. Instala Python 3.11 y, en la carpeta del repositorio, ejecuta una vez `pip install -r requirements.txt`.
3. Crea la carpeta `thesis/` y deja ahí el PDF de tu tesis. Esa carpeta nunca se sube a GitHub.
4. Abre Claude Code en la carpeta y escribe `/build-defense`. Te hará algunas preguntas y escribirá `content/01-defensa.yml` y `content/02-ensayos.md`.
5. Revisa el archivo `content/01-defensa.yml`. Corrige lo que no te represente y completa todo lo que esté entre corchetes.
6. Guarda tus imágenes en `figures/` y escribe su ruta en la lámina, por ejemplo `imagen: figures/diagrama.png`.
7. Ejecuta `python scripts/build_deck.py`. Tu presentación queda en `build/defensa.pptx` y el guion en `build/guion.md`.
8. Abre la presentación en PowerPoint para los ajustes finos y ensaya con el guion en las notas del orador.

Para ver todos los modelos de lámina y sus campos, ejecuta `python scripts/build_deck.py --models`.
