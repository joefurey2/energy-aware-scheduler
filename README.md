# Energy aware scheduling in Kubernetes

The project aims to schedule workloads across a Kubernetes cluster in a more energy efficient way.

There are 3 key components to the project:

A custom controller, providing a framework to control the scheduling of pods onto nodes across a cluster
A model/process to evaluate and rank the energy efficiencies of different nodes
The collection of energy consumption metrics of nodes and clusters as a whole, to be used for evaluation and ranking efficiencies
A custom Mutating Admission Controller (MAC) will be created. This will provide a framework to implement and test different scheduling mechanisms and ideas.

The MAC will intercept pods due to be scheduled and will apply affinity and anti affinity to different nodes based on a ranking provided to the controller. Scheduling tasks on more energy efficient nodes should reduce the overall energy consumption.

This project will utilise the Kepler monitoring tool (https://sustainable-computing.io/) to get information about cluster and nodes energy usage and efficiency

Finally, different models and ranking ideas will be implemented, tested and evaluated to look at the effectiveness of this project
