package mutate

import (
	// "net/http"
	"encoding/json"
	"fmt"
	"log"

	admissionv1 "k8s.io/api/admission/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	corev1 "k8s.io/api/core/v1"
)

// MutateRequest takes in a request body and returns a mutated request body
// Important to note that you instruct k8s how to update the pod, not modify the pod directly
func MutateRequest(body []byte) ([]byte, error) {

    // unmarshalls (byte string -> JSON) request into AdmissionReview struct
	admReview := admissionv1.AdmissionReview{}
	if err := json.Unmarshal(body, &admReview); err != nil {
		return nil, fmt.Errorf("unmarshaling request failed with %s", err)
	}

    log.Println(admReview)

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

		// Audit annotations are stored in the kube-api-server and can be viewed with kubectl describe
		resp.AuditAnnotations = map[string]string{
			"mutating-admission-controller": "this pod was mutated",
		}

        // Swap container image to ubuntu
		p := []map[string]string{}
        for i := range pod.Spec.Containers {
            patch := map[string]string{
                "op":    "replace",
                "path":  fmt.Sprintf("/spec/containers/%d/image", i),
                "value": "ubuntu",
            }
            p = append(p, patch)
        }

        // Add a label to the pod
        labelPatch := map[string]string{
            "op":    "add",
            "path":  "/metadata/labels/modified",
            "value": "true",
        }
        p = append(p, labelPatch)

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