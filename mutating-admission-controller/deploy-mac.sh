#!/bin/bash

k delete -f MAC-deploy.yaml -f webhook-config.yaml 
docker build -t ma-controller:latest --rm .
kind load docker-image ma-controller:latest
k apply -f MAC-deploy.yaml 
k apply -f webhook-config.yaml 