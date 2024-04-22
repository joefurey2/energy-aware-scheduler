import time
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect
import argparse
import csv
import itertools
import requests
import json

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

def runPods(v1, podTemplate, startInstance, numInstances, nodes):
    metrics = {}
    allPodNames = {}
    for i in range(startInstance, numInstances):
        print(f"Testing {i} pods across {len(nodes)} nodes...")
        metrics[str(i)] = []
        for combination in itertools.combinations_with_replacement(nodes, i):
            nodeCounts = {node: combination.count(node) for node in nodes}
            combinationMetrics = {}
            counter = 1
            for nodeName, count in nodeCounts.items():
                if count > 0:
                    print(f"    Running {count} pod(s) on {nodeName}...")
                podNames = []
                for j in range(count):
                    combinationKey = '-'.join(f"{nodeCounts.get(node, 0)}{node}" for node in nodes)
                    podName = f"instances{i}-{combinationKey}-pod{counter}"
                    print(f"        Creating pod {podName}...")
                    createPod(v1, podTemplate, podName, nodeName)
                    counter +=1
                    podNames.append(podName)
                allPodNames[nodeName] = podNames
            for nodeName, podNames in allPodNames.items():
                for podName in podNames:
                    print(f"        Waiting for pod {podName} to complete...")
                    waitForPodCompletion(v1, podName)
            time.sleep(20) 
            for nodeName, podNames in allPodNames.items():
                for podName in podNames:
                    energy = getMetric(podName)
                    if energy == 0:
                        print("kepler stopped working at ", i)
                        print(metrics.items())
                        return metrics
                    combinationKey = '-'.join(f"{nodeCounts.get(node, 0)}{node}" for node in nodes)
                    if combinationKey not in combinationMetrics:
                        combinationMetrics[combinationKey] = []
                    combinationMetrics[combinationKey].append({"nodeName": nodeName, "podName": podName, "energy": energy})
                    deletePod(v1, podName)
            metrics[str(i)].append(combinationMetrics)
            allPodNames = {}
    return metrics

def find_optimal_scheduling(metrics, nodes):
    optimal_scheduling = {}

    for numInstances, combinations in metrics.items():
        min_energy = float('inf')
        optimal_combination = None
        for combinationMetrics in combinations:
            for combination, pods in combinationMetrics.items():
                total_energy = sum(float(pod['energy']) for pod in pods)
                if total_energy < min_energy:
                    min_energy = total_energy
                    node_counts = {node: 0 for node in nodes}
                    for pod in pods:
                        node = pod['nodeName']
                        if node in node_counts:
                            node_counts[node] += 1
                        else:
                            node_counts[node] = 1
                    optimal_combination = node_counts
        optimal_scheduling[numInstances] = optimal_combination

    return optimal_scheduling




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instances', type=int, required=True)
    parser.add_argument('--nodes', nargs='+', required=True)
    parser.add_argument('--start', type=int)

    args = parser.parse_args()

    nodes = args.nodes

    config.load_kube_config()
    v1 = client.CoreV1Api()


    podTemplate["metadata"]["labels"]["test"] = f"full-profiling" 

    start = args.start if args.start else 1
    
    metrics = runPods(v1, podTemplate, start, args.instances+1, nodes)  
    schedule = find_optimal_scheduling(metrics, nodes)
    print(schedule.items())
    for numInstances, combinations in metrics.items():
        print(f"Number of pods: {numInstances}")
        minEnergy = float('inf')
        minEnergyCombination = None
        for combination in combinations:
            totalEnergyCombination = 0
            for combination, pods in combination.items():
                totalEnergy = 0
                for pod in pods:
                    # print(f"Pod: {pod['podName']}, Energy: {pod['energy']}")
                    totalEnergy += float(pod['energy'])
                print(f"Total energy for {combination}: {totalEnergy}")
                # averageEnergy = totalEnergy / len(pods)
                # print(f"Average energy per pod for {combination}: {averageEnergy}\n")
                totalEnergyCombination += totalEnergy
                if totalEnergyCombination < minEnergy:
                    minEnergy = totalEnergyCombination
                    minEnergyCombination = combination
                print(f"Combination: {combination}, Total energy: {totalEnergyCombination}")
        print(f"Combination with minimum energy for {numInstances} instances: {minEnergyCombination}, Energy: {minEnergy}")



        filename = f'{args.instances}.csv'
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['numberOfInstances', 'combination', 'nodeName', 'podName', 'energyConsumption']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for numInstances, combinations in metrics.items():
                for combinationMetrics in combinations:
                    for combination, pods in combinationMetrics.items():
                        for pod in pods:
                            writer.writerow({
                                'numberOfInstances': numInstances,
                                'combination': combination,
                                'nodeName': pod['nodeName'],
                                'podName': pod['podName'],
                                'energyConsumption': pod['energy']
                            })

        try:
            print("Sending schedule to controller....")
            headers = {'Content-Type': 'application/json'}
            response = requests.post('https://localhost:8443/schedule', headers=headers, data=json.dumps(optimal_scheduling), verify=False)

            if response.status_code != 200:
                print(f"POST request failed with status code {response.status_code}")
        except:
            print("Couldnt connect to scheduling component!")


if __name__ == "__main__":
    main()