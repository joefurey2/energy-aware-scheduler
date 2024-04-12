This is my implementation of a basic Mutating Admission Controller (MAC)

Link to K8 [docs][https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/]

My approach to implement an energy aware scheduling will be to use a MAC

The MAC will recieve all pods and deployments before they are scheduled

The MAC will be aware of current energy efficiency of nodes

The MAC will modify the pods due to be scheduled. It will set the affinity 

## To setup locally:

Note: I am using an M1 Mac and Podman

1. Create kind cluster on local machine - Will need podman/docker and kind installed

    - To start kind cluster, run ```kind create cluster --config ./config/kind-config.yaml```
    - To test cluster is running and configured correctly, ```k get nodes``` should return details about the 3 nodes in the cluster
2. Label the nodes within the cluster
    - The nodes need to be labelled so that the MAC can find them
    - To do this, all nodes need to be given an identifier
    - Run the below command, changing the name for each node to label them node from 1 to X (1-3 if using my kind config)
        - ```k label nodes test-cluster-worker node=1 ```
    - To test labelling, run
        - ```k get nodes -L node ```

2. The controller image needs to be built and pushed to the kind cluster
    - In the directory with the dockerfile, run ```podman build -t ma-controller:latest --rm .  ```
    - Ensure the image is pushed to the kind cluster
        - Podman desktop -> images -> ma-controller -> push to kind cluster
3. The controller needs to be deployed to the cluster
*Note: The controller must be deployed before the webhook kubernetes configuration is deployed or it will not succeed*
    - The file service-deploy needs to be deployed to the cluster
    - ```k apply -f ./config/k8s-resources/service-deploy.yaml```
4. The webhook configuration file needs to be deployed
    - ```k apply -f ./config/k8s-resources/webhook-config.yaml```

The Mutating Admission Controller should now be deployed

## To test and use:

### Adding a ranking of efficiency
A ranking of 'node efficiency' needs to be passed to the MAC

Currently there is no mechanism/service to do this within the cluster.

Therefore we need to port forward so that external HTTP calls can reach the MAC. 

*Note: when making any curl command for testing, use -k to ignore the https certificate validation*

Steps:
1. Port forward the service
    - ```k port-forward service/mutating-admission-controller  8443:443```
2. Pass a ranking to the controller:
*note: By default, you cannot schedule to the control-plane node*
    - After port-forwarding, the MAC endpoint is available at https://localhost:8443
    - There is an api endpoint where a ranking can be posted too
    - The endpoint requires the naming labels specified above to be passed with an equivalent ranking
    - "nodeID":"EfficiencyVal"
    - The lower the numbr specified, the more efficient
    - ```curl -kv -H "Content-Type: application/json" -d '{"1":1, "2":2, "3":3 }' https://localhost:8443/ranking```
    - The command above specifies efficiencies for node 1:1, 2:2 and 3:3. This means the controller will try and schedule on the most efficient node which will be 1, as it has the lowest val

To get the current rank, a GET call to the endpoint https://localhost:8443/ranking will return the ranking:
- ```curl -kv -H "Content-Type: application/json"  https://localhost:8443/ranking```

## Scheduling a pod
After following the steps above, the MAC should be created and a ranking has been configured.

To test the sceduling mechanism:
 - Deploy the test-pod 
    - ```k apply -f test-pod.yaml```
- Check the test-pod has been mutated:
    - ```k describe pod testpod```

The testpod should:
- Be scheduled on the pod that is the 'most efficient'
    - The node that has the lowest efficiency score passed previously
    - For me, this is Node:  test-cluster-worker/10.89.0.2
- The label ```modified``` should indicate the nodeID the MAC scheduled the pod on
    - For me, this was ```modified=modifiedTo1```