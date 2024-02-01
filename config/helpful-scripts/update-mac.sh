#!/bin/bash

# This script is used to update the mutating admission controller
# I added this script to my .bash_profile and .zshrc to speed up the process
function deploy_mac() {

        kubectl delete deploy mutating-admission-controller
        kubectl delete mutatingwebhookconfigurations.admissionregistration.k8s.io mutating-admission-controller
        kubectl apply -f /Users/jfurey003/Desktop/diss/energy-aware-scheduler/config/k8s-resources/service-deploy.yaml
        kubectl apply -f /Users/jfurey003/Desktop/diss/energy-aware-scheduler/config/k8s-resources/webhook-config.yaml
        kubectl delete pod testpod

}