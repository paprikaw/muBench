#!/bin/bash
# set -e
kubectl delete -f yamls/
rm yamls/*
python configGenerator.py --workmodel aggregator --replicaCnt 3 --layer edge 
python Deployers/K8sDeployer/RunK8sDeployer.py -c ./tmp/k8s_parameters.json
