import csv
import time
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect
import argparse
import csv

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

def createPod(v1, podTemplate, podName):
    podTemplate.metadata.name = podName
    v1.create_namespaced_pod(body=podTemplate, namespace="default")

def waitForPodCompletion(v1, podName):
    while True:
        pod = v1.read_namespaced_pod(name=podName, namespace="default")
        if pod.status.phase == "Succeeded" or pod.status.phase == "Failed":
            break
        time.sleep(1)

def getMetric(podName):
    prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)
    metric= f'kepler_container_package_joules_total{{pod_name="{podName}"}}'
    energy = prom.get_current_metric_value(metric)[0]['value'][1]
    return energy

def deletePod(v1, podName):
    v1.delete_namespaced_pod(name=podName, namespace="default")

def runPods(v1, podTemplate, numPods):
    metrics = []
    for j in range(numPods):
        podName = f"stress-pod{j+1}"
        print(f"Creating pod {podName}...")
        createPod(v1, podTemplate, podName)
    for j in range(numPods):
        podName = f"stress-pod{j+1}"
        print(f"Waiting for pod {podName} to complete...")
        waitForPodCompletion(v1, podName)
    time.sleep(10)
    for j in range(numPods):
        print(f"Getting metric for pod {podName}...")
        energy = getMetric(podName)
        metrics.append({"podName": podName, "energy": energy})
        print(f"Deleting pod {podName}...")
        deletePod(v1, podName)
    return metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pods', type=int, required=True)
    args = parser.parse_args()

    numPods = args.pods

    config.load_kube_config()
    v1 = client.CoreV1Api()

    podTemplate = client.V1Pod()

    metrics = runPods(v1, podTemplate, numPods)

    totalEnergy = sum(float(pod['energy']) for pod in metrics)
    averageEnergy = totalEnergy / numPods
    print(f"Total Energy: {totalEnergy}, Average Energy: {averageEnergy}")

    with open('all_energies.csv', 'w', newline='') as csvfile:
        fieldnames = ['pod_name', 'pod_energy']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for pod in metrics:
            writer.writerow({
                'pod_name': pod['podName'],
                'pod_energy': pod['energy']
            })

if __name__ == "__main__":
    main()

