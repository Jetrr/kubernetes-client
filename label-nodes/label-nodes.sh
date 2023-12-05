#!/bin/bash
# label-nodes.sh

# Get the name of the current node
NODE_NAME=$(hostname)

# Label the node
kubectl label nodes $NODE_NAME gpu=true --overwrite
