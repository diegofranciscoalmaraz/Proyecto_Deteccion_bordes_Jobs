# Job indexado de detección de bordes (plantilla).
# Las variables ${...} las sustituye scripts/lanzar-job.sh con envsubst.
apiVersion: batch/v1
kind: Job
metadata:
  name: ${JOB_NAME}
spec:
  # Indexed: cada pod recibe JOB_COMPLETION_INDEX (0..completions-1);
  # worker.py lo usa para elegir sus fotos.
  completionMode: Indexed
  completions: ${COMPLETIONS}     # número de tareas (16 en los experimentos)
  parallelism: ${PARALLELISM}     # pods simultáneos como máximo
  # Reintentos por índice (K8s >= 1.33): un índice que falla no reinicia a los demás.
  backoffLimitPerIndex: 2
  maxFailedIndexes: ${COMPLETIONS}
  template:
    metadata:
      labels:
        app: bordes
    spec:
      restartPolicy: Never          # obligatorio con backoffLimitPerIndex
      # Reparte los pods entre los 3 workers de kind.
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              job-name: ${JOB_NAME}
      containers:
        - name: worker
          image: ${IMAGE}
          imagePullPolicy: IfNotPresent   # la imagen se carga con "kind load docker-image"
          command: ["sh", "-c"]
          args: ["python app/worker.py --strategy ${STRATEGY} ${SAVE_EDGES_FLAG}"]
          env:
            - name: TOTAL_TASKS
              value: "${COMPLETIONS}"
            - name: INPUT_DIR
              value: "${INPUT_DIR}"
            - name: OUTPUT_DIR
              value: "${OUTPUT_DIR}"
            - name: NODE_NAME          # nodo donde corrió el pod (sale en part-XXXX.json)
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
          resources:
            requests:
              cpu: "${CPU_REQUEST}"
              memory: "${MEM_REQUEST}"
            limits:
              cpu: "${CPU_LIMIT}"
              memory: "${MEM_LIMIT}"
          volumeMounts:
            - name: datos
              mountPath: /data
      volumes:
        - name: datos
          hostPath:
            path: /data               # carpeta montada por kind en cada nodo
            type: Directory
