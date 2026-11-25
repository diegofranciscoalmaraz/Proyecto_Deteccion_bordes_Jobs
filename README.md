# Proyecto de detección de bordes con Kubernetes Jobs

## Descripción

Proyecto de procesamiento distribuido de imágenes del dataset Imagenette mediante workers en contenedores Docker, con ejecución paralela utilizando Kubernetes Jobs.

El procesamiento de cada imagen incluye:
1. Conversión a escala de grises.
2. Aplicación de filtro Gaussiano.
3. Detección de bordes mediante Sobel.
4. Aplicación de umbralización.

## Requisitos

- Git.
- Docker instalado y en ejecución.
- Python 3.13 (para ejecutar el proyecto fuera de Docker).

## 1. Descargar el proyecto

```bash
git clone https://github.com/diegofranciscoalmaraz/Proyecto_Deteccion_bordes_Jobs.git
cd Proyecto_Deteccion_bordes_Jobs
git checkout feature/worker
```

## 2. Descargar el dataset

Ejecutar:

```bash
bash scripts/descargar-datos.sh
```

Las imágenes de validación deben quedar en:

```text
datos/entrada/imagenette2/val
```

## 3. Construir la imagen Docker

Desde la raíz del repositorio:

```bash
docker build -t bordes:1.0 .
```

Verificar que la imagen se creó:

```bash
docker images
```

La imagen se construye localmente a partir del Dockerfile incluido en el repositorio. No se necesita Docker Hub.

## 4. Probar un worker con Docker

Crear el directorio de salida:

```bash
mkdir -p datos/salida-docker
```

Ejecutar:

```bash
docker run --rm \
  -v "$(pwd)/datos/entrada:/data/entrada:ro" \
  -v "$(pwd)/datos/salida-docker:/data/salida" \
  -e TOTAL_TASKS=4 \
  bordes:1.0 \
  python app/worker.py --index 0 --tasks 4
```

El worker procesa las imágenes que le corresponden y genera un CSV:

```text
datos/salida-docker/part-0000.csv
```

En la salida de la terminal se muestran las imágenes asignadas, procesadas, errores y tiempo de ejecución.

## 5. Ejecutar el worker localmente (opcional)

Crear y activar un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar un worker:

```bash
python app/worker.py --index 0 --tasks 4
```

## 6. Resultados

Los resultados generados por los workers se guardan en el directorio de salida configurado.

El programa de merge (`app/merge.py`) permite integrar los resultados parciales y generar un resumen global.

## 7. Ejecutar en Kubernetes (kind + Job indexado)

Requisitos: Docker, [kind](https://kind.sigs.k8s.io/) >= 0.23, kubectl >= 1.33 y `envsubst`.

```bash
# 1. Dataset (si aún no lo tienes)
bash scripts/descargar-datos.sh imagenette

# 2. Clúster kind (1 control-plane + 3 workers, datos/ montada en /data de cada nodo),
#    construye bordes:1.0 y la carga en los nodos
bash scripts/crear-cluster.sh

# 3. Muestra de 400 fotos para la primera prueba
bash scripts/crear-muestra.sh 400

# 4. Job indexado: 8 tareas, 4 pods en paralelo
bash scripts/lanzar-job.sh 8 4 /data/entrada/muestra400/val
```

`lanzar-job.sh` renderiza `k8s/job.yaml.tpl`, aplica el Job, espera a que termine, guarda
en `docs/evidencias/<corrida>/` el reparto de pods por nodo (`kubectl get pods -o wide`),
`kubectl describe job` y los tiempos del Job, y ejecuta `app/merge.py` sobre
`datos/salida/<corrida>/` (genera `resultados.csv`, `summary.json` y `mosaico.png`).

Opciones por variables de entorno: `STRATEGY` (por ahora `block`), `SAVE_EDGES=0|1`,
`CPU_REQUEST`, `CPU_LIMIT`, `MEM_REQUEST`, `MEM_LIMIT`, `IMAGE`.

Para borrar el clúster: `kind delete cluster --name bordes`.

## Notas

- El dataset y los resultados se mantienen localmente y no se suben al repositorio.
- La imagen Docker debe construirse en cada equipo usando el Dockerfile.
- Para ejecutar los workers en Kubernetes, el entorno debe proporcionar el dataset en la ruta configurada y las variables de entorno correspondientes.
