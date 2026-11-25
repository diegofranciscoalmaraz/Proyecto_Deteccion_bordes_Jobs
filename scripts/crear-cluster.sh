#!/bin/bash
# Crea el clúster kind (1 control-plane + 3 workers), construye la imagen y la carga.
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${IMAGE:-bordes:1.0}"

for cmd in docker kind kubectl envsubst; do
    command -v "$cmd" >/dev/null || { echo "Falta '$cmd' en el PATH"; exit 1; }
done

mkdir -p "$BASE_DIR/datos/entrada" "$BASE_DIR/datos/salida"

if kind get clusters | grep -qx bordes; then
    echo "El clúster 'bordes' ya existe, se reutiliza."
else
    DATOS_DIR="$BASE_DIR/datos" envsubst '${DATOS_DIR}' \
        < "$BASE_DIR/k8s/kind-config.yaml.tpl" > "$BASE_DIR/k8s/kind-config.yaml"
    kind create cluster --config "$BASE_DIR/k8s/kind-config.yaml"
fi

echo "Construyendo $IMAGE..."
docker build -t "$IMAGE" "$BASE_DIR"

echo "Cargando $IMAGE en los nodos de kind..."
kind load docker-image "$IMAGE" --name bordes

kubectl get nodes -o wide
