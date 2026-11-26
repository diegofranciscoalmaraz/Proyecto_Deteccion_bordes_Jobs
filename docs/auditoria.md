# Auditoría de continuidad del equipo 1

La copia feature-kubernetes aporta el mismo worker, merge y Dockerfile de feature-worker y agrega la configuración del clúster. El seguimiento registra 3,925 imágenes procesadas en la prueba secuencial inicial. Las dos copias recibidas carecen de datos, historial Git utilizable y evidencia de un Job real.

| Hallazgo en la fase 2 | Tratamiento en esta entrega |
|---|---|
| El script de lanzamiento continuaba después de un Job fallido o de agotar la espera. | Espera una condición terminal, conserva el estado y propaga el fallo. Selecciona explícitamente el contexto del clúster dedicado. |
| El merge aceptaba partes ausentes. | Exige los índices esperados, pares CSV/JSON, conteos consistentes y nombres únicos. El registrador verifica además el total del dataset. |
| Un error al guardar PNG podía sumar dos filas por imagen. | El worker registra éxito tras guardar el PNG y conserva la ruta relativa y extensión original en el nombre de salida. |
| El script de muestra separaba por espacios y podía fallar en una tubería truncada. | La selección ordenada copia rutas completas y valida el tamaño solicitado. |
| La guía de inicio apuntaba a la copia anterior y omitía el argumento de descarga. | El README parte de esta carpeta e incluye el argumento imagenette. |

La verificación local cubrió tres estrategias, conjuntos incompletos, duplicados, cálculo de métricas y generación de la gráfica y el PDF con mediciones sintéticas temporales. Quedan pendientes el piloto, la prueba de fallo por índice y la matriz en un clúster real. En el entorno de auditoría faltan kind y las imágenes de validación, y el socket de Docker deniega acceso.
