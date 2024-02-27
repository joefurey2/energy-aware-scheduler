#!/bin/bash

# Function to create a new user connection on libvirt
create_user_connection() {
    # Define the name for the user connection (modify as needed)
    # user_connection_name="user1"

    # Create a new user connection using virsh
    sudo virsh -c qemu:///session connect 
    if [ $? -ne 0 ]; then
        echo "Failed to create a new user connection."
        exit 1
    fi
}

# Function to start and enter the VM
start_and_enter_vm() {
    # Define the name of the VM (modify as needed)
    vm_name="V"

    # Start the VM
    virsh -c qemu:///session start F
    if [ $? -ne 0 ]; then
        echo "Failed to start the VM: $vm_name"
        exit 1
    fi

    # Enter the VM
    virsh -c qemu:///session console $vm_name
    if [ $? -ne 0 ]; then
        echo "Failed to enter the VM: $vm_name"
        exit 1
    fi
}

# Main function
main() {
    # Create a new user connection on libvirt
    create_user_connection

    # Start and enter the VM
    start_and_enter_vm
}