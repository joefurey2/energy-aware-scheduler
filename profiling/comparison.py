import time
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect
import argparse
import csv
from kubernetes.client.rest import ApiException

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

def waitForPodCompletion(v1, podName):
    while True:
        try:
            pod = v1.read_namespaced_pod(podName, "default")  # Replace "default" with your namespace if needed
            if pod.status.phase == "Succeeded" or pod.status.phase == "Failed":
                return pod.spec.node_name  # Return the node name when the pod completes
        except ApiException as e:
            print(f"Failed to get info for pod {podName}: {e}")
            return None
        time.sleep(1)

def deletePod(v1, podName, namespace="default"):
    try:
        v1.delete_namespaced_pod(name=podName, namespace=namespace)
    except client.exceptions.ApiException as e:
        print(f"Exception when calling CoreV1Api->delete_namespaced_pod: {e}")

def runPods(v1, podTemplate, numInstances, schedulingType):
    metrics = []
    allPodNames = []
    for i in range(1, numInstances):
        podName = f"{schedulingType}-pod-{i}"
        print(f"Creating pod {podName}...")
        createPod(v1, podTemplate, podName)
        allPodNames.append(podName)

    for podName in allPodNames:
        print(f"Waiting for pod {podName} to complete...")
        nodeName = waitForPodCompletion(v1, podName)
        if nodeName is not None:
            energy = getMetric(podName)
            metrics.append({"podName": podName, "nodeName": nodeName, "energy": energy})
        # deletePod(v1, podName)

    return metrics

def calculateEnergy(scheduling):
    totalEnergy = sum(pod['energy'] for pod in scheduling)
    averageEnergy = totalEnergy / len(scheduling) if scheduling else 0
    return totalEnergy, averageEnergy

def writeSchedulingToCSV(filename, schedulingType, scheduling):
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = ['schedulingType', 'numberOfInstances', 'podName', 'nodeName', 'energyConsumption']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for numInstances, pods in enumerate(scheduling, start=1):
            for pod in pods:
                writer.writerow({
                    'schedulingType': schedulingType,
                    'numberOfInstances': numInstances,
                    'podName': pod['podName'],
                    'nodeName': pod['nodeName'],
                    'energyConsumption': pod['energy']
                })

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instances', type=int, required=True)
    # parser.add_argument('--nodes', nargs='+', required=True)
    args = parser.parse_args()

    config.load_kube_config()
    v1 = client.CoreV1Api()


    podTemplate["metadata"]["labels"]["scheduling"] = f"standard" 
    standardScheduling = runPods(v1, podTemplate, args.instances+1, "standard") 

    podTemplate["metadata"]["labels"]["scheduling"] = f"energy-aware" 
    energyAwareScheduling = runPods(v1, podTemplate, args.instances+1, "energy-aware") 

    standardTotal, standardAverage = calculateEnergy(standardScheduling)
    energyAwareTotal, energyAwareAverage = calculateEnergy(energyAwareScheduling)

    print(f"Standard scheduling: Total energy = {standardTotal}, Average energy = {standardAverage}")
    print(f"Energy-aware scheduling: Total energy = {energyAwareTotal}, Average energy = {energyAwareAverage}")

    writeSchedulingToCSV('scheduling.csv', 'Standard', standardScheduling)
    writeSchedulingToCSV('scheduling.csv', 'EnergyAware', energyAwareScheduling)

if __name__ == "__main__":
    main()