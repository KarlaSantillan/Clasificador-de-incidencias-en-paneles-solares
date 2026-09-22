# Inspector solar

Aplicación web académica desarrollada con Django para clasificar condiciones visibles en paneles solares mediante un modelo ResNet50 entrenado con TensorFlow y Keras.

> Este sistema realiza clasificación de imágenes. Su resultado no sustituye una inspección técnica profesional ni determina la ubicación exacta de un daño.

## 1. Descripción y problema abordado

La inspección visual de paneles fotovoltaicos permite identificar suciedad, obstrucciones y daños aparentes que pueden requerir mantenimiento. El proyecto recibe una fotografía, valida su contenido y utiliza una red neuronal para estimar a cuál de seis categorías visuales se parece más.

El propósito es demostrar la integración de un modelo de aprendizaje profundo en una aplicación web, manteniendo separados la interfaz, la validación, el servicio de inferencia y los artefactos del entrenamiento.

## 2. Funcionalidades

- Selección o arrastre de imágenes JPG, JPEG, PNG y WEBP.
- Validación real con Pillow, límite de 10 MB y límites de dimensiones.
- Vista previa en memoria, sin guardar la imagen.
- Clasificación con ResNet50 y seis probabilidades ordenadas.
- Nombres técnicos y nombres descriptivos en español.
- Niveles visuales de confianza alta, moderada y baja.
- Página informativa con métricas y gráficos originales del modelo.
- Comando de comprobación técnica del archivo `.keras`.
- Pruebas unitarias, funcionales y de integración real separada.

## 3. Tecnologías

- Python 3.11 de 64 bits.
- Django 5.2.16.
- TensorFlow 2.21.0.
- Keras 3.15.0.
- Pillow 12.3.0.
- NumPy 2.4.6.
- HTML semántico, CSS propio, JavaScript vanilla y SVG local.

## 4. Arquitectura Django MVT

El proyecto sigue el patrón Model–View–Template de Django:

- **Model:** no se crean modelos de dominio porque las imágenes y predicciones no se persisten. SQLite se utiliza únicamente para las aplicaciones internas de Django.
- **View:** `predictor/views.py` coordina formularios, vista previa, inferencia y lectura segura de resultados.
- **Template:** `templates/` contiene la presentación de Inicio, Resultado y Modelo.
- **Form:** `predictor/forms.py` aplica las validaciones del archivo antes de la inferencia.
- **Service:** `predictor/services/model_service.py` encapsula carga, preprocesamiento, predicción e interpretación.

## 5. Modelo ResNet50

- Arquitectura: ResNet50 con transfer learning y fine-tuning.
- Entrada: `224 × 224 × 3`, RGB.
- Fine-tuning: últimas 30 capas.
- Dataset: PV Panel Defect Dataset.
- Total: 869 imágenes.
- Entrenamiento: 604 imágenes.
- Validación: 127 imágenes.
- Prueba: 138 imágenes.
- Exactitud de prueba: **77.54%**.
- Pérdida de prueba: **0.6749**.

El modelo utilizado exclusivamente por Django es:

```text
ml_models/best_resnet50_paneles_6clases.keras
```

El archivo `.keras` ya incorpora internamente aumento de datos, conversión RGB→BGR y el preprocesamiento de ResNet50. La aplicación **no** aplica `preprocess_input`, no divide entre 255, no normaliza manualmente y no cambia externamente el orden de canales.

## 6. Categorías reconocidas

El orden es parte del contrato con el modelo y no debe modificarse:

| Índice | Clase técnica | Nombre mostrado |
|---:|---|---|
| 0 | `Bird-drop` | Excremento de aves |
| 1 | `Clean` | Panel limpio |
| 2 | `Dusty` | Panel cubierto de polvo |
| 3 | `Electrical-damage` | Daño eléctrico visible |
| 4 | `Physical-Damage` | Daño físico |
| 5 | `Snow-Covered` | Panel cubierto de nieve |

## 7. Requisitos previos

- Python 3.11 de 64 bits.
- Al menos 2 GB libres para el entorno, TensorFlow y archivos del modelo.
- El archivo `ml_models/best_resnet50_paneles_6clases.keras` presente localmente.
- No se requiere Conda, GPU ni servicios externos.

## 8. Instalación en Windows

