#!/bin/bash
prometheus_multiproc_dir=/app APP="data-compression" ZONE="default" K8S_APP="muBench" PN=1 TN=1 python ServiceCell/CellController-mp-debug.py
