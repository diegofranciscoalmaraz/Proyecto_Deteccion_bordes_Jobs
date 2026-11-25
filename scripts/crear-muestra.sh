#!/bin/bash
# Copia las primeras N fotos (orden alfabético) de val a datos/entrada/muestra<N>/val.
# Se copian (no se enlazan) porque los enlaces simbólicos no funcionan dentro de los nodos kind.
# Uso: scripts/crear-muestra.sh [N]   (por defecto 400)
set -euo pipefail

N="${1:-400}"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$BASE_DIR/datos/entrada/imagenette2/val"
DST="$BASE_DIR/datos/entrada/muestra$N/val"

[[ -d "$SRC" ]] || { echo "Falta $SRC. Ejecuta scripts/descargar-datos.sh imagenette"; exit 1; }

rm -rf "$DST"; mkdir -p "$DST"
( cd "$SRC" && find . -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) | sort | head -n "$N" \
    | xargs cp --parents -t "$DST" )

echo "Muestra creada: $(find "$DST" -type f | wc -l) fotos en $DST"
