package mutate

import (
    "encoding/json"
    "fmt"
    "log"

    admissionv1 "k8s.io/api/admission/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    corev1 "k8s.io/api/core/v1"
)

// MutateRequest takes in a request body and returns a mutated request body
// Important to note that you instruct k8s how to update the pod, not modify the pod directly
func MutateRequest(nodeList map[string]int, body []byte) ([]byte, error) {

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

        // get the Pod object and unmarshal it into its struct, if we cannot, we might as well stop here
        if err := json.Unmarshal(ar.Object.Raw, &pod); err != nil {
            return nil, fmt.Errorf("unable to unmarshal pod json object %v", err)
        }
        // set response options
        resp.Allowed = true
        resp.UID = ar.UID
        pT := admissionv1.PatchTypeJSONPatch
        resp.PatchType = &pT

        // Swap container image to ubuntu
        p := []interface{}{}

        // Find efficientNodes with value 1
        efficientNodes := []string{}
        // inefficientNodes := []string{}

        for node, value := range nodeList {
            if value == 1 {
                efficientNodes = append(efficientNodes, node)
            } 
            // else if value == 3 {
            //     inefficientNodes = append(inefficientNodes, node)
            // }
        }

        log.Println(efficientNodes)
        
        // Check if there are efficent nodes specified
        if len(efficientNodes) > 0 {

            // Add node affinity to efficient node
            // At the moment, this schedules to node 1
            affinityPatch := map[string]interface{}{
                "op":    "add",
                "path":  "/spec/affinity",
                "value": map[string]interface{}{
                    "nodeAffinity": map[string]interface{}{
                        // preferredDuringSchedulingIgnoredDuringExecution - enforces pods to be scheduled on given nodes
                        "requiredDuringSchedulingIgnoredDuringExecution": map[string]interface{}{
                            "nodeSelectorTerms": []map[string]interface{}{
                                {
                                    "matchExpressions": []map[string]interface{}{
                                        {
                                            "key":      "node",
                                            "operator": "In",
                                            "values":   efficientNodes,
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
                "value": "modifiedTo" + efficientNodes[0],
            }
            p = append(p, labelPatch)
        }
        
        // // Check if there are inefficient nodes exists
        // if len(inefficientNodes) > 0 {

        //     // Add node affinity to efficient node
        //     // At the moment, this schedules to node 1
        //     affinityPatch := map[string]interface{}{
        //         "op":    "add",
        //         "path":  "/spec/affinity",
        //         "value": map[string]interface{}{
        //             "nodeAffinity": map[string]interface{}{
        //                 // requiredDuringSchedulingIgnoredDuringExecution - enforces pods to be scheduled on given nodes
        //                 "preferredDuringSchedulingIgnoredDuringExecution": map[string]interface{}{
        //                     "nodeSelectorTerms": []map[string]interface{}{
        //                         {
        //                             "matchExpressions": []map[string]interface{}{
        //                                 {
        //                                     "key":      "node",
        //                                     "operator": "In",
        //                                     "values":   inefficientNodes,
        //                                 },
        //                             },
        //                         },
        //                     },
        //                 },
        //             },
        //         },
        //     }
        //     p = append(p, affinityPatch)
        // }   

		// parse the []map into JSON
		resp.Patch, err = json.Marshal(p)

		resp.Result = &metav1.Status{
			Status: "Success",
		}

		admReview.Response = &resp
		// marshall to JSON so we can return the AdmissionReview
		responseBody, err = json.Marshal(admReview)
		if err != nil {
			return nil, err // untested section
		}
    }

	return responseBody, nil
}