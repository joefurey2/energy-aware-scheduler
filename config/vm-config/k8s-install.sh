#!/bin/bash

# # Update package repositories
# sudo dnf update -y

# # Install dependencies
# sudo dnf install -y curl

# Install Docker Engine (prerequisite for Kubernetes)
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker

# Install Kubernetes tools
sudo dnf install -y kubelet kubeadm kubectl

# Enable and start kubelet service
sudo systemctl enable --now kubelet

echo "Kubernetes installation complete!"
