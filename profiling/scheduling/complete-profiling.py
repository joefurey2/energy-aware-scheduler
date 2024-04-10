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

def runPods(v1, podTemplate, numInstances, nodes):
    metrics = {}
    allPodNames = {}
    for i in range(1, numInstances + 1):
        metrics[str(i) + 'instance'] = []
        for combination in itertools.combinations(nodes, i):
            nodeCounts = {node: combination.count(node) for node in nodes}
            combinationMetrics = {}
            counter = 1
            for nodeName, count in nodeCounts.items():
                print(f"Running {count} pod(s) on {nodeName}...")
                podNames = []
                for j in range(count):
                    combinationKey = '-'.join(f"{nodeCounts.get(node, 0)}{node}" for node in nodes)
                    podName = f"instances{i}-{combinationKey}-pod{counter}"
                    print(f"Creating pod {podName}...")
                    createPod(v1, podTemplate, podName, nodeName)
                    counter +=1
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
                    combinationKey = '-'.join(f"{nodeCounts.get(node, 0)}{node}" for node in nodes)
                    if combinationKey not in combinationMetrics:
                        combinationMetrics[combinationKey] = []
                    combinationMetrics[combinationKey].append({"podName": podName, "energy": energy})
            print(f"Finished running pods on {nodeName}")
            metrics[str(i) + 'instance'].append(combinationMetrics)
            allPodNames = {}
    return metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instances', type=int, required=True)
    parser.add_argument('--nodes', nargs='+', required=True)
    args = parser.parse_args()

    nodes = args.nodes

    config.load_kube_config()
    v1 = client.CoreV1Api()


    podTemplate["metadata"]["labels"]["test"] = f"full-profiling" 


    metrics = runPods(v1, podTemplate, args.instances+1, nodes)  
    print(metrics.items)
    for numInstances, combinations in metrics.items():
        print(f"Number of pods: {numInstances}")
        minEnergy = float('inf')
        minEnergyCombination = None
        for combination in combinations:
            totalEnergyCombination = 0
            for combination, pods in combination.items():
                print(f"Combination: {combination}")
                totalEnergy = 0
                for pod in pods:
                    print(f"Pod: {pod['podName']}, Energy: {pod['energy']}")
                    totalEnergy += float(pod['energy'])
                print(f"Total energy for {combination}: {totalEnergy}")
                averageEnergy = totalEnergy / len(pods)
                print(f"Average energy per pod for {combination}: {averageEnergy}\n")
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