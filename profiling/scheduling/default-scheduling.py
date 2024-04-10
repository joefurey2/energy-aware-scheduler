import csv
import time
from kubernetes import client, config

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
    # Replace with your actual function to get the metric
    return "metric"

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
        print(f"Getting metric for pod {podName}...")
        energy = getMetric(podName)
        metrics.append({"podName": podName, "energy": energy})
        print(f"Deleting pod {podName}...")
        deletePod(v1, podName)
    return metrics

config.load_kube_config()
v1 = client.CoreV1Api()

# Replace with your actual pod template
podTemplate = client.V1Pod()

numPods = 10  # Replace with your actual number of pods
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


