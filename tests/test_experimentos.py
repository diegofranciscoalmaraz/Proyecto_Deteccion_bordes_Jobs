import csv
import json
from itertools import product
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.worker import select_images
import experimentos
from experimentos import STRATEGIES, LEVELS


class Continuidad(unittest.TestCase):
    def test_repartos(self):
        with TemporaryDirectory() as tmp:
            files = [Path(tmp)/str(i) for i in range(5)]
            for path, size in zip(files, (5, 4, 3, 2, 1)):
                path.write_bytes(b"x"*size)
            expected = {"block":[0,1,2], "cyclic":[0,2,4], "lpt":[0,3,4]}
            for strategy in STRATEGIES:
                first = select_images(files,0,2,strategy)
                self.assertEqual(first,[files[i] for i in expected[strategy]])
                for count in (1,2,8,16):
                    parts = [select_images(files,i,count,strategy) for i in range(count)]
                    self.assertEqual(sorted(sum(parts,[])),files)

    def test_merge(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp)
            def merge():
                return subprocess.run([sys.executable, ROOT/"app/merge.py","--input-dir",tmp],
                                      capture_output=True).returncode
            for i in range(2):
                stem = path/f"part-{i:04d}"
                stem.with_suffix(".json").write_text(json.dumps(dict(tasks=2,index=i,
                    strategy="block",images_assigned=1,images_processed=1,errors=0,total_seconds=1)))
                stem.with_suffix(".csv").write_text(f"filename,status\n{i}.jpg,ok\n")
                if i == 0:
                    self.assertNotEqual(merge(),0)
            self.assertEqual(merge(),0)
            stem.with_suffix(".csv").write_text("filename,status\n0.jpg,ok\n")
            self.assertNotEqual(merge(),0)

    def test_matriz_y_reanudacion(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            attempts = []
            def launch(strategy, tasks, parallel):
                name = f"fixture-{len(attempts)}"
                attempts.append(name)
                if len(attempts) == 4:
                    return name, 1
                evidence = root/"docs/evidencias"/name
                evidence.mkdir(parents=True)
                job = dict(metadata=dict(name=name),spec=dict(completionMode="Indexed",
                    completions=tasks,parallelism=parallel),status=dict(succeeded=tasks,
                    conditions=[dict(type="Complete",status="True")],startTime="2026-01-01T00:00:00Z",
                    completionTime="2026-01-01T00:00:08Z"))
                (evidence/"job.json").write_text(json.dumps(job))
                out = root/"datos/salida"/name
                out.mkdir(parents=True)
                (out/"summary.json").write_text(json.dumps(dict(strategy=strategy,workers=tasks,
                    errors=0,processed_images=3925,total_images=3925,imbalance=1.1)))
                return name, 0
            with patch.object(experimentos,"ROOT",root), patch.object(experimentos,"launch",launch):
                with self.assertRaises(SystemExit):
                    experimentos.matrix()
                experimentos.matrix()
                experimentos.matrix()
            self.assertEqual(len(attempts),37)
            with (root/"tiempos.csv").open() as stream:
                rows = list(csv.DictReader(stream))
            combinations = {(r["estrategia"], int(r["p"]), int(r["repeticion"])) for r in rows}
            self.assertEqual(len(rows),36)
            self.assertEqual(combinations,set(product(STRATEGIES,LEVELS,range(1,4))))

if __name__ == "__main__":
    unittest.main()
