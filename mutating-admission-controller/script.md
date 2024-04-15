073  k delete -f MAC-deploy.yaml -f webhook-config.yaml 
 1074  docker build -t ma-controller:latest --rm .
 1075  kind load docker-image ma-controller:latest
 1076  k apply -f MAC-deploy.yaml 
 1077  k apply -f webhook-config.yaml 
 1078  curl -kv -d '{"1":{"kind-worker":0,"kind-worker2":1},"2":{"kind-worker":0,"kind-worker2":2},"3":{"kind-worker":0,"kind-worker2":3},"4":{"kind-worker":0,"kind-worker2":4},"5":{"kind-worker":1,"kind-worker2":4}}' https://localhost:8443/schedule
