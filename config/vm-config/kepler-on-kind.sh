git clone --depth 1 https://github.com/sustainable-computing-io/kepler.git
cd ./kepler
make build-manifest OPTS="CI_DEPLOY PROMETHEUS_DEPLOY"
kubectl apply -f _output/generated-manifest/deployment.yaml
