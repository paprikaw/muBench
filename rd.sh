#!/bin/bash
# set -e
kubectl delete -f yamls/
rm yamls/*
python configGenerator.py --workmodel chain --replicaCnt 1 --layer all
python Deployers/K8sDeployer/RunK8sDeployer.py -c ./tmp/k8s_parameters.json
