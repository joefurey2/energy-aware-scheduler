# Mutating admission controller

This folder contains code to deploy my Mutating Admission controller

## Prerequisites
- You need to retrieve the certificate authority bundle and add it to the webhook config, so that requests can be communicated securely
    - ```kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[].cluster.certificate-authority-data}' ``` 
- You also need to generate a certificate for the MAC to use
    - ```cd ./ssl```
    - ```bash genSSH.sh ```
    - This will generate a key and certificate to use

## Steps to set up and configure
1. First, build the MAC docker image
    - ```build -t ma-controller:latest --rm .```
2. (Optional) Load updated docker image into kind cluster
    - ```kind load docker-image ma-controller:latest```
3. Deploy the mutating admission controller to the cluster
    - ```kubectl apply -f MAC-deploy.yaml```
4. Configure the cluster to forward requests to the controller
    - ```kubectl apply -f webhook-config.yaml```

The MAC should now be set up and configured

## Testing
- The complete profiling script will automatically push an updated optimal schedule to the MAC  
    - (TODO: CHECK NO CERT ISSUES)
- Alternatively, you can interact with the MAC yourself

First, port forward so you can interact from your cli
- ```kubectl port-forward svc/mutating-admission-controller 8443:443```

- You can then push any schedule to the mac or get current optimal schedule

