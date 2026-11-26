# Detección de bordes en Imagenette · Fase 3 · Experimentos

Esta entrega del equipo 1 continúa el worker Sobel, el almacenamiento compartido y el Job indexado de la fase 2. La carpeta contiene la aplicación, el Dockerfile y los manifiestos necesarios para trabajar de forma independiente.

## Preparar datos y clúster

Desde esta carpeta en Linux, con Docker operativo, kind compatible con la imagen de Kubernetes 1.33.1 (por ejemplo kind 0.29), kubectl, envsubst, curl y Python 3.13, ejecutar los siguientes comandos. kind crea un nodo de control y tres workers locales. Si el equipo ya tiene Imagenette, puede copiar su directorio completo a `datos/entrada/imagenette2` y omitir la descarga.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/descargar-datos.sh imagenette
bash scripts/crear-cluster.sh
bash scripts/crear-muestra.sh 400
bash scripts/lanzar-job.sh 8 4 /data/entrada/muestra400/val
```

El contexto es `kind-bordes-f34`, la imagen local es `bordes:f34` y los workers montan el directorio `datos` de esta copia. La prueba de continuidad genera ocho partes, el consolidado y el mosaico. Los resultados quedan en `datos/salida/<job>` y la evidencia del clúster en `docs/evidencias/<job>`.

## Fase 3 · Experimentos

```bash
python experimentos.py --probar-fallo
python experimentos.py
```

La prueba separada fuerza el fallo del índice 0 y comprueba tres pods fallidos (intento inicial y dos reintentos), la finalización del índice 1 y la condición terminal Failed del Job. La matriz procesa las 3,925 fotos completas con 16 índices por Job. Alterna estrategias dentro de cada nivel de paralelismo (1, 2, 4, 8) y repite el ciclo tres veces. Las tres estrategias usan la misma entrada ordenada. Block distribuye bloques contiguos, cyclic reparte por turnos y LPT asigna cada imagen en orden decreciente de bytes al índice con menor carga acumulada. En los empates decide la ruta y después el índice.

Cada corrida guarda el manifiesto, el Job JSON y los pods. El CSV registra una fila después de verificar los 16 índices, 3,925 imágenes procesadas y cero errores. Los segundos provienen de la diferencia entre completionTime y startTime. Las corridas omiten el guardado de PNG. Mantener fijos la imagen, los datos, los recursos y la máquina durante la serie. Si el proceso se interrumpe, comprobar que el Job anterior haya terminado antes de relanzar el comando. El programa valida contra las evidencias las filas ya guardadas y continúa con las combinaciones faltantes. Conservar juntos `tiempos.csv`, `docs/evidencias` y `datos/salida`.

La fase 4 consume el archivo completo de 36 mediciones.

## Validación local

```bash
python -m unittest discover -s tests -v
```

Las pruebas usan directorios temporales. Comprueban las particiones, la integridad del merge y la reanudación de la matriz de experimentos. El estado de la auditoría figura en `docs/auditoria.md`.
