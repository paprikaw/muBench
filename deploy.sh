#!/bin/bash
rm HealthcareWorkspace/yamls/*
rm HealthcareWorkspace/Result/*
python Deployers/K8sDeployer/RunK8sDeployer.py -c Configs/K8sParameters.json
