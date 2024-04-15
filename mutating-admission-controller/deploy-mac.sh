#!/bin/bash

kubectl delete -f MAC-deploy.yaml -f webhook-config.yaml 
docker build -t ma-controller:latest --rm .
kind load docker-image ma-controller:latest
kubectl apply -f MAC-deploy.yaml 
kubectl apply -f webhook-config.yaml 