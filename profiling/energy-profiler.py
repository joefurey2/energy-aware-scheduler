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

def createPod(v1, podTemplate, podName, namespace="default"):
    podTemplate["metadata"]["name"] = podName
    v1.create_namespaced_pod(body=podTemplate, namespace=namespace)

def waitForPodCompletion(v1, podName, namespace="default"):
    while True:
        podStatus = v1.read_namespaced_pod_status(podName, namespace).status.phase
        if podStatus == "Succeeded" or podStatus == "Failed":
            time.sleep(5) # Ensures pod has finished and closed before metric is taken
            break
        time.sleep(1)

def deletePod(v1, podName, namespace="default"):
    try:
        v1.delete_namespaced_pod(name=podName, namespace=namespace)
    except client.exceptions.ApiException as e:
        print(f"Exception when calling CoreV1Api->delete_namespaced_pod: {e}")

def runPods(v1, podTemplate, numInstances):
    metrics = {}
    slept = False
    podNames = []
    for i in range(1, numInstances + 1):
        print(f"Running {i} pod(s)...")
        metrics[i] = []
        podNames = []
        for j in range(i):
            podName = f"stress-{i}instance-pod{j+1}"
            print(f"Creating pod {podName}...")
            createPod(v1, podTemplate, podName)
            podNames.append(podName)
        for podName in podNames:
            podName = f"stress-{i}instance-pod{j+1}"
            print(f"Waiting for pod {podName} to complete...")
            waitForPodCompletion(v1, podName)
        time.sleep(5) # Maybe 10 would be better
        for podName in podNames:
            print(f"Getting metric for pod {podName}...")
            energy = getMetric(podName)
            print("podName", podName, "energy", energy)
            metrics[i].append({"podName": podName, "energy": energy})
        for podName in podNames:
            deletePod(v1, podName)
        print(f"Finished running {i} pod(s), deleted pods and cleanedup")
    return metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("nodeName", help="the name of the node where the pods will be scheduled")
    parser.add_argument("numInstances", type=int, help="the number of pod instances to create")
    args = parser.parse_args()

    config.load_kube_config()
    v1 = client.CoreV1Api()

    podTemplate["spec"]["nodeName"] = args.nodeName
    podTemplate["metadata"]["labels"]["test"] = f"{args.nodeName}-{args.numInstances}" 

    metrics = runPods(v1, podTemplate, args.numInstances)  # replace with your actual values
    for numInstances, pods in metrics.items():
        print(f"Number of instances: {numInstances}")
        totalEnergy = 0
        for pod in pods:
            print(f"Pod: {pod['podName']}, Energy: {pod['energy']}")
            totalEnergy += float(pod['energy'])
        print(f"Total energy for {numInstances} instances: {totalEnergy}")
        averageEnergy = totalEnergy / len(pods)
        print(f"Average energy per pod for {numInstances} instances: {averageEnergy}")

        with open(f'{args.nodeName}-{args.numInstances}.csv', 'w', newline='') as csvfile:
            fieldnames = ['num_instances', 'pod_name', 'pod_energy']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for numInstances, pods in metrics.items():
                totalEnergy = sum(float(pod['energy']) for pod in pods)
                averageEnergy = totalEnergy / len(pods)
                for pod in pods:
                    writer.writerow({
                        'num_instances': numInstances,
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