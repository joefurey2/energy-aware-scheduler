package main

import (
	"encoding/json"
	"fmt"
	"html"
	"io"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	mutate "github.com/joefurey2/mutating-admission-controller/pkg/mutate"
)

// var podCounts = make(map[string]int)
var optimalSchedule = make(map[int]map[string]int)

var mutex = &sync.Mutex{}

// Any unknown path is handled by this function
// Prevents XSS attacks and other errors
func handleRoot(c *gin.Context) {
	log.Println("Root request!")
	fmt.Fprint(c.Writer, "hello %q", html.EscapeString(c.Request.URL.Path))
}

var nodeList map[string]int

/*
Admission controller recieves admission requests from the kube-api server
It then reads and mutates the request, returning the mutated request to the kube-api server
*/
func handleMutate(c *gin.Context) {
	body, err := io.ReadAll(c.Request.Body)
	defer c.Request.Body.Close()

	if err != nil {
		log.Println(err)
		c.Writer.WriteHeader(http.StatusInternalServerError)
		return
	}

	// Mutate the request
	mutated, err := mutate.MutateRequest(nodeList, body)
	if err != nil {
		log.Println(err)
		c.Writer.WriteHeader(http.StatusInternalServerError)
		return
	}

	log.Println("mutated!!")

	// Send back mutated admission controller
	c.Writer.WriteHeader(http.StatusOK)
	c.Writer.Write(mutated)
}

func handleSchedule(c *gin.Context) {

	var schedule map[int]map[string]int

	if err := c.ShouldBindJSON(&schedule); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	mutex.Lock()
	for numInstances, nodeCounts := range schedule {
		if _, exists := optimalSchedule[numInstances]; !exists {
			optimalSchedule[numInstances] = make(map[string]int)
		}
		for node, count := range nodeCounts {
			optimalSchedule[numInstances][node] += count
		}
	}
	mutex.Unlock()

	c.JSON(http.StatusOK, gin.H{"message": "Schedule received successfully"})
}

// Endpoint to return current ranking of nodes stored in controller
func handleGetSchedule(c *gin.Context) {
	rankingJSON, err := json.Marshal(optimalSchedule)
	if err != nil {
		log.Println(err)
		c.Writer.WriteHeader(http.StatusInternalServerError)
		return
	}

	c.Writer.Header().Set("Content-Type", "application/json")
	c.Writer.WriteHeader(http.StatusOK)
	c.Writer.Write(rankingJSON)
}

func main() {

	log.Println("Starting server...")

	router := gin.Default()
	router.GET("/", handleRoot)
	router.POST("/schedule", handleSchedule)
	router.GET("/schedule", handleGetSchedule)
	router.POST("/mutate", handleMutate)

	s := &http.Server{
		Addr:           ":8443",
		Handler:        router,
		ReadTimeout:    10 * time.Second,
		WriteTimeout:   10 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	log.Println("Listing for requests at http://localhost:8443")
	log.Fatal(s.ListenAndServeTLS("./ssl/mutating-admission-controller.pem", "./ssl/mutating-admission-controller.key"))

}
