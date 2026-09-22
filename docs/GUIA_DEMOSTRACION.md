# Guía de demostración — Inspector solar

## Guion aproximado de 5 minutos

### 0:00–0:35 — Presentación del problema

“Los paneles solares pueden presentar suciedad, obstrucciones y daños visibles. Revisar fotografías manualmente requiere tiempo y conocimiento. Este proyecto académico integra un clasificador de imágenes en una aplicación web para apoyar una primera revisión visual.”

Mencionar desde el inicio que no sustituye una inspección profesional.

### 0:35–1:05 — Modelo ResNet50

“Se utilizó ResNet50 con transfer learning y fine-tuning de las últimas 30 capas. La red recibe imágenes RGB de 224 por 224 píxeles y devuelve una distribución Softmax sobre seis clases.”

Nombrar brevemente las clases: excremento de aves, limpio, polvo, daño eléctrico, daño físico y nieve.

### 1:05–1:30 — Apertura de la aplicación

1. Ejecutar `runserver` antes de la exposición.
2. Abrir <http://127.0.0.1:8000/>.
3. Mostrar navegación, instrucciones y condiciones reconocidas.
4. Indicar que la imagen se procesa en memoria y no se guarda.

### 1:30–2:05 — Selección de fotografía

1. Arrastrar una imagen válida o usar el selector.
2. Mostrar vista previa, nombre y tamaño.
3. Señalar formatos JPG, PNG y WEBP, con máximo 10 MB.
4. Demostrar brevemente “Cambiar” o “Quitar” si el tiempo lo permite.

### 2:05–2:40 — Ejecución del análisis

1. Presionar **Analizar panel**.
2. Mostrar el estado “Analizando imagen”.
3. Explicar que Django corrige EXIF, convierte a RGB, crea `float32`, redimensiona y entrega valores 0–255 directamente al modelo.
4. Aclarar que el `.keras` ya contiene internamente el preprocesamiento de ResNet50.

### 2:40–3:25 — Resultado y probabilidades

1. Leer la condición principal y el porcentaje.
2. Diferenciar clase técnica y nombre en español.
3. Explicar descripción y recomendación.
4. Recorrer las seis probabilidades ordenadas.
5. Aclarar que confianza alta/moderada/baja es una regla visual, no calibración científica.

### 3:25–4:15 — Página del modelo

1. Abrir **Modelo**.
2. Mostrar ResNet50, entrada 224 × 224 RGB y seis clases.
3. Indicar la división: 604 entrenamiento, 127 validación y 138 prueba.
4. Mostrar curvas de entrenamiento y matriz de confusión.
5. Recorrer la tabla de precision, recall, F1-score y support.

### 4:15–4:40 — Métricas principales

“El conjunto de prueba obtuvo 77.54% de exactitud y una pérdida de 0.6749. Estas métricas muestran un desempeño útil para una demostración académica, pero también un margen de error que debe comunicarse.”

### 4:40–5:00 — Limitaciones y cierre

“La aplicación clasifica la fotografía completa; no localiza el daño. Solo conoce seis clases y puede verse afectada por iluminación, enfoque o imágenes fuera del dataset. Como trabajo futuro se podría ampliar el dataset, calibrar probabilidades y evaluar detección o segmentación.”

Cerrar agradeciendo y ofrecer ejecutar `check_model` si el docente solicita evidencia técnica.

## Preparación previa

- Confirmar `manage.py check` y `manage.py check_model`.
- Tener una imagen válida y otra inválida disponibles.
- Abrir Inicio y Modelo previamente para comprobar recursos.
- Evitar depender de internet; la aplicación usa recursos locales.
- Mantener visible una terminal para mostrar que el servidor está activo.

## Preguntas posibles y respuestas

### ¿Por qué se eligió ResNet50?

Porque es una arquitectura residual consolidada, adecuada para transfer learning. Sus conexiones residuales facilitan entrenar redes profundas y aprovechar características aprendidas en ImageNet con un dataset académico relativamente pequeño.

### ¿Por qué se redimensiona a 224 × 224?

Es el tamaño de entrada configurado al entrenar el modelo y el tamaño estándar de ResNet50. Mantenerlo garantiza compatibilidad de formas y distribución.

### ¿Qué significa Softmax?

Convierte las puntuaciones finales de las seis clases en valores no negativos que suman aproximadamente uno. Permite compararlas como una distribución relativa.

### ¿Qué representa la confianza?

Es el valor Softmax de la clase con mayor puntuación para esa imagen. No equivale a exactitud global ni a una probabilidad científicamente calibrada.

### ¿Por qué no se usa `preprocess_input` en Django?

Porque el archivo `.keras` ya incluye internamente conversión RGB→BGR, `preprocess_input` y resta de medias. Aplicarlo otra vez alteraría los datos y perjudicaría la predicción.

### ¿Por qué puede confundirse `Clean` con `Dusty`?

Porque una capa fina de polvo, iluminación uniforme o baja resolución puede producir patrones parecidos a una superficie limpia. El tamaño y diversidad del dataset también influyen.

### ¿La aplicación detecta la ubicación exacta del daño?

No. Realiza clasificación global de la imagen. Para localizar daños se necesitaría detección de objetos o segmentación con anotaciones espaciales.

### ¿Por qué no alcanza el 100%?

Por variación de imágenes, clases similares, cantidad limitada de datos y capacidad de generalización. Un 100% también podría sugerir sobreajuste o una evaluación poco representativa.

### ¿Qué mejoras podrían implementarse?

Más datos variados, validación cruzada, calibración de confianza, análisis de imágenes fuera de distribución, explicabilidad visual y comparación con otras arquitecturas. En una fase distinta podrían evaluarse detección o segmentación.

### ¿Cuál es la diferencia entre clasificación y detección?

La clasificación asigna una categoría a la imagen completa. La detección además identifica una o varias ubicaciones mediante cajas delimitadoras. La segmentación delimita píxeles o regiones con mayor precisión.
