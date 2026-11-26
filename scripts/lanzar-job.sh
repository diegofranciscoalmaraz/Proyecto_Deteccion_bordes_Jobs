#!/bin/bash
# Cada intento conserva su manifiesto y sus evidencias en una carpeta propia.
set -euo pipefail
cd "$(dirname "$0")/.."
export COMPLETIONS="${1:-8}" PARALLELISM="${2:-4}" INPUT_DIR="${3:-/data/entrada/imagenette2/val}"
export STRATEGY="${STRATEGY:-block}" IMAGE="${IMAGE:-bordes:f34}" FAIL_INDEX="${FAIL_INDEX:-}"
export CPU_REQUEST="${CPU_REQUEST:-250m}" CPU_LIMIT="${CPU_LIMIT:-1}"
export MEM_REQUEST="${MEM_REQUEST:-256Mi}" MEM_LIMIT="${MEM_LIMIT:-512Mi}"
export HOST_UID="$(id -u)" HOST_GID="$(id -g)"
export SAVE_EDGES_FLAG=""
if [[ "${SAVE_EDGES:-1}" == 1 ]]; then export SAVE_EDGES_FLAG="--save-edges"; fi
case "$STRATEGY" in block|cyclic|lpt) ;; *) exit 2 ;; esac
export JOB_NAME="${RUN_ID:-bordes-$(date +%s)-$RANDOM}"
[[ "$JOB_NAME" =~ ^[a-z0-9][a-z0-9-]{0,48}[a-z0-9]$ ]]
export OUTPUT_DIR="/data/salida/$JOB_NAME"
evidence="docs/evidencias/$JOB_NAME"
mkdir "$evidence"
k=(kubectl --context kind-bordes-f34)
envsubst < k8s/job.yaml.tpl > "$evidence/manifiesto.yaml"
"${k[@]}" create -f "$evidence/manifiesto.yaml"
deadline=$((SECONDS + ${JOB_TIMEOUT:-900}))
while true; do
    "${k[@]}" get job "$JOB_NAME" -o json > "$evidence/job.json"
    state=$(python3 -c 'import json,sys; print(next((c["type"] for c in json.load(sys.stdin).get("status",{}).get("conditions",[]) if c["status"]=="True" and c["type"] in ("Failed","Complete")), "Active"))' < "$evidence/job.json")
    [[ "$state" == Active && $SECONDS -lt $deadline ]] || break
    sleep 3
done
"${k[@]}" get pods -l "job-name=$JOB_NAME" -o wide > "$evidence/pods-por-nodo.txt"
"${k[@]}" get pods -l "job-name=$JOB_NAME" -o json > "$evidence/pods.json"
"${k[@]}" describe job "$JOB_NAME" > "$evidence/describe-job.txt"
if [[ "$state" != Complete ]]; then echo "Job $JOB_NAME terminó la espera en estado $state" >&2; exit 1; fi
python3 app/merge.py --input-dir "datos/salida/$JOB_NAME" | tee "$evidence/merge.txt"
