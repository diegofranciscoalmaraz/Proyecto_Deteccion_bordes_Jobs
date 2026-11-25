
#!/bin/bash
set -euo pipefail

DATASET="${1:-}"

if [[ "$DATASET" != "imagenette" ]]; then
    echo "Uso: $0 imagenette"
    exit 1
fi

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$BASE_DIR/datos"
ENTRADA="$DATA_DIR/entrada"
ARCHIVE="$DATA_DIR/imagenette2.tgz"

URL="https://s3.amazonaws.com/fast-ai-imageclas/imagenette2.tgz"

mkdir -p "$ENTRADA" "$DATA_DIR/salida"

echo "Descargando Imagenette..."

if [[ ! -f "$ARCHIVE" ]]; then
    curl -fL "$URL" -o "$ARCHIVE"
else
    echo "El archivo ya existe, se reutilizará."
fi

if [[ ! -d "$ENTRADA/imagenette2/val" ]]; then
    echo "Descomprimiendo dataset..."
    tar -xzf "$ARCHIVE" -C "$ENTRADA"
fi

VAL_DIR="$ENTRADA/imagenette2/val"

if [[ ! -d "$VAL_DIR" ]]; then
    echo "ERROR: No se encontró la carpeta val."
    exit 1
fi

IMAGE_COUNT=$(find "$VAL_DIR" -type f \
    \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) | wc -l)

cat > "$DATA_DIR/dataset.env" <<EOF
DATASET=imagenette
DATASET_DIR=datos/entrada/imagenette2
VAL_DIR=datos/entrada/imagenette2/val
IMAGE_COUNT=$IMAGE_COUNT
EOF

echo "--------------------------------"
echo "Dataset: Imagenette"
echo "Fotografías en val: $IMAGE_COUNT"
echo "Ubicación: $VAL_DIR"
echo "--------------------------------"

if [[ "$IMAGE_COUNT" -ne 3925 ]]; then
    echo "ADVERTENCIA: Se esperaban 3925 imágenes."
fi
