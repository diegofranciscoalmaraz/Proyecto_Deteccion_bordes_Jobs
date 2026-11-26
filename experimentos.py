"""Ejecutar y reanudar la matriz de Imagenette para el equipo 1."""
import argparse
import csv
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parent
INPUT = "/data/entrada/imagenette2/val"
LEVELS = (1, 2, 4, 8)
STRATEGIES = ("block", "cyclic", "lpt")
FIELDS = ("estrategia", "p", "repeticion", "job", "inicio", "fin", "segundos", "imagenes", "desbalance")


def launch(strategy, tasks, parallel, fail=""):
    name = f"bordes-{strategy}-{uuid.uuid4().hex[:16]}"
    env = dict(os.environ, STRATEGY=strategy, SAVE_EDGES="0", RUN_ID=name, FAIL_INDEX=fail)
    run = subprocess.run(["bash", "scripts/lanzar-job.sh", str(tasks), str(parallel), INPUT],
                         cwd=ROOT, env=env)
    return name, run.returncode


def measurement(name, strategy, parallel, repetition):
    evidence = ROOT / "docs/evidencias" / name
    job = json.loads((evidence / "job.json").read_text())
    status, spec = job["status"], job["spec"]
    if (job["metadata"]["name"] != name or spec["completionMode"] != "Indexed"
            or spec["completions"] != 16 or spec["parallelism"] != parallel
            or status.get("succeeded") != 16 or not any(
                c["type"] == "Complete" and c["status"] == "True" for c in status.get("conditions", []))):
        raise ValueError(f"Job incompleto o incompatible: {name}")
    summary = json.loads((ROOT / "datos/salida" / name / "summary.json").read_text())
    if (summary["strategy"] != strategy or summary["workers"] != 16 or summary["errors"]
            or summary["processed_images"] != 3925 or summary["total_images"] != 3925):
        raise ValueError(f"Cobertura incorrecta: {name}")
    start, end = status["startTime"], status["completionTime"]
    seconds = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    if seconds <= 0:
        raise ValueError(f"Tiempo inválido: {name}")
    return dict(zip(FIELDS, (strategy, parallel, repetition, name, start, end, seconds, 3925, summary["imbalance"])))


def failure_test():
    name, code = launch("block", 2, 2, fail="0")
    evidence = ROOT / "docs/evidencias" / name
    job = json.loads((evidence / "job.json").read_text())
    pods = json.loads((evidence / "pods.json").read_text())["items"]
    attempts = [p for p in pods if p["metadata"]["annotations"].get(
        "batch.kubernetes.io/job-completion-index") == "0" and p["status"]["phase"] == "Failed"
        and any(c.get("state", {}).get("terminated", {}).get("exitCode") == 42
                for c in p["status"].get("containerStatuses", []))]
    status = job["status"]
    if not (code and job["spec"]["backoffLimitPerIndex"] == 2 and len(attempts) == 3
            and status.get("failedIndexes") == "0" and status.get("completedIndexes") == "1"
            and any(c["type"] == "Failed" and c["status"] == "True" for c in status["conditions"])):
        raise ValueError(f"El fallo observado no verifica el reintento por índice: {name}")
    print(f"Prueba verificada: {evidence}")


def matrix():
    path = ROOT / "tiempos.csv"
    rows = []
    done = set()
    if path.exists():
        for row in csv.DictReader(path.read_text().splitlines()):
            key = row["estrategia"], int(row["p"]), int(row["repeticion"])
            verified = measurement(row["job"], *key)
            if key in done or any(str(verified[k]) != row[k] for k in FIELDS):
                raise ValueError("Registro duplicado o discordante con las evidencias")
            rows.append(verified)
            done.add(key)
    for rep in range(1, 4):
        for parallel in LEVELS:
            for strategy in STRATEGIES:
                if (strategy, parallel, rep) in done:
                    continue
                name, code = launch(strategy, 16, parallel)
                if code:
                    raise SystemExit(f"Corrida interrumpida. Revisar docs/evidencias/{name}")
                rows.append(measurement(name, strategy, parallel, rep))
                tmp = path.with_suffix(".tmp")
                with tmp.open("w", newline="") as stream:
                    writer = csv.DictWriter(stream, FIELDS)
                    writer.writeheader()
                    writer.writerows(rows)
                tmp.replace(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probar-fallo", action="store_true")
    args = parser.parse_args()
    data = ROOT / "datos/entrada/imagenette2/val"
    if sum(p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"} for p in data.rglob("*")) != 3925:
        parser.exit(1, "Se requieren las 3925 imágenes de validación de Imagenette.\n")
    with (ROOT / ".ejecucion.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        failure_test() if args.probar_fallo else matrix()
