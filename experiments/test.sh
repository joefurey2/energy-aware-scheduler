#!/bin/bash

# List of job files
jobs=("low-stress.yaml" "medium-stress.yaml" "high-stress.yaml")

for job in ${jobs[@]}; do
  # Apply the job
  kubectl apply -f $job

  # Extract the job name
  job_name=$(cat $job | grep "name:" | head -1 | awk '{print $2}')

  # Wait for the job to complete
  while true; do
    if [[ $(kubectl get jobs $job_name -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}') == "True" ]]; then
      echo "Job $job_name completed"
      break
    else
      echo "Waiting for job $job_name to complete"
      sleep 10
    fi
  done
done