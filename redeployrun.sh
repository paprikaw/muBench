#!/bin/bash
# set -e
kubectl delete -f HealthcareWorkspace/yamls/
rm HealthcareWorkspace/yamls/*
python Deployers/K8sDeployer/RunK8sDeployer.py -c Configs/K8sParameters.json
./run_tests.sh
