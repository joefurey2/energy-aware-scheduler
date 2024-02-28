# Guide for configuring VM

Need to install:
- Kubectl
- Kubernetes
- Docker
- Prometheus
- Kepler
- go
- Make

# To set up prometheus and grafana

Prometheus

In kube-prometheus folder
kubectl apply --server-side -f manifests/setup
    until kubectl get servicemonitors --all-namespaces ; do date; sleep 1; echo ""; done
kubectl apply -f manifests/

kepler:

# git clone --depth 1 https://github.com/sustainable-computing-io/kepler.git

cd ./kepler
make build-manifest OPTS="CI_DEPLOY PROMETHEUS_DEPLOY"
kubectl apply -f _output/generated-manifest/deployment.yaml

To import grafana dashboard:
Json model: https://raw.githubusercontent.com/sustainable-computing-io/kepler/main/grafana-dashboards/Kepler-Exporter.json