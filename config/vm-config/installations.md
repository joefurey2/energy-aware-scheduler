curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"


# Configuring VM for connecting via virsh

edit /etc/default/grub
GRUB_CMDLINE_LINUX="console=ttyS0"
grub-editenv - unset kernelopts

RebootVM

grubby --update-kernel=ALL --args="console=ttyS0"

# Script to connect to VM on feng-linux machine

