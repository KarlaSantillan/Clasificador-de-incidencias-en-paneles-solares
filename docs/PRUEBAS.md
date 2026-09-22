# Documentación de pruebas — Inspector solar

## 1. Estrategia

Las pruebas se dividen en:

- **Automáticas:** ejecutadas por Django, normalmente con el modelo simulado en vistas.
- **Integración:** cargan el archivo `.keras` real una sola vez.
- **Manuales:** verificaciones visuales o de interacción realizadas por una persona.

Las pruebas manuales indicadas como confirmadas fueron reportadas por el usuario. No se atribuyen a Codex.

## 2. Matriz de pruebas

| ID | Prueba | Entrada | Resultado esperado | Tipo | Estado |
|---|---|---|---|---|---|
| F-01 | Formulario sin archivo | POST vacío | Mensaje en español y formulario visible | Automática | Aprobada |
| F-02 | JPG válido | Imagen JPEG real | Formulario válido | Automática | Aprobada |
| F-03 | PNG válido | Imagen PNG real | Formulario válido | Automática | Aprobada |
| F-04 | WEBP válido | Imagen WEBP, si Pillow lo admite | Formulario válido | Automática | Aprobada |
| F-05 | Archivo vacío | JPG de cero bytes | Rechazo con mensaje de archivo vacío | Automática | Aprobada |
| F-06 | Archivo falso | Texto con extensión `.jpg` | Rechazo como imagen inválida | Automática | Aprobada |
| F-07 | Imagen dañada | JPEG truncado | Rechazo como imagen inválida | Automática | Aprobada |
| F-08 | Límite de tamaño | Archivo declarado mayor de 10 MB | Rechazo antes de procesar con Pillow | Automática | Aprobada |
| F-09 | Límite de dimensiones | Imagen de 10 001 píxeles de ancho | Rechazo por dimensiones excesivas | Automática | Aprobada |
| F-10 | Escala de grises | PNG modo `L` | Aceptación y conversión posterior a RGB | Automática | Aprobada |
| F-11 | RGBA | PNG modo `RGBA` | Aceptación y conversión posterior a RGB | Automática | Aprobada |
| P-01 | Preparación de píxeles | RGB con valores conocidos | Lote `(1,224,224,3)`, `float32`, rango 0–255 | Automática | Aprobada |
| P-02 | Conversión de gris a RGB | Píxel gris 90 | Tres canales con valor 90 | Automática | Aprobada |
| P-03 | Relación índice–clase | Cada índice como máximo | Clase técnica exacta según el orden | Automática | Aprobada |
| P-04 | Orden de probabilidades | Vector desordenado | Lista descendente de seis valores | Automática | Aprobada |
| P-05 | Confianza alta | Máximo de 0.75 | Etiqueta “Confianza alta” | Automática | Aprobada |
| P-06 | Confianza moderada | Máximo de 0.60 | Etiqueta “Confianza moderada” | Automática | Aprobada |
| P-07 | Confianza baja | Máximo de 0.59 | Etiqueta y aviso de baja confianza | Automática | Aprobada |
| P-08 | Probabilidad negativa | Distribución con valor negativo | `ModelIntegrationError` | Automática | Aprobada |
| P-09 | Valor no finito | Distribución con `NaN` | `ModelIntegrationError` | Automática | Aprobada |
| P-10 | Suma inválida | Seis valores de 0.10 | `ModelIntegrationError` | Automática | Aprobada |
| P-11 | Barras seguras | Resultado válido | Valores entre 0 y 100 y un ganador | Automática | Aprobada |
| V-01 | GET Inicio | `/` | HTTP 200 y formulario esencial | Automática | Aprobada |
| V-02 | GET Modelo | `/modelo/` | HTTP 200, métricas y clases reales | Automática | Aprobada |
| V-03 | Navegación | Enlaces Inicio y Modelo | URLs reversibles presentes | Automática | Aprobada |
| V-04 | POST válido | PNG válido y servicio simulado | Resultado, base64 y seis probabilidades | Automática | Aprobada |
| V-05 | POST inválido | Texto renombrado | Formulario con error controlado | Automática | Aprobada |
| V-06 | Excepción del modelo | `ModelIntegrationError` simulado | Mensaje amigable, sin detalle interno | Automática | Aprobada |
| V-07 | Ganador destacado | Distribución con máximo único | Una fila con `is-winner` | Automática | Aprobada |
| V-08 | Aviso académico | Resultado válido | Aviso visible en HTML | Automática | Aprobada |
| M-01 | Reporte de clasificación | CSV de `model_results` | Seis filas y 77.54% de exactitud | Automática | Aprobada |
| M-02 | Lista cerrada de gráficos | Clave válida e inválida | PNG para permitida y 404 para desconocida | Automática | Aprobada |
| S-01 | Recursos estáticos | CSS, JS y SVG | Archivos encontrados por staticfiles | Automática | Aprobada |
| I-01 | Comando técnico | `manage.py check_model` | Formas correctas y seis probabilidades válidas | Integración | Aprobada |
| I-02 | Modelo real | Lote sintético `float32` | Salida finita, no negativa y suma uno | Integración | Aprobada |
| I-03 | POST real | Imagen RGB válida | HTTP 200 con resultado completo | Integración | Aprobada |
| H-01 | Rutas HTTP | Inicio, Modelo, CSS, JS y gráficos | HTTP 200 | Integración | Aprobada |
| J-01 | Sintaxis JavaScript | `upload.js` | `node --check` sin errores | Automática | Aprobada |
| D-01 | Migraciones pendientes | `makemigrations --check --dry-run` | Ningún cambio detectado | Automática | Aprobada |
| UI-01 | Navegación responsive | Anchos de escritorio, tableta y móvil | Sin desbordamiento ni cortes | Manual | Confirmada por el usuario; no ejecutada por Codex |
| UI-02 | Menú móvil | Abrir, navegar, cerrar y tecla Escape | Operación accesible y estable | Manual | Confirmada por el usuario; no ejecutada por Codex |
| UI-03 | Selector visual | Seleccionar, quitar y reemplazar | Estados visuales correctos | Manual | Confirmada por el usuario; no ejecutada por Codex |
| UI-04 | Estado de procesamiento | Envío de imagen | Spinner y bloqueo contra doble envío | Manual | Confirmada por el usuario; no ejecutada por Codex |
| UI-05 | Animación de barras | Página de resultado | Barras alcanzan valores reales | Manual | Confirmada por el usuario; no ejecutada por Codex |

## 3. Comandos

Pruebas automáticas:

```powershell
.\venv\Scripts\python.exe manage.py test
```

Integración real:

```powershell
$env:RUN_MODEL_INTEGRATION_TESTS='1'
.\venv\Scripts\python.exe manage.py test predictor.test_model_integration
Remove-Item Env:\RUN_MODEL_INTEGRATION_TESTS
```

Comprobación del modelo:

```powershell
.\venv\Scripts\python.exe manage.py check_model
```

Migraciones:

```powershell
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

## 4. Interpretación del conjunto

La suite normal omite deliberadamente la integración real para evitar cargar el modelo de 216 MB en cada ejecución. Esta omisión no significa fallo: el caso real se activa de forma explícita y `check_model` ofrece una segunda validación independiente.

Las pruebas automáticas no reemplazan una revisión humana del diseño. La revisión manual fue confirmada por el usuario antes de esta fase de cierre.
