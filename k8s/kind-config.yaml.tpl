# Clúster kind: 1 control-plane + 3 workers.
# La carpeta datos/ del equipo se monta en /data de cada worker, así todos los
# pods ven las mismas fotos (/data/entrada) y escriben en el mismo lugar (/data/salida).
# ${DATOS_DIR} lo sustituye scripts/crear-cluster.sh con la ruta absoluta de datos/.
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: bordes-f34
nodes:
  - role: control-plane
    image: kindest/node:v1.33.1
  - role: worker
    image: kindest/node:v1.33.1
    extraMounts:
      - hostPath: ${DATOS_DIR}
        containerPath: /data
  - role: worker
    image: kindest/node:v1.33.1
    extraMounts:
      - hostPath: ${DATOS_DIR}
        containerPath: /data
  - role: worker
    image: kindest/node:v1.33.1
    extraMounts:
      - hostPath: ${DATOS_DIR}
        containerPath: /data
