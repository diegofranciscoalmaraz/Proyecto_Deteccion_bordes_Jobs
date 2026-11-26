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

python3 - "$SRC" "$DST" "$N" <<'PYTHON'
import sys, shutil
from pathlib import Path

src, dst = map(Path, sys.argv[1:3])
count = int(sys.argv[3])
images = sorted(p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"})
if not 1 <= count <= len(images):
    sys.exit("Cantidad solicitada fuera del rango disponible")
if dst.exists():
    shutil.rmtree(dst)
for image in images[:count]:
    target = dst / image.relative_to(src)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image, target)
print(f"Muestra creada con {count} imágenes en {dst}")
PYTHON
