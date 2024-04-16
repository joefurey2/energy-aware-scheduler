# Mutating admission controller

This folder contains code to deploy my Mutating Admission controller

## Prerequisites
- You need to retrieve the certificate authority bundle and add it to the webhook config, so that requests can be communicated securely
    - ```kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[].cluster.certificate-authority-data}' ``` 
- You also need to generate a certificate for the MAC to use
    - ```cd ./ssl```
    - ```bash genSSH.sh ```
    - This will generate a key and certificate to use
- The default namespace needs to be MAC enabled so that pods are sent to the MAC
    - ```kubectl label namespace default MAC=enabled```

## Manual steps to set up and configure
1. First, build the MAC docker image
    - ```build -t ma-controller:latest --rm .```
2. (Optional) Load updated docker image into kind cluster
    - ```kind load docker-image ma-controller:latest```
3. Deploy the mutating admission controller to the cluster
    - ```kubectl apply -f MAC-deploy.yaml```
4. Configure the cluster to forward requests to the controller
    - ```kubectl apply -f webhook-config.yaml```

# Automated deployment

An automated bash script has been configured to automate the deployment process and all steps above

To run:
- ```bash deploy-mac.sh```

The MAC should now be set up and configured

## Testing
- The complete profiling script will automatically push an updated optimal schedule to the MAC  
    - (TODO: CHECK NO CERT ISSUES)
- Alternatively, you can interact with the MAC yourself

First, port forward so you can interact from your cli
- ```kubectl port-forward svc/mutating-admission-controller 8443:443```

- You can then push any schedule to the mac or get current optimal schedule

To push a new schedule 
'''curl -kv -d '{"1":{"kind-worker":0,"kind-worker2":1},"2":{"kind-worker":0,"kind-worker2":2},"3":{"kind-worker":0,"kind-worker2":3},"4":{"kind-worker":0,"kind-worker2":4},"5":{"kind-worker":1,"kind-worker2":4}}' https://localhost:8443/schedule'''

To get the current schedule
'''curl -k  https://localhost:8443/schedule'''
