#!/bin/bash
docker build -t xu/mubench/svc:dev ServiceCell
./redeploy.sh
