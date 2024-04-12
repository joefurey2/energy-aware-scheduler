import csv


def find_optimal_scheduling(metrics):
    optimal_scheduling = {}

    for numInstances, combinations in metrics.items():
        min_energy = float('inf')
        optimal_combination = None
        for combinationMetrics in combinations:
            for combination, pods in combinationMetrics.items():
                total_energy = sum(pod['energy'] for pod in pods)
                if total_energy < min_energy:
                    min_energy = total_energy
                    optimal_combination = combination
        optimal_scheduling[numInstances] = optimal_combination

    return optimal_scheduling



filename = input("10.csv")

metrics = {}

with open(filename, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        numInstances = row['numberOfInstances']
        combination = row['combination']
        nodeName = row['nodeName']
        podName = row['podName']
        energy = float(row['energyConsumption'])  # assuming energy is a float

        if numInstances not in metrics:
            metrics[numInstances] = []
        if not any(combinationMetrics for combinationMetrics in metrics[numInstances] if combination in combinationMetrics):
            metrics[numInstances].append({combination: []})

        for combinationMetrics in metrics[numInstances]:
            if combination in combinationMetrics:
                combinationMetrics[combination].append({"nodeName": nodeName, "podName": podName, "energy": energy})

optimal_scheduling = find_optimal_scheduling(metrics)
print(optimal_scheduling)