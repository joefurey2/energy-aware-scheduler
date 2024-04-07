# Guide for configuring VM

Need to install:
- Kubectl
- Kubernetes
- Docker
- Prometheus
- Kepler
- go
- Make

# Full config for kepler
This is the key page to help set up - https://sustainable-computing.io/installation/kepler-operator/
TODO: test if this works when installing prometheus/grafana

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

# To install k8s metric server
Curl to to get YAML deployment
Edit the deployment to pass the args --kublet-insecure-tls=true

curl -LJO https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
vim -> find deployment and add --kubelet-insecure-tls=true to args


# To import grafana dashboard:
Json model: https://raw.githubusercontent.com/sustainable-computing-io/kepler/main/grafana-dashboards/Kepler-Exporter.json


# To use and install Jmeter

Need to sudo dnf install java-17-openjdk

Need to install jmeter binary from https://jmeter.apache.org/download_jmeter.cgi

Use jmeter to run!