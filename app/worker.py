
import argparse
import csv
import json
import os
import socket
import time
from pathlib import Path

import heapq


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Worker para deteccion de bordes en Imagenette"
    )

    parser.add_argument(
        "--index",
        type=int,
        default=int(os.getenv("JOB_COMPLETION_INDEX", "0"))
    )

    parser.add_argument(
        "--tasks",
        type=int,
        default=int(os.getenv("TOTAL_TASKS", "16"))
    )

    parser.add_argument(
        "--input-dir",
        default=os.getenv(
            "INPUT_DIR",
            "datos/entrada/imagenette2/val"
        )
    )

    parser.add_argument(
        "--output-dir",
        default=os.getenv("OUTPUT_DIR", "datos/salida")
    )

    parser.add_argument(
        "--strategy",
        choices=["block", "cyclic", "lpt"],
        default="block"
    )

    parser.add_argument(
        "--save-edges",
        action="store_true"
    )

    return parser.parse_args()


def list_images(input_dir):
    start = time.perf_counter()

    images = sorted(
        path for path in Path(input_dir).rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )

    elapsed = time.perf_counter() - start

    return images, elapsed


def select_images(images, index, tasks, strategy="block"):
    if strategy == "cyclic":
        return images[index::tasks]
    if strategy == "lpt":
        # Coste estimado por tamaño comprimido. Los empates respetan ruta e índice.
        weighted = sorted((-path.stat().st_size, path) for path in images)
        loads = [(0, task) for task in range(tasks)]
        assigned = []
        for negative_size, path in weighted:
            load, task = heapq.heappop(loads)
            if task == index:
                assigned.append(path)
            heapq.heappush(loads, (load - negative_size, task))
        return assigned
    total = len(images)

    # Reparto por bloques contiguos.
    base = total // tasks
    remainder = total % tasks

    start = index * base + min(index, remainder)
    count = base + (1 if index < remainder else 0)

    return images[start:start + count]


def process_image(image_path):
    import cv2
    import numpy as np

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError("No se pudo leer la imagen")

    height, width = image.shape[:2]
    size_bytes = image_path.stat().st_size

    # 1. Escala de grises
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 2. Desenfoque gaussiano
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Filtro Sobel
    sobel_x = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)

    magnitude = cv2.magnitude(sobel_x, sobel_y)

    magnitude = cv2.normalize(
        magnitude, None, 0, 255, cv2.NORM_MINMAX
    ).astype(np.uint8)

    # 4. Umbral
    _, edges = cv2.threshold(
        magnitude, 50, 255, cv2.THRESH_BINARY
    )

    edge_ratio = float(np.count_nonzero(edges) / edges.size)

    return {
        "width": width,
        "height": height,
        "size_bytes": size_bytes,
        "edge_ratio": edge_ratio,
        "edges": edges
    }


def main():
    args = get_arguments()

    if args.tasks < 1 or not 0 <= args.index < args.tasks:
        raise ValueError("Indice o numero de tareas invalido")

    import cv2

    if os.getenv("FAIL_INDEX") == str(args.index):
        print(f"Fallo de prueba en índice {args.index}", flush=True)
        raise SystemExit(42)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Listar las imagenes
    images, list_seconds = list_images(args.input_dir)

    if not images:
        raise RuntimeError("No se encontraron imagenes")

    # Seleccionar las imagenes de este worker
    assigned_images = select_images(
        images, args.index, args.tasks, args.strategy
    )

    print(
        f"Worker {args.index}: "
        f"{len(assigned_images)} imagenes asignadas"
    )

    part_name = f"part-{args.index:04d}"
    csv_path = output_dir / f"{part_name}.csv"
    json_path = output_dir / f"{part_name}.json"

    edges_dir = output_dir / "bordes" / part_name

    if args.save_edges:
        edges_dir.mkdir(parents=True, exist_ok=True)

    total_start = time.perf_counter()
    total_errors = 0

    rows = []

    for image_path in assigned_images:
        image_start = time.perf_counter()

        try:
            result = process_image(image_path)

            processing_ms = (
                time.perf_counter() - image_start
            ) * 1000

            if args.save_edges:
                destination = edges_dir / (str(image_path.relative_to(args.input_dir)) + ".png")
                destination.parent.mkdir(parents=True, exist_ok=True)

                saved = cv2.imwrite(str(destination), result["edges"])

                if not saved:
                    raise RuntimeError(
                        f"No se pudo guardar la imagen: {destination}"
                    )

            rows.append({
                "filename": str(image_path.relative_to(args.input_dir)),
                "width": result["width"],
                "height": result["height"],
                "size_bytes": result["size_bytes"],
                "processing_ms": round(processing_ms, 3),
                "edge_ratio": round(result["edge_ratio"], 6),
                "status": "ok",
                "error": ""
            })

        except Exception as error:
            total_errors += 1

            rows.append({
                "filename": str(image_path),
                "width": 0,
                "height": 0,
                "size_bytes": 0,
                "processing_ms": round(
                    (time.perf_counter() - image_start) * 1000, 3
                ),
                "edge_ratio": 0,
                "status": "error",
                "error": str(error)
            })

            print(f"Error procesando {image_path}: {error}")

    total_seconds = time.perf_counter() - total_start

    # Guardar CSV
    fieldnames = [
        "filename",
        "width",
        "height",
        "size_bytes",
        "processing_ms",
        "edge_ratio",
        "status",
        "error"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Guardar JSON
    summary = {
        "index": args.index,
        "tasks": args.tasks,
        "strategy": args.strategy,
        "node": os.getenv("NODE_NAME", socket.gethostname()),
        "images_assigned": len(assigned_images),
        "images_processed": sum(r["status"] == "ok" for r in rows),
        "errors": total_errors,
        "list_seconds": round(list_seconds, 6),
        "total_seconds": round(total_seconds, 6),
        "csv_file": str(csv_path)
    }

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)

    print(json.dumps(summary, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
