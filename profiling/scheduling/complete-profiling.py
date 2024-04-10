import time
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect
import argparse
import csv
import itertools

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
            # time.sleep(5)
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
    for numInstances in range(1, max(nodes.values()) + 1):
        metrics[str(numInstances) + 'instance'] = []
        for combination in itertools.combinations_with_replacement(nodes.keys(), numInstances):
            print(combination)
            nodeCounts = {node: combination.count(node) for node in set(combination)}
            combinationMetrics = {}
            for nodeName, numInstances in nodeCounts.items():
                print(f"Running {numInstances} pod(s) on {nodeName}...")
                podNames = []
                for j in range(numInstances):
                    podName = f"stress-{nodeName}-{numInstances}instance-pod{j+1}"
                    print(f"Creating pod {podName}...")
                    createPod(v1, podTemplate, podName, nodeName)
                    podNames.append(podName)
                allPodNames[nodeName] = podNames
            for nodeName, podNames in allPodNames.items():
                for podName in podNames:
                    print(f"Waiting for pod {podName} to complete...")
                    waitForPodCompletion(v1, podName)
            time.sleep(20) 
            for nodeName, podNames in allPodNames.items():
                for podName in podNames:
                    print(f"Getting metric for pod {podName}...")
                    energy = getMetric(podName)
                    combinationKey = '-'.join(f"{nodeCounts.get(node, 0)}{node}" for node in nodes.keys())
                    if combinationKey not in combinationMetrics:
                        combinationMetrics[combinationKey] = []
                    combinationMetrics[combinationKey].append({"podName": podName, "energy": energy})
            print(f"Finished running pods on {nodeName}. Deleting pods...")
            metrics[str(numInstances) + 'instance'].append(combinationMetrics)
            allPodNames = {}
    return metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instances', type=int, required=True)
    parser.add_argument('--nodes', nargs='+', required=True)
    args = parser.parse_args()

    nodes = dict(zip(args.nodes[::2], map(int, args.nodes[1::2])))

    config.load_kube_config()
    v1 = client.CoreV1Api()

    print(str(nodes.items()))

    podTemplate["metadata"]["labels"]["test"] = f"full-profiling" 


    metrics = runPods(v1, podTemplate, nodes)  
    for numInstances, combinations in metrics.items():
        print(f"Number of instances: {numInstances}")
        minEnergy = float('inf')
        minEnergyCombination = None
        for combination in combinations:
            totalEnergyCombination = 0
            for nodeName, pods in combination.items():
                print(f"Node: {nodeName}")
                totalEnergy = 0
                for pod in pods:
                    print(f"Pod: {pod['podName']}, Energy: {pod['energy']}")
                    totalEnergy += float(pod['energy'])
                print(f"Total energy for {nodeName}: {totalEnergy}")
                averageEnergy = totalEnergy / len(pods)
                print(f"Average energy per pod for {nodeName}: {averageEnergy}")
                totalEnergyCombination += totalEnergy
            if totalEnergyCombination < minEnergy:
                minEnergy = totalEnergyCombination
                minEnergyCombination = combination
            print(f"Combination: {combination}, Total energy: {totalEnergyCombination}")
        print(f"Combination with minimum energy for {numInstances} instances: {minEnergyCombination}, Energy: {minEnergy}")

    # totalEnergyAllNodes = 0
    # totalPodsAllNodes = 0
    # for numInstances, combinations in metrics.items():
    #     for combination in combinations:
    #         for nodeName, pods in combination.items():
    #             totalEnergyNode = sum(float(pod['energy']) for pod in pods)
    #             totalEnergyAllNodes += totalEnergyNode
    #             totalPodsAllNodes += len(pods)
    # averageEnergyAllNodes = totalEnergyAllNodes / totalPodsAllNodes
    # print(f"All Nodes, Total Energy: {totalEnergyAllNodes}, Average Energy: {averageEnergyAllNodes}")


    # filename = '-'.join(f"{nodeName}-{numInstances}" for nodeName, numInstances in nodes.items()) + '.csv'
    # with open(filename, 'w', newline='') as csvfile:
    #     fieldnames = ['node_name', 'pod_name', 'pod_energy']
    #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    #     writer.writeheader()
    #     for nodeName, pods in metrics.items():
    #         for pod in pods:
    #             writer.writerow({
    #                 'node_name': nodeName,
    #                 'pod_name': pod['podName'],
    #                 'pod_energy': pod['energy']
    #             })

if __name__ == "__main__":
    main()