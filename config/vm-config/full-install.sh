#!/bin/bash

# Update package repositories
sudo dnf update -y

# Install dependencies
sudo dnf install -y curl wget gnupg2 software-properties-common apt-transport-https ca-certificates

# Install Docker Engine
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker

# Install Kubernetes tools
sudo dnf install -y kubelet kubeadm kubectl

# Install Kind
GO_VERSION="1.19.3"  # Change to desired Go version
KIND_VERSION="v0.20."  # Change to desired Kind version

# Install Go
wget https://golang.org/dl/go${GO_VERSION}.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# Install Kind
GO111MODULE="on" go get sigs.k8s.io/kind@${KIND_VERSION}

# Install Prometheus
sudo dnf install -y prometheus

echo "Installation complete!"
