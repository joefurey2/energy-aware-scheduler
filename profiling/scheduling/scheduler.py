import time
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect
import argparse
import csv

config.load_kube_config()
v1 = client.CoreV1Api()

podTemplate = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "",
        "labels": {
            "test": ""
        }
    },
    "spec": {
        "nodeName": "",
        "containers": [
            {
                "name": "stress-ng-container",
                "image": "ubuntu:latest",
                "command": ["/bin/bash", "-c"],
                "args": [
                    "apt-get update && apt-get install -y stress-ng && stress-ng --cpu 1 --cpu-ops 80000  --metrics-brief"
                ],
                "resources": {
                    "requests": {
                        "cpu": "0.5",
                        "memory": "512Mi"
                    },
                    "limits": {
                        "cpu": "1",
                        "memory": "1Gi"
                    }
                }
            }
        ],
        "restartPolicy": "Never"
    }
}

def getMetric(podName):
    prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)
    metric= f'kepler_container_package_joules_total{{pod_name="{podName}"}}'
    energy = prom.get_current_metric_value(metric)[0]['value'][1]
    return energy

def createPod(v1, podTemplate, podName, nodeName, namespace="default"):
    podTemplate["metadata"]["name"] = podName
    podTemplate["spec"]["nodeName"] = nodeName
    v1.create_namespaced_pod(body=podTemplate, namespace=namespace)

def waitForPodCompletion(v1, podName, namespace="default"):
    while True:
        podStatus = v1.read_namespaced_pod_status(podName, namespace).status.phase
        if podStatus == "Succeeded" or podStatus == "Failed":
            break
        time.sleep(1)

def deletePod(v1, podName, namespace="default"):
    try:
        v1.delete_namespaced_pod(name=podName, namespace=namespace)
    except client.exceptions.ApiException as e:
        print(f"Exception when calling CoreV1Api->delete_namespaced_pod: {e}")

def runPods(v1, podTemplate, nodes):
    metrics = {}
    allPodNames = {}
    for nodeName, numInstances in nodes.items():
        print(f"Running {numInstances} pod(s) on {nodeName}...")
        metrics[nodeName] = []
        podNames = []
        for j in range(numInstances):
            podName = f"stress-{nodeName}-{numInstances}instance-pod{j+1}"
            print(f"Creating pod {podName}...")
            createPod(v1, podTemplate, podName, nodeName)
            podNames.append(podName)
        allPodNames[nodeName]= podNames
    for podName in allPodNames.items():
        for podName in podNames:
            print(f"Waiting for pod {podName} to complete...")
            waitForPodCompletion(v1, podName)
    time.sleep(10) # Maybe 10 would be better
    for nodeName, podNames in allPodNames.items():
        for podName in podNames:
            print(f"Getting metric for pod {podName}...")
            energy = getMetric(podName)
            metrics[nodeName].append({"podName": podName, "energy": energy})
        print(f"Finished running pods on {nodeName}. Deleting pods...")
        for podName in podNames:
            deletePod(v1, podName)
    return metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nodes', nargs='+', required=True)
    args = parser.parse_args()

    nodes = dict(zip(args.nodes[::2], map(int, args.nodes[1::2])))

    config.load_kube_config()
    v1 = client.CoreV1Api()

    print(str(nodes.items()))

    podTemplate["metadata"]["labels"]["test"] = f"scheduling-test" 
    # podTemplate["metadata"]["labels"]["nodes"] = f"{nodes.items()}" 


    metrics = runPods(v1, podTemplate, nodes)  # replace with your actual values
    print(metrics.items())
    for nodeName, pods in metrics.items():
        print(f"Node: {nodeName}")
        totalEnergy = 0
        for pod in pods:
            print(f"Pod: {pod['podName']}, Energy: {pod['energy']}")
            totalEnergy += float(pod['energy'])
        print(f"Total energy for {nodeName}: {totalEnergy}")
        averageEnergy = totalEnergy / len(pods)
        print(f"Average energy per pod for {nodeName}: {averageEnergy}")

    totalEnergyAllNodes = 0
    totalPodsAllNodes = 0
    for nodeName, pods in metrics.items():
        totalEnergyNode = sum(float(pod['energy']) for pod in pods)
        totalEnergyAllNodes += totalEnergyNode
        totalPodsAllNodes += len(pods)
    averageEnergyAllNodes = totalEnergyAllNodes / totalPodsAllNodes
    print(f"All Nodes, Total Energy: {totalEnergyAllNodes}, Average Energy: {averageEnergyAllNodes}")

    filename = '-'.join(f"{nodeName}-{numInstances}" for nodeName, numInstances in nodes.items()) + '.csv'
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['node_name', 'pod_name', 'pod_energy']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for nodeName, pods in metrics.items():
            for pod in pods:
                writer.writerow({
                    'node_name': nodeName,
                    'pod_name': pod['podName'],
                    'pod_energy': pod['energy']
                })
                # writer.writerow({
                #     'num_instances': numInstances,
                #     'pod_name': 'Total',
                #     'pod_energy': totalEnergy
                # })
                # writer.writerow({
                #     'num_instances': numInstances,
                #     'pod_name': 'Average',
                #     'pod_energy': averageEnergy
                # })

if __name__ == "__main__":
    main()