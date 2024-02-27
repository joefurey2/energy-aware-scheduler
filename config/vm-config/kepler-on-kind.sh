git clone --depth 1 git@github.com:sustainable-computing-io/kepler.git
cd ./kepler
make build-manifest OPTS="CI_DEPLOY PROMETHEUS_DEPLOY"
kubectl apply -f _output/generated-manifest/deployment.yaml
