# Guía de usuario — Inspector solar

## 1. Iniciar el servidor

En Windows, desde la carpeta raíz:

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

En Linux o macOS:

```bash
./venv/bin/python manage.py runserver
```

La terminal debe permanecer abierta. Para detener el servidor, presionar `Ctrl+C`.

## 2. Abrir la aplicación

Visitar <http://127.0.0.1:8000/> en un navegador moderno. La barra superior permite regresar a Inicio, consultar Cómo funciona o abrir la página Modelo.

## 3. Seleccionar o arrastrar una imagen

- Hacer clic en el área “Arrastra una imagen del panel”.
- Elegir el archivo en el selector del sistema.
- También se puede arrastrar el archivo desde una carpeta y soltarlo sobre el área.

Cuando el archivo es aceptado, se muestran una vista previa, su nombre y tamaño.

## 4. Formatos y límites

Formatos permitidos:

- JPG o JPEG.
- PNG.
- WEBP.

El contenido real debe corresponder con la extensión. El tamaño máximo es **10 MB**. Las dimensiones no pueden superar 10 000 píxeles por lado ni 40 megapíxeles.

## 5. Eliminar o cambiar la imagen

- **Cambiar:** abre nuevamente el selector para reemplazar la imagen.
- **Quitar:** elimina la selección y deshabilita el botón de análisis.

La acción solo afecta la selección del navegador; la aplicación no guarda el archivo.

## 6. Analizar la imagen

Con una imagen seleccionada, presionar **Analizar panel**. El botón cambia a “Analizando imagen” mientras el modelo evalúa la fotografía. No cerrar ni recargar la página durante ese proceso.

## 7. Interpretar la clase principal

La página de resultado muestra la categoría con el mayor valor Softmax. Incluye:

- Nombre en español.
- Nombre técnico del modelo.
- Descripción visual general.
- Recomendación preventiva.

La categoría expresa similitud visual, no un diagnóstico confirmado.

## 8. Interpretar la confianza

El porcentaje destacado es la salida Softmax de la clase principal multiplicada por cien. Indica la preferencia relativa del modelo entre sus seis categorías para esa imagen.

No representa precisión histórica, probabilidad de falla eléctrica ni certeza científica calibrada.

## 9. Leer las seis probabilidades

Debajo del resultado se muestran las seis categorías ordenadas de mayor a menor. Cada fila contiene nombre, clase técnica, porcentaje y barra proporcional. La suma es aproximadamente 100%, con pequeñas diferencias posibles por redondeo visual.

## 10. Niveles de confianza

- **Confianza alta:** 75% o más.
- **Confianza moderada:** desde 60% hasta menos de 75%.
- **Confianza baja:** menos de 60%.

Los rangos son una regla de presentación. Si el resultado es bajo, conviene tomar otra fotografía con mejor iluminación, enfoque y visibilidad.

## 11. Consultar la página del modelo

Seleccionar **Modelo** en la navegación o visitar <http://127.0.0.1:8000/modelo/>. La página contiene:

- Arquitectura y tamaño de entrada.
- División del dataset.
- Exactitud y pérdida de prueba.
- Curvas de entrenamiento.
- Matriz de confusión.
- Métricas por clase.

## 12. Errores frecuentes

### “Selecciona una imagen para analizar”

No se adjuntó un archivo. Elegir una imagen antes de continuar.

### “El archivo no es una imagen válida o está dañado”

El contenido no puede ser leído completamente por Pillow. Exportar nuevamente la imagen o usar otro archivo.

### “La extensión no coincide con el formato real”

No basta con renombrar un archivo. Utilizar una imagen exportada realmente como JPG, PNG o WEBP.

### “La imagen supera el tamaño máximo”

Reducir resolución o calidad hasta quedar por debajo de 10 MB.

### “No fue posible analizar la imagen”

Reintentar con otra fotografía. Si persiste, revisar la terminal y ejecutar `manage.py check_model`.

## 13. Recomendaciones para la fotografía

- Limpiar la lente de la cámara.
- Evitar movimiento y desenfoque.
- Usar iluminación uniforme, sin reflejos extremos.
- Mostrar la mayor parte posible de la superficie del panel.
- Evitar objetos que oculten la condición relevante.
- Tomar la foto desde un ángulo que reduzca deformaciones.
- No acercarse ni manipular una instalación energizada de forma insegura.

## 14. Advertencia

Este resultado es generado por un modelo académico de clasificación de imágenes y no sustituye una inspección técnica profesional. Ante posibles daños eléctricos o físicos, evitar manipulaciones riesgosas y consultar personal capacitado.
