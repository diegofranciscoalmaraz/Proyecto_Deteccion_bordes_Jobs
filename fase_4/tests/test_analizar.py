import csv
from datetime import datetime, timedelta, timezone
from itertools import product
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analizar import STRATEGIES, LEVELS, metrics, report

FIELDS = ("estrategia", "p", "repeticion", "job", "inicio", "fin", "segundos", "imagenes", "desbalance")


class Analisis(unittest.TestCase):
    def test_analisis(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp)/"tiempos.csv"
            start = datetime(2026,1,1,tzinfo=timezone.utc)
            with path.open("w",newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(FIELDS)
                for s,p,r in product(STRATEGIES,LEVELS,range(1,4)):
                    seconds = 80/p
                    writer.writerow((s,p,r,f"fixture-{s}-{p}-{r}",start.isoformat(),
                                    (start+timedelta(seconds=seconds)).isoformat(),seconds,3925,1))
            rows = metrics(path)
            self.assertEqual(len(rows),12)
            self.assertEqual(rows[-1]["speedup"],8)
            self.assertEqual(rows[-1]["f"],0)
            report(rows,Path(tmp))
            self.assertTrue((Path(tmp)/"reporte.pdf").read_bytes().startswith(b"%PDF"))
            path.write_text("\n".join(path.read_text().splitlines()[:-1]))
            with self.assertRaises(ValueError):
                metrics(path)


if __name__ == "__main__":
    unittest.main()
