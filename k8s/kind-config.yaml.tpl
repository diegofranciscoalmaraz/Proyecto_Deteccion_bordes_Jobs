# Clúster kind: 1 control-plane + 3 workers.
# La carpeta datos/ del equipo se monta en /data de CADA nodo, así todos los
# pods ven las mismas fotos (/data/entrada) y escriben en el mismo lugar (/data/salida).
# ${DATOS_DIR} lo sustituye scripts/crear-cluster.sh con la ruta absoluta de datos/.
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: bordes
nodes:
  - role: control-plane
  - role: worker
    extraMounts:
      - hostPath: ${DATOS_DIR}
        containerPath: /data
  - role: worker
    extraMounts:
      - hostPath: ${DATOS_DIR}
        containerPath: /data
  - role: worker
    extraMounts:
      - hostPath: ${DATOS_DIR}
        containerPath: /data
