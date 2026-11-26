
import argparse
import csv
import json
from pathlib import Path

from statistics import mean


def read_csv_files(input_dir):
    rows = []

    csv_files = sorted(input_dir.glob("part-*.csv"))

    if not csv_files:
        raise FileNotFoundError("No se encontraron archivos part-*.csv")

    for csv_file in csv_files:
        with open(csv_file, "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows.extend(reader)

    return rows


def read_json_files(input_dir):
    summaries = []

    json_files = sorted(input_dir.glob("part-*.json"))

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as file:
            summaries.append(json.load(file))

    if not summaries:
        raise FileNotFoundError("No se encontraron archivos part-*.json")

    return summaries


def save_results(rows, output_dir):
    output_file = output_dir / "resultados.csv"

    if not rows:
        raise ValueError("No hay resultados para guardar")

    with open(output_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return output_file


def calculate_imbalance(summaries):
    times = [item["total_seconds"] for item in summaries]

    average = float(mean(times))
    maximum = float(max(times))

    imbalance = maximum / average if average > 0 else 0

    return {
        "average_worker_seconds": round(average, 6),
        "max_worker_seconds": round(maximum, 6),
        "min_worker_seconds": round(float(min(times)), 6),
        "imbalance": round(imbalance, 6)
    }


def create_mosaic(input_dir, output_dir, count=16, columns=4):
    edges_dir = input_dir / "bordes"

    images = sorted(edges_dir.rglob("*.png"))[:count]

    if not images:
        print("No hay imagenes de bordes para crear el mosaico.")
        return None

    import cv2
    import numpy as np

    thumb_width = 240
    thumb_height = 180

    tiles = []

    for image_path in images:
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            continue

        resized = cv2.resize(image, (thumb_width, thumb_height))

        tiles.append(resized)

    if not tiles:
        print("No se pudieron leer imagenes para el mosaico.")
        return None

    rows = []

    for start in range(0, len(tiles), columns):
        current = tiles[start:start + columns]

        while len(current) < columns:
            current.append(
                np.zeros((thumb_height, thumb_width), dtype=np.uint8)
            )

        rows.append(np.hstack(current))

    mosaic = np.vstack(rows)

    output_file = output_dir / "mosaico.png"

    cv2.imwrite(str(output_file), mosaic)

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Unir resultados de los workers"
    )

    parser.add_argument(
        "--input-dir",
        default="datos/salida"
    )

    parser.add_argument(
        "--mosaic-count",
        type=int,
        default=16
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = input_dir

    if not input_dir.exists():
        raise FileNotFoundError(f"No existe {input_dir}")

    rows = read_csv_files(input_dir)
    summaries = read_json_files(input_dir)

    tasks = summaries[0]["tasks"]
    expected = {f"part-{i:04d}" for i in range(tasks)}
    for extension in ("csv", "json"):
        if {p.stem for p in input_dir.glob(f"part-*.{extension}")} != expected:
            raise ValueError("Conjunto de índices incompleto o inesperado")
    for stem, part in zip(sorted(expected), summaries):
        if (part["tasks"] != tasks or part["strategy"] != summaries[0]["strategy"]
                or stem != f"part-{part['index']:04d}"):
            raise ValueError("Metadatos de partes incompatibles")
        with (input_dir / (stem + ".csv")).open() as stream:
            statuses = [row["status"] for row in csv.DictReader(stream)]
        if (len(statuses) != part["images_assigned"]
                or statuses.count("ok") != part["images_processed"]
                or statuses.count("error") != part["errors"]
                or set(statuses) - {"ok", "error"}):
            raise ValueError(f"Conteos inconsistentes en {stem}")
    if len({row["filename"] for row in rows}) != len(rows):
        raise ValueError("Hay imágenes duplicadas")
    results_file = save_results(rows, output_dir)

    successful = sum(row["status"] == "ok" for row in rows)
    errors = sum(row["status"] == "error" for row in rows)

    imbalance = calculate_imbalance(summaries)

    summary = {
        "total_images": len(rows),
        "processed_images": successful,
        "errors": errors,
        "workers": len(summaries),
        "strategy": summaries[0].get("strategy", "unknown"),
        "worker_times": [
            {
                "index": item["index"],
                "seconds": item["total_seconds"]
            }
            for item in summaries
        ],
        **imbalance
    }

    summary_file = output_dir / "summary.json"

    with open(summary_file, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)

    mosaic_file = create_mosaic(
        input_dir,
        output_dir,
        count=args.mosaic_count
    )

    print("\n========== RESULTADOS ==========")
    print(f"Imagenes encontradas: {len(rows)}")
    print(f"Procesadas correctamente: {successful}")
    print(f"Errores: {errors}")
    print(f"Workers: {len(summaries)}")
    print(f"Desbalance: {imbalance['imbalance']}")
    print(f"CSV: {results_file}")
    print(f"JSON: {summary_file}")
    print(f"Mosaico: {mosaic_file}")
    print("================================")


if __name__ == "__main__":
    main()