Ejecutar desde la raíz del proyecto. Los comandos no dependen de activar PowerShell:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py check_model
.\venv\Scripts\python.exe manage.py runserver
```

## 9. Instalación en Linux o macOS

```bash
python3.11 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python manage.py migrate
./venv/bin/python manage.py check
./venv/bin/python manage.py check_model
./venv/bin/python manage.py runserver
```

En macOS con Apple Silicon, la disponibilidad exacta del paquete TensorFlow fijado debe comprobarse para la plataforma. El entorno académico verificado corresponde a Windows x64 con Python 3.11.

## 10. Ejecución

Después de iniciar el servidor, abrir:

<http://127.0.0.1:8000/>

La página de información del modelo está disponible en:

<http://127.0.0.1:8000/modelo/>

Para detener el servidor, usar `Ctrl+C` en la terminal.

## 11. Comprobación del modelo

Windows:

```powershell
.\venv\Scripts\python.exe manage.py check_model
```

Linux/macOS:

```bash
./venv/bin/python manage.py check_model
```

El comando comprueba rutas, clases, formas de entrada y salida, valores finitos y suma aproximada a uno mediante una entrada sintética. Esta salida no representa una clasificación real.

## 12. Ejecución de pruebas

Pruebas automáticas sin cargar repetidamente el modelo real:

```powershell
.\venv\Scripts\python.exe manage.py test
```

Prueba real separada en Windows PowerShell:

```powershell
$env:RUN_MODEL_INTEGRATION_TESTS='1'
.\venv\Scripts\python.exe manage.py test predictor.test_model_integration
Remove-Item Env:\RUN_MODEL_INTEGRATION_TESTS
```

En Linux/macOS:

```bash
RUN_MODEL_INTEGRATION_TESTS=1 ./venv/bin/python manage.py test predictor.test_model_integration
```

## 13. Estructura principal

```text
clasificador_paneles_solares/
├── manage.py
├── requirements.txt
├── README.md
├── docs/
├── solar_inspector/              # Configuración y URLs principales
├── predictor/
│   ├── forms.py                  # Validación de imágenes
│   ├── views.py                  # Flujo web y métricas
│   ├── urls.py
│   ├── services/model_service.py # Inferencia e interpretación
│   ├── tests.py
│   └── management/commands/check_model.py
├── templates/                    # Plantillas Django
├── static/                       # CSS, JavaScript y SVG
├── ml_models/                    # Modelo utilizado y clases
├── model_results/                # Reporte, historial y gráficos
├── resnet50/                     # Artefactos académicos adicionales
└── media/                        # No se usa para guardar cargas
```

## 14. Flujo de clasificación

1. El usuario selecciona o arrastra una imagen.
2. Django valida tamaño, extensión, contenido, formato y dimensiones.
3. Pillow corrige la orientación EXIF y convierte la imagen a RGB.
4. Se crea un arreglo NumPy `float32` en rango 0–255.
5. TensorFlow redimensiona a `224 × 224` y agrega la dimensión de lote.
6. El singleton carga el modelo una sola vez por proceso y ejecuta `predict(..., verbose=0)`.
7. Se verifican seis probabilidades finitas, no negativas y con suma aproximada a uno.
8. La aplicación presenta la clase principal y la distribución completa.

## 15. Limitaciones

- Clasifica la imagen completa; no localiza daños mediante cajas o máscaras.
- Solo reconoce las seis categorías usadas durante el entrenamiento.
- La exactitud no es del 100%; iluminación, enfoque, ángulo y fondo influyen.
- La confianza Softmax no equivale a una probabilidad clínica ni a una calibración científica.
- La aplicación no mide rendimiento eléctrico ni reemplaza instrumentos de diagnóstico.
- El modelo puede confundir categorías visualmente parecidas, como `Clean` y `Dusty`.

## 16. Aviso académico

Este resultado es generado por un modelo académico de clasificación de imágenes y no sustituye una inspección técnica profesional. No debe utilizarse como única base para manipular, desconectar o reparar una instalación fotovoltaica.

## 17. Solución de errores comunes

### `py` no se reconoce en Windows

Instalar Python 3.11 x64 desde Python.org y habilitar el lanzador de Python. También se puede invocar directamente la ruta del ejecutable de Python 3.11 para crear `venv`.

### Error de rutas largas al instalar TensorFlow

Mover temporalmente el proyecto a una ruta más corta, por ejemplo `C:\proyectos\inspector-solar`, o habilitar rutas largas de Windows según las políticas del equipo. Después, volver a instalar desde `requirements.txt`.

### No se encuentra el modelo

Comprobar que exista exactamente:

```text
ml_models/best_resnet50_paneles_6clases.keras
```

No sustituirlo por `resnet50_paneles_6clases_final.keras`.

### `check_model` informa clases incorrectas

Verificar que `ml_models/class_names.json` contenga las seis clases en el orden documentado.

### La imagen es rechazada

Usar JPG, JPEG, PNG o WEBP real, no superar 10 MB ni 10 000 píxeles por lado y evitar archivos dañados o con extensión renombrada.

### TensorFlow informa que no hay GPU en Windows

La aplicación funciona en CPU. Este aviso no impide la inferencia.

### El puerto 8000 está ocupado

Usar otro puerto:

```powershell
.\venv\Scripts\python.exe manage.py runserver 8001
```

### El favicon anterior continúa apareciendo

Los navegadores suelen conservar los favicons durante más tiempo que otros recursos. Realizar una recarga forzada con `Ctrl+F5`. Si persiste, cerrar la pestaña y volver a abrir la aplicación.
