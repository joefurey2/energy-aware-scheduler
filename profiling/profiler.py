import time
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect
import yaml
import argparse

config.load_kube_config()
v1 = client.CoreV1Api()

podTemplate = {
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "pod-stress",
        "labels": {
            "job": ""
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

def getMetric(metricName):
    prom = PrometheusConnect(url="http://localhost:9090", disable_ssl=True)
    metricData = prom.get_current_metric_value(metricName)
    return metricData

def createPod(v1, podTemplate, podName, namespace="default"):
    podTemplate["metadata"]["name"] = podName
    v1.create_namespaced_pod(body=podTemplate, namespace=namespace)

def waitForPodCompletion(v1, podName, namespace="default"):
    while True:
        podStatus = v1.read_namespaced_pod_status(podName, namespace).status.phase
        if podStatus == "Succeeded" or podStatus == "Failed":
            break
        time.sleep(1)

def runPods(v1, podTemplate, numInstances, metricName):
    metrics = {}
    for i in range(1, numInstances + 1):
        metrics[i] = []
        for j in range(i):
            podName = f"stress-{i}instance-pod{j+1}"
            createPod(v1, podTemplate, podName)
        for j in range(i):
            podName = f"stress-{i}instance-pod{j+1}"
            waitForPodCompletion(v1, podName)
            metric = getMetric(metricName)
            metrics[i].append({"podName": podName, "metric": metric})
    return metrics

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("nodeName", help="the name of the node where the pods will be scheduled")
    parser.add_argument("numInstances", type=int, help="the number of pod instances to create")
    args = parser.parse_args()

    config.load_kube_config()
    v1 = client.CoreV1Api()

    podTemplate["spec"]["nodeName"] = args.nodeName

    metrics = runPods(v1, podTemplate, args.numInstances, "myMetric")  # replace with your actual values
    for numPods, metric in metrics:
        print(f"Number of pods: {numPods}, Metric: {metric}")

if __name__ == "__main__":
    main()