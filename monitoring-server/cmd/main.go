package main

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
	"sync"
    "time"
	"github.com/gin-gonic/gin"
)

var rankings map[string]int
var rankingsMutex = &sync.Mutex{}


type Metric struct {
    Metric struct {
        Node string `json:"node"`
    } `json:"metric"`
    Value []interface{} `json:"value"`
}

type QueryResult struct {
    ResultType string   `json:"resultType"`
    Result     []Metric `json:"result"`
}

type PrometheusResponse struct {
    Status string      `json:"status"`
    Data   QueryResult `json:"data"`
}

func fetchMetrics() ([]Metric, error) {
    resp, err := http.Get("http://prometheus-server:9090/api/v1/query?query=node_cpu_seconds_total")
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    body, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, err
    }

    var data PrometheusResponse
    err = json.Unmarshal(body, &data)
    if err != nil {
        return nil, err
    }

    return data.Data.Result, nil
}

func computeRankings(metrics []Metric) map[string]int {
    rankings := make(map[string]int)
    for _, metric := range metrics {
        // Compute the ranking for each node.
        // This is a placeholder. Replace this with your actual ranking computation.
        rankings[metric.Metric.Node] = 1
    }
    return rankings
}

func updateRankings() {
    for {
        metrics, err := fetchMetrics()
        if err != nil {
            fmt.Println("Error fetching metrics:", err)
            time.Sleep(1 * time.Minute)
            continue
        }

        newRankings := computeRankings(metrics)

        rankingsMutex.Lock()
        rankings = newRankings
        rankingsMutex.Unlock()

        time.Sleep(1 * time.Minute)
    }
}

func main() {
    go updateRankings()

    router := gin.Default()
    router.GET("/rankings", func(c *gin.Context) {
        rankingsMutex.Lock()
        defer rankingsMutex.Unlock()

        c.JSON(http.StatusOK, rankings)
    })

    router.Run(":8080")
}