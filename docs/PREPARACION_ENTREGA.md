# Preparación de la entrega académica

## 1. Objetivo

Esta guía describe cómo preparar el proyecto para un archivo RAR académico sin crear todavía una copia de varios cientos de megabytes.

## 2. Archivos que deben incluirse

- Código Django:
  - `manage.py`
  - `solar_inspector/`
  - `predictor/`
  - `templates/`
  - `static/`
- `requirements.txt`.
- `README.md`.
- `docs/` completo.
- `.env.example` y `.gitignore` como referencia.
- `ml_models/best_resnet50_paneles_6clases.keras`.
- `ml_models/class_names.json`.
- `model_results/` completo.
- `resnet50/` si forma parte de los artefactos solicitados por el docente.

El archivo utilizado por la aplicación es `ml_models/best_resnet50_paneles_6clases.keras`. Confirmar que esté presente antes de comprimir.

## 3. Archivos que no deben incluirse

- `venv/`.
- Cualquier carpeta `__pycache__/`.
- Archivos `*.pyc`.
- `.env` con secretos locales.
- `db.sqlite3` si no contiene información necesaria para la entrega.
- Archivos temporales del editor o sistema operativo.
- Logs.
- Cachés de pruebas, herramientas o gestores de paquetes.
- Capturas de pantalla innecesarias.
- Copias adicionales del RAR dentro del propio proyecto.

No eliminar fuentes, plantillas, estáticos, documentación ni los artefactos originales requeridos.

## 4. El modelo y Git

`.gitignore` contiene `ml_models/*.keras` para evitar subir accidentalmente un archivo pesado a un repositorio. Esta regla **no significa que el modelo deba excluirse de la entrega académica**.

El RAR debe incluir manualmente:

```text
ml_models/best_resnet50_paneles_6clases.keras
```

No sustituirlo por `resnet50_paneles_6clases_final.keras`.

## 5. Lista de comprobación previa

1. Usar Python 3.11 de 64 bits.
2. Instalar `requirements.txt` en un entorno limpio si se desea comprobar reproducibilidad.
3. Ejecutar:

   ```powershell
   .\venv\Scripts\python.exe manage.py migrate
   .\venv\Scripts\python.exe manage.py check
   .\venv\Scripts\python.exe manage.py check_model
   .\venv\Scripts\python.exe manage.py test
   ```

4. Verificar Inicio y Modelo en `http://127.0.0.1:8000/`.
5. Realizar una predicción con una imagen de prueba.
6. Confirmar que `README.md` y `docs/` se abren correctamente.
7. Confirmar que no existe `.env` con información privada.
8. Confirmar que el modelo aparece dentro de la selección para comprimir.

## 6. Estructura esperada dentro del RAR

```text
clasificador_paneles_solares/
├── README.md
├── requirements.txt
├── manage.py
├── docs/
├── predictor/
├── solar_inspector/
├── templates/
├── static/
├── ml_models/
├── model_results/
└── resnet50/        # Solo si fue solicitado
```

La carpeta `venv/` no debe aparecer.

## 7. Creación posterior del RAR

No se crea el RAR durante esta fase para evitar duplicar los modelos en disco. Cuando corresponda:

1. Cerrar el servidor Django.
2. Seleccionar únicamente los archivos indicados.
3. Comprimir con un nombre descriptivo, por ejemplo `Inspector_solar_entrega_academica.rar`.
4. Abrir el RAR y comprobar su contenido antes de enviarlo.
5. Si la plataforma limita el tamaño, consultar al docente antes de excluir cualquier modelo o artefacto.

## 8. Nota de integridad

No modificar los binarios `.keras`, gráficos, CSV o JSON después de la verificación final. Si se requiere demostrar integridad, calcular SHA-256 y comparar con el registro de cierre del proyecto.
