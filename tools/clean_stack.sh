#!/bin/bash

echo "Cleaning resources not deleted by tests..."

if [ ! $OS_USERNAME ]; then
   echo "You must source an rc file first !"
   echo "Exiting."
   exit 1
fi

types=(server image snapshot volume keypair "security group" "floating ip") 

for type in "${types[@]}"; do
    items=$(openstack $type list | awk '/fgmonitoring/{print $2}')
    for i in $items; do
        echo "Deleting $type $i"
        openstack $type delete $i
    done
done
