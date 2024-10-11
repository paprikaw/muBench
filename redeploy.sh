#!/bin/bash
# set -e
kubectl delete -f yamls/
rm yamls/*
python configGenerator.py --workmodel aggregator --replicaCnt 7 --layer cloud 
python Deployers/K8sDeployer/RunK8sDeployer.py -c ./tmp/k8s_parameters.json
