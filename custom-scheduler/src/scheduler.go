package main

import (
     scheduler "k8s.io/kubernetes/pkg/scheduler/apis"		//"k8s.io/kubernetes/cmd/kube-scheduler/app"
	"k8s.io/kubernetes/pkg/scheduler/apis/config"
    "k8s.io/kubernetes/pkg/scheduler/apis/config/scheme"
    "k8s.io/kubernetes/pkg/scheduler/apis/config/v1beta2"
    "k8s.io/kubernetes/pkg/scheduler/profile"
)

func main() {
    command := scheduler.NewSchedulerCommand(
            scheduler.WithPlugin("example-plugin1", ExamplePlugin1),
            scheduler.WithPlugin("example-plugin2", ExamplePlugin2))
    if err := command.Execute(); err != nil {
        fmt.Fprintf(os.Stderr, "%v\n", err)
        os.Exit(1)
    }
}