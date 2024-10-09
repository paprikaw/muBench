#!/bin/bash
set -e
kubectl delete -f HealthcareWorkspace/yamls/
rm HealthcareWorkspace/yamls/*
