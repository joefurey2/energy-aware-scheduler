package main

import (
	"encoding/json"
	"fmt"
	"html"
	"io"
	"log"
	"net/http"
	"time"
	"github.com/gin-gonic/gin"
	mutate "github.com/joefurey2/mutating-admission-controller/pkg/mutate"
)

type Node struct {
	Name string `json:"name"`
	// Add other fields as needed
}
// Any path not specified be handled by this function
// Prevents XSS attacks and other errors
func handleRoot(c *gin.Context) {
	log.Println("Root request!")
	fmt.Fprint(c.Writer, "hello %q", html.EscapeString(c.Request.URL.Path))
}


var nodeList map[string]int

// Update the ranking of nodes based on energy efficiency
// This endpoint can be called to update the ranking of nodes
func handleUpdate(c *gin.Context) {
	body, err := io.ReadAll(c.Request.Body)
	defer c.Request.Body.Close()

	if err != nil {
		log.Println(err)
		c.Writer.WriteHeader(http.StatusInternalServerError)
		return
	}

	var nodes map[string]int
	err = json.Unmarshal(body, &nodes)
	if err != nil {
		log.Println(err)
		c.Writer.WriteHeader(http.StatusInternalServerError)
		return
	}

	err = json.Unmarshal(body, &nodes)
	log.Println(nodes)
	if err != nil {
		log.Println(err)
		c.Writer.WriteHeader(http.StatusBadRequest)
		return
	}

	nodeList = nodes

	log.Println("Node ranking updated!")
	c.Writer.WriteHeader(http.StatusOK)
}

// Function to get current ranking of nodes stored in the system
func handleGetRanking(c *gin.Context) {
	rankingJSON, err := json.Marshal(nodeList)
	if err != nil {
		log.Println(err)
		c.Writer.WriteHeader(http.StatusInternalServerError)
		return
	}

	c.Writer.Header().Set("Content-Type", "application/json")
	c.Writer.WriteHeader(http.StatusOK)
	c.Writer.Write(rankingJSON)
}



/*
	Admission controller recieves admission requests from the API server
	It then reads and mutates the request, returning the mutated request to the API server
*/
func handleMutate(c *gin.Context) {
	body, err := io.ReadAll(c.Request.Body)
	defer c.Request.Body.Close()

	if err != nil {
		log.Println(err)
		c.Writer.WriteHeader(http.StatusInternalServerError)
		return
	}

	// mutate the request
	mutated, err := mutate.MutateRequest(body)
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


func main() {

	log.Println("Starting server...")

	router := gin.Default()
	router.GET("/", handleRoot)
	router.POST("/mutate", handleMutate)
	router.POST("/ranking", handleUpdate)
	router.GET("/ranking", handleGetRanking)

	s := &http.Server {
		Addr:           ":8443",
		Handler: 	  	router,
		ReadTimeout:   	10 * time.Second,
		WriteTimeout: 	10 * time.Second,
		MaxHeaderBytes: 1 << 20,
	}

	log.Println("Listing for requests at http://localhost:8443")
	log.Fatal(s.ListenAndServeTLS("./ssl/mutating-admission-controller.pem", "./ssl/mutating-admission-controller.key" ))

}

