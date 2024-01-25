This is my implementation of a basic Mutating Admission Controller (MAC)

Link to K8 [docs][https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/]

My approach to implement an energy aware scheduling will be to use a MAC

The MAC will recieve all pods and deployments before they are scheduled

The MAC will be aware of current energy efficiency of nodes

The MAC will modify the pods due to be scheduled. It will set the affinity 