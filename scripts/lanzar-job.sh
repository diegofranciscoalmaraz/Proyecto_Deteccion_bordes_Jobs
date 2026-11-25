#!/bin/bash
# Lanza un Job indexado, espera a que termine, guarda evidencias y ejecuta merge.py.
# Uso: scripts/lanzar-job.sh [COMPLETIONS] [PARALLELISM] [INPUT_DIR_EN_/data]
# Ejemplo Fase 2 (8 tareas, 4 en paralelo, 400 fotos):
#   scripts/crear-muestra.sh 400
#   scripts/lanzar-job.sh 8 4 /data/entrada/muestra400/val
# Variables opcionales: STRATEGY (block), SAVE_EDGES (1/0), IMAGE, CPU_REQUEST, CPU_LIMIT, MEM_REQUEST, MEM_LIMIT
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

export COMPLETIONS="${1:-8}"
export PARALLELISM="${2:-4}"
export INPUT_DIR="${3:-/data/entrada/imagenette2/val}"
export STRATEGY="${STRATEGY:-block}"
export IMAGE="${IMAGE:-bordes:1.0}"
export CPU_REQUEST="${CPU_REQUEST:-250m}"  CPU_LIMIT="${CPU_LIMIT:-1}"
export MEM_REQUEST="${MEM_REQUEST:-256Mi}" MEM_LIMIT="${MEM_LIMIT:-512Mi}"
[[ "${SAVE_EDGES:-1}" == "1" ]] && export SAVE_EDGES_FLAG="--save-edges" || export SAVE_EDGES_FLAG=""

RUN="job-${STRATEGY}-c${COMPLETIONS}-p${PARALLELISM}-$(date +%H%M%S)"
export JOB_NAME="bordes-$(echo "$RUN" | tr '_A-Z' '-a-z' | sed 's/^job-//')"
export OUTPUT_DIR="/data/salida/$RUN"
MANIFEST="$BASE_DIR/k8s/job-$RUN.yaml"
EVID="$BASE_DIR/docs/evidencias/$RUN"
mkdir -p "$EVID"

envsubst '${JOB_NAME} ${COMPLETIONS} ${PARALLELISM} ${IMAGE} ${STRATEGY} ${SAVE_EDGES_FLAG} ${INPUT_DIR} ${OUTPUT_DIR} ${CPU_REQUEST} ${CPU_LIMIT} ${MEM_REQUEST} ${MEM_LIMIT}' \
    < "$BASE_DIR/k8s/job.yaml.tpl" > "$MANIFEST"

echo ">> Lanzando $JOB_NAME (completions=$COMPLETIONS, parallelism=$PARALLELISM, entrada=$INPUT_DIR)"
kubectl apply -f "$MANIFEST"

# Espera a que termine el Job (completo o fallido)
kubectl wait --for=condition=complete job/"$JOB_NAME" --timeout=900s || \
    kubectl wait --for=condition=failed job/"$JOB_NAME" --timeout=5s || true

# Evidencias
kubectl get pods -l job-name="$JOB_NAME" -o wide | tee "$EVID/pods-por-nodo.txt"
kubectl describe job "$JOB_NAME" > "$EVID/describe-job.txt"
kubectl get job "$JOB_NAME" -o jsonpath='start={.status.startTime} end={.status.completionTime}{"\n"}' | tee "$EVID/tiempos-job.txt"

# Integración de resultados (los pods escribieron en datos/salida/$RUN)
if command -v python3 >/dev/null && python3 -c "import cv2, numpy" 2>/dev/null; then
    python3 "$BASE_DIR/app/merge.py" --input-dir "$BASE_DIR/datos/salida/$RUN" | tee "$EVID/merge.txt"
else
    echo "Sin cv2/numpy en el host: ejecuta merge.py con el entorno virtual:"
    echo "  python app/merge.py --input-dir datos/salida/$RUN"
fi

echo ">> Resultados: datos/salida/$RUN | Evidencias: docs/evidencias/$RUN"
