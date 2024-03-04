# Guide for configuring VM

Need to install:
- Kubectl
- Kubernetes
- Docker
- Prometheus
- Kepler
- go
- Make

# Full config
This is the key page to help set up - https://sustainable-computing.io/installation/kepler-operator/

Steps:
 - cd kepler-operator
 - make fresh
     - After running it will tell you two commands to run. Run these
     - ./tmp/bin/operator-sdk run bundle localhost:5001/kepler-operator-bundle:0.0.0-dev --install-mode AllNamespaces --namespace operators --skip-tls
     - kubectl apply -f config/samples/kepler.system_v1alpha1_kepler.yaml
 - Port forward 3000

 You should now be able to access kepler and visualise energy consumption!


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
