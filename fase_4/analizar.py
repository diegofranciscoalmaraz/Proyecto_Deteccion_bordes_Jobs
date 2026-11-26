"""Generar el informe a partir de las 36 mediciones de Kubernetes."""
import argparse
import csv
from datetime import datetime
from itertools import product
import math
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
STRATEGIES = ("block", "cyclic", "lpt")
LEVELS = (1, 2, 4, 8)
COLORS = ("#11668a", "#ab4c13", "#496e26")


def metrics(path):
    groups = {}
    jobs = set()
    with path.open() as stream:
        for row in csv.DictReader(stream):
            key = row["estrategia"], int(row["p"]), int(row["repeticion"])
            seconds, imbalance = float(row["segundos"]), float(row["desbalance"])
            delta = datetime.fromisoformat(row["fin"]) - datetime.fromisoformat(row["inicio"])
            if (key in groups or row["job"] in jobs or int(row["imagenes"]) != 3925
                    or delta.total_seconds() != seconds or seconds <= 0
                    or not math.isfinite(imbalance) or imbalance < 1):
                raise ValueError(f"Medición inválida o repetida: {key}")
            jobs.add(row["job"])
            groups[key] = seconds, imbalance
    if set(groups) != set(product(STRATEGIES, LEVELS, (1, 2, 3))):
        raise ValueError("Se requieren las 36 combinaciones completas")
    results = []
    for strategy in STRATEGIES:
        baseline = median(groups[strategy, 1, r][0] for r in range(1, 4))
        for p in LEVELS:
            seconds, imbalance = zip(*(groups[strategy, p, r] for r in range(1, 4)))
            t = median(seconds)
            speed = baseline / t
            results.append(dict(estrategia=strategy, p=p, mediana_s=t, min_s=min(seconds),
                                max_s=max(seconds), speedup=speed, eficiencia=speed/p,
                                f=(1/speed-1/p)/(1-1/p) if p > 1 else None, I=median(imbalance)))
    return results


def font(size):
    return ImageFont.truetype("DejaVuSans.ttf", size)


def chart(rows):
    page = Image.new("RGB", (1100, 560), "white")
    pen = ImageDraw.Draw(page)
    pen.text((32, 20), "Speedup por estrategia", font=font(32), fill="black")
    top = math.ceil(max(r["speedup"] for r in rows))
    def y(v):
        return 445 - 345 * v / top
    for i in range(6):
        v = top*i/5
        pen.line((90, y(v), 1010, y(v)), fill="#d5dce0")
        pen.text((20, y(v)-10), f"{v:.1f}", font=font(18), fill="black")
    for j, p in enumerate(LEVELS):
        pen.text((95+300*j, 456), str(p), font=font(20), fill="black")
    pen.text((400, 505), "Paralelismo del Job (pods)", font=font(20), fill="black")
    for i, (s, color) in enumerate(zip(STRATEGIES, COLORS)):
        points = [(100+300*j, y(r["speedup"])) for j,r in enumerate(r for r in rows if r["estrategia"] == s)]
        pen.line(points, fill=color, width=4)
        for x, height in points:
            pen.ellipse((x-5,height-5,x+5,height+5),fill=color)
        pen.text((550+i*150,30), s, fill=color, font=font(23))
    return page


def report(rows, out):
    out.mkdir(parents=True, exist_ok=True)
    with (out/"metricas.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    graph = chart(rows)
    graph.save(out/"speedup.png")
    page = Image.new("RGB", (1240,1754), "white")
    pen = ImageDraw.Draw(page)
    def line(y, text, size=25):
        pen.text((78,y),text,font=font(size),fill="#193747")
    line(65,"Detección de bordes en Imagenette",49)
    line(145,"Equipo 1  |  Rendimiento de Jobs indexados en Kubernetes",30)
    line(225,"Método",34)
    line(284,"3,925 imágenes por Job, 16 índices, 3 repeticiones por combinación.")
    line(330,"T(p) es la mediana de completionTime menos startTime de los tres Jobs.")
    line(376,"S = T(1)/T(p) por estrategia. E = S/p. Para p > 1, f = (1/S − 1/p)/(1 − 1/p).")
    line(422,"I es la mediana del cociente entre tiempo máximo y medio de los índices.")
    line(468,"LPT estima el costo en bytes. Los Jobs omiten la escritura de bordes.")
    line(540,"Resultados",34)
    line(606,"Estrategia    Pods       T (s)        S         E (%)        f         I")
    for j,r in enumerate(rows):
        fraction = "—" if r["f"] is None else f"{r['f']:.3f}"
        values = (r["estrategia"],str(r["p"]),f"{r['mediana_s']:.1f}",f"{r['speedup']:.2f}",
                  f"{100*r['eficiencia']:.1f}",fraction,f"{r['I']:.2f}")
        for x, value in zip((78,240,350,480,580,720,825),values):
            pen.text((x,655+39*j),value,font=font(24),fill="black")
    page.paste(graph.resize((880,448)),(70,1140))
    best = min(rows,key=lambda r:r["mediana_s"])
    line(1610,f"Menor mediana observada: {best['estrategia']} con p={best['p']}, {best['mediana_s']:.1f} s.")
    line(1655,"Los rangos mínimo y máximo por combinación se incluyen en metricas.csv.",22)
    details = Image.new("RGB", page.size, "white")
    pen = ImageDraw.Draw(details)
    line(65,"Interpretación de las mediciones",45)
    for i, strategy in enumerate(STRATEGIES):
        subset = [r for r in rows if r["estrategia"] == strategy]
        fastest = min(subset, key=lambda r: r["mediana_s"])
        last = subset[-1]
        y = 180 + i*300
        line(y, strategy.upper(), 31)
        line(y+64, f"Menor tiempo a p={fastest['p']}: {fastest['mediana_s']:.1f} s "
             f"(rango {fastest['min_s']:.1f}–{fastest['max_s']:.1f} s).")
        line(y+112, f"Con 8 pods, S={last['speedup']:.2f} y E={100*last['eficiencia']:.1f} %. "
             f"El desbalance mediano es {last['I']:.2f}.")
        line(y+160, f"La fracción serial efectiva estimada a p=8 es {last['f']:.3f}.")
    line(1140,"Alcance",31)
    line(1210,"Los tiempos incluyen planificación de pods, arranque, lectura y procesamiento.")
    line(1260,"El desbalance usa los tiempos del bucle de imágenes de cada índice.")
    line(1310,"Los tres workers de kind comparten los recursos físicos del mismo host.")
    line(1360,"La fracción efectiva incorpora sobrecostos y puede quedar fuera de [0, 1].")
    page.save(out/"reporte.pdf", resolution=150, save_all=True, append_images=[details])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv",type=Path,default=BASE.parent/"fase_3/tiempos.csv")
    parser.add_argument("--salida",type=Path,default=BASE/"resultados")
    args = parser.parse_args()
    if not args.csv.is_file():
        parser.exit(1, "Falta el CSV de las 36 corridas oficiales.\n")
    report(metrics(args.csv), args.salida)
