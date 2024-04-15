package mutate

import (
    "encoding/json"
    "fmt"
    "log"
    "math"
    admissionv1 "k8s.io/api/admission/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    corev1 "k8s.io/api/core/v1"
)

var totalInstances = 0

// MutateRequest takes in a request body and returns a mutated request body
// Note: to modify a pod, instruct k8s how to update the pod, not modify the pod directly
func MutateRequest(optimalSchedule map[int]map[string]int, podCounts map[string]int, body []byte) ([]byte, error) {

    log.Printf("Current pod counts: %v, Total instances: %d\n", podCounts, totalInstances)
    
    totalInstances++
    // unmarshalls (byte string -> JSON) request into AdmissionReview struct
    admReview := admissionv1.AdmissionReview{}
    if err := json.Unmarshal(body, &admReview); err != nil {
        return nil, fmt.Errorf("unmarshaling request failed with %s", err)
    }
    var err error
    var pod *corev1.Pod

    responseBody := []byte{}

    ar := admReview.Request
    resp := admissionv1.AdmissionResponse{}

    if ar != nil {

        // Catches invalid request
        if err := json.Unmarshal(ar.Object.Raw, &pod); err != nil {
            return nil, fmt.Errorf("unable to unmarshal pod json object %v", err)
        }

        resp.Allowed = true
        resp.UID = ar.UID
        pT := admissionv1.PatchTypeJSONPatch
        resp.PatchType = &pT

        // Used for modification
        p := []interface{}{}

        optimalNodeCounts := optimalSchedule[totalInstances]

        // Find the node with the least difference between the current number of pods and the optimal number of pods
        var bestNode string
        var minDifference = math.MaxInt32
        for node, optimalCount := range optimalNodeCounts {
            currentCount := podCounts[node]
            if currentCount >= optimalCount {
                // Skip this node if scheduling another pod on it would exceed the optimal count
                continue
            }
            difference := int(math.Abs(float64(optimalCount - currentCount - 1))) // Subtract 1 because we're adding a new pod
            if difference < minDifference {
                minDifference = difference
                bestNode = node
            }
        }

        log.Printf("affinity set to %s", bestNode)

        labels := pod.GetLabels()

        // Check if the pod has the label "scheduling=energy-aware"
        if value, ok := labels["scheduling"]; ok && value == "energy-aware" {
            // Add node affinity to efficient node
            affinityPatch := map[string]interface{}{
                "op":    "add",
                "path":  "/spec/affinity",
                "value": map[string]interface{}{
                    "nodeAffinity": map[string]interface{}{
                        // requiredDuringSchedulingIgnoredDuringExecution - hard requirement
                        // preferredDuringSchedulingIgnoredDuringExecution - This can be used to give a weighting instesd of enforcing onto a single node
                        "requiredDuringSchedulingIgnoredDuringExecution": map[string]interface{}{
                            "nodeSelectorTerms": []map[string]interface{}{
                                {
                                    "matchExpressions": []map[string]interface{}{
                                        {
                                            "key":      "kubernetes.io/hostname",
                                            "operator": "In",
                                            "values":   []string{bestNode},
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            }        
            p = append(p, affinityPatch)
    
            // Add a label to the pod
            labelPatch := map[string]string{
                "op":    "add",
                "path":  "/metadata/labels/modified",
                "value": "modifiedTo" + bestNode,
            }
            p = append(p, labelPatch)
        }       


        // Marshal patch before return to API server
        resp.Patch, err = json.Marshal(p)

        resp.Result = &metav1.Status{
            Status: "Success",
        }

        admReview.Response = &resp
        // marshall to JSON so we can return the AdmissionReview
        responseBody, err = json.Marshal(admReview)
        if err != nil {
            return nil, err 
        }
        
    }

	return responseBody, nil
}