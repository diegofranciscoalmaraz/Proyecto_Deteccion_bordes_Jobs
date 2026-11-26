# Fase 4 · Análisis de los experimentos de Imagenette

Desde esta carpeta, preparar Python 3.13, Pillow y la fuente DejaVu Sans. El analizador lee por defecto `../fase_3/tiempos.csv`. Si se entrega esta carpeta por separado, indicar la ubicación del CSV con `python analizar.py --csv /ruta/tiempos.csv`.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python analizar.py
```

A partir de las 36 filas, genera `resultados/metricas.csv`, `speedup.png` y un reporte técnico PDF de dos páginas. Para cada estrategia calcula la mediana y el rango de tres tiempos, speedup respecto de su propia mediana a un pod, eficiencia y fracción serial efectiva de Amdahl para p mayor que uno. El desbalance es la mediana de tres cocientes entre el tiempo máximo y el medio de los índices. El PDF interpreta los resultados medidos y señala la configuración con menor mediana. El reparto LPT utiliza el tamaño comprimido como aproximación al tiempo de procesamiento.

## Demostración de cinco minutos

| Minuto | Acción |
|---|---|
| 0–1 | Mostrar los cuatro nodos con `kubectl --context kind-bordes-f34 get nodes -o wide` y explicar el directorio compartido. |
| 1–2 | Mostrar el manifiesto de la corrida de 400 imágenes, sus ocho índices y el mosaico. |
| 2–3 | Abrir el Job y el listado de pods guardados por la prueba de fallo. Identificar los tres intentos del índice 0. |
| 3–4 | Abrir tiempos.csv, elegir una fila y contrastar sus segundos con los dos timestamps de su Job. |
| 4–5 | Mostrar la gráfica y el PDF. Explicar la combinación con menor mediana y su eficiencia. |

## Validación local

```bash
python -m unittest discover -s tests -v
```

Las pruebas generan 36 mediciones sintéticas en un directorio temporal, verifican las métricas y la exportación del reporte y comprueban que una matriz incompleta se rechace.
