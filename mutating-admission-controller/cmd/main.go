package main

import (
	"fmt"
	"html"
	"io/ioutil"
	"log"
	"net/http"
	"time"
)

// Any path not specified be handled by this function
// Prevents XSS attacks and other errors
func handleRoot(w http.ResponseWriter, req *http.Request) {
	log.Println("Root request!")
	fmt.Fprint(w, "hello %q", html.EscapeString(req.URL.Path))
}

/*
	Admission controller recieves admission requests from the API server
	It then reads and mutates the request, returning the mutated request to the API server
*/
func handleMutate(w http.ResponseWriter, req *http.Request) {
	body, err := ioutil.ReadAll(req.Body)
	defer req.Body.Close()

	if err != nil {
		log.Println(err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	log.Println(body)
	
	// Modify the body to say "mutated"
	body = []byte("mutated")
	log.Println("mutated!!")

	// Send back mutated admission controller
	w.WriteHeader(http.StatusOK)
	w.Write(body)
}


func main() {

	log.Println("Starting server...")

	mux := http.NewServeMux()
	mux.HandleFunc("/", handleRoot)
	mux.HandleFunc("/mutate", handleMutate)

	s := &http.Server {
		Addr:           ":8443",
		Handler: 	  	mux,
		ReadTimeout:   	10 * time.Second,
		WriteTimeout: 	10 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	log.Println("Listing for requests at http://localhost:8443")
	log.Fatal(s.ListenAndServeTLS("./ssl/mutating-admission-controller.pem", "./ssl/mutating-admission-controller.key" ))

}

